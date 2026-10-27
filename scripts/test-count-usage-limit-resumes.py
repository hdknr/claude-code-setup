#!/usr/bin/env python3
"""`count-usage-limit-resumes.py` の回帰テスト。

    python3 scripts/test-count-usage-limit-resumes.py

**このテストは実環境を触らない。** 毎回テンポラリに偽の `projects` ツリーを作り、
そこだけを対象にする（`assert_not_real_home` がそれを担保する）。本体は実ホームの
`~/.claude/projects` を既定にするので、**歯止めが無いと、テストが利用者の
トランスクリプトを読んで通ってしまう**。

**試料は合成である。** 形は #454 の周で実データから読んだもの（`rate_limit` のレコード・
`system`／`informational` の予告・`origin.kind`）に合わせてある。**実物そのものは CI に持ち込めない**
（リポジトリの外で、公開できない）。時間帯は `UTC` に固定する（端末の時間帯に依らない）。

**変異テストを含む。** 本体の docstring の「守る」の行数だけ変異を当て、
**壊したのに観測が変わらなければ失格**とする。行を足したら変異も足す。
"""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "count-usage-limit-resumes.py"
REAL_HOME_PROJECTS = Path(os.path.expanduser("~")) / ".claude" / "projects"
REPO = "/work/app"
UTC = datetime.timezone.utc
AUTO_TEXT = ("Your claude.ai usage limit has reset. Continue the task you were working on when the limit "
             "was reached; do not repeat work that is already complete.")
EARLY_TEXT = ("Your claude.ai usage is available again before the usage-limit reset. Continue the task you "
              "were working on when the limit was reached; do not repeat work that is already complete.")
CANCEL = ("Automatic continue cancelled · Claude Code exited during the wait, so the task will not resume "
          "on its own when the usage limit resets")

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"culr_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_home(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_HOME_PROJECTS.resolve(), "テストが実ホームの projects を対象にしている"
    assert not str(resolved).startswith(str(REAL_HOME_PROJECTS.resolve()) + os.sep), (
        "テストの対象が実ホームの projects の内側にある"
    )
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        failures.append(name)


def epoch(iso: str) -> int:
    return int(datetime.datetime.fromisoformat(iso + "+00:00").timestamp())


