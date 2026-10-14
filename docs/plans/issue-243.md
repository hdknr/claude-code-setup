# Issue #243 — 終了コードの突き合わせが一部のシェルの形で exit を取りこぼす・余分に数える

## 1. 変更範囲

触る:

- `scripts/test-worktree-scripts.py` — `script_exit_codes` を行をまたいで状態を持つ字句解析にする・変異を足す
- `docs/plans/issue-243.md` — この計画ファイル

触らない:

- `prepare-worktree.sh` / `check-pr-preconditions.sh` / `SKILL.md`（一覧も本体も正しい。直すのは突き合わせる側）
- プラグインの version（`plugins/` に触れないので上げない）
- #242 の残課題（CR4〜CR8・CR2-3・CR2-6・CR2-7）。とくに `exit 256` を 0 に正規化しない（CR8）・`--exit-code` で `None`（CR2-3）はこの周で変えない
- 方式の切り替え（スクリプト側に機械可読な宣言を置く案）——採らない。宣言と本体の `exit` を突き合わせるのに、結局同じ字句解析が要る

**複製の数**: 「何を `exit` として数えるか」を述べている箇所は 2 つ——`script_exit_codes` の docstring と本体。
テストの期待値（変異）はその写しではなく、外から当てる側。**分けない理由**: docstring と本体は同じ関数の中にあり、片方だけ直す形が無い。

## 2. デプロイ経路

- `scripts/`：CI の回帰テスト（`plugins.yml` が `test-worktree-scripts.py` を回す）。本番への反映経路なし。
- `docs/plans/`：main への push で GitHub Pages に載る（計画ファイル）。

## 3. 受入基準

**不変条件**

- **I1. 数えるのは「実行される `exit N`」だけ。** 引用（`'…'`・`"…"`・`$'…'`）・heredoc の本文・コメントの中の `exit` を、
  スクリプトの終了コードとして数えない——**行をまたいでも**。
- **I2. 実行されうるかどうか読めない `exit` を「無い」に丸めない。** 文字列・heredoc の本文に `exit` が現れたら `None`
  （一覧と一致とは言わせない）。`trap '…exit 7…'`・`eval "exit 7"`・`bash -c 'exit 7'` はこれに当たる。
  数字の付かない `exit`（`exit "$rc"`・`exit -1`・素の `exit`）も従来どおり `None`。
- **I3. heredoc でないものを heredoc として開かない。** `$((a<<b))`・`(( a<<b ))`（算術のシフト）・`<<<`（here-string）は heredoc ではない。
  **heredoc は正しく閉じる**——`<<-` はタブを剥がした行で閉じ、`<<\EOF`・`<<'EOF'`・`<<"EOF"`・`<<E"OF"` は引用を外した語で閉じ、
  1 行に 2 つの heredoc は順に 2 つとも読む。
- **I4. 番号は bash と同じ値に読む。** `exit 010` は 10（bash の実測: `bash -c 'exit 010'` → 10。#243 本文の「bash では 8」は誤り）。
- **I5. 実リポジトリの 2 本は従来どおり緑**（P8）——`{0,1,2,3,5,6,7}`・`{0,1,2,3,4}`。#206 の既存の変異（P1〜P7・CR2-1・CR2-2・CR2-4）も全部赤のまま。

**それを破りうる経路**（`script_exit_codes` に届く入力の形。差分ではなく bash の字句の入口から数える）

| 経路 | 例 | 守る不変条件 | 期待 |
| --- | --- | --- | --- |
| E1 算術のシフト | `x=$((a<<b))`⏎`exit 8`・`(( a<<b ))`⏎`exit 8` | I3 | 8 を数える（#243 N1） |
| E2 実行される文字列 | `trap 'exit 7' EXIT`・`eval "exit 7"`・`bash -c 'exit 7'` | I2 | `None`（#243 N2） |
| E3 複数行の文字列 | `echo "a`⏎`exit 7`⏎`b"`（単引用・`$'…'` も） | I1・I2 | 7 を数えない（`None`）（#243 N3） |
| E4 heredoc の終端語の引用 | `<<\EOF`・`<<'EOF'`・`<<"EOF"`・`<<E"OF"` | I3 | 本文を飛ばし、終端で閉じる（#243 N3・N4） |
| E5 1 行に 2 つの heredoc | `cat <<A <<B`⏎…⏎`A`⏎…`exit 9`…⏎`B` | I3 | 2 つ目の本文も数えない（#243 N3） |
| E6 `<<-` | `cat <<-EOF`⏎`\techo`⏎`\tEOF`⏎`exit 8` | I3 | タブ付きの終端で閉じ、8 を数える（#243 N4） |
| E7 here-string | `cat <<< foo`⏎`exit 8` | I3 | heredoc を開かず 8 を数える（#243 N4） |
| E8 先頭が 0 の番号 | `exit 010` | I4 | 10 |
| E9 `#` を含むがコメントでないもの | `$#`・`${v#p}`・`"see #206"`・`a#b` | I1 | コメントとして落とさない |
| E10 コメント | 行頭・行末の `# … exit 9` | I1 | 数えない |
| E11 実リポジトリと #206 の変異 | — | I5 | 緑・赤のまま |

