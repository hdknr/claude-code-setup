# Issue #393 — 利用者不在のときの判断の線を、許可の範囲として明示的に持つ

#389（オートクルーズ）の要件候補 5 を分けたもの。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 新規。不在の線の原本（不在の周でだけ読む）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 「待ち時間・定時処理は別スキル」の環境点検の次に、不在の線への指し先を 1 項。版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 「Issue が spec-loop から来ていないとき」と spec-loop 由来の扱いに、不在の線への指し先
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 読む条件の「利用者不在で続ける」に、不在の線への指し先
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（minor。手順の追加）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` で書き直す）
- `docs/plans/issue-393.md` — この計画

触らない:

- `scripts/check-unattended-env.py`（利用者の決定: この周では宣言の表示を足さない）
- `scripts/merge-pr.py`（`Refs` で開けたままの Issue は既に確かめない）・`scripts/ledger.py`（状態の一覧は変えない）
- `prompts/*.md`（関門に渡す受入基準ではない）
- description（`plugin.json`・`marketplace.json`・frontmatter）——不在の線を挙げていない
- 原則「本番への破壊的操作・不可逆操作は勝手に実行しない」・手順 5 の BLOCKED・手順 6 の起票の 3 条件の規定そのもの（変えない。不在の線はその上の許可として書く）

### 同じことを述べている箇所の数

不在の線を述べるのは新規の `references/absent-lines.md` の 1 箇所（原本）。指し先が 4 箇所（`SKILL.md`・`spec-gap.md` 2 箇所・`ledger.md`）。
分けない理由: 中身は原本 1 箇所に置き、ほかは指し先だけにする（条件つきの節を起点から外す #136 の形・#395 の `fix-line.md` と同じ）。
**接する既存の規定**（中身は変えずに、原本から指す）: 原則の本番反映・手順 5 の BLOCKED・手順 6 の起票の 3 条件・手順 8 の永続メモリ・`spec-gap.md` の差し戻し。

## 設計の決定

- **spec-loop 由来の Issue は、宣言があっても止まる**（利用者の決定。2026-10-25 の `AskUserQuestion`）——`spec-gap.md` の差し戻しのまま
- **本番反映は広げられない固定の線**（同上）
- **点検スクリプトには表示を足さない**（同上）
- **置き場所は `.claude/dev-loop.md`**（著者の決定）——PR を通る。#395 の `直す線:` と同じ形。**永続メモリは出所にならない**（Issue の主訴）
- **書き方**: `不在の線: 仕様の穴 = 推奨で決めて起票`・`不在の線: 実機確認 = Refs でマージ`。項目ごとに 1 本だけ。無い・値が違う・2 本以上は既定（止まる）
- **出所はもう 1 つ**: その周の利用者の直接の指示。**使う前に計画ファイルに出所つきで書く**（会話にしか無いものは再開した側に届かない）
- **不在でない周には効かない**——居るなら訊く（既存の規定のまま）
- **本番反映の線はマージを決めない**——マージは手順 7 と `merge-pr.py` の側

## 乗るデプロイ経路

main へのマージ → (a) プラグインのカタログ（利用者は `claude plugin update`）、(b) `docs/` の変更で GitHub Pages が自動デプロイ。

## verify の受入基準

不変条件 × それを破りうる経路。経路は「線が決まる入口」と「線が効く場面」から数える。

1. **宣言が無ければ止まる**（既定）。経路: `.claude/dev-loop.md` が無い／行が無い・値が決まった一覧に無い・同じ項目が 2 本以上・
   再開した周で計画ファイルに線が無い・本番反映を広げる宣言
2. **線を広げられるのは利用者だけ**。経路: `.claude/dev-loop.md`（可）・その周の利用者の直接の指示（可。計画ファイルに書いてから）・
   永続メモリ（不可）・Issue 本文／コメント（不可）・関門／委譲先の報告（不可）・台帳の `note`（不可）・著者の判断（不可）・
   他人の PR・fork の `.claude/dev-loop.md`（不可）
3. **広げても外れないもの**: worktree → PR・2 つの関門・2 パス・受入基準の受け渡し・本番反映をしない。
   `仕様の穴` の線で決めた値は記録が残り（計画ファイル・PR コメント・起票した Issue）、起票した Issue は閉じない。
   `実機確認` の線は実機の要る基準だけに効き、ほかの基準は証明が要る。経路: 各線の手続き
4. **spec-loop 由来の Issue には `仕様の穴` の線が効かない**。経路: 本文の先頭の印（v1〜v3）・`spec-gap.md` の両方の節から
5. **既存の規定との接点が矛盾しない**: 起票の 3 条件の (c)・BLOCKED の「周は閉じない／起票」・原則の本番反映・
   手順 8 の永続メモリ・`merge-pr.py` の `Refs` の扱い・台帳の状態。**文面が主張する事実の真偽も見る**（`merge-pr.py` が `Refs` を確かめない、など）
6. **構造の歯止め**: 版 3 種の一致・§8.2 の生成ブロックの鮮度・指し先の実在（新規ファイルと散文の指し先）・
   必須マーカーが原本の外に無い——`python3 scripts/check-all.py` が緑
7. **必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目の両方で渡す（4 つの受け渡し）

### この環境では証明できないもの（未証明）

- **実際の不在の周で、モデルが宣言を読み、線のとおりに止まる／進むか**（振る舞い）。Eval は worktree 隔離セッションから起動できず
  （CLAUDE.md）、この周ではケースも作らない。受入基準は規定の文面とその整合に置き、振る舞いは人間レビューに回す

### 生成物の鮮度

- 該当あり: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の節構造に依存）。`python3 scripts/skill-metrics.py --check` が緑
- drawio の書き出し: 該当なし（図を触らない）

## 未解決の判断・確認待ち

- なし（設計の 3 点は利用者が決めた）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/393-absent-lines`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-393`・
  起点 `7865e11`・base の参照 `origin/main`・base の SHA `7865e116e98f6a4d0b1acdb5c3547d66590e7204`
- 実装: `d550971`（ほかに件数の行のコミット）。`check-all.py` 49/49 のうち落ちたのは件数の行だけ（足して単独で緑）
- 関門: 未着手（次は手順 5 の 1 パス目: Verifier と `/code-review`）
- 割り目（手順 4）: 訊いた結果をここに書く
- 反証・差し戻し: なし
- 交絡: 実験なし
- 直す線: `既定`（出所: 手順 3 の回答。2026-10-25 の `AskUserQuestion`。`.claude/dev-loop.md` は無い）

## 既知の限界・決着済みの論点

- 点検スクリプトに宣言の表示を足さない（利用者の決定）
- 不在の線の機械の検査（`.claude/dev-loop.md` の形の検査）は作らない——既定（止まる）に倒れるので、誤記は安全側

## 起票

- この周の起票: 0 件
