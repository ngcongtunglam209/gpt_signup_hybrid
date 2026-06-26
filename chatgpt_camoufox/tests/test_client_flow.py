"""Orchestration must run the Firefox flow offline: the genuine sdk mints the
sentinel tokens live inside Camoufox (so the client itself does NOT POST
sentinel/req), tokens injected on the right steps, ends at /api/auth/session."""
import json

from chatgpt_camoufox.camoufox_vm import SentinelToken
from chatgpt_camoufox.client import Account, ChatGPTRelay

CAP_STATE = "HL80aFDjpVqPmY_3_CndJRDFLHe6ZvycOmW-_sgFxQQ"
CALLBACK_URL = (
    "https://chatgpt.com/api/auth/callback/openai?code=ac_TEST.abc&state="
    + CAP_STATE)


class FakeResp:
    def __init__(self, status=200, json_data=None):
        self.status_code = status
        self._json = json_data or {}

    def json(self):
        return self._json


class FakeCookies:
    def __init__(self):
        self._d = {}
        self.sets = []  # (name, value, domain) in order

    def set(self, name, value, domain=None):
        self._d[name] = value
        self.sets.append((name, value, domain))

    def __iter__(self):
        class C:
            def __init__(self, n, v):
                self.name, self.value = n, v
        return iter([C(k, v) for k, v in self._d.items()])


class FakeSession:
    def __init__(self):
        self.cookies = FakeCookies()
        self.calls = []
        self.sentinel_headers = {}
        self.sentinel_bodies = []

    def _route(self, method, url, headers=None, data=None, **kw):
        path = url.split("?")[0]
        self.calls.append(f"{method} {path}")
        if path.endswith("/api/auth/csrf"):
            return FakeResp(200, {"csrfToken": "CSRF1"})
        if path.endswith("/api/auth/signin/openai"):
            return FakeResp(200, {"url":
                "https://auth.openai.com/api/accounts/authorize?state=" + CAP_STATE})
        if path.endswith("/api/accounts/authorize"):
            return FakeResp(302, {})
        if path.endswith("/api/accounts/user/register"):
            self.sentinel_headers["register"] = (headers or {}).get("openai-sentinel-token")
            return FakeResp(200, {"continue_url":
                "https://auth.openai.com/api/accounts/email-otp/send"})
        if path.endswith("/api/accounts/email-otp/send"):
            return FakeResp(302, {})
        if path.endswith("/api/accounts/email-otp/validate"):
            self.sentinel_headers["validate"] = (headers or {}).get("openai-sentinel-token")
            return FakeResp(200, {"continue_url": "https://auth.openai.com/about-you"})
        if path.endswith("/api/accounts/create_account"):
            self.sentinel_headers["create"] = (headers or {}).get("openai-sentinel-token")
            self.sentinel_headers["create_so"] = (headers or {}).get("openai-sentinel-so-token")
            return FakeResp(200, {"continue_url": CALLBACK_URL})
        if path.endswith("/api/auth/callback/openai"):
            return FakeResp(302, {})
        if path.endswith("/api/auth/session"):
            return FakeResp(200, {"user": {"email": "argon.baton.3y+1@icloud.com"},
                                  "accessToken": "tok", "expires": "2026-09-24"})
        raise AssertionError("unexpected url " + url)

    def get(self, url, **kw):
        return self._route("GET", url, kw.get("headers"))

    def post(self, url, **kw):
        return self._route("POST", url, kw.get("headers"), kw.get("data"))


class FakeOTP:
    def get_code(self, timeout=120, poll=5):
        return "884382"


class FakeTokens:
    """Stands in for the live sdk: token() yields the full {p,t,c} bundle and
    sessionObserverToken() the `so`, both per-flow. Also exposes the
    cookie/device-id bridge the client uses to keep Camoufox and curl_cffi in
    one session."""

    def __init__(self, cookies=None):
        self.flows = []
        self.device_id = None
        self._cookies = cookies if cookies is not None else [
            {"name": "cf_clearance", "value": "CFC", "domain": ".openai.com"},
            {"name": "oai-sc", "value": "SC", "domain": ".chatgpt.com"},
            {"name": "__cf_bm", "value": "BM", "domain": ".chatgpt.com"},
        ]

    def set_device_id(self, did):
        self.device_id = did

    def export_cookies(self):
        return list(self._cookies)

    def mint_token(self, flow):
        self.flows.append(("token", flow))
        return SentinelToken(p="gAAAAAB_solved", t="ENF_T", c="SERVER_C",
                             flow=flow, raw="{}")

    def mint_so(self, flow):
        self.flows.append(("so", flow))
        return "SESS_SO"


def _relay():
    acct = Account("argon.baton.3y+1@icloud.com", "Zxcv@12345678", "https://mail/api")
    return ChatGPTRelay(acct, FakeOTP(), session=FakeSession(),
                        device_id="dev-1", logging_id="log-1", tokens=FakeTokens())


