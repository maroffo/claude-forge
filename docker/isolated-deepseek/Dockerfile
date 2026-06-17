# ABOUTME: Minimal pi (DeepSeek) image for isolated second opinions (arm64 native)
# ABOUTME: Runs pi-coding-agent against the deepseek provider, review-only use case

# pi-coding-agent requires Node >=22.19 (undici markAsUncloneable), so this image
# pins node:22-slim rather than the node:20-slim used by the other reviewer images.
FROM node:22-slim

ARG PI_VERSION=0.79.6

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

RUN npm install -g @earendil-works/pi-coding-agent@${PI_VERSION} \
  && pi --version > /dev/null \
  && npm cache clean --force

WORKDIR /workspace

ENTRYPOINT ["pi"]
