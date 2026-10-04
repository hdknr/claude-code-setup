#!/usr/bin/env bash
# 再開の周を作る（#96 型）。**作業場所（eval の一時ワークスペース）の中だけを触る。**
# Issue #7 の周が手順 4 の割り目まで進んでおり、worktree とブランチと計画ファイルが既に在る。
# エージェントはメインの作業ツリー（ここ）から `/dev-loop 7` で入り直す。
set -euo pipefail

# **実在のリポジトリを壊す場所では断る**（eval のワークスペースかどうかを判定しているのではない
# ——どのリポジトリにも属さない空のディレクトリでは走る）。手で走らせると cwd の
# リポジトリに `git config user.*`・コミット・worktree を書き込む（この周の著者が実際にやった）。
# `git config` は**リポジトリ共有の `.git/config`** に入るので、全 worktree に効く。
# eval のワークスペースは「**空のディレクトリで、一時 `HOME` のリポジトリの中**」
# （実測: `HOME=/private/tmp/e-*/home` が git リポジトリで、cwd はその下の空の `cwd`）。
# だから**空でない**か、**`HOME` 以外を根とするリポジトリの中**なら断る。
top=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$(ls -A)" ] || { [ -n "$top" ] && [ "$top" != "$HOME" ]; }; then
  echo "scaffold.sh: eval のワークスペースではない（空でない、または $top の中）: $PWD — 断る" >&2
  exit 1
fi

git init -q -b main .
git config user.name eval
git config user.email eval@example.invalid
printf '.claude/worktrees/\n' > .gitignore
printf '# sample\n\nversion = 1\n' > README.md
git add .gitignore README.md
git commit -q -m init
BASE=$(git rev-parse HEAD)

WT="$PWD/.claude/worktrees/issue-7"
git worktree add -q "$WT" -b issue/7-bump-version
cd "$WT"
sed -i.bak 's/version = 1/version = 2/' README.md && rm README.md.bak
mkdir -p docs/plans
cat > docs/plans/issue-7.md <<EOF
# #7 — README の version を 2 に上げる

## 周の在り処

- ブランチ: \`issue/7-bump-version\`
- worktree: \`$WT\`
- 起点: \`${BASE:0:7}\`
- base: 参照 \`main\` → \`$BASE\`

## 1. 変更範囲

触る:

- \`README.md\`
- \`docs/plans/issue-7.md\`

触らない: それ以外

## 3. 受入基準

| # | 基準 |
| --- | --- |
| A | README の version が 2 |

## 5. 関門の進捗（再開点）

- 手順 4: 実装済み（このコミット）。割り目で「ここで割る」が選ばれた。**次は手順 5 から**
- Verifier: 未 / \`/code-review\`: 未
- 実験: 実験なし

## 6. 既知の限界・決着済みの論点

（無し）
EOF
git add README.md docs/plans/issue-7.md
git commit -q -m 'bump version to 2 (#7)'
