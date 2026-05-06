# Windows での SSH 鍵ファイル管理

Windows での SSH 鍵管理は、macOS / Linux に比べて **詰まりどころが多い** です。フォルダの場所、拡張子、パーミッション、改行コード… 一つ一つ手で対処しようとすると半日かかってしまいます。

このページでは、**初心者がまず通る最短ルート**（Claude Code にお願いする）を先に説明し、**詳しい仕組み** はあとからゆっくり読めるリファレンスとして整理しています。

!!! info "このページの前提"
    [SSH と鍵ファイルをやさしく理解する](index.md) を先に読んで、**公開鍵 / 秘密鍵 / `~/.ssh/` フォルダ** の用語が分かっている前提で進めます。

## まずやる：Claude Code に鍵の配置を頼む

鍵ファイルを正しい場所に置いて、Windows 用のパーミッション設定までやってもらうのは、**Claude Code に頼むのが一番安全で早い** です。手作業だと `icacls` の引数や改行コードのような **目に見えない落とし穴** で詰まりますが、Claude Code はそれを全部吸収してくれます。

### 自分でやることは 1 つだけ

エクスプローラーの **拡張子を表示する設定** だけ、先にやっておきます。これだけで `config.txt` のような事故にすぐ気付けるようになります。

1. エクスプローラーを開く
2. 上部メニューの「表示」→「表示」→ **「ファイル名拡張子」にチェック**

### Claude Code への頼みかた（コピペで OK）

xserver からダウンロードした秘密鍵（例: `your-account.key`）が `Downloads` フォルダにある状態で、Claude Code に次のように頼みます。

> ダウンロードフォルダにある `your-account.key` を Windows の `~/.ssh/` 配下に `xserver-deploy.key` として配置してください。
>
> - `.ssh` フォルダが無ければ作成
> - 配置後、Windows のパーミッション（`icacls`）で **自分のユーザーだけが読める** 状態に設定
> - 確認のため、配置先のパスとパーミッションの状態を表示

これで Claude Code が次のことをまとめてやってくれます。

