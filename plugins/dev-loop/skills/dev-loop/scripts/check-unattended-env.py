#!/usr/bin/env python3
r"""利用者が不在になる前に 1 度だけ回す、環境の点検（#394）。

    python3 <このスキルの base ディレクトリ>/scripts/check-unattended-env.py [--project <dir>]
        [--command '<コマンド>' ...] [--flag-settings <file>] [--managed-settings <file>]
    python3 <このスキルの base ディレクトリ>/scripts/check-unattended-env.py --push-result '<返り値>'

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
| 自動継続 | settings の `autoContinueAtUsageLimit`（**managed・flag・user の層だけ**） | `true` | 未設定・`false`・真偽値でない |
| 質問の待ち | settings の `askUserQuestionTimeout`（**managed・flag・user の層だけ**） | `60s` `5m` `10m` | 未設定・`never`・それ以外 |
| 通知 | グローバル設定（下の「設定の層」）の `agentPushNotifEnabled`（`/config` の「Push when Claude decides」）と `inputNeededNotifEnabled`（「Push when actions required」） | `true` | 未設定・`false` |
| スリープ | macOS の `pmset -g custom`・`pmset -g batt`・`ps` | いまの電源の `sleep` が 0、または `-t`・`-w` の無い `caffeinate` が system の idle sleep を防いでいる（`-i`・`-d`・`-s` か、アサーションのフラグ無し） | どちらも無い |

**人が見る**（手元のファイルからは判定できないので、毎回出す。終了コードには効かない）:

- **モバイルの登録**——「No mobile registered」はサーバ側の状態で決まる。`/config` で確かめ、下の「通知の試験」で届くかを見る
- **Remote Control**——いまのセッションで繋がっているかは外から見えない。`remoteControlAtStartup` の値だけ添える。
  **iPhone がつながる先は、いまのセッション（`/remote-control`）であって `claude rc` の待ち受けではない**
  ——待ち受けは新しいセッションを起こすので、そこから送った 1 行は作業中のセッションに届かない
- **蓋を閉じる・電源が変わる**——`pmset` の値は電源ごとで、蓋を閉じればスリープする

## 通知の試験（`--push-result`）

    python3 check-unattended-env.py --push-result '<PushNotification の返り値>'

**送るのはモデル、離れるのは人**なので、スクリプトは**返り値の判定だけ**をする（設定は読まない）。
手順（いつ送るか）は `SKILL.md` の環境点検の項を正とする。返り値の文字列は部分一致で見る——
`Remote Control inactive` と `Mobile push requested` には、非対話のセッション（`isNonInteractiveSession`。`-p` など）でなければ前に
`Terminal notification sent.` が付く（本体は OS の通知が実際に出たかを見ていない）。

| 返り値に含まれる | 判定 | 原因 | 対処 |
| --- | --- | --- | --- |
| `mobile push is disabled in /config` | 要対処 | 「Push when Claude decides」（`agentPushNotifEnabled`）がオフ | `/config` でオン |
| `this terminal is active` | やり直す（2） | 使用中と判定された（端末のフォーカスが分かればそれだけで決まり、分からなければ最後の操作から 60 秒以内） | **失敗ではない。** 遅らせて、端末を前面から外し、端末にも iPhone にも触らずに送り直す |
| `Remote Control inactive` | 要対処 | いまのセッションが Remote Control につながっていない | 作業中のセッションで `/remote-control` |
| `Mobile push requested` | 人が見る | **要求しただけ**——届いたかはサーバと iPhone で決まる | iPhone に届いたか。届かなければ iPhone の通知の許可・集中モード・アカウントと組織 |
| （どれでもない・空） | 判定できない（2） | 知らない文言（版が違う・写し間違い） | **送り直さない。** 返り値を言い換えずにそのまま渡し直す |

**判定の順に注意**（本体の `PushNotification`）: **使用中は Remote Control の有無より先に止まる**ので、
省かれた陰で Remote Control が切れていても分からない。**Remote Control がつながっていなければ
`/config` のオフは出ない**——直すたびに送り直して、次の返り値を見る。

## 設定の層

**managed > flag（`--settings`）> local > project > user** の順に重ねる。`permissions.allow`・
`permissions.ask`・`permissions.deny` は**全層を足し合わせ**、それ以外は**いちばん上の層の値**を採る。
**例外が 2 つある**: `autoContinueAtUsageLimit`・`askUserQuestionTimeout` は **managed・flag・user の層しか読まない**
（project・local に書いても効かない）。managed の `allowManagedPermissionRulesOnly` が `true` なら、
**許可の規則は managed の層のものだけ**を数える。

- user: `~/.claude/settings.json`（`CLAUDE_CONFIG_DIR` を置いていれば `$CLAUDE_CONFIG_DIR/settings.json`）
- project: `<project>/.claude/settings.json`、local: `<project>/.claude/settings.local.json`
  （`--project` の既定は cwd のリポジトリの**メインの作業ツリー**の root——**worktree の root ではない**。
  gitignore された `settings.local.json` は worktree に無い。リポジトリでなければ cwd）
- flag: `--flag-settings` で渡す。**渡さなければ、最寄りの祖先の `claude` の `--settings <file>`・`--settings=<file>`
  から拾う**（cmux は前者の形で起動する）。**最寄りの `claude` に無ければ、それより外側は見ない**。
  `claude` は `argv[0]` の名前が `claude` か、`…/versions/<版>` の本体を指す。
  **渡された・拾ったパスが無ければ「判定できない」**（未設定ではない）。**`ps` が失敗したときと、
  最寄りの `claude` が spare（`--bg-spare`。設定は引き継ぎで渡り、argv に無い）のときも「判定できない」**——
  flag の層を読めない層として積む
- managed: `--managed-settings` で渡す。既定は macOS の
  `/Library/Application Support/ClaudeCode/managed-settings.json`、Linux の `/etc/claude-code/managed-settings.json`。
  **同じ場所の `managed-settings.d/*.json` を名前順に、その上に重ねる**
- グローバル設定（通知）: `<設定のディレクトリ>/.config.json` が在って空でなければそれ、
  無ければ `$CLAUDE_CONFIG_DIR/.claude.json`（置いていなければ `~/.claude.json`）

## 終了コード

- **0**: 要対処も判定できないも無い（**人が見る項目は残っている**——出力を読む）
- **1**: 要対処がある
- **2**: 要対処は無いが、判定できないがある（設定が壊れている・`pmset` が無い・macOS 以外 など）

`--push-result` も同じ 3 つで返す。**2 は「やり直す」（使用中で省かれた）と「判定できない」（知らない返り値）の両方**
——**終了コードでは分けられないので、ラベルを読む**（前者は送り直す、後者は返り値を渡し直す）。

## 実測した前提（2026-10-25・Claude Code 2.1.310・macOS）

本体の文字列で確かめた。**版が変われば変わりうる**:

- `autoContinueAtUsageLimit` は settings の真偽値で、**未設定のときの既定は別の条件で決まる**
  （文字列からは読み切れない）。だから**未設定を要対処にする**——明示させる
- `askUserQuestionTimeout` は settings の `60s` `5m` `10m` `never` で、既定は `never`
- `autoContinueAtUsageLimit`・`askUserQuestionTimeout` は `["policySettings","flagSettings","userSettings"]` の
  層だけから読む（`EM()`）
- `agentPushNotifEnabled`・`inputNeededNotifEnabled` はグローバル設定にある。グローバル設定の場所は
  `<設定のディレクトリ>/.config.json` が在って空でなければそれ、無ければ `.claude<接尾辞>.json`（`y_()`）
- managed（policySettings）の `allowManagedPermissionRulesOnly` が `true` なら、managed 以外の規則は無視される
- `managed-settings.d` を読む（`managed-settings.d read failed:` の文言がある）
- managed の `permissions.disableBypassPermissionsMode` は「a session that requests it anyway is downgraded」
- 設定のディレクトリは「$CLAUDE_CONFIG_DIR or ~/.claude」
- 子のセッションには `--settings=<x>` の形で渡す
- **走っている `claude` は、作業中に子として `caffeinate -i -t 300` を張る**。
  **だから `pmset -g assertions` の `PreventUserIdleSystemSleep` は、Claude 自身の作業で 1 になる**
  ——**待機中に保たれる根拠にならない**。`-t` の付いた `caffeinate` は数えない
- `PushNotification` の判定は ① Remote Control がつながっていて `agentPushNotifEnabled` が偽 → `config_off`、
  ② 使用中 → `user_present`、③ Remote Control がつながっていない → `no_transport`、④ 送信、の順
  （`CLAUDE_CODE_REMOTE`・リモートのセッション・transport が持続するセッションでは ①〜③ をすべて飛ばして送る）。
  使用中は、端末のフォーカスが分かればそれだけで決まり、分からなければ最後の操作から 60 秒以内（`Ins()`）。
  返り値の文字列は上の「通知の試験」の表のとおり
- 「No mobile registered」は `/config` の表示（`has_active_channel === false`）で、`PushNotification` の返り値ではない
- `claude remote-control`（`claude rc`）は「spawned sessions」を起こす待ち受け（`--help`）

## 何を守り、何を守らないか

守る:

- **読めなかったものを「良い」に混ぜない**——壊れた JSON・失敗したコマンドは「判定できない」。
  **ファイルが無いのは失敗ではない**（未設定として扱う。flag の層だけは例外——上の「設定の層」）。
  **値を見つける前に読めない層を通ったら、その項目は「判定できない」**——上の層が値を上書きしているかもしれない。
  許可は、`deny`・`ask` に当たらず読めない層がどこかにあれば「判定できない」
- **層の優先順位**——下の層の `true` を、上の層の `false` が打ち消す
- **`deny`・`ask` は `allow` より強い**——どちらかに当たれば要対処
- **Claude 自身の `caffeinate -t` を、スリープ防止の根拠にしない**——`-it 300`・`-t300` のようにまとめた形と、
  `-w`（プロセスの終わりまで）も時限として数える。`-m`（ディスク）・`-u`（利用者の操作。既定 5 秒）だけの形は数えない
- **人が見る項目を、要対処が無くても毎回出す**
- **使用中で省かれた通知を失敗と数えない**——`--push-result` は「やり直す」（2）で返し、1 にしない。
  **知らない返り値とはラベルで分ける**（どちらも 2）
- **送信の要求を「届いた」と言わない**——`Mobile push requested` は人が見る（iPhone に届いたか）
- **知らない返り値を「良い」に混ぜない**——判定できない
- **何も書かない**——設定ファイルにも、どこにも

守らない:

- **許可の照合は近似である**——`Bash`・`Bash(*)`・`Bash(<前置き>:*)`・`Bash(<前置き> *)`・
  `Bash(<前置き>*)`・`Bash(<コマンド>)` の形だけを見る。**名指しのコマンドは引数つきで呼ばれるものとして
  照合する**——引数の無い `Bash(git push)` は `git push -u origin <ブランチ>` に当たらないので、覆っていない。**ハーネスの照合器が正**で、
  **auto モードの分類器が何を通すかは見ない**（`allow` の無いコマンドは、分類器が拒否しても
  答える人がいないので要対処にしている）
- **サーバから配られる managed settings**——ファイルに無いものは見えない
- **`managed-settings.d/` の重ね方**——名前順に後のものが勝つとしているのは慣例からの推定で、本体の文字列では確かめていない
- **グローバル設定のファイル名の接尾辞**——本体は `.claude<接尾辞>.json` で、接尾辞は認証の形で変わる
  （`-custom-oauth` など）。**接尾辞の無い `.claude.json` だけを見る**。本体が `.config.json` を選ぶ条件の
  うち、空のファイルを書き込み可能な権限で選ぶ分岐は写したが、それより前の分岐（`J()`）は読み切れていない
- **祖先の `claude` の `--allowedTools`・`--disallowedTools`・`--permission-mode`**——規則の出所だが読まない
- **`autoContinueAtUsageLimit: true` が十分であること**——本体は課金の種類とフラグでも自動継続を止める。
  `true` は必要条件で、「良い」はそれを満たしたことしか言わない。**実データにも、続かなかった形がある**（#454。
  `scripts/count-usage-limit-resumes.py` で数えた。件数は少ない）——待ちを張らなかった停止があり（理由は記録に残らない）、
  Claude Code が終わると待ちは消える。
  タイマーを保険に張るかは利用者が決める（`docs/plugins/dev-loop-cruise.md` の §5）
- **macOS の managed preferences（plist）**——読まない
- **`caffeinate <コマンド>` の形**——コマンドが終われば防止も終わるが、`-t` の無い形として数える
- **`ask` の規則と `bypassPermissions` の組**——`bypassPermissions` でも `ask` は要対処にしている（確認が出るかは確かめていない。安全側）
- **submodule・`--separate-git-dir` の作業ツリー**——`--project` の既定の root を誤りうる。`--project` で渡す
- **`--settings` に JSON を直接渡した形と、パスに空白を含む形**——`ps` の出力からは正しく切れない。
  `--flag-settings` で渡す
- **macOS 以外のスリープ**——判定できないと出す
- **2.1.310 以外の版でキー名が同じであること**——`PushNotification` の返り値の文字列も同じ
- **iPhone に届いたこと**——`Mobile push requested` から先は見えない
- **iPhone からの操作が使用中になるか**——本体からは読み切れていない（利用者の実測。#407）。だから手順は両方から離れる形にしてある
"""

