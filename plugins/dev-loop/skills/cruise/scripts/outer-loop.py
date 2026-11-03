#!/usr/bin/env python3
r"""cruise を外から繰り返し起こすループ（外側のループ）。`claude -p "/dev-loop:cruise <親> [--absent]"` を、進められる周があり、
起動のたびに周が進んでいるあいだだけ起こし直す（#791）。

    python3 <このスキルの base ディレクトリ>/scripts/outer-loop.py <親 Issue の番号> [--absent] \
        [--max-launches 20] [--max-stalls 2] [--claude claude] [-- <claude に足す引数> …]

**cruise の既定の回し方は、対話のセッションで 1 度起動して台帳から再開する形である**（cruise の `SKILL.md`）。これは、利用者が
その起動を自分で繰り返す代わりに、決まった条件で止まるループを同梱したもの——プロジェクトごとに手で書いたループは、前進を台帳の
ファイルのハッシュで見て、親が `note` を書き直すだけの起動を前進と読みうる（`ledger.py set` は `updated` を毎回書き換える）。
spec-loop の autopilot（#789）では、止まったことを見落とした外側のループが `claude -p` を約 1,900 回空回りさせた（#790）。

## 1 回の起動

台帳 `issue-<親>`（`../dev-loop/scripts/ledger.py`。このスキルの base ディレクトリからの相対）について、

1. `ledger.py status issue-<親>` を走らせる。**0（親が進められる周がある）のときだけ続ける**——3（人を待つ周だけ）・5（親 Issue の一覧の行が
   すべて済んだ）・4（判定できなかった）・表に無い値では起こさずに止まる。判定の順は `ledger.py` の docstring の「`status` が見るもの」を正とする。
2. `ledger.py progress issue-<親>`（行ごとの番号・`state`・`pr`・`group`。`updated`・`note` を含まない）を控える。
3. 起動の総数が `--max-launches` に達していれば、起こさずに止まる。
4. メインの作業ツリー（台帳と同じ決め方——`ledger.py path` の場所から）を cwd に、標準入力を閉じて

       <--claude> -p "/dev-loop:cruise <親>[ --absent]" --append-system-prompt <追記> [<足す引数> …]

   を起こし、終わるのを待つ。環境には **`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`** を置く——`-p` はターンを閉じた後の背景のタスクを
   上限の時間（既定 10 分）しか待たずに止める（#633。標準エラーの `Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to wait indefinitely.`
   の文言による。0 で止めずに待つことは測っていない）。**利用者の環境に別の値があっても 0 で上書きし、上書きしたことを出す**（`child-cycle.py` と同じ）。
   **追記（`APPEND`）は、非対話の起動の決まりを親に渡す**——権限の判定に拒まれたら周を `await` にして次へ進み、「止まった」と書いて
   ターンを終えない（cruise `SKILL.md` §4 の 5）。進められる周が無いなら台帳を書き換えずにターンを終える（同 §4 の 6）。原本は `SKILL.md` で、追記はそこを指す。
5. `claude` が 0 以外で終わった・起こせなかったら止まる（ログインの期限切れなどで、何も進めずにすぐ終わる起動を繰り返さない）。
6. もう一度 `progress` を取り、2 と同じなら「前進なし」を 1 つ数える。**続けて `--max-stalls` 回になったら止まる**。変わっていれば数を 0 に戻す。

止まるときは、理由を標準出力の最後の行に出し、**通知する**（`osascript` が在れば macOS の通知。本文は argv で渡し、AppleScript の文字列に埋め込まない）。

既定の「前進なし 2 回」は、1 回の起動が周を最後まで進めない（関門の途中で compact した、など）のを 1 度だけ許すためである。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 済んだ——`status` が 5（親 Issue の一覧の行がすべてマージ済みか取り下げ） |
| 2 | 引数が違う（親の番号の形・上限が 1 未満・`--claude` を語に分けられない）。**通知しない**（引数を読む前に止まる） |
| 3 | 人を待つ周だけ——`status` が 3。台帳の `show` の「利用者の判断待ち」「利用者の操作待ち」を見る |
| 4 | 判定できなかった——`status` が 4 か表に無い値・`progress` が 0 以外・`ledger.py` を起こせない・ループの中の予期しない例外。**「済んだ」とも「人待ち」とも答えていない** |
| 6 | 前進なし——`progress` の変わらない起動が続けて `--max-stalls` 回 |
| 7 | 起動の上限——`--max-launches` 回起こした後も `status` が 0 |
| 8 | `claude` が 0 以外で終わった・起こせなかった |
| 130 | 中断された（Ctrl-C・SIGTERM・SIGHUP） |

## 何を守り、何を守らないか

守る:

- **`status` が 0 のときだけ `claude` を起こす**——起動の前に毎回見て、3・4・5・表に無い値では起こさずに止まる。
- **前進は `progress` で比べる**——台帳のファイルのまま比べない（`updated`・`note` だけの書き換えを前進に数えない）。
- **`progress` を読めなければ止まる（4）**——読めない要約を「前進なし」「前進あり」のどちらにも数えない。
- **前進なしの起動が続けて `--max-stalls` 回になったら止まる。**
- **前進があったら、前進なしの数を 0 に戻す**——続けてでない前進なしで止めない。
- **起動の総数が `--max-launches` に達したら、起こさずに止まる。**
- **`claude` が 0 以外で終わった・起こせなかったら止まる。**
- **引数を読めた後の止まるすべての経路で通知する**——済んだ・人待ち・判定できない・前進なし・上限・`claude` の失敗・中断（Ctrl-C・SIGTERM・SIGHUP）・ループの中の予期しない例外。
- **`claude` の cwd はメインの作業ツリー**——worktree の中・サブディレクトリから呼んでも同じ（cruise の親はメインの作業ツリーで起動する。#466）。
- **`claude` の環境に `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` を置く**——利用者の環境に無くても、別の値があっても（上書きしたと出す）。
- **`--append-system-prompt` で追記（`APPEND`）を渡す**——非対話の起動の決まり（拒まれたら `await`・進めないなら台帳を書かない）。
- **`--absent` は渡されたときだけ `/dev-loop:cruise` に付ける**——席を外すかは利用者が決める（cruise `SKILL.md` §3）。

守らない:

- **親が追記に従うか**——`--append-system-prompt` で渡すまでで、本物の `claude -p` で親が拒まれた周を `await` にするか・台帳を書かずに終えるかは測っていない。
- **台帳と実物（PR・worktree）が一致しているか**——`status` も `progress` も台帳の値だけで決める（`ledger.py` の「守らない」）。
- **通知が見えること**——`osascript` が 0 で終わったかも見ない。`osascript` の無い環境（macOS 以外）では通知を出さない（理由は標準出力に出る）。
- **1 回の起動の長さ**——`claude` を待つだけで、時間で打ち切らない。
- **`claude` の版・許可モード・モデル・認証**——足す引数（`--` の後ろ）と `--claude` で利用者が決める（cruise `SKILL.md` §3 の点検）。
  長期トークンの起動口（`../dev-loop/scripts/launch-with-long-token.sh`）に `-p` を渡す形は確かめていない。
- **同じ台帳を回すループ・対話の cruise が他に走っていないか**——台帳を書くのは親 1 体である（`../dev-loop/references/ledger.md`）。
"""

