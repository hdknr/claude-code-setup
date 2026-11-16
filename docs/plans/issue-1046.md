# Issue #1046 — spec-loop autopilot: タグ・Issue 登録を散文でなく権限で止める

**不在の周である**——cruise（親 Issue #1075）の子として回す。出所: `/dev-loop:cruise 1075 --absent` の起動（2026-11-16）。
確かめた線（台帳 `issue-1075`）: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた） /
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。
#1046 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/autopilot-check.py` — `check` に拒むべき操作（`git tag`・`git push --tags`・`gh issue create`・`python3 <spec-loop の根>/scripts/scaffold.py`）の点検を足す。docstring（点検する操作・守る・守らない）
- `scripts/test-autopilot-check.py` — 拒むべき操作の試料・陽性対照・変異（「守る」の行数と 1 対 1）
- `plugins/spec-loop/skills/autopilot/SKILL.md` — 「権限の点検」に拒むべき操作と deny の案を示すことを足す。「守ること」「守らないもの」の該当行。版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.90.0 → 0.91.0）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/spec-loop-autopilot.md` — 起動時の確認の節に拒むべき操作の 1 文（指し先は docstring）
- `plugins/spec-loop/README.md` — 中身の表の `autopilot-check.py` の行の説明
- `CLAUDE.md` — `autopilot-check.py` の項の説明
- `docs/plans/issue-1046.md` — この計画

触らない:

- dev-loop の `check-unattended-env.py` と、その写しの関数（`check_permissions` ほか）——写しは突き合わせで縛られている。拒むべき操作の判定は写しの外の新しい関数に置く
- 各起動（`running` の 1 単位）での点検——Issue の対象は起動時の点検と確認。各起動は今までどおり `lines` だけを検査する
- settings を書き換えること——deny を足すのは利用者（Issue の提案 2）
- 拒むべき操作の一覧を線の値にすること（値に置くと選ばれうる——docstring の「線」の方針のまま）
- `build-proposal.py` など Issue が挙げていない操作を拒むべき操作に足すこと
- frontmatter の description・`plugin.json`／`marketplace.json` の description（要約の内容は変わらない）

複製の数: 拒むべき操作の一覧の原本は `autopilot-check.py`（定数と docstring の「点検する操作」）。スキルの「権限の点検」・公開ページ・README・`CLAUDE.md` は
一覧を名前で挙げるか指すだけ。スキルには起動時の確認の手順として 4 つの名前を書く（利用者に示す場面なので）——一覧の正は docstring と書いて指す。
分けない理由: 判定は 1 箇所（スクリプト）で、指す側は「何を見るか」を 1 文で言うだけ。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`docs/plugins/spec-loop-autopilot.md` を変える）。

## 版の上げ方

spec-loop を minor で上げる（0.90.0 → 0.91.0。能力の追加）——`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md`（7 本）の 2 行。
マージの直前に main が進んでいたら、main の先端の spec-loop の版から minor で 1 つ上げた値にする（cruise の `references/parallel.md` の「版とマージの順」。#1044 の周も spec-loop を触っている）。

## 決めたこと

- **「警告して止める」は、`check` が 1（要対処）で終わり、起動時の確認で deny の案を利用者に示すこと**——Issue の受入基準は点検の終了コード、
  対象は `autopilot-check.py` と起動時の確認。起動時の確認は今までどおり単位を進めない。要対処が残ったまま利用者が続けると選んだときの扱いは、
  スキルの今の決まり（「終了コードで先へ進むかを決めない」）のまま——拒むべき操作は入口が散文でもしないので、許可が残っても入口の振る舞いは変わらない。
- **判定**（settings の `Bash` の規則で、周で使う操作と同じ近似の照合）:
  deny に当たる → 良い ／ deny に当たらず読めない層がある → 判定できない ／ ask に当たる → 人が見る（確認に答えれば通る） ／
  allow に当たる・`defaultMode` が `bypassPermissions` → 要対処 ／ どれでもない → 人が見る（分類器・起動の引数が通しうる）。
  要対処と人が見るの行には、deny に足す規則（`Bash(<操作>:*)`）を出す。
- **ask を要対処にしない**——Issue は「deny か、少なくとも allow に無い」を通るとしている。ask は自動では通らないので「許可されていない」側に入れ、人が見る項目で deny の案を出す。

## 受入基準（不変条件 × 経路）

Issue の受入基準 2 つ（U1: `git tag` が allow の settings で点検が非 0／U2: deny の settings では点検が通る）と提案 2（deny の案を示す）を展開する。
入口は `autopilot-check.py check` の 1 つ（`lines`・`ops` は拒むべき操作に触れない）と、その結果を読むスキルの起動時の確認。
破りうる経路は、規則がどこから来るか（settings の層: user・project・local・flag・managed・managed.d、`allowManagedPermissionRulesOnly`）と、どの形の規則が当たるか。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 (U1) | settings が拒むべき操作を許していれば `check` は 1 で、その操作を要対処と名指す | `Bash(git tag:*)`（陽性対照）・広い allow（`Bash(git:*)`・`Bash(git push:*)` が `git push --tags` を、`Bash(python3:*)` が scaffold を覆う）・`defaultMode: bypassPermissions`・どの層に書いた allow でも | 写しの `collect_rules`・`rule_matches` で全層の規則を集め、allow に当たるか bypass なら要対処 |
| A2 (U2) | 拒むべき操作が deny に当たれば良い——allow・ask と一緒にあっても。ほかに要対処が無ければ 0 | deny を allow と同じ設定に書く（`Bash(git push:*)` を allow しつつ `Bash(git push --tags:*)` を deny）・deny を別の層に書く | deny を最初に見る |
| A3 | deny に当たらない拒むべき操作を「良い」と言わない | allow に無い・ask に当たる | 人が見る項目にし、deny の案を出す |
| A4 | 読めない層があり deny に当たらなければ、判定できない（良いとも要対処とも言わない） | local が壊れている | deny の次に読めない層を見る |
| A5 | 拒むべき操作は線に依らず点検する | `commit = しない`（git も PR も使わない線） | `cmd_check` で線を見ずに足す |
| A6 | scaffold は、点検するスクリプトと同じ絶対パスの形（`python3 <spec-loop の根>/scripts/scaffold.py`）で照合する | 入口が呼ぶ形と食い違う名前で照合する | `HERE / "scaffold.py"` |
| A7 | 周で使う操作・TLC・止まりうる操作の判定は変わらない | 拒むべき操作の deny（`Bash(git push --tags:*)`）が周で使う `git push` に当たる・写しの関数を変える | 写しを変えない（突き合わせのテスト）。deny の案は操作の全体を名指す |
| A8 | 点検は読むだけで、台帳も settings も書かない | `check` の全経路 | 書き込みのコードを足さない。テストが台帳と settings の前後を比べる |
| A9 | 起動時の確認で、要対処・人が見るの拒むべき操作について deny の案を利用者に示し、settings は利用者が書く | スキルの「権限の点検」 | スキル本文に書く。出力の → の行が案 |
| A10 | 書いた記述が事実と合う（docstring・スキル・公開ページ・README・`CLAUDE.md` が実装の判定と一致） | 4 つの判定の区分・一覧の 4 つ | 関門に事実の真偽を当てさせる |
| A11 | 歯止めが全部緑（版 3 種類が 0.91.0・指し先・件数・description の JSON 2 箇所の一致） | `check-all.py` | 順番待ち越しに回す |
| X1 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目に渡す（2 パス目が該当なしなら初回の 2 つ） | — | 再開点で記録 |

**証明できないもの（未証明）**: 実際の Claude Code が、この照合で「deny に当たる」とした規則でそのコマンドを拒むか（照合は近似。自動モード・`bypassPermissions` で deny が効くか）。
受入基準は点検の判定（U1・U2）で、実際の拒否は受入基準ではない——docstring の「守らない」に書き、PR コメントで名指す。

**生成物**: 該当なし——`SKILL.md` の測定値（設計 §8.2 の生成ブロック）は dev-loop の `SKILL.md` だけを測るので spec-loop の変更では動かない（`skill-metrics.py --check` で確かめる）。図の書き出しも無し。

**依存の追加・更新**: なし。**仕様の振る舞い**: このリポジトリに spec-loop の正本は無い（`check-spec-writeback.py` で確かめる）。

## 実機確認

テストのほかに、一時の git リポジトリに台帳と settings を置き、`autopilot-check.py check` を本物の CLI として走らせて、
`git tag` の allow で 1・deny で 0 になること（U1・U2）と、要対処の行の → に deny の案が出ることを目で見る。

## 直す線

既定（出所: cruise の台帳の確かめた線 `直す線 = 既定`）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1046-autopilot-refuse-ops`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1046`・
  起点 `52d73bc`・base（`git merge-base origin/main HEAD`。参照 `origin/main`）`52d73bc36861fd90c59a10ab65ab949d20e96ec5`
- 割り目（手順 4）: 割らない（cruise の周）
- 実機確認: 一時の git リポジトリ（HOME も一時）で本物の CLI を走らせた——`Bash(git tag:*)` の allow で 1（`git tag`・広い allow が覆う `git push --tags`・scaffold が要対処、→ に deny の案）、
  同じ settings に 4 つの deny を足すと 0（4 つとも良い、周で使う `git push` は良いのまま）。
- 交絡: 実験は「deny の有無だけを変えた 2 つの settings」で、1 と 0 が分かれた（陽性対照が 1 側）——0 は点検が走らなかったことによる 0 ではない（`拒む:` の行が 4 つ良いで出ている）。
  テストの最初の 1 回（`test-autopilot-check.py` 単体）は順番待ち（run-serial）を通さずに走らせた（周の手順の誤り。時間で待ち合わせるテストではない）。
- 1 パス目の指摘対応の起点: `5619c2d`（1 パス目の関門に渡した時点の HEAD。計画ファイルだけのコミットはこの後に積む）
- 1 パス目: Verifier（起動済み・報告待ち）／`/code-review`（未）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 照合が近似（`git push origin --tags`・`--follow-tags`・相対パスや `cd` して呼ぶ scaffold は、`Bash(<操作>:*)` の deny に当たらない） | 採らない（守らないに書く） | 周で使う操作と同じ照合の近似で、写しの `rule_matches` を変えない。入口は散文でもしない |
| 各起動で点検しない | 採らない | Issue の対象は起動時の確認。各起動は台帳の線だけを読む今の形のまま |
| ask を要対処にしない | 採った（人が見る） | Issue の「deny か、少なくとも allow に無い」 |
