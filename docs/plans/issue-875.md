# Issue #875 — 仮回答と推奨で決めた事項の台帳（作り直す範囲を引けるようにする）

不在の周（`/dev-loop:cruise 877 --absent` の起動・2026-11-05）。cruise #877 の子として回す。利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かず「割らない（cruise の周）」）。

- 直す線: **既定**（出所: cruise の確かめた線——利用者の確認（起動時・2026-11-05T08:50:03Z、配布を見せて確かめた）。台帳 `issue-877`）
- 仕様の穴: **推奨で決めて起票**（出所: 同上）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`）
- 版の上げ方: **minor・spec-loop と dev-loop の両方**（main の先端 spec-loop 0.63.0 → 0.64.0・dev-loop 1.94.0 → 1.95.0。scaffold に `--provisional` と印を足し、台帳を引くスクリプトを足す——spec-loop は能力の追加。dev-loop は確認の Issue の書き方に台帳の 2 行を足し、spec-gap.md に仮回答の印の読み方を足す——手順の追加）。マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す
- PR は `Fixes #875` と `Refs #870`（#870 は閉じない）。後続の #876（Issue の粒度）も scaffold.py を触るが、この周は #875 の範囲だけ

## 変更範囲

触る:
- `plugins/spec-loop/scripts/scaffold.py` — `--provisional`（暫定反映を通す。指していない暫定の行は止める）と、本文の印（`## 仕様` の `- 仮回答: ` の行・受入基準の表の `（暫定）`）。docstring と守らないもの
- `plugins/spec-loop/scripts/rebuild-scope.py` — 作り直す範囲を引くスクリプト（新規）
- `plugins/spec-loop/references/handoff-issue.md` — 仮回答の印（原本）
- `plugins/spec-loop/references/spec-ir.md` — `qa` の決まりに `--provisional` のときの例外
- `plugins/spec-loop/references/qa-csv.md` — 段ごとの扱いの表の scaffold の行・暫定の回答の確かめ方に台帳を引くこと
- `plugins/spec-loop/references/versions.md` — 前の版の時点の判定に `--provisional` のときの例外（記述があれば最小限）
- `plugins/spec-loop/README.md` — 使い方の行に `--provisional`（1 パス目の指摘 CR8 で広げた）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — `--provisional` を使ってよい場面（利用者の指示のときだけ）と台帳の引き方・版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 確認の Issue の書き方に台帳の 2 行（`決めた値: `・`影響する Issue: `）
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 仮回答の印を持つ Issue の読み方
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-scaffold.py` — `--provisional` の試料・印・写しの突き合わせ・変異
- `scripts/test-rebuild-scope.py` — 台帳のスクリプトの回帰テスト（新規。変異を含む）
- `scripts/test-check-qa-csv.py` — 読む側が `is_provisional` を呼ぶ数（`scaffold.py` は 1 → 4。`--provisional` の判別も `is_provisional` を通す——実装中に `check-all.py` が落として広げた）
- `scripts/check-all.py` — 新しいテストの収録
- `.github/workflows/plugins.yml` — 新しいテストのステップ
- `CLAUDE.md` — プロジェクト構成に新しいスクリプトとテストの行
- `docs/plugins/spec-loop.md` — 公開ページの引き渡しの節に 1 行
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない）
- `docs/plans/issue-875.md` — この計画

触らない:
- 印（`HANDOFF_MARKER` の `v3`）・`SECTIONS`・指紋の式——行とセルの印を足すだけ（#851・#874 と同じ扱い）
- `issues.json` の形——台帳は登録した本文から引くので、索引には足さない
- `--provisional` を付けない既定の振る舞い（暫定反映が残れば止める）
- #876（Issue の粒度）・#870 の他の項目

複製の数（同じことを述べている箇所）: 仮回答の印の形は 4 箇所（`handoff-issue.md`〔原本〕・`scaffold.py` の定数・dev-loop の `spec-gap.md`・`test-scaffold.py` の写し。`rebuild-scope.py` は `scaffold.py` の定数を読み込み、写さない）。確認の Issue の台帳の 2 行は 2 箇所（`absent-lines.md`〔原本〕・`rebuild-scope.py`）。
**分けない理由**: 2 つのプラグインと生成・読み取りの境界の写しで、`test-scaffold.py` と `test-rebuild-scope.py` が原本と突き合わせる（`rebuild-scope.py` は scaffold が実際に作った本文を読む試料で当てる）。

## デプロイ経路

main へのマージで GitHub Pages の再ビルド（`docs/`）とプラグインの配布（spec-loop・dev-loop の版）。マージは親がする。

## 設計（この周で決めたこと）

- **仕様の穴（推奨で決めた）**: Issue は「仮回答（`暫定反映`）に依存する Issue と受入基準に scaffold が印を付ける」と言うが、いまの scaffold は `暫定反映` が 1 行でも残れば止まる（#325）。
  選択肢 A: 既定は止めたまま、利用者の指示で `--provisional` を付けたときだけ通して印を付ける／B: 既定で通して印を付ける（止めるのをやめる）／C: 止めたままで印を付けない（台帳は確定した Q&A と確認の Issue だけ）。
  **推奨 A で決めた**——利用者が確かめていない回答を黙って開発へ渡さない既定（#325）を保ったまま、#402 のように仮回答のまま進めると利用者が決めた場合に、作り直す範囲を引ける形で渡せる。確認の Issue に起票する。
- **`--provisional` のとき**: 暫定反映の行を中間表現の `qa`（機能・ケース）から指してよい。**どの機能にもケースにも指されない暫定反映の行が残れば止める（1）**——指していなければ作り直す範囲を引けない（#325 が止めた理由そのもの）。前の版の時点の判定も、暫定反映を崩れとみなさない（前の版を `--provisional` で作ったなら、そのとき通している）。
  内部の表は暫定反映を使わない（`qa-csv.md`）ので変わらない。`--check`・`--dry-run`・`--red-check` も同じ旗で関門を通す。
- **印**: 本文の `## 仕様` に `- 仮回答: ` の行（暫定反映の Q&A の No と、作り直しの範囲の言い方）を、依存するときだけ 1 本。受入基準の表の Q&A の列で、暫定反映の No に `（暫定）` を付ける。依存しない本文は 1 バイトも変わらない。
- **台帳 = 登録した Issue の本文**（新しいファイルを持たない）。`rebuild-scope.py` は `gh issue list --state all --json number,title,state,body` の出力（決まった取り方）を読み、
  (1) Q&A の No → それを根拠にした spec-loop の Issue と、その受入基準のケース（ケースに無ければ機能全体）、(2) 確認の Issue の番号 → 決めた値と影響する Issue、(3) 引数なしなら一覧（仮回答の印を持つ Q&A と、確認の Issue）を出す。`gh` は呼ばない（取り方を docstring に書く）。
