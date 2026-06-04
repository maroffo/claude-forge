# ABOUTME: Minimal Claude Code image for isolated code reviews
# ABOUTME: No user config, no memories, no rules — clean-slate reviewer

FROM node:20-slim

ARG CLAUDE_CODE_VERSION=latest

RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  ripgrep \
  jq \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share/npm-global

RUN mkdir -p /home/node/.claude && \
  chown -R node:node /home/node/.claude

USER node
WORKDIR /workspace

ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin
ENV NODE_OPTIONS=--max-old-space-size=4096

RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

COPY --chown=node:node entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
