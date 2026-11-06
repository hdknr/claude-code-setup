# Issue #902 — 仕様書（build-proposal.py）が BPMN の書き出しも載せる（#896 の 3）

不在の周（`/dev-loop:cruise 903 --absent` の起動・2026-11-06T08:55Z、利用者の確認（起動時・2026-11-06T08:55:51Z、配布を見せて確かめた））。cruise #903 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かず「このまま続ける」）。従う版は dev-loop 1.99.0（キャッシュ。SKILL.md 1861 行）。
#896 の期待 3 を分けた子 Issue（#900 が線を足し、#901 が書き出しを入れた）。**この周の PR で #896 も閉じる**（`Fixes #902`・`Fixes #896`）。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-903`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #903 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認・マージ前の判断: 台帳に線なし（止まる）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.70.0 → 0.71.0。仕様書が BPMN の書き出しを名指しし、古い書き出しを名指しする——能力の追加）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #902`・`Fixes #896`・`Refs #903`。確認の Issue は `Refs`（閉じるキーワードで指さない）
- 並行する周: #898（dev-loop の版を上げる）——その worktree・ブランチには触らない
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.99.0/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/902-spec-bpmn-figures`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-902`
- 起点コミット: `669e0e0`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `669e0e062456683370760b081c607d32dcf1708e`

## 変更範囲

触る:
- `plugins/spec-loop/scripts/build-proposal.py` — `figures_of` が `.bpmn` も書き出しの無いソースとして名指しし、書き出しが今のソースと合わない図（印が無い・指紋が違う）を名指しする。印と指紋は `render-diagrams.py` の関数を読み込む（写さない）。docstring
- `scripts/test-build-proposal.py` — BPMN の試料（書き出しあり・なし・古い・印が無い）と変異
- `plugins/spec-loop/references/tree.md` — 「業務フロー（BPMN）」の「まだ名指しされない（#902 で入れる）」を外す・「仕様書」の表の「構成の図」の行と「書き出しの…」の 1 文・drawio の「仕様書に載るのは」の 1 文
- `plugins/spec-loop/skills/proposal/SKILL.md` — 仕様書を確かめる項と止まるときの報告に、古い書き出しを足す（#904 の残課題 P2-1 を拾う）・版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（autopilot・scaffold・feasibility・req-loop・spec-review）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-902.md` — この計画

触らない:
- `plugins/spec-loop/scripts/render-diagrams.py` — 読み込むだけ（`marked_digest`・`source_digest`）。振る舞いは #901 のまま
- 仕様書の節の題「構成の図」——業務フローも同じ節に載るが、題を変えると PPTX・手書きの指し先が変わる。Issue の範囲に無い
- `--pptx` の図——今のとおり載せない
- 0.68.0 までに drawio で描いた業務フローの移行（#904 の残課題 P2-2）
- `README.md`（spec-loop）・`CLAUDE.md`——図の載せ方を持たない（`README.md` は「構成の図」の 1 語だけで `tree.md` を指す）
- dev-loop のプラグイン・公開ページ（`docs/`。spec-loop の仕様書の図を持たない——`git grep -i bpmn docs/` は計画ファイルだけ）

複製の数（同じことを述べている箇所）: 仕様書の図の扱いは **5 箇所**——`build-proposal.py` の docstring（振る舞いの原本）、`tree.md` の「仕様書」の表と 1 文（決まりの原本）、
`tree.md` の「図」の drawio の「仕様書に載るのは」と「業務フロー（BPMN）」の「仕様書に載るのは」、`proposal/SKILL.md` の確かめる項と止まるときの報告。
**分けない理由**: スキルは起動したときに読むので確かめる項を残し、決まりは `tree.md`、細部は docstring にだけ書く（#900・#901 と同じ）。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージでプラグインのカタログに入る。マージは親。

## 設計（この周で決めたこと）

- **書き出しの無い `.bpmn` を `.drawio` と同じく「載せていない」と名指しする**——Issue の範囲のとおり。書き出しとして数えるのは、`render-diagrams.py` が書く `<名前>.svg` と、
  今の drawio と同じく `<名前>.bpmn.svg`（大文字小文字を区別しない）。
- **書き出しの鮮度が古い図を載せるか**（Issue が「この周で決める」とした）——**仕様の穴として扱い、推奨で決めて確認の Issue を立てる**（下の「仕様の穴」）。
- **鮮度は `render-diagrams.py` と同じ判定**——ソース `<名前>.drawio`・`<名前>.bpmn` の隣の `<名前>.svg`（大文字小文字を区別しない）の印が無い・印の指紋がソースのバイトの sha256 と違う。
  **判定の関数は `render-diagrams.py` から読み込む**（`marked_digest`・`source_digest`。式を 2 箇所に置かない）。材料は承認したタグの時点の重ねた全体（`whole.files`）で、作業ツリーではない。
  `<名前>.drawio.svg`・`<名前>.bpmn.svg` は `render-diagrams.py` の書き出しではないので鮮度を見ない（今のとおり載せる）。

