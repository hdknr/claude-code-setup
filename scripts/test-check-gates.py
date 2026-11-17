#!/usr/bin/env python3
"""`check-gates.py` の回帰テスト（#1043。影響範囲は #1047）。

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
        ".claude-plugin/plugin.json": '{\n  "name": "p",\n  "version": "1.0.0"\n}\n',
        "other.json": '{\n  "version": "1.0.0"\n}\n',
        "SKILL.md": "# s\n\n<!-- skill-version: 1.0.0 -->\n> **このスキルの版: 1.0.0**（プラグイン `p`）。\n\n本文\n",
    })
    git(repo, "switch", "-qc", "issue/1-x")
    s["C1"] = commit(repo, "impl", {"a.txt": "1\n"})
    s["C2"] = commit(repo, "fix after pass 1", {"a.txt": "2\n"})
    s["C3"] = commit(repo, "fix after pass 2", {"a.txt": "3\n"})
    s["P"] = commit(repo, "plan", {PLAN_REL: "# plan\n"})
    s["V"] = commit(repo, "version", {
        ".claude-plugin/plugin.json": '{\n  "name": "p",\n  "version": "1.0.1"\n}\n',
        "SKILL.md": "# s\n\n<!-- skill-version: 1.0.1 -->\n> **このスキルの版: 1.0.1**（プラグイン `p`）。\n\n本文\n",
    })
    # 脇: SD（main に入らない枝の変更。main の SQ の本文がそれを「戻した」と引く——squash に残った PR の途中の revert）
    git(repo, "switch", "-qc", "side", s["B"])
    s["SD"] = commit(repo, "side work", {"sd.txt": "s\n"})
    git(repo, "switch", "-q", "main")
    # main: R0（rolled.txt を足す）→ RV（R0 を git revert で戻す）→ SQ（本文に SD を戻したと書いた squash）→ M
    s["R0"] = commit(repo, "risky change", {"rolled.txt": "r\n"})
    git(repo, "revert", "--no-edit", s["R0"])
    s["RV"] = git(repo, "rev-parse", "HEAD")
    s["SQ"] = commit(repo, f"squashed pr\n\n* Revert side\n\nThis reverts commit {s['SD']}.", {"q.txt": "q\n"})
    # merge commit で入れた PR の中のコミット IN を、main の上で git revert で戻す（IN は main の最初の親の線に無い）
    git(repo, "switch", "-qc", "pr1")
    s["IN"] = commit(repo, "inner change", {"in.txt": "i\n"})
    git(repo, "switch", "-q", "main")
    git(repo, "merge", "-q", "--no-edit", "--no-ff", "pr1")
    git(repo, "revert", "--no-edit", s["IN"])
    s["M"] = commit(repo, "main moves", {"m.txt": "m\n", "risky/keep.txt": "k\n", ".claude/dev-loop.md": MAIN_MD})
    # 既定ブランチを差し替える試料（M の子。周の head には入らない）: 読めない宣言・glob の文字の無いディレクトリの宣言
    s["M2"] = commit(repo, "unreadable decl", {".claude/dev-loop.md": MAIN_MD + "不在で止める範囲: /risky/\n"})
    git(repo, "reset", "-q", "--hard", s["M"])
    s["M3"] = commit(repo, "dir decl without slash", {".claude/dev-loop.md": MAIN_MD + "不在で止める範囲: deepdir\n"})
    git(repo, "reset", "-q", "--hard", s["M"])
    s["M4"] = commit(repo, "bulleted decl", {".claude/dev-loop.md": MAIN_MD + "- 不在で止める範囲: q.txt\n"})
    git(repo, "reset", "-q", "--hard", s["M"])
    s["M5"] = commit(repo, "decl added after the fork", {".claude/dev-loop.md": MAIN_MD + "不在で止める範囲: q.txt\n"})
    git(repo, "reset", "-q", "--hard", s["M"])
    # J1（#1047）: 非 ASCII のパスの宣言（git は既定で引用符つきで出す——core.quotePath）
    s["M6"] = commit(repo, "non-ascii decl", {".claude/dev-loop.md": MAIN_MD + JP_DECL, "docs/設計/a.md": "a\n"})
    git(repo, "reset", "-q", "--hard", s["M"])
    # R1（#1047）: 飾った宣言・全角のコロン（宣言として読む）と、書き損じ（読めない宣言として止める）
    s["M8"] = commit(repo, "decorated decls", {".claude/dev-loop.md": MAIN_MD + DECORATED,
                                               **{f"dir{i}/k.txt": "k\n" for i in range(1, 11)}})
    git(repo, "reset", "-q", "--hard", s["M"])
    s["M9"] = commit(repo, "misspelled decls", {".claude/dev-loop.md": MAIN_MD + MISSPELLED})
    git(repo, "reset", "-q", "--hard", s["M"])
    # J2（#1047）: キーワードを含むだけの散文の行
    s["M7"] = commit(repo, "prose line", {".claude/dev-loop.md": MAIN_MD + PROSE})
    git(repo, "reset", "-q", "--hard", s["M"])
    # F1・F2（#1148）: 強調の閉じがコロンの内側にある宣言・値の無い宣言
    s["M10"] = commit(repo, "closing emphasis inside colon", {".claude/dev-loop.md": MAIN_MD + FIX_CLOSE,
                                                               **{f"e{i}/k.txt": "k\n" for i in range(1, 5)}, "k.zz": "k\n", "_build/k.txt": "k\n"})
    git(repo, "reset", "-q", "--hard", s["M"])
    s["M11"] = commit(repo, "no value decls", {".claude/dev-loop.md": MAIN_MD + NO_VALUE})
    git(repo, "reset", "-q", "--hard", s["M"])
    git(repo, "update-ref", "refs/remotes/origin/main", s["M"])
    git(repo, "switch", "-q", "issue/1-x")
    git(repo, "merge", "-q", "--no-edit", "--no-ff", "main")
    s["MM"] = git(repo, "rev-parse", "HEAD")
    s["D"] = commit(repo, "late fix", {"a.txt": "4\n"})
    git(repo, "reset", "-q", "--hard", s["MM"])
    s["X"] = commit(repo, "version and more", {
        ".claude-plugin/plugin.json": '{\n  "name": "p",\n  "version": "1.0.2"\n}\n', "a.txt": "5\n"})
    git(repo, "reset", "-q", "--hard", s["MM"])
    s["Y"] = commit(repo, "declare on the branch", {
        ".claude/dev-loop.md": "# 追補\n\nマージの反映: ドキュメントのみ\n"})
    git(repo, "reset", "-q", "--hard", s["MM"])
    s["Z1"] = commit(repo, "banner with more text", {
        "SKILL.md": "# s\n\n<!-- skill-version: 1.0.1 -->\n> **このスキルの版: 1.0.1**（プラグイン `p`）。 ついでに規範を書き換えた\n\n本文\n"})
    git(repo, "reset", "-q", "--hard", s["MM"])
    s["Z2"] = commit(repo, "version of another file", {"other.json": '{\n  "version": "9.9.9"\n}\n'})
    # 影響範囲（#1047）: 宣言した範囲・戻した範囲・main の線に無い revert の範囲・ブランチにだけ足した宣言
    for key, files in (("R1", {"risky/deep/x.txt": "x\n"}), ("R2", {"rolled.txt": "again\n"}),
                       ("R3", {"sd.txt": "s2\n"}), ("R4", {"in.txt": "again\n"}),
                       ("R5", {".claude/dev-loop.md": MAIN_MD.replace("不在で止める範囲: m.txt\n", "")}),
                       ("H2", {".claude/dev-loop.md": MAIN_MD + "不在で止める範囲: /risky/\n"}),
                       ("H3", {".claude/dev-loop.md": MAIN_MD + "不在で止める範囲: deepdir\n", "deepdir/x.txt": "d\n"}),
                       ("H4", {".claude/dev-loop.md": MAIN_MD + "- 不在で止める範囲: q.txt\n"}),
                       ("H6", {".claude/dev-loop.md": MAIN_MD + JP_DECL}),
                       ("H7", {".claude/dev-loop.md": MAIN_MD + JP_DECL, "docs/設計/b.md": "b\n"}),
                       ("H8", {".claude/dev-loop.md": MAIN_MD + PROSE}),
                       ("H9", {".claude/dev-loop.md": MAIN_MD + DECORATED}),
                       ("H10", {".claude/dev-loop.md": MAIN_MD + DECORATED, **{f"dir{i}/x.txt": "x\n" for i in range(1, 11)}}),
                       ("H11", {".claude/dev-loop.md": MAIN_MD + MISSPELLED}),
                       ("H12", {".claude/dev-loop.md": MAIN_MD + FIX_CLOSE,
                                **{f"e{i}/x.txt": "x\n" for i in range(1, 5)}, "x.zz": "x\n", "_build/x.txt": "x\n"}),
                       ("H13", {".claude/dev-loop.md": MAIN_MD + FIX_CLOSE, "ok.txt": "o\n"}),
                       ("H14", {".claude/dev-loop.md": MAIN_MD + NO_VALUE, "ok.txt": "o\n"}),
                       ("Y2", {".claude/dev-loop.md": MAIN_MD + "不在で止める範囲: a.txt\n"})):
        git(repo, "reset", "-q", "--hard", s["MM"])
        s[key] = commit(repo, f"touch {key}", files)
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


MAIN_MD = ("# 追補\n\nマージの反映: ドキュメントとプラグインの配布\n\n```text\nマージの反映: ドキュメントのみ\n"
           "不在で止める範囲: a.txt\n```\n\n"
           "<!--\nマージの反映: ドキュメントのみ\n不在で止める範囲: a.txt\n-->\n\n"
           "不在で止める範囲: risky/\n不在で止める範囲: m.txt\n")
JP_DECL = "不在で止める範囲: docs/設計/\n"
PARTICLES_DOC = "はをがものにでとや"  # check-gates.py の docstring の 9 つ（#1148 F5）
PROSE = "\n不在で止める範囲は risky/ と m.txt にしている。\n" + "".join(
    f"不在で止める範囲{p}説明の行（{p}）。\n" for p in PARTICLES_DOC)
DECORATED = ("\n**不在で止める範囲:** dir1/\n**不在で止める範囲**: dir2/\n## 不在で止める範囲: dir3/\n"
             "> 不在で止める範囲: dir4/\n- [ ] 不在で止める範囲: dir5/\n不在で止める範囲：dir6/\n"
             "- 不在で止める範囲: dir7/\n__不在で止める範囲__: dir8/\n- [x] 不在で止める範囲: dir9/\n- [X] 不在で止める範囲: dir10/\n")
# F1（#1148）: 強調の閉じがコロンの内側にある宣言。最後は、開いた強調の後にコロン・空白・`*.zz`（glob）と続く形（閉じではない）
FIX_CLOSE = ("\n*不在で止める範囲:* e1/\n**不在で止める範囲:**e2/\n_不在で止める範囲:_ e3/\n__不在で止める範囲:__ e4/\n"
             "*不在で止める範囲: *.zz\n_不在で止める範囲:_build/\n")
# F2（#1148）: 値の無い宣言
NO_VALUE = "\n**不在で止める範囲:**\n*不在で止める範囲:*\n"
MISSPELLED = ("\n不在で止める範囲 risky/\n不在で止める範囲=risky/\n不在で止める範囲、つまり risky/ のこと\n")
TABLE = ("## 受入基準（不変条件 × 経路）\n\n| # | 不変条件 | 守り方 |\n| --- | --- | --- |\n"
         "| A1 | x | y |\n| **A2** | x | y |\n\n## ほか\n\n| # | 受入基準ではない |\n| --- | --- |\n| Z9 | z |\n")
CRIT = ["受入基準: A1 満たす", "受入基準: A2 未証明"]
FULL = ["周の base: {B}", "関門: Verifier 1 {C1} 反証=2", "関門: /code-review 1 {C1} 指摘=5",
        "関門: Verifier 2 {C2} 反証=1", "関門: /code-review 2 {C2} 指摘=3", "関門: 狭いパス {C2} {C3} 反証=0"]
REFL = "マージの反映: ドキュメントとプラグインの配布"
ONE_PASS = ["周の base: {B}", "関門: Verifier 1 {C1} 反証=0", "関門: /code-review 1 {C1} 指摘=0",
            "関門: 狭いパス 該当なし"]


def plan_text(lines, crit=CRIT, table=TABLE, block=True, extra="", title="# Issue #1\n") -> str:
    body = "\n".join([*lines, *crit])
    fence = f"```dev-loop-gates\n# 関門の記録\n{body}\n```\n" if block else ""
    return f"{title}\n```bash\n周の base: 読まない\n```\n\n{table}\n## 関門の記録\n\n{fence}{extra}"


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
    "不在の周では満たさないを線（マージ前の判断（後退・未達を含む））で通す（#1176）":
        (FULL + ["マージの反映: ドキュメントとプラグインの配布"], "MM", 0, ["--absent"],
         {"crit": ["受入基準: A1 満たさない 判断=マージ前の判断（後退・未達を含む）", "受入基準: A2 満たす"]}),
    "満たさないを線（マージ前の判断（後退・未達を含む））で通すのは不在の周だけ（#1176）":
        (FULL, "MM", 3, [], {"crit": ["受入基準: A1 満たさない 判断=マージ前の判断（後退・未達を含む）", "受入基準: A2 満たす"]}, "--absent"),
    "不在の周では BLOCKED を線（マージ前の判断（後退・未達を含む））でも通す（#1176）":
        (FULL + ["マージの反映: ドキュメントとプラグインの配布"], "MM", 0, ["--absent"],
         {"crit": ["受入基準: A1 BLOCKED 判断=マージ前の判断（後退・未達を含む）", "受入基準: A2 満たす"]}),
    "満たさないを線（実機確認）で通さない（不在の周でも。#1176 の後も）":
        (FULL + ["マージの反映: ドキュメントとプラグインの配布"], "MM", 3, ["--absent"],
         {"crit": ["受入基準: A1 満たさない 判断=実機確認", "受入基準: A2 満たす"]}, "利用者の指示だけ"),
    "満たさないは利用者の指示（日付）で通す":
        (FULL, "MM", 0, [], {"crit": ["受入基準: A1 満たさない 判断=利用者の指示（2026-11-16）", "受入基準: A2 満たす"]}),
    "日付の無い利用者の指示は読めない出所":
        (FULL, "MM", 3, [], {"crit": ["受入基準: A1 BLOCKED 判断=利用者の指示", "受入基準: A2 満たす"]}, "読めない"),
    "マージの反映の記録が既定ブランチの宣言と違えば非 0":
        (FULL + ["マージの反映: ドキュメントのみ"], "MM", 3, [], {}, "既定ブランチ"),
    "不在の周でマージの反映の記録が無ければ非 0":
        (FULL, "MM", 3, ["--absent"], {}, "マージの反映の記録が無い"),
    "「なし」と記録しても、既定ブランチに宣言があれば非 0":
        (FULL + ["マージの反映: なし"], "MM", 3, ["--absent"], {}, "既定ブランチ"),
    "ブランチにだけ足した宣言は効かない（既定ブランチから読む）":
        (FULL + ["関門: 当て直し {MM} {Y} 反証=0", "マージの反映: ドキュメントのみ"], "Y", 3, [], {}, "既定ブランチ"),
    "周の base が既定ブランチに入っていなければ非 0（base を周の線の上にずらす）":
        (["周の base: {C1}"] + FULL[1:], "MM", 3, [], {}, "既定ブランチ"),
    "版の行の後ろに文を足したコミットは非 0":
        (FULL, "Z1", 3, [], {}, "banner with more text"),
    "plugin.json・marketplace.json でない version の行だけの変更は非 0":
        (FULL, "Z2", 3, [], {}, "version of another file"),
    "2 パス目が該当なしなら、狭いパスで 1 パス目の後の直しを覆えない":
        (["周の base: {B}", "関門: Verifier 1 {C1} 反証=0", "関門: /code-review 1 {C1} 指摘=0",
          "関門: 2 パス目 該当なし {C1}", "関門: 狭いパス {C1} {C2} 反証=0"], "C2", 3, [], {}, "該当なし"),
    "受入基準の番号が重複していれば 2":
        (FULL, "MM", 2, [], {"table": TABLE + "\n## 受入基準（2 つ目の Issue）\n\n| # | x |\n| --- | --- |\n| A1 | x |\n"}, "重複"),
    "題（#）に「受入基準」があっても、文書全体を受入基準の節と読まない":
        (FULL, "MM", 0, [], {"title": "# Issue #1 — 受入基準を照合する\n\n| # | 指摘 |\n| --- | --- |\n| CR1 | x |\n"}),
    "判断に空白を含んでも読める":
        (FULL, "MM", 0, [], {"crit": ["受入基準: A1 BLOCKED 判断=利用者の指示（2026-11-16 Slack で）", "受入基準: A2 満たす"]}),
    "受入基準の節の下位の見出しの下の表も読む":
        (FULL, "MM", 0, [], {"table": "## 受入基準\n\n### 表\n\n| # | x |\n| --- | --- |\n| A1 | x |\n| A2 | y |\n"}),
    # 影響範囲（#1047）
    "不在の周で、宣言した範囲（risky/ の配下）に当たる差分は非 0":
        (FULL + ["関門: 当て直し {MM} {R1} 反証=0", REFL], "R1", 3, ["--absent"], {}, "「不在で止める範囲: risky/」に当たる"),
    "居る周では、宣言した範囲に当たっても止めない":
        (FULL + ["関門: 当て直し {MM} {R1} 反証=0", REFL], "R1", 0, [], {}),
    "不在の周で、既定ブランチで戻したコミットが触ったファイルを変えた差分は非 0":
        (FULL + ["関門: 当て直し {MM} {R2} 反証=0", REFL], "R2", 3, ["--absent"], {}, "risky change"),
    "既定ブランチから辿れないコミットを戻した行（squash に残った revert）は数えない":
        (FULL + ["関門: 当て直し {MM} {R3} 反証=0", REFL], "R3", 0, ["--absent"], {}),
    "merge commit で入れた PR の中のコミットを main で戻したら、その範囲も不在の周で非 0":
        (FULL + ["関門: 当て直し {MM} {R4} 反証=0", REFL], "R4", 3, ["--absent"], {}, "inner change"),
    "周の差分が既定ブランチの範囲の宣言を外せば、不在の周で非 0":
        (FULL + ["関門: 当て直し {MM} {R5} 反証=0", REFL], "R5", 3, ["--absent"], {}, "不在で止める範囲: m.txt」を外す"),
    "読めない範囲の宣言（/ で始まる）は、不在の周で止める":
        (FULL + ["関門: 当て直し {MM} {H2} 反証=0", REFL], "H2", 3, ["--absent"], {"default": "M2"}, "読めない"),
    "箇条書きの印の付いた宣言は、宣言として読む（当たらない差分は止めない）":
        (FULL + ["関門: 当て直し {MM} {H4} 反証=0", REFL], "H4", 0, ["--absent"], {"default": "M4"}),
    "飾った宣言・全角のコロンの宣言は宣言として読み、当たらない差分は止めない（R1）":
        (FULL + ["関門: 当て直し {MM} {H9} 反証=0", REFL], "H9", 0, ["--absent"], {"default": "M8"}),
    "飾った宣言・全角のコロンの宣言に当たる差分は、それぞれ宣言に当たったと言って止める（R1）":
        (FULL + ["関門: 当て直し {MM} {H10} 反証=0", REFL], "H10", 3, ["--absent"], {"default": "M8"},
         *[f"「不在で止める範囲: dir{i}/」に当たる" for i in range(1, 11)]),
    "強調の閉じがコロンの内側にある宣言も宣言として読み、当たらない差分は止めない（F1）":
        (FULL + ["関門: 当て直し {MM} {H13} 反証=0", REFL], "H13", 0, ["--absent"], {"default": "M10"}),
    "強調の閉じがコロンの内側にある宣言は、宣言したパターンで照合して止める（F1）":
        (FULL + ["関門: 当て直し {MM} {H12} 反証=0", REFL], "H12", 3, ["--absent"], {"default": "M10"},
         *[f"「不在で止める範囲: e{i}/」に当たる" for i in range(1, 5)], "「不在で止める範囲: *.zz」に当たる", "「不在で止める範囲: _build/」に当たる"),
    "値の無い宣言は、読めない宣言として名指して止める（全部に当たったとは言わない。F2）":
        (FULL + ["関門: 当て直し {MM} {H14} 反証=0", REFL], "H14", 3, ["--absent"], {"default": "M11"},
         "「**不在で止める範囲:**」", "「*不在で止める範囲:*」", "形で読めない"),
    "コロン抜け・=・読点の書き損じは、読めない宣言として止める（R1）":
        (FULL + ["関門: 当て直し {MM} {H11} 反証=0", REFL], "H11", 3, ["--absent"], {"default": "M9"},
         "「不在で止める範囲 risky/」", "「不在で止める範囲=risky/」", "「不在で止める範囲、つまり risky/ のこと」"),
    "分岐の後に既定ブランチへ足された範囲の宣言を、周が外したと読まない":
        (FULL + [REFL], "MM", 0, ["--absent"], {"default": "M5"}),
    "非 ASCII のパスの宣言に当たらない差分は、不在の周でも止めない（J1）":
        (FULL + ["関門: 当て直し {MM} {H6} 反証=0", REFL], "H6", 0, ["--absent"], {"default": "M6"}),
    "非 ASCII のパスの宣言に当たる差分は、宣言に当たったと言って止める（J1）":
        (FULL + ["関門: 当て直し {MM} {H7} 反証=0", REFL], "H7", 3, ["--absent"], {"default": "M6"},
         "「不在で止める範囲: docs/設計/」に当たる"),
    "キーワードを含むだけの散文の行では止めない（J2）":
        (FULL + ["関門: 当て直し {MM} {H8} 反証=0", REFL], "H8", 0, ["--absent"], {"default": "M7"}),
    "glob の文字の無い範囲の宣言は、配下にも当てる":
        (FULL + ["関門: 当て直し {MM} {H3} 反証=0", REFL], "H3", 3, ["--absent"], {"default": "M3"}, "不在で止める範囲: deepdir」に当たる"),
    "ブランチにだけ足した範囲の宣言は効かない（既定ブランチから読む）":
        (FULL + ["関門: 当て直し {MM} {Y2} 反証=0", REFL], "Y2", 0, ["--absent"], {}),
    "記録が無ければ 2": (FULL, "MM", 2, [], {"block": False}, "記録"),
    "記録が 2 つあれば 2": (FULL, "MM", 2, [], {"extra": "\n```dev-loop-gates\n周の base: {B}\n```\n"}, "2 つ"),
    "読めない行があれば 2": (FULL + ["関門: Verifier 1 {C1}"], "MM", 2, [], {}, "読めない行"),
    "受入基準の表が無ければ 2": (FULL, "MM", 2, [], {"table": "## 受入基準\n\n- A1 x\n"}, "受入基準の表"),
    "判定の値が読めなければ 2": (FULL, "MM", 2, [], {"crit": ["受入基準: A1 OK", "受入基準: A2 満たす"]}, "判定"),
    "head が解決しなければ 7": (FULL, "nosuch", 7, [], {}),
}


def run(script: Path, repo: Path, s: dict, name: str, case) -> tuple[int, str]:
    lines, head, _rc, args, kw, *_ = case
    kw = dict(kw)
    default = kw.pop("default", None)  # 既定ブランチ（origin/main）をこのケースだけ差し替える
    if default:
        git(repo, "update-ref", "refs/remotes/origin/main", s[default])
    try:
        return _run(script, repo, s, lines, head, args, kw)
    finally:
        if default:
            git(repo, "update-ref", "refs/remotes/origin/main", s["M"])


def _run(script: Path, repo: Path, s: dict, lines, head, args, kw) -> tuple[int, str]:
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
    # 守る（追加）: 2 パス目が該当なしなら狭いパスの記録を通さない
    "該当なしと狭いパスを一緒に通す": ("if rec.pass2_none and rec.narrow:", "if False:"),
    # 守る（追加）: 受入基準の番号の重複
    "番号の重複を見ない": ("    if dup:\n", "    if False:\n"),
    # 守る（追加）: コードブロック・コメントの中の行・読めない値・2 本以上を宣言と読まない
    "宣言を素の行で読む": ('return _visible_lines()(text.lstrip("\\ufeff"))', "return text.splitlines()"),
    # 守る 8: 周の base が既定ブランチに入っていない
    "base を既定ブランチと照らさない": ("if not ctx.is_ancestor(base, default):", "if False:"),
    # 守る 9: 関門が見ていないコミット
    "見ていないコミットを通す": ("if seen or exempt(ctx, commit, parents):", "if True:"),
    # 守る 10: 起点そのものを数えない
    "起点を範囲に数える": ("commit != s and ", ""),
    # 守る 11: 計画と版の行だけは通す
    "計画だけのコミットを通さない": ("if f == ctx.plan_rel:", "if False:"),
    # 守る 12: 既定ブランチ以外の取り込み
    "どの枝の取り込みも通す": ("return all(ctx.is_ancestor(p, default) for p in parents[1:])", "return True"),
    # 守る 13: 表の番号に判定
    "判定の無い番号を見ない": ("if i not in rec.criteria:", "if False:"),
    # 守る 14: 判断の出所
    "判断の出所が無くても通す": ('reasons.append(f"受入基準 {i} が {verdict} で、判断の出所（判断=）が無い")', "continue"),
    # 守る 15: 満たさないを線で通さない
    "満たさないを線で通す": ('elif verdict == "満たさない" and judge not in UNMET_JUDGES:', "elif False:"),
    # 守る（#1176）: 満たさないを線 マージ前の判断（後退・未達を含む） で通すのは --absent のときだけ（通すこと自体も）
    "満たさないを後退・未達を含む線でも通さない": ('UNMET_JUDGES = ("マージ前の判断（後退・未達を含む）",)', 'UNMET_JUDGES = ("",)'),
    # 守る 16: 不在の周でなければ線を通さない
    "居る周でも線を通す": ("elif not ctx.absent:", "elif False:"),
    # 守る 17: マージの反映が違う
    "マージの反映を既定ブランチと比べない": ("if value != rec.reflection:", "if False:"),
    # 守る 18: 宣言は既定ブランチから読む
    "宣言を head から読む": ('ctx.git("show", f"{ctx.default_ref()}:.claude/dev-loop.md", ok=(0, 128))',
                         'ctx.git("show", f"{ctx.head}:.claude/dev-loop.md", ok=(0, 128))'),
    # 守る 19: 不在の周で記録が無い
    "不在の周でもマージの反映の記録を求めない": (
        'return ["不在の周で、マージの反映の記録が無い"] if ctx.absent else []', "return []"),
    # 守る（#1047）: 宣言した範囲に当たる差分を不在の周で通さない
    "宣言した範囲を見ない": ("        if hit:\n", "        if False:\n"),
    # 守る（#1047）: / で終わるパターンは配下すべて
    "/ で終わるパターンを配下に当てない": ('return fnmatch.fnmatchcase(path, pattern + "*")',
                                     "return fnmatch.fnmatchcase(path, pattern)"),
    # 守る（#1047）: 戻した範囲に当たる差分を不在の周で通さない
    "戻した範囲を見ない": ("        if f in rolled:\n", "        if False:\n"),
    # 守る（#1047）: main の線に無いコミットを戻した行を数えない
    "辿れないコミットを戻した行も数える": ("if not full or not ctx.is_ancestor(full, default):", "if not full:"),
    # 守る（#1047）: merge commit で入れたコミットを戻した行も数える
    "最初の親の線にあるものだけ数える": ("if not full or not ctx.is_ancestor(full, default):",
                                 'if not full or full not in ctx.git("rev-list", "--first-parent", default).stdout.split():'),
    # 守る（#1047）: 読めない宣言を黙って捨てない
    "当たらない宣言を捨てる": ("            if not any(matches(f, pat) for f in paths):\n", "            if False:\n"),
    # 守る（#1047 R1）: 書き損じを黙って捨てない
    "書き損じを捨てる": ('    return "bad", line.strip()\n', '    return "skip", None\n'),
    # 守る（#1047 J2）: 助詞が続く行は散文
    "助詞の行も書き損じと読む": ("    if rest and rest[0] in PARTICLES:\n", "    if False:\n"),
    # 守る（#1047 R1）: 行頭の飾りを外してから読む
    "飾りを外さない": ("        m = DECOR.match(s)\n", "        m = None\n"),
    # 守る（#1047 R1）: 全角のコロンも宣言
    "全角のコロンを読まない": ('COLONS = (":", "：")', 'COLONS = (":",)'),
    # 守る（#1148 F1）: 強調の閉じがコロンの内側にある宣言も宣言として読む
    "強調の閉じがコロンの内側にある宣言を読まない": ("        if mark and after.startswith(mark) and (", "        if False and ("),
    # 守る（#1148 F2）: 値の無い宣言を `**` のパターンと読まない
    "値の無い宣言をパターンと読む": ('        if value:\n            return "pattern", value\n', '        return "pattern", value\n'),
    # 守る（#1047 J1）: パスは引用符なしで読む
    "パスを引用符つきで読む": ('["git", "-c", "core.quotePath=false", *args]', '["git", *args]'),
    # 守る（#1047）: 分岐の後に足された宣言を外したと読まない
    "後から足された宣言を外したと読む": ("if pat in at_fork and pat not in kept:", "if pat not in kept:"),
    # 守る（#1047）: glob の文字の無いパターンは配下にも当てる
    "glob の無いパターンを配下に当てない": ('return path == pattern or path.startswith(pattern + "/")', "return path == pattern"),
    # 守る（#1047）: 範囲の宣言を外す差分を通さない
    "宣言を外す差分を通す": ("if pat in at_fork and pat not in kept:", "if False:"),
    # 守る（#1047）: 差分は既定ブランチとの分岐点から
    "差分を周の base から取る": ('fork = ctx.git("merge-base", default, ctx.head).stdout.strip()', "fork = rec.base"),
    # 守る（#1047）: 居る周では影響範囲で止めない
    "居る周でも影響範囲で止める": ("    if not ctx.absent:\n        return []\n    default", "    default"),
    # 守る 20: 判定できないことを通過と答えない
    "判定できないを通過と答える": (
        'print(f"**判定できなかった**: {e}", file=sys.stderr)\n        return 7',
        'print(f"**判定できなかった**: {e}", file=sys.stderr)\n        return 0'),
}

# 1 つの「守る」の中の要素ごとの変異（#1148 F5）。「守る」の行とは 1 対 1 にしない——要素の数は docstring の列挙から数える
EXTRA_MUTATIONS = {
    **{f"助詞「{p}」を外す": ('PARTICLES = "' + PARTICLES_DOC + '"', 'PARTICLES = "' + PARTICLES_DOC.replace(p, "") + '"')
       for p in PARTICLES_DOC},
    "閉じの後が空白でも行末でもない形も閉じと読む（`_…:_build/` の先頭の `_` を食う）": (
        'mark == "**" or tail == "" or tail[0].isspace()', "True"),
    "チェックボックス `[ ]` を外す": (r"\[[ xX]\]", r"\[[xX]\]"),
    "チェックボックス `[x]` を外す": (r"\[[ xX]\]", r"\[[ X]\]"),
    "チェックボックス `[X]` を外す": (r"\[[ xX]\]", r"\[[ x]\]"),
}

KILLS = {
    "閉じの後が空白でも行末でもない形も閉じと読む（`_…:_build/` の先頭の `_` を食う）": [
        "強調の閉じがコロンの内側にある宣言は、宣言したパターンで照合して止める（F1）"],
    **{f"助詞「{p}」を外す": ["キーワードを含むだけの散文の行では止めない（J2）"] for p in PARTICLES_DOC},
    **{f"チェックボックス `[{c}]` を外す": ["飾った宣言・全角のコロンの宣言に当たる差分は、それぞれ宣言に当たったと言って止める（R1）"]
       for c in (" ", "x", "X")},
    "強調の閉じがコロンの内側にある宣言を読まない": ["強調の閉じがコロンの内側にある宣言も宣言として読み、当たらない差分は止めない（F1）",
                                 "強調の閉じがコロンの内側にある宣言は、宣言したパターンで照合して止める（F1）"],
    "値の無い宣言をパターンと読む": ["値の無い宣言は、読めない宣言として名指して止める（全部に当たったとは言わない。F2）"],
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
    "満たさないを線で通す": ["満たさないを線で通さない（不在の周でも）",
                           "満たさないを線（実機確認）で通さない（不在の周でも。#1176 の後も）"],
    "満たさないを後退・未達を含む線でも通さない": ["不在の周では満たさないを線（マージ前の判断（後退・未達を含む））で通す（#1176）"],
    "居る周でも線を通す": ["BLOCKED を線（マージ前の判断）で通すのは不在の周だけ",
                         "満たさないを線（マージ前の判断（後退・未達を含む））で通すのは不在の周だけ（#1176）"],
    "マージの反映を既定ブランチと比べない": ["マージの反映の記録が既定ブランチの宣言と違えば非 0",
                               "「なし」と記録しても、既定ブランチに宣言があれば非 0"],
    "宣言を head から読む": ["ブランチにだけ足した宣言は効かない（既定ブランチから読む）",
                         "ブランチにだけ足した範囲の宣言は効かない（既定ブランチから読む）"],
    "宣言した範囲を見ない": ["不在の周で、宣言した範囲（risky/ の配下）に当たる差分は非 0"],
    "/ で終わるパターンを配下に当てない": ["不在の周で、宣言した範囲（risky/ の配下）に当たる差分は非 0"],
    "戻した範囲を見ない": ["不在の周で、既定ブランチで戻したコミットが触ったファイルを変えた差分は非 0"],
    "辿れないコミットを戻した行も数える": ["既定ブランチから辿れないコミットを戻した行（squash に残った revert）は数えない"],
    "最初の親の線にあるものだけ数える": ["merge commit で入れた PR の中のコミットを main で戻したら、その範囲も不在の周で非 0"],
    "当たらない宣言を捨てる": ["読めない範囲の宣言（/ で始まる）は、不在の周で止める"],
    "書き損じを捨てる": ["コロン抜け・=・読点の書き損じは、読めない宣言として止める（R1）"],
    "飾りを外さない": ["飾った宣言・全角のコロンの宣言に当たる差分は、それぞれ宣言に当たったと言って止める（R1）"],
    "全角のコロンを読まない": ["飾った宣言・全角のコロンの宣言は宣言として読み、当たらない差分は止めない（R1）"],
    "後から足された宣言を外したと読む": ["分岐の後に既定ブランチへ足された範囲の宣言を、周が外したと読まない"],
    "助詞の行も書き損じと読む": ["キーワードを含むだけの散文の行では止めない（J2）"],
    "パスを引用符つきで読む": ["非 ASCII のパスの宣言に当たらない差分は、不在の周でも止めない（J1）",
                          "非 ASCII のパスの宣言に当たる差分は、宣言に当たったと言って止める（J1）"],
    "glob の無いパターンを配下に当てない": ["glob の文字の無い範囲の宣言は、配下にも当てる"],
    "宣言を外す差分を通す": ["周の差分が既定ブランチの範囲の宣言を外せば、不在の周で非 0"],
    "差分を周の base から取る": ["不在の周では BLOCKED を線（マージ前の判断）で通す"],
    "居る周でも影響範囲で止める": ["居る周では、宣言した範囲に当たっても止めない"],
    "該当なしと狭いパスを一緒に通す": ["2 パス目が該当なしなら、狭いパスで 1 パス目の後の直しを覆えない"],
    "番号の重複を見ない": ["受入基準の番号が重複していれば 2"],
    "宣言を素の行で読む": ["不在の周では BLOCKED を線（マージ前の判断）で通す"],  # コードブロック・コメントの中の a.txt
    "base を既定ブランチと照らさない": ["周の base が既定ブランチに入っていなければ非 0（base を周の線の上にずらす）"],
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

        print("\n判定できない: 既定ブランチの追跡参照が無ければ 7（base が既定ブランチに入っているかを決められない）")
        git(repo, "update-ref", "-d", "refs/remotes/origin/main")
        rc, out = run(SCRIPT, repo, s, "", (FULL, "MM", 7, [], {}))
        check(f"取り込みがあり、origin の参照が無い: rc={rc}（期待 7）", rc == 7 and "既定ブランチ" in out)
        rc, out = run(SCRIPT, repo, s, "", (FULL[:5] + ["関門: 狭いパス {C2} {C3} 反証=0"], "C3", 7, [], {}))
        check(f"取り込みが無くても、origin の参照が無ければ 7: rc={rc}（期待 7）", rc == 7 and "既定ブランチ" in out)
        git(repo, "update-ref", "refs/remotes/origin/main", s["M"])

        print("\n判定できない: UTF-8 でない計画は 7（traceback の 1 にしない）")
        bad = repo / PLAN_REL
        bad.write_bytes(b"\xff\xfe# plan\n")
        r = subprocess.run([sys.executable, str(SCRIPT), str(bad)], cwd=str(repo), capture_output=True, text=True, env=ENV)
        check(f"UTF-8 でない計画: rc={r.returncode}（期待 7）", r.returncode == 7 and "Traceback" not in r.stderr)

        print("\n変異（壊したのに期待どおりなら失格）")
        if failures:
            print("  陽性対照が落ちているので、変異の結果は読まない")
        else:
            for i, (mname, (old, new)) in enumerate({**MUTATIONS, **EXTRA_MUTATIONS}.items()):
                check(f"変異の当て先が 1 箇所だけ在る: {mname}", source.count(old) == 1)
                mutant = base / f"mutant{i}" / "check-gates.py"
                mutant.parent.mkdir(parents=True)
                mutant.write_text(source.replace(old, new, 1), encoding="utf-8")
                (mutant.parent / "check-unattended-env.py").write_text(  # 宣言を読むのに読み込む
                    (SCRIPT.parent / "check-unattended-env.py").read_text(encoding="utf-8"), encoding="utf-8")
                for t in KILLS[mname]:
                    rc, out = run(mutant, repo, s, t, CASES[t])
                    check(f"{mname} → 赤（{t}: rc={rc}）", not as_expected(CASES[t], rc, out))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        doc = docstring(source)
        section = doc.split("## 何を守るか")[1].split("## 終了コード")[0]
        promises = len([l for l in section.splitlines() if l.startswith("- ")])
        check(f"「守る」{promises} 行に対して変異が {len(MUTATIONS)} 件", promises == len(MUTATIONS))
        check("どの変異にも、赤になるはずの試料がある", all(KILLS.get(m) for m in {**MUTATIONS, **EXTRA_MUTATIONS}))
        listed = re.search(r"助詞（([^）]*)）", doc).group(1).split("・")
        in_src = re.search(r'^PARTICLES = "([^"]*)"', source, re.M).group(1)
        check(f"助詞は docstring の {len(listed)} 個と本体の PARTICLES が同じで、重複が無い（同じ文字を 2 度書くと外す変異が等価になる）",
              len(listed) == 9 and sorted(listed) == sorted(in_src) and len(set(in_src)) == len(in_src) and in_src == PARTICLES_DOC)
        check("助詞の変異は docstring の助詞の数と同じ", len([m for m in EXTRA_MUTATIONS if m.startswith("助詞")]) == len(listed))

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
