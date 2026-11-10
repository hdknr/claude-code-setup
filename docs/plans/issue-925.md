# Issue #925 — spec-loop の autopilot の回し方（外側のループ・線・前提）の公開ページ

不在の周（cruise の子）。出所: `/dev-loop:cruise 916 --absent` の起動（2026-11-10）。親 Issue #916・台帳 `issue-916`（台帳は親だけが書く）。
従う版は dev-loop 1.103.0（キャッシュ `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/dev-loop/SKILL.md`）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-916`。利用者の確認・起動時 2026-11-08T08:00:42Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す。マージ前の判断は線が無い（止まる——人の判断が要るものは「マージ前に人が判断」として報告する）
- 直す線: **既定**（出所: 上の cruise の確かめた線）
- 版の上げ方: **上げない**——`plugins/` を触らない（`docs/` と `mkdocs.yml` だけ。`check-version-bump.py` の対象外）
- PR は `Fixes #925`。手順 7 のマージは親がする（子は PR と PR 側の CI まで）
- 依存: #924（PR #943）はマージ済み（main `8cdd68a`）。この周はその上から切った

## 周の在り処

- ブランチ: `issue/925-spec-loop-autopilot-page`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-925`
- 起点コミット: `8cdd68a`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `8cdd68a7ae9c75e6377f2226f33107aeb302460a`

## 変更範囲

触る:
- `docs/plugins/spec-loop-autopilot.md` — 新しいページ（Issue の 1〜6）
- `mkdocs.yml` — nav の「プラグイン」に新しいページを足す
- `docs/plugins/index.md` — spec-loop の節の `autopilot` の 1 行から新しいページを指す
- `docs/plugins/spec-loop.md` — 冒頭の案内（と流れの節）から新しいページを指す
- `docs/plans/issue-925.md` — この計画

触らない:
- `plugins/spec-loop/` の中（`skills/autopilot/SKILL.md`・`scripts/autopilot-*.py`・`check-tlc.py`・README）——決まりの原本で、新しいページは指すだけ
- `plugins/dev-loop/` の中（`launch-with-long-token.sh`・cruise の `outer-loop.py`）——同上
- `docs/plugins/dev-loop-cruise.md`・`docs/usage/cruise-long-lived-token.md`——指すだけ（autopilot の記述を足さない）

複製の数（同じことを述べている箇所）:
- autopilot が何をするか（1 単位・台帳・しないこと）: 原本 `skills/autopilot/SKILL.md`、要約 `plugins/spec-loop/README.md` の節・`index.md` の spec-loop の節の 1 行・`index.md` の TLC の項、そして**この周が足すページ**。要約が 1 つ増える。
  分けない理由: Issue の求めが専用のページ（cruise の `dev-loop-cruise.md` と同じ形）で、ページは要点と指し先だけを持ち、線の項目・終了コード・止まる条件の細部は写さない。`index.md` の 1 行は新しいページへのリンクに寄せる
- 外側のループの止まる条件: 原本 `autopilot-loop.py` の docstring。ページは条件の名前だけを並べ、終了コードの表は写さない
- 線の項目: 原本 `autopilot-check.py` の docstring（値の一覧）と `SKILL.md` の 2（値ごとの振る舞い）。ページは 4 項目の名前と役割の一言だけ

## デプロイ経路

`docs/` と `mkdocs.yml` の変更——main へのマージで GitHub Pages の再ビルドと公開（`docs.yml`）。プラグインのカタログには何も配布しない（`plugins/` を触らない）。マージは親がする。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **ページがあり、nav と `index.md`・`spec-loop.md` から辿れる。**
   経路: `mkdocs.yml` の nav の行・`index.md` の spec-loop の節の `autopilot` の行のリンク・`spec-loop.md` の冒頭の案内（と流れの節）のリンク。ビルドした HTML でリンクが解決する。
2. **Issue の 1〜6（何をするか・起動時の確認・外側のループ・前提・止まったあと・守らないもの）がページにある。**
   経路: ページの各節。
3. **書いた事実が原本と食い違わない**——台帳のパス（`.claude/plans/spec-autopilot-v<版>.json`）・1 単位の中身（仕様レビューの周の 1 段か feasibility の 1 回）・しないこと（タグ・scaffold・Issue の登録）・起動時の確認（台帳が無いとき・`--lines`。単位を進めない）・
   外側のループの止まる条件の名前（`stopped`・`done`・判定できない・前進なし・起動の上限・同じ状態の上限・`claude` の失敗・上限の解除が遠い）と使用量の上限での待ち・長期トークンの渡し方（`--claude`）・
   TLC を確かめる段（`round1`・`round2`・`narrow`。`commit` と feasibility では確かめない）・ログの場所（`spec-autopilot-v<版>-loop/`）・再開のしかた（`next` を済ませて `status=running reason= next=` で戻す）。
   照合先: `skills/autopilot/SKILL.md`・`autopilot-ledger.py`・`autopilot-check.py`・`autopilot-loop.py`・`check-tlc.py` の docstring、`launch-with-long-token.sh`。
4. **決まり（線の項目と値の一覧・終了コード・止まる条件の細部）を書き写さず、`skills/autopilot/SKILL.md`・`autopilot-check.py`・`autopilot-ledger.py`・`autopilot-loop.py` の docstring を指している。**
   経路: ページの各段落の指し先のリンク。守り方: 指し先のファイルが main に実在する。終了コードの表・線の値の表がページに無い。
5. **既存のページ（`index.md` の spec-loop の節と TLC の項・`spec-loop.md` の形式検査の節・`dev-loop-cruise.md` の外側のループの節・`cruise-long-lived-token.md`）と食い違っていない。**
   経路: 新しいページの同じ話題の文。
6. **`python3 scripts/check-all.py` と `uv run mkdocs build --strict` が通る（ページ内・ページ間のアンカーが実在する）。**

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パス（1 パス目の指摘対応の差分が 0 行なら初回の 2 つ）に渡す。

### この環境では証明できないもの（未証明）

- 本物の `claude -p` で autopilot と外側のループを回したときに、ページの説明どおりに振る舞うこと——原本の docstring 自身が「守らない」としている（本物の上限の出力の形・入口が追記に従うか）。ページはそう書き、主張を「原本がそう決めている」まで弱める。

### 生成物

- **生成物なし**——drawio の書き出し・`SKILL.md` の測定値（`skill-metrics.py`）・spec-loop の生成物のどれにも触らない。サイトの HTML はビルドで作るもので、リポジトリに置かない（`mkdocs build --strict` で作れることだけを見る）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 割り目（手順 4）: 割らない（cruise の周）
- 交絡: 実験なし（ドキュメントの周。ビルドと歯止めの実行だけ）

## 既知の限界・決着済みの論点

- ページは決まりを写さない（`dev-loop-cruise.md` と同じ方針）。線の値の表・終了コードの表を足せという指摘は、受入基準 4 に反するので採らない。
- 「部品をそろえて通しで回した実績」の有無は、この周では確かめない（#789 の試作は部品が入る前の手作りのもの）。ページには「部品だけで通しで回した実績は確かめていない」とだけ書く。

## 手順 8（起票と件数）

- この周の起票: 0 件（cruise の子・不在の周。起票の候補は手順 8 の振り分けで決め、変われば直す）