- **確認の Issue の台帳の 2 行**: `absent-lines.md` の「確認の Issue の書き方」に、重さの行の直後の `決めた値: ` と `影響する Issue: ` の 2 行を足す（機械が読む）。前の書き方の確認の Issue は「台帳の行が無い」と名指しする。

## verify の受入基準

不変条件と経路:

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| A1 | `--provisional` を付けない既定の振る舞いは変わらない——暫定反映が残れば止める（指していても・いなくても、前の版でも） | 書く生成・`--check`・`--dry-run`・`--red-check`・前の版の判定 | 既存の試料（暫定反映の 6 形）がそのまま通る |
| A2 | `--provisional` のとき、暫定反映に依存する本文に印が付く: `## 仕様` の `- 仮回答: ` の行に依存する暫定の No が全部、受入基準の表で暫定の No を根拠にするケースに `（暫定）`。依存しない本文・確定の No には付かない | 機能の `qa`・ケースの `qa`・追加・変更・撤去の本文 | `test-scaffold.py` の試料で本文を読む。変異（行を書かない・セルに付けない・確定の No にも付ける）が落ちる |
| A3 | `--provisional` でも、どこからも指されない暫定反映の行が残れば止める（1）。確認中は従来どおり止める | 書く生成・`--dry-run`・`--check` | 試料。変異（指していない行を見ない）が落ちる |
| A4 | `--provisional` は全モードで受け付け、前の版の時点の判定で暫定反映を崩れとみなさない | v2 の試料（v1 に暫定反映） | 試料 |
| A5 | `rebuild-scope.py`: Q&A の No から、その No を根拠にした spec-loop の Issue とケース（ケースに無ければ機能全体と言う）を引ける。scaffold が実際に作った本文で当てる | 受入基準の表・`## Q&A の回答`・`（暫定）` の付いたセル・閉じた Issue | `test-rebuild-scope.py`（scaffold で作った本文を JSON に包んで渡す）。変異が落ちる |
| A6 | `rebuild-scope.py`: 確認の Issue の番号から、決めた値と影響する Issue を引ける。台帳の行の無い確認の Issue はそう名指しする。引数なしで、仮回答の印を持つ Q&A と確認の Issue の一覧が出る | 印 `<!-- cruise-decision: #<親> -->`・題の `要確認: `・前の書き方 | 試料。変異が落ちる |
| A7 | 引けない番号は名指しして 1、入力が読めない・引数の誤りは 2 | 無い No・確認の Issue でない番号・壊れた JSON | 試料 |
| A8 | 写しの突き合わせ: `scaffold.py`・`rebuild-scope.py` の印の定数が `handoff-issue.md` と dev-loop の `spec-gap.md` に、確認の Issue の 2 行の頭が `absent-lines.md` に在る | 片方だけ言い換える | テストの突き合わせ＋陽性対照 |
| A9 | 版: spec-loop 0.64.0・dev-loop 1.95.0 が 3 種類の箇所で一致 | — | `check-plugin-versions.py` |
| A10 | 歯止めが全部緑（`check-all.py`）・PR 側の CI が全部通る（新しいテストが CI と `check-all.py` に収録されている） | — | `run-serial.py` 越しの `check-all.py`・`test-check-all.py`・`gh pr checks` |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。既知の限界も同じ 4 つに渡す。

