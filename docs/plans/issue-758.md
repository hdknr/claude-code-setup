# Issue #758（#759・#760 と束ねた周）— コードブロックとコメントの読み方の写し 3 つを揃え、同じ試料の表で突き合わせる

同じ規則（`.claude/dev-loop.md`・親 Issue の本文のコードブロックと HTML コメントの読み方）の写しが 3 つあり、PR #757 で
`run-serial.py` だけ CommonMark に合わせたので食い違った。3 件の Issue を **1 周・1 PR** で扱う
（cruise の台帳のまとめ。代表 #758。`plugins/dev-loop/skills/cruise/references/grouping.md` の「まとめの周」。まとめは親が `ledger.py group` で記録済み）。
周の Issue は #758（worktree・ブランチの名前）。受入基準は 3 件のものを、Issue 番号を付けて下に並べる。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-11-01）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる（#557 の形。この周が自分で立てる。
本文に「マージの前に直す」か「後続で直す」かを書く）。
マージは親がする（この周は手順 6 の PR・CI の確認・関門 2 パスと狭いパス・手順 8 の件数の行まで）。台帳は書かない（親が書く）。
**実際に使われている台帳 `.claude/plans/cruise-issue-474.json` には書かない・触らない。**

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。
版の上げ方: `dev-loop` を **patch**（不具合・記述の修正）。main の先端 1.73.2 → **1.73.3**（マージの直前に main が進んでいたら、その先端から patch で上げ直す）。

重い検査（`check-all.py`・各テスト）は順番待ち越しに走らせる（`references/parallel.md`）。**使う `run-serial.py` は origin/main（`3ba84080`）の写し**
（scratchpad の `i758-rs/run-serial.py`）——この周が直す本体（worktree の中）に枠を任せない。

## 設計の判断（推奨で決めた。確認の Issue を立てる）

**1 つのモジュールにまとめず、写しを残して `scripts/test-fence-copies.py` で同じ試料の表を 3 つの本物の読み口に当てる。**
理由（`scripts/test-fence-copies.py` の docstring を正とする）: 3 つはプラグインのキャッシュから単独で動く・`run-serial.py` は重い検査すべての入口で、
読み込みの失敗が全部の検査を止める・`parent-issue.py` はチェックリストの行が段落を切るので 3 か所で意図して違える・各写しの回帰テストは自分の本体の文字列を壊すので、
本体を動かすと 3 本の変異が全部付け替えになる。リポジトリの決まり（式は 1 か所。`diagram_manifest.py`・`markdown_fences.py`）からは外れるので、
**利用者の判断として確認の Issue を立てる**（推奨: このまま。後続で 1 つにまとめるなら別の周）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/run-serial.py` — #758（BOM を 1 つだけ外す・段落の中のコメントの後ろの開き行・docstring）
- `scripts/test-run-serial.py` — #758（`\x0c`・段落の中のコメント・BOM 2 つの試料、変異 3 つ、変異の注釈を守るの順と番号・文言に揃えて機械で突き合わせる）
- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — #759（`visible_lines` を run-serial の読み方に揃える）・docstring の守る
- `scripts/test-check-unattended-env.py` — #759（書き直した `visible_lines` に変異の当て先を付け替えるだけ）
- `plugins/dev-loop/skills/cruise/scripts/parent-issue.py` — #760（`visible_lines` に分ける・改行でだけ分ける・BOM・字下げは空白とタブ・閉じの後ろは空白とタブ）・docstring の書式と守る
- `scripts/test-parent-issue.py` — #760（試料 1 本・変異 4 つ）
- `scripts/test-fence-copies.py` — 3 つの写しの突き合わせ（新規）
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 新しいテストの CI のステップ
- `CLAUDE.md` — 新しいテストの 1 行
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の行だけ
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-758.md` — この計画ファイル

触らない:

- `parent-issue.py` のコメントの読み方（行頭のコメントを閉じた後ろで開き直した `<!--` を文字と読む）——GitHub の描画と食い違うが、3 件の Issue の受入基準の外（下の「周の途中で見つけた課題」）
- `scripts/check-bold-flanking.py` の `FENCE_OPEN`・`COMMENT_BLOCK`——別の目的（太字の検査）の読み方で、`.claude/dev-loop.md` を読まない
- CommonMark の全部（空行・見出し・リストで段落の中のコメントを終わらせる・`<!-->`）——`run-serial.py` の「守らない」に書いた
- 1 つのモジュールにまとめること（上の「設計の判断」）

### 同じことを述べている箇所の数

- 読み方の規則: 3 つの写しの本体（各 1 関数＋docstring）・`parent-issue.py` の書式の節——**4 か所**。分けない理由は上の「設計の判断」。食い違いは `scripts/test-fence-copies.py` が捕まえる。
- 公開ページ（`docs/plugins/dev-loop-cruise.md`）は「フェンスとコメントの中は読まない」だけで細かい規則を持たない——触らない。

## 乗るデプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。
マージは親がする。

## 周の在り処