import argparse
import os
import signal
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent.parent / "dev-loop" / "scripts" / "ledger.py"
BG_CEILING = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"
# 非対話の起動の決まり（#791）。原本は cruise の SKILL.md §4 の 5・6——ここはそれを指す 2 文だけ
APPEND = (
    "この起動は cruise の外側のループ（outer-loop.py）が起こした非対話の起動で、利用者は応答しない（#791）。"
    "権限の判定（自動モードの分類器・許可リスト・ガード）に操作を拒まれたら、cruise の SKILL.md の「4. 周を回す」の 5 のとおり、"
    "その周を `ledger.py set … state=await note=<打ってほしいコマンド>` にして依存しない次の周へ進む——「止まった」と書いてターンを終えない。"
    "進められる周が無いなら、台帳を書き換えずにターンを終える——確かめた回数・時刻・「変わらず」を `note` に書かない（同じ「4. 周を回す」の 6）。"
)
TITLE = "cruise の外側のループが止まりました"

EXIT_DONE = 0
EXIT_USAGE = 2
EXIT_WAITING = 3
EXIT_UNKNOWN = 4
EXIT_STALLED = 6
EXIT_LIMIT = 7
EXIT_CLAUDE = 8
EXIT_INTERRUPTED = 130


def ledger(*args):
    """(終了コード, 標準出力)。起こせなければ (None, 理由)。"""
    try:
        r = subprocess.run([sys.executable, str(LEDGER), *args], capture_output=True, text=True)
    except OSError as exc:
        return None, f"ledger.py を起こせない: {exc}"
    if r.stderr:
        sys.stderr.write(r.stderr)
    return r.returncode, r.stdout


def progress(name):
    code, out = ledger("progress", name)
    return out if code == 0 else None


