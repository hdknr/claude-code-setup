#!/usr/bin/env python3
"""`check-gates.py` の回帰テスト（#1043）。

    python3 scripts/test-check-gates.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）。
**`dev-loop` はどのリポジトリでも使うスキル**なので、対象リポジトリの `scripts/` に在ることを当てにできない
（`test-find-cycle.py` と同じ形）。

**このテストは実環境を触らない。** 一時ディレクトリに本物の git リポジトリを作り、そこにだけ当てる
（`assert_not_real_repo` が担保する。`HOME`・`GIT_CONFIG_GLOBAL` も一時ディレクトリに差し替える）。

**陽性対照**: 壊さない本体で、全部の試料が期待どおりになることを先に見る——とくに
**関門を 1 パスしか通していない計画が非 0**、**全部通した計画が 0**（Issue の受入基準の 2 つ）。そこで落ちれば変異の結果は読まない。
**変異テストを含む。** 本体を 1 箇所ずつ壊し、壊したのに期待どおりのままなら失格とする。
**「守る」の行数と変異の数が 1 対 1 か**は、テスト自身が数える。
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "check-gates.py"
PLAN_REL = "docs/plans/issue-1.md"

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


ENV: dict = {}


def git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, env=ENV)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {res.stderr}")
    return res.stdout.strip()


def commit(repo: Path, msg: str, files: dict[str, str]) -> str:
    for rel, body in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg)
    return git(repo, "rev-parse", "HEAD")


def build(root: Path) -> tuple[Path, dict[str, str]]:
    """試料のリポジトリ。周の線: B → C1 → C2 → C3 → P（計画だけ）→ V（版の行だけ）→ MM（main の取り込み）。

    脇: D（MM の後の直し）・X（MM の後の版の行とほかの行）・MO（V の後に main でない O を取り込む）・
    O（B からの別のブランチ）・O2（C3 からの別のブランチ——head の祖先でない）。
    """
    repo = root / "repo"
    repo.mkdir(parents=True)
    assert_not_real_repo(repo)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.invalid")
    git(repo, "config", "user.name", "t")
    s = {}
    s["B"] = commit(repo, "init", {
        "README.md": "x\n",
        ".claude/dev-loop.md": "# 追補\n",
        "plugin.json": '{\n  "name": "p",\n  "version": "1.0.0"\n}\n',
        "SKILL.md": "# s\n\n<!-- skill-version: 1.0.0 -->\n> **このスキルの版: 1.0.0**（プラグイン `p`）。\n\n本文\n",
    })
    git(repo, "switch", "-qc", "issue/1-x")
    s["C1"] = commit(repo, "impl", {"a.txt": "1\n"})
    s["C2"] = commit(repo, "fix after pass 1", {"a.txt": "2\n"})
    s["C3"] = commit(repo, "fix after pass 2", {"a.txt": "3\n"})
    s["P"] = commit(repo, "plan", {PLAN_REL: "# plan\n"})
    s["V"] = commit(repo, "version", {
        "plugin.json": '{\n  "name": "p",\n  "version": "1.0.1"\n}\n',
        "SKILL.md": "# s\n\n<!-- skill-version: 1.0.1 -->\n> **このスキルの版: 1.0.1**（プラグイン `p`）。\n\n本文\n",
    })
    git(repo, "switch", "-q", "main")
    s["M"] = commit(repo, "main moves", {
        "m.txt": "m\n",
        ".claude/dev-loop.md": "# 追補\n\nマージの反映: ドキュメントとプラグインの配布\n\n```text\nマージの反映: ドキュメントのみ\n```\n",
    })
    git(repo, "update-ref", "refs/remotes/origin/main", s["M"])
    git(repo, "switch", "-q", "issue/1-x")
    git(repo, "merge", "-q", "--no-edit", "--no-ff", "main")
    s["MM"] = git(repo, "rev-parse", "HEAD")
    s["D"] = commit(repo, "late fix", {"a.txt": "4\n"})
    git(repo, "reset", "-q", "--hard", s["MM"])
    s["X"] = commit(repo, "version and more", {
        "plugin.json": '{\n  "name": "p",\n  "version": "1.0.2"\n}\n', "a.txt": "5\n"})
    git(repo, "switch", "-qc", "other", s["B"])
    s["O"] = commit(repo, "other work", {"o.txt": "o\n"})
    git(repo, "switch", "-qc", "other2", s["C3"])
    s["O2"] = commit(repo, "other work 2", {"o2.txt": "o\n"})
    git(repo, "switch", "-qc", "merge-other", s["V"])
    git(repo, "merge", "-q", "--no-edit", "--no-ff", "other")
    s["MO"] = git(repo, "rev-parse", "HEAD")
    git(repo, "switch", "-q", "issue/1-x")
    git(repo, "reset", "-q", "--hard", s["MM"])
    return repo, s


TABLE = ("## 受入基準（不変条件 × 経路）\n\n| # | 不変条件 | 守り方 |\n| --- | --- | --- |\n"
         "| A1 | x | y |\n| **A2** | x | y |\n\n## ほか\n\n| # | 受入基準ではない |\n| --- | --- |\n| Z9 | z |\n")
CRIT = ["受入基準: A1 満たす", "受入基準: A2 未証明"]
FULL = ["周の base: {B}", "関門: Verifier 1 {C1} 反証=2", "関門: /code-review 1 {C1} 指摘=5",
        "関門: Verifier 2 {C2} 反証=1", "関門: /code-review 2 {C2} 指摘=3", "関門: 狭いパス {C2} {C3} 反証=0"]
ONE_PASS = ["周の base: {B}", "関門: Verifier 1 {C1} 反証=0", "関門: /code-review 1 {C1} 指摘=0",
            "関門: 狭いパス 該当なし"]


def plan_text(lines, crit=CRIT, table=TABLE, block=True, extra="") -> str:
    body = "\n".join([*lines, *crit])
    fence = f"```dev-loop-gates\n# 関門の記録\n{body}\n```\n" if block else ""
    return f"# Issue #1\n\n```bash\n周の base: 読まない\n```\n\n{table}\n## 関門の記録\n\n{fence}{extra}"


def sub(lines, **repl):
    out = []
    for l in lines:
        for k, v in repl.items():
            l = l.replace(k, v)
        out.append(l)
    return out


# 名前: (計画の行, head, 期待する終了コード, 追加の引数, 計画の作り方の追加[, 出力に要る文字列])
CASES = {
    "全部通した計画は 0（2 パス・狭いパス・計画と版の行だけのコミット・main の取り込み）":
        (FULL, "MM", 0, [], {}),
    "関門を 1 パスしか通していない計画は非 0（2 パス目の記録も該当なしも無い）":
        (ONE_PASS, "C1", 3, [], {}, "2 パス目"),
    "1 パス目の後に直したのに 2 パス目を該当なしにした計画は非 0":
        (ONE_PASS + ["関門: 2 パス目 該当なし {C1}"], "C2", 3, [], {}, "関門が見ていないコミット"),
    "1 パス目の指摘対応が 0 行で 2 パス目が該当なしなら 0":
        (ONE_PASS + ["関門: 2 パス目 該当なし {C1}"], "C1", 0, [], {}),
    "1 パス目の /code-review の記録が無ければ非 0":
        ([l for l in FULL if "/code-review 1" not in l], "MM", 3, [], {}, "1 パス目の /code-review"),
    "2 パス目の /code-review の記録が無ければ非 0":
        ([l for l in FULL if "/code-review 2" not in l], "MM", 3, [], {}, "2 パス目の /code-review"),
    "狭いパスの記録も該当なしも無ければ非 0（後にコミットが無くても）":
        (FULL[:5], "C2", 3, [], {}, "狭いパス"),
    "狭いパスを該当なしにしたのに 2 パス目の後に直していれば非 0":
        (FULL[:5] + ["関門: 狭いパス 該当なし"], "C3", 3, [], {}, "fix after pass 2"),
    "3 パス目の記録は非 0":
        (FULL + ["関門: Verifier 3 {C3} 反証=0"], "MM", 3, [], {}, "3 パス目"),
    "最後の関門の後に直したコミットがあれば非 0（狭いパスの終点が head でない）":
        (FULL, "D", 3, [], {}, "late fix"),
    "版の行とほかの行を一緒に変えたコミットは非 0":
        (FULL, "X", 3, [], {}, "version and more"),
    "main でない枝を取り込んだ merge commit は非 0":
        (FULL, "MO", 3, [], {}, "Merge branch"),
    "狭いパスの起点そのものは範囲に数えない":
        (FULL[:5] + ["関門: 狭いパス {C3} {C3} 反証=0"], "C3", 3, [], {}, "fix after pass 2"),
    "head の祖先でない終点の記録は非 0（rebase した・別の履歴）":
        (FULL[:5] + ["関門: 狭いパス {C2} {O2} 反証=0"], "C3", 3, [], {}, "祖先でない"),
    "受入基準の表の番号に判定が無ければ非 0":
        (FULL, "MM", 3, [], {"crit": ["受入基準: A1 満たす"]}, "A2 の判定が無い"),
    "表に無い番号の判定は非 0":
        (FULL, "MM", 3, [], {"crit": CRIT + ["受入基準: Z9 満たす"]}, "Z9"),
    "BLOCKED に判断の出所が無ければ非 0":
        (FULL, "MM", 3, [], {"crit": ["受入基準: A1 BLOCKED", "受入基準: A2 満たす"]}, "判断の出所"),
    "BLOCKED を線（マージ前の判断）で通すのは不在の周だけ":
        (FULL, "MM", 3, [], {"crit": ["受入基準: A1 BLOCKED 判断=マージ前の判断", "受入基準: A2 満たす"]}, "--absent"),
    "不在の周では BLOCKED を線（マージ前の判断）で通す":
        (FULL + ["マージの反映: ドキュメントとプラグインの配布"], "MM", 0, ["--absent"],
         {"crit": ["受入基準: A1 BLOCKED 判断=マージ前の判断", "受入基準: A2 満たす"]}),
    "満たさないを線で通さない（不在の周でも）":
        (FULL + ["マージの反映: ドキュメントとプラグインの配布"], "MM", 3, ["--absent"],
         {"crit": ["受入基準: A1 満たさない 判断=マージ前の判断", "受入基準: A2 満たす"]}, "利用者の指示だけ"),
    "満たさないは利用者の指示（日付）で通す":
        (FULL, "MM", 0, [], {"crit": ["受入基準: A1 満たさない 判断=利用者の指示（2026-11-16）", "受入基準: A2 満たす"]}),
    "日付の無い利用者の指示は読めない出所":
        (FULL, "MM", 3, [], {"crit": ["受入基準: A1 BLOCKED 判断=利用者の指示", "受入基準: A2 満たす"]}, "読めない"),
    "マージの反映の記録が既定ブランチの宣言と違えば非 0":
        (FULL + ["マージの反映: ドキュメントのみ"], "MM", 3, [], {}, "既定ブランチ"),
    "不在の周でマージの反映の記録が無ければ非 0":
        (FULL, "MM", 3, ["--absent"], {}, "マージの反映の記録が無い"),
    "マージの反映が「なし」なら既定ブランチを読まない":
        (FULL + ["マージの反映: なし"], "MM", 0, ["--absent"], {}),
    "記録が無ければ 2": (FULL, "MM", 2, [], {"block": False}, "記録"),
    "記録が 2 つあれば 2": (FULL, "MM", 2, [], {"extra": "\n```dev-loop-gates\n周の base: {B}\n```\n"}, "2 つ"),
    "読めない行があれば 2": (FULL + ["関門: Verifier 1 {C1}"], "MM", 2, [], {}, "読めない行"),
    "受入基準の表が無ければ 2": (FULL, "MM", 2, [], {"table": "## 受入基準\n\n- A1 x\n"}, "受入基準の表"),
    "判定の値が読めなければ 2": (FULL, "MM", 2, [], {"crit": ["受入基準: A1 OK", "受入基準: A2 満たす"]}, "判定"),
    "head が解決しなければ 7": (FULL, "nosuch", 7, [], {}),
}


def run(script: Path, repo: Path, s: dict, name: str, case) -> tuple[int, str]:
    lines, head, _rc, args, kw, *_ = case
    repl = {"{" + k + "}": v for k, v in s.items()}
    kw = {k: (sub(v, **repl) if isinstance(v, list) else
              v.replace("{B}", s["B"]) if isinstance(v, str) else v) for k, v in kw.items()}
    plan = repo / PLAN_REL
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(plan_text(sub(lines, **repl), **kw), encoding="utf-8")
    res = subprocess.run([sys.executable, str(script), str(plan), "--head", s.get(head, head), *args],
                         cwd=str(repo), capture_output=True, text=True, env=ENV)
    return res.returncode, res.stdout + res.stderr


def as_expected(case, rc: int, out: str) -> bool:
    _l, _h, want, _a, _k, *said = case
    return rc == want and all(t in out for t in said)


def docstring(source: str) -> str:
    return source.split('"""')[1]


