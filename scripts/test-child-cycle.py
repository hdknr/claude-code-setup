#!/usr/bin/env python3
"""`child-cycle.py`（cruise の周を `claude -p` の子プロセスで回す起動口と要約。#491）の回帰テスト。

    python3 scripts/test-child-cycle.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/`）。`test-parent-issue.py` と同じ形——
**`dev-loop` はどのリポジトリでも使えるプラグイン**なので、本体は対象リポジトリの `scripts/` に在ることを当てにできない。

**このテストは実環境を触らず、本物の `claude` を起こさない。** 毎回テンポラリに本物の git リポジトリと worktree を作り、
`PATH` の先頭に置いた偽の `claude`（受けた引数・cwd・セッション・標準入力・環境の `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` と、
環境の `CLAUDE_CODE_OAUTH_TOKEN` が試料のどの値か（**値は書かない**）を記録し、試料の stream-json を出す）で当てる
（`assert_not_real_repo` が対象の場所を担保する）。**本物の `claude` の出力の形は見ない**——試料の鍵は
2.1.312 の実測（`references/child-process.md` の「確かめた範囲」）に合わせてある。

**起動した `claude`（祖先）の環境は、`PATH` の先頭に置いた偽の `ps` が答える**（#785）——このテストのプロセスの親（`os.getppid()`）を
問われたときだけ、試料の形（`FAKE_PS_MODE`）で答える。**環境つきの `ps`（`eww`）でほかの pid を問われたら失敗を返し、本物には渡さない**
——本物の祖先の `claude`（このテストを走らせたセッション）の環境・本物のトークンには届かない。ほかの問い（走っているかの確かめ）は本物の `ps` に渡す。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が緑であること。本体の docstring の「守る」の行数だけ変異を当て
（**テスト自身に数えさせる**）、終了コードも docstring の表と突き合わせる。
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "child-cycle.py"
LEDGER = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "ledger.py"
UNATTENDED = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "check-unattended-env.py"
NAME = "issue-50"
BRIEF = "あなたは cruise の子である。\n台帳を書かない。\n終わったら親が -p /dev-loop:dev-loop 5 を起こす。\n"  # 別の番号を含む（P1-R8）

failures: list[str] = []
LAUNCHER_TOKEN = "fake-launcher-token-785"  # 偽の ps が「起動した claude の環境」に置く値（本物ではない）
BASH_TOKEN = "fake-bash-token-785"  # 試料が Bash の環境に置く値

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys, time
token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
kind = {None: None, "%s": "launcher", "%s": "bash"}.get(token, "other")  # 値は書かない
with open(os.path.join(os.environ["FAKE_HOME"], "claude-rec-%%d.json" %% os.getpid()), "w") as f:
    json.dump({"argv": sys.argv[1:], "cwd": os.getcwd(), "sid": os.getsid(0), "stdin": sys.stdin.read(),
               "bg": os.environ.get("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"), "token": kind}, f)
src = os.environ.get("FAKE_CLAUDE_OUTPUT")
if src:
    sys.stdout.write(open(src).read())
    sys.stdout.flush()
time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "0")))
""" % (LAUNCHER_TOKEN, BASH_TOKEN)

# 偽の ps（#785）。このテストのプロセスの親を、FAKE_PS_MODE の形の claude（または claude でないもの）にする
FAKE_PS = """#!/bin/sh
P={ppid}
case "$*" in
  *"-o ppid=,command= -p $P")
    case "$FAKE_PS_MODE" in
      unreadable) exit 1 ;;
      noclaude) printf '    1 /bin/zsh -c x\\n' ;;
      spare) printf '    1 /Users/x/.local/bin/claude --bg-spare\\n' ;;
      *) printf '    1 /Users/x/.local/bin/claude --session-id pp\\n' ;;
    esac
    exit 0 ;;
  *"eww -o command= -p $P")
    case "$FAKE_PS_MODE" in
      token) printf '/Users/x/.local/bin/claude --session-id pp PATH=/bin HOME=/h CLAUDE_CODE_OAUTH_TOKEN={token}\\n' ;;
      *) printf '/Users/x/.local/bin/claude --session-id pp PATH=/bin HOME=/h CLAUDE_CODE_OAUTH_TOKEN=\\n' ;;
    esac
    exit 0 ;;
  *"ww -o command= -p $P") printf '/Users/x/.local/bin/claude --session-id pp\\n'; exit 0 ;;
  *eww*) exit 1 ;;
esac
exec {real} "$@"
"""

INIT = {"type": "system", "subtype": "init", "permissionMode": "auto", "session_id": "s-1",
        "plugins": [{"name": "spec-loop", "version": "0.26.0"}, {"name": "dev-loop", "version": "1.63.6"}]}


def result(turns=1, **extra):
    base = {"type": "result", "subtype": "success", "is_error": False, "num_turns": turns, "total_cost_usd": 0.02,
            "api_error_status": None, "permission_denials": [],
            "subagent_stats": {"spawned": 1, "completed": 1, "killed": {"parent": 0, "user": 0, "system": 0}}}
    base.update(extra)
    return base