**I6. 判別力**: E1〜E10 の各形について、`check_exit_code_lists` に変異（または関数への直接の当て）を置き、
**#242 の版（2 パス目の版）の `script_exit_codes` に差し替えると赤になる**ことを陽性対照で確かめる
（#242 の版で既に正しい形——E8・E9 の一部・E10——は「旧版でも緑」と明記して数え分ける）。

**必須要件の掛け算**: 受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目} = 4 つの受け渡し。

### 証明の手段

- I1〜I5・E1〜E11: `test-worktree-scripts.py`（関数を直接当てる＋変異）。I6: 旧版の関数に差し替える対照スクリプト（scratchpad）。
- `check-all.py`、`gh pr checks`。
- **未証明**: なし（純粋な文字列処理で、この環境で全部当てられる）。**BLOCKED**: なし。
- **生成物**: なし（`SKILL.md`・drawio に触れない。`skill-metrics.py` の対象外）。

## 4. 未解決の判断

- なし。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/243-exit-code-lexer` ／ worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-243` ／
  起点 `75516dd` ／ base 参照 `origin/main` → `75516dd8f05d649ceec4f42ef50b417b19e973da`
- 実装: 済。`shell_code_and_data`（行をまたぐ字句解析）を足し、`script_exit_codes` はその上で数える。
  `check_shell_lexing`（E1〜E10 を値で当てる 27 ケース）と、`check_exit_code_lists` に #243 の変異 11 形を追加。
  `test-worktree-scripts.py` 緑。`check-all.py`: 33/33 本、失敗 0。
- 実装中に 1 件、自分の検査で見つかった: `$'a\nexit 7'` の `\n` の `n` が `exit` の語の境界を消し、`None` にならなかった
  → `$'…'` のエスケープを空白に置き換えて直した（E3 `$'…'` のケース）。
- **陽性対照（I6）**: #242 の版の `script_exit_codes` に差し替えると `check_shell_lexing` 12 件・`check_exit_code_lists` 10 件が赤。
  **#242 の版でも緑のもの**（数え分け）: 直接の当て——E1 数字のシフト・E3 文字列の後ろ・E4 `<<\EOF`／`'EOF'`／`"EOF"`
  （`<<\EOF` は heredoc と認識されないが本文に `exit` が無いので偶然一致）・E5 両方閉じる（同上）・E6 `<<-`・E7・E8・E9・E10。
  一覧側の変異——`trap`・`eval`・`<<E"OF"` への置き換えと、`<<-`・here-string・複数行の単引用の後ろ（**#242 の版では
  集合から番号が消え、それでも「不一致」になるので判別しない**——判別は直接の当てが担う）。
- **新しい実装への変異 11 本**（scratchpad で関数のソースを置換）: 11 本とも `check_shell_lexing` が赤。
  #242 の狭いパスで素通りした 2 本（`<<-` のタブ除去を落とす・here-string の除外を外す）も、ここでは赤。
- 割り目 1（手順 4 完了時）: AskUserQuestion で提案 → **人間が「ここで割る」を選択**（2026-10-14）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 243` → **手順 5（Verifier 1 パス目）から**。
  関門はまだ 1 つも通していない（Verifier・`/code-review` とも 0 パス）。base `75516dd`。
- 交絡: 実験は bash の実測 1 件（`exit 010` → 10・`exit 256` → 0・`<<E"OF"`・`<<\EOF` が `EOF` で閉じる）。
  陽性側: 同じスクリプトで heredoc の後ろの `echo` が出る（閉じたことの観測）。

## 6. 既知の限界・決着済みの論点

- **文字列・heredoc の本文に `exit` が現れたら一律 `None`**——採った。理由: 実行されるか（`trap`・`eval`・`bash -c`・`ssh host '…'`）を
  字句で判定しきれない。`echo "type exit to quit"` のような無害な文も赤になる（偽の赤）が、#206 の方針（値の読めない形を「無い」に丸めない）と同じ向き。
- **`$(exit 3)`（サブシェル）の 3 を数える**——直さない（#242 以前からの挙動。過剰に数える向きで、P3 の偽の緑になりうるが現状どのスクリプトにも無い）。
- **`exit 256` を 0 に正規化しない・`--exit-code` で `None`**——#242 の残課題（CR8・CR2-3）。この周では変えない。
