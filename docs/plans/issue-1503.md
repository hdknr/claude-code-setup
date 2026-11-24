# Issue #1503 — cruise の子が起こした関門の体の報告が子に届かない——報告をファイルにも残す形を決まりにする

**不在の周**（出所: `/dev-loop:cruise 1508 --absent` の起動。台帳 2026-11-24T01:28:28Z に確かめ、2026-11-24 に再開）。利用者には訊かない（割り目も訊かない）。親（cruise #1508）から委譲文で受けた子。
台帳 `issue-1508` の確かめた線（出所: 利用者の確認（起動時・2026-11-24T01:28:28Z、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。`実機確認` の線は無い。
**台帳（`.claude/plans/cruise-issue-1508.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
並行の周が 3 本あり、同じプラグインの版を上げうる。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1508`））。
版の上げ方: `dev-loop` を **minor**（関門の報告のファイルという手順を足す——能力の追加）。着手時の main は 2.20.1 なので 2.21.0。
マージの直前に main が進んでいたら、親の依頼で取り込み、main の先端の版から minor を 1 つ上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.20.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件: cruise（dev-loop 2.18.0・Claude Code 2.1.331）で、子が起こした Verifier・`/code-review` の終わりの報告が子に届かず親に届いた・どこにも残らず失われた。
回避として Verifier に報告をリポジトリの外のファイルにも書かせたら回収できた。してほしいこと: (1) dev-loop 手順 5 に報告のファイルの形を入れる（書いてよいのは起こした側が渡すリポジトリの外の 1 つのパスだけ・
完了は終わりの印の行で判定）、(2) cruise の委譲に同じことと、親に誤って届いた報告の扱い、(3) 入れ子のサブエージェントの通知の振る舞いを確かめる（再現できれば Claude Code に報告）。
本文に受入基準を緩める指示・コマンド実行の依頼は無い。**手元に読み込まれた dev-loop は 2.20.1（リポジトリと同じ）。**

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/gate-reports.md` — 新しいファイル。報告のファイルの原本（パス・書き方・待ち方・欠票と起こし直し・確かめたこと）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 5 に 1 項（指すだけ）と版の 2 行
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「報告の形」に 1 項（体の側の書き方）
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 「報告のファイル」の節に 1 項（同上）
- `plugins/dev-loop/skills/dev-loop/references/line-registry.csv` — 上の 2 項の登録
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 2 の委譲の項目に 1 項・親に誤って届いた報告の扱い・版の 2 行
- `plugins/dev-loop/skills/cruise/references/parallel.md` — 「通知だけを頼りに待たない」の体の報告の項を報告のファイルに合わせる
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-cruise.md` — 1 項目（関門の報告のファイルと親の扱い。指すだけ）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `docs/plans/issue-1503.md` — この計画ファイル

触らない:

