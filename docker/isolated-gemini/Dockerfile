# ABOUTME: Minimal Gemini CLI image for isolated code reviews (arm64 native)
# ABOUTME: Based on official Dockerfile, trimmed to review-only use case

FROM node:20-slim

ARG GEMINI_CLI_VERSION=0.45.0

RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  ripgrep \
  jq \
  ca-certificates \
  curl \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local/share/npm-global \
  && chown -R node:node /usr/local/share/npm-global
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

USER node

RUN npm install -g @google/gemini-cli@${GEMINI_CLI_VERSION} \
  && gemini --version > /dev/null \
  && npm cache clean --force

WORKDIR /workspace

ENTRYPOINT ["gemini"]
