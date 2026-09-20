#!/usr/bin/env bash
# #122 — worktree 隔離セッションのガードを、**Linux と macOS の両方**で発火させて測る。
#
# **この測定が答えようとしているのは 1 つだけ**——`SKILL.md` がガードについて
# 述べている運用指示が、**macOS 以外でも成り立つか**。境界の特徴づけは追わない
# （#112 が「運用には要らない」と判定済みで、#110 で 4 度壊れた型である）。
#
# ## probe の一覧はここに無い
#
# **`measure-guard-os-inner.sh` が正である。** このスクリプトは、その同じファイルを
# **コンテナに流し込む**（既定）か**ホストでそのまま実行する**（`--host`）かを
# 選ぶだけ。**2 箇所に置くと、観測された差が OS の差なのか probe の差なのか
# 判別できなくなる。**
#
# ## 交絡について
#
# **振っている次元が「OS」だけになるように組んである:**
#
# | 次元 | 揃え方 |
# | --- | --- |
# | harness 版 | 像が `2.1.278` に固定する。ホスト側も同じ版であることを出力で確かめる |
# | アーキテクチャ | ホストが Apple Silicon なので、どちらも `aarch64` |
# | 認証形態 | どちらも同じサブスクリプションの資格情報 |
# | 当てる形 | 同じ `measure-guard-os-inner.sh` |
#
# **揃っていないものが 1 つ残る: git の版**（macOS 2.54.0 / 像 2.39.5）。
# ガードは harness の機能で git の機能ではないが、**揃っていないことは記録する。**
#
# ## 資格情報の運び方（コンテナ側）
#
# **ホストの `~/.claude` をマウントしても認証は渡らない**——実測（2026-09-20）で
# `Not logged in · Please run /login` になった。**macOS の資格情報は Keychain にあり、
# マウントできる形でファイルシステム上に無い**（`~/.claude.json` も併せて
# マウントして確かめた）。だから **`claude setup-token` の長期トークンを
# 環境変数で渡す**。**トークンはファイルから読む。スクリプトにも引数にも書かない。**
#
# 使い方:
#
#     bash scripts/measure-guard-os.sh <出力先>           # Linux（コンテナ）
#     bash scripts/measure-guard-os.sh --host <出力先>    # macOS（このホスト）
#
# 環境変数:
#
#     GUARD_PROBE_TOKEN_FILE  トークンを書いたファイル（既定: ~/.guard-probe-token）
#     GUARD_PROBE_IMAGE       使う像（既定: guard-probe:2.1.278）

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
INNER="${HERE}/measure-guard-os-inner.sh"

MODE=container
if [ "${1:-}" = "--host" ]; then
  MODE=host
  shift
fi

OUT="${1:?使い方: bash scripts/measure-guard-os.sh [--host] <出力先ディレクトリ>}"
mkdir -p "$OUT"
OUT_ABS="$(cd "$OUT" && pwd)"

if [ "$MODE" = host ]; then
  # ホスト（macOS）で回す。**トランスクリプトは実ホームに書かれる**ので、
  # 収集は `--cwd-prefix` で probe の分だけに絞る。
  PROBE_ROOT="${OUT_ABS}/repo"
  echo "モード: ホスト（このマシン）"
  echo "出力先: $OUT_ABS"
  echo
  PROBE_ROOT="$PROBE_ROOT" PROBE_OUT="$OUT_ABS" bash "$INNER"

  echo
  echo "=== 収集（probe の分だけ）==="
  python3 "${HERE}/collect-guard-rejections.py" \
    --cwd-prefix "$PROBE_ROOT" \
    --json "$OUT_ABS/host-rejections.json"
  exit 0
fi

IMAGE="${GUARD_PROBE_IMAGE:-guard-probe:2.1.278}"
TOKEN_FILE="${GUARD_PROBE_TOKEN_FILE:-$HOME/.guard-probe-token}"

if [ ! -s "$TOKEN_FILE" ]; then
  echo "トークンのファイルが無いか空: $TOKEN_FILE" >&2
  echo "別のターミナルで 'claude setup-token' を実行し、出たトークンを書き込むこと。" >&2
  exit 2
fi

echo "モード: コンテナ"
echo "像:     $IMAGE"
echo "出力先: $OUT_ABS"
echo

# `-i` が要る。**無いとヒアドキュメント（ここでは標準入力に流す本体）がコンテナに
# 届かず、何も実行されないまま終了コード 0 で返る**——「回したのに 0 件」と
# 区別がつかない形で失敗する（実測）。
docker run --rm -i \
  -e CLAUDE_CODE_OAUTH_TOKEN="$(cat "$TOKEN_FILE")" \
  -e PROBE_ROOT=/root/work \
  -e PROBE_OUT=/out \
  -e PROBE_COPY_TRANSCRIPTS=1 \
  -v "$OUT_ABS":/out \
  "$IMAGE" \
  bash -s < "$INNER"

echo
echo "=== 収集 ==="
python3 "${HERE}/collect-guard-rejections.py" --root "$OUT_ABS/projects" \
  --json "$OUT_ABS/linux-rejections.json"
