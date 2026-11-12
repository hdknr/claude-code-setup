# Issue #989 — rework-metrics の集計を PC の中に貯めて分析する

## 変更範囲

触る:

- `plugins/spec-loop/scripts/rework-metrics.py` — `--record`・`--case` と記録の形・記録先の決め方（定数と関数はここに 1 つだけ置く）
- `plugins/spec-loop/scripts/rework-report.py` — 新規。記録を読んで表・差・合計と率を出す（記録の形は `rework-metrics.py` から読み込む——写さない）
- `plugins/spec-loop/references/handoff-issue.md` — 「数えて貼る」を「数えて記録し、分析する」に直す
- `scripts/test-rework-metrics.py` — `--record` の試料と変異・docstring の突き合わせを #980 から書き換え
- `scripts/test-rework-report.py` — 新規。回帰テスト（変異テストを含む）
- `scripts/check-all.py` — `test-rework-report.py` を収録
- `.github/workflows/plugins.yml` — `test-rework-report.py` のステップを足す
- `CLAUDE.md` — `rework-metrics.py` の行の #980 を外し、`rework-report.py` とそのテストの行を足す
- `.claude-plugin/marketplace.json` — spec-loop の版（0.83.0 → 0.84.0）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 同上
- `plugins/spec-loop/skills/` — 各 `SKILL.md` の版の 2 行だけ
- `docs/plans/issue-989.md` — この計画

触らない:

- spec-review の指摘の表を数えること（Issue の「範囲の外」）
- autopilot・proposal から `--record` を自動で呼ぶこと（使ってから別に決める）
- 1 つの案件で開発リポジトリが複数ある形

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`.claude/dev-loop.md`）。docs/ のサイトの中身は変えない。

## 設計

