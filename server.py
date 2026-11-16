#!/usr/bin/env python3
"""Ocarina of Time sync server. Python 3.8+, standard library only.

Run:  python server.py
If you have run setup_https.py, it serves https and is reachable from your home
network (needed for the iPhone). Otherwise it is plain http on this PC only.
  --lan    also listen on the home network without https (not recommended)
  --local  listen on this PC only, even with https set up
It stores your library in the 'ocarina-data' folder next to this file and also
serves the app itself, so you can open http://localhost:8765 on this PC.
"""
import json, mimetypes, os, re, secrets, socket, ssl, sys, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'ocarina-data')
AUDIO, COVERS = os.path.join(DATA, 'audio'), os.path.join(DATA, 'covers')
META, CFG = os.path.join(DATA, 'meta.json'), os.path.join(DATA, 'config.json')
CERT, KEY, CA = (os.path.join(DATA, n) for n in ('cert.pem', 'key.pem', 'ca.crt'))
PORT = int(os.environ.get('PORT', 8765))
STATIC = {'index.html', 'sw.js', 'manifest.webmanifest', 'icon-180.png', 'icon-192.png', 'icon-512.png'}
ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
FILE_URL = re.compile(r'^/api/(audio|cover)/([A-Za-z0-9_-]{1,64})$')
lock = threading.Lock()

for d in (AUDIO, COVERS):
    os.makedirs(d, exist_ok=True)
if os.path.exists(CFG):
    with open(CFG) as f:
        TOKEN = json.load(f)['token']
else:
    TOKEN = secrets.token_urlsafe(18)
    with open(CFG, 'w') as f:
        json.dump({'token': TOKEN}, f)
if os.path.exists(META):
    with open(META) as f:
        state = json.load(f)
else:
    state = {'songs': {}, 'lists': {}, 'tomb': {}, 'covers': {}}


def save():
    tmp = META + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(state, f)
    os.replace(tmp, META)


def snapshot():
    return {**state, 'files': [f for f in os.listdir(AUDIO) if ID.match(f)]}


def remove_files(i):
    for folder in (AUDIO, COVERS):
        p = os.path.join(folder, i)
        if os.path.exists(p):
            os.remove(p)


def merge(inc):
    """Last-write-wins by 'mod' timestamp. Deletions are kept as tombstones."""
    for kind in ('songs', 'lists'):
        for i, r in (inc.get(kind) or {}).items():
            if not ID.match(i) or not isinstance(r, dict):
                continue
            mod = r.get('mod', 0)
            if mod <= state['tomb'].get(i, 0):
                continue
            cur = state[kind].get(i)
            if not cur or mod > cur.get('mod', 0):
                state[kind][i] = r
            state['tomb'].pop(i, None)
    for i, ts in (inc.get('tomb') or {}).items():
        if not ID.match(i) or ts <= state['tomb'].get(i, 0):
            continue
        live = state['songs'].get(i) or state['lists'].get(i)
        if live and live.get('mod', 0) > ts:
            continue
        state['songs'].pop(i, None)
        state['lists'].pop(i, None)
        state['covers'].pop(i, None)
        remove_files(i)
        state['tomb'][i] = ts


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def cors(self):
        for k, v in (('Access-Control-Allow-Origin', '*'),
                     ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
                     ('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS'),
                     ('Access-Control-Allow-Private-Network', 'true'),
                     ('Access-Control-Max-Age', '600')):
            self.send_header(k, v)

    def send(self, code, body=b'', ctype='application/json', extra=()):
        self.send_response(code)
        self.cors()
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def authed(self):
        h = self.headers.get('Authorization', '')
        t = h[7:] if h.startswith('Bearer ') else (parse_qs(urlparse(self.path).query).get('t') or [''])[0]
        return secrets.compare_digest(t.encode(), TOKEN.encode())

    def do_OPTIONS(self):
        self.send(204)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith('/api/'):
            if not self.authed():
                return self.send(401, b'{"error":"bad token"}')
            if path == '/api/ping':
                return self.send(200, b'{"ok":true}')
            if path == '/api/state':
                with lock:
                    body = json.dumps(snapshot()).encode()
                return self.send(200, body)
            m = FILE_URL.match(path)
            if m:
                return self.file(os.path.join(AUDIO if m[1] == 'audio' else COVERS, m[2]))
            return self.send(404)
        name = 'index.html' if path in ('/', '') else path.lstrip('/')
        if name in STATIC:
            return self.file(os.path.join(HERE, name), static=True)
        self.send(404)

    def do_POST(self):
        if not self.authed():
            return self.send(401, b'{"error":"bad token"}')
        if urlparse(self.path).path != '/api/state':
            return self.send(404)
        n = int(self.headers.get('Content-Length', 0))
        try:
            inc = json.loads(self.rfile.read(n) or b'{}')
        except ValueError:
            return self.send(400)
        with lock:
            merge(inc)
            save()
            body = json.dumps(snapshot()).encode()
        self.send(200, body)

    def do_PUT(self):
        if not self.authed():
            return self.send(401, b'{"error":"bad token"}')
        u = urlparse(self.path)
        m = FILE_URL.match(unquote(u.path))
        if not m:
            return self.send(404)
        dest = os.path.join(AUDIO if m[1] == 'audio' else COVERS, m[2])
        tmp = dest + '.part'
        left = int(self.headers.get('Content-Length', 0))
        with open(tmp, 'wb') as f:
            while left > 0:
                b = self.rfile.read(min(1 << 20, left))
                if not b:
                    break
                f.write(b)
                left -= len(b)
        if left:
            os.remove(tmp)
            return self.send(400)
        os.replace(tmp, dest)
        if m[1] == 'cover':
            cmod = int(float((parse_qs(u.query).get('cmod') or ['0'])[0]))
            with lock:
                state['covers'][m[2]] = cmod
                save()
        self.send(200, b'{"ok":true}')

    def file(self, path, static=False):
        if not os.path.isfile(path):
            return self.send(404)
        size = os.path.getsize(path)
        if static:
            ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        elif path.startswith(COVERS):
            ctype = 'image/jpeg'  # the app works out the real image type itself
        else:
            fn = (state['songs'].get(os.path.basename(path)) or {}).get('fn', '')
            ctype = mimetypes.guess_type(fn)[0] or 'application/octet-stream'
        start, end, code = 0, size - 1, 200
        extra = [('Accept-Ranges', 'bytes')]
        if static:
            extra.append(('Cache-Control', 'no-cache'))
        rg = self.headers.get('Range')
        if rg and size:
            m = re.match(r'bytes=(\d*)-(\d*)$', rg.strip())
            if m and (m[1] or m[2]):
                if m[1]:
                    start = int(m[1])
                    end = int(m[2]) if m[2] else size - 1
                else:
                    start = max(0, size - int(m[2]))
                end = min(end, size - 1)
                if start > end:
                    return self.send(416, b'', extra=[('Content-Range', 'bytes */%d' % size)])
                code = 206
                extra.append(('Content-Range', 'bytes %d-%d/%d' % (start, end, size)))
        length = max(0, end - start + 1)
        self.send_response(code)
        self.cors()
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(length))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        if self.command == 'HEAD':
            return
        with open(path, 'rb') as f:
            f.seek(start)
            left = length
            while left > 0:
                b = f.read(min(65536, left))
                if not b:
                    break
                try:
                    self.wfile.write(b)
                except (BrokenPipeError, ConnectionResetError):
                    break
                left -= len(b)


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


