# Issue #487 — spec-loop: spec_ir の出力項目に「型または null」を書けるようにする

`references/spec-ir.md` の項目は null を持たない。項目に `"nullable": true` を書けるようにし、`scaffold.py` の検査（`value_fits` 相当）・
生成する Red テストの型の検査・OpenAPI・`types.py` を対応させる。`nullable` の無い項目は今と同じく null を拒み、既存の中間表現の生成物を 1 バイトも変えない。

**不在の周**である——出所は `/dev-loop:cruise 793 --absent` の起動（2026-11-03）。親からサブエージェントとして委ねられた。
台帳 `issue-793` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: 利用者の確認（起動時・親 Issue #793 の cruise: の行・2026-11-03T03:56:17Z、配布を見せて確かめた））。台帳は書かない（親が書く）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `spec-loop` を **minor**（能力の追加——中間表現に書ける形が増える）。main の先端 0.45.1 → **0.46.0**（PR を出す前・マージの直前に main が進んでいたら、その先端の版から minor で上げ直す）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる（cruise の `references/parallel.md`）:
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — `nullable` の検査・値の検査・OpenAPI・`types.py`・Red テストの生成、docstring
- `plugins/spec-loop/references/spec-ir.md` — 項目の決まりに `nullable` を足す（「null は持たない」を書き換える）
- `plugins/spec-loop/references/handoff-issue.md` — ケースの変化に `nullable` を数えないことを書く
- `scripts/test-scaffold.py` — 試料・変異・OpenAPI と `types.py` の突き合わせの読み方を足す
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-487.md` — この計画ファイル

触らない:

- 入れ子のオブジェクト・配列（Issue の範囲の外。「null は持たない」だけを外す）
- 利用側（tfs-stocks-newslabeling の F-004・spin-dd/tfs-stocks の写しと `EXPECTED_CASES`）——Issue の「広げたら利用側でやること」で、このリポジトリの外
- dev-loop の `spec-fingerprint.py`（指紋の式は変えない。`nullable` は機能のオブジェクトの一部として今の式でそのまま指紋に入る）
- `plugin.json`・`marketplace.json` の description（能力の要約は変わらない）

### 同じことを述べている箇所の数

「項目の型」の決まりを述べている箇所: `references/spec-ir.md` の「項目」の表と注記（原本）・`scaffold.py` の `TYPES` と検査（写し）・
`test-scaffold.py` の `TYPES` の突き合わせ・`handoff-issue.md` の「`変化`」の数えないものの一覧・`scaffold.py` の docstring の同じ一覧（2 箇所）。
計 5 箇所。分けない理由: 原本と写しを同じ周で揃えないと `test-scaffold.py` の突き合わせ（写しが原本と同じか）と記述が食い違う。

## 乗るデプロイ経路

main へのマージでプラグインの配布（spec-loop 0.46.0）。公開サイトは `docs/` の計画ファイルだけで反映経路なし。マージは親がする（手順 7 はしない）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| N1 | 項目に `"nullable": true` を書ける（入力・出力の両方）。`true` 以外の値・決まりに無いキーは今と同じく 1 で断る | `check_fields` の許すキー・値の形 | `test-scaffold.py` の試料: nullable の出力を持つ中間表現が 0、`nullable: false`・`"yes"` が 1 |
| N2 | `nullable` の項目では、ケースの `input`／`expected` に `null` を書ける。`nullable` の無い項目の `null` は今と同じく 1 で断る（enum を持つ項目も） | `check_values`（型の検査・enum の検査の両方の分岐） | 試料: nullable の出力に null を期待するケースが 0・nullable でない出力に null が 1・nullable で enum を持つ項目に null が 0 |
| N3 | 生成する Red テストは、`nullable` の出力に `None` を返す実装を通し、`nullable` でない出力に `None` を返す実装を落とす。型の違う値（`1` を文字列の項目に）は今と同じく落とす | 生成する Red テストの `check` の型の検査 | 試料: 正しい実装（None を返す）で緑（陽性対照）・`nullable` でない項目に None を返す実装と、nullable の項目に型の違う値を返す実装で失敗 |
| N4 | OpenAPI は `nullable` の項目を `{"type": ["<型>", "null"]}`（enum があれば enum に `null` を足す）、`types.py` は `<型> \| None` で表す | `schema_of`・`py_type`（入力・出力・パラメータ・ボディ） | 試料で OpenAPI の schema と `types.py` の注釈を見る。`input_split_problem`（exit 0 の全試料に当てる突き合わせ）が nullable の形も読む |
| N5 | `nullable` を書かない中間表現の生成物（`scaffold/` の 3 種・Issue の本文）は、この周の前と 1 バイトも変わらない | 生成の全経路（OpenAPI・`types.py`・Red テスト・Issue の本文・指紋） | base（412ca8f7）の `scaffold.py` とこの周の `scaffold.py` で、`test-scaffold.py` の基準の試料から作った出力を比べてバイト一致（陽性対照: nullable を書いた試料では違う） |
| N6 | パスの変数に `nullable` は書けない（パスの値は null にならない）——1 で断る | `check_path_vars` | 試料が 1 |
| N7 | `nullable` を足す・外すだけの違いはケースの `変化` に数えない（前の版で通った実装は同じ期待で通る） | `case_changed` | 試料（v2 で出力に nullable を足す）で本文のケースが `回帰` |
| N8 | 原本（`spec-ir.md`）と写し（`scaffold.py` の docstring・`handoff-issue.md`）が同じことを言い、版を 3 箇所で上げる | 記述・`check-plugin-versions.py` | 読んで突き合わせる・`check-all.py` が緑 |
| N9 | 他の歯止めを割らない | `check-all.py` の全部・PR の CI | `run-serial.py -- python3 scripts/check-all.py` が緑、`gh pr checks` が緑 |

**この環境で証明できないもの**: なし（すべて一時ディレクトリの試料と `unittest` で確かめられる）。利用側（tfs-stocks）で F4-3・F4-5 が通ることは Issue の範囲の外。

**生成物**: このリポジトリに鮮度を見る生成物の該当なし（図・`skill-metrics.py` の生成ブロックは触らない——`SKILL.md` は版の 2 行だけで、`skill-metrics.py` が測るのは dev-loop の `SKILL.md`）。
`scaffold.py` 自身が生成するものの「既存の出力が変わらない」は N5 で見る。

必須要件の掛け算: 受入基準を Verifier・`/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

