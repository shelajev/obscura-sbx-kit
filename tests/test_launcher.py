import importlib.util
import socket
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('launcher', 'mixin/scripts/obscura.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_proxy_dns_only_and_ipv4_preference(self):
        with patch.object(socket, 'getaddrinfo', return_value=[
            (socket.AF_INET6, 1, 6, '', ('fd00::2', 3128, 0, 0)),
            (socket.AF_INET, 1, 6, '', ('172.17.0.2', 3128))]) as resolve:
            cmd = launcher.command(['mcp'], {'HTTPS_PROXY': 'http://gateway:3128'})
        resolve.assert_called_once_with('gateway', 3128, type=socket.SOCK_STREAM)
        self.assertEqual(cmd, [launcher.BINARY, '--proxy', 'http://172.17.0.2:3128', 'mcp'])

    def test_explicit_overrides_environment(self):
        for args in (['fetch', '--proxy', 'http://127.0.0.1:9'],
                     ['--proxy=http://127.0.0.1:9', 'mcp']):
            self.assertEqual(launcher.command(args, {'HTTPS_PROXY': 'bad'}), [launcher.BINARY] + args)

    def test_ipv6_and_socks(self):
        self.assertEqual(launcher.literal_proxy('socks5://[fd00::1]:1080'), 'socks5://[fd00::1]:1080')

    def test_invalid_proxy_fails_closed(self):
        for url in ('https://host:3128', 'http://user:secret@host:3128',
                    'http://host', 'http://host:0', 'http://host:99999',
                    'http://host:3128/path', 'http://host:3128/?q=x'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                launcher.literal_proxy(url)
        with self.assertRaises(ValueError):
            launcher.command(['--proxy'], {})

    def test_no_proxy_preserves_native_args_and_ssrf(self):
        args = ['serve', '--host', '127.0.0.1', '--port', '9222']
        self.assertEqual(launcher.command(args, {}), [launcher.BINARY] + args)
        self.assertEqual(launcher.command(['mcp'], {'OBSCURA_PROXY': 'http://127.0.0.1:8',
                         'HTTPS_PROXY': 'bad'}),
                         [launcher.BINARY, '--proxy', 'http://127.0.0.1:8', 'mcp'])


if __name__ == '__main__':
    unittest.main()