import argparse
import json
import os
import re
import stat
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
RETRY = "やり直す"  # --push-result だけが使う。原因は分かっていて、送り直せば済む


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
        if argv and is_claude(argv[0]):
            # 最寄りの claude で止める——外側の claude の --settings は、このセッションのものではない
            if "--bg-spare" in argv:
                return None, f"最寄りの claude（pid {pid}）は spare から引き継いだセッションで、--settings は argv に無い"
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


SESSION_LAYERS = ("user", "flag", "managed", "managed.d")  # 本体の EM() が読む層
MANAGED_LAYERS = ("managed", "managed.d")


def effective(stack, key, only=None):
    """いちばん上の層の値。(値, 層の名前) か、未設定なら (None, None)。

    **値を見つける前に読めない層を通ったら (`Unreadable`, 層の名前)**——その層が値を
    上書きしているかもしれないので、下の層の値を「良い」の根拠にしない。
    `only` を渡せば、その名前の層だけを見る。"""
    for name, _path, data in reversed(stack):
        if only is not None and name not in only:
            continue
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


def check_permissions(stack, commands):
    items = []
    managed_only = managed_rules_only(stack)
    allow = collect_rules(stack, "allow", managed_only)
    ask = collect_rules(stack, "ask", managed_only)
    deny = collect_rules(stack, "deny", managed_only)
    broken = [(name, data) for name, _path, data in stack if isinstance(data, Unreadable)]
    mode, mode_layer = perm_value(stack, "defaultMode")
    bypass_off, _ = perm_value(stack, "disableBypassPermissionsMode")
    bypass_ok = mode == "bypassPermissions" and bypass_off not in ("disable", True)
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
            if managed_only:
                shown += "。managed の allowManagedPermissionRulesOnly で、managed 以外の規則は効かない"
            items.append((ACTION, label,
                          f"allow に無い（defaultMode: {shown}）——拒否・確認されても答える人がいない",
                          f'settings の permissions.allow に "Bash({command}:*)" を足す'))
    return items


