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
        ("~~~ のフェンスの中", "~~~\n検証の関門: enforce\n~~~\n"),
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
    # 形の読み方（1 パス目の指摘: -m を 2 本・&& で続く・$'…'・git commit でないコマンド）
    c = Case(script, cfg("enforce"))
    check("-m を 2 本渡す形のトレーラーを読む", c.hook('git commit -m "x" -m "Verified: tests"').returncode == 0)
    check("&& で続く形のトレーラーを読む", c.hook('git add -A && git commit -m "x\n\nVerified: tests" && git push').returncode == 0)
    check("後ろにオプションが続く形のトレーラーを読む", c.hook('git commit -m "x\n\nVerified: tests" --no-verify').returncode == 0)
    check("$'…' の形のトレーラーを読む", c.hook("git commit -m $'x\\n\\nVerified: tests,gates'").returncode == 0)
    check("none (理由) の後ろに続く形", c.hook('git commit -m "x\n\nVerified: none (計画のみ)" && git push').returncode == 0)
    check("インデントした印を読む", c.hook('git commit -m "x\n\n  Verified: tests"').returncode == 0)
    for cmd in ("git commit-tree HEAD^{tree} -m x", 'gh pr create --title t --body "run git commit -m x to save"',
                "git commit-graph write", 'git log --grep "git commit"'):
        r = c.hook(cmd)
        check(f"git commit でないコマンドを止めない: {cmd[:30]}", r.returncode == 0, f"rc={r.returncode}")
    check("git commit でないコマンドは記録しない", all(e["reason"] != "missing" or "tree" not in e["command_head"] for e in c.entries()))
    check("絶対パスの git commit も見る", c.hook("/usr/bin/git commit -m x").returncode == 2)
    check("引用符つきの -C の git commit も見る", c.hook('git -C "/tmp/a b" commit -m x').returncode == 2)
    check("別のコマンドの --dry-run に引きずられない", c.hook("git push --dry-run && git commit -m x").returncode == 2)
    check("空白なしの ; の後の git commit も見る", c.hook("echo a;git commit -m x").returncode == 2)
    check("最後の印を採る（先が正しく後が誤り）", c.hook('git commit -m "x\n\nVerified: tests\n\nVerified: magic"').returncode == 2)
    check("最後の印を採る（先が誤りで後が正しい）", c.hook('git commit -m "x\n\nVerified: magic\n\nVerified: tests"').returncode == 0)
    check("--amend -m は直前のメッセージを読まない", c.hook('git commit --amend -m "y"').returncode == 2)
    (c.repo / "bin.txt").write_bytes(b"\xff\xfe")
    r = c.hook("git commit -F bin.txt")
    check("UTF-8 でない -F はトレースバックを出さない", "Traceback" not in r.stderr, r.stderr[-200:])
    head = sh("git", "rev-parse", "HEAD", cwd=c.repo).stdout.strip()
    (c.repo / ".git/MERGE_HEAD").write_text(head + "\n")
    r = c.hook("git commit --no-edit")
    check("マージの締めは見ない", r.returncode == 0, f"rc={r.returncode}")
    check("マージ中の -m 付きの commit も見ない", c.hook('git commit -m "Merge x"').returncode == 0)
    (c.repo / ".git/MERGE_HEAD").unlink()
    check("メッセージを渡さない --no-edit は見ない", c.hook("git commit --no-edit").returncode == 0)
    c.close()

    # 2 パス目の指摘: 後ろにリダイレクト・pathspec・連結・前置・引用符・行継続
    c = Case(script, cfg("enforce"))
    for tail in (" 2>&1", " file.py", " -- file.py", ' > /dev/null', ""):
        check(f"印の後ろが「{tail.strip()}」の形でも読む", c.hook('git commit -m "feat: x" -m "Verified: verify"' + tail).returncode == 0)
    check("印の直後の閉じ引用符に > が続く形", c.hook('git commit -m "x\n\nVerified: tests">/dev/null').returncode == 0)
    check("1 本目に印が無い連結は止める", c.hook('git commit -m "a" && git commit -m "b" -m "Verified: verify"').returncode == 2)
    check("2 本目に印が無い連結は止める", c.hook('git commit -m "a\n\nVerified: tests" && git commit -m b').returncode == 2)
    check("2 本とも印のある連結は通す", c.hook('git commit -m "a\n\nVerified: tests" && git commit -m "b\n\nVerified: gates"').returncode == 0)
    check("別コマンドの Verified: に引きずられない（前）", c.hook('echo "Verified: verify" && git commit -m "feat: x"').returncode == 2)
    check("別コマンドの Verified: に引きずられない（後）",
          c.hook('git commit -m "x\n\nVerified: tests" && gh pr create --body "a\nVerified: foo"').returncode == 0)
    check("--no-edit でも -m を渡せば見る", c.hook('git commit --no-edit -m "feat: x"').returncode == 2)
    check("単一引用符の中の \" に崩されない", c.hook("echo 'a\"b' && git commit -m x && echo 'c\"d'").returncode == 2)
    check("if の後ろの git commit も見る", c.hook("if git commit -m x; then echo ok; fi").returncode == 2)
    check("{ } の中の git commit も見る", c.hook("{ git commit -m x; }").returncode == 2)
    check("環境変数の前置の git commit も見る", c.hook("FOO=1 git commit -m x").returncode == 2)
    check("( ) の中の git commit も見る", c.hook("(git commit -m x)").returncode == 2)
    check("後ろにリダイレクトが続く印なしは止める", c.hook("git commit -m x > out.txt").returncode == 2)
    check("行継続の後ろの --dry-run を読む", c.hook("git commit \\\n --dry-run -m x").returncode == 0)
    check("$'…' の中の \\n 以降を値に含めない",
          c.hook("git commit -m $'x\\n\\nVerified: tests\\nCo-Authored-By: a <b>'").returncode == 0)
    check("ヒアドキュメントの本体の git commit は見ない",
          c.hook("cat > notes.md <<'EOF'\nnote\ngit commit -m later\nEOF").returncode == 0)
    check("単一引用符の中の git commit は見ない", c.hook("gh pr create --body 'steps: add; git commit -m x'").returncode == 0)
    check("&& の後ろの --dry-run は別のコマンドのもの", c.hook("git commit -m x && git push --dry-run").returncode == 2)
    check("-F - のヒアドキュメントの後に && が続く形", c.hook("git commit -F - <<'EOF' && git push\nfeat: x\n\nVerified: verify\nEOF").returncode == 0)
    check("区切りに - を含むヒアドキュメント", c.hook("git commit -F - <<'COMMIT-MSG'\nfeat: x\n\nVerified: verify\nCOMMIT-MSG").returncode == 0)
    check("CRLF のヒアドキュメント", c.hook("git commit -F - <<'EOF'\r\nfeat: x\r\n\r\nVerified: verify\r\nEOF\r\n").returncode == 0)
    check("ヒアドキュメントに印が無ければ止める", c.hook("git commit -F - <<'EOF' && git push\nfeat: x\nEOF").returncode == 2)
    check("別のコマンドのヒアドキュメントの印を拾わない",
          c.hook("git commit -m x && cat <<'EOF'\nVerified: verify\nEOF").returncode == 2)
    # #1368 の V1: 引用符の中の `<<` をヒアドキュメントの始まりと読まない
    (c.repo / "plain.txt").write_text("x\n")
    check("V1: -m の引用符の中の <<EOF の後ろのヒアドキュメントの印を拾わない",
          c.hook("git commit -m 'docs: explain <<EOF usage' && cat > notes.md <<'EOF'\nVerified: verify\nEOF").returncode == 2)
    check("V1: 単一引用符の中の <<EOF（-m なし）の後ろのヒアドキュメントの印を拾わない",
          c.hook("git commit --author='Bob <<EOF bob@x>' -F plain.txt && cat > notes.md <<'EOF'\nVerified: verify\nEOF").returncode == 2)
    check("V1: 二重引用符の中の <<EOF（-m なし）の後ろのヒアドキュメントの印を拾わない",
          c.hook('git commit --author="Bob <<EOF bob@x>" -F plain.txt && cat > notes.md <<\'EOF\'\nVerified: verify\nEOF').returncode == 2)
    check("V1: 引用符の中の <<EOF が次の行の git commit を隠さない",
          c.hook("git commit -m 'x' -m 'Verified: tests' --author='A <<EOF a@b>'\ngit commit -m y\nEOF").returncode == 2)
    check("\"$(cat <<'EOF' …)\" の本文の \" に崩されない",
          c.hook("git commit -m \"$(cat <<'EOF'\nfix: 3\" pipe\n\nVerified: verify\nEOF\n)\"").returncode == 0)
    check("前のヒアドキュメントの本文の ' に崩されない",
          c.hook("cat > a.md <<'EOF'\ndon't\nEOF\ngit commit -F - <<'M'\nfeat: x\n\nVerified: tests\nM\necho 'done'").returncode == 0)
    # #1368 の V2: -m を渡したコミットでは、ヒアドキュメント（stdin）を本文に数えない
    check("V2: -m のヒアドキュメントの印を数えない（印なしは止める）",
          c.hook("git commit -m 'feat: x' <<'EOF' && git push\nVerified: verify\nEOF").returncode == 2)
    check("V2: -m に印があればヒアドキュメントの語彙の外に引きずられない",
          c.hook("git commit -m 'feat\\n\\nVerified: verify' <<'EOF' && git push\nVerified: lol\nEOF").returncode == 0)
    check("V2: -am でもヒアドキュメントを数えない", c.hook("git commit -am x <<'EOF'\nVerified: verify\nEOF").returncode == 2)
    check("V2: --message= でもヒアドキュメントを数えない",
          c.hook("git commit --message=x <<'EOF'\nVerified: verify\nEOF").returncode == 2)
    (c.repo / "msg.txt").write_text("x\n\nVerified: gates\n")
    check("--file= のファイルを読む", c.hook("git commit --file=msg.txt").returncode == 0)
    check("-F は commit の部分だけで読む（別コマンドの -F を拾わない）", c.hook("git log -F msg.txt && git commit -m x").returncode == 2)
    c.close()

    # 判定できないとき・記録が書けないとき
    c = Case(script, cfg("enforce"))
    env = {**os.environ, "DEV_LOOP_GATE_LOG": str(c.log), "HOME": str(c.tmp), "GIT_CONFIG_GLOBAL": "/dev/null", "PATH": "/nonexistent"}
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": plain}, "cwd": str(c.repo)})
    r = subprocess.run([sys.executable, str(script)], input=payload, cwd=c.repo, env=env, capture_output=True, text=True)
    check("git が使えなければ通す（enforce でも）", r.returncode == 0 and c.entries() == [], f"rc={r.returncode}")
    env = {**os.environ, "DEV_LOOP_GATE_LOG": str(c.tmp / "no-such-dir" / "x.jsonl"), "HOME": str(c.tmp), "GIT_CONFIG_GLOBAL": "/dev/null"}
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": plain}, "cwd": str(c.repo)})
    r = subprocess.run([sys.executable, str(script)], input=payload, cwd=c.repo, env=env, capture_output=True, text=True)
    check("記録を書けなくても enforce は止める", r.returncode == 2 and "記録を書けなかった" in r.stderr, f"rc={r.returncode} {r.stderr}")
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": plain}, "cwd": str(c.repo)})
    r = subprocess.run([sys.executable, str(script)], input=payload, cwd=c.tmp, env={**env, "DEV_LOOP_GATE_LOG": str(c.log)},
                       capture_output=True, text=True)
    check("stdin の cwd を使う（プロセスの cwd が別でも）", r.returncode == 2, f"rc={r.returncode}")
    c.close()
    # .git でない共通ディレクトリでは設定を読まない
    c = Case(script, None)
    sep = c.tmp / "sep"
    sep.mkdir()
    sh("git", "init", "-q", "--separate-git-dir", str(c.tmp / "gitdir"), str(sep), cwd=c.tmp)
    (c.tmp / ".claude").mkdir()  # 共通ディレクトリ（c.tmp/gitdir）の親。ここを読んでしまうと enforce になる
    (c.tmp / ".claude/dev-loop.md").write_text(cfg("enforce"), encoding="utf-8")
    c.repo = sep
    check(".git でない共通ディレクトリでは off", c.hook(plain).returncode == 0 and c.entries() == [])
    c.close()

    # 設定の行が読めないとき status が名指しする
    c = Case(script, "- 検証の関門: enforce\n")
    s = sh(sys.executable, str(script), "status", "--project", str(c.repo), cwd=c.repo)
    check("status が読めなかった行を名指しする", "行頭から" in s.stdout and "off" in s.stdout, s.stdout)
    check("読めない行は off", c.hook(plain).returncode == 0)
    c.close()

    # status: 別の鍵・散文の行を誤りと名指ししない
    for name, text in (("太字の鍵", "**検証の関門**: enforce\n"), ("バッククォートの鍵", "`検証の関門`: enforce\n"), ("= の行", "検証の関門=enforce\n")):
        c = Case(script, text)
        s = sh(sys.executable, str(script), "status", "--project", str(c.repo), cwd=c.repo)
        check(f"status は {name} を名指しする", "設定の誤り" in s.stdout, s.stdout)
        c.close()
    for name, text in (("逃げ道の行だけ", "検証の関門の逃げ道: なし\n"), ("散文の行", "検証の関門は後で入れる予定。\n")):
        c = Case(script, text)
        s = sh(sys.executable, str(script), "status", "--project", str(c.repo), cwd=c.repo)
        check(f"status は {name} を誤りと名指ししない", "設定の誤り" not in s.stdout, s.stdout)
        c.close()

    # report --since
    c = Case(script, None)
    c.log.write_text(json.dumps({"ts": "2026-01-05T10:00:00+0900", "action": "would_stop", "reason": "missing", "command_head": "a"}) + "\n"
                     + json.dumps({"ts": "2026-12-05T10:00:00+0900", "action": "pass", "reason": None, "command_head": "b"}) + "\n", encoding="utf-8")
    r2 = sh(sys.executable, str(script), "report", "--log", str(c.log), "--since", "2026-06-01", cwd=c.repo)
    check("report --since は古い記録を数えない", "pass 1" in r2.stdout and "would_stop" not in r2.stdout, r2.stdout)
    c.close()

    # 語彙の写し（原本・実装役の指示）
    import importlib.util
    spec = importlib.util.spec_from_file_location("gate_under_test", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ref = (ROOT / "plugins/dev-loop/skills/dev-loop/references/verification-trailer.md").read_text(encoding="utf-8")
    impl = (ROOT / "plugins/dev-loop/skills/dev-loop/prompts/implementer.md").read_text(encoding="utf-8")
    c = Case(script, cfg("enforce"))
    for m in mod.METHODS:
        check(f"語彙 {m} は通る", c.hook(f'git commit -m "x\n\nVerified: {m}"').returncode == 0)
        check(f"語彙 {m} が原本の表にある", f"| `{m}` |" in ref)
        check(f"語彙 {m} が実装役の指示にある", f"`{m}`" in impl)
    for k in mod.MODES + mod.ESCAPES:
        check(f"設定の値 {k} が原本にある", k in ref)
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
    ("コードフェンスを設定に読む", "clean = strip_noise(text)", "clean = text"),
    ("--dry-run を見る", 'if "--dry-run" not in skel[a:b]]', "if True]"),
    ("amend の直前メッセージを読まない", 'and (not has_message_flag(segment) or "--no-edit" in segment)', "and False"),
    ("2 本の行の最初の値を採る", 'return default, f"`{key}:` の行が', 'return values[0], f"`{key}:` の行が'),
    ("値違いをそのまま採る", 'return default, f"`{key}:` の値', 'return values[0], f"`{key}:` の値'),
    ("worktree の写しを読む", 'path = Path(common).parent / ".claude" / "dev-loop.md"', 'path = Path(cwd) / ".claude" / "dev-loop.md"'),
    ("最初の印を採る", "value = clean_value(found[-1])", "value = clean_value(found[0])"),
    ("--amend -m でも直前を読む", '(not has_message_flag(segment) or "--no-edit" in segment)', "(True)"),
    ("非 UTF-8 の -F で落ちる", "        except (OSError, ValueError):\n            pass\n", "        except OSError:\n            pass\n"),
    ("マージの締めも判定する", "merge_in_progress(cwd) or (", "False or ("),
    ("--no-edit も判定する", 'or ("--no-edit" in segment and "--amend" not in segment and not has_message_flag(segment))', ""),
    ("--no-edit の -m を見ない", ' and not has_message_flag(segment)):\n            continue', "):\n            continue"),
    ("git commit-tree に当たる", "commit(?=[ \\t\\n;&|)]|$)", "commit"),
    ("引用符の中の git commit に当たる", "    skel = skeleton(command)\n", "    skel = command\n"),
    ("引用符の閉じ以降を値に含める", "return (value[:m.start()] if m else value).strip()", "return value.strip()"),
    ("-m 2 本の形を読まない", '(?:^|[\\"\']|\\\\n)[ \\t]*Verified:', '^[ \\t]*Verified:'),
    ("記録が書けないと通す", 'print(f"検証の関門: 記録を書けなかった（{exc}）", file=sys.stderr)', "sys.exit(0)"),
    ("stdin の cwd を読まない", 'cwd = data.get("cwd") or os.getcwd()', "cwd = os.getcwd()"),
    ("report --since を無視する", 'if since and r.get("ts", "") < since:', "if False:"),
    ("語彙を足しても止まらない", 'METHODS = ("tests", "gates", "verify", "code-review")', 'METHODS = ("tests", "gates", "verify", "code-review", "lint")'),
    (".git でない共通ディレクトリでも設定を読む", 'if not common or Path(common).name != ".git":', "if not common:"),
    ("読めない行を名指ししない", "        if loose:\n", "        if False:\n"),
    ("単一引用符の中を消さない", """|'[^']*'")""", '")'),
    ("ヒアドキュメントの本体を消さない", "out = HEREDOC.sub(heredoc, out)", "out = out"),
    ("値の文字のままの \\n を切らない", 'value = value.split("\\\\n")[0]', "value = value"),
    ("行継続を畳まない", 'out = command.replace("\\\\\\n", "  ")', "out = command"),
    ("区切りが && を知らない", 'SEGMENT_END = re.compile(r"&&|\\|\\||;|\\||\\n")', 'SEGMENT_END = re.compile(r"\\n")'),
    ("環境変数の前置を見ない", 'r"(?:\\w+=\\S*[ \\t]+)*(?:\\S*/)?git"', 'r"(?:\\S*/)?git"'),
    ("( と { の直後を見ない", r'(?:^|[;&|(\n{])[ \t]*(?:(?:if', r'(?:^|[;&|\n])[ \t]*(?:(?:if'),
    ("if などの前置を見ない", "(?:(?:if|then|else|elif|while|until|do|time|sudo|nohup|command|exec|env|!)[ \\t]+)*", ""),
    ("値の終わりがリダイレクトを知らない", "|[;&|)<>])", "|[;&|)])"),
    ("値の終わりが空白を知らない", "(?=\\s|$|[", "(?=$|["),
    ("判定を全体の文面で行う", "command[a:b] + heredoc_text(command, a, b)", "command"),
    ("1 本でも満たさなければ止める、をやめる", "        if reason:\n            break\n", "        if False:\n            break\n"),
    ("~~~ のフェンスを読む", "(```|~~~)", "(```)"),
    ("--file= を読まない", '(?:-F|--file)(?:=|\\s+)(\\S+)', '(?:-F)(?:=|\\s+)(\\S+)'),
    ("鍵の接頭辞に当たる", '{re.escape(key)}[*` \\t]*[:：=|]")', '{re.escape(key)}")'),
    ("ヒアドキュメントの本文を読まない", '+ heredoc_text(command, a, b)', ""),
    ("区切りに - を許さない", "([\\w.\\-]+)", "(\\w+)"),
    ("CRLF の終端を許さない", "[ \\t]*\\r?(?=\\n|$)", "[ \\t]*(?=\\n|$)"),
    ("太字の鍵を名指ししない", "[*` \\t]*[:：=|]", "[ \\t]*[:：]"),
    ("-F を読まない", 'text += "\\n" + p.read_text(encoding="utf-8")', "pass"),
    ("記録に全文を書く", "command[:HEAD_LEN]", "command"),
    # #1368
    ("骨組みが引用符の中の << を始まりと読む", "    out = hide_quoted_heredoc_ops(out)  # 引用符の中の `<<` を始まりと読まない（#1368）\n", ""),
    ("本文が引用符の中の << を始まりと読む", "HEREDOC.finditer(hide_quoted_heredoc_ops(folded))", "HEREDOC.finditer(folded)"),
    ("単一引用符の中の << を残す", 'chars[k] = chars[k + 1] = "\\x02"', "pass"),
    ("二重引用符の中の << を残す", 'chars[i] = chars[i + 1] = "\\x02"', "pass"),
    ('"$( の中を引用符の中と読む', '            elif text.startswith("$(", i):\n                stack.append("$(")\n                i += 2\n',
     ""),
    ("ヒアドキュメントの本体を跳ばさない", "        elif text.startswith(\"<<\", i) and (m := HEREDOC.match(text, i)):\n            i = m.end()\n", ""),
    ("-m でもヒアドキュメントを数える", '    if MESSAGE_ARG.search(skeleton(command)[a:b]):\n        return ""\n', ""),
    ("-am を -m と読まない", "(?:-[a-zA-Z]*m(?=[\\s=\\\"']|$)|--message\\b)\")", "(?:-m(?=[\\s=\\\"']|$)|--message\\b)\")"),
    ("--message を -m と読まない", "|--message\\b)\")", ")\")"),
    ("ヒアドキュメントの本体を commit の部分に含める", "spans.append((m.end(), body if body >= 0 else stop))", "spans.append((m.end(), stop))"),
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
