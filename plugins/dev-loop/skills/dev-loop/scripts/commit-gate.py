#!/usr/bin/env python3
"""`git commit` に検証の印（`Verified:` のトレーラー）があるかを見る、任意の PreToolUse hook（#1192）。

**このプラグインは hook を登録しない**（`hooks.json` を持たない）。入れるのは利用者で、`settings.json` の PreToolUse に
このスクリプトを書く（書き方は `references/verification-trailer.md`）。**登録しなければ何も起きない**——既定は off。

## 使い方

- **hook として（引数なし）**: stdin に PreToolUse の JSON（`tool_name`・`tool_input.command`・`cwd`）を受ける。
  Bash の `git commit` だけを見て（`git commit-tree`・引用符やヒアドキュメントの中の `git commit` は見ない）、コミットメッセージに `Verified:` の行があるかを数える。
  モードは**メインの作業ツリー**の `.claude/dev-loop.md`（worktree の中の写しは読まない。周のブランチの変更でモードが変わらないように）の `検証の関門: off|observe|enforce` の行（既定 `off`）で決まる。
  - `off`: 何もしない（記録もしない）。
  - `observe`: 通す（終了コード 0）。「止めていたはず」を記録に 1 行残す。
  - `enforce`: 満たさないコミットを止める（終了コード 2 と、直し方を stderr に出す）。
- `status`: いま効いているモードと逃げ道、設定の誤りを出す。読むだけ。
- `report`: 記録を数える（通した・止めていたはず・止めた、と理由ごと）。**止めていたはずの 1 件ずつを出す**——
  誤検知かどうかを判定するのは人間である（このスクリプトは判定しない）。

## 満たす条件（`Verified:` の行）

`Verified: <手段>[,<手段>…]`（手段は `tests`・`gates`・`verify`・`code-review`）か、`Verified: none (<理由>)`。
**満たさない形**: 行が無い（`missing`）・手段が上に無い／空（`malformed`）・`none` に理由が無い（`none_without_reason`）・
**逃げ道が `なし` のとき `none` そのもの**（`none_not_allowed`）。
逃げ道は `検証の関門の逃げ道: 理由を書けば通す|なし`（既定 `理由を書けば通す`）。

## 記録の置き場所

`git rev-parse --git-common-dir` の下の `dev-loop-gate.jsonl`（全 worktree で共有。リポジトリの外に出ないので commit されない）。
`DEV_LOOP_GATE_LOG` で差し替えられる（テスト用）。

## 守ること

- **hook として、判定できないときは通す**（stdin が JSON でない・`git` が使えない・設定の誤り）。**`-F` のファイルが読めないときは、メッセージが空として満たさない扱い（`missing`）になる**（git 自体もそのコミットに失敗する）。**`enforce` でもそう**——
  hook は壊れても止めない側に倒す（止めると利用者の作業を巻き込む）。**だから `enforce` は保証ではない**（下）。
- **設定の誤り（値が表に無い・同じ行が 2 本以上）は `off`**。止める側に倒さない。誤りは `status` が名指しする。
- **コードフェンスと HTML コメントの中の行は設定として読まない。**
- 記録に書くのは、時刻・モード・結果・理由・cwd・コマンドの**先頭 120 文字**だけ。メッセージ全文は書かない。
- **ヒアドキュメントは、引用符の外の `<<` で始まるものだけを読む**（二重引用符の中の `$( … )` の中——`-m "$(cat <<'EOF' … )"`——は外と同じに読む）。
  `-m 'docs: explain <<EOF usage'` の引用符の中の `<<` を始まりと読んで、後ろの別のコマンドのヒアドキュメントの本文を拾わない（#1368 の V1）。
- **ヒアドキュメント（stdin）を判定の文面に足すのは、メッセージを stdin から読む形（`-F -`・`--file=-`。前の `cat <<EOF |` のパイプを含む）だけ**——
  `-m`・`-F <ファイル>`・`-C`・エディタの形では git は stdin を読まない（#1368 の V2）。

## 守らないこと

- **`Verified:` の中身が事実かは見ない。** 手段を名乗っているか（形）しか見ない。**どの関門を通したかの突き合わせは
  `check-gates.py`**（計画ファイルの記録と履歴）で、これは別。
- **hook が動かない環境では何も止まらない**（python3 が無い・hook が登録されていない・Claude Code が hook を読まない）。
  **このスクリプトは、本物の Claude Code に登録して発火させた検証をしていない**——テストは hook の stdin を
  真似て呼ぶ（`scripts/test-commit-gate.py`）。stdin の鍵と終了コード 2 の意味は公式の説明に従った。
- **`git commit` を直接呼ばない形**（`git` の別名・スクリプトの中のコミット・IDE のコミット・`bash -c "…"`・`git --git-dir <パス> commit`）は見ない。
  `if`・`then`・`{ … }`・`env`・`sudo`・`time`・`command`・環境変数の前置の後ろの `git commit` は見る。**`cd <dir> && git commit -F <相対パス>` は、hook の cwd からの相対で読むので外れる。**
- **値の読み方**: 閉じの引用符（後ろが空白・行末・区切り）か文字のままの `\\n` で値が終わる。理由の中の「引用符＋空白」で値が切れる。`Verified:` は行頭か引用符の直後に無いと読まない（`-m x -m Verified:tests` は読めない）。
- `-C`／`-c`（メッセージの再利用）と、エディタを開くコミットはメッセージを読めず、`missing` になる。
- **マージの締め（`MERGE_HEAD` がある）と、メッセージを渡さない `--no-edit` は見ない**（通す。記録もしない）。`--no-edit` でも `-m` を渡すコミットは見る。
- **連結したコマンドは、`git commit` の呼び出しごとに、その呼び出しの部分だけを読む**（別のコミットや別のコマンドの `Verified:` の行を拾わない）。1 本でも満たさなければ止める。
- `--amend` でメッセージを渡さないときは、直前のコミットのメッセージを読む。
- **同じセッションで 2 回止めたら次は通す、という逃げ道は採っていない**（セッションの状態を持つ必要がある）。

終了コード（hook）: 0 通す／2 止める（enforce のみ）。`status`・`report`: 0 表示した／3 記録が無い（`report`）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

MODES = ("off", "observe", "enforce")
ESCAPES = ("理由を書けば通す", "なし")
DEFAULT_MODE = "off"
DEFAULT_ESCAPE = "理由を書けば通す"
METHODS = ("tests", "gates", "verify", "code-review")

# 引用符の中とヒアドキュメントの本体を消した「骨組み」に当てる（`gh ... --body "git commit"`・`git commit-tree` に当てないため）
GIT_COMMIT = re.compile(
    r"(?:^|[;&|(\n{])[ \t]*(?:(?:if|then|else|elif|while|until|do|time|sudo|nohup|command|exec|env|!)[ \t]+)*"
    r"(?:\w+=\S*[ \t]+)*(?:\S*/)?git"
    r"(?:[ \t]+(?:-C[ \t]+\S+|-c[ \t]+\S+|--[\w-]+(?:=\S+)?))*[ \t]+commit(?=[ \t\n;&|)]|$)"
)
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)([\w.\-]+)\1[^\n]*\n.*?\n[ \t]*\2[ \t]*\r?(?=\n|$)", re.DOTALL)
SEGMENT_END = re.compile(r"&&|\|\||;|\||\n")
# パイプライン（`|` でつないだ並び）の区切り。単独の `|` は区切らない
# `{ cat <<EOF; } | git commit -F -` の `}` の前の `;` は区切らない
PIPELINE_BOUND = re.compile(r"&&|\|\||;(?![ \t]*\})|\n")
# メッセージのファイルを渡す引数（-F <x>・-F<x>・--file=<x>・--file <x>）。<x> は骨組みの上の位置で取り、元の文字列から読む
FILE_ARG = re.compile(r"(?:^|\s)(?:-[a-zA-Z]*F[ \t]*|--file(?:=|[ \t]+))([^\s;&|)<>]+)")
# ヒアドキュメントの本文をファイルに書く形（`cat > m.txt <<EOF`・`cat <<EOF >> m.txt`・`tee [-a] m.txt <<EOF`）。ファイル名は 1 番目の組
WRITE_TO = re.compile(r"(?:>>?|\btee(?:[ \t]+-a)?)[ \t]*([^\s;&|)<>]+)")
# git が stdin から読むファイルの名前（引用符を外した形）
STDIN_NAMES = ("-", "/dev/stdin", "/dev/fd/0")
# 行頭・引用符の直後・文字のままの `\n` の直後の `Verified:`（-m を 2 本渡す形・$'…' の形も読む）
TRAILER = re.compile(r"(?:^|[\"']|\\n)[ \t]*Verified:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
# 値の終わり: 閉じの引用符（後ろが空白・行末・区切り・リダイレクト）と、文字のままの `\n`。
# 理由の中に「引用符＋空白」を書くと、そこで値が切れる（`none (skip "a" b)` は malformed）
VALUE_END = re.compile(r"""["'](?=\s|$|[;&|)<>])""")
QUOTED = re.compile(r"\"(?:\\.|[^\"\\])*\"|'[^']*'")
NONE_FORM = re.compile(r"^none(?:[ \t]*[(（](.*)[)）])?$")
FENCE = re.compile(r"^[ \t]*(```|~~~)")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
HEAD_LEN = 120

