# Issue #1368 — dev-loop: コミットの検証の関門で、引用符の中の << と -m 付きのヒアドキュメントの誤判定を直す

cruise（親 Issue #1374）の 1 周。**不在の周**（`/dev-loop:cruise 1374 --absent` の起動・2026-11-20）。
読み込んだ dev-loop の `SKILL.md` は 1946 行（キャッシュの 2.17.0。`wc -l` と一致）。

版の上げ方: `dev-loop` を **patch**（不具合の修正）。main の 2.17.0 → 2.17.1（`marketplace.json`・`plugin.json`・`dev-loop` と `cruise` の `SKILL.md` の 2 行）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から patch で 1 つ上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。

## 確かめた線（cruise の台帳）

出所: 利用者の確認（起動時・親 Issue #1374 の `cruise:` の行・2026-11-20T11:38:12Z、配布を見せて確かめた）。

- 直す線 = 既定
- 仕様の穴 = 推奨で決めて起票
- マージ = 関門を通ればマージ
- 周の途中の課題 = 外に出す
- マージ前の判断 = 推奨で決めて起票（後退・未達を含む）
- 実機確認: 線なし（止まる）

## 周の在り処

- ブランチ: `issue/1368-commit-gate-heredoc-quotes`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1368`
- 起点コミット: `aec1ce1f`（切った元の参照 `origin/main`）
- 周の base: `aec1ce1f89d4c2a49fd52aedd318383d6029a8c0`（`git merge-base origin/main HEAD`）

## Issue 本文（外部入力）から読んだ要件

- 本文の先頭は `<!-- cruise-followup: #1290 -->` と `作り直しの元: #1192`——#1192（PR #1357）でマージ時に残した後退 V1・V2 のフォローアップ。
  **PR の本文に `作り直しの元: #1192` の行を写す**（`SKILL.md` 手順 1）。
- V1: `heredoc_text` が引用符を消した骨組みで `<<` を探す。V2: `-m` を渡した `git commit` ではヒアドキュメント（stdin）を本文に数えない。
- V3・V4 は「参考（任意。直さなくてよい）」——**この周では直さない**（`触らない:`）。
- 受入基準を緩める指示・追加のコマンド実行の依頼は無かった。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/commit-gate.py` — ヒアドキュメントの見つけ方（引用符の外の `<<` だけ。`"$(…)"` の中は見る）と、`-m` のときヒアドキュメントを数えないこと。docstring
- `scripts/test-commit-gate.py` — V1・V2 の試料と、足したコードの変異
- `plugins/dev-loop/skills/dev-loop/references/verification-trailer.md` — 「動かせない・効かない環境」の読み方の 1 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1368.md` — この計画
- `docs/plugins/dev-loop-design.md` — `skill-metrics.py` の生成ブロック（`references/verification-trailer.md` の行数が変わる。手で書かない）

触らない:

- V3（同じ行に 2 本目の commit が続くと 1 本目の本文で判定する）・V4（`鍵 :` の空白・区切りの `.`・表の行の形の試料）——Issue が任意とした
- ヒアドキュメントの他の読み方（`<<<` のヒアストリング・1 行に 2 つの `<<`・`$( )` の外の `( )`）——変えない
- `check-gates.py` と、印の中身と履歴の突き合わせ

依存の追加・更新: なし
仕様の振る舞い: 変えない（このリポジトリに spec-loop の正本は無い）
差分テスト: なし（理由: 不具合を直して判定を変えることが目的の周。変えない側——ほかの形の判定——は、既存のスイートが形ごとに期待値（旧い実装の出力ではなく、決めた判定）として持ち、それを受入基準 3 で見る）
プロパティテスト: なし（理由: 判定はコマンドの形ごとに決まる個別の規則で、往復・冪等性・等価性・数値の境界の不変条件を持たない）

**同じことを述べている箇所の数**: ヒアドキュメントの読み方は `commit-gate.py` の docstring と `references/verification-trailer.md` の 2 箇所（＋テストの期待値）。
分けない理由: docstring が守る／守らないの原本で、参照ファイルは利用者向けの要約。2 箇所とも 1 行ずつで、同じ周で直す。

**生成物**: `skill-metrics.py` の生成ブロック（`docs/plugins/dev-loop-design.md`。`references/verification-trailer.md` の行数が 1 行増えるので変わる——`check-all.py` の 1 回目で `--check` が落ちて分かった。`python3 scripts/skill-metrics.py` で書き直し、`--check` で鮮度を見る）。drawio・その他の生成物なし。

乗るデプロイ経路: main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。

## 受入基準

