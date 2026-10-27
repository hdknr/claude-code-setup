# Issue #375 — check-signoff が比べる範囲の外で、承認と合意の中身が食い違っても一致を返す（#367・#372 のまとめ）

`check-signoff.py` が比べる範囲を、**2 つの承認が見た中身**に揃える。見積りの根拠（`requirements/`・`spec/`）と、
v1 の `removed.csv`・`shared/` の外のファイルの行を範囲に入れ、2 つのタグの時点で違えば **1（一致しない）** にする。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent`（2026-10-27、利用者が会話で「-absent でまわします」と指示）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。**このリポジトリのマージはサイトを再デプロイするので `マージ` の線は効かない**（#476）——PR まで作って止まる。

入場の記録: `find-cycle.py 375` の 1 回目（worktree を作る前）が「当たったものがある」と出したのを確かめずに `prepare-worktree.sh` を走らせた。
作った後の 2 回目では、当たったのは作ったばかりのブランチ `issue/375-signoff-scope` だけで、計画ファイル・計画を足したコミット・`#375` を含むコミットメッセージは無かった
（`prepare-worktree.sh` は同じ番号の worktree・ブランチがあれば 3 で止まるが、0 で作った）。前の周は無いと判断して新規の周とした。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-signoff.py` — 比べる範囲（`compare_scope`）・`removed.csv` の比べる行（`removed_scope_rows`）・出力の範囲の言い方・docstring
- `scripts/test-check-signoff.py` — #367・#372 の試料、範囲の外の陽性対照、期待の文言、変異
- `scripts/test-build-proposal.py` — 「比較は要求のタグの時点から作る」の試料（2 つのタグの間に足すものを範囲の外へ移す）
- `plugins/spec-loop/references/signoff-tags.md` — 「2 つの承認が同じ範囲を見ていたか」の比べる場所
- `plugins/spec-loop/references/tree.md` — 置き方の決まりの「2 つのサインオフが同じ範囲を見ていたかは `shared/` の中身で確かめる」
- `plugins/spec-loop/README.md` — `check-signoff.py` の行
- `CLAUDE.md` — `check-signoff.py` の行
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json`・`plugins/spec-loop/skills/*/SKILL.md` — 版（0.26.0 → 0.27.0。0.x なので振る舞いの変更も minor）
- `docs/plans/issue-375.md` — この計画

触らない:

- 暫定の行の判定（`provisional_rows`）と、要求確定のタグの時点の配置の検査（#325・#338・#348）
- `build-proposal.py`（`resolve` の結果をそのまま使う）
- description（JSON 2 箇所と proposal の frontmatter）——「同じ共有の範囲（docs/v<n>/shared/ ほか）」は「ほか」で外れない

### 同じことを述べている箇所の数

「比べる範囲」: 本体の docstring（概要・守らないもの）・`signoff-tags.md`・`tree.md`・`README.md`・`CLAUDE.md` の 5 箇所。
分けない——同じ決定の写しで、片方だけ直すと範囲の説明が食い違う。

## 仕様の穴（不在の線で推奨により決めた）

