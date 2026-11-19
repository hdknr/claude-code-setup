#!/usr/bin/env python3
"""`launch-with-long-token.sh`（長期トークンの起動口。#584）の回帰テスト。

    python3 scripts/test-launch-with-long-token.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）——`test-check-unattended-env.py` と同じ形。

**このテストは本物のキーチェーンにも `claude` にも届かない。** `PATH` を偽の `security`・`claude`・`uname` と、
本体が使う道具（`grep`・`sed`・`date`）の symlink だけにする——**`/usr/bin` を入れない**ので、本物の `security` は呼べない
（偽の `security` が呼ばれた記録を陽性対照として見る）。`HOME` もテンポラリにする。トークンは偽の文字列である。

**標準入力が端末かどうかで分岐する部分（起動のときの登録。#1287）は、疑似端末（`pty`）を標準入力に渡して当てる**——
ほかのシナリオは標準入力を `/dev/null` にする（テストを端末から走らせても、登録に進む分岐に入らないように）。
**置いた起動口（`--install-launcher`）は、偽のプラグインのキャッシュ（版のディレクトリを複数並べる）を `HOME` の下に作って走らせる**——
本物の `~/.claude` は読まない。**子プロセスの cwd は一時ディレクトリ**（変異した本体が相対パスの置き場所を作っても、リポジトリを汚さない）。

**変異テストを含む。** 本体の冒頭の「守る」の各行に変異を 1 つ以上当て、**壊したのに緑のままなら失格**とする。
**変異の前に、元の本体で全部緑であること（陽性対照）を見る。**
"""
import os
import pty
import shutil
import subprocess
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "launch-with-long-token.sh"
TOKEN = "fake-long-token-584-not-real"

FAKE_SECURITY = r"""#!/bin/sh
printf '%s\n' "$*" >> "$FAKE_DIR/security.log"
case "$1" in
find-generic-password)
    if [ -f "$FAKE_DIR/stored" ] && [ "$FAKE_SEC" = missing ]; then FAKE_SEC=ok; fi
    case "$FAKE_SEC" in missing) exit 44 ;; locked) exit 36 ;; esac
    for a in "$@"; do
        if [ "$a" = "-w" ]; then
            case "$FAKE_SEC" in empty) printf '\n' ;; *) printf '%s\n' "$FAKE_TOKEN" ;; esac
            exit 0
        fi
    done
    printf 'keychain: "/x/login.keychain-db"\nattributes:\n    "icmt"<blob>="launch-with-long-token.sh --store-token 2026-10-29T00:00:00Z"\n    "svce"<blob>="claude-long-token"\n'
    exit 0 ;;
add-generic-password)
    if [ "${FAKE_ADD_RC:-0}" -eq 0 ]; then : > "$FAKE_DIR/stored"; fi
    exit "${FAKE_ADD_RC:-0}" ;;
esac
exit 1
"""

FAKE_CLAUDE = r"""#!/bin/sh
if [ "$CLAUDE_CODE_OAUTH_TOKEN" = "$FAKE_TOKEN" ]; then printf 'token=match\n' > "$FAKE_DIR/claude.log"
else printf 'token=mismatch\n' > "$FAKE_DIR/claude.log"; fi
for a in "$@"; do printf 'arg=[%s]\n' "$a" >> "$FAKE_DIR/claude.log"; done
exit 7
"""


