# Issue #502 — prepare-worktree.sh の出力の「次にすること」が、cruise の子にも EnterWorktree を勧める

**不在の周である**——出所: `/dev-loop:cruise 474 --absent` の再開（2026-10-29）。この周は cruise の親から、worktree の絶対パスで作業する
サブエージェントとして委ねられた。**この周では `EnterWorktree` を呼んでいない**（`prepare-worktree.sh` の出力の「次にすること」は無視した——それがこの Issue）。

使った線（出所: cruise の確かめた線（台帳 `issue-474`）——利用者の確認（起動時・2026-10-27T09:07:27Z）＋利用者の確認（再開時・2026-10-28T07:24:46Z）。親の委譲文で受け取った）:

- `仕様の穴 = 推奨で決めて起票`
- 直す線: **既定**
- `周の途中の課題 = 台帳に足して直す`（台帳には親が足す。この周は台帳を書かず、見つけた課題を親への報告に挙げる）
- マージ: **しない**（この再開では親が配布を起こすマージをしない。PR・CI・関門・手順 8 の記録まで）

スキルの版: 読み込んだのはキャッシュの 1.63.6（`SKILL.md` 1842 行）。リポジトリの main も 1.63.6。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/prepare-worktree.sh` — 出力の「次にすること」の直後に cruise の子の例外を 1 行、冒頭の説明（やらないこと・守る）
- `scripts/test-worktree-scripts.py` — その出力の観測・検査・変異
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行（手順 4 の「`prepare-worktree.sh` の出力の『次にすること』も」の言い回しを、出力が自分で言うようになったことに合わせる）
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.63.6 → 1.63.7。出力の誤った案内を直す修正なので patch）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。変わる場合だけ）
- `docs/plans/issue-502.md` — この計画

触らない:

- `references/resume.md`（再開の周の `EnterWorktree` の記述。cruise の子の例外は `SKILL.md` 手順 4 と cruise §4 の 2 が既に指している）
- cruise `SKILL.md` の本文（§4 の 2 は既に「子も `EnterWorktree` を呼ばない」と書いている）
- スクリプトが cruise の子かどうかを自分で判定すること（シェルからは分からない。両方を出す）
- description（3 箇所。案内の 1 行は要約に現れない）

## 複製の数

「cruise の子は `EnterWorktree` を呼ばず worktree のパスを cwd にする」を述べる箇所: cruise `SKILL.md` §4 の 2、dev-loop `SKILL.md` 手順 4、
この周で足す `prepare-worktree.sh` の出力と冒頭の説明で計 4。**分けない理由**: 決まりの原本は cruise `SKILL.md` §4 の 2（手順 4 がそこを指す）。
スクリプトの出力は「原本を指す 1 行」に留め、条件を書き足さない。

## デプロイ経路

プラグインの版を上げるので、main へのマージが配布を起こす（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。
`docs/` も含む（計画ファイル・生成ブロック）ので Pages も再ビルドされる。**マージは親（cruise）の判断——この周はしない。**

## 受入基準（不変条件 × 経路）

不変条件:

- **I1 出力が cruise の子の例外を言う**——`prepare-worktree.sh` が作れた（rc=0）とき、「次にすること」の行の**直後の行**に、
  cruise から周を委ねられたサブエージェントは `EnterWorktree` を呼ばず、**作った worktree の絶対パス**を cwd にして作業する旨が出る
- **I2 通常の周の案内は変わらない**——「次にすること: EnterWorktree に path=<絶対パス> を渡して入る。」はそのまま出る
- **I3 出力のどこにも、例外を伴わない `EnterWorktree` の勧めが残らない**——スクリプトのすべての終了経路（0・1・2・3・5・6・7・`git worktree add` の失敗）を数える
- **I4 テストが守る**——`scripts/test-worktree-scripts.py` が I1 を観測し（「直後の行」まで見る——離れた行では偽）、例外の行を外す変異で赤になる。「守る」の行数と変異の数が 1 対 1
- **I5 記述が食い違わない**——スクリプト冒頭の説明（やらないこと・守る）・dev-loop `SKILL.md` 手順 4・cruise `SKILL.md` §4 の 2 が、出力と同じことを言う
- **I6 版と歯止め**——版 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本の 2 行）が 1.63.7 で揃い、`python3 scripts/check-all.py` が緑。PR 側の CI も緑

経路（不変条件を述べる／破りうる入口）:

| 入口 | I1 | I2 | I3 | I4 | I5 | I6 |
| --- | --- | --- | --- | --- | --- | --- |
| `prepare-worktree.sh` の rc=0 の出力（末尾の echo） | ○ | ○ | ○ | | | |
| `prepare-worktree.sh` の rc≠0 の出力（stderr・各 exit） | | | ○ | | | |
| `prepare-worktree.sh` 冒頭の説明 | | | | ○ | ○ | |
| `scripts/test-worktree-scripts.py`（観測・MUTATIONS・1 対 1 の数え） | ○ | ○ | | ○ | | |
| dev-loop `SKILL.md` 手順 4（528〜533 行付近） | | | | | ○ | ○ |
| cruise `SKILL.md` §4 の 2 | | | | | ○ | ○ |
| `references/resume.md`（`EnterWorktree` で入る・入り直す） | | | | | ○ | |
| 版 3 種類・`check-all.py`・PR の CI | | | | | | ○ |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目で 4 つの受け渡し（2 パス目が「該当なし」なら 2 つ）。

### 証明できるもの／できないもの

- I1〜I6 は、スクリプトを偽のリポジトリで走らせた出力・テスト・変異・`grep`・CI で証明できる。
- **受入基準ではないもの**: 出力を読んだサブエージェントが実際に `EnterWorktree` を呼ばなくなるか（モデルの振る舞い）。Eval を回さないと測れず、
  この周の受入基準に入れない（入れていない以上 BLOCKED でも未証明でもない）。PR コメントに名指しで残す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`SKILL.md` を触るので該当。`--check` で鮮度を見る。
- drawio の書き出し——該当なし（図を触らない）。

## 未解決の判断・確認待ち

- 無し（仕様の穴は無い。直し方は Issue の候補どおり）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/502-cruise-child-next-step`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-502`、
  起点コミット `94bcd42`、base の参照 `origin/main`（refs/remotes/origin/HEAD・取り直した）、base の SHA `94bcd423f3be1767106cd108e7649de033449940`
- 手順 4 の割り目: 不在のため訊かず続けた
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 1 パス目の指摘対応の起点の SHA: 未
- 反証と差し戻し: 未
- 交絡: 実験なし（スクリプトの出力の観測とテストのみ）

## 既知の限界・決着済みの論点

- スクリプトは自分が cruise の子から呼ばれたかを判定しない（できない）。通常の案内と例外を並べて出す——決着: 採った。理由: シェルから呼び出し元の種別は分からない。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |

## 手順 8（経験の還元）

- この周の起票: 0 件（起票の承認は不在のため訊いていない。仕様の穴の確認の Issue も、台帳に足す課題も無い）
