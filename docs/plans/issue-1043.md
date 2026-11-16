# Issue #1043 — dev-loop: 関門を通ったかをスクリプトで照合してからマージする

cruise（親 Issue #1075）の子として回す周。**不在の周**（出所: `/dev-loop:cruise 1075 --absent` の起動・2026-11-16）。AskUserQuestion は使わない。
spec-loop から来た Issue ではない。`作り直しの元:` の行も無い。`find-cycle.py 1043` は 5 本とも当たらず、新規の周。

台帳の確かめた線（出所: cruise の確かめた線（台帳 `issue-1075`）。親の委譲文で受け取った）:
直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた。**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。

直す線: `既定`（出所: cruise の確かめた線）。

重い検査は `run-serial.py` 越しに回す——`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.111.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。関門にも渡す（並行の検査 1 本・宣言なし）。
この周は導入済みの dev-loop 1.111.0 で回る——この周が足す照合は、この周のマージにも cruise の後の周にも効かない（`plugin update` まで）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-gates.py` — 新設。計画ファイルの関門の記録（`dev-loop-gates` のブロック）を照合する。記録の形の原本は docstring
- `scripts/test-check-gates.py` — 新設。回帰テスト（一時の git リポジトリ）と変異テスト（「守る」の行と 1 対 1）と陽性対照
- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — `gh pr merge` の前に `check-gates.py` を通す段（終了コード 13）・`--plan`・`--absent`・docstring
- `scripts/test-merge-pr.py` — 試料の worktree に通る計画を置く・照合で止まる試料・変異・写す隣のファイル
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 3（再開点に記録を書く）・手順 6（終了コードで分岐するスクリプトの一覧）・手順 7（マージの前に照合を通す。どの経路でも）
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「マージ = 関門を通ればマージ」の止まる条件のうち照合が見るもの・`--absent` で呼ぶこと
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 4（`merge-pr.py --absent`・13 の扱い）・版の 2 行
- `docs/plugins/dev-loop-cruise.md` — 道具の表の `merge-pr.py` の行に照合を足す
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない）
- `scripts/check-all.py` — `test-check-gates.py` を収録
- `.github/workflows/plugins.yml` — `test-check-gates.py` のステップ
- `CLAUDE.md` — プロジェクト構成に `check-gates.py`・`test-check-gates.py`
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.111.0 → 2.0.0）
- `.claude-plugin/marketplace.json` — 同じ版
- `docs/plans/issue-1043.md` — この計画

触らない:

- Issue の提案 3（受入基準ごとに終了コードで合否が決まるコマンドを計画に書かせ、照合スクリプトが再実行する）——Issue が「可能なら」としている。計画に書いたコマンドを照合が走らせると、
  PR の中身が決めるコマンドがマージの直前にメインの作業ツリーで走る（信頼できない入力の実行・重い検査の順番待ち）——別の周で形を決める。PR コメントの残課題に書く
- `references/resume.md`——再開点の書式は `SKILL.md` 手順 3 の 5 番目にあり、`resume.md` は再開の手順（入り方）を持つだけ。記録の形の原本は `check-gates.py` の docstring に置き、`SKILL.md` から指す
- #1047 の判定（影響範囲・ロールバックの履歴）——照合に判定を足す口（`CHECKS`）だけ用意する
- 狭いパスの指摘の振り分け・PR コメントの推奨の読み直し・CI・宣言の外の反映の照合（ワークフローの読み）——今までどおり親のモデルと `merge-pr.py` の既存の段
- `prompts/`（関門の委譲文）・`ledger.py`・`check-unattended-env.py`

依存の追加・更新: なし
仕様の振る舞い: 該当なし（このリポジトリは spec-loop の正本ではない）

版の上げ方: dev-loop を **major**（1.111.0 → 2.0.0。3 種類: `marketplace.json`・`plugin.json`・dev-loop の全 `SKILL.md`（`dev-loop`・`cruise`）の 2 行）。
理由: `merge-pr.py` が関門の記録の無い計画の PR をマージしなくなる——既存の使い方が壊れる変更（`CLAUDE.md` の刻み方の表）。
並行する周が先に dev-loop の版を上げてマージしたら、マージの直前に子が取り込みと上げ直しをする（`parallel.md` の「版とマージの順」。上げ直す値は main の先端の版から major を 1 つ）。

## 決めたこと（Issue が周に委ねた範囲）

- **照合の置き場所**（Issue の提案 2「新設するか、`merge-pr.py` の前段に置くか」）: 両方——新設の `check-gates.py` が照合し、`merge-pr.py` が `gh pr merge` の前に呼ぶ。
  `SKILL.md` 手順 7 は、`merge-pr.py` を使わない経路（リポジトリの runbook の手順・`gh pr merge`）でもマージの前に素の 1 行で呼ぶことを必須にする。
