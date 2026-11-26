# Issue #1590 — フォローアップ: hint の「設定のタグを変える」案内に、承認の取り直しと --external で明示する道を足す

作り直しの元: #1588

**利用者が不在の周**（cruise の子。出所: `/dev-loop:cruise 1583 --absent` の起動、2026-11-26T08:52:16Z。親 Issue #1583）。
この周を cruise に足したのは利用者の指示（2026-11-26「フォローアップは台帳にいれてこの cruise でまわして」）。
読み込んだ dev-loop は 2.26.0（`SKILL.md` 1970 行を読んだ。`wc -l` は 1969——末尾の行に改行が無い）。

直す線: `既定`（出所: cruise の台帳の確かめた線——親 Issue #1583 の `cruise:` の行を利用者が起動時に確かめた）。
台帳の確かめた線: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）。実機確認の線は無い。
版の上げ方: `screen-spec` を **patch**（0.12.2 → 0.12.3。案内の記述の不足を直す修正）。並行する周は無い（親の言）。マージの直前に上げ直すなら、main の先端の版から patch で 1 つ上げる。

Issue 本文（外部入力。作者は利用者本人。#1588 の確認の結果「推奨のまま」から親が立てたフォローアップ）から読んだ要件:
#1582（PR #1587）で `hint` と引数なしの `init` が出すようになった案内の 1 つ目の道「外部の profile を直してタグを付け、`shared/platform/settings.csv` のタグをそれにする」に、
(1) `shared/` を変えるので承認（サインオフ）を取り直し、基盤の層を読む版も変わること（platform-spec の `references/infra-profile.md`）、
(2) `shared/` を触らずに、直したタグを `--profile web-spa --external "org/guide org <新しいタグ>"` で明示する道、の 2 点を足す。PR #1587 の /code-review 2 パス目の CR2-2。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/write-screens.py` — `LayerBroken.advice`（と `LayerBroken` を作る `base_initial` が渡す値）・docstring の #1582 の行
- `plugins/screen-spec/references/profiles.md` — 「基盤の profile から引く初期値」の #1582 の行（決まりの原本）
- `plugins/screen-spec/skills/init/SKILL.md` — 手順 2 の「画面の層が決まりに合わない」の行。版の 2 行
- `plugins/screen-spec/skills/add/SKILL.md` — 版の 2 行
- `scripts/test-write-screens.py` — `LAYER_ADVICE`・docstring の 8・直したタグを `--external` で明示する陽性対照の試料・案内の 2 点を外す変異
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1590.md` — この計画ファイル

触らない:

- 読めないとき（clone が無い・タグが無い・形式の版・設定の形・`重ねる先`・行に写せない形）の `hint` と `init` の文言（#1582 の受入基準）
- `check-screens.py`・`plugins/spec-loop/`・`plugins/platform-spec/`・description（plugin.json・marketplace.json・SKILL.md の frontmatter）
- `CLAUDE.md`——`write-screens.py` の項は案内の文言を持たない
- #1589（層ファイルの中身の欠陥）——この周の範囲の外（親の言）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（spec-loop の正本ではない——このリポジトリはプラグインの配布元）

## 設計の判断

- 案内の文言は `write-screens.py` の `LayerBroken.advice` 1 か所で作り、`hint` と引数なしの `init` の両方がそれを出す（今と同じ）。
- 新しい案内（`<profile>` は層が名指す重ねる先、`<repo> <name>` は基盤の profile の設定の値）:
  `外部の profile を直してタグを付け、shared/platform/settings.csv の タグ をそれにする（shared/ の変更なので 2 つの承認を取り直し、基盤の層もそのタグの時点で読むことになる）か、shared/ を触らずに直したタグを --profile <profile> --external "<repo> <name> <新しいタグ>" で明示するか、--profile <profile> --external なし を渡す`
- 2 つ目の道に `repo`・`name` を実際の値で入れる——利用者が写して `<新しいタグ>` だけを替えれば渡せる。`LayerBroken` に `repo` と `name` を渡す。
- 明示の `init`（`--profile` か `--external` を渡す）は基盤の profile を読まない（`references/profiles.md` の「効くのは…両方省いたときだけ」）ので、設定のタグが古いままでも、直したタグを明示すれば書ける。
- 複製の数: 案内の文言は本体 1 か所・テストの期待 1 か所（`LAYER_ADVICE`）。散文は決まりの原本（`profiles.md`）1 行・`init` の SKILL.md 1 行・本体の docstring 1 行・テストの docstring 1 行。分けない（1 つの案内を足すだけ）。

## verify の受入基準

入口: `write-screens.py hint`・引数なしの `init`・明示の `init`（`--external` に直したタグ）・`check-screens.py`。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | Issue の入力（`GUIDE_LAYOUT` の `list,standard` → `list,wide`）で `hint` の出力に、承認（サインオフ）の取り直し（と基盤の層の版）と、直したタグを `--profile web-spa --external "org/guide org <新しいタグ>"` で明示する道の 2 つが出る | `hint` | `LayerBroken.advice` | 試料 `base-layer-default-outside-vocab`（`LAYER_HINT`。直す前の本体で赤）・変異 |
| 2 | 案内どおり、直したタグを `--external` で明示すると `init` が 0 で書け、直後の検査が 0（陽性対照: 基盤の設定はタグ v1 の壊れた層のまま、profile のリポジトリに直したタグ v2 がある） | 明示の `init` | 明示の引数は基盤の profile を読まない（既存） | 新しい試料（v1 では 4・v2 では 0 を同じ試料で） |
| 3 | #1582 の受入基準を破らない: 層の行の決まりで止まる profile では `hint` と引数なしの `init` が行き止まりでない案内を出し（#1571・#1581 の形）、`--profile web-spa --external なし` で 0 で書ける。読めないときの文言は変えない | `hint`・引数なしの `init`・明示の `init` | 既存の分岐を変えない | 既存の試料（`base-layer-*`・`base-no-clone`・`base-screen-layer-version-out-of-range`・`base-repo-without-slash`）と既存の変異 |
| 4 | 引数なしの `init` の止めた理由（4）にも同じ案内が出る | 引数なしの `init` | `LayerBroken.__init__` が `advice` を理由に入れる（既存） | 試料（`LAYER_INIT`） |
| 5 | 決まりの原本（`profiles.md`）と `init` の SKILL.md と本体の案内が食い違わない（2 点とも書く） | 文書 | 手で揃える | 関門の読み（機械の検査は無い） |

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（Verifier 1・2 パス目、/code-review 1・2 パス目。2 パス目が該当なしなら初回の 2 つ）。

この環境で証明できないもの（未証明）: なし——どれも一時の git リポジトリの試料で走らせて確かめられる。
生成物: なし（このリポジトリの生成物は drawio の書き出しと `SKILL.md` の測定値（dev-loop の設計 §8.2）。screen-spec の `SKILL.md` は測定の対象外——`skill-metrics.py --check` で確かめる）。
プロパティテスト: なし（案内の文言の追記で、入力の空間が広い不変条件が無い）。
差分テスト: なし（受入基準は振る舞いを変える——案内の文言が変わる。「振る舞いを変えない」を含まない）。

## 未解決の判断・確認待ち

（無し）

## 関門の進捗（再開点）

周の在り処:
- ブランチ: `issue/1590-external-tag-advice`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1590`
- 起点コミット: `6cd20a35`
- base: 参照 `origin/main` → `6cd20a357a80038fd876c709451932ebae4b6a97`

割り目（手順 4）: 割らない（cruise の周）

## 手順 8 の記録

- この周の起票: 0 件（不在の周——起票は訊かず、周の途中の課題は found-lines.md の振り分けで PR コメントに残す。確認の Issue は立てない——立てるのは親）
