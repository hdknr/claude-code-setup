# Issue #1590 — フォローアップ: hint の「設定のタグを変える」案内に、承認の取り直しと --external で明示する道を足す

作り直しの元: #1588

**利用者が不在の周**（cruise の子。出所: `/dev-loop:cruise 1583 --absent` の起動、2026-11-26T08:52:16Z。親 Issue #1583）。
この周を cruise に足したのは利用者の指示（2026-11-26「フォローアップは台帳にいれてこの cruise でまわして」）。
読み込んだ dev-loop は 2.26.0（`SKILL.md` 1970 行を読んだ。`wc -l` は 1969——末尾の行に改行が無い）。

直す線: `既定`（出所: cruise の台帳の確かめた線——親 Issue #1583 の `cruise:` の行を利用者が起動時に確かめた）。
台帳の確かめた線: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）。実機確認の線は無い。
版の上げ方: `screen-spec` を **patch**（0.12.2 → 0.12.3。案内の記述の不足を直す修正）。並行する周は無い（親の言）。マージの直前に上げ直すなら、main の先端の版から patch で 1 つ上げる。

Issue 本文（外部入力。作者は利用者本人。#1588 の確認の結果「推奨のまま」から親が立てたフォローアップ）から読んだ要件:
#1582（PR #1587）で `hint` と引数なしの `init` が出すようになった案内の 1 つ目の道「外部の profile を直してタグを付け、`shared/platform/settings.csv` のタグをそれにする」に、
(1) `shared/` を変えるので承認（サインオフ）を取り直し、基盤の層を読む版も変わること（platform-spec の `references/infra-profile.md`）、
(2) `shared/` を触らずに、直したタグを `--profile web-spa --external "org/guide org <新しいタグ>"` で明示する道、の 2 点を足す。PR #1587 の /code-review 2 パス目の CR2-2。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/write-screens.py` — `LayerBroken.advice`（と `LayerBroken` を作る `base_initial` が渡す値）・docstring の #1582 の行
- `plugins/screen-spec/references/profiles.md` — 「基盤の profile から引く初期値」の #1582 の行（決まりの原本）
- `plugins/screen-spec/skills/init/SKILL.md` — 手順 2 の「画面の層が決まりに合わない」の行。版の 2 行
- `plugins/screen-spec/skills/add/SKILL.md` — 版の 2 行
- `scripts/test-write-screens.py` — `LAYER_ADVICE`・docstring の 8・直したタグを `--external` で明示する陽性対照の試料・案内の 2 点を外す変異
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1590.md` — この計画ファイル

触らない:

- 読めないとき（clone が無い・タグが無い・形式の版・設定の形・`重ねる先`・行に写せない形）の `hint` と `init` の文言（#1582 の受入基準）
- `check-screens.py`・`plugins/spec-loop/`・`plugins/platform-spec/`・description（plugin.json・marketplace.json・SKILL.md の frontmatter）
- `CLAUDE.md`——`write-screens.py` の項は案内の文言を持たない
- #1589（層ファイルの中身の欠陥）——この周の範囲の外（親の言）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（spec-loop の正本ではない——このリポジトリはプラグインの配布元）

## 設計の判断

- 案内の文言は `write-screens.py` の `LayerBroken.advice` 1 か所で作り、`hint` と引数なしの `init` の両方がそれを出す（今と同じ）。
- 新しい案内（`<profile>` は層が名指す重ねる先、`<repo> <name>` は基盤の profile の設定の値）:
  `外部の profile を直してタグを付け、shared/platform/settings.csv の タグ をそれにする（shared/ の変更なので 2 つの承認を取り直し、基盤の層もそのタグの時点で読むことになる）か、shared/ を触らずに直したタグを --profile <profile> --external "<repo> <name> <新しいタグ>" で明示するか、--profile <profile> --external なし を渡す`
- 2 つ目の道に `repo`・`name` を実際の値で入れる——利用者が写して `<新しいタグ>` だけを替えれば渡せる。`LayerBroken` に `repo` と `name` を渡す。
- 明示の `init`（`--profile` か `--external` を渡す）は基盤の profile を読まない（`references/profiles.md` の「効くのは…両方省いたときだけ」）ので、設定のタグが古いままでも、直したタグを明示すれば書ける。
- 複製の数: 案内の文言は本体 1 か所・テストの期待 1 か所（`LAYER_ADVICE`）。散文は決まりの原本（`profiles.md`）1 行・`init` の SKILL.md 1 行・本体の docstring 1 行・テストの docstring 1 行。分けない（1 つの案内を足すだけ）。

## verify の受入基準

入口: `write-screens.py hint`・引数なしの `init`・明示の `init`（`--external` に直したタグ）・`check-screens.py`。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | Issue の入力（`GUIDE_LAYOUT` の `list,standard` → `list,wide`）で `hint` の出力に、承認（サインオフ）の取り直し（と基盤の層の版）と、直したタグを `--profile web-spa --external "org/guide org <新しいタグ>"` で明示する道の 2 つが出る | `hint` | `LayerBroken.advice` | 試料 `base-layer-default-outside-vocab`（`LAYER_HINT`。直す前の本体で赤）・変異 |
| 2 | 案内どおり、直したタグを `--external` で明示すると `init` が 0 で書け、直後の検査が 0（陽性対照: 基盤の設定はタグ v1 の壊れた層のまま、profile のリポジトリに直したタグ v2 がある） | 明示の `init` | 明示の引数は基盤の profile を読まない（既存） | 新しい試料（v1 では 4・v2 では 0 を同じ試料で） |
| 3 | #1582 の受入基準を破らない: 層の行の決まりで止まる profile では `hint` と引数なしの `init` が行き止まりでない案内を出し（#1571・#1581 の形）、`--profile web-spa --external なし` で 0 で書ける。読めないときの文言は変えない | `hint`・引数なしの `init`・明示の `init` | 既存の分岐を変えない | 既存の試料（`base-layer-*`・`base-no-clone`・`base-screen-layer-version-out-of-range`・`base-repo-without-slash`）と既存の変異 |
| 4 | 引数なしの `init` の止めた理由（4）にも同じ案内が出る | 引数なしの `init` | `LayerBroken.__init__` が `advice` を理由に入れる（既存） | 試料（`LAYER_INIT`） |
| 5 | 決まりの原本（`profiles.md`）と `init` の SKILL.md と本体の案内が食い違わない（2 点とも書く） | 文書 | 手で揃える | 関門の読み（機械の検査は無い） |

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（Verifier 1・2 パス目、/code-review 1・2 パス目。2 パス目が該当なしなら初回の 2 つ）。

この環境で証明できないもの（未証明）: なし——どれも一時の git リポジトリの試料で走らせて確かめられる。
生成物: なし（このリポジトリの生成物は drawio の書き出しと `SKILL.md` の測定値（dev-loop の設計 §8.2）。screen-spec の `SKILL.md` は測定の対象外——`skill-metrics.py --check` で確かめる）。
プロパティテスト: なし（案内の文言の追記で、入力の空間が広い不変条件が無い）。
差分テスト: なし（受入基準は振る舞いを変える——案内の文言が変わる。「振る舞いを変えない」を含まない）。

## 未解決の判断・確認待ち

（無し）

## 関門の進捗（再開点）

周の在り処:
- ブランチ: `issue/1590-external-tag-advice`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1590`
- 起点コミット: `6cd20a35`
- base: 参照 `origin/main` → `6cd20a357a80038fd876c709451932ebae4b6a97`

