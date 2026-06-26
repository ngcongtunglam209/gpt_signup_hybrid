"""Firefox per-endpoint headers must match the capture shape (no sec-ch-ua,
te:trailers, sentinel text/plain in iframe)."""
from chatgpt_camoufox import fingerprint, headers

P = fingerprint.DEFAULT_PROFILE


def test_no_client_hints_anywhere():
    for b in (headers.csrf, headers.signin, headers.authorize_get,
              headers.register, headers.otp_send, headers.otp_validate,
              headers.create_account, headers.callback, headers.session):
        h = b(P)
        assert not any(k.lower().startswith("sec-ch-ua") for k in h)


# Golden Firefox header order per endpoint, taken verbatim from
# reports/chatgpt-camoufox. The client sends curl_cffi with
# default_headers=False so the builder's dict order is the wire order. The
# `Cookie` slot is present (value None) at the Firefox position; the client
# fills it per request. Token slots (openai-sentinel[-so]-token) likewise.
_GOLDEN_ORDER = {
    "csrf": ["user-agent", "accept", "accept-language", "accept-encoding",
             "referer", "content-type", "cookie", "sec-fetch-dest",
             "sec-fetch-mode", "sec-fetch-site", "priority", "te"],
    "signin": ["user-agent", "accept", "accept-language", "accept-encoding",
               "referer", "content-type", "origin", "cookie", "sec-fetch-dest",
               "sec-fetch-mode", "sec-fetch-site", "priority", "te"],
    "authorize_get": ["user-agent", "accept", "accept-language",
                      "accept-encoding", "referer", "cookie",
                      "upgrade-insecure-requests", "sec-fetch-dest",
                      "sec-fetch-mode", "sec-fetch-site", "sec-fetch-user",
                      "priority", "te"],
    "register": ["user-agent", "accept", "accept-language", "accept-encoding",
                 "referer", "content-type", "openai-sentinel-token",
                 "traceparent", "tracestate", "x-datadog-origin",
                 "x-datadog-parent-id", "x-datadog-sampling-priority",
                 "x-datadog-trace-id", "origin", "cookie", "sec-fetch-dest",
                 "sec-fetch-mode", "sec-fetch-site", "priority", "te"],
    "otp_send": ["user-agent", "accept", "accept-language", "accept-encoding",
                 "referer", "cookie", "upgrade-insecure-requests",
                 "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site",
                 "sec-fetch-user", "priority", "te"],
    "otp_validate": ["user-agent", "accept", "accept-language",
                     "accept-encoding", "referer", "content-type",
                     "traceparent", "tracestate", "x-datadog-origin",
                     "x-datadog-parent-id", "x-datadog-sampling-priority",
                     "x-datadog-trace-id", "origin", "cookie", "sec-fetch-dest",
                     "sec-fetch-mode", "sec-fetch-site", "priority", "te"],
    "create_account": ["user-agent", "accept", "accept-language",
                       "accept-encoding", "referer", "content-type",
                       "openai-sentinel-so-token", "openai-sentinel-token",
                       "traceparent", "tracestate", "x-datadog-origin",
                       "x-datadog-parent-id", "x-datadog-sampling-priority",
                       "x-datadog-trace-id", "origin", "cookie",
                       "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site",
                       "priority", "te"],
    "callback": ["user-agent", "accept", "accept-language", "accept-encoding",
                 "referer", "cookie", "upgrade-insecure-requests",
                 "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site",
                 "priority", "te"],
    "session": ["user-agent", "accept", "accept-language", "accept-encoding",
                "cookie", "upgrade-insecure-requests", "sec-fetch-dest",
                "sec-fetch-mode", "sec-fetch-site", "sec-fetch-user",
                "priority", "te"],
}


def test_header_order_matches_golden_capture():
    builders = {
        "csrf": headers.csrf(P), "signin": headers.signin(P),
        "authorize_get": headers.authorize_get(P), "register": headers.register(P),
        "otp_send": headers.otp_send(P), "otp_validate": headers.otp_validate(P),
        "create_account": headers.create_account(P),
        "callback": headers.callback(P), "session": headers.session(P),
    }
    for name, built in builders.items():
        got = [k.lower() for k in built]  # includes the None-valued Cookie slot
        assert got == _GOLDEN_ORDER[name], (
            f"{name} order mismatch:\n got   ={got}\n golden={_GOLDEN_ORDER[name]}")


def test_cookie_slot_present_but_empty_in_builders():
    # Every builder pre-places a Cookie slot (value None) so the client can fill
    # it in the Firefox position; until filled it must be None (curl drops it).
    for b in (headers.csrf, headers.register, headers.session,
              headers.authorize_get, headers.create_account):
        h = b(P)
        assert "Cookie" in h and h["Cookie"] is None


