#!/usr/bin/env bash
# PR を出す前の前提条件を判定する。
#
#     bash <このスキルの base ディレクトリ>/scripts/check-pr-preconditions.sh [期待するブランチ名]
#
# `SKILL.md` 手順 6 が散文で書いていた 3 つのコマンドと、その突き合わせを 1 本にした。
#
# ## なぜスクリプトなのか
#
# **散文の側は、値の突き合わせを「読む側でやれ」と指示していた**——
# **worktree 隔離セッションのガードが、`test "$(…)" != "$(…)"` の形を拒否する**ためである
# （#110 で実測）。**だからあの節は 1 行ずつに割られている。**
#
# **スクリプトなら、突き合わせをスクリプトの中でやれる。**
# **呼ぶ側は素の 1 行で済む**ので、ガードに当たらない。
#
# ## 何を守るか
#
# - **worktree にいるか**——`--git-dir` と `--git-common-dir` が違えば worktree。
# - **正しい worktree にいるか**——**期待するブランチ名を渡せば突き合わせる。**
#   **worktree かどうかだけの判定は、周のコミットを持たない別の worktree を素通りさせる**
#   （#96 で壊れた周は worktree の中にいた）。
# - **detached を見分ける**——**「一致しない」と「名前が出ていないだけ」は別**である。
# - **終了コードで区別する**——0: 通過 / 1: メインの作業ツリー / 2: ブランチ不一致 /
#   3: detached / **4: 判定できなかった**。**「落ちた」だけでは何をすべきか決まらない。**
#   **一律に 1 で落とすと、呼んだ側は次に何をすべきか決められない。**
# - **判定できなかったことを「メインの作業ツリー」と答えない。** git が失敗すると
#   **両方が空文字になって一致し、「メインにいる」という*確定的に誤った*判定**が出る。
#   **`find-cycle.py` が「1 件も当たらなかった」と「探せなかった」を分けているのと同じ形。**
#
# ## 何を守らないか
#
# - **その周のコミットが乗っているか**——**ブランチ名しか見ない。**
#   **起点コミットとの突き合わせは呼ぶ側**（計画ファイルの「周の在り処」と照らす）。
# - **PR を出してよいか**——**前提条件だけ**である。受入基準も関門も見ていない。
# - **ガードに拒否されない保証**——**このスクリプト自身が拒否される可能性は残る。**
#   **拒否されたらメッセージ全体を読んで従う**（`SKILL.md` 手順 6）。

set -uo pipefail

EXPECTED="${1:-}"

# **絶対パスで取る。** `--git-dir` と `--git-common-dir` は**片方だけ相対で返ることがある**
# ——**メインの作業ツリーのサブディレクトリから走らせると、前者が絶対・後者が相対
# （`../../.git`）になり、文字列比較が必ず不一致になる。** つまり
# **メインの作業ツリーにいるのに「worktree の中にいる」と答えて rc=0 を返す**
# ——**この関門がいちばん止めたい状況で、素通りする。**
# **実測で再現した**（`/code-review` が指摘。#136）。
# **`Bash` の cwd は呼び出し間で持続する**ので、**直前の `cd docs` だけで起きる。**
if ! GIT_DIR="$(git rev-parse --path-format=absolute --git-dir 2>/dev/null)" \
   || ! COMMON_DIR="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
  echo "git でリポジトリを解決できなかった。" >&2
  echo "**「メインの作業ツリーにいる」とは答えない**——判定できていない。" >&2
  exit 4
fi
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
HEAD_LINE="$(git log --oneline -1 2>/dev/null || echo '(コミットなし)')"

echo "--git-dir:        ${GIT_DIR}"
echo "--git-common-dir: ${COMMON_DIR}"
echo "ブランチ:         ${BRANCH}"
echo "HEAD:             ${HEAD_LINE}"
echo

if [ "$GIT_DIR" = "$COMMON_DIR" ]; then
  echo "**メインの作業ツリーにいる。PR を作ってはならない。**" >&2
  echo "手順 4 の worktree 開始に戻り、変更を worktree へ移送すること。" >&2
  echo "移送の手順は SKILL.md 手順 4 を正とする（裸の git stash を使わない理由も含めて）。" >&2
  exit 1
fi

if ! git symbolic-ref -q HEAD >/dev/null; then
  echo "**detached HEAD である。**" >&2
  echo "場所は合っていて名前が出ていないだけかもしれない——HEAD の行を見て確かめること。" >&2
  echo "乗せ直すなら git switch -c <規約どおりの名前>（git branch -m は detached では fatal）。" >&2
  exit 3
fi

if [ -n "$EXPECTED" ] && [ "$BRANCH" != "$EXPECTED" ]; then
  echo "**ブランチが期待と違う: ${BRANCH} ≠ ${EXPECTED}**" >&2
  echo "別の worktree にいる可能性がある。references/resume.md に従って入り直すこと。" >&2
  exit 2
fi

echo "worktree の中にいる。"
if [ -n "$EXPECTED" ]; then
  echo "ブランチも期待と一致した。"
else
  echo "**ブランチは突き合わせていない**——期待するブランチ名を引数で渡すこと。"
  echo "**worktree かどうかだけの判定は、周のコミットを持たない別の worktree を素通りさせる。**"
fi
echo "起点コミットとの突き合わせは、計画ファイルの「周の在り処」と照らすこと。"
