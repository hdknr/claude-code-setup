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
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.26.1 → 0.30.0。終了コードの振る舞いが変わるので minor。PR #479・#481・#483・#485 の 0.26.2〜0.29.0 と重ならない値）
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
- 1 パス目の指摘対応の起点: 下のコミット（計画ファイルを足したコミット）——1 パス目の 2 つの関門に渡した時点の HEAD
- Verifier 1 パス目: 起動（2026-10-28）
- `/code-review` 1 パス目: 起動（2026-10-28）

## 既知の限界・決着済みの論点

（まだなし）

## 起票

- この周の起票: 0 件（不在の周。手順 8 で訊かない）
