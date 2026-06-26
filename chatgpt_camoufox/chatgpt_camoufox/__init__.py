"""ChatGPT auth relay — Firefox/Camoufox edition.

Reverses the browser register/login flow and reproduces EVERY client-side field
with a formula (Firefox-shaped), instead of running a headless DOM. The only two
fields that cannot be reproduced in pure Python — the sentinel enforcement token
`t` and the session-observer token `so` — are minted by running the genuine
sentinel sdk.js inside a real Camoufox (Firefox) browser.

Flow reversed from a real mitmproxy capture (reports/chatgpt-camoufox):
    GET  / (load)                                         (Cloudflare clearance)
    GET  chatgpt.com/api/auth/csrf
    POST chatgpt.com/api/auth/signin/openai               -> authorize url
    GET  auth.openai.com/api/accounts/authorize    (403 Cloudflare)
    POST auth.openai.com/api/accounts/authorize    (302)  (cf challenge answer)
    GET  auth.openai.com/api/accounts/authorize    (302)
      POST sentinel/req (text/plain, in iframe)           -> requirements
    POST auth.openai.com/api/accounts/user/register       + openai-sentinel-token
    GET  auth.openai.com/api/accounts/email-otp/send
        [read OTP over HTTP]
    POST auth.openai.com/api/accounts/email-otp/validate
      POST sentinel/req                                   -> requirements (+so)
    POST auth.openai.com/api/accounts/create_account      + sentinel + so token
    GET  chatgpt.com/api/auth/callback/openai      (302)
    GET  chatgpt.com/api/auth/session                     -> JSON
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
