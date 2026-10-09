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
- 関門: **未着手**（Verifier 1 パス目から）
- 反証・差し戻し: なし（引き継ぎ時に自分で F1 を見つけた。下の表）
- 交絡: 未（実験は手順 5 で行う）
- 実装: F1 の修正をコミット済み（`check-all.py` 30/30 緑）
- 割り目（手順 4 完了時）: 提案した → 「ここで割る」が選ばれた。次は手順 5 の Verifier 1 パス目から（関門は 0 件通過）

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| F1 タブ再利用の部分一致（`target in url`） | **直す**（引き継ぎ時に自分で発見） | 実物で失敗を示せた: `/issues/194` のタブがある状態で `/issues/19` を開くと 194 のタブを再利用して上書きした。I1 P3 を破る |
| cmux にも F1 と同じ穴がある | **残課題**（この周では直さない） | cmux はこの周の変更範囲の外 |
| worktree を `EnterWorktree` のままにする | 初版は cmux に揃える | Orca 管理の worktree には現セッションが入らない。人間が決める（§4） |
| `-n` の cd で、パスに単引用符を含むと壊れる | 残課題 | cmux は引用すらしていない。単引用符を含むパスは実例が無い |
| 計画ファイルを実装の後に書いた | 事実として記録する | dev-loop への引き継ぎがマージ前に決まったため |
