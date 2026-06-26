"""YesCaptcha client for Cloudflare Turnstile / cf_clearance.

Used only when the relay hits an anti-bot challenge (the authorize endpoint
returns a Cloudflare 403 in the capture). The HTTP layer is injected so tests
run without network.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

DEFAULT_ENDPOINT = "https://api.yescaptcha.com"


class CaptchaError(RuntimeError):
    pass


@dataclass
class YesCaptchaClient:
    client_key: str
    endpoint: str = DEFAULT_ENDPOINT
    session: requests.Session | None = None
    poll_interval: float = 3.0
    timeout: float = 180.0

    def __post_init__(self):
        self.session = self.session or requests.Session()

    def _post(self, path: str, payload: dict) -> dict:
        resp = self.session.post(f"{self.endpoint}{path}", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def create_task(self, task: dict) -> str:
        data = self._post("/createTask",
                          {"clientKey": self.client_key, "task": task})
        if data.get("errorId"):
            raise CaptchaError(
                f"createTask error: {data.get('errorCode')} {data.get('errorDescription')}")
        task_id = data.get("taskId")
        if not task_id:
            raise CaptchaError(f"no taskId in response: {data}")
        return task_id

    def get_result(self, task_id: str) -> dict:
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            data = self._post("/getTaskResult",
                              {"clientKey": self.client_key, "taskId": task_id})
            if data.get("errorId"):
                raise CaptchaError(
                    f"getTaskResult error: {data.get('errorCode')} "
                    f"{data.get('errorDescription')}")
            if data.get("status") == "ready":
                return data.get("solution", {})
            time.sleep(self.poll_interval)
        raise CaptchaError("captcha solve timed out")

    def solve_turnstile(self, website_url: str, website_key: str,
                        action: str | None = None, cdata: str | None = None) -> str:
        task = {"type": "TurnstileTaskProxyless",
                "websiteURL": website_url, "websiteKey": website_key}
        if action:
            task["action"] = action
        if cdata:
            task["cdata"] = cdata
        solution = self.get_result(self.create_task(task))
        token = solution.get("token") or solution.get("gRecaptchaResponse")
        if not token:
            raise CaptchaError(f"no turnstile token in solution: {solution}")
        return token

    def solve_cloudflare(self, website_url: str, proxy: str | None = None,
                        user_agent: str | None = None) -> dict:
        task = {"type": "CloudFlareTaskS5" if proxy else "CloudFlareTaskS2",
                "websiteURL": website_url}
        if proxy:
            task["proxy"] = proxy
        if user_agent:
            task["userAgent"] = user_agent
        solution = self.get_result(self.create_task(task))
        cf = (solution.get("cookies", {}).get("cf_clearance")
              or solution.get("cf_clearance"))
        if not cf:
            raise CaptchaError(f"no cf_clearance in solution: {solution}")
        return {"cf_clearance": cf,
                "user_agent": solution.get("user_agent", user_agent)}
