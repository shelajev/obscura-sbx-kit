#!/usr/bin/env python3
"""Validate release versions and fail closed before publishing a new OCI version."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SEMVER = r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
IMAGES = ('obscura-sbx-kit-mixin', 'obscura-sbx-kit')


def version_for(tag, root=Path('.')):
    if not re.fullmatch('v' + SEMVER, tag):
        raise ValueError('tag must be vMAJOR.MINOR.PATCH without leading zeroes')
    version = tag[1:]
    for name in ('mixin/obscura-mixin.yaml', 'standalone/obscura.yaml'):
        matches = re.findall(r'^version: "([^"]+)"$', (root / name).read_text(), re.M)
        if matches != [version]:
            raise ValueError(f'{name}: version must match {tag}')
    package = json.loads((root / 'package.json').read_text())
    lock = json.loads((root / 'package-lock.json').read_text())
    if any(v != version for v in (package['version'], lock['version'],
                                 lock['packages']['']['version'])):
        raise ValueError('package and lockfile versions must match tag')
    return version


def require_absent(version, authfile):
    # Check BOTH destinations before any write. A partial publish blocks retries.
    for image in IMAGES:
        ref = f'docker://ghcr.io/shelajev/{image}:{version}'
        result = subprocess.run(['skopeo', 'inspect', '--raw', '--authfile', authfile,
                                 ref], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            raise ValueError(f'{ref} already exists; version overwrite refused')
        # Only explicit registry unknown-name/manifest responses establish absence.
        # Auth, network, TLS, rate-limit and other errors must stop publication.
        if not re.search(r'\b(?:manifest unknown|name unknown)\b', result.stderr.lower()):
            raise ValueError(f'{ref}: absence not established; registry check failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag')
    parser.add_argument('--require-absent', metavar='AUTHFILE')
    args = parser.parse_args()
    try:
        version = version_for(args.tag)
        if args.require_absent:
            require_absent(version, args.require_absent)
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f'Release refused: {error}\n')
    print(version)


if __name__ == '__main__':
    main()
