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
| A1 | (U1) settings が拒むべき操作を許していれば `check` は 1 で、その操作を要対処と名指す | `Bash(git tag:*)`（陽性対照）・広い allow（`Bash(git:*)`・`Bash(git push:*)` が `git push --tags` を、`Bash(python3:*)` が scaffold を覆う）・`defaultMode: bypassPermissions`・どの層に書いた allow でも | 写しの `collect_rules`・`rule_matches` で全層の規則を集め、allow に当たるか bypass なら要対処 |
| A2 | (U2) 拒むべき操作が deny に当たれば良い——allow・ask と一緒にあっても。ほかに要対処が無ければ 0 | deny を allow と同じ設定に書く（`Bash(git push:*)` を allow しつつ `Bash(git push --tags:*)` を deny）・deny を別の層に書く | deny を最初に見る |
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
- 1 パス目: Verifier——反証 1 件（docstring の scaffold の理由が事実と違う）。**最初の 2 体（背景）と 3 体目（前景）は報告を親に返せなかった**
  （`SubagentHandback` が届かない——欠票として再実行し、3 体目に `SendMessage` で報告をファイルに書かせて受け取った）。`/code-review`（high）——指摘 8 件（報告をファイルで受け取った。テスト・変異は走らせていない）。
  反証・指摘 9 件のうち直す 3 行（下の採否の表）。差し戻しあり（手順 4 へ）。
- 割り目（手順 6・2 パス目の前）: 割らない（cruise の周）
- 1 パス目の指摘対応: `55279d7`（直すの 3 行。成果物の差分は 0 行でない——2 パス目を回した）。その後の `check-all.py`（run-serial 越し）の結果は下の行
- 2 パス目: Verifier——反証 0 件（報告をファイルで受け取った。`test-autopilot-check.py` は別の周の検査の順番待ちで走らせられず、読解と本物の CLI で確かめた）。
  `/code-review`（high）——指摘 7 件。直すの 3 行（下の「2 パス目の採否の表」）。
- 2 パス目の指摘対応の起点: `35342d7c2d33f5cb49d470985cd8f8f26b39d7ca`（計画ファイルだけのコミット）・終点: `08ba971e7f25a6492c906d2cb62efd67838e4648`（直すの 3 行。記述だけ）
- 歯止め: `check-all.py`（run-serial 越し）——1 回目（`5619c2d`）は `check-plan-counts.py` だけ落ちた（件数の行が無い。足して直した）。
  2 回目（`55279d7`）は `test-autopilot-check.py` が出力なしで落ちた（222 秒。同じ時間帯に 2 パス目の Verifier が自分の待ちの検査と子を止めたと報告しており、それに巻き込まれたシグナルの疑い——原因は確かめていない）。
  単独で run-serial 越しに回し直して合格（両方の結果をここに残す）。3 回目（2 パス目の直しを入れた作業ツリー。コミット `08ba971` と同じ中身）は 81/81 合格。
- 狭いパス: Verifier（別ティア）——指摘 3 件（F1〜F3。どれも記述の精度で、後退を示すものは 0 件）。変異は当てていない（コードを変えていない直しで、当てる挙動の変更が無い——Verifier の判断）。採否は人間が決める（下の振り分け）
- PR: #1089。PR 側の CI の 1 回目（`762b9e0`）は `spec-loop` のジョブで `test-autopilot-check.py` の陽性対照（線を書き直した台帳は変わる）が落ちた——
  拒むべき操作の試料の前に `before` と同じ線へ書き戻していて、同じ秒のうちなら台帳がバイトで同じになる（一時のリポジトリで `autopilot-ledger.py` を使って再現した）。
  手元の 3 回の `check-all.py` では起きなかった（遅い機械で秒をまたいだ）。直し: `15f7215`（書き戻しの線の `上限` を違える。起点 `762b9e0`）。直しの後の `check-all.py`（run-serial 越し）81/81。
  直しには狭いパスと同じ形の Verifier（別ティア）を 1 回当てた——反証 0 件（`test-autopilot-check.py` を run-serial 越しに走らせて合格、変異 25 件が全部赤）。2 回目の CI（`15f7215`）は全部通った
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い——`external-reviews.py` が 3）

