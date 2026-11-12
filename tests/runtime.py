#!/usr/bin/env python3
"""Actual native CLI/MCP checks. Run explicitly; localhost opt-in is fixture-only."""
import contextlib
import http.server
import json
import os
from pathlib import Path
import select
import socket
import socketserver
import shlex
import ssl
import subprocess
import tempfile
import threading
import unittest

COMMAND = shlex.split(os.environ.get('OBSCURA_COMMAND', 'obscura'))
HTML = b'''<!doctype html><title>Kit fixture</title><h1>Fixture ready</h1>
<input id="name"><button id="go" onclick="document.getElementById('out').textContent='Hello '+document.getElementById('name').value">Go</button><p id="out">Waiting</p>'''
PROXY_KEYS = ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'OBSCURA_PROXY')


def local_env():
    return {k: v for k, v in os.environ.items() if k not in PROXY_KEYS and k != 'OBSCURA_ALLOW_PRIVATE_NETWORK' and k != 'OBSCURA_STORAGE_DIR'}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript' if self.path == '/app.js' else 'text/html')
        body = b"window.proxyResource='loaded';" if self.path == '/app.js' else HTML + b'<script src="/app.js"></script>'
        if hasattr(self.server, 'paths'):
            self.server.paths.append(self.path)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@contextlib.contextmanager
def fixture(tls=None, paths=None):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.paths = paths if paths is not None else []
    if tls:
        server.socket = tls.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'{"https" if tls else "http"}://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def tls_material(directory):
    root = Path(directory)
    cert, key = root / 'cert.pem', root / 'key.pem'
    ca, ca_key = root / 'ca.pem', root / 'ca-key.pem'
    def openssl(*args):
        subprocess.run(['openssl', *map(str, args)], check=True, capture_output=True)
    openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', ca_key,
            '-out', ca, '-days', '1', '-subj', '/CN=kit-test-ca',
            '-addext', 'basicConstraints=critical,CA:TRUE')
    openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', key,
            '-out', root / 'leaf.csr', '-subj', '/CN=kit-test')
    (root / 'leaf.ext').write_text('subjectAltName=IP:127.0.0.1,DNS:kit-proxy.invalid\nbasicConstraints=critical,CA:FALSE\nextendedKeyUsage=serverAuth\n')
    openssl('x509', '-req', '-in', root / 'leaf.csr', '-CA', ca, '-CAkey', ca_key,
            '-CAcreateserial', '-out', cert, '-days', '1', '-extfile', root / 'leaf.ext')
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert, key)
    return tls, ca


