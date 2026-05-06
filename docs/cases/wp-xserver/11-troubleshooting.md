# 11. トラブルシュート

このページを読むと、**実際に手順を進めたときに詰まりやすい箇所と、その回避方法** が分かります。

困ったら、まずは Claude Code に **エラーメッセージをそのまま貼り付けて相談** するのが一番早いです。

## GitHub 関連

### `gh: command not found`

GitHub CLI が入っていません。Part 1 のセットアップに戻り、`gh` をインストールしてください。

### `Permission denied (publickey)` で push できない

GitHub への認証が切れています。

```bash
gh auth login
```

を実行して再ログインします。

### Issue を作ろうとして「No default repository」と言われる

リポジトリの設定が読まれていません。作業フォルダにいるか確認してください。

```bash
gh repo view
```

で現在のフォルダのリポジトリ情報が表示されればよし。されない場合は [3. GitHub リポジトリの用意](03-github-repo.md) からやり直します。

## Docker 関連

### `docker: command not found`

Docker 環境（Docker Desktop または OrbStack）がインストールされていない、または起動していません。

- macOS（OrbStack）: アプリケーションフォルダから `OrbStack.app` を起動
- macOS（Docker Desktop）: アプリケーションフォルダから `Docker.app` を起動
- Windows: スタートメニューから `Docker Desktop` を起動

### `port is already allocated` でポート 8080 が使えない

別のアプリが 8080 番を使っています。`docker-compose.yml` のポートを変更します。

```yaml
ports:
  - "8081:80"  # 8080 → 8081
```

ブラウザでは `http://localhost:8081` でアクセスします。

### `http://localhost:8080` が真っ白

WordPress が起動中の可能性があります。30 秒ほど待ってリロード。改善しない場合はログを確認します。

```bash
docker compose logs -f
```

ログを Claude Code に貼り付けて相談すれば、原因を切り分けてくれます。

## stage と本番の見た目が違う

### 画像が表示されない

xserver から取り込むときに画像（メディアファイル）が含まれていない可能性があります。

- 7 章の `rsync` で `wp-content/uploads/` を含めて同期したか確認
- DB 内の画像 URL が `https://example.com` のまま → 後述「URL が `https://example.com` のまま」を参照

### URL が `https://example.com` のまま

WordPress のデータベース内に **絶対 URL** が入っているためです。WP-CLI で書き換えます。

> stage の WP-CLI で `search-replace` を使い、`https://example.com` を `http://localhost:8080` に置換してください。

### CSS が崩れている

ブラウザのキャッシュが原因のことが多いです。Mac は `Cmd + Shift + R`、Windows は `Ctrl + F5` でハードリロード。

## SSH 関連（6 章・10 章で使用）

### `Permission denied (publickey)`

SSH 鍵のパーミッションが正しくない可能性があります。

```bash
chmod 600 ~/.ssh/xserver-deploy.key
```

を実行してください。

### `Connection refused`

xserver の SSH 設定が無効になっているか、ポート番号が違います。サーバーパネルの「SSH 設定」で

- SSH が **ON** になっているか
- 表示されているポート番号と `~/.ssh/config` の `Port` が一致しているか

を確認します。

### `Host key verification failed`

xserver の SSH ホスト鍵が変わったときに出ます。Claude Code に頼んで `known_hosts` から該当エントリを削除してから、再接続してください。

## WP REST API 関連（10 章で使用）

### `401 Unauthorized`

アプリケーションパスワードが正しくありません。

- パスワードに **半角スペース** が入っているか確認（4 文字ずつスペース区切り）
- WordPress 管理画面でパスワードを再発行して、`.env.local` を更新

### `403 Forbidden`

xserver の WAF（Web Application Firewall）が API リクエストをブロックしている可能性があります。サーバーパネルの「WAF 設定」で一時的に OFF にして試してみます。

## Claude Code 関連

### Claude Code が止まらず実行を続けてしまう

`Esc` キーで割り込めます。長くなったら `Ctrl + C` で完全終了。

### 同じ質問を何度も聞かれる

`plan.md` や `CLAUDE.md`（プロジェクト用のメモ）に方針を書いておくと、Claude Code が次回から参照してくれます。

> このフォルダに `CLAUDE.md` を作って、これまでの方針（GitHub での管理、stage で確認、PR 経由でデプロイ）を書いておいてください。

## それでも解決しないとき

1. **エラーメッセージをそのまま** Claude Code に貼り付ける
2. 同じ Issue にコメントで状況をまとめる（後から経緯が辿れる）
3. 次回のセミナーミーティングで持ち寄る

詰まること自体は珍しくありません。**詰まったらメモしておく** だけで、次の人が同じ場所で詰まらずに済みます。