- `~/.ssh/`（= `C:\Users\<あなた>\.ssh\`）が無ければ作成
- 秘密鍵を移動
- `icacls` で「自分だけ読める」権限に変更
- 結果を表示してチェック

### `~/.ssh/config` も同じノリで頼む

接続情報を書き込む `config` ファイルも、Claude Code に頼むのが安全です。Windows のメモ帳で直接作ると、**勝手に `.txt` がついたり改行コードが CRLF になったり** して詰まりやすいからです。

> `~/.ssh/config` に xserver への接続設定を追記してください。改行コードは LF で。
>
> - Host: `xserver`
> - HostName: `sv-xxxx.xserver.jp`（自分のサーバー名）
> - User: `your-account-name`
> - Port: `10022`
> - IdentityFile: `~/.ssh/xserver-deploy.key`

### 接続を確認する

ここまで終わったら、PowerShell で次を実行します。

```powershell
ssh xserver
```

パスフレーズを聞かれて、サーバーのプロンプト（`[your-account-name@sv-xxxx ~]$` のような表示）に切り替われば成功です。

!!! warning "クラウド同期フォルダだけは自分でも気にしてほしい"
    OneDrive / Dropbox / iCloud Drive と同期されているフォルダに秘密鍵が入ると、**クラウドに鍵がコピーされて** しまいます。Windows 11 では初期設定で **デスクトップやドキュメントが OneDrive 配下** になっていることがあるので、ダウンロード前に「鍵をどこに保存するか」だけは確認してください。
    
    `~/.ssh/`（= `C:\Users\<名前>\.ssh\`）はホーム直下なので、通常は OneDrive に同期されません。

### うまくいかないとき

エラーが出たら、メッセージを **そのままコピーして** Claude Code に貼り付ければ、原因と対処をその場で教えてくれます。

> SSH の接続でこういうエラーが出ました。原因と直し方を教えてください。
>
> ```
> （ここにエラー全文を貼る）
> ```

これでだいたい解決します。以下のリファレンスは、**「自分でも仕組みを知っておきたい」** 人向けです。読まなくても作業は進みます。

---

## リファレンス：仕組みを知っておきたい人向け

ここから先は、Claude Code が裏で何をやっているのかを理解しておきたい人向けの解説です。トラブル時の自力解決にも役立ちます。

### なぜ Windows の SSH は難しく感じるのか

理由は 3 つに集約されます。

1. **`.ssh` フォルダが標準で見つけにくい**（先頭が `.` のフォルダはエクスプローラーから扱いにくい）
2. **拡張子が標準で非表示**（`id_ed25519` と `id_ed25519.pub` の違いが見えない、勝手に `.txt` がついていることに気付かない）
3. **SSH 環境が複数ある**（Windows 標準 OpenSSH / Git Bash / WSL2 / PuTTY）。同じ「`~/.ssh/`」と書いても、どこを見ているかが違う

### `~/.ssh/` フォルダの実体

Windows での `~/.ssh/` の正体は次のフォルダです。

```
C:\Users\<あなたのユーザー名>\.ssh\
```

PowerShell 上では `$HOME\.ssh\` または `$env:USERPROFILE\.ssh\` と書きます。

エクスプローラーで開きたいときは、アドレスバーに次を入力して Enter:

```
%USERPROFILE%\.ssh
```

!!! tip "新規作成するときの落とし穴"
    エクスプローラーの「新しいフォルダー」で名前を `.ssh` にすると、**Windows によっては「無効なフォルダ名です」と弾かれます**。`.ssh.`（最後にもドットを付けて）と入力すると作成できます（末尾のドットは Windows が自動で消してくれる）。PowerShell の `mkdir $HOME\.ssh` のほうが確実です。

### パーミッションの仕組み（`icacls`）

Windows には Linux の `chmod 600` のような単純なコマンドはありません。代わりに **ACL（Access Control List）** で「誰が読めるか」を細かく指定します。

OpenSSH（Windows 標準・Git Bash・WSL2 のいずれも）は、**「他人から読めるかもしれない秘密鍵」を読み込みません**。これに引っかかると次のようなエラーが出ます。

```
Permissions for 'xserver-deploy.key' are too open.
It is required that your private key files are NOT accessible by others.
```

#### 解決コマンドの中身

Claude Code が裏でやっているのはこのコマンドです。

```powershell
icacls $HOME\.ssh\xserver-deploy.key /inheritance:r /grant:r "$env:USERNAME:(R)"
```

意味は次の通りです。

| 部分 | 意味 |
|---|---|
| `/inheritance:r` | 親フォルダから引き継がれた権限を **すべて削除** |
| `/grant:r` | 既存の権限を置き換える |
| `"$env:USERNAME:(R)"` | **自分自身に「読み取り」だけ** 許可 |

設定後の状態は次で確認できます。

```powershell
icacls $HOME\.ssh\xserver-deploy.key
```

自分のユーザー名と `(R)`（Read）だけが表示されていれば OK です。

### `~/.ssh/config` を手作業で作るときの落とし穴

`~/.ssh/config` は **拡張子なし** のテキストファイルです。Windows ユーザーが踏みやすい地雷が 2 つあります。

#### 地雷 1: メモ帳が `.txt` を勝手につける

メモ帳で「名前を付けて保存」すると、ファイル名を `config` にしても **裏で `config.txt` になる** ことがあります。

回避策:

- ファイルの種類で「**すべてのファイル (\*.\*)**」を選んでから保存する
- そもそもメモ帳は使わず、**VS Code** を使う
- PowerShell から `New-Item $HOME\.ssh\config` で空ファイルを作ってから編集する

ステップ 0 で「ファイル名拡張子」を表示するように設定しておけば、`config.txt` ができていれば一目で分かります。

#### 地雷 2: 改行コードが CRLF になる

Windows の標準エディタは改行を **CRLF**（`\r\n`）で保存しますが、SSH の設定ファイルは **LF**（`\n`）が期待されます。CRLF でも多くのケースで動きますが、`Bad configuration option` のような謎のエラーが出ることがあります。

回避策:

- **VS Code** を使う（右下に「CRLF」と表示されているところをクリックして「LF」に変更できる）

#### config の中身（参考）

```
Host xserver
  HostName sv-xxxx.xserver.jp
  User your-account-name
  Port 10022
  IdentityFile ~/.ssh/xserver-deploy.key