## 未解決の判断・確認待ち

- なし（下の「既知の限界・決着済みの論点」に実装で決めた形を書く）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/487-spec-ir-nullable`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-487`・
  起点 `412ca8f7`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `412ca8f78ff7177110e8250dcce4ebcbcf0d624a`
- 割り目（手順 4 の完了時）: 不在のため訊かず続けた（割らない（不在の cruise））
- 関門: 1 パス目を通した——Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件（指摘 1 件・N8 の版と N9 は未確認と報告）／`/code-review`（high）指摘 9 件。
  **1 パス目の指摘対応の起点**: `6e8cfb33`（関門に渡した時点の HEAD）。直すとした 2 件（R4・R7）を直した——2 パス目を回す
- 歯止め: 1 回目の `check-all.py`（順番待ち越し）は `check-plan-counts.py` だけ落ちた（計画ファイルに件数の行が無かった——足した）。他の 57 本は緑
- 割り目（2 パス目の前）: 不在のため訊かず続けた（割らない（不在の cruise））
- 2 パス目: 通した——Verifier（sonnet）反証 0 件（test-scaffold・A/B は順番待ちで走らせられず未確認、と報告）／`/code-review`（high）指摘 3 件。直すとした 1 件（R2-2）を直した。
  **狭いパスの起点**（2 パス目の指摘対応を始める直前の HEAD）: `84b96397`・**終点**（指摘対応の最後のコミット）: `a16890ab`
