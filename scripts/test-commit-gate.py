#!/usr/bin/env python3
"""`commit-gate.py`（#1192）の回帰テスト。変異テストを含む。

**本体は `plugins/dev-loop/skills/dev-loop/scripts/commit-gate.py`**（`test-find-cycle.py` と同じ形）。
一時ディレクトリに本物の git リポジトリを作り、**PreToolUse の stdin を真似た JSON** を本体に渡して当てる。
記録は `DEV_LOOP_GATE_LOG` で一時ディレクトリに向ける。

**守ること**（受入基準の 2・3 と、`git log --grep` で `none` を引けること）:
- off（既定）: 満たさないコミットでも何もしない・記録もしない
- observe: 満たさないコミットを**通し**（終了コード 0）、記録に `would_stop` を残す
- enforce: 満たさないコミットを**止め**（終了コード 2）、満たすコミットは通す
- 逃げ道（`理由を書けば通す`／`なし`）・`none` の理由・手段の語彙・-m／ヒアドキュメント／-F／amend の読み方
- 設定の誤り（コードフェンスの中・2 本・値違い）は off に倒れる
- 判定できない入力（JSON でない・Bash でない・git commit でない・--dry-run）は通す
- `status`・`report` の出力

**守らないこと**: 本物の Claude Code に登録して発火させること（本物の hook の stdin と終了コードの扱いは見ていない）。
**変異テスト**: 本体の 1 か所を壊した写しで、通常のスイートが落ちること（陽性対照: 壊さない写しでは緑）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/dev-loop/skills/dev-loop/scripts/commit-gate.py"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
}


def sh(*cmd: str, cwd: Path, **kw) -> subprocess.CompletedProcess:
    env = {**os.environ, **GIT_ENV, "HOME": str(cwd), "GIT_CONFIG_GLOBAL": "/dev/null"}
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, **kw)


def make_repo(tmp: Path, config: str | None) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    sh("git", "init", "-q", cwd=repo)
    (repo / "a.txt").write_text("a\n")
    sh("git", "add", ".", cwd=repo)
    sh("git", "commit", "-q", "-m", "init\n\nVerified: none (初期化)", cwd=repo)
    if config is not None:
        (repo / ".claude").mkdir()
        (repo / ".claude/dev-loop.md").write_text(config, encoding="utf-8")
    return repo


class Case:
    def __init__(self, script: Path, config: str | None):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.script = script
        self.repo = make_repo(self.tmp, config)
        self.log = self.tmp / "gate.jsonl"

    def hook(self, command: str, tool: str = "Bash", raw: str | None = None):
        payload = raw if raw is not None else json.dumps(
            {"tool_name": tool, "tool_input": {"command": command}, "cwd": str(self.repo)})
        env = {**os.environ, "DEV_LOOP_GATE_LOG": str(self.log), "HOME": str(self.tmp), "GIT_CONFIG_GLOBAL": "/dev/null"}
        return subprocess.run([sys.executable, str(self.script)], input=payload, cwd=self.repo,
                              env=env, capture_output=True, text=True)

    def entries(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(x) for x in self.log.read_text(encoding="utf-8").splitlines()]

    def close(self):
        self._tmp.cleanup()


def cfg(mode: str | None = None, escape: str | None = None) -> str:
    lines = []
    if mode:
        lines.append(f"検証の関門: {mode}")
    if escape:
        lines.append(f"検証の関門の逃げ道: {escape}")
    return "\n".join(lines) + "\n"


def suite(script: Path) -> list[str]:
    """通常のスイート。失敗の説明の一覧を返す（空なら緑）。"""
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name} {detail}".strip())

    plain = 'git commit -m "feat: x"'
    good = 'git commit -m "feat: x\n\nVerified: tests,gates"'
    heredoc = "git commit -m \"$(cat <<'EOF'\nfeat: x\n\nVerified: verify,code-review\nCo-Authored-By: A <a@b>\nEOF\n)\""

    # off（設定なし・既定）
    c = Case(script, None)
    r = c.hook(plain)
    check("off: 設定なしで通す", r.returncode == 0)
    check("off: 記録しない", c.entries() == [])
    c.close()
    c = Case(script, cfg("off"))
    r = c.hook(plain)
    check("off 明示: 通して記録しない", r.returncode == 0 and c.entries() == [])
    c.close()

    # observe（受入基準 2）
    c = Case(script, cfg("observe"))
    r = c.hook(plain)
    e = c.entries()
    check("observe: 満たさないコミットは通す", r.returncode == 0, f"rc={r.returncode}")
    check("observe: would_stop が残る", len(e) == 1 and e[0]["action"] == "would_stop" and e[0]["reason"] == "missing", str(e))
    r = c.hook(good)
    e = c.entries()
    check("observe: 満たすコミットは pass を残す", r.returncode == 0 and e[-1]["action"] == "pass" and e[-1]["reason"] is None, str(e))
    c.close()

    # enforce（受入基準 3）
    c = Case(script, cfg("enforce"))
    r = c.hook(plain)
    check("enforce: 満たさないコミットを止める", r.returncode == 2, f"rc={r.returncode}")
    check("enforce: 直し方を stderr に出す", "Verified:" in r.stderr, r.stderr)
    check("enforce: stopped を残す", c.entries() and c.entries()[-1]["action"] == "stopped", str(c.entries()))
    check("enforce: 満たすコミットは通す", c.hook(good).returncode == 0)
    check("enforce: ヒアドキュメントの形も通す", c.hook(heredoc).returncode == 0)
    check("enforce: 手段が語彙の外は止める", c.hook('git commit -m "x\n\nVerified: magic"').returncode == 2)
    check("enforce: 手段の一部が語彙の外でも止める", c.hook('git commit -m "x\n\nVerified: tests,magic"').returncode == 2)
    check("enforce: none に理由が無いと止める", c.hook('git commit -m "x\n\nVerified: none"').returncode == 2)
    check("enforce: none () の理由が空でも止める", c.hook('git commit -m "x\n\nVerified: none ()"').returncode == 2)
    check("enforce: 既定の逃げ道は none (理由) を通す", c.hook('git commit -m "x\n\nVerified: none (計画ファイルのみ)"').returncode == 0)
    check("enforce: -m の中の末尾の引用符を値に含めない", c.hook('git commit -m "x\n\nVerified: tests"').returncode == 0)
    check("enforce: 全角括弧の理由も通す", c.hook('git commit -m "x\n\nVerified: none（計画のみ）"').returncode == 0)
    c.close()

    # 逃げ道なし
    c = Case(script, cfg("enforce", "なし"))
    check("逃げ道なし: none (理由) も止める", c.hook('git commit -m "x\n\nVerified: none (理由)"').returncode == 2)
    check("逃げ道なし: 手段があれば通す", c.hook(good).returncode == 0)
    check("逃げ道なし: 理由は none_not_allowed",
          any(x["reason"] == "none_not_allowed" for x in c.entries()), str(c.entries()))
    c.close()

    # メッセージの読み方（-F・amend）
    c = Case(script, cfg("enforce"))
    (c.repo / "msg.txt").write_text("x\n\nVerified: gates\n")
    check("-F のファイルを読む", c.hook("git commit -F msg.txt").returncode == 0)
    (c.repo / "bad.txt").write_text("x\n")
    check("-F のファイルに印が無ければ止める", c.hook("git commit -F bad.txt").returncode == 2)
    check("--amend --no-edit は直前のメッセージを読む（印あり）", c.hook("git commit --amend --no-edit").returncode == 0)
    sh("git", "commit", "-q", "--allow-empty", "-m", "bare", cwd=c.repo)
    check("--amend --no-edit は直前のメッセージを読む（印なし）", c.hook("git commit --amend --no-edit").returncode == 2)
    check("メッセージを渡さない commit（エディタ）は止める", c.hook("git commit").returncode == 2)
    c.close()

    # 通す（見ないもの・判定できないもの）
    c = Case(script, cfg("enforce"))
    check("git commit でないコマンドは通して記録しない", c.hook("git status").returncode == 0 and c.entries() == [])
    check("--dry-run は通す", c.hook("git commit --dry-run -m x").returncode == 0)
    check("Bash 以外のツールは通す", c.hook(plain, tool="Edit").returncode == 0)
    check("JSON でない stdin は通す", c.hook("", raw="not json").returncode == 0)
    check("-C 付きの git commit も見る", c.hook('git -C . commit -m "x"').returncode == 2)
    check("連結コマンドの中の git commit も見る", c.hook('git add -A && git commit -m "x"').returncode == 2)
    c.close()

    # 設定の誤りは off
    for name, text in (
        ("コードフェンスの中", "```\n検証の関門: enforce\n```\n"),
        ("HTML コメントの中", "<!--\n検証の関門: enforce\n-->\n"),
        ("2 本", "検証の関門: enforce\n検証の関門: observe\n"),
        ("値違い", "検証の関門: strict\n"),
    ):
        c = Case(script, text)
        r = c.hook(plain)
        check(f"設定の誤り（{name}）は off", r.returncode == 0 and c.entries() == [], f"rc={r.returncode}")
        c.close()
    c = Case(script, "検証の関門: strict\n")
    s = sh(sys.executable, str(script), "status", "--project", str(c.repo), cwd=c.repo)
    check("status が誤りを名指しする", "設定の誤り" in s.stdout and "off" in s.stdout, s.stdout)
    c.close()
    c = Case(script, cfg("observe", "なし"))
    s = sh(sys.executable, str(script), "status", "--project", str(c.repo), cwd=c.repo)
    check("status が効いている値を出す", "observe" in s.stdout and "なし" in s.stdout, s.stdout)
    c.close()

    # 設定はメインの作業ツリーから読む（worktree の写しは読まない）
    c = Case(script, cfg("enforce"))
    sh("git", "add", ".", cwd=c.repo)
    sh("git", "commit", "-q", "-m", "cfg\n\nVerified: none (設定)", cwd=c.repo)
    wt = c.tmp / "wt"
    sh("git", "worktree", "add", "-q", "-b", "w", str(wt), cwd=c.repo)
    (wt / ".claude/dev-loop.md").write_text(cfg("off"), encoding="utf-8")  # 周のブランチが自分で off にしても効かない
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": plain}, "cwd": str(wt)})
    env = {**os.environ, "DEV_LOOP_GATE_LOG": str(c.log), "HOME": str(c.tmp), "GIT_CONFIG_GLOBAL": "/dev/null"}
    r = subprocess.run([sys.executable, str(script)], input=payload, cwd=wt, env=env, capture_output=True, text=True)
    check("worktree から呼んでもメインの設定（enforce）が効く", r.returncode == 2, f"rc={r.returncode}")
    c.close()

    # 記録に載せるのは先頭だけ
    c = Case(script, cfg("observe"))
    c.hook("git commit -m \"" + "x" * 500 + "\"")
    check("記録は先頭 120 文字だけ", len(c.entries()[0]["command_head"]) == 120, str(c.entries()))
    c.close()

    # git log --grep で none を引ける（受入基準 1 の引く側）
    c = Case(script, None)
    sh("git", "commit", "-q", "--allow-empty", "-m", "a\n\nVerified: tests,gates", cwd=c.repo)
    sh("git", "commit", "-q", "--allow-empty", "-m", "b\n\nVerified: none (計画ファイルのみ)", cwd=c.repo)
    out = sh("git", "log", "--format=%s", "--grep=^Verified: none", cwd=c.repo).stdout.split()
    check("git log --grep で none のコミットを引ける", sorted(out) == ["b", "init"], str(out))
    c.close()

    # report
    c = Case(script, cfg("observe"))
    r0 = sh(sys.executable, str(script), "report", "--log", str(c.log), cwd=c.repo)
    check("report: 記録が無ければ 3", r0.returncode == 3, r0.stdout)
    c.hook(plain)
    c.hook(good)
    r1 = sh(sys.executable, str(script), "report", "--log", str(c.log), cwd=c.repo)
    check("report: 数と would_stop の 1 件ずつを出す",
          r1.returncode == 0 and "would_stop 1" in r1.stdout and "pass 1" in r1.stdout
          and "[would_stop]" in r1.stdout and "missing" in r1.stdout, r1.stdout)
    c.close()
    return fails


# 本体の 1 か所を壊す。通常のスイートが落ちなければ、その変異は素通り。
MUTATIONS = [
    ("enforce が止めない", "        return 2\n    return 0\n\n\ndef status", "        return 0\n    return 0\n\n\ndef status"),
    ("observe が記録しない", '("would_stop" if mode == "observe" else "stopped")', '("pass" if mode == "observe" else "stopped")'),
    ("印が無くても満たす", '    if not found:\n        return "missing"', "    if not found:\n        return None"),
    ("none の理由を見ない", '            return "none_without_reason"', "            pass"),
    ("逃げ道なしが効かない", 'return "none_not_allowed" if escape == "なし" else None', "return None"),
    ("語彙の外を通す", '    return "malformed"', "    return None"),
    ("off でも判定する", '    if mode == "off":\n        return 0', "    if False:\n        return 0"),
    ("コードフェンスを設定に読む", "values = pat.findall(strip_noise(text))", "values = pat.findall(text)"),
    ("--dry-run を見る", ' or "--dry-run" in command', ""),
    ("amend の直前メッセージを読まない", 'and (not has_msg or "--no-edit" in command)', "and False"),
    ("2 本の行の最初の値を採る", 'return default, f"`{key}:` の行が', 'return values[0], f"`{key}:` の行が'),
    ("値違いをそのまま採る", 'return default, f"`{key}:` の値', 'return values[0], f"`{key}:` の値'),
    ("worktree の写しを読む", 'path = Path(common).parent / ".claude" / "dev-loop.md"', 'path = Path(cwd) / ".claude" / "dev-loop.md"'),
    ("-F を読まない", "        try:\n            text += \"\\n\" + p.read_text(encoding=\"utf-8\")\n        except OSError:\n            pass\n", ""),
    ("記録に全文を書く", "command[:HEAD_LEN]", "command"),
]


def mutant_run(item: tuple[str, str, str]) -> tuple[str, str]:
    name, old, new = item
    src = SCRIPT.read_text(encoding="utf-8")
    if src.count(old) != 1:
        return name, f"変異の対象が本体に {src.count(old)} 回ある（1 回でなければ変異が届かない）"
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "commit-gate.py"
        p.write_text(src.replace(old, new), encoding="utf-8")
        fails = suite(p)
    return name, "" if fails else "SURVIVED"


def main() -> int:
    base = suite(SCRIPT)
    if base:
        print("FAIL: 通常のスイートが落ちた")
        for f in base:
            print(f"  - {f}")
        return 1
    print("OK: 通常のスイート緑（陽性対照）")
    bad = []
    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 1)) as ex:
        for name, res in ex.map(mutant_run, MUTATIONS):
            print(("  killed  " if not res else f"  {res}  ") + name)
            if res:
                bad.append((name, res))
    if bad:
        print(f"FAIL: 変異 {len(bad)}/{len(MUTATIONS)} が素通り")
        return 1
    print(f"OK: 変異 {len(MUTATIONS)}/{len(MUTATIONS)} を検出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
