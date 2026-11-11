#!/usr/bin/env python3
"""cruise の親が止まっている枠の持ち主を止める手順（`parallel.md` の照合と止め方）の回帰テスト（#899 の D5）。

    python3 scripts/test-parallel-stop.py

**本体は `plugins/dev-loop/skills/cruise/references/parallel.md` の中にある**——「止まっている枠の持ち主」の節の、
`P=<pid>` で始まる `bash` ブロックである。**写しを作らない**——毎回そこから抜き出し、リストの字下げ（3 桁）を外し、
1 行目の `<pid>` だけ置き換えて **bash ごと流す**（`test-tab-match.py` と同じ形）。

なぜ要るか: #899 の 1 パス目で足した照合（`ps … | grep -q run-serial.py`）は部分一致で、`test-run-serial.py`・
別の周のラッパー・pid の使い回しにも当たり、健全なプロセスに SIGTERM を送りえた（2 パス目の `/code-review` の D5。利用者の判断で直した）。

見るもの（どれも一時の git リポジトリの中で。枠の記録は本物の run-serial が書いたものと、手で書いたものの両方）:

1. **本物の持ち主は止める**——worktree の `run-serial.py` で `bash -c 'sleep …; echo after'` を走らせ、その pid を渡すと、
   照合が「合った」と言い、ラッパーが 143 で終わり、子孫の `sleep` も残らない。
2. **合う偽の持ち主も止める**（下の 3〜6 の陽性対照）——`run-serial.py` という名前の偽のスクリプトを `-- <コマンド>` で起こし、
   pid・コマンド・場所・時刻が合う記録を手で書くと、止める。
3. **ファイル名が違う**（`test-run-serial.py`）なら止めない。
4. **`--` の後ろが記録のコマンドと違う**なら止めない。
5. **cwd が記録の場所と違う**なら止めない。
6. **記録の時刻より後に起きたプロセス**（pid の使い回し）なら止めない。
7. **`--` の無い起動**（`run-serial.py holders`）なら止めない。
8. **枠の記録に無い pid** なら止めない。
9. **`--timeout <秒>`（空白の形）で起こした持ち主**は止める（#917 の E3）。
10. **`--timeout=<秒>`（`=` の形）で起こした持ち主**も止める（#917 の E1——直す前の照合は本物でも拒んだ）。
11. **記録の `started` が別の時間帯で書かれていても**（同じ瞬間）、止める（#917 の E2——直す前の照合は `%z` を見ず、本物を使い回しと拒んだ）。
12. **記録の数秒後に起きたプロセス**（使い回し）なら止めない（#917 の E5——6 の 1 時間の差では、許容を広げた変異が素通りした）。
13. **記録のコマンドが `--` の後ろの一部だけ**（部分一致では合う）なら止めない（#917 の E4）。

止めないケースでは、照合が 1 で終わり、プロセスが生きたままであることを見る（止めたかを見るのはプロセスで、出力の文言ではない）。

**変異テスト**: ブロックの照合を 1 箇所ずつ緩め（部分一致に戻す・コマンドを比べない・cwd を比べない・時刻を比べない・記録を見ない・
`--timeout` の選択肢を外す・`=` の形を外す・時間帯を見ない・コマンドを部分一致で比べる・時刻の許容を広げる）、
**緩めたのに全ケースが期待どおりなら失格**。壊す文字列がブロックにちょうど 1 回現れることを先に確かめる。

**このテストは実環境を触らない**——リポジトリと枠のディレクトリは一時ディレクトリの中で、止めるのは自分が起こしたプロセスだけ。

守らないもの:

- **Linux の `/proc/<pid>/cwd` の経路**——macOS（`lsof`）でだけ走らせている。
- **pid が本当に使い回された実物**——使い回しは「記録の後に起きたプロセス」を手で作って当てる。
- **親と子で `TZ` が本当に違う起動**——記録の `started` を別の時間帯の表記で手で書いて当てる（同じ瞬間を別の表記にした記録と同じ入力になる）。
- **散文の箇条書きとコードの食い違い**——実行するのはコードだけ。

標準ライブラリのみ。POSIX（`ps`・`pgrep`・`lsof` か `/proc`）。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "plugins/dev-loop/skills/cruise/references/parallel.md"
RUN_SERIAL = ROOT / "plugins/dev-loop/skills/cruise/scripts/run-serial.py"
HEADING = "### 止まっている枠の持ち主"
CASES = 13

MUTATIONS = [
    ("部分一致に戻す",
     'm = re.fullmatch(r"(?:\\S*/)?[Pp]ython[0-9.]* (?:\\S*/)?run-serial\\.py(?: --timeout[ =][0-9]+)? -- (.*)", ps("command"))',
     'm = re.search(r"run-serial.py.*?(?: -- (.*))?$", ps("command"))'),
    ("コマンドを比べない", 'elif m.group(1) != rec.get("command"):', 'elif False:'),
    ("cwd を比べない", 'elif cwd() != rec.get("cwd"):', 'elif False:'),
    ("時刻を比べない", "if begun > taken + 1:", "if False:"),
    ("記録を見ない", 'if rec is None:\n    why = "枠の記録にこの pid が無い"',
     'if rec is None:\n    rec = {"command": (m.group(1) if m else None), "cwd": cwd(), "started": "2999-01-01T00:00:00+0000"}'),
    ("`--timeout` の選択肢を外す（E3）", "(?: --timeout[ =][0-9]+)?", ""),
    ("`=` の形を外す（E1）", "(?: --timeout[ =][0-9]+)?", "(?: --timeout [0-9]+)?"),
    ("時間帯を見ない（E2）", 'datetime.strptime(rec["started"], "%Y-%m-%dT%H:%M:%S%z").timestamp()',
     'time.mktime(time.strptime(rec["started"][:19], "%Y-%m-%dT%H:%M:%S"))'),
    ("コマンドを部分一致で比べる（E4）", 'elif m.group(1) != rec.get("command"):', 'elif (rec.get("command") or "") not in m.group(1):'),
    ("時刻の許容を広げる（E5）", "if begun > taken + 1:", "if begun > taken + 3000:"),
]


def block() -> str:
    text = DOC.read_text(encoding="utf-8")
    start = text.find(HEADING)
    if start < 0:
        sys.exit(f"失格: {DOC} に見出し {HEADING} が無い")
    section = text[start:]
    nxt = re.search(r"^## ", section[len(HEADING):], re.M)
    if nxt:
        section = section[: len(HEADING) + nxt.start()]
    for m in re.finditer(r"^( *)```bash\n(.*?)^\1```", section, re.M | re.S):
        indent, body = m.group(1), m.group(2)
        if body.lstrip().startswith("P=<pid>"):
            lines = [line[len(indent):] if line.startswith(indent) else line for line in body.splitlines()]
            return "\n".join(lines) + "\n"
    sys.exit("失格: 節の中に `P=<pid>` で始まる bash ブロックが無い")


def alive(pid: int) -> bool:
    out = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True).stdout.strip()
    return bool(out) and not out.startswith("Z")


def run_block(code: str, repo: Path, pid: int) -> subprocess.CompletedProcess:
    script = code.replace("P=<pid>", f"P={pid}", 1)
    return subprocess.run(["bash", "-c", script], cwd=repo, capture_output=True, text=True, timeout=60)


def wait_for(cond, limit: float = 10.0) -> bool:
    end = time.time() + limit
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.1)
    return cond()


class Fixture:
    def __init__(self, base: Path):
        self.base = base
        self.repo = base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.repo = Path(os.path.realpath(self.repo))
        self.lockdir = self.repo / ".git" / "dev-loop-serial"
        self.other = Path(os.path.realpath(base)) / "other"
        self.other.mkdir()
        fake = base / "fake"
        fake.mkdir()
        body = "import time\ntime.sleep(120)\n"
        (fake / "run-serial.py").write_text(body)
        (fake / "test-run-serial.py").write_text(body)
        self.fake = fake
        self.procs: list[subprocess.Popen] = []
        self.slot = 10

    def spawn(self, argv: list[str], cwd: Path) -> subprocess.Popen:
        proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        self.procs.append(proc)
        return proc

    def record(self, pid: int, command: str, cwd: Path, started: float, shift: timedelta = timedelta(0)) -> None:
        """`shift` は記録を書く時間帯を親（このテスト）の時間帯からずらす量——同じ瞬間を別の表記で書く（#917 の E2）。"""
        self.lockdir.mkdir(exist_ok=True)
        local = datetime.now().astimezone().utcoffset() or timedelta(0)
        stamp = datetime.fromtimestamp(started, timezone(local + shift)).strftime("%Y-%m-%dT%H:%M:%S%z")
        info = {"pid": pid, "cwd": str(cwd), "command": command, "started": stamp}
        (self.lockdir / f"slot-{self.slot}.lock").write_text(json.dumps(info, ensure_ascii=False))
        self.slot += 1

    def cleanup(self) -> None:
        for proc in self.procs:
            try:
                os.killpg(proc.pid, 9)
            except OSError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass


