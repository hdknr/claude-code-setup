#!/usr/bin/env python3
"""`autopilot-check.py`（spec-loop の autopilot の入口が使う線の検査と権限の点検。#849）の回帰テスト。

    python3 scripts/test-autopilot-check.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-autopilot-ledger.py` と同じ形。

**このテストは実環境を触らない。** 毎回テンポラリに本物の git リポジトリを作り、台帳はそこに書く（`assert_not_real_repo`）。
設定の層は `HOME` をテンポラリにし、`CLAUDE_CONFIG_DIR` を外し、flag と managed の層をテンポラリのファイルで渡す——
**渡さないと、本体は祖先の `claude` の `--settings` と実機の managed settings を読む。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測がそろったままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が期待どおりであること（下の「正しい本体」）。本体の docstring の「守る」の行数と変異の数が等しいことを、
テスト自身が数えて見る。終了コードと線の一覧も docstring の表と突き合わせる。

**写しの突き合わせ**: 本体の docstring の「写し」に挙げた関数と定数が、dev-loop の `check-unattended-env.py` と同じであること（陽性対照として、
1 文字変えた写しで「違う」と出ること）。線の値がスキル（`skills/autopilot/SKILL.md`）に書かれていること。点検するスクリプトの名前が実在すること。

**TLC の前提の項目（#912）**: 正本の `CLAUDE.md` をテンポラリの試料に書き、TLC は偽物（絶対パスのスクリプト）で当てる——本物の TLC は走らせない。
"""
import ast
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
SCRIPT = SCRIPTS / "autopilot-check.py"
LEDGER = SCRIPTS / "autopilot-ledger.py"
TLC = SCRIPTS / "check-tlc.py"
SKILL = REAL_REPO / "plugins" / "spec-loop" / "skills" / "autopilot" / "SKILL.md"
ORIGINAL = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "check-unattended-env.py"
COPIED = ("Unreadable", "read_json", "run", "is_claude", "nearest_claude", "find_flag_settings", "config_dir",
          "managed_dropins", "layers", "perm_value", "managed_rules_only", "collect_rules", "rule_matches", "check_permissions")
COPIED_CONSTANTS = ("MANAGED_DEFAULTS", "MANAGED_LAYERS", "GOOD", "ACTION", "UNKNOWN", "HUMAN")

failures: list[str] = []