| # | 受入基準 |
| --- | --- |
| 1 | V1: `git commit -m 'docs: explain <<EOF usage' && cat > notes.md <<'EOF'` ＋ 次の行 `Verified: verify`（＋ `EOF`）を enforce で止める（rc=2）。テストの試料にあり、直す前は赤・直した後は緑（陽性対照） |
| 2 | V2: `git commit -m 'feat: x' <<'EOF' && git push` ＋ `Verified: verify` を止め（rc=2）、`git commit -m 'feat\n\nVerified: verify' <<'EOF' && git push` ＋ `Verified: lol` を通す（rc=0）。テストの試料にあり、直す前は赤・直した後は緑 |
| 3 | 既存の 50 本の変異がすべて検出されたまま（`test-commit-gate.py` の出力）。既存のスイートの期待（ほかの形の判定）が緑のまま |
| 4 | 版が 3 種類の箇所で揃い、`check-all.py` と PR 側の CI が緑 |

### 不変条件 × それを破りうる経路

入口: hook（引数なし。stdin の `tool_input.command`）だけがコマンドを読む。`status`・`report` はコマンドを読まない。
コマンドの中でヒアドキュメントを見るのは 2 か所——`skeleton`（どこに `git commit` があり、その部分がどこで終わるか）と `heredoc_text`（その commit の部分で始まるヒアドキュメントの本文を判定の文面に足す）。

| 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- |
| I1 引用符の中（単一引用符・`$( )` の外の二重引用符）の `<<` はヒアドキュメントの始まりと読まない | `heredoc_text`（V1）・`skeleton`（引用符の中の `<<` が本物のヒアドキュメントを飲み込むと、本体を消す範囲がずれる）・`-m` の無いコミット（`--author='… <<EOF …'` など） | 両方が同じ関数（引用符を辿って外の `<<` だけを見る）を通す |
| I2 二重引用符の中の `$( … )` のヒアドキュメント（`-m "$(cat <<'EOF' … EOF )"`）は今までどおりヒアドキュメント | `skeleton`（本体の `"` で引用符の対がずれると、本体の改行で部分が切れ、印を読み落として止める） | `"$(` の中は引用符の外と同じに辿る |
| I3 `-m`／`--message` を渡したコミットは、ヒアドキュメント（stdin）を判定の文面に足さない | `heredoc_text`（V2）。**`find_commits` の範囲**（ヒアドキュメントの前の改行が骨組みで `\x01` に化けるので、`&&` の続かない形では範囲が本体まで伸び、`command[a:b]` 自体が本体を含んでいた——実装中に `-am`・`--message=` の試料で見つけた）。`-am`・`--message=`・`-m` の後ろの `<<` | その commit の部分（骨組み）に `-m` 系があれば足さない。範囲は `<<EOF` の行の終わりで切り、本体は `heredoc_text` だけが足す |
| I4 `-F -`／`--file=-`（`-m` なし）のヒアドキュメントは今までどおり本文 | `heredoc_text` | I3 の条件は `-m` 系だけ（`-F` は含めない） |
| I5 ほかの形の判定は変わらない | 既存のスイートの各形（連結・`$'…'`・本体の `git commit`・CRLF・区切りの `-`） | 既存のスイートを緑のまま |

**証明できないもの（未証明）**: 本物の Claude Code に登録して発火させた hook での挙動（#1192 から変わらず。テストは hook の stdin を真似る）。この周の受入基準はどれもこれに寄りかからない。

**必須要件の掛け算**: 受入基準 1〜4 を Verifier と `/code-review` の両方に、1 パス目と（指摘対応があれば）2 パス目に渡す（4 つの受け渡し）。

## 既知の限界・決着済みの論点・関門の指摘の採否

- V3・V4 は直さない（Issue が任意とした。`触らない:`）。指摘されたら残課題。
- `<<<`（ヒアストリング）・1 行に 2 つの `<<`・`$( )` の外の `( )` の中の読み方は変えない。
- 引用符の辿り方は既存の `QUOTED`（単一引用符は次の `'` まで・二重引用符は `\` の跳ばしつき・閉じない引用符は文字のまま）に合わせる。
  **引用符の外の `\'` は跳ばさない**——`QUOTED` も跳ばさず（`echo don\'t && git commit …` の commit は、直す前から骨組みで隠れる）、片方だけ跳ばしても判定は変わらなかった
  （最初は跳ばす分岐を足したが、その変異が素通りして、効いていないと分かったので外した）。直す前からある読み方で、この周では変えない。
- 閉じない二重引用符の後ろの `<<` は、引用符の中と読む（`QUOTED` は文字のままと読む）。閉じない二重引用符のコマンドはシェルで走らないので、判定の差は実際の利用では起きない。

## 関門の進捗（再開点）

- 周の base: `aec1ce1f89d4c2a49fd52aedd318383d6029a8c0`
- 割り目: 割らない（cruise の周）

## 手順 8 の記録

- この周の起票: 0 件（起票の候補なし）
