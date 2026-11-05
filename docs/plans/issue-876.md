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

- まとめ方を人が引数で選ぶ（推奨で決めた）——確認の Issue を立てる（番号は下）。

## 手順 8（起票数）

- この周の起票: 1 件（仕様の穴を推奨で決めた確認の Issue）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/876-scaffold-bundle-parent`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-876`・
  起点 `768fb9a7`・base（`origin/main` の merge-base）`768fb9a7c9d4d7b79741737952a8fdc6dfbafbd4`
- 割り目: 不在の周・cruise の子なので訊かずに続ける
- 交絡: 実験なし（テストの試料のみ）

## 既知の限界・決着済みの論点

- まとめ方の妥当さ（同じモジュール・同じ受入基準・同じデプロイ経路か）は機械で決めない——選ぶのは人（設計 1）。
- 撤去の順（呼ぶ側の変更の後に撤去する）は依存に出さない——`called_by` は今の版の機能にしか無い。
