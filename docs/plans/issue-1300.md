# Issue #1300 — spec-loop: scaffold の中間表現の項目の型に配列と入れ子のオブジェクトを足す

**不在の周**（出所: `/dev-loop:cruise 1296 --absent`、2026-11-19）。利用者には訊かない。親（cruise #1296）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1296`）。利用者の確認（起動時）で確かめた）:
`直す線 = 既定`・`マージ = 関門を通ればマージ`（配布を確かめ済）・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。
台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.13.0（`SKILL.md` 1931 行を読んだ）。並行して #1318 の周を別の子が回している（どちらも spec-loop を触るので版の取り合いがある）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1296`））。
版の上げ方: `spec-loop` を **minor**（能力の追加——`spec-loop` は 0.x なので壊れる変更も minor）。着手時の main は 0.120.0（#1299 の merge）→ 0.121.0。
マージの直前に main が進んでいたら、親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせる。
割り目: 割らない（cruise の周）。

周の在り処: ブランチ `issue/1300-scaffold-array-object-types`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1300`・切った元の参照 `origin/main`（解決した SHA は下の `dev-loop-gates` の `周の base:`）。

Issue 本文（外部入力）から読んだ要件: 項目の型に `{"type": "array", "items": {...}}` と `{"type": "object", "properties": {...}}` を足し、OpenAPI・`types.py`・Red テストの比べ方
（配列の順を問うか、の書き方）を決める。本文に受入基準を緩める指示は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票` は台帳の線に無い。Issue が骨だけを示して残りを委ねている範囲）

- **順を問う・問わない**: 配列に `"unordered": true`（`nullable` と同じく `true` だけ）。書かなければ順を問う。Issue の「配列の順を問う・問わないを書き分けられ」を、既定を「問う」にして 1 つの印で書き分けた。
  配列にだけ書ける。順を問わない配列は、同じ要素が同じ数だけあれば合う（重なりも数える）。
