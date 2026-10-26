#!/usr/bin/env python3
"""`check-unattended-env.py` の回帰テスト。

    python3 scripts/test-check-unattended-env.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）——
`test-find-cycle.py` と同じ形で、**`dev-loop` はどのリポジトリでも使えるスキル**なので。

**このテストは実環境を読まない・書かない。** 毎回テンポラリに偽の `HOME` とプロジェクトを作り、
`pmset`・`ps` は `PATH` の先頭に置いた偽物で答える（`assert_not_real_home` が担保する）。
**実 `HOME` を読むと、利用者の設定でテストの結果が変わる**——通っても何の証明にもならない。

**変異テストを含む。** 本体の docstring の「守る」の各行に変異を 1 つ以上当て、
**壊したのに緑のままなら失格**とする。**変異の前に、元の本体で全部緑であること（陽性対照）を見る。**
"""
import builtins
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "check-unattended-env.py"
COMMANDS = ("git push", "gh pr merge")

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"cue_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_home(path: Path) -> None:
    resolved = path.resolve()
    assert resolved != Path.home().resolve(), "テストが実 HOME を対象にしている"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool, sink: list) -> None:
    if not cond:
        sink.append(name)


class Env:
    """偽の HOME・プロジェクト・`pmset`・`ps`。"""

    def __init__(self, base: Path):
        self.home = base / "home"
        self.project = base / "project"
        self.bin = base / "bin"
        for d in (self.home / ".claude", self.project / ".claude", self.bin):
            d.mkdir(parents=True, exist_ok=True)
        assert_not_real_home(self.home)
        self.sleep(0)
        self.processes(["/usr/bin/caffeinate -i -t 300"])

    def write(self, path: Path, data) -> Path:
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
        return path

    def user(self, data):
        return self.write(self.home / ".claude" / "settings.json", data)

    def project_settings(self, data):
        return self.write(self.project / ".claude" / "settings.json", data)

    def local(self, data):
        return self.write(self.project / ".claude" / "settings.local.json", data)

    def global_config(self, data):
        return self.write(self.home / ".claude.json", data)

    def fake(self, name, body):
        p = self.bin / name
        p.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        p.chmod(0o755)

    def sleep(self, minutes, fail=False):
        if fail:
            self.fake("pmset", "exit 1\n")
            return
        self.fake("pmset", f"""case "$2" in
custom) printf 'Battery Power:\\n sleep                1\\nAC Power:\\n sleep                {minutes}\\n' ;;
batt) printf "Now drawing from 'AC Power'\\n" ;;
esac
""")

    def processes(self, lines):
        text = "\\n".join(lines)
        self.fake("ps", f"""case "$*" in
*-axo*) printf '{text}\\n' ;;
*"-p 500"*) printf '  400 /Users/x/.local/bin/claude --session-id s --settings /tmp/flag.json\\n' ;;
*"-p 400"*) printf '    1 /sbin/launchd\\n' ;;
*"-p 600"*) printf '    1 /opt/claude --settings=/tmp/eq.json -p\\n' ;;
*"-p 700"*) printf '  500 /Users/x/.local/bin/claude --session-id inner\\n' ;;
*"-p 800"*) printf '  400 /Users/x/.local/share/claude/versions/2.1.310 --session-id v --settings /tmp/v.json\\n' ;;
*"-p 810"*) printf '  400 claude bg-spare --bg-spare /tmp/claim.sock\\n' ;;
*) exit 1 ;;
esac
""")

    def all_good(self):
        """要対処の無い状態。ここから 1 つずつ崩す。"""
        self.user({"permissions": {"allow": ["Bash(git push:*)", "Bash(gh pr merge *)"]},
                   "autoContinueAtUsageLimit": True, "askUserQuestionTimeout": "10m"})
        self.global_config({"agentPushNotifEnabled": True, "inputNeededNotifEnabled": True})
        return self


PATH_READS = ("read_text", "read_bytes", "open", "stat", "exists", "is_file", "is_dir", "iterdir", "glob", "rglob")
READ_ENTRIES = ([(Path, n) for n in PATH_READS]
                + [(builtins, "open"), (subprocess, "run"), (subprocess, "Popen")])


