# 11. トラブルシュート

このページを読むと、**実際に手順を進めたときに詰まりやすい箇所と、その回避方法** が分かります。

困ったら、まずは Claude Code に **エラーメッセージをそのまま貼り付けて相談** するのが一番早いです。

## ツール別のトラブルはツール解説に集約しています

ツールに関する詰まりどころ（インストール、認証、コマンドエラーなど）は、各ツールの解説ページに **「詰まりやすいエラーと対応」表** としてまとめてあります。事例の途中で詰まった場合は、まずそちらを参照してください。

- **GitHub / `gh` / push まわり** → [GitHub をやさしく理解する / 詰まりやすいエラーと対応](../../tools/github/index.md#troubleshoot)
- **Docker / コンテナ / ポート / ローカル WordPress 真っ白** → [Docker をやさしく理解する / 詰まりやすいエラーと対応](../../tools/docker.md#troubleshoot)
- **SSH 全般（接続拒否・鍵パーミッション・known_hosts など）** → [SSH と鍵ファイルをやさしく理解する / 詰まりやすいエラーと対応](../../tools/ssh/index.md#troubleshoot)
- **Windows 特有の SSH 鍵管理（`icacls` / 改行コード / 3 つの世界問題）** → [Windows での SSH 鍵ファイル管理](../../tools/ssh/windows.md)

以下は、この事例（WordPress + xserver）に **特有のトラブル** だけを残しています。

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
