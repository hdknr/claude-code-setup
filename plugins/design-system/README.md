# design-system

デザインシステムを [spec-loop](../spec-loop/README.md) の決め方（Q&A 表・レビュー会・承認・版）で作るプラグインです（設計は [#1613](https://github.com/hdknr/claude-code-setup/issues/1613)、親は [#1609](https://github.com/hdknr/claude-code-setup/issues/1609)）。
デザインシステム用のリポジトリを新しく作り、そのリポジトリで design-system と spec-loop を使って進めます。表（トークン・部品・部品の仕様・パターン・規則）を検査し、
使う側（案件の screen-spec・組織の UI プロファイル）が読む生成物と、人間がレビューするドキュメントのサイトを作ります。

**デザインシステムと UI プロファイルは別の概念です**——デザインシステムは見た目と振る舞いのルール（技術に依存しない）、UI プロファイルはそれを実装する方式（組織ごとの screen-spec の外部の profile）で、UI プロファイルがデザインシステムを参照します。

design-system は spec-loop の決まりに従い、**spec-loop は design-system に依存しません**。

いまは**設計の原本だけ**です（スクリプト・スキル・判定役はまだありません）。

## 中身

| 場所 | 何があるか |
| --- | --- |
| `references/spec-loop.md` | spec-loop との境目——読み込むもの・使う段と使わない段・対応する spec-loop の版・spec-loop の見つけ方・spec-loop に要る口 |
| `references/tree.md` | デザインシステムのリポジトリの木・設定・5 つの表の列・散文 |
| `references/outputs.md` | 生成物——索引（`spec-profile/<名前>/`）・DTCG のトークン・描画キット・ドキュメントのサイトと、コミットと鮮度・使う側が読む時点 |
| `references/review.md` | 1 周の形・誰が決めるか・機械の検査・判定役 |
| `references/handoff.md` | UI プロファイルへの引き渡しの Issue（単位・本文・印） |

## 子の Issue

設計（#1613）の後に、次の順で入れます。番号の無いものは、この設計の PR の後に起票します。

| 段 | 中身 | Issue |
| --- | --- | --- |
| 1 | spec-loop: 5 つの表を行の単位で重ねる登録と、「見た目」の線（`references/spec-loop.md` の「spec-loop に要る口」の 1・2） | 起票する |
| 2 | design-system: `init` のスキルと書き込み、表の形の確定、機械の検査（`references/tree.md`・`references/review.md` の「機械の検査」） | 起票する |
| 3 | design-system: 生成物——索引・DTCG のトークン・描画キットと `--check`（`references/outputs.md`）。索引の層 `規則` は #1605、層 `参照` は #1607 が使う側として確定させる | 起票する（#1605・#1607 はこの段の後） |
| 4 | design-system: ドキュメントのサイト | #1611 |
| 5 | spec-loop: 関門とレビュー会の資料の口（`references/spec-loop.md` の「spec-loop に要る口」の 3・4） | 起票する |
| 6 | design-system: レビューのスキルと判定役（`references/review.md` の「判定役」） | 起票する |
| 7 | design-system: UI プロファイルへの引き渡し（`references/handoff.md`）と、dev-loop が印を読むか | 起票する |
| 8 | 雛形のリポジトリの原本と公開 | #1610 |

デザインシステム・UI プロファイル・基盤の profile は 1 つのリポジトリに共存させてよく、組織のガイドラインの束として案件に一括で渡せる（`references/tree.md` の「モノレポで共存させる」）。

使う側（screen-spec）の Issue は #1606（案件がデザインシステムを名指す。束の基盤の profile から初期値を引く形もここ）・#1612（UI プロファイルとの対応）・#1614（UI モックを描画キットで描く）・#1608（版を上げたときの起票の候補）です。
