# Issue #950 — spec-loop: システム基盤要件の自律提案と、未定義のときのアラートが無い

不在の周（cruise の子）。出所: `/dev-loop:cruise 963 --absent` の起動（2026-11-11T01:02Z）。親 Issue #963、台帳 `issue-963`（台帳は親だけが書く）。
従う版は dev-loop 1.103.0（キャッシュ。`SKILL.md` 1861 行——`wc -l`）。依存先 #957（PR #966）はマージ済みで、その上に積む（main から切った——積んだ周ではない）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-963`）——利用者の確認（起動時・2026-11-11T01:02:52Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-963`））
- 版の上げ方: **spec-loop を minor で上げる**（0.78.0 → 0.79.0。0.x なので能力の追加は minor）。`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行。
  マージの直前に main が進んでいれば、main の先端の spec-loop の版から minor で 1 つ上げた値に上げ直す（cruise の `parallel.md` の「版とマージの順」。並行の #972 も spec-loop と `tree.md` を触る）
- PR は `Fixes #950`。確認の Issue は閉じるキーワードで指さない（指すなら `Refs`）。手順 7 のマージは親がする（子は PR と PR 側の CI まで）
- 後に #951 → #952 が続く——その範囲（scaffold の Issue から図をたどる「参考資料」の節・UI モックの形式）に踏み込まない
- 重い検査は `run-serial.py` 越し（`/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/cruise/scripts/run-serial.py`）

## 周の在り処

- ブランチ: `issue/950-infra-requirements`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-950`
- 起点コミット: `29d3324e`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `29d3324e90211311174b3da99023947c4f9de805`

## 変更範囲

触る:
- `plugins/spec-loop/scripts/check-infra-csv.py` — 新規。基盤要件の表の検査とゲートの判定（形式の違反・未決定（表が無いを含む）・暫定を分けて出す）
- `plugins/spec-loop/scripts/scaffold.py` — 関門に基盤要件のゲート（違反・未決定・暫定で止める。表が無ければ警告して進む）と、言語が Python 以外なら止める。決まった基盤要件を出力に名指しする
- `plugins/spec-loop/scripts/build-proposal.py` — 承認したタグの時点の全体に基盤要件のゲート（違反・未決定は 1、暫定は 3。表が無ければ警告して進む）
- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — `infra` の印（各版の `shared/infra.csv` を見出しどおりの表に）
- `plugins/spec-loop/templates/mkdocs/docs/infra.md` — 新規。表示用ページ
- `plugins/spec-loop/references/tree.md` — ツリーに `shared/infra.csv`・構成の図・表示用ページを足し、「基盤要件」の節（形式・列・状態と Q&A の対応・必須の項目・誰が提案するか・ゲート・検査・表示）と、ドキュメントのツールの節の 1 行
- `plugins/spec-loop/references/spec-scope.md` — 「費用だけが変わる選択は共有に起票しない」に基盤要件の例外を 1 文
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 「はじめに」の基盤の前提・手順 1（ゲートを当てる）・手順 5（基盤要件の自律提案）と版
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 回答を基盤要件の表に反映する 1 項・手順 4 の検査と版
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 基盤要件で止まったときの扱いと、決まった基盤要件の受け渡しと版
- `plugins/spec-loop/skills/proposal/SKILL.md` — 基盤要件で止まったときの扱いと版
- `plugins/spec-loop/skills/spec-review/SKILL.md`・`autopilot/SKILL.md` — 版の 2 行（spec-review は基盤要件を仕様で決めない 1 項も）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-check-infra-csv.py` — 新規。検査の回帰テスト（変異テストを含む）
- `scripts/test-scaffold.py` — 基盤要件のゲート・言語・表が無いときの警告の試料と変異
- `scripts/test-build-proposal.py` — 基盤要件のゲートの試料と変異
- `scripts/test-check-signoff.py` — 基盤要件の表だけが違うタグの組が 1 になる試料
- `scripts/test-init-mkdocs.py` — 表示用ページ（`infra` の印）の試料
- `scripts/check-all.py` — 新しいテストの収録
- `.github/workflows/plugins.yml` — 新しいテストの収録（CI のステップ）
- `CLAUDE.md` — プロジェクト構成に新しいスクリプトとテストの行
- `docs/plans/issue-950.md` — この計画

触らない:
- #951 の Issue の本文の「参考資料」の節（Issue から図・表をたどる仕組み）——決まった基盤要件は scaffold の出力の 1 行で名指しするだけにする
- #952 の UI モック・#957 の成果物の表（`check-design-csv.py`）の形と検査
- scaffold が Python 以外の言語で生成物を作ること（Issue の受入基準は「黙って Python で作らない」まで）
- `check-signoff.py`・`merge-versions.py` 本体——`shared/` は比べる範囲・重ね合わせの対象に既に入っている
- `check-feasibility-csv.py`・`schedule-to-gantt.py`——feasibility のゲートはスキルが `check-infra-csv.py` を当てる（警告して進む）
- 公開ページ（`docs/` の本文）

