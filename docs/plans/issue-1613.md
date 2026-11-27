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

- 実装: 未着手

## 既知の限界・決着済みの論点

（関門に渡す。採否の表もここに足す）

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| spec-loop の `tree.md`（「画面の表」）と `screen-gate.py` は screen-spec の名前を持つ | 前例として、spec-loop 側の口（関門）だけが design-system の名前を持つ形を子の Issue で採ってよい。この周（A4）は spec-loop を触らないので名前を持たない | screen-spec の前例。platform-spec は `profile-gate.py` だけが名前を持つ（`test-check-infra-csv.py` が見る） |

## 手順 8

- この周の起票: 0 件（手順 8 で利用者に起票を訊いてから書き直す）
