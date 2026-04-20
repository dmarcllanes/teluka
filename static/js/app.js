/* Teluka — global JS loaded on every page */

/* ── CSRF: attach X-CSRF-Token to every HTMX request ──────────────────────── */
(function () {
  function getCsrfToken() {
    var m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  document.addEventListener('htmx:configRequest', function (evt) {
    var token = getCsrfToken();
    if (token) evt.detail.headers['X-CSRF-Token'] = token;
  });
})();

/* ── Theme persistence ─────────────────────────────────────────────────────── */
(function () {
  var t = localStorage.getItem('teluka-theme') ||
    (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  document.documentElement.setAttribute('data-theme', t);
})();

/* ── Geolocation — captured once per page load, injected into every HTMX POST ─ */
var _userLat = null, _userLon = null;

(function () {
  if (!navigator.geolocation) return;
  // Try to get cached/fast position immediately
  navigator.geolocation.getCurrentPosition(
    function (pos) {
      _userLat = pos.coords.latitude.toFixed(6);
      _userLon = pos.coords.longitude.toFixed(6);
    },
    function () {},
    { timeout: 8000, maximumAge: 60000, enableHighAccuracy: false }
  );
})();

// Refresh location before each non-GET HTMX request and inject coordinates
document.addEventListener('htmx:configRequest', function (evt) {
  if (evt.detail.verb === 'get') return;
  if (_userLat !== null) {
    evt.detail.parameters['action_lat'] = _userLat;
    evt.detail.parameters['action_lon'] = _userLon;
  }
});

/* ── Web Push subscription ─────────────────────────────────────────────────── */
function _urlBase64ToUint8Array(b64) {
  var pad = '='.repeat((4 - b64.length % 4) % 4);
  var raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
  var arr = new Uint8Array(raw.length);
  for (var i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

function getCsrfToken() {
  var m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return m ? decodeURIComponent(m[1]) : '';
}

async function telukaPushSubscribe() {
  if (!('PushManager' in window) || !('serviceWorker' in navigator)) return false;
  try {
    // Fetch VAPID public key from server
    var keyRes = await fetch('/push/public-key');
    if (!keyRes.ok) return false;
    var vapidPublicKey = (await keyRes.json()).key;
    if (!vapidPublicKey) return false;

    var reg = await navigator.serviceWorker.ready;
    var sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: _urlBase64ToUint8Array(vapidPublicKey),
    });

    var token = getCsrfToken();
    await fetch('/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
      body: JSON.stringify(sub.toJSON()),
    });
    return true;
  } catch (e) {
    return false;
  }
}

async function telukaPushUnsubscribe() {
  if (!('serviceWorker' in navigator)) return;
  try {
    var reg = await navigator.serviceWorker.ready;
    var sub = await reg.pushManager.getSubscription();
    if (!sub) return;
    var endpoint = sub.endpoint;
    await sub.unsubscribe();
    var token = getCsrfToken();
    await fetch('/push/unsubscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
      body: JSON.stringify({ endpoint }),
    });
  } catch (e) {}
}