def say(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


# 背景の体を待った子は、体の通知の後で result を計 3 つ並べて出し、最後は空（ターン 0・文が空）だった（probe2 の行の順）
FIXTURES = {
    "済んだ（result が 3 つ）": [INIT, say("背景の体を待つ"), say("最後の報告: PR #9"), result(3), result(1), result(0, result="")],
    "最後の result が API の誤り": [INIT, result(3), result(1, api_error_status=529)],
    "result が無い": [INIT, say("途中"), "壊れた行"],
    "成功でない": [INIT, result(5, subtype="error_max_turns", is_error=True)],
    "拒否された操作": [INIT, result(2, permission_denials=[{"tool_name": "Bash", "tool_input": {"command": "git push"}}])],
    "殺された体": [INIT, result(2, subagent_stats={"spawned": 1, "completed": 0, "killed": {"parent": 1, "user": 0, "system": 0}})],
    "利用上限の拒否": [INIT, {"type": "rate_limit_event", "rate_limit_info": {"status": "rejected", "rateLimitType": "seven_day",
                                                                         "resetsAt": 1793269200}}, result(1)],
    "長い文": [INIT, say("あ" * 5000), result(1)],
    "委譲先の発言が最後": [INIT, say("子の報告"), {"type": "assistant", "parent_tool_use_id": "toolu_x",
                                                "message": {"content": [{"type": "text", "text": "委譲先の発言"}]}}, result(1)],
    "途中で版が変わる": [INIT, dict(INIT, plugins=[{"name": "dev-loop", "version": "1.64.0"}]), result(1)],
    "上限が近いだけ": [INIT, {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "rateLimitType": "five_hour"}},
                 {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed_warning", "rateLimitType": "seven_day"}}, result(1)],
}

# 結果の形（#991）。済んだ子の申告
DONE = {"outcome": "pr_ready", "stop_reason": "", "pr": 9, "head_sha": "abc123", "ci": "pass", "skill_path": "/x/SKILL.md",
        "skill_lines": 1200, "denied_commands": [], "needs_user": [], "report": "最後の報告: PR #9"}
EARLY = dict(DONE, outcome="stopped", stop_reason="背景の Verifier を待っている", pr=None, head_sha=None, ci="none")


def shaped(output, turns=1, **extra):
    return result(turns, structured_output=output, **extra)


# 形を渡した記録に置く試料（名前 → (出力, 期待する終了コード)）。p2 の実測: 1 つ目の result は早すぎる報告で、最後が本当の報告
SHAPED = {
    "済んだ": ([INIT, shaped(DONE)], 0),
    "最初が早すぎて最後が済んだ": ([INIT, shaped(EARLY, 3), shaped(DONE, 2)], 0),
    "最初だけ済んで最後が止まった": ([INIT, shaped(DONE, 3), shaped(EARLY, 2)], 3),
    "structured_output が無い": ([INIT, result(1)], 3),
    "オブジェクトでない": ([INIT, shaped("PR #9 を作った")], 3),
    "欄が欠ける": ([INIT, shaped({k: v for k, v in DONE.items() if k != "head_sha"})], 3),
    "型が違う": ([INIT, shaped(dict(DONE, pr="9"))], 3),
    "enum の外": ([INIT, shaped(dict(DONE, ci="green"))], 3),
    "余分な欄": ([INIT, shaped(dict(DONE, extra="x"))], 3),
    "配列の要素の型": ([INIT, shaped(dict(DONE, needs_user=[1]))], 3),
    "真偽値を整数と読まない": ([INIT, shaped(dict(DONE, pr=True))], 3),
    "配列でない needs_user（要約の行で落ちない）": ([INIT, shaped(dict(DONE, needs_user=5))], 3),
    "止まったと申告": ([INIT, shaped(dict(EARLY, ci="pass", pr=9, head_sha="abc123"))], 3),
    "CI が fail": ([INIT, shaped(dict(DONE, ci="fail"))], 3),
    "PR が null": ([INIT, shaped(dict(DONE, pr=None))], 3),
    "利用者に要ること": ([INIT, shaped(dict(DONE, needs_user=["マージの判断"]))], 3),
    "拒まれたと申告": ([INIT, shaped(dict(DONE, denied_commands=["git push"]))], 3),
    "予算切れ": ([INIT, result(3, subtype="error_max_budget_usd", is_error=True)], 3),
}
# 起動の後で本体の形が変わった記録——古い形（欄が少ない）で検査されれば 0、今の形で検査されれば 3
OLD_SCHEMA = {"type": "object", "properties": {"outcome": {"type": "string"}, "pr": {"type": "integer"}, "ci": {"type": "string"}},
              "required": ["outcome", "pr", "ci"]}
OLD_OUTPUT = {"outcome": "pr_ready", "pr": 9, "ci": "pass"}
# 記録の structured が鍵なし・null 以外で形を取り出せない（名前 → (structured, 出力)）——検査せずに 0 にしない
UNREADABLE_RECORDS = {
    "structured が空のオブジェクト": ({}, dict(DONE, outcome="stopped")),
    "structured が文字列": ("x", dict(DONE, outcome="stopped")),
    "schema が null": ({"schema": None}, dict(DONE, outcome="stopped")),
}
# 記録の形の語の値が壊れている・形が出力の型を縛らない——検査の途中で落ちて 1（走っている）にならず 3
BROKEN_SCHEMAS = {
    "type が dict": ({"type": {"a": 1}}, DONE),
    "required が数": ({"type": "object", "required": 5}, DONE),
    "properties が配列": ({"type": "object", "properties": [1]}, DONE),
    "enum が数": ({"enum": 5}, DONE),
    "型を縛らない形に文字列の出力": ({}, "PR #9 を作った"),
}
# 検査器の再帰の上限を越える深さ（#991 の 2 パス目 C3）。json.dumps は Python の版によって深い入れ子で落ちるので、
# 記録は JSON の文字列を手で組んで置く（`plant_deep`）
DEEP = 2000

MUTATIONS = {
    "子を切り離さない": [("start_new_session=True", "start_new_session=False")],
    "子の標準入力を閉じない": [("stdin=subprocess.DEVNULL, ", "")],
    "子の環境に上限 0 を置かない": [(", env=env)", ")")],
    "cwd をメインの作業ツリーにしない": [("cwd=main_tree, stdin", "cwd=None, stdin")],
    "許可モードを既定に任せる": [('launch.add_argument("--permission-mode", required=True)',
                         'launch.add_argument("--permission-mode", default="auto")')],
    "bypassPermissions を拒まない": [('REFUSED_MODES = ("bypassPermissions",)', "REFUSED_MODES = ()")],
    "委譲文の {{ と空を拒まない": [('    if not brief.strip():', '    if False:'), ('    if "{{" in brief:', '    if False:')],
    "走っている子がいても 2 体目を起こす": [('        if is_running(meta["pid"], number):', '        if False:')],
    "起こせなかった記録を残す": [("            leftover.unlink(missing_ok=True)", "            pass")],
    "claude でない pid も走っていると読む": [('    if not any(Path(t).name == "claude" for t in tokens[:2]):\n        return False\n', '')],
    "コマンド全体から番号を探す": [('    return at >= 0 and tokens[at + 1:at + 3] == ["/dev-loop:dev-loop", str(number)]',
                        '    return re.search(rf"/dev-loop:dev-loop {number}(\\s|$)", proc.stdout) is not None')],
    "最初の result を読む": [('last = summary["results"][-1]', 'last = summary["results"][0]'),
                       ('last = results[-1]', 'last = results[0]')],
    "result が無くても済んだと読む": [('return ["result が無い"]', "return []")],
    "要確認の印を見ない": [("    if problems:", "    if False:")],
    "委譲先の発言を最後の文にする": [(' and not event.get("parent_tool_use_id")', "")],
    "途中の init の版を出さない": [("    if later != dev_loop:", "    if False:")],
    "上限が近いだけでも拒否と読む": [('(None, "allowed", "allowed_warning")', '(None,)')],
    "起動した claude の環境の値を子に置かない": [("        env[LONG_TOKEN] = token\n", "        pass\n")],
    "Bash の環境にあっても起動した claude の環境の値で上書きする": [
        ('    if str(env.get(LONG_TOKEN) or "").strip():\n        return None, "bash"', '    if False:\n        return None, "bash"')],
    "Bash の環境だけを継ぐことを言わない": [("    print(token_line)\n", "")],
    "消す設定でも起動した claude の環境から渡す": [("        if mod.env_scrubbed(env):\n", "        if False:\n")],
    "長期トークンの値を出力に出す": [("起動した claude の環境の値を子に渡した（値は出さない）\"", "起動した claude の環境の値を子に渡した（{value}）\"")],
    "要約の行を切り詰めない": [('return text if len(text) <= limit else text[: limit - 1] + "…"', "return text")],
    "既定で形を渡さない": [("    schema = None if args.no_structured else RESULT_SCHEMA", "    schema = None")],
    "--no-structured でも形を渡す": [("    schema = None if args.no_structured else RESULT_SCHEMA", "    schema = RESULT_SCHEMA")],
    "最初の result の structured_output を読む": [('    output = summary["results"][-1].get("structured_output")',
                                            '    output = summary["results"][0].get("structured_output")')],
    "形に合わなくても 3 にしない": [('        return ["結果の形を渡したのに、最後の result に structured_output が無い"]', "        return []"),
                          ("        problems = schema_problems(output, schema)\n        if problems:",
                           "        problems = schema_problems(output, schema)\n        if False:")],
    "真偽値を整数と読む": [('            if isinstance(value, bool) and name in ("integer", "number"):\n'
                   "                return False  # 真偽値を整数と読まない\n", "")],
    "子の申告を見ない": [("    return claimed_problems(output)", "    return []")],
    "記録の形でなく本体の形で検査する": [("    schema = recorded_schema(meta)", "    schema = RESULT_SCHEMA")],
    "形を取り出せない記録を渡していないと読む": [("    return schema if isinstance(schema, dict) else UNREADABLE_SCHEMA",
                                    "    return schema if isinstance(schema, dict) else None")],
    "検査の途中の例外を捕まえない": [("    except (TypeError, AttributeError, ValueError, RecursionError) as exc:",
                         "    except RecursionError as exc:")],
    "検査器の再帰の上限を捕まえない": [("    except (TypeError, AttributeError, ValueError, RecursionError) as exc:",
                          "    except (TypeError, AttributeError, ValueError) as exc:")],
}


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"child_{id(script)}_{script.stat().st_mtime_ns}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.LEDGER = LEDGER  # 変異の写しはテンポラリにあるので、台帳の場所の決め方は本物を読ませる
    mod.UNATTENDED = UNATTENDED  # 起動した claude の環境の読み方も同じ（#785）
    return mod


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def isolate_env(home: Path) -> None:
    """`GIT_*` を外し、`HOME` と git の設定を差し替え、偽の `claude` を `PATH` の先頭に置く——本物の `claude` には届かない。"""
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[key]
    os.environ.pop("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS", None)  # 「親の環境に無い」場合を試料が自分で作る
    # 認証（#785）: Bash の環境の長期トークン・消去の設定は試料が自分で作る（CI は GITHUB_ACTIONS を置く）
    for key in ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "GITHUB_ACTIONS"):
        os.environ.pop(key, None)
    real_ps = shutil.which("ps")
    assert real_ps, "ps が無い"
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    (home / "bin").mkdir()
    fake = home / "bin" / "claude"
    fake.write_text(FAKE_CLAUDE, encoding="utf-8")
    fake.chmod(0o755)
    ps = home / "bin" / "ps"
    ps.write_text(FAKE_PS.format(ppid=os.getppid(), token=LAUNCHER_TOKEN, real=real_ps), encoding="utf-8")
    ps.chmod(0o755)
    os.environ["FAKE_PS_MODE"] = "none"  # 既定は対話ログインの親（起動した claude の環境にトークンが無い）
    # **本物の claude が在る PATH の項を外す**——偽物を実行できなくした試料で、後ろの本物に落ちないように
    # （一度、偽物の実行権を外した試料が本物の claude を起こした）
    rest = [p for p in os.environ["PATH"].split(os.pathsep) if p and not os.access(os.path.join(p, "claude"), os.X_OK)]
    os.environ.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
                      FAKE_HOME=str(home), PATH=os.pathsep.join([str(home / "bin"), *rest]))


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def run(mod, argv, chdir):
    """**cwd を渡さずに、プロセスの cwd を移して呼ぶ**——子の cwd がどこから決まるかを見るため。"""
    out, err = io.StringIO(), io.StringIO()
    before = os.getcwd()
    os.chdir(chdir)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = mod.main(argv)
            except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
                return ("例外", type(exc).__name__, "")
    finally:
        os.chdir(before)
    return (rc, out.getvalue(), err.getvalue())


