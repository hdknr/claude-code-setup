# Issue #1613 — design-system: デザインシステムを spec-loop の決め方で作る専用のプラグインを足す（設計）

利用者が居る周（2026-11-27）。親 #1609。この周は **設計まで**——プラグインの骨組み（カタログ・`plugin.json`・`README.md`）と `references/` の原本を置く。スクリプト・スキル・エージェントは置かない（子の Issue）。
読み込んだ dev-loop は 2.27.0。

直す線: `既定`（出所: `.claude/dev-loop.md` に `直す線:` の行が無い。手順 3 の問いは、この周の判断の多くを利用者に訊いたので、既定のまま進めると周の途中で申告する——下の「未解決の判断」）。

## 周の在り処

- ブランチ: `issue/1613-design-system-plugin`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1613`
- 起点コミット: `0c824eac`
- base: 参照 `origin/main` → `0c824eace80033e869325f8fd757fb58bc766376`

## 利用者と決めたこと（出所: この会話の AskUserQuestion と利用者の発言。2026-11-27）

Issue 本文（外部入力。書いたのは利用者のアカウント）に「利用者と決めた」と書いたものに加え、この周の着手時に訊いた 4 つ:

| # | 問い | 決めた値 |
| --- | --- | --- |
| D1 | プラグインの名前 | `design-system` |
| D2 | デザインシステムの表の重ね方 | **行の単位**（spec-loop の `versions.md`・`merge-versions.py` の `ROW_TABLES` に表を登録する変更が要る——spec-loop 側の別 Issue） |
| D3 | 使う側が読む生成物（索引・DTCG のトークン・描画キット）の渡し方 | **コミットする**（`--check` で鮮度を見る。使う側は `release-v<n>` のタグの時点を git で読む） |
| D4 | 部品の状態とアクセシビリティを誰が確かめるか | **spec-review も通す**（判定役に突かせる） |

D4 の形（この周の判断。人間レビューで確かめてもらう）: spec-loop の `spec-review` スキルそのものは改修しない（Issue の「spec-loop を改修しない」）。
design-system が自分のレビューのスキルと、書き込みツールを持たない判定役を持つ——spec-loop の判定役の決まり（別ティア・書き込みツールなし・`model` を書かない）に従う。
理由: spec-loop の `spec-review` の抜ける条件（`spec/` のチェックリスト・テストケース・TLC）と中間表現はデザインシステムの表に合わず、そのまま当てると spec-loop を改修することになる。

周の途中の利用者の求め（2026-11-27）: 「同じリポジトリにデザインシステム・UI 実装プロファイル・基盤要件プロファイルをモノレポで共存させられるか」——
範囲を広げた（触るファイルは同じ `references/tree.md`。受入基準 A10 を足した）。
続けて「spec-loop＋dev-loop でシステム開発する際に、ガイドラインとして一括でも渡せるようにしたい」——同じファイルに節を足し、受入基準 A11 を足した。

## 変更範囲

触る:

- `plugins/design-system/` — 新規。`.claude-plugin/plugin.json`（0.1.0）・`README.md`・`references/*.md`
- `.claude-plugin/marketplace.json` — design-system のカタログの行
- `CLAUDE.md` — プロジェクト構成に design-system
- `docs/plans/issue-1613.md` — この計画ファイル

触らない:

- spec-loop・screen-spec・platform-spec・dev-loop の本体（spec-loop に要る口・screen-spec の読む側・dev-loop の引き渡しの読み方は子の Issue）
- スクリプト・スキル・エージェント・テスト（実装は子の Issue）
- 公開サイト（`docs/` のページ）——platform-spec と同じく、プラグインの公開ページはまだ作らない

依存の追加・更新: なし

## 設計の判断（この周で決めたもの）

原本は `plugins/design-system/references/`。ここには要点だけ:

- 正本の木: デザインシステムのリポジトリは spec-loop の正本でもある。表は `docs/v<n>/requirements/design-system/data/` の 5 つ（トークン・部品・部品の仕様・パターン・規則）と `settings.csv`、散文は `requirements/design-system/` の Markdown。
- 生成物（コミット）: リポジトリの根の `spec-profile/<名前>/`（使う側が spec-loop の `external-profile.py` で読む索引）・`tokens/`（DTCG）・`kit/`（描画キット）。ドキュメントのサイトはコミットしない（`site/`）。
- spec-loop に要る口（spec-loop 側の別 Issue）: 行の単位の表の登録・「見た目」の線・関門・レビュー会の資料のリンク。
- 引き渡し: 変わった部品ごと（とトークンの変更で 1 件）に、UI プロファイルのリポジトリへ登録する Issue の本文。印 `<!-- design-system-handoff: v1 -->`。

複製の数: 決まりの原本は `references/` の各ファイル（1 か所ずつ）。README・`plugin.json` と `marketplace.json` の description（JSON 2 か所は同じ値）・CLAUDE.md の項は指すだけ。
spec-loop・screen-spec の決まりは写さず、パスと節の名前で指す。**分けない理由**: 原本以外は要約と指し先だけにする（screen-spec・platform-spec と同じ形）。

## デプロイ経路

プラグインの配布（`marketplace.json` のカタログ）。公開サイトは変えない（`docs/` を触らない——計画ファイルは `docs/plans/` だが mkdocs の nav に載らない作業記録）。

## 受入基準

不変条件 × 経路。経路（読む入口）: プラグインのカタログ（`marketplace.json` → `plugin.json`）・`README.md`・`references/` の各原本・CLAUDE.md の項・spec-loop の `scripts/`・`references/`（依存の向き）。

| # | 不変条件 | 経路 | 証明手段 |
| --- | --- | --- | --- |
| A1 | Issue の「この Issue でやること」の 1〜6 が `references/` に、7（子の Issue への分け方）が `README.md` に、決めた形で書かれている。決めずに残したものは「決めていないこと」として名指しされ、どの子 Issue で決めるかが書かれている | `references/`・`README.md` | Verifier が 1〜7 ごとに原本の節を名指し、黙って抜けた項目が無いかを見る |
| A2 | spec-loop・screen-spec の決まりを写さず指す（Q&A 表の列・番号の形・未決定の印・版の重ね方・サインオフの範囲・外部の profile の置き場所の表を複製しない） | `references/` | Verifier の読解と grep |
| A3 | 原本が spec-loop・screen-spec・platform-spec について述べる事実が、今の main の実物と合う（ROW_TABLES の決まり・`screen-gate.py` の形・`external-profile.py` の置き場所・`qa-to-pptx.py --links`・`check-signoff.py` の比べる範囲・screen-spec の項目の種類・spec-loop の判定役の決まり など） | `references/` が引く各ファイル | Verifier が実物を開いて（走らせて）照らす |
| A4 | spec-loop の `scripts/`・`references/` が `design-system` の名前を持たない | spec-loop の `scripts/`・`references/` | `grep -rn design-system plugins/spec-loop/scripts plugins/spec-loop/references` が空 |
| A5 | カタログ・`plugin.json` の版（0.1.0）と description が揃い、版の決まりに沿う | `marketplace.json`・`plugin.json` | `check-plugin-versions.py`・`check-description-sync.py origin/main` |
| A6 | 利用者と決めたこと（D1〜D4 と Issue 本文の「利用者と決めた」——版の管理・ワークフロー・サイトは最新の版で作業中を示す・UI モックを描画キットで描く・サイトの既定は非公開）と原本が食い違わない | `references/`・README | Verifier の読解 |
| A7 | 原本の中の指し先（`references/…`・節の名前）が実在する | `references/`・README | `check-skill-pointers.py`・`check-site-links.py` |
| A8 | 歯止めが全部緑 | リポジトリ全体 | `python3 scripts/check-all.py` |
| A10 | デザインシステム・UI プロファイル・基盤の profile を 1 つのリポジトリに共存させる形が原本にあり、生成物が手で書いた profile を上書きしないこと・タグの系列が混ざらないこと・承認の範囲が書かれている（周の途中で利用者が求めた。2026-11-27） | `references/tree.md` の「モノレポで共存させる」 | Verifier が spec-loop の `external-profile.md`・platform-spec の `check-profile-diff.py` の `name_shape`・spec-loop の `monorepo.md`・`signoff-tags.md` と照らす（必要なら `name_shape` を走らせる） |
| A11 | 束（基盤・アーキテクチャ・開発の進め方・画面の層とデザインシステム）を案件に一括で渡す形が原本にあり、入口が 1 つ（platform-spec の案件の設定）で、今ある口（`profile-layers.py`・screen-spec の基盤の profile から引く初期値）の事実と合い、デザインシステムを作業中の時点で読まない（周の途中で利用者が求めた。2026-11-27） | `references/tree.md` の「ガイドラインとして一括で渡す」 | Verifier が platform-spec の `references/infra-profile.md`・`layers.md`・`scripts/profile-layers.py`、screen-spec の `references/profiles.md` の「基盤の profile から引く初期値」と照らす |
| A9 | A1〜A8・A10・A11 を、Verifier と `/code-review` の両方に、1 パス目と 2 パス目（該当すれば）で渡す（4 つの受け渡し） | 関門 | 下の関門の記録 |

この環境で証明できないもの（未証明）: 設計が実装で成り立つか（たとえば描画キットを screen-spec のモックに埋め込んで同じ入力から同じバイトになるか、DTCG の出力が実際のツールで読めるか）——設計の周なので実装は無い。子の Issue の受入基準に回す。

生成物: なし（このリポジトリの生成物——図の書き出し・`skill-metrics.py` の生成ブロック——に当たる変更は無い。`SKILL.md` を触らない）。
プロパティテスト: なし（文書だけの周で、入力の空間を持つ実装が無い）。
差分テスト: なし（新しいプラグインと文書を足すだけで、既存の振る舞いを変えない周ではない——変える既存の振る舞いが無い）。
仕様の振る舞い: このリポジトリに spec-loop の正本は無い。形式検査のモデルも無い。

## 未解決の判断・確認待ち

- 子の Issue の分け方は `references/` の「子の Issue」に案を置き、起票は手順 8 で利用者に訊く。
- D4 の形（自前のレビューのスキルと判定役）は人間レビューで確かめてもらう。

## 関門の進捗（再開点）

- 実装: 済み（`b078b5cd`）。`check-all.py` は緑（106 本中 19 本を回して失敗 0、87 本は CACHED）。`check-description-sync.py origin/main` 緑。A4 の grep は 0 件
- 割り目（手順 4）: 利用者に訊いた（2026-11-27）——**ここで割る**を選んだ。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 1613`（手順 5 から）
- 再開（2026-11-27、`/clear` の後）: `find-cycle.py` は 1（当たった）。ブランチ・HEAD（`7b419007`）が周の在り処と一致
- 1 パス目の起点（指摘対応の 0 行の判定に使う）: `7b419007`（成果物はコミット済み。この後の未コミットは計画ファイルだけ）
- Verifier 1 パス目: 済み——**反証 2 件**（`dev-loop:dev-loop-verifier`・sonnet。終点 `7b419007`。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/11c8a260-cf14-46c5-ba2f-c9a98c61f4bf/scratchpad/gate-1613-verifier-1-20261127T085919Z.md`）
- `/code-review` 1 パス目: 済み——**指摘 9 件**（high。終点 `7b419007`。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/11c8a260-cf14-46c5-ba2f-c9a98c61f4bf/scratchpad/gate-1613-code-review-1-20261127T085919Z.md`）
- D4 は両方の関門が挙げた。利用者に `AskUserQuestion` で確かめた（2026-11-27）——「自前の判定役で代える」。原本に選ばれた値と理由を書く
- 1 パス目の指摘対応: 採否の表の「直す」10 行を直した（下の採否の表）。差し戻しは手順 4 への 1 回（この指摘対応）
- 指摘対応のコミット: `c550ffb6`。`check-all.py` 緑（16/106 を回して失敗 0、90 は CACHED）。1 パス目の起点 `7b419007` からの成果物の差分は 0 行でない——2 パス目を回す
- 2 パス目の関門に渡す終点: `c550ffb6`。狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: 2 パス目の結果を受けて書く
- 残っている関門: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方。どちらも未着手
- 割り目（手順 6・2 パス目の前）: 利用者に訊いた（2026-11-27）——**ここで割る**を選んだ。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 1613`（Verifier 2 パス目と `/code-review` 2 パス目から。差分の base は周の base のまま、2 パス目の対象は 1 パス目の指摘対応 `7b419007..c550ffb6`）
- 再開（2026-11-27、2 つ目の割り目の `/clear` の後）: `find-cycle.py` は 1（当たった）。ブランチ・HEAD（`cd36a3ec`）が周の在り処と一致。base `0c824eac` は HEAD の祖先
- Verifier 2 パス目: 済み——**反証 2 件**（`dev-loop:dev-loop-verifier`・sonnet。終点 `c550ffb6`（HEAD は計画ファイルだけのコミット `cd36a3ec`）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-verifier-2-20261127T091442Z.md`）
- `/code-review` 2 パス目: 済み——**指摘 10 件**（high。important 6・nit 4。終点 `c550ffb6`。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-code-review-2-20261127T091442Z.md`）
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `cd32a0565d9784852bed8551c1c0de3cb0315a63`
- 2 パス目の指摘対応: 採否の表（2 パス目）の「直す」12 行を直した。終点（指摘対応の最後のコミット）: `0ac8fe9ddbeffe078e31edf50149944c60604179`。`check-all.py` 緑（16/106 を回して失敗 0、90 は CACHED）。A4 の grep は 0 件
- 狭いパス（Verifier）: 済み——**反証 0 件**（`dev-loop:dev-loop-verifier`・sonnet。素通りした変異: 読解の変異 (a) 旧名の残り——対象が 0 件で届かない。注意 1: V2-R1 の根拠は monorepo.md の解釈に依る——人間が決める。`cd32a056..0ac8fe9d` の 2 点。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-narrow-1-20261127T092505Z.md`）
- PR: #1615。PR 側の CI 20 pass・1 skipping（deploy）。外部レビュー: 該当なし（`.claude/dev-loop.md` に宣言が無い）。関門の記録を PR コメントに書いた
- マージ: しない——2026-11-27 に AskUserQuestion で訊いたが答えが無く、承認待ちで止めた
- 交絡を潰した手順: 実験なし（文書の周。指摘の根拠は実物のファイル:行を開いて確かめた——`qa-to-pptx.py` 35〜36・109 行・spec-loop の MkDocs の雛形の `site_dir: site`・`signoff-tags.md` の見出し・`versions.md` 129 行・`build-mock.py` 411 行・screen-spec の `profiles.md` 118〜126 行）

```dev-loop-gates
周の base: 0c824eace80033e869325f8fd757fb58bc766376
関門: Verifier 1 7b419007 反証=2
関門: /code-review 1 7b419007 指摘=9
関門: Verifier 2 c550ffb6 反証=2
関門: /code-review 2 c550ffb6 指摘=10
関門: 狭いパス cd32a0565d9784852bed8551c1c0de3cb0315a63 0ac8fe9ddbeffe078e31edf50149944c60604179 反証=0
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
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

（関門に渡す。採否の表もここに足す）

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| spec-loop の `tree.md`（「画面の表」）と `screen-gate.py` は screen-spec の名前を持つ | 前例として、spec-loop 側の口（関門）だけが design-system の名前を持つ形を子の Issue で採ってよい。この周（A4）は spec-loop を触らないので名前を持たない | screen-spec の前例。platform-spec は `profile-gate.py` だけが名前を持つ（`test-check-infra-csv.py` が見る） |
| D4 の形（spec-review そのものではなく自前の判定役） | 採った——利用者に確かめた（2026-11-27、`AskUserQuestion`「自前の判定役で代える」）。原本（`review.md` の「判定役」・`spec-loop.md` の表）に選ばれた値と代えた理由を書いた | spec-review の抜ける条件と中間表現がデザインシステムの表に合わない |

採否の表（1 パス目。直す線: 既定）:

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1・CR7 | D4 の値「spec-review も通す」と原本の「spec-review: 使わない」が食い違い、原本はそれを書いていない | 示せる——計画の D4 の行と `spec-loop.md` 30 行・`review.md` 47 行 | A6 | 直す（利用者に確かめて形は据え置き、原本に値と理由を書く） |
| V2 | feasibility を使わない正本で、予算側のタグが何に合意するかが無い | 示せる——`check-signoff.py` 384〜399 行が 2 つのタグを求める・`signoff-tags.md` の budget の定義 | A1（決めずに残したものの名指し） | 直す（`spec-loop.md` に「決めていないこと」を足した） |
| CR1 | サイトを直下の `site/` に置くが、同じファイルが `site/` を避けると言い、spec-loop の MkDocs も `site/` を使う | 示せる——spec-loop の `templates/mkdocs/mkdocs.yml` 4 行・`gitignore` 2 行・`tree.md` 151 行 | A10・A3 | 直す（`build/design-system/site/` に） |
| CR2 | 口 4 は `qa-to-pptx.py --links` で足りる見込みとするが、`--links` で表紙に「見た目は確かめる対象ではない」が必ず出る | 示せる——`qa-to-pptx.py` 35〜36・109 行 | A3 | 直す |
| CR3 | 束の「入口は 1 つ」は、層を別の `<名前>` に分けると成り立たない | 示せる——screen-spec の `profiles.md` 118〜126 行（同じ名前・同じタグ） | A11・A3 | 直す（束なら同じ `<名前>` に置くと決めた） |
| CR4 | 「`signoff-tags.md` の「比べる場所」」の見出しが無い（2 か所） | 示せる——`signoff-tags.md` の見出しは「2 つの承認が同じ範囲を見ていたか」 | A7 | 直す |
| CR5 | 索引のリンクを「行を最後に置いた版」の散文にすると、散文がその版に無いことがある | 示せる——表は行の単位・散文はファイルの単位（`versions.md`）、`external-profile.py` の `check_links` はタグの時点のファイルの在否を見る | A3 | 直す（ファイルを最後に置いた版） |
| CR6 | 口 1 の `ROW_TABLES` を読む一覧が screen-spec の `build-mock.py` を落とし、画面の表として読む箇所を絞る必要を書いていない | 示せる——`versions.md` 129 行・`build-mock.py` 411 行・`screen-gate.py` 116 行 | A3 | 直す |
| CR8 | コントラスト比の基準を規則の表で決めるとするが、規則の表に値の列が無い | 示せる——`tree.md` の規則の表の列 | A1（決めずに残したものの名指し） | 直す（`tree.md` の「決めていないこと」に足した） |
| CR9 | 「記事」の出所がプラグインの中に無い | 示せる——`spec-loop.md` 28 行・`tree.md` 73・106 行 | A7 | 直す（`README.md` に「出所」） |

採否の表（2 パス目。直す線: 既定。どれも実物を開いて確かめた）:

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V2-R1 | CR1 の直しが `monorepo.md` の「build/ を分けない」をサイトの置き場所の根拠にしたが、その節は直下の `build/` を spec-loop に任せる決まり | 示せる——`monorepo.md` 50〜52 行 | A3・A7 | 直す（根拠を screen-spec の `build/mock/` の前例にし、monorepo.md が締め出すのは実装の出力だと書いた） |
| V2-R2 | 記事の出所を「#1613 の本文」とするが、URL は #1609 の本文にしかない | 示せる——`gh issue view 1613` の本文に http が 0 件・#1609 の 3 行目 | A3 | 直す（親 #1609） |
| CR2-1 | 表のパス `requirements/design-system/data/` を `ROW_TABLES` に登録すると spec-loop が `design-system` の名前を持つ | 示せる——`merge-versions.py` 118〜124 行の `SCREENS_DATA` がパスを持つ・`spec-loop.md` の口 3 と依存の向き | A1・A6（Issue の「spec-loop に名前を持ち込まない」） | 直す（`requirements/design/` に改名し、理由を `tree.md` に書いた） |
| CR2-2 | CR5 の直しが表の行には誤った版を指す（v2 の表は変えた行だけ） | 示せる——`versions.md` の行の単位で重ねる表 | A3 | 直す（散文はファイルの版、表は行の版） |
| CR2-3 | 「検査を通らない表から作らない」と作業中の版の `--check`・サイトが両立しない | 示せる——`outputs.md` 19〜22・78 行と `review.md` の終了コード 3 | A1 | 直す（1 だけで止め、3 では作る。印のあるセルの出し方は「決めていないこと」） |
| CR2-4 | 「指すトークンが変わった」が別名をたどるかを決めていない | 示せる——`tree.md` の `層` と `値` の別名の例 | A1 | 直す（別名を解いた値で比べる） |
| CR2-5 | `ROW_TABLES`・`ROW_KINDS` を画面として読む箇所の数え落とし（4 か所）、連鎖が画面に固定 | 示せる——`merge-versions.py` 645 行・`diff-versions.py` 166〜180 行・`build-proposal.py` 391 行・`check-signoff.py` 300 行 | A3 | 直す |
| CR2-6 | 既存 UI の棚卸し（Issue の利用のイメージの 2）の行き先が無い | 示せる——#1613 本文 18・41 行 | A1・A6 | 直す（`spec-loop.md` の「決めていないこと」と README の段 2） |
| CR2-7 | 口 4 の注記を口 2 と一緒に決めるのに段が分かれている。リンクの文が「モック:」に固定 | 示せる——README の段 1・5、`qa-to-pptx.py` 308 行 | A3・A1 | 直す（口 4 を段 1 に寄せ、ラベルの口を足した） |
| CR2-8 | 束でもタグの接頭辞を `ui-v<n>`・`infra-v<n>` に分けると読める | 示せる——screen-spec の `profiles.md` 120〜126 行（同じタグで読む） | A10・A11 | 直す（束では 1 つの系列） |
| CR2-9 | トークンの鍵の決まり（英小文字）と例 `color.blue.600` が食い違う | 示せる——`tree.md` 57・63 行 | A1 | 直す（数字と `-` を許す） |
| CR2-10 | Issue の表の一覧（文言の表）から変えた理由が無い | 示せる——#1613 本文 37 行と `tree.md` の 5 つの表 | A1・A6 | 直す（理由を表の節に書いた） |

- 効いた行（Verifier）: V1 は「主張する事実の真偽」の行、V2 も同じ（台帳の ID は手順 8 で引く）

## 手順 8

- この周の起票: 0 件（2026-11-27 に AskUserQuestion で訊いたが 300 秒で答えが無く、起票しない側に倒した。README の子の Issue 6 件は後で利用者が起票する）
