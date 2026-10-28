# Issue #286 — spec-loop: 想定外の例外がトレースバックで 1 になり、1（違反）と 2（検査していない）の区別が崩れる

spec-loop のスクリプトは、終了コード 1（違反・決まりに反する）と 2（判定していない・書いていない）を分けると約束している。
ところが想定外の例外（`csv.Error`・`RecursionError` など）はトレースバックになり、1 で終わる。
さらに、例外を捕まえてはいても原因を取り違えて報告する箇所がある。`build-proposal.py` の `OSError` →「git を起動できない」と、`merge-versions.py` の `Unreadable` →「UTF-8 として読めない」の 2 つ。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent`（2026-10-28 に利用者が同じ引数で起動し直した）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。**このリポジトリのマージはサイトを再デプロイするので `マージ` の線は効かない**（#476）——PR まで作って止まる。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/*.py` — 12 本の入口（想定外の例外を 2 に寄せる）・docstring の終了コードの表・`build-proposal.py` の `OSError` の切り分け・`merge-versions.py` の `Unreadable` の文言。共通の関数を置くなら同じディレクトリの新しいファイル
- `scripts/test-*.py` のうち spec-loop の 12 本に対応するもの — 試料と変異
- `plugins/spec-loop/references/*.md`・`plugins/spec-loop/skills/*/SKILL.md` — 終了コードの意味を述べている箇所があれば、想定外の例外も 2 だと揃える（無ければ触らない）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.26.1 → 0.30.0、main の取り込みで 0.32.0。終了コードの振る舞いが変わるので minor。PR #479・#481・#483・#485 の 0.26.2〜0.29.0 と重ならない値）
- `.claude-plugin/marketplace.json` — 同じ版
- `plugins/spec-loop/skills/*/SKILL.md` — 同じ版の 2 行
- `scripts/check-all.py`・`.github/workflows/plugins.yml` — 新しいテストファイルを足した場合だけ
- `docs/plans/issue-286.md` — この計画

触らない:

- `plugins/spec-loop/templates/mkdocs/` のフック（MkDocs から読まれるもので、終了コードを持たない）
- 想定内の誤りの終了コード（既存の 0/1/2/3 の割り当て）
- 他プラグイン（dev-loop など）のスクリプト

### 同じことを述べている箇所の数

「終了コード 2 の意味」は 12 本の docstring にそれぞれある（12 箇所）。加えて `references/`・`SKILL.md` に終了コードを述べる箇所があれば、それも数に入る。
分けない——同じ規則（想定外の例外は 2）を全部の入口に当てる周なので、一部だけ直すと「入口によって 1 と 2 が混ざる」状態が残る。数の多さは手戻りの危険なので、共通の関数に寄せて写しを減らすかを実装で決める。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。マージで main へ push されるとサイトが再デプロイされる（`docs/plans/` を足す）。

## 周の在り処

