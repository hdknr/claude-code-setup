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
#   **当たり方は部分一致で、広い**——`issue-9` は `issue/99-foo` にも当たる。
#   **失敗する側は安全**（新しい周を再開の道へ送るだけで、踏み潰さない）だが、
#   **広いことは隠さない**（`find-cycle.py` と同じ扱い）。
# - **判定できなかったことを「当たらなかった」と答えない。** `git` が失敗したら
#   **作らずに止まる**（終了コード 5）。**「無い」と「見られなかった」は別である。**
#   **2 つの守りは別の終了コードを返す**（5: root を解決できない / 6: 既存を見られない）
#   ——**同じにすると、片方を壊しても他方が同じ答えを返して変異が殺せない。**
# - **絶対パスで組み立てる。** 相対パスはシェルの cwd を起点に解決されるので、
#   別の worktree の中から走らせると**入れ子で生える**。
# - **メインの作業ツリーを `--path-format=absolute` で解決する。**
#   **`--git-common-dir` は相対で返ることがあり、その相対は cwd を起点にする**
#   ——root を起点に解決すると、**サブディレクトリから走らせたときに
#   リポジトリの*親*を指す**（実測で再現した）。
# - **規約どおりの名前で切る。** `issue/<番号>-<説明>`。
#   **道具に任せると `worktree-` 接頭辞が付いて規約から外れる**（#96 で 3 例）。
# - **肯定的な確認の材料を出す。** 作って終わりにしない——
#   **実際のブランチ名と起点コミットを出力し、呼んだ側が計画ファイルと突き合わせられるようにする。**
#   **「切ったブランチ名と一致するか」を自分で比べても意味が無い**（`-b` で切った直後なので
#   必ず一致する）。**突き合わせる相手は計画ファイルの側にある。**
#
# ## 何を守らないか
#
# - **`--path-format=absolute` は git 2.31 以降でしか使えない。**
#   **古い git では終了コード 5 になり、「root を解決できない」と出る**
#   ——**リポジトリは正常なのに、そう見える。** **版の要求はここに書いてある。**
# - **`EnterWorktree` / `ExitWorktree` の意味論**——呼べないので何も言えない。
#   **条件は `SKILL.md` 手順 4 と `references/resume.md` を正とする。**
# - **未コミットの変更の移送**——`SKILL.md` 手順 4 の移送手順を正とする
#   （**裸の `git stash` を使わない**理由も含めて、あちらにある）。
# - **入場そのもの**——上記。
# - **既存の一覧を取る側が、通常の運用で失敗すること**——**`git rev-parse` が成功していれば
#   まず起きない。** **背後の守りとして置いてあり、テストは「root の守りを壊したときに
#   こちらが受け止める」形で当てている**（終了コード 6 で区別できる）。

set -euo pipefail

NUMBER="${1:?使い方: bash prepare-worktree.sh <issue-number> <説明>}"
SLUG="${2:?使い方: bash prepare-worktree.sh <issue-number> <説明>}"

if ! printf '%s' "$NUMBER" | grep -Eq '^[0-9]+$'; then
  echo "Issue 番号は数字だけで指定する: $NUMBER" >&2
  exit 2
fi

# **`--path-format=absolute` で取る。** `--git-common-dir` は**相対で返ることがあり、
# その相対は*cwd*を起点にする**——**リポジトリの root ではない。**
# 一度 `$ROOT` を起点に解決しており、**メインの作業ツリーのサブディレクトリから
# 走らせると `MAIN` がリポジトリの*親*になっていた**（実測で再現。`/code-review` が指摘）。
# **結果、リポジトリの外に `.claude/worktrees/` を作ろうとする**
# ——実リポジトリなら `~/Projects/hdknr/` である。
if ! COMMON="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
  echo "git でリポジトリを解決できなかった。作らない。" >&2
  exit 5
fi
MAIN="$(cd "$(dirname "$COMMON")" && pwd -P)"

BRANCH="issue/${NUMBER}-${SLUG}"
PATH_ABS="${MAIN}/.claude/worktrees/issue-${NUMBER}"

echo "メインの作業ツリー: ${MAIN}"
echo "作ろうとしているもの: ${PATH_ABS}  [${BRANCH}]"
echo

# **先に見る。** 当たったら作らない。
if ! WT_ALL="$(git worktree list 2>/dev/null)" || ! BR_ALL="$(git branch --all --list "*${NUMBER}*" 2>/dev/null)"; then
  echo "git で既存の worktree / ブランチを見られなかった。作らない。" >&2
  echo "**「当たらなかった」とは答えない**——見られていない。" >&2
  # **root の解決とは別の終了コードにする。** 同じにすると**2 つの守りが
  # 区別できず、片方を壊しても他方が同じ答えを返して変異が殺せない**
  # （実際にそうなっていた）。
  exit 6
fi
EXISTING_WT="$(printf '%s\n' "$WT_ALL" | grep -F "issue-${NUMBER}" || true)"
EXISTING_BR="$BR_ALL"
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