MUTATIONS = {
    # 守る 1: 記録が無い・2 つある
    "記録が 2 つあっても読む": ("if len(blocks) > 1:", "if False:"),
    # 守る 2: 読めない行
    "読めない行を読み飛ばす": ('raise Malformed(f"読めない行: {s}")', "continue"),
    # 守る 3: 受入基準の表が無い
    "受入基準の表が無くても通す": ("if not rec.table_ids:", "if False:"),
    # 守る 4: 1 パス目の両方
    "1 パス目の記録を見ない": ("if (k, 1) not in kinds:", "if False:"),
    # 守る 5: 2 パス目
    "2 パス目の記録を見ない": ("elif not rec.pass2_none and len(two) < 2:", "elif False:"),
    # 守る 6: 狭いパス
    "狭いパスの記録を見ない": ("elif not rec.narrow_none and not rec.narrow:", "elif False:"),
    # 守る 7: head の祖先
    "head の祖先かを見ない": ("if not ctx.is_ancestor(full, ctx.head):", "if False:"),
    # 守る 8: 関門が見ていないコミット
    "見ていないコミットを通す": ("if seen or exempt(ctx, commit, parents):", "if True:"),
    # 守る 9: 起点そのものを数えない
    "起点を範囲に数える": ("commit != s and ", ""),
    # 守る 10: 計画と版の行だけは通す
    "計画だけのコミットを通さない": ("if f == ctx.plan_rel:", "if False:"),
    # 守る 11: 既定ブランチ以外の取り込み
    "どの枝の取り込みも通す": ("return all(ctx.is_ancestor(p, default) for p in parents[1:])", "return True"),
    # 守る 12: 表の番号に判定
    "判定の無い番号を見ない": ("if i not in rec.criteria:", "if False:"),
    # 守る 13: 判断の出所
    "判断の出所が無くても通す": ('reasons.append(f"受入基準 {i} が {verdict} で、判断の出所（判断=）が無い")', "continue"),
    # 守る 14: 満たさないを線で通さない
    "満たさないを線で通す": ('elif verdict == "満たさない":', "elif False:"),
    # 守る 15: 不在の周でなければ線を通さない
    "居る周でも線を通す": ("elif not ctx.absent:", "elif False:"),
    # 守る 16: マージの反映が違う
    "マージの反映を既定ブランチと比べない": ("if values != [rec.reflection]:", "if False:"),
    # 守る 17: 不在の周で記録が無い
    "不在の周でもマージの反映の記録を求めない": (
        'return ["不在の周で、マージの反映の記録が無い"] if ctx.absent else []', "return []"),
    # 守る 18: 判定できないことを通過と答えない
    "判定できないを通過と答える": (
        'print(f"**判定できなかった**: {e}", file=sys.stderr)\n        return 7',
        'print(f"**判定できなかった**: {e}", file=sys.stderr)\n        return 0'),
}

