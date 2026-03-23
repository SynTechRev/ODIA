/**
 * O.D.I.A. Service Worker
 *
 * Strategy:
 *  - App shell (HTML/CSS/JS) is cached on install and served from cache first.
 *  - API calls (/api/*) are NEVER cached — privacy protection for document data.
 *  - Navigation requests fall back to cached shell when offline.
 *  - A broadcast message is sent to open tabs when going offline.
 */

const CACHE_NAME = 'odia-shell-v1';

// App shell paths to pre-cache
const SHELL_PATHS = [
  '/',
  '/upload',
  '/results',
  '/documents',
  '/settings',
  '/manifest.json',
];

// ---------------------------------------------------------------------------
// Install — pre-cache the app shell
// ---------------------------------------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Use individual adds so one failure doesn't block all caching
      return Promise.allSettled(
        SHELL_PATHS.map((path) => cache.add(path).catch(() => null))
      );
    }).then(() => self.skipWaiting())
  );
});

// ---------------------------------------------------------------------------
// Activate — clean up old caches
// ---------------------------------------------------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ---------------------------------------------------------------------------
// Fetch — cache-first for shell, network-only for API
// ---------------------------------------------------------------------------
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Never cache: API calls, uploads, non-GET requests
  if (
    url.pathname.startsWith('/api/') ||
    event.request.method !== 'GET' ||
    url.protocol === 'chrome-extension:'
  ) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      // Try network first for HTML navigation requests (keeps pages fresh)
      const isNavigation =
        event.request.mode === 'navigate' ||
        event.request.headers.get('accept')?.includes('text/html');

      if (isNavigation) {
        return fetch(event.request)
          .then((response) => {
            if (response.ok) {
              const clone = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
            }
            return response;
          })
          .catch(() => {
            // Offline: notify tabs, serve cached version
            self.clients.matchAll().then((clients) => {
              clients.forEach((client) =>
                client.postMessage({ type: 'OFFLINE' })
              );
            });
            return cached || new Response(
              '<html><body><h2>You are offline</h2><p>Cached reports are available in previously visited pages.</p></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          });
      }

      // Static assets: cache-first
      return cached || fetch(event.request).then((response) => {
        if (response.ok && response.type !== 'opaque') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});
