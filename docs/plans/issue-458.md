# Issue #458 — cruise: 周ごとに訊く判断を、台帳を作るときに 1 回だけ確かめて各周へ渡す

方針は Issue のコメント 3 件で利用者と決めた（2026-10-27）:

- 線（動作パラメータ）は**親 Issue に書いて直せる**ようにし、**起動時の確認を経た値だけ**を台帳に残す（出所は「利用者の確認」で、Issue 本文ではない）
- 推奨で決めた `仕様の穴` は、印つきの `要確認` Issue にして台帳から追え、後で承認（閉じる）・修正（親 Issue に足す）できる
- **利用者が居る周でも**、確かめた `仕様の穴 = 推奨で決めて起票` があれば推奨で進めてよい

直す線: **既定**（出所: 手順 3 の回答。2026-10-27・AskUserQuestion）

スキルの版: 読み込まれていたのは 1.37.0（キャッシュ）。この周はリポジトリの 1.57.1 の `SKILL.md` に従う（利用者に申告済み）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/parent-issue.py` — `cruise: 項目 = 値` の行を読む・指紋に含める・`apply` で台帳に残す・既存台帳との違いを名指し・「チェックリストが無い」と「全部済み」を分ける
- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — 台帳に確かめた線（`lines`）を持つ・`lines` コマンド・Issue ごとの `decisions`（要確認 Issue の番号）
- `scripts/test-parent-issue.py` — 回帰テスト（変異を含む）
- `scripts/test-ledger.py` — 同上
- `plugins/dev-loop/skills/cruise/SKILL.md` — §1〜§3・§6
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 3 の直す線の読み順・待ち時間の節の不在の線の 1 文・版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 読む条件・出所・`仕様の穴` の印と承認／修正・居る周で効く条件
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 台帳に確かめた線を置ける（分担）
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 末尾の指し先
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.57.1 → 1.58.0。能力の追加なので minor）・description の末尾
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-cruise.md` — 親 Issue に線を書く例と、戻ってきたら見るもの
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く）
- `CLAUDE.md` — cruise の行に線の一文（実装中に足した。構成の説明が古くなるため）
- `docs/plans/issue-458.md` — この計画

触らない:

- `.claude/dev-loop.md` の宣言の書き方（今のまま有効）
- `fix-line.md` の線の中身（読み順だけを `SKILL.md` 手順 3 に足す）
- 親 Issue のチェックボックスの更新（cruise は書き換えない、を崩さない）
- `本番反映` を広げる手段（どこにも作らない）
- README・`docs/plugins/index.md`（入口の 1 行は変わらない）

### 同じことを述べている箇所の数

- 「線の項目と値の一覧」: `absent-lines.md`（意味の原本）・`fix-line.md`（直す線）・`ledger.py`（コードの表）・公開ページ（例）——4 箇所。
  分けない理由: 意味は references、受け付ける値はコード。**コードの表が references の表と一致することをテストで突き合わせる**（`test-ledger.py`）。`parent-issue.py` は `ledger.py` の表を読み込む（写しを作らない）。
- 「線の出所と読み順（台帳 → `.claude/dev-loop.md` → 既定／訊く）」: `absent-lines.md`（原本）・`SKILL.md` 手順 3（直す線）・`cruise/SKILL.md`・`ledger.md`——4 箇所。原本以外は指すだけにする。
- 「要確認 Issue の印・承認と修正」: `absent-lines.md`（原本）・`cruise/SKILL.md` §6・公開ページ——3 箇所。

## 乗るデプロイ経路

プラグインの版を上げて配布。`docs/` は main への push で Pages に載る。

## 設計

- 親 Issue の行 `cruise: <項目> = <値>`（チェックリストでない行。コードフェンス・HTML コメント・引用の中は読まない）。
  - 項目と値は `ledger.py` の `LINES`（`直す線`・`仕様の穴`・`実機確認`・`マージ`）。
  - `本番反映` の行は**無視して**、`show` に「無視した行」として出す（広げられない）。
  - 一覧に無い項目・値、同じ項目が 2 行 → 拒む（3）。確かめる場面なので、誤記は止めて直させる。
