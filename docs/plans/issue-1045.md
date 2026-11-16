# Issue #1045 — dev-loop・spec-loop: 学習の還元先に「仕事の切り方」の層を足す

cruise（親 Issue #1075）の子として回す周。**不在の周**（出所: `/dev-loop:cruise 1075 --absent`（2026-11-16））。AskUserQuestion は使わない。
spec-loop から来た Issue ではない。`作り直しの元:` の行も無い。`find-cycle.py 1045` は 5 本とも当たらず、新規の周。

台帳の確かめた線（出所: cruise の確かめた線（台帳 `issue-1075`）——利用者の確認（起動時・2026-11-16T00:05:09Z、配布を見せて確かめた）。親の委譲文で受け取った）:
直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。
`.claude/dev-loop.md`（main）の宣言: `マージの反映: ドキュメントとプラグインの配布`。`不在で止める範囲:` の行は無い。

直す線: `既定`（出所: cruise の確かめた線）。

この周は導入済みの dev-loop 1.111.0 の `SKILL.md`（1893 行）で回る。関門の記録は main の 2.3.0 の `check-gates.py` の形で書き、PR の前に `--absent` で当てる。
重い検査は `run-serial.py` 越しに回す——`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.111.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。関門にも渡す。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 8 に「切り分けの層」を足す（作業者向けの指示より先に検討する）
- `plugins/dev-loop/skills/cruise/references/grouping.md` — 切り分けの層の戻し先であることを書く
- `plugins/dev-loop/README.md` — 手順 8 の要約（複製）
- `plugins/spec-loop/scripts/findings-by-feature.py` — 新設。指摘の表から機能ごとの指摘件数を出す
- `plugins/spec-loop/references/spec-scope.md` — 偏りの数え方と、既定の線・scaffold の切り方への返し方
- `plugins/spec-loop/references/spec-exit.md` — 指摘の表の `指摘` の列に機能の印を書く決まり
- `plugins/spec-loop/skills/` — 版の行
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の行
- `scripts/test-findings-by-feature.py` — 新設。回帰テスト（変異テストを含む）
- `scripts/check-all.py` — 収録
- `.github/workflows/plugins.yml` — CI のステップ
- `CLAUDE.md` — スクリプトとテストの一覧
- `docs/plugins/dev-loop-design.md` — §8.4 棚卸し（受入基準 3）と、§8.2 の生成ブロック（`skill-metrics.py`）
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `docs/plans/issue-1045.md` — この計画

触らない:

- `plugins/spec-loop/scripts/rework-metrics.py`・`scaffold.py` — 集計を結ぶ・切り方を変えるのはこの周の受入基準の外（下の「決めたこと」）
- `plugins/spec-loop/scripts/check-findings-csv.py` — 指摘の表の形（列）は変えない
- dev-loop の `SKILL.md` の既存の規則をスクリプトへ移して本文から消すこと（棚卸しだけ。下の「決めたこと」）
- `plugins/dev-loop/skills/cruise/scripts/parent-issue.py`（親 Issue の書式の原本）——指すだけ

依存の追加・更新: なし。spec-loop の正本はこのリポジトリに無い（`仕様の振る舞い:` の申告は要らない——`check-spec-writeback.py` が 0 で確かめる）。

## 周の大きさ（同じことを述べている箇所の数）

- 手順 8 の還元先: `SKILL.md`（原本）・`plugins/dev-loop/README.md` の要約・設計ドキュメントの §7・手順 8 の要約（汎用の言い方で、還元先を列挙していない——直さない）。**直すのは 2 箇所**。
- 機能の印の書き方: `spec-exit.md` の指摘の表（原本）・`spec-scope.md`（起票元の `機能: <名前>` の形を指す）・`findings-by-feature.py` の docstring（写し。テストが突き合わせる）。**3 箇所**。
- 分けない理由: 3 つの提案は互いに指し合う（手順 8 が spec-loop の数え方と棚卸しを指す）ので、1 周で揃える。棚卸しはこの周では本文を消さない（手順 3 の「増やす変更と減らす変更を同時にやらない」）。

## 決めたこと（Issue が周に委ねた範囲）

- **提案 2 は指摘の表だけから数える。** `rework-metrics.py` の集計と結ぶ（作り直しの量を機能ごとに出す）のは、受入基準（「機能ごとの指摘件数を出力する」）の外で、
  確認の Issue と spec-loop の Issue を機能に結ぶ読み方が別に要る——PR コメントの残課題に書く。
- **提案 2 の「提案として返す」は、数を出すところまで。** 閾値（何件から見直しを勧めるか）は決めない——実案件の数が 1 つも無い（下の B7）。
  使い方（偏りを既定の線か `--bundle` の切り方への質問として利用者に返す）は `spec-scope.md` に書く。
- **提案 3 は棚卸しだけ。** 移せる項目を本文から消すのは別の周（増やす変更と減らす変更を同時にやらない）。

## 仕様の穴（不在の線で推奨により決めた）

- **G1 指摘を機能にどう結ぶか**——指摘の表（`spec-review/v<n>-findings.csv`）に機能の列が無い。
  - 選択肢: (a) **`指摘`・`根拠` の文面の印で結ぶ**——`機能: <名前>`（`spec-scope.md` の起票元の詳細と同じ形）と、機能の id（`F-001`。`F-001-C1` のケースの id も機能 `F-001` に数える）。
    印の無い行は「機能を決められない」として別に数える。/ (b) 指摘の表に `機能` の列を足す（壊れる変更。検査と既存の表の移行が要る）。/
    (c) `根拠` のファイルのパスから決める（仕様のファイルが機能ごとに分かれている保証が無い）。
  - 決めた値: **(a)**。推した理由: 表の形を変えないので、今の検査（`check-findings-csv.py`）と既にある表がそのまま通り、起票元の数え方と同じ単位・同じ書き方で数えられる。
    決められない行の数を出すので、印の書き漏れは数として見える。
  - 使った線と出所: 仕様の穴 = 推奨で決めて起票（cruise の確かめた線）。確認の Issue: （起票後に書く）

## デプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。子はマージしない。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 経路・確かめ方 |
| --- | --- | --- |
| B1 | dev-loop の `SKILL.md` 手順 8 の還元先の一覧に「切り分けの層」があり、**作業者向けの指示（`CLAUDE.md`・Skill・`prompts/`・「やってはいけない」・永続メモリ）より先に検討する**順序が明記され、戻し先 3 つ（親 Issue の書き方・`grouping.md` の基準・spec-loop の scaffold の切り方）を名指す | 経路: 手順 8 の本文（原本）・`README.md` の要約・`grouping.md` からの指し戻し。読む＋`check-skill-pointers.py`・`check-norm-markers.py` |
| B2 | `findings-by-feature.py` が、`check-findings-csv.py` の検査を通る指摘の表から、機能ごとの指摘件数（合計と振り分けの区分ごと）を出す。印 `機能: <名前>`・機能の id の両方、`指摘`・`根拠` の両方の列で結び、複数の表（版）を足し合わせる | `test-findings-by-feature.py`（陽性対照）。経路: 1 つの表・2 つの版の表・ケースの id（`F-001-C1`）・全角のコロン・1 行に 2 つの機能 |
| B3 | 機能を決められない行を、黙って落とさず別の行で数え、2 つ以上の機能に数えた行の数も出す | 同上 |
| B4 | 中身を数えていない形を 0 にしない（2）——検査に通らない表・無いファイル・引数の誤り | 同上 |
| B5 | 出力に指摘の文面（`指摘`・`根拠`・`結果` の自由文）を出さない——数と機能の名前だけ（`spec-exit.md` の「外へ出すのは区分ごとの件数だけ」） | 同上（文面の印が出力に無いこと） |
| B6 | `spec-scope.md` の歯止めの節が、偏りの数え方（スクリプト）と、既定の線・scaffold の `--bundle` の切り方への質問として返す使い方を指し、`spec-exit.md` の指摘の表が `指摘` に機能の印を書く決まりを持つ。docstring の印の形が `spec-exit.md` と一致する | 読む＋テスト（原本と本体の突き合わせ）・`check-skill-pointers.py` |
| B7 | 実案件の既存の指摘の表で確かめる（Issue の受入基準 2 の括弧） | **BLOCKED の見込み**——この PC に実案件の `v<n>-findings.csv` が 1 つも無い（`find /Users/hdknr -maxdepth 7 -name '*findings*.csv'` が 0 件）。次善: 検査を通る現行の形の試料（テスト） |
| B8 | 棚卸しの結果（移す／残すと理由）が docs に残っている | `docs/plugins/dev-loop-design.md` §8.4。読む＋`mkdocs build --strict`（CI） |
| B9 | リポジトリの外で単体で動く——標準ライブラリだけ、同じディレクトリの `check-findings-csv.py` を読み込む | テスト（`scripts/` を一時ディレクトリに写し `python3 -I`） |
| B10 | 版が 3 箇所で揃って上がり（dev-loop 2.3.0 → 2.4.0・spec-loop 0.94.0 → 0.95.0）、§8.2 の生成ブロックが新しく、テストが `check-all.py` と CI に収録され、`CLAUDE.md` に載る | `check-plugin-versions.py`・`skill-metrics.py --check`・`test-check-all.py`・`check-all.py` |

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

未証明: なし（B7 は BLOCKED の見込み——手段（実案件の表）があれば証明できる）。
生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）。図の書き出しは触らない。

## 未解決の判断・確認待ち

- G1 の確認の Issue（推奨で決めた値）。
- B7 の BLOCKED——`マージ前の判断 = 推奨で決めて起票` の線で推奨に回すか（確認の Issue は親が立てる）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1045-split-layer`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1045`・
  起点 `a1138bb`・base 参照 `origin/main`・base SHA `a1138bb94f74623273e2a7dcc40e8e55bc9d61c2`
- 割り目（手順 4・6）: **割らない（cruise の周）**——利用者に訊かない（不在の周・cruise の子）
- 交絡: 実験なし（試料は一時ディレクトリの合成）
- 1 パス目: Verifier（sonnet・`dev-loop:dev-loop-verifier`。テンプレート 185 行を読んだ）2089f70 **反証 2 件**／`/code-review`（high）2089f70 **指摘 10 件**。差し戻し: あり（直す 9 件——下の表）。
  1 パス目の指摘対応の起点: `2089f70`（1 パス目の関門に渡した HEAD）

```dev-loop-gates
周の base: a1138bb94f74623273e2a7dcc40e8e55bc9d61c2
```

## 既知の限界・決着済みの論点

### 1 パス目の採否の表（直す線 = 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1 `機能\s*[:：]` が「非機能: 性能が無い」に当たり偽の機能が立つ | 示せる（Verifier が合成表で実行） | B2 | 直す——印は開き括弧か `／` の直後だけ |
| V2 根拠 `requirements/F-001.md:3` のパスの中の id を F-001 に数える | 示せる（実行） | 無し——その機能のファイルを指す根拠で、F-001 に数えるのは誤りと言えない | 残課題 |
| CR1 括弧の外の素の「機能:」に当たり、行の残りが機能名として出る | 示せる（実測） | B5・B2 | 直す——括弧に入った・閉じた印だけ（V1 と同じ直し） |
| CR2 検査に通らない表の違反の行（セルの値を含む）を stderr に写す | 示せる（実測） | B5 | 直す——件数と検査のコマンドだけ出す |
| CR3 区切りの `/`・`、`・`,` で見出しどおりの名前が切れる | 示せる（実測） | B2 | 直す——区切りは `）` `)` `／` だけ |
| CR4 `F-001a` を F-001 に数える（V2 と同根） | 示せる（実測） | B2 | 直す——id の後ろの英数字を見る（パスの中の id は V2 のとおり残す） |
| CR5 B5 を判別するテストが無い | 示せる（変異が無い） | B5 | 直す（CR1・CR2 の試料と変異で） |
| CR6 機能名の `\|` を逃がさず表が崩れる | 示せる（実測） | B2 | 直す |
| CR7 同じ表を 2 度渡すと数が倍になり 0 | 示せる（実測） | B2・B4 | 直す——2 で止める |
| CR8 spec-scope の「上限で返すときに数える」が、上限の経路（spec-exit の「上限」）から呼ばれない | 示せる（spec-exit の上限の節に指し先が無い） | B6 | 直す——いつ数えるかを歯止めのときだけにした |
| CR9 SKILL 手順 8 の「下の 4 つ」が 3 つ・`prompts/` に送る項目が無い・「やってはいけない」を名指さない | 示せる（本文） | B1 | 直す |
| CR10 cruise の子の周（手順 8 は計画ファイルまで）での扱いを書いていない | 示せない（子は計画ファイルに書くので、項の求める 1 行と矛盾しない） | 無し | 残課題 |
| V テストの穴: id の前の lookbehind を外す変異・想定外例外を 0 にする変異が素通り | 前者は示せる | B2 | 前者は直す（試料 `XF-001`）。後者は残課題（例外の経路を作る試料が無い） |


- 機能の印は書く決まりを足すだけで、検査（`check-findings-csv.py`）は強制しない——前からの表は印を持たない。決められない行は数として出る。
- `機能: <名前>` の名前の終わりは、閉じ括弧・区切りの記号（`）` `)` `／` `/` `;` `；` `、` `,` `。`）か行末。名前の言い換えは別の機能に数える（`spec-scope.md` の「言い換えると数が割れる」と同じ）。
- 機能の id と名前は結ばない（同じ機能を id と名前で書けば 2 行に出る）——`requirements/features.csv` を読まない。

## 手順 8（経験の還元）

- この周の起票: 1 件（仕様の穴 G1 の確認の Issue）
