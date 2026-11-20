# Issue #1372: test-qa-to-pptx.py の時計を読む変異の動的な検査の誤った赤と、zip の変異のコメントを直す

## 変更範囲

触る:

- `scripts/test-qa-to-pptx.py` — 動的な入れ忘れの検査を「主な生成が 0 で終わり、決定性の観測が `False` と観測できたとき」だけ数える（2 箇所）。`CLOCK_MUTATIONS` のコメントと、`shifted_clock` の docstring の言い過ぎ（#1371 の CR2-4。C3 が 3 箇所の文言を事実に合わせることを求めるので、この周に入れた）を事実に合わせる
- `docs/plans/issue-1372.md` — この計画

触らない:

- `plugins/`（本体は変えない。版も上げない）
- `CLOCK_MUTATIONS` の中身（「zip の時刻を固定しない」は実時計で待つ組に残す——下の「方針」）
- #1371 のそのほかの残課題（CR2-5〜CR2-7・V2-1・CR4・CR5）

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

## デプロイ経路

main へのマージ → GitHub Pages の再ビルド（計画ファイルだけがサイトに載る）。プラグインの中身は変えないので配布は起きない。

## 周の大きさ

同じことを述べている箇所: 動的な検査が 2 箇所（`MUTATIONS` と `CHECKER_MUTATIONS` のループ）。`CLOCK_MUTATIONS` の意味を述べているのは、その定数のコメント、`shifted_clock` の docstring、`observe` のコメント、変異テストの冒頭のコメント（1 パス目の CR1-1 で見つかった 4 箇所目）の 4 箇所。分けない理由: 同じ決まりの写しなので、片方だけ直すと食い違う。

## 方針（決めたこと）

- Issue の候補 1（`CLOCK_MUTATIONS` を `shifted_clock` で進まない時計に絞り、zip の変異を待たない組へ移す）は採らない。そうすると、zip の変異は待たない回で決定性が割れて殺される。すると「割れた変異は `CLOCK_MUTATIONS` にある」という動的な検査と食い違い、検査の意味を作り直すことになる——この周の範囲を超える
- 候補 2 を採る: 決まりを「時計を読む変異は `CLOCK_MUTATIONS` に入れ、実時計で待って当てる」の 1 つにする。コメントは「待たないと殺せない」ではなく、その決まりと、`datetime` のように進まない時計では入れないと殺せないことを書く

## 受入基準

不変条件 × 経路:

| # | 不変条件 | 経路（入口） | 確かめ方 |
| --- | --- | --- | --- |
| C1 | 時計を読まない変異は、動的な検査で赤にならない——主な生成が非 0 で終わる変異・観測の途中で例外になる変異を含む | `MUTATIONS`・`CHECKER_MUTATIONS` のループの動的な検査 | 写しに「`code, lines = qa.check(path)` → `code, lines = 1, ["x"]`」の変異を足し、動的な検査が赤にならない（「変異を殺せる」は緑）。base の版の写しでは同じ変異で赤になる（陽性対照） |
| C1b | 時計を読まずに、2 回の生成で出力が割れる変異（出力の名前など）は、動的な検査で赤にならない（1 パス目の CR1-3 で足した経路。人間の範囲の拡大ではなく、C1 の「時計を読まない変異」の経路の数え直し） | 同上 | 写しに `info.external_attr = (0o644 << 16) | len(out.name)` の変異を足し、動的な検査が ok |
| C2 | 時計を読む変異を入れ忘れると、動的な検査は今までどおり赤になる | 同上 | 写しに `writestr(name` と `__import__("time").localtime()` の変異を足し、動的な検査が赤 |
| C3 | `CLOCK_MUTATIONS` のコメント・`shifted_clock` の docstring・`observe` のコメントが事実と合う（待たずに殺せる変異を「待たないと殺せない」と書かない） | 3 箇所の文言 | 文言を読む。「zip の時刻を固定しない」を待たずに当てると殺される実測と突き合わせる |
| C4 | 「zip の時刻を固定しない」変異が今と同じく殺され、本物の本体は実時計で待つ | `MUTATIONS`・本物の本体の `observe` | 素の起動が `すべて合格`・「本物の本体の決定性の観測は zip の時刻の刻みをまたぐ」が緑 |
| C5 | 歯止めが全部緑 | リポジトリの CI | `python3 scripts/check-all.py` と PR 側の CI |

掛け算: 受入基準を Verifier と `/code-review` の両方に、2 パス（1 パス目の指摘対応の差分が 0 行なら 1 パス）。

未証明: なし。

生成物: なし（試料と出力は一時ディレクトリにだけ書く）。

