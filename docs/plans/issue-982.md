# Issue #982 — spec-loop: spec-review の指摘の表を正本に残す（振り分けを後から数えられるように）

利用者が居る周（`/dev-loop:dev-loop 982` を利用者が起動。2026-11-11）。従う版は dev-loop 1.103.0（キャッシュ）。

- 直す線: **既定**（出所: 手順 3 の `AskUserQuestion` に 600 秒答えが無かったので既定。2026-11-11）
- 形式の検査: **足す**（Issue が「この周で決める」とした判断。同じ問いに答えが無かったので推奨の側。理由は下の「決着済みの論点」）
- 版の上げ方: **spec-loop を minor で上げる**（0.80.1 → 0.81.0。0.x なので能力の追加は minor）。`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行
- PR は `Fixes #982`

## 周の在り処

- ブランチ: `issue/982-findings-record`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-982`
- 起点コミット: `5b629b5f`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `5b629b5f149408a39ae750ec4dae7462bb134470`

## 変更範囲

触る:
- `plugins/spec-loop/references/spec-exit.md` — 「実行の上限と記録」に「指摘の表」の節（置き場所・いつ足すか・列と値の**原本**）
- `plugins/spec-loop/references/tree.md` — ツリーに `spec-review/v<n>-findings.csv` の 1 行（指すだけ）
- `plugins/spec-loop/references/writing-style.md` — 記法が掛からないセルの列挙に指摘の表を足す
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 手順 4（表を残すことの予告）・手順 6（足して検査する）・手順 7（報告）・`用意してから呼び直す` の扱いと版
- `plugins/spec-loop/skills/autopilot/SKILL.md` — `judge` 段とやり直しの扱いに指摘の表と版
- `plugins/spec-loop/skills/req-loop/SKILL.md`・`feasibility/SKILL.md`・`proposal/SKILL.md`・`scaffold/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/scripts/check-findings-csv.py` — 新規。指摘の表の形式の検査
- `plugins/spec-loop/scripts/autopilot-check.py` — 線に依らず点検するスクリプトの一覧に `check-findings-csv.py` を足す（実装中に見つけた経路: autopilot の周が新しい検査を呼ぶので、権限の点検の対象に要る。受入基準 1 の経路に足した）
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
- `scripts/test-check-findings-csv.py` — 新規。検査の回帰テスト（変異テストを含む）
- `scripts/check-all.py` — テストの登録
- `.github/workflows/plugins.yml` — テストのステップ
- `CLAUDE.md` — 新しいスクリプトとテストの説明
- `docs/plans/issue-982.md` — この計画

触らない:
- 集計のスクリプト（Issue の「入れないもの」）
- 判定役の定義（`agents/`）——判定役の報告の形は変えない。表を書くのは呼び出し元
- `check-spec-exit.py`・`merge-versions.py`・`diff-versions.py`——指摘の表は `docs/` の外なので読む側を変えない

**同じことを述べている箇所の数**: 原本 1（`spec-exit.md` の「指摘の表」）＋指す側 7（`tree.md`・`writing-style.md`・spec-review の手順 4/6/7・autopilot・検査の docstring と定数）＋テスト・`CLAUDE.md`。
**分けない理由**: 1 つの決まりで、原本以外は指すだけ（列を再掲しない）。列の写しは検査の定数だけで、テストが原本と突き合わせる。

## 乗るデプロイ経路

プラグインの配布（main にマージ → 利用者の `claude plugin update`）。公開サイト（`docs/plans/` は mkdocs の対象だが、計画ファイルの追加だけ）。

## verify の受入基準

**この周が主張するのは「決まりが書いてあり、検査が決まりどおりに判定する」まで**——実際の spec-review の実行（モデルが散文に従って表を書くこと）は主張しない（受入基準 1 の文言も「書いてある」）。

| # | 不変条件 | 破りうる経路 | どう守るか |
| --- | --- | --- | --- |
| 1 | 判定のたびに指摘の表が正本の決まった場所に残り、**置き場所と列の原本は `references/` に 1 か所** | spec-review 手順 6（対話）・`claude -p` での実行・autopilot の `judge` 段・autopilot の起動時の権限の点検（`autopilot-check.py`）・2 回目のレビューで止めた回・狭いパスの指摘・手順 7 の報告・tree.md の木 | 原本は `spec-exit.md` の「指摘の表」。ほかは指すだけ（列を再掲していないことを grep で見る） |
| 2 | 振り分けの列は `spec-scope.md` の 6 区分の名前だけ（根拠を確かめられない行だけ `-`） | 自由文・言い換え（`実装へ`）・`確かめられない` を振り分けに書く・区分の表が将来変わる | 検査が値を落とす（1）。定数が `spec-scope.md` の表と一致することをテストが見る |
| 3 | 「実装に渡す」「退ける」（と範囲の外の案）の行も残る | 「結果が残る行だけ写す」読み方・2 回目と狭いパスの行を落とす | 原本に「手順 4 の表の全行（1 回目・2 回目・狭いパス）」と書く。検査は `振り分け` の 6 値をどれも通す（陽性対照） |
| 4 | `用意してから呼び直す` の扱いが `spec-review/v<n>.csv` と食い違わない | 1 回目で止めた（実行の行なし）・2 回目で止めた（実行の行あり）・上限の行・利用者の打ち切り | 指摘の表は**実行の行と同じ回の番号で、同じときに足す**。実行の行を足さない場合は指摘の表にも足さない。検査は `回` が実行の行（`抜けた`／`抜けていない`）を指し、日付が一致することを見る |
| 5 | 指摘の表が版の重ね合わせ・版の差分・条件 1 に混ざらない | `docs/v<n>/` の中に置く | `docs/` の外（`spec-review/`）。理由は記録の表と同じ節を指す |
| 6 | 数える列（決まった値）と文面の列が分かれる | 列の並び・文面に区分を書く | 数える列を前、文面の列（`指摘`・`根拠`・`結果`）を後ろ。検査は数える列の値だけを見る |
| 7 | 検査が決まりどおりに判定する: 違反は 1・通る形は 0・読めない／引数の誤り／実行の記録が無いは 2。標準ライブラリだけで単体で動く | 見出しの違い・列の数・値・`-` の対応・回の結び・BOM・空ファイル・UTF-8 でない・`-OO` | テスト（試料・変異・references との突き合わせ・`python3 -I` で外で動かす） |
| 8 | 版が 3 種類で揃い、テストが `check-all.py` と CI に登録され、`CLAUDE.md` に載る | 登録漏れ・版の据え置き | `check-plugin-versions.py`・`test-check-all.py`・`check-all.py` |

**掛け算**: 「両方の関門に受入基準を渡す」×「2 パス」= 4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

**証明できないもの（未証明）**: 実際の spec-review の実行で、モデルが手順 6 に従って表を書き足すこと——主張しない（上）。

**生成物**: 該当なし——`skill-metrics.py` の対象は dev-loop の `SKILL.md`（触らない）、drawio は触らない。`skill-metrics.py --check` と `check-diagram-freshness.py` は `check-all.py` の中で回る。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 実装: 済み（`659d458b`）。`check-all.py` 73/73・失敗 0。新しいテストは試料 34・変異 17・references の崩し 4
- 割り目（手順 4）: AskUserQuestion で訊いた——600 秒答えが無く、このまま続けた
- 1 パス目の起点（指摘対応の 0 行判定用）: `0f190644`（関門に渡した時点の HEAD）
- Verifier 1 パス目: 未
- /code-review 1 パス目: 未
- 交絡を潰した手順: 実験は変異テストと陽性対照（本物の本体で 34 試料が期待どおり→変異で崩れる。references は崩さない形で一致→崩した形で不一致）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 形式の検査を足すか | 足す | 振り分けの値が散文だけだと崩れる（#304 で件数の行の半分がパターンから落ちた）。数えるための表なので値の崩れが目的を壊す |
| `確かめられない` の行の振り分け | `-`（`確かめたか` の列を `確かめられない` にする） | `spec-scope.md` の「確かめていない行」はどの区分にも確定しない。区分の名前以外を `振り分け` に入れない |
| 打ち切り（実行の行を足さない）の回の指摘 | 足さない | `回` で実行の行と結べない。記録の表と同じく数えない |
| 重さの値の制約 | `範囲の外として記録する`・`実装に渡す` は `-` だけ、ほかは 4 値のどれでも | 手順 4 の表の決まりのまま。ほかは判定役の重さを写す |
| 同じ実行の行を 2 度足した（autopilot のやり直し） | 散文で禁じる（検査は見ない） | 同じ指摘が 2 回の判定役から出るのは正当で、重複を機械で区別できない |

## 起票

- この周の起票: 0 件（起票の候補なし）
