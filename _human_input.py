"""Human-like input helpers cho browser_phase + session_phase.

Anti-ban (journal 260625-1224 Task 2.2 + bug B2 + C1):
    Sentinel SDK của OpenAI build so-token (Session Observer) bằng cách
    track DOM events:
        - keydown / keyup timings + variance + pause
        - input event sequence (focus → type → blur)
        - mousemove paths trước click
        - pointerdown / pointerup pattern
        - scroll, resize, hover events nhẹ

    Code cũ dùng ``loc.type(text, delay=80)`` cố định 80ms, KHÔNG jitter,
    KHÔNG pause, KHÔNG mouse movement → so-token nghèo nàn → server flag.

    Module này cung cấp helper mô phỏng người dùng thật:
    - ``human_type``  — gõ với delay Gaussian + occasional pause
    - ``human_click`` — mousemove tới element rồi click
    - ``random_mouse_wander`` — di chuột vài lần ngẫu nhiên
    - ``dwell``       — async sleep với jitter

Caller pattern:
    ```python
    from _human_input import human_type, human_click, dwell

    await dwell(0.8, 1.5)  # đọc trang
    await human_type(page.locator('input[name="password"]'), pw,
                     delay_min_ms=120, delay_max_ms=260)
    await dwell(0.3, 0.8)  # tab/move
    await human_click(page, 'button[type="submit"]')
    ```
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Defaults — đồng bộ với Settings Store ``reg.human_typing_delay_ms_min/max``
# ─────────────────────────────────────────────────────────────────────

DEFAULT_DELAY_MIN_MS = 120
DEFAULT_DELAY_MAX_MS = 260
DEFAULT_PAUSE_PROBABILITY = 0.08  # 8% ký tự sẽ pause 0.2-0.5s sau khi gõ
DEFAULT_PAUSE_MIN_S = 0.2
DEFAULT_PAUSE_MAX_S = 0.5


# ─────────────────────────────────────────────────────────────────────
# Internal — Gaussian delay sampling
# ─────────────────────────────────────────────────────────────────────


def _sample_delay_ms(min_ms: int, max_ms: int) -> int:
    """Sample delay theo phân phối Gaussian, clamp vào [min_ms, max_ms].

    Mean = (min+max)/2, stddev = (max-min)/4 → 95% sample nằm trong khoảng.
    Người thật gõ phím có distribution Gaussian (Fitts's law variant) — biến
    cố định 80ms → bot signature rõ rệt.
    """
    if max_ms <= min_ms:
        return max(1, int(min_ms))
    mean = (min_ms + max_ms) / 2
    stddev = max(1.0, (max_ms - min_ms) / 4)
    raw = random.gauss(mean, stddev)
    return max(min_ms, min(max_ms, int(raw)))


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────


async def dwell(min_s: float = 0.5, max_s: float = 1.5) -> None:
    """Async sleep với jitter uniform [min_s, max_s].

    Dùng giữa các state transition để page settle + sentinel SDK observe
    'idle reading time'. Tránh bot pattern click-click liên tục.
    """
    delay = random.uniform(max(0.0, min_s), max(min_s, max_s))
    await asyncio.sleep(delay)


async def human_type(
    locator: Any,
    text: str,
    *,
    delay_min_ms: int = DEFAULT_DELAY_MIN_MS,
    delay_max_ms: int = DEFAULT_DELAY_MAX_MS,
    pause_probability: float = DEFAULT_PAUSE_PROBABILITY,
    pause_min_s: float = DEFAULT_PAUSE_MIN_S,
    pause_max_s: float = DEFAULT_PAUSE_MAX_S,
    clear_before: bool = True,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """Gõ ``text`` vào ``locator`` mô phỏng người dùng thật.

    Strategy:
        1. Click locator (force=True để focus dù bị overlay ẩn).
        2. Clear value cũ (fill("")) — nếu ``clear_before=True``.
        3. Loop từng ký tự:
           a. Sample delay Gaussian [delay_min_ms, delay_max_ms].
           b. ``locator.type(ch, delay=delay_ms)``.
           c. Với xác suất ``pause_probability``, sleep [pause_min_s, pause_max_s]
              (mô phỏng "đọc/think").

    Sentinel SDK quan sát ``input``/``keydown`` events sẽ thấy variance
    realistic + occasional long pause = human-like distribution.

    Args:
        locator: Playwright/Camoufox locator (page.locator('input[...]').first).
        text: chuỗi cần gõ.
        delay_min_ms / delay_max_ms: dải delay per-key (mặc định 120-260).
        pause_probability: xác suất pause sau mỗi ký tự (mặc định 8%).
        pause_min_s / pause_max_s: khoảng pause (giây).
        clear_before: True = fill("") trước khi gõ.
        log: optional callable để log progress.
    """
    _log = log or (lambda m: logger.debug(m))

    try:
        await locator.click(force=True, timeout=3000)
    except Exception as exc:  # noqa: BLE001 — best-effort
        _log(f"[human_type] click before type failed (continue): {exc}")

    if clear_before:
        try:
            await locator.fill("")
        except Exception as exc:  # noqa: BLE001
            _log(f"[human_type] fill('') before type failed (continue): {exc}")

    # Small pre-type pause — người thật click rồi suy nghĩ ~100ms
    await asyncio.sleep(random.uniform(0.05, 0.20))

    for idx, ch in enumerate(text):
        delay_ms = _sample_delay_ms(delay_min_ms, delay_max_ms)
        try:
            await locator.type(ch, delay=delay_ms)
        except Exception as exc:  # noqa: BLE001
            _log(f"[human_type] type idx={idx} char={ch!r} failed: {exc}")
            raise
        # Occasional human pause (think/look at screen)
        if random.random() < pause_probability:
            await asyncio.sleep(random.uniform(pause_min_s, pause_max_s))

    # Post-type settle
    await asyncio.sleep(random.uniform(0.1, 0.3))


async def human_click(
    page: Any,
    target: Any,
    *,
    move_steps_min: int = 10,
    move_steps_max: int = 22,
    pre_click_jitter_s: float = 0.15,
    timeout_ms: int = 3000,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """Click ``target`` mô phỏng cursor di chuyển tới rồi click.

    Strategy:
        1. Lấy bounding box của target.
        2. Pick điểm random trong box (không center cứng — center → bot signature).
        3. ``page.mouse.move(x, y, steps=random)`` để generate mousemove events.
        4. Pause ngắn ``pre_click_jitter_s`` (con người không click ngay khi cursor đến).
        5. Click với delay nhỏ (Playwright sẽ tự gen mousedown/up).

    Args:
        page: Playwright Page instance.
        target: selector string HOẶC Locator object.
        move_steps_min / move_steps_max: số bước mousemove (sentinel xem path).
        pre_click_jitter_s: pause trước khi click (jitter ±50%).
        timeout_ms: timeout cho bounding_box + click.
    """
    _log = log or (lambda m: logger.debug(m))

    if isinstance(target, str):
        locator = page.locator(target).first
    else:
        locator = target  # đã là locator

    # 1. Bounding box
    box = None
    try:
        box = await locator.bounding_box(timeout=timeout_ms)
    except Exception as exc:  # noqa: BLE001
        _log(f"[human_click] bounding_box failed: {exc}")

    if box and box.get("width", 0) > 0 and box.get("height", 0) > 0:
        # 2. Pick random point trong box (margin 30-70% để tránh edge)
        x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
        # 3. Move with random steps
        steps = random.randint(move_steps_min, move_steps_max)
        try:
            await page.mouse.move(x, y, steps=steps)
        except Exception as exc:  # noqa: BLE001
            _log(f"[human_click] mouse.move failed (fallback to direct click): {exc}")
        # 4. Pre-click jitter (±50% deviation)
        jitter = pre_click_jitter_s * random.uniform(0.5, 1.5)
        await asyncio.sleep(jitter)

    # 5. Click — Playwright tự gen mousedown/mouseup với short delay.
    await locator.click(timeout=timeout_ms, delay=random.randint(40, 120))


async def random_mouse_wander(
    page: Any,
    *,
    count: int = 3,
    settle_min_s: float = 0.1,
    settle_max_s: float = 0.6,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """Di chuột ``count`` lần tới điểm random trong viewport.

    Sentinel observer record mousemove events → cho thấy "có cursor activity"
    giữa các action. Người thật KHÔNG ngồi yên — cursor luôn drift nhẹ.

    Best-effort: không raise nếu page chết hay viewport không lấy được.
    """
    _log = log or (lambda m: logger.debug(m))

    try:
        vw, vh = await page.evaluate("() => [window.innerWidth, window.innerHeight]")
        vw = int(vw or 1280)
        vh = int(vh or 720)
    except Exception as exc:  # noqa: BLE001
        _log(f"[mouse_wander] viewport probe failed (skip): {exc}")
        return

    for _ in range(max(0, count)):
        x = random.randint(int(vw * 0.1), int(vw * 0.9))
        y = random.randint(int(vh * 0.1), int(vh * 0.9))
        steps = random.randint(8, 20)
        try:
            await page.mouse.move(x, y, steps=steps)
        except Exception as exc:  # noqa: BLE001
            _log(f"[mouse_wander] move failed (skip remaining): {exc}")
            return
        await asyncio.sleep(random.uniform(settle_min_s, settle_max_s))


__all__ = [
    "human_type",
    "human_click",
    "random_mouse_wander",
    "dwell",
    "DEFAULT_DELAY_MIN_MS",
    "DEFAULT_DELAY_MAX_MS",
]
