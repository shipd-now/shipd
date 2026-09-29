# The shipd runner image: a Linux arm64 sandbox that drives headless Claude
# Code sessions inside an Apple `container` VM.
#
# Derived from the axel `claude-runner` Dockerfile. The launcher
# (`tools/container/spike.py`) tags a build `shipd-runner:<sha256(this
# file)[:12]>`, so every edit here produces a new tag and a fresh build.
FROM node:22-bookworm

# Pinned so the image is reproducible; a CLI upgrade edits this default and
# re-tags the image through the Dockerfile hash.
ARG CLAUDE_CODE_VERSION=2.1.284

# The VM's process runs as root. IS_SANDBOX lets Claude Code accept
# `--permission-mode bypassPermissions` there rather than refusing it.
ENV IS_SANDBOX=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl git jq python3 ripgrep \
 && rm -rf /var/lib/apt/lists/*

# gh, from the GitHub apt repository, arm64.
RUN mkdir -p /etc/apt/keyrings \
 && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
 && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
 && echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends gh \
 && rm -rf /var/lib/apt/lists/*

# difftastic, the review engine's structural differ, pinned to the verified
# aarch64 release asset.
RUN curl -fsSL -o /tmp/difft.tar.gz \
      https://github.com/Wilfred/difftastic/releases/download/0.71.0/difft-0.71.0-aarch64-unknown-linux-gnu.tar.gz \
 && mkdir -p /tmp/difft \
 && tar -xzf /tmp/difft.tar.gz -C /tmp/difft \
 && install -m 0755 "$(find /tmp/difft -type f -name difft | head -n 1)" /usr/local/bin/difft \
 && rm -rf /tmp/difft /tmp/difft.tar.gz

RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

WORKDIR /workspace

RUN claude --version && gh --version && difft --version && python3 --version
