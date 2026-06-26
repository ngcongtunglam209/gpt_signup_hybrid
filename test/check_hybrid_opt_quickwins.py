"""Smoke test 3 quick-win optimization cho hybrid mode.

Test cases:
    [1/5] HybridBrowserPool.warm_up + _get_or_create_runner tồn tại, idempotent.
    [2/5] warm_up gọi runner._ensure_browser_in_thread qua dedicated thread.
    [3/5] WorkerMailProvider OTP adaptive backoff: 1s/2s/3s rồi poll_interval.
    [4/5] runner._fire_and_forget_cleanup spawn task, không block caller.
    [5/5] wait_pending_cleanups đợi xong tất cả task.

Chạy:
    .venv/bin/python test/check_hybrid_opt_quickwins.py
"""
from __future__ import annotations

import asyncio
import inspect
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _check(name: str, fn) -> bool:
    try:
        fn()
        print(f"[PASS] {name}", flush=True)
        return True
    except AssertionError as exc:
        print(f"[FAIL] {name} — {exc}", flush=True)
        return False
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print(f"[FAIL] {name} — {type(exc).__name__}: {exc}", flush=True)
        return False


def tc1_pool_warm_up_methods() -> bool:
    from reg_hybrid.browser_pool import HybridBrowserPool

    def _shape() -> None:
        pool = HybridBrowserPool()
        for m in ("warm_up", "_get_or_create_runner", "acquire", "shutdown_all"):
            assert hasattr(pool, m), f"HybridBrowserPool thiếu method {m}"
        sig = inspect.signature(pool.warm_up)
        params = set(sig.parameters.keys())
        assert {"proxy", "headless", "insecure", "log"}.issubset(params), (
            f"warm_up signature sai: {params}"
        )

    return _check("[1/5] HybridBrowserPool có warm_up + helpers", _shape)


def tc2_warm_up_calls_ensure_browser() -> bool:
    """warm_up phải route qua dedicated thread + gọi _ensure_browser_in_thread."""
    from reg_hybrid.browser_pool import HybridBrowserPool, _CamoufoxRunner

    captured = {"tid": None, "main_tid": None, "called": False}

    def _stub_ensure(self) -> None:
        captured["tid"] = threading.get_ident()
        captured["called"] = True

    def _run() -> None:
        captured["main_tid"] = threading.get_ident()
        pool = HybridBrowserPool()
        with patch.object(_CamoufoxRunner, "_ensure_browser_in_thread", _stub_ensure):
            pool.warm_up(
                proxy=None, headless=True, insecure=False,
                log=lambda _m: None,
            )
        # Shutdown các runner đã tạo (close executor).
        pool.shutdown_all()
        assert captured["called"], "warm_up không gọi _ensure_browser_in_thread"
        assert captured["tid"] != captured["main_tid"], (
            f"warm_up không route qua dedicated thread "
            f"(main={captured['main_tid']} ensure={captured['tid']})"
        )

    return _check("[2/5] warm_up route _ensure_browser_in_thread qua dedicated thread", _run)


def tc3_otp_adaptive_backoff() -> bool:
    """WorkerMailProvider phải sleep 1s, 2s, 3s, rồi poll_interval cố định."""
    from mail_providers import WorkerMailProvider

    sleeps: list[float] = []

    class _AbortLoop(Exception):
        pass

    async def _stub_sleep(t: float) -> None:
        sleeps.append(t)
        # Sau 5 vòng đủ data → abort để test thoát loop.
        if len(sleeps) >= 5:
            raise _AbortLoop()

    class _FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"messages": []}

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def get(self, url, headers=None):
            return _FakeResponse()

    async def _run() -> None:
        provider = WorkerMailProvider(
            logs_url="http://test", api_key="k", insecure_tls=False,
        )
        with patch("mail_providers.httpx.AsyncClient", lambda **kw: _FakeClient()), \
             patch("mail_providers.asyncio.sleep", _stub_sleep):
            from datetime import datetime, timezone
            try:
                await provider.poll_otp(
                    recipient="test@example.com",
                    started_at=datetime.now(timezone.utc),
                    timeout_seconds=600.0,
                    poll_interval_seconds=4.0,
                    log=lambda _m: None,
                )
            except (TimeoutError, _AbortLoop):
                pass  # Expected

        assert len(sleeps) >= 4, f"Số sleep call quá ít: {sleeps}"
        assert abs(sleeps[0] - 1.0) < 0.1, f"Sleep #1 phải 1s, got {sleeps[0]}"
        assert abs(sleeps[1] - 2.0) < 0.1, f"Sleep #2 phải 2s, got {sleeps[1]}"
        assert abs(sleeps[2] - 3.0) < 0.1, f"Sleep #3 phải 3s, got {sleeps[2]}"
        assert abs(sleeps[3] - 4.0) < 0.1, f"Sleep #4 phải 4s (poll_interval), got {sleeps[3]}"

    def _go() -> None:
        asyncio.run(_run())

    return _check("[3/5] OTP adaptive backoff 1s→2s→3s→poll_interval", _go)


