# Issue #194 — orca プラグインを追加する（cmux プラグインの Orca 版）

## 1. 変更範囲

触る:

- `plugins/orca/` — 新設（`plugin.json`・`skills/orca/SKILL.md`・`README.md`）
- `.claude-plugin/marketplace.json` — orca のエントリを追加
- `docs/plugins/index.md` — 一覧表・`## orca` 節・素のスキルの列挙
- `docs/part3-post-setup.md` — 一覧表・インストール例・使用例
- `docs/usage/advanced-extensions.md` — 配布プラグインの列挙
- `CLAUDE.md` — プロジェクト構成に `orca/` を追加
- `docs/plans/issue-194.md` — この計画ファイル

触らない:

- `plugins/cmux/` — 同じ部分一致の穴（下の F1）があるが、この周の受入基準の外。残課題にする
- `scripts/` — 歯止めは変えない（`link-skills.sh` は `plugins/*/skills/*` を走査するので orca も拾う）

**経緯**: この周は dev-loop を使わずに実装・PR（#195）まで進め、**そのあとで dev-loop に引き継いだ**。
計画ファイルは引き継いだ時点で初めて書いた。**1〜4 は引き継ぎ時に書き、実装済みの差分に当てている。**

**複製の数**: 同じことを述べている箇所は次のとおり。

| 内容 | 箇所 | 数 |
| --- | --- | --- |
| 版 | `marketplace.json` / `plugin.json` / `SKILL.md`（2 行 1 組） | 3（CI が見る） |
| 紹介文（description） | `marketplace.json` / `plugin.json`（同文）・`SKILL.md` frontmatter（別目的） | 3（CI が共変を見る） |
| モード表（3 行） | `plugins/orca/README.md` / `docs/plugins/index.md` | 2 |
| 一覧の 1 行 | `docs/plugins/index.md` / `docs/part3-post-setup.md` / `docs/usage/advanced-extensions.md` / `CLAUDE.md` | 4 |
| 前提（Orca・`orca` CLI・`gh`・`EnterWorktree`） | `README.md`（本体）/ `docs/plugins/index.md`（列挙して README を指す） | 2 |

**分けない理由**: cmux と同じ構成で、**cmux が既に同じ複製を持っている**。
ここだけ寄せると 2 つのプラグインのページ構造が食い違う。寄せるなら cmux と一緒に別の周で行う。

## 2. デプロイ経路

- **main へのマージで 2 経路に乗る**: (a) GitHub Pages（`docs/` の変更。`docs.yml` が自動デプロイ）、
  (b) マーケットプレイス（`plugins/` と `marketplace.json`。利用者が `plugin update` で取る）。
- 破壊的・不可逆な操作は無い。

## 3. 受入基準

### 不変条件と、それを破りうる経路

**I1. `/orca <n>` は、番号 `<n>` の Issue/PR を内蔵ブラウザの前面に表示する。他のタブの内容を壊さない。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 同じ URL のタブが無い | 新しいタブを作る | `orca tab create --url` |
| P2 同じ URL のタブがある | そのタブを再利用し（リロード）、前面に出す | `orca goto --page` ＋ `orca tab switch --page` |
| P3 **番号が前方一致する別のタブがある**（`/issues/194` のタブがあって `/issues/19` を開く） | **再利用しない**（新しいタブを作る） | URL の一致を「完全一致、または直後が `/` `#` `?`」に限る（F1） |
| P4 同じ URL の下位ページ（`/pull/12/files`、`#issuecomment-…`）のタブ | 再利用してよい | 同上（直後が `/` `#` `?`） |
| P5 タブが 1 枚も無い・`tab list` が失敗する | 新しいタブを作る（失敗を再利用と読まない） | 空出力で `tab create` に落ちる |
| P6 PR モード（`-w` / `-r`）の URL | `gh pr view --json url` の URL で同じ規則 | 同じ共通手順を通る |

**I2. `-n` は現在の worktree に新しいターミナルタブを作り、現在のディレクトリへ cd する。**

| 経路 | 期待 |
| --- | --- |
| P7 cwd が worktree の根 | 新しいタブが同じ場所にいる |
| P8 cwd がサブディレクトリ | cd でそこへ移る |
| P9 cwd に空白を含む | 単引用符で囲んでいるので移る |

