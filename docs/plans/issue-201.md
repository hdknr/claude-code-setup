# Issue #201 — orca: 測っていない挙動を測る（-n 後の前面・バックグラウンド handle・再利用の競合）

## 0. 計測の結果（周の着手前・2026-10-13・Orca 1.4.224・macOS）

| # | 結果 | 証拠 |
| --- | --- | --- |
| CR2-2 | **再現した**。端末を前面にした状態で `tab create`（フォーカス指定なし）を流すと、新しいブラウザタブは裏に追加されるだけで、前面は端末のまま。**`--focus` なしの `tab switch` でも前面は変わらない**（再利用の経路も同じ欠陥）。`tab switch --page <id> --focus` で前面に出る（陽性対照） | `screencapture` で前後を撮って目視（タブ列のアクティブ表示と本文） |
| CR2-6 | **JSON で判別できる**。`terminal create` の結果に `result.terminal.surface` があり、UI に載ると `visible`。Orca のソース（`app.asar`）では既定値が `background` で、表示に成功したときだけ `visible` に変わり、失敗時は `warning` も付く。**スキルは `ok` しか見ていない** | 実行して `surface: "visible"` を観測。`background` 側は**実行では観測していない**（UI が受け取れない状態を作れなかった）——ソースの読解のみ |
| CR2-8（後半） | 閉じたタブの page id に `goto` すると **rc=1・`browser_tab_not_found`**。続く `tab switch` も rc=1。**失敗は表に出るがタブは作られない** | 実タブを作り `tab close` で閉じてから同じ id で `goto`（存在しない id でも同じ） |
| CR2-8（前半） | 仕様の判断（下位ページのタブの再利用で書きかけが消える）。**この周では扱わない**——人間の判断に回す | — |
| CR8 | **再現した**。カタログが orca を含まないコミット（`86b33d9`）で止まったクライアントで `claude plugin install orca@claude-code-setup` は **rc=1・`Plugin "orca" not found`**。取り直さない。`marketplace update` を挟むと通る（陽性対照） | 一時 HOME と、リポジトリの外の空のディレクトリで。`.gitconfig` の `insteadOf` で GitHub への clone を手元の bare リポジトリへ向け替え、clone の HEAD が `86b33d9` であることで向け替えを確認 |

**交絡の潰し方**:

- CR2-2: 「端末が前面なのは `--focus` のせいで、`tab create` とは無関係」という候補 → `--focus` なしの `tab switch` でも前面が変わらないことを別に見た。陽性対照（`--focus` 付きで前に出る）も取った。
- CR8: 「マーケットプレイスが未登録でも同じ文言が出る」ことを最初の失敗した試行で観測した（`file://` を拒否されて未登録のまま install → 同じ `not found`）。そこで、登録が成功し clone が古いコミットにあることを確かめてから install を当てた。利用者のリポジトリの `.claude/settings.json`（マーケットプレイスと `autoUpdate` を宣言）を避けるため、cwd はリポジトリの外。
- CR2-8: 「作ったことのない id」と「閉じたタブの id」を両方当てた。

**観測窓**: CR2-2 は各操作の 1〜2 秒後に 1 回撮っただけ（遅れて前面が変わる可能性は見ていない）。CR8 は `install` 1 回。

## 1. 変更範囲

触る:

- `plugins/orca/skills/orca/SKILL.md` — `-n` の `surface` 判定、共通手順の `--focus` と `goto` 失敗時のフォールバック、版
- `plugins/orca/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/index.md` — orca のインストールに「既存の利用者は先に取り直す」
- `plugins/orca/README.md` — インストール節に同じ事実への指し先
- `docs/plans/issue-201.md` — この計画ファイル

触らない:

- CR2-8 前半（下位ページの再利用の可否）——仕様の判断
- `cmux` プラグイン（同じ形の欠陥があるかは見ていない）
- 他プラグインのインストール案内（CR8 の事実は orca 以外の後発プラグインにも当てはまりうるが、測ったのは orca だけ）

