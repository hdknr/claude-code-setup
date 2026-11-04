# Issue #820 — spec-loop render-diagrams.py: nohup で起動すると SIGHUP で止まる（#806 の後退）

不在の周（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かず「割らない（不在の cruise）」）。
台帳の確かめた線（出所: 利用者の確認・起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z）:
仕様の穴 = 推奨で決めて起票, 直す線 = 既定, マージ = 関門を通ればマージ, 周の途中の課題 = 外に出す。
**マージはこの周（サブエージェント）ではしない**——PR を作り、PR 側の CI を見るところまで（親の指示）。

- 直す線: `既定`（出所: cruise の確かめた線）
- 版の上げ方: **minor・`spec-loop`**（PR を出す直前の main の先端 0.48.0 → **0.49.0**。親の指示。性質は不具合の修正だが、並行する周との衝突を避ける親の割り当てに従う）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/render-diagrams.py` — 起動時に SIG_IGN のシグナルには後始末のハンドラを登録しない・docstring
- `scripts/test-render-diagrams.py` — `nohup` の形の試料と変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-820.md` — この計画

触らない:

- `plugins/dev-loop/skills/cruise/scripts/run-serial.py` の SIGHUP の転送（別のプラグイン・別の振る舞い）
- `references/tree.md` の「図」（シグナルの扱いを書いていない）

### 同じことを述べている箇所の数

「SIGTERM・SIGHUP で止められたら後始末する／起動時に無視させられていたら無視したまま」を述べる箇所は 4 つ——
本体の docstring の表の 1 行・`stop_on_signal` の docstring・`__main__` のコメント・テストの docstring の 7。
どれも同じ 2 ファイルの中にあり、分けない（1 つの振る舞いの説明とその試料なので）。

## 乗るデプロイ経路

プラグインの配布（main へのマージ → 利用者の `claude plugin update`）。公開サイトの変更は無い。

## verify の受入基準

### 検証で証明できるもの

不変条件 × 経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 起動時に SIGHUP を無視させられて（`nohup`）起こされたら、SIGHUP を受けても書き出しを最後まで進め rc=0 で終わる | (a) 端末を閉じた形（本体のプロセスグループへの SIGHUP） (b) 本物の `nohup` コマンドの下 | `__main__` で `signal.getsignal` が SIG_IGN なら登録しない。(a) はテストの試料、(b) は実機確認 |
| A2 | 起動時に無視させられていなければ、今のとおり SIGHUP で止まり、CLI のグループを止めて一時ファイルを消す（rc≠0・前の svg は変えない・後から書かれない） | 素の起動でグループに SIGHUP | 既存の試料「SIGHUP で止められても CLI が後から書かない」と、変異「SIGHUP を受けない」 |
| A3 | `scripts/test-render-diagrams.py` に A1・A2 を判別する試料と、変異（無条件に登録する形に戻す）を足し、変異が赤になる | — | 変異「無視させられた SIGHUP にも登録する」（#806 の形そのもの） |
| A4 | 同じ規則を SIGTERM にも掛ける（起動時に SIGTERM を無視させられていたら無視したまま） | 本体のグループに SIGTERM | 試料と変異「無視させられた SIGTERM にも登録する」 |
| A5 | 版の 3 種類（marketplace.json・plugin.json・各 SKILL.md の 2 行）が 0.49.0 で揃う | 版の上げ忘れ・取り込みでの衝突 | `check-plugin-versions.py`・`check-version-bump.py` |
| A6 | 歯止めが全部緑（`check-all.py`）、PR 側の CI も緑 | — | `run-serial.py` 越しの `check-all.py`、`gh pr checks` |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目・2 パス目（該当すれば）に渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

### この環境では証明できないもの（未証明）

- **Windows**（`SIGHUP` が無い。`hasattr` で飛ばす経路）——このリポジトリの CI も手元も Windows を持たない。人間のレビューに回す。
- **Linux の `nohup`**——実機確認は macOS の `nohup` だけ（CI の Linux ではテストの試料（`preexec_fn` で SIG_IGN）が走る）。

### 生成物

- 該当判定: **生成物なし**——`render-diagrams.py` は正本リポジトリの図を書き出すスクリプトで、このリポジトリの図（`export-diagrams.py`）も
  `skill-metrics.py` の生成ブロック（dev-loop の `SKILL.md`）も触らない。版の行は生成物ではない。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/820-render-diagrams-nohup`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-820`・
  起点 `16967100`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `1696710059cb7477dfbf517c2a9fd66f8af22596`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 交絡を潰した手順: 本物の `nohup` で旧版（`16967100`）と新版を同じ偽の CLI・同じ時刻に SIGHUP で走らせた——旧版 nohup rc=129・書き出し無し／
  新版 nohup rc=0・書き出し在り（陽性）／素の起動は旧版・新版とも rc=129・書き出し無し・一時ファイル無し（陰性の対照）。
  テストの試料は `preexec_fn` で SIG_IGN にする形（`nohup` と同じく exec に引き継がれる）で、変異（無条件の登録＝旧版と同じ形）で赤になる。

## 既知の限界・決着済みの論点

- SIGTERM にも同じ規則を掛けた（Issue は SIGHUP を挙げるが、直し方の案「起動時のハンドラが SIG_IGN なら登録しない」はシグナルを限らない）。
- 無視したまま走る間は後始末のハンドラが無いが、無視しているので止まらず、後始末も要らない。

### 採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |

## 経験の還元（手順 8）

- この周の起票: 0 件（周の途中の課題で直すに当たる行が無い）