- 狭いパス: 通した——Verifier（sonnet。`git diff 84b96397 a16890ab`）反証 0 件・指摘 0 件。`py_type` を実際に走らせて記述（`str | None`・`Literal['a', 'b'] | None`）と一致。変異は設計したが当てていない（文書 1 行の変更で、記述と実出力を直接突き合わせたため）——赤 0・素通り 0
- 歯止め: 2 回目の `check-all.py`（`84b96397`。順番待ち越し）は 58/58 緑
- 歯止め: 3 回目の `check-all.py`（`a16890ab`。順番待ち越し）は 58/58 緑。PR を出す前に main（0.45.1・`412ca8f7` のまま）を見た——取り込みは要らない
- 反証と差し戻し: なし
- 交絡を潰した手順: N5 の A/B（scratchpad の `ab487/ab.py`）——base（412ca8f7）の `plugins/spec-loop/scripts` と今の版で、nullable を書かない 4 つの試料
  （基準・impl_module・パスの変数・v2 の変更）の `scaffold/` と Issue の本文がバイト一致（違うファイル 0）。**陽性対照**: nullable を書いた試料では
  base が 1 で断り、出力は 9 ファイル違う——比べ方が差を出せることを見た。テストの `BASE_SHA256` は base の出力から取った値
- 実装の検査: `test-scaffold.py`（順番待ち越し）が「OK: 試料 224 件・変異 167 件」。1 回目は既存の変異「OpenAPI の schema から enum を落とす」の
  壊す箇所が 2 回現れて落ちた（足した `out["enum"] = field["enum"] + [None]` が同じ文字列を含む）——その変異の文字列に次の行を足して 1 回に絞った

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 書き方を `"nullable": true` にする | 採った | Issue の例の形。`type` を配列にする書き方（`["string", "null"]`）は `type` の決まり（1 つの文字列）と検査をすべて変えるので採らない |
| `"nullable": false` を許すか | 許さない（`true` だけ） | 省くのと同じ意味の書き方を 2 つ作らない——機能の指紋（機能のオブジェクトの sha256）が、意味の同じ 2 つの書き方で違う値になる |
| パスの変数を `nullable` にできるか | できない（1） | パスの値は null にならない（OpenAPI の path パラメータは必須の文字列の置き場所） |
| enum を持つ項目の `nullable` | 許す。`null` は enum に書かない（enum の値は型に合うものだけ）。OpenAPI の enum には `null` を足す | JSON Schema では enum が null を拒むので、`type` に `"null"` を足すだけでは null が通らない |
| Red テストの生成の形 | `nullable` の出力を持つ機能だけ、`NULLABLE` の集合と、`None` を型の検査から外す行を足す | `nullable` を書かない機能の Red テストを 1 バイトも変えない（N5）——`type_fits` を書き換えると既存の `scaffold/` が `--check` で古くなる |
| 仕様の穴か | 穴ではない | Issue が書き方を例で示し、実装に委ねている。上の決着は利用者に見える結果（null を書ける・書けない）を変えず、書き方の細部だけ |

