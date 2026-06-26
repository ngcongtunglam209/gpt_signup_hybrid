// In-page bridge for a REAL Camoufox (Firefox) tab loaded on the sentinel
// origin (frame.html). This snippet is concatenated AFTER the genuine sentinel
// sdk.js source (with its top-level `var SentinelSDK=` rewritten to
// `window.SentinelSDK=`) and injected as a single page-world <script>. It runs
// the sdk in the page's own main world and exposes a postMessage bridge that
// the Python side drives from Playwright's isolated world.
//
// Why the page world + postMessage:
//   * The dx-VM reads live, session-bound page state (loaderData, root,
//     clientBootstrap, cfConnectingIp, cfIpCity, userRegion,
//     cfIp{Latitude,Longitude}, ...). A dx captured in another session is
//     bound to THAT session's globals and can never be replayed -- tokens must
//     be minted live by the sdk itself, which fetches its own fresh dx via
//     sentinel/req.
//   * Running the sdk from Playwright's isolated world trips Camoufox's Xray
//     sandbox ("Accessing TypedArray data over Xrays is forbidden"), so the
//     sdk must execute in the page's own main world.
//
// Protocol (isolated world -> page world):
//   postMessage({__sreq:true, id, kind:"token"|"so", flow})
// Reply (page world -> isolated world):
//   postMessage({__sres:id, ok, value, err})
//
//   kind "token" -> value is the JSON string {p,t,c,flow} from SentinelSDK.token(flow)
//   kind "so"    -> value is the {so:...} object from SentinelSDK.sessionObserverToken(flow)
//                   (call "token" for the same flow first so the SO chat-req is cached)

(function () {
  if (!window.SentinelSDK || !window.SentinelSDK.token) {
    var fail = document.createElement("div");
    fail.id = "__sentinel_bridge_error";
    fail.textContent = "SentinelSDK not exposed";
    document.documentElement.appendChild(fail);
    return;
  }

  window.addEventListener("message", async function (ev) {
    var d = ev.data;
    if (!d || !d.__sreq) return;
    var out = { __sres: d.id };
    try {
      if (d.kind === "token") {
        out.value = await window.SentinelSDK.token(d.flow);
      } else if (d.kind === "so") {
        out.value = await window.SentinelSDK.sessionObserverToken(d.flow);
      } else {
        throw new Error("unknown kind " + d.kind);
      }
      out.ok = true;
    } catch (e) {
      out.ok = false;
      out.err = String((e && e.message) || e);
    }
    window.postMessage(out, "*");
  });

  var ready = document.createElement("div");
  ready.id = "__sentinel_bridge_ready";
  document.documentElement.appendChild(ready);
})();
