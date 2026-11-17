# Issue #1167 — cruise / autopilot: claude -p の子プロセスと外側のループに auto-compact の窓を渡せるようにする

**不在の周**（`/dev-loop:cruise 1168 --absent` の起動・2026-11-17）。利用者には訊かない。親（cruise #1168）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1168`）。不在の周で、起動は `/dev-loop:cruise 1168 --absent`（2026-11-17）、配布を見せて確かめた）:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`。
台帳（`.claude/plans/cruise-issue-1168.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
依存先の #1166 は main にマージ済み（dev-loop 2.6.0）。読み込まれた dev-loop は 2.4.0（本文 1920 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1168`））。
版の上げ方: `dev-loop` を **minor**（起動口に任意の窓の引数を足す——能力の追加）、`spec-loop` を **minor**（0.x。autopilot-loop に同じ引数を足す）。
着手時の main は dev-loop 2.6.0・spec-loop 0.100.1。PR を出す時点の main の先端の版から上げる。マージの直前に main が進んでいたら親の依頼で取り込み、先端の版から上げ直す。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.4.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: 3 つの起動口（`child-cycle.py`・`outer-loop.py`・`autopilot-loop.py`）に窓を渡す任意の引数を足す・既定は渡さない・書式と範囲を起動の前に検査する・
環境変数が既にあって効かないとき表示する・実物で窓が効くことを確かめる。本文に受入基準を緩める指示・コマンド実行の依頼は無い。

