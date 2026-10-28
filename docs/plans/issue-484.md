# Issue #484 — cruise: 文脈で止まった親がタイマーで空回りし、/clear 後も最後の周の worktree に閉じ込められて再開できない

**不在の周である**——出所: `/dev-loop:cruise 474 --absent` の再開（2026-10-28）。この周は cruise の親から、worktree の絶対パスで作業する
サブエージェントとして委ねられた（この周が入れる B の形そのもの）。**この周では `EnterWorktree` を呼んでいない。**

使った線（出所: cruise の確かめた線（台帳 `issue-474`）。親の委譲文で受け取った）:

- `仕様の穴 = 推奨で決めて起票`
- 直す線: **既定**
- `周の途中の課題 = 台帳に足して直す`（台帳には親が足す。この周は起票して番号を報告する）

スキルの版: 読み込んだのはキャッシュの 1.61.0（`SKILL.md` 1838 行）。リポジトリの main も 1.61.0。

## 仕様の穴（不在の線で推奨により決めた）

#484 の「決めること」2 つ。確認の Issue: **#492**。

| 穴 | 選択肢 | 決めた値 | 理由 |
| --- | --- | --- | --- |
| B と C のどちらか | B（親は worktree に入らない）／C（周ごとに `ExitWorktree(keep)` で戻る） | **B**。C は前の版の親が残っていた再開の手当てとしてだけ使う | C は「戻れる」に寄りかかるが、戻れた例は 1 件しか観測していない。B は入らないのでその前提が要らない |
| A の閾値 | 数値を `SKILL.md` に書く／`.claude/dev-loop.md` で宣言／決めない | **決めない**。次の周を始めないと決めたら（理由に依らず）タイマーを止めて通知 | 閾値に根拠の実測が無い。害の本体は止めた後に何もしないこと |

D（再開時の点検で worktree の中を名指し）は #466 で既に入っている——cruise §1「再開でも下の 3 の起動時の点検を回す」と
`check-unattended-env.py --cruise` の「親の起動場所」。この周は、そう言われたときの手当て（`ExitWorktree` を 1 度試す）だけ足す。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/SKILL.md` — 冒頭（親は周の worktree にも入らない）、§1（再開で worktree の中なら `ExitWorktree(keep)` を 1 度試す）、§4 の 2（周をサブエージェントに委ね、委譲文に書くこと）、§5（次の周を始めないと決めたらタイマーを止めて通知）、版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 4 に「cruise の子は `EnterWorktree` を呼ばない」の 1 行、版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.61.0 → 1.62.0。手順の追加なので minor）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-cruise.md` — 「5. 再開する」に利用者向けの説明
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く）
- `docs/plans/issue-484.md` — この計画

触らない:

- `references/absent-lines.md`（並行する #489 の周が触る。線の決まりは変えない）
- `references/resume.md`（`ExitWorktree` の「測っていない」はそのまま。1 例で書き換えない）
- `check-unattended-env.py`・`ledger.py`・`parent-issue.py`（D は入っている。台帳の形も変えない）
- description（3 箇所。「親はメインの作業ツリーから worktree に入らずに起動する」は今も正しい）
- 閾値の数値

## 複製の数

「親は worktree に入らない／周の worktree で作業する」を述べている箇所: cruise `SKILL.md` の冒頭と §4 の 2、dev-loop `SKILL.md` 手順 4、公開ページ 1 箇所、
cruise の frontmatter（起動場所だけ）で計 5。「タイマーで再開する」: cruise §5・公開ページ §5 の 2。
**分けない理由**: 決まりの原本は cruise `SKILL.md` に置き、dev-loop 手順 4 と公開ページは要点と指し先だけにする。

## デプロイ経路

`docs/` を含むので main へのマージが GitHub Pages の再デプロイ。プラグインの版を上げるので配布も変わる。マージは親（cruise）の判断——この周はしない。

## 受入基準（不変条件 × 経路）

不変条件:

