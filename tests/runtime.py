#!/usr/bin/env python3
"""Actual native CLI/MCP checks. Run explicitly; localhost opt-in is fixture-only."""
import contextlib
import http.server
import json
import os
from pathlib import Path
import select
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
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(HTML)))
        self.end_headers()
        self.wfile.write(HTML)

    def log_message(self, *args):
        pass


@contextlib.contextmanager
def fixture(tls=None):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
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


class MCP:
    def __init__(self, args=(), env=None):
        self.stderr = tempfile.TemporaryFile(mode='w+')
        self.proc = subprocess.Popen(COMMAND + list(args) + ['mcp'], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=self.stderr, text=True, env=env)
        self.count = 0

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
                    init = mcp.call('initialize', {'protocolVersion': '2024-11-05',
                                    'capabilities': {}, 'clientInfo': {'name': 'kit-tests', 'version': '1'}})
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
            (root / 'leaf.ext').write_text('subjectAltName=IP:127.0.0.1\nbasicConstraints=critical,CA:FALSE\nextendedKeyUsage=serverAuth\n')
            openssl('x509', '-req', '-in', root / 'leaf.csr', '-CA', ca, '-CAkey', ca_key,
                    '-CAcreateserial', '-out', cert, '-days', '1', '-extfile', root / 'leaf.ext')
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.load_cert_chain(cert, key)
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

    @unittest.skipUnless(os.environ.get('OBSCURA_PUBLIC_HTTPS'), 'public HTTPS target not requested')
    def test_public_https_cli_and_mcp(self):
        url = os.environ['OBSCURA_PUBLIC_HTTPS']
        result = self.cli(['fetch', url, '--eval', 'document.title', '--wait', '0'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Example Domain', result.stdout)
        mcp = MCP()
        try:
            mcp.call('initialize')
            self.assertIn('Example Domain', mcp.tool('browser_navigate', url=url))
            self.assertIn('Example Domain', mcp.tool('browser_snapshot'))
            for target in ('http://127.0.0.1:1', 'http://169.254.169.254/latest/meta-data', 'http://localhost:1'):
                denied = mcp.call('tools/call', {'name': 'browser_navigate', 'arguments': {'url': target}})
                self.assertTrue(denied.get('isError'), denied)
        finally:
            mcp.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
