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

（関門の後に書く）

## 周の記録

- 周の記録（再開点）: 実装・試料・変異を書いた。次は検査と関門。
- 割り目: 割らない（cruise の周）。
