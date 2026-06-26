"""Verify Observer feeder + mint_so retry + classify retry-able.

Test cases:
    [1/5] _OBSERVER_FEEDER_JS có setInterval + mouse/scroll/focus/click events.
    [2/5] _OBSERVER_BURST_JS fire >= 20 mouse events trong 1 burst.
    [3/5] _acquire_context_in_thread inject feeder script + wait 1.5s.
    [4/5] _mint_so_in_thread retry với burst khi empty (attempt 1 → 2).
    [5/5] _classify_error trả "sentinel_observer" cho SO empty exception.

Chạy:
    .venv/bin/python test/check_hybrid_so_observer.py
"""
from __future__ import annotations

import sys
from pathlib import Path

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


def tc1_feeder_shape() -> bool:
    from reg_hybrid import browser_pool

    js = browser_pool._OBSERVER_FEEDER_JS
    assert "setInterval" in js, "feeder thiếu setInterval"
    for token in ("mousemove", "scroll", "focus", "click", "visibilitychange"):
        assert token in js, f"feeder thiếu event {token}"
    assert "dispatchEvent" in js, "feeder không dispatch synthetic events"
    assert "__hybrid_feeder_active" in js, "feeder thiếu idempotent guard"
    return True


def tc2_burst_shape() -> bool:
    from reg_hybrid import browser_pool

    js = browser_pool._OBSERVER_BURST_JS
    assert "for" in js and "mousemove" in js, "burst thiếu loop mousemove"
    assert "click" in js and "scroll" in js, "burst thiếu click/scroll"
    # Đếm số iteration mousemove trong burst (loop 25 lần theo design).
    assert "i < 25" in js or "i<25" in js, (
        "burst phải fire >= 25 mousemove events"
    )
    return True


def tc3_acquire_inject_feeder() -> bool:
    """_acquire_context_in_thread phải inject feeder + wait 1.5s."""
    src = (ROOT / "reg_hybrid" / "browser_pool.py").read_text(encoding="utf-8")
    # Tìm trong method _acquire_context_in_thread (sau bridge ready).
    method_start = src.find("def _acquire_context_in_thread")
    method_end = src.find("def _release_context_in_thread", method_start)
    body = src[method_start:method_end]
    assert "_OBSERVER_FEEDER_JS" in body, (
        "_acquire_context_in_thread không inject _OBSERVER_FEEDER_JS"
    )
    assert "wait_for_timeout(1500)" in body, (
        "_acquire_context_in_thread không wait 1.5s cho feeder collect events"
    )
    return True


def tc4_mint_so_retry() -> bool:
    """_mint_so_in_thread phải retry với burst khi empty."""
    src = (ROOT / "reg_hybrid" / "browser_pool.py").read_text(encoding="utf-8")
    start = src.find("def _mint_so_in_thread")
    end = src.find("def ", start + 30)
    body = src[start:end]
    assert "_OBSERVER_BURST_JS" in body, (
        "_mint_so_in_thread thiếu burst events retry"
    )
    assert "for attempt in" in body or "attempt == 1" in body, (
        "_mint_so_in_thread thiếu logic retry attempt 1 → 2"
    )
    assert "sau retry" in body or "retry" in body, (
        "_mint_so_in_thread thiếu message log retry"
    )
    return True


def tc5_classify_sentinel_observer() -> bool:
    from reg_hybrid.runner import _classify_error

    class _FakeExc(Exception):
        pass

    # Exception message từ HybridContextHandle._mint_so_in_thread khi empty.
    cat = _classify_error(_FakeExc(
        "sessionObserverToken() returned nothing sau retry với burst events "
        "— Observer cache empty"
    ))
    assert cat == "sentinel_observer", (
        f"SO empty phải classify 'sentinel_observer', got {cat!r}"
    )
    # page.evaluate transport error cũng retry-able.
    cat2 = _classify_error(_FakeExc("page.evaluate failed: Connection closed"))
    assert cat2 == "sentinel_observer", (
        f"page.evaluate fail phải classify 'sentinel_observer', got {cat2!r}"
    )
    # Terminal vẫn ok (no false positive).
    cat3 = _classify_error(_FakeExc("OutlookComboError: combo dead"))
    assert cat3 == "terminal", f"combo dead phải terminal, got {cat3!r}"
    return True


def main() -> int:
    results = [
        _check("[1/5] _OBSERVER_FEEDER_JS có events liên tục", tc1_feeder_shape),
        _check("[2/5] _OBSERVER_BURST_JS fire >= 25 mousemove", tc2_burst_shape),
        _check("[3/5] _acquire_context_in_thread inject feeder + wait 1.5s",
               tc3_acquire_inject_feeder),
        _check("[4/5] _mint_so_in_thread retry với burst khi empty",
               tc4_mint_so_retry),
        _check("[5/5] _classify_error trả 'sentinel_observer' cho SO empty",
               tc5_classify_sentinel_observer),
    ]
    passed = sum(results)
    total = len(results)
    print(flush=True)
    if passed == total:
        print(f"=== HYBRID SO OBSERVER PASSED ({passed}/{total}) ===", flush=True)
        return 0
    print(f"=== HYBRID SO OBSERVER FAILED ({passed}/{total}) ===", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
