#!/usr/bin/env python3
"""`line-effects.py`（委譲文の行の台帳と、最後に効いた周の集計）と `check-prompt-lines.py`（行を外す PR の歯止め）の回帰テスト（#1194）。

    python3 scripts/test-line-effects.py

**本体は 2 つ**——プラグインの `plugins/dev-loop/skills/dev-loop/scripts/line-effects.py` と、`scripts/check-prompt-lines.py`（`test-find-cycle.py` と同じ形）。
**試料はすべて一時ディレクトリに書く**（一時の git リポジトリは `HOME`・`GIT_CONFIG_GLOBAL` を差し替える）。実環境・本物の台帳は変えない。

見るもの:

1. **台帳と原文の整合（`check`）**——台帳どおりなら 0。未登録の項・引きが 0 回／2 回・引きが項の頭に当たらない・コードブロックの中の項（数えない）・
   `{{` の穴（数えない）・台帳のヘッダ違い（2）。
2. **集計（`report`）**——一時の git リポジトリで、周の順を**コミットの時刻**で決める（名前順と食い違う試料）。最後に効いた周・効いていない周数・候補の線（窓と同じ値の境界）・
   登録日より前の周を数えない・一度も効かない行・同趣旨の組。形に合わない記録（装飾つき・`なし` と ID の混在）は名指しして 1。コードブロックの中の記録は読まない。
3. **行を外す PR（`check-prompt-lines.py`）**——外した行に eval が無ければ 1、`外した行`・`元の事故`・`graders` が揃う eval が**差分に**あれば 0、
   元の事故の番号が欠ける・eval が base に既にあって差分に無い・graders が無い、は 1。同趣旨の行への統合は eval を求めず、同趣旨が違えば 1。
   台帳の無い base は飛ばし、解決できない base は 2。**陽性対照**: 同じ試料で eval を足すと 0 になる（0 は 1 の試料の差だけで決まる）。
4. **原本との突き合わせ**——本物の台帳が 0 で通る・`references/prune.md` の記録の例が本体の正規表現に当たる・「削らない」が「黙って削らない」に置き換わっている。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、名指しした試料が期待から外れることを確かめる。変異ごとに、壊す箇所が本体にちょうど 1 回現れること・変異の前は期待どおりであることを先に確かめる。
"""
from __future__ import annotations

import csv
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_REL = "plugins/dev-loop/skills/dev-loop"
EFFECTS_SRC = REPO / SKILL_REL / "scripts" / "line-effects.py"
GUARD_SRC = REPO / "scripts" / "check-prompt-lines.py"
HEADER = ["ID", "ファイル", "引き", "元の事故", "登録日", "同趣旨", "統合元"]

PROMPT = """# 試料

**使い方**: 説明。

---

## とくに見てほしいこと

1. **AAA ひとつめの行です**
   - 入れ子は数えない
2. **BBB ふたつめの行です**
- {{穴は数えない}}

## 報告の形

- **CCC みっつめの行です**
"""