### 1 パス目の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | GET・DELETE の入力の `nullable` が、必須の query パラメータの `type: [<型>, "null"]` になり、query string では null を送れない（Verifier と /code-review の両方） | 示せる——GET の入力に nullable を書いた試料が 0 で、OpenAPI が `in: query, required: true, type: ["boolean","null"]`（Verifier の実走） | 無し（N4 は表し方を決めているだけで、query を断るとは言っていない） | 残課題 |
| R2 | `case_changed` が、期待が `None` の項目の型の変更（nullable の integer → nullable の string）を `変更` に数える（Red テストは None の型を見ないので前の版の実装は緑） | 示せない（読んだだけ。型を変える v2 の試料は走らせていない） | 無し（N7 は nullable を足す・外すだけの違い。型を変えるのは今までどおり変化） | 残課題 |
| R3 | `BASE_SHA256` が Issue の本文・v2 の出力を固定していない（N5 の主張より狭い） | 示せない（N5 そのものは A/B で成り立つ——/code-review が 199 試料で同じ結果） | 無し（N5 は A/B で確かめた。テストの範囲の狭さ＝試料の穴） | 残課題 |
| R4 | `spec-ir.md` の「テストケース」の表と Red テストの段落が、null の例外を書いていない（原本の中で食い違う） | 示せる——`spec-ir.md` の `input`・`expected` の行が「その型（と `enum`）で」のまま | N8 | 直す |
| R5 | `BASE_SHA256` は今の生成物のバイトを固定するので、意図して生成を変える後の周がこの試料で落ちる | 示せない（将来の変更） | 無し | 残課題 |
| R6 | パスの変数の nullable の拒否が `path_rules=False`（前の版の比べる相手）で効かない | 示せない（nullable を持つ前の版はこの周より前に作れない——前の `scaffold.py` は `nullable` を断る） | 無し | 残課題 |
| R7 | `check_values` の docstring が null の例外を書いていない | 示せる——docstring が「その型と enum で持つか」のまま | N8（scaffold.py の写し） | 直す |
| R8 | enum に `null` を並べたときの文言が `nullable` を案内しない | 示せる（「enum の値が型 string でない」とだけ出る。Verifier の実走） | 無し | 残課題 |
| R9 | `types.py` の `<型> \| None` は実行時に注釈を解決すると Python 3.10 以上が要る | 示せない（3.9 で走らせていない） | 無し（Issue が `str \| None` を名指し） | 残課題 |

### 2 パス目の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R2-1 | `case_changed` の docstring が、null を許す項目の `None` の型を Red テストが見ないことを書いていない（R2 の隣） | 示せる（docstring の文） | 無し（`case_changed` の判定は N7 のとおり。docstring の言い漏れ） | 残課題 |
| R2-2 | `spec-ir.md` が `types.py` の型を「`<型> \| None`」と書くが、`enum` のある項目は `Literal[...] \| None` になる | 示せる——`py_type` が `Literal['a', 'b'] \| None` を出す（/code-review の実走） | N4・N8（原本が生成物と違うことを言う） | 直す |
| R2-3 | R4 で足した Red テストの段落の null の例外が、同じ原本の「null を許す項目」の写しになっている（指し先にしていない） | 示せない（今は食い違っていない） | 無し | 残課題 |

## 手順 8

### 振り分け（`references/found-lines.md`。不在の cruise・`周の途中の課題 = 外に出す`）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| R1 GET・DELETE の nullable の入力が null を送れない query パラメータになる | #487 Verifier・/code-review 1 パス目 | 示せる | 記録だけ——GET の入力に null を許す仕様はまず書かれない（Issue の用途は出力の null） |
| R2 型を変えた null の期待のケースを `変更` に数える | #487 /code-review 1 パス目 | 示せない | 記録だけ |
| R3・R5 `BASE_SHA256` の範囲が狭い・後の周で固定が古くなる | #487 /code-review 1 パス目 | 示せない | 記録だけ（試料の穴） |
| R6 前の版の比べる相手でパスの変数の nullable を見ない | #487 /code-review 1 パス目 | 示せない | 記録だけ（前の版に nullable は書けなかった） |
| R8 enum に null を並べたときの文言 | #487 /code-review 1 パス目 | 示せる | 記録だけ（文言） |
| R9 `\| None` は注釈の実行時の解決に Python 3.10 が要る | #487 /code-review 1 パス目 | 示せない | 記録だけ |
| R2-1 `case_changed` の docstring の言い漏れ | #487 /code-review 2 パス目 | 示せる | 記録だけ（文言） |
| R2-3 Red テストの段落が写しになっている | #487 /code-review 2 パス目 | 示せない | 記録だけ（文言） |

仕様の穴: なし（確認の Issue は立てていない）。焼き戻す学び: なし（既存の規範——変異の文字列が 1 回だけ現れることの検査——が、この周で足した文字列との重なりを捕まえた）。

- この周の起票: 0 件（起票の承認は不在のため訊いていない）
