# Issue #900 — 業務フロー（スイムレーン）は BPMN で描く線を tree.md と各スキルの文言に足す

不在の周（`/dev-loop:cruise 903 --absent` の起動・2026-11-06T08:55Z、利用者の確認（起動時・2026-11-06T08:55:51Z、配布を見せて確かめた））。cruise #903 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かず「このまま続ける」）。従う版は dev-loop 1.99.0（キャッシュ。SKILL.md 1861 行）。
#896 の期待 1・4 を分けた子 Issue（残りは #901・#902。#901 は この周に依存する）。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-903`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #903 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認・マージ前の判断: 台帳に線なし（止まる）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.68.0 → 0.69.0。図の決まりに BPMN の線を足す——手順の追加）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #900`・`Refs #896`（#896 は #902 の PR で閉じる）・`Refs #903`
- 並行する周: #897（dev-loop の版を上げる。`run-serial.py` を直す周）——その worktree・ブランチには触らない
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.99.0/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/900-bpmn-flow-line`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-900`
- 起点コミット: `6f51485`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `6f51485ac3f374e3263927b4773beb88b9265fdf`

## 変更範囲

触る:
- `plugins/spec-loop/references/tree.md` — 「図」にどちらで描くかの線・業務フロー（BPMN）の置き場所・書き出しが無いあいだの扱い。ツリーに `requirements/flows/`。「仕様書」の指し 1 文
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 図の文言・版の 2 行
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同上
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 同上
- `plugins/spec-loop/skills/proposal/SKILL.md` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（autopilot・scaffold）
- `plugins/spec-loop/README.md` — 「図を書き出す」の文言
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-900.md` — この計画

触らない:
- `plugins/spec-loop/scripts/render-diagrams.py`・`build-proposal.py` — 書き出し・仕様書への掲載は #901・#902（範囲の外）
- `plugins/spec-loop/README.md` の `render-diagrams.py` の行（28 行目）と「図を書き出す」の説明の 3 行——drawio の書き出しの説明で、今も正しい
- `tree.md` の「仕様書」の表の「構成の図」の行——`build-proposal.py` の今の振る舞い（#902 で変える）
- dev-loop のプラグイン・公開ページ（`docs/plugins/`。spec-loop の図の決まりを持たない——`git grep` で確かめた）

複製の数（同じことを述べている箇所）: 図の線は **6 箇所**（`tree.md` の「図」が原本、4 スキルの `SKILL.md` と `README.md` が要約して `tree.md` を指す）。
**分けない理由**: スキルの本文は起動したときに読む規範で、`tree.md` を読まずに図を描く周がある——だから各スキルに 1 行の要約を残し、
細部（置き場所・書き出しが無いあいだの扱い）は `tree.md` にだけ書いて指す。要約の 5 箇所は同じ文で揃える。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージでプラグインのカタログに入る（`.claude/dev-loop.md` の `マージの反映:`）。マージは親。

## 設計（この周で決めたこと）

Issue が範囲と例を与えているので、仕様の穴ではなく Issue に従った判断として決める:

- **どちらで描くかの線**: 業務フロー（業務の手順の流れを担当ごとのレーンに分けて描く図）は BPMN、それ以外（構成・関係・画面の遷移・状態の遷移など）は drawio。業務フローを drawio で描かない。
- **置き場所**: Issue の例のとおり版の中の `requirements/flows/<名前>.bpmn`（実案件 taihei-carrot-revamp も同じ場所）。drawio の「図を使う文書と同じディレクトリ」とは変える——業務単位ごとの図を 1 つにまとめ、どの文書からも同じ場所を指せる。
- **書き出しが入るまで（#901）**: Issue の例のとおり「BPMN の図は仕様書に載らない」。`.svg` を手で作って置かない（手で作った書き出しは鮮度を確かめられないまま仕様書に載るので）。
  `build-proposal.py` の今の振る舞い（`.bpmn` は図として扱わず「載せていない図」にも数えない。ファイルとしては要求のファイルに数え、一覧に出る）をそのまま書く——実験で確かめた（下の「交絡」）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | `tree.md` の「図」に、BPMN と drawio のどちらで描くかの線と、BPMN の置き場所がある | 線が無い・置き場所が無い・版の外を許す・drawio の決まり（置き場所・書き出し）が BPMN にも掛かると読める | 読む |
| A2 | `tree.md` が、BPMN の書き出しが無いあいだの扱いを書き、その記述が今のスクリプトの振る舞いと合う | `render-diagrams.py` が `.bpmn` を見る／見ないの食い違い・`build-proposal.py` が `.bpmn` を図として載せる／「載せていない」と書く／書かないの食い違い | 読む＋スクリプトを走らせて確かめる（`figures_of` と `render-diagrams.py --check` に `.bpmn` を置いた試料。陽性対照に `.svg` の無い `.drawio`） |
| A3 | 図の文言を持つ全ファイル（`req-loop`・`spec-review`・`feasibility`・`proposal` の `SKILL.md`、`README.md`）が同じ線を言い、`tree.md` と食い違わない | 1 つ直し忘れる・「drawio で描き」だけが残る・要約が `tree.md` と違う線を言う・指示語や表・注記で同じ概念を述べる箇所（名前で grep しても当たらない） | `git grep -n -E 'Mermaid でも|drawio で描'` の結果が 5 箇所とも新しい文で、旧い文が 0 件。`plugins/spec-loop` を `drawio`・`draw.io`・`図` で引いて、概念を述べる箇所を読む |
| A4 | spec-loop の版を上げ（3 種類の箇所で 0.69.0）、`check-all.py` が通る | 片方だけ上げる・SKILL.md の 2 行の片方 | `check-plugin-versions.py`・`check-all.py`（順番待ち越し）・PR 側の CI |
| A5 | スキルの中の指し先（`tree.md` の「図」・「業務フロー（BPMN）」・`上の「…」`）が実在する | 見出しの名前の誤記 | `check-skill-pointers.py`（`check-all.py` に含む） |
| A6 | 必須の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（4 つの受け渡し。2 パス目が「該当なし」なら 2 つ） | 片方の関門・片方のパスに渡し忘れる | 再開点に記録 |

- 経路の数え方: 図の決まりを述べる入口は「原本（`tree.md`）・各スキルの本文（起動時に読む）・README（人が読む）・生成スクリプトの docstring（`render-diagrams.py`・`build-proposal.py`）・公開ページ」。
  スクリプトの docstring は drawio の書き出しと仕様書の今の振る舞いを述べるだけで、この周の線と食い違わない（#901・#902 で変える）。公開ページには図の決まりが無い。
- 生成物: **該当判定**——`docs/plugins/dev-loop-design.md` の §8.2 の生成ブロックは dev-loop の `SKILL.md` の測定で、この周は dev-loop を触らないので動かない（`skill-metrics.py --check`）。
  `diagrams/` の drawio の書き出しは触らない（`check-diagram-freshness.py`）。ほかに生成物なし。
- 未証明: **なし**（文書の線と、スクリプトの今の振る舞いとの一致だけで、どちらもこの環境で確かめられる）。

## 未解決の判断・確認待ち

- なし（線・置き場所・書き出しが無いあいだの扱いは Issue が例で決めている——上の「設計」）

## 関門の進捗（再開点）

- 割り目（手順 4 の完了時）: 割らない（cruise の周）
- check-all.py（順番待ち越し）: 67 本中 66 緑・`check-plan-counts.py` だけ赤（件数の行が無かった）→ 行を足して単体で緑（`5f73c27`）。指摘対応の後にもう 1 度全部回す
- 1 パス目の指摘対応の起点: `63a8a50`（1 パス目の関門に渡した時点の HEAD）
- Verifier 1 パス目: 通した（sonnet・dev-loop:dev-loop-verifier）——反証 0 件・観察 2 件（手置きの `.svg` は載る＝決着済み、冒頭の文の「SVG に書き出す」）。報告は通知で届かず、体の transcript の SubagentHandback から読んだ
- /code-review 1 パス目: 通した（high）——指摘 9 件。採否は下の表
- 反証と差し戻し: Verifier 0 件。/code-review の指摘のうち直す 3 件（CR-1・CR-2・CR-4）を手順 4 に戻して直した
- 1 パス目の指摘対応: `4b6d866`（起点 `63a8a50` からの成果物の差分 1 ファイル +7 −4——0 行でない）。check-all.py（順番待ち越し）67/67 緑
- 割り目（2 パス目の前）: 割らない（cruise の周）。残っているもの: 手順 5 の当て直し（Verifier 2 パス目）と /code-review 2 パス目の両方
- 2 パス目: 通した——Verifier（sonnet・dev-loop:dev-loop-verifier）反証 0 件・観察 1 件（手置きの `.svg` は載る＝決着済み。報告は通知で届かず、体の transcript から読んだ）／/code-review（high）指摘 7 件。base は同じ `6f51485`
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `0ecf09da`
- 2 パス目の指摘対応の終点: `a2a0648e`（P2-7 の括弧を消した 1 行）
- 狭いパス: 通した（sonnet・dev-loop:dev-loop-verifier・`git diff 0ecf09da a2a0648e`）——反証 0 件。変異は当てていない（散文の括弧の削除で、検査の掛かる値が動かない——Verifier の判断）。陽性対照: 印の無い `.svg` と `.drawio` で rc=1、印つき `.svg` と `.bpmn` で rc=1。報告は通知で届かず、体の transcript から読んだ
- 狭いパスの指摘: 0 件（人間が決める行なし）
- check-all.py（順番待ち越し）: 終点 `a2a0648e` で 67/67 緑
- 交絡を潰した手順: `figures_of` に `.bpmn`・`.svg` の無い `.drawio`（陽性対照）・`.svg` のある `.drawio` を置いた試料で走らせ、`.drawio` は「載せていない」に出て `.bpmn` はどちらにも出ないことを見た。
  `render-diagrams.py --check` は `.bpmn` だけの `docs/` で「0 件」・0、`.svg` の無い `.drawio` を足すと名指しして 1（陽性対照）——`.bpmn` を見ないことを確かめた

  CR-1 の直しの主張（`render-diagrams.py --check` は印の無い `.svg` を見ない）も、`.bpmn` と手置きの `.svg` だけの `docs/` で 0・rc=0 を見た（陽性対照は上の `.svg` の無い `.drawio`）
## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| BPMN の置き場所を drawio と同じ「図を使う文書と同じディレクトリ」にするか | 採らない——`requirements/flows/` にまとめる | Issue の例。業務単位ごとの図を 1 か所にまとめる。実案件も同じ場所 |
| 書き出しが入るまで、案件側で作った書き出し（`.svg`）を置いてよいか | 採らない——置かない（仕様書に載らない） | Issue の例「書き出しが入るまで BPMN の図は仕様書に載らない」。手で作った書き出しは鮮度を確かめられないまま仕様書に載る |
| `render-diagrams.py`・`build-proposal.py` を直すか | この周では直さない | 範囲の外（#901・#902） |
| `tree.md` の「仕様書」の表の「構成の図」の行に BPMN を書くか | 書かない——「仕様書」の本文の指しで「図」を指す | 表は `build-proposal.py` の今の振る舞いの記述で、#902 が変える。BPMN が載らないことは「図」に 1 か所だけ書く |


### 1 パス目の採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR-1 | 「`.svg` を手で作って置かない」は、Camunda Modeler などの道具で書き出した `.svg` を禁じると読めない。置けば `--check` は 0 で仕様書に載る | 示せる（/code-review が `flows/受注.svg` を置いて実走） | A2（書き出しが無いあいだの扱い） | 直す（道具で書き出したものも置かない、と書く） |
| CR-2 | 「図」の冒頭の太字が BPMN も「SVG に書き出す」と言い、下の節（書き出しを置かない）と食い違う | 示せる（`tree.md:81` と `:118`） | A3（`tree.md` と食い違わない） | 直す（冒頭は drawio だけ書き出す、BPMN は下の節を指す） |
| CR-3 | 5 箇所の要約が置き場所と「`.svg` を置かない」を持たない | 示せない（要約は `tree.md` を指していて食い違わない） | 無し | 残課題 |
| CR-4 | 業務フローの定義が「担当ごとのレーンに分けて描く」なので、担当が 1 つの業務フローが drawio 側に落ちる | 示せる（`tree.md:83` の定義） | A1（どちらで描くかの線） | 直す（担当が 1 つでもレーン 1 本で BPMN） |
| CR-5 | `その後の「業務フロー（BPMN）」` と `「置き場所」から「仕様書に載るのは」` は `check-skill-pointers.py` が見ない | 示せる（変異が素通り） | 無し（指し先は実在する。検査の範囲の話） | 残課題 |
| CR-6 | 要求の文書から業務フローの図をどう指すかが BPMN の節に無い | 示せない（Issue の範囲に無い） | 無し | 残課題 |
| CR-7 | 計画の実験が `figures_of` だけで、要求のファイルに数え一覧に出すことを判別していない | 示せる（実験の形） | 無し（主張は正しい——/code-review がコードで確かめた。計画は関門の検査対象ではない） | 残課題 |
| CR-8 | feasibility の規模の表の「要求の業務フロー」が `requirements/flows/` を指さない | 示せない（`flows/` は `requirements/` の中なので数え漏れにならない） | 無し | 残課題 |
| CR-9 | 最初のコミットのメッセージに `Fixes #900` が無い（CLAUDE.md の Git ワークフロー） | 示せる | 無し | 残課題（指摘対応のコミットと PR の本文に `Fixes #900` を書く。成果物は変えない） |