def tc4_fire_and_forget_cleanup() -> bool:
    """_fire_and_forget_cleanup spawn task, không block caller."""
    from reg_hybrid.runner import (
        _BACKGROUND_CLEANUP_TASKS,
        _fire_and_forget_cleanup,
    )

    captured = {"called_tid": None, "main_tid": None}

    def _stub_cleanup(session, tokens, log) -> None:
        captured["called_tid"] = threading.get_ident()
        time.sleep(0.05)  # mô phỏng I/O blocking

    async def _run() -> None:
        captured["main_tid"] = threading.get_ident()
        with patch("reg_hybrid.runner._cleanup", _stub_cleanup):
            t0 = time.monotonic()
            _fire_and_forget_cleanup(
                session=object(), tokens=object(),
                log=lambda _m: None, name="test-cleanup",
            )
            elapsed = time.monotonic() - t0
            # Phải return ngay (< 50ms cleanup), không block.
            assert elapsed < 0.020, (
                f"_fire_and_forget_cleanup BLOCK caller {elapsed*1000:.1f}ms — "
                f"phải return ngay (task chạy nền)"
            )
            # Task đã add vào set tracking.
            assert len(_BACKGROUND_CLEANUP_TASKS) >= 1, (
                f"Task chưa add vào _BACKGROUND_CLEANUP_TASKS: "
                f"{len(_BACKGROUND_CLEANUP_TASKS)}"
            )
            # Đợi cleanup xong.
            await asyncio.sleep(0.15)
            assert captured["called_tid"] is not None, "cleanup chưa được gọi"
            assert captured["called_tid"] != captured["main_tid"], (
                "cleanup chạy ở main thread thay vì worker thread"
            )

    def _go() -> None:
        asyncio.run(_run())

    return _check("[4/5] _fire_and_forget_cleanup non-blocking + chạy off main", _go)


def tc5_wait_pending_cleanups() -> bool:
    """wait_pending_cleanups đợi tất cả background task xong."""
    from reg_hybrid.runner import (
        _BACKGROUND_CLEANUP_TASKS,
        _fire_and_forget_cleanup,
        wait_pending_cleanups,
    )

    counter = {"n": 0}

    def _slow_cleanup(session, tokens, log) -> None:
        time.sleep(0.05)
        counter["n"] += 1

    async def _run() -> None:
        with patch("reg_hybrid.runner._cleanup", _slow_cleanup):
            # Spawn 3 task song song.
            for i in range(3):
                _fire_and_forget_cleanup(
                    session=object(), tokens=object(),
                    log=lambda _m: None, name=f"test-{i}",
                )
            assert len(_BACKGROUND_CLEANUP_TASKS) == 3, (
                f"Số task không đúng: {len(_BACKGROUND_CLEANUP_TASKS)}"
            )
            t0 = time.monotonic()
            await wait_pending_cleanups(timeout=2.0)
            elapsed = time.monotonic() - t0
            assert counter["n"] == 3, (
                f"Chỉ {counter['n']}/3 cleanup chạy xong sau wait"
            )
            assert elapsed >= 0.04, (
                f"wait_pending_cleanups return quá nhanh ({elapsed:.3f}s) — "
                f"có vẻ không thực sự đợi"
            )

    def _go() -> None:
        asyncio.run(_run())

    return _check("[5/5] wait_pending_cleanups đợi xong tất cả task", _go)


def main() -> int:
    results = [
        tc1_pool_warm_up_methods(),
        tc2_warm_up_calls_ensure_browser(),
        tc3_otp_adaptive_backoff(),
        tc4_fire_and_forget_cleanup(),
        tc5_wait_pending_cleanups(),
    ]
    passed = sum(results)
    total = len(results)
    print(flush=True)
    if passed == total:
        print(f"=== HYBRID OPT QUICKWINS PASSED ({passed}/{total}) ===", flush=True)
        return 0
    print(f"=== HYBRID OPT QUICKWINS FAILED ({passed}/{total}) ===", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
