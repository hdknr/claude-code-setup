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
| 許可 | settings の `permissions`（`allow`・`ask`・`deny`・`defaultMode`・`disableBypassPermissionsMode`） | 名指しのコマンドごとに、`allow` に当たるか `defaultMode` が `bypassPermissions`（`disableBypassPermissionsMode` で落とされていない） | `deny` か `ask` に当たる（`allow` があっても）／どれも無い |
| 自動継続 | settings の `autoContinueAtUsageLimit` | `true` | 未設定・`false`・真偽値でない |
| 質問の待ち | settings の `askUserQuestionTimeout` | `60s` `5m` `10m` | 未設定・`never`・それ以外 |
| 通知 | `~/.claude.json` の `agentPushNotifEnabled`（`/config` の「Push when Claude decides」）と `inputNeededNotifEnabled`（「Push when actions required」） | `true` | 未設定・`false` |
| スリープ | macOS の `pmset -g custom`・`pmset -g batt`・`ps` | いまの電源の `sleep` が 0、または `-t`・`-w` の無い `caffeinate` が在る | どちらも無い |

**人が見る**（手元のファイルからは判定できないので、毎回出す。終了コードには効かない）:

- **モバイルの登録**——「No mobile registered」はサーバ側の状態で決まる。`/config` で確かめる
- **Remote Control**——いまのセッションで繋がっているかは外から見えない。`remoteControlAtStartup` の値だけ添える
- **蓋を閉じる・電源が変わる**——`pmset` の値は電源ごとで、蓋を閉じればスリープする

## 設定の層

**managed > flag（`--settings`）> local > project > user** の順に重ねる。`permissions.allow`・
`permissions.ask`・`permissions.deny` は**全層を足し合わせ**、それ以外は**いちばん上の層の値**を採る。

- user: `~/.claude/settings.json`（`CLAUDE_CONFIG_DIR` を置いていれば `$CLAUDE_CONFIG_DIR/settings.json`）
- project: `<project>/.claude/settings.json`、local: `<project>/.claude/settings.local.json`
  （`--project` の既定は cwd のリポジトリの**メインの作業ツリー**の root——**worktree の root ではない**。
  gitignore された `settings.local.json` は worktree に無い。リポジトリでなければ cwd）
- flag: `--flag-settings` で渡す。**渡さなければ、最寄りの祖先の `claude` の `--settings <file>`・`--settings=<file>`
  から拾う**（cmux は前者の形で起動する）。**最寄りの `claude` に無ければ、それより外側は見ない**。
  **渡された・拾ったパスが無ければ「判定できない」**（未設定ではない）
- managed: `--managed-settings` で渡す。既定は macOS の
  `/Library/Application Support/ClaudeCode/managed-settings.json`、Linux の `/etc/claude-code/managed-settings.json`。
  **同じ場所の `managed-settings.d/*.json` を名前順に、その上に重ねる**

## 終了コード

- **0**: 要対処も判定できないも無い（**人が見る項目は残っている**——出力を読む）
- **1**: 要対処がある
- **2**: 要対処は無いが、判定できないがある（設定が壊れている・`pmset` が無い・macOS 以外 など）

## 実測した前提（2026-10-25・Claude Code 2.1.310・macOS）

本体の文字列で確かめた。**版が変われば変わりうる**:

- `autoContinueAtUsageLimit` は settings の真偽値で、**未設定のときの既定は別の条件で決まる**
  （文字列からは読み切れない）。だから**未設定を要対処にする**——明示させる
- `askUserQuestionTimeout` は settings の `60s` `5m` `10m` `never` で、既定は `never`
- `agentPushNotifEnabled`・`inputNeededNotifEnabled` は `~/.claude.json` にある
- `managed-settings.d` を読む（`managed-settings.d read failed:` の文言がある）
- managed の `permissions.disableBypassPermissionsMode` は「a session that requests it anyway is downgraded」
- 設定のディレクトリは「$CLAUDE_CONFIG_DIR or ~/.claude」
- 子のセッションには `--settings=<x>` の形で渡す
- **走っている `claude` は、作業中に子として `caffeinate -i -t 300` を張る**。
  **だから `pmset -g assertions` の `PreventUserIdleSystemSleep` は、Claude 自身の作業で 1 になる**
  ——**待機中に保たれる根拠にならない**。`-t` の付いた `caffeinate` は数えない

## 何を守り、何を守らないか

守る:

- **読めなかったものを「良い」に混ぜない**——壊れた JSON・失敗したコマンドは「判定できない」。
  **ファイルが無いのは失敗ではない**（未設定として扱う。flag の層だけは例外——上の「設定の層」）。
  **値を見つける前に読めない層を通ったら、その項目は「判定できない」**——上の層が値を上書きしているかもしれない。
  許可は、`deny`・`ask` に当たらず読めない層がどこかにあれば「判定できない」
