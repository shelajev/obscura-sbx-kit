#!/usr/bin/python3
"""Launch native Obscura with the SBX proxy; no browser or MCP implementation."""
import ipaddress
import os
import socket
import sys
from urllib.parse import urlsplit, urlunsplit

BINARY = '/opt/obscura/obscura'


def literal_proxy(value):
    """Resolve only the trusted operator-configured proxy, never target URLs."""
    url = urlsplit(value)
    if url.scheme not in ('http', 'socks5') or not url.hostname or not url.port:
        raise ValueError('proxy must use http:// or socks5:// with an explicit port')
    if url.username is not None or url.password is not None:
        raise ValueError('proxy credentials are unsupported; use SBX proxy credentials')
    if url.path not in ('', '/') or url.query or url.fragment:
        raise ValueError('proxy must not contain a path, query or fragment')
    try:
        ip = ipaddress.ip_address(url.hostname)
    except ValueError:
        addresses = socket.getaddrinfo(url.hostname, url.port, type=socket.SOCK_STREAM)
        # Prefer IPv4 when both are available; IPv6-only proxies remain supported.
        addresses.sort(key=lambda item: item[0] != socket.AF_INET)
        ip = ipaddress.ip_address(addresses[0][4][0])
    host = f'[{ip}]' if ip.version == 6 else str(ip)
    return urlunsplit((url.scheme, f'{host}:{url.port}', '', '', ''))


def command(args, env):
    args = list(args)
    explicit = False
    for i, arg in enumerate(args):
        if arg == '--proxy':
            if i + 1 >= len(args):
                raise ValueError('--proxy requires a URL')
            args[i + 1] = literal_proxy(args[i + 1])
            explicit = True
        elif arg.startswith('--proxy='):
            args[i] = '--proxy=' + literal_proxy(arg.split('=', 1)[1])
            explicit = True
    if not explicit:
        proxy = next((env[key] for key in ('OBSCURA_PROXY', 'HTTPS_PROXY', 'https_proxy',
                     'HTTP_PROXY', 'http_proxy', 'ALL_PROXY', 'all_proxy') if env.get(key)), None)
        if proxy:
            args = ['--proxy', literal_proxy(proxy)] + args
    return [BINARY] + args


def main():
    try:
        args = command(sys.argv[1:], os.environ)
    except (ValueError, OSError):
        # Never echo a malformed URL: it could contain credentials.
        sys.exit('obscura: invalid or unresolvable proxy; see docs/troubleshooting.md')
    env = os.environ.copy()
    env.setdefault('SSL_CERT_FILE', '/etc/ssl/certs/ca-certificates.crt')
    os.execve(BINARY, args, env)


if __name__ == '__main__':
    main()