def registry_text(rows: list[list[str]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(HEADER)
    w.writerows(rows)
    return buf.getvalue()


ROWS = [
    ["V-01", "prompts/verifier.md", "**AAA ひとつめ", "#10", "2026-01-01", "t", ""],
    ["V-02", "prompts/verifier.md", "**BBB ふたつめ", "-", "2026-01-01", "t", ""],
    ["V-03", "prompts/verifier.md", "**CCC みっつめ", "#30;#31", "2026-01-01", "", ""],
]


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def git_env(home: Path, when: str | None = None) -> dict:
    e = {**os.environ, "HOME": str(home), "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"), "GIT_CONFIG_SYSTEM": "/dev/null",
         "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
         "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    if when:
        e["GIT_AUTHOR_DATE"] = e["GIT_COMMITTER_DATE"] = when
    return e


class Tree:
    """一時の skill ディレクトリ（`scripts/line-effects.py`・`prompts/verifier.md`・台帳）。"""

    def __init__(self, tmp: Path, effects_text: str | None = None, prompt: str = PROMPT, rows=None):
        self.skill = tmp / "skill"
        (self.skill / "scripts").mkdir(parents=True)
        (self.skill / "prompts").mkdir()
        (self.skill / "references").mkdir()
        (self.skill / "scripts" / "line-effects.py").write_text(effects_text or EFFECTS_SRC.read_text())
        (self.skill / "prompts" / "verifier.md").write_text(prompt)
        (self.skill / "references" / "line-registry.csv").write_text(registry_text(ROWS if rows is None else rows))

    def run(self, *args: str, env=None) -> subprocess.CompletedProcess:
        return run([sys.executable, "-I", str(self.skill / "scripts" / "line-effects.py"), *args], env=env)


def case_check(effects_text: str | None = None) -> list[str]:
    """台帳と原文の整合（check）の試料。失敗の説明を返す。"""
    bad: list[str] = []
    def expect(label, tree: Tree, rc: int, word: str = "", args=("check",)):
        r = tree.run(*args)
        if r.returncode != rc or (word and word not in r.stdout + r.stderr):
            bad.append(f"{label}: rc={r.returncode}（期待 {rc}）{(r.stdout + r.stderr).strip()[:160]}")
    with tempfile.TemporaryDirectory(prefix="line-effects-") as t:
        t = Path(t)
        def tree(name, **kw):
            d = t / name
            d.mkdir()
            return Tree(d, effects_text, **kw)
        expect("C1 台帳どおりなら 0", tree("c1"), 0, "OK")
        expect("C2 未登録の項は 1", tree("c2", prompt=PROMPT + "- **DDD よっつめの行です**\n"), 1, "台帳に無い項")
        expect("C3a 引きが 0 回なら 1", tree("c3a", prompt=PROMPT.replace("BBB ふたつめ", "BBB ふたつ")), 1, "0 回")
        expect("C3b 引きが 2 回なら 1", tree("c3b", prompt=PROMPT + "\n追記: **AAA ひとつめの行です**\n"), 1, "2 回")
        expect("C4 引きが項の頭に当たらなければ 1",
               tree("c4", prompt=PROMPT.replace("2. **BBB ふたつめの行です**", "2. 前置き **BBB ふたつめの行です**")), 1, "項の頭")
        fenced = PROMPT + "\n```\n- **EEE コードブロックの中の項**\n```\n"
        expect("C6 コードブロックの中の項は数えない", tree("c6", prompt=fenced), 0, "OK")
        d = t / "c7"
        d.mkdir()
        tr = Tree(d, effects_text)
        (tr.skill / "references" / "line-registry.csv").write_text("ID,ファイル\nV-01,x\n")
        expect("C7 ヘッダ違いは 2", tr, 2, "ヘッダ")
        expect("C8 空の台帳は未登録の項で 1", tree("c8", rows=[]), 1, "台帳に無い項")
        d = t / "c9"
        d.mkdir()
        tr = Tree(d, effects_text)
        bad_rows = ROWS + [["V-01"] + ROWS[0][1:]]
        (tr.skill / "references" / "line-registry.csv").write_text(registry_text(bad_rows))
        expect("C9 ID の重複は 2", tr, 2, "重複")
    return bad


def make_plans(tmp: Path, specs: list[tuple[str, str, str]]) -> Path:
    """一時の git リポジトリに計画ファイルを日付つきでコミットする。specs: (ファイル名, 日付, 本文)。"""
    repo = tmp / "plans-repo"
    (repo / "docs" / "plans").mkdir(parents=True)
    home = tmp / "home"
    home.mkdir()
    (home / ".gitconfig").write_text("")
    run(["git", "init", "-q", "-b", "main", str(repo)], env=git_env(home))
    for name, when, body in specs:
        (repo / "docs" / "plans" / name).write_text(body)
        run(["git", "-C", str(repo), "add", "."], env=git_env(home))
        r = run(["git", "-C", str(repo), "commit", "-q", "-m", name], env=git_env(home, when))
        assert r.returncode == 0, r.stderr
    return repo / "docs" / "plans"


def rec(*ids: str) -> str:
    return "# 計画\n\n" + "".join(f"- 効いた行: {i}\n" for i in ids) + "\n- この周の起票: 0 件\n"


def case_report(effects_text: str | None = None) -> list[str]:
    bad: list[str] = []
    def expect(label, r, rc, *has, absent=()):
        out = r.stdout + r.stderr
        miss = [w for w in has if w not in out]
        extra = [w for w in absent if w in out]
        if r.returncode != rc or miss or extra:
            bad.append(f"{label}: rc={r.returncode}（期待 {rc}）欠け={miss} 余計={extra}\n{out[:600]}")
    with tempfile.TemporaryDirectory(prefix="line-effects-rep-") as t:
        t = Path(t)
        tr = Tree(t / "k", effects_text)  # 台帳 3 行（登録日 2026-01-01）
        # R1 周の順はコミットの時刻（名前順と食い違う）: z.md が最初・a.md が 2 番目・b.md が 3 番目
        plans = make_plans(t / "r1", [("z.md", "2026-02-01T00:00:00Z", rec("V-01")),
                                      ("a.md", "2026-02-02T00:00:00Z", rec("V-01")),
                                      ("b.md", "2026-02-03T00:00:00Z", rec("なし")),
                                      ("n.md", "2026-02-04T00:00:00Z", "# 記録の行の無い周\n")])
        r = tr.run("report", str(plans), "--window", "1")
        expect("R1 最後に効いた周は時刻順で a.md（名前順なら z.md）・効いていない周数 1・窓と同じ値は候補", r, 0,
               "記録のある周: 3（記録の行が無い計画ファイル: 1）", "V-01\t2\ta.md\t1\t", "最後に効いた周 a.md の後、記録のある 1 周で効いていない")
        r = tr.run("report", str(plans), "--window", "2")
        expect("R2 窓が 1 大きければ V-01 は候補でない（境界）・一度も効かない V-02 は 3 周で候補", r, 0,
               "V-02\t0\t-\t3\t", "登録日 2026-01-01 以降の記録のある 3 周で 0 回", absent=("V-01（",))
        r = tr.run("report", str(plans), "--window", "1")
        expect("R3 同趣旨 t の組が出る", r, 0, "まとめる候補（同趣旨が 2 行以上）: 1 組", "t: V-01 V-02")
        # R4 登録日より前の周は分母に入れない
        d = t / "late"
        d.mkdir()
        late = Tree(d, effects_text, rows=[["V-02"] + ROWS[1][1:4] + ["2026-02-03", "", ""]] + [ROWS[0], ROWS[2]])
        r = late.run("report", str(plans), "--window", "1")
        expect("R4 登録日 2026-02-03 より前の周を数えない（V-02 は b.md の 1 周だけ）", r, 0, "V-02\t0\t-\t1\t")
        # R5 台帳に無い ID
        plans2 = make_plans(t / "r5", [("p.md", "2026-02-01T00:00:00Z", rec("V-01", "X-99"))])
        r = tr.run("report", str(plans2))
        expect("R5 台帳に無い ID は注記して 0", r, 0, "台帳に無い ID（外した行か綴りの誤り）: X-99")
        # R6 形に合わない記録
        plans3 = make_plans(t / "r6", [("p.md", "2026-02-01T00:00:00Z", "- 効いた行: V-01\n- **効いた行: V-02**\n"),
                                       ("q.md", "2026-02-02T00:00:00Z", "- 効いた行: なし\n- 効いた行: V-03\n"),
                                       ("f.md", "2026-02-03T00:00:00Z", "```\n- 効いた行: V-99!!\n```\n- 効いた行: V-02\n")])
        r = tr.run("report", str(plans3))
        expect("R6 装飾つき・なしと ID の混在は名指しして 1、コードブロックの中は読まない", r, 1,
               "p.md:2 記録の行の形でない", "q.md `なし` と ID を同じファイルに書いている", absent=("f.md:", "V-99"))
        # R7 引数の誤り
        expect("R7a 計画ファイルが 1 本も無ければ 2", tr.run("report", str(t / "k" / "skill" / "references")), 2, "1 本も無い")
        expect("R7b 無いパスは 2", tr.run("report", str(t / "nosuch")), 2, "が無い")
        expect("R7c 窓が 0 は 2", tr.run("report", str(plans), "--window", "0"), 2, "1 以上")
        r = tr.run("items")
        expect("R8 登録済みなら items は何も出さない", r, 0, absent=("V-",))
        d = t / "items"
        d.mkdir()
        it = Tree(d, effects_text, prompt=PROMPT + "- **DDD よっつめの行です**\n")
        r = it.run("items")
        expect("R9 未登録の項は登録行の案として出る（ID は既存と重ならない）", r, 0, "prompts/verifier.md,**DDD よっつめ")
        if "V-01," in r.stdout.split("\n")[0] if r.stdout else False:
            bad.append("R9 ID が既存と重なった")
    return bad


def guard_repo(tmp: Path, guard_text: str | None, effects_text: str | None):
    """base（main）に台帳と原文があり、feat ブランチを切るリポジトリ。"""
    root = tmp / "repo"
    skill = root / SKILL_REL
    for d in ("scripts", "prompts", "references"):
        (skill / d).mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "plugins/dev-loop/evals").mkdir(parents=True)
    (skill / "scripts" / "line-effects.py").write_text(effects_text or EFFECTS_SRC.read_text())
    (root / "scripts" / "check-prompt-lines.py").write_text(guard_text or GUARD_SRC.read_text())
    (skill / "prompts" / "verifier.md").write_text(PROMPT)
    (skill / "references" / "line-registry.csv").write_text(registry_text(ROWS))
    home = tmp / "home"
    home.mkdir()
    (home / ".gitconfig").write_text("")
    env = git_env(home)
    def g(*a):
        r = run(["git", "-C", str(root), *a], env=env)
        assert r.returncode == 0, (a, r.stderr)
    run(["git", "init", "-q", "-b", "main", str(root)], env=env)
    return root, skill, g, env


def eval_case(line_id="V-02", incident="-", graders=True) -> str:
    return (f"schema_version: \"1.1\"\nname: x\n# 外した行: {line_id}\n# 元の事故: {incident}\n"
            + ("graders:\n  - name: g\n    type: tool_used\n" if graders else ""))


def remove_v02(skill: Path):
    (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("2. **BBB ふたつめの行です**\n", ""))
    (skill / "references" / "line-registry.csv").write_text(registry_text([r for r in ROWS if r[0] != "V-02"]))


def case_guard(guard_text: str | None = None, effects_text: str | None = None) -> list[str]:
    bad: list[str] = []
    def scenario(label, rc, word, setup, base_ref="main", pre_base=None):
        with tempfile.TemporaryDirectory(prefix="line-guard-") as t:
            root, skill, g, env = guard_repo(Path(t), guard_text, effects_text)
            if pre_base:
                pre_base(root, skill)
            g("add", "."), g("commit", "-q", "-m", "base")
            g("checkout", "-q", "-b", "feat")
            setup(root, skill)
            g("add", "-A"), g("commit", "-q", "--allow-empty", "-m", "feat")
            r = run([sys.executable, "-I", str(root / "scripts" / "check-prompt-lines.py"), base_ref], cwd=root, env=env)
            out = r.stdout + r.stderr
            if r.returncode != rc or (word and word not in out):
                bad.append(f"{label}: rc={r.returncode}（期待 {rc}）{out.strip()[:300]}")
    def add_eval(root, text, name="e1"):
        (root / "plugins/dev-loop/evals" / name).mkdir(parents=True, exist_ok=True)
        (root / "plugins/dev-loop/evals" / name / "case.yaml").write_text(text)
    def s_none(root, skill):
        pass
    scenario("G0 何も外さない PR は 0", 0, "外した行 0 件", s_none)
    def s_no_eval(root, skill):
        remove_v02(skill)
    scenario("G1 行を外したのに eval が無ければ 1（陽性対照 G2 と台帳・原文の差分は同じ）", 1, "eval が付いていない", s_no_eval)
    def s_eval(root, skill):
        remove_v02(skill)
        add_eval(root, eval_case("V-02", "なし（初期値の `-`）"))
    scenario("G2 eval を足せば 0", 0, "eval plugins/dev-loop/evals/e1/case.yaml が付いている", s_eval)
    def s_incident_ok(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("3. ", "3. "))
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("- **CCC みっつめの行です**\n", ""))
        (skill / "references" / "line-registry.csv").write_text(registry_text([r for r in ROWS if r[0] != "V-03"]))
        add_eval(root, eval_case("V-03", "#30 #31"))
    scenario("G3 台帳の元の事故（#30;#31）が全部入っていれば 0", 0, "V-03 を外す PR に eval", s_incident_ok)
    def s_incident_missing(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("- **CCC みっつめの行です**\n", ""))
        (skill / "references" / "line-registry.csv").write_text(registry_text([r for r in ROWS if r[0] != "V-03"]))
        add_eval(root, eval_case("V-03", "#30"))
    scenario("G4 元の事故の番号が欠ければ 1", 1, "#31", s_incident_missing)
    def s_no_graders(root, skill):
        remove_v02(skill)
        add_eval(root, eval_case("V-02", "x", graders=False))
    scenario("G5 graders が無ければ 1", 1, "graders", s_no_graders)
    def s_wrong_id(root, skill):
        remove_v02(skill)
        add_eval(root, eval_case("V-01", "x"))
    scenario("G6 別の行の eval では 1", 1, "外した行: V-02", s_wrong_id)
    def pre_eval(root, skill):
        add_eval(root, eval_case("V-02", "x"))
    scenario("G7 eval が base に既にあって差分に無ければ 1", 1, "eval が付いていない", s_no_eval, pre_base=pre_eval)
    def s_merge(root, skill):
        remove_v02(skill)
        rows = [r for r in ROWS if r[0] != "V-02"]
        rows[0] = rows[0][:6] + ["V-02"]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
    scenario("G8 同趣旨の行への統合は eval を求めない", 0, "V-02 は V-01 に統合", s_merge)
    def s_merge_diff_tag(root, skill):
        remove_v02(skill)
        rows = [r for r in ROWS if r[0] != "V-02"]
        rows[1] = rows[1][:6] + ["V-02"]  # V-03（同趣旨が空）に統合したことにする
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
    scenario("G9 統合先の同趣旨が違えば 1（空の同趣旨も統合と認めない）", 1, "同趣旨が base で", s_merge_diff_tag)
    def s_dangling(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("2. **BBB ふたつめの行です**\n", ""))
    scenario("G10 原文だけ外して台帳に行が残れば 1（引きが 0 回）", 1, "0 回", s_dangling)
    def s_row_only(root, skill):
        (skill / "references" / "line-registry.csv").write_text(registry_text([r for r in ROWS if r[0] != "V-02"]))
        add_eval(root, eval_case("V-02", "x"))
    scenario("G11 台帳の行だけ消して原文に項が残れば 1（eval があっても）", 1, "台帳に無い項", s_row_only)
    scenario("G12 base を解決できなければ 2", 2, "解決できない", s_none, base_ref="nosuch")
    def pre_nolist(root, skill):
        (skill / "references" / "line-registry.csv").unlink()
    def s_intro(root, skill):
        (skill / "references" / "line-registry.csv").write_text(registry_text(ROWS))
    scenario("G13 base に台帳が無い（導入の PR）なら外した行の検査を飛ばして 0", 0, "導入の PR", s_intro, pre_base=pre_nolist)
    return bad


