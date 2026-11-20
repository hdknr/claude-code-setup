# Issue #1249 — spec-loop: 利用者向けに、ループの運用の決まりを 1 か所で追える要約が無い

**不在の周**（`/dev-loop:cruise 1290 --absent` の起動・2026-11-20）。利用者には訊かない。親（cruise #1290）から委譲文で受けた子（`cruise-1290-1249`）。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1290`））: `直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`（古い値）。
台帳は書かない（親だけ）。手順 7 のマージはしない（PR・PR 側の CI の確認と計画ファイルの関門の記録まで）。読んだ dev-loop の `SKILL.md` は 1933 行（メインの作業ツリー）。worktree の写しは 1938 行（base が新しい）。

直す線: `既定`（出所: cruise の確かめた線）。
版の上げ方: `spec-loop` を **minor**（0.x。利用者向けの要約の追加）。着手時の main は spec-loop 0.125.0 → 0.126.0。マージの直前に main が進んでいたら親の依頼で取り込み、先端の版から上げ直す（cruise の `references/parallel.md`）。
並行して #1191（dev-loop）の周が走る（dev-loop のプラグインを触るので spec-loop の版とは衝突しない見込み）。
重い検査は `plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越し。
割り目: 割らない（cruise の周）。
仕様の振る舞い: 該当なし（このリポジトリに spec-loop の正本は無い）。形式検査のモデル: 無い。依存の追加・更新: なし。生成物: `skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` を変えないので変わらない（`--check` で確かめる）。図なし。

周の在り処:

- ブランチ: `issue/1249-loop-operations-summary`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1249`
- 起点コミット: `6d00ec2d03c7256ed880d223cd21244cb48bd0d3`（`origin/main`。refs/remotes/origin/HEAD から取り直した）
- 周の base: `6d00ec2d03c7256ed880d223cd21244cb48bd0d3`

## 変更範囲

触る:

- `plugins/spec-loop/references/operations.md` — 利用者向けの運用の決まりの要約（新規）
- `plugins/spec-loop/README.md` — 中身の表の行と、読む入口の 1 段落
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 「データの決まり」の後に要約への 1 文と版の 2 行
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（同じプラグインの全スキル）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/spec-loop.md` — 公開ページの冒頭に要約への指し先を 1 文
- `CLAUDE.md` — 構成の記述に `references/operations.md` を 1 行
- `docs/plans/issue-1249.md` — この計画ファイル

触らない:

- `references/` の既存の原本（`qa-csv.md`・`spec-exit.md`・`spec-scope.md` など）の決まりの中身——要約は指すだけで、決まりを変えない
- スクリプト・agents・テスト
- marketplace の description（要約の追加は紹介文を変えない）

## 設計の判断

- **置き場所**: Issue の案は「README か `references/`」。**`references/operations.md` に置き、README とスキルからは指すだけ**にした。README は前提とスキルの一覧が中心で、FAQ を載せると肥大する。
  スキル（書き手）は `references/` を読むので、そこに置けば「書き手が毎回 references を読み直して要約し直す」を避けられる。
- **形**: 先頭に問い → 節の表、各節は要約と「原本: …」の指し先。Issue の 7 つの問いの全部に節を置いた（Q&A 表の 2 層・層を移すと回答はどうなるか・1 回の流れと 2 回で打ち切る理由・抜ける条件 5 つと「抜けた」の意味・回し直し・上限・形式検査の対象・暫定の回答）。
  さらに、利用者が実際に聞いた「なぜ質問が増えたのか」を 1 節に独立させた。
- **複製の数**: 要約は決まりの写しなので、原本を直すと要約も直す必要がある（数は 9 節 × 各原本）。**分けない理由**: 要約であることを冒頭に書き、各節の末尾に原本を名指しし、「食い違ったら原本を正とする」と明記した。
  原本の数値（既定の上限 3・条件 5 つなど）が変わったときの手戻りは、この要約に残る。**この写しの鮮度を機械では見ていない**（残課題）。

## 受入基準（不変条件 × 経路）

入口: 利用者が読む場所（README・公開ページ）と、書き手が読む場所（`req-loop`・`spec-review` の `SKILL.md`）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | Issue の 7 つの問い（Q&A 表の 2 層と層を移したときの回答・1 回の流れと打ち切りの理由・抜ける条件 5 つと「抜けた」が承認でも網羅の証明でもないこと・回し直し（要求を変えた・決まりが増えた・回さなくてよい）・上限と訊かれること・形式検査の対象と検査していない部分・暫定の回答）に、`operations.md` の節が答えている | 問いの抜け・節が答えていない | `operations.md` を問いごとに読む |
| A2 | 要約の記述が、原本の記述と食い違わない（数値・状態の名前・手順の順・「できる／しない」の向き） | 要約が原本と違う数・名前を書く・原本に無いことを書く | 節ごとに原本の該当箇所と突き合わせる（`qa-csv.md`・`spec-exit.md`・`spec-scope.md`・`signoff-tags.md`・`versions.md`・`skills/spec-review/SKILL.md`・`README.md`の前提） |
| A3 | 各節が原本を名指しし、要約が原本ではないことが冒頭にある。決まりを要約で新しく決めない | 原本の無い決まりを書く・原本を名指ししない | `operations.md` の冒頭と各節の末尾を読む。`check-skill-pointers.py` |
| A4 | README・公開ページ・`req-loop`・`spec-review` の `SKILL.md` から `operations.md` へ辿れる。指し先が実在する | 指し先が無い・パスの誤り | `check-skill-pointers.py`・`check-site-links.py`・README と公開ページのリンクを読む |
| A5 | 版が 3 種（`marketplace.json`・`plugin.json`・全 `SKILL.md`）で 0.126.0 に揃い、`check-all.py` が通る | 版の取りこぼし・歯止めの赤 | `check-plugin-versions.py`・`skill-metrics.py --check`・`check-all.py`（run-serial 越し） |

**検証で証明できるもの**: A1〜A5（文書の読み比べと CI の歯止め）。
**この環境では証明できないもの**: 要約が**利用者に実際に伝わるか**（読みやすさ。利用者が読んで追えるか）。実際の利用者の読みは測れないので人間のレビューに回す（PR コメントに名指しで書く）。
**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パスとも渡す（2 パス目が該当なしなら 1 パス目の 2 つ）。

## 未解決の判断・確認待ち

- なし。

## 起票

- この周の起票: 0 件（残課題は PR コメントに書く。起票は親）

## 関門の進捗（再開点）

- 実装: コミット済み（起点 `6d00ec2d`）。次: Verifier と `/code-review` の 1 パス目。
- 割り目: 割らない（cruise の周）。
- 反証・差し戻し: まだ無い。
- 交絡を潰した手順: 実験なし。

## 既知の限界・決着済みの論点

- **要約と原本の鮮度は機械で見ていない**（採った: 見ない。理由: 要約の各節の末尾が原本を名指しし、冒頭で「食い違ったら原本が正」と書いた。数値の写し（既定の上限 3 つ・条件 5 つ・2 回で打ち切り）は原本を直すときに要約も直す必要がある。検査を足すのはスクリプトの新設で、この周の範囲の外。実データで食い違いが起きたと示されたら別の Issue にする）。
- **Issue の「案」のうち、README に載せずに `references/` に置いた**（採った: `references/`。理由: 設計の判断のとおり）。
- **「決着の理由が誤っていると判断したなら、それは新しい反証である」**

### 1 パス目の指摘の採否（直す線: 既定。Verifier 2 体の反証）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1 CLAUDE.md の `references/` の行の字下げが 4→2 に落ちた | 示せる（`sed -n 80,83p CLAUDE.md` の差分） | A4（変更範囲・構造） | 直す（字下げを戻した） |
| R2 形式検査の節の「性質とテストでしか受けていない」「前からの穴」と formal-baseline の並べ方が原本に無い・偽 | 示せる（`spec-exit.md:340`・`tree.md:570`） | A2・A3 | 直す（書き換えた。formal-baseline は選ばれなかった対象を埋める道でないと明記） |
| R3 条件 1 の要約が画面の表・テストケースの番号の重複を落とす | 示せる（`spec-exit.md:15・104`） | A2 | 直す |
| R4 条件 5 の要約が根拠未確認の行・内部の表に残る行を落とす | 示せる（`spec-exit.md:19`） | A2 | 直す |
| R5 上限の選択肢で機能がすべて `-` のとき `範囲を決め直す` が出ない | 示せる（`spec-exit.md:532`） | A2 | 直す |
| R6 凍結の括弧が範囲を狭める・v1 の「例外」の読み | 示せる（`spec-review/SKILL.md:95`・`spec-exit.md:75`） | A2 | 直す |
| V2-2 回し直しの冒頭文が表と矛盾 | 示せる（同じ節の表） | A2 | 直す |
| 狭いパスに内部の行の確かめを入れる記述の脱落（:80） | 示せない（要約の省略で、意味は変えない） | 無し | 残課題 |