def wait_for(pred, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.05)
    return False


def dead_pid() -> int:
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid


def write_stream(path: Path, events) -> None:
    path.write_text("".join((e if isinstance(e, str) else json.dumps(e, ensure_ascii=False)) + "\n" for e in events),
                    encoding="utf-8")


NO_KEY = object()


def plant(main: Path, number: int, pid: int, events, tag: str, structured=NO_KEY) -> None:
    """起動口を通さずに記録を置く（終わった子の要約を当てるため）。

    `structured` を渡さなければ、記録に `structured` の鍵を置かない（#991 より前の起動口の記録の形）。
    """
    d = main / ".claude" / "plans" / f"cruise-{NAME}-children"
    d.mkdir(parents=True, exist_ok=True)
    out = d / f"{number}-{tag}.jsonl"
    write_stream(out, events)
    (d / f"{number}-{tag}.err").write_text("", encoding="utf-8")
    meta = {"pid": pid, "out": str(out), "err": str(d / f"{number}-{tag}.err")}
    if structured is not NO_KEY:
        meta["structured"] = structured
    (d / f"{number}-{tag}.json").write_text(json.dumps(meta), encoding="utf-8")


def plant_deep(main: Path, number: int, pid: int, depth: int, tag: str) -> None:
    """形と出力が `depth` 段の入れ子の記録を、JSON の文字列を手で組んで置く。"""
    schema = '{"type": "array", "items": ' * depth + '{"type": "string"}' + "}" * depth
    output = "[" * depth + '"x"' + "]" * depth
    line = json.dumps(result(1, structured_output="@@"), ensure_ascii=False).replace('"@@"', output)
    plant(main, number, pid, [INIT, line], tag, structured={"schema": "@@"})
    meta = main / ".claude" / "plans" / f"cruise-{NAME}-children" / f"{number}-{tag}.json"
    meta.write_text(meta.read_text(encoding="utf-8").replace('"@@"', schema), encoding="utf-8")