class Env:
    def __init__(self, base: Path, uname="Darwin", security=True):
        self.base = base
        self.bin = base / "bin"
        self.bin.mkdir()
        home = base / "home"
        home.mkdir()
        assert home.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
        for tool in ("grep", "sed", "date", "bash", "ls", "sort", "tail", "mkdir", "chmod", "cat"):
            real = shutil.which(tool, path="/usr/bin:/bin")
            (self.bin / tool).symlink_to(real)
        self.fake("uname", f"#!/bin/sh\nprintf '%s\\n' {uname}\n")
        if security:
            self.fake("security", FAKE_SECURITY)
        self.fake("claude", FAKE_CLAUDE)
        self.env = {"PATH": str(self.bin), "HOME": str(home), "USER": "tester",
                    "FAKE_DIR": str(base), "FAKE_TOKEN": TOKEN, "FAKE_SEC": "ok"}

    def fake(self, name, body):
        p = self.bin / name
        p.write_text(body, encoding="utf-8")
        p.chmod(0o755)

    def run(self, script, *args, **extra):
        env = {**self.env, **extra}
        # 標準入力は端末にしない（端末から走らせても「対話の端末」の分岐に入らない）
        proc = subprocess.run(["/bin/bash", str(script), *args], env=env, capture_output=True, text=True,
                              timeout=30, stdin=subprocess.DEVNULL, cwd=self.base)
        return proc.returncode, proc.stdout + proc.stderr

    def run_tty(self, script, *args, **extra):
        """標準入力を疑似端末にして走らせる（`[ -t 0 ]` が真になる）。"""
        env = {**self.env, **extra}
        master, slave = pty.openpty()
        try:
            proc = subprocess.Popen(["/bin/bash", str(script), *args], env=env, stdin=slave,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.base)
        finally:
            os.close(slave)
        try:
            out, _ = proc.communicate(timeout=30)
        finally:
            os.close(master)
        return proc.returncode, out

    def run_exec(self, program, *args, **extra):
        """置いた起動口のように、実行ファイルそのものを走らせる（実行ビットが要る）。"""
        env = {**self.env, **extra}
        try:
            proc = subprocess.run([str(program), *args], env=env, capture_output=True, text=True, timeout=30,
                                  stdin=subprocess.DEVNULL, cwd=self.base)
        except PermissionError:
            return 126, "実行できない（実行ビットが無い）"
        return proc.returncode, proc.stdout + proc.stderr

    def plugin(self, version):
        """偽のプラグインのキャッシュに、版ごとの起動口（呼ばれた版と引数を記録する）を置く。"""
        d = (self.base / "home" / ".claude" / "plugins" / "cache" / "claude-code-setup" / "dev-loop" / version
             / "skills" / "dev-loop" / "scripts")
        d.mkdir(parents=True, exist_ok=True)
        (d / "launch-with-long-token.sh").write_text(
            "#!/bin/sh\nprintf 'ver=%s\\n' \"" + version + "\" > \"$FAKE_DIR/launcher.log\"\n"
            "for a in \"$@\"; do printf 'arg=[%s]\\n' \"$a\" >> \"$FAKE_DIR/launcher.log\"; done\nexit 9\n",
            encoding="utf-8")

    def log(self, name):
        p = self.base / name
        return p.read_text(encoding="utf-8") if p.exists() else ""


