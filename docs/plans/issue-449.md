# Issue #449 — check-all.py の中でだけ test-worktree-scripts.py の陽性対照が 300 秒で打ち切られる

`check-mutation-claims.py` の中で最も重い `red` は `python3 scripts/test-worktree-scripts.py`（単独 45 秒）で、
`check-all.py` の 10 並列 × `check-mutation-claims.py` の 10 並列が重なると打ち切り（300 秒）に届く、と見ている。
**人間の判断で、直し方は「足場の git リポジトリを 1 度だけ作り、観測ごとに複製する」**（打ち切りの時間は延ばさない）。

## 変更範囲

触る:

- `scripts/test-worktree-scripts.py` — 足場（`make_repo` / `make_ahead_clones` / `make_dangling_origin_head`）を雛形から複製する
- `docs/plans/issue-449.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/*.sh`（テストの対象。中身を変えない）
- `scripts/check-mutation-claims.py` の `TIMEOUT`（延ばさない——人間の判断）
- `scripts/check-all.py` の並列数
- 変異 20 本と観測の項目（判定を弱めない）

### 同じことを述べている箇所の数

`test-worktree-scripts.py` の所要や構造を述べている箇所: `CLAUDE.md` の 1 行（「変異 20 件」——数は変わらない）と、
テスト自身の docstring。**所要時間を書いている箇所は無い**ので、直す複製は 0。分けない。

## 乗るデプロイ経路

テストスクリプトだけ。プラグインの中身は変えないので版は上げない。公開サイトにも載らない——**反映経路なし**。

## 周の在り処

