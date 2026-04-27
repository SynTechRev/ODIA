/**
 * O.D.I.A. Service Worker
 *
 * Strategy:
 *  - App shell (HTML/CSS/JS) is pre-cached on install and served from
 *    `odia-shell-v5` cache.
 *  - Static runtime assets (Next bundles, icons, textures) live in a
 *    separate `odia-static-v1` cache with a stale-while-revalidate
 *    strategy — first request hits the network, subsequent requests
 *    serve from cache while the SW silently re-fetches in the
 *    background. Splitting this from the shell cache keeps the shell
 *    cache small and lets us evict the two independently.
 *  - API calls (/api/*) are NEVER cached — privacy protection for
 *    audit findings, uploaded documents, and authenticated state.
 *    /api/uploads/* (document attachments) are covered by the same
 *    blanket /api/ exclusion.
 *  - Navigation requests are network-first; offline falls back to the
 *    cached shell + an OFFLINE broadcast to open tabs.
 */

// v2.9.0 B4 — split caches:
//   - odia-shell-v5: HTML pages + manifest + intro (pre-cached on install).
//     Bumped from v4 because the activate handler must evict the old shell
//     to pick up any HTML/manifest changes shipped in v2.9.0 (mobile upload
//     card stack, install-prompt entry path).
//   - odia-static-v1: runtime cache for /_next/static/*, /icons/*,
//     /textures/*. New cache; safe to start at v1.
const SHELL_CACHE = 'odia-shell-v5';
const STATIC_CACHE = 'odia-static-v1';
const ACTIVE_CACHES = new Set([SHELL_CACHE, STATIC_CACHE]);

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

// Pathname predicates for the runtime static cache. Kept as a function so
// the matcher can short-circuit cheaply per fetch.
function isRuntimeStatic(pathname) {
  return (
    pathname.startsWith('/_next/static/') ||
    pathname.startsWith('/icons/') ||
    pathname.startsWith('/textures/')
  );
}

// ---------------------------------------------------------------------------
// Install — pre-cache the app shell
// ---------------------------------------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => {
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
        keys.filter((k) => !ACTIVE_CACHES.has(k)).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ---------------------------------------------------------------------------
// Fetch — split routing: API → never, navigation → network-first,
// runtime static → stale-while-revalidate, shell → cache-first
// ---------------------------------------------------------------------------
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Never cache: API calls, uploads (covered by /api/), non-GET, extensions
  if (
    url.pathname.startsWith('/api/') ||
    event.request.method !== 'GET' ||
    url.protocol === 'chrome-extension:'
  ) {
    return;
  }

  // Navigation requests: network-first, fall back to cached shell on offline
  const isNavigation =
    event.request.mode === 'navigate' ||
    event.request.headers.get('accept')?.includes('text/html');

  if (isNavigation) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() =>
          caches.match(event.request).then((cached) => {
            self.clients.matchAll().then((clients) => {
              clients.forEach((client) =>
                client.postMessage({ type: 'OFFLINE' })
              );
            });
            return (
              cached ||
              new Response(
                '<html><body><h2>You are offline</h2><p>Cached reports are available in previously visited pages.</p></body></html>',
                { headers: { 'Content-Type': 'text/html' } }
              )
            );
          })
        )
    );
    return;
  }

  // Runtime static assets: stale-while-revalidate against odia-static-v1.
  // Same-origin only — third-party (e.g. CDN fonts) bypass the cache.
  if (url.origin === self.location.origin && isRuntimeStatic(url.pathname)) {
    event.respondWith(
      caches.open(STATIC_CACHE).then((cache) =>
        cache.match(event.request).then((cached) => {
          const networkFetch = fetch(event.request)
            .then((response) => {
              if (response.ok && response.type !== 'opaque') {
                cache.put(event.request, response.clone());
              }
              return response;
            })
            .catch(() => cached);
          return cached || networkFetch;
        })
      )
    );
    return;
  }

  // Everything else (shell-cached static): cache-first against odia-shell-v5
  event.respondWith(
    caches.match(event.request).then(
      (cached) =>
        cached ||
        fetch(event.request).then((response) => {
          if (response.ok && response.type !== 'opaque') {
            const clone = response.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
    )
  );
});