## 未解決の判断

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1372-clock-check-fix`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1372`・起点 `de438dca`・base は `origin/main`（refs/remotes/origin/HEAD）を解決した `de438dcacaae20c2a44c2006cb8107add0fb69b0`
- 探索（`find-cycle.py`）の当たりは #1369 の計画ファイルのコミット `fa2d3479`（メッセージが #1372 を起票先として名指ししていた）だけで、#1372 の worktree・ブランチ・計画ファイルは無かった——新規の周と判断した
- 直す線: 既定（出所: 手順 3 の回答 2026-11-20）
- 実装: `5c1843b3`（`Fixes #1372`）
- 割り目（手順 4）: `AskUserQuestion` で「ここで割る」（2026-11-20）。**再開は手順 5 から**——1 パス目の Verifier と `/code-review` を当てる。1 パス目の起点は再開した側が関門に渡す時点の HEAD を書く（この計画を書いたコミット）。`check-all.py` もまだ回していない
- 1 パス目の起点（関門に渡した時点の HEAD）: `659caee108e19ab588675837106a35274d879117`
- 関門 1 パス目（2026-11-20）: Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件（前からある限界 1 件を添えた——CR1-3 と同じ）。`/code-review`（high）指摘 6 件。`check-all.py`: 55/99 本を回して失敗 0（44 本はキャッシュ）
- 1 パス目の指摘対応: CR1-1・CR1-2・CR1-3・CR1-5 を直した（採否の表）。CR1-3 の直しで `frozen_clock`・`split_with_frozen_clock` を足した（同じファイルの中。受入基準 C1 に経路「時計のほかで決定性が割れる変異」を足した）
- 指摘対応の実測（2026-11-20。写しはリポジトリの外）: 素の起動 `すべて合格`・刻みをまたぐ `True`（C4）。時計を読まない「出力名を属性に混ぜる」（`info.external_attr = (0o644 << 16) | len(out.name)`）は動的な検査が ok（直す前の版では赤——/code-review の実測が陽性対照）。`writestr(name`・`__import__("time").localtime()`・`CLOCK_MUTATIONS` から外した「zip の時刻を固定しない」は動的な検査が赤のまま（C2）。主な生成を非 0 にする変異は動的な検査が ok（C1）。`__import__("time").strftime` を読む変異は「変異を殺せる」だけが赤（新しいコメントのとおり）
- 指摘対応のコミット: `db55e432`。その後の `check-all.py`: 18/99 本を回して失敗 0（81 本はキャッシュ）
- 割り目（手順 6、2 パス目の前）: `AskUserQuestion` で「ここで割る」（2026-11-20）。**再開は 2 パス目から**——残りは**手順 5 の当て直し（Verifier 2 パス目）**と **`/code-review` 2 パス目**の**両方**（どちらも未着手）。base は上の `de438dca…` のまま。2 パス目の指摘対応を始める直前に、狭いパスの起点（その時点の HEAD）をここに書く
- 再開（2026-11-20、`/clear` の後）: 肯定的な確認でブランチ `issue/1372-clock-check-fix`・HEAD `11c16bc8` を確かめた。1 パス目の指摘対応の差分（起点 `659caee1` から、計画ファイルを除く）は `scripts/test-qa-to-pptx.py` の 75 行で 0 行ではない——2 パス目を回す
- 関門 2 パス目: Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件・限界 1 件（V2-1。採否の表）。git status は前後とも空。`/code-review`（high）指摘 5 件（important 3・nit 2）。採否は「2 パス目の採否の表」——直す 4 件（V2-1・CR2-1・CR2-2・CR2-3）、残課題 2 件
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `c247b771cad4053b6faae6d7284843dd266e9549`
- 2 パス目の指摘対応: V2-1・CR2-1・CR2-2・CR2-3 を直した（`split_with_frozen_clock` を `output_follows_clock` に置き換え、`frozen_clock` に止める時刻と `monotonic`・`perf_counter` を足し、コメントを合わせた）。狭いパスの終点: `28842c625c455e7d693da62ef66fe975d002f222`
- 指摘対応の実測（2026-11-20。写しはリポジトリの外）: 素の起動 `すべて合格`・刻みをまたぐ `True`（C4）。時計を読む `X-both`・`X-mono`・`X-lt` は「時計を読むらしい…」が FAIL（C2）。時計を読まない `X-state`・`X-rand`・`X-name`・`X-rc` は ok（C1・C1b）。`check-all.py`: 17/99 本を回して失敗 0（82 本はキャッシュ）
- 狭いパス: 起動中
- 手元の実測（2026-11-20）:
  - 素の起動: `PPTX 生成のテスト: すべて合格`・「本物の本体の決定性の観測は zip の時刻の刻みをまたぐ（実際: True）」（C4）
  - 陽性対照の写し（走らせた後に消した）: 新しい版に「主な生成を非 0 にする」変異を足した写しは終了コード 0（動的な検査は緑・「変異を殺せる」も緑）（C1）。base（`de438dca`）の版に同じ変異を足した写しは「時計を読むらしい変異が CLOCK_MUTATIONS に無い: X: 主な生成を非 0 にする」で赤（直す前の欠陥の陽性対照）。新しい版に `writestr(name`・`__import__("time").localtime()` の変異を足した写しは 2 本とも動的な検査が赤（違った観測は `deterministic`）（C2）
  - docstring の主張: `time.time`・`time.localtime` を差し替えた中で、属性として呼ぶ `time.localtime()` は進み、`from time import localtime` で束縛した関数・引数なしの `time.strftime`・`time.ctime()` は進まなかった（C3）
