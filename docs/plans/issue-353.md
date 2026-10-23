# Issue #353 — spec-loop: Q&A 表の内部の層の見分け方を 1 か所にする（#343・#344・#345 のまとめ）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-qa-csv.py` — 番号から層を決める関数 `is_internal_number`（`INTERNAL_NUMBER` の全一致）を置く（**層の判定の原本**。A）
- `plugins/spec-loop/scripts/merge-versions.py` — `removed.csv` の Q&A の行の消し先を**番号**で決める（キーの有無をやめる。A）
- `plugins/spec-loop/scripts/diff-versions.py` — Q&A の差分を層で 2 つの種類に分ける（`Q&A` と `Q&A（内部）`）。分けるのは番号（`is_internal_number`）。削除の理由の引き当ては `removed.csv` の種類 `Q&A` で（B）
- `plugins/spec-loop/scripts/build-proposal.py` — `drop_internal` の判定を `is_internal_number` に。比較の節は共有の種類だけ（`diffs.SHARED_KINDS`）
- `plugins/spec-loop/scripts/scaffold.py` — `INTERNAL_QA_PATH` は `merge-versions.py` の定数を読む（写しをやめる）。`D-` の判定は `is_internal_number`
- `plugins/spec-loop/scripts/check-signoff.py` — `D-` の判定 2 箇所を `is_internal_number` に
- `plugins/spec-loop/references/versions.md` — 「版の差分」に層の分け方を書く
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 差分の読み方（利用者向けは `Q&A` の節）。版の 2 行
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同上（1 パス目の指摘で読み方を足した）
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 同上（同）
- `plugins/spec-loop/skills/proposal/SKILL.md` — 版の 2 行だけ（全 `SKILL.md` に版を書く規則。1 パス目の Verifier の反証で範囲に足した）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 同上
- `plugins/spec-loop/README.md` — 該当すれば
- `scripts/test-check-qa-csv.py` — `is_internal_number` の試料と変異。移す手順への指し先（`check-qa-csv.py` の `MIGRATION` と MkDocs のフックの `QA_MIGRATION`）を `references/tree.md` の見出しと突き合わせる（C）
- `scripts/test-merge-versions.py` — 層の判定を外す・入れ替える変異（E）
- `scripts/test-diff-versions.py` — 同上。期待値の更新（B）
- `scripts/test-build-proposal.py` — 同上。v1 に内部の表を置く試料（D）
- `scripts/test-scaffold.py` — 同上
- `scripts/test-check-signoff.py` — 同上
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.18.1 → 0.19.0。差分の出力の形が変わる＝読む側に効くので minor。0.x）
- `.claude-plugin/marketplace.json` — 同上
- `CLAUDE.md` — `diff-versions.py` の説明（層を分ける）
- `docs/plans/issue-353.md` — この計画

触らない:

- 層の決まりそのもの（`references/qa-csv.md` の「層」）と内部の表の置き場所
- `check-qa-csv.py` の「ファイルの名前で層を決める」（表 1 枚を検査するときの層。番号の層と食い違わないことは `merge` の `read_qa` が検査で保証している）
- `references/tree.md` の見出し（C はテストを足すだけ）
- `check-spec-exit.py`・`qa-to-pptx.py`（ファイルの名前で層を決める側。番号を見ていない）

### 同じことを述べている箇所の数

