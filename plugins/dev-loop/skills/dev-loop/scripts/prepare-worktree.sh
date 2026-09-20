#!/usr/bin/env bash
# 新規の周のために、規約どおりの worktree を作って確かめる。
#
#     bash <このスキルの base ディレクトリ>/scripts/prepare-worktree.sh <issue-number> <説明>
#
# **置き場所に理由がある。** `dev-loop` は**どのリポジトリでも使うスキル**なので、
# **対象リポジトリの `scripts/` に置いてはならない**——そこに在るとは限らない。
# **一度そこに置いて PR に出し、マージ後に気づいた**（#136 段 1）。
#
# ## このスクリプトがやらないこと
#
# **`EnterWorktree` は呼べない。** あれはハーネスの道具で、シェルからは起動できない。
# **このスクリプトは worktree を*作って確かめる*ところまで**で、
# **セッションをそこへ入れるのは道具の仕事**である。作ったあとに
# `EnterWorktree` へ `path` を渡すこと。
#
# **既存の worktree には入らない。** 再開の周は形が違う——
# **`find-cycle.py` で探し、`references/resume.md` に従う。**
# **このスクリプトは、当たるものが無かったときだけ使う。**
#
# ## 何を守るか
#
# - **先に見る。** 同じ番号の worktree / ブランチが在れば**作らずに止まる**
#   （**再開の周を新規として踏み潰さない**）。
# - **絶対パスで作る。** 相対パスはシェルの cwd を起点に解決されるので、
#   別の worktree の中から走らせると**入れ子で生える**。
# - **規約どおりの名前で切る。** `issue/<番号>-<説明>`。
#   **道具に任せると `worktree-` 接頭辞が付いて規約から外れる**（#96 で 3 例）。
# - **肯定的な確認の材料を出す。** 作って終わりにしない——
#   **実際のブランチ名と起点コミットを出力し、呼んだ側が計画ファイルと突き合わせられるようにする。**
#   **「切ったブランチ名と一致するか」を自分で比べても意味が無い**（`-b` で切った直後なので
#   必ず一致する）。**突き合わせる相手は計画ファイルの側にある。**
#
# ## 何を守らないか
#
# - **`EnterWorktree` / `ExitWorktree` の意味論**——呼べないので何も言えない。
#   **条件は `SKILL.md` 手順 4 と `references/resume.md` を正とする。**
# - **未コミットの変更の移送**——`SKILL.md` 手順 4 の移送手順を正とする
#   （**裸の `git stash` を使わない**理由も含めて、あちらにある）。
# - **入場そのもの**——上記。

set -euo pipefail

NUMBER="${1:?使い方: bash prepare-worktree.sh <issue-number> <説明>}"
SLUG="${2:?使い方: bash prepare-worktree.sh <issue-number> <説明>}"

if ! printf '%s' "$NUMBER" | grep -Eq '^[0-9]+$'; then
  echo "Issue 番号は数字だけで指定する: $NUMBER" >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
COMMON="$(git rev-parse --git-common-dir)"
# `--git-common-dir` は worktree の中からでも**共有の .git** を指す。
# その親が**メインの作業ツリー**である。**cwd がどこでも同じ場所を指す。**
case "$COMMON" in
  /*) MAIN="$(dirname "$COMMON")" ;;
  *)  MAIN="$(cd "$ROOT/$(dirname "$COMMON")" && pwd -P)" ;;
esac

BRANCH="issue/${NUMBER}-${SLUG}"
PATH_ABS="${MAIN}/.claude/worktrees/issue-${NUMBER}"

echo "メインの作業ツリー: ${MAIN}"
echo "作ろうとしているもの: ${PATH_ABS}  [${BRANCH}]"
echo

# **先に見る。** 当たったら作らない。
EXISTING_WT="$(git worktree list | grep -F "issue-${NUMBER}" || true)"
EXISTING_BR="$(git branch --all --list "*${NUMBER}*" || true)"
if [ -n "$EXISTING_WT" ] || [ -n "$EXISTING_BR" ]; then
  echo "既に当たるものがある。**作らない。**" >&2
  [ -n "$EXISTING_WT" ] && echo "  worktree:" && printf '    %s\n' "$EXISTING_WT" >&2
  [ -n "$EXISTING_BR" ] && echo "  ブランチ:" && printf '    %s\n' "$EXISTING_BR" >&2
  echo >&2
  echo "再開の周かもしれない。find-cycle.py で探し、references/resume.md に従うこと。" >&2
  exit 3
fi

git worktree add "$PATH_ABS" -b "$BRANCH" >&2

# **肯定的な確認。** 作って終わりにしない。
ACTUAL_BRANCH="$(git -C "$PATH_ABS" rev-parse --abbrev-ref HEAD)"
ACTUAL_HEAD="$(git -C "$PATH_ABS" log --oneline -1)"

echo
echo "=== 肯定的な確認 ==="
echo "ブランチ: ${ACTUAL_BRANCH}"
echo "起点:     ${ACTUAL_HEAD}"

echo
echo "次にすること: EnterWorktree に path=${PATH_ABS} を渡して入る。"
echo "計画ファイルの「周の在り処」に、上のブランチ名・パス・起点を書くこと。"
