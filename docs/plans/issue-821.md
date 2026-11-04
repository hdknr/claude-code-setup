# Issue #821 — cruise: 狭いパスの指摘も振り分け、マージを止めるのは「直す」の指摘だけにする

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かない）。
この周そのものは 2026-11-04 に利用者が「#821 を推奨案で採用して周を回して」と指示して始まった（親からの委譲文で受けた。訊かずに cruise の線で進める）。
台帳 `issue-793` の確かめた線（出所: cruise の確かめた線（台帳 `issue-793`）。利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳（`.claude/plans/cruise-issue-793.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（cruise のマージを止める条件を変える）。PR を出す直前の main の先端から minor を 1 つ上げる（着手時の main は 1.78.0）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件: #793 の不在の cruise で、`マージ = 関門を通ればマージ` があっても 15 周のうち 12 周が `利用者の判断待ち:` で止まった。
cruise の `SKILL.md` §4 の 4 が「狭いパスの指摘がある——振り分けに依らない」で止めるので、2 パス目で何かを直した周はほぼ必ず止まる。
案は、狭いパスの指摘も `found-lines.md` の「振り分け」に通し、マージを止めるのは「直す」に入るものだけにすること。
**仕様の決定は、Issue の利用者の決定のコメント（2026-11-04、hdknr。推奨案の 3 点）を正とする**:
(1) 採用——止めるのは「直す」に入るもの（受入基準を破る・利用者に見える誤り・その周が持ち込んだ後退）と、子が「マージ前に人が判断」と報告したものだけ。
(2) 振り分けるのは子で、狭いパスの指摘ごとに振り分けと理由を PR コメントに書く。親はマージの前にそのコメントを読み、「記録だけ」「捨てる」の理由が 3 つのどれかに当たりうるなら `利用者の判断待ち:` にする。迷ったら止める側。
(3) 後退は振り分けに依らず止める（狭いパスが「この周の直しで前は動いていたものが動かなくなった」と示した指摘——修正前の版で通り新しい版で落ちる、など）。素通りした変異・試料の穴・テストの無い分岐・文言の曖昧さだけなら止めない。
本文とコメントに、受入基準を緩める指示・コマンド実行の依頼は無い。

## 設計の判断

- **規範の原本は `absent-lines.md` の「`マージ = 関門を通ればマージ`」**——止まる条件の箇条書きの「狭いパスの指摘が 1 件でもある」を、
  cruise の台帳で回す周とそうでない周に分ける。**cruise の外の不在の周（`.claude/dev-loop.md` の `不在の線:` だけで回す周）は振り分けをしない**
  （`found-lines.md` の読む条件）ので、**今のとおり 1 件でもあれば止める**。決定 (1)〜(3) は cruise の周に掛ける。
- **振り分けと理由が PR コメントに無い狭いパスの指摘は止める側に倒す**——決定 (2) の「迷ったら止める側に倒す」から。親が読み直せない指摘を記録だけと読まない。
- **`merge-pr.py` は変えない**——止めるのは台帳の印（#631）で、印を付けるかを決めるのが親である。決定はその「付けるか」の条件だけを変える。
  **判断は行に閉じる・前例を根拠にしない（#631）は変えない**——親が行ごとに PR コメントを読み直す。記録だけの指摘だけの行は、利用者の判断を待たずに進む（判断が要らない）ので、前例の話にならない。
- **狭いパスの指摘の採否（直すか）は今のとおり人間が決める**——周の中では直さない（`SKILL.md` 手順 6）。変わるのはマージを止めるかだけで、記録だけの指摘は PR コメントに残ったままマージされる。
- **dev-loop の `SKILL.md` 本文は変えない**（版の 2 行だけ）——手順 6 の狭いパスの規定（直さない・人間が採否）は変わらず、マージの判断は `absent-lines.md` を指している。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「`マージ = 関門を通ればマージ`」の止まる条件（原本）
- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — 「狭いパスの指摘」（PR コメントに 1 件ずつ振り分けと理由・マージの判断）と「変えないもの」
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 4 の止める PR と親の読み直し・§4 の 2 の委譲文の項目・版
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 子プロセスの委譲文の 9（振り分けと理由を PR コメントに）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-cruise.md` — 公開ページの振り分けの段落の「マージは人の判断を待ちます」
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-821.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py`・`ledger.py`・`check-unattended-env.py`——印の読み方は変えない（`check-unattended-env.py` の「狭いパスの指摘があるのに印の無い PR は『進む』と出る」は、記録だけの指摘の PR については今後は意図どおりの値になる。文言は事実のまま）
- 線の項目（`ledger.py` の `LINES`）——狭いパスの扱いの項目は足さない
- dev-loop の `SKILL.md` 手順 6 の狭いパスの規定（直さない・採否は人間）
- spec-loop の狭いパス（`spec-review`）

### 同じことを述べている箇所の数

「狭いパスの指摘がある PR は cruise でマージを止める」を述べる箇所: `absent-lines.md`（原本）・`found-lines.md`（狭いパスの指摘・変えないもの の 2 か所）・
cruise `SKILL.md` §4 の 4・公開ページ——**5 か所**。加えて「子が振り分けを PR コメントに書く」を渡す委譲文: cruise `SKILL.md` §4 の 2・`prompts/child-cycle.md` の 2 か所。
分けない理由: 原本は `absent-lines.md` で、`found-lines.md` と cruise `SKILL.md` は読む側の場面（子の振り分け・親のマージ）に要る分だけを持ち、原本を指す。公開ページは利用者向けの説明。

## デプロイ経路

main へのマージで GitHub Pages の再ビルド（`docs/plugins/dev-loop-cruise.md`）とプラグインの配布（`dev-loop` の版）。マージは親がする。

## 受入基準

### 不変条件

- **I1**（Issue の受入基準 1）: cruise `SKILL.md` §4 の 4 と `absent-lines.md` が、cruise の周では狭いパスの指摘のうち
  「直す」に入るもの（3 つ）・後退を示すもの（振り分けに依らない）・子が「マージ前に人が判断」と報告したものだけでマージを止めると書いている。
  「記録だけ」「捨てる」だけなら止めない。決定 (1)〜(3) と食い違わない。
- **I2**（決定 (2)）: 子が狭いパスの指摘ごとに振り分けと理由を PR コメントに書くことが、子に届く経路（cruise `SKILL.md` §4 の 2 の委譲文の項目・
  `prompts/child-cycle.md`・`found-lines.md` の「狭いパスの指摘」）のすべてにある。親がマージの前にそれを読み直し、理由が 3 つに当たりうるなら・迷ったら止めることが §4 の 4 にある。
- **I3**（Issue の受入基準 2）: `merge-pr.py` の判断待ちの止め方（#631）と食い違わない——印・行に閉じた判断・前例を根拠にしない・`merge-pr.py` の 12 の記述が残り、
  新しい文言が「印を付けずに進む」のは振り分けで止めない指摘だけの行に限る。
- **I4**（Issue の受入基準 3）: 「記録だけ」の指摘だけが残った cruise の周は、`マージ = 関門を通ればマージ` の下でマージまで進む——規範の文面と、
  `merge-pr.py` が印の無い行の PR を止めないこと（既存の試料）の両方。
- **I5**: 「狭いパスの指摘が 1 件でもあれば、振り分けに依らず止める」と読める記述が、cruise の周について残っていない（`plugins/`・`docs/plugins/` の全部。計画ファイルは除く）。
  cruise の外の不在の周では今のとおり止める。
- **I6**: 版が 3 種類で揃い、`check-all.py` が緑、PR 側の CI が緑。

### 経路（I1〜I5 を破りうる入口）

| 入口 | 何が読むか | 守り方 |
| --- | --- | --- |
| cruise の親（サブエージェントで回す周） | cruise `SKILL.md` §4 の 2・4 | §4 の 4 の条件と読み直し、§4 の 2 の委譲文の項目 |
| cruise の親（`claude -p` の子で回す周） | `prompts/child-cycle.md` の 9 | 同じ項目を足す |
| 周を回す子（dev-loop） | `found-lines.md`（cruise の周で読む）・`absent-lines.md`（台帳に線がある周で読む） | 「狭いパスの指摘」と「マージ」の節 |
| `merge-pr.py` | 台帳の印だけ | 変えない（I3）。印を付けるかは親 |
| `check-unattended-env.py` の到達の見込み | 印だけ | 変えない |
| cruise の外の不在の周 | `absent-lines.md` | 1 件でも止めるを残す |
| 公開ページ | 利用者 | 段落を直す |

### 証明の手段

- 文面: 該当箇所を読み、`grep -rn "狭いパス" plugins docs/plugins` で残りを全部見る（I1・I2・I5）。
- I4 の機械側: `scripts/test-merge-pr.py` の既存の試料（印の無い行の PR はマージに進む・印のある行は 12）を走らせる。
- I6: `check-all.py`（run-serial 越し）と `gh pr checks`。

### 未証明

- **実際の cruise の親が、PR コメントの振り分けを読み直して正しく止める／進めるか**——LLM の振る舞いで、この環境では回せる cruise が無い（次の不在の cruise で観測する）。人間のレビューに回す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`。dev-loop の `SKILL.md` は版の行だけ変える）——`skill-metrics.py --check` で鮮度を見る。
- 図の書き出し: 触らない（drawio を変えない）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/821-narrow-pass-triage`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-821`・
  起点 `c16e3a43`・base `origin/main`（`refs/remotes/origin/HEAD`）= `c16e3a432b13eaca62516d0259e7c8266bd3a1c5`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 交絡: 実験なし

## 既知の限界・決着済みの論点

- `merge-pr.py` は PR コメントを読まない——親が読み直して印を付ける（#631 の形のまま。決定 (2) が親に読ませる）。
- cruise の外の不在の周は振り分けをしないので、狭いパスの指摘が 1 件でもあれば止めるのまま（決定は cruise の周の話）。