**I3. Orca のランタイムに届かないときは、何も操作せずにエラーで止まる。**

| 経路 | 期待 |
| --- | --- |
| P10 `orca` が `PATH` に無い | 判定が非ゼロ |
| P11 Orca は在るがランタイムに届かない（`result.runtime.reachable` が偽） | 判定が非ゼロ |
| P12 届く | 判定がゼロ |

**I4. 配布の整合**: 版が 3 箇所で揃い、`check-all.py` が全部緑、PR 側の CI も緑。
カタログの description と `plugin.json` の description が同文。

**I5. 文書の主張が事実である**: `SKILL.md`・`README.md`・docs に書いた Orca のコマンド・フラグ・
JSON の項目名が、実在の `orca` CLI（1.4.223）の挙動と一致する。

### 必須要件の掛け算

受入基準 I1〜I5 × 関門（Verifier・`/code-review`）× パス（1・2）= **4 つの受け渡し**。
既知の限界（§6）も同じ 4 つに渡す。

### 検証で証明できるもの

- I1 P1〜P5: 実機の Orca（1.4.223）で、手順の bash をそのまま流してタブの一覧を見る
- I2 P7〜P9: 実機で `terminal create` → `send` → `terminal read` で cwd を見る
- I3 P10〜P12: `PATH` から外した実行・偽の `orca` を置いた実行・素の実行
- I4: `check-all.py`・`gh pr checks`
- I5: `orca <cmd> --help` と実際の JSON 出力との突き合わせ

### この環境では証明できないもの（未証明）

- **Orca の他の版での挙動**。手元にあるのは 1.4.223 だけ。JSON の形（`result.runtime.reachable`
  など）が版で変わるかは分からない。
- **Linux・Windows の Orca**。手元は macOS だけ。

### 受入基準に入れないもの（付随の主張）

- `-w` / `-r` の worktree 経路（`EnterWorktree` → `gh pr checkout` → `gh pr diff`）は、
  **cmux と同じ文面で Orca 固有の部分が無い**。通しでは回していない。PR 本文にそう書いてある。

### 生成物

**該当なし**。この差分は drawio の図にも、`skill-metrics.py` が測る dev-loop の `SKILL.md` にも触れない。
**確認として** `check-diagram-freshness.py` と `skill-metrics.py --check` を回す（`check-all.py` に含まれる）。

## 4. 未解決の判断

- worktree を Orca 管理の `orca worktree create --pr <n>` に寄せるか（Issue の「未決」）。初版は cmux に揃える。人間が決める。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/194-orca-plugin`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/orca-plugin`、
  起点コミット `5114914`（引き継ぎ時の HEAD。F1 の修正後の HEAD は `f023950`）、
  base は `origin/main` の merge-base = `86b33d953c3d1f5f75ea435ef3be404305b3b1ff`。PR #195。
- 関門:
    - **Verifier 1 パス目: 済**（sonnet。1 度セッション終了で報告なしに止まり＝欠票、同じ体を再開して完走）。
      **反証 0 件**、観察 4 件（V1〜V4）
    - **`/code-review` 1 パス目: 済**（high）。**指摘 9 件**（CR1〜CR9）
    - **1 パス目の指摘対応: 済**（F3・F4・CR1・CR3・CR5・CR6 を直した。採否は下の表）
    - **残り: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方**
    - 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: 2 パス目の報告が揃った時点で書く
- 反証・差し戻し: 実機確認で 3 件（F2〜F4）、関門で 13 件（V1〜V4・CR1〜CR9）。手順 4 へ差し戻して 6 件を直した
- 指摘対応後の実機確認（SKILL.md の bash ブロックを**機械的に抜き出して**流した——手で写すと CR1 の経路を通らないため）:
  前提の確認 = worktree の中 0・Orca 管理外 1・`orca` が `PATH` に無い 1（P10）・偽の `orca` で reachable 偽 1（P11）／
  **陽性対照** reachable 真の偽 `orca` 0。`-n` = サブディレクトリから新しい端末のプロンプトが `orca %`（P8）・
  Orca 管理外では rc=1 で端末の数が 8 のまま（F4）。共通手順 = `/issues/194` を 2 回でタブ 2→3（P1・P2）・
  `https://` で始まらない URL で rc=1。`check-all.py` 30/30 緑
