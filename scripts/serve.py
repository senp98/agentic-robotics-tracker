#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地工作台：打开页面，在页面上改状态、写批注，自动保存到 notes/<编号>.md。

    python3 scripts/serve.py            然后浏览器会打开 http://127.0.0.1:8000
    python3 scripts/serve.py --port 9000 --no-open

只监听本机。写完批注后 git add notes && git commit && git push，线上页面会自动更新。
"""
import argparse
import functools
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import tracker as T


class Handler(SimpleHTTPRequestHandler):
    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/ping':
            return self._send(200, {'ok': True})
        if path == '/data.js':  # 每次现算，刷新页面就能看到最新的批注
            return self._send(200, T.build_js().encode('utf-8'), 'application/javascript; charset=utf-8')
        return super().do_GET()

    def do_POST(self):
        if self.path.split('?')[0] != '/api/note':
            return self._send(404, {'ok': False, 'error': '没有这个接口'})
        # 只接受本页面发来的 JSON 请求，别的网页不能借浏览器往这里写文件
        host = self.headers.get('Host', '')
        origin = self.headers.get('Origin')
        if 'application/json' not in self.headers.get('Content-Type', '') or (origin and origin.split('://')[-1] != host):
            return self._send(403, {'ok': False, 'error': '拒绝了这个请求'})
        try:
            req = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8'))
            pid = req['id']
            if pid not in {p['id'] for p in T.load_papers()}:
                raise ValueError('库里没有这个编号：%s' % pid)
            T.write_note(pid, status=req.get('status'), body=req.get('note'), reads=req.get('reads'))
        except (KeyError, ValueError, TypeError) as e:
            return self._send(400, {'ok': False, 'error': str(e)})
        self._send(200, {'ok': True})

    def log_message(self, fmt, *args):
        if self.command == 'POST':
            super().log_message(fmt, *args)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='本地工作台')
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--no-open', action='store_true', help='不自动打开浏览器')
    a = ap.parse_args()
    T.build()
    url = 'http://127.0.0.1:%d/' % a.port
    server = ThreadingHTTPServer(('127.0.0.1', a.port), functools.partial(Handler, directory=T.DOCS))
    print('已打开 %s  （Ctrl+C 退出）' % url)
    if not a.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n已退出')