- ブランチ: `issue/758-fence-rule-one-table`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-758`
- 起点: `3ba84080`（origin/main。`prepare-worktree.sh` の出力）
- base: 参照 `origin/main` → `3ba84080b22af474d79f2b078a07b4a613a02db7`

## verify の受入基準

### 不変条件と経路

| # | 不変条件 | それを破りうる経路（入口） | 守り方・確かめ方 |
| --- | --- | --- | --- |
| A1 | 3 つの写しが、表の試料で同じに読む（#759・#760） | run-serial: `declaration` → `declared_lines` → `slots_from`（枠の本数）／ check-unattended-env: `read_dev_loop_md` → `visible_lines` → `declared_commands`（`cruise の操作:`）と `merge_effect`（`マージの反映:`・`不在の線:`）／ parent-issue: `read_body` → `visible_lines` → `parse`（チェックリスト・`cruise:` の線） | `scripts/test-fence-copies.py` が本物の読み口でファイルから読む |
| A2 | 写しの 1 つが古い読み方に戻ると、テストが落ちる（陽性対照） | 3 つの写しのどれか | `test-fence-copies.py` の `DRIFTS`（#759・#760 が名指しした形） |
| A3 | parent-issue だけ違えるのは、docstring が挙げる理由の試料だけ | 表の parent-issue の列 | `test-fence-copies.py` が理由の語句を docstring と突き合わせる |
| B1 | `\x0c` の後ろを別の行と読まない試料がある（#758） | run-serial の `NEWLINE` | `PARSE_SAMPLES`「後ろに \x0c のある閉じ行」と変異「\x0c でも行を分ける」 |
| B2 | 先頭の BOM は 1 つだけ外す（#758） | run-serial の `declared_lines` | BOM を重ねた試料が書式に合わない行として 1 と言う・変異「続く BOM も外す」 |
| B3 | 段落の中で始まったコメントの後ろの開き行はコードブロックを始める（#758） | run-serial（と check-unattended-env）の開き行の判定 | 「段落の途中のコメントの後ろの印」が 1・変異。GitHub の描画で確かめる |
| B4 | docstring がコードと合う（#758） | run-serial のモジュールと `declared_lines` の docstring | 読む |
| B5 | 変異の注釈が守るの番号・文言と合う（#758） | `test-run-serial.py` の `MUTATIONS` | `annotations()` が番号・順・文言を本体と突き合わせる |
| C1 | 既存の振る舞いを壊さない | 3 本の回帰テスト（変異テストを含む） | 3 本とも緑。守るの行数と変異の数（run-serial 29・parent-issue 35） |
| C2 | 新しいテストが歯止めの集合に入る | `check-all.py`・CI | `test-check-all.py` の収録漏れの検査 |

### Issue ごとの受入基準

- #758: B1・B2・B3・B4・B5（チェックリストの 5 行）
- #759: A1（check-unattended-env の 4 形——コメントを外した残りで開き行を見る・`splitlines`・字下げを `\s*`・閉じ行の後ろを `.strip()`）・A2
- #760: A1（parent-issue の 5 形——タブの字下げ・後ろの空白とタブ以外・改行だけで分ける・バッククォートの情報文字列・開き行は元の行）・A2

### 必須要件の掛け算

受入基準を 2 つの関門（Verifier・`/code-review`）× 2 パス（1 パス目・2 パス目）に渡す——4 つの受け渡し。2 パス目で直した行があれば狭いパス。

### 証明できないもの（未証明）

- なし。CommonMark の主張（段落の中のコメントの後ろでフェンスが始まる・行頭のコメントの中の印はフェンスでない）は GitHub の描画で確かめた（下の「交絡」）。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の版の行を変える）——`skill-metrics.py --check`（`check-all.py`）で鮮度を見る。図の書き出しは無し。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 1 つのモジュールにまとめるか | 採らなかった（写しのまま `test-fence-copies.py` で突き合わせる） | 上の「設計の判断」。確認の Issue で利用者に渡す |
| parent-issue だけ読み方を違える 3 か所（開きの字下げを数えない・閉じの深さを開きの幅から数える・行の途中で同じ行に閉じない `<!--` を文字と読む） | 違えたまま（表に parent-issue の値と理由を書く） | チェックリストの行が段落を切る・リストの中のフェンス。GitHub の描画で 2 つを確かめた（「関門の進捗」の交絡） |
| `<!-- a --> b <!--` の次の行を parent-issue が読む（GitHub では隠れる） | この周では直さない。周の途中で見つけた課題として起票する | 3 件の Issue の受入基準（フェンスの読み方）の外。表はいまの読み方を固定しているだけで、正しいと言っていない（試料のコメント） |
| CommonMark の全部（空行・見出し・リストで段落の中のコメントが終わる・`<!-->`・`<!--->`） | 写さない | `run-serial.py` の「守らない」。run-serial では宣言が増えない側に倒れる。**check-unattended-env では宣言を点検から落とす側に倒れる**（1 パス目 CR5。残課題） |
| check-unattended-env の BOM | 読む側（`read_dev_loop_md` の `utf-8-sig`）が 1 つ外す | `visible_lines` でも外すと 2 つ外れる。突き合わせはファイルから読むので、読み口ごと比べている |
| `scripts/check-bold-flanking.py` の `FENCE_OPEN`・`COMMENT_BLOCK` | 突き合わせに入れない | 太字の検査の読み方で、`.claude/dev-loop.md` も親 Issue も読まない |

### 1 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1: `COMMENT_BLOCK` の字下げを ` *` にする変異が素通り（字下げ 4 つの `<!--` の試料が無い） | 示せる（変異で `    <!--\n```\n-->\n宣言` が見えると読む。GitHub は隠す） | 無し（いまの読み方は正しい。試料の欠け） | 残課題 |
| V2: レビュー中に計画ファイルが変わった（git status の 2 回が違う） | 示せる（著者が再開点を書いた） | 無し | 残課題ではない（周の記録で、成果物でない） |
| CR1: `-->` で閉じた行頭のコメントの残りで開き直した `<!--` を段落の中のコメントと読み、開き行で終わらせる | 示せる（`slots_from` が main で (1, None)、この周の変更で (3, None)。GitHub は ` x ` だけで後ろを隠す） | C1・B3（この周の変更が入れた退行） | 直す |
| CR2: parent-issue が行頭のコメントを閉じる行の `-->` の後ろを読まない（docstring の「違うのは 3 つ」の外） | 示せる（`<!--\nx -->宣言` を run-serial は読み、parent-issue は読まない。GitHub は見せる） | A3（違えてよい理由の列挙が偽） | 直す（docstring に 4 つ目として書き、表に試料。読み方そのものは後続の Issue） |
| CR3: parent-issue の拒否（Refused）をそれまでの行で読んだことにする | 示せない（誤って緑になる戻し方を示していない） | 無し | 残課題 |
| CR4: 判定が `line.strip() == 宣言` で、宣言を読む側（`slots_from` など）まで当てていない | 示せる（`<!--\nx --> 並行の検査: 3` は表では見える、`slots_from` は 1） | 無し（宣言の書式の違いで、読み方の写しの食い違いではない） | 残課題 |
| CR5: check-unattended-env で、段落の中のコメントが空行の後ろの宣言を隠す（GitHub は見せる） | 示せる（描画） | 無し（前からの読み方。#759 の 4 形の外） | 残課題（決着の理由「宣言が増えない側」は check-unattended-env には当たらない——既知の限界を直す） |
| CR6: check-unattended-env で BOM が 2 つの宣言の行を黙って読み飛ばす | 示せる | 無し（前からの読み方） | 残課題 |
| CR7: parent-issue の `DRIFTS` に #760 の 3 形（タブの字下げ・バッククォートの情報文字列・開き行は元の行）が無い | 示せる（`DRIFTS` に無い） | A2（守り方が「名指しした形」と言う） | 直す |
| CR8: check-unattended-env の戻し方「開き行をコメントを外した残りで見る」が旧いコードと同じでない（元の行の判定を残す） | 示せる | A2 | 直す（元の行の判定を外す） |
| CR9: parent-issue が `-->` の行で開き直した `<!--` を捨て、GitHub が隠す行を読む | 示せる（描画） | 無し（前からの読み方。#760 の外） | 残課題 |