## 仕様の穴（不在の線で推奨により決めた）

- **穴**: 書き出しがソースと合わない（`render-diagrams.py` の印が無い・指紋が違う）図を、仕様書に載せるか。決裁者が仕様書で見る図が今のソースと違いうる——利用者に見える結果が変わる
- **選択肢**:
  - A: 載せて、仕様書に「書き出しが今のソースと合わない図」として名指しする（**推奨**）
  - B: 載せない（「載せていない図」として名指しする）
  - C: 仕様書を作らない（1 で止まる）
  - D: 鮮度を見ずに載せる（今のまま）
- **決めた値**: A
- **推した理由**: 仕様書の材料は 2 つの承認のタグの時点の中身で、承認した人が見た図は書き出しのほう（MkDocs も書き出しを出す）——載せないと承認した図が仕様書から消える（B）。
  C は承認の取り直し（タグを打ち直す）まで提案書も作れず、図 1 枚の書き出し忘れには重い。D は鮮度を保証できないという #896 の問題が残る。A は承認した図を見せたまま、
  決裁者と作る人に「ソースと合わない」ことを見せ、`render-diagrams.py --check` で直すきっかけを残す
- **確認の Issue**: （PR を出した後に立てる）

## 受入基準（不変条件 × 経路）

不変条件:

- **I1** BPMN の書き出し（`requirements/`・`spec/` の `<名前>.svg`）が仕様書の図に載り（`spec-figure-NN.svg` に写る）、書き出しの無い `.bpmn` は「書き出し（`.svg`）が無いので載せていない図」に名指しされ、規模の表の数に入る
- **I2** 印 `.build-proposal` の扱い（消すのは印が名指しするものだけ。#405）が崩れない——載せる図が増えても減っても、既存の印の試料と変異が全部通る
- **I3** `scripts/test-build-proposal.py` に BPMN の試料（書き出しあり・なし）と変異テストがある
- **I4** spec-loop の版を上げ（3 種類）、`check-all.py` が通る
- **I5**（穴の決めた値）書き出しが今のソースと合わない図（印が無い・指紋が違う。drawio・BPMN とも）を載せたうえで仕様書に名指しし、合う図は名指ししない。終了コードは変えない
- **I6**（後退させない）drawio の図・`.drawio.svg`・`shared/` の図の扱い（載せる・載せない・名指し）が変わらない
- **I7** 文書（`tree.md`・`proposal/SKILL.md`・docstring）が新しい振る舞いと食い違わない（「まだ名指しされない」「#902 で入れる」が残らない）

経路（`build-proposal.py` の入口から数える）:

| 経路 | 守り方 | 不変条件 |
| --- | --- | --- |
| 仕様書を作る（v1・照合 0） | `compose_spec` → `figures_of` | I1・I5・I6 |
| 仕様書を作る（v2 以降。図とソースが別の版から重なる） | 重ねた全体（`whole.files`）で見る | I1・I5 |
| `--pptx` | 図は載せない（今のまま）。仕様書の Markdown の名指しは PPTX の本文にも出る | I6 |
| 前の出力の印・消す・上書きしない・残った出力の名指し | 触らない（図の数が変わるだけ） | I2 |
| 承認の後に作業ツリーで書き出した `.svg` | タグの時点の中身だけを見る（今のまま） | I1・I5 |
| `proposal` スキルの確かめる項・止まるときの報告 | 古い書き出しを足す | I7 |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目に渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

**証明できるもの**: I1〜I7 全部（回帰テスト・変異テスト・`check-all.py`）。
**この環境では証明できないもの（未証明）**: なし——本物の BPMN の書き出し（Chrome・bpmn-js）は要らない（`build-proposal.py` は書き出し済みの `.svg` を写すだけで描画系を起動しない）。

**生成物の該当判定**: 該当あり——`build-proposal.py` 自身が生成物（仕様書・`spec-figure-NN.svg`）を作る道具で、その中身がこの周の成果物。
このリポジトリの生成物（`diagrams/exports.json` の図・設計 §8.2 の生成ブロック）は触らない——`check-diagram-freshness.py`・`skill-metrics.py --check` が `check-all.py` の中で見る。

## 関門の進捗（再開点）

- 割り目（手順 4）: **割らない（cruise の周）**
- 実験: なし

## 既知の限界・決着済みの論点

- 仕様の穴（鮮度の古い図）は上の「仕様の穴」で推奨 A に決めた。決めた理由が誤っていると判断したなら新しい反証である
- 節の題「構成の図」は業務フローにも使う（変更範囲の「触らない」）
- `--pptx` には今のとおり図を載せない
