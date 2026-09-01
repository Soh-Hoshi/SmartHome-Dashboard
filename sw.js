// SmartHome Dashboard PWA Service Worker
// Dedicated Scope: /dashboard

const CACHE_NAME = 'smarthome-dashboard-v4';
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
  // LiveReload や POST リクエスト、APIはネットワークをダイレクト通過
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
        // オフライン時はキャッシュから返す
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
// WebPush & 通知アクションハンドラー (消し忘れ通知 ＆ バックグラウンド一括消灯)
// =======================================================================

self.addEventListener('push', (event) => {
  let data = {
    title: 'スマートホーム',
    body: '通知を受信しました。',
    icon: '/dashboard/icon-192.png',
    badge: '/dashboard/icon-192.png',
    tag: 'smarthome-alert',
    actions: []
  };

  if (event.data) {
    try {
      data = Object.assign(data, event.data.json());
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/dashboard/icon-192.png',
    badge: data.badge || '/dashboard/icon-192.png',
    tag: data.tag || 'smarthome-notification',
    renotify: true,
    requireInteraction: true,
    data: data.data || { url: '/dashboard' },
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
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
