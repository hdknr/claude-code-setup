# Issue #440 — build-proposal.py の remove_owned が unlink の失敗で traceback・1 になり、古い出力が残る

`remove_owned` が `unlink` の失敗を受けないので、出力先のディレクトリが書けないと traceback・終了コード 1（照合の不一致と同じ値）になる。
消せなかったものを名指しして **2** で止め、印は残す（次の実行が消せるように）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent`（2026-10-27、利用者が会話で「-absent でまわします」と指示）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。**このリポジトリは main への push でサイトをデプロイするので、`マージ` の線は効かない**
（`references/absent-lines.md` の `本番反映`）——PR まで作って止まる。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/build-proposal.py` — `remove_owned` が消せなかった名前を返す・`main` と `write_outputs` が 2 で止まり名指しする・docstring の終了コード 2
- `scripts/test-build-proposal.py` — 書けない出力先（mode 555）の試料と、捕捉を外す変異
- `plugins/spec-loop/references/tree.md` — 「前の出力の印」の決まりに、消せなければ 2 で止まることを 1 文
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.26.0 → 0.26.1）
- `.claude-plugin/marketplace.json` — 同じ版
- `plugins/spec-loop/skills/*/SKILL.md` — 同じ版の 2 行
- `docs/plans/issue-440.md` — この計画

触らない:

- proposal の `SKILL.md` 手順 3 の「0 以外で終わったら、提案書は無い」と `tree.md` の移行の節（#441 の範囲）
- `bad_out` の文言（#442 の範囲）
- 想定外の例外を 2 に寄せる全体の作り（#286 の範囲）

### 同じことを述べている箇所の数

「消せなかったら」: 本体の docstring（終了コード 2）・`tree.md` の生成物の置き場所の段落の 2 箇所。分けない——同じ決定の写し。

### 決めたこと

- **消せなかったら 2 で止まり、残ったファイルを名指しする**——書けない場所では、どのみち新しい出力は書けない。照合（1）と取り違えない。
- **消せなかったものがあれば印は消さない**——印を消すと、残った出力をこの道具のものと確かめる跡が無くなり、次の実行が「印に無い」で 2 になる。
- `write_outputs` の書きかけの片付けで消せなければ、`書けない` の 2 に「書きかけを消せなかった」と名指しを添える（2 つ目の例外を逃がさない）。
- これは開発者が決めてよい範囲（失敗したあとの状態・終了コード）で、利用者に見える結果は変わらない——仕様の穴として起票しない。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。マージで main へ push されるとサイトが再デプロイされる（`docs/plans/` を足す）。

## 周の在り処

- ブランチ: `issue/440-remove-owned-unlink`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-440`
- 起点: `9b562d0`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `9b562d0f72947fe5f0f140ec5a835ca564ecafa5`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1**: `build-proposal.py` は消せない古い出力を理由に traceback で終わらず、終了コード 1 にならない（2 で終わる）。
- **I2**: 消せなかった古い出力を名指しする（「提案書は作っていない」と併せて）——黙って残さない。
- **I3**: 消せなかったものがあれば、印 `.build-proposal` を残す（名指ししていた出力の跡を消さない）。
- **I4**: 消せる場所では今までどおり消す（陽性対照。既存の試料が緑）。
- **I5**: 書きかけの片付けで消せなくても、2 つ目の例外を逃がさず 2 で終わる。

経路（古い出力を消す入口。`remove_owned` の呼び出し 3 箇所）:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| `main` の `remove_owned(out.parent)`（引数が正しい・誤り両方の前） | 消せなければ 2・名指し | CLI に mode 555 のディレクトリと有効な印（I1・I2・I3） |
| `main` の `remove_owned(out)`（`--out` にディレクトリ） | 同じ | CLI に `--out <書けないディレクトリ>` |
| `write_outputs` の `except OSError` の中 | 消せなければ名指しを足して 2 | `write_outputs` を直接呼び、片付けの `unlink` を失敗させる（I5） |

各経路の守りを外す変異で赤になる（陽性対照: 書ける場所では既存の試料が緑）。python3.12 と 3.14 の両方で回す（`Path.is_file` の例外の差。メモリの記録）。

生成物: `skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけを測るので該当しない。図の書き出しも無い——**生成物なし**。

未証明: root で走らせると mode 555 でも消せるので、試料が判別しない（CI は root でない前提）——試料の中で「消せないこと」を先に確かめ、消せたら試料を飛ばしたと言う。

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 実験: 未
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未

## 起票

- この周の起票: 0 件（仕様の穴は無かった。周の途中の課題も無い）

## 既知の限界・決着済みの論点

- #441（文面）・#442（`bad_out` の文言）・#286（例外の全体）はこの周で触らない（別の周として台帳にある）。