### 関門の記録（check-gates.py。#1043）

終点はその関門に渡した時点の HEAD（1 パス目はどちらも `ff04772`、2 パス目はどちらも `55279d7`）。

```dev-loop-gates
周の base: 52d73bc36861fd90c59a10ab65ab949d20e96ec5
関門: Verifier 1 ff04772dc762fd358a2368f537519222120385a6 反証=1
関門: /code-review 1 ff04772dc762fd358a2368f537519222120385a6 指摘=8
関門: Verifier 2 55279d7770cf1f26151dc043f8bab81595954a9b 反証=0
関門: /code-review 2 55279d7770cf1f26151dc043f8bab81595954a9b 指摘=7
関門: 狭いパス 35342d7c2d33f5cb49d470985cd8f8f26b39d7ca 08ba971e7f25a6492c906d2cb62efd67838e4648 反証=3
関門: 当て直し 762b9e078cd4bd878484da7dbf379544fca748b9 15f7215ae31c01aaf8fc36aeb9697ef01c666310 反証=0
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
受入基準: A5 満たす
受入基準: A6 満たす
受入基準: A7 満たす
受入基準: A8 満たす
受入基準: A9 満たす
受入基準: A10 満たす
受入基準: A11 満たす
受入基準: X1 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 照合が近似（`git push origin --tags`・`--follow-tags`・相対パスや `cd` して呼ぶ scaffold は、`Bash(<操作>:*)` の deny に当たらない） | 採らない（守らないに書く） | 周で使う操作と同じ照合の近似で、写しの `rule_matches` を変えない。入口は散文でもしない |
| 各起動で点検しない | 採らない | Issue の対象は起動時の確認。各起動は台帳の線だけを読む今の形のまま |
| ask を要対処にしない | 採った（人が見る） | Issue の「deny か、少なくとも allow に無い」 |

### 1 パス目の採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | docstring の「scaffold は…照合する」の理由（名前で照合すると `Bash(python3:*)` の allow を見落とす）が事実と違う | 示せる——`rule_matches("Bash(python3:*)", "python3 scaffold.py <引数>")` は True | A10 | 直す（理由を「入口が打つ形に当たらない deny を良いと言い、打つ形の deny を見落とす」に） |
| CR1 | scaffold のスキルの本文は `<base>/../../scripts/scaffold.py`（`..` を畳まない）で打つので、畳んだ絶対パスの deny は当たらない。A6 の「入口が呼ぶ形」は事実と違う | 示せる——`rule_matches("Bash(python3 scaffold.py:*)", "python3 /x/scaffold.py <引数>")` は False、畳まない形と畳んだ形の前方一致は当たらない | A10（記述）。A6 の不変条件（点検するスクリプトと同じ形）は満たしている | 直す（記述だけ: 守るの行を「入口のスキルがスクリプトを畳んだ形で打つ」に、守らないに畳まない形を足す）。照合の形は変えない（既知の限界の 1 行目と同じ近似） |
| CR2 | スキルの手順 2 が「出力の『人が見る』」を止まりうる操作と言い、`拒む:` の人が見るの行に「許可を足す」を勧めうる | 示せる——本物の CLI の出力に `[人が見る] 拒む: \`gh issue create\`` が出る | A9・A10 | 直す（手順 2 を `止まりうる操作` の項目に限り、`拒む:` の行は手順 1 の deny の案で扱うと書く） |
| CR3 | スキルの手順 1 の要対処の説明（deny・ask に当たる・allow に無い）が `拒む:` の行と逆 | 示せる——本物の CLI で `[要対処] 拒む: \`git tag\`: allow に当たる` | A10 | 直す（区分を行の種類で分けて書く） |
| CR4 | deny の案が層を名指さず、`Bash(git tag:*)` は `git tag --list` も拒む。利用者の層に足すと他のリポジトリのタグ打ちも止まる | 示せる（2 パス目の CR2-1 で訂正）——`rule_matches` が `git tag --list` に当たり、spec-loop の `references/tree.md` の Q&A 表の移行の手順がそれを打つ。Claude Code が実際に拒むかは測っていない | 無し | 残課題（受入基準を破らない。found-lines の振り分けで扱う） |
| CR5 | `allowManagedPermissionRulesOnly` のとき、案のとおり user・project に deny を足しても良いにならない（managed に足すと言わない） | 示せない（その設定の環境は手元に無い。点検の判定そのものは Claude Code の規則の効き方と同じ向き） | 無し | 残課題 |
| CR6 | ask を常に人が見るにする——`bypassPermissions`・`claude -p` で ask が確認を出すかは確かめていない | 示せない | 無し | 残課題 |
| CR7 | `check_refused` が `check_permissions` と同じ集計と bypass の式を写しの外に手で複製している | 示せない（いま食い違ってはいない） | 無し | 残課題 |
| CR8 | テストの観測 `o["全部 allow"]` の中身を deny 入りに変えたのに名前がそのまま | 示せない（観測の辞書は全体で比べるので、allow だけの `許可:` の行も `拒む: 全部 allow・deny なし` の観測に入っている） | 無し | 残課題 |