@contextlib.contextmanager
def recording_reads():
    """OS への読む入口を呼ばれた順に記録する（呼び出しはそのまま通す）。

    **関数名ではなく OS への入口で見る**——本体の読む入口は道具関数に散っており
    （`read_json`・`run`・`managed_dropins`・`global_config_path`）、関数名でフックすると
    入口を足すたびに素通りする（#424 の N2: `check_notifications` を呼ぶ変異が素通りした）。
    **記録するのは `READ_ENTRIES` だけで、ほかは素通りする**——`Path` の他のメソッド（`resolve` など。
    3.14 では `lstat`・`is_symlink` も `stat` を経由しない）・`os` の直呼び（`os.stat`・`os.listdir`・
    `os.scandir`・`os.lstat`・`os.path.*`・`os.open`・`os.system`）・`io.open`・import 時に束ねた名前
    （`from subprocess import run`）・環境変数の読み取り。本体は `--push-result` の分岐でどれも使っていない
    （環境変数は全点検の側で読む）。
    **`os.stat`・`os.path.*` を差し替えないのは、argparse が gettext 経由で `os.stat` を呼ぶから**——記録が本体の読みでなくなる。
    **ほかの `os` の直呼びと `io.open` は、差し替えても `--push-result` の記録は汚れない（#424 の 2 パス目で測った）が、
    足していないだけである**——だから 3.14 の `lstat`・`is_symlink` を呼ぶ変異は、ローカル（3.14）では素通りする
    （CI の 3.12 では `stat` を経由するので捕まる）。
    **記録名には持ち主を付ける**（`Path.open` と `builtins.open` を分ける）——同じ名前だと、陽性対照の
    「`Path` の読みを拾う」が `builtins.open` だけで満たされ、`Path` の差し替えが死んでいても緑になる。
    **記録器が効いていることは、使う側が陽性対照で見る。**"""
    reads: list[str] = []
    originals = [(owner, name, getattr(owner, name)) for owner, name in READ_ENTRIES]

    def wrap(name, f):
        def recorded(*a, **k):
            reads.append(name)
            return f(*a, **k)
        return recorded

    for owner, name, f in originals:
        setattr(owner, name, wrap(f"{owner.__name__}.{name}", f))
    try:
        yield reads
    finally:
        for owner, name, f in originals:
            setattr(owner, name, f)


@contextlib.contextmanager
def scenario(mod_path: Path):
    with tempfile.TemporaryDirectory() as tmp:
        env = Env(Path(tmp))
        old = os.environ["PATH"]
        os.environ["PATH"] = f"{env.bin}{os.pathsep}{old}"
        try:
            yield env
        finally:
            os.environ["PATH"] = old


def run(mod, env, flag=None, managed=None, platform="darwin", environ=None, flag_note=None):
    # environ は既定で空——実環境の CLAUDE_CONFIG_DIR を読むと、実 HOME の外の利用者の設定を読む
    stack, items = mod.gather(env.project, COMMANDS, flag, managed, env.home, platform, flag_note,
                              env=environ if environ is not None else {})
    buf = io.StringIO()
    code = mod.report(stack, items, out=buf)
    return code, items, buf.getvalue()


def status_of(items, label_part):
    return [s for s, label, *_ in items if label_part in label]


