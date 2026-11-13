# Issue #1008 — absent-lines.md: uv run の暗黙の sync を止める形に --frozen を並べている

**不在の周である**——cruise（親 Issue #999）の子として回す。出所: `/dev-loop:cruise 999 --absent` の起動（2026-11-13T04:29Z）。
確かめた線（台帳 `issue-999`。出所: 利用者の確認（起動時・2026-11-13T04:29:54Z、配布を見せて確かめた））:
仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票。
#1008 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。本文の先頭は `<!-- cruise-found: #999 -->`（#996 の周の 3 回目の当て直しの Verifier の E-V1 から起票された周——後続の後続の扱いは dev-loop の `references/found-lines.md`）。
確認の Issue #1003 は閉じず、閉じるキーワードで指さない。

直す線: `既定`（出所: cruise の確かめた線）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「`依存の追加・更新 = 表で確かめて進める`」の 4 の「暗黙に入れる操作も同じ」の 1 文（557 行目）だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.106.0 → 1.106.1）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行だけ（dev-loop・cruise の 2 本）
- `docs/plans/issue-1008.md` — この計画

触らない:

- `prompts/verifier.md`・`references/dependencies.md`・`agents/dev-loop-verifier.md`（`--frozen` も `uv run` の止め方も書いていない——`grep -rn -- '--frozen' plugins/ docs/ CLAUDE.md scripts/`（`docs/plans/` を除く）で当たるのは 557 行目だけ）
- description（能力は変わらない）

複製の数: 「`uv run` の暗黙の sync を止める形」を述べている箇所は 557 行目の 1 箇所（上の grep と、`uv run`・`no-sync`・`uv sync` の grep で確かめた。`agents/dev-loop-verifier.md` の `uv run mkdocs build` は検証の副作用の例で、止め方は述べていない）。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と公開サイトの再ビルド（`docs/plans/` もビルド対象）。

## 版の上げ方

dev-loop を patch で上げる（1.106.0 → 1.106.1。記述の修正）——`marketplace.json`・`plugin.json`・dev-loop の全 `SKILL.md`（2 本）の 2 行。
マージの直前に main が進んでいたら（#997・#1007 の周も dev-loop を上げうる）、main の先端の dev-loop の版から patch で 1 つ上げた値にする（cruise の `references/parallel.md` の「版とマージの順」）。

## 受入基準（不変条件 × 経路）

Issue の 2 行（チェックリスト）を不変条件にする。入口は「不在の周で依存を足した後、`uv run` で検証・テストを走らせる体（周の本人・実装役・Verifier・`/code-review`）が absent-lines.md の 4 を読む」こと——この手順を案内しているのは 557 行目だけ（複製の数）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| U1 | 557 行目は sync を止める形として `--no-sync` だけを案内し、`--frozen` を同じ効き目のものとして並べない | (a) 557 行目の本文 (b) 同じ手順をほかの場所（`dependencies.md`・`verifier.md`・公開ページ・`CLAUDE.md`）が述べている | (a) `--no-sync` だけを付ける形に書き換え、`--frozen` は「sync は止めない」と効き目の違いを添えて並べない (b) grep で他に無いことを確かめた（複製の数） |
| U2 | 書き換えた文の事実が正しい——`uv run --no-sync` は sync（sdist の build）をしない／`uv run --frozen` は sync して sdist を build する | uv の版（手元 0.11.14） | 実際に走らせて確かめる（陽性対照つき。下の「交絡」） |
| U3 | dev-loop の版を patch で上げ、3 種類（marketplace.json・plugin.json・各 SKILL.md の 2 行）を揃える | 4 ファイル | `check-plugin-versions.py`・`check-version-bump.py origin/main` |

**検証で証明できるもの**: U1〜U3。
**この環境では証明できないもの**: uv の他の版（0.11.14 以外）で `--frozen` が sync するか——`uv run --help` の文言（"Run without updating the `uv.lock` file"）と、手元の 1 版の実走だけ。未証明として PR コメントに書く。

**生成物**: 無し（`skill-metrics.py` の生成ブロックは SKILL.md の節構造から作るが、版の行を変えるだけで節は変わらない——`skill-metrics.py --check` で確かめる。図は触らない）。

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

## 未解決の判断・確認待ち

- 無し（Issue の受入基準どおり。仕様の穴ではない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1008-absent-lines-no-sync`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1008`・起点 `b68e125d`・base `origin/main` → `b68e125dc5d399a31bdc1e6ff5d683b90913c57e`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目済み——Verifier（sonnet・dev-loop:dev-loop-verifier）反証 0 件、/code-review（high）指摘 6 件（直す 0・残課題 6）。1 パス目の指摘対応の起点: `326b91224e422699311e2232a6b4e2bf583007ae`
- 2 パス目: 該当なし（1 パス目の指摘対応の差分 0 行——起点 `326b9122` から `git diff <起点> -- ':(top)' ':(top,exclude)docs/plans/issue-1008.md'` が空、`git status --porcelain` は計画ファイルだけ）
- 狭いパス: 該当なし
- 割り目（手順 6・2 パス目の前）: 2 パス目が無いので置かない
- 歯止め: `check-all.py`（run-serial 越し）76 本中 75 本が緑・`check-plan-counts.py` だけ件数の行が無くて赤 → 件数の行を足して `check-plan-counts.py` が緑（`326b9122`）
- 反証と差し戻し: 1 パス目 Verifier 0 件・/code-review 6 件（直す 0）。手順 4 への差し戻しなし
- 交絡: 実験 1 つ（U2）。一時ディレクトリ（scratchpad）に、`setup.py` が build のたびに印のファイルへ 1 行書く sdist だけの path 依存を持つ uv の project を作り、`uv lock` の後に
  `uv run --no-sync python -c …`（ログに `Building`/`Built` の行が出ない）と `uv run --frozen python -c 'import markerdep'`（ログに `Built markerdep` と `Installed 1 package` が出た）を比べた。
  判別に使うのはログの build の行である——印のファイルは `MARKER` の環境変数が無いと `/dev/null` に書く作りで、`--no-sync` の側の「印が無い」だけでは判別しない（/code-review 1 パス目 CR1-6）。Verifier 1 パス目も独立に、印を数えて（lock の後 2 行・`--no-sync` で増えず・`--frozen` で 4 行）同じ結論を出した。
  陽性対照は `--frozen` の側（同じ観測点で build が起きると印が出ることを示す）。`UV_CACHE_DIR` を一時ディレクトリに向け、手元のキャッシュの wheel で build が飛ばされる形を外した。観測窓: uv 0.11.14・1 回ずつ・path 依存の sdist（レジストリの sdist では試していない）。