### 2 パス目の採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR2-1 | CR4 の決着理由「示せない」は誤り（`git tag --list` を打つ手順が spec-loop の中にある） | 示せる（上の CR4 の行を訂正した） | 無し | 残課題（CR4 の採否は変えない） |
| CR2-2 | docstring の守るの行「入口のスキルがスクリプトをそう打つと決めている形」は scaffold に当たらない——autopilot のスキルの「畳む」決まりは `ops` の行と spec-review・feasibility のスクリプトだけで、scaffold を打つ指示は scaffold のスキルの畳まない形だけ | 示せる——autopilot `SKILL.md` の 27〜29 行、scaffold `SKILL.md` の 125・159・160 行、`rule_matches` が畳まない形に False | A10 | 直す（記述: 守るの行を「`ops` の行と同じ畳んだ形」に直し、scaffold のスキルの形に当たらないことを守らないに書く。照合の形は変えない） |
| CR2-3 | スキルの守らないもの「版に依らない規則にする」は scaffold の deny では点検と両立しない（途中に `*` を置く規則に `rule_matches` は False） | 示せる——`rule_matches("Bash(python3 *scaffold.py:*)", …)` は False | A9・A10 | 直す（scaffold の deny は更新のたびに足し直すと書き、版に依らない形を勧めない） |
| CR2-4 | `disableBypassPermissionsMode` の分岐を通る試料が無い・守るの行に例外が書かれていない | 示せない（判定は正しい向き。試料の穴） | 無し | 残課題 |
| CR2-5 | 「allow に当たれば要対処」「逆に」は、ask と読めない層が allow より先に効くことを書いていない（allow と ask の両方で人が見る） | 示せる——テストの「拒む: ask」（allow もある）で人が見る | A10 | 直す（守るの行・スキルの手順 1・公開ページ・`CLAUDE.md` を「deny・ask に当たらず allow に当たる」に） |
| CR2-6 | `git push --tags` の deny は名前を指したタグの push（`git push origin signoff/v1/req-1`）を覆わない | 示せない（照合の近似の範囲。既知の限界の 1 行目と同じ型） | 無し | 残課題 |
| CR2-7 | `defaultMode: dontAsk` のとき allow に無い拒むべき操作は自動で拒まれるのに「人が見る——通しうる」と出る | 示せない（人が見るは良いと言わない側で、誤った緑ではない。dontAsk の振る舞いは測っていない） | 無し | 残課題 |

### 狭いパスの指摘（採否は人間が決める。振り分けは下）

