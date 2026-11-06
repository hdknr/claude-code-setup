# Issue #886 — 仮回答・確認の Issue の変化と作り直しの量を数えるスクリプト（rework-metrics.py）

不在の周（`/dev-loop:cruise 887 --absent` の起動・2026-11-06T01:37:35Z、利用者の確認・配布を見せて確かめた）。cruise #887 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かず「このまま続ける」）。従う版は dev-loop 1.74.1（キャッシュ。SKILL.md 1852 行）。
依存 #885 は PR #894 でマージ済み（main の先端 `f1e756a5`）。

- 直す線: **既定**（出所: cruise の確かめた線——上の起動。台帳 `issue-887`）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #887 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認の線: 台帳に無い（`.claude/dev-loop.md` の宣言か既定）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.67.0 → 0.68.0。スクリプトを足す——能力の追加）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #886` と `Refs #870`（#870 は閉じない）・`Refs #887`
- 並行する周: #823（PR #890・worktree `.claude/worktrees/issue-823`）——dev-loop の版を上げる。その worktree・ブランチには触らない
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/886-rework-metrics`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-886`
- 起点コミット: `f1e756a5`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `f1e756a556c0670b2717f86b07c268025ac8c97a`

## 変更範囲

触る:
- `plugins/spec-loop/scripts/rework-metrics.py` — 新しいスクリプト（数える側）
- `scripts/test-rework-metrics.py` — 回帰テスト（Q&A 表の履歴は一時の git リポジトリで作る。変異テストつき）
- `scripts/check-all.py` — 収録
- `.github/workflows/plugins.yml` — CI のステップ
- `plugins/spec-loop/references/handoff-issue.md` — 「作り直しの元の印」の節に、数えるスクリプトの指し（1 文）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `CLAUDE.md` — プロジェクト構成に `rework-metrics.py` と `test-rework-metrics.py` の行
- `docs/plans/issue-886.md` — この計画

触らない:
- `plugins/spec-loop/scripts/rebuild-scope.py` — 読み込むだけ（`Decision`・`Handoff` など既存の関数を使う。変えない）
- `plugins/spec-loop/scripts/scaffold.py` — 作り直した本文に印を載せる手段は #885 の既知の限界のまま（Issue に無い）
- dev-loop のプラグイン（印の写し・確認の Issue の書き方は変えない）
- `docs/plugins/spec-loop.md`（公開ページ）——数える道具は docstring と `handoff-issue.md` の指しで足りる

複製の数（同じことを述べている箇所）: 「回答が変わった」の見分け方は 1 箇所（`rework-metrics.py` の docstring と実装）。
確認の Issue の結果の行・作り直しの元の印の頭は `rebuild-scope.py` の定数を読む（写さない——写しを増やさない）。
`handoff-issue.md` は指すだけ。**分けない理由**: 定数を読み込むので複製は増えない。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージでプラグインのカタログに入る。マージは親。

## 設計（この周で決めたこと）

Issue が「どう見分けるかを決めて docstring に書く」と委ねているので、仕様の穴ではなく実装の判断として決める:

- **入力**: `--issues`（`gh issue list --json number,title,state,body,comments`）・`--prs`（`gh pr list --json number,title,state,body,additions,deletions`）・
  `--spec-repo <正本リポジトリ>`（Q&A 表の git の履歴。既定は cwd）・`--ref`（既定 `HEAD`）。**`gh` は呼ばない。`git` は呼ぶ**（読むだけ）。
- **Q&A 表の履歴**: `--ref` の first-parent の履歴で、Q&A 表（`docs/v<n>/shared/qa.csv`・`docs/v<n>/spec/qa-dev.csv`）を変えたコミットを古い順に読む。
  各コミットで、**同じ No は版の大きいほうの行が効く**（`versions.md` の重ね合わせの Q&A の行の決まりと同じ）。
- **仮回答**: どこかのコミットで `状態` が `暫定反映` だった No（`check-qa-csv.py` の `is_provisional` で判定）。
- **確かめた**: 前のコミットで `暫定反映` だった No が、次のコミットで `暫定反映` でなくなった（行が消えたら「消えた」）。
- **回答が変わった**: 確かめたコミットで、**`回答` の先頭の選択肢のラベル（英大文字 1 字。`A（…）` の `A`）が、直前の `暫定反映` の行と違う**。
  **`回答` の列全体の変化では見ない**——同じ選択肢で確定するときも `A（暫定で採用…）` → `A（業務部が確認）` と書き換えるので（`qa-csv.md` の「暫定の回答」）、全体で比べると確定を変化と数える。
  ラベルが読めない（`未回答`・ラベルで始まらない）なら「見分けられない」と名指しする。
- **確認の Issue**: `rebuild-scope.py` の `Decision` で読む——推奨のまま・変えた・結果なし（形に反する結果の行は名指し）。`comments` の鍵が無い入力は 2（数えられない）。
- **作り直しの量**: 変わった 1 件ごとに、引いた範囲（No なら `rebuild-scope.py` と同じ引き方で Issue とケースの数、確認の Issue なら影響する Issue の数）と、
  **作り直しの元の印**（`rebuild-scope.py` の `ORIGIN`）を本文の行頭に持つ Issue・PR、PR の差分の行数（マージした PR の `additions + deletions`）。