- **層の優先順位**——下の層の `true` を、上の層の `false` が打ち消す
- **`deny`・`ask` は `allow` より強い**——どちらかに当たれば要対処
- **Claude 自身の `caffeinate -t` を、スリープ防止の根拠にしない**——`-it 300`・`-t300` のようにまとめた形と、
  `-w`（プロセスの終わりまで）も時限として数える
- **人が見る項目を、要対処が無くても毎回出す**
- **何も書かない**——設定ファイルにも、どこにも

守らない:

- **許可の照合は近似である**——`Bash`・`Bash(*)`・`Bash(<前置き>:*)`・`Bash(<前置き> *)`・
  `Bash(<前置き>*)`・`Bash(<コマンド>)` の形だけを見る。**ハーネスの照合器が正**で、
  **auto モードの分類器が何を通すかは見ない**（`allow` の無いコマンドは、分類器が拒否しても
  答える人がいないので要対処にしている）
- **サーバから配られる managed settings**——ファイルに無いものは見えない
- **`managed-settings.d/` の重ね方**——名前順に後のものが勝つとしているのは慣例からの推定で、本体の文字列では確かめていない
- **`CLAUDE_CONFIG_DIR` を置いたときの `.claude.json` の場所**——`$CLAUDE_CONFIG_DIR/.claude.json` を読む。
  本体の文字列では確かめていない
- **`ask` の規則と `bypassPermissions` の組**——`bypassPermissions` でも `ask` は要対処にしている（確認が出るかは確かめていない。安全側）
- **submodule・`--separate-git-dir` の作業ツリー**——`--project` の既定の root を誤りうる。`--project` で渡す
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
        if argv and Path(argv[0]).name == "claude":
            # 最寄りの claude で止める——外側の claude の --settings は、このセッションのものではない
            for i, arg in enumerate(argv):
                if arg == "--settings" and i + 1 < len(argv):
                    return argv[i + 1], None
                if arg.startswith("--settings="):
                    return arg[len("--settings="):], None
            return None, None
        try:
            pid = int(ppid)
        except ValueError:
            return None, f"ps の出力を読めなかった: {out.strip()[:80]}"
    return None, None


def config_dir(home, env):
    """`$CLAUDE_CONFIG_DIR`、無ければ `~/.claude`。"""
    value = env.get("CLAUDE_CONFIG_DIR")
    return Path(value).expanduser() if value else home / ".claude"


def managed_dropins(managed_path):
    """`managed-settings.json` と同じ場所の `managed-settings.d/*.json`（名前順）。"""
    d = Path(managed_path).parent / "managed-settings.d"
    if not d.is_dir():
        return []
    try:
        return sorted(p for p in d.iterdir() if p.suffix == ".json")
    except OSError as e:
        return [Unreadable(d, str(e))]


def layers(project, flag_path, managed_path, home, env=None):
    """低い層から高い層の順に (名前, パス, 中身) を返す。"""
    env = os.environ if env is None else env
    stack = [("user", config_dir(home, env) / "settings.json")]
    stack.append(("project", project / ".claude" / "settings.json"))
    stack.append(("local", project / ".claude" / "settings.local.json"))
    stack = [(name, path, read_json(path)) for name, path in stack]
    if flag_path:
        # 渡された（拾った）のに無いのは「未設定」ではない——読むはずのファイルが読めていない
        path = Path(flag_path)
        stack.append(("flag", path, read_json(path) if path.exists() else Unreadable(path, "ファイルが無い")))
    if managed_path:
        stack.append(("managed", Path(managed_path), read_json(managed_path)))
        for dropin in managed_dropins(managed_path):
            if isinstance(dropin, Unreadable):
                stack.append(("managed.d", dropin.path, dropin))
            else:
                stack.append(("managed.d", dropin, read_json(dropin)))
    return stack


def effective(stack, key):
    """いちばん上の層の値。(値, 層の名前) か、未設定なら (None, None)。

    **値を見つける前に読めない層を通ったら (`Unreadable`, 層の名前)**——その層が値を
    上書きしているかもしれないので、下の層の値を「良い」の根拠にしない。"""
    for name, _path, data in reversed(stack):
        if isinstance(data, Unreadable):
            return data, name
        if isinstance(data, dict) and key in data:
            return data[key], name
    return None, None


