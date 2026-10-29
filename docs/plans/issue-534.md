# Issue #534 — schedule-to-gantt.py の `except ValueError` の分岐に試料が無い

`plugins/spec-loop/scripts/schedule-to-gantt.py` の `remove_stale` は、前の出力を消すときの `except ValueError` で
**符号化できない名前**（NUL・単独のサロゲート）を「無い」と読んで `None` を返す。**この分岐を外す変異が `scripts/test-schedule-to-gantt.py` で素通りする**
（#499 / PR #521 の `/code-review` 2 パス目 P2-3）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-10-29）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる。
マージは親がする（この周は手順 6 の PR・CI の確認・手順 8 の件数の行まで）。

## 変更範囲

触る:

- `scripts/test-schedule-to-gantt.py` — 符号化できない出力先（NUL・単独のサロゲート）の試料を、同じプロセスの中で `sys.argv` を差し替えて `main` に届かせる・分岐を外す変異・docstring
- `docs/plans/issue-534.md` — この計画

触らない:

- `plugins/spec-loop/scripts/schedule-to-gantt.py`——分岐は残す（下の「決めたこと」）。本体を変えないので**プラグインの版は上げない**
  （`check-version-bump.py` はプラグインの中身の変更にだけ版を求める）
- #535・#536（同じファイルを触る兄弟の周。後で回る）の範囲
- `merge-versions.py` の `remove_stale`（別の道具）

### 同じことを述べている箇所の数

「符号化できない名前は無いと読む」: 本体のコメント 1 箇所と、テストの docstring（足す 1 箇所）。分けない——テストは本体の振る舞いを試料で写すもの。

### 決めたこと

- **分岐は外さず、届く試料を足す。** 理由:
  1. **CLI からは届かない**ことを実測で確かめた（下の「交絡」）。だが `remove_stale`・`main` は**同じプロセスから呼べる**
     （`build-proposal.py` がこのモジュールを `_load` している——いま使うのは `render` だけ）。
  2. 分岐を外すと、符号化できない名前は `except Exception` に落ちて「前に作った出力を消せない」と名指しされ、**1 の経路が 2 になる**。
     **在りえない名前を「無い」と読む**のは、NAME_MAX を超える名前（`absent` の `ENAMETOOLONG`。CR3）と同じ決まりで、外すとそこから外れる。
  3. Issue の受入基準（案）の 2 項目（分岐に届く試料・分岐を外す変異で赤）を両方そのまま満たせる。
- **これは仕様の穴ではない**——Issue が「届く試料を足すか、届かない分岐なら外すか」を周に委ねており、利用者に見える結果（CLI の振る舞い）はどちらでも変わらない。`要確認` は立てない。

## 乗るデプロイ経路

テストだけの変更。マージで main へ push され、サイトの再デプロイ（`docs/plans/` もサイトに載る）が動く。プラグインの中身は変わらない。

## 周の在り処

- ブランチ: `issue/534-gantt-valueerror-sample`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-534`（`prepare-worktree.sh` で作った。cruise の子なので `EnterWorktree` は使わず、`cd <worktree> && …` で作業した）
- 起点: `8e0f9c6`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`、取り直した）→ `8e0f9c61b236cd66606b1002342991838699f97a`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1**: `remove_stale` の `except ValueError` の分岐に、テストの試料が届く——符号化できない出力先（NUL・単独のサロゲート）で、`main` が表の違反の **1** で終わり、「前に作った出力を消せない」と言わず、traceback を出さない。
- **I2**: その分岐を外す（`except ValueError` を別の例外に変える）変異で、`scripts/test-schedule-to-gantt.py` が赤になる——**赤になった理由が分岐の不在である**こと（陽性対照: 変異の出力が「消せない」と名指しして 2）。
- **I3**: 既存の試料と変異は全部緑のまま（`OK: 試料 N 件・変異 M 件` の M が 1 増える）。python3.12（CI）と 3.14（手元）の両方で。
- **I4**: 「CLI からは届かない」の主張が事実である——argv に NUL・単独のサロゲートは渡らず、符号化できないバイトは surrogateescape で符号化できる名前になる。

経路（`remove_stale` に符号化できない名前が届く入口）:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| CLI（`python3 schedule-to-gantt.py <csv> <out>`） | 届かない（OS とインタプリタが argv で拒否する・surrogateescape） | 3.12・3.14 で NUL・`\ud800` を argv に渡そうとして例外、`\xff` のバイトは `\udcff` になり lstat が FileNotFoundError |
| 同じプロセスで `main` を呼ぶ（`sys.argv` を差し替えた `runpy`） | 分岐で「無い」→ 元の終了コード | 試料（NUL・`\ud800`）で 1・「消せない」無し |
| 同じプロセスで `remove_stale`／`stop` を直接呼ぶ | 同じ関数 | 上の試料が `stop` を通る（表の違反の経路） |
| `build-proposal.py` の `_load` | `render` しか使わない——届かない | `grep gantt\. build-proposal.py` |

未証明: 無し。Windows（argv の扱いが違う）は測っていない——受入基準ではない。

生成物の該当判定: `skill-metrics.py`（`SKILL.md` を触らない）・図の書き出し（drawio を触らない）——**生成物なし**。

### 交絡

- **I4 の「届かない」は否定的な結果**なので、陽性対照として**同じ名前を同じプロセスで `lstat` すると ValueError（`UnicodeEncodeError` は ValueError の子）が出る**ことを 3.12・3.14 で見た。
  argv の側は、例外が `subprocess` で起きて子が起動していない（「子が走って何も起きなかった」ではない）。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 手順 4: 済み。試料 2 件（NUL・単独のサロゲート）を `entry_problems` に、変異 1 件を `ENTRY_MUTATIONS` に足した（`OK: 試料 13 件・変異 26 件`、3.12・3.14）。
  陽性対照: 変異を入れた本体に同じ試料を当てると「前に作った出力を消せない: …（ValueError: …）」と名指しして 2（変異前は 1）。
- 割り目（手順 4）: 不在のため訊かず続けた。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 分岐を外すか、試料を足すか | 試料を足す（分岐は残す） | 上の「決めたこと」。外すと在りえない名前が 2 になり、NAME_MAX の決まりと食い違う |
| CLI から届く試料を作れるか | 作れない | argv に NUL・単独のサロゲートは渡らない（3.12・3.14 で実測）。だから同じプロセスで `sys.argv` を差し替える |
| Windows の argv | 測っていない | 受入基準ではない |

- この周の起票: 0 件（起票の承認は不在のため訊いていない）
