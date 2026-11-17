# Issue #1153 — screen-spec: prose.md と check-screens.py の docstring が、profile の共通仕様の節を検査することと食い違う

**不在の周である**——cruise（親 Issue #1168）の子として回す。出所: `/dev-loop:cruise 1168 --absent` の起動（2026-11-17）。
確かめた線（台帳 `issue-1168`。出所: cruise の確かめた線（台帳 issue-1168）。不在の周で、起動は `/dev-loop:cruise 1168 --absent`、2026-11-17）:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。
#1153 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い。親は #1081）。
この周はマージしない（親がする）——PR を作り、PR 側の CI が通るのを見るところまで。手順 8 は計画ファイルに書くところまで。
他の周（#1144・#1148・#1149・#1152）が並行している。重い検査は run-serial 越しに回す。

## 周の在り処

- ブランチ: `issue/1153-prose-docstring-profile-sections`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1153`
- 切った元の参照: `origin/main`（解決した SHA = base: `05aa0d5c36b012abe57239ba0f288a47f74083fc`）
- 起点コミット: `05aa0d5`

## 変更範囲

触る:

- `plugins/screen-spec/references/prose.md` — 「共通仕様」の節の 1 行（検査は共通仕様の節を見ない）を、profile の節を見ることと合わせる
- `plugins/screen-spec/scripts/check-screens.py` — docstring の「守らないもの」の表の 1 行だけ（検査の中身は触らない）
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版（0.6.1。patch）
- `.claude-plugin/marketplace.json` — 同じ版
- `plugins/screen-spec/skills/init/SKILL.md` — 版の 2 行
- `plugins/screen-spec/skills/add/SKILL.md` — 版の 2 行
- `docs/plans/issue-1153.md` — この計画

触らない:

- `check-screens.py` の検査の振る舞い（`check_profile_section` など。Issue の受入基準）
- `references/profiles.md`・`references/tables.md`（すでに profile の共通仕様の節を検査すると書いている）
- テスト（`scripts/test-check-screens.py`。振る舞いを変えない・記述だけを直すので試料は足さない）
- 公開ページ・README

複製の数: 「共通仕様の節の検査」を述べる箇所は、原本 `references/profiles.md`（「足すもの」の 3・共通仕様の小見出し）、`references/prose.md` の「共通仕様」、`check-screens.py` の docstring の 2 か所（先頭の「profile があれば」と守らないものの表）。
食い違っていたのは後ろの 2 か所（Issue の 2 記述）。分けない理由: 直す記述は 2 つで、どちらも原本 `profiles.md` を指して合わせる。1 つの周で足りる。

依存の追加・更新: なし

生成物: なし（生成物なし。図・スナップショット・生成コードは触らない）。

版の上げ方: PR ごとに版を上げるリポジトリ。この周は `screen-spec` を patch（0.6.0 → 0.6.1）。マージの直前に main の先端の版から patch を 1 つ上げ直す（`marketplace.json`・`plugin.json`・`SKILL.md` 2 ファイルの 2 行）。
同じプラグインを触る他の周（#1148・#1152 ほか）が先にマージされたら取り込んで上げ直す。

## 直す線

直す線: 既定（出所: cruise の確かめた線（台帳 issue-1168））。

## 受入基準（verify）

不変条件:

- A. profile を選んだ案件では、共通仕様の profile の節（`## 実現方式: <profile>`）の小見出しが検査されることを、記述が言う（言わないと、記述に従って小見出しを空にした利用者が止められる）
- B. 検査の振る舞いは変わらない（記述を振る舞いに合わせる）
- C. profile を選ばない案件（`未設定`）では共通仕様の profile の節を求めないことと、core の節は空でよいことを、記述が崩さない

| # | 受入基準 | 判定の手段 |
| --- | --- | --- |
| 1 | `prose.md` の共通仕様の記述が、profile を選んだ案件では共通仕様の profile の節（小見出し）を検査することと合う | prose.md を読み、`check-screens.py` の `check_profile_section`・試料 `web-spa-common-subsection-missing` の振る舞いと照らす |
| 2 | `check-screens.py` の docstring の「守らないもの」が、同じことと合う | 同上 |
| 3 | 検査の振る舞いを変えていない | 実行コードの差分が 0 行（docstring 内の行のみ）。`git diff` で関数・定数の行が変わらないこと |

経路（その記述を述べている入口を、grep ではなくページを開いて数えた）: 共通仕様の節の扱いを述べる場所は `profiles.md`（原本・合っている）・`tables.md`（検査の表。合っている）・`prose.md` の「共通仕様」（直す）・
`check-screens.py` の docstring の先頭の「profile があれば」（合っている）と「守らないもの」の表（直す）・`profiles/web-spa/common.md` の雛形（記述でなく雛形）。
未証明: なし。BLOCKED: なし。

## 決めたこと