# 本体の docstring の「守る」の各行に 1 つずつ。(探す文字列, 置き換え) の組
MUTATIONS = {
    "項目の欠けを通す": [('    problems = [f"項目が無い: {item}" for item in LINES if item not in values]\n', "    problems = []\n")],
    "一覧に無い項目を通す": [('    problems += [f"一覧に無い項目: {item!r}" for item in values if item not in LINES]\n', "")],
    "一覧に無い値を通す": [("            ok = value in LINES[item]\n", "            ok = True\n")],
    "N に 0・先頭の 0・5 桁を許す": [('LIMIT_RE = re.compile(r"周 ([1-9][0-9]{0,3}) まで続ける")', 'LIMIT_RE = re.compile(r"周 ([0-9]+) まで続ける")')],
    "線の無い台帳を通す": [('    if "lines" not in data:\n', '    if "lines" not in data:\n        data["lines"] = {"values": dict.fromkeys(LINES, "止まる") | '
                                                        '{"commit": "しない", "止まる地点": "spec-review を抜けたら"}, "source": ""}\n    if False:\n')],
    "読めない台帳を 0 と読む": [("        return EXIT_UNKNOWN\n    except LinesError", "        return EXIT_OK\n    except LinesError")],
    "台帳を書く": [("    data = lg.load(lg.ledger_path(version, cwd), version)\n",
                "    data = lg.load(lg.ledger_path(version, cwd), version)\n    data[\"updated\"] = \"2000-01-01T00:00:00Z\"\n"
                "    lg.save(lg.ledger_path(version, cwd), data)\n")],
    "線がそろわなくても点検する": [("    except LinesError as exc:\n        print(",
                           "    except LinesError as exc:\n        if args.cmd == \"check\":\n"
                           "            return cmd_check(args, {\"commit\": \"しない\", \"止まる地点\": \"spec-review を抜けたら\"}, lg.main_worktree(cwd))\n"
                           "        print(")],
    "commit = しない でスクリプトを点検しない": [('    return [f"python3 {root / name}" for name in scripts] + list(COMMIT_OPS[values["commit"]])',
                                       '    return ([f"python3 {root / name}" for name in scripts] if values["commit"] != "しない" else []) '
                                       '+ list(COMMIT_OPS[values["commit"]])')],
    "マージを点検から落とす": [('"マージまで": PR_OPS + ("gh pr merge",)}', '"マージまで": PR_OPS}')],
    "commit = しない で git を点検する": [('COMMIT_OPS = {"しない": (),', 'COMMIT_OPS = {"しない": PR_OPS,')],
    "feasibility のスクリプトを落とす": [('(FEASIBILITY_SCRIPTS if values["止まる地点"] == "feasibility の後" else ())', "()")],
    "allow が deny・ask に勝つ": [("        if denied:\n", "        if denied and not allowed:\n"),
                               ("        elif asked:\n", "        elif asked and not allowed:\n")],
    "読めない層があっても良いと言う": [("        elif broken:\n", "        elif False:\n")],
    "止まりうる操作を要対処のときだけ出す": [("    items.append(stoppable_item(commands))\n",
                                  "    if exit_code(items):\n        items.append(stoppable_item(commands))\n")],
    "TLC が無くても要対処にしない": [("        return (ACTION, label, detail,", "        return (GOOD, label, detail,")],
    "外す宣言でも TLC を確かめる": [("tlc.judge(project, autopilot=True)", "tlc.judge(project, autopilot=False)")],
    "判定できないを要対処より先に返す": [("    if any(item[0] == ACTION for item in items):\n        return EXIT_ACTION\n"
                                "    if any(item[0] == UNKNOWN for item in items):\n        return EXIT_UNKNOWN\n",
                                "    if any(item[0] == UNKNOWN for item in items):\n        return EXIT_UNKNOWN\n"
                                "    if any(item[0] == ACTION for item in items):\n        return EXIT_ACTION\n")],
}

TLC_LABEL = "TLC（業務フローの形式検査）"
GOOD_LINES = {"上限": "周 5 まで続ける", "判断が要る": "推奨を暫定で採る", "commit": "マージまで", "止まる地点": "feasibility の後"}
ALLOW_ALL = ["Bash(python3:*)", "Bash(git switch:*)", "Bash(git pull:*)", "Bash(git add:*)", "Bash(git commit:*)",
             "Bash(git push:*)", "Bash(gh pr create:*)", "Bash(gh pr merge:*)"]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_{id(path)}_{path.stat().st_mtime_ns}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def isolate_env(home: Path) -> None:
    """`GIT_*`・`CLAUDE_CONFIG_DIR` を外し、`HOME` と git の設定を差し替える。"""
    for key in [k for k in os.environ if k.startswith("GIT_") or k == "CLAUDE_CONFIG_DIR"]:
        del os.environ[key]
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    os.environ.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")


def build_repo(root: Path) -> None:
    assert_not_real_repo(root.parent)
    root.mkdir(parents=True)
    git(root, "init", "-q")
    git(root, "commit", "-q", "--allow-empty", "-m", "init")


def snapshot(path: Path):
    return path.read_bytes() if path.is_file() else None


def run(mod, argv, cwd):
    """(終了コード, 標準出力, 標準エラー)。**本体の場所はふせる**——正しい本体と変異で場所が違う。"""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = mod.main(argv, cwd=str(cwd))
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            return ("例外", type(exc).__name__, "")
    here = str(mod.HERE)
    return (rc, out.getvalue().replace(here, "<scripts>"), err.getvalue().replace(here, "<scripts>"))


def items_of(text: str) -> list:
    """`check` の出力の項目（区分とラベル）。"""
    return re.findall(r"^\[([^\]]+)\] (許可: `[^`]+`|[^:]+):", text, re.M)


