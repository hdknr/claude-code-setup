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
- 実装: 完了（コミット前に書く）。

```dev-loop-gates
周の base: 05aa0d5c36b012abe57239ba0f288a47f74083fc
```

## 既知の限界・決着済みの論点

（関門が挙げたものの採否の表をここに書く）

## 手順 8 の記録

- 切り分けの層: 学びなし（記述を振る舞いに合わせる 1 行の直しで、切り方で防げる形ではない）
- 焼き戻す学びなし。
- この周の起票: 0 件