確かめたこと（実物の `claude` 2.1.326 で走らせた。`claude -p "say ok" --model haiku --max-budget-usd 0.05` に `--autocompact <値>` を付けた）:
`400000`・`400k` は受ける。`99999`・`2M` は `must be 'auto', or between 100k and 1M (e.g. 500k, 200000, or 200 as shorthand)` で起動前に拒む。
**`400` は受ける（フラグでは 400k の略記）**——環境変数 `CLAUDE_CODE_AUTO_COMPACT_WINDOW` では数字だけはトークン数（400 は 400 トークンで最小を下回る）なので、**手段で書式の解釈が違う**。
だからスクリプトは**トークン数（100000〜1000000）の整数に正規化してから渡す**（`400000`。両方の手段が同じ値に読む）。入力の書式は「数字だけ（トークン数）」「数字 + `k`（千）」「数字 + `M`（百万）」で、
`400` のような小さい数字だけは**拒む**（フラグの略記と取り違えない。`400k` と書くよう案内する）。渡す手段はフラグ（`--autocompact`）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/child-cycle.py` — 窓の引数・正規化・検査・フラグを渡す・環境変数の通知・記録（正規化の原本）
- `plugins/dev-loop/skills/cruise/scripts/outer-loop.py` — 同じ引数。検査と正規化は `child-cycle.py` を読み込む（写さない）
- `plugins/spec-loop/scripts/autopilot-loop.py` — 同じ引数。spec-loop だけの利用者に dev-loop は無いので、関数は写しを持つ
- `scripts/test-child-cycle.py` — 回帰テスト（変異テストを含む）
- `scripts/test-outer-loop.py` — 回帰テスト（変異テストを含む）
- `scripts/test-autopilot-loop.py` — 回帰テスト（変異テストを含む）
- `plugins/dev-loop/skills/cruise/references/child-process.md` — 「auto-compact の窓」の 1 節（実物で確かめた記録の置き場）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ（cruise の `SKILL.md` の説明は別 Issue）
- `plugins/spec-loop/skills/` — 各 `SKILL.md` の版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `CLAUDE.md` — 3 起動口の項目に窓の 1 文（プロジェクトの構成の一覧。原本は docstring）
- `docs/plans/issue-1167.md` — この計画ファイル

触らない:

- cruise の `SKILL.md` の説明（別 Issue。Issue の範囲の外）
- 判定役のエージェントの frontmatter（Issue の範囲の外）
- screen-spec（`claude -p` を自分で起動している場所が無い）
- `autopilot-check.py` と cruise の線の確認での窓の表示（Issue の「提案」にはあるが受入基準に無い。穴 G1 で決めた）
- 子の環境への `CLAUDE_CODE_AUTO_COMPACT_WINDOW` の設定（手段はフラグ。環境変数は「利用者が既に置いている」場合の通知にだけ使う）

## 設計の判断

- **原本は `child-cycle.py` の 1 組**（`parse_window`・`window_flag`・`window_override_note`）。`outer-loop.py` は `child_cycle()` で読み込む（`read_cost` などと同じ形）。
  `autopilot-loop.py` は spec-loop 単体で動くので**写しを持ち**、`test-autopilot-loop.py` が 3 関数のソースを突き合わせる（陽性対照: 1 文字変えた写しは「違う」と出る）。
  複製の数: 2（原本 1 + 写し 1）。分けない理由: 1 本の周で書ける量で、写しの一致はテストが見る（既存の `COPIED` の仕組みに乗せる）。
- 既定は渡さない（引数が無ければ起動コマンドは今と 1 バイトも変わらない）。渡したときだけ `--autocompact <トークン数>` を、`claude` の引数の `-p` の組の後・`--append-system-prompt` の後ろ・利用者が足す引数（`--` の後ろ）の前に足す。
- 範囲外・書式違いは起動の前に 2（`child-cycle.py` は Usage の 2、`outer-loop.py`・`autopilot-loop.py` は引数の 2。**通知もしない**——引数を読む前に止まる形）。
- 環境変数 `CLAUDE_CODE_AUTO_COMPACT_WINDOW` が空でなく設定されていれば、渡した窓は**効かない**（公式: 環境変数がフラグに優先する）ので、起動時に 1 行で言う（値は利用者の設定なので出してよい）。
  それでも渡す（利用者が環境変数を後で外せば効く）。
- 記録: `child-cycle.py` は記録の `.json` に `autocompact`（渡したトークン数と、環境変数に上書きされるか）を残す。渡さなければ null。

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **G1 cruise の線の確認・`autopilot-check.py` で窓を利用者に見せるか**: Issue の「提案」にあるが受入基準に無い。選択肢: (a) 今回は足さない（推奨）／(b) 足す。
  推した理由: 窓は起動口の引数で、点検の時点では起動口の引数が決まっていない（`autopilot-check.py` は線と権限を見るもので、外側のループの引数を知らない。cruise の線の確認は cruise の `SKILL.md` の説明で、別 Issue の範囲）。
  代わりに起動口自身が起動時に「子に渡す窓」を 1 行で出す（Issue の目的の「利用者に見せる」は起動口の出力で満たす）。→ 確認の Issue（親が立てる）
- **G2 outer-loop が起こす cruise の親が起こす子（`child-cycle.py` の子）にも窓を掛けるか**: Issue の対象は 3 つの起動口がそれぞれ起こす `claude -p` 1 つずつ。選択肢: (a) 各起動口が起こす `claude` にだけ渡す（推奨）／(b) 外側のループが環境変数を置いて子孫すべてに掛ける。
  推した理由: 環境変数は判定役のサブエージェントにも掛かる（#1166 で公式から確かめた）ので範囲が広がり、フラグは起こした `claude` 1 つにだけ効く。子の窓は `child-cycle.py` の引数で別に決める。
  決めた値は `references/child-process.md` に 1 文で書く。→ 確認の Issue（親が立てる）

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口（`claude -p` を起こす場所）: `child-cycle.py launch`・`outer-loop.py`・`autopilot-loop.py`。ほかに自分で `claude -p` を起こす場所が無いことを `grep` で確かめる（B2）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 3 つの起動口が窓を受け取り、指定したときだけ子に渡す。**指定しないときの起動コマンドは今と変わらない** | 常に渡す・渡さないのに空の引数を足す | 引数が無いときの argv を、変更前の版の期待値と一致させる（3 起動口とも）。変異: 常に渡す |
| A2 | 範囲（100000〜1000000）の外・書式の誤りを、**起動の前に**拒む（記録・出力の置き場・子・`claude` を作らない） | 検査が起動の後・境界の取り違え・数字だけの小さい値を略記と読む | 境界（99999・100000・1000000・1000001）と書式の誤り（`400`・`4e5`・空・負・全角・小数・`k` 抜け）で、3 起動口とも 2・`claude` を起こさない |
| A3 | トークン数の整数に正規化して渡す（`400k` → `400000`、`1M` → `1000000`、数字だけ → そのまま） | k を 1024 と読む・数字だけを千と読む | 渡された argv の値を見る（3 起動口とも） |
| A4 | `CLAUDE_CODE_AUTO_COMPACT_WINDOW` が既に設定されていて効かないとき、その旨を表示する。設定されていなければ言わない | 言わない・常に言う・値が空でも言う | 環境変数あり・なし・空で、3 起動口の起動時の出力を見る |
| A5 | 窓を渡さないとき、環境変数があっても何も言わない | 渡していないのに警告する | 同上 |
| A6 | 子で窓が効いていることを実物の実行で確かめた記録がある（陽性対照: 渡さない場合と比べる） | 効いていない陰性を「効いた」と読む | 下の「実物の確かめ」 |
| A7 | 版を上げ（dev-loop 2.7.0・spec-loop 0.101.0。3 種で揃う）、`check-all.py` が通る | 版の取りこぼし | `check-plugin-versions.py`・`skill-metrics.py --check`・`check-all.py` |
| A8 | 範囲の外（cruise の `SKILL.md` の説明・判定役の frontmatter・screen-spec）に手を入れていない | 範囲の拡大 | 差分が `触る:` に収まる（`check-plan-scope.py`） |
| A9 | 3 起動口の「守る」の行数と変異の数が 1 対 1（テスト自身が数える） | 守る行を足して変異を足さない | 3 本のテスト |

**検証で証明できるもの**: A1〜A5・A7〜A9（偽の `claude` と一時ディレクトリ。実物の `claude` には届かない）。A6 は実物の `claude -p` で確かめる（子の起動口 `child-cycle.py` の経路。最小の呼び出しと費用の上限つき）。
**この環境では証明できないもの（未証明）**: `outer-loop.py`・`autopilot-loop.py` で起こした実物の `claude` で窓が効くこと（同じフラグを同じ形で渡すことは偽の `claude` で見たが、実物の長い cruise・autopilot の親では起こしていない）。
`child-cycle.py` で実物を回すときも、`/dev-loop:dev-loop` の周そのものは回さない（周を回すと費用と副作用が大きい）。起動口が組んだ引数を、使い捨てのディレクトリで最小の呼び出しに差し替えて実物の `claude` に渡す（差し替えは `claude` の前に置いた包みで、`-p` の文と委譲文だけを替える。窓の引数と環境は起動口のもの）。
**生成物**: 該当あり——`docs/plugins/dev-loop-design.md` §8.2 の生成ブロックは dev-loop の `SKILL.md` の節構造から `skill-metrics.py` が作る（この周は `SKILL.md` の行数・節を変えず、`skill-metrics.py` は「変更なし」・`--check` は最新）。図なし。
**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パスとも渡す。

## 実物の確かめ（A6）

実物の Claude Code 2.1.326・`--model haiku`（init の `model` は `claude-haiku-5-5`）で、`child-cycle.py launch` が組んだ引数を、使い捨てのディレクトリ（リポジトリの外のスクラッチ・空の git リポジトリ）で最小の呼び出しに差し替えて実物の `claude` に渡した。
差し替えは `claude` の前に置いた包み（`-p` の文と `--append-system-prompt` の中身だけ。`/dev-loop:dev-loop` の周は回さない）。`--autocompact` と環境は起動口のまま。許可モード `dontAsk`・`--allowed-tools Read`・`--max-budget-usd 0.6`。長期トークンの値は出力に出していない（`認証:` の行は「値は出さない」）。
計約 $0.89（出力ファイルの合計 $0.85 に書式の確かめと逆向きの対照の分を足した。最初の試しの $0.45 を含む。1 回目は 1 ターンに約 44.5 万トークンを渡して予算を食った）。詳細な表と読み方は `plugins/dev-loop/skills/cruise/references/child-process.md` の「auto-compact の窓」。

- **交絡の候補**（主張が偽でも同じ出力が出る設定）: (1) 窓を渡した子が compact したのは、渡した窓のせいではなく入力が違うから → 同じ 7 ファイル・同じ文で、窓を渡さない子（compact 0・8 ターン）と比べた。(2) 窓を渡さない子が compact しないのは「もともと compact しない」設定だから → 窓を渡した子が同じ入力で compact した（陽性対照）。
  (3) 環境変数が効くはずなのに効かない → 環境変数 `CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` と窓 100k を併せた子は compact 0（環境変数が優先。起動口の「効かない」の表示と合う）。
  (4) 1 ターンの長い入力（約 13 万トークン・窓 100k）は compact しなかった——これを「窓が効かない」と読まない。ターンをまたいで積み上がる子で測り直し、compact が出た。
- **観測窓**: 各条件 1 回ずつ。出力ファイル（stream-json）の `compact_boundary` の行を数えた。窓 100k の子は 10 ターンで compact 2 回（圧縮前 71188・72882 トークン）。ほかの窓の値・ほかのモデル・長い周は測っていない。

| 条件 | `compact_boundary` | ターン数 |
| --- | --- | --- |
| 窓を渡さない（環境変数も無い） | 0 | 8 |
| `--autocompact-window 100k` | 2 | 10 |
| `--autocompact-window 100k` ＋ 環境変数 1000000 | 0 | 8 |
| `--autocompact-window 1M` ＋ 環境変数 100000（逆向き） | 2 | 10 |

**実物を起こしたのは `child-cycle.py` の経路だけである。** `outer-loop.py`・`autopilot-loop.py` は、同じ `--autocompact <整数>` を同じ位置で渡すことを偽の `claude` で確かめた（未証明に書いた）。

## 未解決の判断・確認待ち

- G1・G2（上）は推奨で決めた。確認の Issue は親が立てる。

## 起票

- この周の起票: 0 件（確認の Issue は親が立てる。残課題の起票はしない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1167-autocompact-window`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1167`・
  起点 `692913b`・切った元の参照 `origin/main`（解決した SHA `692913bc4b579ffa03ec0e4d70ccd2c58a35f40d`）・base `692913bc4b579ffa03ec0e4d70ccd2c58a35f40d`
- 割り目: 割らない（cruise の周）。交絡を潰した手順: 後の「実物の確かめ」に書く。

## 既知の限界・決着済みの論点

（関門の採否の表をここに畳む）
