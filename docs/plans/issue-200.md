# Issue #200 — orca: ドキュメントの記述を事実に合わせる

## 1. 変更範囲

触る:

- `plugins/orca/skills/orca/SKILL.md` — CR2-1（`-n` の付き先）・V4/M2（`tab list` の範囲）・版のバナー
- `plugins/orca/README.md` — CR2-1・CR2-7（前提と「スキルが確かめること」）
- `plugins/orca/.claude-plugin/plugin.json` — version 1.0.4 → 1.0.5（patch: 記述の修正）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/index.md` — CR2-1・CR7（素のスキルの節の末尾）・CR9/CR2-10（版のバナーの段落）
- `docs/plans/issue-200.md` — この計画ファイル

触らない:

- スキルの動作（コマンド・引数・前提の確認のコード）——Issue が「どれも動作は変えない」と決めている
- `plugins/cmux/` ・ `plugins/dev-loop/`（バナーの段落は docs 側だけを直す）
- 他の worktree の周（#196 / #197 / #199 も `plugins/orca/` を触っている可能性がある。版はマージ時に衝突しうる）

**複製の数**: CR2-1 の「付き先」は 3 箇所（SKILL.md・README・docs）。CR2-7 は README の 1 箇所
（docs は README を指すだけ）。V4/M2 は SKILL.md の 1 箇所。CR7 は docs の 1 箇所。CR9/CR2-10 は docs の 1 段落。
**分けない理由**: どれも同じ Issue の「文言を事実に合わせる」で、3 箇所の付き先を片方だけ直すと食い違いが残る。

## 2. デプロイ経路

- `docs/` は main へのマージで GitHub Pages に自動デプロイされる（**反映経路あり**）。
- `plugins/orca/` は版を上げて配布（利用者側は `plugin update`）。破壊的・不可逆な操作は無い。

## 3. 受入基準

**事実の出所**（この周で確かめたもの）:

- F-a: Orca CLI（アプリ 1.4.224）の `out/cli/selectors.js` の `resolveCurrentWorktreeSelector` は、
  `worktree.list` のうち **cwd を含む最も深い（パスが最長の）** worktree を選ぶ。無ければ `selector_not_found`。
- F-b: 同 `getBrowserWorktreeSelector` は、`--worktree` を省くとローカルでは cwd から解決した worktree で絞り、
  **解決に失敗したら絞らない**（`--worktree all` も絞らない）。`tab list` はこれを使う（`handlers/browser-tab.js`）。
- F-c: この環境の Orca 管理の worktree は 3 件ですべて `isMainWorktree: true`（リンク worktree が無い）。
  リンク worktree からの `-n` は**この周でも測れない**。
- F-d: 前提の確認のコードは `orca status`（`runtime.reachable`）と `orca worktree current`（`ok`）の 2 つだけ。
- F-e: バナーが入った版——dev-loop 1.7.1・cmux 1.1.2（どちらも `ff8920d` / #67）・orca 1.0.0（`5114914`、最初から）。
- F-f: `#194` の記録では V4（「既定の範囲が現在の worktree」）と M2（「全 worktree のタブを返す」）が食い違っている。
  この周の `tab list` は 0 件で、範囲を実測できない。

**I1（CR2-1）** 3 箇所とも、付き先を「cwd を含む Orca 管理の worktree（いちばん内側）」と書き、
`.claude/worktrees/` 配下の例は「メインのチェックアウトが Orca 管理ならそこに付く（この環境の 1 件で確認）」に留め、
**リンク worktree の配下からは測っていない**ことを書く。3 箇所が互いに食い違わない。

**I2（CR2-7）** README の前提が、スキルが確かめるもの（ランタイムに届く・cwd が Orca 管理の worktree の中）と、
確かめないもの（Orca の端末の中で起動しているか）を分けて書く。「スキルが確かめて止まる」が確かめないものに掛からない。

**I3（V4/M2）** SKILL.md の共通手順が `tab list` の範囲を書く: CLI の実装上の既定（F-b）と出所、
#194 の観測との食い違いを解いていないこと、別の worktree のタブを前面に出したときの見え方は測っていないこと。

**I4（CR7）** docs の素のスキルの節の末尾が、同じ節の列挙（`cmux`・`orca`・`dev-loop`）と一致する。

**I5（CR9/CR2-10）** docs の版のバナーの段落から「キャッシュが更新されていません」の断定を外し（#120）、
「1.7.1 で入れた」を dev-loop の話に限定して cmux / orca の版も事実どおり書く（F-e）。

**I6** `check-all.py` が緑。版が 3 種類（marketplace / plugin.json / SKILL.md）で揃う。

**I7（交点）** I1〜I5 の文言の事実は、2 つの関門 × 2 パスに渡す（事実の真偽まで確かめさせる）。

### 証明の手段

- I1〜I5: 一次ソース（CLI の実装・git 履歴・スキルのコード）と差分の突き合わせ。
- I6: `python3 scripts/check-all.py`。
- **未証明**: リンク worktree での `-n` の付き先、`tab list` の実際の範囲（サーバ側が `worktree` を尊重するか）、
  別 worktree のタブの見え方——**どれも「測っていない」と書く主張に落としてあるので受入基準ではない**。

