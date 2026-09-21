ARG BASE_IMAGE=ghcr.io/openhands/agent-canvas:1.20.0@sha256:7c3d078f408dbc75233a098b63bb3f3cda475ee5d0024d8b934e148c8f063638
ARG NODE_IMAGE=node:24-alpine@sha256:e67514e5d0f6c46656005e1b693b2ec9d52e80b641307de684d4a015ba7a4eaf
FROM ${NODE_IMAGE} AS frontend
WORKDIR /build
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1
COPY sources/canvas/package.json sources/canvas/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY sources/canvas/ ./
ENV VITE_BASE_PATH=/canvas
RUN npm run build

FROM ${BASE_IMAGE}
USER root
COPY sources/sdk/openhands-sdk/ /tmp/custom-sdk/
COPY sources/sdk/openhands-agent-server/ /tmp/custom-server/
RUN uv pip install --system --no-deps /tmp/custom-sdk /tmp/custom-server \
    && rm -rf /tmp/custom-sdk /tmp/custom-server
# The upstream executable embeds Python (PyInstaller). Use the matching source
# package so SDK changes are actually loaded; do not patch the embedded binary.
COPY scripts/openhands-agent-server /usr/local/bin/openhands-agent-server
RUN chmod 755 /usr/local/bin/openhands-agent-server
COPY --from=frontend /build/build/ /opt/agent-canvas/frontend/
LABEL local.openhands.customization="per-profile-system-prompt-v1"
USER openhands
