# Issue #1000 — spec-loop: scaffold の Red テストを製品の CI で走らせ続ける決まり

**不在の周である**——cruise（親 Issue #1014）の子として回す。出所: `/dev-loop:cruise 1014 --absent` の起動（2026-11-14T04:56Z）。
確かめた線（台帳 `issue-1014`。出所: 利用者の確認（起動時・2026-11-14T04:56:18Z、配布を見せて確かめた））:
仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票。
#1000 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1014`））。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/green-list.py` — 新規。`scaffold/tests` の Red テストを走らせ、緑のケースとその中身の指紋を一覧（既定 `scaffold-green.txt`）に書く `record` と、一覧に載ったケースが緑のままかを見る `check`
- `plugins/spec-loop/references/tree.md` — 「scaffold の出力」の後ろに「Red テストを CI で走らせ続ける」の節（決まりの原本。対象の選び方・一覧の書き方・性能テストの扱い・別リポジトリの形・GitHub Actions の雛形）
- `plugins/spec-loop/references/monorepo.md` — 「CI のパスの分け方」の最後の段落（全部を回す検査は赤い）を、原本を指す形に直す
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 手順 7 の「次にすること」に、原本を指す 1 項。版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/README.md` — 中身の表に `scripts/green-list.py` の 1 行と、scaffold の節の使い方の 1 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.86.1 → 0.87.0）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/spec-loop.md` — Red テストの節に、CI で回し続ける決まりを指す 1 項
- `scripts/test-green-list.py` — 新規。回帰テスト（変異テストと、別リポジトリの形の陽性対照を含む）
- `scripts/check-all.py` — 上のテストの収録
- `.github/workflows/plugins.yml` — 上のテストのステップ
- `CLAUDE.md` — `green-list.py` と `test-green-list.py` の 1 項ずつ
- `docs/plans/issue-1000.md` — この計画

触らない:

- `scaffold.py` の生成物の形（Red テストの中身・`scaffold/` の置き方）——一覧は `scaffold/` の外に置く（`scaffold/` は生成物で、`--check` の範囲）
- dev-loop の `SKILL.md`・`spec-gap.md`・Issue の本文の形（`handoff-issue.md`）——一覧を書き直すのは、CI が赤（3）で名指ししたときの PR の作業で、dev-loop の手順は変えない（周を回す側が CI を見れば足りる）
- 性能テスト（`scaffold/perf/`）をマージごとの CI で回すこと（下の「仕様の穴」の 2）
- 一覧から手で行を消す改ざんを CI で見ること（`git` の base の一覧と比べる形）——守らないものとして docstring に書く
- description（`plugin.json`・`marketplace.json`・各 frontmatter）——スキルの起動条件は変わらない

複製の数: 決まりの本体は `references/tree.md` の新しい節の 1 箇所。`monorepo.md`（1 段落）・scaffold の `SKILL.md`（1 項）・README（2 行）・公開ページ（1 項）・`CLAUDE.md`（2 項）は指すだけで列挙を持たない。
スクリプトの docstring は終了コードと守る／守らないの正（`CLAUDE.md` の他の項と同じ形）。分けない理由: 指し先が 1 つなら本体を直しても指す側は古くならない。

## 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票` の線）

Issue は「やること（たたき台）」で 3 つを「決める」としている。実装に要るので、選択肢を挙げて推奨で決め、穴ごとに確認の Issue を立てる。

1. **CI で走らせる Red テストの選び方**
   - A（推奨）: 緑のケースの一覧（`scaffold-green.txt`。ケースの名前とその中身の指紋）を `green-list.py record` が機械で書き、CI の `check` は一覧に載って指紋の同じケースが緑のままかを見る。緑なのに一覧に無い・指紋が変わった・消えたケースは「一覧が古い（3）」で赤にして、その PR で `record` させる
   - B: scaffold の Issue の状態（閉じた機能）から選ぶ——CI から `gh` で GitHub を引く・Issue の番号と機能の対応が要る・閉じた後の作り直しで食い違う
   - C: 中間表現に「実装済み」の印を足す——実装の状態を仕様（正本）に書くことになり、機能の指紋が変わって dev-loop の点検が合わなくなる
   - 推した理由: 製品のリポジトリの中だけで決まり（GitHub も正本も引かない）、実装したことを Red テストの結果そのもので数える。指紋で「仕様が変えたケース」を「壊したケース」と分けられる
