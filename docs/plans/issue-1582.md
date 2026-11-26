# Issue #1582 — screen-spec: 既定が語彙の外の基盤の profile で、write-screens.py hint の案内が行き止まりを指す

**利用者が不在の周**（cruise の子。出所: `/dev-loop:cruise 1583 --absent` の起動、2026-11-26T08:52:16Z。親 Issue #1583）。読み込んだ dev-loop は 2.26.0（`SKILL.md` 1969 行）。

直す線: `既定`（出所: cruise の台帳の確かめた線——親 Issue #1583 の `cruise:` の行を利用者が起動時に確かめた）。
台帳の確かめた線: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）。実機確認の線は無い。
版の上げ方: `screen-spec` を **patch**（0.12.1 → 0.12.2。案内の誤りを直す不具合の修正。マージの直前に上げ直すなら、main の先端の版から patch で 1 つ上げる）。

Issue 本文（外部入力。作者は利用者本人。#1571 の 2 パス目の /code-review の指摘から起票）から読んだ要件:
基盤の profile が名指す画面の層が行の決まりに合わない（#1571 の既定が語彙の外など）とき、`hint` は「--profile と --external を明示して渡す」と案内するが、
同じ外部の profile を `--external` で明示しても `init` は 4 で止まる——案内が行き止まり。
提案: 止まった原因が層の行の決まりなら「外部の profile を直すか、`--external なし` を渡す」と言い分ける。`hint` と引数なしの `init` の経路の試料を足す。
親の依頼: #1581（PR #1584）の止まり方（決まった値の列の語彙が決まった値と 1 つも重ならない）も言い分ける対象に含める。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/check-screens.py` — `load_external` の画面の層の行の決まり（読めた後の行の照合）で止めたものを `Stop` の下位の `LayerRule` として名指す（読めないのとは分ける。終了コード・文言は変えない）
- `plugins/screen-spec/scripts/write-screens.py` — `base_initial` が `LayerRule` を受けて案内を言い分け、`hint` と引数なしの `init` が出す。docstring
- `plugins/screen-spec/references/profiles.md` — 「基盤の profile から引く初期値」の「値を明示して渡せば進める」を言い分ける（決まりの原本）
- `plugins/screen-spec/skills/init/SKILL.md` — 手順 2 の `hint` の行の読み方に、新しい行を足す。版の 2 行
- `plugins/screen-spec/skills/add/SKILL.md` — 版の 2 行
- `scripts/test-write-screens.py` — `hint` と引数なしの `init` の試料（#1571・#1581 の形）・案内どおりに進める陽性対照・変異（`check-screens.py` を壊す変異を含む）
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1582.md` — この計画ファイル

触らない:

- 明示の `init --external` が層の行の決まりで止まるときの文言——Issue の範囲は `hint` と引数なしの `init` の案内（明示の `init` は案内を出していない——行き止まりを指さない）
- 読めないとき（clone が無い・タグが無い・形式の版が範囲の外・設定の形・`重ねる先` がこのプラグインの profile でない・行に写せない形）の `hint` の文言——今までどおり「読めない（…）——明示して渡す」。理由は下の「既知の限界」
- `check-screens.py` の終了コードと止めた理由の文言（`LayerRule` は `Stop` の下位なので 4 のまま）
- `plugins/spec-loop/`・`plugins/platform-spec/`、plugin.json・marketplace.json・SKILL.md の description
- `CLAUDE.md`——#1581 の周で、`CLAUDE.md` を含むコミットが自動モードの分類器に拒まれた。決まりの原本は `profiles.md` と docstring で、CLAUDE.md の `write-screens.py` の項は案内の文言を持たない

依存の追加・更新: なし

## 設計の判断

- `check-screens.py` の `load_external` を、読む部分（clone・タグ・層・`重ねる先`）と行の決まりを照らす部分（`check_layer`）に分け、後者で止めたものを `LayerRule`（`Stop` の下位）に包み直す。
  照らす行のコードは動かさない（字下げも同じ——既存の変異の文字列がそのまま当たる）。`check-screens.py` の振る舞い（4 と文言）は変わらない。
- `write-screens.py` の `base_initial` は `LayerRule` を受け、理由と案内（`外部の profile を直すか、--profile <重ねる先> --external なし を渡す`）を持つ `LayerBroken`（`checks.Stop` の下位）を投げる。
  `hint` は `基盤の profile: 画面の層が決まりに合わない（<理由>）——init の引数を省いても、同じ外部の profile を --external で明示して渡しても止まる（<案内>）` を出して 0。
  引数なしの `init` は `止めた: <理由>——同じ外部の profile を --external で明示して渡しても止まる（<案内>）——書いていない` で 4（`main` の `Stop` の扱いのまま）。
- 案内に `--profile <重ねる先>` を入れる——`--external なし` だけを渡すと `profile` が `未設定` になり、基盤の profile が名指した組み込みの profile まで落ちる（`references/profiles.md` の「効くのは…両方省いたときだけ」）。
- 複製の数: 案内の文言は `write-screens.py` に 1 か所（`LayerBroken`）。決まりの原本（`profiles.md`）1 行・`init` の SKILL.md 1 行・docstring（終了コード 4 と守ること）——原本以外は指すか読み方だけ。分けない（1 つの案内）。

## verify の受入基準

不変条件 × 経路（入口: `write-screens.py hint`・引数なしの `init`・明示の `init`・`check-screens.py`。`load_external` を読み込むのはこの 2 本だけ）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | 基盤の profile が名指す画面の層が行の決まりに合わない（#1571 の既定が語彙の外）とき、`hint` は 0 で、「明示して渡す」だけの行き止まりでなく、同じ外部の profile を明示しても止まることと「外部の profile を直すか、`--profile web-spa --external なし` を渡す」を出す | `hint`（Issue の再現: `list,standard` → `list,wide`） | `LayerRule` → `LayerBroken` → `hint` の分岐 | 試料（直す前の本体で赤） |
| 2 | 同じ形で引数なしの `init` は 4 で何も書かず、止めた理由に同じ案内を出す | 引数なしの `init` | 同上 | 試料 |
| 3 | 案内が行き止まりでない: `init --profile web-spa --external なし` が 0 で書き、直後の検査が 0。明示の `init --external "org/guide org v1"` は 4（Issue の再現の 4） | 明示の `init` | — | 試料（陽性対照） |
| 4 | #1581 の形（`ステータス` の語彙が決まった値と 1 つも重ならない）でも 1・2 と同じに言い分ける | `hint`・引数なしの `init` | 同上 | 試料 |
| 5 | 読めないときは層の決まりと言わない——今までどおり「読めない（…）——明示して渡す」（clone が無い・形式の版が範囲の外・行に写せない形） | `hint` | `LayerRule` だけを分ける | 既存の試料 `base-no-clone`・`base-screen-layer-version-out-of-range`・`base-repo-without-slash` |
| 6 | `check-screens.py` の振る舞いは変わらない（層の行の決まりで 4・同じ文言） | `check-screens.py` | `LayerRule` は `Stop` の下位 | 既存の `test-check-screens.py` |
| 7 | 明示の `init --external` が層の決まりで止まる振る舞いは変わらない（4・同じ文言） | 明示の `init` | — | 既存の試料（#1571・#1581） |
| 8 | 分岐を外す・緩めると試料が赤になる（`write-screens.py` と `check-screens.py` の両方の変異） | テスト | `MUTATIONS` | `test-write-screens.py` |
| 9 | 決まりの原本（`profiles.md`）・`init` の SKILL.md・docstring が新しい言い分けを書き、偽の文（「値を明示して渡せば進める」を層の決まりにも掛ける）を残さない | 文書 | — | 目視・`check-all.py` |
| 10 | 版を 3 か所（marketplace.json・plugin.json・SKILL.md 2 本の 2 行）で揃えて上げ、既存の試料が今までどおり（後退が無い） | 全テスト | — | `check-all.py` |

- 未証明: なし。BLOCKED: なし。
- 生成物: 該当判定——screen-spec の書き込みと検査には生成物が無い。`SKILL.md` は版の 2 行と手順 2 の 1 行で、`skill-metrics.py` の対象は dev-loop の `SKILL.md` だけ（`--check` を回して確かめる）。図は触らない。→ 生成物なし。
- プロパティテスト: なし（入力は「止まった理由が層の行の決まりか、読めないか」の 2 分で、例で尽くせる）。
- 差分テスト: なし（振る舞い（案内の文言）を変える周）。
- 必須要件の掛け算: 受入基準を Verifier・/code-review の両方 × 1・2 パス目に渡す（2 パス目が該当なしなら初回の 2 つ）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1582-hint-layer-rule-advice`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1582`・起点 `fe7bf5c6`・base 参照 `origin/main` → `fe7bf5c69973428ce6a3929672723c706655e44a`

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 読めないとき（clone が無い・タグが無い・形式の版が範囲の外）も、同じ外部の profile を明示すれば止まる | 言い分けない（採らなかった） | Issue の範囲は層の行の決まり。読めないときの原因は手元（clone・タグ・profile の版）で、出力が原因を名指し、`init` の SKILL.md が「直してから hint を走らせ直すか、値を決めて明示で渡す」と読む（`--external なし` も明示の値） |
| 明示の `init --external` が層の行の決まりで止まるとき案内を足さない | 足さない | 明示の `init` は「明示して渡す」の案内を出していない（行き止まりを指していない）。Issue の提案の範囲の外 |

## 経験の還元（手順 8）

- この周の起票: 0 件（不在の周で、手順 8 の起票は訊かない。振り分けで直すに入った行は、まだ無い）
