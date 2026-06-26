"""Mint the sentinel tokens by running the GENUINE sentinel sdk.js inside a real
Camoufox (Firefox) browser, live.

Why live (and not by replaying a captured dx):
  The sdk's `token(flow)` builds the whole `{p,t,c}` bundle itself. Its `t` is
  produced by a dx-VM that interprets encrypted bytecode fetched fresh from
  sentinel/req for THIS session, and that bytecode reads live, session-bound
  page globals (loaderData, root, clientBootstrap, cfConnectingIp, cfIpCity,
  userRegion, cfIp{Latitude,Longitude}, ...). A dx captured in another session
  is bound to that session and can never be replayed. So we let the real sdk do
  the whole job in a real Gecko page -- the fingerprint payload then matches a
  real Firefox (unlike a jsdom shim).

  * `token(flow)`                -> JSON string {p,t,c,flow}
  * `sessionObserverToken(flow)` -> {so:...}  (call token(flow) first so the
                                    SO chat-req is cached)

The sdk runs in the page's own main world (Camoufox's Xray sandbox forbids
running it from Playwright's isolated world); Python talks to it over a
postMessage bridge. Inject a `runner` callable in tests to avoid a browser.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass

_ASSETS = os.path.join(os.path.dirname(__file__), "assets")
SDK_PATH = os.path.join(_ASSETS, "sentinel_sdk.js")
HARNESS_PATH = os.path.join(_ASSETS, "camoufox_harness.js")

FRAME_URL = "https://sentinel.openai.com/backend-api/sentinel/frame.html"

# Cookies the genuine sdk's own sentinel/req earns inside Camoufox that the
# curl_cffi session must replay so the protected POSTs share the same Cloudflare
# clearance / sentinel session (otherwise: token minted by browser A, sent by
# client B -> anti-bot mismatch).
SHARED_COOKIE_NAMES = frozenset({
    "cf_clearance", "__cf_bm", "__cflb", "_cfuvid", "oai-sc", "oai-did",
})

_BRIDGE_CALL = """
async ([kind, flow]) => {
  return await new Promise((resolve) => {
    const id = Math.random().toString(36).slice(2) + Date.now().toString(36);
    function handler(ev) {
      const d = ev.data;
      if (d && d.__sres === id) {
        window.removeEventListener('message', handler);
        resolve({ ok: d.ok, value: d.value, err: d.err });
      }
    }
    window.addEventListener('message', handler);
    window.postMessage({ __sreq: true, id, kind, flow }, '*');
    setTimeout(() => resolve({ ok: false, err: 'bridge timeout' }), 30000);
  });
}
"""


class EnforcementError(RuntimeError):
    pass


@dataclass
class SentinelToken:
    """The full sentinel token the sdk mints for one flow."""

    p: str
    t: str
    c: str
    flow: str
    raw: str  # the exact JSON string the sdk returned (what the header carries)

    @classmethod
    def from_json(cls, raw: str, flow: str) -> "SentinelToken":
        obj = json.loads(raw)
        return cls(p=obj.get("p", ""), t=obj.get("t", ""), c=obj.get("c", ""),
                   flow=obj.get("flow", flow), raw=raw)


def camoufox_available() -> bool:
    try:
        import camoufox  # noqa: F401
        return True
    except Exception:
        return False


class CamoufoxTokenGenerator:
    """Mints sentinel tokens via the genuine sdk in a real Camoufox page.

    A single browser/page is reused across calls. Inject a `runner` callable
    (kind, flow) -> {"ok":bool, "value":..., "err":...} in tests to avoid
    launching a browser.
    """

    def __init__(self, runner=None, sdk_path: str = SDK_PATH,
                 harness_path: str = HARNESS_PATH, profile=None,
                 proxy: str | None = None, headless: bool = True,
                 frame_url: str = FRAME_URL, insecure: bool = False):
        self.sdk_path = sdk_path
        self.harness_path = harness_path
        self.profile = profile
        self.proxy = proxy
        self.headless = headless
        self.frame_url = frame_url
        self.insecure = insecure
        self._runner = runner or self._run_browser
        self._cm = None
        self._browser = None
        self._page = None

    # ---- real browser path -------------------------------------------------
    def _ensure_page(self):
        if self._page is not None:
            return self._page
        from camoufox.sync_api import Camoufox

        with open(self.sdk_path, "r", encoding="utf-8") as f:
            sdk_src = f.read()
        with open(self.harness_path, "r", encoding="utf-8") as f:
            bridge_src = f.read()
        # Expose the module on window, then install the bridge in the SAME
        # page-world script so both share the main world.
        page_src = sdk_src.replace("var SentinelSDK=", "window.SentinelSDK=",
                                   1) + "\n;" + bridge_src

        opts: dict = {"headless": self.headless}
        if self.proxy:
            opts["proxy"] = {"server": self.proxy}
        if self.profile is not None:
            opts["os"] = {"Windows": "windows", "macOS": "macos",
                          "Linux": "linux"}.get(
                getattr(self.profile, "platform", "Windows"), "windows")
            lang = getattr(self.profile, "language", None)
            if lang:
                opts["locale"] = lang
        self._cm = Camoufox(**opts)
        self._browser = self._cm.__enter__()
        # ignore_https_errors lets the page load through a MITM proxy whose
        # re-signed certs Firefox would otherwise reject.
        self._page = self._browser.new_page(
            ignore_https_errors=True) if self.insecure else self._browser.new_page()
        self._page.goto(self.frame_url, wait_until="domcontentloaded",
                        timeout=45000)
        self._page.add_script_tag(content=page_src)
        # Wait for the bridge to come up (attached, not visible -- it has no
        # layout box).
        try:
            self._page.wait_for_selector(
                "#__sentinel_bridge_ready", state="attached", timeout=15000)
        except Exception:
            err = self._page.eval_on_selector(
                "#__sentinel_bridge_error", "e => e.textContent"
            ) if self._page.query_selector("#__sentinel_bridge_error") else None
            raise EnforcementError(err or "sentinel bridge did not initialise")
        return self._page

    def _run_browser(self, kind: str, flow: str) -> dict:
        if not camoufox_available():
            raise EnforcementError("camoufox not installed")
        page = self._ensure_page()
        result = page.evaluate(_BRIDGE_CALL, [kind, flow])
        return result or {}

    def close(self):
        try:
            if self._cm is not None:
                self._cm.__exit__(None, None, None)
        finally:
            self._cm = None
            self._browser = None
            self._page = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # ---- cookie / device-id bridge ----------------------------------------
    def export_cookies(self) -> list[dict]:
        """Return the Cloudflare / sentinel session cookies Camoufox earned, so
        the curl_cffi session can replay them on the protected POSTs."""
        if self._page is None:
            return []
        cookies = self._page.context.cookies()
        return [c for c in cookies if c.get("name") in SHARED_COOKIE_NAMES]

    def set_device_id(self, device_id: str) -> None:
        """Seed `oai-did` into Camoufox so the sdk's own sentinel/req uses the
        same device id the curl_cffi flow sends (keeps the id consistent)."""
        page = self._ensure_page()
        page.context.add_cookies([
            {"name": "oai-did", "value": device_id, "domain": dom, "path": "/"}
            for dom in (".openai.com", ".chatgpt.com")
        ])

    # ---- public API --------------------------------------------------------
    def mint_token(self, flow: str) -> SentinelToken:
        """Run the genuine sdk `token(flow)` and return the full {p,t,c} bundle."""
        res = self._runner("token", flow)
        if not res.get("ok"):
            raise EnforcementError(res.get("err") or "token() failed")
        raw = res.get("value")
        if not isinstance(raw, str) or not raw:
            raise EnforcementError("token() returned no string")
        return SentinelToken.from_json(raw, flow)

    def mint_so(self, flow: str) -> str:
        """Run `sessionObserverToken(flow)` and return the `so` string.

        Call `mint_token(flow)` first so the sdk has cached the SO chat-req for
        this flow.
        """
        res = self._runner("so", flow)
        if not res.get("ok"):
            raise EnforcementError(res.get("err") or "sessionObserverToken() failed")
        val = res.get("value")
        if isinstance(val, dict):
            return val.get("so", "")
        if isinstance(val, str) and val:
            try:
                return json.loads(val).get("so", val)
            except Exception:
                return val
        raise EnforcementError("sessionObserverToken() returned nothing")
