# Issue #412 — CLAUDE.md: 取り込みで増えた検査の見方（ORIG_HEAD）が空になる・混ざる・取りこぼす

#409 の周（PR #411）の `/code-review` 2 パス目の残課題 R1〜R3 を直す。

## 変更範囲

触る:

- `CLAUDE.md` — 「並行する周は、同じ版に上げて衝突する」の節の、取り込みで増えた検査の見方の 1 文（現 499〜500 行）
- `docs/plans/issue-412.md` — この計画

触らない:

- `docs/plans/issue-409.md`（元の周の記録。`ORIG_HEAD` の形が残るが、記録なので直さない）
- 歯止め・プラグイン（`plugins/` を触らないので版を上げない）
- 公開ページ（この見方は公開ページに複製していない）

### 同じことを述べている箇所の数

- 「取り込みで増えた検査の見方」: `CLAUDE.md` の 1 箇所だけ（`grep -rn ORIG_HEAD` ——ほかは `docs/plans/issue-409.md` の記録）。分けない。

## 乗るデプロイ経路

`CLAUDE.md` はサイトに載らない（`mkdocs.yml` の nav にあるのは `docs/usage/claude-md.md` で、ルートの `CLAUDE.md` ではない）。反映経路はマージのみ。

## 周の在り処