未証明（この環境では証明できない）:
- 実案件で、利用者が仮回答を確かめたときに台帳から引いた範囲で作り直しが足りるか——実データが無い（#870 の「作り直しの量の記録」が測る）。
- `gh issue list` の実際の出力（GitHub の API の形）——テストは同じ鍵の試料で当てる。本物の GitHub には届かない。

生成物の該当判定:
- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`absent-lines.md`・`spec-gap.md` の行数が変わるので該当。`skill-metrics.py --check` が 0 であること
- 図（drawio）——触らないので該当なし
- `scaffold/` の契約——このリポジトリには正本が無い（試料は一時ディレクトリ）。該当なし

## 未解決の判断・確認待ち

- 仕様の穴（上の設計の 1 つ目）——確認の Issue #881 に起票した（閉じない。利用者が判断する）

## 手順 8（起票数）

- この周の起票: 1 件（#881——仕様の穴を推奨で決めた確認の Issue。不在の線 `仕様の穴 = 推奨で決めて起票`）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/875-qa-ledger`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-875`・起点 `b17560b9`・base `origin/main` → `b17560b9352d4afd7447cd5e15044ba8ca50d562`
- 割り目（手順 4 の完了時）: 割らない（cruise の周。訊かない）
- PR: #880
- 1 パス目の指摘対応の起点: `60e272cd`（1 パス目の関門に渡した時点の成果物の HEAD。以後の計画ファイルだけのコミットは判定から除く）
- 1 パス目の結果: Verifier 反証 0 件（軽微な所見 1 件 = CR10 と同じ）・`/code-review` 指摘 10 件（CR1〜CR10）。直す 7 件（CR1・CR2・CR4・CR5・CR7・CR8・CR10。CR4 と CR5 は同じ直し、V1 は CR10 と同じ直し）・残課題 3 件（CR3・CR6・CR9）。手順 4 への差し戻しは指摘対応として 1 回
- 割り目（2 パス目の前）: 割らない（cruise の周。訊かない）。残っているのは手順 5 の当て直しと手順 6 の 2 パス目の両方
- 交絡: 実験は試料と変異（陽性対照: 変異ごとに壊す箇所が 1 回現れることを先に見る）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 既定を変えず `--provisional` を足す（仕様の穴） | 推奨で決めた（確認の Issue） | #325 の既定を保ち、利用者が決めた場合だけ通す |
| 台帳を新しいファイルにせず、登録した Issue の本文から引く | 採った | 本文が既に受入基準と Q&A の対応を持つ。開発のリポジトリが正本と別でも引ける |
| 本文に仮回答の印を付けた後に利用者が確かめても、登録済みの本文の印は残る | 守らない（docstring に書く） | 本文は生成した時点の写し。いまの状態の正は Q&A 表（dev-loop の `spec-gap.md` と同じ） |
| 中間表現の書き起こしが暫定の行を指し漏らした機能は、台帳に出ない | 守らない | 指しているかは書き起こしの判断。機械は「どこからも指されない行」だけを止める |
| `rebuild-scope.py` は `gh` を呼ばない | 採った | 取り方を決まった 1 行にし、標準ライブラリだけで試料に当てられる |