2. **性能テスト（`scaffold/perf/`）を毎回走らせるか**
   - A（推奨）: マージごとの CI には入れない。回すなら別のジョブ（手で起こすか定時）にし、マージの条件にしない
   - B: 毎回走らせてマージの条件にする
   - 推した理由: 性能テストは受入基準ではなく（`nfr.md`）、CI の機械の速さで結果が揺れる。回帰の検査（Red テスト）と混ぜると、揺れで赤になったものを「性質を壊した」と読む
3. **別リポジトリのとき、写した `scaffold/` が正本と同じ時点かを CI でどう確かめるか**
   - A（推奨）: 写すときに正本のリポジトリとコミットを開発のリポジトリのファイル（`scaffold-source.txt`。`<owner>/<repo>@<コミット>` の 1 行）に書き、CI はその時点の正本を取って `scaffold.py --check`（正本の `scaffold/` が仕様から見て新しい）と `diff -r`（写しが正本の `scaffold/` と同じ）を当てる
   - B: 正本を git submodule にして `scaffold/` を指す——写しが無くなるが、開発のリポジトリの構成を変える
   - C: CI では確かめず、写す人に任せる——受入基準の 4 を満たさない
   - 推した理由: 開発のリポジトリの構成を変えずに、受入基準の 4（CI で確かめられる）を満たす。`spec-gap.md` の「写し方と確かめ方」と同じく、比べる相手の時点を名指しする

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`docs/plugins/spec-loop.md` を変える）。

## 版の上げ方

spec-loop を minor で上げる（0.86.1 → 0.87.0。能力の追加）——`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行。
マージの直前に main が進んでいたら、main の先端の spec-loop の版から minor で 1 つ上げた値にする（cruise の `references/parallel.md` の「版とマージの順」）。

## 受入基準（不変条件 × 経路）

Issue の受入基準 4 つ（U1〜U4）を、不変条件と破りうる入口に展開する。入口は `green-list.py` の 2 つの口（`record`・`check`）と、決まりの文書（`tree.md` の節と雛形のジョブ）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 (U1) | Red テストを製品の CI で走らせ続ける決まりが 1 箇所（`tree.md` の新しい節）にあり、ほかは指すだけ | `monorepo.md` の CI の節・scaffold の `SKILL.md`・README・公開ページが列挙を持つ | 原本は `tree.md`。ほかは指し先だけ |
| A2 (U2) | 実装していない機能の赤で CI が落ちない——`check` が見るのは一覧に載ったケースだけ | 一覧が無い（v1 で何も実装していない）・一部の機能だけ実装・v2 で作り直して追加・変更のケースが赤 | 一覧に無いケースの失敗は数えない。指紋の変わったケースは「壊した」に数えない（3 で一覧の書き直しを求める） |
| A3 (U2) | 対象は機械で選ぶ——一覧は `record` が Red テストの結果から書く | 手で一覧を書く・`record` が落ちているケースを足す・`record` が指紋の同じ載ったケースを黙って落とす | `record` は緑のケースだけを書き、載っていて指紋の同じケースが緑でなければ何も書かずに 1 |
| A4 (U3) | 実装済みの機能の性質を壊すと CI（`check`）が赤（1）になり、壊したケースを名指しする（陽性対照） | 実装の値を変える・関数を消す・例外を投げる・`PYTHONPATH` の付け忘れで全部が「未実装」 | テストで実装を壊して `check` が 1 を返すことを見る（陽性対照: 壊す前は 0） |
| A5 (U3) | 指紋は「そのケースの Red テストが実行する中身」で決まる——同じ機能の別のケースや題・コメントが変わっても変わらず、そのケースの期待・呼び出し・共通の部分（型・実装のモジュール名）が変われば変わる | 題だけ直した作り直し・別のケースだけ変えた作り直し・出力の型の変更・`impl_module` の変更 | AST でテストのメソッドの行を取り、コメントと空行を除いた共通の部分とそのメソッドの行から sha256 |
| A6 (U4) | 別リポジトリの形でも、写した `scaffold/` が正本の名指しした時点と同じかを CI で確かめられる | 写しを手で直した・正本を作り直したのに写していない・正本の `scaffold/` が仕様より古い | 雛形のジョブは `scaffold.py --check`（正本）と `diff -r`（写し）を当てる。テストで、写しを変えると `diff` が非 0、正本の仕様だけ変えると `--check` が 1 を見る |
| A7 | 性能テストの扱いが決まりに書いてある（マージごとの CI に入れない） | 雛形のジョブが `scaffold/perf` を回す・一覧が `perf/` を数える | `green-list.py` は `scaffold/tests` だけを見る。雛形のジョブは perf を回さない |
| A8 | 雛形のジョブが走らせるコマンドが、テストで確かめたコマンドと同じ | 雛形だけ別のフラグ・別の順 | 雛形のコマンドの行をテストと同じ形にする（`--repo`・`check`） |
| A9 | 指し先が実在する・散文の指し先が当たる・版が 3 種類で 0.87.0・description の 2 つの JSON が一致する | `check-skill-pointers.py`・`check-site-links.py`・`check-plugin-versions.py`・`check-version-bump.py`・`check-description-sync.py` | `check-all.py` |
| A10 | 新しいテストが `check-all.py` と CI に収録されている | 収録漏れ | `test-check-all.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目に渡す | — | 再開点で記録 |

