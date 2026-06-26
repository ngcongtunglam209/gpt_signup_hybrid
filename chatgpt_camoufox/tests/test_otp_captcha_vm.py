"""Unit tests for OTP (HTTP only), captcha client, and the token generator API."""
import pytest

from chatgpt_camoufox import camoufox_vm
from chatgpt_camoufox.captcha import CaptchaError, YesCaptchaClient
from chatgpt_camoufox.otp import (
    HttpOTPReader, ManualOTPReader, build_reader, extract_code,
)


# ---- OTP -------------------------------------------------------------------

def test_extract_code():
    assert extract_code("Your code is 123456 now") == "123456"
    assert extract_code("no code here") is None


def test_build_reader_requires_http():
    assert isinstance(build_reader("https://m/api"), HttpOTPReader)
    with pytest.raises(ValueError):
        build_reader("imap://h:993")


def test_build_reader_manual_keyword():
    # "manual" (or empty) selects the interactive prompt reader.
    assert isinstance(build_reader("manual"), ManualOTPReader)
    assert isinstance(build_reader(""), ManualOTPReader)


def test_manual_reader_prompts_and_extracts_code():
    # Operator pastes the mail line; the 6-digit code is extracted.
    reader = ManualOTPReader(prompt=lambda msg: "Your code is 246810")
    assert reader.get_code() == "246810"


def test_manual_reader_accepts_bare_code():
    reader = ManualOTPReader(prompt=lambda msg: "  135790 ")
    assert reader.get_code() == "135790"


def test_manual_reader_reprompts_until_valid():
    answers = iter(["nope", "still nope", "code 112233"])
    reader = ManualOTPReader(prompt=lambda msg: next(answers), max_tries=5)
    assert reader.get_code() == "112233"


def test_manual_reader_gives_up_after_max_tries():
    reader = ManualOTPReader(prompt=lambda msg: "no digits", max_tries=2)
    with pytest.raises(ValueError):
        reader.get_code()


class _FakeHTTP:
    def __init__(self, payloads):
        self._p = list(payloads)

    def get(self, url, timeout=30):
        class R:
            status_code = 200
            headers = {"content-type": "application/json"}

            def __init__(s, body):
                s._b = body

            def raise_for_status(s):
                pass

            def json(s):
                return s._b
        return R(self._p.pop(0))


def test_http_reader_polls_until_code():
    r = HttpOTPReader("https://m/api", session=_FakeHTTP([{"text": "wait"},
                                                          {"text": "code 654321"}]))
    assert r.get_code(timeout=5, poll=0) == "654321"


# ---- captcha ---------------------------------------------------------------

class _FakeCaptchaHTTP:
    def __init__(self, responses):
        self._r = list(responses)
        self.calls = []

    def post(self, url, json=None, timeout=60):
        self.calls.append((url, json))

        class R:
            def __init__(s, body):
                s._b = body

            def raise_for_status(s):
                pass

            def json(s):
                return s._b
        return R(self._r.pop(0))


def test_turnstile_solve():
    http = _FakeCaptchaHTTP([
        {"errorId": 0, "taskId": "T1"},
        {"errorId": 0, "status": "ready", "solution": {"token": "TS"}},
    ])
    c = YesCaptchaClient("k", session=http, poll_interval=0)
    assert c.solve_turnstile("https://u", "key") == "TS"


def test_captcha_error_propagates():
    http = _FakeCaptchaHTTP([{"errorId": 1, "errorCode": "X", "errorDescription": "bad"}])
    c = YesCaptchaClient("k", session=http, poll_interval=0)
    with pytest.raises(CaptchaError):
        c.create_task({"type": "x"})


# ---- token generator (stub runner, no browser) -----------------------------
# The genuine sdk mints the whole {p,t,c} bundle live; the runner takes
# (kind, flow) and returns {"ok":bool, "value":..., "err":...}.

