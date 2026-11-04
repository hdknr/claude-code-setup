#!/usr/bin/env bash
# 正本リポジトリ（在庫管理の小さな業務システム）を作る。v1 はリリース済み（release-v1）で、v1 の見積りがある。
# 作業中の版 v2 は売上帳票の機能を足し（追加）、在庫照会の期間を 30 日から 90 日に変える（変更）。受注登録は変えない。
# 要求・Q&A・仕様は済んでいる。見積り（feasibility/）はまだ v2 に無い
# ——feasibility が数える番である。
# **作業場所（eval の一時ワークスペース）の中だけを触る。**
#
# FORMAT は Q&A 表の列の形を選ぶ。リポジトリの中では current（現行の列）のまま置く。
# 差分モードが入る前の版（0.7.0）に当てるときだけ、複製の中でこの行を FORMAT=0.7 に差し替える
# （0.7.0 の表には `推奨`・`推奨の理由` の列が無い。形が合わないと検査で止まり、振る舞いと関係なく赤になる）。
# 差し替え方と結果は docs/plans/issue-274.md を正とする。
FORMAT=current
set -euo pipefail

# **実在のリポジトリを壊す場所では断る**（dev-loop の evals/resume-no-new-worktree/scaffold.sh と同じ判定）。
# eval のワークスペースは「空のディレクトリで、一時 HOME のリポジトリの中」。
top=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$(ls -A)" ] || { [ -n "$top" ] && [ "$top" != "$HOME" ]; }; then
  echo "scaffold.sh: eval のワークスペースではない（空でない、または $top の中）: $PWD — 断る" >&2
  exit 1
fi

# qa_row No 起票元 質問 選択肢 推奨 推奨の理由 回答 反映先 状態 費用への影響
qa_header() {
  if [ "$FORMAT" = current ]; then
    echo "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響"
  else
    echo "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響"
  fi
}
qa_row() {
  if [ "$FORMAT" = current ]; then
    echo "$1,$2,$3,$4,$5,$6,$7,$8,$9,${10}"
  else
    echo "$1,$2,$3,$4,$7,$8,$9,${10}"
  fi
}

git init -q -b main .
git config user.name eval
git config user.email eval@example.invalid

cat > CLAUDE.md <<'EOF'
# 在庫管理システムの正本リポジトリ

- ツリーは spec-loop の references/tree.md のとおり（docs/v1 はリリース済み、作業中の版は docs/v2）。
- ドキュメントのツール: 使わない（MkDocs は入れない。ファイルを直接編集する）。
- レビュー会のスライド: spec-loop 同梱のスクリプトで作る。出力先は既定のとおり。
- 規模の数え方: 要求のファイル 1 つ（= 機能 1 つ）を 10 人日と数える。単価は 1 人日 50000 円。
- 形式検査の道具: 入れていない。照合先（既存システムのコード・規約の文書）: 無い。
- commit・push はしない（変更したファイルを示して止まる）。
EOF

mkdir -p docs/v1/shared docs/v1/requirements docs/v1/spec docs/v1/feasibility docs/v1/proposal
{
  qa_header
  qa_row Q-001 要求確定 在庫を照会できる期間はどれだけですか？ "A: 30 日 / B: 1 年" A 照会の多くは直近の確認のため "A（業務部が回答）" requirements/stock.md 反映済み ""
  qa_row Q-002 要求確定 受注を取り消せるのは誰ですか？ "A: 担当者 / B: 管理者のみ" B 誤った取り消しを防ぐため "B（業務部が回答）" requirements/order.md 反映済み ""
} > docs/v1/shared/qa.csv
printf '# 受注登録\n\n- 担当者が受注を登録する。\n- 受注を取り消せるのは管理者のみ（Q-002）。\n' > docs/v1/requirements/order.md
printf '# 在庫照会\n\n- 担当者が商品ごとの在庫数を照会する。\n- 照会できる期間は過去 30 日（Q-001）。\n' > docs/v1/requirements/stock.md
printf '# 受注登録の仕様\n\n- 取り消しは管理者の権限を持つ利用者だけが行える。それ以外は拒否する。\n' > docs/v1/spec/order.md
printf '# 在庫照会の仕様\n\n- 照会の期間は過去 30 日。30 日より前の日付を指定したら拒否する。\n' > docs/v1/spec/stock.md
printf 'No,区分,項目,金額,根拠\nE-001,開発費,受注登録,500000,requirements/order.md（10 人日）\nE-002,開発費,在庫照会,500000,requirements/stock.md（10 人日）\n' > docs/v1/feasibility/estimate.csv
printf 'No,工程,開始,終了,前提\nT-001,受注登録,2026-04-01,2026-04-14,\nT-002,在庫照会,2026-04-15,2026-04-28,T-001\n' > docs/v1/feasibility/schedule.csv
printf '# 背景と目的\n\n紙の台帳で管理している受注と在庫を、担当者が画面で扱えるようにする。\n' > docs/v1/proposal/01-background.md
git add -A
git commit -q -m 'v1'
git tag release-v1

# 作業中の版 v2: 売上帳票を足し、在庫照会の期間を変える（要求・Q&A・仕様は済み）
mkdir -p docs/v2/shared docs/v2/requirements docs/v2/spec
printf '# 売上帳票\n\n- 管理者が月次の売上帳票を CSV で出力する（Q-003）。\n' > docs/v2/requirements/report.md
printf '# 在庫照会\n\n- 担当者が商品ごとの在庫数を照会する。\n- 照会できる期間は過去 90 日（Q-004）。\n' > docs/v2/requirements/stock.md
printf '# 在庫照会の仕様\n\n- 照会の期間は過去 90 日。90 日より前の日付を指定したら拒否する。\n' > docs/v2/spec/stock.md
printf '# 売上帳票の仕様\n\n- 管理者だけが出力できる。それ以外は拒否する。\n- 対象の月に売上が無ければ、見出しだけの CSV を返す。\n' > docs/v2/spec/report.md
{
  qa_header
  qa_row Q-003 要求確定 売上帳票はどの形式で出力しますか？ "A: CSV / B: PDF" A 表計算で集計し直すため "A（業務部が 2026-11-01 に回答）" requirements/report.md 反映済み ""
  qa_row Q-004 要求確定 在庫を照会できる期間を延ばしますか？ "A: 30 日のまま / B: 90 日に延ばす" B "季節の比較に 3 か月分が要るため" "B（業務部が 2026-11-01 に回答）" requirements/stock.md 反映済み ""
} > docs/v2/shared/qa.csv
git add -A
git commit -q -m 'v2: 売上帳票と在庫照会の期間（要求・仕様）'
