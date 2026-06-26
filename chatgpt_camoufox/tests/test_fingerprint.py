"""Firefox profile: only the facts that are actually SENT (UA / TLS / locale /
tz). The PoW array is no longer built in Python -- the genuine sdk.js mints it
live inside Camoufox -- so the profile carries no screen/PoW-flag fields."""
import random

from chatgpt_camoufox import fingerprint


def test_user_agent_is_firefox_gecko():
    p = fingerprint.DEFAULT_PROFILE
    assert "Firefox/135.0" in p.user_agent
    assert "Gecko/20100101" in p.user_agent
    assert "Chrome" not in p.user_agent


def test_user_agent_tracks_platform():
    win = fingerprint.profile_for_locale("vi-VN", platform="Windows")
    mac = fingerprint.profile_for_locale("vi-VN", platform="macOS")
    lin = fingerprint.profile_for_locale("vi-VN", platform="Linux")
    assert "Windows NT 10.0; Win64; x64" in win.user_agent
    assert "Macintosh; Intel Mac OS X" in mac.user_agent
    assert "X11; Linux x86_64" in lin.user_agent


def test_impersonate_tracks_major():
    p = fingerprint.profile_for_locale("vi-VN", firefox_major=135)
    assert p.impersonate == "firefox135"


def test_profile_for_locale_tz_and_lang():
    p = fingerprint.profile_for_locale("vi-VN")
    assert p.language == "vi-VN"
    assert p.languages == "vi-VN,vi"
    assert p.accept_language == "vi-VN,vi;q=0.5"
    assert p.tz_offset_minutes == 420
    assert p.tz_name == "Giờ Đông Dương"


def test_profile_for_locale_other_locale():
    p = fingerprint.profile_for_locale("ja", firefox_major=135)
    assert p.language == "ja"
    assert p.tz_offset_minutes == 540


def test_tz_for_locale_fallback_is_utc():
    off, name = fingerprint.tz_for_locale("xx-YY")
    assert off == 0
    assert "Universal" in name


def test_camoufox_os_name_maps_from_platform():
    # Camoufox expects lowercase os names; the profile exposes the mapping.
    assert fingerprint.DEFAULT_PROFILE.camoufox_os == "windows"
    assert fingerprint.profile_for_locale("vi-VN", platform="macOS").camoufox_os == "macos"
    assert fingerprint.profile_for_locale("vi-VN", platform="Linux").camoufox_os == "linux"


def test_no_pow_fields_remain():
    # Guard against re-introducing the dead PoW fingerprint surface.
    p = fingerprint.DEFAULT_PROFILE
    for dead in ("feature_flags", "screen_w", "screen_h", "hardware_concurrency",
                 "has_perf_memory", "window_globals"):
        assert not hasattr(p, dead), f"dead PoW field still present: {dead}"
