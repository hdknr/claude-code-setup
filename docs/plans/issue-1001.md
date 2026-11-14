# Issue #1001 — dev-loop: spec-loop から来ていない周が変えた振る舞いを、正本の仕様に戻す道

**不在の周である**——cruise（親 Issue #1014）の子として回す。出所: `/dev-loop:cruise 1014 --absent` の起動（2026-11-14T04:56Z）。
確かめた線（台帳 `issue-1014`。出所: 利用者の確認（起動時・2026-11-14T04:56:18Z、配布を見せて確かめた））:
仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票。
#1001 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1014`））。

依存の追加・更新: なし

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/spec-writeback.md` — 新規。**規定の原本**（いつ申告するか・値・振る舞いを変える周が残すもの・正本が別リポジトリのとき・申告漏れの検出と赤になったときの扱い）
- `plugins/dev-loop/skills/dev-loop/scripts/check-spec-writeback.py` — 新規。正本があるリポジトリで、計画に `仕様の振る舞い:` の申告が無い・`変える` なのに Q&A 表の行（別リポジトリなら計画の `正本に起票する行:`）が無い・緑のケースの一覧から載った行を外した、の周を赤くする（PR の前に素の 1 行で当てる）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 3 の変更範囲の項に原本を指す 1 項、手順 6 の PR の前に当てる 1 項と「終了コードで分岐するスクリプト」の一覧。版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 「Issue が spec-loop から来ていないとき」に原本を指す 1 文
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版（1.107.1 → 1.108.0）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `scripts/test-check-spec-writeback.py` — 新規。回帰テスト（変異テストと、緑のケースの一覧を使った申告漏れの陽性対照を含む）
- `scripts/check-all.py` — 上のテストの収録
- `.github/workflows/plugins.yml` — 上のテストのステップ
- `CLAUDE.md` — `check-spec-writeback.py` と `test-check-spec-writeback.py` の 1 項ずつ
- `docs/plans/issue-1001.md` — この計画

触らない:

- spec-loop の中身（`qa-csv.md`・`req-loop`・`green-list.py`）——起票元 `開発` の行は `spec-gap.md` の「差し戻す」と同じ道で、`req-loop` は今のまま読む。検出は #1000 の `green-list.py check` をそのまま使う
- description（`plugin.json`・`marketplace.json`・frontmatter）——スキルの起動条件は変わらない
- このリポジトリの `check-plan-scope.py` への組み込み——このリポジトリには spec-loop の正本（`docs/v<n>/`）が無く、常に「該当なし」になる
- 公開ページ（`docs/plugins/dev-loop.md`）——依存の申告（#996）と同じく、規定は `references/` にだけ置く

複製の数: 規定の本体は `references/spec-writeback.md` の 1 箇所。`SKILL.md`（手順 3・6 の 2 項）・`spec-gap.md`（1 文）・`CLAUDE.md`（2 項）は指すだけで列挙を持たない。
スクリプトの docstring は終了コードと守る／守らないの正（`check-deps-declared.py` と同じ形）。値の名前（`変える`・`変えない`・`spec-loop の Issue`）は原本とスクリプトの 2 箇所にあり、テストが突き合わせる。
分けない理由: 申告の書き方とスクリプトの判定は同じ周の同じ判断で、指し先が 1 つなら指す側は古くならない。

## 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票` の線）

Issue は「やること（たたき台）」で 2 つを「要確認」「決める」としている。実装に要るので、選択肢を挙げて推奨で決め、穴ごとに確認の Issue を立てる。

1. **振る舞いを変える周が正本に何を残すか**
   - A（推奨）: 作業中の版の共有の Q&A 表（`docs/v<n>/shared/qa.csv`）に、起票元 `開発（#<Issue>）`・回答 `未回答`・状態 `確認中` の行を 1 行足す（`spec-gap.md` の「差し戻す」と同じ道）。仕様（`spec/`・`requirements/`・`shared/` のほかの表）は周の中で直さない
   - B: 作業中の版の仕様を直す差分を、別の PR で出す
   - C: A と B のどちらでもよい
   - 推した理由: 仕様の変更はサインオフ（要求確定・仕様レビュー）を通る決まりで、開発の周が仕様を直すとそれを飛ばす。Q&A 表の行なら次の `req-loop` が拾い、反映されるまで `check-spec-exit.py` が数えるので次の版の仕様レビューを抜けられない——忘れられない。機械でも「行を足したか」を見られる