```

`IdentityFile` のパスは `~/.ssh/...` のように **チルダ表記** で書けば、Windows OpenSSH が `C:\Users\<名前>\.ssh\...` に自動展開してくれます。

### 「3 つの世界」問題

Windows では SSH が動く環境が **同時に複数存在することがあります**。同じ「`~/.ssh/`」と書いても、実際に見ているフォルダがバラバラなのが、Windows ユーザーが混乱する最大の理由です。

| 環境 | 「`~/.ssh/`」の実体 | コマンドの場所 |
|---|---|---|
| **Windows 標準 OpenSSH**（PowerShell / コマンドプロンプト） | `C:\Users\<名前>\.ssh\` | `C:\Windows\System32\OpenSSH\ssh.exe` |
| **Git Bash**（Git for Windows 付属） | `C:\Users\<名前>\.ssh\`（同じ場所を共有） | Git のインストール先の `usr\bin\ssh.exe` |
| **WSL2**（Ubuntu 等） | `/home/<Linux ユーザー名>/.ssh/`（**完全に別世界**） | Ubuntu の `/usr/bin/ssh` |

たとえば PowerShell で鍵を `C:\Users\you\.ssh\` に置いたあと、WSL2 のターミナルで `ssh xserver` を実行すると **「鍵が見つかりません」** と言われます。WSL2 から見ると、Windows 側の `.ssh` はまったく別のフォルダにあるからです。

!!! tip "迷ったら PowerShell に統一"
    `docs/cases/wp-xserver/` の事例で扱う `git` / `ssh` / Claude Code は、**Windows 標準の OpenSSH（PowerShell から呼ばれる）** で完結するように書かれています。最初は WSL2 を介さず、PowerShell だけで操作するのが一番混乱しません。

### 詰まりやすいエラーと対応

| エラー | 主な原因 | 対応 |
|---|---|---|
| `Permissions for ... are too open.` | 秘密鍵のパーミッションが緩い | `icacls` を再実行（または Claude Code に再依頼） |
| `Could not open ...:No such file or directory` | ファイル名に `.txt` がついている | 拡張子表示を ON にして確認、リネーム |
| `Bad configuration option: ...` | `config` の改行コードが CRLF | VS Code で開いて LF に変更 |
| `Permission denied (publickey)` | `IdentityFile` のパス間違い、公開鍵未登録、別環境（WSL2）から実行 | `config` のパスと、どのターミナルで実行しているかを確認 |
| `Host key verification failed` | 古い `known_hosts` のエントリ | Claude Code に「`known_hosts` から xserver の古いエントリを削除して」と依頼 |

### 自分で確認したいときのチェックコマンド

PowerShell で次を順番に実行すると、設定状態を一通り確認できます。

```powershell
# .ssh フォルダが存在する
Test-Path $HOME\.ssh

# 秘密鍵が .ssh の中にある
Test-Path $HOME\.ssh\xserver-deploy.key

# 拡張子が .key.txt になっていない（False が出れば OK）
Test-Path $HOME\.ssh\xserver-deploy.key.txt

# config が拡張子なしで存在する
Test-Path $HOME\.ssh\config

# 鍵のパーミッションを確認
icacls $HOME\.ssh\xserver-deploy.key

# 接続テスト
ssh xserver
```

## まとめ

- **初心者はまず Claude Code に頼む**：鍵の配置、パーミッション設定、`config` の作成は全部任せる
- **自分でやるのはエクスプローラーの拡張子表示と、鍵を OneDrive に入れない注意だけ**
- 仕組みを知りたくなったら、上のリファレンス節を辞書として参照する

ここまでできたら、[6. SSH 接続を設定する](../../cases/wp-xserver/06-ssh-setup.md) の事例ページに戻って、xserver 側の設定を進めてください。