**複製の数**: 「既存の利用者は先に取り直す」は公開ページ 1 箇所に置き、README は指すだけ（2 箇所・列挙は 1 つ）。
版は 3 箇所（CI が見る）。前面に出す処理は共通手順 1 箇所に寄せる（`-n` 側には書かない）。

## 2. デプロイ経路

- `docs/` の変更は main への push で GitHub Pages に反映される。
- プラグインは version bump → 利用者が `marketplace update` → `plugin update`。

## 3. 受入基準

**I1. 開いた Issue/PR のブラウザタブが前面に出る。**

| 経路 | 守り方 |
| --- | --- |
| P1 新規作成（`-n` あり＝端末が前面） | `tab create` の `browserPageId` に `tab switch --focus` |
| P2 新規作成（`-n` なし。Claude Code が Orca の端末にいれば端末が前面） | 同上（共通手順なのでモードに依らない） |
| P3 再利用（`goto` が成功） | `tab switch --focus` |
| P4 再利用で `tab list` と `goto` の間にタブが閉じられた | `goto` の失敗で新規作成に落とし、P1 と同じく前面に出す |

**I2. `-n` の端末が UI に載らなかったとき、成功と読まない。** `surface` が `visible` 以外なら非ゼロで止まり、理由を出す。

**I3. 既存の手順を壊さない。** `python3 -I`・URL を引数で渡す・完全一致優先・1 回の Bash 呼び出し・`https://` 検査は残す。

**I4. CR8: orca のインストール案内で、既存の利用者が先に `marketplace update` を走らせることが分かる**（事実は公開ページに 1 箇所）。

**I5. 版を 3 箇所で揃える**（`check-all.py` が緑）。

### 証明の手段

- I1 P1〜P3: 直したブロックを実際の Orca で流し、`screencapture` で前面を目視。
- I1 P4: 直したブロックの `goto` の分岐に、閉じたタブの page id を与えて流し、新規作成と前面化を目視。
- I2: `surface` が `visible` の JSON と `background` の JSON を判定部に流して終了コードを見る。**実際に Orca が `background` を返す状態は作れない**——UI が端末を受け取れない状態の作り方が分からない。→ **未証明**（判定部が実物の `background` の出力に効くかは、ソースの読解だけで確かめている）。
- I3〜I5: 差分の読解と `check-all.py`。

### 生成物

生成物なし（drawio と `SKILL.md` の測定値は対象外——`skill-metrics.py` が測るのは dev-loop の `SKILL.md`）。`check-all.py` で確かめる。

## 4. 未解決

- CR2-8 前半（下位ページの再利用）は人間の判断。

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/201-orca-measured-fixes`・worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-201`・
  起点 `9968727`・base 参照 `origin/main` → `9968727b8b800c31c7b94a9929105caac44b37e9`
- 実装: 済。`check-all.py` 32/32 緑
- 著者の実機確認（SKILL.md からブロックを抜き出して流した。手書きの写しではない）:
  - I2: 判定部に 4 形の JSON（`visible`／`background`／`ok:false`／`surface` 無し）→ rc 0／1／1／0。
    **`surface` 無しを止めると古い Orca で `-n` が毎回止まる**ので、通して注記を出す形にした（実装中に気づいて直した）
  - P1: `-n` → 新規作成。タブ 0→1、ブラウザが前面（screencapture）
  - P3: 端末を前面にしてから再利用。タブ 1→1、ブラウザが前面
  - P4: `tab list` を「閉じたタブがある」と答える偽物に差し替えて流した。`goto` が `browser_tab_not_found` →
    新規作成に落ちてタブ 1→2、新しいタブが前面、rc=0
  - 片付け: テストの端末とタブは閉じた（タブ 0・端末は元の 1 本）
- 関門: 未
- 交絡: §0 のとおり。P1〜P4 は各操作の約 2 秒後に 1 回撮っただけ

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `surface: background` を実行で観測していない | 残す（未証明） | UI が受け取れない状態を作れない。ソースでは既定値が `background` |
| CR2-8 前半 | 扱わない | 仕様の判断（P4 は「再利用してよい」） |
| cmux に同じ欠陥があるか | 扱わない | 測っていない。範囲の外 |

この周の起票: 0 件