GUIDE = (
    "コミットメッセージの最後の段落に検証の印を付けてください: "
    "`Verified: tests,gates,verify,code-review` のうち実際に回したものだけ（回していない手段は書かない）、"
    "何も回していなければ `Verified: none (理由)`。"
)


def strip_noise(text: str) -> str:
    """コードフェンスと HTML コメントの中を消す（そこに書いた設定の行は設定ではない）。"""
    text = COMMENT.sub("", text)
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def read_setting(text: str, key: str, allowed: tuple[str, ...], default: str) -> tuple[str, str | None]:
    """`<key>: <値>` の行を読む。(値, 誤りの説明)。誤りは既定に倒す。"""
    pat = re.compile(rf"^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
    clean = strip_noise(text)
    values = pat.findall(clean)
    if not values:
        keyed = re.compile(rf"^[ \t>*+`|\-]*{re.escape(key)}[*` \t]*[:：=|]")
        loose = [ln for ln in clean.splitlines() if keyed.match(ln)]
        if loose:
            return default, f"`{key}` を含む行が行頭から `{key}: <値>` の形でない（{loose[0].strip()[:40]!r}）ので読まなかった"
        return default, None
    if len(values) > 1:
        return default, f"`{key}:` の行が {len(values)} 本ある（1 本にまとめる）"
    if values[0] not in allowed:
        return default, f"`{key}:` の値 {values[0]!r} は {' / '.join(allowed)} のどれでもない"
    return values[0], None


def git(cwd: str, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, errors="replace", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def load_config(cwd: str) -> tuple[str, str, list[str]]:
    """(モード, 逃げ道, 誤りの一覧)。.claude/dev-loop.md が無ければ既定。"""
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common or Path(common).name != ".git":
        return DEFAULT_MODE, DEFAULT_ESCAPE, ["メインの作業ツリーが決まらない（.git でない共通ディレクトリ・submodule・bare・"
                                              "`--path-format=absolute` を持たない git 2.31 未満）ので設定を読まない"]
    path = Path(common).parent / ".claude" / "dev-loop.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_MODE, DEFAULT_ESCAPE, []
    mode, e1 = read_setting(text, "検証の関門", MODES, DEFAULT_MODE)
    esc, e2 = read_setting(text, "検証の関門の逃げ道", ESCAPES, DEFAULT_ESCAPE)
    errors = [e for e in (e1, e2) if e]
    return mode, esc, errors


def hide_quoted_heredoc_ops(text: str) -> str:
    """引用符の中の `<<` を、**同じ長さで**別の文字に置き換えた写し（#1368 の V1）。

    `-m 'docs: explain <<EOF usage' && cat <<'EOF'` の引用符の中の `<<EOF` を、ヒアドキュメントの始まりと読まないため。
    引用符の外の `<<` と、二重引用符の中の `$( … )`・`` `…` `` の `<<`（`-m "$(cat <<'EOF' … )"`）は残す。
    ヒアドキュメントの本体は跳ばす（本体の `'`・`"` を引用符と読まない）。
    """
    chars = list(text)
    stack: list[str] = []  # '"'（二重引用符の中）か '$(' と '`'（コマンド置換の中。引用符の外と同じに辿る）
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if stack and stack[-1] == '"':
            if c == "\\":
                i += 2
            elif c == '"':
                stack.pop()
                i += 1
            elif text.startswith("$(", i):
                stack.append("$(")
                i += 2
            elif c == "`":
                stack.append("`")
                i += 1
            elif text.startswith("<<", i):
                chars[i] = chars[i + 1] = "\x02"
                i += 2
            else:
                i += 1
            continue
        if c == "\\":  # 引用符の外の `\"`・`\'` は文字（引用符の始まりではない）
            i += 2
        elif c == "'":
            j = text.find("'", i + 1)
            if j < 0:
                i += 1  # 閉じない単一引用符は文字のまま（QUOTED と同じ）
                continue
            for k in range(i, j):
                if text.startswith("<<", k):
                    chars[k] = chars[k + 1] = "\x02"
            i = j + 1
        elif c == '"':
            stack.append('"')
            i += 1
        elif text.startswith("$(", i):
            stack.append("$(")
            i += 2
        elif c == ")" and stack and stack[-1] == "$(":
            stack.pop()
            i += 1
        elif c == "`":  # 逆引用符のコマンド置換は、閉じで抜け、開きで入る
            if stack and stack[-1] == "`":
                stack.pop()
            else:
                stack.append("`")
            i += 1
        elif text.startswith("<<", i) and (m := HEREDOC.match(text, i)):
            i = m.end()
        else:
            i += 1
    return "".join(chars)


def skeleton(command: str) -> str:
    """ヒアドキュメントの本体と引用符の中を、**同じ長さで**消す（コマンドの形だけを残す。位置は元の文字列と同じ）。"""
    out = command.replace("\\\n", "  ")  # 行継続は空白に畳む
    out = hide_quoted_heredoc_ops(out)  # 引用符の中の `<<` を始まりと読まない（#1368）

    def heredoc(m: re.Match) -> str:
        first, _, rest = m.group(0).partition("\n")
        return first + "\x01" + "_" * len(rest)

    out = HEREDOC.sub(heredoc, out)
    return QUOTED.sub(lambda m: m.group(0)[0] + "_" * (len(m.group(0)) - 2) + m.group(0)[-1], out)


def heredoc_text(command: str, a: int, b: int) -> str:
    """その commit の部分（a〜b）で始まるヒアドキュメントの本文（`git commit -F - <<EOF && git push` の形）。

    **引用符の外の `<<` で始まるものだけ**（#1368 の V1）。**メッセージを stdin から読む形（`-F -`・`--file=-`・`-F /dev/stdin`。引用符つきも）のコミットでだけ数える**——
    ほかの形（`-m`・`-F <ファイル>`・`-C`・エディタ）では git は stdin を読まない（#1368 の V2。`-m "$(cat <<'EOF' … )"` の本文は、その commit の部分の中にある）。
    例外は、`-F <ファイル>` のファイルを同じコマンドの前のヒアドキュメントが `> <ファイル>`・`tee <ファイル>` で書く形——最後に書いた本文を読む。
    """
    folded = command.replace("\\\n", "  ")
    shape = skeleton(command)  # 骨組み（引用符の中を消した形）
    found = list(HEREDOC.finditer(hide_quoted_heredoc_ops(folded)))
    args = [folded[x.start(1):x.end(1)].strip("'\"") for x in FILE_ARG.finditer(shape, a, b)]
    if any(x in STDIN_NAMES for x in args):
        # パイプで commit の stdin に渡るヒアドキュメント（`cat <<'EOF' | git commit -F -`）も数える——同じパイプラインの始まりから数える
        bounds = [x.end() for x in PIPELINE_BOUND.finditer(shape, 0, a)]
        start = bounds[-1] if bounds else 0
        return "".join("\n" + folded[m.start():m.end()] for m in found if start <= m.start() < b)
    # `-F <ファイル>` で、そのファイルを同じコマンドの前のヒアドキュメントが書く形（`cat > m.txt <<'EOF' && git commit -F m.txt`）——
    # hook の時点ではファイルがまだ無いので、書くヒアドキュメントの本文を読む
    # 書き込みは骨組みの上で探し（引用符の中の `> x` を書き込みと読まない）、ファイル名は元の文字列から読む。同じファイルを何度も書くなら最後のものだけ
    out = []
    for path in args:
        last = None
        for m in found:
            if m.start() >= a:
                continue
            start = folded.rfind("\n", 0, m.start()) + 1
            end = folded.find("\n", m.start())
            for w in WRITE_TO.finditer(shape, start, end if end >= 0 else len(folded)):
                if os.path.normpath(folded[w.start(1):w.end(1)].strip("'\"")) == os.path.normpath(path):
                    last = m
        if last is not None:
            out.append("\n" + folded[last.start():last.end()])
    return "".join(out)


def find_commits(command: str) -> tuple[str, list[tuple[int, int]]]:
    """(骨組み, `git commit` の呼び出しごとの、続く部分の範囲（次の `&&`・`;`・`|`・改行まで）)。範囲は元の文字列にも当たる。

    **ヒアドキュメントの本体はその範囲に入れない**（`<<EOF` の行の終わりで切る）——本体は `heredoc_text` が、数えてよいときだけ足す（#1368 の V2）。
    """
    skel = skeleton(command)
    spans = []
    for m in GIT_COMMIT.finditer(skel):
        end = SEGMENT_END.search(skel, m.end())
        stop = end.start() if end else len(skel)
        body = skel.find("\x01", m.end(), stop)  # 骨組みでは、ヒアドキュメントの本体の前の改行が \x01 になっている
        if body >= 0 and skel.count("$(", m.end(), body) > skel.count(")", m.end(), body):
            body = -1  # 引用符の無い `$( … )` の中のヒアドキュメントは、その commit の引数の一部（切らない）
        spans.append((m.end(), body if body >= 0 else stop))
    return skel, spans


def merge_in_progress(cwd: str) -> bool:
    return git(cwd, "rev-parse", "-q", "--verify", "MERGE_HEAD") is not None


def clean_value(value: str) -> str:
    """トレーラーの値から、コマンドの続き（閉じの引用符以降）と文字のままの `\\n` 以降を落とす。"""
    value = value.split("\\n")[0]
    m = VALUE_END.search(value)
    return (value[:m.start()] if m else value).strip()


def has_message_flag(segment: str) -> bool:
    return bool(re.search(r"(?:^|\s)(?:-[a-zA-Z]*m(?=[\s=\"']|$)|--message\b|-F\b|--file\b)", segment)) or "<<" in segment


def commit_message_text(command: str, segment: str, cwd: str) -> str:
    """判定に使うメッセージの文面。**その 1 回の commit の部分**（-m・ヒアドキュメント）＋ -F のファイル＋ amend の直前のメッセージ。"""
    text = command
    for m in re.finditer(r"(?:-F|--file)(?:=|\s+)(\S+)", command):
        p = Path(m.group(1).strip("'\""))
        p = p if p.is_absolute() else Path(cwd) / p
        try:
            text += "\n" + p.read_text(encoding="utf-8")
        except (OSError, ValueError):
            pass
    if re.search(r"--amend\b", segment) and (not has_message_flag(segment) or "--no-edit" in segment):
        prev = git(cwd, "log", "-1", "--format=%B")
        if prev:
            text += "\n" + prev
    return text


def judge(text: str, escape: str) -> str | None:
    """満たさない理由の名前。満たせば None。"""
    found = TRAILER.findall(text)
    if not found:
        return "missing"
    value = clean_value(found[-1])
    m = NONE_FORM.match(value)
    if m:
        if not (m.group(1) or "").strip():
            return "none_without_reason"
        return "none_not_allowed" if escape == "なし" else None
    tokens = [t.strip() for t in value.split(",")]
    if all(t in METHODS for t in tokens):
        return None
    return "malformed"


def log_path(cwd: str) -> Path | None:
    env = os.environ.get("DEV_LOOP_GATE_LOG")
    if env:
        return Path(env)
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) / "dev-loop-gate.jsonl" if common else None


def write_log(cwd: str, record: dict) -> None:
    p = log_path(cwd)
    if p is None:
        return
    try:
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"検証の関門: 記録を書けなかった（{exc}）", file=sys.stderr)


