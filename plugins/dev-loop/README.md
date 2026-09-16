# dev-loop plugin

GitHub Issue 1 件を **検証（verify）が通ることを停止条件**として 1 周させる、
ループ志向開発のスキルを提供するプラグイン。どのプロジェクトでも使える汎用版。

設計思想（なぜループ志向か・verify を停止条件に据える理由・Dreaming・トークンコスト・
アンチパターン）は [dev-loop の設計](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/) を参照。

## 提供スキル

### `/dev-loop:dev-loop <issue-number>`

> **なぜ `/dev-loop` ではなく `/dev-loop:dev-loop` なのか**
>
> プラグインが提供するスキルは、名前の衝突を防ぐため**常にプラグイン名で名前空間化される**。
> `commands/` に置いても同じ名前空間に載るので、bare な `/dev-loop` をプラグインで提供する
> 方法は無い。`/dev-loop` で呼びたい場合は、**マニフェストを持たない素のスキル**として
> skills ディレクトリへ置く（全プロジェクトなら `~/.claude/skills/dev-loop/`、そのプロジェクト
> だけなら `<プロジェクト>/.claude/skills/dev-loop/`）。手順は下記「インストール」を参照。
> 以下の本文では短い方の `/dev-loop` で表記する。

対象 Issue を、以下の標準サイクルで 1 周させる。5↔4 は verify が通るまで繰り返す。

1. **Issue 選択** — 要件・受入条件・関連 PR を把握する
2. **文脈収集** — 関連設計・既存実装・過去の議論を読む
3. **計画** — 変更範囲を切り分け、**計画と verify の受入基準をファイルに書き出す**
4. **実装** — **まず worktree を開始**してから変更する
5. **検証（停止条件）** — 実機で目視確認 ＋ **別モデルの検証エージェント**で反証を探す
6. **レビュー → PR** — **`/code-review` は必須**。指摘を直したら verify とレビューの両方に当て直す
7. **本番反映** — CLAUDE.md / deploy runbook に従う
8. **経験の還元** — 学びを CLAUDE.md / Skill / メモリへ焼き戻す

