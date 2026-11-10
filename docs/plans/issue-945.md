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
- 実験: 実物の `plugins.yml` の複製に (a) の形を入れ、新しい版で `--part registry` が組の検査だけ赤（他の 5 つは緑）、元の版（`be39787b`）で緑——を確かめた（A/B。同じ複製・同じ変異で版だけ変えた）