def scenario(mod, lg, base: Path, tag: str) -> dict:
    """1 つの本体に全試料を当て、観測を辞書で返す。**観測にはテンポラリのパスを入れない。**"""
    root = base / tag / "repo"
    build_repo(root)
    o = {}
    ledger = root / ".claude" / "plans" / "spec-autopilot-v3.json"
    flag = base / tag / "flag.json"
    flag.write_text("{}", encoding="utf-8")
    managed = base / tag / "managed" / "managed-settings.json"  # 無い（未設定）
    settings = root / ".claude" / "settings.json"
    local = root / ".claude" / "settings.local.json"
    # 正本の CLAUDE.md（#912）。許可の試料では TLC を外す宣言を置き、TLC の項目を「人が見る」にしておく
    claude_md = root / "CLAUDE.md"
    claude_md.write_text("業務フローの形式検査: しない\n", encoding="utf-8")
    fake_tlc = base / tag / "fake-tlc"
    fake_tlc.write_text("#!/bin/sh\nfor a in \"$@\"; do f=\"$a\"; done\ncase \"$f\" in\n"
                        "  Probe.tla) echo 'Model checking completed. No error has been found.'; exit 0;;\n"
                        "  Broken.tla) echo 'Error: Invariant Inv is violated.'; exit 12;;\nesac\nexit 1\n", encoding="utf-8")
    fake_tlc.chmod(0o755)

    def call(argv):
        return run(mod, argv, root)

    def write_lines(values):
        return lg.main(["lines", "3", *[f"{k}={v}" for k, v in values.items()], "--source", "テスト"], cwd=str(root))

    def check_with(perms, broken_local=False):
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({"permissions": perms}), encoding="utf-8")
        if broken_local:
            local.write_text("{壊れた", encoding="utf-8")
        elif local.exists():
            local.unlink()
        rc, out, _ = call(["check", "3", "--flag-settings", str(flag), "--managed-settings", str(managed)])
        return rc, items_of(out)

    o["台帳が無い"] = tuple(call([c, "3"])[0] for c in ("lines", "ops", "check"))
    o["版の形"] = tuple(call([c, "03"])[0] for c in ("lines", "ops", "check"))
    with contextlib.redirect_stdout(io.StringIO()):
        lg.main(["init", "3"], cwd=str(root))
    before = snapshot(ledger)
    o["線が無い"] = tuple(call([c, "3"])[0] for c in ("lines", "ops", "check"))
    o["線が無い check の項目"] = items_of(call(["check", "3", "--flag-settings", str(flag), "--managed-settings", str(managed)])[1])
    o["線が無いとき台帳は同じ"] = snapshot(ledger) == before

    # 線の形
    cases = {
        "そろった": GOOD_LINES,
        "上限が欠け": {k: v for k, v in GOOD_LINES.items() if k != "上限"},
        "commit が欠け": {k: v for k, v in GOOD_LINES.items() if k != "commit"},
        "余りの項目": GOOD_LINES | {"上限 ": "止まる"},
        "綴り違いの項目": {("commit の線" if k == "commit" else k): v for k, v in GOOD_LINES.items()},
        "上限が 止める": GOOD_LINES | {"上限": "止める"},
        "commit が マージ": GOOD_LINES | {"commit": "マージ"},
        "判断が要るが 暫定": GOOD_LINES | {"判断が要る": "暫定"},
        "止まる地点が scaffold": GOOD_LINES | {"止まる地点": "scaffold の後"},
        "周 0": GOOD_LINES | {"上限": "周 0 まで続ける"},
        "周 05": GOOD_LINES | {"上限": "周 05 まで続ける"},
        "周 全角": GOOD_LINES | {"上限": "周 ５ まで続ける"},
        "周 5 桁": GOOD_LINES | {"上限": "周 12345 まで続ける"},
        "周 1": GOOD_LINES | {"上限": "周 1 まで続ける"},
        "周 9999": GOOD_LINES | {"上限": "周 9999 まで続ける"},
        "上限 止まる": GOOD_LINES | {"上限": "止まる"},
    }
    for name, values in cases.items():
        write_lines(values)
        before = snapshot(ledger)
        o["線: " + name] = (call(["lines", "3"])[0], call(["ops", "3"])[0], snapshot(ledger) == before)
    write_lines(GOOD_LINES)
    o["lines の出力"] = call(["lines", "3"])[1]

    # 線から決まる操作
    for commit in ("しない", "PR で止まる", "マージまで"):
        for stop in ("spec-review を抜けたら", "feasibility の後"):
            write_lines(GOOD_LINES | {"commit": commit, "止まる地点": stop})
            o[f"ops: {commit} / {stop}"] = call(["ops", "3"])[1].splitlines()

    # 権限
    write_lines(GOOD_LINES)
    before = snapshot(ledger)
    o["全部 allow"] = check_with({"allow": ALLOW_ALL})
    o["merge を deny（allow もある）"] = check_with({"allow": ALLOW_ALL, "deny": ["Bash(gh pr merge:*)"]})
    o["push を ask（allow もある）"] = check_with({"allow": ALLOW_ALL, "ask": ["Bash(git push:*)"]})
    o["allow に無い"] = check_with({"allow": ["Bash(python3:*)"]})
    o["読めない層"] = check_with({"allow": ALLOW_ALL}, broken_local=True)
    o["読めない層と deny"] = check_with({"allow": ALLOW_ALL, "deny": ["Bash(gh pr merge:*)"]}, broken_local=True)
    write_lines(GOOD_LINES | {"commit": "しない"})
    o["しない で python3 だけ allow"] = check_with({"allow": ["Bash(python3:*)"]})
    o["--command を足す"] = check_with({"allow": ["Bash(python3:*)"]})  # 下で --command つきと比べる
    rc, out, _ = call(["check", "3", "--flag-settings", str(flag), "--managed-settings", str(managed), "--command", "gh workflow run"])
    o["--command つき"] = (rc, items_of(out))
    o["線の書き直しで台帳は変わる（陽性対照）"] = snapshot(ledger) != before  # 線を書き直したので変わっている（陽性対照）
    before = snapshot(ledger)
    for c in ("lines", "ops"):
        call([c, "3"])
    check_with({"allow": ALLOW_ALL})
    o["読むだけ"] = snapshot(ledger) == before

    # TLC の前提（#912）。許可は全部 allow にして、TLC の項目だけを動かす
    for name, text in (("宣言なし・呼び方なし", "# 正本\n"),
                       ("宣言なし・通る呼び方", f"TLC の呼び方: {fake_tlc}\n"),
                       ("宣言なし・通らない呼び方", "TLC の呼び方: false\n"),
                       ("宣言あり・呼び方なし", "業務フローの形式検査: しない\n"),
                       ("同じ宣言が 2 行", "業務フローの形式検査: しない\n業務フローの形式検査: しない\n")):
        claude_md.write_text(text, encoding="utf-8")
        o["TLC: " + name] = check_with({"allow": ALLOW_ALL})
    claude_md.unlink()
    o["TLC: CLAUDE.md が無い"] = check_with({"allow": ALLOW_ALL})
    claude_md.write_text("業務フローの形式検査: しない\n", encoding="utf-8")

    # 壊れた台帳
    ledger.write_text("{壊れた", encoding="utf-8")
    o["壊れた台帳"] = tuple(call([c, "3"])[0] for c in ("lines", "ops", "check"))
    return o