複製の数（同じことを述べている箇所）: 列・状態・必須の項目の決まりは `tree.md`（原本）と `check-infra-csv.py` の定数（写し）の 2 箇所——`test-check-infra-csv.py` が突き合わせる。
ゲートの段ごとの扱い（警告・停止）は `tree.md`（原本）と、`scaffold.py`・`build-proposal.py` の docstring と各スキルの手順（指すだけ）。分けない理由: スクリプトの振る舞いはそれぞれの docstring が正で、スキルは原本を指すだけにする。
フックの写し（版の表を見出しどおりに描く）は決定表の描き方を共用する（写しを増やさない）。

## 決めたこと（Issue の「案」を形にした値）

- 置き場所と形式: `docs/v<n>/shared/infra.csv`（UTF-8。見出しの行はこの順・この綴り）。v2 以降はファイルごと置き換わる（`shared/` のほかの表と同じ）。
  構成の図は `shared/infra.drawio` と書き出し `shared/infra.svg`（「図」の drawio の決まり）。表示用ページは版の外の `docs/infra.md`（フックの `infra` の印が CSV から描く）。
- 列: `項目`・`決定`・`理由`・`費用への影響`・`水準`・`根拠`・`状態`
  - `項目`: 空にしない・重複させない。**`言語`・`DBMS`・`ホスティング環境` の 3 行は必ず置く**（無ければ未決定）。ほか（認証基盤・既存システムとの連携・監視・バックアップの手段など）は自由に足してよい
  - `状態`: `決定`・`暫定`・`未決定` のどれか
  - `根拠`: 共有の Q&A 表の `No`（`Q-` の形。内部の `D-` は指さない——発注者が決める）。**根拠の行の状態が、表の状態と対応すること**: `決定` ↔ `反映済み`、`暫定` ↔ `暫定反映`、`未決定` ↔ `確認中`（未決定の行も質問を起票してから置く）
  - `水準`: 満たす非機能要求の `shared/nfr.csv` の `No`（`N-001`。複数は `・` で区切る）。空でよい。指した No は nfr.csv に在ること
  - `決定`・`理由`・`費用への影響`: `決定`・`暫定` の行は空にしない。`未決定` の行は空でよい
  - 未決定の印（`spec-exit.md`）のあるセルは未決定に数える（値の決まりに当てない）
- 検査 `check-infra-csv.py <版のディレクトリか重ね合わせた全体>`: 0 = 全部決定 ／ 1 = 形式の違反 ／ 3 = 未決定（表が無い・必須の項目が無い・未決定の行・印・決定の行の空の欄）／ 4 = 未決定は無いが暫定がある ／ 2 = 判定していない
- ゲート（段ごと。**仕様の穴として推奨で決めた——下**）:
  - feasibility: 止めない。0 でなければ、未決定・暫定の項目を推奨の構成で見積もり、見積りの前提が暫定であることを規模の文書と報告に明示し、未決定の項目を質問にする
  - proposal（`build-proposal.py`）: 違反・未決定は 1、暫定は 3 で書かない
  - scaffold（`scaffold.py`）: 違反・未決定・暫定で 1（何も作らない）。**言語が `Python` で始まらない決定なら 1**（生成物は Python だけ——黙って Python で作らない）
  - 表が無い: proposal・scaffold とも**警告して進む**（前からの正本を壊さない）。検査の単体は 3
- 自律提案は feasibility の手順 5（費用付きの質問）で行う。入力は要求・制約・`shared/nfr.csv` の水準・正本の `CLAUDE.md` の基盤の前提（コンサルタントの初期提案があれば、それ）。
  水準が未決定なら水準の質問を先に起票する（#950 のコメント）。共有の Q&A 表に起票し（基盤要件は費用だけの選択でも共有——発注者の資産・保守の人材・ベンダーへの依存に効く）、表に `未決定` の行を置く。
  回答の反映は req-loop（`決定`／`暫定` に進める）
