#!/usr/bin/env python3
r"""spec-loop の autopilot（#789）の入口（#849）が使う判定——台帳の線の検査と、周で使う操作の権限の点検。

    python3 <spec-loop の根>/scripts/autopilot-check.py lines <版>
    python3 <…>/autopilot-check.py ops   <版>
    python3 <…>/autopilot-check.py check <版> [--project <dir>] [--command '<コマンド>' …]
                                             [--flag-settings <file>] [--managed-settings <file>]

`<版>` は autopilot で回している版の番号で、台帳（`autopilot-ledger.py`。#848）の名前と同じ。**台帳は書かない**——読むのは
`autopilot-ledger.py` の `ledger_path`・`load` で、台帳の場所と形の決まりはそちらの docstring を正とする。
**いつ回し、結果をどう使うか（起動時の確認・各起動の最初）は、入口のスキル（`skills/autopilot/SKILL.md`）を正とする。**

## なぜ在るのか（#789・#790）

#789 の試作では、起動の前に利用者に訊いた線（周 5 まで続ける・推奨を暫定で採る・マージまで）を手作りのメモに書いて、各起動がそれを読んだ。
読み方は起動ごとのモデル任せだった。#790 では、PR を作ったあとのマージが自動モードの権限の判定で拒まれて止まり、**それを起動の前に知る手段が無かった**。
このスクリプトはその 2 つを塞ぐ——**線の項目と値の一覧をここに 1 つだけ置いて機械で検査し、線から周で使う操作を決めて、その許可を起動の前に点検する。**

## 線（`lines`）

台帳の `lines`（`autopilot-ledger.py lines` が書く）は、次の 4 項目がちょうどそろい、値が一覧の中にあるときだけ通る。**値ごとに各起動が何をするかは入口のスキルを正とする。**

| 項目 | 値 |
| --- | --- |
| `上限` | `止まる`・`周 <N> まで続ける`（N は 1 から始まる半角の整数。4 桁まで） |
| `判断が要る` | `推奨を暫定で採る`・`止まる` |
| `commit` | `しない`・`PR で止まる`・`マージまで` |
| `止まる地点` | `spec-review を抜けたら`・`feasibility の後` |

**サインオフのタグ・scaffold・Issue の登録は線の値にしない**——入口は線に依らずそれらをしない。値に置くと選ばれうる。

## 点検する操作（`ops`・`check`）

線がそろった台帳から、周で使う操作を決める（`ops` が出すのと同じ一覧を `check` が点検する）:

- **spec-loop のスクリプト**——`python3 <spec-loop の根>/scripts/<名前>`。線に依らず `SPEC_REVIEW_SCRIPTS`、`止まる地点` が `feasibility の後` なら `FEASIBILITY_SCRIPTS` も。
  **入口はこの絶対パスの形で呼ぶ**（許可の規則は文字列で当たるので、`../../` を含む形で呼ぶと点検と食い違う）
- **git と PR**——`commit` の値で `COMMIT_OPS` から（`しない` なら無し）
- `--command` で渡したもの（繰り返し可）

`check` は、これらの許可を settings で判定し（下の「写し」）、**止まりうる操作**（人が見る）を毎回足す——自動モードの分類器と worktree 隔離のガードは
settings に現れないので、「良い」と出た操作も止まりうる。設定の層（user・project・local・flag・managed）の読み方は dev-loop の
`check-unattended-env.py` の docstring の「設定の層」を正とする。`--project` の既定はメインの作業ツリー（`autopilot-ledger.py` の `main_worktree`）。

## 写し

**`Unreadable`・`read_json`・`run`・`is_claude`・`nearest_claude`・`find_flag_settings`・`config_dir`・`managed_dropins`・`layers`・`perm_value`・
`managed_rules_only`・`collect_rules`・`rule_matches`・`check_permissions` は、dev-loop の `check-unattended-env.py` の写しである**——
spec-loop だけを入れた利用者に dev-loop が在るとは限らず、プラグインをまたいで相対パスで指せない（`autopilot-ledger.py` の `main_worktree` と同じ理由）。
写しが元とずれないことは `scripts/test-autopilot-check.py`（リポジトリの根）が関数と定数のソースを突き合わせて見る。**許可の照合が近似であること**
（規則の形・名指しのコマンドを引数つきで照合する）**と、その他の守らないものは元の docstring の「守らない」を正とする。**

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 通った——`lines`・`ops` は線がそろっている、`check` は要対処も判定できないも無い（**人が見る項目は残っている**——出力を読む） |
| 1 | `check` だけ: 要対処がある（`deny`・`ask` に当たる・`allow` に無い） |
| 2 | 引数が違う（版の形を含む） |
| 3 | 線がそろっていない（台帳に線が無い・項目の欠けや余り・一覧に無い値）。**`check` は点検していない** |
| 4 | 判定できなかった（git の外・台帳が無い・読めない・形が違う、`check` で読めない設定の層がある） |

`check` で要対処と判定できないが両方あれば 1。

## 何を守り、何を守らないか

守る:

- **線の項目が欠けた台帳を 0 にしない**——4 項目のどれかが無ければ 3。
- **一覧に無い項目を通さない**——綴りの違う項目（`上限 `・`commit の線`）は読み手の判定から黙って外れるので 3。
- **一覧に無い値を通さない**——`止める`・`マージ` のような近い値も 3。
- **`周 <N> まで続ける` の N は 1 から始まる半角の整数だけ**——0・先頭の 0・全角の数字・5 桁以上を 3。
- **線の無い台帳を 0 にしない**——起動時の確認を済ませていない台帳は 3。
- **読めない台帳を「線がそろっている」と読まない**——台帳が無い・壊れている・形が違うは 4。
- **台帳を書かない**——`lines`・`ops`・`check` のどれも。
- **線がそろっていなければ権限を点検しない**——`check` は 3 で終え、許可の項目を出さない（そろっていない線から操作を決めない）。
- **spec-loop のスクリプトを線に依らず点検する**——`commit = しない` でも、各起動が呼ぶスクリプトの許可は見る。
- **`commit = マージまで` で `gh pr merge` を点検から落とさない**——#790 で拒まれたのはマージである。
- **`commit = しない` で git の書き込みと PR を点検しない**——使わない操作で要対処を作らない。
- **`止まる地点 = feasibility の後` で feasibility のスクリプトを点検から落とさない。**
- **`deny`・`ask` は `allow` より強い**——どちらかに当たれば、`allow` に当たっても要対処（写しの `check_permissions`）。
- **読めない設定の層があれば、許可を「良い」と言わない**——判定できない（4）。
- **止まりうる操作を、要対処が無くても毎回出す**——点検した操作を全部並べる。
- **要対処があれば 1 で終える**——判定できないが一緒にあっても 1。

守らない:

- **線の値が利用者の意図どおりか**——値の形だけを見る。線を書いたのが利用者かも見ない（`autopilot-ledger.py` の出所の文字列を残すだけ）。
- **入口が線どおりに振る舞うか**——振る舞いは入口のスキルの散文で、ここは判定だけ。
- **分類器・ガードが実際にどの操作を止めるか**——試さない。止まりうるとして並べるだけ（cruise の点検と同じ限界）。
- **点検の一覧の網羅**——正本リポジトリの `CLAUDE.md` が求める操作（別のブランチの規則・タグなど）は `--command` で渡さない限り見えない。
  **判定役（`Agent`）の起動の許可も見ない**——settings の `Bash` の規則しか照合しない。
- **起動の後に設定が変わること**——点検は起動のときの 1 回。
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

LINES = {
    "上限": ("止まる", "周 <N> まで続ける"),
    "判断が要る": ("推奨を暫定で採る", "止まる"),
    "commit": ("しない", "PR で止まる", "マージまで"),
    "止まる地点": ("spec-review を抜けたら", "feasibility の後"),
}
LIMIT_RE = re.compile(r"周 ([1-9][0-9]{0,3}) まで続ける")

# 線に依らず各起動が呼ぶスクリプト（spec-review の周と入口）。`止まる地点 = feasibility の後` なら FEASIBILITY_SCRIPTS も
SPEC_REVIEW_SCRIPTS = ("autopilot-ledger.py", "autopilot-check.py", "check-qa-csv.py", "merge-versions.py",
                       "diff-versions.py", "check-spec-exit.py", "render-diagrams.py")
FEASIBILITY_SCRIPTS = ("check-feasibility-csv.py", "schedule-to-gantt.py")
PR_OPS = ("git switch", "git pull", "git add", "git commit", "git push", "gh pr create")
COMMIT_OPS = {"しない": (), "PR で止まる": PR_OPS, "マージまで": PR_OPS + ("gh pr merge",)}

MANAGED_DEFAULTS = {
    "darwin": "/Library/Application Support/ClaudeCode/managed-settings.json",
    "linux": "/etc/claude-code/managed-settings.json",
}

GOOD, ACTION, UNKNOWN, HUMAN = "良い", "要対処", "判定できない", "人が見る"

EXIT_OK = 0
EXIT_ACTION = 1
EXIT_USAGE = 2
EXIT_LINES = 3
EXIT_UNKNOWN = 4


def ledger_module():
    """同じプラグインの `autopilot-ledger.py`（写さずに読む）。"""
    spec = importlib.util.spec_from_file_location("spec_loop_autopilot_ledger", HERE / "autopilot-ledger.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ここから dev-loop の `check-unattended-env.py` の写し（`scripts/test-autopilot-check.py` が突き合わせる）
class Unreadable:
    """読めなかったこと。**値と別の型にして、空と混ぜない。**"""

    def __init__(self, path, reason):
        self.path = path
        self.reason = reason


def read_json(path):
    """無ければ None（未設定）、壊れていれば `Unreadable`。"""
    p = Path(path)
    try:
        # exists() は使わない——親ディレクトリを読めないときの PermissionError を飲んで「無い」と言う
        text = p.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None
    except (OSError, ValueError) as e:
        # ValueError: UTF-8 として読めない（UnicodeDecodeError）——例外で落とさない
        return Unreadable(p, str(e))
    try:
        data = json.loads(text)
    except ValueError as e:
        return Unreadable(p, str(e))
    if not isinstance(data, dict):
        return Unreadable(p, "オブジェクトでない")
    return data


def run(cmd):
    """(成功したか, 標準出力)。コマンドが無いのも失敗。"""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError:
        return False, ""
    return proc.returncode == 0, proc.stdout


def is_claude(argv0):
    """`claude`、または `…/versions/<版>` で走る本体。"""
    p = Path(argv0)
    return p.name == "claude" or (p.parent.name == "versions" and re.fullmatch(r"\d+(\.\d+)+", p.name) is not None)


def nearest_claude(pid=None):
    """最寄りの祖先の `claude` のプロセス。(pid, argv, 失敗の理由)。見つからなければ (None, None, None)。
    flag の層（`--settings`）と認証（起動した環境）が、同じ 1 つのプロセスを見る。"""
    pid = pid or os.getppid()
    seen = set()
    found = None
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        ok, out = run(["ps", "-o", "ppid=,command=", "-p", str(pid)])
        if not ok or not out.strip():
            return None, None, f"ps が pid {pid} を読めなかった"
        ppid, _, command = out.strip().partition(" ")
        argv = command.split()
        if argv and is_claude(argv[0]):
            found = (pid, argv)
            break  # 最寄りの claude で止める——外側の claude は、このセッションのものではない
        try:
            pid = int(ppid)
        except ValueError:
            return None, None, f"ps の出力を読めなかった: {out.strip()[:80]}"
    return (*found, None) if found else (None, None, None)


def find_flag_settings(pid=None):
    """祖先の `claude … --settings <file>` を探す。(パス or None, 失敗の理由 or None)。"""
    pid, argv, why = nearest_claude(pid)
    if why:
        return None, why
    if argv is None:
        return None, None
    if "--bg-spare" in argv:
        return None, f"最寄りの claude（pid {pid}）は spare から引き継いだセッションで、--settings は argv に無い"
    for i, arg in enumerate(argv):
        if arg == "--settings" and i + 1 < len(argv):
            return argv[i + 1], None
        if arg.startswith("--settings="):
            return arg[len("--settings="):], None
    return None, None


def config_dir(home, env):
    """`$CLAUDE_CONFIG_DIR`、無ければ `~/.claude`。"""
    value = env.get("CLAUDE_CONFIG_DIR")
    return Path(value).expanduser() if value else home / ".claude"


def managed_dropins(managed_path):
    """`managed-settings.json` と同じ場所の `managed-settings.d/*.json`（名前順）。"""
    d = Path(managed_path).parent / "managed-settings.d"
    try:
        # is_dir() も PermissionError を飲むので使わない
        return sorted(p for p in d.iterdir() if p.suffix == ".json")
    except (FileNotFoundError, NotADirectoryError):
        return []
    except OSError as e:
        return [Unreadable(d, str(e))]


def layers(project, flag_path, managed_path, home, env=None, flag_note=None):
    """低い層から高い層の順に (名前, パス, 中身) を返す。"""
    env = os.environ if env is None else env
    stack = [("user", config_dir(home, env) / "settings.json")]
    stack.append(("project", project / ".claude" / "settings.json"))
    stack.append(("local", project / ".claude" / "settings.local.json"))
    stack = [(name, path, read_json(path)) for name, path in stack]
    if flag_path:
        # 渡された（拾った）のに無いのは「未設定」ではない——読むはずのファイルが読めていない
        path = Path(flag_path)
        data = read_json(path)
        stack.append(("flag", path, Unreadable(path, "ファイルが無い") if data is None else data))
    elif flag_note:
        # 祖先を読めなかった——flag の層が在るかどうか分からないので、読めない層として積む
        where = Path("（祖先の claude）")
        stack.append(("flag", where, Unreadable(where, flag_note)))
    if managed_path:
        stack.append(("managed", Path(managed_path), read_json(managed_path)))
        for dropin in managed_dropins(managed_path):
            if isinstance(dropin, Unreadable):
                stack.append(("managed.d", dropin.path, dropin))
            else:
                stack.append(("managed.d", dropin, read_json(dropin)))
    return stack


MANAGED_LAYERS = ("managed", "managed.d")


def perm_value(stack, key):
    """`permissions.<key>` について `effective()` と同じこと。"""
    for name, _path, data in reversed(stack):
        if isinstance(data, Unreadable):
            return data, name
        perms = data.get("permissions") if isinstance(data, dict) else None
        if isinstance(perms, dict) and key in perms:
            return perms[key], name
    return None, None


def managed_rules_only(stack):
    """managed の `allowManagedPermissionRulesOnly` が true か。"""
    return any(isinstance(data, dict) and data.get("allowManagedPermissionRulesOnly") is True
               for name, _path, data in stack if name in MANAGED_LAYERS)


def collect_rules(stack, kind, managed_only=False):
    rules = []
    for name, _path, data in stack:
        if managed_only and name not in MANAGED_LAYERS:
            continue
        if isinstance(data, dict):
            perms = data.get("permissions")
            if isinstance(perms, dict) and isinstance(perms.get(kind), list):
                rules.extend(r for r in perms[kind] if isinstance(r, str))
    return rules


def rule_matches(rule, command):
    """`Bash(...)` の規則が command に当たるか（**近似**。docstring）。"""
    if rule == "Bash":
        return True
    m = re.fullmatch(r"Bash\((.*)\)", rule)
    if not m:
        return False
    body = m.group(1)
    if body in ("*", ":*"):
        return True
    for suffix in (":*", " *", "*"):
        if body.endswith(suffix):
            prefix = body[: -len(suffix)]
            if suffix == "*":
                return command.startswith(prefix)
            return command == prefix or command.startswith(prefix + " ")
    return command == body


def check_permissions(stack, commands, present=False):
    items = []
    managed_only = managed_rules_only(stack)
    allow = collect_rules(stack, "allow", managed_only)
    ask = collect_rules(stack, "ask", managed_only)
    deny = collect_rules(stack, "deny", managed_only)
    broken = [(name, data) for name, _path, data in stack if isinstance(data, Unreadable)]
    mode, mode_layer = perm_value(stack, "defaultMode")
    bypass_off, _ = perm_value(stack, "disableBypassPermissionsMode")
    bypass_ok = mode == "bypassPermissions" and bypass_off not in ("disable", True)
    wait = "確認で周が止まる（利用者の操作を待つ）" if present else "確認されても答える人がいない"
    for command in commands:
        # 名指しのコマンドは引数つきで呼ばれる——引数の無い Bash(git push) は覆っていない
        call = command + " <引数>"
        denied = [r for r in deny if rule_matches(r, call)]
        asked = [r for r in ask if rule_matches(r, call)]
        allowed = [r for r in allow if rule_matches(r, call)]
        label = f"許可: `{command}`"
        if denied:
            items.append((ACTION, label, f"deny に当たる（{', '.join(denied)}）",
                          "deny の規則を外すか、この周の手順からそのコマンドを外す"))
        elif asked:
            # ask は allow より強い——確認を出して、答える人がいないまま止まる
            items.append((ACTION, label, f"ask に当たる（{', '.join(asked)}）——" + wait,
                          "ask の規則を外すか、この周の手順からそのコマンドを外す"))
        elif broken:
            # 読めない層に deny・ask があるかもしれない
            items.append((UNKNOWN, label, "読めない層がある（" + ", ".join(n for n, _ in broken) +
                          "）——そこに deny・ask があるかもしれない", ""))
        elif allowed:
            items.append((GOOD, label, f"allow に当たる（{', '.join(allowed)}）", ""))
        elif bypass_ok:
            items.append((GOOD, label, f"defaultMode が bypassPermissions（{mode_layer}）", ""))
        else:
            shown = mode or "未設定"
            if mode == "bypassPermissions":
                shown += "。ただし disableBypassPermissionsMode で落とされる"
            if managed_only:
                shown += "。managed の allowManagedPermissionRulesOnly で、managed 以外の規則は効かない"
            items.append((ACTION, label,
                          f"allow に無い（defaultMode: {shown}）——拒否・" + wait,
                          f'settings の permissions.allow に "Bash({command}:*)" を足す'))
    return items
# 写しはここまで


class LinesError(Exception):
    """線がそろっていない（3）。"""


def line_problems(values):
    """線の項目と値の誤りの一覧（空ならそろっている）。"""
    problems = [f"項目が無い: {item}" for item in LINES if item not in values]
    problems += [f"一覧に無い項目: {item!r}" for item in values if item not in LINES]
    for item, value in values.items():
        if item not in LINES:
            continue
        if item == "上限":
            ok = value == "止まる" or LIMIT_RE.fullmatch(value) is not None
        else:
            ok = value in LINES[item]
        if not ok:
            problems.append(f"{item} の値が一覧に無い: {value!r}（{'・'.join(LINES[item])}）")
    return problems


def read_lines(lg, version, cwd):
    """台帳の線（項目 → 値）と出所。読めなければ `lg.Unknown`、そろっていなければ `LinesError`。"""
    data = lg.load(lg.ledger_path(version, cwd), version)
    if "lines" not in data:
        raise LinesError(["台帳に線が無い（起動時の確認を済ませていない）"])
    values = data["lines"]["values"]
    problems = line_problems(values)
    if problems:
        raise LinesError(problems)
    return values, data["lines"]["source"]


def operations(values, root=HERE):
    """線から決まる、周で使う操作（点検する順）。"""
    scripts = SPEC_REVIEW_SCRIPTS + (FEASIBILITY_SCRIPTS if values["止まる地点"] == "feasibility の後" else ())
    return [f"python3 {root / name}" for name in scripts] + list(COMMIT_OPS[values["commit"]])


def stoppable_item(commands):
    return (HUMAN, "止まりうる操作",
            "自動モードの分類器と worktree 隔離のガードは settings に現れない——上で「良い」と出た操作も止まりうる: "
            + "、".join(f"`{c}`" for c in commands),
            "起動時に操作ごとに選ぶ: (a) 許可を足す ／ (b) `commit` の線を下げる（`マージまで` → `PR で止まる` → `しない`）"
            " ／ (c) このまま回し、拒まれたらその段で止まる（`stopped`）")


def exit_code(items):
    if any(item[0] == ACTION for item in items):
        return EXIT_ACTION
    if any(item[0] == UNKNOWN for item in items):
        return EXIT_UNKNOWN
    return EXIT_OK


def report(stack, items):
    print("設定の層（低 → 高）:")
    for name, path, data in stack:
        state = "読めない" if isinstance(data, Unreadable) else ("無い" if data is None else "読んだ")
        print(f"  {name}: {path}（{state}）")
    print()
    for status, label, detail, fix in items:
        print(f"[{status}] {label}: {detail}")
        if fix:
            print(f"        → {fix}")
    code = exit_code(items)
    print()
    print({EXIT_OK: "要対処なし（人が見る項目は上を読む）",
           EXIT_ACTION: "要対処がある——起動時に利用者に示して選んでもらう",
           EXIT_UNKNOWN: "判定できない項目がある"}[code])
    return code


def cmd_check(args, values, project):
    flag_path, flag_note = args.flag_settings, None
    if flag_path is None:
        flag_path, flag_note = find_flag_settings()
    managed = args.managed_settings or MANAGED_DEFAULTS.get(sys.platform)
    stack = layers(project, flag_path, managed, Path.home(), None, flag_note)
    commands = operations(values) + [c for c in (args.command or []) if c not in operations(values)]
    items = [(UNKNOWN, f"設定（{name}）", f"{path} を読めなかった: {data.reason}", "")
             for name, path, data in stack if isinstance(data, Unreadable)]
    items += check_permissions(stack, commands)
    items.append(stoppable_item(commands))
    return report(stack, items)


def build_parser():
    p = argparse.ArgumentParser(description="spec-loop の autopilot の線の検査と権限の点検（読むだけ）")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("lines", "ops"):
        sub.add_parser(name).add_argument("version")
    c = sub.add_parser("check")
    c.add_argument("version")
    c.add_argument("--project", type=Path, default=None)
    c.add_argument("--command", action="append", default=None)
    c.add_argument("--flag-settings", default=None)
    c.add_argument("--managed-settings", default=None)
    return p


def main(argv=None, cwd=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    lg = ledger_module()
    try:
        version = lg.parse_version(args.version)
        values, source = read_lines(lg, version, cwd)
        project = args.project if args.cmd == "check" and args.project else None
        if args.cmd == "check" and project is None:
            project = lg.main_worktree(cwd)
    except lg.Usage as exc:
        print(f"引数が違う: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except lg.Unknown as exc:
        print(f"判定できなかった: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN
    except LinesError as exc:
        print("線がそろっていない（台帳は変えていない）:", file=sys.stderr)
        for problem in exc.args[0]:
            print(f"  - {problem}", file=sys.stderr)
        return EXIT_LINES
    if args.cmd == "lines":
        for item in LINES:
            print(f"{item} = {values[item]}")
        print(f"出所: {source}")
    elif args.cmd == "ops":
        for command in operations(values):
            print(command)
    else:
        return cmd_check(args, values, project)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
