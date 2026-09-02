// SmartHome Dashboard PWA Service Worker
// Dedicated Scope: /dashboard

const CACHE_NAME = 'smarthome-dashboard-v6';
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

// =======================================================================
// WebPush & 通知アクションハンドラー (Android Chrome 完全準拠)
// =======================================================================

self.addEventListener('push', (event) => {
  let title = 'お出かけですか？';
  let body = '照明・空調が稼働したままです。消灯しますか？';
  let actions = [
    { action: 'run_leaving', title: '🚪 いってきます（全消灯）' },
    { action: 'dismiss', title: 'そのまま' }
  ];
  let customData = { url: '/dashboard', scene: 'leaving' };

  if (event.data) {
    try {
      const payload = event.data.json();
      if (payload.title) title = payload.title;
      if (payload.body) body = payload.body;
      if (payload.actions && payload.actions.length > 0) actions = payload.actions;
      if (payload.data) customData = payload.data;
    } catch (e) {
      const text = event.data.text();
      if (text) body = text;
    }
  }

  const notifPromise = self.registration.showNotification(title, {
    body: body,
    tag: 'away-device-warning',
    renotify: true,
    requireInteraction: true,
    actions: actions,
    data: customData
  }).catch(() => {
    // actions が拒否された場合のフォールバック（シンプルな通知）
    return self.registration.showNotification(title, {
      body: body,
      tag: 'away-device-warning',
      renotify: true,
      data: customData
    });
  });

  event.waitUntil(notifPromise);
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const action = event.action;
  const notifData = event.notification.data || {};
  const basePath = self.location.pathname.startsWith('/dashboard') ? '/dashboard' : '';

  // 1. 「いってきます（全消灯）」ボタンがタップされた場合
  if (action === 'run_leaving') {
    event.waitUntil(
      fetch(basePath + '/api/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'いってきます' })
      })
      .then((res) => res.json())
      .then((data) => {
        return self.registration.showNotification('✅ いってきます実行完了', {
          body: data.message || 'すべての照明と空調を停止しました。',
          icon: '/dashboard/icon-192.png',
          badge: '/dashboard/icon-192.png',
          tag: 'scene-leaving-complete',
          data: { url: basePath || '/' }
        });
      })
      .catch((err) => {
        console.error('[SW Action Error]', err);
      })
    );
    return;
  }

  // 2. 「そのまま」ボタンがタップされた場合
  if (action === 'dismiss') {
    return;
  }

  // 3. 通知本体がタップされた場合はダッシュボードを開く / フォーカスする
  const targetUrl = (notifData && notifData.url) ? notifData.url : (basePath || '/');
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url.includes(basePath || '/dashboard') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