- **I1 親は周の worktree に入らない**——cruise の親が周を回す経路のどこにも、親が `EnterWorktree` を呼ぶ指示が残っていない
- **I2 子も `EnterWorktree` を呼ばない**——周を回す子への委譲文の規定に、`EnterWorktree` を呼ばず worktree の絶対パスで作業することが入っており、
  dev-loop 手順 4 の「`EnterWorktree` へ `path` を渡して入る」と食い違わない（例外として指している）
- **I3 次の周を始めないと決めたら、タイマーを止めて通知して止まる**——理由に依らない。止められなかったらそう書く。閾値は決めない
- **I4 再開で worktree の中なら、`ExitWorktree(keep)` を 1 度だけ試し、点検を回し直して外と出たときだけ戻れたとする**。戻れなければ周を始めず I3 で止まる
- **I5 測っていないことを断定しない**——`ExitWorktree` の効く条件・サブエージェントの `EnterWorktree` が親に効くかは「確かめていない」と書く。1 例を一般化しない
- **I6 既存の必須を緩めない**——委譲しても周の必須（worktree → PR・2 関門・2 パス・受入基準）は外れない。台帳を書くのは親だけ。子の報告で PR・CI を確かめない
- **I7 版とリンクの整合**——版 3 種類が 1.62.0 で揃う。スキルの中の指し先・散文の指し先が解決する。生成ブロックが新しい

経路（その不変条件を述べる／破りうる入口）:

| 入口 | I1 | I2 | I3 | I4 | I5 | I6 | I7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cruise `SKILL.md` 冒頭 | ○ | | | | ○ | | |
| cruise §1（新規・再開） | | | | ○ | ○ | | |
| cruise §3（起動時の点検） | ○ | | | ○ | | | |
| cruise §4 の 2・5（周を回す・操作待ち） | ○ | ○ | | | ○ | ○ | |
| cruise §5（割って続ける・タイマー） | | | ○ | | | | |
| cruise §6（終える） | | | ○ | | | | |
| dev-loop `SKILL.md` 手順 4（入場・`ExitWorktree` の後片付け・割り目） | | ○ | | | ○ | ○ | |
| dev-loop `references/ledger.md`・`resume.md`（再開） | ○ | | | ○ | ○ | | |
| `check-unattended-env.py --cruise` の「親の起動場所」 | | | | ○ | | | |
| 公開ページ `dev-loop-cruise.md` | ○ | | ○ | ○ | ○ | | |
| 版 3 種類・`check-all.py` | | | | | | | ○ |

検証で証明できるもの: I1〜I7 の記述の有無と事実の真偽（読解と `check-all.py`）。

この環境では証明できないもの（未証明）:

- **I3・I4 の振る舞い**——実際の cruise で、文脈で止まった親がタイマーを止めるか・`ExitWorktree` で戻れるかは、cruise を回さないと見えない
  （この周は 1 周の子であって親ではない）。人間のレビューに回す。
- **サブエージェントの `EnterWorktree` が親のセッションに効くか**——確かめていない（I5 で「確かめていない」と書くことが基準）。

生成物: **該当あり**——`docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を変えるので `skill-metrics.py --check`）。図は触らない。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目 = 4 つの受け渡し（2 パス目が該当なしなら 2）。

## 未解決・確認待ち

- #492（仕様の穴の確認）——利用者が戻って答えるまで開いたまま

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/484-cruise-parent-outside-worktree`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-484`、
  起点 `9950e48`、base `origin/main` → `9950e48576e9b93fd1be04981d9070ea91b74d2d`
- 割り目（手順 4 の完了時）: 不在のため訊かず続けた
- 1 パス目の起点: （関門に渡すときに書く）
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 交絡を潰した手順: 実験なし

## 既知の限界・決着済みの論点

- 閾値は決めない（#492）。台帳の `note` には止まった理由を書かない（起動し直せば台帳からふつうに続くため）
- `resume.md` の `ExitWorktree` の「測っていない」は書き換えない——観測は 1 例（`/clear` の前に `EnterWorktree` を呼んでいたセッション）
- D は #466 で入っている（`check-unattended-env.py --cruise`）