> **各段の必須要件は [`skills/dev-loop/SKILL.md`](skills/dev-loop/SKILL.md) が正で、
> ここには書かない。** 上の 1 行ずつは「その段が何をする段か」であって、**要件の要約ではない**
> ——**読んで従う先は `SKILL.md`** である。
>
> **これは一度失敗して決めたことである**（#94）。規範を減らしたのではなく、
> **規範の住所を 1 つにした**。**経緯と実測は
> [dev-loop の設計 §8.1](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#miscount)
> を正とする**（ここに書かない——**それを書くことがまさにこの節が直した形**である）。

> **「小さいから」では縮退しない。** 1 行の typo 修正でも**ファイルを変更する周は
> worktree → PR** に乗り、2 つの関門を通る。何を落としてよく何を落とせないかは
> [`skills/dev-loop/SKILL.md`](skills/dev-loop/SKILL.md) の「縮退の線」の節に**そこだけ**
> まとめてある（ここで列挙すると片方だけが古くなる）。落としてよい側は**各手順の「（任意）」**に
> 付いている。線の引き方の根拠は
> [dev-loop の設計 §4.1](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#degradation)、
> BLOCKED と「未証明」の違いは
> [§2.3](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#blocked)、
> 実験の交絡は
> [§2.4](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#confounded) を参照。

## プロジェクト固有部分の扱い

このスキルは特定プロジェクトに依存しない。実機検証コマンド・デプロイ経路・一次ソース
ドキュメントといった**プロジェクト固有の事情は、対象リポジトリの `CLAUDE.md`（および任意の
`.claude/dev-loop.md`）から発見**して従う。見つからなければ汎用手順（テスト実行＋アプリ起動での
手動確認）に縮退するので、設定ファイルが無くても動く。

より効果を出すには、対象リポジトリの `CLAUDE.md` に次を書いておくとよい:

- **実機検証（verify）の手順** — 開発サーバの起動方法、実データ接続、E2E の走らせ方
- **デプロイ経路** — 何をマージ／ビルド／apply すると本番に反映されるか
- **やってはいけない制約** — 破壊的操作・不可逆 apply の前提条件

## 前提

**ここに書くのは「何が要るか」までで、「どう使うか」は書かない**（要件は
[`skills/dev-loop/SKILL.md`](skills/dev-loop/SKILL.md) が正）。

- `gh` CLI が認証済みであること
- 対象リポジトリが git 管理下にあること
- **worktree を作れること**（`git worktree add`、または `EnterWorktree` ツール）
  — 手順 4 で**必要**
- **受入基準に照らした差分レビューの手段**（`/code-review` 等）— 手順 6 で**必要**。
  道具が無い環境でも**省略はできない**ので、同等のレビューを別の手段（人間レビュー等）で行う。
  **代替手段が満たすべき要件**（受入基準の渡し方・2 パス）は `SKILL.md` の手順 6 にある
- **別モデルの検証エージェント**（`Agent` ツール等）— 手順 5 で**必要**。
  レビューとは**相互に代替できない別々の関門**で、片方があるからもう片方を省くことはできない。
  使えない環境での扱い（申告して指示を仰ぐ・3 つの選択肢）は `SKILL.md` の手順 5 にある
    - **このプラグインは検証用の agent 定義を同梱している。** `subagent_type` に
      **`dev-loop:dev-loop-verifier`** を指定すればよい（手で書く必要はない）。
      **名前空間を落として `dev-loop-verifier` と書くと、解決に失敗して汎用 agent に静かに
      フォールバックする**ので注意する。素のスキルとして使う場合の置き方と、
      **なぜ書き込みツールを持たない体を既定にするのか**は `SKILL.md` の手順 5 を見ること
- （任意）`/loop`・`/schedule`・`/run` などの Claude Code 汎用スキルや、フェーズ分割型の
  プランニングプラグイン。無い環境では手動の待機・確認に読み替える


## インストール

まずマーケットプレイスを追加する（最初に一度だけ）。

```
/plugin marketplace add hdknr/claude-code-setup
```

`/plugin install` はスコープの選択画面を出す。**User** が自分の全プロジェクト、**Project** が
このリポジトリの全メンバー、**Local** がこのリポジトリで自分だけ。

```
/plugin install dev-loop@claude-code-setup
```

### すべてのプロジェクトで使う（ユーザースコープ）

上のコマンドで **User** を選ぶ。シェルから非対話で入れる場合は `--scope` を渡す。

```bash
claude plugin marketplace add hdknr/claude-code-setup
claude plugin install dev-loop@claude-code-setup --scope user
```

`claude plugin install` はセッションの外で走るため、反映は次回起動時か、開いている
セッションで `/reload-plugins` を実行したときになる。

### 更新のしかた

**version を上げただけでは届かない。** 利用者のマーケットプレイスのクローンは
**導入時のコミットで凍結したままになる**——#63 で実際に、`dev-loop` が 1.0.0 のまま
使われていた。**再実測でもまだ 1.0.0 のまま**だった。
**確認方法・注意点・最新の実測値は[プラグイン一覧の「更新のしかた」](https://hdknr.github.io/claude-code-setup/plugins/#updating)を正とする**（ここには再掲しない）。2 段階で更新する。

```
/plugin marketplace update                  # カタログを取り直す
/plugin update dev-loop@claude-code-setup      # 新しい版に上げる（要再起動）
```

入っている版は **`SKILL.md` の冒頭**に書いてある。読み込まれた版がここより古ければ、
キャッシュが更新されていない。

**常に最新を使いたいなら、下の symlink 経路を選ぶ**——キャッシュを経由しないので、
`git pull` した時点で反映される（構造的に古くならない）。
**ただしスクリプトは自分の位置からリポジトリを解決して絶対パスで張る**ので、
**worktree から実行するとその worktree に固定される**。メインの作業ツリーから実行する。

### bare `/dev-loop` で使う

`plugins/dev-loop/skills/dev-loop/` は `SKILL.md` だけで `.claude-plugin/` を持たないので、
素のスキルとして skills ディレクトリに置けば名前空間の付かない `/dev-loop` になる。
置き場所で有効範囲が変わる。

| 置き場所 | 有効範囲 |
|---|---|
| `~/.claude/skills/dev-loop/` | すべてのプロジェクト |
| `<プロジェクト>/.claude/skills/dev-loop/` | そのプロジェクトだけ |

以下は全プロジェクトで使う場合の手順。リポジトリを clone して、付属のスクリプトを実行する。

```bash
git clone https://github.com/hdknr/claude-code-setup.git ~/src/claude-code-setup
~/src/claude-code-setup/scripts/link-skills.sh dev-loop
```

スキル名を省略すると（`scripts/link-skills.sh`）、このリポジトリが配布する素のスキルを
すべて張る。`-d <dir>` で置き場所を変えられ（既定は `~/.claude/skills`）、`-n` を付けると
何をするかだけ表示して変更しない。

> **なぜスクリプトなのか。** 素朴に `ln -s` を並べるだけだと、宛先や clone の状態によって
> **黙って壊れる**（動いているスキルを退避したうえで壊れた symlink を張り、終了コード 0 で
> 何も出力しない、など）。手順を文書に手で複製していたところ 4 ラウンド連続でこの類のバグが
> 出たので、1 箇所に集めてテスト（`scripts/test-link-skills.py`）を当てている。
>
> スクリプトは**リポジトリの位置を自分で解決する**ので clone 先を入力する必要がなく、
> 同名の実ディレクトリがあれば `.bak.<日時>` へ退避し、**張った後に解決を確認して、
> できていなければ非 0 で終わる**。

- **プラグインと併用すると `/dev-loop` と `/dev-loop:dev-loop` が両方並ぶ。** 中身は同じなので
  どちらでも動くが、スキル一覧が二重になる。片方だけにしたいなら、プラグインを入れずに
  symlink だけにする。
- **スクリプトは sh / bash / zsh / dash でテストしている**（`scripts/test-link-skills.py`）。
  テストは macOS で回しているが、POSIX sh で書いてあり dash も含めて通るので Linux でも
  同じ挙動になる見込み。**Windows は未検証**で、symlink を使わない場合はディレクトリを
  コピーする（`git pull` のたびにコピーし直す）。