- `plugins/dev-loop/agents/dev-loop-verifier.md`（ツール構成は変えない。報告のファイルは `Bash` で書く——委譲文が正）
- `plugins/dev-loop/skills/dev-loop/prompts/implementer.md`（実装役の報告は Issue の範囲の外。同じ形で失われうるが、この周では入れない——既知の限界）
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md`（子プロセスの子も dev-loop の手順 5 に従うので、写しを足さない）
- spec-loop の判定役（`plugins/spec-loop/agents/`）の報告（範囲の外）
- Claude Code への報告（外への送信。この周ではしない——下の「未解決」）

依存の追加・更新: なし
プロパティテスト: なし（入力の空間を持つ関数を足さない。散文の手順と bash の待ちの形だけ）
差分テスト: なし（振る舞いを変えない周ではない——関門の体に書き先を足す）
生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を変えるので `python3 scripts/skill-metrics.py --check`）。図の書き出しは触らない。

## 設計の判断

- **原本は新しい `references/gate-reports.md`**。`SKILL.md` 手順 5 は 1 項で指し、委譲文 2 つは体の側の書き方だけを持つ（受け手が違うので写しが要る——SKILL.md 原則の「委譲文は prompts/」）。
  cruise は §4 の 2 で指し、親に誤って届いたときの扱いだけを持つ（親の仕事なので cruise の側）。`parallel.md` は待ちの項を合わせる。
  **複製の数**: 報告のファイルを述べる箇所は 7（原本・SKILL.md・verifier.md・review-handoff.md・cruise SKILL.md・parallel.md・公開ページ）。**分けない理由**: Issue が dev-loop と cruise の両方を求め、
  受け手（体・子・親・利用者）がそれぞれ別の文面を読む。細部（終わりの印・パスの形・起こし直しの条件）は原本だけに置き、ほかは印の名前と指し先だけにする。
- **終わりの印は `__DEV_LOOP_REPORT_DONE__`**（cruise の `__CRUISE_DONE__` と分ける——コマンドの出力ファイルと取り違えない）。体は `<パス>.tmp` に書いて印を足してから `mv` で置く（途中で切れた報告を終わったと読ませない）。
- **パスは起こすたびに新しい名前**（`<scratchpad>/gate-<周>-<関門>-<パス>-<UTC 時刻>.md`）——古いファイルの印で待ちが抜けないように。計画ファイルの再開点に書く（再開した側が読める）。
- **起こし直しの条件**: 印が無いことだけでは起こし直さない（動いているかもしれない——Issue の「起こし直そうとした」の形）。体の終わりが分かった（通知が届いた・親から知らされた）のに、通知にもファイルにも報告が無ければ、
  体に 1 度だけ `SendMessage` で書くよう頼み（宛先が分かるとき）、それでも無ければ新しいパスで起こし直す。通知もファイルも無いまま起こしてから 2 時間（推奨で決めた値）たったら欠票として起こし直す。
- **親に誤って届いた報告**: 親は本文を親の scratchpad の新しいファイルに写して終わりの印を足し、子にパスだけを `SendMessage` で知らせる（本文を貼らない——Issue の 2 の「転送するか、ファイルを指すか」はファイルを指す）。
  宛先の周を決める材料として、子は体の `description` に周の Issue 番号を入れる（この周で、サブエージェントの子が `Agent` に `name` を付けると拒まれた——下の「確かめたこと」）。

## verify の受入基準

### 不変条件

| # | 不変条件 |
| --- | --- |
| 1 | dev-loop 手順 5 が、関門の体（Verifier の 1・2 パス目・狭いパス・当て直し、`/code-review` の 1・2 パス目、fan-out・多レンズの体）に、起こす側がリポジトリの外の 1 つのパスを渡し、体が全文を終わりの印つきで書くことを必須にし、細部の原本（`references/gate-reports.md`）を指す |
| 2 | 委譲文（`prompts/verifier.md`・`prompts/review-handoff.md`）が、体に報告をそのパスに書かせ、書いてよいのはそのパス（と `.tmp`）だけと言い、既存の禁止（リポジトリと `~/.claude/` を書かない・副作用のある操作をしない）と食い違わない |
| 3 | 起こした側は通知の有無に依らず終わりの印で完了を判定し、印が無いだけでは起こし直さず、起こし直す条件（終わりが分かったのに報告が無い・上限の時間）と、通知とファイルのどちらかに報告があれば欠票でないことが原本に書いてある |
| 4 | cruise の §4 の 2 の委譲の項目にこの決まりがあり、親に誤って届いた報告の扱い（写してパスを知らせる・宛先の決め方・報告が無い通知の知らせ方）が決まり、`parallel.md` の体の報告の項が報告のファイルと食い違わない |
| 5 | 振る舞いの確かめ（Issue の 3）の結果が、観測窓つきで原本に書かれ、原因を断定せず、Claude Code への報告をしていないことが明記されている |
| 6 | 原本の待ちの形（bash）が実際に働く——印で抜ける・印が無ければ区切りの時間で抜ける・`.tmp` だけでは抜けない |
| 7 | 版（`dev-loop` 2.21.0 を marketplace.json・plugin.json・2 つの SKILL.md に）・委譲文の台帳（`line-effects.py check`）・`check-all.py` が緑・生成ブロックの鮮度 |
| 8 | 写しの一致——終わりの印の文字列・パスの形・指し先の名前が原本と写し（SKILL.md・2 つの委譲文・cruise SKILL.md・parallel.md・公開ページ）で同じ |

### これを破りうる経路

| 経路 | 守り方 |
| --- | --- |
| dev-loop を単独で回す周（最上位のセッションが前景・背景で関門を起こす） | SKILL.md 手順 5 の必須の項 → 原本 |
| cruise のサブエージェントの子が関門を起こす | 同上 ＋ cruise §4 の 2 の項 |
| cruise の子プロセス（`claude -p`）の子が関門を起こす | dev-loop 手順 5 に従う（child-cycle.md は手順 5 を指す） |
| `/code-review`（スキルとして同じ文脈で走る・分岐した実行として走る） | `prompts/review-handoff.md` の項 |
| fan-out のレビューの体・多レンズの Verifier | 手順 5 の項が名指す・各体に同じ委譲文 |
| 狭いパス・当て直し（absent-lines の推奨の直し・外部レビューの直し） | `prompts/verifier.md` の同じ「報告の形」に入る（狭いパスの差し込みは「報告の形」の項目を削らないと言う） |
| 委譲文を「参照＋差分」で渡す（差し込みの値を渡すだけ） | `{{報告のファイルの絶対パス}}` は穴なので値を渡すことが要る（原則の「すべての `{{ }}` に値を渡す」） |
| 体がリポジトリの中に書く・`~/.claude/` に書く | 委譲文がパスを 1 つに限る。既存の禁止は残る |
| 親に誤って届く | cruise §4 の 2 の親の扱い |
| 割り目・圧縮の後に再開した側 | パスを計画ファイルの再開点に書く（原本） |

### この環境では証明できないもの（未証明）

- **入れ子の通知が最上位の親に届く条件**（Issue の 3）——この周で観測できるのは自分の起こした体の分だけで、親の会話は見えない。原因の特定は Claude Code の側。
- **`/code-review` が報告のファイルの指示に従うか**は、この周で回す 2 回の観測だけ（スキルの版・分岐の有無で変わりうる）。

### BLOCKED

- なし（着手時の見立て）

## 未解決・確認待ち

- Claude Code への報告（Issue の 3 の後半）は、外への送信なので利用者が決める——PR コメントに材料を書く。

## 確かめたこと（この周の観測。実績）

- Claude Code 2.1.331。この周の子（cruise の親が起こしたサブエージェント）から、`Agent` に `name` を付けると「Teammates cannot spawn other teammates」で拒まれた（1 回）。
- `name` 無しで起こした体 3 体（`Explore`・haiku ×2、`dev-loop:dev-loop-verifier`・haiku ×1。2026-11-24T01:37〜01:39Z）は、どれも前景で返り、結果は
  「The subagent ended without delivering a report through SubagentHandback, so no report was delivered. Its unsent text is not shown.」だった（3/3）。
  3 体目に Bash で scratchpad のファイルに書かせたものは、終わりの印つきで読めた（陽性対照: 書かせた文字列が 3 行とも在る）。
- 3 体目へ `SendMessage` で報告を届けるよう頼んだ（01:40Z）——結果は下の関門の進捗に追記する。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/1503-gate-report-file`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1503`・
  起点 `089f1b4b`（`計画: #1465 の起票の件数…`）・base の参照 `origin/main`・base の SHA `089f1b4b2d38a343045439b90072c16ca5449dc1`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目の起点（指摘対応の起点）`3bae2687`。Verifier 1 パス目を起こした（報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/5855c3c5-3ba4-4b44-9ad6-67392a71e877/scratchpad/gate-1503-verifier-1-20261124T015915Z.md`）