KILLS = {
    "記録が 2 つあっても読む": ["記録が 2 つあれば 2"],
    "読めない行を読み飛ばす": ["読めない行があれば 2"],
    "受入基準の表が無くても通す": ["受入基準の表が無ければ 2"],
    "1 パス目の記録を見ない": ["1 パス目の /code-review の記録が無ければ非 0"],
    "2 パス目の記録を見ない": ["関門を 1 パスしか通していない計画は非 0（2 パス目の記録も該当なしも無い）",
                         "2 パス目の /code-review の記録が無ければ非 0"],
    "狭いパスの記録を見ない": ["狭いパスの記録も該当なしも無ければ非 0（後にコミットが無くても）"],
    "head の祖先かを見ない": ["head の祖先でない終点の記録は非 0（rebase した・別の履歴）"],
    "見ていないコミットを通す": ["最後の関門の後に直したコミットがあれば非 0（狭いパスの終点が head でない）",
                           "1 パス目の後に直したのに 2 パス目を該当なしにした計画は非 0"],
    "起点を範囲に数える": ["狭いパスの起点そのものは範囲に数えない"],
    "計画だけのコミットを通さない": ["全部通した計画は 0（2 パス・狭いパス・計画と版の行だけのコミット・main の取り込み）"],
    "どの枝の取り込みも通す": ["main でない枝を取り込んだ merge commit は非 0"],
    "判定の無い番号を見ない": ["受入基準の表の番号に判定が無ければ非 0"],
    "判断の出所が無くても通す": ["BLOCKED に判断の出所が無ければ非 0"],
    "満たさないを線で通す": ["満たさないを線で通さない（不在の周でも）"],
    "居る周でも線を通す": ["BLOCKED を線（マージ前の判断）で通すのは不在の周だけ"],
    "マージの反映を既定ブランチと比べない": ["マージの反映の記録が既定ブランチの宣言と違えば非 0"],
    "不在の周でもマージの反映の記録を求めない": ["不在の周でマージの反映の記録が無ければ非 0"],
    "判定できないを通過と答える": ["head が解決しなければ 7"],
}


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        home.mkdir()
        ENV.update(os.environ, HOME=str(home), GIT_CONFIG_GLOBAL=str(home / ".gitconfig"),
                   GIT_CONFIG_NOSYSTEM="1", LC_ALL="C.UTF-8")
        ENV.pop("GIT_DIR", None)
        ENV.pop("GIT_WORK_TREE", None)
        repo, s = build(base)

        print("陽性対照: 壊さない本体で、全部の試料が期待どおりか")
        for name, case in CASES.items():
            rc, out = run(SCRIPT, repo, s, name, case)
            ok = as_expected(case, rc, out)
            check(f"{name}: rc={rc}（期待 {case[2]}）", ok)
            if not ok:
                print("    " + out.strip().replace("\n", "\n    "))

        print("\n判定できない: 取り込みがあるのに既定ブランチの追跡参照が無ければ 7")
        git(repo, "update-ref", "-d", "refs/remotes/origin/main")
        rc, out = run(SCRIPT, repo, s, "", (FULL, "MM", 7, [], {}))
        check(f"取り込みがあり、origin の参照が無い: rc={rc}（期待 7）", rc == 7 and "既定ブランチ" in out)
        rc, _ = run(SCRIPT, repo, s, "", (FULL[:5] + ["関門: 狭いパス {C2} {C3} 反証=0"], "C3", 0, [], {}))
        check(f"取り込みが無ければ、origin の参照が無くても判定できる: rc={rc}（期待 0）", rc == 0)
        git(repo, "update-ref", "refs/remotes/origin/main", s["M"])

        print("\n変異（壊したのに期待どおりなら失格）")
        if failures:
            print("  陽性対照が落ちているので、変異の結果は読まない")
        else:
            for i, (mname, (old, new)) in enumerate(MUTATIONS.items()):
                check(f"変異の当て先が 1 箇所だけ在る: {mname}", source.count(old) == 1)
                mutant = base / f"mutant{i}" / "check-gates.py"
                mutant.parent.mkdir(parents=True)
                mutant.write_text(source.replace(old, new, 1), encoding="utf-8")
                for t in KILLS[mname]:
                    rc, out = run(mutant, repo, s, t, CASES[t])
                    check(f"{mname} → 赤（{t}: rc={rc}）", not as_expected(CASES[t], rc, out))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        doc = docstring(source)
        section = doc.split("## 何を守るか")[1].split("## 終了コード")[0]
        promises = len([l for l in section.splitlines() if l.startswith("- ")])
        check(f"「守る」{promises} 行に対して変異が {len(MUTATIONS)} 件", promises == len(MUTATIONS))
        check("どの変異にも、赤になるはずの試料がある", all(KILLS.get(m) for m in MUTATIONS))

        print("\n終了コードの一覧が本体と一致するか")
        codes_doc = {int(n) for n in re.findall(r"^- \*\*(\d+)\*\*:", doc.split("## 終了コード")[1]
                                                 .split("## 何を守らないか")[0], re.M)}
        body = source.split('"""', 2)[2]
        codes_src = {int(n) for n in re.findall(r"\breturn (\d+)\b", body)} | \
                    {int(n) for n in re.findall(r"sys\.exit\((\d+)\)", body)}
        check(f"一覧 {sorted(codes_doc)} が本体 {sorted(codes_src)} と一致", codes_doc == codes_src)
        check("試料が 0 と 1 以外の全終了コードを当てている", {c[2] for c in CASES.values()} >= codes_src - {1})

        print("\n引数の誤りは 1")
        r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=tmp, env=ENV)
        check(f"引数なしで rc=1（実際 {r.returncode}）", r.returncode == 1)

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("check-gates.py のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
