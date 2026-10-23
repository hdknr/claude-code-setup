# Issue #354 — 公開ページの spec-loop の節に、版の構成と判定役の役目を足す（#271・#277 のまとめ）

## 変更範囲

触る:

- `docs/plugins/index.md` — spec-loop の節だけ。版の構成・凍結・移し方の小節を足し、`spec-review` の小節に 3 つの判定役の説明を足す。同じ小節の振り分けの区分の行を `references/spec-scope.md` の 6 区分に合わせる。**1 パス目の指摘対応（R3）で `feasibility` の小節の費用の振り分けの行にも広げた**——新しい spec-review の記述（費用だけの選択は内部の表）と同じページで食い違うため
- `docs/plans/issue-354.md` — この計画

触らない:

- `plugins/spec-loop/` の中（`references/`・`agents/`・`README.md`・`SKILL.md`）——決まりの原本で、この周は指すだけ。プラグインの版は上げない
- 公開ページの spec-loop 以外の節

### 同じことを述べている箇所の数

- 版の構成・凍結・移し方: 原本は `references/versions.md` の 1 か所。公開ページには**指し先と要点（1〜2 行）だけ**を置き、ツリー・コマンド・手順の写しは置かない → 新しい複製は 0（要点の 1 行ずつ）
- 判定役の役目: 原本は `agents/*.md`（3 ファイル）と `references/spec-exit.md` の条件の表。公開ページの説明が 1 か所増える（README にも短い言及がある）。**分けない理由**: 利用者が公開ページだけで分かること自体が受入基準 B なので、要約を置かざるをえない。食い違いを防ぐため、条件の番号は `spec-exit.md` の表と突き合わせ、細部は定義ファイルへ指す
- 振り分けの区分: 公開ページの既存の行が「5 つ」（`shared`/内部を分ける前の数え方）。原本 `spec-scope.md` は 6 区分（判定役の案は「退ける」以外の 5 つ）。同じ小節なので直す

## 乗るデプロイ経路

`docs/` の変更 → main へのマージで GitHub Pages に自動デプロイ（`.github/workflows/docs.yml`）。

## verify の受入基準

不変条件と、それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 版の構成（`docs/v<n>/`・v1 から置く・v2 以降は差分・作業中は最大の番号・リリースは凍結）を**指し先として**書き、`references/versions.md` の写し（ツリー・手順）を作らない | 要点の言い換えが原本と食い違う／ツリーや `git mv` の手順を写す | 差分を原本と突き合わせる。コードブロックを足していないこと |
| A2 | `check-frozen.py` が何を確かめるか（リリースした版の `docs/v<n>/` が直されていないか・CI で走らせる・タグはスキルが付けない）を書き、原本の「凍結」を指す | 終了コードなどを写して古くなる | 同上 |
| A3 | 旧い構成（`docs/shared/` 直下）・旧いタグ（`req-signoff-v<n>` など）を 0.7.0 以降読まないこと、症状、移し方の指し先 | **症状の記述（scaffold・check-signoff が 2 を返す）が事実と違う**／版の番号が違う | **一時ディレクトリに旧い構成の正本リポジトリを作り、`scaffold.py --check` 相当と `check-signoff.py` を実際に走らせて終了コードを見る**。0.7.0 は `git show e6f570e:plugins/spec-loop/.claude-plugin/plugin.json`（#262 で 0.6.0 → 0.7.0） |
| B1 | 公開ページだけで 3 役それぞれの役目（何をするか・何を判定するか・何をしないか）が分かる | 説明が名前の言い換えに留まる | 読む |
| B2 | 判定する条件の番号が `spec-exit.md` の表・`agents/*.md` と一致（Red Team = 2・3、Formal Checker = 4、Domain Checker は番号付きの条件を持たない） | Domain Checker に番号を付ける／条件の中身を取り違える | 表・定義と突き合わせる |
| B3 | 3 役とも書き込みツールを持たず（`tools: Read, Grep, Glob, Bash`）、仕様を書いた側と別のティアで呼ばれること | 「読み取り専用」と書いて Bash を落とす | 定義の frontmatter |
| B4 | Red Team の名前の由来（攻撃側に立って弱点を探す役）を一言 | 無い | 読む |
| C1 | タグの命名が `signoff/v<n>/req-<k>`・`signoff/v<n>/budget-<k>`（`signoff-tags.md`） | 旧い名前を新しい名前として書く | grep |
| C2 | 振り分けの区分が `spec-scope.md` の 6 区分（判定役の案は「退ける」以外） | 既存の「5 つ」の行が残る | 差分 |
| C3 | Q&A 表の層（共有 `shared/qa.csv`・内部 `spec/qa-dev.csv`） | 判定役の振り分けの案から内部の表が抜ける | 差分 |
| C4 | （1 パス目の指摘対応で追加）`feasibility` の小節が、費用だけが変わる選択を共有の表に起票せず内部の表（`spec/qa-dev.csv`）に拾うと書き、`feasibility/SKILL.md` と一致する | 共有の表への起票だけが残る | `feasibility/SKILL.md` の description・123-125 行と突き合わせる |
| A4 | （1 パス目の指摘対応で追加）警告が 0.7.0〜0.11.x の名前のタグ（`v<n>/req-signoff-<k>`）も読まないこと・消さないと `v<n>` でリリースできないことを書き、片付け方は `signoff-tags.md` を指す。移し方の手順を写さない | 版の範囲が違う／手順の一部だけを写す | `git show e6f570e:` と `8d30068` の前後の `plugin.json`・`signoff-tags.md` と突き合わせる |
| D1 | `python3 scripts/check-site-links.py` が通る | 新しい絶対リンクのアンカーが無い | 実行 |
| D2 | `uv run mkdocs build --strict` が通る | 書式・リンク | 実行 |
| E | `python3 scripts/check-all.py` が通る（歯止めを全部） | — | 実行 |

掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目・2 パス目（該当すれば）とも渡す。

証明できないもの（未証明）: 「利用者が迷わなくなるか」は読み手の理解で、この環境では測れない。B1 は「ページの記述だけで 3 つの問いに答えられるか」を関門に読ませる範囲まで。

生成物: **生成物なし**——`docs/plugins/index.md` は手書き。`diagrams/exports.json`・`skill-metrics.py` の生成ブロックは触らない（`SKILL.md` を触らない）。mkdocs の `site/` はコミットしない。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/354-spec-loop-public-page`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-354`・起点 `f712197`・base の参照 `origin/main`・base の SHA `f712197f0664ff85bd6853451ce4fbdcca4521c8`
- 実装: `e938a0a`（手順 4 完了）。**1 パス目の起点（関門に渡す時点の HEAD）: `e938a0a`**
- 割り目（手順 4 の後）: AskUserQuestion で訊き、**「ここで割る」が選ばれた**（2026-10-23）。再開は手順 5 から
- 関門 1 パス目（起点 `e938a0a`・base `f712197f0664ff85bd6853451ce4fbdcca4521c8`）: **済み**
    - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**。A3 を一時リポジトリで実走して一致。D2（`mkdocs build --strict`）は未実行と報告——依存の取得にネットワークが要るため
    - `/code-review`: **指摘 7 件**。採否は下の「1 パス目の指摘の採否」（直す 4・R1 に畳む 1・残課題 2）
- 1 パス目の指摘対応: `5bfc829`。変更範囲を `feasibility` の小節の 1 行に広げ、受入基準 C4・A4 を足した。
  当て直し: `check-all.py` 44/44（失敗 0 / 飛ばし 0）・`check-site-links.py` 0・`mkdocs build --strict`（CPython 3.13 ＋ ロックした依存・`--site-dir` を scratchpad に）警告 0 で成功
