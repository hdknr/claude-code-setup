# Issue #262: spec-loop 段 5b — 既存の決まりとスクリプトを版の構成に移す

親: #260（段 5b）。前提: #261（5a。マージ済み・PR #265）。後続: #263（5c）・#264（5d）。

## 変更範囲

触る:

- `plugins/spec-loop/references/` — `tree.md`・`versions.md`・`signoff-tags.md`・`spec-ir.md`・`qa-csv.md`・`feasibility-csv.md`・`handoff-issue.md` を版の構成に
- `plugins/spec-loop/scripts/check-signoff.py` — タグ `v<n>/req-signoff-<k>`・`v<n>/budget-signoff-<k>` と版の `shared/` の照合
- `plugins/spec-loop/scripts/build-proposal.py` — 版のパスから読む
- `plugins/spec-loop/scripts/scaffold.py` — 重ね合わせた全体（メモリ上）から作る
- `plugins/spec-loop/scripts/merge-versions.py` — 重ね合わせを関数として呼べるようにする（挙動は変えない）
- `plugins/spec-loop/scripts/check-frozen.py` — 新規。凍結の確認（`release-v<n>` と `docs/v<n>/`）
- `plugins/spec-loop/scripts/check-spec-exit.py` — docstring の usage の例だけ（引数は今もパス）
- `plugins/spec-loop/skills/*/SKILL.md` — パス・タグ名・版のバナー
- `plugins/spec-loop/agents/estimate-checker.md` — パス
- `plugins/spec-loop/README.md`
- `plugins/spec-loop/.claude-plugin/plugin.json` — spec-loop 0.7.0・description（照合が版ごとになった）
- `.claude-plugin/marketplace.json` — spec-loop 0.7.0・dev-loop 1.39.1・description（plugin.json と同じ値）
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 写しの追随（パス）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版のバナーだけ
- `plugins/dev-loop/.claude-plugin/plugin.json`
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く）
- `docs/plugins/index.md` — spec-loop の節（照合・凍結）
- `scripts/test-check-signoff.py`
- `scripts/test-build-proposal.py`
- `scripts/test-scaffold.py`
- `scripts/test-merge-versions.py`
- `scripts/test-check-frozen.py` — 新規
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上
- `CLAUDE.md` — プロジェクト構成
- `docs/plans/issue-262.md` — この計画

触らない:

- 各スキルの差分モード（レビュー会に載せる範囲・判定役に全体を渡す・差分の見積り・前の版との比較） — 5c（#263）
- `scaffold` の追加・変更・削除の振り分けと Issue の新しい形（`spec-loop-handoff: v2`）・dev-loop の v2 本文 — 5d（#264）
- 差分の周を始める前の「乖離」の確認（前の版の `--check`・既存の Red テスト） — 5c/5d。#262 の「やること」に無い
- 旧い構成（`docs/shared/` 直下）の後方互換 — 持たない。spec-loop は 0.x なので minor で上げ、移し方を案内する（#260 の決定）

**周の大きさ（同じことを述べている箇所）**: パスとタグ名は**約 20 箇所**にある——references 7・スクリプト 4・スキル 5・
agent 1・README・`docs/plugins/index.md`・dev-loop の `spec-gap.md`（写し）・`CLAUDE.md`。**分けない**: 決まりとスクリプトが
同じ周で変わらないと食い違う（#261 の計画で 5b に寄せた理由そのもの）。#262 は既に親から切り出した段で、利用者が選んだ単位。
**パスは references を正とし、スキル・README は指し先とコマンド例だけにして複製を増やさない。**

## 決めたこと

1. **版の発見は `merge-versions.py` の `find_versions` を使う**（写しを作らない）。作業中の版 = 番号の最大。版の並びが決まりに反すれば
   照合も生成もしない（2）。
2. **タグ**: `v<n>/req-signoff-<k>`・`v<n>/budget-signoff-<k>`（`n`・`k` は 1 以上・先頭 0 なし）。`check-signoff.py` は
   `--version <n>`（省けば作業ツリーの作業中の版）の 2 種のタグだけを数え、`k` の数の最大を最新とする。**`--req`/`--budget` で
   別の版のタグを渡したら 2**（別の版の承認を組にしない）。
3. **照合の範囲**: `docs/v1/shared/`〜`docs/v<n>/shared/` と `docs/v2/removed.csv`〜`docs/v<n>/removed.csv`。
   v<n> の全体の共有範囲は、それより前の版の `shared/` と、行を消す `removed.csv` にも依る。凍結が守られていれば前の版は動かないので、
   含めても誤検知は無い（凍結が破られていればここでも見える）。**どちらかの時点で比べる中身が 1 つも無ければ 2**（今と同じ）。
4. **提案書**: `docs/v<n>/shared/qa.csv`（req のタグの時点）・`docs/v<n>/feasibility/{schedule,estimate}.csv`（budget のタグの時点）・
   `docs/v<n>/proposal/*.md`（作業ツリー）。v2 以降はその版の差分の表になる——前の版との比較は 5c。
5. **scaffold**: `docs/` を**メモリ上で**重ね合わせ（`merge-versions.py` と同じ関数・同じバイト）、一時ディレクトリに書いて、
   条件 1 の関門・中間表現の検査・生成をそこに当てる。**`build/merged/` には書かない**（`--check`・`--dry-run` が書かない約束を守る）。
   重ね合わせが決まりに反すれば 1、読めなければ 2（`merge-versions.py` と同じ区別）。どちらも Issue の本文を消す。
6. **`source` は重ね合わせた全体の根からのパス**（`spec/order.md`）。版のディレクトリのパスにすると、後の版で変えたときに指し先が動く。
   Issue の本文が名指す中間表現は `build/merged/spec/spec_ir.json`（`merge-versions.py docs build/merged` で作るもの。sha256 はそのバイト）。