def cases(code: str) -> list[tuple[str, bool, bool]]:
    """(名前, 期待: 止める, 実際: 止めた——照合が 0 で終わり、プロセスが終わった)。"""
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        fx = Fixture(Path(tmp))
        try:
            # 1. 本物の持ち主（worktree の run-serial.py が枠を取って記録を書く）
            out = fx.base / "real.out"
            with open(out, "w") as fh:
                real = subprocess.Popen([sys.executable, str(RUN_SERIAL), "--", "bash", "-c", "sleep 117; echo after"],
                                        cwd=fx.repo, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
            fx.procs.append(real)
            if not wait_for(lambda: any(p.read_text().strip() for p in fx.lockdir.glob("slot-*.lock")) if fx.lockdir.is_dir() else False):
                sys.exit("失格: 本物の run-serial が枠の記録を書かなかった")
            r = run_block(code, fx.repo, real.pid)
            stopped = wait_for(lambda: real.poll() is not None)
            orphan = subprocess.run(["pgrep", "-f", "sleep 117"], capture_output=True, text=True).stdout.split()
            for pid in orphan:
                os.kill(int(pid), 9)
            results.append(("1 本物の持ち主", True, stopped and real.returncode == 143 and not orphan and r.returncode == 0))

            def fake_case(name: str, expect: bool, script: str, argv_tail: list[str], cwd: Path,
                          rec_command: str | None, rec_cwd: Path, started: float, record: bool = True,
                          shift: timedelta = timedelta(0)) -> None:
                """`started` は偽のプロセスを起こす直前の時刻からの秒数（記録の時刻）。"""
                spawned = time.time()
                proc = fx.spawn([sys.executable, str(fx.fake / script), *argv_tail], cwd)
                if not wait_for(lambda: alive(proc.pid)):
                    sys.exit(f"失格: {name} の偽のプロセスが起きない")
                if record:
                    command = rec_command if rec_command is not None else " ".join(argv_tail[argv_tail.index("--") + 1:] if "--" in argv_tail else argv_tail[1:])
                    fx.record(proc.pid, command, rec_cwd, spawned + started, shift)
                res = run_block(code, fx.repo, proc.pid)
                # 止めるときはブロックの中で kill してから 2 秒おく——ブロックが終わった後に生きていれば止めていない
                stopped = wait_for(lambda: proc.poll() is not None, 10.0 if expect else 1.0)
                results.append((name, expect, stopped and res.returncode == 0))

            later, earlier = 3600, -3600

            fake_case("2 合う偽の持ち主（陽性対照）", True, "run-serial.py", ["--", "copy", "db"], fx.repo, None, fx.repo, later)
            fake_case("3 ファイル名が test-run-serial.py", False, "test-run-serial.py", ["--", "copy", "db"], fx.repo, None, fx.repo, later)
            fake_case("4 記録のコマンドと違う", False, "run-serial.py", ["--", "copy", "db"], fx.repo, "other command", fx.repo, later)
            fake_case("5 cwd が記録の場所と違う", False, "run-serial.py", ["--", "copy", "db"], fx.other, None, fx.repo, later)
            fake_case("6 記録の後に起きたプロセス", False, "run-serial.py", ["--", "copy", "db"], fx.repo, None, fx.repo, earlier)
            fake_case("7 `--` の無い起動（holders）", False, "run-serial.py", ["holders"], fx.repo, "holders", fx.repo, later)
            fake_case("8 枠の記録に無い pid", False, "run-serial.py", ["--", "copy", "db"], fx.repo, None, fx.repo, later, record=False)
            fake_case("9 `--timeout <秒>` の形", True, "run-serial.py", ["--timeout", "600", "--", "copy", "db"], fx.repo, None, fx.repo, later)
            fake_case("10 `--timeout=<秒>` の形", True, "run-serial.py", ["--timeout=600", "--", "copy", "db"], fx.repo, None, fx.repo, later)
            fake_case("11 記録が別の時間帯（同じ瞬間）", True, "run-serial.py", ["--", "copy", "db"], fx.repo, None, fx.repo, 60,
                      shift=timedelta(hours=-5))
            fake_case("12 記録の数秒後に起きたプロセス", False, "run-serial.py", ["--", "copy", "db"], fx.repo, None, fx.repo, -5)
            fake_case("13 記録のコマンドが一部だけ", False, "run-serial.py", ["--", "copy", "db"], fx.repo, "copy", fx.repo, later)
        finally:
            fx.cleanup()
    return results


def main() -> int:
    code = block()
    failures = 0
    results = cases(code)
    if len(results) != CASES:
        print(f"失格: ケースが {CASES} 件でない（{len(results)} 件）")
        return 1
    for name, expect, actual in results:
        ok = expect == actual
        print(f"  {'OK  ' if ok else 'FAIL'} {name}（期待: {'止める' if expect else '止めない'}）")
        failures += not ok
    if failures:
        print(f"照合と止め方のテスト: 失敗 {failures} 件")
        return 1

    killed = 0
    for name, old, new in MUTATIONS:
        count = code.count(old)
        if count != 1:
            print(f"失格: 変異「{name}」の壊す文字列がブロックに {count} 回（1 回のはず）")
            return 1
        mutant = code.replace(old, new)
        res = cases(mutant)
        bad = [n for n, expect, actual in res if expect != actual]
        if bad:
            killed += 1
            print(f"  殺せた 変異「{name}」: {', '.join(bad)}")
        else:
            print(f"  素通り 変異「{name}」")
    if killed != len(MUTATIONS):
        print(f"失格: 変異 {len(MUTATIONS)} 件のうち殺せたのは {killed} 件")
        return 1
    print(f"照合と止め方のテスト: すべて合格（ケース {CASES} 件・変異 {len(MUTATIONS)} 件をすべて殺せた）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
