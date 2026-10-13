# Issue #205 — dev-loop: 手順 4 の「下の／上の〜の項」が references/resume.md への移設後も更新されていない

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 4 の散文の指し先（F1 の各箇所）・「新規の周では読まなくてよい」の例外・版
- `plugins/dev-loop/skills/dev-loop/references/resume.md` — 冒頭の「新規の周では読まなくてよい」の例外・切れた指し先 1 件（385 行）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.37.0 → 1.37.1）
- `.claude-plugin/marketplace.json` — 版
- `scripts/check-skill-pointers.py` — 散文の指し先（`上の「X」` `下の「X」` と `` `references/x.md` の「X」 ``）を見る
- `scripts/test-check-skill-pointers.py` — 上の回帰テスト（変異テストを含む）
- `CLAUDE.md` — `check-skill-pointers.py` の説明（散文の指し先も見る）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-205.md` — この計画ファイル

触らない:

- #204 の F2〜F8（終了コード 7・経緯の語りの削除など）——別の指摘。この周は F1 だけ
- 手順 4 以外の「上項／下項」（「上の『…』」の形でない、項を名指ししない指し先）——機械で見られない形として記録に留める
- `prepare-worktree.sh` の挙動

**複製の数**: 「`resume.md` は新規の周では読まなくてよい」を述べている箇所が 3 つ
（`SKILL.md:211`・`SKILL.md:598`・`resume.md:9`）。**分けない理由**: 例外を 1 箇所にだけ書くと、
残りの 2 箇所が例外の無い文として読まれる。歯止めの説明は `check-skill-pointers.py` の docstring と
`CLAUDE.md` の 2 箇所（`CLAUDE.md` は docstring を正とする形で短く書く）。

## 2. デプロイ経路

- `plugins/`：プラグインの配布物。版を上げて main にマージすれば、利用者が `plugin update` で受け取る。
- `scripts/`・`CLAUDE.md`：CI の歯止め。
- `docs/`：main への push で GitHub Pages に載る（計画ファイルと生成ブロック）。破壊的・不可逆な操作は無い。

## 3. 受入基準

**I1. 手順 4 の散文の指し先が、実在する項を名指ししている。**

| 経路（Issue が挙げた箇所・main の行番号） | 期待 |
| --- | --- |
| S1 `SKILL.md:425`「途中から再開する周」の `EnterWorktree` の項 | `references/resume.md` の実在する項を「〜」の形で名指しする |
| S2 `SKILL.md:459-461` 新規の周は「下のブランチ名の確認と改名の項へ」 | `SKILL.md` に実在する行き先（`prepare-worktree.sh` で入り直す）を名指しする |
| S3 `SKILL.md:464` 下の「改名のコマンドは…」項 | `references/resume.md` の「改名のコマンドは『いまブランチの上にいるか』で分岐する」項 |
| S4 `SKILL.md:548` 上の `EnterWorktree` の項 | 一次ソース（道具の説明文）を名指しする |
| S5 `SKILL.md:552` 下の「規約どおりの名前で最初から切る」形 | `prepare-worktree.sh` の形。手で書く形は `references/resume.md` の実在する項 |
| S6 `SKILL.md:562` 実測。下の `EnterWorktree` の項 | `references/resume.md` の実測がある項 |
| S7 `SKILL.md:575` 下の「取れる道」 | 実在する文言（「取れるのは次のどちらか」） |
| S8 `SKILL.md:617` 直前の項のブランチ名の規約確認 | 新規の周／再開の周それぞれの実在する確認を名指しする |
| S9 `resume.md:385` 上の「裸のブランチ名を渡す」 | 実在する文言（「渡すのは『裸のブランチ名』」） |

**I2. 新規の周が辿る分岐が、「読まなくてよい」とされたファイルの中身に依存しない。依存するなら明示する。**

| 経路 | 期待 |
| --- | --- |
| N1 新規の周で場所が違う（S2） | `SKILL.md` の中だけで行き先が決まる |
| N2 新規の周で場所は合っていて名前だけ違う（S3） | `resume.md` の改名の項を読むことが明示され、`SKILL.md:211`・`SKILL.md:598`・`resume.md:9` の「読まなくてよい」がこの例外を述べている |
| N3 新規の周の、それ以外の手順 4 の指し先（S1・S4〜S8） | 根拠を示すだけで、行為が `resume.md` の中身に依存しない |

**I3. 散文の指し先を機械で見る（`check-skill-pointers.py`）。**

| 経路 | 期待 |
| --- | --- |
| M1 `上の「X」`／`下の「X」` の X が同じファイルに無い（指し先自身の文字列は数えない） | 赤 |
| M2 `` `references/x.md` の「X」``／`` `SKILL.md` 手順 N の「X」`` の X が指したファイルに無い | 赤 |
| M3 X の中の『』と、本文の「」・太字・バッククォート・改行の違い | 一致として扱う（緑） |
| M4 フェンスの中の「上の「X」」 | 見ない |
| M5 修正後のリポジトリ | 緑 |
| M6 修正前（main）の本文に新しい検査を当てる | 赤（S3・S5・S7・S9 を報告） |
| M7 修正前の検査（main の `check-skill-pointers.py`）を S3 を戻した本文に当てる | 緑（＝これまで見えていなかった。陽性対照） |

守らないこと（docstring に書く）: 位置（上か下か）が合っているか・X が項の見出しか本文の一部か・
「上項」「直前の項」「上の `EnterWorktree` の項」のように X を「」で書かない指し先。

**I4. 版と歯止め**: 3 箇所の版が 1.37.1 で揃い、`python3 scripts/check-all.py` が全部緑、PR の CI が緑。

**生成物**: `skill-metrics.py` の §8.2 生成ブロック（`SKILL.md` の行数が変わるので該当）——
`--check` が緑であること。図は触らないので該当なし。

### 証明の手段

- I1・I2: `grep` と目視。I3 の検査が S1〜S9 のうち「」の形のものを機械で見る。
- I3: テストに M1〜M4 のケースを足し、変異（新しい検査を外す）で赤になることを見る。M6・M7 は実際に走らせる。
- I4: `check-all.py`・`gh pr checks`。
- **未証明**: なし。

## 4. 未解決の判断

- なし。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/205-prose-pointers`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-205`・
  起点 `8df3a56`・base 参照 `origin/main` → `8df3a56ad5384771869eb1799d7f87a0b9a603b8`
- 実装: `25fe435`（`check-all.py` 32/32 緑）。M6（新しい検査 × main の本文 → 4 件で赤）・
  M7（main の検査 × main の本文 → 緑）を実際に走らせた
- 関門: **1 パス目 済**——Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 1 件（V1）、
  `/code-review`（high）指摘 8 件（R1〜R8）。採否は §6 の表（直す: R1・R4／残課題: 他 7 件）
- 1 パス目の指摘対応: R1（`の` と `「` の間の改行を跨ぐ。試料 2 つと変異 1 件を追加）・R4（`SKILL.md` の新規の周の行き先）。
  `check-all.py` 32/32 緑。R1 の陽性対照: `.git` を持たない複製で S1 の指し先の文言を壊す → 新しい検査は rc=1、
  変異（`NO = r"の"`）は rc=0
- 割り目（手順 6・2 パス目の前）: 人間が「ここで割る」を選んだ（2026-10-13）。再開は 2 パス目から
- 次: **2 パス目**（手順 5 の Verifier と手順 6 の `/code-review` の両方。指摘対応の差分を重点に、受入基準はまるごと）
- 反証: 1 パス目 Verifier 1 件（残課題）。手順 4 への差し戻しは R1・R4 の 2 件
- 交絡: M6・M7 が陽性対照と陰性対照の組（同じ main の本文に、新旧の検査を当てた）。R1 は上の陽性対照
- 割り目（手順 4）: 人間が「ここで割る」を選んだ（2026-10-13）。再開は手順 5 から（1 パス目の Verifier と `/code-review`）

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| #204 の F1 の置き換え文案をそのまま使うか | 一部だけ採る | 案の S2 は終了コードの一覧に触れておらず、S4 は `resume.md` を指す——新規の周の分岐を `resume.md` に依存させない（I2）ため一次ソースを指す |

### 1 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | `の` と `「` の間で改行した散文の指し先を拾わない（S1・S5・S6・`SKILL.md:460`）（`/code-review`） | 示せる——複製で S1・S5・S6 の指し先の文言を壊しても rc=0、S3 を壊すと rc=1 | I3（S1〜S9 の「」形を機械で見る） | 直す |
| R2 | `` `../../references/x.md` の「X」 `` を拾わない（spec-loop）（`/code-review`） | 示せる——複製で `tree.md` の「スライドの置き場所」を変えても rc=0 | 無し（I3 の経路は dev-loop の S1〜S9 と `references/x.md` の形） | 残課題 |
| R3 | `以下の「…」` `画面上の「…」` を指し先と誤認する（`/code-review`） | 作った入力でだけ示せる——いまのリポジトリは緑（M5） | 無し | 残課題 |
| R4 | 新規の周の「場所が違う」の行き先で、項に「戻る」と読めて走らせ直すと終了コード 3 で `resume.md` へ送られる。0 以外の次の手も無い（`/code-review`） | 示せる——作った後に `prepare-worktree.sh` を走らせ直すと 3 を返し、出力は `find-cycle.py`／`references/resume.md` を指す | I2（N1: `SKILL.md` の中だけで行き先が決まる） | 直す |
| R5 | 照合相手の本文がフェンスの中の文言も数える（`/code-review`） | 示せない（実例なし） | 無し | 残課題 |
| R6 | M7 は旧検査が散文を見ないので常に緑で、判別していない（`/code-review`） | ——（計画の記録についての指摘） | 無し（M6 は新検査 × main の本文で 4 件を赤にしている） | 残課題 |
| R7 | 対象ファイルを指し先ごとに読み直す（効率）（`/code-review`） | 示せない（遅さの実害なし） | 無し | 残課題 |
| R8 | `normalize` が引用の `>` や `_強調_` を外さない（`/code-review`） | 示せない（実例なし） | 無し | 残課題 |
| V1 | S3 を元の形に戻しても、`SKILL.md:213` に同じ文言が地の文で在るので緑のまま（Verifier） | 示せる——現行の本文で S3 だけを戻して rc=0 | 無し（M1 は「X が同じファイルに無い」。位置は守らないと docstring に明記） | 残課題 |