- 交絡: 2 件見つけて潰した（下の「実機確認」）
- 実機確認（2026-10-09、Orca 1.4.223、macOS。手順の bash をそのまま scratchpad のスクリプトに写して流した）:
    - P12 緑（`status` 判定 rc=0）。P1 緑（タブ 0 → 1、作成）。P2 緑（同じ URL で件数が増えず、
      **非アクティブにしてから開き直して前面に出る**ことも確認——1 枚目のときは「前面」が自明だったので測り直した）。
    - P3 緑（`/issues/194` があって `/issues/19` → 194 のタブは無傷で新規作成）。
      **陽性対照**: 同じタブ一覧に旧い `target in url` を当てると 194 のタブを返した。
    - P4・P6 緑（`gh pr view 195 --json url` の URL。タブを `/pull/195/files` に移してから開いて再利用）。
    - P7・P8・P9 緑（新しいターミナルで `echo PWD_IS=$(pwd)` が期待のパス）。
      **交絡 1**: P9 を最初は Orca 管理外の scratch で回し、`terminal create` が失敗したのに
      後続が別のターミナルで動いて「緑」に見えた → worktree の中に空白入りのディレクトリを作って測り直した（F4 の発見）。
      **交絡 2**: 迷い込み先を `grep` で探したとき、このセッション自身の端末が自分のコマンド文字列を表示していて当たった
      → 空の handle が何に解決されるかを `terminal read --terminal ""` で直接見て確定した。
    - **副作用**: F4 の再現で、利用者の別プロジェクト（`blogs`）の端末に `cd` と `echo` が入った。人間に報告済み。
    - P10・P11 は未（Verifier に偽の `orca` で当てさせている）
- 実装: F1 の修正をコミット済み（`check-all.py` 30/30 緑）
- 割り目（手順 4 完了時）: 提案した → 「ここで割る」が選ばれた。次は手順 5 の Verifier 1 パス目から（関門は 0 件通過）
- 割り目（2 パス目の前）: 提案した → **「ここで割る」が選ばれた**。
  **次は Verifier 2 パス目（当て直し）と `/code-review` 2 パス目の両方**。どちらも未着手。
  渡す受入基準は §3、既知の限界と採否は §6（1 パス目の指摘 13 件の採否を含む）
- 再開（2026-10-09）: `find-cycle.py` で当たり、ブランチ・HEAD `5f9e2e0`・base の祖先関係を確認。
  - **Verifier 2 パス目: 済**（sonnet、`dev-loop:dev-loop-verifier` が起動したと報告。ツールは Read・Bash 等で書き込みなし）。
    **反証 0 件**、軽微な注記 2 件（M1・M2）。`check-all.py` 30/30・PR CI 緑を独立に確認
  - **`/code-review` 2 パス目: 済**（high）。**指摘 10 件**（CR2-1〜CR2-10）
  - 2 パス目の指摘対応: 直すのは CR2-4 の 1 件。ほかに**検証のやり直し**が 2 件（CR2-3・CR2-5。コードは変えず、HEAD で測り直す）
  - 狭いパスの起点: この行を書いたコミット（指摘対応の直前の HEAD）。SHA は下の「狭いパス」の行に写す

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| F1 タブ再利用の部分一致（`target in url`） | **直す**（引き継ぎ時に自分で発見） | 実物で失敗を示せた: `/issues/194` のタブがある状態で `/issues/19` を開くと 194 のタブを再利用して上書きした。I1 P3 を破る |
| cmux にも F1 と同じ穴がある | **残課題**（この周では直さない） | cmux はこの周の変更範囲の外 |
| worktree を `EnterWorktree` のままにする | 初版は cmux に揃える | Orca 管理の worktree には現セッションが入らない。人間が決める（§4） |
| `-n` の cd で、パスに単引用符を含むと壊れる | 残課題 | cmux は引用すらしていない。単引用符を含むパスは実例が無い |
| 計画ファイルを実装の後に書いた | 事実として記録する | dev-loop への引き継ぎがマージ前に決まったため |

