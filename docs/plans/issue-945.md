# Issue #945 — test-check-all.py: 無条件のジョブで狭め、全部を回すのは条件つきのジョブだけ、の形を full_runs と gated_runs が両方緑にする

不在の周（cruise の子）。出所: `/dev-loop:cruise 947 --absent` の起動（2026-11-10）。親 Issue #947、台帳 `issue-947`（台帳は親だけが書く）。
従う版は dev-loop 1.99.0（キャッシュ。`SKILL.md` 1861 行——`wc -l`）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-947`）——利用者の確認（起動時・2026-11-10T08:57:23Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-947`））
- 版の上げ方: **上げない**——`plugins/` を触らない（`scripts/test-check-all.py` と計画だけ。`check-version-bump.py` の対象外）。マージ直前の取り込みでも版の行は出ない
- PR は `Fixes #945`（`Refs #931 #942 #687`）。確認の Issue #949 は指さない。手順 7 のマージは親がする（子は PR と PR 側の CI まで）

## 周の在り処

- ブランチ: `issue/945-full-and-ungated`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-945`
- 起点コミット: `be39787b`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `be39787b04cc36397793ff8fc7a802717cb673c3`

## 変更範囲

触る:
- `scripts/test-check-all.py` — `full_runs`・`gated_runs` を行ごとの形（`full_lines`・`gate_records`）に分け、同じ行で両方を満たす名前を返す `full_ungated_runs` を足す。収録漏れの検査（`--part registry`）に組の検査を足し、試料（`SAMPLE_SPLIT`）・契約（`scan_contract`）・判別の変異（`SCAN_MUTANTS`）・docstring の守る／守らないを直す
- `docs/plans/issue-945.md` — この計画

触らない:
- `.github/workflows/*.yml`——書き方は変えない（今の 3 つの yml は、収録した回帰テストを全部、無条件のジョブで引数なしで回している）
- `CLAUDE.md`——`test-check-all.py` の行は条件を docstring に任せていて、`full_runs`・`gated_runs` に触れていない（`grep` で確かめた）
- 歯止め（`GUARDS`）の引数——組の検査は `full_runs` と同じく回帰テスト（`TESTS`）にだけ掛ける

複製の数（同じことを述べている箇所）: 2 つの検査が別々であることを述べるのは `test-check-all.py` の中だけ——モジュールの docstring の守る（2 項）と守らない（`full_runs` の項）・`full_runs` と `gated_runs` の docstring。1 ファイルの中なので分けない。

## デプロイ経路

`CI の歯止め`——main へのマージで次の PR・push から効く。`plugins/` を触らないので、プラグインの配布は起きない（GitHub Pages の再ビルドは起きるが、計画ファイルのページが 1 枚足されるだけ）。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **収録した回帰テストは、無条件に走るジョブの `steps:` の下の、同じ `run:` の行で引数なしで呼ばれていなければ赤（`--part registry`）。**
   経路（入口は `plugins.yml`・`docs.yml`・`release.yml` に人が書きうる書き方）:
   (a) 無条件のジョブでは引数を付けて狭め、引数なしの行は `if:` のジョブにだけ置く、
   (b) 同じく、引数なしの行は `needs:` のジョブにだけ置く、
   (c) 無条件のジョブの同じ行で、別の名前は引数なし・その名前は狭める（`a --part x && b`）、
   (d) 引数なしの行が無条件のジョブにある（陽性——数える）。
   守り方: `full_lines`（行ごとの引数なしの名前）と `gate_records`（行ごとの位置の理由）を同じ行の番号で突き合わせる `full_ungated_runs`。
   名前ごとの集合の積では (a)(b) が緑のまま。
2. **陽性対照: 今の 3 つの yml で `--part registry` が緑のまま。**
3. **試料と変異**: (a)〜(d) の試料を `SAMPLE_SPLIT` に持ち、判定を戻す変異（名前ごとの集合の積に戻す・条件つきの位置の行も数える・狭めた行も数える）が `--part scan` で赤になる。
   実物の `plugins.yml` に (a) の形を入れる `mutation-claim` が `--part registry` で赤になる。
4. **docstring**: モジュールの守る／守らない・`full_runs`・`gated_runs` の docstring が実装と合う（2 つが別々に見ること、組は `full_ungated_runs` が見ること）。
5. **既存の判別を壊さない**: `scan_ci_runs`・`full_runs`・`gated_runs` の既存の契約（`--part scan`）と既存の `mutation-claim` が緑のまま。
6. `python3 scripts/check-all.py` が緑（run-serial 越し）で、PR 側の CI も全部緑。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）に渡す——4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

検証で証明できるもの: 1〜6。

未証明: なし（行を読む判定で、GitHub の実物の挙動には寄りかからない）。

生成物: なし（`skill-metrics.py` の対象の `SKILL.md`・図の書き出しを触らない）。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目: Verifier（`dev-loop:dev-loop-verifier`、sonnet）と `/code-review`（high）に受入基準 1〜6・既知の限界を渡した。起点 `3d2ee4204c0d489d9ab33e6d0a5f45e1425aed15`
  - Verifier: 反証 0 件（受入基準 1〜5 一致。mutation-claim を外の複製で当てて赤を確認。`git status --porcelain` は前後とも空）
  - `/code-review`: 指摘 6 件（受入基準を破るものは 0 件）——採否は下の表。差し戻し: なし
- 2 パス目: 該当なし——理由: 1 パス目の指摘対応の差分 0 行（「直す」の行 0 件）。起点 `3d2ee420`、`git diff 3d2ee420 -- ':(top)' ':(top,exclude)docs/plans/issue-945.md'` は空、`git status --porcelain` に計画ファイル以外は出なかった
- 狭いパス: 該当なし
- 割り目（手順 6）: 2 パス目が無いので置かない
- 実験: 実物の `plugins.yml` の複製に (a) の形を入れ、新しい版で `--part registry` が組の検査だけ赤（他の 5 つは緑）、元の版（`be39787b`）で緑——を確かめた（A/B。同じ複製・同じ変異で版だけ変えた）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `full_ungated_runs` は `full_runs`・`gated_runs` の守らないものをそのまま持つ（ステップの `env:` で狭めた行・ステップの `if:`・アンカーなど） | 採らなかった（直さない） | Issue の範囲は 2 つの判定の組だけ。各判定の守らないものはモジュールの docstring に書いてある |
| 組の検査は回帰テスト（`TESTS`）にだけ掛け、歯止め（`GUARDS`）には掛けない | 採った | `full_runs` と同じ——歯止めには引数が要るもの（`skill-metrics.py --check` など）があり、引数なしを要求できない |
| `full_runs`・`gated_runs` のどちらかで既に赤の名前は、組の検査に重ねて出さない | 採った | 直し方が別の行に出ているので、同じ名前を 2 度挙げない |

### 1 パス目の指摘の採否（`/code-review` 6 件・Verifier 0 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 | 振り分け（found-lines） |
| --- | --- | --- | --- | --- |
| CR1: 無条件のジョブの行に名前が書いてあるだけ（`test -f scripts/test-x.py`）でも「全部を回す」に数える | 示せる（レビューの probe） | 無し（`full_runs` の `FULL_RE` から来た穴で、この周の前から同じ） | 残課題 | 記録だけ（実際の利用でまず起きない形・この周の後退ではない） |
| CR2: 組の検査の失敗の文言が、理由に依らず「条件つきのジョブにだけ」「SKIPPED」と言う（全部を回す行が `jobs:` の外・`steps:` の外・鍵の重なりのときも） | 示せる（レビューの probe e・f） | 無し（赤にはなる。受入基準は赤にすることと docstring） | 残課題 | 直す（利用者に見える誤り。この周が足した文言。後退ではない——前は緑だった）。仕様の穴ではない |
| CR3: (b)(c) の試料を単独で要る変異が無い | 示せる（レビューの追加変異） | 無し | 残課題 | 記録だけ（試料の穴） |
| CR4: `scan_contract` の docstring が `SAMPLE_SPLIT`・`both_of` に触れていない | 示せる（docstring） | 無し（受入基準 4 はモジュール・`full_runs`・`gated_runs` の docstring） | 残課題 | 記録だけ |
| CR5: 3 つの検査を 1 つ（`full_ungated_runs`）にまとめる高さの提案 | 示せない（設計の提案） | 無し | 残課題 | 捨てる |
| CR6: CI の文字列を 2 度読む（`full_lines` が O(n²)） | 示せない（遅さの実測なし） | 無し | 残課題 | 捨てる |

## 手順 8（起票と学び）

- この周の起票: 0 件（不在の cruise の周——起票の候補は振り分けで直すの行だけで、いまは無い）
