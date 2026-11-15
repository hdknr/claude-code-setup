# Issue #1020 — TLC の反例の JSON（`-dumpTrace json`）から trace ケースの `steps` を作る

## この周の形（不在の cruise の周）

- **不在の周**——cruise（親 Issue #1038）の子として回す。利用者は周の途中にいない。
- **台帳の確かめた線**（出所: 利用者の確認（起動時・2026-11-15T02:04:18Z、配布を見せて確かめた）。`/dev-loop:cruise 1038 --absent` の起動・2026-11-15）:
  仕様の穴 = 推奨で決めて起票, 直す線 = 既定, マージ = 関門を通ればマージ, 周の途中の課題 = 台帳に足して直す, マージ前の判断 = 推奨で決めて起票。実機確認の線は無い（既定）。
- **直す線: 既定**（出所: cruise の確かめた線）。
- **手順 7 のマージは親がする。** 子は PR を作り、PR 側の CI の最終結果を見るところまで。台帳は書かない。
- **割り目（手順 4・6）は訊かない**——割らない（cruise の周）。
- **版の上げ方: spec-loop を minor で上げる（0.88.0 → 0.89.0）**——変換のスクリプトを足す能力の追加（0.x）。

## 周の在り処

- ブランチ: `issue/1020-tlc-trace-json`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1020`
- 起点コミット: `902bc79`
- base: `origin/main`（`refs/remotes/origin/HEAD`）を解決した `902bc79d136a73a5c9275a1aa85ddc00dc919318`

## 変更範囲

触る:

- `plugins/spec-loop/scripts/tlc-trace.py` — 変換（新規。反例の JSON と対応表から trace ケースを出す）
- `scripts/test-tlc-trace.py` — 回帰テスト（新規。変異テストを含む）
- `scripts/check-all.py` — テストの収録
- `.github/workflows/plugins.yml` — CI のステップ
- `plugins/spec-loop/references/spec-ir.md` — 「トレースのケース」に変換を指す 1 段落
- `plugins/spec-loop/agents/formal-checker.md` — `トレース` の段の並びを、`-dumpTrace` を持つ TLC なら変換で出す
- `plugins/spec-loop/README.md` — 中身の表に 1 行・「TLC の用意」に `-dumpTrace` の版の 1 段落
- `plugins/spec-loop/skills/*/SKILL.md` — 版のバナー（全スキル）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `CLAUDE.md` — プロジェクト構成（スクリプトとテスト）
- `docs/plans/issue-1020.md` — この計画

触らない:

- `plugins/spec-loop/scripts/check-tlc.py`（`-dumpTrace` は必須にしない——下の「仕様の穴」。確かめの 2 つのモデルは変えない）
- `plugins/spec-loop/scripts/scaffold.py`（trace ケースの形・検査は変えない。変換の出力はそれに当てるだけ）
- spec-review・scaffold のスキルの手順（変換は Formal Checker の報告を作る段で使う）
- プラグインの紹介文（description）

## 乗るデプロイ経路

main へのマージでプラグインの配布（`marketplace.json`・`link-skills.sh`）。`docs/` は触らないが、`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」に乗る。

## 周の大きさ（同じことを述べている箇所の数）

「TLC の反例の JSON から `steps` を作る変換」を述べる箇所: `tlc-trace.py` の docstring（原本——対応表の形・終了コード・守る／守らない）・`spec-ir.md`・`formal-checker.md`・`README.md`（2 箇所）・`CLAUDE.md` の **6 箇所**。
**分けない理由**: スクリプトを足すと README・CLAUDE.md の一覧は同じ PR で揃える決まり。決まり（対応表の形・止める条件）は docstring だけに書き、ほかは指すだけにする。

## 仕様の穴（不在の線で推奨により決めた）

- **穴**: Issue の「やること」の 2 つ目——正本の `TLC の呼び方:` の TLC（TLC 2.19）は `-dumpTrace` を持たない。TLC の版を上げるか、`apalache.jar` の TLC を使うか。
- **選択肢**: A: `-dumpTrace` を必須にせず、持つ TLC の呼び方なら変換を使い、持たなければ今のとおり出力から手で写す（`check-tlc.py` は変えない） / B: TLC を v1.8.0 のプレリリース以上に上げることを前提にし、`check-tlc.py` で `-dumpTrace` を確かめる / C: `apalache.jar` の TLC を呼び方にすることを前提にする
- **決めた値: A**
- **推した理由**: v1.8.0 はプレリリースで安定版（v1.7.4 = TLC 2.19）は `-dumpTrace` を持たない。B・C は利用者の環境に前提を足し、今の正本を「TLC が無い」側に倒しうる。A は今の動きを変えずに、持つ TLC を入れた利用者（手元は v1.8.0 プレリリースを入れた——Issue のコメント）にだけ機械の変換が効く。変換そのものはどの TLC の JSON でも同じ形を読む（形は v1.8.0 で確かめた）。
- **使った線**: 仕様の穴 = 推奨で決めて起票（cruise の確かめた線）。確認の Issue: （起票後に書く）

## verify の受入基準

### 証明できるもの

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | 反例の JSON の行為の並びの順と、`steps` の並びの順が同じで、各段の呼び出し・段の名前は対応表で引いた値 | (1) 行為の名前を `pc` の差から推す (2) 対応表の鍵に無い行為を黙って捨てる・推す (3) 呼び出しの引数の値を文字列化の違いで取り違える | 行為の `name` と `context` の呼び出しの引数だけで決める。表に無い行為・`skip` に無い行為は 1 |
| B | 呼び出しを決められない行為を、推して段にしない | (1) 引数の無い行為（`Done`、`\E` を行為の中に書いたモデルの `Next`） (2) 呼び出しの引数のほかの引数がある行為 (3) 呼び出しの値が `calls` に無い | どれも 1 で止める（`skip` に挙げた行為だけ飛ばす） |
| C | 有限の順で再現できない反例（繰り返しのある反例＝活性の違反）を `steps` にしない | (1) 最後の行為が前の状態へ戻る（`Back to state`） (2) 状態の番号が飛ぶ・前の行為の後の状態と次の行為の前の状態が食い違う | 戻る形は 1、番号の食い違いは 2 |
| D | 反例の無い・形の違う入力を、空の `steps` で 0 にしない | (1) 行為が 0 個（初めの状態で違反） (2) JSON でない・鍵が無い (3) 対応表の形が違う（`rest` に `steps` などを入れて上書きする） | 段が 2 つより少なければ 1。形の違いは 2 |
| E | 出力は spec-ir の trace ケースの形で、本物の `scaffold.py` の `check_trace` を通る | (1) `calls` の形を変える (2) `rest` を写さない | テストが本物の `scaffold.py` の `check_trace` に当てる。本物の TLC v1.8.0 の JSON（#1015 のモデル）から #1015 の A4 と同じ `steps` が出る |
| F | 文書の指し先が実在し、決まりを写さない | (1) spec-ir.md・formal-checker.md・README が別の名前を指す (2) 対応表の形を 2 箇所に書く | `check-skill-pointers.py`、テストが指し先を見る |
| G | 版を 3 種類で揃える | (1) バナーの上げ忘れ | `check-plugin-versions.py` |

### この環境では証明できないもの（未証明）

- **本物の TLC の版ごとの JSON の形**——v1.8.0 のプレリリース（`2026.11.15.002146`）で確かめた形だけ。apalache.jar の TLC の JSON の形は #1015 の記録（行為の名前・`context`・`parameters`）に合うことしか確かめていない。CI には TLC が無いので、テストは手元で取った JSON を試料として埋める。

### 生成物

- **生成物なし**——`diagrams/`・`SKILL.md` の測定値（§8.2 の生成ブロック）は触らない（`skill-metrics.py --check` は dev-loop の `SKILL.md` だけを測る）。

### 必須の組み合わせ

- 受入基準を Verifier と `/code-review` の両方に、1 パス目・2 パス目とも渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

## 未解決の判断

- 上の「仕様の穴」の確認の Issue（利用者の確認待ち）。

## 関門の進捗（再開点）

- 再開点: 割らない（cruise の周）。
- 実験: 本物の TLC v1.8.0 で `-dumpTrace json` の形を確かめた（#1015 の付録 A のモデルの守りなし・引数の 2 つの行為・`\E` を行為の中に書いたモデル・活性の違反（繰り返し）・初めの状態の違反・デッドロック）。

## 既知の限界・決着済みの論点

（関門の後に書く）

## 手順 8（起票数）

- この周の起票: 1 件（仕様の穴を推奨で決めた確認の Issue。不在の線のため利用者には訊いていない）
