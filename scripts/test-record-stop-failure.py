#!/usr/bin/env python3
"""`record-stop-failure.py` の回帰テスト。

    python3 scripts/test-record-stop-failure.py

**このテストは実環境を触らない。** 本体は子プロセスとして、**一時ディレクトリを `HOME` にして**起こす
（`assert_not_real_home` がそれを担保する）。本体は `$HOME/.claude` に書くので、**歯止めが無いと、
テストが利用者の `~/.claude` に追記して通ってしまう**。**通知も本物を出さない**——`PATH` を偽の `osascript`
（受け取った引数をファイルに書くだけ）のディレクトリだけにする。

**入力は合成である。** キーの名前は本体 2.1.311 の文字列から読んだもの（`hook_event_name`・`error`・
`error_details`・`last_assistant_message`）と、hook の共通の入力（`session_id`・`cwd`）。

**変異テストを含む。** 本体の docstring の「守る」の行数だけ変異を当て、
**壊したのに観測が変わらなければ失格**とする。行を足したら変異も足す。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "record-stop-failure.py"
REAL_HOME = Path(os.path.expanduser("~"))
SECRET_MSG = "SECRET-ASSISTANT-MESSAGE"
SECRET_CWD = "/work/secret-project"
WAIT = "「継続」と打たずに"

GOOD = json.dumps({
    "hook_event_name": "StopFailure", "session_id": "s1", "cwd": SECRET_CWD,
    "transcript_path": "/x.jsonl", "error": "rate_limit", "error_details": "D" * 500,
    "last_assistant_message": SECRET_MSG,
}).encode()

# (名前, stdin, 通知の形)。通知の形: "fake" 偽の osascript ／ "broken" 実行できない osascript ／ "none" 無い
CASES = [
    ("good", GOOD, "fake"),
    ("auth", json.dumps({"hook_event_name": "StopFailure", "error": "authentication_failed"}).encode(), "fake"),
    ("not-json", b"not json", "fake"),
    ("list", b"[1, 2]", "fake"),
    ("no-error", json.dumps({"cwd": SECRET_CWD, "last_assistant_message": SECRET_MSG}).encode(), "fake"),
    ("null-error", b'{"error": null}', "fake"),
    ("empty", b"", "fake"),
    ("non-utf8", b"\xff\xfe{", "fake"),
    ("billing", json.dumps({"hook_event_name": "StopFailure", "error": "billing_error"}).encode(), "fake"),
    # 対にならないサロゲート——json.loads は通すが UTF-8 では書けない
    ("surrogate", b'{"error": "\\ud800x", "session_id": "\\udc00"}', "fake"),
    # cwd のサロゲート——ハッシュを取るときに符号化するので、ここで落ちると上限の記録ごと失う
    ("surrogate-cwd", b'{"error": "rate_limit", "cwd": "\\ud800"}', "fake"),
    # NUL——subprocess の引数にできない
    ("nul", b'{"error": "a\\u0000b"}', "fake"),
    ("odd-values", json.dumps({"error": "E" * 5000, "session_id": {"a": "SECRET-SID"},
                               "hook_event_name": {"cwd": SECRET_CWD}, "error_details": {"k": "SECRET-DET"}}).encode(),
     "fake"),
    ("broken-osascript", GOOD, "broken"),
    ("no-osascript", GOOD, "none"),
]

MUTATIONS = {
    "last_assistant_message を書く": (
        '"error": text(data["error"], SHORT)}',
        '"error": text(data["error"], SHORT), "message": data.get("last_assistant_message")}'),
    "cwd の生の値を書く": (
        'row["cwd_hash"] = hashlib.sha256(cwd.encode("utf-8", "surrogatepass")).hexdigest()[:12]',
        'row["cwd_hash"] = cwd'),
    "cwd の書けない文字で記録を落とす": ('cwd.encode("utf-8", "surrogatepass")', 'cwd.encode("utf-8")'),
    "error_details を切らない": ('text(data.get("error_details"), DETAILS)', 'text(data.get("error_details"), None)'),
    "error などを切らない": ("SHORT = 100", "SHORT = None"),
    "文字列でない値を書く": ("value[:limit] if isinstance(value, str) else None",
                             "value[:limit] if isinstance(value, str) else value"),
    "オブジェクトでない入力を見分けない": ("if not isinstance(data, dict):", "if data is None:"),
    "error が無い入力を見分けない": ('if not isinstance(data.get("error"), str):', "if False:"),
    "追記せずに上書きする": ('path.open("a"', 'path.open("w"'),
    "書けない文字で記録を落とす": ("ensure_ascii=True", "ensure_ascii=False"),
    "通知の失敗を握らない": ("except Exception:  # noqa: BLE001 — 通知の", "except OSError:  # 通知の"),
    "待てと添えない": ('f"{error}。{WAIT}" if limit', "error if limit"),
    "上限でなくても待てと添える": ("if limit else error", 'if limit else f"{error}。{WAIT}"'),
}

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        failures.append(name)


def assert_not_real_home(home: Path) -> None:
    resolved = home.resolve()
    assert resolved != REAL_HOME.resolve(), "テストが実ホームを HOME にしている"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "テストの HOME がテンポラリの外にある"


def fake_bins(root: Path) -> dict[str, Path]:
    bins = {}
    for kind in ("fake", "broken", "none"):
        d = root / f"bin-{kind}"
        d.mkdir()
        bins[kind] = d
    fake = bins["fake"] / "osascript"
    fake.write_text('#!/bin/sh\nprintf \'%s\\0\' "$@" >> "$OSA_LOG"\n', encoding="utf-8")
    fake.chmod(0o755)
    broken = bins["broken"] / "osascript"
    broken.write_bytes(b"\x00\x01 not an executable\n")  # 実行ビットはあるが exec できない
    broken.chmod(0o755)
    return bins


def run_case(script: Path, root: Path, bins: dict[str, Path], name: str, stdin: bytes, kind: str, times: int = 1):
    home = root / f"home-{name}"
    home.mkdir()
    assert_not_real_home(home)
    osa_log = root / f"osa-{name}"
    env = {"HOME": str(home), "PATH": str(bins[kind]), "OSA_LOG": str(osa_log)}
    codes, errs = [], []
    for _ in range(times):
        p = subprocess.run([sys.executable, str(script)], input=stdin, env=env, capture_output=True, timeout=30)
        codes.append(p.returncode)
        errs.append(p.stderr.decode("utf-8", "replace"))
    log = home / ".claude" / "usage-limit-stops.jsonl"
    rows = []
    raw_log = log.read_text(encoding="utf-8") if log.exists() else ""
    for line in raw_log.splitlines():
        row = json.loads(line)
        row.pop("time", None)
        rows.append(row)
    args = osa_log.read_bytes().decode("utf-8", "replace").split("\0")[:-1] if osa_log.exists() else []
    return {"codes": codes, "errs": errs, "rows": rows, "raw": raw_log, "osa": args}


def observe(script: Path, root: Path, bins: dict[str, Path]) -> dict:
    out = {}
    for name, stdin, kind in CASES:
        out[name] = run_case(script, root, bins, name, stdin, kind, times=2 if name == "good" else 1)
    return out


def without_raw(obs: dict) -> dict:
    """比べるための観測。`raw` は時刻を含むので外す（行の中身は `rows` が持つ）。"""
    return {n: {k: v for k, v in o.items() if k != "raw"} for n, o in obs.items()}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "correct").mkdir()
        bins = fake_bins(root)
        obs = observe(SCRIPT, root / "correct", bins)

        print("記録")
        good = obs["good"]
        check("何が来ても 0 で終わり、stderr に何も出さない",
              all(c == 0 for o in obs.values() for c in o["codes"]) and all(e == "" for o in obs.values() for e in o["errs"]))
        check("~/.claude が無くても作って書く", len(good["rows"]) == 2)
        check("2 回起こすと 2 行（追記）", good["rows"][0] == good["rows"][1])
        row = good["rows"][0]
        check("書くキーは決まったものだけ",
              set(row) == {"hook_event_name", "session_id", "error", "cwd_hash", "error_details"})
        check("error・session_id・hook_event_name をそのまま書く",
              (row["error"], row["session_id"], row["hook_event_name"]) == ("rate_limit", "s1", "StopFailure"))
        check("cwd はハッシュの先頭 12 文字", len(row["cwd_hash"]) == 12 and row["cwd_hash"] != SECRET_CWD)
        check("error_details は先頭 200 文字", row["error_details"] == "D" * 200)
        leaked = [n for n, o in obs.items() if SECRET_MSG in o["raw"] or SECRET_CWD in o["raw"] or "SECRET-" in o["raw"]
                  or any(SECRET_MSG in a or SECRET_CWD in a for a in o["osa"])]
        check("last_assistant_message と cwd の生の値は記録にも通知にも出ない", leaked == [])
        check("cwd が無ければ cwd_hash を書かない", "cwd_hash" not in obs["auth"]["rows"][0])

        odd = obs["odd-values"]["rows"]
        check("error は先頭 100 文字", len(odd) == 1 and odd[0].get("error") == "E" * 100)
        check("文字列でない session_id・hook_event_name・error_details は書かない",
              len(odd) == 1 and odd[0].get("session_id") is None and odd[0].get("hook_event_name") is None
              and "error_details" not in odd[0])
        check("対にならないサロゲートでも記録は残る",
              obs["surrogate"]["rows"] == [{"hook_event_name": None, "session_id": "\udc00", "error": "\ud800x"}])
        sc = obs["surrogate-cwd"]
        check("cwd が対にならないサロゲートでも error を残し、通知に「継続と打たずに」を添える",
              len(sc["rows"]) == 1 and sc["rows"][0].get("error") == "rate_limit" and len(sc["rows"][0].get("cwd_hash", "")) == 12
              and len(sc["osa"]) == 4 and WAIT in sc["osa"][2])
        check("NUL を含む error でも記録は残る（通知は出せない）",
              obs["nul"]["rows"] == [{"hook_event_name": None, "session_id": None, "error": "a\x00b"}]
              and obs["nul"]["osa"] == [])

        print("\n読めない入力")
        expect = {"not-json": "JSON として読めない", "list": "JSON のオブジェクトでない",
                  "no-error": "error が無い", "null-error": "error が無い",
                  "empty": "JSON として読めない", "non-utf8": "JSON として読めない"}
        for name, reason in expect.items():
            check(f"{name}: 理由だけの 1 行（{reason}）", obs[name]["rows"] == [{"unreadable": reason}])

        print("\n通知")
        osa = good["osa"]
        check("通知の本文に error と「継続と打たずに」を添える",
              len(osa) == 2 * 4 and "rate_limit" in osa[2] and WAIT in osa[2])
        billing = obs["billing"]["osa"]
        check("billing_error にも「継続と打たずに」と「利用上限」を添える",
              len(billing) == 4 and WAIT in billing[2] and "利用上限" in billing[3])
        auth = obs["auth"]["osa"]
        check("上限らしくない error には「継続と打たずに」を添えない",
              len(auth) == 4 and "authentication_failed" in auth[2] and WAIT not in auth[2])
        check("利用上限なら題に「利用上限」", "利用上限" in osa[3])
        check("利用上限でなければ題に「利用上限」と書かない",
              len(obs["auth"]["osa"]) == 4 and "利用上限" not in obs["auth"]["osa"][3])
        check("読めない入力でも通知する", len(obs["not-json"]["osa"]) == 4)
        check("osascript が exec できなくても記録は残る", len(obs["broken-osascript"]["rows"]) == 1)
        check("osascript が無ければ通知せず、記録は残る",
              obs["no-osascript"]["osa"] == [] and len(obs["no-osascript"]["rows"]) == 1)

        print("\n変異テスト（壊したのに観測が変わらなければ失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for i, (name, (needle, replacement)) in enumerate(MUTATIONS.items()):
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所: {name}", False)
                continue
            broken = root / f"mut-{i}" / SCRIPT.name
            broken.parent.mkdir()
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            (root / f"obs-{i}").mkdir()
            mutated = observe(broken, root / f"obs-{i}", bins)
            check(f"変異を殺せる: {name}", without_raw(mutated) != without_raw(obs))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_home(REAL_HOME)
        except AssertionError:
            check("実ホームを HOME にすると落ちる", True)
        else:
            check("実ホームを HOME にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("StopFailure の hook のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
