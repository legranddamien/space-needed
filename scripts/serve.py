#!/usr/bin/env python3
"""Serve a local preview at the same project prefix as GitHub Pages."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PreviewHandler(SimpleHTTPRequestHandler):
    """Map the public project prefix to the repository while rejecting other routes."""
    def do_GET(self):
        if urlsplit(self.path).path == '/':
            self.send_response(302)
            self.send_header('Location', '/space-needed/')
            self.end_headers()
            return
        if not self.path.startswith('/space-needed/'):
            self.send_error(404)
            return
        self.path = self.path[len('/space-needed'):]
        super().do_GET()


if __name__ == '__main__':
    print('Preview: http://localhost:8000/space-needed/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), partial(PreviewHandler, directory=str(ROOT))).serve_forever()