### 生成物

**生成物なし**——図（`diagrams/`）も `skill-metrics.py` の対象（dev-loop の `SKILL.md`）も触らない。

## 4. 未解決

- なし

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/200-orca-doc-facts`・worktree `.claude/worktrees/issue-200`・
  起点 `8df3a56`・base 参照 `origin/main` → `8df3a56ad5384771869eb1799d7f87a0b9a603b8`
- 実験: なし（一次ソースの読解と git 履歴のみ）
- 実装: 済（コミット済み）。関門 1 パス目: **済**（2026-10-13。Verifier は `dev-loop:dev-loop-verifier`・sonnet、
  `/code-review` は high。どちらも base `8df3a56` を渡した）。
  **Verifier: 事実の反証 0 件・指摘 2 件。`/code-review`: 指摘 7 件**（採否は §6 の表。直す 3 件・残課題 4 件）
- 1 パス目の指摘対応: 済（V1-1/CR1-1・CR1-2・V1-2/CR1-3）。**残り: 手順 5 の当て直し（Verifier 2 パス目）と
  `/code-review` 2 パス目の両方**（base は同じ `8df3a56`。2 パス目にも受入基準と §6 をまるごと渡す）
- 割り目 2（2 パス目の前）: 提案した → **人間が「ここで割る」を選択**（2026-10-13）。
  再開は `.claude/worktrees/issue-200` の中で `/clear` → `/dev-loop 200`（手順 5 の当て直しと手順 6 の 2 パス目から）
- `check-all.py`: 32/32 緑（1 パス目の起動時点・ローカル）
- 割り目 1（手順 4 の完了時）: 提案した → **人間が「ここで割る」を選択**（2026-10-13）。
  再開は `.claude/worktrees/issue-200` の中で `/clear` → `/dev-loop 200`（手順 5 から）

## 6. 既知の限界・決着済みの論点

- 動作は変えない（Issue の決定）。`tab list` に `--worktree` を明示する案は採らない。

### 1 パス目の指摘と採否

| # | 関門 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- | --- |
| V1-1 | Verifier | README の前提の箇条書きの途中に「スキルが確かめるのは…」の段落が挟まり、`gh` と `EnterWorktree` の 2 項目が別リストに見える | 示せる——`plugins/orca/README.md` の「前提」節（この周の差分が段落を箇条書きの間に入れた） | I2（前提の書き分けが読み違えられる） | 直す |
| V1-2 | Verifier | F-b にはリモート接続時（`client.isRemote`）に絞らない分岐もあり、SKILL.md はローカルを暗黙に仮定 | 示せる（CR1-3 と同じ——`getBrowserWorktreeSelector` の分岐。両関門が独立に同じ行を引いた） | I3（F-b の「ローカルでは」が文面から落ちている） | 直す（CR1-3 と統合） |
| CR1-1 | `/code-review` | V1-1 と同じ | 同上 | I2 | 直す（V1-1） |
| CR1-2 | `/code-review` | SKILL.md だけ「（実装どおりならそのリンク worktree に付く）」があり、README・docs に無い | 示せる——3 箇所の文面 | I1（3 箇所が食い違わない） | 直す（SKILL.md から外す。測っていない予想なので、足すより外す） |
| CR1-3 | `/code-review` | `tab list` の範囲の注記がリモートの分岐と `handlers/browser-tab.js` を落としている | 示せる——`selectors.js` の `isRemote` 分岐 | I3（F-b と出所） | 直す |
| CR1-4 | `/code-review` | 「前提の確認を通っていれば前者」は、確認と `tab list` が同じ cwd・同じ worktree 一覧であることを仮定 | 示せない（cwd が変わる経路——`EnterWorktree` で `.claude/worktrees/` へ——でもメインのチェックアウトの配下に留まり、この環境では解決先が変わらない。登録の変化は起こせていない） | 無し | 残課題 |
| CR1-5 | `/code-review` | 公開ページの「この環境の 1 件」は読者に誰の環境か分からない | 示せる（文面） | 無し（I1 がこの文言を指定している） | 残課題 |
| CR1-6 | `/code-review` | docs の指し先の文が、スキルが確かめる worktree の条件を前提の列挙から落としている | 示せる（文面） | 無し（I2 は README の前提の話。docs の文はこの周で触っていない） | 残課題 |
| CR1-7 | `/code-review` | 付き先の段落を 3 箇所に全文で書いており、CLAUDE.md の「〇〇を正とする」に反する | 示せる（3 箇所の文面） | 無し（§1 で「分けない理由」として決めた範囲。寄せるのは別の周の判断） | 残課題 |

- Verifier 1 パス目: **事実の反証 0 件**、構成の指摘 1 件（V1-1）・範囲の限定 1 件（V1-2）。F-a〜F-e・I4〜I6 を一次ソースで一致と報告。
  起動した agent は `dev-loop:dev-loop-verifier`（ツール: Read / Bash のみと報告。定義の許可リストと一致）。
