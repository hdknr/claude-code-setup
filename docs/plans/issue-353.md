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
- `plugins/spec-loop/skills/req-loop/SKILL.md`・`skills/spec-review/SKILL.md`・`skills/feasibility/SKILL.md` — 差分の読み方（利用者向けは `Q&A` の節）。版の 2 行
- `plugins/spec-loop/README.md` — 該当すれば
- `scripts/test-check-qa-csv.py` — `is_internal_number` の試料と変異。移す手順への指し先（`check-qa-csv.py` の `MIGRATION` と MkDocs のフックの `QA_MIGRATION`）を `references/tree.md` の見出しと突き合わせる（C）
- `scripts/test-merge-versions.py`・`scripts/test-diff-versions.py`・`scripts/test-build-proposal.py`・`scripts/test-scaffold.py`・`scripts/test-check-signoff.py` — 層の判定を外す・入れ替える変異（E）。`test-build-proposal.py` に v1 に内部の表を置く試料（D）。`test-diff-versions.py` の期待値の更新（B）
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版（0.18.1 → 0.19.0。差分の出力の形が変わる＝読む側に効くので minor。0.x）
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
- 関門: 未着手
- 交絡: 実験なし（変異テストのみ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 指し先の見出しの照合は完全一致か | 完全一致、または ` — ` の前の部分（「層 — 共有の表と内部の表」を「層」で指す）を見出しの名前とする | フックの docstring が `qa-csv.md` の「層」を指しており、実在する見出しの名前の部分。照合の範囲は本体の `MIGRATION` とフックのソース全体 |
| `build-proposal` の変異「内部の Q&A も比較に載せる」の殺し役 | 「内部の表の違反でも比較を作る」に替えた | 共有の種類だけを描くようになり（B3）、`drop_internal` を外しても `Q&A（内部）` は提案書に出ない。外すことが効くのは内部の表の違反のほう |
| `check-qa-csv.py` の「ファイルの名前で層を決める」 | 残す（範囲外） | 表 1 枚を検査するときの層。番号の層と食い違わないことは `merge` の `read_qa` が検査で保証する |
