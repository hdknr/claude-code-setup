# Issue #424 — test(dev-loop): --push-result のテストで素通りする変異 3 件を塞ぐ（#407 の狭いパス）

#407 の狭いパスで素通りした変異 N1〜N3 を、`scripts/test-check-unattended-env.py` の内蔵の変異として足し、赤にする。
**本体は触らない**——3 件ともテストの穴で、現行のコードの誤りではない。

## 変更範囲

触る:

- `scripts/test-check-unattended-env.py` — `--push-result` のシナリオと変異
- `docs/plans/issue-424.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py`（本体。直す誤りが無い）——だから版も上げない
- `SKILL.md`・公開ページ・`CLAUDE.md`（記述は変わらない）

### 同じことを述べている箇所の数

- 「`--push-result` は設定を読まない」: 本体の docstring（**正**）・テスト —— 2 箇所。テストは docstring の主張を当てる側なので分けない。
- 「使用中は 60 秒以内」: 本体の docstring の表・本体の `PUSH_RESULTS`・`SKILL.md`・テスト —— 4 箇所。この周はテストだけ足す（他は #407 で本体と突き合わせ済み）。

## 設計: 「読まない」をどの単位で見るか（N2）

**関数名でフックしない。** #407 のテストは `layers`・`find_flag_settings`・`default_project` の 3 つをフックし、
4 つ目の入口（`check_notifications`）を呼ぶ変異が素通りした（N2）。本体の読む入口は道具関数に散っている
（`read_json`・`run`・`managed_dropins`・`global_config_path`）ので、**関数名で数える限り、入口を足すたびに同じ穴が開く。**

**一段下の、OS への入口で記録する**——`pathlib.Path` の読む系メソッド（`read_text`・`read_bytes`・`open`・`stat`・
`exists`・`is_file`・`is_dir`・`iterdir`・`glob`・`rglob`）・`builtins.open`・`subprocess.run`・`subprocess.Popen`。
`--push-result` の `main()` を呼ぶ間だけ差し替え、1 回でも呼ばれたら赤。

- **陽性対照を同じ記録器で取る**: `--push-result` を付けない `main()`（全点検）を同じ記録器の下で走らせ、記録が**空でない**ことを見る。
  空なら記録器が効いていない——「読まない」の緑は何も証明しない
- **取りこぼす形**（テストの docstring に書く）: `os.stat`・`os.listdir`・`os.scandir` を直に呼ぶ読み方と、環境変数の読み取り。
  本体はいまどれも `--push-result` の外でしか使っていない

## 乗るデプロイ経路

なし（テストだけ。`plugins/` も `docs/`（計画ファイルを除く）も公開物を変えない。計画ファイルは `docs/plans/` で、`mkdocs.yml` の nav には載らない）。
CI（`plugins.yml`）でテストが回る。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| 1 | N1: `--push-result ''`（空）を `main` 経由で渡すと、判定できない（2）を返し、全点検に落ちない | `main` の分岐（`is not None` を真偽で見る変異） | テストで `main(["--push-result", ""])` の終了コードと出力。変異「空の --push-result を見ない」が赤 |
| 2 | N2: `--push-result` は設定・ファイル・コマンドを 1 つも読まない | 本体のどの読む入口を呼ぶ変異でも（`check_notifications`・`check_sleep`・`read_json`・`run`） | OS への入口の記録が空。変異 2 本以上（`check_notifications` を呼ぶ・`check_sleep` を呼ぶ）が赤 |
| 3 | 2 の記録器が実際に効いている（陽性対照） | 記録器の差し替えが本体に届かない | 全点検の `main()` で記録が空でない |
| 4 | N3: 使用中の行の原因が「フォーカス」と「60 秒」を言う | `PUSH_RESULTS` の使用中の行の文言 | テストで原因の文字列。変異「60 秒を 30 秒にする」が赤 |
| 5 | テストは実環境を読まない・書かない（既存の約束） | 新しいシナリオが実 `HOME` を指す | 既存の形（偽の `HOME`・`--project`・`--managed-settings`・`--flag-settings` をテンポラリに）を踏襲 |
| 6 | 陽性対照（元の本体）が緑・全変異が赤・`check-all.py` が緑 | 登録漏れ・既存シナリオへの干渉（差し替えの戻し忘れ） | `python3 scripts/test-check-unattended-env.py`・`check-all.py` |

### 必須要件の掛け算

- 受入基準 × 2 つの関門 × 2 パス = 4 つの受け渡し（1 パス目の指摘対応の差分が 0 行なら 2 パス目は無い）。既知の限界も同じ回数渡す。

### この環境では証明できないもの（未証明）

- なし（テストだけで閉じる）

### 生成物

- 生成物なし（`SKILL.md` を触らないので §8.2 は動かない。図も触らない）

## 未解決の判断

- なし

## 周の在り処

- ブランチ: `issue/424-push-result-test-gaps`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-424`
- 起点: `159d0e6`（#422 のマージ）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `159d0e6ec03dd3345816a4232f615199ffa4d6ec`

## 関門の進捗（再開点）

- 実装: 済み。テストに `recording_reads()`（OS への読む入口の記録器）を足し、`--push-result` の `main()` を 3 形（`/config` のオフ・空・全点検＝陽性対照）で記録の下に走らせる。使用中の原因の「フォーカス」「60 秒以内」を見る。名前でのフック（#407 の S3）は記録器に置き換えた
- 変異: 4 件を足した（空の `--push-result` を見ない・通知の設定を読むが出さない・スリープを見るが出さない・60 秒を 30 秒に）。計 51 件すべて赤、陽性対照は緑。python3（3.14）と python3.12 の両方で「OK（失敗 0 件）」
- 交絡を潰した手順: 新しい変異と、#407 の「設定を読むが出さない」の 5 件について、どのチェックで赤になったかを scratchpad の複製で出した——どれも狙ったチェック（読まない・空・60 秒）で赤。記録器が効いていることは、テストの中の陽性対照（全点検の記録が空でない）で毎回見る。`check_sleep` の変異は `'darwin'` を渡す形にした（`sys.platform` だと Linux の CI では何も読まずに返り、変異が届かない）
- 実装のコミット: `a49d457`。`check-all.py`（`a49d457` の時点）: 49/49・失敗 0
- 1 パス目の指摘対応の起点: `a49d457`（1 パス目の関門に渡す時点の HEAD）
- 次: 手順 5 の Verifier 1 パス目と `/code-review` 1 パス目（base `159d0e6ec03dd3345816a4232f615199ffa4d6ec`）

## 起票

- この周の起票: 0 件（マージ前に確認する）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 本体を直す | 採らない | N1〜N3 はテストの穴で、現行のコードは正しい（#407 の狭いパスで Verifier が確かめた） |
| 「読まない」を関数名のフックで見る | 採らない | 入口を足すたびに同じ穴が開く（N2 そのもの）。OS への入口で見る |
| `os.stat`・`os.listdir`・`os.scandir`・環境変数の読み取りは記録しない | 採る（限界として docstring に書く） | 本体はいま使っていない。全部を塞ぐには `os` を丸ごと差し替えることになり、テスト自体の動作（テンポラリの読み書き）と干渉する |