def suite(script: Path) -> list[str]:
    """全シナリオ。失敗した名前を返す。"""
    mod = load(script)
    bad: list[str] = []

    # 陽性の基準: 全部良い → 0、人が見るは 3 件出る
    with scenario(script) as env:
        env.all_good()
        code, items, out = run(mod, env)
        check("全部良ければ 0", code == 0, bad)
        check("人が見るを毎回出す", sum(1 for s, *_ in items if s == mod.HUMAN) == 3, bad)
        check("人が見るは出力にも出る", "[人が見る] モバイルの登録" in out, bad)

    # 守る: 読めなかったものを良いに混ぜない
    with scenario(script) as env:
        env.all_good()
        env.local("{ broken")
        code, items, _ = run(mod, env)
        check("壊れた JSON は判定できない", status_of(items, "設定（local）") == [mod.UNKNOWN], bad)
        check("判定できないだけなら 2", code == 2, bad)
        check("自動継続を読まない local が壊れていても、自動継続は user で決まる",
              status_of(items, "自動継続") == [mod.GOOD], bad)
        check("読めない層があれば allow だけで許可を良いにしない",
              status_of(items, "`git push`") == [mod.UNKNOWN], bad)
        env.user({"permissions": {"deny": ["Bash(git push:*)"]}})
        _, items, _ = run(mod, env)
        check("読めない層があっても deny に当たれば要対処", status_of(items, "`git push`") == [mod.ACTION], bad)
    with scenario(script) as env:
        env.all_good()
        _, items, _ = run(mod, env, flag=env.write(env.project / "flag.json", "{ broken"))
        check("読めない上の層を飛ばして下の層の true を良いにしない",
              status_of(items, "自動継続") == [mod.UNKNOWN], bad)
        check("読めない上の層があれば質問の待ちも判定できない",
              status_of(items, "質問の待ち") == [mod.UNKNOWN], bad)
    with scenario(script) as env:
        env.all_good()
        _, items, _ = run(mod, env, flag_note="ps が pid 1 を読めなかった")
        check("祖先を読めなければ flag の層は判定できない", status_of(items, "設定（flag）") == [mod.UNKNOWN], bad)
        check("祖先を読めなければ自動継続も判定できない", status_of(items, "自動継続") == [mod.UNKNOWN], bad)
        check("祖先を読めなければ allow だけで許可を良いにしない",
              status_of(items, "`git push`") == [mod.UNKNOWN], bad)
    # 親ディレクトリを読めないファイルは「無い」ではない（exists() は PermissionError を飲む）
    with tempfile.TemporaryDirectory() as tmp:
        locked = Path(tmp) / "locked"
        locked.mkdir()
        target = locked / "settings.json"
        target.write_text("{}", encoding="utf-8")
        locked.chmod(0)
        try:
            check("親ディレクトリを読めなければ判定できない", isinstance(mod.read_json(target), mod.Unreadable), bad)
        finally:
            locked.chmod(0o755)
        check("無いファイルは未設定", mod.read_json(Path(tmp) / "nope.json") is None, bad)
        binary = Path(tmp) / "binary.json"
        binary.write_bytes(b"\xff\xfe{")
        try:
            check("UTF-8 として読めなければ判定できない", isinstance(mod.read_json(binary), mod.Unreadable), bad)
        except ValueError:
            check("UTF-8 として読めないファイルで例外を投げない", False, bad)
    with scenario(script) as env:
        env.all_good()
        _, items, _ = run(mod, env, flag=env.project / "no-such-flag.json")
        check("flag のパスが無ければ判定できない", status_of(items, "設定（flag）") == [mod.UNKNOWN], bad)
        check("flag のパスが無ければ自動継続も判定できない", status_of(items, "自動継続") == [mod.UNKNOWN], bad)
    with scenario(script) as env:
        env.all_good()
        env.global_config("[1]")
        code, items, _ = run(mod, env)
        check("~/.claude.json が壊れていれば通知は判定できない",
              status_of(items, "agentPushNotifEnabled") == [mod.UNKNOWN], bad)
    # ファイルが無いのは失敗ではない
    with scenario(script) as env:
        code, items, _ = run(mod, env)
        check("ファイルが無ければ判定できないを出さない",
              mod.UNKNOWN not in {s for s, *_ in items}, bad)
        check("ファイルが無ければ自動継続は要対処", status_of(items, "自動継続") == [mod.ACTION], bad)
        check("要対処があれば 1", code == 1, bad)

    # 守る: 層の優先順位
    with scenario(script) as env:
        env.all_good()
        flag = env.write(env.project / "flag.json", {"autoContinueAtUsageLimit": False})
        _, items, _ = run(mod, env, flag=flag)
        check("flag の false が user の true を打ち消す", status_of(items, "自動継続") == [mod.ACTION], bad)
        env.user({"permissions": {"allow": ["Bash(git push:*)", "Bash(gh pr merge *)"]},
                  "autoContinueAtUsageLimit": False, "askUserQuestionTimeout": "10m"})
        flag = env.write(env.project / "flag.json", {"autoContinueAtUsageLimit": True})
        _, items, _ = run(mod, env, flag=flag)
        check("flag の true が user の false に勝つ", status_of(items, "自動継続") == [mod.GOOD], bad)
        managed = env.write(env.project / "managed.json", {"askUserQuestionTimeout": "never"})
        _, items, _ = run(mod, env, flag=flag, managed=managed)
        check("managed の never が user の 10m に勝つ", status_of(items, "質問の待ち") == [mod.ACTION], bad)

        check("managed の false が flag の true に勝つ",
              status_of(run(mod, env, flag=flag, managed=env.write(
                  env.project / "managed.json", {"autoContinueAtUsageLimit": False}))[1], "自動継続")
              == [mod.ACTION], bad)
    # 自動継続・質問の待ちは project・local から読まない（2.1.310 の EM() は policy・flag・user だけ）
    with scenario(script) as env:
        env.global_config({"agentPushNotifEnabled": True, "inputNeededNotifEnabled": True})
        env.local({"autoContinueAtUsageLimit": True, "askUserQuestionTimeout": "10m"})
        env.project_settings({"autoContinueAtUsageLimit": True, "askUserQuestionTimeout": "10m"})
        _, items, _ = run(mod, env)
        check("local・project の true は自動継続に効かない", status_of(items, "自動継続") == [mod.ACTION], bad)
        check("local・project の 10m は質問の待ちに効かない", status_of(items, "質問の待ち") == [mod.ACTION], bad)
    # project と local の並び（許可の defaultMode で当てる）
    with scenario(script) as env:
        env.all_good()
        env.user({"autoContinueAtUsageLimit": True, "askUserQuestionTimeout": "10m"})
        env.project_settings({"permissions": {"defaultMode": "auto"}})
        env.local({"permissions": {"defaultMode": "bypassPermissions"}})
        _, items, _ = run(mod, env)
        check("local の defaultMode が project に勝つ", status_of(items, "`git push`") == [mod.GOOD], bad)
        env.project_settings({"permissions": {"defaultMode": "bypassPermissions"}})
        env.local({"permissions": {"defaultMode": "auto"}})
        _, items, _ = run(mod, env)
        check("local の auto が project の bypass を打ち消す", status_of(items, "`git push`") == [mod.ACTION], bad)
    # managed-settings.d は managed の上に重なる
    with scenario(script) as env:
        env.all_good()
        mdir = env.project / "managed"
        (mdir / "managed-settings.d").mkdir(parents=True)
        env.write(mdir / "managed-settings.d" / "10.json", {"askUserQuestionTimeout": "never"})
        _, items, _ = run(mod, env, managed=mdir / "managed-settings.json")
        check("managed-settings.d の never が user の 10m に勝つ", status_of(items, "質問の待ち") == [mod.ACTION], bad)
        env.write(mdir / "managed-settings.d" / "20.json", "{ broken")
        _, items, _ = run(mod, env, managed=mdir / "managed-settings.json")
        check("managed-settings.d の壊れたファイルは判定できない",
              status_of(items, "設定（managed.d）") == [mod.UNKNOWN], bad)
    # CLAUDE_CONFIG_DIR
    with scenario(script) as env:
        alt = env.home.parent / "alt"
        alt.mkdir()
        assert_not_real_home(alt)
        env.write(alt / "settings.json", {"autoContinueAtUsageLimit": True})
        env.write(alt / ".claude.json", {"agentPushNotifEnabled": True})
        _, items, _ = run(mod, env, environ={"CLAUDE_CONFIG_DIR": str(alt)})
        check("CLAUDE_CONFIG_DIR の settings.json を user の層にする", status_of(items, "自動継続") == [mod.GOOD], bad)
        check("CLAUDE_CONFIG_DIR の .claude.json を通知に読む",
              status_of(items, "agentPushNotifEnabled") == [mod.GOOD], bad)

    # グローバル設定は <設定のディレクトリ>/.config.json が在って空でなければそれ（2.1.310 の y_()）
    with scenario(script) as env:
        env.all_good()
        env.write(env.home / ".claude" / ".config.json",
                  {"agentPushNotifEnabled": False, "inputNeededNotifEnabled": True})
        _, items, _ = run(mod, env)
        check(".config.json が在ればそちらを通知に読む", status_of(items, "agentPushNotifEnabled") == [mod.ACTION], bad)
        env.write(env.home / ".claude" / ".config.json", "")
        _, items, _ = run(mod, env)
        check("空の .config.json は飛ばして .claude.json を読む",
              status_of(items, "agentPushNotifEnabled") == [mod.GOOD], bad)

    # 通知の値も厳密に
    with scenario(script) as env:
        env.all_good()
        env.global_config({"agentPushNotifEnabled": False, "inputNeededNotifEnabled": "true"})
        _, items, _ = run(mod, env)
        check("通知の false は要対処", status_of(items, "agentPushNotifEnabled") == [mod.ACTION], bad)
        check("通知の文字列 \"true\" は良いにしない",
              status_of(items, "inputNeededNotifEnabled") == [mod.ACTION], bad)

    # 値の検査は厳密に
    with scenario(script) as env:
        env.all_good()
        env.user({"permissions": {"allow": ["Bash(git push:*)", "Bash(gh pr merge *)"]},
                  "autoContinueAtUsageLimit": "true", "askUserQuestionTimeout": "15m"})
        _, items, _ = run(mod, env)
        check("文字列の \"true\" は良いにしない", status_of(items, "自動継続") == [mod.ACTION], bad)
        check("列挙に無い値は良いにしない", status_of(items, "質問の待ち") == [mod.ACTION], bad)

    # 守る: deny は allow より強い（層をまたいでも）
    with scenario(script) as env:
        env.all_good()
        env.local({"permissions": {"deny": ["Bash(git push:*)"]}})
        _, items, _ = run(mod, env)
        check("deny は allow に勝つ", status_of(items, "`git push`") == [mod.ACTION], bad)
        check("deny は他のコマンドに漏れない", status_of(items, "`gh pr merge`") == [mod.GOOD], bad)
    with scenario(script) as env:
        env.all_good()
        env.local({"permissions": {"ask": ["Bash(git push:*)"]}})
        _, items, _ = run(mod, env)
        check("ask は allow に勝つ", status_of(items, "`git push`") == [mod.ACTION], bad)
        check("ask は他のコマンドに漏れない", status_of(items, "`gh pr merge`") == [mod.GOOD], bad)
    # 規則の書式
    for rule, cmd, want in (("Bash", "git push", True), ("Bash(*)", "git push", True),
                            ("Bash(git:*)", "git push", True), ("Bash(git push *)", "git push", True),
                            ("Bash(git push)", "git push", True), ("Bash(gh pr:*)", "git push", False),
                            ("Bash(git push:*)", "git pushx", False), ("Read", "git push", False)):
        check(f"規則 {rule} と {cmd} → {want}", mod.rule_matches(rule, cmd) is want, bad)
    with scenario(script) as env:
        env.all_good()
        env.user({"permissions": {"allow": ["Bash(git push)", "Bash(gh pr merge:*)"]},
                  "autoContinueAtUsageLimit": True, "askUserQuestionTimeout": "10m"})
        _, items, _ = run(mod, env)
        check("引数の無い Bash(git push) は引数つきの git push を覆わない",
              status_of(items, "`git push`") == [mod.ACTION], bad)
        check("Bash(gh pr merge:*) は覆う", status_of(items, "`gh pr merge`") == [mod.GOOD], bad)
    with scenario(script) as env:
        env.all_good()
        managed = env.write(env.project / "managed.json", {"allowManagedPermissionRulesOnly": True,
                                                           "permissions": {"allow": ["Bash(gh pr merge:*)"]}})
        _, items, _ = run(mod, env, managed=managed)
        check("allowManagedPermissionRulesOnly なら user の allow は効かない",
              status_of(items, "`git push`") == [mod.ACTION], bad)
        check("allowManagedPermissionRulesOnly でも managed の allow は効く",
              status_of(items, "`gh pr merge`") == [mod.GOOD], bad)
    with scenario(script) as env:
        env.all_good()
        env.user({"permissions": {"defaultMode": "bypassPermissions"},
                  "autoContinueAtUsageLimit": True, "askUserQuestionTimeout": "5m"})
        code, items, _ = run(mod, env)
        check("bypassPermissions なら許可は良い", status_of(items, "`git push`") == [mod.GOOD], bad)
        env.local({"permissions": {"defaultMode": "auto"}})
        _, items, _ = run(mod, env)
        check("上の層の defaultMode が勝つ", status_of(items, "`git push`") == [mod.ACTION], bad)
        env.local({})
        managed = env.write(env.project / "managed.json",
                            {"permissions": {"disableBypassPermissionsMode": "disable"}})
        _, items, _ = run(mod, env, managed=managed)
        check("disableBypassPermissionsMode があれば bypass を良いにしない",
              status_of(items, "`git push`") == [mod.ACTION], bad)

    # 守る: Claude 自身の caffeinate -t を根拠にしない
    with scenario(script) as env:
        env.all_good()
        env.sleep(10)
        code, items, _ = run(mod, env)
        check("caffeinate -t 300 だけならスリープは要対処", status_of(items, "スリープ") == [mod.ACTION], bad)
        env.processes(["/usr/bin/caffeinate -i -t 300", "caffeinate -i"])
        _, items, _ = run(mod, env)
        check("-t の無い caffeinate があれば良い", status_of(items, "スリープ") == [mod.GOOD], bad)
        for line in ("caffeinate -it 300", "caffeinate -t300 -i", "caffeinate -i -w 123"):
            env.processes(["/usr/bin/caffeinate -i -t 300", line])
            _, items, _ = run(mod, env)
            check(f"{line} は時限として数える", status_of(items, "スリープ") == [mod.ACTION], bad)
        env.processes(["caffeinate -di"])
        _, items, _ = run(mod, env)
        check("caffeinate -di は時限でない", status_of(items, "スリープ") == [mod.GOOD], bad)
        for line in ("caffeinate -m", "caffeinate -u", "caffeinate -mu"):
            env.processes(["/usr/bin/caffeinate -i -t 300", line])
            _, items, _ = run(mod, env)
            check(f"{line} は system の idle sleep を防がない", status_of(items, "スリープ") == [mod.ACTION], bad)
        env.processes(["/usr/bin/caffeinate"])
        _, items, _ = run(mod, env)
        check("フラグの無い caffeinate は idle sleep を防ぐ", status_of(items, "スリープ") == [mod.GOOD], bad)
        env.sleep(0, fail=True)
        _, items, _ = run(mod, env)
        check("pmset が失敗すれば判定できない", status_of(items, "スリープ") == [mod.UNKNOWN], bad)
        _, items, _ = run(mod, env, platform="linux")
        check("macOS 以外は判定できない", status_of(items, "スリープ") == [mod.UNKNOWN], bad)

    # flag 層を祖先の claude から拾う
    with scenario(script) as env:
        path, note = mod.find_flag_settings(500)
        check("祖先の --settings を拾う", path == "/tmp/flag.json" and note is None, bad)
        path, note = mod.find_flag_settings(999)
        check("ps が読めなければ理由を返す", path is None and note, bad)
        path, note = mod.find_flag_settings(600)
        check("--settings=<file> の形も拾う", path == "/tmp/eq.json" and note is None, bad)
        path, note = mod.find_flag_settings(700)
        check("最寄りの claude で止まり、外側の --settings を拾わない", path is None and note is None, bad)
        path, note = mod.find_flag_settings(800)
        check("versions/<版> で走る本体を claude と見る", path == "/tmp/v.json" and note is None, bad)
        path, note = mod.find_flag_settings(810)
        check("spare のセッションは判定できない理由を返す", path is None and note, bad)

    # 通知の試験: 返り値は本体（2.1.310）の文字列と一字一句同じものを当てる。端末の通知あり・なしの 2 形ずつ
    push = {
        "Push not sent — mobile push is disabled in /config.": mod.ACTION,
        "Not sent — this terminal is active, so your output here already reaches the user; "
        "a separate notification would be redundant.": mod.RETRY,
        "Terminal notification sent. Mobile push not sent (Remote Control inactive).": mod.ACTION,
        "Mobile push not sent (Remote Control inactive).": mod.ACTION,
        "Terminal notification sent. Mobile push requested.": mod.HUMAN,
        "Mobile push requested.": mod.HUMAN,
        "": mod.UNKNOWN,
        "Notification delivered.": mod.UNKNOWN,
    }
    for text, want in push.items():
        items = mod.check_push_result(text)
        check(f"返り値 {text!r} は {want}", [s for s, *_ in items] == [want], bad)
    active = mod.check_push_result("Not sent — this terminal is active, so ...")
    check("使用中で省かれたのは失敗（1）ではなく 2", mod.exit_code(active) == 2, bad)
    check("使用中の対処は送り直す", "送り直す" in active[0][3] and "失敗ではない" in active[0][3], bad)
    check("使用中の対処は端末を前面から外す（フォーカスが分かれば 60 秒は効かない）", "前面から外し" in active[0][3], bad)
    unknown = mod.check_push_result("Notification delivered.")
    check("知らない返り値も 2 だが、ラベルで使用中と分かれる",
          mod.exit_code(unknown) == 2 and unknown[0][0] != active[0][0], bad)
    check("知らない返り値は送り直させない", "送り直さない" in unknown[0][3] and "前面から外し" not in unknown[0][3], bad)
    buf = io.StringIO()
    mod.report_push(active, out=buf)
    check("使用中は [やり直す] と出し、[判定できない] と出さない",
          "[やり直す]" in buf.getvalue() and "[判定できない]" not in buf.getvalue(), bad)
    buf = io.StringIO()
    code = mod.report_push(mod.check_push_result("Terminal notification sent. Mobile push requested."), out=buf)
    check("送信の要求は 0 で、届いたかを人が見る", code == 0 and "[人が見る]" in buf.getvalue()
          and "iPhone に届いたか" in buf.getvalue(), bad)
    check("Remote Control が切れていれば /remote-control を案内する",
          "/remote-control" in mod.check_push_result("Mobile push not sent (Remote Control inactive).")[0][3], bad)
    # 原因と対処は行ごとに見る——判定だけ見ると、原因・対処を別の行と入れ替えても緑になる
    for text, cause, fix in (
            ("Push not sent — mobile push is disabled in /config.", "agentPushNotifEnabled", "/config でオン"),
            ("Mobile push not sent (Remote Control inactive).", "Remote Control につながっていない", "/remote-control"),
            ("Mobile push requested.", "要求しただけ", "iPhone に届いたか")):
        (_, _, got_cause, got_fix), = mod.check_push_result(text)
        check(f"返り値 {text!r} の原因と対処", cause in got_cause and fix in got_fix, bad)
    check("知らない返り値は、その文字列を原因に出す", "'Notification delivered.'" in unknown[0][2], bad)
    check("使用中の原因はフォーカスと 60 秒を言う（本体の Ins() と P3e=60000）",
          "フォーカス" in active[0][2] and "から 60 秒以内" in active[0][2], bad)
    with scenario(script) as env:
        env.all_good()
        before = {p: p.read_bytes() for p in Path(env.home).parent.rglob("*") if p.is_file()}
        # 変異で判定の分岐が外れても実環境を読まないよう、HOME・project・managed・flag をテンポラリに向ける
        saved = {k: os.environ.get(k) for k in ("HOME", "CLAUDE_CONFIG_DIR")}
        os.environ["HOME"] = str(env.home)
        os.environ.pop("CLAUDE_CONFIG_DIR", None)
        paths = ["--project", str(env.project),
                 "--managed-settings", str(env.project / "no-managed.json"),
                 "--flag-settings", str(env.project / "no-flag.json")]
        runs = {}
        try:
            # 読まないことは、OS への入口が呼ばれないことで見る——出力に出さずに読む変異は出力では見えない
            for key, argv in (("config_off", ["--push-result", "Push not sent — mobile push is disabled in /config."]),
                              ("empty", ["--push-result", ""]),
                              ("full", [])):
                buf = io.StringIO()
                with recording_reads() as reads, contextlib.redirect_stdout(buf):
                    code = mod.main(argv + paths)
                runs[key] = (code, buf.getvalue(), list(reads))
            # 陽性対照のもう半分: 本体の run() から subprocess に届くこと（Linux の全点検はコマンドを走らせない）。
            # 走らせるのは偽の ps——本物のコマンドを起こすと、テストが実環境を読む
            with recording_reads() as reads:
                patched = all(getattr(o, n).__name__ == "recorded" for o, n in READ_ENTRIES)
                ran, _ = mod.run([str(env.bin / "ps"), "-p", "500"])
            runs["cmd"] = (patched and ran, list(reads))
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        after = {p: p.read_bytes() for p in Path(env.home).parent.rglob("*") if p.is_file()}
        code, out, reads = runs["config_off"]
        check("--push-result は判定だけを出して 1 を返す", code == 1 and "設定の層" not in out
              and "[要対処] 通知の試験" in out, bad)
        check("--push-result は設定もファイルもコマンドも読まない", reads == [], bad)
        code, out, reads = runs["empty"]
        check("空の --push-result も判定に回り、全点検に落ちない（2）",
              code == 2 and "[判定できない] 通知の試験" in out and "設定の層" not in out and reads == [], bad)
        # 陽性対照: 同じ記録器が全点検の読みを拾う——拾わなければ上の「読まない」は何も証明しない。
        # 「何か 1 つ拾った」では足りない（コマンドだけ拾って Path の差し替えが死んでいても緑になる）ので、入口の種類ごとに見る
        check("記録器は全点検の Path の読みを拾う（陽性対照）",
              any(r.startswith("Path.") for r in runs["full"][2]) and "設定の層" in runs["full"][1], bad)
        patched, cmd_reads = runs["cmd"]
        check("記録器は全部の入口を差し替え、本体の run() のコマンドを拾う（陽性対照）",
              patched and "subprocess.run" in cmd_reads, bad)
        check("--push-result は何も書かない", before == after, bad)

    # 人が見る: Remote Control は claude rc との違い、モバイルの登録は通知の試験を指す
    with scenario(script) as env:
        env.all_good()
        _, _, out = run(mod, env)
        check("Remote Control の項が claude rc の待ち受けと区別する", "claude rc" in out and "/remote-control" in out, bad)
        check("モバイルの登録の項が --push-result を指す", "--push-result" in out, bad)

    # 守る: 何も書かない
    with scenario(script) as env:
        env.all_good()
        env.local({"permissions": {"defaultMode": "auto"}})
        before = {p: p.read_bytes() for p in Path(env.home).parent.rglob("*") if p.is_file()}
        run(mod, env)
        after = {p: p.read_bytes() for p in Path(env.home).parent.rglob("*") if p.is_file()}
        check("ファイルを書かない・増やさない", before == after, bad)

    return bad