## 未解決の判断・確認待ち

- 設計の判断（写しのまま突き合わせる）——確認の Issue を立てる（番号は下の「関門の進捗」に書く）。

## 関門の進捗（再開点）

- 実装: 済み（`7fe39040`〜`94e3565d`）。割り目は訊かない（不在の周。`references/absent-lines.md` の「訊く場面」）。
- 1 パス目の起点（先に当てた関門に渡した時点の HEAD）: `c113bdf1e386eebcc49da43d404714dedd3dbd83`
- 1 パス目: Verifier（`dev-loop:dev-loop-verifier`・sonnet）——反証 2 件（受入基準を破るものは 0。C1・B5 は順番待ちで回せず未確認と報告、著者の実行で緑）。
  `/code-review`（high）——指摘 9 件。採否は下の「1 パス目の採否」。直すは 4 件（CR1・CR2・CR7・CR8）、手順 4 への差し戻し 1 回（CR1 はこの周の変更が入れた退行）
- 1 パス目の指摘対応: コミット後に起点からの差分を書く
- 交絡: GitHub の描画（`gh api -X POST /markdown`、2026-11-01）で 3 つ確かめた——`memo <!--` の次の ` ``` ` はコードブロック（宣言は `<pre>` の中）・
  行頭の `<!--` の中の ` ``` ` はコードブロックでない（宣言は `<p>`）・`memo <!--` の次の宣言の行は隠れる。陽性対照は素の宣言の行（`<p>` で見える）。
  parent-issue の読み方: `memo <!--` の次のチェックリストの行は見える・リストの中で字下げしたフェンスの中のチェックリストは `<pre>`（理由 INDENT の根拠）。
  **`<!-- a --> b <!--` の次の行は GitHub では隠れる**——parent-issue は読む（周の途中で見つけた課題）。

## 経験の還元（手順 8）

- この周の起票: 0 件（PR を作った時点。確認の Issue と周の途中で見つけた課題を立てたら直す）
