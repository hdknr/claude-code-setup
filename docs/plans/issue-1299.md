# Issue #1299 — spec-loop: scaffold の Red テストで実行ごとに変わる出力を型・同一性で比べる

**不在の周**（出所: `/dev-loop:cruise 1296 --absent`、2026-11-19）。利用者には訊かない。親（cruise #1296）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1296`）。利用者の確認（起動時）で確かめた）:
`直す線 = 既定`・`マージ = 関門を通ればマージ`（配布を確かめ済）・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。
台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.13.0（`SKILL.md` 1931 行を読んだ）。並行して #1301 の周を別の子が回している（どちらも spec-loop を触るので版の取り合いがある）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1296`））。
版の上げ方: `spec-loop` を **minor**（能力の追加——`spec-loop` は 0.x なので壊れる変更も minor）。着手時の main は 0.118.0（#1298 の merge）→ 0.119.0。
マージの直前に main が進んでいたら、親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせる。
割り目: 割らない（cruise の周）。

周の在り処: ブランチ `issue/1299-scaffold-any-ref-compare`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1299`・切った元の参照 `origin/main`（解決した SHA は下の `dev-loop-gates` の `周の base:`）。

Issue 本文（外部入力）から読んだ要件: 入出力のケースの `expected`（と #1298 の `setup`・`after` の呼び出しの `expected`）に、等しさの代わりの比べ方 `{"$any": "<型>"}`（型だけ）・
`{"$ref": "<名前>.<項目>"}`（`setup` の結果を名前で受けて同じ値）を書ける。`$ref` が無い名前・後ろの呼び出しを指すと生成が止まる。書かないケースの生成物は同じバイト。
`spec-ir.md` に「URN を返す」例を足し、例を生成に通す。本文に受入基準を緩める指示は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票` は台帳の線に無い。Issue が書き方の骨だけを示して残りを委ねている範囲）

- **`as`**: 結果を名前で束ねる印。`setup`・`after` の入口の呼び出しと、ケースの本体（`as` をケースに書く）に書ける。Issue の「`setup` の結果を名前で受けて」を、
  `after` の `$ref` が本体の結果を指せるよう（「作る → 読む」の定番）本体と `after` にも広げた。束ねるのは `expected` を持つ呼び出しだけ（失敗の形は項目を持たない）。
