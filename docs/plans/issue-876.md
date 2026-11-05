# Issue #876 — scaffold の Issue の粒度を選べるようにし、依存の連鎖を親子の構造で出す

- 出どころ: #870（#402 の改善の候補）。`Refs #870`（閉じない）
- **不在の周**（cruise #877 の子。`/dev-loop:cruise 877 --absent` の起動・2026-11-05）。
  台帳の確かめた線（出所: 利用者の確認（起動時・2026-11-05T08:50:03Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票、直す線 = 既定、マージ = 関門を通ればマージ、周の途中の課題 = 台帳に足して直す。
  周ごとに利用者に訊かない（割り目でも割らずに続ける）。マージは親がする（子は PR 側の CI まで）。
- 直す線: **既定**（出所: cruise #877 の台帳の確かめた線）

## 変更範囲

触る:
- `plugins/spec-loop/scripts/scaffold.py` — `--bundle`（まとめる選択肢）・まとめた本文・`issues.json` の `features`・`depends`。docstring と守らないもの
- `plugins/spec-loop/scripts/parent-checklist.py` — 登録した Issue から、cruise の親 Issue の書式のチェックリストを出す（新規）
- `plugins/spec-loop/scripts/rebuild-scope.py` — まとめた本文を機能ごとの部分に分けて読む
- `plugins/spec-loop/references/handoff-issue.md` — まとめた本文の形（原本）・`issues.json` の鍵・依存の連鎖
- `plugins/spec-loop/references/tree.md` — 生成物の置き場所の行（まとめた本文のファイル名）
- `plugins/spec-loop/README.md` — 使い方の行に `--bundle` と `parent-checklist.py`
- `plugins/spec-loop/skills/scaffold/SKILL.md` — まとめるかを利用者が選ぶ場面・登録の重複の探し方・親 Issue の一覧の出し方・版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — まとめた本文の読み方
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-scaffold.py` — `--bundle` の試料・既定が変わらないこと・写しの突き合わせ・変異
- `scripts/test-parent-checklist.py` — 親 Issue の一覧のスクリプトの回帰テスト（新規。変異を含む）
- `scripts/test-rebuild-scope.py` — まとめた本文の試料と変異
- `scripts/check-all.py` — 新しいテストの収録
- `.github/workflows/plugins.yml` — 新しいテストのステップ
- `CLAUDE.md` — プロジェクト構成に新しいスクリプトとテストの行
- `docs/plugins/spec-loop.md` — 公開ページの引き渡しの節
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない）
- `docs/plans/issue-876.md` — この計画

触らない:
- `--bundle` を付けない既定の振る舞い（1 機能 = Issue 1 件・本文のバイト）
- 中間表現（`spec_ir.json`）の形と機能の指紋——まとめ方は仕様ではないので中間表現に持たせない
- scaffold の SKILL.md の frontmatter と JSON の description（既定の「1 機能 = Issue 1 件で登録する」は変わらない）
- dev-loop の cruise の `parent-issue.py`（まとめた本文も 1 行目が handoff の印なので、そのまま spec-loop の子と読める）

## デプロイ経路

main へのマージ → GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。マージは cruise の親がする。

## 設計（この周で決めたこと）

1. **まとめる選択肢は引数 `--bundle F-001,F-002`（繰り返せる）**。書く生成と `--dry-run` でだけ使える。機械は「同じモジュール・同じ受入基準・同じデプロイ経路」を
   中間表現から決められない（デプロイ経路は中間表現に無く、`impl_module` は全体で 1 つ）ので、選ぶのは scaffold を回す人。機械が見るのは
   名指しした機能がこの版で本文を作る機能であること・変化（`add`／`modify`／`remove`）が揃うこと・2 件以上・重複しないこと・まとめた結果の依存に循環が無いこと。
   反すれば 2（引数の誤り）。**仕様の穴として推奨で決めた——確認の Issue を立てる**（下の「未解決」）。
2. **まとめた本文**: 1 行目は今の handoff の印（dev-loop・cruise の判別が変わらない）、2 行目に `<!-- spec-loop-bundle: F-001・F-002 -->`、
   機能のチェックリスト、続けて機能ごとの部分を `---` で区切って並べる。**部分は機能 1 件の本文から 1 行目（handoff の印）を外したもの**——
   印・6 つの節・指紋・sha256 がそのまま残るので、dev-loop は部分ごとに今の読み方と確かめ方を当てる。ファイルは `bundle-F-001-F-002.md`。
3. **依存の連鎖**: `called_by` から——呼ぶ機能（入口）の Issue は、呼ばれる機能（関数）の Issue に依存する。`issues.json` の項目に、依存があるときだけ
   `depends`（依存先の機能の id）を足す。まとめた項目は `feature` の代わりに `features` を持つ。
4. **親 Issue の書式で出す**: Issue の番号は登録の後にしか無いので、登録した後に `parent-checklist.py --index build/scaffold/issues/issues.json --issues <gh issue list の出力>`
   で、生成した本文と同じ本文の Issue を探し、`- [ ] #12 F-001 (depends: #11)` の形で出す（閉じた Issue は `[x]`）。題は機能の id だけにする
   （`parent-issue.py` は題の `#番号` と「依存」の語を拒むので、機能の題を写さない）。