- ブランチ: `issue/449-worktree-test-fixture-copy`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-449`
- 起点: `0fd44ac`（start-point `origin/main`）
- base: `0fd44ac9622f66697a7e8f4e446b754e4b745fdf`

## 着手前の実測（著者。関門ではない）

- 単独で `test-worktree-scripts.py`: real 45.0 秒（user 17.5 / sys 19.2）
- `observe()` 1 回 ≒ 2.3 秒（裏で `check-all.py` が走っていた時の値）。内訳は `bash` で本体 18 回 1.37 秒、足場 約 0.7 秒
- `observe()` は 21 回（正しい版 1 ＋ 変異 20）を直列に回す
- `check-all.py` を 2 回: 50/50 と 50/50（再現せず）。wall は 226 秒と 365 秒
- **`check-all.py` の中での `red` 1 回の所要**（`PATH` の先頭に記録だけする `python3` を置いて 3 回。コードは触っていない）:
  `test-worktree-scripts.py` の陽性対照が **192.6 / 118.6 / 128.1 秒**——単独の最大 4.3 倍、打ち切りの 2/3。
  2 番目に重い `red`（`test-check-mutation-claims.py`）は 96 秒以下。3 回とも 10 件確認（再現せず）
  - **観測窓**: 3 回だけ。#449 の 300 秒超えは 3 回中 2 回で起きた別の日の値で、今日は届いていない

## 実装後の実測（著者）

- 雛形の作成と複製（同じ負荷の下で 5 回ずつ）: `ahead` 0.497 → 0.042 秒、`dangling` 0.175 → 0.019 秒、`repo` 0.059 → 0.007 秒
- 旧（メインの作業ツリー）と新（worktree）を**交互に** 3 回ずつ: wall 71.3/51.1/50.5 → 35.8/37.0/35.8 秒、
  CPU（子の user+sys）56.4/41.3/41.3 → 29.0/29.2/28.8 秒。**中央値で wall −30%、CPU −30%**
  （旧の 1 回目は暖機を含む）
  - **この比較は交絡していた**（`/code-review` 1 パス目）——旧はメインの作業ツリーで走らせたので、
    `REAL_REPO`（`__file__` から決まる）が違い、テスト対象のスクリプトも別のツリーのものだった。**根拠に使わない**
- **取り直し**（同じ worktree で、旧のテストファイルだけを `scripts/` に一時的に置いて交互に 3 回ずつ）:
  wall 49.3/47.5/51.1 → 33.8/35.5/34.4 秒、CPU（user+sys）40.1/39.4/42.1 → 26.7/28.6/27.4 秒。
  **中央値で wall −29%、CPU −32%**。3 回とも rc=0、1 回目の出力は旧と同じ（`diff` が空）。
  Verifier も独立に 1 回取っている（CPU 38.7 → 25.2 秒、wall 46.7 → 32.1 秒）
- 出力は旧と 1 行も違わない（`real`/`user`/`sys` の行を除いて `diff` が空）
- 陽性対照（不変条件 3）: 付け替えの 1 行を `pass` にすると `_from_template` の assert が落ちる。
  正しい版では `ahead` の 3 クローンと seed、`dangling` の work の remote が複製の bare を指し、
  「未取得(専用)」に `origin/sibling` が無い

## verify の受入基準

不変条件:

1. **判定が変わらない**——正しい版で全項目 ok、変異 20 本がすべて殺せる、2 変異の区別も今のまま
2. **観測は互いに独立**——ある観測（変異）が足場に書いたものが、別の観測に見えない
   （「未取得(専用)」のクローンが取り直されていない、という前提を含む）
3. **複製の remote は複製の bare を指す**——雛形の bare に push / fetch しない（雛形が汚れれば 2 が破れる）
4. **実環境を触らない**——`assert_not_real_repo` が複製先にも掛かる
5. **CPU 時間が減る**——単独の user+sys と wall が下がる

経路（足場を使う入口）: `observe()` の 4 箇所（`repo` / `listless` / `ahead` / `dangling`）、
`check_no_network_on_reject`、`demonstrate_base_rule`（seed から push する——3 に効く）。

確かめ方:

- 1: テストが合格する。変異 1 本を手で戻しても赤いことは、既存の変異ループ自体が見ている
- 2・3: 複製の `.git/config` に雛形のパスが残らないことをテストの中で確かめる（`assert`）。
  **陽性対照**: 書き換えを外すと assert が落ちることを 1 度見る
- 4: 既存の `assert_not_real_repo` を複製先にも当てる
- 5: 前後で `/usr/bin/time` を取る
- mutation-claim（`:302`。着手前は `:248`）が単独の `check-mutation-claims.py` で確認のままであること

### この環境で証明できないもの

- **#449 の症状が消えたこと**——3 回中 2 回しか起きず、今日の 2 回は再現しなかった。
  **「打ち切りに届かなくなった」は未証明**で、言えるのは「最も重い `red` の CPU 時間が下がった」まで

### 生成物

生成物なし（`skill-metrics.py` の対象・図の書き出しとも触らない）。

## 未解決の判断

なし

## 関門の進捗（再開点）

- 実装: 済み（`scripts/test-worktree-scripts.py`。コミット `2353aaa`）。`check-all.py` 50/50（計画の件数の行を足した後）
- 実験の交絡: 最初の新版の計測（wall 59 秒）は裏で `check-all.py` を回していたので捨てた。
  比較は交互に回した A/B だけを使う
- 割り目（手順 4 の後）: 利用者が「ここで割る」を選んだ（2026-10-27）
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 済み。**反証 0 件**。不変条件 1〜5 を実行で確認。
  計画の「`pass` にすると assert が落ちる」を外で当てて真、`check-mutation-claims.py` 単独で 10/10 確認
- `/code-review` 1 パス目（high）: 済み。**指摘 8 件**——採否は下の表。**直す行 0 件**
  （実験の交絡 1 件は、コードではなく測り直しで手当てした——上の「取り直し」）
- 実験の交絡: 上の A/B を同じ worktree で取り直した。Verifier の 1 回も同じ配置（`__file__` を揃えた）
- **2 パス目**: 1 パス目で直したコードが 0 行なので、当て直す差分が無い。
  割り目（2 パス目の前）: 利用者が「このまま PR へ」を選んだ（2026-10-27）
- 狭いパス: 該当なし（2 パス目で直した行が無い）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 打ち切りの時間を延ばす | 採らない | 人間の判断。症状を隠すだけ |
| 変異の観測を並列にする | 採らない | CPU 時間は減らず、`check-all.py` の中では取り合いが増える |
| 変異ごとに観測を絞る | 採らない | 「観測のどこかが変われば殺せた」の判定を弱める |

### 1 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: 根本は `check-all.py` × `check-mutation-claims.py` の入れ子の並列（N×N）で、この差分は 1 本を軽くしただけ | 示せない（打ち切りは今日再現しない） | 無し（直し方は人間が決めた） | 残課題 → **#460 に起票**（手順 8 で利用者が承認。実データは着手前の実測の 192.6 秒） |
| CR2: `:302` の mutation-claim は、行を消すと `main()` の `KeyError` で赤になる——主張の中身（変異が生き残る）は当たっていない | 示せる（外の複製で `KeyError`）。差分の前から | 無し（不変条件 1 の「確認のまま」は満たす） | 残課題 |
| CR3: 複製の `FETCH_HEAD` と reflog に雛形のパスが文字列で残る。assert は `config` しか見ない | 示せる（grep）。Verifier も同じ観測 | 無し（push/fetch の先ではなく履歴の文字列。読む観測が無い） | 残課題 |
| CR4: `/var` → `/private/var` の実パスで書かれた remote は付け替えも検出もされない | 示せない（今の git は与えたまま書く。Verifier が両方を grep して 0） | 無し | 残課題 |
| CR5: `copytree(dirs_exist_ok=True)` は既存の行き先に黙って重ねる（旧は `mkdir` が落ちた） | 示せない（既存の行き先を渡す呼び出しが無い） | 無し | 残課題 |
| CR6: 付け替えの理由のコメント（後の複製に push が見える）は、今の呼び出し順では起きない | 示せる（`main()` の順で `demonstrate_base_rule` が最後） | 無し | 残課題 |
| CR7: 前後比較の A/B が交絡（旧をメインの作業ツリーで実行） | 示せる | 5 の根拠 | **測り直した**（コードは変えない。上の「取り直し」） |
| CR8: `rglob('config')` が `objects/` まで 2 回なめる | 示せない（取り直しで CPU −32%） | 無し | 残課題 |

- この周の起票: 1 件