- 1 パス目の指摘対応の差分（起点 `e938a0a`・計画ファイルを除く）: `docs/plugins/index.md` 12 行追加・7 行削除——0 行ではないので 2 パス目を回す
- 2 パス目: 再開後（2026-10-23）に Verifier（`dev-loop:dev-loop-verifier`・sonnet）と `/code-review` を起動。base `f712197f0664ff85bd6853451ce4fbdcca4521c8`・HEAD `3a178e2`
- **2 パス目の指摘対応を始める直前の SHA（狭いパスの起点）: `3a178e2`**
- 2 パス目の結果: Verifier **反証 1 件**（P1）・`/code-review` **指摘 4 件**（P1〜P4。P1 は両方が挙げた）。採否は下の「2 パス目の指摘の採否」（直す 2・残課題 2）
- 2 パス目の指摘対応: `1fff8c5`（P1・P2）
- 狭いパス（起点 `3a178e2`・`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**。Verifier が設計した試料で P1（旧い構成で `--version 1` も「版（v1 など）が 1 つも無い」rc=2、`--req`/`--budget` に旧いタグを渡しても同じ）と P2（`v1/req-signoff-1` があると `git tag v1` が `cannot lock ref` で失敗、`release-v1` は作れる）を実走して一致。赤になった変異 0・素通りした変異 0
- 2 パス目の指摘対応後の当て直し: `check-all.py` 44/44（失敗 0 / 飛ばし 0。`1fff8c5` で）・`check-site-links.py` 0・`mkdocs build --strict`（CPython 3.13 ＋ ロックした依存）警告 0 で成功
- 割り目（2 パス目の前）: AskUserQuestion で訊き、**「ここで割る」が選ばれた**（2026-10-23）。再開は 2 パス目から
- 次: 2 パス目——**手順 5 の Verifier と手順 6 の `/code-review` の両方**を、base `f712197f0664ff85bd6853451ce4fbdcca4521c8`・HEAD `5bfc829` 以降に当てる
- 反証と差し戻し: 1 パス目の Verifier 反証 0 件・差し戻しなし
- 交絡: 実験あり（A3 の終了コード）。一時ディレクトリに `docs/shared/`・`docs/spec/` 直下の旧い構成と
  旧いタグ（`req-signoff-v1`・`budget-signoff-v1`）を持つリポジトリを作り（`GIT_CONFIG_GLOBAL=/dev/null`・`HOME` 差し替え）、
  `scaffold.py --dry-run` → **2**「版（v1 など）が 1 つも無い（…「移し方」で移す）。判定していない」、
  `check-signoff.py` → **2**「作業ツリーの docs/ に版（v1 など）が 1 つも無い。照合していない」。
  **陽性対照**: 同じリポジトリを `git mv` で `docs/v1/` に移し `signoff/v1/req-1`・`signoff/v1/budget-1` を付けると、
  「版が無い」の文言は消え、別の理由（試料の Q&A 表の見出し）で止まる——**2 は構成のせいで出ていた**。
  観測窓: この 2 本のスクリプト・この 1 つの試料。`proposal`（`build-proposal.py`）は走らせていないので、ページには 2 本の名前だけを書いた
- `mkdocs build --strict`: **手元の uv の venv（CPython 3.12.8）では main の時点（`f712197` を `git archive` で展開）でも失敗する**——
  `docs/plans/issue-332.md` の `<![` で標準ライブラリの `html.parser` が `AssertionError`。この周の変更とは無関係で、同じコミットの main の CI（`docs.yml`）は成功。
  **CPython 3.13.11 ＋ ロックした依存（`uv export` → `uv run --isolated --no-project`）では `--strict` で警告 0・成功**。
  新しいアンカー `spec-loop-judges`・`spec-loop-versions` と、ページ内リンク `#spec-loop-versions` が HTML にあることを確認
- `check-site-links.py`: 0（250 ファイル）
- `check-all.py`: 44/44（失敗 0 / 飛ばし 0）——`e938a0a` と同じ中身の作業ツリーで

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| Issue 本文は「振り分けの 5 区分」と書く | 原本の 6 区分に合わせる | Issue 自身が「着手時点の `references/` を正として書く」と書いており、`spec-scope.md` は #339 で 6 区分になっている |
| 見積りの検証役（estimate-checker）も判定役として書くか | 書かない（`feasibility` の小節の既存の 1 行のまま） | Issue の対象は spec-review の 3 役 |
| `plugins/spec-loop/README.md` の判定役の記述も直すか | 触らない | 食い違いは無い（名前と書き込みツールを持たないことだけ）。プラグインの版を上げる周になる |

### 1 パス目の指摘の採否（Verifier 反証 0 件・`/code-review` 指摘 7 件）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | 警告が「0.6.0 以前」だけを対象にし、0.7.0〜0.11.x の #260 の名前のタグ（`v<n>/req-signoff-<k>`）を書いていない。消さないと `v<n>` でリリースできない | 示せる——`git show e6f570e:plugins/spec-loop/references/signoff-tags.md` の 10 行が `v<n>/req-signoff-<k>`、`8d30068` で 0.11.1 → 0.12.0 に改名。`signoff-tags.md` 25-34 行が「読まない」「手元とリモートから消す」 | A3・C1 | 直す |
| R2 | 警告の移し方の括弧書きが 6 手順のうち 4 つだけを写している | 示せる——`versions.md` の「移し方」は 6 手順（`release-v1` の付け直し・CLAUDE.md と CI のパスを含む） | A1（写しを作らない） | 直す（括弧書きを消して指し先だけにする） |
| R3 | `feasibility` の小節の既存の行が、費用だけが変わる選択も Q&A 表に起票すると読める（#339 以降は内部の表） | 示せる——`feasibility/SKILL.md` 3 行の description「共有の表に起票せず、内部の Q&A 表の行として見積りに拾う」 | C3 | 直す |
| R4 | タグの行に #260 の名前の片付け（`--prune-tags`）への指し先が無い | R1 と同じ実物 | C1 | R1 に畳む（警告から `signoff-tags.md` を指す） |
| R5 | `check-signoff.py --version 1` では「版が無い」ではなく「タグが無い」と出る（終了コードは 2） | 示せる——`check-signoff.py` 297 行 | A3（症状の記述） | 直す |
| R6 | 冒頭の「指摘と判定を返すだけ」と、Domain Checker が番号付きの条件を判定しないことが食い違う | 示せない——`domain-checker.md` は自分を判定役と呼び、指摘ごとの判定を返す。読み手の解釈の問題 | 無し | 残課題 |
| R7 | 条件 5 が Domain Checker の行にだけ付いている | 示せない——その行が既に「3 役の指摘が 1 件残らず振り分け済み」と書いている | 無し | 残課題 |

**R5 の決着の理由（297 行）は誤りだった**——2 パス目の 2 つの関門がともに反証した（下の P1）。

### 2 パス目の指摘の採否（Verifier 反証 1 件・`/code-review` 指摘 4 件。P1 は両方が挙げた）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| P1 | 旧い構成で `check-signoff.py` に版を指定すると「タグが 1 つも無い」と出る、という 1 パス目の R5 対応の記述が事実と違う——版を指定しても「版（v1 など）が 1 つも無い」で 2 | 示せる——`check-signoff.py` 279-280 行（`--version` の有無に関わらず `working_version` を先に呼ぶ）。Verifier が旧い構成の試料で `--version 1` を実走し「版（v1 など）が 1 つも無い」rc=2、陽性対照（`docs/v1/`）で 297 行の「タグが 1 つも無い」rc=2 | A3 | 直す（版を指定しても同じ症状と書き、R5 で足した文を消す） |
| P2 | 「消さないと `v<n>` でリリースできません」が、同じ節の「リリースは `release-v<n>`」と食い違って読める。詰まるのは素の `v<n>` タグでリリースするリポジトリだけ | 示せる——`signoff-tags.md` 24 行「凍結のタグ `release-v<n>` は衝突しない」・30 行 | A4 | 直す（素の `v<n>` タグでリリースする場合に限る、と書く） |
| P3 | spec-review の小節の既存の行が「Q&A 表に起票」のままで共有の表に限ると書いていない | 示せない——2 行下の 6 区分が共有／内部を分けて書いており、読み手が誤る実物は無い | 無し | 残課題 |
| P4 | `feasibility` の小節の既存の行が「費用への影響を添えた質問」で、description の「推奨」が抜けている | 示せない——C4 が見るのは費用だけの選択の振り分けで、そこは一致。推奨の列はページが扱う範囲（列の原本は `qa-csv.md` を指す）の外 | 無し | 残課題 |

## 起票

- この周の起票: 0 件（残課題 R6・R7・P3・P4 はどれも実物で失敗を示せず、起票の条件 (a) を満たさない。PR コメントの残課題に載せる）