割り目（手順 4）: 割らない（cruise の周）

1 パス目の起点（0 行の判定。1 パス目の関門に渡した時点の HEAD）: `67bb352b`
1 パス目の報告のファイル: Verifier `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/60512778-ba8a-4b9c-afb8-fadbe195ec94/scratchpad/gate-1590-verifier-1-20261126T111925Z.md`・/code-review `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/60512778-ba8a-4b9c-afb8-fadbe195ec94/scratchpad/gate-1590-code-review-1-20261126T111925Z.md`（どちらも終わりの印つき）
- 関門 1 パス目を通した（HEAD `67bb352b`）——**Verifier（dev-loop:dev-loop-verifier・sonnet）反証 0 件・/code-review（high）指摘 7 件**（採否は下の表。直す 0・残課題 7）。
  どちらも `git status --porcelain` は前後同じ（計画ファイルだけ）。Verifier は verifier.md を 261 行読んだと報告（`wc -l` は 260——末尾の行に改行が無い）。
  /code-review は base の写しで新しい試料が赤になること・`if not explicit` を壊すと新しい試料の v2 の段が赤になることを独立に当てた。
- 差し戻し: なし（1 パス目の反証で手順 4 に戻った修正は無い）。
- **2 パス目: 該当なし**——理由: 1 パス目の指摘対応の差分 0 行（直す線は既定で、採否の表に「直す」の行が 0 件）。起点 `67bb352b`。判定の 2 本（`git diff 67bb352b -- ':(top)' ':(top,exclude)docs/plans/issue-1590.md'` が空・`git status --porcelain` は計画ファイルだけ）。
- **狭いパス: 該当なし**（2 パス目が無い）。
- 割り目（手順 6）: 2 パス目が無いので置かない。
交絡を潰した手順: 実験なし（試料の赤／緑は、直す前の本体で赤・直した本体で緑を同じ試料で見た——`base-layer-default-outside-vocab`・`base-layer-fixed-tag-explicit`・`base-layer-status-vocab-disjoint` は 6cd20a35 の本体で `hint` の案内が期待と違って赤）

