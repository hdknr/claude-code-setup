# Issue #468 — StopFailure の hook で利用上限の停止をその場で記録・通知する

#456（自動継続の陽性対照）は上限を狙って起こせないので、自然に当たるのを待つしかない。
いまは利用者が気づくことに頼っており、気づかなければ記録は埋もれ、人間が「継続」と打てば陽性対照にならない。
`StopFailure` の hook で、止まったその場で手元のファイルに 1 行残し、通知を出す。

## 変更範囲

触る:

- `scripts/record-stop-failure.py` — 新規。hook の本体（stdin の JSON → `~/.claude/usage-limit-stops.jsonl` に 1 行・通知）
- `scripts/test-record-stop-failure.py` — 新規。回帰テスト（変異テストを含む。偽の stdin・一時 `HOME`・偽の `osascript`）
- `scripts/check-all.py` — `TESTS` に登録
- `.github/workflows/plugins.yml` — テストのステップを登録
- `docs/usage/usage-limit-stop-hook.md` — 新規。設定の手順
- `docs/plugins/dev-loop-cruise.md` — 「2. 環境を点検する」の節から指す
- `mkdocs.yml` — nav に足す
- `CLAUDE.md` — `scripts/` の一覧に 2 行
- `docs/plans/issue-468.md` — この計画

触らない:

- `plugins/` 配下（`check-unattended-env.py` に hook の点検を足すのは Issue に無い。版も上げない）
- 利用者の settings（リポジトリから書き換えない——Issue の「しないこと」）
- `scripts/count-usage-limit-resumes.py`（数えるのは後から。この周は合図を置くだけ）

### 同じことを述べている箇所の数

「hook が何を書き、何を書かないか」: 本体の docstring・docs の新ページ・`CLAUDE.md` の 1 行の 3 箇所。
docs と `CLAUDE.md` は**本体の docstring を正とする**と書いて列挙を持たない形にする（分けない理由: 利用者向けの手順は
登録の形が要り、docstring には置けない）。

## 乗るデプロイ経路

`docs/` の新ページと `dev-loop-cruise.md` は main への push で GitHub Pages に出る（公開サイトへの反映あり）。
`scripts/` は反映経路なし。プラグインの中身は変えないので版は上げない。

## 周の在り処

- ブランチ: `issue/468-stopfailure-hook`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-468`
- 起点: `c495860`（start-point `origin/main`）
- base: `c4958600e80be45a84e38340913c7699bd7d525b`

## 受入基準

不変条件:

1. **案件の中身を書かない**——`last_assistant_message` と `cwd` の生の値が、記録のファイルにも通知にも出ない。
   `error_details` は先頭だけ（長さに上限）
2. **壊れた入力で例外を出さず、読めなかったことを 1 行残す**——JSON でない・オブジェクトでない・キーが無い・
   stdin が空・非 UTF-8。終了コードは常に 0（fire-and-forget）。読めなかった行にも入力の生の値を書かない
3. **記録の先は `$HOME/.claude/usage-limit-stops.jsonl` で、追記**（前の行を消さない）。`~/.claude` が無ければ作る
4. **通知が失敗しても記録は残る**（`osascript` が無い・失敗する）。通知には「『継続』と打たずにリセットまで待つ（#456）」を添える
5. **テストは実環境の `~/.claude` を対象にしない**——一時 `HOME` をアサートで担保。本物の通知を出さない（偽の `osascript`）
6. **`check-all.py` と CI に登録**——`test-check-all.py` が緑（収録漏れの検査）
7. **docs の手順**: user の settings に `StopFailure`（matcher `rate_limit`）を足す形。登録は利用者が行う。
   `dev-loop-cruise.md` の環境の点検の節から指す。`mkdocs build --strict` が通る（リンク切れなし）
8. **陽性対照**: hook を登録した状態で、実際に `StopFailure` が発火した記録を 1 件取る（上限以外の `StopFailure` で経路だけでも）。
   取れなければ BLOCKED。**記録が出ないことを「発火しない」と読まない**
9. **文面の事実**: docs と docstring が述べる `StopFailure` の性質（発火条件・入力のキー・matcher の値）は、
   本体 2.1.311 の文字列か陽性対照で確かめた範囲に留める。確かめていないもの（上限で `rate_limit` になるか・待ちの間の回数）は
   「確かめていない」と書く

経路（記録のファイル・通知に値が入る入口）:

| 経路 | 守り方 |
| --- | --- |
| hook として Claude Code が起こす（stdin の JSON） | 本体が書くキーを許可リストで選ぶ（1・2） |
| 人が手で走らせる（stdin が端末・空） | 空の入力として「読めなかった」1 行（2） |
| 通知（`osascript` の引数） | 固定の文言と `error` の値だけ（1・4） |
| テスト | 一時 `HOME`・偽の `osascript`（5） |

検証で証明できるもの: 1〜6（テストと変異）、7（`mkdocs build --strict`・目視）、8（実際に `claude` を起こして観測できれば）、9（関門）。

この環境では証明できないもの（**未証明**）: 利用上限（claude.ai のセッションの上限）で実際に発火し `error` が `rate_limit` になること・
待ちの間の発火回数——上限を狙って起こせない（#456 そのもの）。

生成物: なし（図の書き出し・`skill-metrics.py` の生成ブロックは触らない。`SKILL.md` も触らない）。

## 未解決の判断

- なし

## 手順 8

- この周の起票: 0 件

## 関門の進捗（再開点）

- 手順 4: 実装済み（`check-all.py` 52/52 緑・`mkdocs build --strict`（`plans/` を外した一時の設定）が通る）
- 範囲の追加（手を動かす前に記録）: `docs/plugins/dev-loop-cruise.md` の見出し「2. 環境を点検する」に明示の id `{ #env-check }` を付けた
  ——日本語の見出しはスラグが `2` 程度にしかならず、新ページからのリンクが strict で落ちた。既存のリンクで `#2` を指すものは無い（grep）
- 交絡を潰した手順（受入基準 8 の陽性対照。著者の実験で、関門ではない）:
  - 一時 `HOME`・無効な `ANTHROPIC_API_KEY`・`claude -p "hi" --settings <一時の settings>`（2.1.311・macOS）。
    scratchpad の `probe-stopfailure.sh`
  - matcher なし → 1 行（`error: authentication_failed`・`error_details` 無し）／ `authentication_failed` → 1 行／ `rate_limit` → 記録なし。
    **同じ設定で matcher だけを変えて有無が分かれた**ので、「hook が壊れていて出ない」ではなく matcher が `error` に当たっていると読める
  - 確かめていないもの: user の settings の層・対話のセッション・利用上限での発火（docs の「確かめていないこと」に書いた）
- 割り目（手順 4 の終わり）: 利用者が「ここで割る」を選んだ（2026-10-27）
- 次にすること: 手順 5 の 1 パス目（Verifier。別ティア・`dev-loop:dev-loop-verifier`）と手順 6 の 1 パス目（`/code-review`）。
  どちらも未着手・反証 0 件（まだ当てていない）。base は上の「周の在り処」の SHA

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `cwd` のハッシュに塩を入れない | 採らなかった | 同じ `cwd` の停止を手元で束ねられるようにするため。既知のパスなら辞書で戻せるが、ファイルは手元にしか無い |