def real_checks() -> list[str]:
    bad: list[str] = []
    r = run([sys.executable, "-I", str(EFFECTS_SRC), "check"])
    if r.returncode != 0:
        bad.append(f"本物の台帳が通らない: {r.stdout.strip()[-300:]}")
    prune = (REPO / SKILL_REL / "references" / "prune.md").read_text()
    import importlib.util
    spec = importlib.util.spec_from_file_location("le", EFFECTS_SRC)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    sys.modules["le"] = mod
    spec.loader.exec_module(mod)
    lines = [l for l in prune.split("\n") if l.startswith("- 効いた行: ")]
    if len(lines) < 2 or not all(mod.RECORD_RE.match(l) for l in lines):
        bad.append(f"prune.md の記録の例が本体の正規表現に当たらない: {lines}")
    for rel in (f"{SKILL_REL}/prompts/verifier.md", f"{SKILL_REL}/SKILL.md"):
        t = (REPO / rel).read_text()
        if "**黙って削らない**——**各行は、過去の周で実際に破られた形に対応している" not in t:
            bad.append(f"{rel} が「黙って削らない」に置き換わっていない")
        if re.search(r"\*\*削らない\*\*——\*\*各行は", t):
            bad.append(f"{rel} に古い「削らない」が残っている")
        if "references/prune.md" not in t:
            bad.append(f"{rel} が references/prune.md を指していない")
    return bad