- **#885 の限界**: Q&A の No の作り直しで scaffold が作り直す spec-loop の Issue とその PR は印を持たない——数えられるのは下書きから立てた Issue（範囲の記録）とその周の PR だけ。docstring の「守らない」に書き、出力にも No の行に 1 句添える。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 仮回答の数と、確かめたときに回答が変わった数を Q&A 表の git の履歴から出す | 同じ選択肢での確定（回答の文言だけ変わる）・違う選択肢・`暫定反映` のまま・確認中のままの行・行が消えた・ラベルの読めない回答・v2 で同じ No を置いた・内部の表・Q&A 表を触らないコミット・暫定反映 → 確認中 → 暫定反映 → 反映済み（2 度確かめた）・Q&A 表の無いリポジトリ・git でないディレクトリ | `test-rework-metrics.py` の一時の git リポジトリの試料と変異 |
| A2 | 確認の Issue の数と、推奨のまま・変えた・結果なしの内訳を出す | 印で見分ける・題で見分ける・結果の行が形に反する・`comments` の鍵が無い入力・確認の Issue でない Issue | 試料と変異 |
| A3 | 変わった 1 件ごとに、引いた範囲（Issue・ケースの数）と、作り直しの元の印で結んだ Issue・PR・差分の行数を出す | No（ケース・機能全体）・確認の Issue（影響する Issue）・印を本文の行頭に持つ Issue・PR／行頭でない・装飾つきの印（数えない）・マージしていない PR（行数に入れない）・印の無い変わった件（0 件と出す）・PR の入力の形が違う | 試料と変異 |
| A4 | 「回答が変わった」の見分け方と、守らないもの（#885 の限界を含む）が docstring にある | 書いていない・#885 の限界を落とす | 読む＋テストの突き合わせ（docstring に見分け方の語と限界の語がある） |
| A5 | 実案件で数えて #870 に貼るまでの手順が書いてある | 取り方の 1 行・走らせ方・貼り方のどれかが欠ける | 読む（docstring の「使い方」） |
| A6 | 既存の `rebuild-scope.py`・`parent-checklist.py` は変わらない | 読み込みのために変えた | 差分に無い・`test-rebuild-scope.py`・`test-parent-checklist.py` が緑 |
| A7 | 版が 3 種類の箇所で揃い（spec-loop 0.68.0）、テストが `check-all.py` と CI の両方に収録されている | 片方だけ上げる・収録漏れ | `check-plugin-versions.py`・`test-check-all.py`・`check-all.py` |
| A8 | 必須の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（4 つの受け渡し。2 パス目が「該当なし」なら 2 つ） | 片方の関門・片方のパスに渡し忘れる | 再開点に記録 |

- 生成物: **該当判定**——`docs/plugins/dev-loop-design.md` の §8.2 の生成ブロックは dev-loop の `SKILL.md` の測定で、この周は dev-loop を触らないので**動かない**（`skill-metrics.py --check` で確かめる）。図（drawio）・`scaffold/` の生成物は触らない。ほかに生成物なし。
- 未証明: **実案件の Issue・PR・Q&A 表の履歴で数えた結果が正しいこと**——実案件の入力はこの環境に無い（試料は `gh` と同じ鍵の JSON と一時の git リポジトリ）。本物の `gh pr list` が `additions`・`deletions` を返す形は見ない。

## 未解決の判断・確認待ち

- なし（見分け方は Issue が委ねている——上の「設計」）

## 関門の進捗（再開点）

- 割り目（手順 4 の完了時）: 不在のため訊かず続けた
- check-all.py（順番待ち越し）: 66/66 緑（実装のコミット e8dd8eb0 の前）。`test-rework-metrics.py` は python3.12 でも緑（順番待ちの外で 1 回）
- Verifier 1 パス目: 起動（sonnet・dev-loop:dev-loop-verifier）
- /code-review 1 パス目: 未
- 1 パス目の指摘対応の起点: `e8dd8eb0`（1 パス目の関門に渡した時点の HEAD）
- 2 パス目: 未
- 狭いパス: 未
- 反証と差し戻し: なし（まだ関門に渡していない）
- 交絡を潰した手順: 実験なし（テストの試料のみ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 「回答が変わった」を `回答` の列全体の変化で見るか | 採らない——選択肢のラベルで見る | 同じ選択肢で確定するときも回答の文言を書き換える決まり（`qa-csv.md`）なので、列全体だと確定を変化と数える |
| Q&A の No の作り直しで scaffold が作り直す本文・その PR に作り直しの元の印が無い | この周では直さない（#885 で利用者が記録のままマージを承認した限界） | 数えられるのは下書きから立てた Issue とその周の PR だけ。docstring の守らないものと出力の 1 句で示す |

## 手順 8

- 焼き戻す学び: 未

- この周の起票: 0 件（起票の承認は不在のため訊いていない）
