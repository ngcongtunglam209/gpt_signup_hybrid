"""Firefox browser profile (Camoufox is a hardened Firefox).

This profile only carries the facts that are ACTUALLY SENT on the wire or used
to align Camoufox:

  * `user_agent` / `impersonate` -> the Firefox UA string and the curl_cffi TLS
    (JA3/JA4) impersonation target, both keyed off the major version + platform.
  * `language(s)` / `accept_language` / `tz_*` -> locale headers and the
    timezone we set on Camoufox so its geo/Intl matches the account locale.

The sentinel proof-of-work array and all the canvas/WebGL/navigator probes are
NOT built here anymore: the genuine sdk.js mints them live inside Camoufox using
the real browser fingerprint (see camoufox_vm.py). Reproducing them in Python
would only risk drifting from what the browser actually reports.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

# locale -> (tz offset minutes east of UTC, JS localized tz name)
_LOCALE_TZ = {
    "vi": (420, "Giờ Đông Dương"),
    "en-US": (-420, "Pacific Daylight Time"),
    "en-GB": (60, "British Summer Time"),
    "ja": (540, "日本標準時"),
    "zh": (480, "中国标准时间"),
    "ko": (540, "대한민국 표준시"),
    "fr": (120, "heure d’été d’Europe centrale"),
    "de": (120, "Mitteleuropäische Sommerzeit"),
}

# Python `platform` -> Camoufox `os` name.
_CAMOUFOX_OS = {"Windows": "windows", "macOS": "macos", "Linux": "linux"}


def tz_for_locale(locale: str) -> tuple[int, str]:
    primary = locale.split(",")[0]
    base = primary.split("-")[0]
    if primary in _LOCALE_TZ:
        return _LOCALE_TZ[primary]
    if base in _LOCALE_TZ:
        return _LOCALE_TZ[base]
    return (0, "Coordinated Universal Time")


@dataclass(frozen=True)
class FirefoxProfile:
    firefox_major: int = 135
    platform: str = "Windows"           # Windows | macOS | Linux
    accept_language: str = "vi-VN,vi;q=0.5"
    language: str = "vi-VN"
    languages: str = "vi-VN,vi"
    tz_offset_minutes: int = 420
    tz_name: str = "Giờ Đông Dương"

    @property
    def user_agent(self) -> str:
        rv = f"rv:{self.firefox_major}.0"
        if self.platform == "Windows":
            plat = "Windows NT 10.0; Win64; x64"
        elif self.platform == "macOS":
            plat = "Macintosh; Intel Mac OS X 10.15"
        else:
            plat = "X11; Linux x86_64"
        return (f"Mozilla/5.0 ({plat}; {rv}) "
                f"Gecko/20100101 Firefox/{self.firefox_major}.0")

    @property
    def impersonate(self) -> str:
        """curl_cffi impersonation target for the Firefox major version."""
        return f"firefox{self.firefox_major}"

    @property
    def camoufox_os(self) -> str:
        """Lowercase OS name Camoufox expects."""
        return _CAMOUFOX_OS.get(self.platform, "windows")


DEFAULT_PROFILE = FirefoxProfile()


def profile_for_locale(locale: str = "vi-VN", firefox_major: int = 135,
                       platform: str = "Windows",
                       rng: random.Random | None = None) -> FirefoxProfile:
    """Build a locale-consistent Firefox profile. `rng` is accepted for API
    compatibility but no longer perturbs a fingerprint (the browser supplies the
    real screen/hardware values now)."""
    primary = locale.split(",")[0]
    base = primary.split("-")[0]
    tz_off, tz_name = tz_for_locale(locale)
    return FirefoxProfile(
        firefox_major=firefox_major,
        platform=platform,
        accept_language=f"{primary},{base};q=0.5",
        language=primary,
        languages=f"{primary},{base}",
        tz_offset_minutes=tz_off,
        tz_name=tz_name,
    )