def notify(body):
    if not shutil.which("osascript"):
        return
    # 値は argv で渡す（AppleScript の文字列に埋め込まない）
    script = ("on run argv\n"
              "display notification (item 1 of argv) with title (item 2 of argv)\n"
              "end run")
    try:
        subprocess.run(["osascript", "-e", script, body, TITLE],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def launch(args, main_tree):
    prompt = f"/dev-loop:cruise {args.parent}" + (" --absent" if args.absent else "")
    cmd = [*args.claude_cmd, "-p", prompt, "--append-system-prompt", APPEND, *args.extra]
    env = dict(os.environ)
    if env.get(BG_CEILING) not in (None, "0"):
        print(f"{BG_CEILING}={env[BG_CEILING]} を 0 で上書きした")
    env[BG_CEILING] = "0"
    print(f"起こす: {shlex.join(cmd[:3])} …（cwd: {main_tree}）", flush=True)
    try:
        return subprocess.run(cmd, cwd=main_tree, stdin=subprocess.DEVNULL, env=env).returncode
    except OSError as exc:
        print(f"claude を起こせない: {exc}", file=sys.stderr)
        return None


def run_loop(args):
    """(終了コード, 理由)。"""
    name = f"issue-{args.parent}"
    code, out = ledger("path", name)
    if code != 0:
        return EXIT_UNKNOWN, f"台帳の場所を決められない（ledger.py path: {code}）"
    main_tree = Path(out.strip()).parent.parent.parent
    launches = stalls = 0
    while True:
        code, out = ledger("status", name)
        print(f"status: {code} {out.strip()}", flush=True)
        if code == 5:
            return EXIT_DONE, f"済んだ（{out.strip()}）"
        if code == 3:
            return EXIT_WAITING, f"人を待つ周だけ（{out.strip()}）"
        if code != 0:
            return EXIT_UNKNOWN, f"判定できなかった（status: {code}）"
        before = progress(name)
        if before is None:
            return EXIT_UNKNOWN, "判定できなかった（progress を読めない）"
        if launches >= args.max_launches:
            return EXIT_LIMIT, f"起動の上限 {args.max_launches} 回に達した（status は 0 のまま）"
        launches += 1
        rc = launch(args, main_tree)
        if rc != 0:
            return EXIT_CLAUDE, f"claude が失敗した（{rc if rc is not None else '起こせない'}・{launches} 回目の起動）"
        after = progress(name)
        if after is None:
            return EXIT_UNKNOWN, "判定できなかった（progress を読めない）"
        if after == before:
            stalls += 1
            print(f"前進なし（続けて {stalls} 回）", flush=True)
            if stalls >= args.max_stalls:
                return EXIT_STALLED, f"前進なしが続けて {stalls} 回（{launches} 回目の起動）"
        else:
            stalls = 0


def build_parser():
    p = argparse.ArgumentParser(description="cruise を外から繰り返し起こすループ（#791）")
    p.add_argument("parent", help="親 Issue の番号")
    p.add_argument("--absent", action="store_true", help="/dev-loop:cruise に --absent を付ける")
    p.add_argument("--max-launches", type=int, default=20, help="起動の総数の上限（既定 20）")
    p.add_argument("--max-stalls", type=int, default=2, help="前進なしが続けてこの回数で止まる（既定 2）")
    p.add_argument("--claude", default="claude", help="claude を起こすコマンド（既定 claude）")
    return p


class Interrupted(Exception):
    """SIGTERM・SIGHUP を受けた。"""


def _on_signal(signum, _frame):
    raise Interrupted(signal.Signals(signum).name)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # `--` の後ろは claude に足す引数。argparse に任せない——Python 3.11 以前は、位置引数の後に選択肢があると `--` の後ろを拒む
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    head = argv[:argv.index("--")] if "--" in argv else argv
    try:
        args = build_parser().parse_args(head)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else 0
    args.extra = extra
    try:
        args.claude_cmd = shlex.split(args.claude)
    except ValueError:
        args.claude_cmd = []
    if (not args.parent.isdigit() or int(args.parent) <= 0 or args.max_launches < 1 or args.max_stalls < 1
            or not args.claude_cmd):
        print("引数が違う: 親は正の番号、上限は 1 以上、--claude は語に分けられるコマンド", file=sys.stderr)
        return EXIT_USAGE
    args.parent = str(int(args.parent))
    saved = {s: signal.signal(s, _on_signal) for s in (signal.SIGTERM, signal.SIGHUP)}
    try:
        code, reason = run_loop(args)
    except KeyboardInterrupt:
        code, reason = EXIT_INTERRUPTED, "中断された"
    except Interrupted as exc:
        code, reason = EXIT_INTERRUPTED, f"中断された（{exc}）"
    except Exception as exc:  # noqa: BLE001 — どの経路でも通知する（守る）
        code, reason = EXIT_UNKNOWN, f"判定できなかった（予期しない例外: {type(exc).__name__}: {exc}）"
    finally:
        for s, h in saved.items():
            signal.signal(s, h)
    line = f"外側のループ: 止まった（issue-{args.parent}: {reason}）"
    print(line, flush=True)
    notify(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