### 2 パス目の採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| P2-1 | proposal の仕様書の確かめ（手順 3）と止まるときの報告（手順 4）が、載らない BPMN の業務フローを報告しない。仕様書は「（図はありません）」と出る | 示せる（/code-review の実走: `.bpmn` だけで「図 0」） | 無し（仕様書への掲載は #902。`tree.md` は載らないことを書いた） | 残課題 |
| P2-2 | 「業務フローを drawio で描かない」が、0.68.0 までに drawio で描いた業務フローの扱い（描き直すか）を書かない。移行の手順が `references/` に無い | 示せない（既存の drawio の業務フローは今のまま書き出され仕様書に載る——壊れるものは無い） | 無し | 残課題（描き直すかは #901 の書き出しが入ってから決める論点） |
| P2-3 | CR-4 の直しが `tree.md` の本文だけで、5 箇所の要約と冒頭の太字は「業務フロー（スイムレーン）」のまま——担当が 1 つの手順を要約だけ読んで drawio に回しうる | 示せない（要約は「どちらで描くかの線」を `tree.md` の「図」に指していて食い違わない。読み違えは推測） | 無し | 残課題 |
| P2-4 | 計画の CR-1 の実験の陽性対照（`.svg` の無い `.drawio`）は「印の無い」を判別しない（正しい対照は `.bpmn` と印のある `.svg`） | 示せる（実験の形）。主張は正しい——/code-review が印のある `.svg` で rc=1 を見た | 無し（計画は関門の検査対象ではない） | 残課題 |
| P2-5 | `render-diagrams.py` の `.svg` の拾い方が大文字小文字を区別し（121 行）、docstring の「区別しない」と食い違う——印のある `.SVG` も `--check` が見ず、仕様書に載る | 示せる（121 行と docstring 43 行） | 無し（この周の前からの不具合。`tree.md` の主張「印の無い `.svg` を見ない」は正しい。BPMN では `.svg` を置かない決まりで、`.SVG` に改名して置く形は実際の利用でまず起きない） | 残課題（#901 が `render-diagrams.py` を触る） |
| P2-6 | `上の「置き場所」` は BPMN の節自身の「置き場所」や「生成物の置き場所」でも満たされ、指し先の検査が判別しない | 示せる（変異が素通り） | 無し（指し先は今は正しい。検査の範囲の話——CR-5 と同じ型） | 残課題 |
| P2-7 | 「（上の『書き出しを手で作らない』と同じ理由）」が誤り——drawio の手で作った `.svg` は `--check` が「印が無い」と名指しする（rc=1）が、`.bpmn` の隣の `.svg` は名指しされない。理由は逆 | 示せる（試料: 手で作った `b.svg` と `b.drawio` で rc=1「印が無い」） | A2（記述が今のスクリプトの振る舞いと合う） | 直す（括弧を消す） |

### 周の途中の課題の振り分け（found-lines.md）

直す: 0 件（関門の指摘で直したのは周の中で直した CR-1・CR-2・CR-4・P2-7 だけで、起票・`要確認` の Issue・台帳に足す行は無い）。
記録だけ: CR-3・CR-5・CR-6・CR-7・CR-8・CR-9・P2-1・P2-2・P2-3・P2-4・P2-5・P2-6（受入基準を破らず、利用者に見える誤りでもこの周の後退でもない——P2-5 は前からの不具合で、実際の利用でまず起きない形）。
捨てる: 0 件。台帳に足す行: なし。仕様の穴: なし（線・置き場所・書き出しが無いあいだの扱いは Issue が例で決めている）。確認の Issue: なし。

## 手順 8

- 焼き戻す学び: なし（周の規範に足す学びは無い。関門の体の報告が通知で届かず transcript から読んだことは PR コメントに残す）

- この周の起票: 0 件（確認の Issue・振り分けで直すの行の起票なし）
