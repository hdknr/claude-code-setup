# Issue #944 — test-check-all.py: steps: と同じ字下げの run:（コンパクトな列）を gated_runs が偽の赤にする

不在の周（cruise の子）。出所: `/dev-loop:cruise 947 --absent` の起動（2026-11-10）。親 Issue #947、台帳 `issue-947`（台帳は親だけが書く）。
従う版は dev-loop 1.99.0（キャッシュ。`SKILL.md` 1861 行——`wc -l`）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-947`）——利用者の確認（起動時・2026-11-10T08:57:23Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-947`））
- 版の上げ方: **上げない**——`plugins/` を触らない（`scripts/test-check-all.py` と計画だけ。`check-version-bump.py` の対象外）
- PR は `Fixes #944`。手順 7 のマージは親がする（子は PR と PR 側の CI まで）

## 周の在り処

- ブランチ: `issue/944-compact-steps`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-944`
- 起点コミット: `0215da4`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `0215da441d9f250d2fff5bd62d999ea61485e23e`

## 変更範囲

触る:
- `scripts/test-check-all.py` — `gated_runs` がコンパクトな列（`steps:` と同じ字下げの `- `）を前の鍵の値の続きと読む。試料（`SAMPLE_JOBS`）・契約（`scan_contract`）・判別の変異（`SCAN_MUTANTS`）・docstring の守る／守らないを直す
- `docs/plans/issue-944.md` — この計画

触らない:
- `.github/workflows/*.yml`——書き方は変えない（今の 3 つの yml はコンパクトな列を使っていない）
- `docs/plans/issue-931.md`——前の周の記録（「記録だけ」と書いた当時の判断のまま残す）
- `CLAUDE.md`——`test-check-all.py` の行は条件を docstring に任せていて、コンパクトな列に触れていない（`grep コンパクト` で確かめた）
- タブで始まる行・必ず走る `if:` の偽の赤——Issue の範囲外（守らないに残す）

複製の数（同じことを述べている箇所）: コンパクトな列の偽の赤を述べるのは `test-check-all.py` の 3 箇所——モジュールの docstring の「守らない」（69 行）・`gated_runs` の docstring（714 行）・`scan_contract` の契約の「守らない」の項（1195 行）。`grep -rn コンパクト` で確かめた（ほかは `docs/plans/issue-931.md` の記録だけ）。1 ファイルの中なので分けない。

## デプロイ経路

`CI の歯止め`——main へのマージで次の PR・push から効く。`plugins/` を触らないので、プラグインの配布は起きない（GitHub Pages の再ビルドは起きるが、計画ファイルのページが 1 枚足されるだけ）。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **`steps:` と同じ字下げの `- run:`（コンパクトな列）を、`steps:` の下の `run:` として数える（無条件のジョブなら無条件）。**
   経路（入口は `plugins.yml`・`docs.yml`・`release.yml` に人が書きうる書き方）:
   (a) `steps:` の直下の項を全部コンパクトな列で書く（`- run:` / `- name: …` の次の行の `  run:`）、
   (b) コンパクトな列の後ろにジョブ単位の鍵（`needs:`・`if:`）が来る——ジョブ単位の鍵は今までどおり効く（条件つきに数える）、
   (c) ジョブ単位の `needs:` をコンパクトな列で書く（`needs:` の下の `- plain`）——`needs:` は 1 つの鍵のまま（重なりに数えない）、
   (d) `steps:` でない鍵の下のコンパクトな列——その鍵の下のまま（`steps:` の外）、
   (e) 鍵の段より浅い `- `——今までどおり鍵の段でない（`steps:` の外）。
   守り方: `gated_runs` で、鍵の段と同じ字下げの `- ` で始まる行は、鍵を読み直さず前の鍵のまま、鍵の一覧にも足さない。
2. **陽性対照: 今の 3 つの yml で `--part registry` が緑のまま。**
3. **試料と変異**: コンパクトな列の試料を `SAMPLE_JOBS` に持ち（(a)〜(e)）、読み方を #944 の前に戻す変異（コンパクトな列を `steps:` の外と読む）が `--part scan` で赤になる。(d)(e) を壊す変異（コンパクトな列を `steps` と決め打ち・字下げに依らず続きと読む）も赤になる。
4. **docstring**: モジュールの docstring と `gated_runs` の docstring の守らないから、コンパクトな列の偽の赤の記述を外し、守るに書く。契約の「守らない——偽の赤」の項を外す。
5. **既存の判別を壊さない**: `scan_ci_runs`・`full_runs`・`gated_runs` の既存の契約（`--part scan`）と既存の `mutation-claim` が緑のまま。
6. `python3 scripts/check-all.py` が緑（run-serial 越し）で、PR 側の CI も全部緑。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）に渡す——4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

検証で証明できるもの: 1〜6。

未証明: **GitHub がコンパクトな列をどう読むか**は、YAML の仕様（ブロックの列はその親の鍵と同じ字下げに置ける）と PyYAML で読めることで代える（GitHub の実物で走らせてはいない）。受入基準は行を読む判定の側なので、証明に要らない。

生成物: なし（`test-check-all.py` は手で書くテストで、生成ブロックを持たない。`skill-metrics.py` の対象は `SKILL.md` だけ）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 実装: 着手
- 手順 4 の割り目: 割らない（cruise の周）
- 交絡を潰した手順: 実験なし（変異と試料の当ては `--part scan`・`check-mutation-claims.py` が陽性対照つきで回す）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| タブで始まる行・必ず走る `if:` の偽の赤 | 直さない（守らないに残す） | #944 の範囲外。#931 で受け入れた |
| YAML として読めないコンパクトな列（鍵の段より浅い `- `・値を持つ鍵の後ろの `- `） | 今までどおり `steps:` の外（赤） | GitHub もそのワークフローを読めない。向きは赤 |

## 手順 8

- この周の起票: 0 件（周の途中。手順 8 の振り分けで決まったら書き直す）