def check_auto_continue(stack):
    value, layer = effective(stack, "autoContinueAtUsageLimit", SESSION_LAYERS)
    label = "自動継続（autoContinueAtUsageLimit）"
    if isinstance(value, Unreadable):
        return [unknown_item(label, value, layer)]
    if value is True:
        return [(GOOD, label, f"true（{layer}）", "")]
    shown = "未設定（既定は条件で変わる）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'user の settings に "autoContinueAtUsageLimit": true を書く'
             '（/config の「Continue automatically at usage limit」。project・local では効かない）')]


def check_question_timeout(stack):
    value, layer = effective(stack, "askUserQuestionTimeout", SESSION_LAYERS)
    label = "質問の待ち（askUserQuestionTimeout）"
    if isinstance(value, Unreadable):
        return [unknown_item(label, value, layer)]
    if value in TIMEOUT_OK:
        return [(GOOD, label, f"{value}（{layer}）", "")]
    shown = "未設定（既定は never）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'user の settings に "askUserQuestionTimeout": "10m" などを書く（60s / 5m / 10m。project・local では効かない）'
             '——never だと質問で止まり続ける')]


def global_config_path(home, env):
    """本体の y_() の写し: `<設定のディレクトリ>/.config.json` が在って空でなければそれ、
    無ければ `$CLAUDE_CONFIG_DIR/.claude.json`（置いていなければ `~/.claude.json`）。接尾辞は見ない（docstring）。"""
    legacy = (Path(env["CLAUDE_CONFIG_DIR"]).expanduser() if env.get("CLAUDE_CONFIG_DIR") else home) / ".claude.json"
    candidate = config_dir(home, env) / ".config.json"
    try:
        st = candidate.stat()
    except OSError:
        return legacy
    if stat.S_ISREG(st.st_mode) and (st.st_size > 0 or (st.st_mode & 0o222 and not legacy.exists())):
        return candidate
    return legacy


