# Issue #275: spec-loop — build-proposal の NFC/NFD だけ違うディレクトリの試料を足す

元の周: #263（PR #273 の狭いパスの Verifier が見つけたテストの穴）。

## 変更範囲

触る:

- `scripts/test-build-proposal.py` — `i` ステップを `--index-info`（stdin）に替える・NFC/NFD だけ違うディレクトリの試料・`fold` を `lower()` に替える変異
- `docs/plans/issue-275.md` — この計画

触らない:

- `plugins/spec-loop/scripts/build-proposal.py` — 実装は正しい（Issue の陽性対照）。本体を変えないので版も上げない
- `plugins/spec-loop/scripts/merge-versions.py` の `fold` と `scripts/test-merge-versions.py` — そちらは既に NFC/NFD の試料と「正規化を畳まない」変異を持つ
- ファイル名（ディレクトリでない）が NFC/NFD だけ違う試料 — Issue の範囲の外。必要なら残課題に書く

**周の大きさ（同じことを述べている箇所）**: 試料の置き方（`build_repo` の `i`）1 箇所・試料 1 件・変異 1 件。
`copy_docs` の docstring は「Unicode の正規化」を既に述べている。**複製 1 箇所なので分けない理由は要らない。**

## 乗るデプロイ経路

**反映経路なし**——`scripts/` のテストだけで、`docs/` もプラグインの中身も変えない（計画ファイルは `docs/plans/` だが
mkdocs の nav に載らない——`mkdocs build` が通ることは `check-all.py` 外なので手順 7 で CI を見る）。

## verify の受入基準

不変条件と、それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | `copy_docs` の `fold` が NFC 正規化を外すと、テストが赤になる | `fold` を `lower()` / `casefold()` / 恒等に替える・ディレクトリの重なり検査（`if other != parent`）を外す | 新しい試料「ディレクトリが正規化だけ違うと比較で断る」と変異「正規化を畳まない」 |
| B | 試料が本当に NFD のエントリを索引に置いている（NFC に潰れていない） | macOS の `core.precomposeunicode` が `--cacheinfo` の引数を NFC に直す | `i` を `--index-info`（stdin）に替える。試料の判定に**NFD の綴りが出力に出ること**を入れる（潰れれば衝突が起きず `made` になり赤） |
| C | 既存の試料・変異が `i` の置き換えで変わらない（ASCII のパスでは同じ索引） | `--index-info` の書式の誤り（モード・種類・SHA・タブ） | `check-all.py` で全試料・全変異が従来どおり |
| D | 実環境を触らない | 試料の git が一時ディレクトリの外を触る | 既存の `assert_in_tmp`・`sandbox_env` をそのまま使う |

陽性対照（手順 5）: 変異「`fold = lambda p: p.lower()`」を**手で**当て、新しい試料が赤（exit 0・提案書あり）になり、
HEAD では exit 1 になること。**加えて `--cacheinfo` に戻した版で新しい試料が赤になる**ことを見て、B の判別力を示す
（macOS でしか判別しない——Linux では潰れないので `--cacheinfo` でも緑）。

**この環境では証明できないもの**: Linux（`precomposeunicode` が無い）での挙動は CI でしか見ない。CI は ubuntu で
`check-all.py` 相当を回すので、そこで緑であることを手順 6 で `gh pr checks` で見る（未証明ではなく、PR 側の確認）。

**生成物**: 該当なし（試料は実行時に一時ディレクトリへ作る。`diagrams/`・`skill-metrics.py` の生成ブロックは触らない）。

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に・1 パス目と 2 パス目の両方に渡す（4 つの受け渡し）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/275-nfd-dir-fixture`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-275`・
  起点 `50b1d1b`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `50b1d1be2ad0efd20726333e712a4b91dcfccc0a`