- 交絡を潰した手順: C1 の「赤にならない」は否定的な結果なので、同じ変異を base の版に当てて赤になる陽性対照を取った（上）

- この周の起票: 0 件

## 既知の限界・決着済みの論点

- 候補 1 を採らない理由は上の「方針」
- `datetime` の時計は `shifted_clock` で進まない（#1369 から残る限界。この周では変えない）

### 1 パス目の採否の表（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1-0 | Verifier: 反証 0 件。時計のほかの非決定性も「時計を読む」と数える限界を添えた | CR1-3 と同じ | C1 | CR1-3 で直す |
| CR1-1 | 818 行のコメント「時計を読む変異が漏れると、待たずに当てて生き残る」が偽 | 示せる——「zip の時刻を固定しない」を `CLOCK_MUTATIONS` から外すと殺され、動的な検査が赤（/code-review の実測） | C3 | 直す |
| CR1-2 | `CLOCK_MUTATIONS` のコメントと `shifted_clock` の docstring の冒頭が言い過ぎ（`time.strftime`・`time.ctime` は属性でも進まない） | 示せる——`__import__("time").strftime` を読む変異が待たずに生き残った | C3 | 直す |
| CR1-3 | 時計を読まずに出力が割れる変異も、動的な検査で赤になる | 示せる——`len(out.name)` を混ぜる変異で赤（/code-review の実測） | C1 | 直す（時計を止めて同じ名前で 2 回作り、割れたら時計のほかと読む） |
| CR1-4 | 静的な検査 `CLOCK_READERS` が `__import__("time")`・`from time import` を見逃す | 示せる | 無し（前からある。C2 は動的な検査） | 残課題 |
| CR1-5 | `observe` のコメントが、待つ枝だけが zip の変異を捕まえるように読める | 示せる——待たない枝でも `deterministic=False` | C3 | 直す |
| CR1-6 | `SOURCE_DATE_EPOCH` を設定した Python 3.13 以降では `zipfile` の既定の時刻が固定され、docstring が当たらない | 示せない（走らせていない） | 無し | 残課題 |

### 2 パス目の採否の表（直す線: 既定）

再現は著者がリポジトリの外の写し（`git archive` で展開）に変異を 1 つ足して素の起動を回した。HEAD は `11c16bc8`、base は `de438dca`。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V2-1 | Verifier: 時計も読み出力名でも割れる変異（`X-both`）を `CLOCK_MUTATIONS` に入れ忘れても、動的な検査が赤にならない（Verifier は「限界」として添えた） | 示せる——`X-both`（`len(out.name)` と `__import__("time").localtime()[5]`）が HEAD で rc=0・「時計を読むらしい…」ok、base で FAIL | C2（今までどおり赤、が後退） | 直す |
| CR2-1 | `frozen_clock` が止めない時計（`monotonic_ns`・`perf_counter` など）を読む変異が、入れ忘れても赤にならない | 示せる——`X-mono`（`__import__("time").monotonic_ns()`）が HEAD で rc=0、base で FAIL | C2 | 直す |
| CR2-2 | `split_with_frozen_clock` が `observe` で何度も呼んだ同じ `mod` で作り直すので、初回と 2 回目以降で出力が変わる（時計を読まない）変異が赤になる | 示せる——`X-state`（`globals()` に名前を貯める）が HEAD で FAIL（base でも FAIL——前からある） | C1 | 直す |
| CR2-3 | `CLOCK_MUTATIONS` のコメント「進まない時計を読む変異は、ここに入れないと殺せない」が偽 | 示せる——`X-mono` は入れずに待たないで殺された（違った観測: deterministic） | C3 | 直す |
| CR2-4 | 時計を止めた生成の例外・出力なし・非 0 を「時計のほかで割れた」と扱い、赤を消す | 示せない（走らせていない） | 無し | 残課題（ただし CR2-1・CR2-2 の書き直しで同じ関数の振る舞いを決め直すので、「決められない」は時計を読む側（赤）に倒す——狭いパスで見る） |
| CR2-5 | `frozen_clock` が `shifted_clock` の時計の一覧と退避・復元を写している | 示せない（一覧がずれた実例は無い） | 無し | 残課題 |

直し方: 時計を止めた生成は、同じ変異の本体を毎回新しく読み込み直し（`load`）、同じ出力名で別のディレクトリに 3 回作る——止めた時刻 T で 2 回（割れたら止めた時計のほかで割れている）、T+`CLOCK_SHIFT` で 1 回（T の 1 回と割れたら時計を読む）。`frozen_clock` は止める時刻を引数に取り、`monotonic`・`perf_counter`（と `_ns`）も止める。コメント・docstring を合わせる（C3）
