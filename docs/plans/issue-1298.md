# Issue #1298 — spec-loop: scaffold の入出力のケースに setup・after を書けるようにする

**不在の周**（`/dev-loop:cruise 1296 --absent` の起動・2026-11-19）。利用者には訊かない。親（cruise #1296）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1296`）。利用者の確認（起動時）で確かめた）:
`直す線 = 既定`・`マージ = 関門を通ればマージ`（配布を確かめ済）・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。
台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.13.0（`SKILL.md` 1931 行を読んだ）。並行して #1297 の周を別の子が回している。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1296`））。
版の上げ方: `spec-loop` を **minor**（能力の追加——`spec-loop` は 0.x なので壊れる変更も minor）。着手時の main は 0.116.0 → 0.117.0。
マージの直前に main が進んでいたら、親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせる。
割り目: 割らない（cruise の周）。

周の在り処: ブランチ `issue/1298-scaffold-setup-after`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1298`・切った元の参照 `origin/main`（解決した SHA は下の `dev-loop-gates` の `周の base:`）。

Issue 本文（外部入力）から読んだ要件: 入出力のケースに `setup`・`after` を許す（トレースのケースと同じ形）。Red テストは `reset_state()` → `setup` → 本体 → `after`。
入口の無い前提を作る口（`seed`）を決める。書かないケースの生成物は同じバイト。機能の指紋の式は変えるなら dev-loop の写しと揃える。本文に受入基準を緩める指示は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票` は台帳の線に無い。Issue が口の名前と形を「決める」と委ねている範囲）

- **seed の形**: `setup`・`after` の配列の要素に `{"seed": "<名前>", "values": {"<項目>": <値>}}` を書く。実装は `seed(<名前>, /, **値)`（名前だけ位置引数）。
  Issue の `seed(<名前>, **values)` の形に従い、`values` の項目名が名前の引数と重ならないよう位置専用にした。値は文字列・数・真偽・`null`（入れ子にしない）。
- **口の重なり**: 入口の名前 `seed` と入力の項目 `seed` は、`seed` を書いたケースがあるときだけ断る（`reset_state` は `setup`・`after` を書いたケースがあるとき入口の名前だけ。`checkpoint` と同じ流儀）。
- **seed はトレースのケースの `setup`・`after` には書けない**（今回は入出力のケースだけ。トレースの Red テストのバイトを変えないため）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 検査（`check_stage`・`check_seed`）・Red テストの生成・版の比べ方・本文の口の行
- `plugins/spec-loop/references/spec-ir.md` — 「前提と後の状態」の節・例・口の表
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 書き起こしの 1 行
- `scripts/test-scaffold.py` — 試料・変異
- `docs/plugins/spec-loop.md` — 公開ページの 1 段落
- `CLAUDE.md` — scaffold.py の項に 1 文
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1298.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/spec-fingerprint.py`（指紋の式は変えない）
- トレースのケースの `setup`・`after` の挙動（`seed` を許さない）
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）

依存の追加・更新: なし
仕様の振る舞い: 変えない

生成物: なし（このリポジトリの生成物は図の書き出しと `SKILL.md` の測定値だけで、どちらも触らない）。

**複製の数**: 「口の名前と形」を述べる箇所は 3（`spec-ir.md` が原本、`scaffold.py` の定数と docstring（`test-scaffold.py` が口の表と突き合わせる）、`scaffold/SKILL.md` は指すだけ）。分けない理由: 1 つの機能追加で、複製は表の 1 箇所に寄せて突き合わせの試験を足した。

## 受入基準

| 番号 | 基準 |
| --- | --- |
| A1 | 入出力のケースに `setup`・`after` を書け、生成した Red テストがその順（`reset_state()` → `setup` → 本体 → `after`）に呼んで期待と比べる。正しい実装で緑、`setup` を無視する・`after` の状態を変えない実装で赤（陽性対照） |
| A2 | `setup`・`after` を書かないケースだけの機能は、生成物（Red テスト・Issue の本文・機能の指紋）が今までと同じバイト |
| A3 | 入口の無い前提を作る口（`seed`）を書け、口の名前が入口の名前・入力の項目と重なれば生成が止まる（`reset_state`・`checkpoint` と同じ扱い） |
| A4 | `references/spec-ir.md` に「前提あり」「2 回の操作」の例を足し、例がテストで生成を通る |
| A5 | 機能の指紋の式を変えるなら、dev-loop の `spec-fingerprint.py` の写しと `scripts/test-scaffold.py` の突き合わせを揃える（式は変えない——機能のオブジェクト全体の sha256 なので、書いたケースを持つ機能だけ指紋が変わる。dev-loop の照合で一致することをテストが見る） |

経路（不変条件 × 破りうる入口）: 入力の入口は中間表現（`check_ir`）のケースの `setup`・`after`（入口の呼び出し・`seed`）だけ。生成の入口は `scaffold.py` の書く生成・`--dry-run`・`--check`・`--red-check`・`--upto`（前の版の時点）・v2 以降の差分（`behavior`・`case_changed`・`trace_moved`）・`--bundle`・性能テスト（入出力のケースの入力だけを使う）。
どれも `red_test`・`check_ir`・`behavior` を通る。トレースのケースの `setup`・`after`（`check_trace`）は別の入口で、変えない。
未証明: 実際の実装の言語・フレームワークとの組み合わせ（生成物は Python の `unittest` だけ）。

## 周の記録

- 周の記録（再開点）: 実装済み。関門はこれから。
- 割り目: 割らない（cruise の周）。

```dev-loop-gates
周の base: e34481971f14a2b8f67e452dfce7b1e50fbe475f
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
受入基準: A5 満たす
マージの反映: ドキュメントとプラグインの配布
```

- この周の起票: 0 件（手順 8 の起票は、親が立てる確認の Issue を除いて無い）
