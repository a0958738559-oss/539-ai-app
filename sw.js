

const CACHE_NAME = "539-ai-v2";

const FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon.svg",
  "./icon-192.png",
  "./icon-512.png",
  "./history.csv"
];

// 安裝時預先儲存離線檔案
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(FILES))
      .then(() => self.skipWaiting())
  );
});

// 啟用新版並清除舊快取
self.addEventListener("activate", event => {
  event.waitUntil(
    Promise.all([
      caches.keys().then(keys =>
        Promise.all(
          keys.filter(key =>
            key.startsWith("539-ai-") &&
            key !== CACHE_NAME
          ).map(key => caches.delete(key))
        )
      ),
      self.clients.claim()
    ])
  );
});

// 網頁與歷史資料離線讀取
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  const isHistory = url.pathname.endsWith("/history.csv");

  if (isHistory) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response.ok) {
            const copy = response.clone();
            event.waitUntil(
              caches.open(CACHE_NAME).then(cache =>
                cache.put(event.request, copy)
              )
            );
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.match("./index.html")
      )
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cached =>
      cached || fetch(event.request)
    )
  );
});