2. **正本が別のリポジトリのとき**
   - A（推奨）: 開発のリポジトリの `.claude/dev-loop.md` に `仕様の正本: <owner>/<repo>` を宣言する。周は正本へ書きに行かず、起票する行を計画ファイルの `正本に起票する行: ` の行と PR コメントに残して人に渡す（権限が無くても同じ）
   - B: 周が正本のリポジトリに Issue を立てる（`gh` で別のリポジトリへ書く）
   - C: 周が正本のリポジトリに Q&A 表の行を足す PR を出す
   - 推した理由: `spec-gap.md` の「差し戻す」が「別のリポジトリにあるなら、そこへ書きに行かない——起票する行を人間に渡す」と既に決めている（worktree の外を触らない）。権限の有無で手順が分かれない。計画ファイルに 1 行で残すので、機械で「残したか」を見られる

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`docs/plugins/dev-loop-design.md` の生成ブロック）。

## 版の上げ方

dev-loop を minor で上げる（1.107.1 → 1.108.0。能力の追加）——`marketplace.json`・`plugin.json`・dev-loop の全 `SKILL.md`（dev-loop・cruise）の 2 行。
マージの直前に main が進んでいたら、main の先端の dev-loop の版から 1 つ上げた値にする（cruise の `references/parallel.md` の「版とマージの順」）。

## 受入基準（不変条件 × 経路）

Issue の受入基準 4 つ（U1〜U4）を、不変条件と破りうる入口に展開する。入口は `check-spec-writeback.py` の判定（正本の有無・申告・値ごとの残すもの・緑のケースの一覧）と、規定の文書（`spec-writeback.md` と、それを指す `SKILL.md` 手順 3・6）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| W1 (U1) | spec-loop の正本がある（同じリポジトリの `docs/v<n>/`、か `.claude/dev-loop.md` の `仕様の正本:`）リポジトリでは、計画に `仕様の振る舞い:` の申告が 1 本あり、値が決まった 3 つのどれかでないと PR を作れない | 行が無い・値が違う・2 本以上・コードフェンスの中だけ・計画が見つからない・正本が別リポジトリの宣言だけ | スクリプトが 1（計画が見つからなければ 2）。`SKILL.md` 手順 6 が「0 以外なら PR を作らない」 |
| W2 (U1) | 正本が無いリポジトリでは何も求めない | `docs/` があるだけ・`docs/v1-notes/` のような名前 | 正本は `docs/v<数字>/` の下に `shared/`・`requirements/`・`spec/` のどれかがあるときだけ。無ければ申告が無くても 0 |
| W3 (U2) | `変える` の周は、正本（同じリポジトリ）の作業中の版の共有の Q&A 表に、起票元 `開発（#<この Issue>）` の新しい行を足さずには 0 にならない | 行を足していない・内部の表（`qa-dev.csv`）にだけ足した・前の版（凍結）に足した・別の Issue の起票元・既にあった行を書き換えただけ・未コミットの行 | 作業中の版（番号が最大）の `shared/qa.csv` を base の時点と比べ、新しい No の行の起票元が `開発（#<n>）` か。未コミット・未追跡も見る |
| W4 (U2) | `変える` の周で正本が別のリポジトリなら、計画に `正本に起票する行: ` の行（Q&A 表の 1 行の CSV。起票元 `開発（#<n>）`・回答 `未回答`・状態 `確認中`）が無ければ 0 にならない | 行が無い・CSV の列の数が違う・起票元が違う | スクリプトが列を数えて照らす |
| W5 (U3) | 申告漏れ（`変えない` と書いた・申告せずに）で、仕様にある振る舞い（緑のケースの一覧に載った Red テスト）を変えたとき、少なくとも 1 つの機械の検査が赤になる | 実装の値を変えた（`green-list.py check` が 1）・赤になったケースを一覧から手で外して緑に戻した（`check` は base と比べない——#1000 の守らないもの） | 前者は #1000 の `green-list.py check`（テストで陽性対照を取る）。後者は `check-spec-writeback.py` が、`spec-loop の Issue` 以外の値で緑のケースの一覧から載った行（`# accepted-changed:` を含む）が減ったら 1 |
| W6 (U3) | 緑のケースの一覧から載った行が減っても、`spec-loop の Issue`（作り直した `scaffold/` を実装する周）なら赤にしない | 作り直しで機能を消した・`--accept-changed` | 値が `spec-loop の Issue` なら一覧の比べをしない |
| W7 (U3) | `green-list.py check` が赤（1）になったとき、周がどうするか（仕様を直すべき変更か、コードの誤りか）が規定にある | 赤のまま一覧から外す・Red テストを直す | `spec-writeback.md` に、Red テストを直さず・一覧から外さず、コードの誤りなら直し、仕様を直すべき変更なら `spec-gap.md` の「差し戻す」（Red テストと食い違う穴）に従うと書く |
| W8 (U4) | 規定は `references/spec-writeback.md` の 1 箇所にあり、`SKILL.md`・`spec-gap.md`・`CLAUDE.md` は指すだけ | 値・残すもの・正本が別のときの扱いを指す側に列挙する | 読解と `grep`。値の名前はテストが原本とスクリプトで突き合わせる |
| W9 | 指し先が実在する・散文の指し先が当たる・版が 3 種類で 1.108.0・生成ブロックが新しい | `check-skill-pointers.py`・`check-plugin-versions.py`・`check-version-bump.py`・`skill-metrics.py --check` | `check-all.py` |
| W10 | 新しいテストが `check-all.py` と CI に収録されている | 収録漏れ | `test-check-all.py` |
| W11 | 本体の判定は、未コミットの変更・未追跡のファイル・base の時点に無かった Q&A 表（新しい版を足した周）を落とさない | 2 点の差分を 3 点にする・未追跡を見ない・base に表が無いと落ちる | 試料と変異 |
| X1 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目に渡す | — | 再開点で記録 |