## verify の受入基準

不変条件:

- **A1（既定）**: `--bundle` を付けない生成は、本文（`<機能>.md`）と課題一覧（案）・契約（`scaffold/`）が変わらない。`issues.json` は依存の無い中間表現では 1 バイトも変わらない
  （依存のある中間表現では各項目に `depends` が足されるだけ）。経路: 書く生成・`--dry-run`・`--check`・`--red-check`・v1／v2（追加・変更・撤去）。
- **A2（まとめる）**: `--bundle` で名指しした機能は 1 件の本文にまとまり、`issues.json` も 1 項目になる。部分は機能 1 件の本文から 1 行目を外したものとバイトで一致する
  （指紋・sha256 が残る）。名指ししない機能は機能 1 件の本文のまま。
- **A3（まとめ方の誤り）**: 本文を作らない機能・無い機能・変化の揃わない機能・1 件だけ・重複・依存の循環を作るまとめ方は 2 で、書く生成なら前の本文を消す。
  `--check`・`--red-check` と一緒には使えない（2）。
- **A4（依存の連鎖）**: `parent-checklist.py` の出力が cruise の `parent-issue.py show` にそのまま通り（拒まれない）、依存がそのとおり読まれる。
  経路: 依存なし・依存あり・まとめた項目への依存・閉じた Issue・未登録（1）・同じ本文が 2 件（1）・壊れた入力（2）。
- **A5（読む側）**: dev-loop の `spec-gap.md` がまとめた本文の読み方を持ち、`rebuild-scope.py` がまとめた本文の各部分の Q&A を引ける。
- **A6（写し）**: まとめた本文の印は `handoff-issue.md` と `scaffold.py` と dev-loop の `spec-gap.md` で同じ（`test-scaffold.py` が突き合わせる）。
- **A7（掛け算）**: A1〜A6 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目に渡す（2 パス目が該当なしなら 1 パス目の 2 つ）。

証明できないもの（未証明）:

- GitHub が登録した本文を変えずに返すか（`parent-checklist.py` は改行と前後の空白だけをならして比べる）——本物の GitHub には届かない。テストは同じ鍵の試料で当てる。

生成物の該当判定:

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`spec-gap.md` の行数が変わるので該当。`skill-metrics.py --check` が 0 であること
- `scaffold/` の契約——このリポジトリには正本が無い（試料は一時ディレクトリ）。該当なし
- 図の書き出し——触らない。該当なし

複製の数: まとめた本文の印は 3 箇所（`scaffold.py`・`handoff-issue.md`・`spec-gap.md`）。テストが突き合わせるので分けない。
「1 機能 = Issue 1 件」の記述は 5 箇所（README・公開ページ 2・handoff-issue.md・spec-gap.md・SKILL.md）——既定のままなので、まとめる選択肢を足す箇所だけ直す。

版の上げ方: main の先端の値から minor——spec-loop 0.64.0 → 0.65.0、dev-loop 1.95.0 → 1.96.0（能力の追加）。