def test_mint_token_parses_bundle():
    raw = '{"p":"gAAAAAB_p","t":"TT","c":"CC","flow":"login"}'
    g = camoufox_vm.CamoufoxTokenGenerator(
        runner=lambda kind, flow: {"ok": True, "value": raw})
    tok = g.mint_token("login")
    assert tok.p == "gAAAAAB_p"
    assert tok.t == "TT"
    assert tok.c == "CC"
    assert tok.flow == "login"
    assert tok.raw == raw


def test_mint_so_from_object():
    g = camoufox_vm.CamoufoxTokenGenerator(
        runner=lambda kind, flow: {"ok": True, "value": {"so": "SS"}})
    assert g.mint_so("oauth_create_account") == "SS"


def test_mint_so_from_string():
    g = camoufox_vm.CamoufoxTokenGenerator(
        runner=lambda kind, flow: {"ok": True, "value": '{"so":"SS2"}'})
    assert g.mint_so("oauth_create_account") == "SS2"


def test_runner_receives_kind_and_flow():
    seen = {}

    def runner(kind, flow):
        seen["kind"], seen["flow"] = kind, flow
        return {"ok": True, "value": '{"p":"p","t":"t","c":"c","flow":"f"}'}

    camoufox_vm.CamoufoxTokenGenerator(runner=runner).mint_token("username_password_create")
    assert seen == {"kind": "token", "flow": "username_password_create"}


def test_mint_token_propagates_error():
    g = camoufox_vm.CamoufoxTokenGenerator(
        runner=lambda kind, flow: {"ok": False, "err": "boom"})
    with pytest.raises(camoufox_vm.EnforcementError):
        g.mint_token("login")


def test_mint_token_missing_value():
    g = camoufox_vm.CamoufoxTokenGenerator(
        runner=lambda kind, flow: {"ok": True})
    with pytest.raises(camoufox_vm.EnforcementError):
        g.mint_token("login")


# ---- cookie / device-id bridge between Camoufox and curl_cffi --------------

class _FakeContext:
    def __init__(self, cookies):
        self._cookies = cookies
        self.added = []

    def cookies(self):
        return self._cookies

    def add_cookies(self, cookies):
        self.added.extend(cookies)
        self._cookies.extend(cookies)


class _FakePage:
    def __init__(self, cookies):
        self.context = _FakeContext(cookies)


def test_export_cookies_returns_session_cookies():
    cookies = [
        {"name": "cf_clearance", "value": "CFC", "domain": ".openai.com"},
        {"name": "__cf_bm", "value": "BM", "domain": ".chatgpt.com"},
        {"name": "oai-sc", "value": "SC", "domain": ".chatgpt.com"},
        {"name": "irrelevant", "value": "x", "domain": ".example.com"},
    ]
    g = camoufox_vm.CamoufoxTokenGenerator(runner=lambda k, f: {"ok": True})
    g._page = _FakePage(cookies)
    out = g.export_cookies()
    names = {c["name"] for c in out}
    # Cloudflare + sentinel session cookies are carried; unrelated ones dropped.
    assert {"cf_clearance", "__cf_bm", "oai-sc"} <= names
    assert "irrelevant" not in names


def test_export_cookies_empty_without_page():
    g = camoufox_vm.CamoufoxTokenGenerator(runner=lambda k, f: {"ok": True})
    assert g.export_cookies() == []


def test_set_device_id_adds_oai_did_cookie():
    g = camoufox_vm.CamoufoxTokenGenerator(runner=lambda k, f: {"ok": True})
    g._page = _FakePage([])
    g.set_device_id("dev-123")
    added = g._page.context.added
    assert any(c["name"] == "oai-did" and c["value"] == "dev-123" for c in added)
    domains = {c["domain"] for c in added if c["name"] == "oai-did"}
    assert any("openai.com" in d for d in domains)


def test_assets_exist():
    import os
    assert os.path.exists(camoufox_vm.SDK_PATH)
    assert os.path.exists(camoufox_vm.HARNESS_PATH)
