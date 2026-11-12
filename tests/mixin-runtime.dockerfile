# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
# Test the actual frontend-produced OCI overlay, not a parallel installation.
FROM browser-overlay AS overlay
FROM dhi.io/sbx-templates:shell@sha256:6b18c6805d152ef6f4182fcafc313374a31205900be0dcdad5c1db3bffbe2fbf
USER root
COPY --from=overlay / /
USER agent
ENTRYPOINT ["bash"]
CMD ["-l"]