- 「番号で層を決める」の実装: いま `check-signoff.py` 2・`build-proposal.py` 1・`scaffold.py` 1・`merge-versions.py`（キーの有無）1 —— **5 箇所 → 関数 1 つ**。
- 内部の表のパス: `merge-versions.py`・`scaffold.py` の 2 箇所 → 1。
- 差分の Q&A の層: 原本 `versions.md` の「版の差分」、読む側の `req-loop`・`spec-review`・`feasibility` の `SKILL.md`、`CLAUDE.md` —— 5 箇所。
- 移す手順への指し先: `check-qa-csv.py`・フック（定数と docstring）・`tree.md` 本文・`qa-csv.md` —— 5 箇所（テストで突き合わせるのは定数の 2 つ）。
- 分けない理由: Issue のとおり、3 件とも「層の決め方を 1 か所にする」で、別々に直すと規則がまた割れる。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/plans/` は main への push で Pages に載る。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 番号から層を決める式は `check-qa-csv.py` の `is_internal_number` の 1 つだけ。`merge-versions`・`diff-versions`・`scaffold`・`build-proposal`・`check-signoff` に `INTERNAL_NUMBER.fullmatch`・`startswith("D-")`・キーの有無による判定が残らない | 各スクリプトのソース | `grep` |
| A2 | `merge-versions` の `removed.csv` の Q&A の行は番号で消し先が決まる（`D-` → 内部の表、それ以外 → 共有の表） | `Whole.apply` | `is_internal_number` |
| A3 | `scaffold.py` は内部の表のパスを `merge-versions.py` の `INTERNAL_QA_PATH` から読む（写しが無い） | `scaffold.py` の定数 | ソースを見る |
| A4 | 振る舞いは変えない（`merge`・`scaffold`・`check-signoff`・`build-proposal` の既存の全試料が緑） | 既存の全試料 | `check-all.py` |
| B1 | `diff-versions` の出力は Q&A を `Q&A`（共有。`Q-`）と `Q&A（内部）`（`D-`）の 2 つの種類に分け、`D-` の行が `Q&A` の節に出ない・`Q-` の行が内部の節に出ない | `compare`・`render` | 試料（全行の突き合わせ） |
| B2 | 内部の行の削除にも `removed.csv` の理由が付く（`removed.csv` の種類は `Q&A` のまま） | 理由の引き当て | 試料 |
| B3 | 提案書（`build-proposal`）の比較の節・件数の表に `Q&A（内部）` が出ない（決裁者に内部の層を見せない） | `render`（提案書） | 既存試料＋文字列の不在 |
| B4 | どれにしたか（種類を分けた）と、読む側（`req-loop`・`spec-review`・`feasibility`・提案書）への影響が `versions.md`・`SKILL.md` に書かれ、事実と一致する | 文書 | 目視＋試料の出力 |
| C1 | `MIGRATION`（`check-qa-csv.py`）と `QA_MIGRATION`（フック）が指す `references/tree.md` の「X」の X が `tree.md` の見出しにある | テスト | `test-check-qa-csv.py` |
| C2 | 見出しを改名する変異で C1 の検査が赤になる（陽性対照: 改名前は緑） | テスト | 変異 |
| D1 | v1 に内部の表（`暫定反映` の `D-` 行）を置き v2 を重ねる試料で、提案書が作られる | `drop_internal` | 試料 |
| D2 | `drop_internal` を最後の版だけに絞る変異（`[-1:]`）が D1 で赤（陽性対照: 変異なしで緑） | `MUTATIONS` | 変異 |
| E | 層の判定を外す（常に共有／常に内部）・入れ替える変異で、`check-qa-csv`・`merge-versions`・`diff-versions`・`scaffold`・`build-proposal`・`check-signoff` の各テストが赤 | 各呼び出し箇所と関数本体 | 各テストの `MUTATIONS` |
| V | 版が 3 種類で揃い、歯止めが全部緑 | bump 漏れ | `python3 scripts/check-all.py` |

組み合わせ: A × B（差分の層分けも同じ関数で決める——B1 は A1 の読み手）。A × E（関数本体の変異と呼び出し箇所の変異の両方）。
B × D（提案書は内部を外したうえで、共有の種類だけ描く——`drop_internal` が漏れても `Q&A（内部）` の節は出ない。漏れの検出は D1）。

**この環境では証明できないもの（未証明）**: なし（すべて一時ディレクトリの試料で当てられる）。

生成物: 図・`SKILL.md` の測定値（dev-loop のみ）に関係しない。**生成物なし**。

## 未解決の判断・確認待ち

- なし（B は「種類を分ける」を選んだ。理由: 読む側が節単位で読み飛ばせ、件数も層ごとに出る。印を付ける案は件数が混ざり、引数の案は既定の出力が混ざったまま残る）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/353-qa-layer-one-place`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-353`・
  起点 `4e498b2`・base の参照 `origin/main`・base の SHA `4e498b28d799d41a8774386b17af8e2f3108b802`
- 実装: 済み（手順 4）。`check-all.py` 44/44 緑。`test-check-qa-csv` 60/47・`test-diff-versions` 13/15・`test-merge-versions` 57/53・`test-build-proposal` 40/37
- 割り目（手順 4 の後）: 提案した → 人間の選択は「ここで割る」（2026-10-23）。再開は手順 5（Verifier 1 パス目と `/code-review` 1 パス目）から
- 関門: 1 パス目 済み（2026-10-23。Verifier = `dev-loop:dev-loop-verifier`・sonnet → 反証 1 件（V）。`/code-review` high → 指摘 7 件）。採否は下の表——直す 3 件・残課題 5 件。指摘対応は済み。残るのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目
- 割り目（手順 6 の 2 パス目の前）: 提案した → 人間の選択は「ここで割る」（2026-10-23）。指摘対応のコミットは `930cfed`（`check-all.py` 44/44 緑）。再開は 2 パス目から——**手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方が残っている**。base は周の base のまま（`4e498b2…`）
- 関門 2 パス目: 起動（2026-10-23。Verifier = `dev-loop:dev-loop-verifier`・sonnet、`/code-review` high。base `4e498b2…`）。Verifier 2 パス目: 済み——反証 1 件（V: main が #370 で spec-loop 0.19.0 に先着し `check-version-bump.py origin/main` が赤。親が再現を確認）。`/code-review` 2 パス目: **結果待ち——済んでいない**
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `1c02161484ffbf3a27809a56953c92b9f8aac729`
- 交絡: 実験なし（変異テストのみ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 指し先の見出しの照合は完全一致か | 完全一致、または ` — ` の前の部分（「層 — 共有の表と内部の表」を「層」で指す）を見出しの名前とする | フックの docstring が `qa-csv.md` の「層」を指しており、実在する見出しの名前の部分。照合の範囲は本体の `MIGRATION` とフックのソース全体 |
| `build-proposal` の変異「内部の Q&A も比較に載せる」の殺し役 | 「内部の表の違反でも比較を作る」に替えた | 共有の種類だけを描くようになり（B3）、`drop_internal` を外しても `Q&A（内部）` は提案書に出ない。外すことが効くのは内部の表の違反のほう |
| `check-qa-csv.py` の「ファイルの名前で層を決める」 | 残す（範囲外） | 表 1 枚を検査するときの層。番号の層と食い違わないことは `merge` の `read_qa` が検査で保証する |

### 1 パス目の指摘の採否

| 関門 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| `/code-review` | feasibility・spec-review の `SKILL.md` に層で分かれた差分の読み方が無い | 示せる（`git diff 4e498b2` で両ファイルの差分が版の 2 行だけ） | B4 | 直す（両 `SKILL.md` に 1 項） |
| `/code-review` | `build-proposal` だけが `removed.csv` の対象を `strip()` してから層を決める | 示せない（`build-proposal` は照合が 0 のときだけ動き、前に空白のある `D-` 行は照合（`check-signoff`）が 2 を返すので提案書の経路に届かない。食い違いは #353 以前から） | 無し | 残課題 |
| `/code-review` | `scaffold.py` の `QA_NO` が番号の形式（`Q-`・`D-`）の写し | 示せない（形式を変えたときの話） | 無し（A1 は層の判定の式。番号の形式は範囲外） | 残課題 |
| `/code-review` | `scaffold.py` の `QA_PATH` が `merge-versions.py` の写し | 示せない（パスを変えたときの話） | 無し（A3 は内部の表のパス） | 残課題 |
| `/code-review` | `diff-versions.py` の `qa_layers` が表で分けるのと同値（等価変異が素通り） | 示せる（変異 `return whole.qa, whole.internal` は緑になるはず。`read_qa` が表と番号の一致を保証） | 無し（B1 の出力の分け方は守られている。番号で分けるのは A1 の読み手として計画で決めたこと） | 残課題 |
| `/code-review` | `test-check-qa-csv.py` の変異の件数が 4c の変異を数えない | 示せる（4c は `check` に出るが「変異 N 件」に入らない） | 無し | 残課題 |
| `/code-review` | フックの定数 `QA_MIGRATION` を別のファイルに向けても 4c が緑 | 示せる（リポジトリの外の複製で定数を `qa-csv.md` に向けて `test-check-qa-csv.py` が exit 0） | C1 | 直す（定数を単独の指し先として数え、別ファイルに向ける変異を足した） |
| Verifier | `check-plan-scope.py` が赤（変更範囲の外に 9 ファイル） | 示せる（`python3 scripts/check-plan-scope.py origin/main` が 9 本を挙げた） | V | 直す（「変更範囲」を 1 行 1 パターンに書き直し、proposal・scaffold の `SKILL.md`（版の 2 行）を足した。再実行で exit 0） |

### 2 パス目の指摘の採否

| 関門 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| Verifier・`/code-review` | main が #370 で spec-loop 0.19.0 に先着。版が据え置き扱いになり、#370 は `check-signoff.py` の同じ箇所に `qa.INTERNAL_NUMBER.fullmatch` を足している | 示せる（`python3 scripts/check-version-bump.py origin/main` が exit 1） | V・A1 | 直す（main を取り込み、`is_internal_number` に置き換え直し、0.20.0 に上げる） |
| `/code-review` | feasibility の `SKILL.md` に足した「予算責任者に見せる見積りの根拠に引くのは `Q&A` の節だけ」は、同じファイルの手順 3（内部の費用の行を `D-` の番号で拾う）と `qa-csv.md` の「層」に反する | 示せる（`feasibility/SKILL.md` の 97 行と 125〜127 行が食い違う） | B4 | 直す |
| `/code-review` | scaffold の層の判定を外す変異（常に内部の表を挙げる）が `test-scaffold.py` を素通りする | 示せる（リポジトリの外で `if True else` にして全ケース緑） | E | 直す（`D-` を指さない機能で内部の表が出ないことを見るケースと変異を足す） |
| `/code-review` | 4c の「フックの定数を別のファイルに向ける」は `references/` を落としていて「指し先が無い」で落ちる。別の実在する見出し（`references/qa-csv.md の「層」`）に向けると緑 | 示せる（リポジトリの外で緑） | C1 | 直す（定数は `tree.md` の「Q&A 表を移す」を指すことまで見る） |
| `/code-review` | E の「常に内部」の変異が test-merge-versions にしか無い | 示せない（挙げた変異はいまのテストで赤。scaffold は上の行） | 無し | 残課題 |
| `/code-review` | 本体の指し先の変異だけが置換の回数を確かめていない | 示せない（失敗する側に倒れる。理由の表示が違うだけ） | 無し | 残課題 |
| `/code-review` | `HEADING` がコードフェンスの中の `#` 行も見出しと数える | 示せない（いまの `references/*.md` で当たる例が無い） | 無し | 残課題 |
| `/code-review` | `versions.md` が `Q&A（内部）` を誰が使うかを書いていない | 示せない（書いてあることは事実。誤読の起点は feasibility の引用で、上の行で直す） | 無し | 残課題 |