- 交絡を潰した手順: 上の「確かめたこと」の観測は 1 環境・1 回ずつ（陽性対照はファイルの読み出し）

```dev-loop-gates
周の base: 089f1b4b2d38a343045439b90072c16ca5449dc1
```

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 実装役（`prompts/implementer.md`）の報告にも同じ形を入れるか | 入れない | Issue の範囲は関門の体。実装役は変更をコミットで残すので、報告が失われても成果物は worktree に残る |
| 待ちの形をスクリプトにするか | しない | 既存の `parallel.md` の待ちと同じ形の bash で足りる。歯止めの新設は範囲の外 |
| Claude Code に報告するか | この周ではしない | 外への送信は利用者が決める |

### 1 パス目の採否の表（Verifier 1 パス目 反証 1 件・`/code-review` 1 パス目 指摘 10 件）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | 計画ファイルの経路の表に `（必須）` があり `check-norm-markers.py` が 1 | 示せる（`python3 scripts/check-norm-markers.py` が `docs/plans/issue-1503.md:81` を名指して 1） | 7 | 直す（計画ファイルだけ） |
| C1 | 委譲文の新しい項「書いてよいのは、この 2 つのパスだけ」が、既存の例外（外の作業場所で変異を当てる）を禁じたと読め、「例外は 1 つだけ」も偽に読める | 示せる（`prompts/verifier.md` の新しい項と「例外は 1 つだけ」の項の文面。review-handoff.md・gate-reports.md も同じ文） | 2 | 直す |
| C2 | SKILL.md 手順 5 の既存の項「Verifier が報告を返さなかったら…再実行する」が手つかずで、新しい項の「印が無いだけでは起こし直さない」と逆の扱いを指す | 示せる（SKILL.md の 2 つの項の文面） | 3・8 | 直す |
| C3 | ヒアドキュメントの区切りが本文の行と一致すると、そこで閉じて残りの行がコマンドとして走り、切れた報告に印が付く | 示せる（scratchpad で、本文に `EOF` の行を含む報告を `<<'EOF'` で書かせると `injected.txt` が作られ、r.md は前半だけで印つき） | 2・3 | 直す |
| C4 | 宛先の周を決められない「報告の無い終わりの通知」を親が全部の子に知らせると、子が自分の体の終わりと読んで起こし直す | 示せる（cruise SKILL.md の親の扱いの段落が、宛先を決められないときを報告のある場合しか決めていない——文面） | 4 | 直す |
| C5 | 本文は「最後の行」で判定と言うのに、待ちの形は `grep -qx` でどの行でも抜ける | 示せる（scratchpad で、途中に印の行がある d.md に `grep -qx` は「届いた」、`tail -n 1` は「区切り」） | 3・6 | 直す |
| C6 | `SendMessage` で頼む救済は確かめていないのに処方として書き、計画の「追記する」も無い | 示せる（gate-reports.md の「確かめていないこと」に無い。計画に追記が無い） | 5 | 直す（確かめていないことに足す） |
| C7 | 誤って届いた通知に体の `description` が載る前提を確かめていない | 示せる（gate-reports.md の「確かめていないこと」に無い） | 5 | 直す（確かめていないことに足す） |
| C8 | 親が子を前景で呼んでいる間は、誤って届いた通知を親が処理できない限界が「守らないもの」に無い | 示せない（前景の呼び出し中に通知が親に届く形を走らせていない） | 無し | 残課題 |
| C9 | cruise SKILL.md・parallel.md の掛かる体の一覧に多レンズ・fan-out の体が無い（SKILL.md・原本にはある） | 示せる（4 つの一覧の文面） | 8 | 直す |
| C10 | 「2 つの呼び出しのどちらにも」は parallel.md から写した文で、ここの形は待ちの 1 行だけ | 示せる（文面） | 無し | 残課題 |
