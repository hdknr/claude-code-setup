#!/usr/bin/env python3
r"""利用者が不在になる前に 1 度だけ回す、環境の点検（#394）。

    python3 <このスキルの base ディレクトリ>/scripts/check-unattended-env.py [--project <dir>]
        [--command '<コマンド>' ...] [--flag-settings <file>] [--managed-settings <file>]

**直さない。読むだけ**——何が足りないかと、どう直すかを出す。**利用者の設定を書き換える道具は、
不在の前に回すものとしては危険が勝る**（`--fix` を置かないのは意図である）。

## なぜ要るか（#389）

利用者不在で複数の周を回した運用で、**通知は「No mobile registered」のまま届かず、原因は
切り分けられなかった**。`PushNotification` は「Push when Claude decides」がオフだと
`mobile push is disabled in /config` で送られない。**どれも不在になってからでは直せない**
——気づく人がいない。

## 点検する項目

| 項目 | 見るもの | 良い | 要対処 |
| --- | --- | --- | --- |
| 許可 | settings の `permissions`（`allow`・`deny`・`defaultMode`） | 名指しのコマンドごとに、`allow` に当たるか `defaultMode` が `bypassPermissions` | `deny` に当たる（`allow` があっても）／どちらも無い |
| 自動継続 | settings の `autoContinueAtUsageLimit` | `true` | 未設定・`false`・真偽値でない |
| 質問の待ち | settings の `askUserQuestionTimeout` | `60s` `5m` `10m` | 未設定・`never`・それ以外 |
| 通知 | `~/.claude.json` の `agentPushNotifEnabled`（`/config` の「Push when Claude decides」）と `inputNeededNotifEnabled`（「Push when actions required」） | `true` | 未設定・`false` |
| スリープ | macOS の `pmset -g custom`・`pmset -g batt`・`ps` | いまの電源の `sleep` が 0、または `-t` の無い `caffeinate` が在る | どちらも無い |

**人が見る**（手元のファイルからは判定できないので、毎回出す。終了コードには効かない）:

- **モバイルの登録**——「No mobile registered」はサーバ側の状態で決まる。`/config` で確かめる
- **Remote Control**——いまのセッションで繋がっているかは外から見えない。`remoteControlAtStartup` の値だけ添える
- **蓋を閉じる・電源が変わる**——`pmset` の値は電源ごとで、蓋を閉じればスリープする

## 設定の層

**managed > flag（`--settings`）> local > project > user** の順に重ねる。`permissions.allow`・
`permissions.deny` は**全層を足し合わせ**、それ以外は**いちばん上の層の値**を採る。

- user: `~/.claude/settings.json`
- project: `<project>/.claude/settings.json`、local: `<project>/.claude/settings.local.json`
  （`--project` の既定は cwd のリポジトリの**メインの作業ツリー**の root——**worktree の root ではない**。
  gitignore された `settings.local.json` は worktree に無い。リポジトリでなければ cwd）
- flag: `--flag-settings` で渡す。**渡さなければ、祖先のプロセスの `claude … --settings <file>` から拾う**
  （cmux はこの形で起動する）
- managed: `--managed-settings` で渡す。既定は macOS の
  `/Library/Application Support/ClaudeCode/managed-settings.json`、Linux の `/etc/claude-code/managed-settings.json`

## 終了コード

- **0**: 要対処も判定できないも無い（**人が見る項目は残っている**——出力を読む）
- **1**: 要対処がある
- **2**: 要対処は無いが、判定できないがある（設定が壊れている・`pmset` が無い・macOS 以外 など）

## 実測した前提（2026-10-25・Claude Code 2.1.310・macOS）

本体の文字列で確かめた。**版が変われば変わりうる**:

- `autoContinueAtUsageLimit` は settings の真偽値で、**未設定のときの既定は別の条件で決まる**
  （文字列からは読み切れない）。だから**未設定を要対処にする**——明示させる
- `askUserQuestionTimeout` は settings の `60s` `5m` `10m` `never` で、既定は `never`
- `agentPushNotifEnabled`・`inputNeededNotifEnabled` は `~/.claude.json` にあり、既定は false
- **走っている `claude` は、作業中に子として `caffeinate -i -t 300` を張る**。
  **だから `pmset -g assertions` の `PreventUserIdleSystemSleep` は、Claude 自身の作業で 1 になる**
  ——**待機中に保たれる根拠にならない**。`-t` の付いた `caffeinate` は数えない

## 何を守り、何を守らないか

守る:

- **読めなかったものを「良い」に混ぜない**——壊れた JSON・失敗したコマンドは「判定できない」。
  **ファイルが無いのは失敗ではない**（未設定として扱う）
- **層の優先順位**——下の層の `true` を、上の層の `false` が打ち消す
- **`deny` は `allow` より強い**——両方に当たれば要対処
- **Claude 自身の `caffeinate -t` を、スリープ防止の根拠にしない**
- **人が見る項目を、要対処が無くても毎回出す**
- **何も書かない**——設定ファイルにも、どこにも

守らない:

- **許可の照合は近似である**——`Bash`・`Bash(*)`・`Bash(<前置き>:*)`・`Bash(<前置き> *)`・
  `Bash(<前置き>*)`・`Bash(<コマンド>)` の形だけを見る。**ハーネスの照合器が正**で、
  **auto モードの分類器が何を通すかは見ない**（`allow` の無いコマンドは、分類器が拒否しても
  答える人がいないので要対処にしている）
- **サーバから配られる managed settings**——ファイルに無いものは見えない
- **`--settings` に JSON を直接渡した形と、パスに空白を含む形**——`ps` の出力からは正しく切れない。
  `--flag-settings` で渡す
- **macOS 以外のスリープ**——判定できないと出す
- **2.1.310 以外の版でキー名が同じであること**
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_COMMANDS = (
    "git push",
    "gh pr create",
    "gh pr merge",
    "gh pr comment",
    "gh issue create",
)
TIMEOUT_OK = ("60s", "5m", "10m")
MANAGED_DEFAULTS = {
    "darwin": "/Library/Application Support/ClaudeCode/managed-settings.json",
    "linux": "/etc/claude-code/managed-settings.json",
}

GOOD, ACTION, UNKNOWN, HUMAN = "良い", "要対処", "判定できない", "人が見る"


class Unreadable:
    """読めなかったこと。**値と別の型にして、空と混ぜない。**"""

    def __init__(self, path, reason):
        self.path = path
        self.reason = reason


def read_json(path):
    """無ければ None（未設定）、壊れていれば `Unreadable`。"""
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
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


def find_flag_settings(pid=None):
    """祖先の `claude … --settings <file>` を探す。(パス or None, 失敗の理由 or None)。"""
    pid = pid or os.getppid()
    seen = set()
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        ok, out = run(["ps", "-o", "ppid=,command=", "-p", str(pid)])
        if not ok or not out.strip():
            return None, f"ps が pid {pid} を読めなかった"
        ppid, _, command = out.strip().partition(" ")
        argv = command.split()
        if argv and Path(argv[0]).name == "claude" and "--settings" in argv:
            i = argv.index("--settings")
            if i + 1 < len(argv):
                return argv[i + 1], None
        try:
            pid = int(ppid)
        except ValueError:
            return None, f"ps の出力を読めなかった: {out.strip()[:80]}"
    return None, None


def layers(project, flag_path, managed_path, home):
    """低い層から高い層の順に (名前, パス, 中身) を返す。"""
    out = [("user", home / ".claude" / "settings.json")]
    out.append(("project", project / ".claude" / "settings.json"))
    out.append(("local", project / ".claude" / "settings.local.json"))
    if flag_path:
        out.append(("flag", Path(flag_path)))
    if managed_path:
        out.append(("managed", Path(managed_path)))
    return [(name, path, read_json(path)) for name, path in out]


def effective(stack, key):
    """いちばん上の層の値。(値, 層の名前) か、未設定なら (None, None)。"""
    for name, _path, data in reversed(stack):
        if isinstance(data, dict) and key in data:
            return data[key], name
    return None, None


def collect_rules(stack, kind):
    rules = []
    for _name, _path, data in stack:
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


def check_permissions(stack, commands):
    items = []
    allow = collect_rules(stack, "allow")
    deny = collect_rules(stack, "deny")
    # defaultMode は permissions の中にあるので、effective() では取れない
    mode, mode_layer = None, None
    for name, _path, data in reversed(stack):
        perms = data.get("permissions") if isinstance(data, dict) else None
        if isinstance(perms, dict) and "defaultMode" in perms:
            mode, mode_layer = perms["defaultMode"], name
            break
    for command in commands:
        denied = [r for r in deny if rule_matches(r, command)]
        allowed = [r for r in allow if rule_matches(r, command)]
        label = f"許可: `{command}`"
        if denied:
            items.append((ACTION, label, f"deny に当たる（{', '.join(denied)}）",
                          "deny の規則を外すか、この周の手順からそのコマンドを外す"))
        elif allowed:
            items.append((GOOD, label, f"allow に当たる（{', '.join(allowed)}）", ""))
        elif mode == "bypassPermissions":
            items.append((GOOD, label, f"defaultMode が bypassPermissions（{mode_layer}）", ""))
        else:
            items.append((ACTION, label,
                          f"allow に無い（defaultMode: {mode or '未設定'}）——拒否・確認されても答える人がいない",
                          f'settings の permissions.allow に "Bash({command}:*)" を足す'))
    return items


def check_auto_continue(stack):
    value, layer = effective(stack, "autoContinueAtUsageLimit")
    label = "自動継続（autoContinueAtUsageLimit）"
    if value is True:
        return [(GOOD, label, f"true（{layer}）", "")]
    shown = "未設定（既定は条件で変わる）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'settings に "autoContinueAtUsageLimit": true を書く（/config の「Continue automatically at usage limit」）')]


def check_question_timeout(stack):
    value, layer = effective(stack, "askUserQuestionTimeout")
    label = "質問の待ち（askUserQuestionTimeout）"
    if value in TIMEOUT_OK:
        return [(GOOD, label, f"{value}（{layer}）", "")]
    shown = "未設定（既定は never）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'settings に "askUserQuestionTimeout": "10m" などを書く（60s / 5m / 10m）——never だと質問で止まり続ける')]


def check_notifications(home):
    path = home / ".claude.json"
    data = read_json(path)
    items = []
    keys = (("agentPushNotifEnabled", "Push when Claude decides"),
            ("inputNeededNotifEnabled", "Push when actions required"))
    for key, ui in keys:
        label = f"通知（{key}）"
        if isinstance(data, Unreadable):
            items.append((UNKNOWN, label, f"{path} を読めなかった: {data.reason}", ""))
        elif isinstance(data, dict) and data.get(key) is True:
            items.append((GOOD, label, "true", ""))
        else:
            shown = "未設定（既定は false）" if not isinstance(data, dict) or key not in data else json.dumps(data[key])
            items.append((ACTION, label, shown, f"/config の「{ui}」をオンにする"))
    return items


def parse_pmset_custom(text):
    """{電源の名前: sleep の分}。"""
    out, source = {}, None
    for line in text.splitlines():
        if line and not line.startswith(" ") and line.rstrip().endswith(":"):
            source = line.rstrip()[:-1]
            continue
        m = re.match(r"^\s*sleep\s+(\d+)", line)
        if m and source:
            out[source] = int(m.group(1))
    return out


def long_lived_caffeinate(ps_text):
    """`-t` の無い caffeinate のコマンド行。"""
    found = []
    for line in ps_text.splitlines():
        argv = line.split()
        if argv and Path(argv[0]).name == "caffeinate" and "-t" not in argv:
            found.append(line.strip())
    return found


def check_sleep(platform):
    label = "スリープ"
    if platform != "darwin":
        return [(UNKNOWN, label, f"{platform} のスリープは点検しない（macOS だけ）", "")]
    ok_custom, custom = run(["pmset", "-g", "custom"])
    ok_batt, batt = run(["pmset", "-g", "batt"])
    ok_ps, ps_text = run(["ps", "-axo", "command="])
    if not (ok_custom and ok_batt and ok_ps):
        return [(UNKNOWN, label, "pmset か ps を読めなかった", "")]
    m = re.search(r"Now drawing from '([^']+)'", batt)
    sleeps = parse_pmset_custom(custom)
    if not m or m.group(1) not in sleeps:
        return [(UNKNOWN, label, "いまの電源の sleep を pmset から読めなかった", "")]
    source, minutes = m.group(1), sleeps[m.group(1)]
    if minutes == 0:
        return [(GOOD, label, f"{source} の sleep が 0（スリープしない）", "")]
    keep = long_lived_caffeinate(ps_text)
    if keep:
        return [(GOOD, label, f"-t の無い caffeinate が在る（{keep[0][:60]}）", "")]
    return [(ACTION, label,
             f"{source} の sleep が {minutes} 分で、-t の無い caffeinate が無い"
             "（Claude 自身の caffeinate -t 300 は作業中しか張られない）",
             "別の端末で `caffeinate -i` を回しておく（または `sudo pmset -c sleep 0`）")]


def human_items(stack):
    rc, layer = effective(stack, "remoteControlAtStartup")
    rc_shown = f"remoteControlAtStartup: {json.dumps(rc)}（{layer}）" if layer else "remoteControlAtStartup: 未設定"
    return [
        (HUMAN, "モバイルの登録", "/config の通知の欄に「No mobile registered」が出ていないか", ""),
        (HUMAN, "Remote Control", f"いまのセッションが繋がっているか（{rc_shown}）", ""),
        (HUMAN, "電源と蓋", "蓋を閉じない・電源を AC のまま保つ（pmset の値は電源ごと）", ""),
    ]


def exit_code(items):
    statuses = {s for s, *_ in items}
    if ACTION in statuses:
        return 1
    if UNKNOWN in statuses:
        return 2
    return 0


def gather(project, commands, flag_path, managed_path, home, platform, flag_note=None):
    stack = layers(project, flag_path, managed_path, home)
    items = []
    for name, path, data in stack:
        if isinstance(data, Unreadable):
            items.append((UNKNOWN, f"設定（{name}）", f"{path} を読めなかった: {data.reason}", ""))
    if flag_note:
        items.append((UNKNOWN, "設定（flag）", flag_note, "--flag-settings で渡す"))
    items += check_permissions(stack, commands)
    items += check_auto_continue(stack)
    items += check_question_timeout(stack)
    items += check_notifications(home)
    items += check_sleep(platform)
    items += human_items(stack)
    return stack, items


def report(stack, items, out=sys.stdout):
    print("設定の層（低 → 高）:", file=out)
    for name, path, data in stack:
        state = "無い" if data is None else ("読めない" if isinstance(data, Unreadable) else "在る")
        print(f"  {name:8} {path}  [{state}]", file=out)
    print(file=out)
    for status, label, detail, fix in items:
        print(f"[{status}] {label}: {detail}", file=out)
        if fix:
            print(f"        → {fix}", file=out)
    code = exit_code(items)
    print(file=out)
    print({0: "要対処なし（人が見る項目は上を読む）",
           1: "要対処がある——不在になる前に直す",
           2: "判定できない項目がある"}[code], file=out)
    return code


def default_project():
    """メインの作業ツリーの root。**worktree の root ではない**——gitignore された
    `settings.local.json` はメインの作業ツリーにしか無い。"""
    ok, out = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"])
    if ok and out.strip():
        return Path(out.strip()).parent
    return Path.cwd()


def main(argv=None):
    ap = argparse.ArgumentParser(description="利用者が不在になる前の環境点検（読むだけ）")
    ap.add_argument("--project", type=Path, default=None)
    ap.add_argument("--command", action="append", default=None,
                    help="許可を点検するコマンド（繰り返し可。既定: %s）" % ", ".join(DEFAULT_COMMANDS))
    ap.add_argument("--flag-settings", default=None)
    ap.add_argument("--managed-settings", default=None)
    args = ap.parse_args(argv)

    flag_path, flag_note = args.flag_settings, None
    if flag_path is None:
        flag_path, flag_note = find_flag_settings()
    managed = args.managed_settings or MANAGED_DEFAULTS.get(sys.platform)
    stack, items = gather(args.project or default_project(), tuple(args.command or DEFAULT_COMMANDS),
                          flag_path, managed, Path.home(), sys.platform, flag_note)
    return report(stack, items)


if __name__ == "__main__":
    sys.exit(main())