### 指摘の採否（1 件 1 行）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| F2 Issue モードに PR の番号を渡すと、GitHub が `/issues/19` → `/pull/19` に転送するので、呼ぶたびにタブが増える | 示せる: `/issues/19` を 2 回開いて `/pull/19` のタブが 2 枚になった（実機確認） | 無し——I1 は「表示する・他のタブを壊さない」で、どちらも守られている。P2 は「同じ URL のタブがある」に限っている（転送先は別の URL）。cmux も同じ挙動 | 残課題 |
| F3 文書（README・docs）の「現在の worktree に新しいターミナルタブを作成」が事実と違う。`--worktree active` は **cwd を含む Orca 管理の worktree** に解決され、`.claude/worktrees/` 配下からはメインのチェックアウトに付く | 示せる: P7 の `terminal create` の結果の `worktreeId` がメインのチェックアウト。`orca worktree list` に `.claude/worktrees/orca-plugin` は無い | I5（文書の主張が事実）・I2 の文面 | 直す（文言） |
| F4 `-n` で `terminal create` が失敗しても止まらず、空の handle で `send` する。空の handle は**別のライブ端末**に解決され、`cd` が他人の端末に打ち込まれる | 示せる: Orca 管理外の cwd で create が `selector_not_found`（rc=1）、続く `send --terminal ""` は rc=0 で `blogs` の端末に入った（`terminal read --terminal ""` がその handle を返した） | I2（cd が自分の新しいタブではなく無関係な端末に行く） | 直す（CR6 の形で。`send` を無くす） |
| V1（Verifier）`result.terminal.handle` の項目名が一次ソースで未確認 | 示せない（反対の実物がある: 実機の P7〜P9 で `term_…` が返った） | 無し | 不採用（実機で確認済み） |
| V2 = CR4 `tab switch` に `--focus` が無いので前面に出ない恐れ | **示せない**: 人間に Orca の端末を前面にしてもらい、再利用の経路（`goto` ＋ `tab switch`、`--focus` 無し）を流したら PR #195 のブラウザが前面に出た（人間の目視、2026-10-09）。**作成の経路を端末が前面の状態で流すのは測っていない** | — | 不採用 |
| V3 = CR5 Issue モードの URL を `sed` で作るので、`ssh://`・GHE・末尾 `/` のリモートで壊れる | 示せる: `sed` の出力が `ssh://git@github.com/o/r`・`o/r`（ホストが落ちる）・`o/r/` | I1（番号の Issue を表示しない） | 直す（`gh repo view --json url`） |
| V4 `tab list` の既定の範囲が「現在の worktree」であることを書いていない | 示せない（害の実例が無い） | 無し | 残課題 |
| CR1 共通手順と `-n` が変数を共有する別々のコードブロックに分かれ、`TARGET_URL` を代入する行が無い。Bash の呼び出しをまたぐと変数は消える | 示せる: 実機確認は 1 本のスクリプトに写して流したので、この経路を通っていない（交絡）。変数が呼び出しをまたいで消えることはハーネスの仕様 | I2（`-n` を 2 回の呼び出しで流すと空の handle で `send` する＝F4 と同じ）・I1 P2（`BROWSER_PAGE` が消えると毎回作成） | 直す（各モードを 1 ブロックにし、`TARGET_URL` を代入する） |
| CR2 Orca では最初から worktree の中にいるので、`-r` の「worktree 内でなければ」が常に偽になり、`gh pr checkout` が利用者の作業ブランチを切り替える | 示せない（走らせていない） | 無し——`-w`/`-r` は受入基準の外（§3）。**CR2 は「外に置いた理由（cmux と同文で Orca 固有の部分が無い）」が誤りだと言っている**。人間に渡す | 残課題（人間が判断） |
| CR3 前提の確認が `runtime.reachable` しか見ず、cwd が Orca 管理の worktree の中かを見ない | 示せる: scratch で `status` は reachable、`worktree current` は `selector_not_found`。F4 はこの状態で起きた | I2（F4 と同じ） | 直す（前提に `orca worktree current --json` を足す） |
| CR6 `-n` は `terminal create --command` で 1 回にできる | 示せる（修正の実物）: `--command "cd '…'"` で新しいシェルのプロンプトが `orca %`、Orca 管理外では create が rc=1 で何も送らない | I2（F4 の機構を消す） | 直す（F4 の修正の形） |
| CR7 `docs/plugins/index.md` の素のスキルの節の末尾が `/cmux` `/dev-loop` だけを挙げ、同じ節で足した `orca` と食い違う | 示せる（同じ節の 2 行） | 無し——I5 は Orca の CLI についての主張に限っている | 残課題 |
| CR8 既存の利用者は `marketplace update` を先に走らせないと `orca` が見つからない | 示せない（確かめていない） | 無し | 残課題 |
| CR9 版のバナーの段落（この差分で `orca` を足した）が #120 で外した「キャッシュが更新されていない」の断定を持ったまま | 示せる（CLAUDE.md の #120 の記録） | 無し（I5 の範囲外） | 残課題 |