def check_notifications(home, env=None):
    env = os.environ if env is None else env
    path = global_config_path(home, env)
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


def prevents_idle_sleep(argv):
    """system の idle sleep を防ぐか——`-i`・`-d`・`-s` を持つか、アサーションのフラグが 1 つも無い
    （`man caffeinate`: 無ければ idle sleep を防ぐ）。`-m`（ディスク）・`-u`（利用者の操作）だけなら防がない。"""
    flags = ""
    for arg in argv[1:]:
        if not arg.startswith("-"):
            if arg.isdigit():
                continue
            break
        flags += re.sub(r"\d", "", arg[1:])
    assertions = set(flags) & set("dimsu")
    return not assertions or bool(assertions & set("ids"))


def long_lived_caffeinate(ps_text):
    """`-t`・`-w` の無い、idle sleep を防ぐ caffeinate のコマンド行。"""
    found = []
    for line in ps_text.splitlines():
        argv = line.split()
        if (argv and Path(argv[0]).name == "caffeinate" and not timed_caffeinate(argv)
                and prevents_idle_sleep(argv)):
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
        (HUMAN, "モバイルの登録", "/config の通知の欄に「No mobile registered」が出ていないか",
         "通知の試験で届くかを見る（SKILL.md の環境点検の項。返り値は --push-result で判定）"),
        (HUMAN, "Remote Control", f"いまのセッションが繋がっているか（{rc_shown}）",
         "作業中のセッションで /remote-control——claude rc の待ち受けは別のセッションを起こす。"
         "iPhone から 1 行送って、このセッションに届くかを見る"),
        (HUMAN, "電源と蓋", "蓋を閉じない・電源を AC のまま保つ（pmset の値は電源ごと）", ""),
    ]


