"""Per-endpoint request headers, mirroring the real Firefox capture.

curl_cffi's `impersonate="firefox<major>"` injects the low-level TLS (JA3/JA4)
and the ordered default headers a Firefox sends (User-Agent, Accept-Encoding,
DNT, etc.). Here we add the request-specific fetch-metadata / accept / referer /
origin that differ per endpoint — taken verbatim from reports/chatgpt-camoufox.

Key Firefox vs Chrome differences encoded here:
  * NO `sec-ch-ua*` client hints (Chromium-only).
  * `te: trailers` on every request.
  * `priority` is `u=4` for XHR and `u=0, i` for navigations (Firefox values).
  * sentinel/req is `content-type: text/plain;charset=UTF-8`, runs inside the
    sentinel iframe (origin/referer = sentinel.openai.com/.../frame.html).
"""
from __future__ import annotations

import secrets

from .fingerprint import FirefoxProfile

CHATGPT = "https://chatgpt.com"
AUTH = "https://auth.openai.com"
SENTINEL = "https://sentinel.openai.com"

_NAV_ACCEPT = ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "*/*;q=0.8")


def datadog_rum() -> dict:
    """Headers the page's Datadog RUM SDK injects on every same-origin XHR to
    auth.openai.com (register / otp validate / create_account in the golden
    capture). The values are per-request random trace ids; the server can't
    verify them, but a real browser running the SDK always emits them, so their
    absence is mildly suspicious. We mirror the exact golden format:

      x-datadog-trace-id   = low 64 bits, decimal
      x-datadog-parent-id  = span id, decimal
      traceparent          = 00-<64 zero bits + trace64 hex>-<span hex>-01
      tracestate           = dd=s:1;o:rum   (sampling priority 1, origin rum)

    The high 64 bits of the W3C trace-id are always zero here (Datadog 64-bit
    trace ids zero-extended into the 128-bit W3C field), exactly as captured.
    """
    trace64 = secrets.randbits(64)
    span64 = secrets.randbits(64)
    traceparent = f"00-{0:016x}{trace64:016x}-{span64:016x}-01"
    return {
        "traceparent": traceparent,
        "tracestate": "dd=s:1;o:rum",
        "x-datadog-origin": "rum",
        "x-datadog-parent-id": str(span64),
        "x-datadog-sampling-priority": "1",
        "x-datadog-trace-id": str(trace64),
    }


def _base(profile: FirefoxProfile) -> dict:
    return {
        "User-Agent": profile.user_agent,
        "Accept-Language": profile.accept_language,
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "te": "trailers",
    }


# Sentinel value marking the slot where the client must drop in the live Cookie
# header (kept in Firefox's exact position). Left as None on the wire when there
# are no cookies yet (curl_cffi drops None-valued headers).
COOKIE_SLOT = "Cookie"

# Token header slots the client fills after minting inside Camoufox. Declared
# here (value None) so they occupy the golden position; the client overwrites
# the value in place, which preserves dict insertion order.
SENTINEL_TOKEN_SLOT = "openai-sentinel-token"
SENTINEL_SO_TOKEN_SLOT = "openai-sentinel-so-token"


def _xhr(profile: FirefoxProfile, *, site: str, referer: str,
         origin: str | None = None, accept: str = "*/*",
         content_type: str | None = None, sentinel_token: bool = False,
         so_token: bool = False, rum: bool = False) -> dict:
    """Build an XHR/fetch header dict in the EXACT order a real Firefox emits
    (see reports/chatgpt-camoufox). curl_cffi is created with
    `default_headers=False`, so this order is sent verbatim.

    Order: User-Agent, Accept, Accept-Language, Accept-Encoding, Referer,
    Content-Type, [so-token], [sentinel-token], [datadog-rum...], Origin,
    Cookie, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, priority, te.
    """
    h: dict = {
        "User-Agent": profile.user_agent,
        "Accept": accept,
        "Accept-Language": profile.accept_language,
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": referer,
    }
    if content_type:
        h["Content-Type"] = content_type
    if so_token:
        h[SENTINEL_SO_TOKEN_SLOT] = None
    if sentinel_token:
        h[SENTINEL_TOKEN_SLOT] = None
    if rum:
        h.update(datadog_rum())
    if origin:
        h["Origin"] = origin
    h[COOKIE_SLOT] = None
    h["Sec-Fetch-Dest"] = "empty"
    h["Sec-Fetch-Mode"] = "cors"
    h["Sec-Fetch-Site"] = site
    h["priority"] = "u=4"
    h["te"] = "trailers"
    return h