class ConnectProxy(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class Tunnel(socketserver.StreamRequestHandler):
    def handle(self):
        request = self.rfile.readline().decode().strip()
        while self.rfile.readline() not in (b'\r\n', b'\n', b''):
            pass
        method, target, _ = request.split()
        if method != 'CONNECT':
            return
        # Test-only proxy permits exactly the fixture endpoint, never arbitrary targets.
        if target != self.server.allowed:
            self.wfile.write(b'HTTP/1.1 403 Forbidden\r\n\r\n')
            return
        self.server.hits.append(target)
        host, port = target.rsplit(':', 1)
        with socket.create_connection(self.server.target) as upstream:
            self.wfile.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            self.wfile.flush()
            peers = [self.connection, upstream]
            while True:
                ready, _, _ = select.select(peers, [], [], 10)
                if not ready:
                    return
                for peer in ready:
                    data = peer.recv(65536)
                    if not data:
                        return
                    (upstream if peer is self.connection else self.connection).sendall(data)


class MCP:
    def __init__(self, args=(), env=None):
        self.stderr = tempfile.TemporaryFile(mode='w+')
        self.proc = subprocess.Popen(COMMAND + list(args) + ['mcp'], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=self.stderr, text=True, env=env)
        self.count = 0
        self.initialization = self.call('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                  'clientInfo': {'name': 'kit-tests', 'version': '1'}})
        self.proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n')
        self.proc.stdin.flush()

    def call(self, method, params=None):
        self.count += 1
        self.proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': self.count,
                                          'method': method, 'params': params or {}}) + '\n')
        self.proc.stdin.flush()
        if not select.select([self.proc.stdout], [], [], 45)[0]:
            raise TimeoutError('MCP response timed out')
        line = self.proc.stdout.readline()
        if not line:
            self.stderr.seek(0)
            raise RuntimeError(self.stderr.read())
        response = json.loads(line)
        assert response['id'] == self.count, response
        assert 'error' not in response, response
        return response['result']

    def tool(self, name, **arguments):
        result = self.call('tools/call', {'name': name, 'arguments': arguments})
        assert not result.get('isError'), result
        return json.dumps(result)

    def close(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.proc.stdout.close()
        self.stderr.close()


class RuntimeTests(unittest.TestCase):
    def cli(self, args, env=None):
        return subprocess.run(COMMAND + args, env=env, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=45)

    def test_cli_js_render_and_ssrf(self):
        with fixture() as url, tempfile.TemporaryDirectory() as directory:
            denied = self.cli(['fetch', url, '--dump', 'text'], local_env())
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn('private/internal', denied.stderr)
            png = Path(directory) / 'fixture.png'
            result = self.cli(['fetch', url, '--allow-private-network', '--wait', '0',
                               '--eval', 'document.title', '--screenshot', str(png)], local_env())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Kit fixture', result.stdout)
            self.assertTrue(png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertGreater(png.stat().st_size, 100)

    def test_mcp_interaction_and_independent_state(self):
        with fixture() as url:
            a = MCP(['--allow-private-network'], local_env())
            b = MCP(['--allow-private-network'], local_env())
            try:
                for mcp in (a, b):
                    init = mcp.initialization
                    self.assertEqual(init['serverInfo']['name'], 'obscura-mcp')
                    self.assertIn('browser_navigate', json.dumps(mcp.call('tools/list')))
                    mcp.tool('browser_navigate', url=url)
                a.tool('browser_fill', selector='#name', value='SBX')
                a.tool('browser_click', selector='#go')
                self.assertIn('Hello SBX', a.tool('browser_snapshot'))
                a.tool('browser_evaluate', expression="localStorage.setItem('kit','secret'); document.cookie='kit=secret; path=/'; 'set'")
                self.assertNotIn('secret', b.tool('browser_evaluate', expression="JSON.stringify([localStorage.getItem('kit'),document.cookie,document.getElementById('name').value])"))
                self.assertIn('Waiting', b.tool('browser_snapshot'))
            finally:
                a.close()
                b.close()

    def test_https_trust_positive_and_negative(self):
        with tempfile.TemporaryDirectory() as directory:
            tls, ca = tls_material(directory)
            with fixture(tls) as url:
                env = local_env()
                env['SSL_CERT_FILE'] = '/etc/ssl/certs/ca-certificates.crt'
                env.pop('SSL_CERT_DIR', None)
                denied = self.cli(['fetch', url, '--allow-private-network', '--dump', 'text', '--wait', '0'], env)
                self.assertNotEqual(denied.returncode, 0)
                self.assertRegex(denied.stderr.lower(), 'cert|tls|issuer')
                env['SSL_CERT_FILE'] = str(ca)
                passed = self.cli(['fetch', url, '--allow-private-network', '--dump', 'text', '--wait', '0'], env)
                self.assertEqual(passed.returncode, 0, passed.stderr)
                self.assertIn('Fixture ready', passed.stdout)

    def test_proxy_https_subresources_and_live_ssrf(self):
        with tempfile.TemporaryDirectory() as directory:
            tls, ca = tls_material(directory)
            paths = []
            with fixture(tls, paths) as url, ConnectProxy(('127.0.0.1', 0), Tunnel) as proxy:
                port = int(url.rsplit(':', 1)[1])
                proxy.allowed = f'kit-proxy.invalid:{port}'
                proxy.target = ('127.0.0.1', port)
                proxied_url = f'https://{proxy.allowed}'
                proxy.hits = []
                thread = threading.Thread(target=proxy.serve_forever, daemon=True)
                thread.start()
                try:
                    env = local_env()
                    env['HTTPS_PROXY'] = f'http://localhost:{proxy.server_address[1]}'
                    env['SSL_CERT_FILE'] = str(ca)
                    env.pop('SSL_CERT_DIR', None)
                    passed = self.cli(['fetch', proxied_url, '--allow-private-network', '--wait', '0',
                                      '--eval', 'window.proxyResource'], env)
                    self.assertEqual(passed.returncode, 0, passed.stderr)
                    self.assertIn('loaded', passed.stdout)
                    self.assertTrue(proxy.hits, 'document/script did not transit CONNECT proxy')
                    self.assertIn('/', paths)
                    self.assertIn('/app.js', paths)
                    denied = self.cli(['fetch', url, '--dump', 'text'], env)
                    self.assertNotEqual(denied.returncode, 0)
                    self.assertIn('private/internal', denied.stderr)
                    env['SSL_CERT_FILE'] = '/etc/ssl/certs/ca-certificates.crt'
                    untrusted = self.cli(['fetch', proxied_url, '--allow-private-network', '--wait', '0'], env)
                    self.assertNotEqual(untrusted.returncode, 0)
                    self.assertRegex(untrusted.stderr.lower(), 'cert|tls|issuer')
                finally:
                    proxy.shutdown()
                    thread.join()

    @unittest.skipUnless(os.environ.get('OBSCURA_PUBLIC_HTTPS'), 'public HTTPS target not requested')
    def test_public_https_cli_and_mcp(self):
        url = os.environ['OBSCURA_PUBLIC_HTTPS']
        result = self.cli(['fetch', url, '--eval', 'document.title', '--wait', '0'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Example Domain', result.stdout)
        mcp = MCP()
        try:
            self.assertIn('Example Domain', mcp.tool('browser_navigate', url=url))
            self.assertIn('Example Domain', mcp.tool('browser_snapshot'))
            for target in ('http://127.0.0.1:1', 'http://169.254.169.254/latest/meta-data', 'http://localhost:1'):
                denied = mcp.call('tools/call', {'name': 'browser_navigate', 'arguments': {'url': target}})
                self.assertTrue(denied.get('isError'), denied)
        finally:
            mcp.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
