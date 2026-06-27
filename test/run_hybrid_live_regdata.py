"""Live test reg hybrid + POST-REG DEACTIVATION RECHECK cho bugfix nhánh A.

Spec: reg-hybrid-deactivated-after-signup (nhánh A — bỏ double-POST
create_account trong HybridChatGPTRelay.run()). Bug: account reg hybrid báo
success=True (callback + /api/auth/session 200) nhưng bị server vô hiệu hóa NGAY
SAU reg (deferred ban). Test này reg 5 account rồi đợi một khoảng và GỌI LẠI
session endpoint để phân loại ACTIVE vs DEACTIVATED.

Tái dùng MẪU CHUẨN production (giống test/smoke_reg_icloud_v3.py):
  - Settings Store: db.get_settings_repo(get_engine()).list() → headless /
    job_timeout / default_password (reg.headless / reg.job_timeout /
    reg.default_password).
  - Proxy: web.manager._resolve_job_proxy() (giống autoreg/production).
  - Mail: web.mail_modes.get_spec("icloud_v3") → spec.parse_line / build_request.
  - Chạy signup.run_signup(request, log=...).

KHÁC smoke:
  1. 5 dòng data (hằng LINES).
  2. ÉP reg_mode="hybrid" mỗi request (smoke mặc định browser).
  3. Chạy TUẦN TỰ 5 account, lưu JSON ra runtime/live_hybrid_regdata/.
  4. POST-REG DEACTIVATION RECHECK: sau reg success đợi HYBRID_RECHECK_DELAY giây
     rồi GET /api/auth/session (cookies) + /backend-api/me (Bearer access_token)
     → ACTIVE / DEACTIVATED / recheck_skipped.
  5. Summary cuối: bảng success + active/deactivated từng account.

ENV:
  - HYBRID_RECHECK_DELAY : số giây đợi trước recheck (mặc định 60). =0 → recheck ngay.
  - HYBRID_RECHECK       : "0"/"false" → tắt recheck hẳn (mặc định bật).

Cách dùng:
  - Validate OFFLINE (KHÔNG signup, KHÔNG network):
        .venv/bin/python test/run_hybrid_live_regdata.py --dry-run
  - Chạy THẬT (reg network + recheck):
        .venv/bin/python test/run_hybrid_live_regdata.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ─── 5 dòng reg data user cung cấp (email|api_url icloud_v3) ──────────
LINES: list[str] = [
    "blog.pod_36+8pjb9p@icloud.com|https://icloud-cf-mail-v2.n5pskgzs9g.workers.dev/readmail/rbH7JDLf1uMxsEpqQfuQ-9GclVPddc2M/data",
    "blog.pod_36+aupcv@icloud.com|https://icloud-cf-mail-v2.n5pskgzs9g.workers.dev/readmail/_HbsUPnYX7EbOfrPhC2HLUY7ymO2gqQA/data",
    "blog.pod_36+gl48bl@icloud.com|https://icloud-cf-mail-v2.n5pskgzs9g.workers.dev/readmail/eXOshjYH5fDmI-nV1IZGaQkvMwm1h13C/data",
    "blog.pod_36+i7drxc@icloud.com|https://icloud-cf-mail-v2.n5pskgzs9g.workers.dev/readmail/DXGt1ZRPf3quuMToOH3UbDpzigebAZqK/data",
    "blog.pod_36+j0uw70g@icloud.com|https://icloud-cf-mail-v2.n5pskgzs9g.workers.dev/readmail/dOGBlSw7sAWrSgIcFKhE92FB7v3944D3/data",
]

REG_MODE = "hybrid"
MAIL_MODE = "icloud_v3"

OUT_DIR = ROOT / "runtime" / "live_hybrid_regdata"

# Recheck endpoints
_CHATGPT_BASE = "https://chatgpt.com"
_SESSION_URL = f"{_CHATGPT_BASE}/api/auth/session"
_ME_URL = f"{_CHATGPT_BASE}/backend-api/me"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _make_logger(prefix: str):
    def _log(msg: str) -> None:
        print(f"[{_ts()}][{prefix}] {msg}", flush=True)
    return _log


def _recheck_delay_seconds() -> float:
    raw = os.environ.get("HYBRID_RECHECK_DELAY", "60").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 60.0


def _recheck_enabled() -> bool:
    raw = os.environ.get("HYBRID_RECHECK", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


# ─── Build request từ mail_modes spec (mẫu chuẩn) + ÉP reg_mode=hybrid ──
def _build_request(line: str, *, password: str | None, headless: bool, proxy: str | None):
    from web.mail_modes import get_spec

    spec = get_spec(MAIL_MODE)
    parsed = spec.parse_line(line)
    request = spec.build_request(
        parsed,
        password=password,
        headless=headless,
        proxy=proxy,
        reg_mode=REG_MODE,  # spec hỗ trợ truyền reg_mode trực tiếp
    )
    # ÉP cứng lại lần nữa (đảm bảo dù spec đổi default) — đây là điểm khác smoke.
    if request.reg_mode != REG_MODE:
        request = request.model_copy(update={"reg_mode": REG_MODE})
    return request


# ─── POST-REG DEACTIVATION RECHECK ───────────────────────────────────
def _recheck_sync(*, request, result, log) -> dict:
    """GET /api/auth/session (cookies) + /backend-api/me (Bearer) để phân loại.

    Trả dict: {status, session_http, me_http, has_user, reason}.
    status ∈ {ACTIVE, DEACTIVATED, UNKNOWN, recheck_skipped}.
    """
    from curl_cffi import requests as curl_requests
    from user_agent_profile import (
        SEC_CH_UA,
        SEC_CH_UA_MOBILE,
        SEC_CH_UA_PLATFORM,
    )

    session_token = result.session_token
    access_token = result.access_token
    cookies = result.cookies or []

    if not session_token and not access_token and not cookies:
        return {
            "status": "recheck_skipped",
            "reason": "không có session_token/access_token/cookies để recheck",
            "session_http": None,
            "me_http": None,
            "has_user": False,
        }

    session = curl_requests.Session(impersonate=request.impersonate)
    if request.proxy:
        session.proxies = {"http": request.proxy, "https": request.proxy}

    base_headers = {
        "User-Agent": request.user_agent,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"{_CHATGPT_BASE}/",
        "sec-ch-ua": SEC_CH_UA,
        "sec-ch-ua-mobile": SEC_CH_UA_MOBILE,
        "sec-ch-ua-platform": SEC_CH_UA_PLATFORM,
    }

    try:
        # Inject cookies chatgpt.com (gồm __Secure-next-auth.session-token nếu có)
        for c in cookies:
            name = c.get("name")
            value = c.get("value")
            if not name or value is None:
                continue
            domain = (c.get("domain") or "chatgpt.com").lstrip(".")
            session.cookies.set(name, value, domain=domain, path=c.get("path") or "/")
        # Bảo đảm session-token có mặt (nếu result.cookies không kèm)
        has_session_cookie = any(
            c.get("name") == "__Secure-next-auth.session-token" for c in cookies
        )
        if session_token and not has_session_cookie:
            session.cookies.set(
                "__Secure-next-auth.session-token", session_token,
                domain="chatgpt.com", path="/",
            )

        # (1) /api/auth/session — dựa trên cookies
        session_http: int | None = None
        has_user = False
        try:
            r = session.get(_SESSION_URL, headers=base_headers, timeout=30)
            session_http = r.status_code
            if session_http == 200:
                try:
                    data = r.json()
                except Exception:
                    data = {}
                user = (data.get("user") or {}) if isinstance(data, dict) else {}
                has_user = bool(data.get("accessToken")) and bool(user.get("id"))
        except Exception as exc:  # noqa: BLE001
            log(f"[recheck] /api/auth/session error: {type(exc).__name__}: {exc}")

        # (2) /backend-api/me — dựa trên Bearer access_token (nếu có)
        me_http: int | None = None
        if access_token:
            me_headers = {
                **base_headers,
                "Authorization": f"Bearer {access_token}",
            }
            try:
                rm = session.get(_ME_URL, headers=me_headers, timeout=30)
                me_http = rm.status_code
            except Exception as exc:  # noqa: BLE001
                log(f"[recheck] /backend-api/me error: {type(exc).__name__}: {exc}")

        # ── Phân loại ──
        deactivated_signal = (
            session_http in (401, 403)
            or me_http in (401, 403)
            or (session_http == 200 and not has_user)
        )
        active_signal = (
            (session_http == 200 and has_user)
            or me_http == 200
        )

        if deactivated_signal and not (me_http == 200):
            status = "DEACTIVATED"
            reason = f"session_http={session_http} me_http={me_http} has_user={has_user}"
        elif active_signal:
            status = "ACTIVE"
            reason = f"session_http={session_http} me_http={me_http} has_user={has_user}"
        else:
            status = "UNKNOWN"
            reason = f"session_http={session_http} me_http={me_http} has_user={has_user}"

        return {
            "status": status,
            "reason": reason,
            "session_http": session_http,
            "me_http": me_http,
            "has_user": has_user,
        }
    finally:
        try:
            session.close()
        except Exception:
            pass


async def _recheck(*, request, result, log) -> dict:
    return await asyncio.to_thread(_recheck_sync, request=request, result=result, log=log)


# ─── Chạy 1 account ──────────────────────────────────────────────────
async def _run_one(
    line: str, idx: int, total: int, *,
    password: str | None, headless: bool, proxy: str | None, job_timeout: float,
) -> dict:
    from models import SignupResult
    from signup import run_signup

    email_preview = line.split("|", 1)[0]
    prefix = f"{idx}/{total} {email_preview[:28]}"
    log = _make_logger(prefix)

    request = _build_request(line, password=password, headless=headless, proxy=proxy)
    log(
        f"START email={request.email} provider={request.mail_provider} "
        f"reg_mode={request.reg_mode} url_set={bool(request.icloud_v3_url)} "
        f"headless={request.headless}"
    )

    row: dict = {
        "email": request.email,
        "reg_mode": request.reg_mode,
        "success": False,
        "error": None,
        "total_seconds": 0.0,
        "phase1_seconds": 0.0,
        "otp_seconds": 0.0,
        "phase2_seconds": 0.0,
        "session_token_len": 0,
        "access_token_len": 0,
        "cookies_count": 0,
        "recheck": {"status": "not_run", "reason": "reg chưa success"},
    }

    t0 = time.monotonic()
    try:
        result: SignupResult = await asyncio.wait_for(
            run_signup(request, log=log),
            timeout=max(job_timeout, request.otp_timeout_seconds + 120.0),
        )
    except asyncio.TimeoutError:
        row["error"] = "TimeoutError"
        row["total_seconds"] = round(time.monotonic() - t0, 2)
        log(f"TIMEOUT after {row['total_seconds']}s")
        _save_json(idx, request.email, {"row": row})
        return row
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["total_seconds"] = round(time.monotonic() - t0, 2)
        log(f"FATAL: {row['error']}")
        _save_json(idx, request.email, {"row": row})
        return row

    dt = time.monotonic() - t0
    row.update(
        success=result.success,
        error=result.error,
        total_seconds=round(dt, 2),
        phase1_seconds=round(result.phase1_seconds or 0.0, 2),
        otp_seconds=round(result.otp_seconds or 0.0, 2),
        phase2_seconds=round(result.phase2_seconds or 0.0, 2),
        session_token_len=len(result.session_token or ""),
        access_token_len=len(result.access_token or ""),
        cookies_count=len(result.cookies or []),
        user_id=result.user_id,
        account_id=result.account_id,
    )
    log(
        f"END success={result.success} total={dt:.1f}s "
        f"session_token={'<set>' if result.session_token else None} "
        f"access_token={'<set>' if result.access_token else None} "
        f"error={result.error or '<none>'}"
    )

    # ── POST-REG DEACTIVATION RECHECK ──
    if not result.success:
        row["recheck"] = {"status": "not_run", "reason": "reg không success"}
    elif not _recheck_enabled():
        row["recheck"] = {"status": "recheck_skipped", "reason": "HYBRID_RECHECK tắt"}
    else:
        delay = _recheck_delay_seconds()
        log(f"[recheck] đợi {delay:.0f}s trước khi recheck deactivation...")
        if delay > 0:
            await asyncio.sleep(delay)
        recheck = await _recheck(request=request, result=result, log=log)
        row["recheck"] = recheck
        log(f"[recheck] status={recheck['status']} ({recheck['reason']})")

    # Lưu JSON đầy đủ result + row
    payload = result.model_dump()
    payload["__row"] = row
    _save_json(idx, request.email, payload)
    return row


def _save_json(idx: int, email: str, payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe = email.replace("@", "_at_").replace("+", "_plus_")
    (OUT_DIR / f"{idx:02d}_{safe}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


# ─── Load settings + proxy (mẫu chuẩn production) ────────────────────
def _load_settings() -> dict:
    from db import get_engine, get_settings_repo
    from db.repositories import RepositoryError

    try:
        repo = get_settings_repo(get_engine())
        return repo.list()
    except RepositoryError as exc:
        print(f"[settings] load fail: {exc} → dùng default", flush=True)
        return {}


async def _resolve_proxy(log) -> str | None:
    try:
        from web.manager import _resolve_job_proxy
        proxy, _proxy_line = await _resolve_job_proxy()
        log(f"[proxy] resolved={'<set>' if proxy else 'DIRECT (pool rỗng)'}")
        return proxy
    except Exception as exc:  # noqa: BLE001
        log(f"[proxy] resolve fail: {type(exc).__name__}: {exc} → DIRECT")
        return None


# ─── DRY-RUN: parse + build 5 request, KHÔNG signup, KHÔNG network ────
def _dry_run() -> int:
    log = _make_logger("dry-run")
    log(f"=== DRY-RUN: build {len(LINES)} request (KHÔNG signup, KHÔNG network) ===")

    # Settings (local SQLite — offline) cho password/headless; proxy=None.
    all_settings = _load_settings()
    headless = bool(all_settings.get("reg.headless", True))
    password = all_settings.get("reg.default_password") or "Autogen#2026Xy"
    log(f"[cfg] headless={headless} password={'<set>' if password else '<auto>'} proxy=None(dry)")

    ok = 0
    for i, line in enumerate(LINES):
        try:
            request = _build_request(line, password=password, headless=headless, proxy=None)
        except Exception as exc:  # noqa: BLE001
            log(f"[{i}] BUILD FAIL: {type(exc).__name__}: {exc}")
            continue
        url_ok = bool(request.icloud_v3_url)
        mode_ok = request.reg_mode == REG_MODE
        if url_ok and mode_ok:
            ok += 1
        log(
            f"[{i}] email={request.email} reg_mode={request.reg_mode} "
            f"provider={request.mail_provider} "
            f"icloud_v3_url={'SET' if url_ok else 'MISSING'} "
            f"otp_timeout={request.otp_timeout_seconds}s "
            f"→ {'OK' if (url_ok and mode_ok) else 'FAIL'}"
        )

    log(f"=== DRY-RUN result: {ok}/{len(LINES)} request build OK (reg_mode={REG_MODE}, url set) ===")
    log("LƯU Ý: dry-run KHÔNG gọi run_signup, KHÔNG gọi network signup, KHÔNG recheck.")
    return 0 if ok == len(LINES) else 1


# ─── Chạy thật ───────────────────────────────────────────────────────
async def _live_run() -> int:
    log = _make_logger("main")
    log(f"=== LIVE reg hybrid — {len(LINES)} account (TUẦN TỰ) ===")

    all_settings = _load_settings()
    headless = bool(all_settings.get("reg.headless", True))
    job_timeout = float(all_settings.get("reg.job_timeout", 360))
    password = all_settings.get("reg.default_password") or "Autogen#2026Xy"
    log(
        f"[cfg] headless={headless} job_timeout={job_timeout}s reg_mode={REG_MODE} "
        f"recheck={'on' if _recheck_enabled() else 'off'} "
        f"recheck_delay={_recheck_delay_seconds():.0f}s "
        f"password={'<set>' if password else '<auto>'}"
    )

    proxy = await _resolve_proxy(log)

    summary: list[dict] = []
    grand_start = time.monotonic()
    for idx, line in enumerate(LINES, 1):
        bar = "─" * 78
        print(f"\n{bar}\n[{idx}/{len(LINES)}] {line.split('|', 1)[0]}\n{bar}", flush=True)
        row = await _run_one(
            line, idx, len(LINES),
            password=password, headless=headless, proxy=proxy, job_timeout=job_timeout,
        )
        summary.append(row)
    grand_total = time.monotonic() - grand_start

    # Cleanup pool nếu hybrid runner có
    try:
        from reg_hybrid.runner import wait_pending_cleanups
        from reg_hybrid.browser_pool import get_pool
        await wait_pending_cleanups(timeout=10.0)
        get_pool().shutdown_all()
    except Exception as exc:  # noqa: BLE001
        log(f"[cleanup] skip: {type(exc).__name__}: {exc}")

    # ── Summary ──
    print(f"\n{'═' * 78}", flush=True)
    print(f"SUMMARY ({len(LINES)} account, grand total {grand_total:.1f}s)", flush=True)
    print("═" * 78, flush=True)
    print(f"{'#':<3}{'email':<40}{'reg':<4}{'success':<9}{'recheck':<14}{'total':>9}", flush=True)
    print("─" * 78, flush=True)
    n_success = n_active = n_deact = 0
    for i, r in enumerate(summary, 1):
        ok = "✓" if r["success"] else "✗"
        if r["success"]:
            n_success += 1
        rc = (r.get("recheck") or {}).get("status", "?")
        if rc == "ACTIVE":
            n_active += 1
        elif rc == "DEACTIVATED":
            n_deact += 1
        em = r["email"][:38] + ".." if len(r["email"]) > 40 else r["email"]
        print(
            f"{i:<3}{em:<40}{'hyb':<4}{ok:<9}{rc:<14}{r['total_seconds']:>9.1f}",
            flush=True,
        )
        if not r["success"] and r.get("error"):
            print(f"     └─ error: {r['error']}", flush=True)
        elif (r.get("recheck") or {}).get("reason"):
            print(f"     └─ recheck: {r['recheck']['reason']}", flush=True)
    print("─" * 78, flush=True)
    print(
        f"Success: {n_success}/{len(LINES)} | "
        f"ACTIVE: {n_active} | DEACTIVATED: {n_deact} | "
        f"other: {len(LINES) - n_active - n_deact}",
        flush=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(
        json.dumps({
            "reg_mode": REG_MODE,
            "grand_total_seconds": round(grand_total, 2),
            "success_count": n_success,
            "active_count": n_active,
            "deactivated_count": n_deact,
            "recheck_delay_seconds": _recheck_delay_seconds(),
            "rows": summary,
        }, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # Pass khi tất cả success VÀ không account nào bị deactivated.
    return 0 if (n_success == len(LINES) and n_deact == 0) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Live test reg hybrid + deactivation recheck")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Chỉ parse + build 5 request (KHÔNG signup, KHÔNG network).",
    )
    args = parser.parse_args()

    if args.dry_run:
        return _dry_run()
    return asyncio.run(_live_run())


if __name__ == "__main__":
    sys.exit(main())