- ブランチ: `issue/412-merge-new-guards-view`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-412`
- 起点: `e7aedee`（PR #411 のマージ）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `e7aedeeb9b22dda924562cd6cbd183f916fbdf20`

## verify の受入基準

Issue 本文の「案」は検査対象であって要件ではない（とくに `<merge>^1 <merge>^2` は周の側の変更を逆向きに含むので採らない）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| G1 | 書いた見方の出力が、**main が周を切った後に `scripts/` と `plugins/*/scripts/` へ入れた変更**だけを出す（周の側の変更を含まない） | 取り込む前に見る形／取り込んだ後に見る形 | 一時リポジトリで両方の形を走らせ、期待の行と突き合わせる |
| G2 | R1: 取り込んだ後に「Already up to date」の `git merge`・`git reset --soft` を挟んでも、取り込んだ後の形の出力が空にならない | 取り込んだ後の形 | 一時リポジトリで実測 |
| G3 | R2: 取り込んだ後に周が `scripts/` をコミットしても、取り込んだ後の形の出力に混ざらない | 取り込んだ後の形 | 同上 |
| G4 | R3: `plugins/*/scripts/` 側の変更が出る。新しく足したものと変えたものが見分けられる | 両方の形 | 同上（`--name-status` の `A`／`M`） |
| G5 | 本文が書く限定・注意（いつ走らせるか、クォート）が実測と一致する。主張が偽でも同じ出力になる設定でない（陽性対照） | 記述 | 一時リポジトリ。取り込んだ後に取り込む前の形を走らせると空になること、クォートしない zsh で手元に無いプラグインが落ちることも実測 |
| G6 | #389 の実データ（`e541e76`→`47a45e9`）に当てて、#384 が足した `check-plan-counts.py` が出る | 取り込んだ後の形 | 本物のリポジトリで読み取りだけ |
| X1 | 全歯止めが緑 | 全体 | `python3 scripts/check-all.py` |

規定の掛け算: 受入基準 × 2 つの関門 × 2 パス（1 パス目の指摘対応の差分が 0 行なら 2 パス目は無い）。

### この環境で証明できないもの

- 無し（git の挙動はすべて一時リポジトリで再現できる）。

### 生成物

- 生成物なし（`CLAUDE.md` は図の書き出し・`skill-metrics.py` の生成ブロック・JSON の版のどれにも関わらない）。

## 未解決の判断

- 無し

## 関門の進捗（再開点）

- 実装: 済み（`CLAUDE.md` の 1 文を、取り込む前の形・取り込んだ後の形・クォートの注意・`A`/`M` の読み方に置き換えた）
- 交絡を潰した手順:
    - 一時リポジトリ（`GIT_CONFIG_GLOBAL=/dev/null`）で、周の側に `scripts/` のコミット、main 側に `scripts/` の追加・`plugins/a/scripts/` の変更・**手元に無い** `plugins/b/scripts/` の追加を置いた。
    - 陽性対照: 2 点の `HEAD origin/main` では周の側の `cycle-own.py` が `D` で出た——3 点の形でそれが消えるのは、判別している証拠。
    - **Issue の案のパス `'plugins/*/scripts/'` は 1 件も当たらなかった**（初回の実験で `plugins/` の行が 0）。`'plugins/*/scripts/*'` で 3 件とも出た。
    - クォートしない zsh では `plugins/b`（手元に無い）が落ちた。
    - R1（Already up to date の merge ＋ `reset --soft`）・R2（取り込んだ後の周のコミット）は、旧い形が空／混ざる、新しい形が変わらない、を同じリポジトリで並べて見た。
    - 実データ: `47a45e9`（#389 の取り込み）で、新しい形は 8 件（`A scripts/check-plan-counts.py` を含み、`plugins/spec-loop/scripts/` の 3 件を含む）、旧い形の `-- scripts/` は 5 件。
- 実装のコミット: `32824c2`。`check-all.py` は初回に件数の行を足す前に走り `check-plan-counts.py` だけ赤→足して**単独で**再実行し緑（**通しの 47/47 緑はこの時点では観測していない**。関門の 1 パス目で 2 体がそれぞれ通しで 47/47 緑を観測した）
- 割り目（手順 4）: AskUserQuestion で「ここで割る」が選ばれた（2026-10-25）
- 関門 1 パス目: 済み（2026-10-25。再開したセッションで手順 5 から）——Verifier（`dev-loop:dev-loop-verifier`・sonnet）**反証 0 件**、`/code-review`（high）**指摘 6 件**（採否は下の表。直す 2 件・残課題 4 件）。
  指摘対応（C1・C3）のコミット: `bc6a299`。`check-all.py` 通しで 47/47 緑（失敗 0 / 飛ばし 0）。
  **残っているのは 2 つ**——Verifier の当て直し（2 パス目）と `/code-review` の 2 パス目。どちらも base は同じ `e7aedee…`。
  2 パス目の指摘対応を始める直前の HEAD（狭いパスの起点）は、2 パス目の報告を受けた時点でここに書く。
  割り目（手順 6 の 2 パス目の前）: AskUserQuestion で訊く（結果をここに書き戻す）。
  起動直後に親がこの計画ファイルの進捗欄を書き換えたため、両体の `git status --porcelain` の 2 回目に ` M docs/plans/issue-412.md` が出た（関門の変更ではない）。
  base は `e7aedeeb9b22dda924562cd6cbd183f916fbdf20`。関門に渡したときの HEAD: `26d4860aa5239d92e4bb8523a6bcacfa40dd6da5`（1 パス目の指摘対応の起点）

## 起票

- この周の起票: 0 件

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| Issue 本文の案 `<merge>^1 <merge>^2` | 採らない | 2 つの親の比較は周の側の変更も（逆向きに）含む。取り込みが足したものは `<merge>^1 <merge>` |
| Issue 本文の案のパス `plugins/*/scripts/` | 採らない | 末尾が `/` の glob の pathspec は `plugins/` の下に当たらない（実測）。`'plugins/*/scripts/*'` にした |
| Issue 本文の案 `--diff-filter=A` | 採らない | `plugins/*/scripts/` 側の検査の強化は `M` で、`A` だけにすると R3 の取りこぼしが戻る。`--name-status` で `A`/`M` を見分ける |
| 取り込みが fast-forward だったとき、merge コミットが無い | 本文に書かない | 周が自分のコミットを持たない取り込みで、周の途中ではまず起きない。`git log --merges -1` が別の merge を返しうるので、件名で確かめる、と書いた |
| （1 パス目 C4 で理由を補う）`git rebase origin/main` で取り込んだときも merge コミットが無い | 本文に書かない（残課題） | 節の手順は `git merge origin/main` を指定しており、rebase はその手順の外。件名で確かめれば自分の取り込みでないことには気づける |

### 1 パス目の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| C1 | クォートしない場合に落ちるのは「main が足したプラグイン」だけではなく、手元に在るプラグインの中の新しいファイルと入れ子（`skills/*/scripts`）も落ちる | 示せる——一時リポジトリ（bash）で `A plugins/a/scripts/new-in-a.py` と `A plugins/d/skills/d/scripts/f.py` が落ち、`A scripts/new.py` だけが出た（親も再現） | G5 | 直す |
| C2 | 手順 1〜5 の 1 番目が `git merge` のままで、取り込む前に見る段が手順に無い | 示せない（取り込んだ後に走らせると空になることは本文が既に書き、取り込んだ後の形を示している） | 無し | 残課題 |
| C3 | `git reset --soft` の後は ORIG_HEAD が HEAD と同じにならない（周のコミットを指し、逆向きに混ざる） | 示せる——一時リポジトリで `reset --soft HEAD~1` 直後に ORIG_HEAD≠HEAD、差分は `D scripts/after.py`（親も再現） | G5 | 直す |
| C4 | `git rebase` で取り込んだとき `git log --merges -1` が main 側の merge を返し、代わりの手段が無い | 示せる（一時リポジトリ）が、節の手順（`git merge`）の外 | 無し | 残課題（決着の表に理由を補った） |
| C5 | 計画ファイルの「47/47 緑」は通しで観測していない | 記録の正確さ（関門は記録を検査しない） | 無し | 残課題（記録は直した） |
| C6 | 周の中で 2 回以上取り込んだとき、直近の merge だけを見ると前の取り込みの検査が出ない | 示せない（起きた記録が無い） | 無し | 残課題 |
| V | Verifier: 反証 0 件 | — | — | — |