## 未解決の判断・確認待ち

- **仕様の穴（不在の線で推奨により決めた）**: まとめる組の決め方を #876 が決めていなかった。選択肢 A: 人が引数 `--bundle` で選ぶ（推奨）／B: 中間表現に組の名前を書き自動でまとめる。
  A で決めた（理由: 組は仕様の外の判断で、中間表現に混ぜると仕様の決まりと機能の指紋を崩す）。線: 仕様の穴 = 推奨で決めて起票（cruise #877 の台帳）。確認の Issue: #883

## 手順 8（起票数）

- この周の起票: 1 件（#883 仕様の穴を推奨で決めた確認の Issue）

## 関門の進捗（再開点）

- PR: #882
- 周の在り処: ブランチ `issue/876-scaffold-bundle-parent`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-876`・
  起点 `768fb9a7`・base（`origin/main` の merge-base）`768fb9a7c9d4d7b79741737952a8fdc6dfbafbd4`
- 実装のコミット `0d080beb`。`check-all.py`（run-serial 越し）65/65 緑
- 1 パス目の関門に渡した時点の HEAD（0 行判定の起点）: `0d080beb`
- 1 パス目: Verifier 反証 1 件・`/code-review` 指摘 10 件（重なり 1）。直す 2 件・残課題 9 件（下の表）。指摘対応 `a2d3009f`（0 行ではない——2 パス目を回す）
- 2 パス目: Verifier（sonnet）反証 0 件（低優先の所見 2 件——P2-1 と同じもの・引数の解釈の誤りは従来どおり）・`/code-review`（high）指摘 7 件（下の表。直す 0 件）。差分の base は同じ `768fb9a7`。指摘対応の起点 `f4e949ee`
- 狭いパス: 該当なし（2 パス目で直した行が 0 件）
- 割り目（2 パス目の前）: 不在の周・cruise の子なので訊かずに続ける
- 割り目: 不在の周・cruise の子なので訊かずに続ける（手順 4 の割り目: このまま続ける）
- 交絡: 実験なし（テストの試料のみ）

## 既知の限界・決着済みの論点

- まとめ方の妥当さ（同じモジュール・同じ受入基準・同じデプロイ経路か）は機械で決めない——選ぶのは人（設計 1）。
- 撤去の順（呼ぶ側の変更の後に撤去する）は依存に出さない——`called_by` は今の版の機能にしか無い。

### 1 パス目の指摘と採否（直す線: 既定）

Verifier（sonnet・`dev-loop:dev-loop-verifier`）反証 1 件、`/code-review`（high）指摘 10 件。重なり 1 件（CRLF）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: `--bundle` の形の誤り（1 件・重複・形）は 2 で返るが、書く生成で前の本文を消さない | 示せる（関門が古い `F-001.md` を置いて再現。著者もテストに `plant_old_issues` を足して確認） | A3 | 直す |
| V1/CR2: まとめた本文が CRLF だと `rebuild-scope.py` の `parts()` が 1 部分にしか分けない | 示せる（両関門が実測。著者も CRLF の試料で再現） | A5 | 直す |
| CR3: scaffold SKILL.md 手順 6 の「まとめた本文は機能ごとに探し、当たれば登録しない」が、変更・撤去は前の版の Issue に当たっても止めない例外を上書きして読める | 示せない（文面の読み。実行するものではない） | 無し | 残課題 |
| CR4: 間の Issue が閉じていると、`parent-issue.py` が `[x]` への依存を外すので間接の依存が落ちる | 示せる（関門が `show` で再現） | 無し（A4 は出した行がそのまま読まれること——読まれている） | 残課題 |
| CR5: 本文の基準コミットの行が生成のたびに変わるので、登録の途中で作り直すと、登録済みの Issue が本文の一致で見つからず 1 になる | 示せない（筋書きの推論。実行していない） | 無し | 残課題 |
| CR6: まとめた本文の長さが GitHub の本文の上限（65,536 文字）を超えうる | 示せない | 無し | 残課題 |
| CR7: 1 つの組の中の重複（`F-001,F-001`）の試料が無い（変異の片側が生き残りうる） | 示せない（推論。変異を当てていない） | 無し | 残課題 |
| CR8: `dependencies()` の `groups[at][0].kind != REMOVE` は到達しない | 示せない | 無し | 残課題 |
| CR9: 4 桁の id を文字列で並べるので、`F-1000` が `F-999` より前になる | 示せない（実行していない） | 無し | 残課題 |
| CR10: spec-loop の description（JSON 2 箇所・scaffold の frontmatter）が `--bundle`・親 Issue の一覧に触れていない | 示せない（振る舞いではない） | 無し | 残課題 |
| CR（分類）: 未証明に「本文の上限」「GitHub の `in:body` 検索が部分の印に当たるか」も入れるべき | 示せない | 無し | 残課題 |

### 2 パス目の指摘と採否（直す線: 既定。指摘対応の起点 `f4e949ee`）

`/code-review`（high）指摘 7 件。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P2-1: `main` の `fail()` は `run` の外なので、本文の消去が失敗したとき（読み取り専用）「消せなかった——登録しないこと」の文言が出ず、想定外の例外の文言になる | 示せる（関門が読み取り専用で再現） | 無し（A3 の消去そのものは、消せる環境では消す。消せない環境の文言の違い） | 残課題 |
| P2-2: `--dry-run` で形の誤りの `--bundle` を当てる試料が無い（`writing` を無視する変異が生き残る） | 示せる（関門が変異で確認） | 無し（本体は正しい。試料の穴） | 残課題 |
| P2-3: `--red-check` と `--bundle` の組み合わせの試料が無い（変異が生き残る） | 示せる（同） | 無し（本体は正しい。試料の穴） | 残課題 |
| P2-4: まとめた本文の機能の一覧がタスクリスト（`- [ ]`）なので、Issue の画面で 1 クリックで本文が書き換わり、`parent-checklist.py` が本文の一致で見つけられなくなる | 示せる（関門が `[x]` に変えた本文で 1 を再現） | 無し（A4 の経路に「本文を書き換えた Issue」は入っていない） | 残課題 |
| P2-5: まとめた題の長さに上限（GitHub の 256 文字）を見ていない | 示せない（GitHub に当てていない） | 無し | 残課題 |
| P2-6: `parent-checklist.py` が項目ごとに全 Issue の本文をならし直す（計算量） | 示せない（失敗ではない） | 無し | 残課題 |
| P2-7: `parts()` の見分け（`splitlines`）と部分の頭の正規表現で、改行の扱いが揃っていない（`\r` だけの改行） | 示せない | 無し | 残課題 |

### 親の指示による直し（2026-11-05。cruise #877 の親から。#849 の R-1 と同じ扱い）

この周が持ち込んだ利用者に見える誤り 2 件を、マージの前にこの PR で直す（台帳に足さない）。3 件目（基準コミットの行と本文の一致）は記録だけ。

- P2-4 → 直す: まとめた本文の機能の一覧を素の箇条書きにした（タスクリストの行が無いことを `test-scaffold.py` が見る。変異「機能の一覧をタスクリストにする」）
- CR3 → 直す: scaffold SKILL.md 手順 6 の 1 で、まとめた本文にも変更・撤去の例外（同じ変化の印を比べる）を機能ごとに掛け直した
- 直しの差分: 起点 `64a19d84` → 終点 `98071e3c`。この差分だけに dev-loop-verifier（sonnet）を 1 回当てる（変異は Verifier が設計）
- 狭いパス（直しの差分 `64a19d84`→`98071e3c`。dev-loop-verifier・sonnet）: 反証 0 件・新たな後退なし。Verifier が設計した変異 6 本（`* [ ]`・`- [x]`・字下げ付き `  - [ ]`・`+ [X]`・一覧を消す・部分にタスクリストを混ぜる）は 6 本とも赤、素通り 0 本（無変異の写しで陽性対照の緑を確認）。SKILL.md 手順 6 の 1 の文面は散文で、機械で当てるテストは無い
- `check-all.py`（`98071e3c` の上で）65/65 緑
