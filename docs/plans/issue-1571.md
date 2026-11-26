# Issue #1571 — screen-spec: 外部の profile の画面の層で、既定の値が同じ表・列の語彙に無ければ止める

利用者が居る周（`/dev-loop:dev-loop 1571`・2026-11-26）。読み込んだ dev-loop は 2.25.1。

直す線: `既定`（出所: 手順 3 の回答・2026-11-26）。
版の上げ方: `screen-spec` を **minor**（0.11.0 → 0.12.0。0.x なので、今まで通っていた食い違った profile が 4 で止まる変更も minor）。

Issue 本文（外部入力。作者は利用者本人）から読んだ要件: 外部の profile の画面の層で、種類 `既定` の行の `値` が同じ `表`・`列` の `語彙` に無ければ、
「読めないとき」（4）として検査の前に止める。語彙を 1 つも持たない列の既定は見ない。core・組み込みの profile に値の決まった列に既定を置いた場合の扱いも決める。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/check-screens.py` — `load_external` で既定の値を語彙と core の決まった値に照らす。守る／守らないは docstring
- `plugins/screen-spec/references/profiles.md` — 行の種類 `既定` の説明と「読めないとき」に足す（決まりの原本）
- `scripts/test-check-screens.py` — 試料・変異
- `scripts/test-write-screens.py` — `init` が食い違った画面の層で書かずに 4 で止まる試料（受入基準 7）
- `CLAUDE.md` — プロジェクト構成の `check-screens.py` の項に 1 句
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行（2 本）
- `docs/plans/issue-1571.md` — この計画ファイル

触らない:

- `plugins/screen-spec/scripts/write-screens.py`——`init` は `load_external` を読み込むので、同じ止め方を受け継ぐ（コードは変えない）
- `plugins/spec-loop/`（`external-profile.py` は読み込むだけ）
- plugin.json・marketplace.json の description

依存の追加・更新: なし

## 設計の判断（手順 3 の回答・2026-11-26）

- 既定の値は、その列の**外部の profile の語彙**（`screens.csv` の同じ列の `語彙` の行。在れば）と、**core の決まった値**（`screens.csv` の `種別`・`ステータス`）の**両方**に在ること。無ければ 4。
- `種別` の列の既定は、その行の `種別` と同じ値でなければ 4（画面の `種別` はその種別そのものなので、違う値の既定はどの画面でも違反になる）。
- 組み込みの profile（`web-spa`）の `screens.csv` の列は `パス` だけで、決まった値を持たない。`パス` の形（`/` で始まる）に既定が合うかは見ない（守らないもの）。
- 語彙の行と既定の行の順に依らない（全部を読んでから照らす）。
- 複製の数: 決まりの原本（`profiles.md`）1・本体の docstring 1・CLAUDE.md の 1 句——原本以外は指すだけ。分けない（1 つの規則）。

## verify の受入基準

不変条件 × 経路（入口は `check-screens.py` と、`load_external` を読み込む `write-screens.py init`・`hint`）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | 既定の値が同じ列の外部の語彙に無ければ 4 で止まる | `check-screens.py`（既定が語彙の外 `L-080` / 語彙の行を差し替え） | `load_external` で Stop | 試料（Issue の再現 2 形） |
| 2 | 語彙を持たない列の既定は語彙で止めない | `check-screens.py`（語彙の無い足した列に既定） | 語彙が無ければ照らさない | 試料（陰性対照） |
| 3 | 既定の値が core の決まった値（`ステータス`・`種別`）に無ければ 4 | `check-screens.py` | Stop | 試料 |
| 4 | `種別` の列の既定がその行の種別と違えば 4、同じなら通る | `check-screens.py` | Stop | 試料（陽性・陰性） |
| 5 | 語彙の行が既定の行より後ろにあっても判定が同じ | `check-screens.py` | 全行を読んでから照らす | 試料 |
| 6 | 既存の正しい profile（`ext-good` ほか）は今までどおり 0 | `check-screens.py` | — | 既存の試料 |
| 7 | `init` が食い違った profile で書く前に 4 で止まる（書かない） | `write-screens.py init --external` | `load_external` を共有 | `test-write-screens.py` の試料 `explicit-external-default-outside-vocab`（書いたファイル 0） |
| 8 | 止める行の理由に行の ID・列・種別・値・語彙を名指す | 出力 | メッセージ | 試料の期待文字列 |
| 9 | 決まりの原本（`profiles.md`）と docstring が新しい止め方を書き、「守らないもの」から「既定の値が語彙の中にあるか」を外す | 文書 | — | 目視・`check-all.py` |
| 10 | 新しい分岐を外すと試料が赤になる（変異） | テスト | `MUTATIONS` | `test-check-screens.py` |

- 未証明: なし。BLOCKED: なし。
- 生成物: 該当判定——screen-spec の検査には生成物が無い。`SKILL.md` は触るが版の 2 行だけで、`skill-metrics.py` の対象は dev-loop の `SKILL.md` だけ（`--check` を回して確かめる）。図は触らない。→ 生成物なし（`skill-metrics.py --check` は回す）。
- プロパティテスト: なし（入力は profile の行の小さな組み合わせで、境界は語彙の有無・決まった値の有無・種別の一致の 3 つ。例で尽くせる）。
- 差分テスト: なし（振る舞いを変える周）。
- 必須要件の掛け算: 受入基準を Verifier・/code-review の両方 × 1・2 パス目に渡す（2 パス目が該当なしなら初回の 2 つ）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1571-default-in-vocab`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1571`・起点 `366a3c7e`・base 参照 `origin/main` → `366a3c7eca1c629a04b5f4dd9742f037dbf7bf39`
- 関門: まだ
- 交絡: 実験なし

```dev-loop-gates
周の base: 366a3c7eca1c629a04b5f4dd9742f037dbf7bf39
```

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `パス` の形に既定が合うか | 見ない（採らなかった） | 形の規則は語彙ではない。Issue の範囲は「語彙のある列」 |
| 外部の語彙が core の決まった値の外の値を持つとき | 見ない | 既定の食い違いと違い、全部の値が違反になる形ではない（語彙の中の決まった値を書けば通る） |

## 経験の還元（手順 8）

- この周の起票: 0 件（起票の候補が無い）
