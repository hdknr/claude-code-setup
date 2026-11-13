# Issue #994 — spec-loop → dev-loop をモノレポで引き継ぐときのレイアウト

## 変更範囲

触る:

- `plugins/spec-loop/references/monorepo.md` — 新規。モノレポの推奨レイアウト・`build/` を分けない理由・`pyproject.toml` と `.gitignore`・Red テストの走らせ方・CLAUDE.md の分担・開発用の文書・2 つの「版」・CI のパスの分け方
- `plugins/spec-loop/references/tree.md` — 冒頭・「生成物の置き場所」・「scaffold の出力」・「ドキュメントのツール」から `monorepo.md` を指す（列挙は持たない）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 「はじめに」の表と「データの決まり」から `monorepo.md` を指す。版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — spec-loop の版（0.84.0 → 0.85.0）
- `docs/plugins/spec-loop.md` — 公開ページから `monorepo.md` を指す 1 項
- `docs/plans/issue-994.md` — この計画

触らない:

- `build/` の出力先の移動（`build/spec-loop/` へ寄せる）——利用者が「移さず理由を書く」を選んだ（2026-11-13・手順 3 の回答）。理由は `monorepo.md` に書く
- `init-mkdocs.py` と雛形の `pyproject.toml`・`gitignore` の中身——workspace に足す形は、雛形を変えずに 1 節足せば済むことを確かめた（下の実験）。雛形を変えると既存の正本には届かない（`tree.md` の「既に雛形を写した正本には、新しい雛形は届かない」）
- `scaffold.py`（Red テストの読み込み方）——`PYTHONPATH` か workspace で読み込めることを確かめた。コードは変えない
- dev-loop の README・SKILL.md——dev-loop は `CLAUDE.md` と `.claude/dev-loop.md` を読むだけで、モノレポでの分担は正本側（spec-loop）の決め事として `monorepo.md` に書く。dev-loop の版を上げずに済ませる（受入基準の外）

複製の数: レイアウトの本体は `monorepo.md` の 1 箇所。`tree.md`（4 箇所）・scaffold の `SKILL.md`（2 箇所）・公開ページ（1 箇所）は指すだけで列挙を持たない。分けない理由: 指し先が 1 つなら、本体を直しても指す側は古くならない。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`docs/plugins/spec-loop.md` を変える）。

## 実験（交絡を潰した手順）

`/private/tmp/.../scratchpad/mono.py`（一時ディレクトリだけを触る。試料は `scripts/test-scaffold.py` の `IR`・`GOOD_IMPL`・`WRONG_IMPL` を読み込む）:

- 実装を `backend/app/spec_impl.py`、`impl_module` を `app.spec_impl` にして `scaffold.py` で生成。
- `PYTHONPATH` 無しで `python3 -m unittest discover -s scaffold/tests` → 3 件とも **「未実装: app.spec_impl.can_cancel が無い」で失敗**（読み込めないことと未実装が同じ出力）。
- `PYTHONPATH=backend` → 3 件緑。**陽性対照**: 同じ形で `WRONG_IMPL` に替えると 3 件失敗（実装を実際に読んでいる）。
- `--red-check` は `PYTHONPATH=backend` で「もう緑 3 件」、**`PYTHONPATH` 無しで 0（失敗 3 件・期待どおり）**——v1 では付け忘れが黙って通る。
- `merge-versions.py docs build/merged` は `docs/dev/adr-001.md` を重ねない（出力は `v1` の 3 ファイルと印だけ）。

`uvws.sh`（uv 0.11.14・CPython 3.12.8）: 雛形の `pyproject.toml` に `[tool.uv.workspace] members = ["backend"]` を足すと `uv lock` が通り、`uv sync` だけでは `import app` できず、`uv sync --all-packages` の後はできる。**workspace の形で `--red-check` を走らせることは確かめていない**（確かめたのは `import` まで）。

