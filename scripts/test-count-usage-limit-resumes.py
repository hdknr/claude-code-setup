#!/usr/bin/env python3
"""`count-usage-limit-resumes.py` の回帰テスト。

    python3 scripts/test-count-usage-limit-resumes.py

**このテストは実環境を触らない。** 毎回テンポラリに偽の `projects` ツリーを作り、
そこだけを対象にする（`assert_not_real_home` がそれを担保する）。本体は実ホームの
`~/.claude/projects` を既定にするので、**歯止めが無いと、テストが利用者の
トランスクリプトを読んで通ってしまう**。

**試料は合成である。** 形は #454 の周で実データから読んだもの（`rate_limit` のレコード・
`system`／`informational` の予告・`origin.kind`）に合わせてある。**実物そのものは CI に持ち込めない**
（リポジトリの外で、公開できない）。時間帯は `UTC` に固定する（端末の時間帯に依らない）——
**`--tz` の効き目だけは、固定の +9 時間でもう 1 度読んで見る**（UTC だけでは時間帯を無視しても緑になる）。

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
JST = datetime.timezone(datetime.timedelta(hours=9))
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
    # 履歴のコピー（fork / --resume）: sa の最初の停止を同じ uuid で別ファイルに写す。
    # **途中で切れていて、sa より先に読まれる**（`-aaa` < `-work-app`）——先に読んだほうが勝つと行方が変わる
    copy = Session("sacopy")
    copy.rows = [dict(sa.rows[0]), dict(sa.rows[1])]
    copy.write(root, project="-aaa")
    # sa の自動継続の記録だけを写したコピー——停止の記録を持たない側に数えてはならない
    auto_copy = Session("saauto")
    auto_copy.rows = [dict(sa.rows[-1])]
    auto_copy.write(root, project="-aab")
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
    # sh: 週の上限。予告を張らない。本体が差し込んだ isMeta（origin なし）の後に人間が来る
    (Session("sh").limit("2026-09-19T00:00:00", "2026-09-21T00:00:00", kind="seven_day")
     .user("2026-09-19T04:00:00", "Caveat: injected", meta=True)
     .user("2026-09-19T05:00:00", "継続", kind="human").write(root))
    # si: 人間が予告より前に来て続いた後、予告の 10 時間後に自動継続（その間の停止の記録が無い）
    (Session("si").limit("2026-09-22T09:00:00", "2026-09-22T10:00:00").armed("2026-09-22T09:00:01", "10am")
     .user("2026-09-22T09:30:00", "継続", kind="human").reply("2026-09-22T09:31:00")
     .user("2026-09-22T20:01:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))

    # sj: 表示は +9 時間の端末（「7pm」＝ 10 時 UTC）を UTC で読む。予告だけの停止が resetsAt を持つ待ちに並ぶ
    (Session("sj").limit("2026-09-23T09:00:00", "2026-09-23T10:00:00").armed("2026-09-23T09:00:01", "7pm")
     .user("2026-09-23T09:01:00", "<task-notification>x</task-notification>", kind="task-notification")
     .reply("2026-09-23T09:01:30").armed("2026-09-23T09:02:00", "7pm")
     .user("2026-09-23T10:01:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))
    # sk: 予告の無い停止に、同じ resetsAt の rate_limit と予告の組が並ぶ（表示は sj と同じ時間帯）
    (Session("sk").limit("2026-09-24T09:00:00", "2026-09-24T10:00:00", kind="seven_day")
     .user("2026-09-24T09:01:00", "<task-notification>x</task-notification>", kind="task-notification")
     .reply("2026-09-24T09:01:30").limit("2026-09-24T09:02:00", "2026-09-24T10:00:00")
     .armed("2026-09-24T09:02:01", "7pm")
     .user("2026-09-24T10:01:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))
    # sl: 誰も来ないまま、予告の 45 分後に自動継続（スリープで遅れた）
    (Session("sl").limit("2026-09-25T09:00:00", "2026-09-25T10:00:00").armed("2026-09-25T09:00:01", "10am")
     .user("2026-09-25T10:45:00", AUTO_TEXT, kind="auto-continuation", meta=True).reply("2026-09-25T10:45:30")
     .write(root))
    # sm: 停止の直後から分かれた fork——窓の長さは同じ（1 件ずつ）。人間の側が先に読まれる（`-aac` < `-work-app`）
    sm = (Session("sm").limit("2026-09-26T09:00:00", "2026-09-26T10:00:00").armed("2026-09-26T09:00:01", "10am")
          .user("2026-09-26T10:01:00", AUTO_TEXT, kind="auto-continuation", meta=True))
    sm.write(root)
    fork = Session("smfork")
    fork.rows = [dict(sm.rows[0]), dict(sm.rows[1])]
    fork.user("2026-09-26T09:30:00", "継続", kind="human").write(root, project="-aac")
    # sn: 予告より前の自動継続（早く使えるようになったとき）→ 応答 → 予告の 5 時間後に自動継続（その間の停止の記録が無い）。
    # 予告の後には何も記録が無いので、外す理由は「既に自動継続が来た」だけ
    (Session("sn").limit("2026-09-27T09:00:00", "2026-09-27T10:00:00").armed("2026-09-27T09:00:01", "10am")
     .user("2026-09-27T09:50:00", EARLY_TEXT, kind="auto-continuation", meta=True).reply("2026-09-27T09:50:30")
     .user("2026-09-27T15:00:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))
    # so: 予告の後に通知と応答だけ → 予告の 10 時間後に自動継続
    (Session("so").limit("2026-09-28T09:00:00", "2026-09-28T10:00:00").armed("2026-09-28T09:00:01", "10am")
     .user("2026-09-28T10:10:00", "<task-notification>x</task-notification>", kind="task-notification")
     .reply("2026-09-28T10:10:30")
     .user("2026-09-28T20:00:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))
    # sp: 予告より前にローカルコマンド → 予告の 10 時間後に自動継続
    (Session("sp").limit("2026-09-29T09:00:00", "2026-09-29T10:00:00").armed("2026-09-29T09:00:01", "10am")
     .user("2026-09-29T09:10:00", "<command-name>/usage</command-name>", kind="human")
     .user("2026-09-29T20:00:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root))
    # sq: 自動継続の時刻だけが違う 2 つのコピー（窓の長さも種類も同じ）。早いほう（10:01）が先に読まれる（`-aad` < `-work-app`）
    sq = (Session("sq").limit("2026-09-30T09:00:00", "2026-09-30T10:00:00").armed("2026-09-30T09:00:01", "10am")
          .user("2026-09-30T10:05:00", AUTO_TEXT, kind="auto-continuation", meta=True))
    sq.write(root)
    late_copy = Session("sqcopy")
    late_copy.rows = [dict(sq.rows[0]), dict(sq.rows[1])]
    late_copy.user("2026-09-30T10:01:00", AUTO_TEXT, kind="auto-continuation", meta=True).write(root, project="-aad")


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
        "jst": sorted((s["session"], str(iso(mod.reset_of(s)))) for s in mod.collect(root, tz=JST)[0]),
    }
    for name, path, extra in (("plain", root, []), ("anon", root, ["--anonymize"]), ("blind", blind, []),
                              ("since", root, ["--since", "2026-09-19"]), ("future", root, ["--since", "2099-01-01"])):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            status = mod.main(["--root", str(path), "--tz", "UTC"] + extra)
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
    "続けて並んだ停止の記録を畳まない": ("(not burst and not same_wait", "(not same_wait"),
    "予告の時刻が同じ停止を畳まない": ("and not same_wait(stop, reset, shown))", ")"),
    "畳む判定で表示の時刻を resetsAt と比べる":
        ('    if reset is not None and stop["reset"] is not None:\n        known, new = stop["reset"], reset\n'
         '    elif shown is not None and stop["shown_reset"] is not None:\n        known, new = stop["shown_reset"], shown\n'
         '    else:\n        known', "    if True:\n        known"),
    "畳んだあとに並んだ停止の記録を、続けて並んだものと読まない":
        ("(not burst and not same_wait", '(stop["inputs"] and not same_wait'),
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
    "isMeta を人間の入力と読む": ('    if rec.get("isMeta") or rec.get("isCompactSummary"):\n        return OTHER\n', ""),
    "コピーの窓の長さを見ない（先に読んだほうが勝つ）":
        ('if window_key(s) <= window_key(stops[s["id"]]):', "if True:"),
    "同じ自動継続を待ちと停止の記録を持たない側の両方に数える": ('o["id"] not in windowed and ', ""),
    "人間が続けたあとの遅い自動継続も待ちに入れる": ("and at > reset_of(stop) + LATE\n", "and False\n"),
    "誰も続けていない待ちでも、遅い自動継続を外す":
        ("\n                    and (any(seen in (AUTO, HUMAN, LOCAL) for seen, _ in stop[\"inputs\"])\n"
         "                         or any(t is not None and t > reset_of(stop) for _, t in stop[\"inputs\"])))", ")"),
    "ローカルコマンドが続けたあとの遅い自動継続を待ちに入れる":
        ("any(seen in (AUTO, HUMAN, LOCAL) for", "any(seen in (AUTO, HUMAN) for"),
    "自動継続が既に来た待ちの遅い自動継続を待ちに入れる":
        ("any(seen in (AUTO, HUMAN, LOCAL) for", "any(seen in (HUMAN, LOCAL) for"),
    "予告の時刻より後の記録を見ない":
        ("\n                         or any(t is not None and t > reset_of(stop) for _, t in stop[\"inputs\"])", ""),
    "窓の中身を種類だけで比べる":
        ("[(label, iso_or_empty(at)) for label, at in stop[\"inputs\"]]", "[label for label, at in stop[\"inputs\"]]"),
    "窓の長さが同じコピーは、先に読んだほうが勝つ":
        ('return len(stop["inputs"]), [(label, iso_or_empty(at)) for label, at in stop["inputs"]]',
         'return len(stop["inputs"])'),
    "表示の時刻を UTC で読む（--tz を無視する）":
        ("local = at.astimezone(tz)", "local = at.astimezone(datetime.timezone.utc)"),
    "--since を見ない": ('(s for s in stops.values() if not since or s["ts"] >= since)', "(s for s in stops.values())"),
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
        check("待ちは 18（コピーは畳む・同じ予告の時刻の停止は 1 つ）",
              len(correct["waits"]) == 18 and correct["dups"] == 3 and len(waits["sa"]) == 1)
        sa = waits["sa"][0]
        check("先に読んだコピーの窓が短くても、長いほうの窓で行方を決める", sa[7] == "自動継続")
        check("通知が先でも、その後の自動継続を拾う（予告の 1 分後）",
              sa[6:] == ("task-notification", "自動継続", "2026-09-10T10:01:00+00:00") and sa[2] and sa[4] == "five_hour")
        sb1, sb2 = waits["sb"]
        check("人間の「継続」は人間の入力で、予告より前", sb1[6:8] == ("人間の入力", "予告より前に人間"))
        check("人間が自動継続の文言を打っても人間の入力（予告の後）", sb2[6:8] == ("人間の入力", "予告の後に人間が先"))
        sc1, sc2 = waits["sc"]
        check("origin の無い旧い形は、早く使えるようになったときの文言でも自動継続", sc1[6:8] == ("自動継続", "自動継続"))
        check("origin が human でもスラッシュコマンドはローカルコマンド", sc2[6] == "ローカルコマンド")
        check("予告だけの停止も待ちで、その後の自動継続を拾う", waits["sd"][0][7] == "自動継続" and waits["sd"][0][2])
        check("停止の記録を持たない自動継続は別に数える（予告の 5〜10 時間後のものも。コピーの自動継続は数えない）",
              correct["orphans"] == 5 and "se" not in waits)
        si = waits["si"][0]
        check("予告の時刻から遅い自動継続は、その待ちのものと読まない", si[7:] == ("予告より前に人間", None))
        sf = waits["sf"]
        check("resetsAt の無い rate_limit と予告は 1 つの待ち。表示は日付をまたぐ。取り消しを数える",
              len(sf) == 1 and sf[0][3] and sf[0][5] == "2026-09-17T01:00:00+00:00" and sf[0][7] == "取り消し")
        check("予告の時刻は resetsAt を先に使う", waits["sg"][0][5] == "2026-09-18T01:00:00+00:00")
        check("表示の時刻は --tz の時間帯で読む（+9 時間の 23 時 UTC は 8 時。「1am」は翌日の 16 時 UTC）",
              dict(correct["jst"])["sf"] == "2026-09-17T16:00:00+00:00")
        sh = waits["sh"][0]
        check("張らなかった待ちは上限の種類を持つ。origin の無い isMeta は人間の入力ではない",
              sh[2] is False and sh[4] == "seven_day" and sh[6] == "その他の入力" and sh[7] == "予告より前に人間")

        check("予告だけの停止は、表示の時刻同士で比べて resetsAt を持つ待ちに畳む（--tz が違っても割らない）",
              len(waits["sj"]) == 1 and waits["sj"][0][7] == "自動継続")
        check("畳んだあとの rate_limit と予告の組も、続けて並んだものとして畳む",
              len(waits["sk"]) == 1 and waits["sk"][0][2] and waits["sk"][0][7] == "自動継続")
        check("誰も来ないまま遅れた自動継続は、その待ちのもの（予告の 45 分後）",
              waits["sl"][0][6:] == ("自動継続", "自動継続", "2026-09-25T10:45:00+00:00"))
        check("窓の長さが同じコピーは、読む順に依らず窓の中身で決める",
              len(waits["sm"]) == 1 and waits["sm"][0][7] == "自動継続")

        sn = waits["sn"][0]
        check("自動継続が既に来た待ちの、予告の 5 時間後の自動継続は別に数える",
              sn[7:] == ("自動継続", "2026-09-27T09:50:00+00:00"))
        check("予告の後に通知と応答だけ来た待ちの、予告の 10 時間後の自動継続は、その待ちのものと読まない",
              waits["so"][0][7:] == ("続かなかった", None))
        check("ローカルコマンドが続けた待ちの、予告の 10 時間後の自動継続は、その待ちのものと読まない",
              waits["sp"][0][7:] == ("予告より前に人間", None))
        check("自動継続の時刻だけが違うコピーは、読む順に依らず同じほう（遅いほう）を使う",
              len(waits["sq"]) == 1 and waits["sq"][0][8] == "2026-09-30T10:05:00+00:00")

        print("\n出力")
        status, text = correct["plain"]
        check("停止があれば 0 で終わる", status == 0)
        check("月ごとの行方（張った 17・自動継続 10・前 4・後 1・取り消し 1・続かなかった 1）",
              "| 2026-09 | 18 | 17 | 10 | 4 | 1 | 1 | 1 | 0 | 5 |" in text)
        check("張らなかった待ちの上限の種類を出す", "seven_day 1" in text)
        check("自動継続の差（分）を出す", "最小 -10・中央 +1・最大 +45（10 件）" in text)
        check("本文を出さない", "task-notification>x" not in text and "Continue the task" not in text and "/usage" not in text)
        astatus, atext = correct["anon"]
        check("--anonymize はリポジトリ名とセッションを伏せる",
              "| sa |" in text and astatus == 0 and "app" not in atext and "| sa |" not in atext
              and "## 待ちの一覧" not in atext)
        bstatus, btext = correct["blind"]
        check("停止が 0 件なら終了コード 3", bstatus == 3 and "検出できていない" in btext)
        sstatus, stext = correct["since"]
        check("--since より前の停止を数えない（sh〜sq の 10 件）", sstatus == 0 and "待ち: 10・" in stext)
        fstatus, ftext = correct["future"]
        check("--since を狭くして 0 件なら終了コード 3", fstatus == 3 and "検出できていない" in ftext)

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