def apply(text: str, before: str, after: str) -> str:
    assert text.count(before) == 1, f"壊す箇所が {text.count(before)} 回ある: {before!r}"
    return text.replace(before, after)


# (名前, 対象 "effects"|"guard", 前, 後, 殺す試料)
MUTATIONS = [
    ("引きの回数を 1 回に限らない", "effects", "if n != 1:", "if n < 1:", "check"),
    ("`{{` の穴を項に数える", "effects", 'if m and not line[m.end():].startswith("{{"):', "if m:", "check"),
    ("コードブロックを読まない処理を外す", "effects", "                fence = m.group(1)\n                continue", "                fence = None\n                continue", "check"),
    ("周の順を名前順にする", "effects", "cycles.sort(key=lambda c: (c[0], c[1]))", "cycles.sort(key=lambda c: (c[1], c[0]))", "report"),
    ("候補の線を超えたときだけにする", "effects", "if s[3] >= window]", "if s[3] > window]", "report"),
    ("登録日より前の周を数える", "effects", '>= r["登録日"]', '< r["登録日"]', "report"),
    ("なしと ID の混在を見ない", "effects", "if none and ids:", "if False and ids:", "report"),
    ("形に合わない行を拾わない", "effects", "elif LABEL_RE.match(line):", "elif False and LABEL_RE.match(line):", "report"),
    ("外した行を見ない", "guard", 'if r["ID"] not in head_ids]', 'if r["ID"] in head_ids]', "guard"),
    ("差分でなく全部の eval を見る", "guard", 'changed.stdout.split("\\n")', 'git(root, "ls-files").stdout.split("\\n")', "guard"),
    ("元の事故の番号を見ない", "guard", "if want and not want <= have:", "if False and want and not want <= have:", "guard"),
    ("graders を見ない", "guard", 'if not re.search(r"^\\s+-\\s+name:", text, re.M) or not re.search(r"^graders:", text, re.M):', "if False:", "guard"),
    ("統合の同趣旨を見ない", "guard", 'base_target["同趣旨"] == r["同趣旨"]', "True", "guard"),
]


def main() -> int:
    sys.dont_write_bytecode = True
    bad: list[str] = []
    bad += case_check()
    bad += case_report()
    bad += case_guard()
    bad += real_checks()
    for line in bad:
        print(f"NG: {line}")
    if bad:
        return 1
    print("  試料 OK（check・report・guard・原本の突き合わせ）")
    effects = EFFECTS_SRC.read_text()
    guard = GUARD_SRC.read_text()
    survived = []
    for name, target, before, after, killer in MUTATIONS:
        e = apply(effects, before, after) if target == "effects" else None
        g = apply(guard, before, after) if target == "guard" else None
        fn = {"check": lambda: case_check(e), "report": lambda: case_report(e),
              "guard": lambda: case_guard(g, e)}[killer]
        if not fn():
            survived.append(name)
    if survived:
        for s in survived:
            print(f"NG: 変異が素通り: {s}")
        return 1
    print(f"OK: 変異 {len(MUTATIONS)} 件（すべて赤）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
