"""OpenAI Sentinel token assembly + requirements parsing (Firefox flavour).

The proof-of-work array and the dx-VM enforcement token are NOT built here: the
genuine sdk.js mints the whole `{p,t,c}` bundle live inside Camoufox (see
camoufox_vm.py). This module only:

  * serialises the `openai-sentinel-token` / `openai-sentinel-so-token` header
    values around the sdk-minted parts, stamping our device id + flow, and
  * parses a raw sentinel/req response into a typed struct (used by callers that
    inspect requirements, e.g. tests / diagnostics).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

ASYNC_PREFIX = "gAAAAAC"     # async (sentinel/req body) answers
SYNC_PREFIX = "gAAAAAB"      # sync (header) answers


@dataclass
class SentinelRequirements:
    seed: str
    difficulty: str
    token: str            # server "token" -> becomes `c`
    turnstile_dx: str | None = None
    so_required: bool = False
    collector_dx: str | None = None
    snapshot_dx: str | None = None
    persona: str | None = None
    expire_at: int | None = None

    @property
    def has_so(self) -> bool:
        return bool(self.so_required and self.snapshot_dx)


def parse_requirements(resp_json: dict) -> SentinelRequirements:
    pw = resp_json.get("proofofwork") or {}
    ts = resp_json.get("turnstile") or {}
    so = resp_json.get("so") or {}
    return SentinelRequirements(
        seed=pw.get("seed", ""),
        difficulty=pw.get("difficulty", ""),
        token=resp_json.get("token", ""),
        turnstile_dx=ts.get("dx"),
        so_required=bool(so.get("required")),
        collector_dx=so.get("collector_dx"),
        snapshot_dx=so.get("snapshot_dx"),
        persona=resp_json.get("persona"),
        expire_at=resp_json.get("expire_at"),
    )


def build_sentinel_token(p: str, enforcement_t: str, c: str,
                         device_id: str, flow: str) -> str:
    """Serialize the openai-sentinel-token header value (compact JSON)."""
    return json.dumps(
        {"p": p, "t": enforcement_t, "c": c, "id": device_id, "flow": flow},
        separators=(",", ":"), ensure_ascii=False,
    )


def build_so_token(so: str, c: str, device_id: str, flow: str) -> str:
    """Serialize the openai-sentinel-so-token header (sent only on create_account)."""
    return json.dumps(
        {"so": so, "c": c, "id": device_id, "flow": flow},
        separators=(",", ":"), ensure_ascii=False,
    )
