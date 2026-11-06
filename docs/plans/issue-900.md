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
- 交絡を潰した手順: `figures_of` に `.bpmn`・`.svg` の無い `.drawio`（陽性対照）・`.svg` のある `.drawio` を置いた試料で走らせ、`.drawio` は「載せていない」に出て `.bpmn` はどちらにも出ないことを見た。
  `render-diagrams.py --check` は `.bpmn` だけの `docs/` で「0 件」・0、`.svg` の無い `.drawio` を足すと名指しして 1（陽性対照）——`.bpmn` を見ないことを確かめた

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| BPMN の置き場所を drawio と同じ「図を使う文書と同じディレクトリ」にするか | 採らない——`requirements/flows/` にまとめる | Issue の例。業務単位ごとの図を 1 か所にまとめる。実案件も同じ場所 |
| 書き出しが入るまで、案件側で作った書き出し（`.svg`）を置いてよいか | 採らない——置かない（仕様書に載らない） | Issue の例「書き出しが入るまで BPMN の図は仕様書に載らない」。手で作った書き出しは鮮度を確かめられないまま仕様書に載る |
| `render-diagrams.py`・`build-proposal.py` を直すか | この周では直さない | 範囲の外（#901・#902） |
| `tree.md` の「仕様書」の表の「構成の図」の行に BPMN を書くか | 書かない——「仕様書」の本文の指しで「図」を指す | 表は `build-proposal.py` の今の振る舞いの記述で、#902 が変える。BPMN が載らないことは「図」に 1 か所だけ書く |

## 手順 8

- 焼き戻す学び: （周の終わりに書く）

- この周の起票: 0 件（確認の Issue・振り分けで直すの行の起票なし）