**証明できないもの（未証明）**: 雛形の GitHub Actions のジョブ（YAML）を GitHub Actions の上で走らせること——この周の環境では走らせない（外部に試しのリポジトリを作ることになる）。
走らせるコマンドはテストで確かめるが、`actions/checkout` の引数・別リポジトリの取り出しの権限は人間のレビューに回す。

**生成物**: `SKILL.md` の測定値（設計 §8.2 の生成ブロック）は dev-loop の `SKILL.md` だけを測るので、spec-loop の変更では動かない——`skill-metrics.py --check` で確かめる。
図の書き出しは無し。`scaffold/` の生成物の形は変えない（`test-scaffold.py` が見る）。

## 実機確認

一時ディレクトリに正本（`docs/v1/`）と実装の見本（`spec_impl.py`）を置き、本物の `scaffold.py` で `scaffold/` を作り、
`record` → `check`（0）→ 実装を壊して `check`（1）→ 戻して v2 で 1 つのケースを変えて作り直して `check`（3）→ `record` → `check`（0）を走らせる。
別リポジトリの形は、正本と開発の 2 つのディレクトリで `scaffold.py --check` と `diff -r` を当てる。テスト（`scripts/test-green-list.py`）がこの流れを持つ。

## 未解決の判断・確認待ち

- 上の「仕様の穴」の 3 つ——確認の Issue（番号は下の再開点）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1000-scaffold-red-ci`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1000`・起点 `3aa4f0b7`・base の参照 `origin/main`・base の SHA `3aa4f0b70b3bc519871679bfc01ca7614030c7bd`
- 割り目（手順 4）: 割らない（cruise の周）
- Verifier: 未
- `/code-review`: 未
- 手順 5 の反証と差し戻し: 未
- 交絡を潰した手順: 未

## 既知の限界・決着済みの論点

- 一覧から手で行を消すと、そのケースは見られなくなる（`check` は base の一覧と比べない）——PR の差分で見える。docstring の「守らないもの」に書く
- 指紋が変わったケースは、`record` するまで見られない（作り直しで型や `impl_module` を変えると、その機能の全ケースが一度外れる）——`check` は 3 で赤にして書き直しを求めるので、黙っては外れない

## 起票（手順 8）

- この周の起票: 3 件（`仕様の穴` の線で推奨により決めた 3 つの確認の Issue。起票の承認は不在のため訊いていない）