| # | 指摘 | 後退を示すか |
| --- | --- | --- |
| F1 | 直した記述（守るの 2 行・スキルの手順 1 と箇条・公開ページ・`CLAUDE.md`）は「deny・ask に当たらずに allow に当たれば要対処」と書き、読めない層があれば判定できないになる分岐を省く（docstring の表と読めない層の守るの行は正しい） | 示さない（起点の記述も同じ省略） |
| F2 | スキルの守らないもの「scaffold の deny は版に依らない形にできない」は言い過ぎ——確かめたのは点検が途中の `*` を照合しないことまでで、Claude Code が途中の `*` の deny を効かせるかは測っていない | 示さない（起点は点検が良いにならない形を勧めていた） |
| F3 | 「権限の点検」の箇条「ask に当たるか、どれにも当たらなければ人が見る」は、bypass で要対処・読めない層で判定できないの分岐を省く（直前の文に bypass がある） | 示さない |

## 振り分け（found-lines。手順 8）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け | 理由 |
| --- | --- | --- | --- | --- |
| deny の案が層を名指さず、`Bash(git tag:*)` は `git tag --list` も拒む | #1046 /code-review 1 パス目（CR4）・2 パス目（CR2-1） | 示せる（`rule_matches` が `git tag --list` に当たる。spec-loop の `references/tree.md` の移行の手順がそれを打つ） | 直す（利用者に見える誤り——案に従って利用者の層に足すと他のリポジトリのタグ打ちも、正本に足すと移行の手順も止まりうる）。仕様の穴か: 穴（Issue は deny を足す層を決めていない。選択肢: (1) 案に正本の `.claude/settings.local.json` を名指し、`git tag --list` も拒むと添える（推奨——利用者の層に入れる誤りを防ぎ、移行の手順の止まり方も先に言える） (2) 層は利用者に任せ、守らないに書くだけ） | 起票の候補（`周の途中の課題 = 外に出す`。不在のため起票は訊いていない） |
| `allowManagedPermissionRulesOnly` のとき案のとおりに足しても良いにならない | #1046 /code-review 1 パス目（CR5） | 示せない | 記録だけ | まれな環境 |
| ask が `bypassPermissions`・`claude -p` で確認を出すか | #1046 /code-review 1 パス目（CR6） | 示せない | 記録だけ | 測っていない |
| `check_refused` の集計と bypass の式の複製 | #1046 /code-review 1 パス目（CR7） | 示せない | 記録だけ | いま食い違っていない |
| テストの観測の名前 | #1046 /code-review 1 パス目（CR8） | 示せない | 記録だけ | 文言 |
| `disableBypassPermissionsMode` の分岐の試料が無い | #1046 /code-review 2 パス目（CR2-4） | 示せない | 記録だけ | 試料の穴 |
| 名前を指したタグの push を覆わない | #1046 /code-review 2 パス目（CR2-6） | 示せる（`rule_matches`） | 記録だけ | 照合の近似の範囲。タグを作る `git tag` を拒めば押す元が無い |
| `dontAsk` で人が見ると出る | #1046 /code-review 2 パス目（CR2-7） | 示せない | 記録だけ | 良いと言わない側 |
| F1 読めない層の分岐の省略 | #1046 狭いパス | 示せる（読解） | 記録だけ | 文言。後退を示さない |
| F2 版に依らない deny の言い過ぎ | #1046 狭いパス | 示せない（Claude Code の効き方は測っていない） | 記録だけ | 文言。後退を示さない |
| F3 箇条の分岐の省略 | #1046 狭いパス | 示せる（読解） | 記録だけ | 文言。後退を示さない |

## 手順 8

- この周の起票: 0 件（直すの 1 行は PR コメントの起票の候補に残した。起票の承認は不在のため訊いていない）
- 焼き戻す学び: `dev-loop:dev-loop-verifier` と `/code-review` の体の最終の応答が、この環境（cruise の子のサブエージェントから起こした体）では親に届かなかった（`SubagentHandback` が無い）——報告を scratchpad のファイルに書かせて受け取った。リポジトリへの焼き戻しは、この周の範囲の外（PR コメントに書く）
