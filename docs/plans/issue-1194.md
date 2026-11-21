# Issue #1194 — dev-loop: 委譲文とスキル本文の行を見直して刈り込む段が無い（「削らない」の先）

cruise（親 Issue #1290）の子として回す周。**不在の周**（`--absent`）。AskUserQuestion は使わない。
spec-loop から来た Issue ではない（本文の先頭に `<!-- spec-loop-handoff:` の印が無い）。`作り直しの元:` の行も無い。`find-cycle.py 1194` は 5 本とも当たらず、新規の周。

台帳の確かめた線（親の委譲文で受け取った）: 直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）。`.claude/dev-loop.md`（main）の宣言: `マージの反映: ドキュメントとプラグインの配布`。
直す線: `既定`（出所: cruise の確かめた線）。

版の上げ方: **dev-loop を minor**（base は 2.17.1 → 2.18.0。手順・スクリプト・台帳の新設）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/line-effects.py` — 新設。台帳の検査・最後に効いた周の集計・外す候補とまとめる候補
- `plugins/dev-loop/skills/dev-loop/references/line-registry.csv` — 新設。`prompts/*.md` の全項の台帳
- `plugins/dev-loop/skills/dev-loop/references/prune.md` — 新設。記録の書き方・見直しの段・行を外す手順（原本）
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「削らない」を「黙って削らない」に置き換え。報告に「反証ごとの番号」を足す
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 項 7（`/code-review` に項の番号を返させる）を足す
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

- `plugins/dev-loop/evals/` — eval ケースは足さない（外す行が 1 つも無い周。外す PR が足す）
- `plugins/spec-loop/` — spec-loop の見直しの規定（`spec-exit.md`）には触れない
- 既存の計画ファイル（`docs/plans/issue-*.md`）への `効いた行` の後付け——記録は周が書くもので、遡って埋めない（既知の限界）

依存の追加・更新: なし。spec-loop の正本はこのリポジトリに無い（`仕様の振る舞い:` の申告は要らない）。

## 周の大きさ（同じことを述べている箇所の数）

- 記録の行の形: `line-effects.py` の docstring と正規表現（原本）・`references/prune.md` の例（写し。テストが正規表現に当てる）。**2 箇所**。
- 「黙って削らない」の置き換え: `prompts/verifier.md`・`prompts/implementer.md`・`SKILL.md` 手順 5（約 1057 行）と手順 4 の委譲文の項（約 772 行）の 4 箇所（テストが verifier.md と SKILL.md を見る）。
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
| A8 | 版が 3 箇所で揃って上がり（2.17.1 → 2.18.0）、§8.2 の生成ブロックが新しく、テストと歯止めが `check-all.py` と CI に収録され、`CLAUDE.md` に載る | `check-plugin-versions.py`・`skill-metrics.py --check`・`test-check-all.py`・`check-all.py` |

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す。

### この環境では証明できないもの

- **「外した後も eval が通る」（Issue の受入基準 3 の後半）**——**この周の主張ではない**（BLOCKED に分類しない。Verifier の反証 10 を採った）。この周は行を 1 つも外さないので、通す eval が実在しない。
  eval の実行は別の端末で worktree の絶対パスを渡して回せば可能だが、外す PR が現れてから行うものである。この周が主張するのは、**外す PR に eval が差分に在って名指しが揃うこと**（`check-prompt-lines.py`）と、**外す最初の PR が `references/prune.md` のとおり `run-dev-loop-evals.py` の要約を貼る決まり**まで。
- **周が実際に `効いた行` を書くか・実データで候補が出るか**——既存の計画ファイルに記録が無い（登録日は今日）。記録は周が貯めるもので、窓 30 周分が貯まるまで候補は出ない。試験は合成の計画ファイルで行った（A1・A2）。PR コメントで人間に回す。

生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）。図の書き出しは触らない。

## 未解決の判断・確認待ち

- D1〜D5（推奨で決めた値）。確認の Issue の下書きは PR 報告に書く（起票は親）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1194-prune-delegation-lines`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1194`・
  起点 `5484e228`・base 参照 `origin/main`・base SHA `5484e2285a7ac5827a9aa2e5f5626332ff4ebd3a`
- 割り目（手順 4・6）: **割らない（cruise の周）**。
- 交絡: 実験なし（試料は一時ディレクトリの合成）

- 周の記録（関門）:
  1 パス目の対象 HEAD `cee250a70796e2a9949f8ec17c79616e57bf43a8`（main 取り込み後の merge-base `1dfd6847b236fc81c4da344c757b060d42b6f02f` からの差分）。
  Verifier（opus・`dev-loop:dev-loop-verifier`）**反証 11 件**／`/code-review`（high）**指摘 8 件**（重なりあり）。
  採否: 直す = 台帳の行が 1 項に複数当たる（V1・CR1）・付け替え（V1）・統合を同じファイルに限る（V2・CR4）・graders のブロック（V5・CR3）・ローカルの日付（V6）・
  テストを素通りした変異 7 件（V7）・SKILL.md 772 行の絶対の「削らない」（V8）・prune.md の陽性対照の向き（V9）・BLOCKED の分類と版の誤り（V10）・
  base の先端でなく merge-base と比べる（V11）・verifier.md の「最後に効いた周」の言い方（CR5）・prune.md の誤った指摘を数えない（CR6）・
  測れない行を候補に出さず `/code-review` にも番号を返させる（CR2。台帳に `測り方` の列を足した）。
  残課題 = 項の本文の弱め方・入れ子の行・字下げした行・段落の規則・穴への移動（V3・V4・CR8。定義どおりで、docstring と prune.md の「守らないもの」に書いた）・
  同趣旨の自己申告を別 PR で書き換える抜け道（V2 の後半。人間のレビュー）・committer time が rebase で変わる（CR7。docstring に書いた）。
  2 パス目の指摘対応の起点（狭いパスの起点）: `cee250a70796e2a9949f8ec17c79616e57bf43a8`（指摘対応に入る前に書いた）。
  `test-line-effects.py` は試料に加えて変異 26 件すべて赤（1 パス目の直しで 25 件、狭いパスの後退の直しで 1 件足した）。

- 狭いパス（Verifier opus。`git diff cee250a7 df8eb6f7`。**1 パス目の直しの差分に当てた**）: **反証 9 件**。後退は 2 件——(a) 付け替えの検査が同じ項の言い換えを偽の赤にする（G20・G21 の入力で df8eb6f7 は rc=1・直した後 rc=0）、
  (b) `prune.md:19` の入れ子の太字が `check-bold-flanking.py` を赤にする（df8eb6f7 で rc=1・直した後 rc=0。`check-all.py` 2 回目もここだけが落ちた）。この 2 件を直した（起点 `df8eb6f71a331d150c212cfa0b9654325379c936`・終点 `3fc80693fb6d145df6c63a0243f041ce0e06358f`）。
  残りの 7 件は後退でないので直さず、残課題に回した（下の「既知の限界・決着済みの論点」）。
- 当て直し（Verifier opus 1 回。`git diff df8eb6f7 3fc80693`）: **反証 2 件、どちらも後退**。陽性対照は著者のものが一致（G20・G21: 旧 rc=1 → 新 0 件、bold-flanking rc=1 → 0）。ただし (c) 付け替えと言い換えを同じ PR で組み合わせると付け替えを素通しする（S1・S2。df8eb6f7 は rc=1・3fc80693 は rc=0）、
  (d) 縮めた引きが、同じ PR で外した別の項の base の頭にも前方一致すると偽の赤（S5。df8eb6f7 は rc=0・3fc80693 は rc=1）。**当て直しは 1 回だけなので直し直さない**——absent-lines.md の「後退の分け方」の 3（当て直しで新たな後退が出た）。推奨と確認 Issue の下書きは PR コメントと最終報告に書く。
- 2 パス目（Verifier 2・`/code-review` 2。先端 `2a4806a2f7d42e685f7de984d3a5ceb06ffec41d`）: Verifier **反証 6 件（後退 0）**／`/code-review`（high）**指摘 6 件**。
  採否: 直す = 統合・付け替えがファイルをまたぐ形（Verifier F1。`prompts/` の外へ ID を移して eval を逃れる）・テストの穴 F2〜F4（統合先が base に無い・`元の事故: -`・`case.yaml` 以外）・
  「まとめる候補」が同じファイルの組だけを出す（CR1。13 組すべてがファイルをまたいでいた）・V-23 の測り方（CR3）・verifier.md の番号の直書き（CR4）・この周の `効いた行` の記録（CR6。下）・PR 本文の件数と確認 Issue の下書き（F6）。
  残課題 = 付け替えと言い換えを同じ PR で組み合わせる素通し・縮めた引きの偽の赤（CR2。当て直しの S1・S2・S5 と同じ）・周の順が決められない周（リネーム・浅い clone。CR5）・弱いテスト（F5）。
  2 パス目の指摘対応の起点（狭いパスの起点）: `2a4806a2f7d42e685f7de984d3a5ceb06ffec41d`（指摘対応に入る前に書いた）。

- 効いた行: V-01
- 効いた行: V-03
- 効いた行: V-05
- 効いた行: V-06
- 効いた行: V-07

## 既知の限界・決着済みの論点

1 パス目と狭いパスで挙がり、**直さないと決めたもの**（再指摘は要らない。決着の理由が誤りと判断したなら新しい反証として報告してよい）:

- 項の本文の弱め方・入れ子の行・字下げした行・段落で足した規則・差し込みの穴の中への移動・項を本文ごと別の新しい文面に差し替えて ID を付け替える形は、守られていない（項の頭だけを見る）。
  docstring と `references/prune.md` の「守らないもの」に書いた。本文の変更は人間のレビューが見る。
- 同趣旨の自己申告（別の PR で先に書き換える）・committer time が rebase で変わる・登録日はローカルの日付で比べる。docstring に書いた。
- 次の 5 件は後退ではない（前の版に無かった機能の不足）ので、この周では直さず残課題とした: (1) 台帳のファイルの `prompts/./verifier.md` のような別名で 1 項 1 行と付け替えの検査を抜ける、(2) `graders` を字下げしない形・フロー形で書いた YAML を偽の赤にし、入れ子の `- name:` を通す、
  (3) 台帳の V-23（報告の形の項）の `測り方` が `指摘` のまま（2 パス目で `不可` に直した）、(4) 効いた行の記録の 2 つ目の ID を黙って落とす形が残る（`V-05 と V-07` など）、(5) base の台帳のヘッダが列を足した後の台帳と違うと判定できない（rc=2）。テストの穴（ファイルをまたぐ付け替えの試料）も同じ。

- 狭いパス（Verifier opus。`git diff 2a4806a2 ad17ac24`。2 パス目の指摘対応に当てた）: **反証 4 件**（後退 1 件）。(R1・後退) prompts のファイルの改名だけで「ファイルを変えた」NG になる偽の赤（起点は rc=0）。(R2・R3) F1 の素の形と report の「またぐ組」の判定をテストが判別しない。
  (R4) 計画の `効いた行` の記録に V-01 が欠けていた（採否の記録の誤り。**指摘を受けて V-01 を足した**——記録は計画ファイルの行なので、狭いパスの指摘のうちこの 1 件だけ周の記録として直した）。**R1〜R3 は直さず人間に渡す**（狭いパスの指摘は直さない。R1 は prompts のファイル改名が稀で、改名なら ID を外して eval を付けるか、改名と台帳の列を別の PR で扱う。確認 Issue の下書きは PR コメント）。
  `check-all.py`（run-serial 越し）3 回目: 27 本を回し（74 本はキャッシュ）失敗 0。1 回目は 101/101 失敗 0、2 回目は `check-bold-flanking.py` だけ失敗（直した）。

```dev-loop-gates
周の base: 1dfd6847b236fc81c4da344c757b060d42b6f02f
関門: Verifier 1 cee250a70796e2a9949f8ec17c79616e57bf43a8 反証=11
関門: /code-review 1 cee250a70796e2a9949f8ec17c79616e57bf43a8 指摘=8
関門: Verifier 2 2a4806a2f7d42e685f7de984d3a5ceb06ffec41d 反証=6
関門: /code-review 2 2a4806a2f7d42e685f7de984d3a5ceb06ffec41d 指摘=6
関門: 狭いパス 2a4806a2f7d42e685f7de984d3a5ceb06ffec41d ad17ac24b9358bdbe5383f2c6355eef7d4cfa412 反証=4
関門: 当て直し cee250a70796e2a9949f8ec17c79616e57bf43a8 df8eb6f71a331d150c212cfa0b9654325379c936 反証=9
関門: 当て直し df8eb6f71a331d150c212cfa0b9654325379c936 3fc80693fb6d145df6c63a0243f041ce0e06358f 反証=2
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
受入基準: A5 満たす
受入基準: A6 満たす
受入基準: A7 満たす
受入基準: A8 満たす
マージの反映: ドキュメントとプラグインの配布
```

- この周の起票: 0 件（確認の Issue は親が立てる。この周では起票しない）
