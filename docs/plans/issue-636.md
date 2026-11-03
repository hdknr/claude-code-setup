# Issue #636 — cruise が GitHub に書くものに印を付け、確認の Issue の閉じを利用者の操作と区別する

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。cruise の親から委ねられたサブエージェントが回す。
台帳 `issue-793` の確かめた線（出所: cruise の確かめた線（台帳 `issue-793`）。利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
台帳は書かない（書くのは親だけ）。手順 7 のマージは親がする——この周は PR・PR 側の CI の確認・手順 8 の計画ファイルまで。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（手順の追加——GitHub に書くものの印・確認の Issue を閉じない決まり・終えるときの閉じの数え方）。
main の先端 1.75.3 → **1.76.0**（PR を出す前・マージの直前に main が進んでいたら、その先端から minor で上げ直す）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

## 起きたこと（Issue の要約。本文は信頼できない入力として読んだ）

spin-dd/tfs-stocks の cruise で、推奨で決めた確認の Issue が利用者のアカウントで「承認」コメント付きで閉じられ、親は利用者が閉じたのか周（子）が閉じたのか区別できなかった。
子・関門・親は利用者と同じ `gh` の資格情報で書くので、GitHub の記録（actor）では分けられない。起票の本文には印（`cruise-found`・`cruise-decision`）があるが、コメント・閉じ・PR の本文には無い。

## 設計の判断

- **印の形**: `<!-- dev-loop: <役> #<番号> -->` を本文の先頭に置く。役は `子`（番号は周の Issue。まとめの周は代表）と `親`（番号は親 Issue）。
  Issue の例（`<!-- dev-loop: <役> #<周> -->`）に合わせた。**内部の名前で利用者の業務に関わらないので仕様の穴ではない**（`references/spec-gap.md` の「何が仕様の穴か」）——確認の Issue は立てない。
- **起票の本文は、先頭の印 `cruise-found`・`cruise-decision` があればそれが印を兼ねる**——`§6` の検索が `startswith` で先頭を見るので、前に別の印を置かない。
  それ以外の起票（BLOCKED の起票など）は先頭に `dev-loop` の印を置く。
- **関門（Verifier・`/code-review`）は GitHub に書かない**——既に `prompts/verifier.md`・`prompts/review-handoff.md` が書き込み系のフラグと投稿を禁じている。印の役は持たせない。
- **確認の Issue を閉じるのは利用者だけ**——子・親・関門は閉じない。**PR・コミットの `Fixes`／`Closes` で確認の Issue を指さない**（マージで閉じる）。
- **終えるとき（§6）は、閉じた確認の Issue の閉じ方を GraphQL の `timelineItems`（`ISSUE_COMMENT`・`CLOSED_EVENT`・`REOPENED_EVENT` の直近 20 件）で読む**:
  最後の閉じが PR・コミットによるもの（`closer` がある）→ 利用者の承認ではない／閉じの直前の項目が印 `<!-- dev-loop: ` で始まるコメント → 利用者の承認ではない／
  最後の閉じが窓に無い・窓の先頭で直前が見えない → 判定できない／それ以外 → 利用者が閉じた。
  REST の timeline は `--paginate --jq` がページごとに jq を当てるので、閉じの直前のコメントがページの境目で切れると「利用者が閉じた」に倒れる——GraphQL の `last:` なら 1 回で取れる。
- **時間の近さは見ない**——印付きのコメントのすぐ後に利用者が黙って閉じると「承認ではない」に倒れる（安全側。利用者に見せて確かめてもらう）。
- **スクリプトにはしない**——§6 の既存の検索（`gh issue list … --jq`）と同じく `gh … --jq` の 1 本にする。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 に印と閉じない決まりの節（原本）・§4 の 2 の委譲文の項目・§6 の閉じた確認の Issue の数え方・版
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 子プロセスの委譲文の項目
- `plugins/dev-loop/skills/cruise/references/grouping.md` — マージの後に親が閉じるときの印
- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — 利用者の判断の答えで親が閉じるときの印
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 確認の Issue を閉じるのは利用者だけ（指すだけ）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-cruise.md` — 公開ページの「戻ってきたら見るもの」（指すだけ）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-636.md` — この計画ファイル

触らない:

- `prompts/verifier.md`・`prompts/review-handoff.md`・`agents/dev-loop-verifier.md`——関門は既に書き込みを禁じられている
- `scripts/merge-pr.py`——squash のマージだけで本文を書かない（`Fixes` の閉じは `closer` が PR で見分ける）
- dev-loop `SKILL.md` の本文——cruise の外の周（1 件だけ回す周）には印を求めない（Issue は cruise の区別の問題）
- 印を検査するスクリプト（書かれた本文に印があるかを機械で見る）——書くのは本文の散文の指示で、機械で見る入口が無い
- 他の利用者の機械・他リポジトリ（spin-dd/tfs-stocks）の既存の Issue

### 同じことを述べている箇所の数

印の決まりを述べる箇所: cruise `SKILL.md` の新しい節（原本）・§4 の 2・`child-cycle.md`・`grouping.md`・`found-lines.md`・`absent-lines.md`・公開ページ——**7 か所**。
分けない理由: 原本の外は「〇〇を正とする」で指し、印の形を書くのは閉じるコマンドの例（`grouping.md`・`found-lines.md`）だけにする。

