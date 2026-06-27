"""Verify wiring cờ --only-upi: setup.sh → CLI web → server inject → FE ẩn tab.

Run: python3 test/check_only_upi.py

Kiểm:
  [1] Syntax cli.py + web/server.py.
  [2] server.py: _only_upi + set_only_upi() + replace __ONLY_UPI__.
  [3] index.html: body data-only-upi="__ONLY_UPI__".
  [4] style.css: rule ẩn tab-btn != upi khi only-upi.
  [5] app.js: _isOnlyUpiMode + guard persist + ép tab upi.
  [6] cli.py: option --only-upi + gọi set_only_upi().
  [7] setup.sh: parse --only-upi + truyền $ONLY_UPI_FLAG vào lệnh web.
  [8] Functional: index() render body data-only-upi="1"/"0" theo set_only_upi().
"""
from __future__ import annotations

import ast
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _parse(p: Path) -> None:
    ast.parse(p.read_text(encoding="utf-8"), filename=str(p))


def main() -> int:
    failures: list[str] = []

    def check(cond: bool, label: str) -> None:
        if cond:
            print(f"[PASS] {label}", flush=True)
        else:
            failures.append(label)
            print(f"[FAIL] {label}", flush=True)

    # [1] Syntax
    for f in [ROOT / "cli.py", ROOT / "web" / "server.py"]:
        try:
            _parse(f)
            print(f"[PASS] syntax {f.relative_to(ROOT)}", flush=True)
        except SyntaxError as e:
            failures.append(f"syntax {f}: {e}")
            print(f"[FAIL] syntax {f.relative_to(ROOT)} :: {e}", flush=True)

    server_src = (ROOT / "web" / "server.py").read_text(encoding="utf-8")
    html_src = (ROOT / "web" / "static" / "index.html").read_text(encoding="utf-8")
    css_src = (ROOT / "web" / "static" / "style.css").read_text(encoding="utf-8")
    app_src = (ROOT / "web" / "static" / "app.js").read_text(encoding="utf-8")
    cli_src = (ROOT / "cli.py").read_text(encoding="utf-8")
    setup_src = (ROOT / "setup.sh").read_text(encoding="utf-8")

    # [2] server.py wiring
    check("_only_upi" in server_src, "server.py: có global _only_upi")
    check("def set_only_upi" in server_src, "server.py: có set_only_upi()")
    check('.replace("__ONLY_UPI__"' in server_src,
          "server.py: index() replace __ONLY_UPI__")

    # [3] index.html
    check('data-only-upi="__ONLY_UPI__"' in html_src,
          'index.html: body có data-only-upi="__ONLY_UPI__"')

    # [4] style.css
    check('body[data-only-upi="1"] .tab-btn:not([data-tab="upi"])' in css_src,
          "style.css: ẩn tab-btn != upi khi only-upi")

    # [5] app.js
    check("_isOnlyUpiMode" in app_src, "app.js: có _isOnlyUpiMode()")
    check("dataset.onlyUpi === '1'" in app_src,
          "app.js: đọc dataset.onlyUpi")
    check("if (!_isOnlyUpiMode()) Settings.save('ui.active_tab'" in app_src,
          "app.js: skip persist ui.active_tab khi only-upi")
    check("if (_isOnlyUpiMode()) {\n      activateTab('upi');" in app_src,
          "app.js: ép tab upi trong initTabs")

    # [6] cli.py
    check('"--only-upi"' in cli_src, "cli.py: có option --only-upi")
    check("set_only_upi(only_upi)" in cli_src,
          "cli.py: gọi set_only_upi(only_upi)")

    # [7] setup.sh
    check("--only-upi) ONLY_UPI=" in setup_src,
          "setup.sh: parse case --only-upi")
    check('ONLY_UPI_FLAG="--only-upi"' in setup_src,
          "setup.sh: set ONLY_UPI_FLAG")
    check('web --host "$HOST" --port "$PORT" $ONLY_UPI_FLAG' in setup_src,
          "setup.sh: truyền $ONLY_UPI_FLAG vào lệnh web")

    # [8] Functional render
    try:
        from web.server import index, set_only_upi

        async def _render() -> str:
            resp = await index()
            return resp.body.decode("utf-8")

        set_only_upi(True)
        html_on = asyncio.run(_render())
        check('data-only-upi="1"' in html_on,
              "render: only-upi ON → body data-only-upi=\"1\"")
        check("__ONLY_UPI__" not in html_on,
              "render: placeholder __ONLY_UPI__ đã được thay")

        set_only_upi(False)
        html_off = asyncio.run(_render())
        check('data-only-upi="0"' in html_off,
              "render: only-upi OFF → body data-only-upi=\"0\"")
    except Exception as e:  # noqa: BLE001
        failures.append(f"functional render: {type(e).__name__}: {e}")
        print(f"[FAIL] functional render :: {e}", flush=True)

    print("", flush=True)
    if failures:
        print(f"=== {len(failures)} FAILURE(S) ===", flush=True)
        for x in failures:
            print(f"  - {x}", flush=True)
        return 1
    print("=== ALL PASS ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