**証明できないもの（未証明）**:

- **U1 の「周が申告する」の LLM の振る舞い**——申告の行が無いと PR を作れないこと（W1）は機械で見るが、**値が正しいか**（本当は振る舞いを変えたのに `変えない` と書く）は機械では見えない。
  見えるのは W5 の範囲（緑のケースの一覧に載った Red テストが覆う振る舞い）だけで、Red テストの無い振る舞い（仕様の原文にしかない振る舞い）の申告漏れは赤にならない。Eval はこの周では回さない（`claude` を起こして課金する。CLAUDE.md の「振る舞いを Eval で当てる」）——人間のレビューに回す。
- **`green-list.py check` を製品の CI に載せたこと**——#1000 の雛形の YAML を GitHub Actions の上で走らせていない（#1000 の未証明と同じ）。

**生成物**: `SKILL.md` の測定値（設計 §8.2 の生成ブロック）——dev-loop の `SKILL.md` と `references/` を足すので動く。`skill-metrics.py` で書き直し、`--check` で確かめる。図の書き出しは無し。

## 実機確認

一時ディレクトリに正本（`docs/v1/shared/qa.csv`）と周の形（`issue/<n>-…` のブランチと計画ファイル）を置いて、スクリプトの終了コードを値ごとに見る。
申告漏れの検出は、spec-loop の本物の `scaffold.py` で `scaffold/` を作り、実装の見本と `green-list.py record` で一覧を書いた試料で、
(1) 実装の値を変える → `green-list.py check` が 1、(2) その行を一覧から手で外す → `check` は 0 に戻るが、`変えない` の計画で `check-spec-writeback.py` が 1、を見る（陽性対照: 変える前は両方 0）。
テスト（`scripts/test-check-spec-writeback.py`）がこの流れを持つ。

## 未解決の判断・確認待ち

- 上の「仕様の穴」の 2 つ——確認の Issue を立てる（番号は下の「起票」）。閉じるのは利用者

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1001-spec-writeback`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1001`・起点 `804c5726`・base の参照 `origin/main`・base の SHA `804c57266287f7cad57a26a3a7def43b46a3297d`
- 割り目（手順 4）: 割らない（cruise の周）
- 交絡を潰した手順: （実装後に書く）

## 既知の限界・決着済みの論点

- `仕様の振る舞い:` の値の真偽はスクリプトが見ない（`変えない` と書けば、一覧の行を減らさない限り通る）——見えるのは緑のケースの一覧が覆う範囲だけ（上の「未証明」）
- 正本が別リポジトリのときは、計画に行を残したかまでしか見ない。正本の表に実際に足されたかは見ない（周は書きに行かない決まり）
- 仕様の原文を直す差分（仕様の穴 1 の B）は、この周の決めた値では「残すもの」に数えない

## 起票（手順 8）

- この周の起票: 0 件（確認の Issue を立てたら書き直す）
