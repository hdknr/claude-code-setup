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
- タグを取らずに履歴だけ全部取った clone（`--no-tags`）で `check-frozen.py` が凍結の破れを見ること（タグが無いことと
  見分けられない。浅い clone は 2 で止まる——CR4）
- 移し方の案内どおりに既存の正本リポジトリを移せること（移す対象の実物が無い。手順を一時リポジトリで再現するまでは証明できる——やる）

**生成物**: 該当あり——`docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（dev-loop の `SKILL.md` のバナーを変えるため。
`skill-metrics.py --check`）。図の書き出し: 該当なし（drawio を触らない）。このリポジトリの `scaffold/`: 無い。

## 未解決の判断・確認待ち

- なし（「決めたこと」は #260・#262 の本文の決定から導いた。5c/5d に送るものは「触らない」に書いた）

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/262-version-layout`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-262`・
  起点 `f40dcbb`・**base: 参照 `origin/main` → `f40dcbb9fa2c46bb197052fcb73ac0297fcd5531`**
- 実装: 済み（`e6f570e`）。`check-all.py` 42/42 緑・`check-plan-scope.py`／`check-version-bump.py`／
  `check-description-sync.py`（`Skip-description-sync` の trailer つき）緑
- 移し方の再現: 一時リポジトリで手順 1〜5 を流した（旧い構成で scaffold=1・signoff=2 → 移して source を直すと
  scaffold=0・本文の sha256 が `merge-versions.py` の出力と一致・旧いタグでは signoff=2 → 取り直すと 0・proposal=0・
  release-v1 で frozen=0 → 直すと 1）。**`git mv` に無いディレクトリを混ぜると全体が失敗する**ことが分かり、案内に書いた
- 関門 1 パス目: **済み**。Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 **1 件**（C）・
  `/code-review`（high）指摘 **8 件**（うち 1 件は Verifier と同じ）。採否は下の「1 パス目の指摘と採否」——直す 5・残課題 3
- 割り目（手順 6・2 パス目の前）: 提案した → **「ここで割る」が選ばれた**。再開は worktree の中で `/clear` →
  `/dev-loop:dev-loop 262`、**Verifier 2 パス目と `/code-review` 2 パス目から**（base は周の base `f40dcbb` のまま）
- 1 パス目の指摘対応: **済み**（CR1〜CR5。起点 `f31c341`・コミット `e08806b`）。`test-check-signoff.py` 35/24・`test-check-frozen.py` 17/14・
  `test-build-proposal.py` 20/17（試料/変異）緑。新しい変異はどれも旧い挙動に戻す形で、対応する試料を落とす（陽性対照）。
  `check-all.py` 42/42 緑
- 関門 2 パス目: **済み**（再開した周で当てた。base `f40dcbb`）。Verifier（`dev-loop:dev-loop-verifier`・sonnet）
  反証 **0 件**・指摘 2 件（V2-1・V2-2）。`/code-review`（high）指摘 **10 件**。採否は下の「2 パス目の指摘と採否」——直す 3・残課題 7（＋計画の記録の直し 1）
- **狭いパスの起点**（2 パス目の指摘対応を始める直前の HEAD）: `fa34dd1`
- 2 パス目の指摘対応: **済み**（R3・R5・R6）。`test-check-signoff.py` 38/26・`test-scaffold.py` 91/51・
  `test-build-proposal.py` 20/17（試料/変異）緑。新しい変異 4 本（版が無いのを 1 と言う・`.` のファイルで版があると言う・
  `.` のファイルの違いを数える・`removed.csv` の決まりを見ない）はどれも、対応する試料を落とす。CR3 で入れた
  「理由も比べる」の変異は、理由の列を読まなくなったので外した
- 狭いパス: **済み**（`dev-loop:dev-loop-verifier`・sonnet。起点 `fa34dd1`・対象 `0d1a6ab`）。修正した挙動への反証 **0 件**、
  素通りした変異 **4 件**（陽性対照つき）・低い指摘 3 件。下の「狭いパスの指摘」——**直さず、採否は人間が決める**
- 残り: PR → PR コメント（未証明・残課題・狭いパスの指摘）→ 人間レビュー
- この周の起票: 3 件（#270・#271・#272。PR #269 のマージ後に起票し、件数の行を書いていなかった——#287 で追記）
- 反証: 1 パス目に 5 件を直した。差し戻し 1 回（手順 4 へ）
- 交絡を潰した手順: 実験は移し方の再現 1 件。陽性側（移した後に 0）と陰性側（移す前・取り直す前・直した後に非ゼロ）を同じ観測点で取った
- 割り目（手順 4）: 提案した → **「ここで割る」が選ばれた**。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 262`、手順 5 から

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 旧い構成（`docs/shared/` 直下）を読み続けるか | 読まない | #260 の決定（0.x の minor・移し方を案内）。2 つの構成を読むと、どちらを読んだかが出力で分からない |
| 照合の範囲に前の版を含めるか | 含める | 決めたこと 3。凍結が守られていれば誤検知は無い |
| v2 以降の提案書がその版の表だけになる | この周では受け入れる | 前の版との比較は 5c（#263） |

