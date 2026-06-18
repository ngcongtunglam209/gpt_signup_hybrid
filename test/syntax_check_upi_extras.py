"""Syntax check cho các file đã sửa khi thêm tính năng UPI:
- highlight + scroll line input khi click job
- nút Retry Failed (giống màn reg)

Check Python AST cho web/manager.py + web/server.py.
JS/HTML không có parser stdlib — chỉ check token cơ bản (cân bằng ngoặc, chuỗi).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PY_FILES = [
    ROOT / "web" / "manager.py",
    ROOT / "web" / "server.py",
]

JS_FILES = [
    ROOT / "web" / "static" / "upi.js",
]

HTML_FILES = [
    ROOT / "web" / "static" / "index.html",
]


def check_python(path: Path) -> tuple[bool, str]:
    try:
        src = path.read_text(encoding="utf-8")
        ast.parse(src, filename=str(path))
        return True, f"AST ok ({len(src.splitlines())} lines)"
    except SyntaxError as exc:
        return False, f"SyntaxError: {exc}"
    except OSError as exc:
        return False, f"IOError: {exc}"


def check_braces(path: Path, *, allow_html: bool = False) -> tuple[bool, str]:
    """Check balance ngoặc { } ( ) [ ] (loại trừ trong string + comment đơn giản).

    Không phải full parser nhưng đủ để bắt typo nghiêm trọng.
    """
    try:
        src = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"IOError: {exc}"

    stack: list[tuple[str, int, int]] = []  # (char, line, col)
    pairs = {")": "(", "}": "{", "]": "["}
    in_string: str | None = None  # ' " ` or None
    escape = False
    in_line_comment = False
    in_block_comment = False
    line = 1
    col = 0

    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            col = 0
            in_line_comment = False
            i += 1
            continue
        col += 1

        if in_block_comment:
            if c == "*" and i + 1 < n and src[i + 1] == "/":
                in_block_comment = False
                i += 2
                col += 1
                continue
            i += 1
            continue
        if in_line_comment:
            i += 1
            continue
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == in_string:
                in_string = None
            i += 1
            continue

        # Detect comment starts (JS only)
        if not allow_html and c == "/" and i + 1 < n:
            nxt = src[i + 1]
            if nxt == "/":
                in_line_comment = True
                i += 2
                col += 1
                continue
            if nxt == "*":
                in_block_comment = True
                i += 2
                col += 1
                continue

        if c in ("'", '"', "`") and not allow_html:
            in_string = c
            i += 1
            continue

        if c in "({[":
            stack.append((c, line, col))
        elif c in ")}]":
            if not stack:
                return False, f"Unmatched closing '{c}' at {line}:{col}"
            top = stack[-1][0]
            if top != pairs[c]:
                return False, (
                    f"Mismatched '{c}' at {line}:{col}, expected close of "
                    f"'{top}' opened at {stack[-1][1]}:{stack[-1][2]}"
                )
            stack.pop()
        i += 1

    if stack:
        ch, ln, cl = stack[-1]
        return False, f"Unclosed '{ch}' opened at {ln}:{cl} (depth={len(stack)})"
    return True, f"braces ok ({len(src.splitlines())} lines)"


def check_html_marker(path: Path, marker: str) -> tuple[bool, str]:
    try:
        src = path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"IOError: {exc}"
    if marker in src:
        return True, f"contains marker {marker!r}"
    return False, f"missing marker {marker!r}"


def main() -> int:
    failed = 0
    print("[1/4] Python AST check")
    for p in PY_FILES:
        ok, msg = check_python(p)
        tag = "[PASS]" if ok else "[FAIL]"
        print(f"  {tag} {p.relative_to(ROOT)} :: {msg}", flush=True)
        if not ok:
            failed += 1

    print("[2/4] JS brace balance check")
    for p in JS_FILES:
        ok, msg = check_braces(p)
        tag = "[PASS]" if ok else "[FAIL]"
        print(f"  {tag} {p.relative_to(ROOT)} :: {msg}", flush=True)
        if not ok:
            failed += 1

    print("[3/4] HTML markers")
    for p in HTML_FILES:
        ok, msg = check_html_marker(p, 'id="upi-btn-retry-failed"')
        tag = "[PASS]" if ok else "[FAIL]"
        print(f"  {tag} {p.relative_to(ROOT)} :: {msg}", flush=True)
        if not ok:
            failed += 1

    print("[4/4] JS markers (handler + endpoint + highlight)")
    for p in JS_FILES:
        for marker in (
            "btnRetryFailed",
            "/api/upi/jobs/retry-failed",
            "highlightInputLine",
        ):
            ok, msg = check_html_marker(p, marker)
            tag = "[PASS]" if ok else "[FAIL]"
            print(f"  {tag} {p.relative_to(ROOT)} :: {msg}", flush=True)
            if not ok:
                failed += 1

    print(f"\nDone. {failed} failure(s).", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