観測窓: Python 3.14.3（手元）で Red テストを走らせた。CI の 3.12 では走らせていない（`scaffold.py` の Red テストは標準ライブラリだけ）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | `monorepo.md` を読めば、実装をどこに置き、何を CLAUDE.md に書けばよいかが分かる（Issue の受入基準 1） | 読み手が `tree.md`・scaffold の `SKILL.md`・公開ページのどれから入っても | 3 つの入口から指す。推奨のレイアウトの木と、CLAUDE.md に書く項目の雛形を置く |
| A2 | spec-loop の生成物と実装のビルドの出力先について、分けない理由が書かれている（受入基準 2） | 実装を直下に置く形・`build/` を使うビルド道具 | 理由（実装はサブディレクトリ・`.gitignore` の `build/` はどの階層にも効く・移すと壊れる変更）と、直下に置くときの注意を書く |
| A3 | 実装をサブディレクトリに置いたモノレポで Red テストを走らせる手順が文書にある（受入基準 3） | `python3 -m unittest`・`--red-check`・dev-loop の周・CI | `PYTHONPATH` と workspace の 2 つの形。**付け忘れが「未実装」と同じに見える落とし穴と、それを見分ける 1 行**を書く |
| A4 | 文書が主張する挙動は実験で確かめた範囲だけで、確かめていないことはそう書く | workspace で `--red-check`・Claude Code のサブディレクトリの CLAUDE.md の読み込み | 「確かめていない」と書く。読み込みの仕組みは断定しない |
| A5 | `impl_module` を最初の scaffold の前に決めることが書かれている | 後から変える | `spec-ir.md` の決まりを指す |
| A6 | アプリのリリースのタグが凍結のタグ（`release-v<n>`）と衝突しないことが書かれている | アプリが `release-v1` を付ける | `check-frozen.py` の命名を挙げ、避ける形を書く |
| A7 | 開発用の文書の置き場所（`docs/dev/`）がサインオフ・重ね合わせに混ざらない | `docs/v<n>/` の下に置く・`v` と数字で始まる名前 | 実験で確かめた範囲を書き、`v<数字>` で始まる名前を避けることを書く |
| A8 | 指し先が実在する・散文の指し先が当たる | `check-skill-pointers.py`・`check-site-links.py` | `check-all.py` |
| A9 | 版は 3 種類で 0.85.0 | 上げ忘れ | `check-plugin-versions.py`・`check-version-bump.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と /code-review の両方 × 1・2 パス目に渡す | — | 再開点で記録 |

**証明できないもの（未証明）**: Claude Code がサブディレクトリの `CLAUDE.md` をいつ読み込むか（ハーネスの挙動。文書は断定せず公式の説明を指す）。

**生成物**: `SKILL.md` の測定値（設計 §8.2 の生成ブロック）は dev-loop の `SKILL.md` だけを測るので、spec-loop の版の行の変更では動かない——`skill-metrics.py --check` で確かめる。図の書き出しは無し。

## 未解決の判断

- 無し（直す線と `build/` の扱いは手順 3 で利用者が決めた）。

## 起票

- この周の起票: 0 件（起票の候補なし）

## 直す線

`既定`（出所: 手順 3 の回答 2026-11-13）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/994-spec-loop-monorepo`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-994`・起点 `90a9c503`・base `origin/main` → `90a9c503c6a9fd1ef1e77036909434a4f5696350`
- 関門: 1 パス目（Verifier・/code-review）に渡した。1 パス目の指摘対応の起点 `d570055d7d21f637aa8afcada1f01e2d40ba93cd`
- 割り目 1（手順 4 の後）: 訊かずに続けた——利用者が「続けて」と指示（2026-11-13）
- 交絡: 上の「実験」（陽性対照: `WRONG_IMPL` で失敗すること）

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| `build/` を `build/spec-loop/` に移すべき | — | — | 採らない（利用者が「移さず理由を書く」を選んだ。理由は `monorepo.md`） |
