#!/usr/bin/env python3
"""`launch-with-long-token.sh`（長期トークンの起動口。#584）の回帰テスト。

    python3 scripts/test-launch-with-long-token.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）——`test-check-unattended-env.py` と同じ形。

**このテストは本物のキーチェーンにも `claude` にも届かない。** `PATH` を偽の `security`・`claude`・`uname` と、
本体が使う道具（`grep`・`sed`・`date`）の symlink だけにする——**`/usr/bin` を入れない**ので、本物の `security` は呼べない
（偽の `security` が呼ばれた記録を陽性対照として見る）。`HOME` もテンポラリにする。トークンは偽の文字列である。

**変異テストを含む。** 本体の冒頭の「守る」の各行に変異を 1 つ以上当て、**壊したのに緑のままなら失格**とする。
**変異の前に、元の本体で全部緑であること（陽性対照）を見る。**
"""
import os
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
    case "$FAKE_SEC" in missing) exit 44 ;; esac
    for a in "$@"; do
        if [ "$a" = "-w" ]; then
            case "$FAKE_SEC" in empty) printf '\n' ;; *) printf '%s\n' "$FAKE_TOKEN" ;; esac
            exit 0
        fi
    done
    printf 'keychain: "/x/login.keychain-db"\nattributes:\n    "icmt"<blob>="launch-with-long-token.sh --store-token 2026-10-29T00:00:00Z"\n    "svce"<blob>="claude-long-token"\n'
    exit 0 ;;
add-generic-password)
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
        for tool in ("grep", "sed", "date"):
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
        proc = subprocess.run(["/bin/bash", str(script), *args], env=env, capture_output=True, text=True,
                              timeout=30)
        return proc.returncode, proc.stdout + proc.stderr

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

    # 止まる: 項目が無い・値が空・security が無い・macOS でない
    for name, kw, extra in (("項目が無い", {}, {"FAKE_SEC": "missing"}), ("値が空", {}, {"FAKE_SEC": "empty"}),
                            ("security が無い", {"security": False}, {}), ("macOS でない", {"uname": "Linux"}, {})):
        tmp, e = scenario(**kw)
        with tmp:
            code, out = e.run(script, **extra)
            check(f"止まる（{name}）: 2", code == 2)
            check(f"止まる（{name}）: claude を起動しない", e.log("claude.log") == "")
            check(f"止まる（{name}）: 理由と手順を出す", "claude を起動しない" in out and "cruise-long-lived-token" in out)
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
    return bad


MUTATIONS = {
    "macOS でなくても読む": ('if [ "$(uname -s)" != "Darwin" ]; then', 'if false; then'),
    "先に使われる認証を見ない": ("for name in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY; do", "for name in; do"),
    "API キーを見ない": ("for name in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY; do", "for name in ANTHROPIC_AUTH_TOKEN; do"),
    "項目が無くても起動する": ('if ! token=$(security find-generic-password -s "$SERVICE" -w 2>/dev/null); then',
                     'if ! token=$(security find-generic-password -s "$SERVICE" -w 2>/dev/null) && false; then'),
    "値が空でも起動する": ('if [ -z "$token" ]; then', "if false; then"),
    "security が無くても進む": ("if ! command -v security >/dev/null 2>&1; then", "if false; then"),
    "引数を割る": ('exec claude "$@"', "exec claude $*"),
    "トークンを出す": ('export CLAUDE_CODE_OAUTH_TOKEN="$token"', 'echo "$token" >&2\nexport CLAUDE_CODE_OAUTH_TOKEN="$token"'),
    "環境の古い値を残す": ('export CLAUDE_CODE_OAUTH_TOKEN="$token"',
                    'export CLAUDE_CODE_OAUTH_TOKEN="${CLAUDE_CODE_OAUTH_TOKEN:-$token}"'),
    "セッションの中でも入れる": ('if [ "$CLAUDECODE" = "1" ]; then', "if false; then"),
    "-w を最後に置かない": ('-j "launch-with-long-token.sh --store-token $(date -u +%Y-%m-%dT%H:%M:%SZ)" -w',
                      '-w -j "launch-with-long-token.sh --store-token $(date -u +%Y-%m-%dT%H:%M:%SZ)"'),
    "-U を付けない": ("exec security add-generic-password -U -a", "exec security add-generic-password -a"),
    "--status で値を読む": ('if ! attrs=$(security find-generic-password -s "$SERVICE" 2>/dev/null); then',
                       'if ! attrs=$(security find-generic-password -s "$SERVICE" -w 2>/dev/null); then'),
    "--account を無視する": ('    SERVICE="claude-long-token-$2"\n', '    SERVICE="claude-long-token"\n'),
    "--account の名前を検めない": ("if ! printf '%s' \"$2\" | grep -Eq", "if false && printf '%s' \"$2\" | grep -Eq"),
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
