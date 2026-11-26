const C='ocarina-v15',F=['./','index.html','manifest.webmanifest','icon-180.png','icon-192.png','icon-512.png','ocarina-logo.png',...['zeldas-lullaby','eponas-theme','suns-song','sarias-song','song-of-time','song-of-storms'].map(n=>'sounds/'+n+'.mp3')];
self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>Promise.all(F.map(f=>c.add(f).catch(()=>{})))).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!=C).map(x=>caches.delete(x)))).then(()=>clients.claim())));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);
if(e.request.method!='GET'||u.origin!=location.origin||u.pathname.includes('/api/'))return;
e.respondWith(fetch(e.request).then(r=>{if(r.ok){const c=r.clone();caches.open(C).then(x=>x.put(e.request,c))}return r}).catch(()=>caches.match(e.request).then(r=>r||(e.request.mode=='navigate'?caches.match('index.html'):Response.error()))))});