def suite(script: Path) -> list[str]:
    bad: list[str] = []

    def check(name, cond):
        if not cond:
            bad.append(name)

    def scenario(**kw):
        tmp = tempfile.TemporaryDirectory()
        return tmp, Env(Path(tmp.name), **kw)

    # 起動する: トークンを環境変数で渡し、引数をそのまま渡し、終了コードは claude のもの。値は出さない
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, "a b", "--x", CLAUDE_CODE_OAUTH_TOKEN="old-token")
        claude = e.log("claude.log")
        check("陽性対照: 偽の security が呼ばれた", "find-generic-password" in e.log("security.log"))
        check("起動: claude の終了コードを返す", code == 7)
        check("起動: キーチェーンの値で上書きして渡す", "token=match" in claude)
        check("起動: 空白を含む引数を割らない", "arg=[a b]" in claude and "arg=[--x]" in claude)
        check("起動: トークンを出力に出さない", TOKEN not in out)
        check("起動: トークンを引数に載せない", TOKEN not in e.log("security.log") and TOKEN not in claude)
        code, out = e.run(script, SHELLOPTS="xtrace")
        check("起動: 受け継いだ xtrace でもトークンを出さない", code == 7 and TOKEN not in out)

    # 起動のときの登録（#1287）: 項目が無く・標準入力が端末で・Claude Code のセッションの外のときだけ、登録に進んでから起動する
    tmp, e = scenario()
    with tmp:
        code, out = e.run_tty(script, "a b", FAKE_SEC="missing")
        sec = e.log("security.log")
        add = [ln for ln in sec.splitlines() if ln.startswith("add-generic-password")]
        check("登録して起動: 登録に進み、そのまま claude を起動する（claude の終了コード）", code == 7 and len(add) == 1
              and "token=match" in e.log("claude.log") and "arg=[a b]" in e.log("claude.log"))
        check("登録して起動: 登録は --store-token と同じ呼び方（-U・-s claude-long-token・最後に -w）",
              bool(add) and " -U " in add[0] and "-s claude-long-token " in add[0] and add[0].endswith(" -w"))
        check("登録して起動: 登録の後で値を読み直して渡す", sec.rstrip().splitlines()[-1].startswith("find-generic-password")
              and "登録してから起動する" in out)
        check("登録して起動: claude setup-token は別のタブで走らせると案内する", "claude setup-token" in out and "別のタブ" in out)
        check("登録して起動: トークンを出力・引数・記録に出さない",
              TOKEN not in out and TOKEN not in sec and TOKEN not in e.log("claude.log").replace("token=match", ""))
        n = len(sec.splitlines())
        code, out = e.run_tty(script, "x", FAKE_SEC="ok")
        check("登録済み: 登録に進まず入力なしで起動する", code == 7 and "登録してから起動する" not in out
              and "add-generic-password" not in "\n".join(e.log("security.log").splitlines()[n:]))
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, FAKE_SEC="missing")
        check("非対話（標準入力が端末でない）: 項目が無ければ今までどおり 2 で止まり、登録に進まない",
              code == 2 and "add-generic-password" not in e.log("security.log") and e.log("claude.log") == "")
        code, out = e.run_tty(script, FAKE_SEC="missing", CLAUDECODE="1")
        check("Claude Code のセッションの中: 項目が無ければ 2 で止まり、登録に進まない",
              code == 2 and "add-generic-password" not in e.log("security.log") and e.log("claude.log") == "")
        code, out = e.run_tty(script, FAKE_SEC="locked")
        check("44 以外（ロック 36）の読めない理由: 端末でも登録に進まず、「読めなかった」と言って止まる",
              code == 2 and "add-generic-password" not in e.log("security.log") and "読めなかった" in out
              and e.log("claude.log") == "")
        code, out = e.run_tty(script, FAKE_SEC="missing", ANTHROPIC_API_KEY="fake-key")
        check("先に使われる認証が環境にあれば、登録に進む前に 3 で止まる",
              code == 3 and "add-generic-password" not in e.log("security.log"))
        code, out = e.run_tty(script, FAKE_SEC="missing", FAKE_ADD_RC="5")
        check("登録が失敗したら起動せずに 2 で止まり、終了コードを言う",
              code == 2 and e.log("claude.log") == "" and "入れられなかった" in out and "5" in out)
        before = len(e.log("security.log").splitlines())
        code, out = e.run_tty(script, "--account", "work", "x", FAKE_SEC="missing")
        add = [ln for ln in e.log("security.log").splitlines()[before:] if ln.startswith("add-generic-password")]
        check("--account: 登録も claude-long-token-work に入れて起動する", code == 7 and len(add) == 1
              and "-s claude-long-token-work " in add[-1] and "arg=[x]" in e.log("claude.log"))
    tmp, e = scenario()
    with tmp:
        code, out = e.run_tty(script, "--status", FAKE_SEC="missing")
        check("--status: 端末でも登録に進まない", code == 2 and "add-generic-password" not in e.log("security.log"))

    # --install-launcher（#1287）: 版を含まない起動口。呼ぶたびに最新の版を探す
    tmp, e = scenario()
    with tmp:
        for v in ("2.9.0", "2.12.0", "2.10.1"):
            e.plugin(v)
        target = e.base / "home" / ".local" / "bin" / "dev-loop-cruise"
        code, out = e.run(script, "--install-launcher")
        check("--install-launcher: ~/.local/bin/dev-loop-cruise を実行可能で置く", code == 0 and target.is_file()
              and os.access(target, os.X_OK) and str(target) in out)
        check("--install-launcher: 置く場所が PATH に無ければそう言う", "PATH" in out)
        check("--install-launcher: キーチェーンに触れない・トークンを書かない",
              e.log("security.log") == "" and TOKEN not in target.read_text(encoding="utf-8"))
        check("--install-launcher: 起動口に版を埋めない", all(v not in target.read_text(encoding="utf-8")
                                                          for v in ("2.9.0", "2.12.0", "2.10.1")))
        code, out = e.run_exec(target, "1290", "--absent")
        log = e.log("launcher.log")
        check("起動口: 最新の版（2.12.0。文字列順なら 2.9.0）の起動口を、cruise の 1 本の引数で呼ぶ",
              code == 9 and "ver=2.12.0" in log and log.count("arg=[") == 1 and "arg=[/dev-loop:cruise 1290 --absent]" in log)
        code, out = e.run_exec(target, "--account", "work", "1290")
        log = e.log("launcher.log")
        check("起動口: --account は最初に置いて起動口へ渡す（cruise の引数には入れない）",
              "arg=[--account]" in log and "arg=[work]" in log and "arg=[/dev-loop:cruise 1290]" in log)
        for flag in ("--store-token", "--status"):
            code, out = e.run_exec(target, flag)
            check(f"起動口: {flag} は cruise の引数にせず起動口へ渡す", "arg=[" + flag + "]" in e.log("launcher.log")
                  and "dev-loop:cruise" not in e.log("launcher.log"))
        code, out = e.run_exec(target, "--account", "work", "--store-token")
        check("起動口: --account work --store-token", "arg=[--account]" in e.log("launcher.log")
              and "arg=[--store-token]" in e.log("launcher.log") and "dev-loop:cruise" not in e.log("launcher.log"))
        code, out = e.run_exec(target)
        check("起動口: 引数が無ければ使い方を出して 1", code == 1 and "使い方" in out)
        code, out = e.run_exec(target, "--account")
        check("起動口: --account だけなら 2", code == 2)
        e.plugin("2.13.0")
        e.run_exec(target, "1")
        check("起動口: プラグインを更新しても（新しい版が入っても）置き直さずに新しい版を呼ぶ",
              "ver=2.13.0" in e.log("launcher.log"))
        code, out = e.run_exec(target, "1", CLAUDE_CONFIG_DIR=str(e.base / "nowhere"))
        check("起動口: プラグインが見つからなければ 2", code == 2 and "見つからない" in out)
        code, out = e.run(script, "--install-launcher")
        check("--install-launcher: 置いた起動口は置き直せる", code == 0)
        custom = e.base / "custom"
        code, out = e.run(script, "--install-launcher", str(custom))
        check("--install-launcher <場所>: その場所に置く", code == 0 and (custom / "dev-loop-cruise").is_file())
    tmp, e = scenario()
    with tmp:
        foreign = e.base / "home" / ".local" / "bin" / "dev-loop-cruise"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
        code, out = e.run(script, "--install-launcher")
        check("--install-launcher: 置いた起動口でない同名のファイルは上書きせず 2",
              code == 2 and foreign.read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n")
        code, out = e.run(script, "--account", "work", "--install-launcher")
        check("--install-launcher: --account と一緒には使わない（2）", code == 2 and "--account" in out)
        code, out = e.run(script, "--install-launcher", "a", "b")
        check("--install-launcher: 後ろの引数が 2 つ以上なら 2", code == 2)
        check("--install-launcher: 止まったときも security を呼ばない", e.log("security.log") == "")

    # 止まる: 項目が無い・値が空・security が無い・macOS でない
    for name, kw, extra in (("項目が無い", {}, {"FAKE_SEC": "missing"}), ("値が空", {}, {"FAKE_SEC": "empty"}),
                            ("security が無い", {"security": False}, {}), ("macOS でない", {"uname": "Linux"}, {})):
        tmp, e = scenario(**kw)
        with tmp:
            code, out = e.run(script, **extra)
            check(f"止まる（{name}）: 2", code == 2)
            check(f"止まる（{name}）: claude を起動しない", e.log("claude.log") == "")
            check(f"止まる（{name}）: 理由と手順を出す", "claude を起動しない" in out and "cruise-long-lived-token" in out)
    # 項目が無い（44）とほかの理由（ロック 36 など）を分けて言う
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, FAKE_SEC="missing")
        check("44 は「無い」と入れ方を言う", "が無い" in out and "--store-token" in out)
        code, out = e.run(script, FAKE_SEC="locked")
        check("44 でなければ「読めなかった」と終了コードを言い、「無い」と言わない",
              code == 2 and "読めなかった" in out and "36" in out and "が無い" not in out
              and e.log("claude.log") == "")
        code, out = e.run(script, "--status", FAKE_SEC="locked")
        check("--status: 44 でなければ「読めなかった」", code == 2 and "読めなかった" in out and "が無い" not in out)
    tmp, e = scenario(security=False)
    with tmp:
        code, out = e.run(script)
        check("security が無い: その理由を名指しする", "security コマンドが無い" in out)
    tmp, e = scenario(uname="Linux")
    with tmp:
        e.run(script)
        check("macOS でなければ security を呼ばない", e.log("security.log") == "")

    # 長期トークンより先に使われる認証があれば止まる
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        tmp, e = scenario()
        with tmp:
            code, out = e.run(script, **{name: "fake-key"})
            check(f"{name}: 3 で止まる", code == 3 and e.log("claude.log") == "" and name in out)
            check(f"{name}: 値を出さない", "fake-key" not in out)

    # --store-token: セッションの中では止まる。外では -U・サービス名・最後に -w（値は引数に載せない）
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, "--store-token", CLAUDECODE="1")
        check("--store-token: セッションの中では 2 で止まり security を呼ばない",
              code == 2 and e.log("security.log") == "")
        code, out = e.run(script, "--store-token", FAKE_ADD_RC="5")
        check("--store-token: 端末でなくても（入れる操作なので）security に任せ、claude を起動しない",
              e.log("claude.log") == "")
        line = e.log("security.log").strip().splitlines()[-1] if e.log("security.log").strip() else ""
        check("--store-token: add-generic-password に -U と -s claude-long-token",
              line.startswith("add-generic-password") and " -U " in line and "-s claude-long-token " in line)
        check("--store-token: -w を最後に置く（プロンプトで入れる）", line.endswith(" -w"))
        check("--store-token: security の終了コードを返す", code == 5)
        check("--store-token: claude を起動しない", e.log("claude.log") == "")

    # --status: 値を読まない（-w を付けない）。在れば 0 と入れた記録、無ければ 2
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, "--status")
        check("--status: 在れば 0 と入れた記録", code == 0 and "2026-10-29T00:00:00Z" in out and "発行日・期限ではない" in out)
        check("--status: -w を付けない", " -w" not in e.log("security.log"))
        code, out = e.run(script, "--status", FAKE_SEC="missing")
        check("--status: 無ければ 2", code == 2 and "--store-token" in out)

    # --account: 別のサービス名。名前を検める。案内にも付ける
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, "--account", "work", "x")
        check("--account: claude-long-token-work を読む", "-s claude-long-token-work " in e.log("security.log")
              and code == 7 and "arg=[x]" in e.log("claude.log") and "arg=[--account]" not in e.log("claude.log"))
        code, out = e.run(script, "--account", "work", FAKE_SEC="missing")
        check("--account: 案内に --account を付ける", "--account work --store-token" in out)
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, "--account", "../x")
        check("--account: 不正な名前は 2 で、security を呼ばない", code == 2 and e.log("security.log") == "")
        for args in (("--account", "--store-token"), ("--account", "-x")):
            code, out = e.run(script, *args)
            check(f"--account: - で始まる名前（{args[1]}）は 2 で、security を呼ばない",
                  code == 2 and e.log("security.log") == "" and e.log("claude.log") == "")
        for args in (("--store-token", "--account", "work"), ("--status", "--account", "work"),
                     ("x", "--account", "work"), ("--store-token", "--account=work"), ("x", "--account=work")):
            code, out = e.run(script, *args)
            check(f"--account が最初に無い（{' '.join(args)}）と 2 で止まり、security も claude も呼ばない",
                  code == 2 and e.log("security.log") == "" and e.log("claude.log") == "")
        for args in (("--store-token", "work"), ("--status", "x")):
            code, out = e.run(script, *args)
            check(f"{args[0]} の後ろの引数は 2 で止まり、security を呼ばない",
                  code == 2 and "後ろに引数を置かない" in out and e.log("security.log") == "")
        code, out = e.run(script, "--account", "a\n-x", "--status")
        check("--account: 改行を含む名前は 2 で、security を呼ばない", code == 2 and e.log("security.log") == "")
    tmp, e = scenario()
    with tmp:
        code, out = e.run(script, "--account", "work", "--store-token")
        line = e.log("security.log").strip().splitlines()[-1] if e.log("security.log").strip() else ""
        check("--account work --store-token は claude-long-token-work に入れる",
              line.startswith("add-generic-password") and "-s claude-long-token-work " in line)
        code, out = e.run(script, "--account", "work", "--status")
        line = e.log("security.log").strip().splitlines()[-1]
        check("--account work --status は claude-long-token-work を見る",
              code == 0 and line == "find-generic-password -s claude-long-token-work" and "claude-long-token-work" in out)
    return bad