### 2 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1 F3 の文言「`.claude/worktrees/` 配下ならメインのチェックアウトに付く」は一般化しすぎ。付く先は cwd を含む Orca 管理の worktree で、Orca のリンク worktree から始めればそちら | 示せない（Orca のリンク worktree で測っていない。この環境の 1 件は文言どおり） | — | 残課題 |
| CR2-2 `-n` は `--focus` で端末を前面にしてから `tab create`（focus 無し）するので、ブラウザが前面に出ないかもしれない。**あわせて V2 の前提「`tab switch` に `--focus` が無い」は誤り**（`orca tab switch --help` に `--focus` がある） | 示せない（その経路は測っていない）。V2 の前提の誤りは `--help` で確認 | — | 残課題（V2 の行は判断が人間の目視によるので変えないが、前提の誤りをここに記録する） |
| CR2-3 P7・P9 の「緑」は `send` 方式の旧コードで測ったもので、`--command` にしてから測り直したのは P8 だけ | 示せる（§5 の記録） | I2 の証明が HEAD に対して無い | **測り直す**（コードは変えない） |
| CR2-4 一致は先頭の 1 件を取るので、手前に下位ページのタブ（`/pull/12/files`）があると、後ろに完全一致のタブ（`/pull/12`）があってもそちらを選んで上書きする | 示せる: SKILL.md の一致規則をそのまま写した python に `[/pull/12/files, /pull/12]` を渡すと `p-files` を返した | I1（完全一致のタブがあるのに、別のタブの内容を壊す） | **直す**（完全一致を先に探す） |
| CR2-5 P2 の実験は「`goto --page` が指定のページを動かす」と「アクティブなタブを動かす」を判別していない（ほかのタブの URL を見ていない） | 示せない（失敗の実物は無い）が、I1 の証明に交絡が残る | I1 の証明が判別していない | **測り直す**（ほかのタブの URL を前後で見る） |
| CR2-6 `terminal create` は UI が受け取れないとバックグラウンドの handle で `ok: true` を返すので、見えるタブが無くても成功と読む | 示せない | — | 残課題 |
| CR2-7 README は「Orca の端末で起動していること」を前提に挙げ「スキルが最初に確かめて止まる」と書くが、確かめるのは cwd が Orca 管理の worktree の中にあるかだけ | 示せる（前提の確認は `status` と `worktree current` だけ） | 無し——I3 は届くかどうか、I5 は CLI の主張 | 残課題 |
| CR2-8 下位ページのタブを再利用すると、書きかけのレビューコメントなどが消える。`tab list` と `goto` の間に閉じられると何も作らない | 示せない | 無し——P4 は再利用してよいと決めている | 残課題 |
| CR2-9 PR #195 の本文が `-n` を `terminal send` のまま説明している | 示せる（PR 本文） | 無し（成果物の差分ではない） | PR 本文を直す（周の記録の更新） |
| CR2-10 版のバナーの段落の「1.7.1 で入れた」の注意は dev-loop の話で、orca には当たらない | 示せる（同じ段落） | 無し | 残課題（CR9 と同じ段落） |
| M1（Verifier）`--command "cd '…'"` は単引用符を含むパスで壊れる | — | — | 決着済み（§6「単引用符」の行） |
| M2（Verifier）`tab list` は全 worktree のタブを返すので、別の worktree のタブを前面に出して見えるかは未確認 | 示せない | — | 残課題 |
