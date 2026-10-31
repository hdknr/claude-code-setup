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
- `plugins/dev-loop/skills/cruise/SKILL.md`・`plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
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
| B2 | 先頭の BOM は 1 つだけ外す（#758） | run-serial の `declared_lines` | 「BOM が 2 つ」が 1 と言う・変異「続く BOM も外す」 |
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

## 未解決の判断・確認待ち

- 設計の判断（写しのまま突き合わせる）——確認の Issue を立てる（番号は下の「関門の進捗」に書く）。

## 関門の進捗（再開点）

- 実装: 済み（コミット前）。割り目は訊かない（不在の周）。
- 交絡: GitHub の描画（`gh api -X POST /markdown`、2026-11-01）で 3 つ確かめた——`memo <!--` の次の ` ``` ` はコードブロック（宣言は `<pre>` の中）・
  行頭の `<!--` の中の ` ``` ` はコードブロックでない（宣言は `<p>`）・`memo <!--` の次の宣言の行は隠れる。陽性対照は素の宣言の行（`<p>` で見える）。
  parent-issue の読み方: `memo <!--` の次のチェックリストの行は見える・リストの中で字下げしたフェンスの中のチェックリストは `<pre>`（理由 INDENT の根拠）。
  **`<!-- a --> b <!--` の次の行は GitHub では隠れる**——parent-issue は読む（周の途中で見つけた課題）。
