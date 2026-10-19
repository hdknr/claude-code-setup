# Issue #264: spec-loop 段 5d — scaffold の追加・変更・削除と dev-loop の v2 本文

親: #260（段 5d・最後の子）。前提: #262（5b）・#263（5c。どちらもマージ済み）。
`/dev-loop 260` で起動し、人間が「#264 の周を回す」を選んだ（2026-10-19）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 機能を追加・変更・削除に分ける／本文 v2（変化の印・`--upto <n>`）／変更・削除の本文／`--upto`（`--check`・`--dry-run`）／`--red-check`
- `plugins/spec-loop/references/handoff-issue.md` — 本文 v2 の形（印・変化の列・回帰・撤去・再現コマンド）
- `plugins/spec-loop/references/versions.md` — 「差分の周を始める前に」（乖離の確かめ）と、scaffold の読み方の行
- `plugins/spec-loop/references/tree.md` — 必要なら `issues.json` の中身の 1 行
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 手順 4（`--red-check`）・手順 6（変更・削除の重複の確かめ）・frontmatter
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 新しい版を始める前に乖離を確かめる（指し先 1 項）
- `plugins/spec-loop/README.md` — scaffold の節（引数）
- `plugins/spec-loop/.claude-plugin/plugin.json` — spec-loop 0.9.0・description
- `.claude-plugin/marketplace.json` — spec-loop 0.9.0・dev-loop 1.40.0・description（歯止めは 1 行目のパターンしか読まないので行を分けた）
- `plugins/spec-loop/skills/*/SKILL.md` — 版のバナー（5 本）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 1 で v1・v2 の両方の印を見る・版のバナー
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — v2 本文の読み方（変化の列・回帰・撤去・`--upto`）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 1.40.0
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `scripts/test-scaffold.py` — 試料・変異・印の写しの突き合わせ
- `CLAUDE.md` — scaffold.py の行（`--red-check`・`--upto`）
- `docs/plans/issue-264.md` — この計画

触らない:

- `merge-versions.py`・`diff-versions.py` — 関数を呼ぶだけ（重ね方・比べ方を写さない）
- 「決めていないこと」3 件（#260）——凍結した版の直し方・コード側の版との対応・ドリフトの意味
- 登録済みの v1 本文を書き換える仕組み——本文はスクリプトの外で登録される
- `check-frozen.py`（凍結は #262 で済み）

**周の大きさ（同じことを述べている箇所）**: 本文の形は `handoff-issue.md`（正）・`scaffold.py`（写し。テストが突き合わせる）・
`spec-gap.md`（写し。同上）・dev-loop `SKILL.md`（印だけ。同上）・scaffold `SKILL.md`（手順）・README の **約 6 箇所**。
**分けない**: 本文の形を変える側（spec-loop）と読む側（dev-loop）を別の周にすると、間の版で dev-loop が v2 本文を読めない。

## 決めたこと

1. **分け方は `diff-versions.py` の `compare` の機能の比較**（作業中の版 v<n> と v<n-1> の全体）。v1 だけなら全部が追加。
   **本文を作るのは追加・変更・削除の機能だけ**（変わっていない機能は Issue を作らない——前の版の Issue がある）。
2. **ケースの変化は「Red テストが実行する中身」で決める**——ケースの `input`・期待（`expected`／`error`）・
   機能の `operation.id`・出力の型・`impl_module` のどれかが違えば `変更`。題だけの違いは変更に数えない（テストの振る舞いは変わらない）。
   v<n> にだけあるケースは `追加`、両方にあって変わらないものは `回帰`、v<n-1> にだけあるものは `削除`。
3. **本文は全部 v2 の形にする**（追加も）。印は 3 行:
   `<!-- spec-loop-handoff: v2 -->`・`<!-- spec-loop-feature: F-xxx -->`・`<!-- spec-loop-change: <add|modify|remove>; base=<v<n-1>|none> -->`。
   **理由**: #262 の残課題 R2——再現コマンドに `--upto <n>` が無いと、v3 を足した後に本文の sha256 と合わなくなる。
   追加の本文にも同じ欠陥があるので、追加だけ v1 の形に残すことはしない（Issue の「今と同じ」は、新しい Issue を立てる点が同じと読む）。
4. **受入基準の表に `変化` の列**（追加・変更・回帰）。**消したケースは表の下に列挙**（Red テストから外れた）。
   **Red の状態**: 前の版の実装の上で、失敗するのは `追加`・`変更` のケースだけ、`回帰` は緑。
5. **削除の本文（撤去）**: 前の版の機能の API・ケースを示し、受入基準は「`scaffold/tests/` から消えた Red テストの実装を撤去し、
   ほかの Red テストが緑のまま」。節は 5 つとも持つ（dev-loop は同じ節を読む）。
