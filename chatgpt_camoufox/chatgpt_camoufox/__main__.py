"""CLI: read `email|password|api` lines and run the Camoufox relay.

Usage:
    python -m chatgpt_camoufox "email|password|https://mail-api/latest" --locale vi-VN
    YESCAPTCHA_KEY=... python -m chatgpt_camoufox --file accounts.txt --proxy http://...
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys

from .camoufox_vm import CamoufoxTokenGenerator
from .captcha import YesCaptchaClient
from .client import Account, ChatGPTRelay, make_session
from .fingerprint import profile_for_locale
from .otp import build_reader


def run_line(line: str, *, locale: str, firefox_major: int, platform: str,
             yescaptcha_key: str | None, proxy: str | None,
             headless: bool, insecure: bool = False) -> dict:
    acct = Account.parse(line)
    profile = profile_for_locale(locale, firefox_major=firefox_major,
                                 platform=platform, rng=random.Random())
    reader = build_reader(acct.api)
    session = make_session(profile, verify=not insecure)
    if proxy:
        # Camoufox (which mints `t` with its egress IP/geo) and curl_cffi (which
        # sends the request) MUST share one proxy, or the token's IP won't match
        # the request IP. run_line passes the same `proxy` to both below.
        session.proxies = {"http": proxy, "https": proxy}
    else:
        print("WARNING: no --proxy set; Camoufox and curl_cffi will use the "
              "local IP. Use the SAME proxy for both to avoid an IP mismatch "
              "in the sentinel token.", file=sys.stderr)
    captcha = YesCaptchaClient(yescaptcha_key) if yescaptcha_key else None
    tokens = CamoufoxTokenGenerator(profile=profile, proxy=proxy,
                                    headless=headless, insecure=insecure)
    try:
        relay = ChatGPTRelay(acct, reader, session=session, profile=profile,
                             tokens=tokens, captcha=captcha)
        result = relay.run()
    finally:
        tokens.close()
    return {
        "email": acct.email,
        "device_id": result.device_id,
        "session": result.session_json,
        "steps": result.steps,
    }


def main(argv=None):
    p = argparse.ArgumentParser(prog="chatgpt_camoufox")
    p.add_argument("line", nargs="?", help="email|password|api")
    p.add_argument("--file", help="file with one email|password|api per line")
    p.add_argument("--locale", default="vi-VN")
    p.add_argument("--firefox-major", type=int, default=135)
    p.add_argument("--platform", default="Windows",
                   choices=["Windows", "macOS", "Linux"])
    p.add_argument("--yescaptcha-key", default=os.environ.get("YESCAPTCHA_KEY"))
    p.add_argument("--proxy", default=None)
    p.add_argument("--no-headless", action="store_true")
    p.add_argument("--insecure", "-k", action="store_true",
                   help="disable TLS verification (for local MITM proxies like "
                        "Clash/mitmproxy that re-sign certs)")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="print each HTTP step to stderr")
    args = p.parse_args(argv)

    lines = []
    if args.file:
        with open(args.file) as f:
            lines = [ln.strip() for ln in f if ln.strip() and "|" in ln]
    elif args.line:
        lines = [args.line]
    else:
        p.error("provide a line or --file")

    for line in lines:
        try:
            out = run_line(line, locale=args.locale,
                           firefox_major=args.firefox_major,
                           platform=args.platform,
                           yescaptcha_key=args.yescaptcha_key,
                           proxy=args.proxy, headless=not args.no_headless,
                           insecure=args.insecure)
            if args.verbose:
                print("--- steps ---", file=sys.stderr)
                for s in out.get("steps", []):
                    print("  " + s, file=sys.stderr)
            print(json.dumps(out, ensure_ascii=False))
        except Exception as e:  # noqa: BLE001 - per-account failure, continue
            print(json.dumps({"line": line.split("|")[0], "error": str(e)}))
            continue
    return 0


if __name__ == "__main__":
    sys.exit(main())
