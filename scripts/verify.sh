#!/usr/bin/env bash
set -euo pipefail
# Run from repository root, inside the build/test environment.
arch="${1:-$(uname -m)}"
case "$arch" in aarch64|arm64) arch=arm64 ;; x86_64|amd64) arch=amd64 ;; *) exit 2 ;; esac
mkdir -p .local
python3 -m unittest discover -s tests -v
secret=()
if [[ -n "${BUILD_CA_FILE:-}" ]]; then
  secret=(--secret "id=build-ca,src=$BUILD_CA_FILE")
fi
for kind in mixin standalone; do
  stem=obscura
  [[ "$kind" != mixin ]] || stem=obscura-mixin
  docker buildx build "$kind" -f "$kind/$stem.yaml" \
    "${secret[@]}" --platform "linux/$arch" -t "$stem:0.1.0" \
    --output "type=oci,dest=.local/$kind-$arch,tar=false"
  kit-tck validate --layout ".local/$kind-$arch" 0.1.0 --verbose
done
docker buildx build standalone -f standalone/obscura.dockerfile \
  "${secret[@]}" --platform "linux/$arch" -t obscura-runtime:0.1.0 --load
docker run --rm --entrypoint python3 -v "$PWD/tests:/tests:ro" \
  obscura-runtime:0.1.0 /tests/runtime.py
docker buildx build . -f tests/mixin-runtime.dockerfile \
  --build-context "browser-overlay=oci-layout://.local/mixin-$arch:0.1.0" \
  --platform "linux/$arch" -t obscura-overlay-test:0.1.0 --load
docker run --rm --entrypoint python3 -v "$PWD/tests:/tests:ro" \
  obscura-overlay-test:0.1.0 /tests/runtime.py
for image in obscura-runtime:0.1.0 obscura-overlay-test:0.1.0; do
  docker run --rm --entrypoint python3 "$image" -c \
    'from pathlib import Path; assert all(Path("/opt/obscura",p).is_file() for p in ("LICENSE", "NOTICE", "licenses/V8.txt"))'
done
npm ci --ignore-scripts
OBSCURA_DOCKER_IMAGE=obscura-runtime:0.1.0 node tests/cdp.mjs
OBSCURA_DOCKER_IMAGE=obscura-overlay-test:0.1.0 node tests/cdp.mjs