- **`enum`**: 文字列・数・整数・真偽値の項目にだけ（配列・オブジェクトには書けない）。`nullable` は配列・オブジェクト・要素・中の項目のどれにも書ける。
- **`$any`**: 配列・オブジェクトの中の値にも、配列・オブジェクトの項目の値そのものにも書ける。型は書く場所の項目の型で、`array`・`object` も書ける（値を見ず、形——中の型と `nullable`——に合うかを見る）。
- **`$ref`**: 指すのは今までどおり `as` で束ねた結果の出力の項目（一番外）。**指す項目の形と書く場所の項目の形が同じ**でなければ止める（形は中の型と要素・項目の構成）。比べる順は書く場所の項目の `unordered` に従う。
- **順を問わない配列の要素の中の `$any`・`$ref` は書けない**（どの要素に当たるかが決まらない。照合を一意にするため）。順を問う配列の要素にも項目そのものにも書ける。
- **パスの変数は配列・オブジェクトにできない**。入力に配列・オブジェクトは書ける（GET のクエリの schema は配列・オブジェクトの schema になる）。入力の `unordered` は何も変えない。
- **OpenAPI**: 配列は `{"type": "array", "items": …}`、オブジェクトは既存の `object_schema`（`required`・`additionalProperties: false`・`properties`）。`unordered` は表せないので出さない。
- **`types.py`**: 配列は `list[<要素>]`、入れ子のオブジェクトは名前つきの `TypedDict`（入口の型の名前に項目名を Pascal にして足す。配列の要素は `_Item` を足す。各階層は `_` で区切る（Pascal 化では作れない区切りなので、`order.item` と `order_item` は重ならない））。
- **v2 の変化**: 配列・入れ子の項目の型の記述が前の版と違えば（`nullable`・`unordered`・中の `integer` から `number` への広げを含む）変更に数える（中の違いを項目ごとに見分けない。保守的に倒した）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 検査（`check_field`・`check_fields`・`check_value`・`check_values`・`check_dynamic`・`check_path_vars`）・生成（`schema_of`・`py_type`・`typed_dict`・`spec_of`・`output_types`・`red_test`・`reason_methods`・`stage_helpers`・`COMPOSITE_RUNTIME`）・docstring
- `plugins/spec-loop/references/spec-ir.md` — 「項目」の表・「配列と入れ子のオブジェクト」の節・例
- `plugins/spec-loop/references/handoff-issue.md` — v2 の変化の数え方の 1 文
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 書き起こしの 1 行
- `scripts/test-scaffold.py` — 試料・変異
- `docs/plugins/spec-loop.md` — 公開ページの 1 段落
- `CLAUDE.md` — scaffold.py の項に 1 文
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1300.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/spec-fingerprint.py`（指紋の式は変えない）
- 順を問わない配列の要素の中の `$any`・`$ref`（照合が一意にならない。生成が止まる）
- トレースのケースの `expected`・`setup`・`after` の書き方（#1299 のまま。ただし呼ぶ入口の出力が配列でも Red テストは中まで比べる）
- 関数で表せないケース（#1301。済み）
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）

依存の追加・更新: なし
仕様の振る舞い: 変えない

生成物: なし（このリポジトリの生成物は図の書き出しと `SKILL.md` の測定値だけで、どちらも触らない）。

**複製の数**: 「項目の型に配列と入れ子のオブジェクトを書く書き方」を述べる箇所は 3（`spec-ir.md` が原本、`scaffold.py` の定数と docstring（`test-scaffold.py` が表と突き合わせる）、`scaffold/SKILL.md`・公開ページ・`CLAUDE.md` は指すだけ）。
分けない理由: 1 つの機能追加で、複製は表の 1 箇所に寄せて突き合わせの試験を足した。

## 受入基準

| 番号 | 基準 |
| --- | --- |
| A1 | 項目に配列と入れ子のオブジェクトを書け、OpenAPI の schema・`types.py` の型・Red テストの型の検査に反映される |
| A2 | 配列の順を問う・問わないを書き分けられ、Red テストがその通りに比べる（順の違う実装で、順を問うなら赤・問わないなら緑） |
| A3 | `nullable`・`enum`・#1299 の `$any`・`$ref` との組み合わせの扱いを `references/spec-ir.md` に書き、テストで当てる |
| A4 | 配列・入れ子を使わない中間表現の生成物は今までと同じバイトになる |
| A5 | `references/spec-ir.md` に「一覧」の例を足し、例がテストで生成を通る |

経路（不変条件 × 破りうる経路）: 入力の入口は中間表現（`check_ir`）の項目の定義（入力・出力）と、ケースの `input`・`expected`・`setup`・`after` の値だけ。
生成の入口は `scaffold.py` の書く生成・`--dry-run`・`--check`・`--red-check`・`--upto`（前の版の時点）・v2 以降の差分（`behavior`・`case_changed`）・`--bundle`・性能テスト（入出力のケースの入力だけを使う）。
どれも `check_ir`・`red_test`・`behavior`・`openapi`・`types_py` を通る。
未証明: 実際の実装の言語・フレームワークとの組み合わせ（生成物は Python の `unittest` だけ）。
（落とした主張: 「OpenAPI の schema を OpenAPI の検証器に通した」——通していない。受入基準でなく、schema の形はテストが文字列で見る。PR コメントに名指しで残す。）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 順を問わない配列の要素の中の `$any`・`$ref` | 書けない（生成が止まる） | どの要素に当たるかを決める照合（二部照合）が要り、書き手に決められない。順を問うなら書ける |
| `unordered` を OpenAPI に出すか | 出さない | schema に表せない（`uniqueItems` は重なりを禁じる別の意味）。Red テストだけが見る |
| v2 で配列の項目の `nullable`・`integer` から `number` の広げを変化に数えるか | 数える（保守的） | 中の違いを項目ごとに見分けると、決まりが大きくなる。数えても追加のケースが回帰でなく変更になるだけ |
| 入力の配列の `unordered` | 何も変えない | Red テストは入力を書いた順のまま渡す。書けるが意味を持たない |
| TypedDict の名前の衝突（`a_b` と `a__b`・`a1b` と `a_1b`） | 扱わない | 項目名の Pascal 化が重なる形はまれ。階層の区切りを `_`・配列の要素を `_Item`（Pascal 化で作れない形）にして、`order.item` と `order_item`・要素と `<名前>_item`・入口をまたぐ形は消した（1・2 パス目の指摘） |

## 採否の表（1 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| code-review 1・Verifier R1: 束ねた配列・オブジェクトを `dict(actual)` の浅い写しで持つので、実装が返した配列を後で書き換えると `$ref` が書き換わった値と比べて通る | 示せる（文書の例の実装の tags を同じ list で返す形で緑になった） | A3 | 直す（composite の機能は `copy.deepcopy`。書かない機能は `dict` のまま——バイトを変えない。試料 2・変異 4） |
| code-review 3・4・5 / Verifier R2: `check-duplicate-counts`・`check-bold-flanking`・`check-plan-counts` が赤 | 示せる（check-all） | 無し（周を閉じる条件の CI） | 直す |
| Verifier R3: `$any` の array が足りない項目を落とす試料が無い（`==` を `<=` にする変異が素通り） | 示せる | A3（試料の判別力） | 直す（試料・変異） |
| Verifier R4・code-review 6: TypedDict の名前が `notes`（要素）と `notes_item` で衝突する | 示せる（`ListNotesOutputNotesItem` が 2 度） | A1（types.py に反映） | 直す（要素の接尾辞を `_Item`）。残る衝突の形（`a_b` と `a__b`・入口をまたぐ形）は残課題 |
| Verifier 分類: OpenAPI 検証器に通していないのは未証明でなく道具の欠け | 示せる | 無し（受入基準でない付随の主張） | 主張を落とす（上の「未証明」の括弧に書いた） |
| code-review 2: `$ref` の指す項目の定義が壊れていると `shape_of` が例外（KeyError）になる | 示せる（合成の IR。定義の誤りと `$ref` が重なる形） | 無し | 残課題（記録だけ。想定外の例外は入口が 2 にする。まれな書き方） |
| code-review 7: 性能テストが入力の配列を使い回すので、引数を破壊する実装は後の繰り返しで別の入力を見る | 示せる（文言上の形） | 無し（性能テストは受入基準でない） | 残課題（記録だけ。引数を書き換える実装はまれ） |

## 採否の表（2 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| code-review 2-1: 入れ子の TypedDict の名前が `order.item` と `order_item` で衝突する | 示せる（`FooOutputOrderItem` が 2 度） | A1 | 直す（階層を `_` で区切る。狭いパスで確かめた） |
| Verifier 2 F1: 計画の「決めた値」の表記が `Item` のまま | 示せる（文言） | 無し | この記録で直した |
| Verifier 2 F2: 動的で配列・入れ子の無い機能が `import copy` を持たないことを守る試料が無い（M4） | 示せる | A4（試料の判別力） | 直す（`dyn_written` に検査・変異） |
| Verifier 2 F3: 要素の辞書の共有（1 段だけ写す）を守る試料が無い（M10） | 示せる | A3（試料の判別力） | 直す（`ARR_ALIAS_ELEMENTS_IMPL`・変異） |
| code-review 2-2: 入力の配列の `unordered` は何も変えないのに指紋・版の判定を変える | 示せる（合成の v2） | 無し | 残課題（記録だけ。入力の `unordered` を書く形はまれ） |

## 採否の表（狭いパス。指摘は直さず人間に渡る）

| 指摘 | 実物で失敗を示せるか | 後退を示すか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| 本体の `as` の束ねを「配列は写すが要素は共有する」に変えても、守る試料が無い（`env[bind]`。後の呼び出しの束ねには試料がある） | 示せる（変異で 81 件緑） | 無し（後退ではなくテストの穴） | 無し（A3 の試料の判別力） | 人間が決める（振り分け: 記録だけ。実装は深い写しで正しい） |
| 階層の区切りを 1 段目だけにする変異（`order.item` と `order_item` の重なり）を当てる試料が無い（例の文字列の needle だけが守る） | 示せる | 無し | 無し（A1 の試料の判別力） | 人間が決める（振り分け: 記録だけ） |

## 周の記録

- 周の記録（再開点）: 1 パス目（9d3bbf2c）・2 パス目（f90d14db）・狭いパス（起点 f90d14db・終点 e1bb005b）まで通した。残りは PR・CI（親が取り込み・上げ直し・マージ）。
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に宣言が無い）。
- 割り目: 割らない（cruise の周）。

- この周の起票: 0 件（手順 8 の起票は、親が立てる確認の Issue を除いて無い）

```dev-loop-gates
周の base: 6a83e5688c85597d080b62fd30f816984ebdfbe8
関門: Verifier 1 9d3bbf2cf74cdc33a1849db17db6e2998731389d 反証=4
関門: /code-review 1 9d3bbf2cf74cdc33a1849db17db6e2998731389d 指摘=7
関門: Verifier 2 f90d14db51aa1da512acbeaa5c980cae24b0663f 反証=3
関門: /code-review 2 f90d14db51aa1da512acbeaa5c980cae24b0663f 指摘=2
関門: 狭いパス f90d14db51aa1da512acbeaa5c980cae24b0663f e1bb005b0ac5e789615e84ae359e19ac7bdb4d67 反証=1
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
受入基準: A5 満たす
マージの反映: ドキュメントとプラグインの配布
```