def perm_value(stack, key):
    """`permissions.<key>` について `effective()` と同じこと。"""
    for name, _path, data in reversed(stack):
        if isinstance(data, Unreadable):
            return data, name
        perms = data.get("permissions") if isinstance(data, dict) else None
        if isinstance(perms, dict) and key in perms:
            return perms[key], name
    return None, None


def unknown_item(label, value, layer):
    return (UNKNOWN, label, f"{layer} の層 {value.path} を読めなかった（{value.reason}）——上書きされているかもしれない", "")


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
    ask = collect_rules(stack, "ask")
    deny = collect_rules(stack, "deny")
    broken = [(name, data) for name, _path, data in stack if isinstance(data, Unreadable)]
    mode, mode_layer = perm_value(stack, "defaultMode")
    bypass_off, _ = perm_value(stack, "disableBypassPermissionsMode")
    bypass_ok = mode == "bypassPermissions" and bypass_off not in ("disable", True)
    for command in commands:
        denied = [r for r in deny if rule_matches(r, command)]
        asked = [r for r in ask if rule_matches(r, command)]
        allowed = [r for r in allow if rule_matches(r, command)]
        label = f"許可: `{command}`"
        if denied:
            items.append((ACTION, label, f"deny に当たる（{', '.join(denied)}）",
                          "deny の規則を外すか、この周の手順からそのコマンドを外す"))
        elif asked:
            # ask は allow より強い——確認を出して、答える人がいないまま止まる
            items.append((ACTION, label, f"ask に当たる（{', '.join(asked)}）——確認されても答える人がいない",
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
            items.append((ACTION, label,
                          f"allow に無い（defaultMode: {shown}）——拒否・確認されても答える人がいない",
                          f'settings の permissions.allow に "Bash({command}:*)" を足す'))
    return items


def check_auto_continue(stack):
    value, layer = effective(stack, "autoContinueAtUsageLimit")
    label = "自動継続（autoContinueAtUsageLimit）"
    if isinstance(value, Unreadable):
        return [unknown_item(label, value, layer)]
    if value is True:
        return [(GOOD, label, f"true（{layer}）", "")]
    shown = "未設定（既定は条件で変わる）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'settings に "autoContinueAtUsageLimit": true を書く（/config の「Continue automatically at usage limit」）')]


def check_question_timeout(stack):
    value, layer = effective(stack, "askUserQuestionTimeout")
    label = "質問の待ち（askUserQuestionTimeout）"
    if isinstance(value, Unreadable):
        return [unknown_item(label, value, layer)]
    if value in TIMEOUT_OK:
        return [(GOOD, label, f"{value}（{layer}）", "")]
    shown = "未設定（既定は never）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'settings に "askUserQuestionTimeout": "10m" などを書く（60s / 5m / 10m）——never だと質問で止まり続ける')]


def check_notifications(home, env=None):
    env = os.environ if env is None else env
    # CLAUDE_CONFIG_DIR を置いたときは、その中の .claude.json（近似。docstring）
    path = (config_dir(home, env) if env.get("CLAUDE_CONFIG_DIR") else home) / ".claude.json"
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
            shown = "未設定" if not isinstance(data, dict) or key not in data else json.dumps(data[key])
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


def timed_caffeinate(argv):
    """`-t`（時間）か `-w`（プロセスの終わりまで）を持つか。`-it 300`・`-t300` のようにまとめた形も見る。"""
    for arg in argv[1:]:
        if not arg.startswith("-"):
            if arg.isdigit():
                continue  # -t・-w の値
            return False  # ここから先は caffeinate が走らせるコマンド
        if re.fullmatch(r"-[dimsutw]*[tw][dimsutw]*\d*", arg):
            return True
    return False


def long_lived_caffeinate(ps_text):
    """`-t`・`-w` の無い caffeinate のコマンド行。"""
    found = []
    for line in ps_text.splitlines():
        argv = line.split()
        if argv and Path(argv[0]).name == "caffeinate" and not timed_caffeinate(argv):
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
    if isinstance(rc, Unreadable):
        rc_shown = f"remoteControlAtStartup: {layer} の層を読めなかった"
    else:
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


def gather(project, commands, flag_path, managed_path, home, platform, flag_note=None, env=None):
    stack = layers(project, flag_path, managed_path, home, env)
    items = []
    for name, path, data in stack:
        if isinstance(data, Unreadable):
            items.append((UNKNOWN, f"設定（{name}）", f"{path} を読めなかった: {data.reason}", ""))
    if flag_note:
        items.append((UNKNOWN, "設定（flag）", flag_note, "--flag-settings で渡す"))
    items += check_permissions(stack, commands)
    items += check_auto_continue(stack)
    items += check_question_timeout(stack)
    items += check_notifications(home, env)
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