- `show` は回す Issue に加えて線を出す。書いていない項目は「書いていない（`.claude/dev-loop.md` の宣言、無ければ既定）」と出す。指紋に線を含める。
- `apply` は台帳を作ったあと `ledger.py lines issue-<親> 項目=値 … --source "利用者の確認（親 Issue #<親>・指紋 <d>）"`。台帳が既に在れば、本文の線が台帳と違うことも名指しする（台帳は変えない）。
- `ledger.py`: 台帳の上位に任意の `lines`（`{"values": {...}, "source": "...", "updated": "..."}`）。無い台帳は今までどおり読める。`lines` コマンドは値を置き換え（指定しない項目は消える）、`--source` 必須。Issue ごとに `decisions`（要確認 Issue の番号のカンマ区切り）。
- 各周の読み順: **台帳の確かめた値 → `.claude/dev-loop.md` → 既定（直す線は訊く）**。`実機確認`・`マージ` は `--absent` の周だけに効く。`仕様の穴` は居る周でも効く（spec-loop の Issue には効かない・推せなければ居る周は訊く）。

## verify の受入基準

不変条件と経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | 線を広げる出所は利用者だけ——本文の線は確かめた後にしか台帳に入らない | `apply` に古い指紋／確かめた後の本文の書き換え／再開時に本文の線が変わった／子の報告・Issue コメント | 指紋に線を含める（テスト）／再開は名指しだけで台帳を変えない（テスト）／規範で出所を台帳と `.claude/dev-loop.md` と利用者の直接の指示に限る |
| B | `本番反映` は広げられない | 親 Issue の行／`ledger.py lines` | 無視して表示（テスト）／`lines` が拒む（テスト） |
| C | 誤記は止まる側 | 一覧に無い項目・値・重複／台帳の `lines` を手で崩す | `show`・`apply` が 3（テスト）／`load` が 4（テスト） |
| D | 線を持たない既存の台帳を壊さない | `load`・`set`・`show` | テスト |
| E | 読み順と効く周が規範で 1 箇所に決まり、他は指す | `SKILL.md` 手順 3・`absent-lines.md`・`spec-gap.md`・`cruise/SKILL.md`・`ledger.md` | 原本は `absent-lines.md`。他は指し先（`check-skill-pointers.py`） |
| F | 推奨で決めた仕様の穴は後で承認・修正できる | 印・台帳の `decisions`・cruise §6 | `ledger.py set decisions=` が番号以外を拒む（テスト）／§6 で開いた要確認を渡し「済んだ」と言わない |
| G | チェックリストが無い親 Issue と、全部済んだ親 Issue を分けて言う | `show`・`apply` | 文言が違う（テスト） |
| H | コードの線の表と references の表が一致する | `LINES` の改変・表の改変 | `test-ledger.py` が突き合わせる |
| I | 版 3 箇所一致・生成ブロックが新鮮・歯止め全部緑 | | `check-all.py` |

掛け算: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（4 つの受け渡し）。

未証明:

- **実際に cruise を回して、居る周で訊かずに推奨で進むか**（モデルの振る舞い）——この周では Eval を作らない。人間レビューに回す。

生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）。図は触らない。

## 未解決の判断

なし（3 件のコメントで決めた）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/458-cruise-confirmed-lines`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-458`・起点 `4f4b6f9`・base 参照 `origin/main` → `4f4b6f90255309fb2ae5be05ad49ae252076ec6b`
- 実装: 済み（コミット `bbed533` を amend したもの。`check-all.py` は 51/51 のうち 2 本が落ち、指し先と件数の行を直して個別に緑を確認——全体の回し直しは関門の前に行う）
- 関門: 未着手（次は手順 5 の Verifier 1 パス目と手順 6 の `/code-review` 1 パス目）
- 反証: なし（まだ関門に当てていない）
- 交絡: 実験なし
- 割り目（手順 4）: 利用者が「ここで割る」を選んだ（2026-10-27・AskUserQuestion）。再開は手順 5 から

## 起票

- この周の起票: 0 件（周の途中。手順 8 で確かめる）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 確かめた線と `.claude/dev-loop.md` の優先 | 台帳の確かめた値が先 | どちらも利用者の出所で、台帳のほうがこの cruise に限った新しい確認。狭める向きの指定も効かせるため |
| 誤記の扱い（`.claude/dev-loop.md` は既定に倒すが、親 Issue は拒む） | 拒む | 確かめる場面があるので、黙って既定にするより直させるほうが利用者に見える |
| `実機確認`・`マージ` を居る周に効かせるか | 効かせない | 利用者が決めたのは `仕様の穴` だけ。居るならマージは人が行う |