6. **`--upto <n>`**: `--check`・`--dry-run` でだけ使える（書く生成で古い版の契約を置かない）。乖離の確かめ（`--check --upto <n-1>`）に使う。
7. **`--red-check`**: `scaffold/` が新しいことを確かめてから Red テストを走らせ、失敗した集合が「追加・変更のケース」と一致するかを見る。
   0 一致・1 不一致（名指し）・2 判定していない（走らせられない・**実装が無いので回帰を判定できない**）。
   実装が無くても期待が「全部失敗」（v1・追加だけ）なら判定できる（0）。
8. **重複の確かめ（SKILL 手順 6）**: 追加は機能の印で、変更・削除は**機能の印と変化の印の両方**で探す——前の版の Issue があっても止まらない。
9. **乖離の確かめ**は `versions.md` の 1 箇所に置き、req-loop（版を始める）と scaffold が指す。
10. 版: spec-loop 0.8.0 → **0.9.0**、dev-loop 1.39.1 → **1.40.0**（どちらも能力の追加）。

## verify の受入基準

### 不変条件

- **A**: v1 だけの正本では、全部の機能が `add; base=none` の本文になり、`scaffold/` は今と同じバイト（契約は変わらない）。
- **B**: v2 で変えた機能は `modify; base=v1`、足した機能は `add; base=v1`、消した機能は `remove; base=v1` の本文になり、変わっていない機能の本文は作らない。
- **C**: 変更の本文の受入基準の表で、ケースの `変化` が決めたこと 2 のとおり（追加・変更・回帰）で、消したケースが列挙される。題だけ変えたケースは回帰。
- **D**: 本文の再現コマンドが `merge-versions.py docs build/merged --upto <n>` で、**v3 を足した後でも**そのコマンドで作った中間表現の sha256 が本文と一致する（R2）。
- **E**: `--red-check` は前の版の実装の上で、追加・変更のケースだけ失敗・回帰は緑なら 0、ずれれば 1（名指し）、実装が無く回帰を判定できなければ 2。v1（全部追加）で実装が無ければ 0。
- **F**: `--upto` は書く生成では断る（2）。`--check --upto 1` は v1 から作った `scaffold/` を新しいと言い、v2 で作り直した後は古いと言う。
- **G**: 削除の本文は 5 つの節を持ち、消えた Red テストを名指しし、回帰を受入基準に持つ。
- **H**: `handoff-issue.md` の印・節と `scaffold.py` の定数、`spec-gap.md`・dev-loop `SKILL.md` の印が一致する（v1 と v2 の両方の印を dev-loop が持つ）。
- **I**: 決定論的（同じ入力から同じバイト）。関門・中間表現の誤りでは今までどおり何も作らない。
- **J**: 版が 3 種類（marketplace・plugin.json・SKILL.md）で揃い、description は JSON 2 箇所が同じ。`check-all.py` が全部緑。

### 経路（A〜J を破りうる入口）

- `scaffold.py` の 4 つの動き方（書く・`--check`・`--dry-run`・`--red-check`）× `--upto` の有無
- 版の構成: v1 だけ／v2 に追加・変更・削除／v2 が `spec_ir.json` を持たない（機能は変わらない）／v3 を足した後
- 本文を読む側: dev-loop の手順 1（印）・`spec-gap.md`（sha256 の確かめ・受入基準の写し方）・scaffold SKILL 手順 6（重複）
- Red テストを走らせる側: 実装なし・前の版の実装・正しい実装

### 証明できないもの（未証明）

- GitHub の検索（`gh issue list --search`）が HTML コメントの印の語句で当たるか——実際の Issue を作って検索しない（公開リポジトリに書く）。
  SKILL 手順 6 の確かめ方は現行（v1 の印での検索）と同じ形に乗っている。

### 生成物

- **該当あり**: dev-loop の `SKILL.md` を触るので、設計ドキュメント §8.2 の生成ブロック（`skill-metrics.py --check`）。
- `scaffold/`・Issue の本文はこのリポジトリには無い（試料の中でだけ作る）。図の書き出しは該当なし。

## 未解決の判断

- なし（着手時点）。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/264-scaffold-change-kinds`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-264`・
  起点 `e41079b`・base 参照 `origin/main` → `e41079b3a1f3f5b76e5813ec308e363420cf048f`
- 実装: `f9807ef` まで。`test-scaffold.py` は試料 108 件・変異 64 件で緑。`check-all.py` は 43 本中 1 本（`check-skill-pointers.py`：
  `spec-gap.md` の散文の指し先）が落ち、直して単体で緑——**全部を回し直すのはコミット後**