**決着の理由が誤っていると判断したなら、それは新しい反証である。**

### 1 パス目の指摘と採否（Verifier 1 件・`/code-review` 8 件。Verifier の 1 件は CR1 と同じ）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1（=V1） | n≥2 で、タグの時点に `docs/v<n>/` が無くても v1 の `shared/` があれば一致（0）になる | 示せる（一時リポジトリで v1 だけのコミットに v2 のタグ → rc=0。CR・V とも再現） | C | 直す——各タグの時点に `docs/v<n>/` のファイルが 1 つも無ければ 2 |
| CR2 | v2 以降で `shared/qa.csv` を置かない版（決まりで許される）は提案書が作れない | 示せる（照合 0 → build-proposal rc=1「承認の時点に無い」） | E | 直す——v2 以降で `qa.csv` が無ければ Q&A は 0 行として作る（v1 は今どおり必須） |
| CR3 | `removed.csv` を丸ごと比べるので、`requirements/`・機能の削除だけでも不一致（1） | 示せる（`ファイル,requirements/r.md` だけの `removed.csv` → rc=1） | B（範囲の外だけ違う → 一致のまま） | 直す——`removed.csv` は `shared/` に効く行（種類 `Q&A`、`ファイル` で対象が `shared/` から始まるもの）だけを比べる |
| CR4 | タグを取らない浅い clone（`actions/checkout` の既定）では、凍結した版を直しても 0 | 示せる（`--no-tags --depth=1` の clone で rc=0） | H | 直す——浅いリポジトリ（`git rev-parse --is-shallow-repository`）は 2。タグを取らない深い clone は残る（未証明に書く） |
| CR5 | `--version` を渡すと作業ツリーの版の並びを検査しない（`v03` があっても 0） | 示せる（同じ木で `--version` 無し 2・有り 0） | D | 直す——`--version` の有無に依らず作業ツリーの版を検査する |
| CR6 | `check-frozen.py` がタグと HEAD を比べるので、リリースのタグを含まないブランチが誤って 1 になる | 示せる | 無し（H は「直したら落ちる」で、誤検知の側は受入基準に無い） | 残課題 |
| CR7 | `--version` を省いて前の版のタグを渡すと「命名に合わない」と言う（命名には合っている） | 示せる | 無し（2 で照合しないのは決めたこと 2 どおり。文言の問題） | 残課題 |
| CR8 | 最大の版をリリースした後、作業中の版が凍結した版を指す（次の版を作れと書いていない）。scaffold の SKILL.md の手順 1 の箇条が紛らわしい | 示せない（読解のみ） | — | 残課題 |