MUTATIONS = {
    "macOS でなくても読む": ('if [ "$(uname -s)" != "Darwin" ]; then', 'if false; then'),
    "先に使われる認証を見ない": ("for name in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY; do", "for name in; do"),
    "API キーを見ない": ("for name in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY; do", "for name in ANTHROPIC_AUTH_TOKEN; do"),
    "項目が無くても起動する": ('if [ "$rc" -eq 44 ]; then\n    stop 2', 'if false; then\n    stop 2'),
    "値が空でも起動する": ('if [ -z "$token" ]; then', "if false; then"),
    "security が無くても進む": ("if ! command -v security >/dev/null 2>&1; then", "if false; then"),
    "引数を割る": ('exec claude "$@"', "exec claude $*"),
    "トークンを出す": ('export CLAUDE_CODE_OAUTH_TOKEN="$token"', 'echo "$token" >&2\nexport CLAUDE_CODE_OAUTH_TOKEN="$token"'),
    "環境の古い値を残す": ('export CLAUDE_CODE_OAUTH_TOKEN="$token"',
                    'export CLAUDE_CODE_OAUTH_TOKEN="${CLAUDE_CODE_OAUTH_TOKEN:-$token}"'),
    "セッションの中でも入れる": ('if [ "$CLAUDECODE" = "1" ]; then', "if false; then"),
    "-w を最後に置かない": ('-j "launch-with-long-token.sh --store-token $(date -u +%Y-%m-%dT%H:%M:%SZ)" -w',
                      '-w -j "launch-with-long-token.sh --store-token $(date -u +%Y-%m-%dT%H:%M:%SZ)"'),
    "-U を付けない": ("security add-generic-password -U -a", "security add-generic-password -a"),
    "--status で値を読む": ('    attrs=$(security find-generic-password -s "$SERVICE" 2>/dev/null)',
                       '    attrs=$(security find-generic-password -s "$SERVICE" -w 2>/dev/null)'),
    "--account を無視する": ('    SERVICE="claude-long-token-$2"\n', '    SERVICE="claude-long-token"\n'),
    "--account の名前を検めない": ('if ! [[ "$2" =~', 'if false && [[ "$2" =~'),
    "- で始まる名前を通す": ('[[ "$2" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]', '[[ "$2" =~ ^[A-Za-z0-9._-]+$ ]]'),
    "名前を行ごとに照合する": ('if ! [[ "$2" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then',
                       "if ! printf '%s' \"$2\" | grep -Eq '^[A-Za-z0-9][A-Za-z0-9._-]*$'; then"),
    "xtrace を止めない": ("set +x\n", "\n"),
    "--account= の形を見ない": (' || [ "${arg#--account=}" != "$arg" ]', ""),
    "--store-token・--status の後ろの引数を捨てる": ("    if [ $# -gt 1 ]; then\n", "    if false; then\n"),
    "--store-token で --account を無視する": ('security add-generic-password -U -a "$USER" -s "$SERVICE"',
                                        'security add-generic-password -U -a "$USER" -s "claude-long-token"'),
    "--account を先頭でしか見ない": ('    if [ "$arg" = "--account" ] || [ "${arg#--account=}" != "$arg" ]; then', "    if false; then"),
    "読めなかったのを「無い」と言う": ('if [ "$rc" -eq 44 ]; then\n    stop 2', 'if [ "$rc" -ne 0 ]; then\n    stop 2'),
    "--status で読めなかったのを「無い」と言う": ('    if [ "$rc" -eq 44 ]; then\n        echo', '    if [ "$rc" -ne 0 ]; then\n        echo'),
    "44 でない失敗を見ない": ('elif [ "$rc" -ne 0 ]; then\n    # 44', 'elif false; then\n    # 44'),
    "対話の端末でなくても登録に進む": (' && [ -t 0 ] && [ "$CLAUDECODE" != "1" ]; then', ' && [ "$CLAUDECODE" != "1" ]; then'),
    "セッションの中でも登録に進む": (' && [ -t 0 ] && [ "$CLAUDECODE" != "1" ]; then', ' && [ -t 0 ]; then'),
    "44 以外でも登録に進む": ('if [ "$rc" -eq 44 ] && [ -t 0 ]', 'if [ "$rc" -ne 0 ] && [ -t 0 ]'),
    "登録の失敗を言わない": ('if [ "$store_rc" -ne 0 ]; then', "if false; then"),
    "登録の後に読み直さない": ('    read_token\nfi\nif [ "$rc" -eq 44 ]; then', 'fi\nif [ "$rc" -eq 44 ]; then'),
    "登録に進む前に認証の衝突を見ない": ('for name in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY; do\n    if [ -n', 'for name in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY; do\n    if false && [ -n'),
    "起動口が文字列順で版を選ぶ": ("sort -V | tail -1", "sort | tail -1"),
    "起動口を実行可能にしない": ('    chmod +x "$target" || exit 2\n', ""),
    "起動口が cruise の引数を落とす": ('exec bash "$script" "${account[@]}" "/dev-loop:cruise $*"', 'exec bash "$script" "${account[@]}" "/dev-loop:cruise"'),
    "起動口が --account を渡さない": ('account=(--account "$2")', "account=()"),
    "起動口が --store-token を cruise の引数にする": ('--store-token | --status)\n    exec bash "$script"', '--never)\n    exec bash "$script"'),
    "起動口が引数なしで cruise を起こす": ('"")\n    echo "使い方:', '"x")\n    echo "使い方:'),
    "起動口の置き場所を無視する": ('dir="${2:-$HOME/.local/bin}"', 'dir="$HOME/.local/bin"'),
    "同名の別ファイルを上書きする": ('if [ -e "$target" ] && ! grep -qF', "if false && ! grep -qF"),
    "--install-launcher が --account を無視する": ('    if [ -n "$ACCT" ]; then\n        echo "launch-with-long-token: --install-launcher', '    if false; then\n        echo "launch-with-long-token: --install-launcher'),
    "--install-launcher の余分な引数を捨てる": ('    if [ $# -gt 2 ]; then\n        echo "launch-with-long-token: --install-launcher', '    if false; then\n        echo "launch-with-long-token: --install-launcher'),
    "起動口の中の変数を置くときに展開する": ("cat >\"$target\" <<'LAUNCHER_EOF'", 'cat >"$target" <<LAUNCHER_EOF'),
    "案内に --account を付けない": ('    ACCT="--account $2 "\n', '    ACCT=""\n'),
}


def main() -> int:
    failures = []
    print("陽性対照（元の本体）")
    bad = suite(SCRIPT)
    for name in bad:
        print(f"  FAIL {name}")
    failures += bad
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
            mutant = Path(tmp) / "launch-with-long-token.sh"
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
