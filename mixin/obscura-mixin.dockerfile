# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
FROM --platform=$BUILDPLATFORM dhi.io/sbx-templates:shell@sha256:6b18c6805d152ef6f4182fcafc313374a31205900be0dcdad5c1db3bffbe2fbf AS download
ARG TARGETARCH
USER root
COPY scripts/install-browser.py /tmp/install-browser.py
# Optional public trust root; never included in the resulting overlay.
RUN --mount=type=secret,id=build-ca,target=/run/build-ca \
    python3 /tmp/install-browser.py "$TARGETARCH"
COPY --chmod=755 scripts/obscura.py /out/usr/local/bin/obscura
COPY --chmod=644 LICENSE NOTICE /out/opt/obscura/
COPY --chmod=644 licenses/ /out/opt/obscura/licenses/
RUN chmod 0755 /out /out/opt /out/opt/obscura /out/usr /out/usr/local /out/usr/local/bin /out/opt/obscura/licenses
FROM scratch
COPY --from=download /out/ /