Issue の「決めること」A・B・C。**線は `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線（台帳 `issue-474`））**。確認の Issue: **#478**（台帳の `decisions` に記録）。

- **A（#367）: `requirements/`・`spec/` の差分の扱い**
  - 選択肢: (a) 比べる範囲に入れ、違えば 1 ／ (b) 範囲は今のまま、違えば警告（0 のまま）／ (c) 別の終了コード
  - **決めた値: (a)**。`spec/qa-dev.csv`（内部の層の Q&A 表）は外す。
  - 理由: 見積りは `requirements/`・`spec/` から数える（feasibility の手順 2）ので、そこが違えば予算の合意は承認と別の中身を見ている。
    (b) は `build-proposal.py` が終了コードしか見ないので、警告が提案書の手前で消える。(c) は呼ぶ側を全部直すことになる。
    `qa-dev.csv` は feasibility が 2 つのタグの間に正当に書く（費用の行）うえ、#339 で「内部の層はサインオフを割らない」と決めている。
- **B（#372）: 予算側だけにある、`merge` が拒否する配置**
  - 選択肢: (a) 比べる範囲に `docs/v1/removed.csv` と、範囲の中のファイル・機能の行を入れる ／ (b) 予算側にも配置の検査を当てる（2）
  - **決めた値: (a)**。`removed.csv` で比べる行は「共有の層の Q&A」「範囲の中（`shared/`・`requirements/`・`spec/`。`spec/qa-dev.csv` を除く）のファイル」「機能」。
  - 理由: A と同じ「範囲」の定義で説明できる（C）。(b) は予算側の時点に `merge` の読み方を写すことになる（#348 で避けた形）。
- **C**: 範囲は「2 つの承認が見た中身」= v1〜v<n> の `shared/`・`requirements/`・`spec/`（`qa-dev.csv` を除く）と `removed.csv`（v1 を含む）。
  **外すのは `feasibility/`・`proposal/`（予算の合意と決裁の側が書くもの）と内部の層だけ。**

別の値を選んだら直す場所: `check-signoff.py` の `compare_scope`・`removed_scope_rows`、`signoff-tags.md` の比べる場所、試料の期待。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。マージで main へ push されるとサイトが再デプロイされる（`docs/plans/` を足す）。

## 周の在り処

- ブランチ: `issue/375-signoff-scope`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-375`
- 起点: `eab5e13`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `eab5e1387a3fa7587aed615754fcb7bc35cd75e0`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1（#367）**: 2 つのタグの時点で `requirements/`・`spec/`（`spec/qa-dev.csv` を除く）の中身が違えば、一致とは言わない（1。違うパスを出す）。前の版のものも同じ。
- **I2（#372）**: 予算側だけに `docs/v1/removed.csv` がある・`removed.csv` の範囲の中（`requirements/`・`spec/`）のファイルの行や機能の行が違うなら、一致とは言わない（1）。
- **I3（陽性対照）**: 範囲の外（`feasibility/`・`proposal/`・`spec/qa-dev.csv`・内部の層の Q&A の行・`removed.csv` の範囲の外のファイルの行・理由の列・行の順序・`.` で始まる名前）だけが違えば、今までどおり 0。
- **I4**: 今までの判定（2 の条件・3 の暫定・`shared/` の比較）は変わらない（既存の試料が緑）。
- **I5**: 範囲の説明（docstring・`signoff-tags.md`・`tree.md`・`README.md`・`CLAUDE.md`）が本体の範囲と一致する。

経路（2 つのタグの時点の中身が照合に入る入口）:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| `git diff` の比べる場所（`compare_scope`） | `requirements/`・`spec/`・`docs/v1/removed.csv` を足し、`spec/qa-dev.csv` を除く | 試料: `spec/` だけ違う・`requirements/` だけ違う・前の版の `spec/` だけ違う・v1 の `removed.csv` が予算側だけ（1）／`qa-dev.csv` だけ違う・`feasibility/` だけ違う（0） |
| `removed.csv` の行（`removed_scope_rows`） | 範囲の中のファイル・機能・共有の Q&A の行を比べる | 試料: `ファイル,spec/…`・`ファイル,requirements/…`・`機能,…` の行が予算側だけ（1）／`ファイル,feasibility/…`・`D-` の行だけ（0） |
| `build-proposal.py`（`resolve` を呼ぶ） | 本体を変えない | `test-build-proposal.py` が緑。2 つのタグの間に `requirements/` を足すと作らない |

各経路の守りを外す変異で赤になる（陽性対照つき）。

生成物: `skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけ・図の書き出しも無い——**生成物なし**。

未証明: なし（照合は git の出力だけで決まり、試料で全部当てられる）。

## 未解決の判断

上の「仕様の穴」を確認の Issue で利用者に渡す。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 実験: 未
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未

## 起票

- この周の起票: 1 件（仕様の穴の確認の Issue。起票の承認は不在のため訊いていない）

## 既知の限界・決着済みの論点

- 仕様の穴 A・B・C は上の「仕様の穴」で推奨により決めた（確認の Issue を起票）。**決めた値は受入基準を緩める理由にならない。**
- 暫定の行・要求確定のタグの時点の配置の検査は触らない（#325・#338・#348 で決着）。
- `test-build-proposal.py` の変異「比較を予算のタグの時点から作る」と試料「比較は要求のタグの時点から作る」を外した——
  この周で照合の範囲（`shared/`・`requirements/`・`spec/`）が重ね合わせの読むもの（`merge-versions.py` の `AREAS`）と同じになり、
  照合が通る組では 2 つの時点の比較が同じになる（等価変異）。試料を `feasibility/` や内部の Q&A 表に置き換えても、
  比較（提案書は内部の層を載せない）に出ないので殺せないことを確かめた（どちらの置き換えでも変異が生き残った）。
  代わりに「2 つのタグの間に要求を足すと照合で止まる」を足した。
