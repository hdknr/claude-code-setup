# Issue #994 — spec-loop → dev-loop をモノレポで引き継ぐときのレイアウト

## 変更範囲

触る:

- `plugins/spec-loop/references/monorepo.md` — 新規。モノレポの推奨レイアウト・`build/` を分けない理由・`pyproject.toml` と `.gitignore`・Red テストの走らせ方・CLAUDE.md の分担・開発用の文書・2 つの「版」・CI のパスの分け方
- `plugins/spec-loop/references/tree.md` — 冒頭・「生成物の置き場所」・「scaffold の出力」・「ドキュメントのツール」から `monorepo.md` を指す（列挙は持たない）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 「はじめに」の表と「データの決まり」から `monorepo.md` を指す。版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/.claude-plugin/plugin.json` — spec-loop の版（0.84.0 → 0.85.0）
- `.claude-plugin/marketplace.json` — 同上
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
  - 1 パス目の結果: Verifier（sonnet・dev-loop:dev-loop-verifier）反証 2 件、/code-review（high）指摘 10 件（うち 2 件は Verifier と同じ）。採否は下の表——直す 8・残課題 2。手順 4 への差し戻し 1 回（指摘対応）
  - 1 パス目の指摘対応のコミット: `329eb6122b67b4393aa9de18f0a4e7c88b2da867`（差分は 0 行でない——2 パス目を回す）
  - 割り目 2（2 パス目の前）: AskUserQuestion で訊いた。10 分答えが無く、先に「続けて」と言われていたので続けた（2026-11-13）
  - 2 パス目: 手順 5 の当て直し（Verifier）と /code-review 2 パス目に渡した。2 パス目の指摘対応の起点（狭いパスの起点）は `655e953185a1c0892f31372142076091dcd38d6f`
  - 2 パス目の結果: Verifier 反証 0 件（受入基準に反するもの。軽微 1 件は残課題 V2-1）、/code-review 指摘 8 件——直す 7・残課題 1。直した行に狭いパスを当てる——起点 `655e953`・終点 `567eaae24380fad0510d088c278809929d959f44`
  - 狭いパスの結果: Verifier（sonnet）反証 0 件。軽微 2 件（N-m1・N-m2）は直さず人間に渡す。Verifier の変異 3 本: 2 本は実行して主張どおり、1 本はコードの読解だけ（未実行）。素通りして穴と言える変異は無し
- 割り目 1（手順 4 の後）: 訊かずに続けた——利用者が「続けて」と指示（2026-11-13）
- 交絡: 上の「実験」（陽性対照: `WRONG_IMPL` で失敗すること）

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| `build/` を `build/spec-loop/` に移すべき | — | — | 採らない（利用者が「移さず理由を書く」を選んだ。理由は `monorepo.md`） |
| V1-1: scaffold の `SKILL.md` の「はじめに」の表の途中に段落を挟み、後ろの 2 行（Issue の登録先・commit の決まり）が表から外れた | 示せる（`sed -n 47,63p`。表の行が段落の後ろに残る） | A1 | 直す |
| V1-2: `monorepo.md` の「`--red-check` も緑になることを確かめた。誤った実装で失敗する」は、v1 の `--red-check` が正しい実装・付け忘れ・誤った実装のどれでも 0 を返すので、`--red-check` について判別していない | 示せる（Verifier が 3 通りを走らせて全部 0） | A4 | 直す |
| R1-1: V1-1 と同じ（表が切れる）。加えて新しい行の「無いとき」と段落の「利用者に確かめる」が食い違う | 示せる（同上） | A1 | 直す（段落を表の後ろへ。行の「無いとき」に確かめる条件を入れた） |
| R1-2: V1-2 と同じ | 示せる | A4 | 直す |
| R1-3: Issue の本文の「回し方」は `PYTHONPATH` を持たず、実装の場所はモジュール名だけ。dev-loop はそれを写すので、`monorepo.md` が dev-loop の経路を覆っていない | 示せる（`scaffold.py:2286` の本文の行） | A3 | 直す（`monorepo.md` に 4 番目の項と、`CLAUDE.md` の雛形に行を足した。`scaffold.py` の本文は変えない） |
| R1-4: workspace で `--all-packages` の後に素の `uv sync` を走らせると member が消える | 示せる（著者も再実行。`Uninstalled 1 package - backend`→`ModuleNotFoundError`） | A3 | 直す |
| R1-5: 「`PYTHONPATH` はどちらの形でも使える」は依存の無い試料でしか確かめていない | 示せる（試料の実装は標準ライブラリだけ。`--red-check` は `sys.executable`） | A4 | 直す（主張を確かめた範囲に弱め、依存のある形は確かめていないと書いた） |
| R1-6: 「v1 の `--red-check` が 0」は狭い。回帰のケースが無い版（全部を足した・変えた版、`impl_module` を変えた版）も 0 | 示せる（`scaffold.py` の `red_check`: 2 で止まるのは回帰のケースがあり全部が「未実装」のときだけ） | A3 | 直す（`monorepo.md`・scaffold の `SKILL.md`・公開ページ） |
| R1-7: `render-diagrams.py` は `docs/` 全体を歩くので、`docs/dev/` の図もその検査に入る | 示せる（`render-diagrams.py:137`） | 無し（A7 はサインオフと重ね合わせ） | 残課題 |
| R1-8: `release-v<n>` を読むのは `check-frozen.py` だけでなく `scaffold.py`（前の版の凍結）もで、影響の書き方が狭い | 示せる（`scaffold.py:32`） | 無し（A6 の「衝突を避ける形を書く」は満たす） | 残課題 |
| R1-9: 「正本の `CLAUDE.md` が先に立つ」の出典に挙げた `tree.md` の「プロジェクトに任せること」は、置き場所について言っていない | 示せる（`tree.md` の同節はドキュメントの道具・サイト・スライドだけ） | A8 | 直す（出典を外し、推奨であると書いた） |
| V2-1（2 パス目）: `monorepo.md` が `--red-check` のメッセージを「回帰のケースを判定していない」と引用符つきで書くが、実際は「回帰のケース N 件を判定していない」 | 示せる（`scaffold.py:2761`） | 無し | 残課題 |
| R2-1（2 パス目）: 「全部の機能を足したか変えた版」は回帰のケースが無い版ではない——回帰はケースごとに決まり、変更の機能の変わらないケースは回帰 | 示せる（`rev2.py`: 変更 2・追加 0 の v2 で付け忘れると rc=2「回帰のケース 2 件を判定していない」。著者も再実行） | A3・A4 | 直す（条件を「変わらないケースが 1 つも無い版」にした） |
| R2-2: workspace の主張は `backend/src/app` と hatch の `packages` の形で確かめたが、文書はそれを言わず `backend/app/` を勧める。その形では `uv sync --all-packages` が失敗する | 示せる（`revflat.sh`。著者も再実行して rc=1・`ModuleNotFoundError`） | A4 | 直す（確かめた形を書き、`backend/app/` のままでは member を作れないことがあると書いた） |
| R2-3: 撤去の本文の「回帰」と変更の本文の「ほかの機能を含む回帰」のコマンドも `PYTHONPATH` を持たない | 示せる（`scaffold.py:2265-2268`・`2295-2296`） | A3 | 直す（項 4 と雛形を「本文の `unittest` のコマンドすべて」に広げた） |
| R2-4: 実装の CI の例が `scaffold/tests` を全部回し、版を実装し終えるまで赤い | 示せる（Red テストは未実装の機能で失敗する——`scaffold.py` の本文「実装が無い状態では、ケースの数だけ失敗する」） | A3（CI の経路） | 直す（例に注記し、周ごとには Issue の `-p` で絞ると書いた） |
| R2-5: 性能テスト（`scaffold/perf/`）も同じ読み込み方で、同じ `PYTHONPATH` が要る | 示せる（`scaffold.py:1461-1471` の `IMPLEMENTATION` を共有。`2390` の回し方） | A3 | 直す（R2-3 と同じ項で覆った） |
| R2-6: `import` の 1 行は `PYTHONPATH` を自分で付けるので、テストのコマンドに付けたかは見分けない | 示せる（1 行目が通り、`PYTHONPATH` 無しの `--red-check` が v1 で 0） | A3（「見分ける 1 行」） | 直す（1 行が見分けるのは置き場所までと書き、テストの出力で見分ける形を足した） |
| R2-7: workspace の形での落とし穴の確かめ方が無い（`import` の 1 行は `PYTHONPATH` の形） | 示せる（R2-2・R1-4 と同じ実験） | A3 | 直す（workspace の形の確かめ方を足した） |
| R2-8: 落とし穴の条件を scaffold の `SKILL.md` と公開ページでも言い直していて、3 箇所の同期が要る | 示せる（3 箇所の文言） | 無し（2 箇所の「v1 など」は R2-1 の後も正しい） | 残課題 |
| N-m1（狭いパス）: 「`--red-check` の終了コードは、読み込めているかを決めない」は強い——変わらないケースのある版では付け忘れで 2 になる | 示せる（`rev2.py`） | 無し（直後の本文が版による違いを書く） | 人間が決める |
| N-m2（狭いパス）: 「足した・変えたケースで失敗するように作る」は「もう緑」を含めると厳密には「失敗しうる」 | 示せる（`rev2.py` の出力の「もう緑 1 件」） | 無し | 人間が決める |
| R1-10: 生成物の一覧が `tree.md` の表と合わず、`build/merged-v<n-1>/` が抜けている | 示せる（`build/merged-v<n-1>` は references・SKILL に 6 箇所） | A2 | 直す（一覧に足し、出典を直し、「直下の `build/` の下に実装の出力を置かない」にした） |