def test_te_trailers_everywhere():
    for b in (headers.csrf, headers.signin, headers.register,
              headers.otp_validate, headers.create_account, headers.session):
        assert b(P)["te"] == "trailers"


def test_csrf_headers():
    h = headers.csrf(P)
    assert h["Sec-Fetch-Site"] == "same-origin"
    assert h["Sec-Fetch-Mode"] == "cors"
    assert h["Content-Type"] == "application/json"
    assert h["priority"] == "u=4"
    assert h["Accept-Language"].endswith("q=0.5")


def test_signin_origin_and_form():
    h = headers.signin(P)
    assert h["Origin"] == "https://chatgpt.com"
    assert h["Content-Type"] == "application/x-www-form-urlencoded"


def test_authorize_get_is_cross_site_navigation():
    h = headers.authorize_get(P)
    assert h["Sec-Fetch-Site"] == "cross-site"
    assert h["Sec-Fetch-Mode"] == "navigate"
    assert h["priority"] == "u=0, i"


def test_sentinel_req_is_text_plain_from_iframe():
    frame = "https://sentinel.openai.com/backend-api/sentinel/frame.html?sv=x"
    h = headers.sentinel_req(P, frame)
    assert h["Content-Type"] == "text/plain;charset=UTF-8"
    assert h["Origin"] == "https://sentinel.openai.com"
    assert h["Referer"] == frame
    assert h["Sec-Fetch-Site"] == "same-origin"


def test_register_headers():
    h = headers.register(P)
    assert h["Origin"] == "https://auth.openai.com"
    assert h["Accept"] == "application/json"
    assert h["Referer"] == "https://auth.openai.com/create-account/password"


def test_xhr_drops_curl_navigation_defaults():
    # Real browsers never send Sec-Fetch-User / Upgrade-Insecure-Requests on an
    # XHR. curl_cffi injects them by default, so the builder must explicitly map
    # them to None (which removes the leaked default over the wire).
    for b in (headers.csrf, headers.signin, headers.register,
              headers.otp_validate, headers.create_account):
        h = b(P)
        assert h.get("Sec-Fetch-User") is None
        assert h.get("Upgrade-Insecure-Requests") is None
    # sentinel_req takes a frame referer arg
    sh = headers.sentinel_req(P, f"{headers.SENTINEL}/backend-api/sentinel/frame.html")
    assert sh.get("Sec-Fetch-User") is None
    assert sh.get("Upgrade-Insecure-Requests") is None


def test_navigations_keep_navigation_headers():
    # Navigations legitimately carry these (matches golden capture).
    for b in (headers.authorize_get, headers.otp_send, headers.session):
        h = b(P)
        assert h["Upgrade-Insecure-Requests"] == "1"


_RUM_KEYS = ("traceparent", "tracestate", "x-datadog-origin",
             "x-datadog-parent-id", "x-datadog-sampling-priority",
             "x-datadog-trace-id")


def test_datadog_rum_on_auth_posts():
    for b in (headers.register, headers.otp_validate, headers.create_account):
        h = b(P)
        for k in _RUM_KEYS:
            assert k in h, f"{b.__name__} missing {k}"
        assert h["tracestate"] == "dd=s:1;o:rum"
        assert h["x-datadog-origin"] == "rum"
        assert h["x-datadog-sampling-priority"] == "1"


def test_datadog_rum_absent_on_non_rum_requests():
    for b in (headers.csrf, headers.signin, headers.authorize_get,
              headers.otp_send, headers.callback, headers.session):
        h = b(P)
        assert "traceparent" not in h
        assert "x-datadog-trace-id" not in h


def test_datadog_traceparent_matches_datadog_ids():
    # traceparent low-64 hex must equal x-datadog-trace-id (decimal) and the
    # span hex must equal x-datadog-parent-id, with the high 64 trace bits zero
    # -- exactly the golden-capture relationship.
    h = headers.register(P)
    trace_hex = h["traceparent"].split("-")[1]
    span_hex = h["traceparent"].split("-")[2]
    assert trace_hex[:16] == "0" * 16
    assert int(trace_hex[16:], 16) == int(h["x-datadog-trace-id"])
    assert int(span_hex, 16) == int(h["x-datadog-parent-id"])


def test_datadog_rum_ids_are_random_per_call():
    assert (headers.register(P)["x-datadog-trace-id"]
            != headers.register(P)["x-datadog-trace-id"])


def test_session_is_top_level_nav_no_referer():
    h = headers.session(P)
    assert h["Sec-Fetch-Site"] == "none"
    assert "Referer" not in h
    assert h["Upgrade-Insecure-Requests"] == "1"


def test_user_agent_consistent():
    for b in (headers.csrf, headers.register, headers.session):
        assert b(P)["User-Agent"] == P.user_agent