- 手順 4 の割り目: AskUserQuestion で提案し、**「ここで割る」が選ばれた**（2026-10-19）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 264`。**再開したら最初に `check-all.py` を回し直す**
- 再開後の `check-all.py`（300cad9）: 43 本中 2 本 FAIL——`check-plan-scope.py`（計画の 1 行に 2 パターン。行を分けて緑）・`check-description-sync.py`（P1-3）
- 関門 1 パス目: **Verifier（sonnet・`dev-loop:dev-loop-verifier`）反証 2 件**／**`/code-review`（high）指摘 10 件**。base `e41079b3a1f3f5b76e5813ec308e363420cf048f`。採否は下の表（直す 4・残課題 8）
- 反証・差し戻し: 1 パス目の反証で手順 4 へ差し戻し（P1-1〜P1-4）
- 1 パス目の指摘対応: `6b0cfb4`（P1-1〜P1-4。`test-scaffold.py` 試料 112 件・変異 67 件で緑。P1-4 の変異の差し替えと、
  P1-1・P1-2 の試料 4 件・変異 3 本を足した——型を広げる試料は最初 C1 の期待も変えていて判別せず、変異が生き残ったので型だけを広げる形に直した）
- 手順 6 の割り目（2 パス目の前）: AskUserQuestion で提案し、**「ここで割る」が選ばれた**（2026-10-19）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 264`
- 次（2 パス目）: **手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方が残っている**。base は同じ `e41079b3a1f3f5b76e5813ec308e363420cf048f`
- 交絡: 実験なし（`--red-check` の陽性対照は試料の中にある——正しい前の版の実装で 0・壊れた実装で 1・実装なしで 2）

## 既知の限界・決着済みの論点

### 1 パス目の指摘（Verifier 反証 2 件・`/code-review` 10 件。重複を畳んで 12 行）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| P1-1 | `behavior()` が出力の型を丸ごと入れるので、出力に項目を足す・`integer`→`number` に広げると、変わっていないケース（とくに失敗のケース）が `変更` になり、`--red-check` が 1 を返す（review） | 示せる（review が scratchpad で再現: F-001-C2 が `変更`、`--red-check` 1「追加・変更のケースなのに緑」） | C・E | **直す** |
| P1-2 | v2 がトップレベルの `impl_module` だけを変えると本文 0 件、`--red-check` は「実装が無い」で 2（Verifier・review） | 示せる（両方が再現。`classify` を読んで原因も確認） | B・E | **直す** |
| P1-3 | `check-description-sync.py` が赤（trailer なし）（Verifier・review） | 示せる（`check-all.py` でも FAIL） | J | **直す**（trailer。4 スキルの起動条件は変わらない） |
| P1-4 | 変異「前の版の中間表現を検査しない」が AttributeError で殺されている（意味では殺していない）（review） | 示せる（review が実行: exit 2・AttributeError） | I | **直す**（変異を「検査を飛ばして中間表現は返す」形に替える） |
| P1-5 | `versions.md` の「同じリポジトリなら `--red-check` が同じことを見る」は事実と違う（review） | 示せる（コードを読めば `--red-check` は最新版の追加・変更を赤と期待する） | 無し | 残課題 |
| P1-6 | SKILL 手順 6 の `add` は機能の印だけで探すので、消して再び足した機能が登録されない（review） | 示せない（`gh` の検索を当てていない。未証明の項と同じ限界） | 無し | 残課題 |
| P1-7 | 将来の版で `check_ir` が厳しくなると、凍結した v<n-1> の中間表現で生成が永久に止まる（review） | 示せない（将来の決まり） | 無し | 残課題 |
| P1-8 | 撤去の本文が原文のパスを `build/merged/` 抜きで書き、spec-gap の節が本文に無い sha256 を比べよと言う（review） | 示せる（本文を再現） | 無し（G の 5 節・名指し・回帰は満たす） | 残課題 |
| P1-9 | `case_changes()` を 3 箇所で計算し直している（review） | 示せない（不一致は起きていない） | 無し | 残課題 |
| P1-10 | 機能の比較は `==`、ケースの比較は `repr` なので `0`→`0.0` で食い違う（review） | 示せる（合成した入力で） | 無し（決めたこと 2 の外。v1 の本文の sha256 は書き換えない——「触らない」） | 残課題 |
| P1-11 | 同じ版の中で中間表現を直して作り直すと、手順 6 が直した本文を登録しない（Verifier の軽い所見） | 示せない（`gh` を当てていない） | 無し | 残課題 |
| P1-12 | `--red-check` が `scaffold/tests/__pycache__` を作る（Verifier の軽い所見） | 示せる | 無し（`--check` は新しいと言う） | 残課題 |

- 未証明（`gh` の検索が印で当たるか）は Verifier が「妥当」と判定した。
