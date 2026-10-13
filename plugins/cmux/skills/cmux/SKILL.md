---
name: cmux
description: "cmux のブラウザペインで GitHub Issue/PR を開く。番号だけなら Issue を表示、-w は PR を表示して worktree で gh pr checkout、-r はさらに gh pr diff でレビューを始める。-n は先に新しいターミナルタブを作る。cmux の中で Issue/PR を見たい・PR をローカルでレビューしたいときに使う。引数: [-n] [-w|-r] <number>"
---

# cmux スキル

<!-- skill-version: 1.1.8 -->
> **このスキルの版: 1.1.8**（プラグイン `cmux`）。
> 手元で読まれている版がリポジトリの最新より古いなら、
> `/plugin marketplace update` → `/plugin update cmux@claude-code-setup` の順に実行し、
> Claude Code を再起動する（[#63](https://github.com/hdknr/claude-code-setup/issues/63)）。

cmux のブラウザペインで GitHub Issue/PR を開き、worktree でレビューを行うスキル。

**呼び出し形**: プラグインとして入れた場合は `/cmux:cmux`（プラグイン提供のスキルは常に
プラグイン名で名前空間化される）。マニフェスト（`.claude-plugin/`）を持たない素のスキルとして
skills ディレクトリに置いた場合は `/cmux`（`~/.claude/skills/cmux/` なら全プロジェクト、
`<プロジェクト>/.claude/skills/cmux/` ならそのプロジェクトだけ）。
以下の本文は短い方の `/cmux` で表記する。

## `-n` フラグ — 新しいターミナルタブで開く

`-n` が指定された場合、処理の **最初に** 現在のペインに新しいターミナルタブ（サーフェス）を、
現在のディレクトリを作業ディレクトリにして作成する。非ゼロなら終了する:

```bash
cmux new-surface --working-directory "$(pwd)"
```

- **cd を送らない**（`cmux send "cd …"` を使わない）——送った文字列はシェルが解釈するので、
  **空白や単引用符を含むパスで壊れる**。`--working-directory` はシェルを通らない。
- **作ったサーフェスの ref を取り出して後から操作する形にしない**——取り出し方が版に依る
  （cmux 0.65.1 の `new-surface --json` は `surface_ref` を返し、`surface_id`・`ref` は無い）。
  取り損ねた空の ref で `send` すると、行き先が新しいタブではなくなる。

以降の処理（ブラウザ、worktree 等）を続ける。

## ブラウザペインの開き方（共通手順）

すべてのモードで URL をブラウザに表示する際は、**対象の GitHub URL を表示しているブラウザサーフェス** があれば再利用し、なければ新規作成する:

- **一致は「完全一致、または直後が `/` `#` `?`」に限る**——部分一致にすると
  `/issues/19` を開くときに `/issues/194` のサーフェスを再利用して上書きする。
- **完全一致のサーフェスを先に探し、無いときだけ下位ページ（直後が `/` `#` `?`）のサーフェスを使う**——
  先頭から順に取ると、`/pull/12/files` のサーフェスが手前にあるだけで、`/pull/12` のサーフェスがあっても
  `/pull/12/files` のほうを上書きする。
- **`list-panels` がブラウザサーフェスの `url` を返さない版がある**（cmux 0.65.1 で実測）。
  そのときは `cmux --json browser --surface <ref> url` で 1 枚ずつ取る——取らないと一致が
  1 度も起きず、開くたびにサーフェスが増える。
- **1 行目の `TARGET_URL=` を各モードの指示どおりに置き換え、ブロック全体を 1 回の Bash 呼び出しで流す。**
  呼び出しを分けるとシェル変数が消え、`BROWSER_SURFACE` が空になって毎回サーフェスが増える。
  `TARGET_URL` が空のまま探すと、URL を取れなかったサーフェス（空文字列）と一致して上書きするので、
  2 行目で `https://` で始まらない URL を拒否する。

URL は文字列に埋め込まず引数で渡す。`python3` は `-I` で起動する——無いと、カレントディレクトリ
（レビュー対象のリポジトリ）に置かれた `json.py`・`subprocess.py` が import されて走る:

```bash
TARGET_URL="<各モードで決める URL>"
case "$TARGET_URL" in https://*) ;; *) echo "URL を決められない: $TARGET_URL" >&2; exit 1 ;; esac
BROWSER_SURFACE=$(cmux --json list-panels 2>/dev/null | python3 -I -c "
import sys, json, subprocess
target = sys.argv[1]
data = json.load(sys.stdin)
def url_of(s):
    if s.get('url'):
        return s['url']
    try:
        out = subprocess.run(['cmux', '--json', 'browser', '--surface', s['ref'], 'url'],
                             capture_output=True, text=True, timeout=10).stdout
        return json.loads(out).get('url') or ''
    except Exception:
        return ''
urls = [(s, url_of(s)) for s in data.get('surfaces', []) if s.get('type') == 'browser']
hit = [s for s, u in urls if u == target] or \
      [s for s, u in urls if u.startswith(target) and u[len(target)] in '/#?']
if hit:
    print(hit[0]['ref'])
" "$TARGET_URL" 2>/dev/null || echo "")
if [ -n "$BROWSER_SURFACE" ]; then
    cmux browser --surface "$BROWSER_SURFACE" navigate "$TARGET_URL"
else
    cmux browser open-split "$TARGET_URL"
fi
```

## 使い方

### `/cmux <number>` — Issue モード

1. 「ブラウザペインの開き方」の共通手順を、1 行目を次に置き換えて流す:
   ```bash
   TARGET_URL="https://github.com/$(git remote get-url origin 2>/dev/null | sed -E 's#^(https?://[^/]+/|git@[^:]+:)##; s#\.git$##')/issues/<number>"
   ```

### `/cmux -w <number>` — PR worktree モード

1. `gh pr view <number>` で PR であることを確認する。PR でなければエラーメッセージを表示して終了。
2. 「ブラウザペインの開き方」の共通手順を、1 行目を次に置き換えて流す
   （`gh pr view` が失敗すると `TARGET_URL` が空になり、共通手順の 2 行目で止まる）:
   ```bash
   TARGET_URL=$(gh pr view <number> --json url -q '.url')
   ```
3. `EnterWorktree` ツールで worktree を作成する。
4. worktree 内で以下を実行:
   ```bash
   gh pr checkout <number>
   ```

### `/cmux -r <number>` — PR レビューモード

1. `gh pr view <number>` で PR であることを確認する。PR でなければエラーメッセージを表示して終了。
2. 「ブラウザペインの開き方」の共通手順を、1 行目を次に置き換えて流す
   （`gh pr view` が失敗すると `TARGET_URL` が空になり、共通手順の 2 行目で止まる）:
   ```bash
   TARGET_URL=$(gh pr view <number> --json url -q '.url')
   ```
3. worktree 内でなければ `EnterWorktree` ツールで worktree を作成する。
4. worktree 内で以下を実行:
   ```bash
   gh pr checkout <number>
   ```
5. PR のコード差分をレビュー開始する（`gh pr diff <number>` で差分を取得し、変更内容を分析）。
