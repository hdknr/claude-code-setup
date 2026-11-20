# Issue #1194 — dev-loop: 委譲文とスキル本文の行を見直して刈り込む段が無い（「削らない」の先）

cruise（親 Issue #1290）の子として回す周。**不在の周**（`--absent`）。AskUserQuestion は使わない。
spec-loop から来た Issue ではない（本文の先頭に `<!-- spec-loop-handoff:` の印が無い）。`作り直しの元:` の行も無い。`find-cycle.py 1194` は 5 本とも当たらず、新規の周。

台帳の確かめた線（親の委譲文で受け取った）: 直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）。`.claude/dev-loop.md`（main）の宣言: `マージの反映: ドキュメントとプラグインの配布`。
直す線: `既定`（出所: cruise の確かめた線）。

版の上げ方: **dev-loop を minor**（2.17.0 → 2.18.0。手順・スクリプト・台帳の新設）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/line-effects.py` — 新設。台帳の検査・最後に効いた周の集計・外す候補とまとめる候補
- `plugins/dev-loop/skills/dev-loop/references/line-registry.csv` — 新設。`prompts/*.md` の全項の台帳
- `plugins/dev-loop/skills/dev-loop/references/prune.md` — 新設。記録の書き方・見直しの段・行を外す手順（原本）
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「削らない」を「黙って削らない」に置き換え。報告に「反証ごとの番号」を足す
- `plugins/dev-loop/skills/dev-loop/prompts/implementer.md` — 同趣旨の「削らない」の置き換え
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 5 の「削らない」の置き換え・手順 8 に効いた行の記録・版の行
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/check-prompt-lines.py` — 新設。CI の歯止め（台帳の整合・行を外す PR の eval）
- `scripts/test-line-effects.py` — 新設。回帰テスト（変異テストを含む）
- `scripts/check-all.py` — 収録
- `.github/workflows/plugins.yml` — CI のステップ
- `CLAUDE.md` — スクリプトとテストの一覧
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す）
- `docs/plans/issue-1194.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 本文は変えない（台帳に載せるだけ。「削らない」の記述が無い）
- `plugins/dev-loop/evals/` — eval ケースは足さない（外す行が 1 つも無い周。外す PR が足す）
- `plugins/spec-loop/` — spec-loop の見直しの規定（`spec-exit.md`）には触れない
- 既存の計画ファイル（`docs/plans/issue-*.md`）への `効いた行` の後付け——記録は周が書くもので、遡って埋めない（既知の限界）

依存の追加・更新: なし。spec-loop の正本はこのリポジトリに無い（`仕様の振る舞い:` の申告は要らない）。

## 周の大きさ（同じことを述べている箇所の数）

- 記録の行の形: `line-effects.py` の docstring と正規表現（原本）・`references/prune.md` の例（写し。テストが正規表現に当てる）。**2 箇所**。
- 「黙って削らない」の置き換え: `prompts/verifier.md`・`prompts/implementer.md`・`SKILL.md` 手順 5 の 3 箇所（テストが verifier.md と SKILL.md を見る）。
- スクリプトの一覧: `CLAUDE.md`（1 箇所）。

## 決めたこと（仕様の穴——不在の線で推奨により決めた）

- **D1 行の同一性をどう持つか**
  - 選択肢: (a) **台帳 CSV（ID・引き・元の事故・登録日・同趣旨）**／(b) 各項に ID の印をコメントで埋め込む／(c) 項の内容のハッシュ
  - 決めた値: **(a)**。推した理由: (b) は委譲文に毎回渡す文字が増え、Verifier の注意を薄める（Issue の問題そのもの）。(c) は言い換えのたびに行が別物になり、最後に効いた周が途切れる。(a) は引き（原文の一部）が原文に 1 回あることを機械で見て、ずれを CI で落とせる。
- **D2 台帳に載せる範囲**
  - 選択肢: (a) **`prompts/*.md` の項は全部必須・`SKILL.md` は任意**／(b) `SKILL.md` の全行も必須
  - 決めた値: **(a)**。推した理由: 受入基準は委譲文の行。`SKILL.md` は 1950 行で「行」の単位が決まらず、全行を載せるとほぼ全部が未記録のままの行になる。載せたい行は台帳に足せる。
- **D3 候補の窓の既定**
  - 選択肢: (a) **30 周**／(b) 10 周／(c) 100 周
  - 決めた値: **(a)**（`--window` で変えられる）。推した理由: Issue は「N 周」とだけ書く。1 周の関門で挙がる指摘は 0〜10 件で、行は約 60 本。数周では効いた行がまばらで、100 周では記録が貯まるのを待つ間に決まりが働かない。実データに当てて決めたものではない（記録がまだ無い）。
- **D4 「効いた」の定義**
  - 決めた値: **採否の表に載せた関門の指摘のうち、その指摘を挙げさせた委譲文の行**（直す・残課題を問わない。誤った指摘として退けたものは数えない）。Verifier は反証ごとに「とくに見てほしいこと」の番号を返す（報告の形に 1 行足した）。
- **D5 見直しの段を周の決まりにするか**
  - 決めた値: **しない**（人間が起こす・Claude が集計する）。推した理由: 周ごとに回すと 1 周が重くなり、記録が貯まる前の集計は空になる。起こす条件（台帳の行が増えたとき・利用者が求めたとき）は `references/prune.md` に書いた。

## デプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の `マージの反映`）。子はマージしない。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 経路・確かめ方 |
| --- | --- | --- |
| A1 | 委譲文（`prompts/*.md`）の各行（項）について、最後に効いた周を引ける——台帳の全項が載り、計画ファイルの `- 効いた行: <ID>` から行ごとに最後に効いた周・効いた周数・効いていない周数を出す。**周の順はコミットの時刻**（名前順でない） | `test-line-effects.py`（R1 の試料は時刻順と名前順で最後に効いた周が違う。変異: 順を名前順にする） |
| A2 | 見直しの段を走らせると、外す候補の行が根拠（効いていない周数・元の事故の番号・最後に効いた周）つきで挙がる。窓と同じ値は候補・登録日より前の周は数えない・一度も効かない行は登録日以降の周数で出す・同趣旨の組はまとめる候補に出す | `test-line-effects.py`（R1〜R4。窓の境界・登録日の変異） |
| A3 | 台帳と原文が食い違わない——項が増えたのに台帳に無い・引きが原文に 1 回でない・引きが項の頭に当たらない行は 1（CI） | `test-line-effects.py`（C1〜C9）・`check-prompt-lines.py`（本物の台帳が 0） |
| A4 | 台帳から行を外す PR は、その行の元の事故を再現する eval（`# 外した行`・`# 元の事故`・`graders`）が差分に無ければ 1。同趣旨の行への統合は eval を求めず、同趣旨が違えば 1 | `test-line-effects.py`（G0〜G13。陽性対照 G1 と G2 は台帳・原文の差分が同じで、eval の有無だけが違う） |
| A5 | 「削らない」が「黙って削らない」に置き換わり、外し方（人間の承認・見直しの段・eval）を指す。`verifier.md`・`implementer.md`・`SKILL.md` 手順 5 の 3 箇所 | `test-line-effects.py`（原本の突き合わせ）・`check-skill-pointers.py`・`check-norm-markers.py` |
| A6 | 記録の書式・見直しの段・外す手順が `references/prune.md` にあり、`SKILL.md` 手順 8 が指す。Verifier が反証ごとの番号を返す | 読む＋`check-skill-pointers.py`。例の行を本体の正規表現に当てる（テスト） |
| A7 | 測るだけ——集計は読むだけで、削る判断・ファイルの書き込みをしない | 読む（`line-effects.py` は `check`・`report`・`items` のいずれもファイルを書かない） |
| A8 | 版が 3 箇所で揃って上がり（2.17.0 → 2.18.0）、§8.2 の生成ブロックが新しく、テストと歯止めが `check-all.py` と CI に収録され、`CLAUDE.md` に載る | `check-plugin-versions.py`・`skill-metrics.py --check`・`test-check-all.py`・`check-all.py` |

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す。

### この環境では証明できないもの

- **A4 の後半「外した後も eval が通る」**——`claude plugin eval` は課金し、worktree 隔離セッションから起動できない（ガードが shell の `eval` と読んで拒否する）。**外す行が 1 つも無い周なので、通す eval も実在しない。**
  **BLOCKED の分類は、手段が無いからではなく、見る対象（外す PR）がまだ存在しないから**——代替は置かず、見られる範囲（eval が差分に在って名指しが揃うこと）だけを `check-prompt-lines.py` で見る。外す最初の PR は `references/prune.md` のとおり `run-dev-loop-evals.py` の要約を貼って人間が見る。
- **周が実際に `効いた行` を書くか・実データで候補が出るか**——既存の計画ファイルに記録が無い（登録日は今日）。記録は周が貯めるもので、窓 30 周分が貯まるまで候補は出ない。試験は合成の計画ファイルで行った（A1・A2）。PR コメントで人間に回す。

生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）。図の書き出しは触らない。

## 未解決の判断・確認待ち

- D1〜D5（推奨で決めた値）。確認の Issue の下書きは PR 報告に書く（起票は親）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1194-prune-delegation-lines`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1194`・
  起点 `5484e228`・base 参照 `origin/main`・base SHA `5484e2285a7ac5827a9aa2e5f5626332ff4ebd3a`
- 割り目（手順 4・6）: **割らない（cruise の周）**。
- 交絡: 実験なし（試料は一時ディレクトリの合成）

- この周の起票: 0 件（確認の Issue は親が立てる。この周では起票しない）