- **`$ref` が指せる範囲**: 呼ぶ順（`setup` → 本体 → `after`）で前の `as` だけ。後ろ・自分自身・書いていない名前は生成が止まる（受入基準 2）。
- **書ける場所**: `expected` の項目の値だけ。`input` と `seed` の値には書けない（前に返った値を入力に渡すのは Issue の範囲外）。トレースのケースの `expected`・`setup`・`after` にも書けない（トレースの Red テストのバイトを変えない）。
- **`$any`**: 型は項目の型と同じでなければ止める。`enum` は見ない。`nullable` の項目の `null` は型を見ない（既存の `check` と同じ）。
- **`$ref` の型**: 指す項目の型と書く項目の型が違えば止める。実行時は値の等しさに加えて、項目の型も見る（`True == 1` を通さない）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 検査（`check_dynamic`・`check_binding`・`check_values`・`check_call`・`check_stage`・`check_ir`）・Red テストの生成（`dynamic_methods`・`red_test`）・docstring
- `plugins/spec-loop/references/spec-ir.md` — 「実行ごとに変わる出力」の節・例・テストケースの表
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 書き起こしの 1 行
- `scripts/test-scaffold.py` — 試料・変異
- `docs/plugins/spec-loop.md` — 公開ページの 1 段落
- `CLAUDE.md` — scaffold.py の項に 1 文
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1299.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/spec-fingerprint.py`（指紋の式は変えない）
- `input`・`seed` の値への `$ref`（前に返った値を入力に渡す書き方。Issue の範囲外）
- トレースのケースの `expected`・`setup`・`after` の挙動
- 項目の型に配列・入れ子（#1300）、関数で表せないケース（#1301）
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）

依存の追加・更新: なし
仕様の振る舞い: 変えない

生成物: なし（このリポジトリの生成物は図の書き出しと `SKILL.md` の測定値だけで、どちらも触らない）。

**複製の数**: 「`$any`・`$ref`・`as` の書き方」を述べる箇所は 3（`spec-ir.md` が原本、`scaffold.py` の定数と docstring（`test-scaffold.py` が表と突き合わせる）、`scaffold/SKILL.md` と公開ページは指すだけ）。
分けない理由: 1 つの機能追加で、複製は表の 1 箇所に寄せて突き合わせの試験を足した。

## 受入基準

| 番号 | 基準 |
| --- | --- |
| A1 | `$any` の項目は型だけを、`$ref` の項目は指した値との同一性を Red テストが確かめる。違う型・違う値を返す実装で赤（陽性対照） |
| A2 | `$ref` が無い名前・後ろの呼び出しを指すと生成が止まる |
| A3 | `$any`・`$ref` を使わないケースの生成物は今までと同じバイト |
| A4 | `references/spec-ir.md` に「URN を返す」例を足し、例がテストで生成を通る |

経路（不変条件 × 破りうる入口）: 入力の入口は中間表現（`check_ir`）のケースの `expected`・`setup`・`after` の呼び出しの `expected` と `as` だけ（`input`・`seed`・トレースのケースは書けない）。
生成の入口は `scaffold.py` の書く生成・`--dry-run`・`--check`・`--red-check`・`--upto`（前の版の時点）・v2 以降の差分（`behavior`・`case_changed`）・`--bundle`・性能テスト（入出力のケースの入力だけを使う）。
どれも `red_test`・`check_ir`・`behavior` を通る。
未証明: 実際の実装の言語・フレームワークとの組み合わせ（生成物は Python の `unittest` だけ）。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `$ref` を `input` に書けるか（前に返った URN を入力に渡す） | 書けない | Issue は `expected` の比べ方だけを求める。入力に参照を入れると `input` の型・性能テストの入力の決まりが変わる |
| `$any` が `enum` を見るか | 見ない | 値を見ない書き方。`enum` を見たいなら `$any` でなく値を書く |
| `as` を本体に書けるか | 書ける（Issue は `setup` の結果と書いたが、`after` の `$ref` が本体を指す定番のため） | 計画の「仕様の穴」に書いた |
| 前提も後の状態も無い動的なケースは `reset_state()` を呼ぶか | 呼ばない | 呼ぶと実装に新しい口を求める。#1298 の「前提を書かないケースは呼ばない」と同じ |

## 採否の表（1 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| code-review: `as` で束ねた結果を写さず、実装が返した辞書を後の呼び出しが書き換えると `$ref` が書き換わった値と比べて通る | 示せる（F-009/F-010 の例で、読むたびに版を上げる実装が緑になった） | A1 | 直す（`dict(actual)` で写す・試料 DYN_ALIAS_IMPL・変異 2） |
| Verifier 1: 本体の自分自身への `$ref` を判別する試料が無い（変異 M1 が生き残る） | 示せる（M1 で「動的:」36 件が全部緑） | A2（試料の判別力） | 直す（試料・変異） |
| Verifier 2: 前提・後の状態だけの機能のバイトを #1299 の前と固定する試料が無い（M2・M3 が生き残る） | 示せる | A3（試料の判別力） | 直す（`stage_written` に動的な道具の不在を足した） |
| Verifier 3: `$ref` の null の扱いを判別する試料が無い（M4） | 示せる | A1（試料の判別力） | 直す（試料・変異） |
| Verifier 4: 動的なケースの `setup` の失敗を期待する呼び出しを判別する試料が無い（M5） | 示せる | A1（試料の判別力） | 直す（試料・変異） |
| code-review nit: 動的なケースだけで前提・後の状態が無い機能の Red テストが、定義の無い名前（`TRACE_TYPES` など）を参照する関数を持つ（実行はされない） | 示せる（生成物の文字列） | 無し | 残課題（記録だけ。実行に影響せず、利用者に見える誤りでない） |
| code-review nit: null を許す項目から null を許さない項目への `$ref`（指した値が null だと緑にできない） | 示せる（合成の IR） | 無し | 残課題（記録だけ。まれな書き方） |
| code-review nit: `number` で `1` と `1.0` を同じ値と見ることが文書に無い | 示せる（記述の欠け） | 無し | 残課題（記録だけ。文言） |

## 採否の表（2 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| Verifier 2 R1・code-review 2: 動的な値を書いた本体の項目の `nullable` を v2 で外すと、`case_changed` が回帰と読む（前の版で通る実装が v2 の Red テストで赤になる） | 示せる（合成の IR。v1 緑・v2 赤） | 無し（A1〜A4 のどれも破らない） | 残課題（記録だけ。動的な値を書いた項目の `nullable` だけを v2 で外す書き方はまず起きない。`handoff-issue.md` の「`nullable` だけは変化に数えない」はその形では偽） |
| Verifier 2 R2: 「書かないケースの生成物は同じバイト」は、動的なケースを 1 つでも書いた機能のファイルでは成り立たない（機能の単位） | 示せる（文言） | 無し | 残課題（記録だけ。`spec-ir.md` は「1 つも書いていない機能」と正しく書いてある） |
| code-review 2: `isinstance` の守り 2 つ（`$ref` が文字列・`as` が文字列）を判別する試料が無い | 示せる（変異で生き残る） | 無し | 残課題（記録だけ。試料の穴） |
| code-review 2 nit: 試料のコメントの件数（8 件は基本の 3 件を含む） | 示せる（文言） | 無し | 残課題（記録だけ） |
| code-review 2: 計画の再開点が古い・関門の記録が無い | 示せる | 無し | この記録で直した |
| code-review 2: main が 0.119.0 に進んだ（版の取り合い） | 示せる | 無し | 親がマージの直前に取り込み、0.120.0 に上げ直す（計画の版の上げ方のとおり） |

2 パス目で直した行: なし（上の表は全部残課題）。狭いパス: 該当なし。

## 周の記録

- 周の記録（再開点）: 1 パス目・2 パス目まで通した。2 パス目で直した行が無いので狭いパスは該当なし。残りは PR・CI（親が取り込み・上げ直し・マージ）。
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に宣言が無い）。
- 割り目: 割らない（cruise の周）。

```dev-loop-gates
周の base: 3fe44e069f9b1a59df2641d0daad1f5520dd2899
関門: Verifier 1 4e1844a5cc3c090d571102b14a53151873c7f464 反証=4
関門: /code-review 1 4e1844a5cc3c090d571102b14a53151873c7f464 指摘=4
関門: Verifier 2 f052935846dfaa12a0e6bb30c74ac380e2c2d11b 反証=2
関門: /code-review 2 f052935846dfaa12a0e6bb30c74ac380e2c2d11b 指摘=5
関門: 狭いパス 該当なし
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
マージの反映: ドキュメントとプラグインの配布
```

- この周の起票: 0 件（手順 8 の起票は、親が立てる確認の Issue を除いて無い）
