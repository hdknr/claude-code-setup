# プラグイン一覧

このリポジトリは **プラグイン・マーケットプレイス**（`claude-code-setup`）として、いくつかのプラグインを配布しています。Claude Code から以下のコマンドでマーケットプレイスを追加し、必要なプラグインをインストールできます。

```
# マーケットプレイスを追加（最初に一度だけ）
/plugin marketplace add hdknr/claude-code-setup

# インストール済み・追加済みの一覧を確認・管理
/plugin
```

配布中のプラグインは以下のとおりです。

| プラグイン | 提供スキル | 概要 |
|---|---|---|
| [`workspace-setup`](#workspace-setup) | `/workspace-setup:workspace-setup` | ワークスペースの初期セットアップ |
| [`cmux`](#cmux) | `/cmux:cmux` | cmux ウィンドウで GitHub Issue/PR を操作 |
| [`dev-loop`](#dev-loop) | `/dev-loop:dev-loop` | 1 Issue = 1 周のループ志向開発 |

!!! warning "呼び出しは `プラグイン名:スキル名`"
    プラグインが提供するスキルは、名前の衝突を防ぐため**常にプラグイン名で名前空間化されます**。
    たとえば `cmux` プラグインのスキルは `/cmux` ではなく **`/cmux:cmux`** で呼び出します
    （`commands/` に置いても同じ名前空間に載るため、bare な `/cmux` をプラグインで提供する方法は
    ありません）。名前空間の付かない短い名前で呼びたい場合は
    [bare な名前で呼びたい場合](#bare-invocation) を参照してください。

!!! info "プラグインの入れ方・使い方の全体像"
    インストール手順と日常利用の流れは [Part 3: インストール後の環境準備](../part3-post-setup.md) にもまとまっています。このページは各プラグインの**詳細リファレンス**です。

---

## インストールのスコープ

`/plugin install` を実行するとスコープの選択画面が出ます。

| スコープ | 意味 |
|---|---|
| **User** | 自分の**全プロジェクト**で使う |
| **Project** | このリポジトリの**全メンバー**で使う（`.claude/settings.json` に入る） |
| **Local** | このリポジトリで**自分だけ**が使う（共有しない） |

**全プロジェクトで使いたい場合は User を選びます。** シェルから非対話で入れる場合は
`--scope` を渡します。

```bash
claude plugin marketplace add hdknr/claude-code-setup
claude plugin install cmux@claude-code-setup --scope user
```

`claude plugin install` はセッションの外で走るため、反映は次回起動時か、開いている
セッションで `/reload-plugins` を実行したときになります。

---

## workspace-setup

作業用ワークスペースの初期セットアップを対話的に行うプラグインです。Claude Code を使い始める最初の一歩をまとめて実行します。

### インストール

```
/plugin install workspace-setup@claude-code-setup
```

### 提供スキル

#### `/workspace-setup:workspace-setup`

以下を対話的にセットアップします。

1. **ワークスペースディレクトリの作成** — `~/Projects/` 配下にディレクトリを作成し `git init`（デフォルト名 `my-workspace`）
2. **CLAUDE.md の作成** — リポジトリの目的・日本語応答の指示などを記述
3. **GitHub プライベートリポジトリの作成と連携** — `gh repo create --private` で非公開リポジトリを作成・プッシュ
4. **完了確認** — 作成先パス・リポジトリ URL・次のステップの提示

!!! warning "必ずプライベートで作成"
    作業用リポジトリには個人情報や機密情報が含まれる可能性があるため、**必ず非公開（Private）**で作成します。詳細は [Part 3: インストール後の環境準備](../part3-post-setup.md) を参照してください。

### 前提

- `gh` CLI が認証済みであること

---

## cmux

[cmux](https://github.com/manaflow-ai/cmux) ウィンドウ内で GitHub の Issue/PR を扱うためのプラグインです。ブラウザペインに Issue/PR を表示し、worktree でレビューを行えます。

### インストール

```
/plugin install cmux@claude-code-setup
```

### 提供スキル

#### `/cmux:cmux [-n] [-w|-r] <number>`

cmux のブラウザペインで GitHub Issue/PR を開き、worktree でレビューを行います。

| 呼び出し | モード | 動作 |
|---|---|---|
| `/cmux:cmux <number>` | Issue | Issue の URL をブラウザペインに表示 |
| `/cmux:cmux -w <number>` | PR worktree | PR をブラウザ表示し、worktree を作成して `gh pr checkout` |
| `/cmux:cmux -r <number>` | PR レビュー | worktree でチェックアウトし、`gh pr diff` でレビュー開始 |

`-n` フラグを付けると、処理の最初に新しいターミナルタブ（サーフェス）を作成し、そこで実行します。

**使用例:**

```
# Issue 番号 12 をブラウザペインに表示
/cmux:cmux 12

# PR 番号 34 を worktree でチェックアウトしてレビュー
/cmux:cmux -r 34
```

### 前提

- `cmux` CLI がインストールされていること
- `gh` CLI が認証済みであること
- Claude Code の `EnterWorktree` ツールが利用可能であること

---

## dev-loop

GitHub Issue 1 件を、**検証（verify）が通ることを停止条件**として 1 周させる、
ループ志向開発のスキルを提供するプラグインです。どのプロジェクトでも使える汎用版で、
プロジェクト固有の事情は対象リポジトリの `CLAUDE.md` から発見して従います。

!!! info "設計の背景"
    「なぜループ志向か」「verify を停止条件に据える理由」「Dreaming・トークンコスト・
    アンチパターン」といった設計思想は [dev-loop の設計（ループ志向開発）](dev-loop-design.md)
    にまとめています。

### インストール

```
/plugin install dev-loop@claude-code-setup
```

### 提供スキル

#### `/dev-loop:dev-loop <issue-number>`

対象 Issue を、以下の標準サイクルで 1 周させます。**5↔4 は verify が通るまで繰り返します。**

1. **Issue 選択** — `gh issue view` で要件・受入条件を把握
2. **文脈収集** — 関連設計・既存実装・過去の議論を読む
3. **計画** — 変更範囲を切り分け、設定／フラグで済むかを先に判断。**計画と verify の受入基準を
   ファイルに書き出す**（コンテキスト圧縮・セッション跨ぎに耐えさせる）。受入基準は
   **「不変条件 × それを破りうる経路」に展開**する（**経路は差分ではなくアプリの入口一覧から
   数える** —— 差分を読むレビューは差分に現れていない経路を構造的に見落とす）。**この環境では
   証明できないもの**を分けて「未証明」と明示する。**生成物があればその鮮度**（再生成して差分ゼロ）も
   受入基準に入れる（該当が無ければ「生成物なし」と明記する）
4. **実装** — **まず worktree を開始**してから、対象リポジトリの `CLAUDE.md` のルールに従って変更。
   **ファイルを変更する周では worktree は必須**で、その周の成果は必ず PR になります
   （例外は調査だけで終わる周）
5. **検証（停止条件）** — 実機で目視確認 ＋ **別モデルの検証エージェント**で受入条件の反証を探す。
   回せないときは**黙って飛ばさず、着手前に申告して指示を仰ぐ**
6. **レビュー → PR** — **`/code-review` は手順 5 の有無に関わらず必須**。**受入基準は Verifier と
   `/code-review` の両方に渡し、問いを局面に絞らない**。指摘を直したら verify とレビューの
   **両方**に当て直し、**2 パス目にも受入基準を渡す**（＝受け渡しは計 4 回）。
   **変更が 1 行でもあれば PR にする**（直接コミット／push で閉じない）。**worktree 上であることを
   確認**して PR 作成、結果と**手順 3 で「未証明」とした項目**を PR コメントに残す
7. **本番反映** — CLAUDE.md / deploy runbook に従う
8. **経験の還元** — 学びを CLAUDE.md / Skill / メモリへ焼き戻す

!!! tip "CLAUDE.md に書いておくと効く"
    実機検証（verify）の手順・デプロイ経路・やってはいけない制約を対象リポジトリの
    `CLAUDE.md`（または `.claude/dev-loop.md`）に書いておくと、スキルがそれを発見して従います。
    無ければテスト実行＋アプリ起動での手動確認に**縮退**するので、設定が無くても動きます。

**使用例:**

```
# Issue 番号 42 を 1 周させる
/dev-loop:dev-loop 42
```

### 前提

- `gh` CLI が認証済みであること
- 対象リポジトリが git 管理下にあること
- **worktree を作れること**（`git worktree add`、または `EnterWorktree` ツール）— 手順 4 で
  **必須**です。**ファイルを変更する周は必ず worktree で作業し、PR にします**（デフォルト
  ブランチへの直接コミット／push はしません）。「小さい変更だから」は例外になりません。
- **受入基準に照らした差分レビューの手段**（`/code-review` 等）— 手順 6 で**必須**です。道具が
  無い環境では、同等のレビューを別の手段（人間レビュー等）で行います。**省略はできません。**
  代替手段でも次を満たします: **受入基準（不変条件と経路の一覧）をまるごと渡す／問いを局面に
  絞らない／初回と指摘対応後の 2 パスを回す（2 パス目にも受入基準を渡す）**。「差分を眺める」
  だけでは要件を満たしません。
- **別モデルの検証エージェント**（`Agent` ツール等）— 手順 5 で**必須**です。レビューとは**相互に
  代替できない別々の関門**で、片方があるからもう片方を省くことはできません。**代替手段（人間の
  検証等）でも受入基準をまるごと渡し、問いを局面に絞りません。** 使えない環境では
  **黙って飛ばさず、着手前に申告して指示を仰ぎます**——(1) 使用許可を求める / (2) `/code-review` に
  受入基準を渡した**追加**パスで代替する（手順 6 の必須分とは別に回す） / (3) 理由付きで省略を
  宣言し PR コメントに残す、のいずれかを明示的に選びます。
- （任意）`/loop`・`/schedule`・`/run` などの汎用スキルや、フェーズ分割型のプランニング
  プラグイン。無い環境では手動の待機・確認に読み替えます。

---

## bare な名前で呼びたい場合 { #bare-invocation }

プラグイン経由の呼び出しは必ず `プラグイン名:スキル名` になります。`/cmux` のように
名前空間の付かない名前で呼びたい場合は、**マニフェスト（`.claude-plugin/`）を持たない素のスキル**
として skills ディレクトリに置きます。置き場所で有効範囲が変わります
（[スキル活用ガイド](../usage/skills-guide.md) の置き場所の表と同じ区別です）。

| 置き場所 | 有効範囲 |
|---|---|
| `~/.claude/skills/<name>/` | すべてのプロジェクトで自動的に読み込まれる |
| `<プロジェクト>/.claude/skills/<name>/` | そのプロジェクトだけ |

以下は全プロジェクトで使う場合の手順です。

このリポジトリの `plugins/<name>/skills/<name>/` は `SKILL.md` だけで `.claude-plugin/` を
持たないので、そのまま symlink できます。

```bash
git clone https://github.com/hdknr/claude-code-setup.git ~/src/claude-code-setup

mkdir -p ~/.claude/skills

# 同名の実ディレクトリが既にあるなら先に退避する（symlink なら不要）
for name in cmux dev-loop; do
  if [ -d ~/.claude/skills/$name ] && [ ! -L ~/.claude/skills/$name ]; then
    mv ~/.claude/skills/$name ~/.claude/skills/$name.bak
  fi
done

# /cmux で呼べるようにする
ln -sfn ~/src/claude-code-setup/plugins/cmux/skills/cmux ~/.claude/skills/cmux

# /dev-loop で呼べるようにする
ln -sfn ~/src/claude-code-setup/plugins/dev-loop/skills/dev-loop ~/.claude/skills/dev-loop
```

!!! note "退避のガードが入っている理由"
    `~/.claude/skills/cmux/` を**実ディレクトリとして**すでに持っている場合（個人スキルとして
    直置きしていた場合）、`ln -sfn` は**エラーを出さずに** `~/.claude/skills/cmux/cmux` を
    作ってしまい、`/cmux` は増えません（`-f` はディレクトリを unlink できないため）。
    上のブロックはその状態を先に `.bak` へ退避するので、置き場所がどの状態でもそのまま
    コピー＆ペーストできます。

次のセッションから、どのプロジェクトでも `/cmux` `/dev-loop` で呼べます。更新は
`git -C ~/src/claude-code-setup pull` だけでよく、symlink の張り直しは不要です。

!!! note "プラグインと併用すると両方並びます"
    プラグインを入れたまま symlink も張ると、`/cmux` と `/cmux:cmux` の両方がスキル一覧に
    出ます（中身は同じなのでどちらでも動きます）。片方だけにしたい場合は、プラグインを
    入れずに symlink だけにしてください。

    macOS / Linux 向けの手順です。Windows で symlink を使わない場合はディレクトリをコピーし、
    `git pull` のたびにコピーし直してください。
