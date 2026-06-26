"""ChatGPT auth relay client (Firefox/Camoufox).

Drives the full register/login flow with curl_cffi impersonating Firefox (TLS +
ordered headers), generating EVERY client-side field by formula:

  * oai-did / auth_session_logging_id   -> UUID4
  * sentinel proof-of-work `p`          -> pure-Python FNV-1a solver (Firefox arr)
  * sentinel enforcement `t`            -> real sdk.js dx-VM in Camoufox
  * sentinel `c`                        -> server token from sentinel/req
  * session-observer `so`               -> real snapshot dx-VM in Camoufox

then calls /api/auth/session and returns the JSON. The HTTP session, token
generator and captcha client are injected so orchestration is testable offline.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from http.cookiejar import Cookie, CookieJar
from typing import Any
from urllib.request import Request as _UrlRequest

ACCEPT_ENCODING = "gzip, deflate, br, zstd"


class _SetCookieResponse:
    """Minimal adapter so a stdlib CookieJar can extract Set-Cookie headers from
    a curl_cffi response (it expects an `info().get_all('Set-Cookie')` API)."""

    def __init__(self, set_cookie_values: list[str]):
        self._values = set_cookie_values

    def info(self):
        return self

    def get_all(self, name, default=None):
        if name.lower() == "set-cookie":
            return self._values
        return default if default is not None else []

from . import fields, headers, sentinel
from .camoufox_vm import CamoufoxTokenGenerator
from .fingerprint import DEFAULT_PROFILE, FirefoxProfile
from .identity import birthdate_from_age, random_birthdate, random_name
from .otp import HttpOTPReader

BASE_CHATGPT = "https://chatgpt.com"
BASE_AUTH = "https://auth.openai.com"


@dataclass
class Account:
    email: str
    password: str
    api: str  # HTTP OTP endpoint
    name: str | None = None
    birthdate: str | None = None
    age: int | None = None

    @classmethod
    def parse(cls, line: str) -> "Account":
        parts = line.strip().split("|")
        if len(parts) < 2:
            raise ValueError("expected email|password[|api]")
        # 3rd field optional: omit (or set "manual") to type the OTP by hand.
        api = parts[2] if len(parts) >= 3 and parts[2] else "manual"
        return cls(email=parts[0], password=parts[1], api=api)

    def resolved_name(self) -> str:
        return self.name or random_name()

    def resolved_birthdate(self) -> str:
        if self.birthdate:
            return self.birthdate
        if self.age is not None:
            return birthdate_from_age(self.age)
        return random_birthdate()


def make_session(profile: FirefoxProfile = DEFAULT_PROFILE,
                 verify: bool = True):
    """curl_cffi session impersonating the profile's Firefox version.

    `verify=False` disables TLS verification -- needed when a local MITM proxy
    (Clash / mitmproxy / Surge) re-signs certs with a CA curl doesn't trust.

    `default_headers=False` stops curl_cffi from injecting its own (mis-ordered)
    Firefox header template, so the exact per-endpoint header ORDER we build is
    sent verbatim -- including placing `cookie` near the end where a real
    Firefox puts it, instead of first. The TLS fingerprint (JA3/JA4) is set by
    `impersonate` and is unaffected by this flag (verified identical). We then
    drive Accept-Encoding ourselves via the `accept_encoding` request arg so
    brotli/gzip responses still auto-decode.
    """
    from curl_cffi import requests as cffi_requests

    return cffi_requests.Session(impersonate=profile.impersonate, verify=verify,
                                 default_headers=False)


@dataclass
class RelayResult:
    session_json: dict
    device_id: str
    cookies: dict
    steps: list = dc_field(default_factory=list)


class ChatGPTRelay:
    def __init__(
        self,
        account: Account,
        otp_reader: HttpOTPReader,
        session: Any = None,
        profile: FirefoxProfile | None = None,
        device_id: str | None = None,
        logging_id: str | None = None,
        tokens: CamoufoxTokenGenerator | None = None,
        captcha=None,
    ):
        self.account = account
        self.otp_reader = otp_reader
        self.profile = profile or DEFAULT_PROFILE
        self.session = session if session is not None else make_session(self.profile)
        self.device_id = device_id or fields.new_device_id()
        self.logging_id = logging_id or fields.new_auth_session_logging_id()
        self.tokens = tokens or CamoufoxTokenGenerator(profile=self.profile)
        self.captcha = captcha
        self.steps: list[str] = []
        self._camoufox_identity_synced = False
        # We manage cookies ourselves (see _request) so we can place the Cookie
        # header in Firefox's exact position. curl_cffi's own jar would force it
        # to the front, which is a bot tell.
        self._jar = CookieJar()
        self._set_cookie("oai-did", self.device_id, domain=".chatgpt.com")
        # The page's Datadog RUM SDK keeps a client-side `_dd_s` session cookie
        # on .openai.com that rides along on every same-origin XHR (register /
        # otp-validate / create_account in the golden capture). We don't run the
        # SDK, so we synthesize one in the captured format -- the server does not
        # validate it, but its presence matches a real browser.
        self._set_cookie("_dd_s", fields.new_datadog_session(),
                         domain=".openai.com")

    # ---- low level ---------------------------------------------------------
    def _set_cookie(self, name: str, value: str, domain: str = ".chatgpt.com"):
        initial_dot = domain.startswith(".")
        cookie = Cookie(
            version=0, name=name, value=value, port=None, port_specified=False,
            domain=domain, domain_specified=True, domain_initial_dot=initial_dot,
            path="/", path_specified=True, secure=True, expires=None,
            discard=False, comment=None, comment_url=None, rest={}, rfc2109=False)
        self._jar.set_cookie(cookie)

    def _cookie_header_for(self, url: str) -> str | None:
        """Build the Cookie header value the way a browser would for `url`."""
        req = _UrlRequest(url)
        self._jar.add_cookie_header(req)
        return req.get_header("Cookie")

    def _absorb_response_cookies(self, response, url: str) -> None:
        """Store Set-Cookie from a curl_cffi response into our own jar, matching
        normal browser cookie persistence across the redirect-driven flow."""
        resp_headers = getattr(response, "headers", None)
        if resp_headers is None:
            return
        set_cookies: list[str] = []
        getter = getattr(resp_headers, "get_list", None)
        if callable(getter):
            try:
                set_cookies = list(getter("set-cookie"))
            except Exception:
                set_cookies = []
        if not set_cookies:
            try:
                sc = resp_headers.get("set-cookie")
            except Exception:
                sc = None
            set_cookies = [sc] if sc else []
        if not set_cookies:
            return
        self._jar.extract_cookies(_SetCookieResponse(set_cookies),
                                  _UrlRequest(url))

    def _request(self, method: str, url: str, *, headers=None, **kw):
        # The builders pre-place a `Cookie` slot (value None) in Firefox's exact
        # position; fill it with our jar's value for this URL. curl_cffi
        # (default_headers=False) sends the dict order verbatim and drops any
        # header still valued None, so an empty cookie slot simply vanishes.
        headers = self._fill_cookie_slot(dict(headers or {}), url)
        kw.setdefault("allow_redirects", False)
        # Own the cookie jar: curl must neither send its jar nor reorder Cookie.
        kw["discard_cookies"] = True
        kw.setdefault("accept_encoding", ACCEPT_ENCODING)
        sender = self.session.get if method == "GET" else self.session.post
        r = sender(url, headers=headers, **kw)
        self._absorb_response_cookies(r, url)
        self.steps.append(f"{method} {url.split('?')[0]} -> {r.status_code}")
        return r

    def _fill_cookie_slot(self, headers: dict, url: str) -> dict:
        cookie_value = self._cookie_header_for(url)
        if not cookie_value:
            return headers
        # Find the existing Cookie slot (case-insensitive) and set it in place.
        for key in headers:
            if key.lower() == "cookie":
                headers[key] = cookie_value
                return headers
        # No pre-placed slot: insert before the first sec-fetch-* header.
        out: dict = {}
        inserted = False
        for k, v in headers.items():
            if not inserted and k.lower().startswith("sec-fetch-"):
                out["Cookie"] = cookie_value
                inserted = True
            out[k] = v
        if not inserted:
            out["Cookie"] = cookie_value
        return out

    def _get(self, url: str, **kw):
        return self._request("GET", url, **kw)

    def _post(self, url: str, **kw):
        return self._request("POST", url, **kw)

    # ---- sentinel ----------------------------------------------------------
    # The genuine sdk.js does its OWN sentinel/req inside Camoufox (fetching its
    # own fresh `p`/dx/`c`) and mints the whole {p,t,c} bundle live; the dx-VM
    # reads session-bound page globals, so a captured dx cannot be replayed.
    # We just take that bundle and stamp our device id onto it.
    #
    # Because two clients touch one logical session (Camoufox mints the token,
    # curl_cffi sends the request), we keep them in lock-step: seed Camoufox
    # with our device id BEFORE it mints, and copy the Cloudflare / sentinel
    # cookies it earns back into the curl_cffi session AFTER. The `t` token also
    # embeds Camoufox's egress IP/geo, so both must share one proxy (enforced by
    # the CLI) or the IP will not match.
    def _sync_identity_to_camoufox(self) -> None:
        if self._camoufox_identity_synced:
            return
        setter = getattr(self.tokens, "set_device_id", None)
        if callable(setter):
            setter(self.device_id)
        self._camoufox_identity_synced = True

    # Only the cookies the curl_cffi session CANNOT earn on its own get copied
    # over from Camoufox. `cf_clearance` is minted by solving Cloudflare's JS
    # challenge (browser-only) and `oai-sc` is set by the sdk's own sentinel/req
    # inside Camoufox. The rest (`__cf_bm`, `__cflb`, `_cfuvid`) are ordinary
    # Cloudflare cookies that curl_cffi already receives from its OWN responses
    # -- re-copying Camoufox's (from a different TLS session) only overwrites the
    # fresh ones with stale, mismatched values, which is itself a bot tell.
    _ABSORB_COOKIE_NAMES = frozenset({"cf_clearance", "oai-sc"})

    def _absorb_camoufox_cookies(self) -> None:
        exporter = getattr(self.tokens, "export_cookies", None)
        if not callable(exporter):
            return
        for c in exporter():
            name, value = c.get("name"), c.get("value")
            if not name or value is None:
                continue
            if name not in self._ABSORB_COOKIE_NAMES:
                continue
            for domain in self._absorb_domains(name, c.get("domain")):
                self._drop_cookie_variants(name, domain)
                self._set_cookie(name, value, domain=domain)

    @staticmethod
    def _absorb_domains(name: str, exported_domain: str | None) -> list[str]:
        """Domains to register an absorbed cookie under.

        `oai-sc` is set by the sdk's own sentinel/req; in our setup the sdk runs
        in the chatgpt.com iframe so Camoufox only scopes it to `.chatgpt.com`.
        The genuine flow (sdk in the sentinel.openai.com frame) also has it on
        `.openai.com`, where the protected auth.openai.com POSTs read it. Mirror
        that by also scoping `oai-sc` to `.openai.com`."""
        base = exported_domain or ".openai.com"
        if name == "oai-sc":
            domains = [base]
            if ".openai.com" not in domains:
                domains.append(".openai.com")
            return domains
        return [base]

    def _drop_cookie_variants(self, name: str, domain: str) -> None:
        """Remove any existing copies of `name` for this domain (host-only and
        dot-prefixed) so we don't end up sending a duplicate / the wrong variant
        over the wire."""
        host = domain.lstrip(".")
        for cookie in list(self._jar):
            if cookie.name == name and (cookie.domain or "").lstrip(".") == host:
                try:
                    self._jar.clear(cookie.domain, cookie.path, cookie.name)
                except (KeyError, Exception):
                    pass

    def build_sentinel_header(self, flow: str) -> str:
        self._sync_identity_to_camoufox()
        token = self.tokens.mint_token(flow)
        self._absorb_camoufox_cookies()
        return sentinel.build_sentinel_token(
            p=token.p, enforcement_t=token.t, c=token.c,
            device_id=self.device_id, flow=flow)

    def build_sentinel_and_so_headers(self, flow: str) -> tuple[str, str | None]:
        """Mint the sentinel token and (for create_account) the session-observer
        token from the same live sdk session.

        `mint_token` must run first so the sdk caches the SO chat-req for this
        flow before `mint_so` reads it."""
        self._sync_identity_to_camoufox()
        token = self.tokens.mint_token(flow)
        sentinel_token = sentinel.build_sentinel_token(
            p=token.p, enforcement_t=token.t, c=token.c,
            device_id=self.device_id, flow=flow)
        so_token = None
        so = self.tokens.mint_so(flow)
        if so:
            so_token = sentinel.build_so_token(
                so=so, c=token.c, device_id=self.device_id, flow=flow)
        self._absorb_camoufox_cookies()
        return sentinel_token, so_token

    # ---- flow steps --------------------------------------------------------
    def get_csrf(self) -> str:
        r = self._get(f"{BASE_CHATGPT}/api/auth/csrf",
                      headers=headers.csrf(self.profile))
        return fields.parse_csrf_token(r.json())

    def signin(self, csrf_token: str) -> str:
        q = fields.signin_query(self.device_id, self.logging_id, self.account.email)
        r = self._post(f"{BASE_CHATGPT}/api/auth/signin/openai?{q}",
                       data=fields.signin_body(csrf_token),
                       headers=headers.signin(self.profile))
        return r.json()["url"]

    def authorize(self, authorize_url: str) -> str:
        """GET authorize. In the capture this returns a Cloudflare 403, the
        browser answers it (POST) and a final GET 302 establishes the session.
        With curl_cffi we GET it; on a 403 a captcha solver (if configured)
        clears Cloudflare, then we retry."""
        r = self._get(authorize_url, headers=headers.authorize_get(self.profile))
        if r.status_code == 403 and self.captcha:
            self._clear_cloudflare(authorize_url)
            r = self._get(authorize_url,
                          headers=headers.authorize_get(self.profile))
        return fields.extract_state(authorize_url)

    def _clear_cloudflare(self, url: str) -> None:
        sol = self.captcha.solve_cloudflare(
            url, proxy=getattr(self.session, "_proxy", None),
            user_agent=self.profile.user_agent)
        cf = sol.get("cf_clearance")
        if cf:
            self._set_cookie("cf_clearance", cf, domain=".openai.com")

    def register(self) -> dict:
        h = headers.register(self.profile)
        h["openai-sentinel-token"] = self.build_sentinel_header(
            "username_password_create")
        r = self._post(f"{BASE_AUTH}/api/accounts/user/register",
                       json={"password": self.account.password,
                             "username": self.account.email},
                       headers=h)
        return r.json()

    def otp_send(self) -> None:
        self._get(f"{BASE_AUTH}/api/accounts/email-otp/send",
                  headers=headers.otp_send(self.profile))

    def otp_validate(self, code: str) -> dict:
        # No sentinel token on this endpoint (verified in capture).
        r = self._post(f"{BASE_AUTH}/api/accounts/email-otp/validate",
                       json={"code": code},
                       headers=headers.otp_validate(self.profile))
        return r.json()

    def create_account(self) -> str:
        h = headers.create_account(self.profile)
        sentinel_token, so_token = self.build_sentinel_and_so_headers(
            "oauth_create_account")
        h["openai-sentinel-token"] = sentinel_token
        if so_token:
            h["openai-sentinel-so-token"] = so_token
        r = self._post(f"{BASE_AUTH}/api/accounts/create_account",
                       json={"name": self.account.resolved_name(),
                             "birthdate": self.account.resolved_birthdate()},
                       headers=h)
        return fields.parse_callback_from_create_account(r.json())

    def callback(self, callback_url: str) -> None:
        self._get(callback_url, headers=headers.callback(self.profile))

    def get_session(self) -> dict:
        r = self._get(f"{BASE_CHATGPT}/api/auth/session",
                      headers=headers.session(self.profile))
        return r.json()

    # ---- orchestration -----------------------------------------------------
    def run(self) -> RelayResult:
        csrf = self.get_csrf()
        authorize_url = self.signin(csrf)
        self.authorize(authorize_url)
        self.register()
        self.otp_send()
        code = self.otp_reader.get_code()
        self.otp_validate(code)
        callback_url = self.create_account()
        self.callback(callback_url)
        session_json = self.get_session()
        cookies = self._dump_cookies()
        return RelayResult(session_json=session_json, device_id=self.device_id,
                           cookies=cookies, steps=list(self.steps))

    def _dump_cookies(self) -> dict:
        """Flatten our manually-managed jar to {name: value} for the result."""
        return {c.name: c.value for c in self._jar}