def stop(pid) -> None:
    with contextlib.suppress(OSError):
        os.kill(pid, signal.SIGKILL)


def scenario(mod, tmp: Path, tag: str) -> dict:
    """全試料を 1 本のリポジトリで走らせ、観測を辞書で返す。**変異の前後で同じ関数を使う。**"""
    o: dict = {}
    home = Path(os.environ["FAKE_HOME"])
    for rec in home.glob("claude-rec-*.json"):
        rec.unlink()
    main = tmp / f"repo-{tag}"
    main.mkdir()
    assert_not_real_repo(main)
    git(main, "init", "-q", "-b", "main")
    git(main, "commit", "-q", "--allow-empty", "-m", "init")
    wt = main / ".claude" / "worktrees" / "w"
    git(main, "worktree", "add", "-q", str(wt), "-b", "issue/50-x")
    sub = wt / "sub"
    sub.mkdir()
    brief = main / ".claude" / "plans" / "brief-50.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text(BRIEF, encoding="utf-8")
    children = main / ".claude" / "plans" / f"cruise-{NAME}-children"
    started: list[int] = []
    try:
        # 起こす（走り続ける子）
        os.environ.pop("FAKE_CLAUDE_OUTPUT", None)
        os.environ["FAKE_CLAUDE_SLEEP"] = "30"
        t0 = time.time()
        # 親の標準入力に中身を置く——子が継げば読める（P1-R4）
        r, w = os.pipe()
        os.write(w, b"PARENT-INPUT")
        os.close(w)
        saved = os.dup(0)
        os.dup2(r, 0)
        os.close(r)
        # 親の環境に別の上限を置く——子では 0 に上書きされるはず（#491。下の #51 は親の環境に無い場合）
        os.environ["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] = "600000"
        try:
            rc, out, err = run(mod, ["launch", NAME, "50", "--brief", str(brief), "--permission-mode", "auto",
                                     "--model", "haiku", "--allowed-tools", "Bash(git status)", "Agent"], sub)
        finally:
            os.environ.pop("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS", None)
            os.dup2(saved, 0)
            os.close(saved)
        o["上書きしたと出す"] = "上書きした: 親の環境の CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS='600000'" in str(out)
        o["launch の戻りが速い"] = time.time() - t0 < 5
        m = re.search(r"pid (\d+)", str(out))
        pid = int(m.group(1)) if m else None
        if pid:
            started.append(pid)
        rec_path = home / f"claude-rec-{pid}.json"
        o["launch"] = rc
        rec = json.loads(rec_path.read_text(encoding="utf-8")) if pid and wait_for(rec_path.exists) and wait_for(
            lambda: rec_path.stat().st_size > 0) else {}
        o["引数"] = rec.get("argv")
        o["cwd"] = rec.get("cwd")
        o["別のセッション"] = rec.get("sid") is not None and rec.get("sid") != os.getsid(0)
        o["標準入力は空"] = rec.get("stdin")
        o["上限(親に別の値)"] = rec.get("bg")
        agent = re.search(r"^台帳の agent: claude-p:(.+)$", str(out), re.M)
        o["記録の場所"] = (Path(agent.group(1)).parent == children and Path(agent.group(1)).exists()) if agent else False
        o["記録の env"] = json.loads(Path(agent.group(1)).read_text(encoding="utf-8")).get("env") if agent else None
        o["記録の structured"] = (json.loads(Path(agent.group(1)).read_text(encoding="utf-8")).get("structured", "鍵が無い")
                                if agent else None)
        o["worktree に書かない"] = sorted(p.name for p in sub.parent.iterdir())
        # 走っている間
        o["status(走っている)"] = run(mod, ["status", NAME, "50"], main)[0]
        o["2 体目"] = run(mod, ["launch", NAME, "50", "--brief", str(brief), "--permission-mode", "auto"], main)[0]
        o["2 体目の後の記録の数"] = len(list(children.glob("50-*.json")))
        # 番号の境界: #50 が走っていても #5 は走っていない
        plant(main, 5, pid or dead_pid(), [INIT, result(1)], "z")
        o["#5 は走っていない"] = run(mod, ["status", NAME, "5"], main)[0]
        if pid:
            stop(pid)
            wait_for(lambda: run(mod, ["status", NAME, "50"], main)[0] != 1)
        o["status(止めた後)"] = run(mod, ["status", NAME, "50"], main)[0]

        # 起こして、出力を出して終わる子（端から端まで）
        stream = tmp / f"stream-{tag}.jsonl"
        # 形を渡した子（既定）: 最初の result は早すぎる報告、最後の 2 つが済んだ報告（最後は文が空・ターン 0）
        write_stream(stream, [INIT, say("背景の体を待つ"), say("最後の報告: PR #9"), shaped(EARLY, 3), shaped(DONE, 1),
                              shaped(DONE, 0, result="")])
        os.environ["FAKE_CLAUDE_OUTPUT"] = str(stream)
        os.environ["FAKE_CLAUDE_SLEEP"] = "0"
        assert "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS" not in os.environ
        rc, out, _ = run(mod, ["launch", NAME, "51", "--brief", str(brief), "--permission-mode", "dontAsk"], main)
        m = re.search(r"pid (\d+)", str(out))
        if m:
            started.append(int(m.group(1)))
        o["#51 で上書きしたと出さない"] = "上書きした" not in str(out)
        rec51 = home / f"claude-rec-{m.group(1)}.json" if m else None
        o["上限(親に無い)"] = (json.loads(rec51.read_text(encoding="utf-8")).get("bg")
                           if rec51 and wait_for(rec51.exists) and wait_for(lambda: rec51.stat().st_size > 0) else "記録なし")
        wait_for(lambda: run(mod, ["status", NAME, "51"], main)[0] != 1)
        o["端から端"] = run(mod, ["status", NAME, "51"], main)[:2]
        # 親の環境が既に "0"——上書きではないので出さない（経路 (c)。#491 の 1 パス目 V1・CR3）
        os.environ["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] = "0"
        try:
            rc, out, _ = run(mod, ["launch", NAME, "54", "--brief", str(brief), "--permission-mode", "auto"], main)
        finally:
            os.environ.pop("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS", None)
        m = re.search(r"pid (\d+)", str(out))
        if m:
            started.append(int(m.group(1)))
        rec54 = home / f"claude-rec-{m.group(1)}.json" if m else None
        o["親が 0 なら上書きしたと出さない"] = (rc, "上書きした" not in str(out),
                                    json.loads(rec54.read_text(encoding="utf-8")).get("bg")
                                    if rec54 and wait_for(rec54.exists) and wait_for(lambda: rec54.stat().st_size > 0) else "記録なし")
        wait_for(lambda: run(mod, ["status", NAME, "54"], main)[0] != 1)
        # --no-structured（#991）: 形を渡さず、記録は null、形の無い出力でも 0
        plain = tmp / f"plain-{tag}.jsonl"
        write_stream(plain, FIXTURES["済んだ（result が 3 つ）"])
        os.environ["FAKE_CLAUDE_OUTPUT"] = str(plain)
        rc, out, _ = run(mod, ["launch", NAME, "55", "--brief", str(brief), "--permission-mode", "auto", "--no-structured"], main)
        m = re.search(r"pid (\d+)", str(out))
        if m:
            started.append(int(m.group(1)))
        rec55 = home / f"claude-rec-{m.group(1)}.json" if m else None
        agent55 = re.search(r"^台帳の agent: claude-p:(.+)$", str(out), re.M)
        o["--no-structured"] = (rc, json.loads(rec55.read_text(encoding="utf-8")).get("argv")
                                if rec55 and wait_for(rec55.exists) and wait_for(lambda: rec55.stat().st_size > 0) else "記録なし",
                                json.loads(Path(agent55.group(1)).read_text(encoding="utf-8")).get("structured", "鍵が無い")
                                if agent55 else None)
        wait_for(lambda: run(mod, ["status", NAME, "55"], main)[0] != 1)
        o["--no-structured の要約"] = run(mod, ["status", NAME, "55"], main)[:2]
        os.environ["FAKE_CLAUDE_OUTPUT"] = str(stream)

        # 認証（#785）: 子の環境の CLAUDE_CODE_OAUTH_TOKEN の出所。偽の ps が起動した claude の環境を答える
        os.environ.pop("FAKE_CLAUDE_OUTPUT", None)
        os.environ["FAKE_CLAUDE_SLEEP"] = "0"
        for number, mode, extra in ((40, "token", {}), (41, "token", {"CLAUDE_CODE_OAUTH_TOKEN": BASH_TOKEN}),
                                    (42, "none", {}), (43, "unreadable", {}), (44, "noclaude", {}),
                                    (45, "token", {"CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1"}),
                                    (46, "token", {"CLAUDE_CODE_OAUTH_TOKEN": " "}),
                                    (47, "spare", {}), (48, "raises", {})):
            os.environ["FAKE_PS_MODE"] = mode
            os.environ.update(extra)
            saved_unattended = mod.UNATTENDED
            if mode == "raises":  # 読み方が想定外の例外を出す（例外の文に値が入っていても出さない）
                raising = tmp / f"raising-{tag}.py"
                raising.write_text("def env_scrubbed(env):\n    return False\n\n\n"
                                   f"def launcher_auth_env(pid=None):\n    raise RuntimeError('CLAUDE_CODE_OAUTH_TOKEN={LAUNCHER_TOKEN}')\n",
                                   encoding="utf-8")
                mod.UNATTENDED = raising
            try:
                rc, out, err = run(mod, ["launch", NAME, str(number), "--brief", str(brief), "--permission-mode", "auto"], main)
            finally:
                mod.UNATTENDED = saved_unattended
                os.environ["FAKE_PS_MODE"] = "none"
                for key in extra:
                    os.environ.pop(key, None)
            m = re.search(r"pid (\d+)", str(out))
            if m:
                started.append(int(m.group(1)))
            rec_n = home / f"claude-rec-{m.group(1)}.json" if m else None
            kind = (json.loads(rec_n.read_text(encoding="utf-8")).get("token")
                    if rec_n and wait_for(rec_n.exists) and wait_for(lambda: rec_n.stat().st_size > 0) else "記録なし")
            agent = re.search(r"^台帳の agent: claude-p:(.+)$", str(out), re.M)
            meta_auth = json.loads(Path(agent.group(1)).read_text(encoding="utf-8")).get("auth") if agent else None
            wait_for(lambda: run(mod, ["status", NAME, str(number)], main)[0] != 1)
            texts = [str(out), str(err)] + [p.read_text(encoding="utf-8", errors="replace")
                                            for p in children.glob(f"{number}-*") if p.is_file()]
            o[f"認証 #{number}"] = (rc, kind, [l for l in str(out).splitlines() if l.startswith("認証")], meta_auth,
                                  any(t in x for x in texts for t in (LAUNCHER_TOKEN, BASH_TOKEN)))

        # 拒む
        os.environ.pop("FAKE_CLAUDE_OUTPUT", None)
        bad = main / ".claude" / "plans" / "brief-bad.md"
        bad.write_text("Issue #{{issue}}\n", encoding="utf-8")
        empty = main / ".claude" / "plans" / "brief-empty.md"
        empty.write_text(" \n", encoding="utf-8")
        o["{{ が残る"] = run(mod, ["launch", NAME, "52", "--brief", str(bad), "--permission-mode", "auto"], main)[0]
        o["空の委譲文"] = run(mod, ["launch", NAME, "52", "--brief", str(empty), "--permission-mode", "auto"], main)[0]
        o["委譲文が無い"] = run(mod, ["launch", NAME, "52", "--brief", str(main / "none.md"), "--permission-mode", "auto"], main)[0]
        o["bypassPermissions"] = run(mod, ["launch", NAME, "52", "--brief", str(brief), "--permission-mode", "bypassPermissions"], main)[0]
        o["許可モードなし"] = run(mod, ["launch", NAME, "52", "--brief", str(brief)], main)[0]
        o["選べない許可モード"] = run(mod, ["launch", NAME, "52", "--brief", str(brief), "--permission-mode", "yolo"], main)[0]
        o["拒んだ後の #52 の記録"] = sorted(p.name for p in children.glob("52-*"))
        o["引数"] = (o["引数"], run(mod, ["status", NAME, "0"], main)[0], run(mod, ["status", "a/b", "1"], main)[0])

        # 起こせない（claude が実行できない）
        fake = home / "bin" / "claude"
        fake.chmod(0o644)
        try:
            if shutil.which("claude") is not None:  # 本物に落ちるなら、起こさずに止める
                raise AssertionError(f"実行できる claude が PATH に残っている: {shutil.which('claude')}")
            o["起こせない"] = run(mod, ["launch", NAME, "53", "--brief", str(brief), "--permission-mode", "auto"], main)[0]
        finally:
            fake.chmod(0o755)
        o["起こせなかった記録"] = sorted(p.name for p in children.glob("53-*"))

        # 判定できない
        o["記録が無い"] = run(mod, ["status", NAME, "99"], main)[0]
        outside = tmp / f"outside-{tag}"
        outside.mkdir()
        o["git の外"] = run(mod, ["status", NAME, "50"], outside)[0]

        # 終わった子の要約（試料ごと）
        for i, (name, events) in enumerate(FIXTURES.items()):
            number = 60 + i
            plant(main, number, dead_pid(), events, "a")
            rc, out, _ = run(mod, ["status", NAME, str(number)], main)
            o[f"要約 {name}"] = (rc, out)
        # 形を渡した記録（#991）
        for i, (name, (events, _)) in enumerate(SHAPED.items()):
            number = 100 + i
            plant(main, number, dead_pid(), events, "a", structured={"schema": mod.RESULT_SCHEMA})
            o[f"形 {name}"] = run(mod, ["status", NAME, str(number)], main)[:2]
        plant(main, 130, dead_pid(), [INIT, shaped(OLD_OUTPUT)], "a", structured={"schema": OLD_SCHEMA})
        o["形 古い形の記録"] = run(mod, ["status", NAME, "130"], main)[:2]
        plant(main, 131, dead_pid(), [INIT, result(1)], "a", structured=None)
        o["形 null の記録"] = run(mod, ["status", NAME, "131"], main)[:2]
        plant(main, 132, dead_pid(), [INIT, shaped(DONE)], "a", structured={"schema": dict(OLD_SCHEMA, minimum=1)})
        o["形 読めない語"] = run(mod, ["status", NAME, "132"], main)[:2]
        for i, (name, (structured, output)) in enumerate(UNREADABLE_RECORDS.items()):
            plant(main, 140 + i, dead_pid(), [INIT, shaped(output)], "a", structured=structured)
            o[f"取り出せない {name}"] = run(mod, ["status", NAME, str(140 + i)], main)[:2]
        for i, (name, (schema, output)) in enumerate(BROKEN_SCHEMAS.items()):
            plant(main, 150 + i, dead_pid(), [INIT, shaped(output)], "a", structured={"schema": schema})
            o[f"壊れた形 {name}"] = run(mod, ["status", NAME, str(150 + i)], main)[:2]
        plant_deep(main, 160, dead_pid(), DEEP, "a")
        o["深い入れ子"] = run(mod, ["status", NAME, "160"], main)[:2]
        plant_deep(main, 161, dead_pid(), 50, "a")
        o["浅い入れ子"] = run(mod, ["status", NAME, "161"], main)[:2]
        # pid が居ても claude でなければ走っていない
        sleeper = subprocess.Popen(["sleep", "30"])
        started.append(sleeper.pid)
        plant(main, 80, sleeper.pid, [INIT, result(1)], "a")
        o["claude でない pid"] = run(mod, ["status", NAME, "80"], main)[0]
        # claude でないが、-p の引数がその Issue のもの（P1-V2）
        imposter = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", "-p", "/dev-loop:dev-loop", "81"])
        started.append(imposter.pid)
        plant(main, 81, imposter.pid, [INIT, result(1)], "a")
        o["-p を持つが claude でない pid"] = run(mod, ["status", NAME, "81"], main)[0]
    finally:
        for pid in started:
            stop(pid)
    return o


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        isolate_env(tmp / "home")
        mod = load()
        o = scenario(mod, tmp, "correct")
        main_tree = tmp / "repo-correct"

        print("起こす（L1・L3）")
        check("launch は 0 で、子の終わりを待たずに戻る", o["launch"] == 0 and o["launch の戻りが速い"])
        schema_text = json.dumps(mod.RESULT_SCHEMA, ensure_ascii=False)
        check("引数: -p にスラッシュコマンド・stream-json・verbose・名指しした許可モード・委譲文・モデル・結果の形・最後に --allowedTools",
              o["引数"][0] == ["-p", "/dev-loop:dev-loop 50", "--output-format", "stream-json", "--verbose",
                              "--permission-mode", "auto", "--append-system-prompt", BRIEF, "--model", "haiku",
                              "--json-schema", schema_text, "--allowedTools", "Bash(git status)", "Agent"])
        check("記録の .json に渡した結果の形を残す（#991）", o["記録の structured"] == {"schema": mod.RESULT_SCHEMA})
        check("結果の形の文字列に ' -p ' が無い（走っているかの判定が -p の直後を読むので）", " -p " not in schema_text)
        rc55, argv55, structured55 = o["--no-structured"]
        check("--no-structured なら --json-schema を渡さず、記録の structured は null",
              rc55 == 0 and isinstance(argv55, list) and "--json-schema" not in argv55 and structured55 is None)
        check("--no-structured の子は形を検査せず、形の無い出力でも 0（「結果の形: 渡していない」と出す）",
              o["--no-structured の要約"][0] == 0 and "結果の形: 渡していない" in str(o["--no-structured の要約"][1]))
        check("worktree のサブディレクトリから呼んでも、子の cwd はメインの作業ツリー", o["cwd"] == str(main_tree))
        check("子は新しいセッション（親から切り離す）", o["別のセッション"])
        check("子の標準入力は閉じている（空）", o["標準入力は空"] == "")
        check("親の環境に別の上限があっても、子の CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS は 0（上書きしたと出す）",
              o["上限(親に別の値)"] == "0" and o["上書きしたと出す"])
        check("親の環境に無くても、子の CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS は 0（上書きしたとは出さない）",
              o["上限(親に無い)"] == "0" and o["#51 で上書きしたと出さない"])
        check("親の環境が既に 0 なら、子は 0 で、上書きしたとは出さない", o["親が 0 なら上書きしたと出さない"] == (0, True, "0"))
        check("記録の .json に子へ渡した上限を残す", o["記録の env"] == {"CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0"})
        check("記録は台帳の隣（.claude/plans/cruise-<名前>-children/）に在り、その場所を出す", o["記録の場所"])
        check("worktree の中には書かない", o["worktree に書かない"] == [".git", "sub"])

        print("\n認証（#785）: 子の環境の CLAUDE_CODE_OAUTH_TOKEN")
        def auth(n):
            return o[f"認証 #{n}"]
        launched = lambda n: auth(n)[0] == 0 and len(auth(n)[2]) == 1
        check("Bash の環境に無く、起動した claude の環境にあれば、子はその値を受ける",
              launched(40) and auth(40)[1] == "launcher" and "起動した claude の環境の値を子に渡した" in auth(40)[2][0]
              and auth(40)[3] == {"name": "CLAUDE_CODE_OAUTH_TOKEN", "passed": True, "from": "launcher"})
        check("Bash の環境にあれば、それを継ぎ、起動した claude の環境の値で上書きしない",
              launched(41) and auth(41)[1] == "bash" and "Bash の環境の CLAUDE_CODE_OAUTH_TOKEN を継ぐ" in auth(41)[2][0]
              and auth(41)[3] == {"name": "CLAUDE_CODE_OAUTH_TOKEN", "passed": True, "from": "bash"})
        check("起動した claude の環境にも無ければ（対話ログイン）、子は受けず、そう言う",
              launched(42) and auth(42)[1] is None and "起動した claude の環境にも" in auth(42)[2][0]
              and "Bash の環境だけを継ぐ" in auth(42)[2][0]
              and auth(42)[3] == {"name": "CLAUDE_CODE_OAUTH_TOKEN", "passed": False, "from": None})
        check("起動した claude の環境を読めなければ、子は受けず、読めなかったと言う",
              launched(43) and auth(43)[1] is None and "読めなかった" in auth(43)[2][0] and "Bash の環境だけを継ぐ" in auth(43)[2][0])
        check("祖先に claude が無ければ、子は受けず、そう言う",
              launched(44) and auth(44)[1] is None and "祖先に claude のプロセスが見つからなかった" in auth(44)[2][0])
        check("子の環境から認証の変数を消す設定なら、起動した claude の環境から渡さない",
              launched(45) and auth(45)[1] is None and "消す設定" in auth(45)[2][0])
        check("Bash の環境の値が空白だけなら無いものとし、起動した claude の環境の値を渡す",
              launched(46) and auth(46)[1] == "launcher"
              and auth(46)[3] == {"name": "CLAUDE_CODE_OAUTH_TOKEN", "passed": True, "from": "launcher"})
        check("最寄りの claude が spare なら、子は受けず、読めなかったと言う",
              launched(47) and auth(47)[1] is None and "spare" in auth(47)[2][0])
        check("読み方が想定外の例外を出したら、子は受けず、型の名前だけを言う",
              launched(48) and auth(48)[1] is None and "RuntimeError" in auth(48)[2][0])
        not_passed = {"name": "CLAUDE_CODE_OAUTH_TOKEN", "passed": False, "from": None}
        check("渡さなかった形の記録は passed=False・from=None（読めない・祖先に無い・消す設定・spare・例外）",
              all(auth(n)[3] == not_passed for n in (43, 44, 45, 47, 48)))
        check("長期トークンの値を出力・標準エラー・記録に出さない（どの形でも。例外の文に値があっても）",
              not any(auth(n)[4] for n in range(40, 49)))

        print("\n走っている間（L2・S1）")
        check("status は 1", o["status(走っている)"] == 1)
        check("同じ Issue の 2 体目は 3 で、記録を増やさない", o["2 体目"] == 3 and o["2 体目の後の記録の数"] == 1)
        check("#50 の子の pid でも、#5 の記録からは走っていない（委譲文に「-p /dev-loop:dev-loop 5」があっても）", o["#5 は走っていない"] != 1)
        check("止めた子は走っていない（result が無いので 3）", o["status(止めた後)"] == 3)
        check("pid が居ても claude でなければ走っていない", o["claude でない pid"] == 0)
        check("-p /dev-loop:dev-loop 81 を持っていても claude でなければ走っていない", o["-p を持つが claude でない pid"] == 0)

        print("\n拒む（L2）")
        check("{{ が残る委譲文は 3", o["{{ が残る"] == 3)
        check("空の委譲文は 3", o["空の委譲文"] == 3)
        check("無い委譲文は 3", o["委譲文が無い"] == 3)
        check("bypassPermissions は 3", o["bypassPermissions"] == 3)
        check("許可モードなし・選べない許可モードは 2", (o["許可モードなし"], o["選べない許可モード"]) == (2, 2))
        check("拒んだら記録を残さない", o["拒んだ後の #52 の記録"] == [])
        check("番号が 0・名前に区切りは 2", o["引数"][1:] == (2, 2))
        check("claude を起こせなければ 4 で、記録を残さない", o["起こせない"] == 4 and o["起こせなかった記録"] == [])
        check("記録が無い・git の外は 4", (o["記録が無い"], o["git の外"]) == (4, 4))

        print("\n要約（S2〜S5）")
        rc, out = o["端から端"]
        check("端から端: 終わった子は 0", rc == 0)
        check("result を 3 つ数え、最後の result（ターン 0）を読む", "result: 3 個 ／ 最後: success・is_error=False・ターン 0" in str(out))
        check("dev-loop の版・許可モード・セッションを出す", "dev-loop の版: 1.63.6 ／ 許可モード: auto ／ セッション: s-1" in str(out))
        check("最後の文は最後の assistant の文（最後の result の文は空）", "最後の文: 最後の報告: PR #9" in str(out))
        expected = {"済んだ（result が 3 つ）": 0, "最後の result が API の誤り": 3, "result が無い": 3, "成功でない": 3,
                    "拒否された操作": 3, "殺された体": 3, "利用上限の拒否": 3, "長い文": 0, "上限が近いだけ": 0, "委譲先の発言が最後": 0, "途中で版が変わる": 0}
        for name, code in expected.items():
            check(f"{name} は {code}", o[f"要約 {name}"][0] == code)
        check("拒否された操作の道具の名前を出す", "拒否された操作: Bash" in o["要約 拒否された操作"][1])
        check("利用上限の種類を出す", "利用上限: rejected（seven_day" in o["要約 利用上限の拒否"][1])
        check("読めなかった行を数える", "読めなかった行: 1" in o["要約 result が無い"][1])
        check("最後の文は子自身の発言（委譲先の発言ではない）", "最後の文: 子の報告" in o["要約 委譲先の発言が最後"][1])
        check("途中の init で dev-loop の版が変わったら両方を出す", "dev-loop の版: 1.63.6, → 途中から 1.64.0" in o["要約 途中で版が変わる"][1])
        check("長い文を切り詰める（要約は 1500 文字未満）", len(o["要約 長い文"][1]) < 1500)
        check("形の鍵が無い記録（#991 より前の起動口）は形を検査しない（「結果の形: 渡していない」）",
              "結果の形: 渡していない" in o["要約 済んだ（result が 3 つ）"][1])

        print("\n結果の形（#991）")
        check("端から端: 最後の result の structured_output の欄を 1 行で出す（最初の早すぎる報告ではない）",
              "結果の形: outcome=pr_ready・PR 9・head abc123・CI pass" in str(out))
        for name, (_, code) in SHAPED.items():
            check(f"形 {name} は {code}", o[f"形 {name}"][0] == code)
        check("形が無い出力は理由を出す", "structured_output が無い" in o["形 structured_output が無い"][1])
        check("形に合わない出力は合わない欄を出す", "$.ci" in o["形 enum の外"][1] and "$.extra" in o["形 余分な欄"][1])
        check("子の申告の止まった理由を出す", "子が止まったと申告" in o["形 止まったと申告"][1])
        check("記録に残した古い形で検査する（今の形では欄が足りないが 0）", o["形 古い形の記録"][0] == 0)
        check("記録の structured が null なら形を検査しない", o["形 null の記録"][0] == 0)
        check("形に読めない語があれば 3", o["形 読めない語"][0] == 3 and "読めない語" in o["形 読めない語"][1])
        for name in UNREADABLE_RECORDS:
            check(f"記録の {name} は「渡していない」と読まずに 3", o[f"取り出せない {name}"][0] == 3
                  and "形を取り出せない" in o[f"取り出せない {name}"][1])
        for name in BROKEN_SCHEMAS:
            check(f"壊れた形（{name}）でも落ちずに 3", o[f"壊れた形 {name}"][0] == 3)
        # 浅い入れ子は検査器が最後まで歩いて「オブジェクトでない」に着く（試料が組めていることの陽性対照）
        check("浅い入れ子（50 段）の記録は検査器が歩ききって 3", o["浅い入れ子"][0] == 3
              and "オブジェクトでない" in o["浅い入れ子"][1])
        check(f"深い入れ子（{DEEP} 段）の記録でも再帰の上限で落ちずに 3", o["深い入れ子"][0] == 3)
        brief_text = (SCRIPT.parent.parent / "prompts" / "child-cycle.md").read_text(encoding="utf-8").split("\n---\n", 1)[-1]
        missing = [k for k in mod.RESULT_SCHEMA["properties"] if f"`{k}`" not in brief_text]
        check(f"委譲文（--- より下）が形の欄を全部名指しする（無い: {missing}）", not missing)
        enums = [v for p in mod.RESULT_SCHEMA["properties"].values() for v in p.get("enum", [])]
        missing_enum = [v for v in enums if f"`{v}`" not in brief_text]
        check(f"委譲文が enum の値を全部名指しする（無い: {missing_enum}）", not missing_enum)

        print("\n終了コードが docstring の表と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_RUNNING, mod.EXIT_USAGE, mod.EXIT_REJECTED, mod.EXIT_UNKNOWN}
        check(f"表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)

        print("\n変異テスト（壊したのに緑なら失格）")
        for name, pairs in MUTATIONS.items():
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}: {missing}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "child-cycle.py"
            broken.write_text(mutated, encoding="utf-8")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**（test-parent-issue.py と同じ）
            try:
                mutant = load(broken)
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, tmp, f"mut-{abs(hash(name))}")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            # **最初の launch が通らない変異は「殺せた」ではなく「当てられなかった」**——一度、変異の写しが
            # 台帳の決め方を読めずに全部の launch が 4 になり、12 件とも違う理由で「殺せた」と出た
            if got.get("launch") != 0:
                check(f"変異の最初の launch が通る（当てられなかった）: {name}: {got.get('launch')}", False)
                continue
            got_cmp = {k: v for k, v in got.items() if k not in ("cwd",)}
            want_cmp = {k: v for k, v in o.items() if k not in ("cwd",)}
            # cwd はリポジトリごとに違うので、メインの作業ツリーからの相対で比べる
            rel = lambda v, tag: None if v is None else os.path.relpath(v, tmp / tag)
            same_cwd = rel(got.get("cwd"), f"repo-mut-{abs(hash(name))}") == rel(o.get("cwd"), "repo-correct")
            check(f"変異を殺せる: {name}", not (same_cwd and normalize(got_cmp) == normalize(want_cmp)))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("子プロセスの起動口と要約のテスト: すべて合格")
    return 0


def normalize(obs: dict) -> dict:
    """リポジトリごとに違うパスと pid を、観測から外す（変異の前後で比べるため）。"""
    out = {}
    for key, value in obs.items():
        text = json.dumps(value, ensure_ascii=False, default=str)
        text = re.sub(r"/[^\s\"']*?/repo-[^/\s\"']+", "<repo>", text)
        text = re.sub(r"pid \d+", "pid N", text)
        text = re.sub(r"\d{8}T\d{12}Z", "<時刻>", text)
        out[key] = text
    return out


if __name__ == "__main__":
    raise SystemExit(main())