- 受け渡し: feasibility の前提は表から読む。scaffold は決まった基盤要件を出力の 1 行で名指しする（開発のリポジトリの `CLAUDE.md` に写すのは利用者）

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージで spec-loop 0.79.0 がカタログに載る（利用者が `plugin update` で受け取る）。GitHub Pages は計画ファイルのページが足されるだけ。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **置き場所と形式**: 基盤要件の置き場所（`shared/infra.csv`）・列・状態・必須の項目・根拠と水準の指し方・構成の図・表示用ページが `tree.md` に書かれ、本体の定数と一致する（ずれれば `test-check-infra-csv.py` が落ちる）。
2. **検査が決まりに反する表で止まる（陽性対照つき）**: 経路（人・スキルが表に書きうる誤り）——見出しの違い（順・綴り・列の過不足）・列の数・項目の空・重複・状態の値・根拠の形（`D-` を含む）・根拠が Q&A 表に無い・Q&A 表が無い・状態と根拠の行の状態の食い違い（3 通り）・水準の形・水準が nfr.csv に無い・UTF-8 でない・空のファイル・読めない Q&A 表。陽性: 決まりどおりの表（`tree.md` の例を含む）で 0。
3. **未決定と暫定を分けて報告する**: 表が無い・必須の項目が無い・`未決定` の行・決定の行の空の欄・未決定の印は 3、暫定だけなら 4、違反は 1、読めないは 2。印のあるセルは値の違反に数えない。
4. **ゲート（陽性対照つき）**: scaffold は 1・3・4 で何も作らず（`--check`・`--dry-run`・書く生成の経路とも）、全部決定なら作る。build-proposal は違反・未決定で 1、暫定で 3、全部決定なら書く。表が無ければ両方とも警告を出して進む。`--upto <前の版>` には当てない。
5. **言語**: 言語が `Python` で始まらない決定なら scaffold は 1 で何も作らない（`Python 3.12` は通る）。表が無ければ警告に「Python で作る」と出る。
6. **自律提案の規範**: 基盤要件が無い・未決定のとき、推測で決めずに選択肢・推奨・理由・費用への影響を付けた質問を共有の Q&A 表に起票し、表に未決定の行を置くことが feasibility の手順に書かれている。水準が未決定なら水準の質問を先に起票すること、コンサルタントの初期提案を入力にすることも。回答の反映が req-loop に書かれている。
7. **承認の照合の範囲**: `check-signoff.py` の比べる範囲に基盤要件の表が入る——表だけが違うタグの組で 1。
8. **表示用ページ**: 雛形のフックが `infra` の印で各版の `shared/infra.csv` を見出しどおりに描き、雛形に `docs/infra.md` があり `init-mkdocs.py` が写す。
9. **既存の振る舞いを壊さない**: 表の無い正本で scaffold・build-proposal の終了コードと生成物が変わらない（警告の行が増えるだけ）・`check-all.py` が緑・版が 3 種類で揃う。
10. **掛け算**: 上の基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）で渡す（4 つの受け渡し）。

検証で証明できないもの（未証明）:
- **スキルが実際に推測で決めずに推奨付きの質問を起票するか**（6 の振る舞い）——このリポジトリで検査できるのは本文に書かれていることと、`未決定` の行が Q&A の行を指すことの機械の検査まで。振る舞いは Eval（`claude` を起こして課金する）でしか見られず、この周では回さない。人間のレビューに回す。
- **表示用ページが MkDocs で描けること**——`mkdocs build` は CI に無い（`test-init-mkdocs.py` と同じ限界）。描画関数の出力までを見る。

生成物: 該当判定——`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけが対象で、この周は触らない。drawio の図も触らない。**生成物なし**（`skill-metrics.py --check`・`check-diagram-freshness.py` が `check-all.py` で緑のままであることだけ見る）。

## 仕様の穴（不在の線で推奨により決めた）

- **表が無いときに止めるか**: Issue は「未決定・暫定のまま進むと警告し、止める（または暫定であることを明示して進める）」で、表そのものが無いときを決めていない。
  選択肢 A: 警告して進む（前からの正本は表を持たない）／ B: proposal・scaffold を止める（0.x の壊れる変更、移行の手順を書く）。**推奨 A**——
  表はこの版から feasibility が自律提案で作るので、ふつうの流れでは表が在る。止めると前からの正本の scaffold と提案書が全部止まる。確認の Issue: （起票後に書く）
- **段ごとに止めるか暫定と明示して進むか**: Issue は「止める（または暫定であることを明示して進める）」で段を決めていない。
  選択肢 A: feasibility は進む（暫定と明示）・proposal と scaffold は止める ／ B: 3 段とも止める ／ C: 3 段とも暫定と明示して進む。**推奨 A**——
  見積りは基盤の選択肢の費用を比べる材料なので、基盤が決まる前に要る。提案書（予算の決裁）と scaffold（開発に渡す）は決まっていない基盤で進めると、誰も決めていない基盤が実装される。確認の Issue: （起票後に書く）

## 未解決の判断・確認待ち

- なし（上の 2 つは確認の Issue で利用者に渡す）

## 関門の進捗（再開点）

- 割り目（手順 4・手順 6）: **割らない（cruise の周）**——訊かずに続ける
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 交絡: 実験なし（まだ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 表が無いことで proposal・scaffold を止めるか | 止めない（警告して進む。検査の単体は 3） | 仕様の穴として推奨で決めた（上）。前からの正本は表を持たない |
| scaffold が Python 以外の言語の生成物を作るか | 作らない（止める） | 受入基準は「黙って Python で作らない」まで。別の言語の生成は別の Issue の大きさ |
| 基盤要件の質問を共有の表に置くか（費用だけの選択は内部、の例外） | 共有に置く | Issue が発注者（予算の責任者）の合意が要る要件と書き、レビュー会で回答をもらうとしている。言語・基盤は発注者の資産・保守の人材・ベンダーへの依存に効く |
| 状態を表に書くか Q&A から導くか | 表に書き、根拠の Q&A の行の状態と食い違えば違反 | Issue の列の案に `状態` がある。書いた状態を Q&A で照らすので、スキルが `決定` と書いて通すことはできない |
| feasibility のゲートをスクリプトに埋めるか | 埋めない（スキルが `check-infra-csv.py` を当て、3・4 でも進む） | feasibility は止めない段で、判定は `check-infra-csv.py` が持つ。見積りの表の検査は表の形だけを見る |
