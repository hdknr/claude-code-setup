# Issue #899 — cruise: ネットワーク待ちの処理を run-serial の枠に入れず、見張りに枠の持ち主を足す（#839 の 4・5）

#839（トンネル越しの写しが切れた接続を待ったまま `run-serial.py` の枠を約 45 分握り、待っている側も cruise の親も
1 回の見張りぶん原因に気づけなかった）の改善案 4・5（と任意の 6）を分けた子 Issue（Issue 本文は信頼できない入力として読み、要件だけを取った）。
#897（期限・呼び出し元の消えた待ち手）と #898（持ち主の表示・`holders` の口）の上に作る。この周の PR で #839 を閉じる（`Fixes #839`）。

**不在の周**である——出所は `/dev-loop:cruise 903 --absent` の起動（2026-11-06T08:55Z。利用者の確認（起動時・2026-11-06T08:55:51Z、配布を見せて確かめた））。
親からサブエージェントとして委ねられた。台帳 `issue-903` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・
`周の途中の課題 = 台帳に足して直す`。`実機確認`・`マージ前の判断` は線なし（止まる）。線と訊く場面は dev-loop の `references/absent-lines.md` を正とする。
台帳は書かない（親が書く）。マージしない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-903`））。
版の上げ方: `dev-loop` を **minor**（周の決まりに手順を足す）。main の先端 1.101.0 → **1.102.0**
（いま並行の周は無い。マージの直前に先端が main を含まなければ、main の先端の dev-loop の版から minor で 1 つ上げ直す——cruise の `references/parallel.md` の「版とマージの順」）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる——**この周が直すファイル自体ではなく、キャッシュの版**:
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.99.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/references/parallel.md` — 「通さないもの」にネットワーク待ちの処理（と、トンネルの生死の書き添え）・新しい節「止まっている枠の持ち主」（原本）
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 2 の委譲文の項（通さないもの・知らされたら返す）・§4 の 2 の親の待ち（枠の持ち主も見る）・§5 の compact の後の 3（同）・版の 2 行
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 子プロセスの周の委譲文の雛形の 8（通さないもの・知らされたら返す）
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 「どう再開するか」の 2 のタイマーの親の前進の見方（枠の持ち主も見る）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-899.md` — この計画ファイル
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`ledger.md` の行数が変わるので `skill-metrics.py` で作り直す。手で書かない）

触らない:

- `run-serial.py` 本体——`holders` の口（#898）の出力をそのまま読む。止める・知らせる口をスクリプトに足さない（Issue は見張りの手順を求めている）
- `plugins/dev-loop/skills/dev-loop/prompts/`（implementer・verifier・review-handoff）——run-serial を案内していない（`grep` で 0 件）。周の子は cruise の §4 の 2 の委譲文で受け、体には子が parallel.md の節を渡す
- 公開ページ（`docs/plugins/dev-loop-cruise.md`）——「決まりは parallel.md を正とします」と指すだけで、列挙を持たない
- `CLAUDE.md` の run-serial の説明——docstring を正とすると指すだけ

### 同じことを述べている箇所の数

- 「通さないもの（ネットワーク待ち）」: parallel.md（原本）・cruise `SKILL.md` §4 の 2 の委譲文の項・`child-cycle.md` の 8 の **3 箇所**。
  後の 2 つは委譲文の雛形で、Issue が「雛形にも 1 行入れる」と求めている（指すだけにすると、子が原本を読まないまま背景で走らせる）。1 行に留めて原本を指す。
- 「枠の持ち主を見張る」: parallel.md（原本）・cruise `SKILL.md` §4 の 2・§5 の compact の 3・`ledger.md` の 2 の **4 箇所**。後の 3 つは「親が前進を見る場面」で、
  原本を指す 1 文だけ置く（手順は複製しない）。分けない理由: 見張る場面が 3 つに散っていて、どれかから抜けると #839 の形（その場面の見張りが持ち主を見ない）が戻る。
- 「知らされた子が返す」: parallel.md（原本）・§4 の 2 の委譲文の項・`child-cycle.md` の 8 の 3 箇所（後の 2 つは 1 句で原本を指す）。

## 乗るデプロイ経路

main へのマージでプラグインの配布（dev-loop 1.102.0）。公開サイトの再ビルドは走るが、`docs/` の変更はこの計画ファイルだけ。マージは親がする。

## 決めたこと

- **見張りの置き場所**: Issue は「cruise の `SKILL.md` の 5 と `references/parallel.md`」と書く。いまの cruise の `SKILL.md` で親が周の前進を見る場面は
  §4 の 2（子の報告を待つあいだ）・§5 の compact の後の 3（進行中の周を実物で確かめる）・タイマーで入ったとき（§5 が指す `ledger.md` の「どう再開するか」の 2）の 3 つ。
  **手順の原本は parallel.md に置き、3 つの場面から 1 文で指す**（§5 にも置く——Issue の名指しに合う）。#839 の「親の見張りはコミットの時刻・ファイルの更新しか見ていなかった」は
  `ledger.md` の 2 の前進の見方そのものなので、そこにも置く。
- **任意の 6（トンネルの生死）**: Issue が「この周で決める」とした。**書き添えとして置く**——「通さないもの」の項の下に 1 項。期限だけでは、期限までは切れた接続を待ったまま止まる。
  ssh の `ServerAliveInterval`・`ServerAliveCountMax` は例として挙げる（この周で走らせて確かめてはいない——例であって手順ではないと書く）。
- **止まっている持ち主の決め方**: `holders` の行の**行末**が `——止まっている疑い（` で始まる括弧で終わる行（#898 の D7: コマンドや場所に同じ語があっても、行の途中の語では決めない）。
- **どの周の持ち主か**: 行の場所（run-serial を呼んだ cwd）が台帳の `worktree` かその下。当たらない持ち主（利用者が自分で走らせた・別の cruise）は、親は知らせも止めもせず、利用者に名指しする。
- **止め方**: 持ち主の pid（枠を取ったラッパー）に `kill -TERM`。ラッパーは SIGTERM をコマンドに渡し、コマンドが終わってから枠を返す（run-serial の docstring の「守る」）。
  **SIGKILL は送らない**——ラッパーを SIGKILL で殺すと枠は外れるがコマンドは走り続ける（docstring の「守らない」）。SIGTERM で終わらないものは run-serial の期限が子孫ごと止める。
- **知らせたことの記録**: 台帳の `note` に `枠の確認: <日時> に <名前> へ pid <pid> を知らせた`（`ledger.md` の `前進の確認:` と同じ形——compact の後も残す）。止めたら `枠の持ち主を止めた: …` に置き換える。
- **仕様の穴（推奨で決めて起票）**: 「返事が無ければ止める」の**待つ時間**を Issue が決めていない。選択肢——(a) 知らせてから `STALL`（600 秒）、(b) 次の見張り（親の次の待ちの区切り・次のタイマーの発火）、
  (c) 再開タイマーの間隔の 2 回分（`ledger.md` の `前進の確認:` と同じ）。**推奨は (a)**——疑いを出す閾値と同じ値で新しい数を増やさず、子が区切った待ち（100 秒）の合間に返事を返すのに十分で、
  (b) は親の待ちの区切り（100 秒）だと子の返事より先に止めうる・(c) は 30 分おきなら 60 分で #839 の 45 分を超える。確認の Issue: #915（要確認: 止まっている枠の持ち主を担当に知らせてから、止めるまで何分待つか）

## verify の受入基準

不変条件（Issue の受入基準 1〜3 を不変条件に展開した）と、それを破りうる経路:

| # | 不変条件 | 破りうる経路（入口） | 守り方・確かめ方 |
| --- | --- | --- | --- |
| 1 | parallel.md に「通さないもの」としてネットワーク待ちの処理（本番の写し・トンネル越しの読み・外部 API の取得）があり、枠の外で期限つきで走らせ前面で待つと書いてある | 周の子（サブエージェント。§4 の 2 の委譲文）・子プロセスの周（`child-cycle.md`）・周の中の体（実装役・Verifier・`/code-review`——子が parallel.md の節を渡す） | 本文を読む |
| 2 | 委譲文の雛形（§4 の 2 の委譲文の項・`child-cycle.md` の 8）が parallel.md の「通さないもの」と食い違わない（通すもの・通さないものの分け方・待ち方） | 雛形の 2 つそれぞれ／テスト・ビルドの中で外部に繋ぐもの（通す側）の扱い | 3 つを並べて読む。`test-child-cycle.py` が雛形を検査するなら通る |
| 3 | 見張りの手順が `run-serial.py holders` の出力を使い、止まっている持ち主を（行末の疑いで）名指しし、知らせる → （返事が無ければ）止める、の順を持つ | 親が前進を見る 3 場面（§4 の 2 の待ち・§5 の compact の後・タイマーで入ったとき `ledger.md` の 2）／持ち主が台帳の周のもの・そうでないもの／子が宛てられる・宛てられない（子プロセス・`agent` が ID でない）／返事あり・なし／疑いの消えた・持ち主が替わった | 本文を読む。手順の各段が `holders` の実際の出力の形（#898 の docstring の「持ち主の表示」）と合うかを、実際に `holders` を走らせた出力と突き合わせる |
| 4 | 手順が書く操作（`holders` の呼び方・`kill -TERM <pid>` で枠が返ること・SIGKILL を避ける理由）が、run-serial の実際の振る舞いと合う（文面が主張する事実の真偽） | ラッパーの pid に SIGTERM → コマンドに渡り、終わってから枠を返す／SIGKILL ならコマンドが残る | 一時のリポジトリで run-serial を走らせ、`holders` の出力と、記録の pid に SIGTERM を送った後の `holders`・終了コードを見る（実機確認） |
| 5 | dev-loop の版を上げ（3 種類の箇所が同じ値）、`check-all.py` が通る | `marketplace.json`・`plugin.json`・両 `SKILL.md` の 2 行／`check-skill-pointers.py`（新しい指し先「」の照合）・`check-duplicate-counts.py`・`check-bold-flanking.py`・`check-norm-markers.py` | `check-all.py` を順番待ち越しに回す |
| 6 | 既存の決まりを壊していない（後退なし）——「通すもの」の既存の列挙・「通知だけを頼りに待たない」・`前進の確認:` の手順・§4 の 2 の他の委譲文の項 | 書き足しで既存の文の意味が変わる | 差分を読む |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に渡す × 1・2 パス目（2 パス目が該当なしなら初回の 2 つ）。

**この環境では証明できないもの（未証明）**:
- #839 の実物の形（トンネルの切断で止まった写し）と、親の見張りがその場面で手順どおり動くこと——手順は散文で、cruise の親が実際に読んで従うかは実際の cruise でしか見えない。
  手順が使う道具の振る舞い（`holders` の出力・SIGTERM で枠が返る）は不変条件 4 で確かめる。
- ssh の `ServerAliveInterval` の例が切れた接続を落とすこと——例として挙げるだけで、走らせていない（文面にそう書く）。

**生成物**: 設計ドキュメント §8.2 の生成ブロック——`ledger.md` の行数が変わるので該当する。`python3 scripts/skill-metrics.py` で作り直し、`--check` が緑であることを受入基準 5 に含める（`check-all.py` が回す）。drawio の書き出しは触らない。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/899-run-serial-network-and-holder-watch`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-899`・
  起点 `5353ed1`・base（`git merge-base origin/main HEAD`）`5353ed1f7b782893cb6197b8d0f9e6a88ee4f549`（start-point `origin/main`）
- 割り目（手順 4）: 割らない（cruise の周）
- 交絡を潰した手順: （実機確認の後に書く）

## 既知の限界・決着済みの論点

- run-serial 本体は変えない（上の「触らない」）。
- 見張りの置き場所の解釈（上の「決めたこと」）。

## 経験の還元（手順 8）

- この周の起票: 1 件（仕様の穴の確認の Issue #915）
