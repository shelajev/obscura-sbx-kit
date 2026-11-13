#!/usr/bin/python3
"""Build-only installer for verified upstream binaries; never runs downloaded code."""
import hashlib
from pathlib import Path
import shutil
import ssl
import sys
import tarfile
import tempfile
from urllib.request import HTTPSHandler, HTTPRedirectHandler, ProxyHandler, build_opener

VERSION = '0.2.6'
ARCHIVES = {
    'arm64': ('aarch64', 'e12aff8bbe40326386a471060083e9cec5255b67048996b84f649efef10cac39'),
    'amd64': ('x86_64', 'eed986e478c5ec5439f531f2d7fb6b0e36a356f1df7a6c44a8e8fd4f2486bd76'),
}


class HTTPSOnlyRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith('https://'):
            raise ValueError('non-HTTPS release redirect refused')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def extract_verified(archive, digest, destination):
    with open(archive, 'rb') as source:
        if hashlib.file_digest(source, 'sha256').hexdigest() != digest:
            raise ValueError('release SHA256 mismatch')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, 'r:gz') as bundle:
        for name in ('obscura', 'obscura-worker'):
            member = bundle.getmember(name)
            if not member.isfile():
                raise ValueError('release member must be a regular file')
            with bundle.extractfile(member) as source, (destination / name).open('wb') as target:
                shutil.copyfileobj(source, target)
            (destination / name).chmod(0o755)


def main():
    arch, digest = ARCHIVES[sys.argv[1]]
    url = f'https://github.com/h4ckf0r0day/obscura/releases/download/v{VERSION}/obscura-{arch}-linux.tar.gz'
    ca = Path('/run/build-ca')
    context = ssl.create_default_context(cafile=str(ca) if ca.exists() else None)
    opener = build_opener(ProxyHandler(), HTTPSHandler(context=context), HTTPSOnlyRedirect())
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / 'browser.tar.gz'
        with opener.open(url, timeout=120) as response, archive.open('wb') as target:
            shutil.copyfileobj(response, target)
        extract_verified(archive, digest, '/out/opt/obscura')


if __name__ == '__main__':
    main()
