#!/usr/bin/env bash
# #122 — ガードに当てる probe の本体。**probe の一覧はこのファイルにしかない。**
#
# **2 箇所に置かない理由**: macOS 側と Linux 側で probe がずれたら、
# **観測された差が「OS の差」なのか「当てた形の差」なのか判別できなくなる**。
# 外側（`measure-guard-os.sh`）は、この同じファイルを
# **コンテナに流し込む**か**ホストでそのまま実行する**かを選ぶだけである。
#
# 入力（環境変数）:
#
#     PROBE_ROOT              probe 用の git リポジトリを作る場所
#     PROBE_OUT               各 probe の出力を書く場所
#     PROBE_COPY_TRANSCRIPTS  非空なら `$HOME/.claude/projects` を `$PROBE_OUT/projects`
#                             へ複製する。**コンテナで要る**——`--rm` で容器ごと
#                             消えるので、**同じ実行の中で持ち出さないと記録が残らない**。
#                             ホストでは設定しない（実ホームを複製する意味が無く、
#                             収集は `--cwd-prefix` で probe の分だけに絞れる）。
#
# **`PROBE_ROOT` は OS が判別できる場所にすること**——収集側は `cwd` を
# OS の代理変数として読む（`/root` や `/home` なら Linux、`/Users` や
# `/private` なら macOS）。`/work` のような中立なパスに置くと「不明」になる。

set -uo pipefail

ROOT="${PROBE_ROOT:?PROBE_ROOT が未設定}"
OUT="${PROBE_OUT:?PROBE_OUT が未設定}"

echo "=== 環境 ==="
uname -sm
claude --version
git --version
date -u +%Y-%m-%dT%H:%M:%SZ
echo "PROBE_ROOT=${ROOT}"

rm -rf "${ROOT}"
mkdir -p "${ROOT}" "${OUT}"
cd "${ROOT}"
git init -q
git config user.email probe@example.invalid
git config user.name probe
echo hello > README.md
git add -A
git commit -qm init

run_probe() {
  local name="$1"
  local command="$2"
  local tools="${3:-Bash}"
  echo
  echo "=== probe ${name} ==="
  echo "コマンド: ${command}"
  cd "${ROOT}"
  claude -w "${name}" --allowedTools ${tools} \
    -p "${command}" \
    < /dev/null > "${OUT}/${name}.out" 2>&1
  echo "rc=$?"
  tail -c 500 "${OUT}/${name}.out"
}

# ---- 拒否されるはずの形（#112 が macOS で観測した形 ＋ `-C .`）----
BASH_ASK='Run exactly this bash command, then report its output or the refusal verbatim in a fenced block: '

# **コマンド本体は単引用で書く。** 二重引用に入れると `$(…)` や `$F` が
# **この場で展開され、モデルに渡るのは展開後の文字列になる**——当てたい形が消える。
# パスを埋める必要がある 2 件（R2 / R5）だけ、埋める箇所を分けて連結する。

run_probe R1 "${BASH_ASK}"'test "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" && echo differ'
run_probe R2 "${BASH_ASK}"'S=probe; python3 '"${ROOT}"'/$S.py'
run_probe R4 "${BASH_ASK}"'F=/etc/hostname; sed -n 1,2p $F'
run_probe R5 "${BASH_ASK}"'git -C '"${ROOT}"' rev-parse --git-dir'
run_probe R6 "${BASH_ASK}"'git -C . rev-parse --git-dir'

# **ファイル編集の拒否**。#112 で「規則文を持たないメッセージ形」が観測されたのは
# この経路で、**Bash の拒否とは原因が別**（共有チェックアウト側のパスを編集したとき）。
# **これを当てないと、`SKILL.md` の「メッセージの形が 1 つだと思わない」を
# 他の OS で確かめたことにならない。**
run_probe R7 \
  "Use the file editing tool to append the line 'probe' to the file ${ROOT}/README.md. Report the result or the refusal verbatim in a fenced block." \
  "Bash Edit Write Read"

# ---- 通るはずの形（陽性対照）----
# **これが全部落ちたら、観測されたことは OS の差ではなく測定の失敗である。**
run_probe C1 "${BASH_ASK}"'echo a && echo b'
run_probe C2 "${BASH_ASK}"'git rev-parse --git-dir'

if [ -n "${PROBE_COPY_TRANSCRIPTS:-}" ]; then
  echo
  echo "=== トランスクリプトを持ち出す ==="
  mkdir -p "${OUT}/projects"
  cp -a "${HOME}/.claude/projects/." "${OUT}/projects/" 2>/dev/null || true
  echo "jsonl: $(find "${OUT}/projects" -name '*.jsonl' | wc -l)"
fi

echo
echo "=== 済 ==="