```dev-loop-gates
周の base: 6cd20a357a80038fd876c709451932ebae4b6a97
関門: Verifier 1 67bb352b 反証=0
関門: /code-review 1 67bb352b 指摘=7
関門: 2 パス目 該当なし 67bb352b
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 読めないとき（clone が無い・タグが無い・形式の版・設定の形・`重ねる先`・行に写せない形）の文言 | 変えない | #1590 の受入基準 3（#1582 の受入基準）が「読めないときの文言は変えない」 |
| 明示の `init --external` が層の行の決まりで止まるときの文言 | 変えない | #1582 の周で決着（明示の `init` は案内を出していない）。#1590 の範囲は `hint` と引数なしの `init` の案内 |
| `<新しいタグ>` を本体が推さない（profile のリポジトリのタグを探して直ったものを名指さない） | 推さない | 直すのは利用者で、まだ直したタグが無いことがふつう。案内は形を示すだけ |
| #1589（層ファイルの中身の欠陥） | 触らない | この周の範囲の外（親の言） |
| 2 つ目の道で `--external` の値を `"…"` で囲んで出す | 囲む | 値が空白を含む 3 語なので、シェルで 1 つの引数として渡すには囲みが要る（init の SKILL.md の手順 3 のコマンドと同じ形） |

### 1 パス目の採否の表（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1（important）: 1 つ目の道にだけ「承認を取り直す」と添え 2 つ目を「shared/ を触らずに」と対にするので、2・3 つ目の道なら取り直さずに済むと読める。init はどの道でも requirements/ を書き、check-signoff.py は requirements/ も比べる | 示せない（読み。サインオフ済みの版で init を走らせて取り直しになる形を走らせていない。案内は 2・3 つ目の道で承認が要らないとは書いていない） | 無し（1 は Issue の 2 点が出ることで満たす。5 は 3 か所が同じことを書く） | 残課題 |
| CR1-2: 2 つ目の道で基盤の設定（v1）と画面の設定（v2）のタグが割れることを言わない | 示せる（試料 base-layer-fixed-tag-explicit の終わりの状態） | 無し | 残課題 |
| CR1-3: 「同じ外部の profile を明示しても止まる」と同じリポジトリ・名前を明示する道を並べて自己矛盾に読める | 示せない（文の読み。違いはタグで、案内は「直したタグ」と言う） | 無し | 残課題 |
| CR1-4: init の SKILL.md が <新しいタグ> を利用者に訊く・推さないと書かない | 示せない（スキルが推した記録は無い） | 無し | 残課題 |
| CR1-5: 1 つ目の道が infra.csv の profile の行と表の行を新しいタグに合わせて直すことに触れない | 示せない（読み） | 無し | 残課題 |
| CR1-6: repo・name に `"`・`$`・バッククォートがあると写したコマンドが崩れる（Verifier も同じ所見を反証でないと添えた） | 示せない（実物の設定でその形は無い） | 無し | 残課題 |
| CR1-7: 周のコミットに Fixes #1590 が無い | 示せる（git log） | 無し | 残課題（PR 本文に `Fixes #1590` を書く——squash のマージのコミットに入る） |

### 振り分け（found-lines.md。周の途中の課題 = 外に出す）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| CR1-1 承認の取り直しが 1 つ目の道だけに見える | #1590 /code-review 1 パス目 | 示せない | 記録だけ（文言。案内は他の道で承認が要らないとは言わない。迷ったら記録だけ） |
| CR1-2 タグの割れ | #1590 /code-review 1 パス目 | 示せる（試料） | 記録だけ（検査は通り、利用者が受け取る結果は誤っていない——文言の不足） |
| CR1-3 「同じ外部の profile」の読み | #1590 /code-review 1 パス目 | 示せない | 記録だけ（文言） |
| CR1-4 新しいタグを推さない | #1590 /code-review 1 パス目 | 示せない | 記録だけ（文言） |
| CR1-5 profile の行を直すこと | #1590 /code-review 1 パス目 | 示せない | 記録だけ（文言。止めるのは check-infra-profile.py で、黙って通らない） |
| CR1-6 シェルの特殊文字 | #1590 /code-review 1 パス目・Verifier 1 パス目 | 示せない | 記録だけ（まれな書き方） |
| CR1-7 Fixes #1590 | #1590 /code-review 1 パス目 | 示せる | 捨てる（PR 本文の Fixes #1590 で満たす） |

## 手順 8 の記録

- 切り分けの層: 焼き戻す学びなし（案内の文言の追記で、仕事の切り方に戻す偏りは無い）。
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: なし
- 効いた行: なし
- 効いた行: なし
- 効いた行: なし

- この周の起票: 0 件（不在の周——起票は訊かず、周の途中の課題は found-lines.md の振り分けで PR コメントに残す。確認の Issue は立てない——立てるのは親）
