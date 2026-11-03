# Issue #630 — 周の途中で足した行の世代を数え、後続の後続を台帳で回さない

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。cruise の親から委ねられたサブエージェントが回す。
台帳 `issue-793` の確かめた線（出所: 利用者の確認（起動時・親 Issue #793 の cruise: の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳 `.claude/plans/cruise-issue-793.json` には書かない**（書くのは親だけ）。**手順 7 のマージはしない**（PR・CI の確認まで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（能力の追加——`ledger.py` が世代を数えて足し方を変える）。main の先端 1.77.0 → **1.78.0**
（PR を出す前・マージの直前に main が進んでいたら、その先端から minor で上げ直す）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

## 設計の判断

- **世代の定義**: 親 Issue の一覧から作った行（`origin` が空）は 0。`origin` のある行は、`origin` の最初の `#<番号>`
  （found-lines.md の出所の書式 `#<元の周> <関門> <パス>` の元の周）が台帳に在ればその行の世代 + 1、無ければ（辿れない）1。
  辿った先が循環していたら、そこで止めて数えた分で答える（無限ループにしない）。
- **世代 2 以上の `add` は拒まず、`blocked`・`note` が `利用者の判断待ち: …` の行として足す**（Issue の受入基準案の「拒否されるか利用者の判断待ち」の後者）。
  拒むと出所の記録が台帳から消え、cruise の終わり（§6）の「周の途中で足した行」で渡せない。`blocked` なら `next` に出ず、`show`・`status`・§6 が
  既に「利用者の判断待ち」として扱う（新しい状態を作らない）。利用者が直すと答えたら既存の手順（`found-lines.md` の「利用者の判断をまとめて訊く」）で `todo` に戻す。
- **`deps` ではなく `origin` で辿る**——`--deps` は元の周の他にも依存を持ちうる。`origin` の書式は found-lines.md が決めている。
- **found-lines.md は PR #803（#670。未マージ）が書き換える節（表の列・「`要確認` の Issue」・「台帳に足す」）を避け、「直すのは 3 つだけ」と「後続の後続」にだけ書く**——
  食い違いと衝突を避ける。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — 世代を数える関数・`add` の世代 2 以上の足し方・`show` の世代の表示・docstring
- `scripts/test-ledger.py` — 世代の試料（合成の台帳で main の本体が赤・新しい本体が緑）と変異
- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — 「直すのは 3 つだけ」に「実物に在る形」・「後続の後続」に世代の上限
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-630.md` — この計画ファイル

触らない:

- `references/ledger.md`・cruise `SKILL.md` §6 の本文——足し方の原本は found-lines.md と ledger.py の docstring で、そこは指すだけ（`blocked` の扱いは既存のまま効く）
- found-lines.md の「台帳に足す」「`要確認` の Issue」・表の列——PR #803 が書き換える
- `LINES` の値——変えない（互換）
- 公開ページ（`docs/plugins/dev-loop-cruise.md`）——世代の規則は原本を指す形で足りる

### 同じことを述べている箇所の数

世代の上限を述べる箇所: `found-lines.md`「後続の後続」（規範の原本）・`ledger.py` の docstring（守るもの）——**2 か所**。
分けない理由: 規範（なぜ・何を訊くか）と、スクリプトが守る振る舞いは別のもので、docstring は found-lines.md を指す。
「実物に在る形」: `found-lines.md`「直すのは 3 つだけ」の 1 か所。

## 受入基準

不変条件と、それを破りうる経路（経路は「周の途中の課題の行が台帳に入り、回される入口」から数える: `add`・`set`・手で直した台帳の `load`・`next`・`status`・`show`）:

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | 世代 2 以上の行は、足しても周として回されない（利用者の判断待ちになる） | `add --origin`（出所の `#N` が出所のある行） | `add` が `state=blocked`・`note=利用者の判断待ち: …` で足す | 合成の台帳（#1 一覧 → #2 世代 1 → #3 世代 2）で **main の本体は `next` に #3 を出す（赤）**・新しい本体は出さない（緑） |
| A2 | 同上 | `next`・`status` | `blocked` は既存のとおり `next` に出ず、`status` は着手できると数えない | 同じ試料で `next` と `status` を見る |
| A3 | 同上（世代 3 以上も） | 世代 2 の行から足した行 | 辿りが再帰 | 世代 3 の試料 |
| B | 世代 1 の行はこれまでどおり `todo` で足す（後退しない） | `add --origin`（出所の `#N` が一覧の行） | 世代 1 は変えない | 既存の試料（`origin の add`）が緑のまま＋世代 1 の `next` |
| C | `show` が、周の途中で足した行の世代を出す | `show` | 「周の途中で足した行のうち済んでいないもの」に世代を添える | 試料の `show` の出力 |
| D | 辿れない・循環した出所で、止まらない・壊れない | `origin` に `#` が無い・台帳に無い番号・自分を指す・2 行で互いに指す（手で直した台帳・`set origin=`） | 辿れなければ 1、循環は訪れた行で止める | 試料（自己参照・相互参照・番号なし・台帳に無い番号） |
| E | `found-lines.md` に世代の上限と「実物に在る形」の規則があり、`ledger.py` の振る舞いと食い違わない | 文書 | 「後続の後続」と「直すのは 3 つだけ」 | 読んで突き合わせる（関門） |
| F | 拒んだ操作で台帳を変えない・台帳の形を変えない（新しい鍵・状態を作らない） | `add` | 既存の `validate` の範囲 | 既存のテスト |
| G | 版の 3 箇所一致・`check-all.py` が緑・変異の数が「守る」の行数と一致 | CI | — | `check-all.py`・PR の CI |

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（該当すれば）に渡す——4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

**証明できないもの（未証明）**: 実際の cruise の中で親が世代 2 の行を足したときに、利用者の判断待ちとして終わりに渡されるか（cruise を 1 本回さないと見えない）。
`blocked` の行の扱いは既存のテストが見ているので、`add` が `blocked` で足すことまでを証明する。

**生成物**: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を触るので `skill-metrics.py --check` で鮮度を見る）。図の書き出しは無し。

## 未解決の判断・確認待ち

- なし（不在の周。仕様の穴は無い——Issue の提案 2 が「利用者の判断として blocked にして渡す」と決めている）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/630-ledger-generation-limit`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-630`・
  起点 `63872f51`・base `origin/main` = `63872f5167ac87b9c7280b308c1f57e28ab5ca5d`
- 割り目（手順 4）: 割らない（不在の cruise）
- 実験: 合成の台帳で main と新しい本体を比べる（陽性対照: main の本体で赤）

## 既知の限界・決着済みの論点

（関門の指摘の採否の表はここに足す）

- `set origin=` で後から出所を書き換えて世代 2 にした行は `blocked` にしない——`add` の時点だけで決める（docstring の「守らない」）。
- `origin` の最初の `#番号` を元の周と読む——書式（found-lines.md）を外した出所は辿れず世代 1 と数える。
