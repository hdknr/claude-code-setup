# #204 plugins/ のプロンプト監査

監査結果は #204 のコメントを正とする。この Issue の周は 2 本ある。

- **1 本目**（PR #212、マージ済み）: cmux / orca / workspace-setup の修正。記録は末尾の「1 本目の記録」。
- **2 本目**（この周）: 監査で人間の判断待ち（flag）にした dev-loop の 3 件を、2026-10-14 に人間が判断した結果どおりに適用する。
  - 補助 F1 → **(a)**: `~/.claude/` は「書き換えない（読むのは構わない）」に揃える
  - 補助 F2 → **監査案どおり**: `references/resume.md` の手順 1 を `find-cycle.py` を正とする形に置き換える
  - 後半 F14 → **案 A**: 任意ブロックの中から必須要件を外し、「並列化の指針 > 守ること」を指す

  補助 F3 は #210 に含めて起票済みなので、この周では扱わない。

## 1. 変更範囲

触る:

- `plugins/dev-loop/agents/dev-loop-verifier.md` — F1（`$HOME/.claude/` の行）
- `plugins/dev-loop/skills/dev-loop/references/resume.md` — F2（手順 1）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — F14（2 つの任意ブロック）・F2 で切れる指し先（426-428 行）・版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く）
- `docs/plans/issue-204.md` — この計画

触らない:

- `prompts/verifier.md`・`prompts/review-handoff.md`（F1 は (a) なので、こちらは既に正しい側）
- 「（任意）検証を多観点化する」の多数決（#207）、「検証スコープを絞って」（#210）、Haiku／Sonnet の体数（#208）
- 手順 3・4 の「プランニングプラグインへの委譲（任意）」の中にある`（必須）`——F14 が名指ししたのは fan-out の 2 ブロックだけ。PR コメントの残課題に書く
- `resume.md` の手順 2 以降と「既に worktree がある場合」の節（**例外**: その節の 211 行「見るのは上に置いた 2 本」は手順 1 の 2 本を指していて、置き換えで指し先を失うので直す——B3 に入れる）

## 2. 周の大きさ

同じことを述べている箇所の数:

- F1: 3 箇所（agent・`prompts/verifier.md`・`prompts/review-handoff.md`）。直すのは agent の 1 箇所だけで、残り 2 箇所に揃える。
- F2: 2 箇所（`resume.md` の手順 1 と `find-cycle.py` の docstring）。加えて `SKILL.md` から手順 1 の中の項を名指ししている指し先が 1 箇所ある。
- F14: 3 箇所（2 つの任意ブロックと「守ること」）。

**3 件をまとめる理由**: どれも同じ監査の flag で、人間が同じ問いの中で判断した。どれも「食い違う 2 つの記述の片方を、もう片方に揃える」修正で、互いに同じ行を触らない。3 件とも記述を**減らす**か**揃える**変更で、**増やす変更は混ぜない**。

## 3. 乗るデプロイ経路

main へのマージ → GitHub Pages（`docs/` の生成ブロックが変わる）。プラグインは利用者が `claude plugin update` で取得する。

## 4. 受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | Verifier に渡る文面が `~/.claude/` について同じことを言う（書き換えない・読むのは構わない） | agent:30 と agent:36、`prompts/verifier.md`:108 と :113、`prompts/review-handoff.md`:88 と :91 | agent:36 を直す。6 行を並べて読み、「読まない」と読める行が無いことを確かめる |
| B1 | `resume.md` の手順 1 が探索をやり直さない。経路は `find-cycle.py` の docstring を正とし、新規の周の判定（旧 153-159 行）を持たない | `resume.md` の手順 1・`SKILL.md`「途中から再開する周」 | 手順 1 を置き換える |
| B2 | 当たったものの扱いの規範は残る: 部分一致の確認・detached なら SHA で引く・`git -C` を当てにしない・2 本以上当たったら「周の在り処」と突き合わせる・worktree の無いブランチは `git show <ブランチ>:<パス>`・gitignore された計画ファイルは人間に渡す | 置き換えで落ちる | 旧本文の規範を 1 つずつ新本文と突き合わせる |
| B3 | `SKILL.md` から `resume.md` への指し先と、`resume.md` の中の指し先がすべて解決する | `SKILL.md`:426-428 が手順 1 の中の項を名指ししている。`resume.md`:211「見るのは上に置いた 2 本」 | 指し先を `find-cycle.py` の docstring に変える。`check-skill-pointers.py` を回す |
| C1 | 2 つの任意ブロック（手順 5「（任意）検証を多観点化する」・手順 6「（任意）レビューを fan-out する」）の中に必須要件の本文と`（必須）`が無く、「守ること」を指している | 2 ブロック | 書き換える |
| C2 | ブロックから外した要件が、指した先（「守ること」か手順 5）に全部ある: 受入基準をまるごと渡す／「経路を全部挙げる」担当を置く／書き込みツールを持たない `subagent_type`／信頼できない入力の扱い／実行できない場合は明記 | 「守ること」に「実行できない場合は明記」が無い | 外した要件を 1 つずつ指し先と突き合わせる。無いものは手順 5 を指す |
| D | 版が 3 箇所で揃う（1.37.1 → 1.37.2、patch: 記述の修正） | `marketplace.json`・`plugin.json`・`SKILL.md` | `check-plugin-versions.py` |
| E | 生成物が新しい（§8.2 の生成ブロック） | `SKILL.md` の行数・`（必須）`の数が変わる | `skill-metrics.py` で再生成し、`--check` が通る。図は触らないので該当なし |
| F | `check-all.py` が緑。push 後に PR 側の CI も緑 | — | 回す |