def hook() -> int:
    try:
        data = json.load(sys.stdin)
        command = data["tool_input"]["command"]
        tool = data.get("tool_name", "Bash")
        cwd = data.get("cwd") or os.getcwd()
    except (ValueError, KeyError, TypeError):
        return 0  # 判定できないときは通す
    if tool != "Bash" or not isinstance(command, str):
        return 0
    skel, spans = find_commits(command)
    spans = [(a, b) for a, b in spans if "--dry-run" not in skel[a:b]]
    if not spans:
        return 0
    mode, escape, errors = load_config(cwd)
    if mode == "off":
        return 0
    judged, reason = False, None
    for a, b in spans:  # 1 回ずつ、その commit の部分だけを見る（1 本でも満たさなければ止める）
        segment = skel[a:b]
        if merge_in_progress(cwd) or ("--no-edit" in segment and "--amend" not in segment and not has_message_flag(segment)):
            continue  # マージの締め・メッセージを渡さない --no-edit は、メッセージを読めない（見ない）
        judged = True
        reason = judge(commit_message_text(command[a:b] + heredoc_text(command, a, b), segment, cwd), escape)
        if reason:
            break
    if not judged:
        return 0
    action = "pass" if reason is None else ("would_stop" if mode == "observe" else "stopped")
    write_log(cwd, {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "mode": mode, "action": action,
        "reason": reason, "cwd": cwd, "command_head": command[:HEAD_LEN],
    })
    if action == "stopped":
        print(f"検証の関門（enforce）: コミットを止めた（{reason}）。{GUIDE}", file=sys.stderr)
        return 2
    return 0