- 実装: `20c65bc`。`test-build-proposal.py` は緑（試料 35・変異 30）。`check-all.py` は 43/43 本（失敗 0 / 飛ばし 0）
- 関門: 1 パス目を起動（2026-10-20、再開したセッションから）——Verifier（`dev-loop:dev-loop-verifier`・sonnet）と
  `/code-review`（high）。
  - Verifier 1 パス目: **反証 0 件**。A〜D すべて一致。陽性対照 2 つを当てた（`.git` を除いた複製で——
    複製先が git リポジトリでないことは親が `git rev-parse` で確かめた）。`--cacheinfo` 戻しで赤は新試料 1 件だけ
  - `/code-review` 1 パス目（high）: **指摘 7 件**。陽性対照（`lower()`・`casefold()`・`if False`・`--cacheinfo` 戻し）を
    独立に当て、A・B は成り立つと報告。**7 件とも残課題**（下の採否の表）——**直した行 0 件**
- 2 パス目: **当てる差分なし**——1 パス目の指摘対応で直した行が 0 件なので、2 パス目が対象にする「指摘対応の差分」が無い。
  **黙って飛ばしたのではなく、この理由で回していない**（PR コメントで人間に申告する）
- 狭いパス: 該当なし（2 パス目で直した行 0 件）
- 反証・差し戻し: なし
- 交絡: 陽性対照を 1 つ取った——`i` を `--cacheinfo` に戻した複製（scratchpad。リポジトリは変えていない）で、
  新しい試料**だけ**が赤（exit=0・提案書あり）。macOS で B を判別している。Linux での判別力は無い（潰れないため）
- 割り目（手順 4）: 提案した（`AskUserQuestion`）。人間は**「ここで割る」**を選んだ（2026-10-20）。
  **再開したら手順 5 の 1 パス目から**——Verifier（`dev-loop:dev-loop-verifier`・別ティア）と `/code-review` の両方に、
  base `50b1d1be2ad0efd20726333e712a4b91dcfccc0a` と上の受入基準・下の決着済みの論点を渡す

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 本体（`build-proposal.py`）を直すか | 直さない | Issue の陽性対照で HEAD は正しく断る。穴はテストの側だけ |
| ファイル名同士の NFC/NFD 試料も足すか | 足さない（残課題） | Issue の範囲はディレクトリ。`fold` 全体を `lower()` にする変異はディレクトリの試料で殺せる——**ただしファイル側の 1 箇所だけ外す変異は素通りする**（R2。1 パス目の `/code-review` で理由を狭めた） |

### 1 パス目の指摘と採否（`/code-review`。Verifier は反証 0 件）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | `merge-versions.py` の `collisions` がディレクトリ同士（大文字小文字・NFC/NFD）を比べない | 示せる（レビューがハーネスで「警告なし」を報告。親は未再現） | 無し（変更範囲の外・`触らない:`） | 残課題（起票候補——手順 8 で人間に訊く） |
| R2 | ファイル側の照合だけ `fold` を外す変異（`seen.setdefault(path.lower(), …)`）が素通りする。**決着済みの論点の理由は、`fold` を 1 箇所で共有している間だけ成り立つ** | 示せる（レビューの報告。親は未再現） | 無し（A はディレクトリの穴。ファイル名の試料は決着済みで範囲外） | 残課題。決着の理由を狭めて書き直した |
| R3 | `--index-info` を `-z` なしで使い、`"` で始まるパスは git が C-unquote する | 示せない（いまの試料に該当パスが無い） | 無し | 残課題 |
| R4 | `NFC_E`/`NFD_E` が生の文字で書かれ、違うことを assert していない | 示せない（Verifier が `od` でいまは別の綴りと確認済み） | 無し | 残課題 |
| R5 | B は macOS でしか守られず、ubuntu CI では `--cacheinfo` に戻しても緑 | 示せる（計画が既に書いている限界） | 無し（既知の限界） | 残課題 |
| R6 | 新しい `subprocess.run` が `check=True` で git の stderr を捨てる | 示せない（いまは成功している） | 無し | 残課題 |
| R7 | 新試料の判定が `ディレクトリ ` の語を要求しない | 示せない（いまの出力はディレクトリの分岐が出している） | 無し | 残課題 |

- この周の起票: 0 件（R1 は手順 8 で人間に訊き、「起票しない」が選ばれた。2026-10-20）

## 経験の還元（手順 8）

- 焼き戻す学びなし——ガードの拒否（複合コマンド・`; echo exit=$?` を付けたスクリプト呼び出し）は `references/guard-rejections.md` の既知の形で、素の 1 行に割って通った
- PR #285 を作った。CI は緑（check・build）。マージは人間の承認待ち