### 1 パス目の指摘と採否（直す線: 既定）

| # | 関門 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- | --- |
| V1 | Verifier | absent-lines.md の新しい項目 4 の後ろに、項目 3（重さ）の続きの段落が付いて見える | 示せる（本文） | 無し（読みやすさ） | CR10 と同じ直しで直した |
| CR1 | `/code-review` | `--provisional` のとき前の版の指されない暫定の行まで崩れに数えず、v1 を作れていないのに v2 を差分で作り、変わらない機能の Issue が渡らない（#335 の形） | 示せる（試料で再現。指摘者のプローブ） | A3（指されない暫定の行は止める）——この周が持ち込んだ後退 | 直す——前の版の中間表現が指す暫定の行だけ数えない。試料と変異を足した |
| CR2 | `/code-review` | 撤去の本文に前の版の時点の状態で印が付き、生成した時点で確定した行にも付く | 示せる（プローブ） | A2（依存しない本文に付けない・生成した時点） | 直す——撤去の本文には付けない（handoff-issue.md にも書いた）。試料と変異 |
| CR3 | `/code-review` | 機能とケースの両方が指す No はケースだけを挙げ、機能全体の依存が落ちる | 示せる（試料の F-001） | 無し（A5 は「ケースに無ければ機能全体」で、本文の形が両者を見分けない） | 残課題（docstring の守らないものに書いた） |
| CR4 | `/code-review` | `影響する Issue: ` の行を `#N` の全部で読むので、説明の中の番号も数え、`#` の無い行は黙って「なし」 | 示せる（プローブ） | A6 | 直す——番号だけを `, ` で並べるか `なし` だけを受け、ほかは「決まりの形でない」で 1 |
| CR5 | `/code-review` | 台帳の行の書き方（番号だけ）が同じファイルの「番号の指し方」（必須の規定）と食い違う | 示せる（本文） | A6・A8 | 直す——CR4 と同じ直し。「番号の指し方」に台帳の行の例外を書いた |
| CR6 | `/code-review` | 利用者が同じ選択肢で確定しても、dev-loop が回答の食い違いで差し戻す | 示せない（周の流れの想定。食い違いの差し戻しはこの周の前からの決まり） | 無し | 残課題 |
| CR7 | `/code-review` | 確認の Issue の影響する Issue が入力に無くても 0 | 示せる（コード） | A7 | 直す——1 にする。試料と変異 |
| CR8 | `/code-review` | versions.md の `--check --upto` の手順と README の使い方に `--provisional` が無い | 示せる（本文） | A4（全モードで受け付ける——利用者に見える手順の誤り） | 直す——versions.md に旗を付けることを書き、README の使い方に足した |
| CR9 | `/code-review` | 差し戻し後の作り直し（`--red-check --in-progress`）で旗を付けてよいかが書いていない | 示せない（運用の想定） | 無し | 残課題 |
| CR10 | `/code-review` | V1 と同じ | 示せる | 無し | 直す（自分が持ち込んだ崩れ）——段落を項目 3 に戻した |