def status(project: str) -> int:
    mode, escape, errors = load_config(project)
    print(f"検証の関門: {mode}（既定 {DEFAULT_MODE}）／逃げ道: {escape}（既定 {DEFAULT_ESCAPE}）")
    for e in errors:
        print(f"設定の誤り（既定に倒した）: {e}")
    return 0


def report(log: str | None, since: str | None, cwd: str) -> int:
    p = Path(log) if log else log_path(cwd)
    if p is None or not p.exists():
        print("検証の関門: 記録が無い")
        return 3
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if since and r.get("ts", "") < since:
            continue
        rows.append(r)
    counts: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for r in rows:
        counts[r.get("action", "?")] = counts.get(r.get("action", "?"), 0) + 1
        if r.get("reason"):
            reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    print(f"検証の関門の記録: {len(rows)} 件（{p}）")
    print("  結果: " + "・".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print("  理由: " + ("・".join(f"{k} {v}" for k, v in sorted(reasons.items())) or "なし"))
    stops = [r for r in rows if r.get("action") in ("would_stop", "stopped")]
    for r in stops:
        print(f"  [{r.get('action')}] {r.get('ts')} {r.get('reason')} — {r.get('command_head')}")
    print("誤検知かは、上の 1 件ずつを人が見て決める（このスクリプトは判定しない）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")
    sp = sub.add_parser("status")
    sp.add_argument("--project", default=os.getcwd())
    rp = sub.add_parser("report")
    rp.add_argument("--log")
    rp.add_argument("--since", help="ISO 時刻（これ以降の記録だけ数える）")
    rp.add_argument("--project", default=os.getcwd())
    args = ap.parse_args()
    if args.cmd == "status":
        return status(args.project)
    if args.cmd == "report":
        return report(args.log, args.since, args.project)
    return hook()


if __name__ == "__main__":
    sys.exit(main())
