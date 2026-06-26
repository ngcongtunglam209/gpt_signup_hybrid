"""CLI orchestration: run_line wires profile/session/tokens/otp without a real
browser, threads the proxy into BOTH the curl_cffi session and Camoufox (so
they share one egress IP), and isolates per-account failures."""
import json

import pytest

from chatgpt_camoufox import __main__ as cli


class _StubResult:
    def __init__(self):
        self.device_id = "dev-x"
        self.session_json = {"user": {"email": "e@x.com"}}
        self.steps = ["GET a", "POST b"]


class _StubRelay:
    last = None

    def __init__(self, acct, reader, session=None, profile=None, tokens=None,
                 captcha=None, **kw):
        _StubRelay.last = self
        self.session = session
        self.profile = profile
        self.tokens = tokens
        self.captcha = captcha

    def run(self):
        return _StubResult()


class _StubTokens:
    instances = []

    def __init__(self, profile=None, proxy=None, headless=True, insecure=False):
        self.profile = profile
        self.proxy = proxy
        self.headless = headless
        self.insecure = insecure
        self.closed = False
        _StubTokens.instances.append(self)

    def close(self):
        self.closed = True


class _StubSession:
    def __init__(self, verify=True):
        self.proxies = None
        self.verify = verify


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    _StubRelay.last = None
    _StubTokens.instances = []
    monkeypatch.setattr(cli, "ChatGPTRelay", _StubRelay)
    monkeypatch.setattr(cli, "CamoufoxTokenGenerator", _StubTokens)
    monkeypatch.setattr(cli, "make_session",
                        lambda profile, verify=True: _StubSession(verify=verify))
    monkeypatch.setattr(cli, "build_reader", lambda api: object())
    # captcha only built when a key is given
    monkeypatch.setattr(cli, "YesCaptchaClient", lambda key: ("captcha", key))


def test_run_line_builds_result():
    out = cli.run_line("e@x.com|pw|https://mail/api", locale="vi-VN",
                       firefox_major=135, platform="Windows",
                       yescaptcha_key=None, proxy=None, headless=True)
    assert out["email"] == "e@x.com"
    assert out["device_id"] == "dev-x"
    assert out["session"]["user"]["email"] == "e@x.com"
    assert _StubTokens.instances[-1].closed is True  # generator closed in finally


def test_proxy_threaded_into_session_and_camoufox():
    cli.run_line("e@x.com|pw|https://mail/api", locale="vi-VN",
                 firefox_major=135, platform="Windows",
                 yescaptcha_key=None, proxy="http://p:8080", headless=True)
    # curl_cffi session gets the proxy...
    assert _StubRelay.last.session.proxies == {"http": "http://p:8080",
                                               "https": "http://p:8080"}
    # ...and Camoufox gets the SAME proxy (shared egress IP).
    assert _StubTokens.instances[-1].proxy == "http://p:8080"


def test_insecure_disables_tls_verify_for_both_clients():
    cli.run_line("e@x.com|pw|https://mail/api", locale="vi-VN",
                 firefox_major=135, platform="Windows",
                 yescaptcha_key=None, proxy="http://p:8080", headless=True,
                 insecure=True)
    assert _StubRelay.last.session.verify is False   # curl_cffi skips verify
    assert _StubTokens.instances[-1].insecure is True  # Camoufox ignores cert errors


def test_secure_by_default():
    cli.run_line("e@x.com|pw|https://mail/api", locale="vi-VN",
                 firefox_major=135, platform="Windows",
                 yescaptcha_key=None, proxy=None, headless=True)
    assert _StubRelay.last.session.verify is True
    assert _StubTokens.instances[-1].insecure is False


def test_captcha_only_when_key_present():
    cli.run_line("e@x.com|pw|https://mail/api", locale="vi-VN",
                 firefox_major=135, platform="Windows",
                 yescaptcha_key=None, proxy=None, headless=True)
    assert _StubRelay.last.captcha is None
    cli.run_line("e@x.com|pw|https://mail/api", locale="vi-VN",
                 firefox_major=135, platform="Windows",
                 yescaptcha_key="K", proxy=None, headless=True)
    assert _StubRelay.last.captcha == ("captcha", "K")


def test_main_two_lines_isolated(monkeypatch, tmp_path, capsys):
    seen = []

    def fake_run_line(line, **kw):
        seen.append(line)
        if "bad" in line:
            raise RuntimeError("boom")
        return {"email": line.split("|")[0]}

    monkeypatch.setattr(cli, "run_line", fake_run_line)
    f = tmp_path / "accts.txt"
    f.write_text("good@x.com|pw|https://m/api\nbad@x.com|pw|https://m/api\n")
    rc = cli.main(["--file", str(f)])
    assert rc == 0
    assert len(seen) == 2
    out = capsys.readouterr().out
    # both lines produce a JSON line; the failing one carries an "error".
    lines = [json.loads(l) for l in out.strip().splitlines()]
    assert any(d.get("email") == "good@x.com" for d in lines)
    assert any("error" in d for d in lines)