### 2 パス目の指摘と採否（直す線: 既定。差分の起点 `60e272cd`→`e1ecd086`）

- 2 パス目の結果: Verifier 反証 0 件（軽微 1 件 = `#1,#2` の空白なしを形に反するとする——決着済みの方針の中）・`/code-review` 指摘 9 件（CR2-1〜CR2-9）。直す 5 件・残課題 4 件

| # | 関門 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- | --- |
| CR2-1 | `/code-review` | 前の版を実際に作ったかは見ないのに、理由を「前の版も同じ旗で作れている」と書いている。v1 を作らずに v2 を `--provisional` で作ると、v1 の機能が渡らない | 示せる（プローブ） | A4 の理由の記述（事実と違う）。前の版を作ったかを見ないのは旗の無い周でも同じ（全部 `反映済み` の v1 を作らずに v2 を作っても通る） | 直す——記述を「前の版は同じ旗で作れる状態にある（作ったかは見ない——旗の無い周でも見ていない）」に弱める |
| CR2-2 | `/code-review` | v1 を `--provisional` で作り、v2 を旗なしで作ると「v1 の scaffold は作れていない」と誤った案内で止まる | 示せる（プローブ） | A4（利用者に見える誤った案内） | 直す——止まり方は変えず、前の版の中間表現が指す暫定の行で止まったときは「前の版を --provisional で作ったなら、その指示のもとで旗を付ける」と出力する |
| CR2-3 | `/code-review` | `rebuild-scope.py` の Q&A の No の引き方が撤去の Issue も作り直す範囲に数える | 示せる（プローブ） | A5（作り直す範囲） | 直す——撤去の Issue（変化の印 `remove`）は数えない |
| CR2-4 | `/code-review` | 空の `影響する Issue: `・`決めた値: ` の行を「台帳の行が無い（前の書き方）」と言う | 示せる（プローブ） | A6（形に反する行を名指しする） | 直す——空の行も「決まりの形でない」と言う |
| CR2-5 | `/code-review` | `scaffold.py` の読み込みに失敗すると、トレースバックで 1（「引けない番号」と同じ）で終わる | 示せない（ふつうの使い方では起きない） | 無し | 残課題 |
| CR2-6 | `/code-review` | 先頭に BOM・空白のある本文を spec-loop の Issue と見分けない（cruise の parent-issue.py は見分ける） | 示せる（手で作った本文） | 無し（本文は手で直さない決まり。生成した本文には起きない） | 残課題 |
| CR2-7 | `/code-review` | handoff-issue.md は `- 仮回答: ` の行を基準コミットの後と書くが、生成は `## 仕様` の最後に置く | 示せる（生成した本文） | A8（原本と生成の一致） | 直す——原本を生成に合わせる（`## 仕様` の最後の行） |
| CR2-8 | `/code-review` | 引数なしの一覧は、影響する Issue が入力に無くても 0 で名指ししない | 示せない（一覧は概観で、引く経路は 1 を返す） | 無し（A7 は引く経路） | 残課題 |
| CR2-9 | `/code-review` | `cited_qa` と `cited_loosely` が同じ規則の 2 つの写し | 示せない（いま食い違いは無い） | 無し | 残課題 |