def test_full_flow_sequence_and_result():
    relay = _relay()
    result = relay.run()
    expected = [
        "GET https://chatgpt.com/api/auth/csrf",
        "POST https://chatgpt.com/api/auth/signin/openai",
        "GET https://auth.openai.com/api/accounts/authorize",
        "POST https://auth.openai.com/api/accounts/user/register",
        "GET https://auth.openai.com/api/accounts/email-otp/send",
        "POST https://auth.openai.com/api/accounts/email-otp/validate",
        "POST https://auth.openai.com/api/accounts/create_account",
        "GET https://chatgpt.com/api/auth/callback/openai",
        "GET https://chatgpt.com/api/auth/session",
    ]
    # The sdk POSTs sentinel/req itself inside Camoufox -- the relay's own HTTP
    # session never hits it.
    assert relay.session.calls == expected
    assert result.session_json["user"]["email"] == "argon.baton.3y+1@icloud.com"
    assert result.device_id == "dev-1"
    assert result.cookies["oai-did"] == "dev-1"


def test_token_minted_per_flow_token_before_so():
    relay = _relay()
    relay.run()
    # register mints a token for its flow; create_account mints token THEN so
    # (so the sdk's SO chat-req is cached before sessionObserverToken runs).
    assert relay.tokens.flows == [
        ("token", "username_password_create"),
        ("token", "oauth_create_account"),
        ("so", "oauth_create_account"),
    ]


def test_tokens_injected_on_protected_posts_only():
    relay = _relay()
    relay.run()
    sh = relay.session.sentinel_headers
    assert sh.get("validate") is None  # no token on otp validate
    for step, flow in [("register", "username_password_create"),
                       ("create", "oauth_create_account")]:
        obj = json.loads(sh[step])
        assert obj["c"] == "SERVER_C"
        assert obj["t"] == "ENF_T"
        assert obj["id"] == "dev-1"
        assert obj["flow"] == flow
        assert obj["p"].startswith("gAAAAAB")  # sdk-minted sync PoW
    so = json.loads(sh["create_so"])
    assert so == {"so": "SESS_SO", "c": "SERVER_C", "id": "dev-1",
                  "flow": "oauth_create_account"}


def test_account_parse():
    a = Account.parse("e@x.com|secret|https://mail/api")
    assert a.email == "e@x.com" and a.password == "secret"


def test_device_id_pushed_into_camoufox_before_minting():
    relay = _relay()
    relay.run()
    # The relay must seed Camoufox with the SAME device id so the sdk's own
    # sentinel/req uses it (keeps oai-did consistent across both clients).
    assert relay.tokens.device_id == "dev-1"


def _jar_names(relay):
    return {c.name for c in relay._jar}


def _jar_cookie(relay, name):
    return [c for c in relay._jar if c.name == name][0]


def test_camoufox_cookies_copied_into_curl_session():
    relay = _relay()
    relay.run()
    # Only the browser-exclusive clearance cookies are copied: cf_clearance
    # (Cloudflare JS challenge) and oai-sc (set by the sdk's own sentinel/req).
    names = _jar_names(relay)
    assert "cf_clearance" in names
    assert "oai-sc" in names
    # domain preserved from the browser cookie
    assert "openai.com" in (_jar_cookie(relay, "cf_clearance").domain or "")


def test_ordinary_cloudflare_cookies_not_copied_from_camoufox():
    # __cf_bm / __cflb / _cfuvid are earned by curl_cffi's OWN responses;
    # re-copying Camoufox's stale variants would overwrite the fresh ones and
    # make curl send a value from a different TLS session (a bot tell).
    relay = _relay()
    # The FakeSession returns no Set-Cookie, so the only way these names could
    # appear is via the Camoufox absorb path -- which we now exclude.
    relay.run()
    assert "__cf_bm" not in _jar_names(relay)
    assert "__cflb" not in _jar_names(relay)
    assert "_cfuvid" not in _jar_names(relay)


class CloudflareSession(FakeSession):
    """authorize returns 403 once (Cloudflare), then 302 after clearance."""

    def __init__(self):
        super().__init__()
        self._authorize_hits = 0

    def _route(self, method, url, headers=None, data=None, **kw):
        path = url.split("?")[0]
        if path.endswith("/api/accounts/authorize") and method == "GET":
            self.calls.append(f"{method} {path}")
            self._authorize_hits += 1
            return FakeResp(403 if self._authorize_hits == 1 else 302, {})
        return super()._route(method, url, headers, data, **kw)


class FakeCaptcha:
    def __init__(self):
        self.calls = 0

    def solve_cloudflare(self, url, proxy=None, user_agent=None):
        self.calls += 1
        return {"cf_clearance": "CF_SOLVED"}


def test_cloudflare_403_triggers_solver_and_retry():
    acct = Account("argon.baton.3y+1@icloud.com", "Zxcv@12345678", "https://mail/api")
    captcha = FakeCaptcha()
    relay = ChatGPTRelay(acct, FakeOTP(), session=CloudflareSession(),
                         device_id="dev-1", logging_id="log-1",
                         tokens=FakeTokens(), captcha=captcha)
    result = relay.run()
    assert captcha.calls == 1
    # authorize was retried (two GETs) and the clearance cookie was stored
    assert relay.session.calls.count("GET https://auth.openai.com/api/accounts/authorize") == 2
    assert "cf_clearance" in _jar_names(relay)
    assert result.session_json["user"]["email"] == "argon.baton.3y+1@icloud.com"