- 「検査は共通仕様の節を見ない」を、「profile の節以外は見ない・profile の節の小見出しは見る」に直す。core の節と案件で足した節は空でよいまま。

## 関門の進捗（再開点）

- 割り目: 割らない（cruise の周）。
- 実装: 完了。1 パス目の関門に渡した終点: `500a4c138b4a19098515ce6218e29b255cfb63fd`。check-all.py 91/91 緑（run-serial 越し）。
- 1 パス目: Verifier 反証 1 件（R1）・/code-review 指摘 5 件。採否は下の表。
- 2 パス目の指摘対応の起点（1 パス目の関門に渡した HEAD）: `500a4c138b4a19098515ce6218e29b255cfb63fd`。指摘対応の終点: `91a6501e0ed0cb2a4abf5a8e6fe3d4a0b9118189`。
- 2 パス目: Verifier 反証 1 件（V2-R1）・/code-review 指摘 5 件（CR2-1〜5）。採否は下の表。
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `91a6501e0ed0cb2a4abf5a8e6fe3d4a0b9118189`。
- 狭いパス: 起点 `91a6501e0ed0cb2a4abf5a8e6fe3d4a0b9118189`・終点 `81bdd49e20f39b9606af425c8d3149fff934bcd3`。Verifier（別ティア）反証 0 件。素通りした変異 4 本（prose.md:40 を狭く・広く・条件落としに崩した文）は、記述を見る機械の歯止めが無いことによる（陽性対照: 照合が prose.md を読むことは別の変異で確認）。受入基準 1 は目で読む判定で、この周は試料を足さない。
- 割り目: 割らない（cruise の周）。

```dev-loop-gates
周の base: 05aa0d5c36b012abe57239ba0f288a47f74083fc
関門: Verifier 1 500a4c138b4a19098515ce6218e29b255cfb63fd 反証=1
関門: /code-review 1 500a4c138b4a19098515ce6218e29b255cfb63fd 指摘=5
関門: Verifier 2 91a6501e0ed0cb2a4abf5a8e6fe3d4a0b9118189 反証=1
関門: /code-review 2 91a6501e0ed0cb2a4abf5a8e6fe3d4a0b9118189 指摘=5
関門: 狭いパス 91a6501e0ed0cb2a4abf5a8e6fe3d4a0b9118189 81bdd49e20f39b9606af425c8d3149fff934bcd3 反証=0
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

1 パス目の採否（直す線: 既定）:

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-R1: prose.md:40 の「`common.md` は節を見ない」が偽 | 示せる（Verifier が web-spa の試料で小見出し欠落・空・理由なし N/A を実行し exit=1） | 1・A | 直す |
| CR-1: prose.md:90 が「common.md を置いたときだけ」に触れない | 示せない（41 行目と profiles.md が「置いたなら」を持つ。省略であり偽ではない） | 無し | 残課題 |
| CR-2: check-screens.py:56 の行が「置いたときだけ」に触れない | 示せない（同じ行が「上の『profile があれば』」を指し、そこに「置いたときだけ」がある） | 無し | 残課題 |
| CR-3: prose.md:90 が節そのものの有無・重複・位置に触れない | 示せない（記述は小見出しの検査だけを述べ、偽ではない。節の要件は profiles.md が原本） | 無し | 残課題 |
| CR-4: prose.md:90 の 1 行が長い | 示せない（読みにくさの指摘） | 無し | 残課題 |
| CR-5: 計画ファイルの空欄と関門の記録 | この表と記録で埋めた（計画ファイルは関門の検査対象ではない） | 無し | 捨てる（埋めた） |

## 手順 8 の記録

- 切り分けの層: 学びなし（記述を振る舞いに合わせる 1 行の直しで、切り方で防げる形ではない）
- 焼き戻す学びなし。
- この周の起票: 0 件

## 2 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-R1: prose.md:40 の「…小見出し…だけ」が検査の範囲を狭く言う | 示せる（Verifier が common.md の profile の節が無い・2 つあるで exit=1 を実行） | 1・A | 直す（狭いパスに当てる） |
| CR2-1: prose.md:90 が「置いたときだけ」に触れない | 示せない（省略。CR-1 と同じ） | 無し | 残課題 |
| CR2-2: prose.md:40 の「だけ」が狭い | V2-R1 と同じ（直す） | 1・A | 直す（V2-R1 に含む） |
| CR2-3: check-screens.py:56 の行が守る内容を混ぜる | 示せない（表の書き方の好み。節は守らないが profile の節だけ見ると書いてあり偽ではない） | 無し | 残課題 |
| CR2-4: prose.md:90 の「だけ」と後半の係り | 示せない（読み違えの可能性の指摘） | 無し | 残課題 |
| CR2-5: 90 行目が `N/A。実現方式が未定` の印の例外に触れない | 示せない（79 行目と profiles.md に在る。省略） | 無し | 残課題 |
