# Issue #1537 — platform-spec: 設定のタグ v1.0-lts と同じ数字の v1.0 を後ろの版に数えて逆向きに比べる（#1536 のフォローアップ）

**不在の周**（出所: `/dev-loop:cruise 1540 --absent` の起動・2026-11-25）。利用者には訊かない。親（cruise #1540）から委譲文で受けた子。
Issue #1537 は #1535 のマージ前の判断（確認の Issue #1536。利用者が 2026-11-24 に「確認の結果: 推奨のまま」で閉じた）のフォローアップ（`<!-- cruise-followup: #1508 -->`）。
本文の `作り直しの元: #1536` を PR の本文に写す。**選んだ値は (a)（今のまま。外し方を原本と docstring に書き、試料で固定する）**——#1536 の結果が「推奨のまま」で、推奨は (a)。

確かめた線（出所: cruise の確かめた線（台帳 `issue-1540`）。利用者の確認（起動時））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。
子はマージしない（親の委譲文）。台帳は書かない。

直す線: `既定`（出所: cruise の確かめた線）。
版の上げ方: `platform-spec` を **patch**（0.2.3 → 0.2.4）。マージ直前に main が先に上げていたら取り込んで次の patch に上げ直す。

## 変更範囲

触る:

- `plugins/platform-spec/scripts/check-profile-diff.py` — docstring の「守らないもの」の行に、この形と外し方を書く（振る舞いは変えない）
- `plugins/platform-spec/references/infra-profile.md` — 「版の差分と関門」の名前の形の文に、この形と外し方を書く（決まりの原本）
- `scripts/test-check-profile-diff.py` — 試料（`v1.0-lts` ＋ `v1.0` の系列だけの clone。1・`確かめたタグ`・`--new` で外して 0）
- `plugins/platform-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1537.md` — この計画

触らない:

- `newest()` の振る舞い（(a) は今のまま。(b)・(c) は選ばれていない）
- spec-loop の `profile-gate.py`
- platform-spec はスキルを持たないので `SKILL.md` の版の行は無い

依存の追加・更新: なし
仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない）

同じことを述べている箇所の数: 2（docstring の「守らないもの」の行と、決まりの原本）。試料はテスト側。
分けない理由: 同じ規則の言い換えなので、片方だけ直すと #1514 の型（原本と本体の食い違い）が戻る。同じ周で 2 箇所を揃える。

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json` の版）と GitHub Pages。子はマージしない。

## 受入基準

不変条件 × 破りうる経路（入口: CLI `check-profile-diff.py`（`--new` なし・あり）・spec-loop の `profile-gate.py` 越し・決まりの原本を読む人）:

| # | 不変条件 | 経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| 1 | Issue の示した入力（clone のタグ `v1.0`・`v1.0-lts`、設定のタグ `v1.0-lts`）で、`v1.0` を新しい版に数えて 1。原本と docstring の「守らないもの」にこの形と外し方（`確かめたタグ`・`--new`）が書かれ、試料が今の振る舞いを固定する | CLI（`--new` なし）・`確かめたタグ`・`--new v1.0-lts` | 試料「線の設定と同じ数字のリリース」（1）・「リリースを確かめたタグで外す」（0）・「リリースを --new で外す」（0）。(a) は振る舞いを変えないので陽性対照は要らない |
| 2 | #1515 の受入基準と既存の試料・変異が緑のまま | テスト | `python3 scripts/test-check-profile-diff.py`・`test-profile-gate.py` |
| 3 | 版が `plugin.json`・`marketplace.json` で揃って patch で上がる | 版 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| 4 | 本体の docstring と原本が同じ規則を同じ言い方で述べる | 原本・docstring | テストの原本との突き合わせ（既存）。新しい文は「守らないもの」と原本の同じ形・同じ外し方 |
| 5 | 歯止め全部（`check-all.py`）が緑 | 全体 | `run-serial.py` 越しの `check-all.py` |

必須要件の掛け算: 受入基準を両方の関門（Verifier・`/code-review`）に × 2 パス = 4 つの受け渡し（1 パス目の指摘対応が 0 行なら 2 パス目は該当なし）。

証明できないもの（未証明）: なし。
生成物: なし。
プロパティテスト: なし（名前の付け方ごとの試料で当てる。#1515 と同じ理由）
差分テスト: なし（振る舞いを変えない周。文面と試料だけ）

## 未解決の判断・確認待ち

- 仕様の穴: なし（選んだ値は (a) と確認の Issue #1536 の結果で決まっている）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1537-profile-lts-same-digits`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1537`・
  起点 `a50e080f`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `a50e080fb1e3715c0ae3e0aa51ac238ee1c2ec32`
- 割り目（手順 4）: 割らない（cruise の周）

## 既知の限界・決着済みの論点

- 綴りがプレリリースか版の線かを名前から見分けない（決着: 採らない——(b)・(c) は #1536 で選ばれなかった。外し方を書く）。

- この周の起票: 0 件（振る舞いを変えない文面と試料の周。起票の候補なし）
