// BabyLog Service Worker
const CACHE_NAME = 'babylog-v3';

// 预缓存的静态资源（App Shell）
const PRECACHE_URLS = [
  '/',
  '/login',
  '/static/style.css',
  '/static/manifest.json',
  '/static/icons/192x192.png',
  '/static/icons/512x512.png',
];

// ========== Install: 预缓存 App Shell ==========
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS).catch((err) => {
        console.warn('[SW] Precache failed (some may be ok):', err);
      });
    })
  );
  self.skipWaiting();
});

// ========== Activate: 清理旧缓存 ==========
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// ========== Fetch: 策略分发 ==========
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API 请求：Network First
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  // 静态资源：Cache First
  if (
    url.pathname.startsWith('/static/') ||
    url.pathname === '/sw.js' ||
    url.pathname === '/manifest.json'
  ) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  // 页面请求（HTML）：Network First
  event.respondWith(networkFirst(event.request));
});

// ========== 策略函数 ==========

// Cache First：优先读缓存，缓存未命中才走网络
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    return new Response('Offline', { status: 503 });
  }
}

// Network First：优先走网络，网络失败才读缓存
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    // 对 HTML 页面请求返回离线页面提示
    if (request.headers.get('Accept')?.includes('text/html')) {
      return new Response(
        '<html><body style="font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#FFF5F7;color:#FF69B4;"><h2>离线模式</h2><p>请连接网络后重试</p></body></html>',
        { status: 503, headers: { 'Content-Type': 'text/html' } }
      );
    }
    return new Response('Offline', { status: 503 });
  }
}