7. **凍結**: `check-frozen.py` を新設。命名に合う `release-v<n>` ごとに、タグの時点と HEAD で `docs/v<n>/` が同じか
   （`git diff --name-status <tag> HEAD`）、作業ツリーに未コミット・未追跡の変更が無いか（`git status --porcelain --untracked-files=all`）を見る。
   違えば 1。タグの時点に `docs/v<n>/` が無い・git が使えない は 2。**リリースのタグが 1 つも無ければ 0 で、そう言う**（凍結した版が無い）。
8. **移し方の案内は `versions.md` に置く**（`tree.md` は指すだけ）——`git mv`・`source` の書き換え・`scaffold.py` で作り直し・
   旧いタグは読まれないので**承認を取り直す**（タグはスキルが付けない）。

## verify の受入基準

**証明できるもの（回帰テスト・実データ相当の試料で確かめる）**

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | 照合は版 n のタグだけを組にし、`k` の数で最新を選ぶ | 省略時の自動選択／`--version`／`--req`・`--budget` の明示／命名に合わないタグ（`v2/req-signoff-03`・`req-signoff-v3`・`v02/…`）／別の版のタグ | `check-signoff.py` の命名の正規表現と版の一致検査。テストで各形 |
| B | 照合の範囲は v1〜v<n> の `shared/` と v2〜v<n> の `removed.csv` | 作業中の版の `shared/` だけ違う／前の版の `shared/` だけ違う／`removed.csv` だけ違う／範囲の外（`requirements/`）だけ違う（一致のまま） | テストで各形 |
| C | 比べる中身が無ければ一致と言わない（2） | タグの時点に版のディレクトリが無い（旧い構成のタグ） | テスト |
| D | 版の並びが決まりに反すれば判定しない（2） | `v02`・欠番・版が 0 個 | `find_versions` を使う。テスト |
| E | 提案書は照合が 0 のときだけ・承認したタグの時点の版のパスから作る | 照合 1/2／タグ後に作業ツリーの `docs/v<n>/shared/qa.csv` を直した／別の版のファイル | テスト |
| F | scaffold は重ね合わせた全体に当てる | v2 で機能を変更・削除／v2 の Q&A が未反映（関門が止める）／v2 の `source` が v2 の仕様を指す／重ね合わせが決まりに反する（1・本文を消す）／`--check`・`--dry-run` で何も書かない／版が無い（2） | テスト |
| G | Issue の本文の中間表現の sha256 が `merge-versions.py` の出力のバイトと一致する | 同じ docs から 2 本のスクリプトで作って比べる | テスト |
| H | 凍結した版を直したら CI が落とせる | コミット済みの変更／未コミットの変更／未追跡のファイル／ファイルの削除／タグの時点に版が無い（2）／命名に合わないリリースのタグ（数えない）／タグが無い（0） | `check-frozen.py`。テストで各形 |
| I | 決まりの原本が 1 箇所で、スキル・README は指すだけ | references 間の食い違い／`versions.md` の「移行中」の残り／旧いパス（`docs/shared/` 直下・`req-signoff-v<n>`）の残り | 宣言の範囲で grep（プラグイン全体・CLAUDE.md・docs/plugins） |
| J | dev-loop の `spec-gap.md` の写しが `handoff-issue.md` と合う | 印・節（`test-scaffold.py`）／パスの記述 | テスト＋grep |
| K | version 3 箇所（spec-loop 0.7.0・dev-loop 1.39.1） | `check-plugin-versions.py` | `check-all.py` |
| L | `merge-versions.py` の挙動が変わらない | 関数に切り出した | `test-merge-versions.py` がそのまま緑 |

**掛け算**: 受入基準 A〜L を **Verifier × {1 パス目・2 パス目}**・**`/code-review` × {1 パス目・2 パス目}** の 4 つの受け渡しすべてに渡す。
既知の限界も同じ 4 つに渡す。2 パス目で直した行があれば狭いパスにも同じ表を渡す。

**この環境では証明できないもの（未証明）**

- 利用者の正本リポジトリの CI で `check-frozen.py` が実際に走ること（正本リポジトリはこのリポジトリの外にある。`fetch-depth: 0` の要否も含む）
- 移し方の案内どおりに既存の正本リポジトリを移せること（移す対象の実物が無い。手順を一時リポジトリで再現するまでは証明できる——やる）

**生成物**: 該当あり——`docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（dev-loop の `SKILL.md` のバナーを変えるため。
`skill-metrics.py --check`）。図の書き出し: 該当なし（drawio を触らない）。このリポジトリの `scaffold/`: 無い。

## 未解決の判断・確認待ち

- なし（「決めたこと」は #260・#262 の本文の決定から導いた。5c/5d に送るものは「触らない」に書いた）

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/262-version-layout`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-262`・
  起点 `f40dcbb`・**base: 参照 `origin/main` → `f40dcbb9fa2c46bb197052fcb73ac0297fcd5531`**
- 関門: 未着手
- 反証: —
- 交絡を潰した手順: —
- 割り目（手順 4）: —

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 旧い構成（`docs/shared/` 直下）を読み続けるか | 読まない | #260 の決定（0.x の minor・移し方を案内）。2 つの構成を読むと、どちらを読んだかが出力で分からない |
| 照合の範囲に前の版を含めるか | 含める | 決めたこと 3。凍結が守られていれば誤検知は無い |
| v2 以降の提案書がその版の表だけになる | この周では受け入れる | 前の版との比較は 5c（#263） |

**決着の理由が誤っていると判断したなら、それは新しい反証である。**
