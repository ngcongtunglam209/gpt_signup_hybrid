"""OTP retrieval.

Two modes, chosen by the 3rd field of the `email|password|api` line:
  * an http(s) URL  -> `HttpOTPReader` polls a mailbox API for the latest mail.
  * "manual" / ""   -> `ManualOTPReader` prompts the operator to paste the code
                       (handy for a quick end-to-end run without a mail API).
The 6-digit OpenAI code is extracted in both cases.
"""
from __future__ import annotations

import re
import time
from typing import Callable

import requests

# OpenAI OTP mails contain a standalone 6-digit code.
_CODE_RE = re.compile(r"\b(\d{6})\b")


def extract_code(text: str) -> str | None:
    if not text:
        return None
    m = _CODE_RE.search(text)
    return m.group(1) if m else None


class HttpOTPReader:
    """Generic HTTP mailbox API reader. `api` returns the latest mail (json/raw)."""

    def __init__(self, api: str, session: requests.Session | None = None):
        self.api = api
        self.session = session or requests.Session()

    def _fetch_text(self) -> str:
        resp = self.session.get(self.api, timeout=30)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        if "json" in ctype:
            data = resp.json()
            for key in ("text", "body", "html", "subject", "content"):
                if isinstance(data, dict) and data.get(key):
                    return str(data[key])
            return str(data)
        return resp.text

    def get_code(self, timeout: float = 120.0, poll: float = 5.0) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            code = extract_code(self._fetch_text())
            if code:
                return code
            time.sleep(poll)
        raise TimeoutError("OTP code not received in time")


class ManualOTPReader:
    """Interactive reader: prompt the operator to paste the OTP mail or code.

    `prompt` is injectable for tests (defaults to `input`). It re-prompts until
    a 6-digit code is found or `max_tries` is exhausted.
    """

    def __init__(self, prompt: Callable[[str], str] | None = None,
                 max_tries: int = 5):
        self.prompt = prompt or input
        self.max_tries = max_tries

    def get_code(self, timeout: float = 0.0, poll: float = 0.0) -> str:
        msg = ("\n>>> Nhập mã OTP (6 số) từ email ChatGPT vừa nhận "
               "(dán cả dòng mail cũng được): ")
        for _ in range(self.max_tries):
            answer = self.prompt(msg)
            code = extract_code(answer or "")
            if code:
                return code
            print("  Không thấy mã 6 số, thử lại...")
        raise ValueError("OTP không hợp lệ sau nhiều lần thử")


def build_reader(api: str) -> "HttpOTPReader | ManualOTPReader":
    if api in ("", "manual", "prompt", "stdin"):
        return ManualOTPReader()
    if not (api.startswith("http://") or api.startswith("https://")):
        raise ValueError("api must be an http(s) mailbox URL, or 'manual'")
    return HttpOTPReader(api)