### 2 パス目の指摘と採否（Verifier 反証 0 件・指摘 2 件・`/code-review` 10 件）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | タグ `v<n>/req-signoff-<k>` は素の `v<n>` タグ（よくあるリリースの命名）と ref の名前で衝突し、どちらかがあると他方を作れない | 示せる（`git tag v1` の後の `git tag v1/req-signoff-1` が `cannot lock ref`・rc=128） | 無し（A は付いたタグの選び方で、付けられるかは表に無い） | 残課題——**命名の変更は #260 の決定に触れるので人間が決める**（PR コメントで最初に挙げる） |
| R2（=V2-2） | Issue の本文が名指す再現のコマンド（`merge-versions.py docs build/merged`）に版（`--upto`）が無く、後の版が足されると sha256 が合わなくなる | 示せる（v3 を足すと同じコマンドの出力が変わる） | 無し（G は同じ docs で 2 本を比べる。後の版を足した docs は別の入力） | 残課題——差分の周の Issue は 5d（#264） |
| R3 | `docs/` に版が 1 つも無い（旧い構成）と scaffold が 1 を返す。F の経路は「版が無い（2）」で、check-signoff も 2 | 示せる（試料「版に分けていない」が 1 を期待している） | F | 直す——版が 1 つも無ければ 2（移し方を指す） |
| R4 | check-signoff の docstring の「（`--version` を省いたとき）」が CR5 の後で古い。`--version` つきで版が無い経路の試料が無い | 示せる（docstring と挙動が違う） | 無し（挙動は D どおり） | 残課題 |
| R5 | check-signoff は `shared/` の `.` で始まるファイルも比べ、版の有無の確かめも `.gitkeep` だけで通る。merge-versions は `.` で始まる名前を読まない | 示せる（`.DS_Store` だけ違う組が 1、`docs/v2/.gitkeep` だけの時点が「版がある」） | B（範囲の外だけ違う → 一致のまま）・C | 直す——`.` で始まる名前を含むパスは数えない |
| R6 | CR3 の後、`removed.csv` を緩く読む（見出しを見ない・知らない種類を捨てる）ので、決まりに反する `removed.csv` と無い `removed.csv` が一致になる | 示せる（見出しの順を変えた `removed.csv` と無い時点の組が 0） | B | 直す——merge-versions の `read_removed` で読み、決まりに反すれば 2 |
| R7 | scaffold の関門の失敗が `build/merged/...` のパスで出て、直すべき `docs/v<n>/` を名指さない | 示せる | 無し | 残課題 |
| R8 | build-proposal の `exists()` が check-signoff の `ls-tree` の存在確認と重複 | 示せない（重複の指摘） | 無し | 残課題 |
| R9 | 公開ページ（`docs/plugins/index.md`）の spec-loop の節が版の構成・`check-frozen.py`・移し方を述べていない | 示せる（grep） | 無し | 残課題 |
| R10 | 深い入れ子の JSON で scaffold は 2・merge-versions は traceback（1） | 示せる | 無し（merge-versions の挙動は #261 のまま——L） | 残課題 |
| V2-1 | CR4 の採否で「未証明に書く」とした項目が、未証明の節に無い | 示せる（計画ファイル） | — | 計画の記録を直す（成果物ではない） |

### 狭いパスの指摘（R3・R5・R6 の差分。直さない——採否は人間が決める）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | 変異 `not all(hidden…)` → `any` が素通り。片側だけ `.` の rename（`R100 .x → vis.md`）の試料が無い | 示せる（自前の試料が 1 → 0） | B（テストの網の穴。挙動は正しい） | 人間が決める |
| N2 | 変異 `hidden()` を最後の要素だけ見る形が素通り。`.` のディレクトリの中の通常名（`.cache/x`）の試料が無い | 示せる（0 → 1） | B・C（同上） | 人間が決める |
| N3 | 変異 `return sorted(rows)` → `return rows` が素通り。行の順序だけ違う `removed.csv` の試料が無い | 示せる（0 → 1） | B（同上） | 人間が決める |
| N4 | 変異 scaffold の `and not probe` を外すのが素通り。`v02` だけ（1 のまま）と版が無い（2）を分ける試料が無い | 示せる（1 → 2） | F（同上） | 人間が決める |
| N5 | `docs/v2/notes.md` のような置き場所の外のファイルだけで、版 n があると見なされる | 示せる（rc=0） | C（低） | 人間が決める |
| N6 | `removed.csv` に同じ行が重複すると、重複の無い側と「違う」（1） | 示せる | 無し（取り直しを促す側） | 人間が決める |
| N7 | `read_removed` の `Unreadable` が UTF-8 以外の理由でも「UTF-8 として読めない」と出る | 示せる | 無し（文言） | 人間が決める |
