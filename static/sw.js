/* ─────────────────────────────────────────────────────────────────────────────
   Teluka Service Worker  —  v2
   Strategy:
     • Static assets (CSS/JS/fonts/images) → Cache First (long-lived)
     • App shell pages (/, /login)         → Stale While Revalidate
     • Auth / API routes                   → Network Only  (never cache)
     • Everything else                     → Network First w/ cache fallback
     • Offline fallback                    → /offline  (pre-cached)
   ───────────────────────────────────────────────────────────────────────────── */

const CACHE_VERSION  = "teluka-v3";
const STATIC_CACHE   = `${CACHE_VERSION}-static`;
const PAGES_CACHE    = `${CACHE_VERSION}-pages`;
const ALL_CACHES     = [STATIC_CACHE, PAGES_CACHE];

/* Files cached immediately on install (app shell) */
const PRECACHE_STATIC = [
  "/static/css/app.css",
  "/static/css/landing.css",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

const PRECACHE_PAGES = [
  "/",
  "/login",
];

/* Routes that must NEVER be served from cache */
const NETWORK_ONLY_PATTERNS = [
  /\/check-identifier/,
  /\/register/,
  /\/verify-otp/,
  /\/set-pin/,
  /\/resend-otp/,
  /\/logout/,
  /\/transactions\/.+/,
  /\/sellers\//,
  /\/health/,
  /* Third-party APIs */
  /supabase\.co/,
  /paymongo\.com/,
];

/* Static asset extensions → cache first */
const STATIC_EXTENSIONS = /\.(css|js|woff2?|ttf|otf|png|jpg|jpeg|webp|svg|ico|gif)$/i;


/* ── Install: pre-cache app shell ──────────────────────────────────────────── */
self.addEventListener("install", (event) => {
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then((c) => c.addAll(PRECACHE_STATIC)),
      caches.open(PAGES_CACHE).then((c) => c.addAll(PRECACHE_PAGES)),
    ]).then(() => self.skipWaiting())
  );
});


/* ── Activate: delete old caches ───────────────────────────────────────────── */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => !ALL_CACHES.includes(k))
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});


/* ── Fetch: route-based strategies ────────────────────────────────────────── */
self.addEventListener("fetch", (event) => {
  const { request } = event;

  /* Only handle GET (never intercept mutations) */
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  /* Skip cross-origin requests (Supabase, fonts CDN handled separately) */
  const isSameOrigin = url.origin === self.location.origin;
  const isGoogleFont = url.hostname === "fonts.gstatic.com";

  if (!isSameOrigin && !isGoogleFont) return;

  /* ── Strategy 1: Network Only ── */
  if (NETWORK_ONLY_PATTERNS.some((re) => re.test(url.pathname + url.search))) {
    return; /* fall through to browser default */
  }

  /* ── Strategy 2: Cache First (static assets + Google Fonts) ── */
  if (STATIC_EXTENSIONS.test(url.pathname) || isGoogleFont) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  /* ── Strategy 3: Stale While Revalidate (app shell pages) ── */
  if (url.pathname === "/" || url.pathname === "/login") {
    event.respondWith(staleWhileRevalidate(request, PAGES_CACHE));
    return;
  }

  /* ── Strategy 4: Network First (everything else) ── */
  event.respondWith(networkFirst(request, PAGES_CACHE));
});


/* ── Strategy implementations ──────────────────────────────────────────────── */

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response("Offline — resource not cached.", { status: 503 });
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(request);

  const networkFetch = fetch(request).then((response) => {
    if (response.ok) cache.put(request, response.clone());
    return response;
  }).catch(() => null);

  return cached || await networkFetch || offlinePage();
}

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || offlinePage();
  }
}

/* ── Push notifications ────────────────────────────────────────────────────── */

self.addEventListener("push", (event) => {
  if (!event.data) return;
  let payload = { title: "Teluka", body: "You have a new update.", url: "/dashboard" };
  try { payload = event.data.json(); } catch {}

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body:    payload.body,
      icon:    "/static/icons/icon-192.png",
      badge:   "/static/icons/icon-192.png",
      tag:     "teluka-deal",        // replace previous notification of same type
      renotify: true,
      data:    { url: payload.url },
      actions: [{ action: "open", title: "View Deal" }],
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/dashboard";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if (client.url.includes(self.location.origin) && "focus" in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});


function offlinePage() {
  return new Response(
    `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Offline — Teluka</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:system-ui,sans-serif;background:#030307;color:#E9EEF5;
         min-height:100svh;display:flex;align-items:center;justify-content:center;
         flex-direction:column;gap:16px;padding:24px;text-align:center}
    .logo{width:64px;height:64px;border-radius:18px;
          background:linear-gradient(135deg,#0D9488,#40E0FF);
          display:flex;align-items:center;justify-content:center;
          font-size:1.8rem;font-weight:900;color:#fff;margin:0 auto 8px}
    h1{font-size:1.5rem;font-weight:800}
    p{color:#94A3B8;font-size:0.95rem;max-width:320px;line-height:1.6}
    a{margin-top:8px;padding:12px 28px;border-radius:999px;
      background:linear-gradient(135deg,#0D9488,#40E0FF);color:#fff;
      font-weight:700;text-decoration:none;display:inline-block}
  </style>
</head>
<body>
  <div class="logo">T</div>
  <h1>You're offline</h1>
  <p>Check your internet connection and try again.</p>
  <a onclick="location.reload()">Try again</a>
</body>
</html>`,
    { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } }
  );
}
