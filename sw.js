// SmartHome Dashboard PWA Service Worker
// Dedicated Scope: /dashboard

const CACHE_NAME = 'smarthome-dashboard-v9';
const STATIC_ASSETS = [
  '/dashboard',
  '/dashboard/',
  '/dashboard/manifest.json',
  '/dashboard/icon-192.png',
  '/dashboard/icon-512.png',
  '/dashboard/icon.svg',
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './icon.svg'
];

// インストール時に初期キャッシュ
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[SW Install Cache Warning]', err);
      });
    })
  );
});

// アクティベーション時に古いキャッシュを即時パージ
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// フェッチ処理 (Network First: 常に最新コード・APIデータを優先)
self.addEventListener('fetch', (event) => {
  if (
    event.request.method !== 'GET' ||
    event.request.url.includes('/__livereload__') ||
    event.request.url.includes('/api/')
  ) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          if (event.request.headers.get('accept')?.includes('text/html')) {
            return caches.match('/dashboard') || caches.match('./index.html');
          }
        });
      })
  );
});

// PWA 通知は廃止（Android ネイティブアプリ NovaAssist に一本化）

