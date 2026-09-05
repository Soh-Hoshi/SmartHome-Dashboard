// SmartHome Dashboard PWA Service Worker
// Dedicated Scope: /dashboard

const CACHE_NAME = 'smarthome-dashboard-v19';
const STATIC_ASSETS = [
  '/dashboard',
  '/dashboard/',
  '/dashboard/manifest.json',
  '/dashboard/icon-192.png',
  '/dashboard/icon-512.png',
  '/dashboard/icon-maskable-192.png',
  '/dashboard/icon-maskable-512.png',
  '/dashboard/icon.svg',
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-192.png',
  './icon-maskable-512.png',
  './icon.svg'
];

// インストール時に初期キャッシュ＆即座に待機状態をスキップ
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

// アクティベーション時に古いキャッシュ（v10等）を即時全削除し、全クライアントを即時制御
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => {
          console.log('[SW Activate] Deleting old cache:', key);
          return caches.delete(key);
        })
      );
    }).then(() => self.clients.claim())
  );
});

// フェッチ処理 (Network First: 常に最新コード・APIデータを最優先)
self.addEventListener('fetch', (event) => {
  if (
    event.request.method !== 'GET' ||
    event.request.url.includes('/__livereload__') ||
    event.request.url.includes('/api/')
  ) {
    return;
  }

  // HTML / ナビゲーションリクエストはキャッシュ無視で常にネットワークへ問い合わせ
  const isHtml = event.request.mode === 'navigate' || event.request.headers.get('accept')?.includes('text/html');

  if (isHtml) {
    event.respondWith(
      fetch(event.request, { cache: 'no-cache' })
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
          // オフライン時のみキャッシュへフォールバック
          return caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || caches.match('/dashboard') || caches.match('./index.html');
          });
        })
    );
    return;
  }

  // 静的アセット (画像・アイコン等)
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
        return caches.match(event.request);
      })
  );
});