- ブランチ: `issue/286-unexpected-error-exit-2`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-286`
- 起点: `e361b20`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `e361b204f259c7e9bd5bd8cbb7cb041d3810e981`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1**: spec-loop の 12 本のスクリプトのどれを CLI から走らせても、想定外の例外（そのスクリプトがもともと捕まえていない例外。少なくとも `csv.Error`・`RecursionError` を含む）は**終了コード 2** で終わり、**1 では終わらない**。標準エラーには、例外の型と文言と「判定していない」の旨が出る。
- **I2**: 想定内の誤りの終了コードは変わらない（既存の回帰テストが緑のまま。0/1/2/3 の割り当ては docstring のとおり）。
- **I3**: `SystemExit` は寄せない——スクリプトが自分で返した終了コードはそのまま出る。`KeyboardInterrupt` も 2 に化けない（Python の既定どおり）。
- **I4**: `python3 -OO <スクリプト>` を引数なしで呼んでもトレースバックにならない（`__doc__` が `None` でも使い方の誤りとして 2）。
- **I5**: `build-proposal.py` は、git を起動できない・手書き部分が読めない・出力を書けないを**別の文言**で報告し、それぞれ `strerror` とパスを出す（「git を起動できない」に寄せない）。
- **I6**: `merge-versions.py` の読めないファイルの報告は、権限などの `OSError` を「UTF-8 として読めない」と言わない（`strerror` を出す）。UTF-8 でないときは今までどおり UTF-8 と言う。
- **I7**: 2 について docstring が約束していること（「書かない」「前の出力を消す」など）は、**想定外の例外による 2 でも守る**。守れない場合は、守らないことをその docstring が名指しする。黙って約束を破らない。
- **I8**: I1・I4〜I6 を回帰テストが押さえる——試料（128KB 超のセルの CSV・深い入れ子の JSON・読めない手書き部分・`-OO` の引数なし）と、捕捉を外す変異。変異を入れるとテストが赤になる。
- **I9**: 他のスクリプトから関数として読み込まれる経路（例: `qa-to-pptx.py` が `check-qa-csv.py` を読む・`scaffold.py` が `merge-versions.py` を読む）の振る舞いは変わらない。2 に寄せるのは CLI の入口だけで、読み込まれた関数は例外をそのまま呼び出し元へ返す。

これを破りうる経路:

| 経路 | 関係する不変条件 |
| --- | --- |
| 12 本それぞれの CLI 実行（`python3 <スクリプト> …`。cwd を問わない） | I1・I2・I3・I4・I7 |
| CSV を読むスクリプト（`check-qa-csv.py`・`check-feasibility-csv.py`・`qa-to-pptx.py`・`check-spec-exit.py`・`schedule-to-gantt.py`・`build-proposal.py`・`scaffold.py`・`check-signoff.py`・`diff-versions.py`・`merge-versions.py` のうち実際に CSV を読むもの）に巨大なセル | I1・I8 |
| JSON を読むスクリプト（`merge-versions.py`・`diff-versions.py`・`scaffold.py`）に深い入れ子 | I1・I8 |
| `build-proposal.py` の git の起動・手書き部分の読み・出力の書き込み | I5 |
| `merge-versions.py`（と同じ `Unreadable` を使う呼び出し元）の権限エラー | I6 |
| 出力を書くスクリプト（`merge-versions.py`・`schedule-to-gantt.py`・`build-proposal.py`・`qa-to-pptx.py`・`scaffold.py`・`init-mkdocs.py`）が書いている途中で想定外の例外 | I7 |
| 他のスクリプト・テストからの関数の読み込み（`importlib`） | I9 |
| スキル（`SKILL.md`）・`references/` が終了コードを読む説明 | I1（説明と挙動の一致） |

証明できないもの: なし（どれもテストで確かめられる）。

生成物: なし（`SKILL.md` の測定値の生成ブロックは dev-loop のもので、spec-loop の `SKILL.md` は版の 2 行と終了コードの説明しか触らない。`skill-metrics.py --check` は `check-all.py` が回す）。

## 未解決の判断

なし（共通の関数にするかは実装で決める。Issue のとおり）。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 実験: なし
- 実装: 実装役に委譲（`prompts/implementer.md`）——`c7f2df9`。親が確かめたこと: `check-all.py` 52/52 緑、128KB 超のセルの `qa.csv` で `check-qa-csv.py` が rc=2（「想定外の例外で止まった（Error: field larger than field limit (131072)）。判定していない」）
- 実装役の報告の留意点: 共通の関数は置かず各 `__main__` に同じ形で入れた（テストが `-I` で単体を写して走らせるため）。I3 の `KeyboardInterrupt` に専用の試料は無い。`check-frozen.py`・`init-mkdocs.py`・`scaffold.py`（引数の解析）は実入力で想定外の例外を作れず、差し替え（`subprocess.run`・`os.link`・`argparse` に ValueError）で当てた。`build-proposal.py` の一時ファイルの読み書きの `OSError` の文言には試料が無い
- 割り目（手順 4 の完了時）: 不在の周なので訊いていない（`absent-lines.md` の「訊く場面」）。再開は `/dev-loop:dev-loop 286` を `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-286` の中で
- 1 パス目の指摘対応の起点: `f63bd10`——1 パス目の 2 つの関門に渡した時点の HEAD
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 通した。反証 0 件（見てほしい点 3 件——下の表の V1〜V3）
- `/code-review` 1 パス目（high）: 通した。指摘 10 件（下の表の CR1〜CR10）。「直す」は CR2 の 1 件
- 手順 4 への差し戻し: 1 件（CR2）——`merge-versions.py` で `docs` を辿れない（3.12 の `resolve` がリンクの輪で `RuntimeError`）とき、前の出力を消して 2。試料「入力が自分を指すリンクでも前の出力を消す」と変異「辿れない入力で前の出力を消さない（3.12 でだけ死ぬ）」を足した（3.12 で 61 変異・3.14 で 60 変異＋当てていない 1 件）
- 割り目（2 パス目の前）: 不在の周なので訊いていない
- 1 パス目の指摘対応: `f63bd10`..`28fdff4`（CR2 の修正）
- Verifier 2 パス目（sonnet）: 通した。反証 0 件（気づいた点 1 件——下の表の V2-1。P2-1 と同じもの）
- `/code-review` 2 パス目（high）: 通した。指摘 6 件（下の表の P2-1〜P2-6）。「直す」は P2-1 の 1 件
- 2 パス目の指摘対応の起点: `28fdff4`（狭いパスの起点）
- 2 パス目の指摘対応: P2-1 を直した——`docs`・`out` を `os.path.realpath` で辿る（3.12 でもリンクの輪で投げない）ので、1 パス目の早期の分岐を外し、出力先の検査と「ディレクトリが無い」の後始末が版によらず同じ順で走る。試料「自分を指すリンクを含む場所は消さない」を足し、3.12 でだけ死ぬ変異を「辿るのに Path.resolve を使う」に付け替えた（3.12 で 66 試料・61 変異、3.14 で 66 試料・60 変異＋当てていない 1 件）。終点 `6abb359`
- 狭いパス（Verifier・sonnet・`28fdff4`..`6abb359`）: 通した。挙動の反証 0 件・テストの穴 1 件（NP-1。下の表）。Verifier の設計した 9 通りの配置は 3.12・3.14 で rc・文言・残ったファイルが一致
- 利用者の判断（2026-10-28、`/dev-loop:cruise 474` の再開時に訊いた）: NP-1・P2-4・P2-6 は**この PR で直す**。直した差分に Verifier を当て直してからマージ待ちに戻す
- 判断を受けた修正（テストだけ。本体は触らない）: `test-merge-versions.py` は全試料を 3.12 の `Path.resolve` を再現して走らせ、`only_312` を外した。変異は docs 側と出力先側の 2 つに分け、出力先側を殺す試料を足した（NP-1）。`test-build-proposal.py` は辿れない symlink の試料だけ 3.12 の `Path.is_file` を再現し、版で当てない変異の扱いを外した。3.12・3.14 の両方で `test-merge-versions.py` 67 試料・62 変異、`test-build-proposal.py` 84 試料・102 変異。陽性対照: 再現を外すと 3.14 では 3 つの変異が生き残る（3.12 では外しても死ぬ）。`check-all.py` 52/52
- 判断を受けた修正の Verifier（sonnet・`2e285ae`..`86cbe7b`）: 通した。主張 6 件すべて成り立つ・反証 0 件。再現は 3.12 の素の `Path.resolve` と 24 通りで一致。気づいた点: OS の ELOOP 上限を超える輪でない長いリンクの連鎖では 3.12 と再現が食い違いうる（45 段では観測されず、変異の判定には効かない）
- main の取り込み（#485・spec-loop 0.26.2 の後）: 衝突は版の行（marketplace.json・plugin.json・SKILL.md 5 本）と `build-proposal.py` の docstring の終了コード 2 の行。版は周の 0.30.0 を取った（main より上で、計画の「重ならない値」のまま）。docstring は main の「前後に空白がある」に周の #286 の追記を足した
- main の 2 度目の取り込み（#483・spec-loop 0.29.0 の後）: 衝突は版の行だけ（`scaffold.py`・`test-scaffold.py` は自動で合わさった）。版は coordinator の割り振りで 0.32.0（#479 が 0.30.0、#481 が 0.31.0）
- main の 3 度目の取り込み（#479・spec-loop 0.30.0 の後）: 衝突は版の行だけ（`check-signoff.py`・`test-check-signoff.py`・`test-build-proposal.py` は自動で合わさった）。版は 0.32.0 のまま

## 既知の限界・決着済みの論点

- **計画の記述の訂正（V1）**: 「`merge-versions.py` の `Unreadable` →『UTF-8 として読めない』」は誤りだった——`merge-versions.py` は基準時点から `strerror` と UTF-8 を分けていた。この周で I6 のために直したのは `check-signoff.py` の `read_removed_at`（`Unreadable` の文言を通す）。I6 の不変条件そのものは変えない
- **`proposal` 以外の 4 スキルの `SKILL.md`（V3）**: 下の採否の表を参照

### 狭いパスの採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| NP-1: `out_real` だけを `out.resolve()` に戻す変異は、どの試料でも赤にならない（試料は輪を `docs` 側にしか置かない）。P2-5 の「`out` の `resolve` の例外は出なくなった」はコードでは事実だが、テストが押さえていない | 示せる——Verifier が python3.12 で、出力先 `L/out`（`L` は自分を指すリンク）に当てた: 変異ありで「想定外の例外で止まった（RuntimeError: Symlink loop…）」、本物は「`L/out`: 書けない（Too many levels of symbolic links）。書きかけを消した」。どちらも rc=2 | 無し（挙動は正しく、どちらも 2。I8 が押さえを求めるのは I1・I4〜I6） | **直す**（利用者の判断。2026-10-28 の再開時）——試料「出力先が自分を指すリンクの下でも書けないとして止まる」と変異「出力先を辿るのに Path.resolve を使う」 |

### 2 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P2-1 / V2-1: 1 パス目の修正の早期の分岐が、出力先の検査より前に `remove_stale` を呼ぶので、3.12 では `docs` を含む印つきの場所を丸ごと消す | 示せる——親が python3.12 で走らせた（`28fdff4`）: `x/.merged-versions`・`x/keep.txt`・`x/docs`（自分を指すリンク）で `merge-versions.py x/docs x` が rc=2・`keep.txt` が消えた。3.14 は「`docs` を含む場所には書かない」で残った | I7（docstring の「`docs/` を含む場所…は消さない」） | **直す**（`os.path.realpath` に替えて早期の分岐を外した。修正後は 3.12 も 3.14 と同じ文言で `keep.txt` が残る） |
| P2-2: 早期の分岐ではなく、`docs_real` の計算を投げない形にすべき（高度） | 示せない（設計の指摘） | 無し | P2-1 の直し方として採った |
| P2-3: 新しい試料は `docs` と別の出力先しか見ず、消してはいけないものを消さないことを見ていない | 示せない（テストの網羅） | 無し | P2-1 の修正で試料「自分を指すリンクを含む場所は消さない」を足した |
| P2-4: 3.13 以降では試料「入力が自分を指すリンクでも前の出力を消す」は修正の有無によらず通る（修正を確かめるのは CI の 3.12 の変異だけ） | 示せない（指摘のとおりで、計画にも書いた限界） | 無し | **直す**（利用者の判断。同上）——試料を 3.12 の `Path.resolve` を再現して走らせ（`RESOLVE_312`）、変異をどの版でも殺す |
| P2-5: `out.resolve()` は捕まえておらず、出力先がリンクの輪の下だと「想定外の例外」と報告される | 示せない（著者は走らせていない） | 無し | P2-1 の修正で `out` も `os.path.realpath` に替えたので、`resolve` の例外は出なくなった（狭いパスで確かめる） |
| P2-6: `only_312` は変異の名前の部分一致で決め、`test-build-proposal.py` にも同じ判定が写してある | 示せない（保守の指摘） | 無し | **直す**（利用者の判断。同上）——`only_312` と `test-build-proposal.py` の写しを両方外した（`test-build-proposal.py` は 3.12 の `Path.is_file` を再現する） |

### 1 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2: `merge-versions.py` で `docs` が辿れない（自分を指すリンク）と、3.12 では 2 なのに前の出力が残る | 示せる——親が python3.12 で走らせた: 修正後（`c7f2df9`）rc=2・`old.md` が残る（「想定外の例外で止まった（RuntimeError: Symlink loop…）」）。docstring は「入力が無い・読めないときは…前の出力を消す」 | I7 | **直す**（`merge-versions.py` で `resolve` を分けて捕まえ、`remove_stale`。試料と変異を足した） |
| CR5: `schedule-to-gantt.py` で前の出力を消せないと、決まりの違反（1）が 2 になり、古い svg が残る | 示せる——親が python3.12 で走らせた: rc=2、「想定外の例外で止まった（PermissionError: … gantt.svg）」 | 無し——docstring の 2 は「前の出力そのものを消せないときは、消せなかった理由を出して 2」。修正前は同じ入力がトレースバックの 1 だった | 残課題（文言が「前の出力が残っている」と言わない） |
| CR1: `build-proposal.py` で手書き部分のディレクトリが読めないと、`glob` が空を返して「無い」（1）になる | 示せない（著者は CLI では走らせていない。関門は `glob` が空を返すことだけを確かめた） | 無し（I5 が見るのはファイルの読みの失敗。ディレクトリの列挙はこの周より前からの挙動） | 残課題 |
| CR3: CLI から git を起動できないとき、出る文言は `check-signoff.py` のもので、ファイル名が付かない（`run_git` の文言は CLI から届かない） | 示せない（著者は走らせていない） | 無し——文言は「git を起動できない（strerror）」で、起動できなかったものは名指しされている | 残課題 |
| CR4: `check-spec-exit.py` の `rglob` は読めないサブディレクトリを黙って飛ばし、条件 1 を満たすと言いうる | 示せない（著者は走らせていない。この周より前からの挙動） | 無し（I1 は想定外の例外の扱い） | 残課題 |
| CR6: `init-mkdocs.py` の想定外の例外では、写したファイルの一覧が出ない | 示せない（著者は走らせていない） | 無し——docstring の「書けないと同じ」は一時ファイルの後始末を指す | 残課題 |
| CR7: `build-proposal.py` の `main` の残りの `except OSError` のコメントは「一時ファイルだけ」と言うが、他の `OSError` も来る | 示せない（コメントの正確さ） | 無し | 残課題 |
| CR8: `check-signoff.py` の新しい文言でパスが 2 度出る | 示せない（著者は走らせていない） | 無し | 残課題 |
| CR9: `test-init-mkdocs.py` の `-OO` の試料は何も判別しない（`init-mkdocs.py` は `__doc__` を読まない） | 示せない | 無し（I4 は成り立つ。判別しない試料が 1 つあるだけ） | 残課題 |
| CR10: 同じ入口の形が 12 本に写してあり、テストが文言を錨にしている | 示せない（保守の指摘） | 無し | 残課題 |
| V2: `init-mkdocs.py` を引数なしで走らせると rc=0 で書く | 示せない（既存の設計どおり） | 無し | 残課題 |
| V3: `proposal` 以外の 4 スキルの `SKILL.md` に想定外の例外の 2 の追記が無い | 示せない——`grep -n "終了コード" plugins/spec-loop/skills/*/SKILL.md` は `proposal` の表と、`scaffold` の「docstring を正とする」の 2 行だけ（散文の「1 なら」「2 なら」までは数えていない） | 無し | 残課題（決着: 表を持つのは `proposal` だけで、そこは直した） |

## 起票

- この周の起票: 0 件（不在の周。手順 8 で訊かない）