**組み合わせ**: 必須要件は「両方の関門に渡す」×「2 パス回す」の 4 回の受け渡し。

**証明できないもの（未証明）**: 「モデルが新しい `resume.md` を読んで、正しく再開する」という振る舞いは、この環境では回さない（`claude plugin eval` は worktree 隔離セッションから起動できない。CLAUDE.md）。既存の eval ケース（`resume-no-new-worktree`）は `find-cycle.py` を当てにしている。人間が別の端末で回すかを決める。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/204-audit-flags`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-204`、起点 `53d06c3`、base の参照 `origin/main`、base の SHA `53d06c35b1c94561dae32203f20adf57f03d43fa`
- 関門: 未着手
- 反証・差し戻し: なし
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| F1 を (a) と (b) のどちらにするか | (a) 読むのは構わない | 人間の判断（2026-10-14） |
| F2 を監査案どおりにするか | する | 人間の判断（同上） |
| F14 を案 A と案 B のどちらにするか | 案 A | 人間の判断（同上） |
| `test-tab-match.py` が落ちる | この周の失敗ではない（触らない） | base の `53d06c3` の main CI（run 38484185853）が同じステップ「orca・cmux のタブ一致規則のテスト（#202）」で failure。この周は orca／cmux も `scripts/test-tab-match.py` も触っていない |
| 手順 3・4 の委譲ブロック（任意）の中にある`（必須）` | この周では触らない | F14 が名指ししたのは fan-out の 2 ブロックだけ。残課題にする |

---

## 1 本目の記録（PR #212、マージ済み）

この PR が扱ったのは、**cmux / orca / workspace-setup スライスで判断が済んだ指摘だけ**である。
dev-loop の指摘は、個別に起票した Issue（#205〜#211）で扱う。

### 範囲

- `plugins/cmux/` — F1（バナーと README の「キャッシュが更新されていない」）・F4（description）・版
- `plugins/orca/` — F2（「動作は揃えてある」）・F4（description）・版
- `plugins/workspace-setup/` — F3（プライベートを強制。人間が判断済み）・F5（frontmatter）・版
- `.claude-plugin/marketplace.json` — 版だけ

触らなかったもの: `plugins/dev-loop/` 一切、cmux の振る舞いの指摘（FL1〜FL6。#196 / #197 / #202 ほか）

### 受入基準

- [x] cmux の `SKILL.md` と `README.md` に「キャッシュが更新されていない」という断定が無い
- [x] orca の `SKILL.md` と `README.md` が「動作は揃えてある」と主張していない
- [x] workspace-setup が、プライベートで作るかどうかを利用者に訊かない（強制だけが残っている）
- [x] cmux / orca の frontmatter description が各モードの動作と、いつ使うかを述べている。workspace-setup に description がある
- [x] 版が 3 箇所（workspace-setup は 2 箇所）で揃っている: cmux 1.1.5 / orca 1.0.1 / workspace-setup 1.0.2
- [x] `check-all.py` が緑（下の「検証」）

### 検証

コミット後に `python3 scripts/check-all.py` を回し、30/30 本 OK（失敗 0 / 飛ばし 0）。

**コミット前の check-all.py は緑だったが、それは根拠にならなかった。** PR 限定の 3 本（version-bump・description-sync・plan-scope）は `origin/main..HEAD` のコミットしか見ないので、未コミットの変更は素通しになる。コミットしてから回すと `check-description-sync.py` が cmux / orca で落ちた。frontmatter だけ直して JSON を直していなかったためである。そこで、片側だけの変更が正しい理由を、プラグイン名を前置した `Skip-description-sync` trailer で書いた。最初は trailer を最後の段落の外に置いており、それでは効かなかった。

PR 側の結果は `gh pr checks` で確認する。
