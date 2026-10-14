# Issue #253 — check-version-bump.py が版の後退（1.38.4 -> 1.38.3）を OK と判定する

元の周: #210（PR #252）で観測。

## 1. 変更範囲

触る:

- `scripts/check-version-bump.py` — 「変わったか」ではなく「上がったか」を見る（数値の semver 比較）
- `scripts/test-check-version-bump.py` — 新規。回帰テスト（変異テストを含む。使い捨ての git リポジトリだけを対象にする）
- `scripts/check-all.py` — `TESTS` に新しいテストを登録
- `.github/workflows/plugins.yml` — 新しいテストの CI ステップ
- `CLAUDE.md` — プロジェクト構成の `scripts/` 一覧に新しいテストと「下がった版も落とす」を足す
- `docs/plans/issue-253.md` — この計画ファイル

触らない:

- `plugins/` 配下（プラグインの中身は変えないので version bump も無い）
- `check-plugin-versions.py`（3 箇所の一致は別の歯止め。版の書式検査もここでは足さない）
- base に plugin.json が無い新規プラグインの扱い（従来どおり対象外）
- プラグインを触っていない PR で base 側だけ版が進んだ場合（マージ結果は base の版のままなので後退しない）

**複製の数**: 「版は上げる」を述べる箇所は 3（`CLAUDE.md`「プラグインの更新」・本体の docstring・CI のコメント）。
`CLAUDE.md`「プラグインの更新」は既に「上げる」と書いており、直すのは本体（実装と docstring）と構成一覧だけ。
分けない理由: 実装とテストと登録は 1 つの歯止めとして同時でないと `test-check-all.py` が落ちる。
**増やす変更と減らす変更**: 増やすだけ（判定を 1 つ足す）。

## 2. デプロイ経路

プラグイン配布物は変えない。main へのマージで Pages が再ビルドされる経路には乗る
（`docs/plans/issue-253.md` が載る。記録のみ）。CI の歯止めは main 到達後の PR から効く。

## 3. 受入基準

不変条件（触ったプラグインごと。base = 渡された base-ref の先端）:

- **V1** head の版 < base の版 → **非ゼロ終了**し、どのプラグインがどの版からどの版へ下がったかを出す（本件）
- **V2** head の版 > base の版 → OK（誤検知しない）。**比較は数値**——`1.38.10` > `1.38.9`、`1.10.0` > `1.9.0`
  （文字列比較なら逆になる）
- **V3** head の版 == base の版 → 従来どおり（挙動に影響する変更ならエラー、README.md だけなら警告）
- **V4** 版を比較できない（`X.Y.Z` の数字 3 つでない・欠落）→ **黙って OK にしない**（エラー）
- **V5** base に plugin.json が無い新規プラグイン → 従来どおり対象外
- **V6** 新しいテストが `check-all.py` の `TESTS` と `plugins.yml` に登録されている（`test-check-all.py` が緑）
- **V7** テストは実リポジトリを触らない（作業先が実リポジトリの内側ならアサートで落とす）
- **V8** テストに変異テストがある——本体の判定を「`!=`」に戻す／文字列比較にする変異で、テストが赤になる

| 経路（版の後退がマージに入る入口） | 守り方 |
| --- | --- |
| P1 PR の CI（`plugins.yml` の bump ステップ。base = `origin/<base_ref>`） | 本体の判定（V1〜V4） |
| P2 手元の `check-all.py`（`--base origin/main`） | 同じスクリプトを呼ぶ |
| P3 直接 `python3 scripts/check-version-bump.py <ref>` | 同上 |
| P4 ブランチが plugin.json を下げた（自分で書き換えた） | P1〜P3。plugin.json が diff に入るので対象になる |
| P5 ブランチは据え置き・他の PR が base を先に上げた（本件。#252） | base の**先端**と比べるので P1〜P3 で捕まる |
| P6 main への push（CI はこのステップを回さない） | **守らない**（既存の線引き。PR を経ずに main へ入れない規約が前提） |

**V1×V5 の交点**: 新規プラグインは base に版が無いので比較しない（後退という概念が無い）。
**V3×V4**: 両方とも同じ壊れた文字列なら「同じ」ではなく比較不能としてエラー（黙って従来判定に流さない）。

未証明: なし（すべて使い捨ての git リポジトリで再現できる）。

**生成物**: 該当なし——図（`diagrams/`）も `SKILL.md`（§8.2 の生成ブロック）も触らない。`check-all.py` の
`check-diagram-freshness.py` と `skill-metrics.py --check` が緑であることで確認する。

## 4. 未解決

- なし

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/253-version-bump-regression` ／ worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-253` ／ 起点 `6331379` ／
  base 参照 `origin/main`（解決した SHA `63313790e6781d3e70b3cf042dd30c4e0203853b`）
- 関門: 未着手
- 反証と差し戻し: なし
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

- base の**先端**と比べる（merge-base ではない）。マージ結果の版が下がるかを見たいので先端が正しい。
- prerelease（`1.0.0-rc.1`）は比較不能としてエラーにする。リポジトリの版はすべて `X.Y.Z` で、使う予定が無い。