def _navigate(profile: FirefoxProfile, *, site: str, referer: str | None,
              origin: str | None = None, content_type: str | None = None,
              user: bool = True) -> dict:
    """Build a top-level navigation header dict in golden Firefox order.

    Order: User-Agent, Accept, Accept-Language, Accept-Encoding, [Referer],
    Cookie, Upgrade-Insecure-Requests, Sec-Fetch-Dest, Sec-Fetch-Mode,
    Sec-Fetch-Site, [Sec-Fetch-User], priority, te.
    """
    h: dict = {
        "User-Agent": profile.user_agent,
        "Accept": _NAV_ACCEPT,
        "Accept-Language": profile.accept_language,
        "Accept-Encoding": "gzip, deflate, br, zstd",
    }
    if referer:
        h["Referer"] = referer
    if origin:
        h["Origin"] = origin
    if content_type:
        h["Content-Type"] = content_type
    h[COOKIE_SLOT] = None
    h["Upgrade-Insecure-Requests"] = "1"
    h["Sec-Fetch-Dest"] = "document"
    h["Sec-Fetch-Mode"] = "navigate"
    h["Sec-Fetch-Site"] = site
    if user:
        h["Sec-Fetch-User"] = "?1"
    h["priority"] = "u=0, i"
    h["te"] = "trailers"
    return h


# ---- per-endpoint builders (names match client steps) ----------------------

def csrf(profile: FirefoxProfile) -> dict:
    return _xhr(profile, site="same-origin", referer=f"{CHATGPT}/",
                content_type="application/json")


def signin(profile: FirefoxProfile) -> dict:
    return _xhr(profile, site="same-origin", referer=f"{CHATGPT}/",
                origin=CHATGPT,
                content_type="application/x-www-form-urlencoded")


def authorize_get(profile: FirefoxProfile) -> dict:
    return _navigate(profile, site="cross-site", referer=f"{CHATGPT}/")


def authorize_post(profile: FirefoxProfile, referer: str) -> dict:
    """The Cloudflare-challenge answer POST back to the authorize URL."""
    return _navigate(profile, site="same-origin", referer=referer,
                     origin=AUTH,
                     content_type="application/x-www-form-urlencoded")


def sentinel_req(profile: FirefoxProfile, frame_referer: str) -> dict:
    """sentinel/req runs inside the sentinel iframe: text/plain, same-origin."""
    return _xhr(profile, site="same-origin", referer=frame_referer,
                origin=SENTINEL, accept="*/*",
                content_type="text/plain;charset=UTF-8")


def register(profile: FirefoxProfile) -> dict:
    return _xhr(profile, site="same-origin",
                referer=f"{AUTH}/create-account/password", origin=AUTH,
                accept="application/json", content_type="application/json",
                sentinel_token=True, rum=True)


def otp_send(profile: FirefoxProfile) -> dict:
    return _navigate(profile, site="same-origin",
                     referer=f"{AUTH}/create-account/password")


def otp_validate(profile: FirefoxProfile) -> dict:
    return _xhr(profile, site="same-origin", referer=f"{AUTH}/email-verification",
                origin=AUTH, accept="application/json",
                content_type="application/json", rum=True)


def create_account(profile: FirefoxProfile) -> dict:
    return _xhr(profile, site="same-origin", referer=f"{AUTH}/about-you",
                origin=AUTH, accept="application/json",
                content_type="application/json",
                sentinel_token=True, so_token=True, rum=True)


def callback(profile: FirefoxProfile) -> dict:
    return _navigate(profile, site="cross-site", referer=f"{AUTH}/", user=False)


def session(profile: FirefoxProfile) -> dict:
    # /api/auth/session is a top-level navigation with no referer (site=none).
    return _navigate(profile, site="none", referer=None)
