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
関門の 2 パスと狭いパスの後（2026-11-27）: 「spec-profile がモノレポで管理されるのであれば、これらの human readable ドキュメントも追加することになる」——
`AskUserQuestion` で確かめた: **同じサイトに載せる**（ドキュメントのサイトをリポジトリ全体のガイドラインのサイトにし、手で書く profile の層の表と `guides/` の本文、束の入口の頁を描く）・**この PR に足す**（足した差分だけに Verifier を 1 回当てる——当て直し）。
触るファイルは同じ `references/tree.md`・`references/outputs.md`（と README の要約）。受入基準 A12 を足した。
同じ時に「docs を design とか design-system にした方がわかりやすい」——正本の根の `docs/` は spec-loop が決め打ちしている（スクリプト 8 本・MkDocs の `docs_dir`）と伝え、
`AskUserQuestion` で確かめた: **spec-loop に口を足す（子 Issue）**。`references/spec-loop.md` の「spec-loop に要る口」に 5 を足し、入るまでは `docs/`。受入基準 A13 を足した。
続けて利用者が、組織のシステム構築ガイドの文書のリポジトリ（非公開。名前と中身は計画・原本・PR に書かない——利用者の指示）の中にデザインシステムと spec-profile を置く形を示した——
「全体の世界観を文書で説明して、その構成要素でデザインシステムや UI プロファイルなどがある」。そのリポジトリは直下の `docs/` がガイドの MkDocs のサイトで、手で書いた profile を `spec-profile/<名前>/` に持つ。
`AskUserQuestion` で確かめた: **この PR で書き直す**（プライベートリポジトリの情報は出さない）。A12 を「人が読む入口はガイドのサイト 1 つで、design-system は頁を差し込む」形に直し、`guides/` をやめ、口 5 をガイドのリポジトリで使う前提と書く。受入基準 A14 を足した。
続けて利用者（2026-11-27）: 「ガイドの無いリポジトリ、の想定は不要で、ガイドに何を含めるかで決まる。人によってはガイドにデザインシステムだけを定義するかもしれない」——
リポジトリはいつもガイドで、構成要素（デザインシステム・UI プロファイル・基盤の profile・プラグイン）はどれも任意にする。design-system が自分でサイトを作る形（`build/design-system/site/`）をやめ、人が読む入口はいつもガイドのサイト。口 5 は design-system を使う前提になる。
A12・A14 をこの形に直した。当て直し 3 の注記 2 件（フックの口の書き方・直下の名前の行）もこの書き直しで直す。

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
| A12 | 人が読む文書の入口が原本に決まっている——人が読む入口はいつもガイドの MkDocs のサイト 1 つで、design-system はデザインシステムの頁と手で書く profile の層の表をそこへ差し込む（サイトを丸ごと作らない）。「ガイドの無いリポジトリ」の形を持たない。手で書く profile の本文はガイドの文書で、design-system は書き換えない。作業中かリリース済みかの示し方・profile のレビューと承認（サインオフの外）が書かれ、今ある原本（spec-loop の `external-profile.md`・`init-mkdocs.py`・screen-spec の `mkdocs.md`）の事実と合う（関門の後に利用者が求めた。2026-11-27） | `references/outputs.md` の「ドキュメントのサイト」・`references/tree.md` | 当て直しの Verifier が原本と照らす |
| A13 | 正本の根の `docs/` の名前を変える口（spec-loop の子 Issue）が原本にあり、決め打ちしている箇所の数え上げが今の main の実物と合い、名前の候補が spec-loop の既存の名前（根の `design/sources.csv` など）とぶつからない。入るまでは `docs/` と書かれている（関門の後に利用者が求めた。2026-11-27） | `references/spec-loop.md` の「spec-loop に要る口」・`references/tree.md` の「木」・README | 当て直しの Verifier が spec-loop の `scripts/`・`templates/`・`references/` と照らす |
| A14 | ガイドのリポジトリの世界観（ガイドの文書が全体を説明し、デザインシステム・UI プロファイル・基盤の profile・プラグインを構成要素として持つ。**どの構成要素も任意で、ガイドに何を含めるかで決まる**——デザインシステムだけのガイドもある）と、その中の木が原本にある。ガイドの `docs/` と spec-loop の正本の `docs/` がぶつかることと、その解き方（口 5）が書かれている。非公開のリポジトリの名前と中身を書かない（関門の後に利用者が求めた。2026-11-27） | `references/tree.md`・`README.md`・`references/spec-loop.md` の口 5 | 当て直しの Verifier が原本と照らし、名前が出ていないことを grep で見る |
| A9 | A1〜A8・A10・A11 を、Verifier と `/code-review` の両方に、1 パス目と 2 パス目（該当すれば）で渡す（4 つの受け渡し） | 関門 | 下の関門の記録 |