class Server(ThreadingHTTPServer):
    daemon_threads = True
    ctx = None

    def get_request(self):
        sock, addr = super().get_request()
        if self.ctx:  # handshake happens in the handler thread, so one bad client can't block the rest
            sock = self.ctx.wrap_socket(sock, server_side=True, do_handshake_on_connect=False)
        return sock, addr

    def handle_error(self, request, client_address):
        pass


PAGE = """<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>Ocarina of Time certificate</title>
<body style="font:17px system-ui;max-width:30em;margin:2em auto;padding:0 1em"><h2>Ocarina of Time</h2>
<p>Install this certificate once so your phone trusts your PC's sync server.</p>
<p><a href="/ca.crt" style="display:inline-block;padding:12px 18px;background:#4a5fb8;color:#fff;border-radius:10px;text-decoration:none">Download certificate</a></p>
<ol><li>Tap Allow when asked to download a profile.</li><li>Open <b>Settings</b>, tap <b>Profile Downloaded</b>, then <b>Install</b>.</li>
<li>Go to <b>Settings &rarr; General &rarr; About &rarr; Certificate Trust Settings</b> and switch the new certificate on.</li></ol></body>"""


class CAHandler(BaseHTTPRequestHandler):
    """Plain-http page that only hands out the public certificate, so an iPhone can install it."""

    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/ca.crt' and os.path.exists(CA):
            with open(CA, 'rb') as f:
                body = f.read()
            ctype, extra = 'application/x-x509-ca-cert', 'attachment; filename="ocarina-ca.crt"'
        elif path in ('/', ''):
            body, ctype, extra = PAGE.encode(), 'text/html; charset=utf-8', None
        else:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        if extra:
            self.send_header('Content-Disposition', extra)
        self.end_headers()
        self.wfile.write(body)


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


if __name__ == '__main__':
    https = os.path.exists(CERT) and os.path.exists(KEY)
    lan = ('--lan' in sys.argv or https) and '--local' not in sys.argv
    srv = Server(('0.0.0.0' if lan else '127.0.0.1', PORT), Handler)
    scheme = 'http'
    if https:
        srv.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        srv.ctx.load_cert_chain(CERT, KEY)
        scheme = 'https'
    ip, host = lan_ip(), socket.gethostname()
    lines = ['Ocarina of Time sync server is running.', '',
             'Address on this PC:  %s://localhost:%d' % (scheme, PORT)]
    if lan and ip:
        lines.append('Address on phone:    %s://%s:%d   (or %s://%s.local:%d)' % (scheme, ip, PORT, scheme, host, PORT))
    if https and lan and os.path.exists(CA):
        ca = Server(('0.0.0.0', PORT + 1), CAHandler)
        threading.Thread(target=ca.serve_forever, daemon=True).start()
        if ip:
            lines.append('Phone certificate page: http://%s:%d' % (ip, PORT + 1))
    lines += ['Access token:       %s' % TOKEN, 'Library folder:     %s' % DATA]
    if not https:
        lines += ['', 'Run setup_https.py once to enable sync with your iPhone.']
    print('\n' + '\n'.join(lines) + '\n\nPress Ctrl+C to stop.\n')
    with open(os.path.join(DATA, 'connection-info.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('Stopped.')