PUSH_RESULTS = (  # (返り値に含まれる文字列, 判定, 原因, 対処)。判定の順は本体の PushNotification と同じ
    ("mobile push is disabled in /config", ACTION,
     "「Push when Claude decides」（agentPushNotifEnabled）がオフ", "/config でオン"),
    ("this terminal is active", RETRY,
     "使用中と判定された（端末のフォーカスが分かればそれだけで決まり、分からなければ最後の操作から 60 秒以内）",
     "失敗ではない。遅らせて、端末を前面から外し（別のアプリを前面に）、端末にも iPhone にも触らずに送り直す"),
    ("Remote Control inactive", ACTION,
     "いまのセッションが Remote Control につながっていない", "作業中のセッションで /remote-control"),
    ("Mobile push requested", HUMAN,
     "要求しただけ——届いたかはサーバと iPhone で決まる",
     "iPhone に届いたか。届かなければ iPhone の通知の許可・集中モード・アカウントと組織"),
)


def check_push_result(text):
    for needle, status, cause, fix in PUSH_RESULTS:
        if needle in text:
            return [(status, "通知の試験", cause, fix)]
    return [(UNKNOWN, "通知の試験", f"知らない返り値: {text!r}",
             "送り直さない——PushNotification の返り値を言い換えずにそのまま渡し直す。それでも知らないなら版が違う")]


def report_push(items, out=None):
    out = out or sys.stdout
    for status, label, detail, fix in items:
        print(f"[{status}] {label}: {detail}", file=out)
        print(f"        → {fix}", file=out)
    return exit_code(items)


def exit_code(items):
    statuses = {s for s, *_ in items}
    if ACTION in statuses:
        return 1
    if UNKNOWN in statuses or RETRY in statuses:
        return 2
    return 0


def gather(project, commands, flag_path, managed_path, home, platform, flag_note=None, env=None):
    stack = layers(project, flag_path, managed_path, home, env, flag_note)
    items = []
    for name, path, data in stack:
        if isinstance(data, Unreadable):
            items.append((UNKNOWN, f"設定（{name}）", f"{path} を読めなかった: {data.reason}",
                          "--flag-settings で渡す" if name == "flag" else ""))
    items += check_permissions(stack, commands)
    items += check_auto_continue(stack)
    items += check_question_timeout(stack)
    items += check_notifications(home, env)
    items += check_sleep(platform)
    items += human_items(stack)
    return stack, items


def report(stack, items, out=None):
    out = out or sys.stdout
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
    ap.add_argument("--push-result", default=None,
                    help="PushNotification の返り値を判定する（設定は読まない）")
    args = ap.parse_args(argv)

    if args.push_result is not None:
        return report_push(check_push_result(args.push_result))

    flag_path, flag_note = args.flag_settings, None
    if flag_path is None:
        flag_path, flag_note = find_flag_settings()
    managed = args.managed_settings or MANAGED_DEFAULTS.get(sys.platform)
    stack, items = gather(args.project or default_project(), tuple(args.command or DEFAULT_COMMANDS),
                          flag_path, managed, Path.home(), sys.platform, flag_note)
    return report(stack, items)


if __name__ == "__main__":
    sys.exit(main())
