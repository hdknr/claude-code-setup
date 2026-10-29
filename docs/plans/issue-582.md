# Issue #582 — schedule-to-gantt.py: 出力先の名前が符号化できないと、書く途中の「想定外の例外」で 2 になる

`plugins/spec-loop/scripts/schedule-to-gantt.py` の `main` は、書くときの `OSError` だけを「書けない」と読む。
出力先の名前（または親のディレクトリの名前）に NUL・単独のサロゲートが入ると、`mkdir`／`write_bytes` が `ValueError`
（`UnicodeEncodeError` はその子）を出し、`except Exception` の「書く途中の想定外の例外で止まった（ValueError…）」の 2 になる。
この経路に試料も無い（#534 / PR #579 の `/code-review` 1 パス目 CR1。cruise の台帳に足した行）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-10-29）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる
（背景を書き、専門用語を避け、1 Issue 1 判断、具体的な帰結を書く）。
マージは親がする（この周は手順 6 の PR・CI の確認・手順 8 の件数の行まで）。台帳は書かない（親が書く）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/schedule-to-gantt.py` — 書く途中の `ValueError` を「書けない（出力先の名前が使えない: …）」と名指しして 2・docstring の終了コード 2 の行
- `scripts/test-schedule-to-gantt.py` — 表が正しく出力先が符号化できない試料 3 件（名前の NUL・名前の単独のサロゲート・親のディレクトリの名前の NUL）・分岐を外す変異 1 件・docstring
- `.claude-plugin/marketplace.json` — spec-loop の版
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（5 本）
- `docs/plans/issue-582.md` — この計画

触らない:

- `remove_stale` の `except ValueError`（#534 で試料を足した。符号化できない名前は「無い」と読む——変えない）
- #535（辿れない先の symlink）・#536（NAME_MAX の境界）——同じファイルを触る兄弟の周。後で回る
- 出力先の名前を表示するときの NUL のエスケープ（いまの `{out}` の表示はほかの経路と同じ。下の「既知の限界」）
- `references/tree.md`（終了コードは docstring を正とすると書いており、2 の意味は変わらない）

### 同じことを述べている箇所の数

「書く途中の ValueError は書けない」: 本体のコメント 1・本体の docstring の 2 の行 1・テストの docstring 1・テストの試料のコメント 1・変異のコメント 1 = 5 箇所。
分けない——本体とテストの docstring はそれぞれの単体で読める必要があり、コメントは隣の行の説明。

### 決めたこと

- **「書けない」として名指しする**（Issue の受入基準（案）の 1 つ目の前半）。「在りえない出力先」として別の扱いにはしない。理由:
  1. 終了コードはどちらでも 2 で、変わるのは言い方だけ。docstring は既に「2: … 書けない」を持つ。
  2. 「在りえない」は `remove_stale` の側の読み方（消すものが無い）で、**書く側から見れば書けなかったことに変わりはない**。
  3. CLI からは届かない（#534 で実測。同じプロセスから `main` を呼んだときだけ）ので、利用者に見える CLI の振る舞いは変わらない。
- **これは仕様の穴ではない**——Issue が 2 つの言い方を周に委ねており、終了コード（利用者に見える結果）はどちらでも 2。`要確認` は立てない。

## 乗るデプロイ経路

プラグイン（spec-loop）のスクリプトの変更。main へのマージで、カタログの新しい版（0.38.1）が配られ、サイト（`docs/plans/` を含む）が再ビルドされる。
マージの可否は親（cruise。台帳の確かめた線 `マージ = 関門を通ればマージ`、印「配布を見せて確かめた」）が決める。

## 周の在り処

- ブランチ: `issue/582-gantt-write-valueerror`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-582`（`prepare-worktree.sh` で作った。cruise の子なので `EnterWorktree` は使わず、`cd <worktree> && …` で作業した）
- 起点: `4abb280`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`、取り直した）→ `4abb280dda86eac24190df155e9196f6c0fbb730`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1**: 表が正しく、出力先の名前（または親のディレクトリの名前）が符号化できない（NUL・単独のサロゲート）とき、`main` は **2** で終わり、
  標準エラーに「`<out>: 書けない（出力先の名前が使えない: <例外の型>: …）`」と名指しする。「想定外の例外」と言わず、「前に作った出力を消せない」と言わず、traceback を出さない。
- **I2**: その経路の試料が `scripts/test-schedule-to-gantt.py` にあり、分岐を外す（`except ValueError` を別の例外に変える）変異で赤になる——
  **赤になった理由が分岐の不在である**こと（陽性対照: 変異の本体に同じ入力を当てると「書く途中の想定外の例外で止まった（ValueError…）」）。
- **I3**: 既存の試料と変異は全部緑のまま（`OK: 試料 13 件・変異 27 件`）。python3.12（CI）と 3.14（手元）の両方で。既存の経路（`OSError` の「書けない（…）」、
  書く途中の想定外の例外（`RuntimeError` の注入）、表の違反の経路で符号化できない出力先が 1 のまま）の振る舞いは変わらない。
- **I4**: プラグインの版が 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 5 本の 2 行）で揃って main（0.38.0）より上（0.38.1）。

経路（書く途中に `ValueError` が出る入口）:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| `out.parent.mkdir`（親のディレクトリの名前が符号化できない） | 同じ `try` の `except ValueError` | 試料「親に NUL」 |
| `out.write_bytes`（名前が符号化できない） | 同じ | 試料「NUL」「単独のサロゲート」 |
| 書けなかった後の `stop` → `remove_stale` | `remove_stale` の `except ValueError` が「無い」と読む（#534）→ 2 のまま、「消せない」と言わない | 上の試料で `LEFT` が出ない |
| CLI（`python3 schedule-to-gantt.py <csv> <out>`） | 届かない（argv に NUL・単独のサロゲートは渡らない。#534 で実測） | #534 の計画の I4（この周では測り直していない） |
| 同じプロセスから `main` を呼ぶ（`sys.argv` を差し替えた `runpy`） | 上の分岐 | 試料 3 件 |
| `build-proposal.py` の `_load` | `render` しか使わない——`main` に届かない | `grep` |
| 入口（`__main__` の `except Exception`） | `main` の中で捕まえるので届かない | 試料の stderr に「想定外の例外」が無い |

未証明: 無し。Windows（argv の扱いが違う）は測っていない——受入基準ではない。

生成物の該当判定: `skill-metrics.py`（dev-loop の `SKILL.md` を触らない。spec-loop の `SKILL.md` は版の 2 行だけ）・図の書き出し（drawio を触らない）——**生成物なし**。
`check-all.py` が両方の鮮度を見る。

### 交絡

- I1 の再現（修正前）: 修正前の本体（`4abb280`）に、同じプロセスで `main` を呼ぶ形で表の正しい試料と NUL・`\ud800` の出力先を当て、3.12・3.14 とも 2・「書く途中の想定外の例外で止まった（ValueError: embedded null byte）」「（UnicodeEncodeError: …）」を見た。
- 修正後は同じ入力で 2・「書けない（出力先の名前が使えない: ValueError: embedded null byte）」。変異の本体（`except ImportError`）では修正前と同じ出力に戻る（陽性対照）。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 手順 4: 済み。`OK: 試料 13 件・変異 27 件`（3.12・3.14）。
- 割り目（手順 4）: 不在のため訊かず続けた。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 「書けない」か「在りえない出力先」か | 「書けない」（終了コード 2） | 上の「決めたこと」。終了コードは同じで、書く側から見れば書けなかった |
| CLI から届く試料を作れるか | 作れない（#534 で実測） | argv に NUL・単独のサロゲートは渡らない。同じプロセスで `sys.argv` を差し替える |
| 名指しの行の `{out}` に NUL がそのまま出る | 直さない（範囲の外） | ほかの経路（「書けない（…）」「消せない」）も `{out}` をそのまま出す。CLI からは届かない |
| Windows の argv | 測っていない | 受入基準ではない |
| #535・#536 の範囲 | 触らない | 兄弟の周が後で回る |

## 手順 8

- この周の起票: 0 件（手順 8 の振り分けの前の値。起票の承認は不在のため訊いていない）
