# #122 — ガードの挙動を Linux で測るための像。
#
# **harness 版を固定するのが、この像の存在理由である。** 版を固定しないと、
# 「OS が違う」と「harness 版が違う」が同時に変わり、どちらが効いたか判別できない
# （#122 の前半で、拒否の形は 31 版にまたがると実測済み）。
#
# 既定の 2.1.278 は、比較相手である macOS 側の版に合わせてある。
FROM node:22-slim

ARG CLAUDE_VERSION=2.1.278

RUN apt-get update \
 && apt-get install -y --no-install-recommends git python3 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_VERSION}"

WORKDIR /work
