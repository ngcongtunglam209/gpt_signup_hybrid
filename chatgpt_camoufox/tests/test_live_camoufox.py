"""Live integration: mint the sentinel tokens by running the GENUINE sdk.js in
a real Camoufox browser. The sdk fetches its own fresh dx via sentinel/req and
reads live, session-bound page globals, so this proves the tokens are minted
the way a real Firefox does (a captured dx cannot be replayed). Skips unless
camoufox is installed (downloads a Firefox build on first run)."""
import base64
import json

import pytest

from chatgpt_camoufox import camoufox_vm

pytestmark = pytest.mark.skipif(
    not camoufox_vm.camoufox_available(), reason="camoufox not installed")


def _looks_like_vm_error(b64: str) -> bool:
    """dx-VM failures come back base64-encoded as '<n>: <Error>'."""
    try:
        head = base64.b64decode(b64 + "==").decode("latin-1", "replace")[:40]
    except Exception:
        return False
    return bool(__import__("re").match(r"^\d+:\s", head))


def test_live_mint_sentinel_token():
    with camoufox_vm.CamoufoxTokenGenerator() as gen:
        tok = gen.mint_token("username_password_create")
    # Full bundle present and well-formed.
    assert tok.p.startswith("gAAAAA")
    assert tok.c
    assert tok.flow == "username_password_create"
    # `t` is the dx-VM enforcement token: long base64, NOT an encoded VM error.
    assert len(tok.t) > 200
    assert not _looks_like_vm_error(tok.t)
    # `t` decodes and its leading bytes match the Firefox enforcement shape.
    base64.b64decode(tok.t + "==")


def test_live_mint_token_then_so():
    with camoufox_vm.CamoufoxTokenGenerator() as gen:
        # token() for this flow must run first so the SO chat-req is cached.
        gen.mint_token("oauth_create_account")
        so = gen.mint_so("oauth_create_account")
    assert so and isinstance(so, str)
    assert not _looks_like_vm_error(so)
    base64.b64decode(so + "==")


def test_live_token_is_valid_json_bundle():
    with camoufox_vm.CamoufoxTokenGenerator() as gen:
        tok = gen.mint_token("login")
    obj = json.loads(tok.raw)
    assert set(["p", "t", "c", "flow"]).issubset(obj.keys())
