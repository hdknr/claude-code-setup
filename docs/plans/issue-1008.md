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
- 関門: 未着手
- 反証と差し戻し: 未着手
- 交絡: 実験 1 つ（U2）。一時ディレクトリ（scratchpad）に、`setup.py` が build のたびに印のファイルへ 1 行書く sdist だけの path 依存を持つ uv の project を作り、`uv lock` の後に
  `uv run --no-sync python -c …`（印のファイルが作られない）と `uv run --frozen python -c 'import markerdep'`（`Built markerdep` と出て印のファイルに 2 行）を比べた。
  陽性対照は `--frozen` の側（同じ観測点で build が起きると印が出ることを示す）。`UV_CACHE_DIR` を一時ディレクトリに向け、手元のキャッシュの wheel で build が飛ばされる形を外した。観測窓: uv 0.11.14・1 回ずつ・path 依存の sdist（レジストリの sdist では試していない）。

## 既知の限界・決着済みの論点

- **`--frozen` を消さずに「sync は止めない」と添えた**——Issue の受入基準は「同じ効き目のものとして並べない」で、並べないまま違いを書けば、`--frozen` を付けて済ませる読み方を塞げる。消すだけにする形は採らなかった（理由: 元の文が `--frozen` を挙げていたので、読んだことのある体が同じものと思い込んだままになる）。
- **`--locked` には触れない**——lockfile が変わらないことを確かめるだけで、sync は止めない（`uv run --help`）。557 行目は `--locked` を挙げていないので、足さない。
- **`UV_NO_SYNC` の環境変数・`[tool.uv]` の設定で止める形は書かない**——Issue の範囲の外（557 行目は引数の形で案内している）。

## 経験の還元（手順 8）

- この周の起票: 0 件（起票の承認は不在のため訊いていない。周の途中の課題の振り分けで直すの行が出たら直す）
