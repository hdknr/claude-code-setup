# Issue #926 — spec-loop の正本リポジトリのドキュメントの道具（図の書き出し・MkDocs の雛形）を公開ページに足す

不在の周（cruise の子）。出所: `/dev-loop:cruise 916 --absent` の起動（2026-11-10T09:14Z）。親 Issue #916・台帳 `issue-916`（台帳は親だけが書く）。
従う版は dev-loop 1.103.0（キャッシュ `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/dev-loop/SKILL.md`。1861 行を読んだ）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-916`。利用者の確認・起動時 2026-11-08T08:00:42Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す。マージ前の判断は線が無い（止まる——人の判断が要るものは「マージ前に人が判断」として報告する）。
  `.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`
- 直す線: **既定**（出所: 上の cruise の確かめた線）
- 版の上げ方: **上げない**——`plugins/` を触らない（`docs/` だけ。`check-version-bump.py` の対象外）
- PR は `Fixes #926`。手順 7 のマージは親がする（子は PR と PR 側の CI まで）
- 依存: #924（PR #943）・#925（PR #960）はマージ済み（main `b46a923`）。この周はその上から切った

## 周の在り処

- ブランチ: `issue/926-spec-loop-doc-tools`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-926`
- 起点コミット: `b46a923`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `b46a923429cc2793c20ca961552cb420359ac68d`

## 変更範囲

触る:
- `docs/plugins/spec-loop.md` — 節「正本リポジトリのドキュメントの道具」（図・MkDocs の雛形）を足し、`data` の節の表と冒頭の案内から辿れるようにする（Issue の 1〜3）
- `docs/plans/issue-926.md` — この計画

触らない:
- `plugins/spec-loop/` の中（`references/tree.md`・`README.md`・`render-diagrams.py`・`render-bpmn.mjs`・`init-mkdocs.py`・`templates/mkdocs/`）——決まりの原本で、ページは指すだけ
- `mkdocs.yml`——nav の題は変えない（ページは同じ。節を足すだけ）
- `docs/plugins/index.md`——spec-loop の節の要約は変えない

複製の数（同じことを述べている箇所）:
- 図の決まり（どちらで描くか・置き場所・形式・描かないもの・BPMN の書き出しに要るもの）: 原本 `references/tree.md` の「図」、写し `render-diagrams.py` の docstring（要るもの・終了コード）・`README.md` の「図を書き出す」・各スキルの `SKILL.md` の 1 行（4 本）、そして**この周が足す節**。要約が 1 つ増える。
  分けない理由: Issue の求めが公開ページから辿れること。節は要点（どちらで描くか・コマンド・要るものの名前・止まること・指紋の理由）と指し先だけを持ち、終了コードの表・守らないものの表は写さない
- MkDocs の雛形（いつ何を写すか）: 原本 `references/tree.md` の「ドキュメントのツール」、写し `init-mkdocs.py` の docstring・`README.md` の中身の表・`req-loop` の `SKILL.md`。節は写す条件と「在るファイルを変えない」・フックの役割だけを書き、写すファイルの一覧は写さない

## デプロイ経路

`docs/` の変更——main へのマージで GitHub Pages の再ビルドと公開（`docs.yml`）。プラグインのカタログには何も配布しない（`plugins/` を触らない）。マージは親がする。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **`spec-loop.md` に Issue の 1〜3 がある**——(1) 図: どちらで描くか（業務フローは BPMN・ほかは drawio・アスキーアートと Mermaid は描かない）・置き場所・`render-diagrams.py` の書き出しと `--check`・BPMN の書き出しに要るもの（`SPEC_LOOP_BPMN_DEPS`・`CHROME_PATH`、draw.io は `DRAWIO`）・無ければ何も書かずに名指しして止まること・バイトではなくソースの指紋で鮮度を見る理由。
   (2) MkDocs の雛形: `init-mkdocs.py` で写すこと・写す条件・フックが単独で動くこと・MkDocs 以外のツールは正本の `CLAUDE.md` に書くこと。(3) `data` の節の表から図と表示のサイトへ辿れる。
   経路: 新しい節とその小節・`data` の表の行・冒頭の案内。
2. **書いた事実が原本と食い違わない**——とくに BPMN の書き出しに要るもの（Node・bpmn-js と puppeteer-core を `npm install` した正本の外のディレクトリ・Chrome の探し方・draw.io の探し方・`--check` には要らない・足りなければ 1 件も書かない）が `render-diagrams.py` の docstring と、
   写す条件・在るファイルを変えないことが `init-mkdocs.py` の docstring と、置き場所が `tree.md` と、どのスキルが図と雛形に関わるかが各 `SKILL.md` と合う。
   照合先: `references/tree.md` の「図」「業務フロー（BPMN）」「ドキュメントのツール」「プロジェクトに任せること」「Q&A 表を移す」・`README.md` の「図を書き出す」・`render-diagrams.py`・`init-mkdocs.py`・`render-bpmn.mjs`・`templates/mkdocs/hooks/spec_loop_pages.py` の docstring・各スキルの `SKILL.md`。
3. **決まりを書き写さず、`references/tree.md`・`README.md`・`render-diagrams.py` と `init-mkdocs.py` の docstring を指している**（終了コードの表・守らないものの表・写すファイルの一覧はページに無い）。
   経路: 節の各段落の指し先のリンク。守り方: 指し先のファイルが main に実在する。
4. **既存の記述（同じページの他の節・`index.md` の spec-loop の節・`spec-loop-autopilot.md`）と食い違っていない。**
   経路: 新しい節と同じ話題の文。
5. **`python3 scripts/check-all.py` と `uv run mkdocs build --strict` が通る（ページ内・ページ間のアンカーが実在する）。**

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パス（1 パス目の指摘対応の差分が 0 行なら初回の 2 つ）に渡す。

### この環境では証明できないもの（未証明）

- 本物の draw.io・Node・Chrome で書き出しが通ること——原本の docstring 自身が「`render-bpmn.mjs` は回帰テストで走らない」「確かめたのは macOS で 1 枚を手で書き出したことだけ」としている。ページはそれを超える主張をしない（要るものの名前と、無ければ止まることだけを書く）。

### 生成物

- **生成物なし**——drawio の書き出し・`SKILL.md` の測定値（`skill-metrics.py`）・spec-loop の生成物のどれにも触らない。サイトの HTML はビルドで作るもので、リポジトリに置かない（`mkdocs build --strict` で作れることだけを見る）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 割り目（手順 4）: 割らない（cruise の周）
- 交絡: 実験なし（ドキュメントの周。ビルドと歯止めの実行だけ）
- 実装: 未

## 既知の限界・決着済みの論点

- ページは決まりを写さない（`spec-loop.md` の冒頭の注意書きと同じ方針）。終了コードの表・守らないものの表・写すファイルの一覧を足せという指摘は、受入基準 3 に反するので採らない。
- このページ自身の図（流れの節）は Mermaid で描いている——「Mermaid で描かない」は正本リポジトリの決まりで、このサイトの決まりではない。

## 手順 8（起票と件数）

- この周の起票: 0 件（未定。手順 8 の振り分けの後に書き直す）