この環境で証明できないもの（未証明）: 設計が実装で成り立つか（たとえば描画キットを screen-spec のモックに埋め込んで同じ入力から同じバイトになるか、DTCG の出力が実際のツールで読めるか）——設計の周なので実装は無い。子の Issue の受入基準に回す。

生成物: なし（このリポジトリの生成物——図の書き出し・`skill-metrics.py` の生成ブロック——に当たる変更は無い。`SKILL.md` を触らない）。
プロパティテスト: なし（文書だけの周で、入力の空間を持つ実装が無い）。
差分テスト: なし（新しいプラグインと文書を足すだけで、既存の振る舞いを変えない周ではない——変える既存の振る舞いが無い）。
仕様の振る舞い: このリポジトリに spec-loop の正本は無い。形式検査のモデルも無い。

## 未解決の判断・確認待ち

- 子の Issue の分け方は README の「子の Issue」に置き、利用者の指示で 6 件を起票した（#1617〜#1622。手順 8）。
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
- マージ: 最初に訊いたときは答えが無く止めた。関門の後の書き直しを終えたあと、利用者の指示「マージして」（2026-11-27）でマージする（子の Issue 6 件は利用者の指示で起票した——手順 8）
- 関門の後の範囲の追加（A12・A13。利用者の求め、2026-11-27）: 起点 `4b21fe18`（計画ファイルだけのコミットの後）→ 終点 `0abb3e2f`。`check-all.py` 緑
- 当て直し 1（Verifier・sonnet。`4b21fe18..0abb3e2f`）: 済み——**反証 1 件**（A13 の決め打ちの数え上げに dev-loop の 2 本が漏れた）→ 直した（`3fee47b6`）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-redo-1-20261127T095131Z.md`
- 当て直し 2（Verifier・sonnet。`0abb3e2f..3fee47b6`）: 済み——**反証 1 件（軽微）**: 同じ 2 ファイルの中の正規表現（`formal-sync.py` 134 行の `BASE_README`・`rework-metrics.py` 127 行の `TABLE`）も `docs/` を決め打ちしていて、数え上げから漏れている。**直さずに人間に渡す**（狭いパスと同じ扱い）。A13 は文字どおりには満たしていない——マージするかは利用者が決める。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-redo-2-20261127T095510Z.md`
- ガイドのリポジトリの形への書き直し（A12 の直し・A14。利用者の求め、2026-11-27）: 起点 `2d9f0226` → 終点 `7ffde7c2`。`check-all.py` 緑。非公開のリポジトリの名前の grep 0 件
- 当て直し 3（Verifier・sonnet。`2d9f0226..7ffde7c2`）: 済み——**反証 0 件**。注記 2 件（反証ではない。人間に渡す）: (1) 「spec-loop のフックの口はガイドには無い」は、`init-mkdocs.py --hook` が設定の在る根でも登録だけはする点と書き方が食い違う（呼び出し側が写されないので、登録しても呼ばれない——結論は同じ）。(2) `tree.md` の「直下の名前は spec-loop が使うものを避ける（`docs/` …）」と、ガイドのリポジトリの木で直下の `docs/` をガイドが使う形に緊張がある（後者は口 5 が前提）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-redo-3-20261127T100514Z.md`
- リポジトリはいつもガイドにする書き直し（A12・A14 の直し。利用者の求め、2026-11-27）: 起点 `0c38d35f` → 終点 `3b16c00f`。`check-all.py` 緑。非公開の名前の grep 0 件
- 当て直し 4（Verifier・sonnet。`0c38d35f..3b16c00f`）: 済み——**反証 1 件**（カタログの description が書き直し前の「デザインシステム用のリポジトリ」のまま）→ 直した（`63c99330`。注記 N1 の Q&A 表の頁・N2 の雛形の段も一緒に）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-redo-4-20261127T101658Z.md`
- 当て直し 5（Verifier・sonnet。`3b16c00f..63c99330`）: 済み——**反証 1 件（軽微）**: README の 5 行目「人間がレビューするドキュメントのサイトを作ります」に旧い言い回しが残る（頁を差し込む形と食い違う）。**直さずに人間に渡す**（直すとまた当て直しが要る）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-redo-5-20261127T102048Z.md`
- 人間に渡した 2 件（README の 5 行目・A13 の正規表現 2 か所）を、利用者の指示「提案通りに修正して」（2026-11-27）で直した: 起点 `e3475f91` → 終点 `2bec11be`。A13 は一覧に 2 か所を足し、子の Issue が着手の時点で数え直すと添えた。`check-all.py` 緑
- 当て直し 6（Verifier・sonnet。`e3475f91..2bec11be`）: 済み——**反証 0 件**（数え上げを自分で grep で数え直して一致）。軽微な注記（反証ではない）: `review.md` 13 行の「生成したドキュメントのサイト」は節の名前と同じで誤りではない。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-redo-6-20261127T103209Z.md`
- 子の Issue 6 件を利用者の指示「課題も起票して」（2026-11-27）で起票し、README の番号を書いた: 起点 `9a982542` → 終点 `133732de`。`check-all.py` 緑
- 当て直し 7（Verifier・sonnet。`9a982542..133732de`）: 済み——**反証 0 件**（各 Issue の題と本文が README の段と原本に一致、非公開の名前 0 件）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1613/bd1212a6-503b-4ea8-a894-56eafb305470/scratchpad/gate-1613-redo-7-20261127T104413Z.md`
- 交絡を潰した手順: 実験なし（文書の周。指摘の根拠は実物のファイル:行を開いて確かめた——`qa-to-pptx.py` 35〜36・109 行・spec-loop の MkDocs の雛形の `site_dir: site`・`signoff-tags.md` の見出し・`versions.md` 129 行・`build-mock.py` 411 行・screen-spec の `profiles.md` 118〜126 行）

```dev-loop-gates
周の base: 0c824eace80033e869325f8fd757fb58bc766376
関門: Verifier 1 7b419007 反証=2
関門: /code-review 1 7b419007 指摘=9
関門: Verifier 2 c550ffb6 反証=2
関門: /code-review 2 c550ffb6 指摘=10
関門: 狭いパス cd32a0565d9784852bed8551c1c0de3cb0315a63 0ac8fe9ddbeffe078e31edf50149944c60604179 反証=0
関門: 当て直し 4b21fe18e1cc467bc87e7704c43a585150c6aab6 0abb3e2f4bd5f42aaab8abb223e7a6f478642b90 反証=1
関門: 当て直し 0abb3e2f4bd5f42aaab8abb223e7a6f478642b90 3fee47b64d933edbb1d140184e5295f84af82efb 反証=1
関門: 当て直し 2d9f02265f682fdc9df6d546a28ec2e1cfdd17f5 7ffde7c2b71e8f3d53fd4f82cd2084e8fbec17b1 反証=0
関門: 当て直し 0c38d35fe55ac8c8360bf0e1dedb60a5cbaa0986 3b16c00f48a4ca0ad3ec9a3cdab7d988544e68e4 反証=1
関門: 当て直し 3b16c00f48a4ca0ad3ec9a3cdab7d988544e68e4 63c993307a5d9f33c41e9273f5b4db033a9d0152 反証=1
関門: 当て直し e3475f912abba6c7d9358a4a079f6839c542bb7b 2bec11beb3f56ecfcae339a0a9319002a4e7f5b5 反証=0
関門: 当て直し 9a98254284dfbbe087043d922245232cf5bc65b6 133732de02008c7aaeb5c4f04e2bc7a354597d3f 反証=0
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
受入基準: A5 満たす
受入基準: A6 満たす
受入基準: A7 満たす
受入基準: A8 満たす
受入基準: A9 満たす
受入基準: A12 満たす
受入基準: A13 満たす
受入基準: A14 満たす
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

効いた行（手順 8。マージの後に記録した——マージの前に書き忘れた。台帳は dev-loop 2.27.0 の `references/line-registry.csv`）:

- 効いた行: V-03（Verifier 1 パス目の V1・V2、2 パス目の V2-R1・V2-R2、当て直し 1・2・4・5 の反証——どれも記述の事実を実物と照らして見つけた。報告は項 3 を挙げた）
- 効いた行: R-02（`/code-review` 2 パス目の CR2-1〜CR2-10——報告は項 2 を挙げた。1 パス目の CR1〜CR9 は報告に項の番号が無く、指摘の中身（原本が書く事実と実物の照合）から著者が当てた）

## 手順 8

- この周の起票: 6 件（#1617・#1618・#1619・#1620・#1621・#1622。README の「子の Issue」の段 1・2・3・5・6・7——利用者の指示「課題も起票して」、2026-11-27、マージの前）