- **記録の形**: 計画ファイルの中の 1 つのコードブロック（情報文字列 `dev-loop-gates`）に、1 行 1 記録。原本は `check-gates.py` の docstring。
  関門の記録は「その関門に渡した時点の HEAD（終点）」で、照合は**周の base から head までの、周自身の線（first-parent）のコミットを 1 つずつ**、それを見た関門があるかで見る
  ——「狭いパスの SHA が PR の head と一致するか」（Issue の提案 2 の 1 つ目）を一般にした形（狭いパスの後の計画のコミット・版の上げ直し・main の取り込みを通すため）。
- **関門が見ていなくても通すコミット**: 計画ファイルだけを変えたもの・版の行（`"version":`・`skill-version` の印・`このスキルの版:` の行）だけを変えたもの・
  既定ブランチ（`origin/HEAD`→`origin/main`→`origin/master`）に入っている親を取り込んだ merge commit。
- **受入基準の判定**: 計画の受入基準の表（見出しに「受入基準」を含む節の、第 1 列の見出しが `#`・`番号`・`ID` の表）の番号ごとに `満たす`・`満たさない`・`BLOCKED`・`未証明` の 1 つ。
  表の番号に判定が無ければ通さない。`未証明` は通す（PR コメントで人間のレビューに回す——手順 6）。
- **`マージの反映:` の出所**（Issue の提案 2 の 3 つ目）: 記録に書いた値（`なし` 以外）が、既定ブランチの `.claude/dev-loop.md` にちょうど 1 本ある値と同じでなければ通さない。
  `--absent`（不在の周のマージ）では記録が要る。
- **不在の周の印**: `check-gates.py --absent`。`merge-pr.py --absent` が渡す。cruise の親は `--absent` の cruise で `merge-pr.py <PR> --absent` と呼ぶ。

## 仕様の穴（不在の線で推奨により決めた）

