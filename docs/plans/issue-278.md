# Issue #278 — Q&A 表の番号に、起票したループの印を付ける

## 変更範囲

触る:

- `plugins/spec-loop/references/qa-csv.md` — `No` の書式（印）・起票元と印の対応・番号の振り方・行の並び・前の形の番号。**決まりの原本**
- `plugins/spec-loop/scripts/check-qa-csv.py` — 印つきの番号の書式・印と起票元の一致（`is_internal_number` も印つきを内部と読む）
- `plugins/spec-loop/scripts/scaffold.py` — 中間表現の `qa` が印つきの番号を指せる（`QA_NO`）
- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — 本文の印つきの番号もリンクにする（`QA_NUMBER`）
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 番号の振り方（同じ印の中の最大の次）
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 内部の表の番号（`D-S-`）
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 根拠に書く内部の番号の言い方
- `plugins/spec-loop/agents/estimate-checker.md` — 同上
- `plugins/spec-loop/references/tree.md` — `D-` の番号で移す、の言い方
- `plugins/spec-loop/references/feasibility-csv.md` — `根拠` の例の番号（`qa-csv.md` の例を印つきに振り直したので、指し先の `Q-005` が無くなる。実装中に広げた）
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 開発が起票する番号（`Q-D-`・`D-D-`）
- `scripts/test-check-qa-csv.py` — 試料・変異・`qa-csv.md` との突き合わせ
- `scripts/test-scaffold.py` — `QA_NO` の変異と試料
- `scripts/test-init-mkdocs.py` — フックの番号の形の変異と試料・`check-qa-csv.py` との突き合わせ
- `plugins/spec-loop/.claude-plugin/plugin.json`・`plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md`・`plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `docs/plans/issue-278.md` — この計画

触らない:

- 既存の表の番号の振り直し（スクリプトも作らない。下の D2）
- ループの順序の制約（下の D6。人間が「足さない」と決めた）
- `check-signoff.py`・`merge-versions.py`・`diff-versions.py`・`build-proposal.py`（層の判定は `is_internal_number` を読むだけなので、そこを直せば足りる）
- `qa-to-pptx.py`（番号の形を見ない）

### 同じことを述べている箇所の数

番号の書式と振り方: `qa-csv.md`（原本）・`check-qa-csv.py`（実装）・`scaffold.py` の `QA_NO`・フックの `QA_NUMBER`・
req-loop の SKILL 2 箇所・spec-review の SKILL 1 箇所・feasibility の SKILL 2 箇所・estimate-checker 1 箇所・tree.md 1 箇所・
spec-gap.md 2 箇所 の **13 箇所**。**分けない理由**: 書式を変えると、写しのどれか 1 つでも古いと起票した行が検査で落ちる
（あるいはリンクにならない・scaffold が止まる）ので、同じ周で揃えないと壊れた状態がマージされる。写しのうちスクリプトの 3 つは
テストで `check-qa-csv.py` と突き合わせ、散文は `qa-csv.md` を指す形にする。

## 乗るデプロイ経路

main へのマージ。プラグインは利用者の `plugin update` で届く（サイトのページは触らない——反映経路は main のマージだけ）。

## 設計の決定（関門に渡す）

- **D1 印は起票元で決まる**: `要求確定`→`R`・`仕様レビュー`→`S`・`実現性・コスト`→`F`・`開発`→`D`。
  共有の表は `Q-<印>-` に 3 桁以上の数字（`Q-S-001`）、内部の表は `D-<印>-`（`D-F-001`。人間が「内部の表にも付ける」と決めた）。
  **印と起票元が合わない行は検査が落とす**。
- **D2 印の無い番号（`Q-001`・`D-001`）は「前の形」として通す。振り直さない。** リリースした版は凍結されていて直せない
  （`check-frozen.py`）うえ、中間表現の `qa`・見積りの根拠・`removed.csv`・本文の番号が元の番号を指しているので、
  振り直すと指し先が全部切れる。前の版の行を作業中の版で置き換える（問い直す）ときも元の番号のまま。
  **新しく起票する行は印をつける**——これは検査できない（新しい行か前の形の行かを表から見分けられない）。
- **D3 新しい番号 = 同じ表の、同じ印の番号の中の、全部の版を通した最大の次。** 印の無い番号は数えない（別の連番）。
  同じループを 2 つ並行して動かさない限りぶつからない——**これが唯一の制約**として `qa-csv.md` に書く。
- **D4 行の並びは「印の無い番号を先に、そのあと印の順（R・S・F・D）、同じ印の中は数の順」と決める。検査はしない**
  （凍結した前の版の表を並べ直せない・既存の表が並んでいる保証が無い）。並べておけば、並行するループの行は表の別の場所に入るので、
  マージでぶつかりにくく、ぶつかっても両方を残して並べ直すだけで済む——これを `qa-csv.md` に書く。
- **D5 層を移すときは、移した先の表で、同じ起票元の印で振り直す**（`D-S-003` → `Q-S-012`）。
- **D6 ループの順序の制約は足さない**（Issue のコメントへの答え）。req-loop・spec-review・feasibility は表を介して互いに差し戻し合う関係で、
  「前のループが終わるまで次を始めない」順序ではない（spec-review は利用者の判断が要る指摘を req-loop に差し戻し、feasibility は途中の
  成果物から見積もる。unity-signage では spec-review と feasibility が同時に動いていた）。人間が「制約は足さない」と決めた。
- **D7 版**: spec-loop は 0.x なので minor（0.23.0 → 0.24.0。前の形を通すので既存の表は壊れない）。dev-loop は spec-gap.md の
  起票の手順が変わるので minor（1.46.0 → 1.47.0）。

## verify の受入基準

不変条件 × 経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | 印つきの番号（4 つの印 × 共有／内部）が検査を通る | `check-qa-csv.py` の `NUMBER`・`INTERNAL_NUMBER` | 試料（全印） |
| 2 | 印と起票元が合わない行を落とす（共有・内部の両方。起票元に詳細の括弧があっても） | `check_row` | 試料＋変異 |
| 3 | 印の無い前の形の番号（`Q-001`・`D-001`）を今までどおり通す | 同上 | 既存の試料（GOOD_ROWS・記事の行・`qa-csv.md` の例） |
| 4 | 層の判定: `D-S-001` は内部、`Q-D-001` は共有 | `is_internal_number`（`merge-versions`・`diff-versions`・`scaffold`・`build-proposal`・`check-signoff` が読む） | 試料（`is_internal_number` を直接と、`merge-versions` の `removed.csv` 経由で 1 つ） |
| 5 | 中間表現の `qa` が印つきの番号（共有・内部）を指せ、内部の表を写す | `scaffold.py` の `QA_NO` と層の判定 | 試料 |
| 6 | 本文の印つきの番号がリンクになり、前の形も今までどおり | フックの `QA_NUMBER` | 試料＋変異。印の集合を `check-qa-csv.py` と突き合わせる |
| 7 | 決まりの原本と写しが一致する（印の対応・書式） | `qa-csv.md` ↔ `check-qa-csv.py` | `test-check-qa-csv.py` の突き合わせ＋参照の変異 |
| 8 | 番号の振り方を述べる散文がすべて新しい決まり（同じ印の中の最大の次・印をつける）を言う | 上の 13 箇所 | 目視（grep で `D-`・`Q-` を述べる箇所を洗う） |
| 9 | 版が 3 種類で揃い、歯止めが全部緑 | `check-all.py` | 実行 |

掛け算: 1×2（印つきで、起票元と合う／合わない）・2×3（前の形の番号には起票元との照合を掛けない）・4×5（内部の印つきの番号を指す機能で内部の表が写る）。
受入基準は Verifier と `/code-review` の両方に、1 パス目・2 パス目とも渡す（4 つの受け渡し）。

### 証明できないもの（未証明）

- 実際に 2 つのループを並行して動かしたときに番号がぶつからないこと——スキル（モデル）が決まりどおりに振るかは振る舞いで、
  この周では回さない（`claude` を起こす Eval は spec-loop に無い）。決まりと検査が揃っていることまでを証明する。

### 生成物

- 図の書き出し・`skill-metrics.py` の生成ブロック: `dev-loop/SKILL.md` は版の 2 行の値しか変えないので節構造は動かないはずだが、
  `check-all.py`（`skill-metrics.py --check` を含む）で確かめる。それ以外の生成物なし。

## 未解決の判断・確認待ち

- なし（D1 の内部の表・D6 の順序の制約は人間が決めた）

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/278-qa-number-loop-mark`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-278`・
  起点 `0330977`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `0330977fc31ed62314e1dbb8c16f876b946d8e46`
- 実装: 済み（`99424a7`）。`check-all.py` 46/46 緑（初回は 3 本赤——`test-check-spec-exit.py`・`test-merge-versions.py` が
  旧いエラー文 `` `D-001` の形でない`` を期待していた・この計画ファイルに件数の行が無かった。直して緑）
- 実装中の発見: `scaffold.py` の並びの鍵が `int("S-001")` で落ちた（印つきの番号を指す試料で exit=2）——`number_order` に寄せた
- 割り目（手順 4 の終わり）: 訊いた → 人間は「このまま続ける」を選んだ
- 関門: まだ（次は手順 5 の Verifier 1 パス目と手順 6 の `/code-review` 1 パス目）
- 反証・差し戻し: まだ
- 交絡: 実験なし

## 手順 8

- この周の起票: 0 件（周の途中。手順 8 で確定する）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 新しい行が印をつけているかを検査しない | 採った（限界） | D2。表から新旧を見分けられない |
| 行の並びを検査しない | 採った（限界） | D4 |
| 同じループを 2 つ並行して動かすとぶつかる | 採った（限界） | D3。唯一の制約として書く |
