#!/usr/bin/env python3
"""Validate release versions and fail closed before publishing a new OCI version."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SEMVER = r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
IMAGES = ('obscura-sbx-kit-mixin', 'obscura-sbx-kit')
OCI_INDEX = 'application/vnd.oci.image.index.v1+json'
OCI_MANIFEST = 'application/vnd.oci.image.manifest.v1+json'


def check_layout(layout, version):
    """Inspect tagged content, not just the OCI layout's index.json wrapper.

    Skopeo adds compression annotations for zstd children on registry copies,
    changing even an OCI index and making --preserve-digests fail.
    """
    layout = Path(layout)
    wrapper = json.loads((layout / 'index.json').read_text())
    tagged = [d for d in wrapper['manifests'] if
              d.get('annotations', {}).get('org.opencontainers.image.ref.name') == version]
    if len(tagged) != 1:
        raise ValueError('layout must contain exactly one matching version tag')

    def read(descriptor):
        digest = descriptor['digest']
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            raise ValueError('manifest digest must be SHA256')
        raw = (layout / 'blobs' / 'sha256' / digest[7:]).read_bytes()
        if len(raw) != descriptor['size'] or hashlib.sha256(raw).hexdigest() != digest[7:]:
            raise ValueError('manifest size or digest mismatch')
        value = json.loads(raw)
        if value.get('mediaType') != descriptor['mediaType']:
            raise ValueError('manifest media type disagrees with descriptor')
        return value

    content = read(tagged[0])
    if content.get('mediaType') == OCI_INDEX:
        if not content.get('manifests'):
            raise ValueError('tagged index is empty')
        manifests = [(descriptor, read(descriptor))
                     for descriptor in content['manifests']]
    elif content.get('mediaType') == OCI_MANIFEST:
        # Single-platform exports without provenance tag the image directly.
        manifests = [(tagged[0], content)]
    else:
        raise ValueError('tagged manifest must be an OCI index or OCI image manifest')
    for descriptor, manifest in manifests:
        if manifest.get('mediaType') != OCI_MANIFEST:
            raise ValueError('index children must be OCI manifests')
        attestation = descriptor.get('annotations', {}).get(
            'vnd.docker.reference.type') == 'attestation-manifest'
        expected = 'application/vnd.in-toto+json' if attestation else 'application/vnd.oci.image.layer.v1.tar+gzip'
        if any(layer['mediaType'] != expected for layer in manifest['layers']):
            raise ValueError('registry digest preservation requires gzip image layers (or in-toto attestations)')


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
    parser.add_argument('--check-layout', metavar='LAYOUT')
    args = parser.parse_args()
    try:
        version = version_for(args.tag)
        if args.check_layout:
            check_layout(args.check_layout, version)
        if args.require_absent:
            require_absent(version, args.require_absent)
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f'Release refused: {error}\n')
    print(version)


if __name__ == '__main__':
    main()