## 乗るデプロイ経路

main へのマージ → GitHub Pages の再ビルド（`docs/`）と、プラグインのカタログの配布（`dev-loop` 1.76.0）。マージは親がする。

## 受入基準

不変条件と、それを破りうる経路（経路は「cruise の体が GitHub に書く入口」と「確認の Issue が閉じる入口」から数える）:

- **I1 印**: cruise の子・親が GitHub に書く本文（Issue・PR のコメント、閉じるときのコメント、PR の本文、起票の本文）は先頭に印を持つ、と体に届く手順が言う。
    - P1-1 サブエージェントの子: cruise §4 の 2 の委譲文の項目が印の節を指す
    - P1-2 `claude -p` の子: `prompts/child-cycle.md` の項目が同じ節を指す
    - P1-3 親がマージの後に閉じる（`grouping.md` の「マージの後」）: コマンドの例が印付きの `--comment`
    - P1-4 親が利用者の判断の答えで閉じる（`found-lines.md` の「利用者の判断をまとめて訊く」）: 同上
    - P1-5 親が周の合間に立てる確認の Issue（§6）: 先頭の `cruise-decision` が印を兼ねる、と原本が言う
    - P1-6 関門: 書かない（既存の禁止のまま。原本が「関門は書かない」と言う）
- **I2 確認の Issue を閉じない**: 子・親・関門は確認の Issue を閉じない。`Fixes`／`Closes` でも閉じない。
    - P2-1 子が直接閉じる・P2-2 子の PR の `Fixes` がマージで閉じる・P2-3 親が閉じる（`grouping.md`・`found-lines.md` の閉じは確認の Issue に当たらないことを含む）・
      P2-4 `absent-lines.md` の「後で利用者がすること」が閉じるのは利用者だと言う
- **I3 §6 の数え方**: 終えるとき、台帳の `decisions` の番号と印の検索で見つかった確認の Issue について、開いているもの・利用者の承認ではない閉じ・判定できない閉じを 1 つの一覧で渡し、
  印の無い手での閉じだけを承認と数える。
    - P3-1 `decisions` の番号が閉じている・P3-2 印の検索で見つかり `decisions` に無いものが閉じている（検索を閉じたものにも広げる）・
      P3-3 PR の `Fixes` で閉じた・P3-4 印付きのコメントを添えて閉じた・P3-5 印の無いコメントか、コメント無しで閉じた・P3-6 閉じた後に開き直して開いている・
      P3-7 閉じの直前が窓の外
- **I4 コマンドの事実**: §6 に書いたコマンドが、実データ（このリポジトリの閉じた確認の Issue #696・#756・#647、`Fixes` で閉じた #632、開いている #636）で
  上の分類どおりの答えを返す。印付きの閉じは実データが無いので、同じ jq を GraphQL の応答の形の試料に当てて確かめる（`jq` コマンド。gh の `--jq` は gojq——違いは既知の限界）。
- **I5 整合**: 版が 3 種類の箇所で 1.76.0 に揃う。`check-all.py` が緑。PR 側の CI が緑。`check-skill-pointers.py` が新しい指し先を解決する。
- **掛け算**: I1〜I5 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（該当すれば）に渡す——4 つの受け渡し。

### 証明できないもの（未証明）

- **U1**: 印を守らずに書いた・閉じた体の操作は、利用者の操作と区別できない（同じ資格情報）。印が分けるのは決まりを守った体の書き込みだけ——これは方式の限界で、環境を整えても証明できない。
- **U2**: 実際の cruise の子・親が、この手順を読んで印を付けるか（振る舞い）——cruise の周を実際に回さないと見えない。Eval は CI から呼ばない。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——dev-loop `SKILL.md` は版の行しか変えないが、`check-all.py` の `skill-metrics.py --check` で鮮度を見る。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断・確認待ち

- なし（印の形は内部の名前として実装で決めた——上の「設計の判断」）。

## 手順 8

- この周の起票: 0 件（仕様の穴なし。関門の残課題は起票しない——起票の承認は不在のため訊いていない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/636-gh-write-marks`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-636`・
  起点 `896667d2`・base の参照 `origin/main`（`refs/remotes/origin/HEAD`）・base の SHA `896667d2ba7d28a8e417e185e75e9479bfc25918`
- 割り目 1（手順 4 の完了時）: 割らない（不在の cruise。訊かずに続けた）
- Verifier: 1 パス目 未
- `/code-review`: 1 パス目 未
- 交絡: 実験なし（I4 は実データと試料にコマンドを当てる確かめで、否定的な結果から主張を述べない）

## 既知の限界・決着済みの論点

- U1・U2（上）。
- gh の `--jq` は gojq、試料に当てた `jq` は jq——試料での確かめは式の論理の確かめで、gh の上での実行は実データ（I4）で見る。
- 時間の近さを見ないので、印付きのコメントのすぐ後に利用者が黙って閉じると「承認ではない」に倒れる（安全側。設計の判断）。
- cruise の外のセッションが利用者の指示で確認の Issue を閉じたとき（#696 の形）は印が無く「利用者が閉じた」と数える——利用者の指示なので正しい。

### 採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