- **記録先**: 環境変数 `SPEC_LOOP_REWORK_LOG` があればそのパス、無ければ `~/.claude/spec-loop/rework-metrics.jsonl`（`Path.home()`）。決め方は `rework-metrics.py` の `record_path()` 1 箇所。
- **1 行**（JSON・1 行 1 記録・鍵の一覧は `rework-metrics.py` の `RECORD_KEYS`）: 案件（`--case`、既定は正本リポジトリの最上位のディレクトリ名）・`ref`・`commit`（解決した SHA）・`date`（そのコミットの日付）・`recorded`（記録した日）・数（仮回答・確かめた・変わった・同じ・見分けられない・消えた・まだ暫定反映・確認の Issue・推奨のまま・変えた・結果なし・形に反する・変わった件・作り直しの Issue・PR・差分の行・数えきれない件数）。
- **二重の記録**: 同じ案件・同じ `commit` の行がすでにあれば書かずに終了コード 3（数は標準出力に出す）。記録のファイルに読めない行があっても、二重かを決められないので書かずに 2。
- **終了コード**: 0・1・2 は今のまま。`--record` で書いたなら 0 か 1（数えきれないものがあっても、その件数を行に入れて書く）。3 は「書かなかった（二重）」。
- **rework-report.py**: 案件 × 時点の表（日付順）・同じ案件の隣どうしの時点の差・案件ごとの最新を足した合計と率（Q&A の変わった率＝変わった／確かめた、確認の Issue の変えた率＝変えた／（推奨のまま＋変えた）、変わった 1 件あたりの差分の行）。読めない行（JSON でない・鍵が足りない・型が違う）は名指しして 1。記録のファイルが無ければ 2。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | `--record` は記録の項目を 1 行の JSON で追記し、既存の行を消さない | 新規ファイル・既存ファイルへの追記・親ディレクトリが無い | `open("a")`・`mkdir(parents=True)`。試料: 2 回の別コミットで 2 行 |
| A2 | 同じ案件・同じコミットの 2 度目は書かずに 3 | 同じ `--ref`・別名の参照で同じコミット・`--case` を変えた | 比べるのは `case` と `commit`。試料 3 つ |
| A3 | 記録の数は標準出力の数と同じ | 1 つの集計から両方を作る | 集計を 1 つの辞書に作ってから出す。試料で突き合わせ |
| A4 | 記録先の既定は利用者の `~/.claude` の下で、テストは実物に触らない | 既定のパス・環境変数・テストの `HOME` | テストは一時 `HOME` と `SPEC_LOOP_REWORK_LOG` の両方で当て、実物の `~/.claude/spec-loop/` を見ないことをアサート |
| A5 | 記録に読めない行があれば黙って書かない（2） | 壊れた JSON・鍵の欠け | 書く前に全行を読む |
| B1 | rework-report は表・差・合計・率を出す | 案件 2 つ × 時点 2〜3 | 試料の期待値 |
| B2 | 読めない行は名指しして 1、黙って捨てない | JSON でない・鍵が足りない・型が違う・空行 | 試料 |
| B3 | 記録のファイルが無ければ 2 | パス違い | 試料 |
| B4 | 率の分母が 0 のとき割らない（`-` を出す） | 確かめた 0 件 | 試料 |
| C1 | 記録の形は `rework-metrics.py` に 1 つだけ置き、report はそれを読み込む | report に鍵の写しを置く | `_load` で読み込む。テストで静的に見る |
| C2 | 回帰テスト（変異テストを含む）を `check-all.py` と CI に収録し、本体は CI から呼ばない | 収録漏れ | `test-check-all.py` が見る |
| C3 | #980 を指す記述が残らない（docstring・CLAUDE.md・references） | grep | `grep -rn 980` |
| C4 | `--summary` の決まり（題・No・SHA を出さない）は変わらない | `--record` と併用 | 既存の試料と変異のまま |
| C5 | 版は 3 種類（marketplace・plugin.json・SKILL.md）で 0.84.0 | 上げ忘れ | `check-plugin-versions.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と /code-review の両方 × 1・2 パス目に渡す | — | 計画の再開点で記録 |

**証明できないもの（未証明）**: 利用者の実際の `~/.claude` に書けること（テストは一時 `HOME` だけを当てる。実物には書かない）。

**生成物**: `SKILL.md` の測定値（設計 §8.2 の生成ブロック）は spec-loop の SKILL.md の版の行だけを触るので、`skill-metrics.py --check` で見る（dev-loop の SKILL.md は触らない）。図の書き出しは無し。

**複製の数**: 記録の形（鍵）は `rework-metrics.py` に 1 つ。手順の散文は `rework-metrics.py` の docstring 1 つを正とし、CLAUDE.md と handoff-issue.md は指すだけ。分けない理由: 1 本の docstring に寄せれば足りる。

## 直す線

既定（出所: 手順 3 の回答 2026-11-12）。

## 未解決の判断

- #980 を閉じるのはマージの後（Issue の「やること」4）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/989-rework-local-store`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-989`・起点 `5c2f4a3e`・base `origin/main` → `5c2f4a3e3e10f15d672865db345c73654ba4076b`
- 実験: なし
- 実装（手順 4）: 済み。`check-all.py` 74 本中 73 本 OK、`test-render-diagrams.py` の 1 本だけ「プロセスグループを止めない」の変異が生き残った——
  同時に python3.12 で `test-rework-metrics.py` を走らせていた（負荷）。この周で触っていないファイルで、単独で回し直すと緑（試料 60・変異 53）。
  `test-rework-metrics.py`（試料 10・変異 61）・`test-rework-report.py`（試料 7・変異 24）は python3.14・3.12 の両方で緑
- 実装のコミット: `29516084`
- 割り目 1（手順 4 の後）: AskUserQuestion で訊いたが 600 秒答えが無かった——このまま続けた（2026-11-12）
- 1 パス目の指摘対応の起点: このコミットの直後の HEAD（下の行に SHA を書く）
- 1 パス目の指摘対応の起点（1 パス目の関門に渡した時点の HEAD）: `aaec397831572951adef4cebb3e7073beb009ccf`
- 関門 1 パス目: Verifier（dev-loop:dev-loop-verifier・sonnet）反証 1 件（R1）・/code-review（high）指摘 8 件（CR1〜CR8）。下の採否の表。手順 4 へ差し戻し（R1・CR1・CR2・CR3・CR4・CR6 を直す）
- 1 パス目の指摘対応: 済み（`a5f29872`）。`git diff aaec3978 -- ':(top)' ':(top,exclude)docs/plans/issue-989.md'` は空でない（テスト 2 本・CLAUDE.md・漏れたファイルの削除）——2 パス目を回す。
  陽性対照: cwd の分離を外した写しで「テストを走らせた cwd に記録のファイルを作っていない」が赤（1 件の失敗）。
  `check-all.py` 74 本中 73 本 OK、`check-plan-scope.py` だけ漏れたファイルの削除を未コミットのまま回して落ち、コミット後に単独で緑
- 次: 手順 5 の当て直し（Verifier 2 パス目）と /code-review 2 パス目（どちらも未）。base は同じ `5c2f4a3e…`

## 既知の限界・決着済みの論点

- Issue・PR の JSON は取った時点の全件なので、同じコミットで後から取り直しても二重として断る（取り直した数を残したいなら行を手で消す）——docstring の守らないものに書く。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1・CR1 テストが漏らした記録のファイル `.claude/spec-loop/rework-metrics.jsonl` がコミット `29516084` に入っている | 示せる——`git show --stat 29516084` に出る・作業ツリーに 443 バイトのファイルが在る | A4 | 直す（ファイルを消す） |
| CR2 「既定のパスを HOME の下にしない」の変異体が cwd に書く（cwd を分けていない）。`$HOME` から走らせれば利用者の記録に書く | 示せる——Verifier と /code-review がそれぞれ外の複製で走らせ、cwd にファイルができた（R1 の証拠 3） | A4 | 直す（子プロセスの cwd を一時ディレクトリにし、テストを走らせた cwd に記録ができないことを見る） |
| CR3 test-rework-report の「利用者の記録に触っていない」は mtime だけで、読むことは見られない | 示せる——読むだけでは mtime は変わらない（report は書かない）ので、このアサートは常に通る | A4（守り方の「実物の ~/.claude/spec-loop/ を見ないことをアサート」） | 直す（子プロセスの cwd も一時ディレクトリにする。アサートの名前を見ているもの——書いていない——に合わせる） |
| CR4 記録の `date` を形だけ見ていて、値を今日にしても通る | 示せる——/code-review が外の複製で変異を当てて OK（61 件）のまま | A1（記録の項目） | 直す（`early` のコミットの日付と突き合わせる・変異を足す） |
| CR6 記録の `recorded` も形だけ | 示せる——同上 | A1 | 直す（今日の日付と突き合わせる・変異を足す） |
| CR5 記録しなかった 3・2 が「数えきれない」の 1 を上書きする（優先が docstring に無い） | 示せる（コードの振る舞い） | 無し——3 の定義どおり。数えきれない件数は標準エラーに出る | 残課題 |
| CR7 A3 の守り方（1 つの辞書から両方を出す）がコードと違い、テストも記録と標準出力を直接突き合わせていない | 示せない——記録と標準出力が食い違う実例は無い（同じ変数から作っている） | 無し | 残課題（計画の守り方の記述は周の記録で、成果物ではない） |
| CR8 `--log` にディレクトリを渡すと「記録のファイルが無い」と出る（終了コード 2 は正しい） | 示せる | 無し——B3 は終了コードを決めている | 残課題 |

- この周の起票: 0 件
