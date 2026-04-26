/**
 * O.D.I.A. Service Worker
 *
 * Strategy:
 *  - App shell (HTML/CSS/JS) is cached on install and served from cache first.
 *  - API calls (/api/*) are NEVER cached — privacy protection for document data.
 *  - Navigation requests fall back to cached shell when offline.
 *  - A broadcast message is sent to open tabs when going offline.
 */

// v2.8.0 — bumped to v4 for the mineral-palette refresh: globals.css is
// substantially rewritten and the texture WebPs in /public/textures/ are
// new static assets. Texture files are NOT pre-cached (16 files × ~30KB
// would balloon the install payload) — they fall through to the existing
// cache-first static-asset handler at line 102, getting cached on first
// request and served from cache thereafter, which is exactly the
// stale-while-revalidate behaviour the handoff calls for.
const CACHE_NAME = 'odia-shell-v4';

// App shell paths to pre-cache
const SHELL_PATHS = [
  '/',
  '/upload',
  '/results',
  '/documents',
  '/settings',
  '/manifest.json',
  // v2.7.9 — Oraculus intro sequence. Cached so the gemstone boot
  // animation plays even on first launch under flaky connectivity.
  '/intro/index.html',
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
