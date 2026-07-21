---
name: cmux
description: "cmux ウィンドウの Issue/PR 切替: /cmux [-n] [-w|-r] <number>"
---

# cmux スキル

cmux のブラウザペインで GitHub Issue/PR を開き、worktree でレビューを行うスキル。

## `-n` フラグ — 新しいターミナルタブで開く

`-n` が指定された場合、処理の **最初に** 現在のペインに新しいターミナルタブ（サーフェス）を作成する:

1. 新しいターミナルサーフェスを作成する:
   ```bash
   NEW_SURFACE=$(cmux --json new-surface | python3 -c "
   import sys, json
   data = json.load(sys.stdin)
   print(data.get('surface_id', data.get('ref', '')))
   ")
   ```
2. 新しいタブに cd を送信する:
   ```bash
   CURRENT_DIR=$(pwd)
   cmux send --surface "$NEW_SURFACE" "cd $CURRENT_DIR"
   cmux send-key --surface "$NEW_SURFACE" Return
   ```
3. 以降の処理（ブラウザ、worktree 等）はこのタブ上で行う。

## ブラウザペインの開き方（共通手順）

すべてのモードで URL をブラウザに表示する際は、**対象の GitHub URL を表示しているブラウザサーフェス** があれば再利用し、なければ新規作成する:

1. 対象 URL を表示しているブラウザサーフェスを探す:
   ```bash
   BROWSER_SURFACE=$(cmux --json list-panels 2>/dev/null | python3 -c "
   import sys, json
   target = '$TARGET_URL'
   data = json.load(sys.stdin)
   for s in data.get('surfaces', []):
       if s.get('type') == 'browser' and target in s.get('url', ''):
           print(s['ref'])
           break
   " 2>/dev/null || echo "")
   ```
2. 見つかった場合はナビゲート（リロード）、なければ新規作成:
   ```bash
   if [ -n "$BROWSER_SURFACE" ]; then
       cmux browser --surface "$BROWSER_SURFACE" navigate "$TARGET_URL"
   else
       cmux browser open-split "$TARGET_URL"
   fi
   ```

## 使い方

### `/cmux <number>` — Issue モード

1. GitHub Issue の URL を構築する:
   ```bash
   REMOTE_URL=$(git remote get-url origin 2>/dev/null)
   REPO_SLUG=$(echo "$REMOTE_URL" | sed -E 's#^(https?://[^/]+/|git@[^:]+:)##; s#\.git$##')
   GITHUB_URL="https://github.com/${REPO_SLUG}/issues/<number>"
   ```
2. 「ブラウザペインの開き方」の共通手順で `TARGET_URL=$GITHUB_URL` として開く。

### `/cmux -w <number>` — PR worktree モード

1. `gh pr view <number>` で PR であることを確認する。PR でなければエラーメッセージを表示して終了。
2. PR の URL を取得する:
   ```bash
   PR_URL=$(gh pr view <number> --json url -q '.url')
   ```
3. 「ブラウザペインの開き方」の共通手順で `TARGET_URL=$PR_URL` として開く。
4. `EnterWorktree` ツールで worktree を作成する。
5. worktree 内で以下を実行:
   ```bash
   gh pr checkout <number>
   ```

### `/cmux -r <number>` — PR レビューモード

1. `gh pr view <number>` で PR であることを確認する。PR でなければエラーメッセージを表示して終了。
2. PR の URL を取得する:
   ```bash
   PR_URL=$(gh pr view <number> --json url -q '.url')
   ```
3. 「ブラウザペインの開き方」の共通手順で `TARGET_URL=$PR_URL` として開く。
4. worktree 内でなければ `EnterWorktree` ツールで worktree を作成する。
5. worktree 内で以下を実行:
   ```bash
   gh pr checkout <number>
   ```
6. PR のコード差分をレビュー開始する（`gh pr diff <number>` で差分を取得し、変更内容を分析）。
