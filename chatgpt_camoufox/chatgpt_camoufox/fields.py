"""Pure helpers that reproduce the client-side (JS-generated) request fields.

Deterministic / unit-testable, no network. Mirrors what the ChatGPT web bundle
generates in Firefox before hitting the API. Constants are the genuine server
values from the capture (reports/chatgpt-camoufox).
"""
from __future__ import annotations

import re
import uuid
from urllib.parse import urlencode

# ---- server constants observed in the capture (authorize query) ----
OPENAI_CLIENT_ID = "app_X8zY6vW2pQ9tR3dE7nK1jL5gH"
REDIRECT_URI = "https://chatgpt.com/api/auth/callback/openai"
AUDIENCE = "https://api.openai.com/v1"
RESPONSE_TYPE = "code"
SCOPE = ("openid email profile offline_access "
         "model.request model.read organization.read organization.write")
# Firefox passkey capability bitmask (Chrome sent 11111; Firefox sends 01001).
EXT_PASSKEY_CLIENT_CAPABILITIES = "01001"

_UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def new_device_id() -> str:
    """`oai-did` / `device_id` / `ext-oai-did` — a fresh v4 UUID."""
    return str(uuid.uuid4())


def new_auth_session_logging_id() -> str:
    """`auth_session_logging_id` query param — a fresh v4 UUID per auth."""
    return str(uuid.uuid4())


def new_datadog_session(now_ms: int | None = None) -> str:
    """`_dd_s` cookie value the Datadog RUM SDK keeps client-side. Format taken
    verbatim from the capture: `aid=<uuid>&rum=2&id=<uuid>&created=<ms>&expire=<ms>`.
    The server does not validate it; the SDK refreshes `expire` on activity (the
    session window is ~15 min after `created`)."""
    import time

    created = now_ms if now_ms is not None else int(time.time() * 1000)
    expire = created + 15 * 60 * 1000  # 15-minute session window
    return (f"aid={uuid.uuid4()}&rum=2&id={uuid.uuid4()}"
            f"&created={created}&expire={expire}")


def is_uuid4(value: str) -> bool:
    return bool(_UUID4_RE.match(value or ""))


def signin_query(device_id: str, logging_id: str, login_hint: str) -> str:
    """Query string for POST chatgpt.com/api/auth/signin/openai (order verbatim)."""
    params = [
        ("prompt", "login"),
        ("ext-passkey-client-capabilities", EXT_PASSKEY_CLIENT_CAPABILITIES),
        ("ext-oai-did", device_id),
        ("auth_session_logging_id", logging_id),
        ("screen_hint", "login_or_signup"),
        ("login_hint", login_hint),
    ]
    return urlencode(params)


def signin_body(csrf_token: str, callback_url: str = "https://chatgpt.com/") -> str:
    """application/x-www-form-urlencoded body for signin/openai."""
    return urlencode(
        {"callbackUrl": callback_url, "csrfToken": csrf_token, "json": "true"}
    )


def extract_state(authorize_url: str) -> str:
    m = re.search(r"[?&]state=([^&]+)", authorize_url)
    if not m:
        raise ValueError("state not found in authorize url")
    return m.group(1)


def parse_csrf_token(json_body: dict) -> str:
    token = json_body.get("csrfToken")
    if not token:
        raise ValueError("csrfToken missing in /api/auth/csrf response")
    return token


def parse_callback_from_create_account(json_body: dict) -> str:
    """create_account returns the chatgpt callback URL (with code+state)."""
    url = json_body.get("continue_url")
    if not url:
        payload = (json_body.get("page") or {}).get("payload") or {}
        url = payload.get("url")
    if not url or "callback/openai" not in url:
        raise ValueError("callback url with code not found in create_account response")
    return url