MUTATIONS = {
    "読めなかったものを空として扱う": (
        "    except ValueError as e:\n        return Unreadable(p, str(e))",
        "    except ValueError as e:\n        return {}"),
    "exists() のように読めない親を無いとする": (
        "    except (FileNotFoundError, NotADirectoryError):\n        return None\n"
        "    except (OSError, ValueError) as e:\n",
        "    except (FileNotFoundError, NotADirectoryError, OSError):\n        return None\n"
        "    except ValueError as e:\n"),
    "読めない文字コードで例外を投げる": (
        "    except (OSError, ValueError) as e:\n        # ValueError",
        "    except OSError as e:\n        # ValueError"),
    "層を低い順に見る": (
        "    for name, _path, data in reversed(stack):\n        if only is not None",
        "    for name, _path, data in stack:\n        if only is not None"),
    "自動継続を全層から読む": (
        'effective(stack, "autoContinueAtUsageLimit", SESSION_LAYERS)',
        'effective(stack, "autoContinueAtUsageLimit")'),
    "質問の待ちを全層から読む": (
        'effective(stack, "askUserQuestionTimeout", SESSION_LAYERS)',
        'effective(stack, "askUserQuestionTimeout")'),
    "managed 以外の規則も数える": (
        "    managed_only = managed_rules_only(stack)\n",
        "    managed_only = False\n"),
    "引数なしの規則で覆ったとする": (
        '        call = command + " <引数>"\n',
        "        call = command\n"),
    "ps の失敗で flag の層を積まない": (
        "    elif flag_note:\n",
        "    elif False:\n"),
    ".config.json を見ない": (
        '    candidate = config_dir(home, env) / ".config.json"\n',
        "    return legacy\n"),
    "versions の本体を claude と見ない": (
        'return p.name == "claude" or (',
        'return p.name == "claude" and ('),
    "spare を見ない": (
        '            if "--bg-spare" in argv:\n',
        "            if False:\n"),
    "-m・-u もスリープ防止と数える": (
        "                and prevents_idle_sleep(argv)):",
        "                and True):"),
    "読めない上の層を飛ばす": (
        "        if isinstance(data, Unreadable):\n            return data, name\n        if isinstance(data, dict) and key in data:",
        "        if isinstance(data, dict) and key in data:"),
    "読めない層があっても allow で良いにする": (
        "        elif broken:\n",
        "        elif False:\n"),
    "ask を読まない": (
        "        elif asked:\n",
        "        elif False:\n"),
    "flag のパスが無ければ未設定とする": (
        'Unreadable(path, "ファイルが無い") if data is None else data',
        "data"),
    "--settings= を拾わない": (
        '                if arg.startswith("--settings="):',
        '                if False:'),
    "最寄りの claude で止まらない": (
        "                    return arg[len(\"--settings=\"):], None\n            return None, None\n",
        "                    return arg[len(\"--settings=\"):], None\n"),
    "managed-settings.d を読まない": (
        "        for dropin in managed_dropins(managed_path):",
        "        for dropin in []:"),
    "disableBypassPermissionsMode を見ない": (
        'bypass_off not in ("disable", True)',
        "True"),
    "CLAUDE_CONFIG_DIR を見ない": (
        '    value = env.get("CLAUDE_CONFIG_DIR")\n',
        "    value = None\n"),
    "project と local の並びを入れ替える": (
        '    stack.append(("project", project / ".claude" / "settings.json"))\n'
        '    stack.append(("local", project / ".claude" / "settings.local.json"))\n',
        '    stack.append(("local", project / ".claude" / "settings.local.json"))\n'
        '    stack.append(("project", project / ".claude" / "settings.json"))\n'),
    "managed を flag より下に置く": (
        "    if flag_path:\n",
        "    if managed_path:\n"
        "        stack.append((\"managed\", Path(managed_path), read_json(managed_path)))\n"
        "        managed_path = None\n    if flag_path:\n"),
    "通知を truthy で見る": (
        "data.get(key) is True",
        "data.get(key)"),
    "まとめた caffeinate -it を数えない": (
        'r"-[dimsutw]*[tw][dimsutw]*\\d*"',
        'r"-[tw]"'),
    "allow を deny より先に見る": (
        "        if denied:\n",
        "        if denied and not allowed:\n"),
    "caffeinate -t を数える": (
        'Path(argv[0]).name == "caffeinate" and not timed_caffeinate(argv)',
        'Path(argv[0]).name == "caffeinate"'),
    "人が見るを出さない": (
        "    items += human_items(stack)\n",
        "\n"),
    "判定できないを 0 にする": (
        "    if UNKNOWN in statuses or RETRY in statuses:\n        return 2",
        "    if UNKNOWN in statuses or RETRY in statuses:\n        return 0"),
    "設定を書く": (
        "    stack = layers(project, flag_path, managed_path, home, env, flag_note)\n",
        "    stack = layers(project, flag_path, managed_path, home, env, flag_note)\n"
        "    (home / '.claude.json').write_text('{}')\n"),
    "使用中で省かれたのを要対処にする": (
        '    ("this terminal is active", RETRY,',
        '    ("this terminal is active", ACTION,'),
    "使用中を判定できないにする": (
        '    ("this terminal is active", RETRY,',
        '    ("this terminal is active", UNKNOWN,'),
    "知らない返り値を送り直させる": (
        '"送り直さない——PushNotification の返り値を言い換えずにそのまま渡し直す。それでも知らないなら版が違う"',
        '"失敗ではない。遅らせて、端末を前面から外し（別のアプリを前面に）、端末にも iPhone にも触らずに送り直す"'),
    "使用中の対処が画面ロックだけ": (
        '"失敗ではない。遅らせて、端末を前面から外し（別のアプリを前面に）、端末にも iPhone にも触らずに送り直す"),',
        '"失敗ではない。遅らせて、画面をロックし、端末からも iPhone からも離れてから送り直す"),'),
    "--push-result のあとも設定を読んで点検を出す": (
        "        return report_push(check_push_result(args.push_result))\n",
        "        push_code = report_push(check_push_result(args.push_result))\n"
        "        report(*gather(args.project or default_project(), tuple(DEFAULT_COMMANDS), args.flag_settings,\n"
        "                       args.managed_settings, Path.home(), sys.platform))\n"
        "        return push_code\n"),
    "空の --push-result を見ない": (
        "    if args.push_result is not None:\n",
        "    if args.push_result:\n"),
    "--push-result で通知の設定を読むが出さない": (
        "        return report_push(check_push_result(args.push_result))\n",
        "        check_notifications(Path.home())\n"
        "        return report_push(check_push_result(args.push_result))\n"),
    "--push-result でスリープを見るが出さない": (
        "        return report_push(check_push_result(args.push_result))\n",
        "        check_sleep('darwin')\n"  # sys.platform を渡すと Linux の CI では何も読まずに返り、素通りする
        "        return report_push(check_push_result(args.push_result))\n"),
    "使用中の 60 秒を 30 秒にする": (
        "分からなければ最後の操作から 60 秒以内）\",",
        "分からなければ最後の操作から 30 秒以内）\","),
    "使用中の 60 秒を 160 秒にする": (  # 「60 秒以内」の部分一致では素通りする
        "分からなければ最後の操作から 60 秒以内）\",",
        "分からなければ最後の操作から 160 秒以内）\","),
    "--push-result のあと設定を読むが出さない": (
        "        return report_push(check_push_result(args.push_result))\n",
        "        gather(args.project or default_project(), tuple(DEFAULT_COMMANDS), args.flag_settings,\n"
        "               args.managed_settings, Path.home(), sys.platform)\n"
        "        return report_push(check_push_result(args.push_result))\n"),
    "/config のオフの対処を Remote Control にする": (
        '"「Push when Claude decides」（agentPushNotifEnabled）がオフ", "/config でオン"),',
        '"「Push when Claude decides」（agentPushNotifEnabled）がオフ", "作業中のセッションで /remote-control"),'),
    "Remote Control が切れた原因を /config にする": (
        '"いまのセッションが Remote Control につながっていない", "作業中のセッションで /remote-control"),',
        '"「Push when Claude decides」（agentPushNotifEnabled）がオフ", "作業中のセッションで /remote-control"),'),
    "知らない返り値を原因に出さない": (
        'f"知らない返り値: {text!r}"',
        '"知らない返り値"'),
    "送信の要求を良いにする": (
        '    ("Mobile push requested", HUMAN,',
        '    ("Mobile push requested", GOOD,'),
    "Remote Control が切れていても見ない": (
        '    ("Remote Control inactive", ACTION,',
        '    ("Remote Control inactive", HUMAN,'),
    "/config のオフを見ない": (
        '    ("mobile push is disabled in /config", ACTION,',
        '    ("mobile push is disabled in /config", GOOD,'),
    "知らない返り値を良いにする": (
        '    return [(UNKNOWN, "通知の試験", f"知らない返り値',
        '    return [(GOOD, "通知の試験", f"知らない返り値'),
    "--push-result を見ない": (
        "    if args.push_result is not None:\n",
        "    if False:\n"),
    "人が見るの Remote Control が claude rc を言わない": (
        '         "作業中のセッションで /remote-control——claude rc の待ち受けは別のセッションを起こす。"\n',
        '         "作業中のセッションで /remote-control。"\n'),
    "文字列の true を受ける": (
        "    if value is True:",
        "    if value:"),
}


def main() -> int:
    print("陽性対照（元の本体）")
    bad = suite(SCRIPT)
    for name in bad:
        print(f"  FAIL {name}")
        failures.append(name)
    if not bad:
        print("  ok   全シナリオ")

    print("変異テスト")
    src = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        for name, (old, new) in MUTATIONS.items():
            if src.count(old) != 1:
                print(f"  FAIL 変異「{name}」の置換元が本体に 1 つだけ無い")
                failures.append(name)
                continue
            mutant = Path(tmp) / f"m{len(name)}_{abs(hash(name))}.py"
            mutant.write_text(src.replace(old, new), encoding="utf-8")
            killed = bool(suite(mutant))
            print(f"  {'ok  ' if killed else 'FAIL'} 変異「{name}」が{'赤になる' if killed else '緑のまま'}")
            if not killed:
                failures.append(name)

    print()
    print("FAIL" if failures else "OK", f"（失敗 {len(failures)} 件）")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