class Session:
    """1 ファイル分のレコードを組み立てる。時刻はレコードごとに渡す（UTC）。"""

    def __init__(self, sid: str):
        self.sid, self.rows, self.n = sid, [], 0

    def _rec(self, ts, **fields):
        self.n += 1
        self.rows.append({"uuid": f"{self.sid}-{self.n}", "timestamp": ts + "Z", "cwd": REPO, **fields})
        return self

    def limit(self, ts, reset=None, kind="five_hour"):
        quota = {} if reset is None else {"quotaLimits": {"status": "rejected", "resetsAt": epoch(reset),
                                                          "rateLimitType": kind}}
        return self._rec(ts, type="assistant", error="rate_limit", isApiErrorMessage=True,
                         message={"role": "assistant", "content": [{"type": "text", "text": "limit"}]}, **quota)

    def notice(self, ts, text):
        return self._rec(ts, type="system", subtype="informational", level="notice", content=text)

    def armed(self, ts, clock):
        return self.notice(ts, f"Usage limit reached · continuing automatically at {clock} · esc to cancel")

    def user(self, ts, text, kind=None, meta=None):
        extra = {} if kind is None else {"origin": {"kind": kind}}
        if meta is not None:
            extra["isMeta"] = meta
        return self._rec(ts, type="user", message={"role": "user", "content": text}, **extra)

    def tool_result(self, ts):
        return self._rec(ts, type="user", message={"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]})

    def reply(self, ts):
        return self._rec(ts, type="assistant", message={"role": "assistant", "content": [{"type": "text", "text": "x"}]})

    def write(self, root: Path, project="-work-app"):
        d = root / project
        d.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(r, ensure_ascii=False) for r in self.rows]
        (d / f"{self.sid}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self


def build_tree(root: Path) -> None:
    # sa: 通知 → 応答 → 同じ予告の時刻でまた上限 → 道具の結果 → 自動継続（#454 の実データの典型）
    sa = (Session("sa").limit("2026-09-10T09:00:00", "2026-09-10T10:00:00").armed("2026-09-10T09:00:01", "10am")
          .user("2026-09-10T09:01:00", "<task-notification>x</task-notification>", kind="task-notification")
          .reply("2026-09-10T09:01:30").limit("2026-09-10T09:02:00", "2026-09-10T10:00:00")
          .tool_result("2026-09-10T09:03:00")
          .user("2026-09-10T10:01:00", AUTO_TEXT, kind="auto-continuation", meta=True))
    sa.write(root)
    # 履歴のコピー（fork / --resume）: sa の最初の停止を同じ uuid で別ファイルに写す
    copy = Session("sacopy")
    copy.rows = [dict(sa.rows[0]), dict(sa.rows[1])]
    copy.write(root, project="-work-app--claude-worktrees-x")
    # sb: 人間の「継続」（予告より前）と、人間が自動継続の文言を打った形（予告の後）
    (Session("sb").limit("2026-09-11T09:00:00", "2026-09-11T10:00:00").armed("2026-09-11T09:00:01", "10am")
     .user("2026-09-11T09:30:00", "継続", kind="human")
     .limit("2026-09-12T09:00:00", "2026-09-12T10:00:00").armed("2026-09-12T09:00:01", "10am")
     .user("2026-09-12T10:05:00", AUTO_TEXT, kind="human").write(root))
    # sc: origin の無い旧い形——早く使えるようになったときの文言。続けてローカルコマンド（origin は human）
    (Session("sc").limit("2026-09-13T09:00:00", "2026-09-13T10:00:00").armed("2026-09-13T09:00:01", "10am")
     .user("2026-09-13T09:50:00", EARLY_TEXT, meta=True)
     .limit("2026-09-14T09:00:00", "2026-09-14T10:00:00").armed("2026-09-14T09:00:01", "10am")
     .user("2026-09-14T09:10:00", "<command-name>/usage</command-name>", kind="human").write(root))
    # sd: 予告だけの停止（rate_limit のレコードが無い）→ 通知 → 自動継続
    (Session("sd").armed("2026-09-15T09:00:00", "10am")
     .user("2026-09-15T09:01:00", "<task-notification>x</task-notification>", kind="task-notification")
     .user("2026-09-15T10:01:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))
    # se: 停止の記録を持たない自動継続
    Session("se").user("2026-09-16T10:01:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root)
    # sf: resetsAt の無い rate_limit と予告が並ぶ。予告は日付をまたぐ（23 時に「1am」）。終了で取り消し
    (Session("sf").limit("2026-09-16T23:00:00").armed("2026-09-16T23:00:01", "1am")
     .notice("2026-09-16T23:30:00", CANCEL).write(root))
    # sg: resetsAt（01:00）と表示（「10am」——端末の時間帯で書かれた）が食い違う。resetsAt を使う
    (Session("sg").limit("2026-09-18T00:00:00", "2026-09-18T01:00:00").armed("2026-09-18T00:00:01", "10am")
     .user("2026-09-18T01:01:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))
    # sh: 週の上限。予告を張らない。人間が来る
    (Session("sh").limit("2026-09-19T00:00:00", "2026-09-21T00:00:00", kind="seven_day")
     .user("2026-09-19T05:00:00", "継続", kind="human").write(root))


def build_blind(root: Path) -> None:
    """停止が 1 つも無い（形式が変わった・検出器が壊れた）。"""
    Session("b1").user("2026-09-20T00:00:00", "hello", kind="human").reply("2026-09-20T00:00:05").write(root)


def iso(at):
    return at.isoformat() if at else None


def observe(mod, root: Path, blind: Path) -> dict:
    assert_not_real_home(root)
    assert_not_real_home(blind)
    stops, orphans, stats = mod.collect(root, tz=UTC)
    out = {
        "waits": sorted((s["session"], s["ts"], s["armed"], s["cancelled"], s["limit"], iso(mod.reset_of(s)),
                         s["first"], s["fate"], iso(s["auto_ts"])) for s in stops),
        "orphans": len(orphans), "dups": stats["duplicate_stops"],
    }
    for name, path, anon in (("plain", root, False), ("anon", root, True), ("blind", blind, False)):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            status = mod.main(["--root", str(path), "--tz", "UTC"] + (["--anonymize"] if anon else []))
        out[name] = (status, buf.getvalue())
    return out


MUTATIONS = {
    "自動継続を文言だけで決める（origin を見ない）":
        ("if kind is None and text.startswith(AUTO_TEXTS):", "if text.startswith(AUTO_TEXTS):"),
    "人間の「継続」を自動継続と読む": ("if kind == AUTO_KIND:", "if kind in (AUTO_KIND, HUMAN_KIND):"),
    "早く使えるようになったときの文言を読まない":
        ('    "Your claude.ai usage is available again before the usage-limit reset. Continue the task",\n', ""),
    "ローカルコマンドを人間の入力に混ぜる": ("if text.startswith(LOCAL_MARKS):", "if False:"),
    "道具の結果を入力と読む": ("if only_tool_results(content):", "if False:"),
    "履歴のコピーを畳まない": ('if s["id"] in stops:', "if False:"),
    "続けて並んだ停止の記録を畳まない": ('(stop["inputs"] and not same_wait', "(not same_wait"),
    "予告の時刻が同じ停止を畳まない": ("and not same_wait(stop, reset or shown))", ")"),
    "予告だけの停止を落とす": ("if is_limit or notice.startswith(STOP_NOTICE):", "if is_limit:"),
    "最初に来たものの後の自動継続を拾わない":
        ('next((at for label, at in inputs if label == AUTO), None)',
         'next((at for label, at in inputs[:1] if label == AUTO), None)'),
    "停止の記録を持たない自動継続を落とす": ("orphans.append({", "[].append({"),
    "表示の時刻を resetsAt より先に使う":
        ('return stop["reset"] or stop["shown_reset"]', 'return stop["shown_reset"] or stop["reset"]'),
    "表示の時刻が日付をまたがない": ("if reset < local:", "if False:"),
    "取り消しを数えない": ('stop["cancelled"] = True', "pass"),
    "予告より前の人間を予告の後と分けない": ("resumer[1] < reset", "resumer[1] > reset"),
    "上限の種類を出さない": ('quota.get("rateLimitType")', "None"),
    "停止が 0 件でも 0 で終わる": ('return "\\n".join(lines) + "\\n", 3', 'return "\\n".join(lines) + "\\n", 0'),
    "--anonymize でも一覧を出す": ("if not anonymize:", "if True:"),
}


def main() -> int:
    mod = load()
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        root, blind = tmpdir / "projects", tmpdir / "blind"
        build_tree(root)
        build_blind(blind)
        correct = observe(mod, root, blind)
        waits = {}
        for w in correct["waits"]:
            waits.setdefault(w[0], []).append(w)

        print("待ちと行方")
        check("待ちは 9（コピーは畳む・同じ予告の時刻の停止は 1 つ）",
              len(correct["waits"]) == 9 and correct["dups"] == 1 and len(waits["sa"]) == 1)
        sa = waits["sa"][0]
        check("通知が先でも、その後の自動継続を拾う（予告の 1 分後）",
              sa[6:] == ("task-notification", "自動継続", "2026-09-10T10:01:00+00:00") and sa[2] and sa[4] == "five_hour")
        sb1, sb2 = waits["sb"]
        check("人間の「継続」は人間の入力で、予告より前", sb1[6:8] == ("人間の入力", "予告より前に人間"))
        check("人間が自動継続の文言を打っても人間の入力（予告の後）", sb2[6:8] == ("人間の入力", "予告の後に人間が先"))
        sc1, sc2 = waits["sc"]
        check("origin の無い旧い形は、早く使えるようになったときの文言でも自動継続", sc1[6:8] == ("自動継続", "自動継続"))
        check("origin が human でもスラッシュコマンドはローカルコマンド", sc2[6] == "ローカルコマンド")
        check("予告だけの停止も待ちで、その後の自動継続を拾う", waits["sd"][0][7] == "自動継続" and waits["sd"][0][2])
        check("停止の記録を持たない自動継続は別に数える", correct["orphans"] == 1 and "se" not in waits)
        sf = waits["sf"]
        check("resetsAt の無い rate_limit と予告は 1 つの待ち。表示は日付をまたぐ。取り消しを数える",
              len(sf) == 1 and sf[0][3] and sf[0][5] == "2026-09-17T01:00:00+00:00" and sf[0][7] == "取り消し")
        check("予告の時刻は resetsAt を先に使う", waits["sg"][0][5] == "2026-09-18T01:00:00+00:00")
        sh = waits["sh"][0]
        check("週の上限は張らず、上限の種類を持つ", sh[2] is False and sh[4] == "seven_day")

        print("\n出力")
        status, text = correct["plain"]
        check("停止があれば 0 で終わる", status == 0)
        check("月ごとの行方（張った 8・自動継続 4・前 2・後 1・取り消し 1・続かなかった 0）",
              "| 2026-09 | 9 | 8 | 4 | 2 | 1 | 1 | 0 | 0 | 1 |" in text)
        check("張らなかった待ちの上限の種類を出す", "seven_day 1" in text)
        check("自動継続の差（分）を出す", "最小 -10・中央 +1・最大 +1（4 件）" in text)
        check("本文を出さない", "task-notification>x" not in text and "Continue the task" not in text and "/usage" not in text)
        astatus, atext = correct["anon"]
        check("--anonymize はリポジトリ名とセッションを伏せる",
              "| sa |" in text and astatus == 0 and "app" not in atext and "| sa |" not in atext
              and "## 待ちの一覧" not in atext)
        bstatus, btext = correct["blind"]
        check("停止が 0 件なら終了コード 3", bstatus == 3 and "検出できていない" in btext)

        print("\n変異テスト（壊したのに観測が変わらなければ失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所: {name}", False)
                continue
            broken = tmpdir / f"mut-{abs(hash(name))}" / SCRIPT.name
            broken.parent.mkdir()
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            check(f"変異を殺せる: {name}", observe(load(broken), root, blind) != correct)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_home(REAL_HOME_PROJECTS)
        except AssertionError:
            check("実ホームの projects を対象にすると落ちる", True)
        else:
            check("実ホームの projects を対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("利用上限の後の継続の計数のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
