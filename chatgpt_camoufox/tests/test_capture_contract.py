"""Contract: reversed constants + flow + Firefox PoW shapes must match the real
mitmproxy capture reports/chatgpt-camoufox. Skips if dump/mitmproxy absent."""
import base64
import json
import os
import re

import pytest

from chatgpt_camoufox import fields

DUMP = os.path.join(os.path.dirname(__file__), "..", "..", "chatgpt-camoufox")
pytest.importorskip("mitmproxy.io")


def _sorted_flows():
    from mitmproxy.io import FlowReader

    flows = []
    with open(DUMP, "rb") as f:
        for flow in FlowReader(f).stream():
            req = getattr(flow, "request", None)
            if req:
                flows.append((req.timestamp_start or 0, flow))
    flows.sort(key=lambda x: x[0])
    return flows


def _core_sequence(flows):
    seq = []
    for _, flow in flows:
        req = flow.request
        h = req.host or ""
        p = req.path.split("?")[0]
        if h == "auth.openai.com" and p.startswith("/api/accounts/"):
            seq.append(f"{req.method} {h}{p}")
        elif h == "chatgpt.com" and p in (
            "/api/auth/csrf", "/api/auth/signin/openai",
            "/api/auth/callback/openai", "/api/auth/session",
        ):
            seq.append(f"{req.method} {h}{p}")
    return seq


def _decode_arrays(flows):
    arrs = []
    for _, flow in flows:
        req = flow.request
        cands = []
        if "sentinel/req" in req.path.split("?")[0] and req.method == "POST":
            try:
                cands.append(json.loads(req.get_text() or "{}").get("p"))
            except Exception:
                pass
        for hk in ("openai-sentinel-token", "openai-sentinel-so-token"):
            raw = req.headers.get(hk)
            if raw:
                try:
                    cands.append(json.loads(raw).get("p"))
                except Exception:
                    pass
        for p in cands:
            if not p or not p.startswith("gAAAAA"):
                continue
            core = p[7:].split("~")[0]
            try:
                a = json.loads(base64.b64decode(core + "=" * (-len(core) % 4)))
            except Exception:
                continue
            if isinstance(a, list) and len(a) == 25:
                arrs.append(a)
    return arrs


@pytest.mark.skipif(not os.path.exists(DUMP), reason="capture dump not present")
def test_core_flow_present_and_ordered():
    seq = _core_sequence(_sorted_flows())
    # The Firefox flow includes a Cloudflare authorize dance (GET 403, POST, GET)
    # and ends at /api/auth/session. Assert the key milestones appear in order.
    must = [
        "GET chatgpt.com/api/auth/csrf",
        "POST chatgpt.com/api/auth/signin/openai",
        "GET auth.openai.com/api/accounts/authorize",
        "POST auth.openai.com/api/accounts/user/register",
        "GET auth.openai.com/api/accounts/email-otp/send",
        "POST auth.openai.com/api/accounts/email-otp/validate",
        "POST auth.openai.com/api/accounts/create_account",
        "GET chatgpt.com/api/auth/callback/openai",
        "GET chatgpt.com/api/auth/session",
    ]
    idx = 0
    for item in seq:
        if idx < len(must) and item == must[idx]:
            idx += 1
    assert idx == len(must), f"missing/out-of-order; got {seq}"


@pytest.mark.skipif(not os.path.exists(DUMP), reason="capture dump not present")
def test_authorize_constants_match():
    flows = _sorted_flows()
    q = None
    for _, flow in flows:
        req = flow.request
        if req.host == "auth.openai.com" and req.path.split("?")[0].endswith(
                "/api/accounts/authorize") and req.method == "GET":
            q = dict(req.query.items())
            break
    assert q is not None
    assert q["client_id"] == fields.OPENAI_CLIENT_ID
    assert q["redirect_uri"] == fields.REDIRECT_URI
    assert q["audience"] == fields.AUDIENCE
    assert q["scope"] == fields.SCOPE
    assert q["response_type"] == fields.RESPONSE_TYPE
    # Firefox passkey capability differs from Chrome (01001 vs 11111).
    assert q["ext-passkey-client-capabilities"] == fields.EXT_PASSKEY_CLIENT_CAPABILITIES
    assert fields.is_uuid4(q["device_id"])
    assert fields.is_uuid4(q["auth_session_logging_id"])


@pytest.mark.skipif(not os.path.exists(DUMP), reason="capture dump not present")
def test_useragent_is_firefox():
    for _, flow in _sorted_flows():
        req = flow.request
        if req.path.split("?")[0].endswith("/user/register"):
            ua = req.headers.get("user-agent")
            assert "Firefox/" in ua and "Gecko" in ua
            assert req.headers.get("sec-ch-ua") is None  # no client hints
            return
    pytest.fail("register not found")


@pytest.mark.skipif(not os.path.exists(DUMP), reason="capture dump not present")
def test_sentinel_req_is_text_plain():
    for _, flow in _sorted_flows():
        req = flow.request
        if "sentinel/req" in req.path.split("?")[0] and req.method == "POST":
            assert "text/plain" in (req.headers.get("content-type") or "")
            assert req.headers.get("origin") == "https://sentinel.openai.com"
            return
    pytest.fail("sentinel/req not found")


@pytest.mark.skipif(not os.path.exists(DUMP), reason="capture dump not present")
def test_protected_posts_carry_sentinel_token():
    wanted = {
        "/api/accounts/user/register": "username_password_create",
        "/api/accounts/create_account": "oauth_create_account",
    }
    found = {}
    for _, flow in _sorted_flows():
        req = flow.request
        if req.host != "auth.openai.com":
            continue
        p = req.path.split("?")[0]
        if p in wanted and req.method == "POST":
            raw = req.headers.get("openai-sentinel-token")
            assert raw, f"no sentinel token on {p}"
            obj = json.loads(raw)
            assert set(obj) >= {"p", "t", "c", "id", "flow"}
            assert obj["p"].startswith("gAAAAA")
            assert obj["flow"] == wanted[p]
            found[p] = True
    assert set(found) == set(wanted)


@pytest.mark.skipif(not os.path.exists(DUMP), reason="capture dump not present")
def test_create_account_carries_so_token():
    seen = {}
    for _, flow in _sorted_flows():
        req = flow.request
        raw = req.headers.get("openai-sentinel-so-token")
        if raw:
            p = req.path.split("?")[0]
            obj = json.loads(raw)
            assert set(obj) == {"so", "c", "id", "flow"}
            assert obj["flow"] == "oauth_create_account"
            seen[p] = True
    assert list(seen) == ["/api/accounts/create_account"]


# ---- the captured PoW arrays are Firefox-shaped (sanity on the dump) --------
# We no longer build these in Python (the genuine sdk.js mints them live in
# Camoufox), but the captured bytes still document the Firefox shape we target.

@pytest.mark.skipif(not os.path.exists(DUMP), reason="capture dump not present")
def test_captured_arrays_are_firefox_shaped():
    arrs = _decode_arrays(_sorted_flows())
    assert arrs
    for a in arrs:
        assert a[2] is None                       # no performance.memory
        assert a[18:25] == [0, 0, 0, 0, 0, 1, 1]  # FF feature flags
        assert isinstance(a[9], int)              # integer timers
        assert isinstance(a[13], int)
        assert isinstance(a[17], int)
        assert re.search(r"GMT[+-]\d{4} \(.+\)$", a[1])  # Date has (tz)