- **穴 G1**: Issue の提案 2 は「BLOCKED・満たさないが残っていないか」を照合するとし、受入基準は 1 つでも残れば止める形に読める。一方、既存の決まりは
  (a) 手順 5・6——居る周では BLOCKED・満たしていない受入基準を、人間が判断してマージを決める、
  (b) `absent-lines.md` の「マージ前の判断 = 推奨で決めて起票」（#1037。利用者の決定 2026-11-15）——不在の cruise で `実機確認` の線の外の BLOCKED を推奨でマージする、
  (c) 「実機確認 = Refs でマージ」——実機の BLOCKED を Refs でマージする、
  を許している。Issue の文面どおりに作ると (a)〜(c) の経路が塞がる（「回答どおりに作ると、別の回答と両立しない」——`spec-gap.md` の「何が仕様の穴か」）。
  - 選択肢 A（推奨）: `BLOCKED`・`満たさない` は、判断の出所（`判断=`）を記録した行だけ通す。出所は `利用者の指示（<日付>）`（両方）・`マージ前の判断`（`BLOCKED` だけ・`--absent` だけ）・`実機確認`（`BLOCKED` だけ・`--absent` だけ）。
    `満たさない` を線で通さない（#1037 が「満たしていない受入基準は推奨に回さない」と決めた）。
  - 選択肢 B: 1 件でも残れば止める（Issue の文面どおり）。(a)〜(c) で決めたマージは照合を通らず、利用者が手で `gh pr merge` するしかなくなる。
  - 推した理由: A は既存の 3 つの決まりと両立し、照合で塞ぐのは「判断の記録が無いのに BLOCKED・満たさないでマージする」形——Issue が塞ぎたい形——だけである。
    判断の出所が本当かは照合では見えない（守らない）が、B でも記録を書き換えれば同じ。
  - 使った線と出所: `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線・台帳 `issue-1075`）。確認の Issue: #（起票後に書く）

## デプロイ経路

main へのマージで、プラグインの配布（カタログ）と公開サイトの再ビルド（`docs/plugins/`・`docs/plans/`）。子はマージしない（親が `merge-pr.py`）。

## 受入基準（不変条件 × 経路）

入口（マージに進む経路）: (1) `merge-pr.py <PR>`（cruise の親・手順 7 の任意の道）、(2) 手で `gh pr merge`（手順 7 の 1）、(3) 対象リポジトリの runbook のマージの手順、
(4) `merge-pr.py --absent`（不在の cruise の親）。照合の入口: `check-gates.py <計画> [--head] [--absent]` を周・親・`merge-pr.py` が呼ぶ。
記録を書く入口: 周（手順 3 の再開点）・再開した周・cruise の子・計画ファイルを手で直す人。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 関門を 1 パスしか通していない計画（2 パス目の記録も「該当なし」も無い・1 パス目の後に関門の見ていないコミットがある）で、`check-gates.py` が非 0（陽性対照） | 2 パス目の記録の有無を見ない・コミットを関門の記録と突き合わせない | 2 パス目は両方の記録か `該当なし` を求める。周の線のコミットを 1 つずつ、それを見た関門があるかで見る。テストの試料 |
| A2 | 全部通した計画（2 パス・狭いパス・計画と版の行だけのコミット・main の取り込み）で 0 | 通すべきコミットを止める | 通すコミットの 3 つの形。テストの試料（陰性側の対照） |
| A3 | `SKILL.md` 手順 7 から、照合を通らずにマージへ進む経路が無い——`merge-pr.py` は照合が 0 でなければ `gh pr merge` を呼ばない（13）。手で・runbook でマージする経路も、手順 7 がマージの前に素の 1 行で呼ぶことを必須にする | `merge-pr.py` が照合を飛ばす・計画が見つからないと通す・手順 7 の手の経路に照合が無い | `merge-pr.py` の段（計画が見つからない・照合が 0 以外なら 13、照合が判定できなければ 7）。`test-merge-pr.py` の試料と変異。`SKILL.md` 手順 7 の文面（関門に当てさせる） |
| A4 | 狭いパス・当て直し（外部レビュー・推奨の直し）の後に、関門が見ていないコミット（計画・版の行・main の取り込みのほか）があれば非 0 | 最後の関門の終点と head を比べない | 範囲 (起点, 終点] で見たコミットだけを覆ったとみなす。テストの試料 |
| A5 | 受入基準の表の番号に判定が無い・`BLOCKED`/`満たさない` に判断の記録が無い・線で `満たさない` を通す・`--absent` でないのに線の判断を通す、のどれでも非 0 | 表を読まない・判断を見ない | 表の番号と判定の突き合わせ・判断の出所の表（穴 G1 の A）。テストの試料 |
| A6 | 記録の `マージの反映:` が既定ブランチの `.claude/dev-loop.md` の宣言と違えば非 0。`--absent` で記録が無ければ非 0 | PR の中で足した宣言を通す | 既定ブランチの参照から `git show` で読む。テストの試料（ブランチにだけ宣言がある形） |
| A7 | 記録が無い・2 つある・読めない行がある・受入基準の表が無いなら 2、判定できない（`--head` が解決しない・必要な既定ブランチの参照が無い）なら 7——0 と答えない | 読めない行を飛ばす・例外で 0 | パーサが知らない行で 2。テストの試料 |
| A8 | `test-check-gates.py` に回帰テストと変異テスト（「守る」の行と 1 対 1）と陽性対照がある。`test-merge-pr.py` の既存の試料は全部期待どおりのまま、照合の段に変異がある。実リポジトリを触らない | 変異が届かない・試料が実リポジトリを指す | テスト自身が数える。`assert_not_real_repo` |
| A9 | `SKILL.md`・`absent-lines.md`・cruise の `SKILL.md`・公開ページ・`CLAUDE.md` の記述が実装と合う。版を 3 種類で上げ、生成ブロックが新しい | 片方だけ直す | `check-all.py`・`check-plugin-versions.py`・`skill-metrics.py --check`。関門に文面と実装の一致を当てさせる |

**検証で証明できるもの**: A1〜A9（A3 の `merge-pr.py` の経路は偽の `gh` で。手の経路は文面）。
**この環境では証明できないもの（未証明）**: (a) A3 のうち、手で `gh pr merge`・runbook でマージする経路が照合を通るか——文面で必須にするだけで、モデルが従うかは実際の周でしか見えない（構造で縛れない）。
(b) 本物の GitHub に対する `merge-pr.py` の新しい段——テストは偽の `gh`。PR コメントで人間のレビューに回す。
**生成物**: `docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`skill-metrics.py`）。`--check` で鮮度を見る。図の書き出しは触らない（drawio を触らない）。

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。run-serial の指示も両方に渡す。

## 未解決の判断・確認待ち

- 穴 G1（上）——確認の Issue で利用者に確かめる。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1043-check-gates`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1043`・起点 `52d73bc`・base `origin/main` → `52d73bc36861fd90c59a10ab65ab949d20e96ec5`
- 割り目 1（手順 4 の後）: 割らない（cruise の周）
- 交絡を潰した手順: （実装後に書く）

## 既知の限界・決着済みの論点

- 穴 G1 は選択肢 A で決めた（上）。
- 判断の出所（`判断=`）が本当かは照合では見えない——記録を書き換えれば通る。照合が塞ぐのは「記録が無い」形だけ。
- merge commit の中で衝突を解いた変更は、関門が見ていなくても通る（既定ブランチの親を取り込んだ merge commit を丸ごと通すため）。

## 手順 8（経験の還元）

- この周の起票: 0 件