## 既知の限界・決着済みの論点

- **`--frozen` を消さずに「sync は止めない」と添えた**——Issue の受入基準は「同じ効き目のものとして並べない」で、並べないまま違いを書けば、`--frozen` を付けて済ませる読み方を塞げる。消すだけにする形は採らなかった（理由: 元の文が `--frozen` を挙げていたので、読んだことのある体が同じものと思い込んだままになる）。
- **`--locked` には触れない**——lockfile が変わらないことを確かめるだけで、sync は止めない（`uv run --help`）。557 行目は `--locked` を挙げていないので、足さない。
- **`UV_NO_SYNC` の環境変数・`[tool.uv]` の設定で止める形は書かない**——Issue の範囲の外（557 行目は引数の形で案内している）。

### 採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1-1 | /code-review 1 パス目: `--no-sync` は PEP 723 の script（inline の依存）では no-op で、`--with` も止めない——557 行目は `--no-sync` だけで足りるように読める | 示せる（/code-review が uv 0.11.14・offline で `Building markerdep`） | 無し（U1 は `--frozen` を並べないこと、U2 は project の `uv run` の事実） | 残課題 |
| CR1-2 | 使わない一覧（`npx`・`pnpm dlx`・`yarn dlx`）に uv の `uvx`／`uv tool run` が無い | 示せる（`uvx --from <path>` で build） | 無し | 残課題 |
| CR1-3 | 新しい worktree には `.venv` が無く、`uv run --no-sync` は空の環境を作る——先に入れる方法を書いていない | 示せる（空の venv で ModuleNotFoundError） | 無し | 残課題 |
| CR1-4 | 根の直し方: `uv run --no-build`（sync はするが build を拒む）で書く | 示せる（`--no-build` で exit 2・印なし） | 無し | 残課題 |
| CR1-5 | `prompts/verifier.md:127` の「包を入れない」に `uv run` が無く、`agents/dev-loop-verifier.md:49-50` は `uv run`・`uv sync` を副作用として許す | 示せない（Verifier が `uv run` で sdist を build する形を実物で示していない） | 無し | 残課題 |
| CR1-6 | 計画の交絡の証拠を「印のファイルが作られない」としているが、`setup.py` は `MARKER` が無いと `/dev/null` に書く | 示せる（`dep/setup.py`） | 無し（計画は成果物でない。U2 の結論は変わらない） | 残課題（計画の記述は直した——成果物の差分ではない） |

## 経験の還元（手順 8）

### 周の途中の課題の振り分け（`references/found-lines.md`。この周は `<!-- cruise-found:` の周——後続の後続なので、3 つに当たらなければ記録だけ）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け | 理由 |
| --- | --- | --- | --- | --- |
| CR1-1 PEP 723 の script・`--with` では `--no-sync` が効かない | #1008 /code-review 1 パス目 | 示せる | 記録だけ | 依存を足す不在の周で、PEP 723 の script や `--with` で検証を走らせる形はまず起きない（ふつうは project の `uv run pytest`）。迷ったら記録だけ |
| CR1-2 `uvx`／`uv tool run` が使わない一覧に無い | #1008 /code-review 1 パス目 | 示せる | 記録だけ | 一覧の抜け（文言）。書いてあることに従って誤った操作になる記述ではない |
| CR1-3 新しい worktree で `--no-sync` が空の環境を作る | #1008 /code-review 1 パス目 | 示せる | 捨てる | 同じ文の前半が「検証・テスト・重い検査で入れ直すとき（… `uv sync` …）も同じ止める形で走らせ」と、先に止める形（`--no-build`）で入れることを求めている——文に従えば空の環境にならない |
| CR1-4 `uv run --no-build` で書く | #1008 /code-review 1 パス目 | 示せる（代案が動くこと） | 記録だけ | 設計の代案。今の文の失敗ではない |
| CR1-5 `prompts/verifier.md`・`agents/dev-loop-verifier.md` が `uv run` を止めない | #1008 /code-review 1 パス目 | 示せない | 記録だけ | 手順 4 の止める形（`--no-build`）で入れた後の lock には wheel の無い包が残らないので、Verifier の素の `uv run` が包の build を走らせる形を示していない |
| CR1-6 計画の交絡の証拠の書き方 | #1008 /code-review 1 パス目 | 示せる | 捨てる | 計画は成果物でない。記述は直し、U2 は 2 つの関門が独立に確かめた |


- この周の起票: 0 件（振り分けで直すの行が無かった。起票の承認は不在のため訊いていない）
