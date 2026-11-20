# Issue #1358: spec-ir.md の見積もりの「理由は 3 つ」を、乗る割合に効く理由の数に合わせる

## 変更範囲

触る:

- `plugins/spec-loop/references/spec-ir.md` — 「書き起こす前の見積もり」の「理由は 3 つ」を「理由は 2 つ」にし、理由 3（Red テストだけの割合）を箇条から外して注記に回す
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版 0.127.2 → 0.127.3（patch）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1358.md` — この計画

触らない:

- spec-ir.md の他の節・他の文言（理由 1・2 の本文、「実案件で…」の行）
- `CLAUDE.md`・`scaffold-estimate.py`・scaffold の `SKILL.md`（理由を指すだけで数を持たない）
- `docs/plans/issue-1328.md`・`docs/plans/issue-1302.md`（前の周の記録）

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）
依存の追加・更新: なし

版の上げ方: spec-loop を patch で 1 つ上げる（マージ直前に main が進んでいたら、main の先端の spec-loop の版から patch で 1 つ上げた値に上げ直す。parallel.md の「版とマージの順」）

## 不在の周と線

- 不在の周: `/dev-loop:cruise 1374 --absent` の起動（2026-11-20）の子。
- 台帳の確かめた線（出所: 利用者の確認——起動時・親 Issue #1374 の `cruise:` の行・2026-11-20T11:38:12Z、配布を見せて確かめた）:
  - 直す線 = 既定
  - 仕様の穴 = 推奨で決めて起票
  - マージ = 関門を通ればマージ（マージは親がする）
  - 周の途中の課題 = 外に出す
  - マージ前の判断 = 推奨で決めて起票（後退・未達を含む）
  - 実機確認: 線なし（止まる）

## デプロイ経路

main へのマージ → GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。spec-loop の `references/` はサイトの `docs/` の外なので、サイトには載らない——配布はプラグインの版で届く。

## 周の大きさ

理由の数を述べている箇所はリポジトリに 1 箇所（spec-ir.md 133 行）。`CLAUDE.md` 217 行・`scaffold-estimate.py` 10・30 行・scaffold の `SKILL.md` 110 行は「理由は spec-ir.md の同じ節」と指すだけで数を写していない（`grep -rn "理由は 3 つ\|線を引かない理由\|止める割合の線"` で確かめた）。複製は 1。

## 受入基準

不変条件 × 経路（経路はこの文言を読む入口: spec-ir.md 本文を読む利用者・scaffold スキル（`../../references/spec-ir.md` の同じ節を指す）・`scaffold-estimate.py` の docstring が指す先・`CLAUDE.md` が指す先。どれも同じ 1 箇所に着く）:

| # | 不変条件 | 経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 「止める割合の線」の項で数えた理由の数と、その下に箇条で並ぶ理由の数と、乗る割合に効く理由の数が一致する（2） | spec-ir.md 本文 | 直した後の節を読み、`理由は 2 つ` の下の箇条が 2 つで、どちらも乗る割合に効く（「当たらない」と書かれた理由が箇条に無い）。陽性対照: base `aec1ce1f` では `理由は 3 つ` で箇条 3 つ・うち 1 つが「当たらない」 |
| A2 | Red テストだけの割合についての記述（仕様の性質で変わる・画面中心は低く計算中心は高い・一律の線はどちらかで誤る・乗る割合には当たらない）が消えずに残る | spec-ir.md 本文 | `git diff` で、消した語句が全部書き換え後の文に在る |
| A3 | 指す側（`CLAUDE.md`・`scaffold-estimate.py`・scaffold の `SKILL.md`）が指す節の名前が変わらず、指し先が解決する | 指す側の 3 ファイル | 見出し「書き起こす前の見積もり」を変えない。`python3 scripts/check-skill-pointers.py` |
| A4 | spec-loop の版が 3 種類（marketplace.json・plugin.json・SKILL.md の 2 行）で揃い、base より上がっている | カタログ・マニフェスト・スキル本文 | `python3 scripts/check-plugin-versions.py`・`python3 scripts/check-version-bump.py origin/main` |
| A5 | 歯止めが全部緑 | リポジトリの CI | `python3 scripts/check-all.py`（run-serial 越し）と PR 側の CI |

掛け算: 受入基準を Verifier と `/code-review` の両方に、2 パス（1 パス目の指摘対応の差分が 0 行なら 1 パス）。

未証明: なし。BLOCKED: なし。
生成物: なし（spec-ir.md から生成するものは無い。`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけを測る）。
プロパティテスト: なし（文言の書き換えで、入力の空間を持つ不変条件が無い）
差分テスト: なし（振る舞いを持つコードを変えない。文書の文言だけ）

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1358-spec-ir-reason-count`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1358`・起点 `aec1ce1f`・base `origin/main` = `aec1ce1f89d4c2a49fd52aedd318383d6029a8c0`
- 直す線: 既定（出所: cruise の台帳の確かめた線）
- 割り目: 割らない（cruise の周）。手順 4 の割り目は訊かずに続けた。
- 実験なし
- 1 パス目の関門に渡した成果物: `5f189679`（1 パス目の指摘対応の起点）。Verifier（sonnet・`dev-loop:dev-loop-verifier`）と `/code-review` に渡した。

