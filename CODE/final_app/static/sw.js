const CACHE_NAME = "echogenesis-v2";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys()
    .then((names) => Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))))
    .then(() => self.clients.claim())
));

const networkFirst = (req) => fetch(req)
  .then((res) => {
    if (res.ok) caches.open(CACHE_NAME).then((c) => c.put(req, res.clone()));
    return res;
  })
  .catch(() => caches.match(req));

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;        // speak, log, check-in etc. always need the live server
  const url = new URL(e.request.url);

  // Real-recording phrase audio: cache-first, so it plays with zero network once heard.
  if (url.pathname.startsWith("/quick_phrase_audio/")) {
    e.respondWith(caches.open(CACHE_NAME).then((cache) =>
      cache.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
        if (res.ok) cache.put(e.request, res.clone());
        return res;
      }))
    ));
    return;
  }

  // App shell + phrase list: network-first, fall back to the last good copy when offline.
  if (url.pathname === "/" || url.pathname.startsWith("/static/") ||
      url.pathname === "/quick_phrases" || url.pathname === "/voices") {
    e.respondWith(networkFirst(e.request));
  }
});