def function_sources(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return {n.name: ast.get_source_segment(source, n) for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in COPIED}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test-autopilot-check-")).resolve()
    saved_env = dict(os.environ)
    try:
        isolate_env(tmp / "home")
        mod = load_module(SCRIPT, "apc")
        lg = load_module(LEDGER, "apl")
        print("正しい本体")
        o = scenario(mod, lg, tmp, "correct")
        check("台帳が無い: lines・ops・check とも 4", o["台帳が無い"] == (4, 4, 4))
        check("版の形が違う（先頭の 0）: 2", o["版の形"] == (2, 2, 2))
        check("線が無い台帳: lines・ops・check とも 3、check は許可を点検しない、台帳を変えない",
              o["線が無い"] == (3, 3, 3) and o["線が無い check の項目"] == [] and o["線が無いとき台帳は同じ"])
        for name in ("そろった", "周 1", "周 9999", "上限 止まる"):
            check(f"線: {name} は 0", o["線: " + name] == (0, 0, True))
        for name in ("上限が欠け", "commit が欠け", "余りの項目", "綴り違いの項目", "上限が 止める", "commit が マージ",
                     "判断が要るが 暫定", "止まる地点が scaffold", "周 0", "周 05", "周 全角", "周 5 桁"):
            check(f"線: {name} は 3 で台帳を変えない", o["線: " + name] == (3, 3, True))
        check("lines の出力は 4 項目と出所", o["lines の出力"] == "上限 = 周 5 まで続ける\n判断が要る = 推奨を暫定で採る\ncommit = マージまで\n"
                                                    "止まる地点 = feasibility の後\n出所: テスト\n")
        sr = [f"python3 <scripts>/{n}" for n in mod.SPEC_REVIEW_SCRIPTS]
        fe = [f"python3 <scripts>/{n}" for n in mod.FEASIBILITY_SCRIPTS]
        pr = list(mod.PR_OPS)
        check("ops: しない は spec-loop のスクリプトだけ", o["ops: しない / spec-review を抜けたら"] == sr)
        check("ops: しない・feasibility の後 は feasibility のスクリプトも", o["ops: しない / feasibility の後"] == sr + fe)
        check("ops: PR で止まる は git と PR の作成（マージなし）", o["ops: PR で止まる / spec-review を抜けたら"] == sr + pr
              and "gh pr merge" not in o["ops: PR で止まる / spec-review を抜けたら"])
        check("ops: マージまで は gh pr merge も", o["ops: マージまで / feasibility の後"] == sr + fe + pr + ["gh pr merge"])
        check("ops: PR の操作は git switch・pull・add・commit・push と gh pr create",
              pr == ["git switch", "git pull", "git add", "git commit", "git push", "gh pr create"])
        n_ops = len(sr + fe + pr) + 1
        allowed = o["全部 allow"]
        check("全部 allow（TLC を外す宣言あり）: 0、全操作が良い、TLC と止まりうる操作が人が見る",
              allowed[0] == 0 and [s for s, _ in allowed[1]] == ["良い"] * n_ops + ["人が見る", "人が見る"]
              and allowed[1][-2][1] == TLC_LABEL and allowed[1][-1][1] == "止まりうる操作")
        merge = o["merge を deny（allow もある）"]
        check("deny は allow より強い: 1、gh pr merge が要対処", merge[0] == 1 and ("要対処", "許可: `gh pr merge`") in merge[1])
        push = o["push を ask（allow もある）"]
        check("ask は allow より強い: 1、git push が要対処", push[0] == 1 and ("要対処", "許可: `git push`") in push[1])
        missing = o["allow に無い"]
        check("allow に無い git と PR は要対処: 1", missing[0] == 1
              and [s for s, lab in missing[1] if lab.startswith("許可: `g")] == ["要対処"] * (len(pr) + 1))
        broken = o["読めない層"]
        check("読めない層: 4、許可は判定できない（良いと言わない）", broken[0] == 4 and ("判定できない", "設定（local）") in broken[1]
              and all(s == "判定できない" for s, lab in broken[1] if lab.startswith("許可:")))
        check("読めない層と deny: 1（要対処が先）", o["読めない層と deny"][0] == 1)
        check("しない で python3 だけ allow: 0（使わない git・PR で要対処を作らない）", o["しない で python3 だけ allow"][0] == 0
              and not any(lab.startswith("許可: `g") for _, lab in o["しない で python3 だけ allow"][1]))
        check("--command で足した操作も点検する", o["--command つき"][0] == 1
              and ("要対処", "許可: `gh workflow run`") in o["--command つき"][1] and o["--command を足す"][0] == 0)
        check("lines・ops・check は台帳を書かない（線を書き直した台帳は変わる——陽性対照）", o["読むだけ"] and o["線の書き直しで台帳は変わる（陽性対照）"])
        check("壊れた台帳: lines・ops・check とも 4", o["壊れた台帳"] == (4, 4, 4))
        def tlc_status(key):
            rc, items = o["TLC: " + key]
            return rc, [st for st, lab in items if lab == TLC_LABEL]
        check("TLC: 宣言なし・呼び方なし は 1 で要対処（単位を進める前に示す）", tlc_status("宣言なし・呼び方なし") == (1, ["要対処"]))
        check("TLC: CLAUDE.md が無い は 1 で要対処", tlc_status("CLAUDE.md が無い") == (1, ["要対処"]))
        check("TLC: 宣言なし・通らない呼び方 は 1 で要対処", tlc_status("宣言なし・通らない呼び方") == (1, ["要対処"]))
        check("TLC: 宣言なし・通る呼び方 は 0 で良い（陽性対照）", tlc_status("宣言なし・通る呼び方") == (0, ["良い"]))
        check("TLC: 宣言あり・呼び方なし は 0 で人が見る（要対処にしない）", tlc_status("宣言あり・呼び方なし") == (0, ["人が見る"]))
        check("TLC: 同じ宣言が 2 行 は 4 で判定できない", tlc_status("同じ宣言が 2 行") == (4, ["判定できない"]))

        print("\n写しは dev-loop の check-unattended-env.py と同じ")
        mine, theirs = function_sources(SCRIPT), function_sources(ORIGINAL)
        for name in COPIED:
            check(f"{name} が両方に在って同じ", name in mine and mine.get(name) == theirs.get(name))
        listed = re.findall(r"`([A-Za-z_]+)`", SCRIPT.read_text(encoding="utf-8").split("## 写し")[1].split("は、dev-loop の")[0])
        check(f"docstring の「写し」の一覧 {listed} と COPIED が同じ", tuple(listed) == COPIED)
        altered = dict(mine, rule_matches=mine["rule_matches"].replace('":*"', '":**"'))
        check("陽性対照: 1 か所変えた写しは「違う」と出る", altered["rule_matches"] != theirs["rule_matches"])
        original = load_module(ORIGINAL, "cue")
        for name in COPIED_CONSTANTS:
            check(f"定数 {name} が同じ", getattr(mod, name) == getattr(original, name))

        print("\n線の一覧・終了コード・スクリプトの名前が、docstring・スキル・実物と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 線（`lines`）")[1].split("## ")[0]
        documented = {m.group(1): tuple(re.findall(r"`([^`]+)`", m.group(2)))
                      for m in re.finditer(r"^\| `([^`]+)` \| (.+) \|$", table, re.M)}
        check(f"docstring の線の表 {documented} と LINES", documented == mod.LINES)
        skill = SKILL.read_text(encoding="utf-8")
        for item, values in mod.LINES.items():
            check(f"スキルに線 {item} の値がすべて書かれている", f"`{item}`" in skill and all(f"`{v}`" in skill for v in values))
        exits = source.split("## 終了コード")[1].split("## ")[0]
        documented_codes = {int(m) for m in re.findall(r"^\| (\d+) \|", exits, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_ACTION, mod.EXIT_USAGE, mod.EXIT_LINES, mod.EXIT_UNKNOWN}
        check(f"終了コードの表 {sorted(documented_codes)} と定数 {sorted(defined)}", documented_codes == defined)
        for name in mod.SPEC_REVIEW_SCRIPTS + mod.FEASIBILITY_SCRIPTS:
            check(f"点検するスクリプトが実在する: {name}", (SCRIPTS / name).is_file())

        print("\n変異テスト（壊したのに観測がそろったままなら失格）")
        for i, (name, pairs) in enumerate(MUTATIONS.items()):
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}: {missing}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{i}"
            (d / "scripts").mkdir(parents=True)
            broken = d / "scripts" / "autopilot-check.py"
            broken.write_text(mutated, encoding="utf-8")
            shutil.copy(LEDGER, d / "scripts" / "autopilot-ledger.py")
            shutil.copy(TLC, d / "scripts" / "check-tlc.py")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
            try:
                mutant = load_module(broken, "mut")
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, lg, d, "s")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", got != o)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)
    finally:
        os.environ.clear()
        os.environ.update(saved_env)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("autopilot の線と権限の点検のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