この計画の「理由は 3 つ」と「理由は 2 つ」は、`check-duplicate-counts.py` の免除を使っている——前者は直す前の spec-ir.md の文言、後者は直した後の文言で、別々の状態を引いている。

dup-counts-ok: 理由

## 既知の限界・決着済みの論点

- Issue 本文の行番号（131・137・138）は #1356 の時点のもので、main `aec1ce1f` では 133・137・138。採った: 今の行で書く。理由: 文言は同じで、行だけずれた。
- 直し方は Issue の案 1（「理由は 2 つ」にし、理由 3 を注記に回す）を採った。案 2（見出しで分ける）は採らなかった——節の中の小見出しを増やすと、指す側が節の名前で指している形（「同じ節」）の読み方が変わるため。

### 1 パス目の採否（Verifier 反証 1 件・/code-review 指摘 3 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1・CR1（同じもの）注記（137 行）が空行なしの 2 字下げで、CommonMark では理由 2 の箇条の段落の続き（lazy continuation）になり、「上の 2 つ」が自分を含む箇条の中に入る。「実案件で…」の行も同じ | 示せる——`sed -n 133,141p … \| pandoc -f commonmark -t html` で、注記の文が `<li><strong>線を引いても…` の `</li>` の前に入る（著者が走らせて確かめた） | A1（注記が理由の箇条の外に在る） | 直す——注記の前と「実案件で…」の前に空行を入れた（字下げ 2 のまま外側の箇条の段落に）。直した後の pandoc: 内側の箇条は 2 項で、注記と「実案件で…」は外側の項の `<p>` |
| CR2 133 行の「理由は 2 つ」がどの割合についてかを言わず、Red テストだけの割合の読み手には注記の 3 つ目と合わない | 示せない（文言の読み方。A1 の数は乗る割合で一致している） | 無し | 残課題 |
| CR3 注記の「上の 2 つ（実測が無い・…）」の要約が、理由 1（実測は 1 点・今の定義で 0 点）より強い | 示せる（文面）。ただしこの要約の言い回しは base の 138 行のまま | 無し | 残課題 |

## 歯止め

- `python3 scripts/check-all.py`（run-serial 越し。実装の差分の上で）: 1 回目は 2 本が落ちた——`check-duplicate-counts.py`（この計画の直す前・直した後の文言の引用）と `check-plan-counts.py`（件数の行が無い）。どちらも計画ファイルで、上の免除と下の件数の行で直して回し直した。
- 2 回目: 99 本のうち 17 本を回して失敗 0（82 本は入力が前回の緑から変わっていないので `CACHED`。PR 側の CI は全部回す）。

## 手順 8

- この周の起票: 0 件（不在の cruise の周。起票は手順 8 の振り分けで直すとした行だけで、子は起票しない）
