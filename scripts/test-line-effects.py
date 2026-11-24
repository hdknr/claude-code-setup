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
   付け替え（G16・G27〜G29。付け替え先を同じ PR で言い換えても 1——#1423 の S1・S2）・言い換えと縮め（G20〜G22・G30。外した項の頭に縮めた引きが当たっても 0——S5）・
   統合と言い換えの組み合わせ（G31・G35。統合元の除外は言い換えない付け替えに掛けない——G40）・外した項の文面を入れ子に残す（G36）・段落にした項への付け替え（G37・G38）・
   本文が別の項の頭を引く項の言い換え（G41）と、本文で引いていた頭の言い換え（飾りを外す・前置きを足す・延ばす・折り返す・本文に下ろす）への付け替え（G42〜G46。1——#1430）と、
   引いた文を頭に含める自分の頭の言い換え（G47・G48。0）・元の項を引いていた頭を写した新しい項に差し替える付け替え（G49・G52。1——#1452）・
   引いた先の項の頭も言い換えた自分の頭の言い換え（G50。0——#1453）・引用の片側を言い換える言い換え（G51。0）・行の印を引用の文面に数えない（G53。1）・
   頭だけの行・折り返した引用を残して自分の頭だけを言い換える言い換え（G54・G55。0）・記号だけを添えた行を下ろす・写す付け替え（G56〜G60。1）・
   引用の両側・括弧の言い換えと、引いた先も言い換えて続きの行に文面がある言い換え（G61〜G63・G67。0）・引用の行ごと付け替え先へ移す・文字を含む印で下ろす・番号の印だけを写す・
   付け替え先の ID も新しい引きの項へ寄せる付け替え（G64〜G66・G68・G69。1）・元の項の頭を付け替え先の頭の写しにして付け替え先を言い換える付け替え（G70。1）・
   引いた先の項の頭も言い換えたうえで、引用の行を頭の行に上げる・頭だけの本文の行を残す・上げた引用を折り返す・括弧を落とす自分の頭の言い換え（G71〜G73・G81。0——#1453）・
   元の項の頭を付け替え先の頭と引用の後ろの文面の写しにする付け替え（G74〜G80・G82。1）・
   元の項の頭を付け替え先の新しい頭の写しか `要点: <付け替え先の頭の言い換え>` に差し替えて本文を残し、付け替え先を言い換える付け替え（G83・G84。1——#1522）と、
   引いた先の新しい頭の文面を含める自分の頭の言い換え（G85。0）・付け替え先の新しい頭が元の項の頭の書き出しを持つ G64・G69 の形（G86・G87。1）・
   元の頭の書き出しを言い換える自分の頭の言い換え（G88。0）・頭の書き出しを共有する項どうしの付け替えと言い換え（G89。1／G90。0）・
   改名（G32〜G34・G39。改名だけなら 0——R1。コミット前でも 0）。
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
HEADER = ["ID", "ファイル", "引き", "元の事故", "登録日", "同趣旨", "統合元", "測り方"]

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
    ["V-01", "prompts/verifier.md", "**AAA ひとつめ", "#10", "2026-01-01", "t", "", "指摘"],
    ["V-02", "prompts/verifier.md", "**BBB ふたつめ", "-", "2026-01-01", "t", "", "指摘"],
    ["V-03", "prompts/verifier.md", "**CCC みっつめ", "#30;#31", "2026-01-01", "", "", "不可"],
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
        expect("C10 1 つの項に台帳の行が 2 つ当たれば 1",
               tree("c10", rows=ROWS + [["V-04", "prompts/verifier.md", "**AAA ひ", "-", "2026-01-01", "", "", "指摘"]]), 1, "1 項に 1 行")
        expect("C11 統合元の ID が台帳に残っていれば 1",
               tree("c11", rows=[ROWS[0][:6] + ["V-02", "指摘"]] + ROWS[1:]), 1, "台帳に残っている")
        expect("C12 統合元が ID の形でなければ 1", tree("c12", rows=[ROWS[0][:6] + ["zz", "指摘"]] + ROWS[1:]), 1, "ID の形でない")
        expect("C13 測り方が違えば 2", tree("c13", rows=[ROWS[0][:7] + ["何か"]] + ROWS[1:]), 2, "測り方")
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
        expect("R3 同じファイルの同趣旨 t の組が出る", r, 0, "まとめる候補（同じファイルで同趣旨が 2 行以上。統合できるのは同じファイルの行だけ）: 1 組", "t（prompts/verifier.md）: V-01 V-02")
        d = t / "across"
        d.mkdir()
        ac = Tree(d, effects_text, rows=[ROWS[0], ["I-01", "prompts/implementer.md", "**ZZZ いち", "-", "2026-01-01", "t", "", "不可"]])
        r = ac.run("report", str(plans), "--window", "1")
        expect("R14 ファイルをまたぐ同趣旨の組は、まとめる候補に出さず別の表に出す", r, 0, "同じファイルで同趣旨が 2 行以上。統合できるのは同じファイルの行だけ）: 0 組", "同趣旨だがファイルをまたぐ組（統合できない。重複の目印）: 1 組", "t: V-01 I-01")
        # R4 登録日より前の周は分母に入れない
        d = t / "late"
        d.mkdir()
        late = Tree(d, effects_text, rows=[["V-02"] + ROWS[1][1:4] + ["2026-02-03", "", "", "指摘"]] + [ROWS[0], ROWS[2]])
        r = late.run("report", str(plans), "--window", "1")
        expect("R4 登録日 2026-02-03 より前の周を数えない（V-02 は b.md の 1 周だけ）", r, 0, "V-02\t0\t-\t1\t")
        # R10 測れない行（不可）は候補に出さない
        r = tr.run("report", str(plans), "--window", "1")
        expect("R10 測り方 = 不可の V-03 は候補でなく、測れない行に並ぶ", r, 0, "測れない行（測り方 = 不可。候補に出さない）: 1 件", absent=("V-03（",))
        # R11 履歴に無い計画ファイルは最新として数える
        (plans / "u.md").write_text(rec("なし"))
        r = tr.run("report", str(plans), "--window", "1")
        expect("R11 履歴に無い計画ファイルは最新（V-01 の効いていない周数が 2）", r, 0, "V-01\t2\ta.md\t2\t")
        (plans / "u.md").unlink()
        # R12 登録日の比べはローカルの日付（JST 02-03 01:00 の周は登録日 02-03 の行に数える）
        plans4 = make_plans(t / "r12", [("j.md", "2026-02-02T16:00:00Z", rec("なし"))])
        d = t / "tz"
        d.mkdir()
        tz = Tree(d, effects_text, rows=[["V-02"] + ROWS[1][1:4] + ["2026-02-03", "", "", "指摘"]] + [ROWS[0], ROWS[2]])
        r = tz.run("report", str(plans4), "--window", "1", env={**os.environ, "TZ": "Asia/Tokyo"})
        expect("R12 ローカルの日付で登録日と比べる", r, 0, "V-02\t0\t-\t1\t")
        # R13 1 行に 2 つの ID
        plans5 = make_plans(t / "r13", [("m.md", "2026-02-01T00:00:00Z", "- 効いた行: V-01 V-02\n")])
        expect("R13 1 行に 2 つの ID は名指しして 1", tr.run("report", str(plans5)), 1, "1 行に 1 つの ID")
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
    def scenario(label, rc, word, setup, base_ref="main", pre_base=None, advance=None, commit=True):
        with tempfile.TemporaryDirectory(prefix="line-guard-") as t:
            root, skill, g, env = guard_repo(Path(t), guard_text, effects_text)
            if pre_base:
                pre_base(root, skill)
            g("add", "."), g("commit", "-q", "-m", "base")
            g("checkout", "-q", "-b", "feat")
            setup(root, skill)
            g("add", "-A")
            if commit:
                g("commit", "-q", "--allow-empty", "-m", "feat")
            if advance:
                g("checkout", "-q", "main")
                advance(root, skill)
                g("add", "-A"), g("commit", "-q", "-m", "main advances")
                g("checkout", "-q", "feat")
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
        rows[0] = rows[0][:6] + ["V-02", rows[0][7]]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
    scenario("G8 同趣旨の行への統合は eval を求めない", 0, "V-02 は V-01 に統合", s_merge)
    def s_merge_diff_tag(root, skill):
        remove_v02(skill)
        rows = [r for r in ROWS if r[0] != "V-02"]
        rows[1] = rows[1][:6] + ["V-02", rows[1][7]]  # V-03（同趣旨が空）に統合したことにする
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
    def add_impl(root, skill):
        (skill / "prompts" / "implementer.md").write_text("---\n1. **ZZZ いち**\n")
        (skill / "references" / "line-registry.csv").write_text(registry_text(ROWS + [["I-01", "prompts/implementer.md", "**ZZZ いち", "-", "2026-01-01", "t", "", "不可"]]))
    def s_merge_other_file(root, skill):
        remove_v02(skill)
        rows = [r for r in ROWS if r[0] != "V-02"] + [["I-01", "prompts/implementer.md", "**ZZZ いち", "-", "2026-01-01", "t", "V-02", "不可"]]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
    scenario("G14 別のファイルの同趣旨の行への統合は 1", 1, "別のファイル", s_merge_other_file, pre_base=add_impl)
    def add_v04(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT + "- **DDD よっつめの行です**\n")
        (skill / "references" / "line-registry.csv").write_text(registry_text(ROWS + [["V-04", "prompts/verifier.md", "**DDD よっつめ", "-", "2026-01-01", "", "", "指摘"]]))
    def s_merge_empty(root, skill):
        (skill / "prompts" / "verifier.md").write_text((PROMPT + "- **DDD よっつめの行です**\n").replace("- **CCC みっつめの行です**\n", ""))
        rows = [r for r in ROWS if r[0] != "V-03"] + [["V-04", "prompts/verifier.md", "**DDD よっつめ", "-", "2026-01-01", "", "V-03", "指摘"]]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
    scenario("G15 同趣旨が空の行どうしの統合は 1", 1, "eval が付いていない", s_merge_empty, pre_base=add_v04)
    def s_reassign(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("- **CCC みっつめの行です**\n", ""))
        rows = [r[:2] + ["**AAA ひとつめの"] + r[3:] if r[0] == "V-03" else r for r in ROWS]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
    scenario("G16 ID を base に既にある別の項に付け替えたら 1", 1, "付け替えた", s_reassign)
    def s_prefix(root, skill):
        remove_v02(skill)
        add_eval(root, eval_case("V-021", "x"))
    def s_rephrase_a(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**", "1. AAA ひとつめの行です"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "AAA ひとつめ"] + ROWS[0][3:]] + ROWS[1:]))
    scenario("G20 頭の飾りを外した言い換え（同じ項）は 0（偽の赤にしない）", 0, "問題 0 件", s_rephrase_a)
    def s_rephrase_b(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない", "1. 入れ子は数えない（旧本文）\n   - **AAA ひとつめの行です**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "入れ子は数えない"] + ROWS[0][3:]] + ROWS[1:]))
    scenario("G21 本文の文を頭に上げた言い換え（同じ項）は 0", 0, "問題 0 件", s_rephrase_b)
    def s_shorten(root, skill):
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "**AAA ひ"] + ROWS[0][3:]] + ROWS[1:]))
    scenario("G22 引きを縮めるだけなら 0", 0, "問題 0 件", s_shorten)
    def s_move_file(root, skill):
        rows = [r[:1] + ["prompts/implementer.md", "**ZZZ いち"] + r[3:] if r[0] == "V-03" else r for r in ROWS]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("- **CCC みっつめの行です**\n", ""))
    scenario("G23 生き残る ID のファイルを変えたら 1（prompts/ の外・別の受け手へ移して eval を逃れない）", 1, "ファイルを", s_move_file, pre_base=add_impl)
    def s_merge_new_target(root, skill):
        remove_v02(skill)
        (skill / "prompts" / "verifier.md").write_text((skill / "prompts" / "verifier.md").read_text() + "- **NEW あたらしい行です**\n")
        rows = [r for r in ROWS if r[0] != "V-02"] + [["V-99", "prompts/verifier.md", "**NEW あたらしい", "-", "2026-01-01", "t", "V-02", "指摘"]]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
    scenario("G24 統合先が base に無い新しい行なら 1", 1, "統合先が base に無い", s_merge_new_target)
    def s_dash(root, skill):
        remove_v02(skill)
        add_eval(root, eval_case("V-02", "-"))
    scenario("G25 台帳が `-` で eval の `元の事故:` も `-` なら 1", 1, "元の事故:` が空", s_dash)
    def s_other_yaml(root, skill):
        remove_v02(skill)
        (root / "plugins/dev-loop/evals/e1").mkdir(parents=True)
        (root / "plugins/dev-loop/evals/e1/other.yaml").write_text(eval_case("V-02", "x"))
    scenario("G26 case.yaml でないファイルは eval に数えない", 1, "eval が付いていない", s_other_yaml)
    scenario("G17 `外した行: V-021` では V-02 を外せない（前方一致で受けない）", 1, "外した行: V-02", s_prefix)
    def s_graders_empty(root, skill):
        remove_v02(skill)
        add_eval(root, "# 外した行: V-02\n# 元の事故: x\ngraders: []\nprompt: |\n  - name: z\n")
    scenario("G18 graders が空で別の場所に `- name:` があっても 1", 1, "graders", s_graders_empty)
    scenario("G19 base の先端が進んでも、周が分かれた時点の台帳と比べる（先端に足された行を外したと見ない）", 0, "外した行 0 件", s_none, advance=add_v04)
    # #1423: #1194 の当て直しと狭いパスが示した後退（S1・S2・S5・R1）。直す前の版では S1・S2・S5・R1 が期待から外れる（陽性対照は計画ファイル）
    def drop_v01_with_eval(root, skill, prompt, v02_hiki):
        (skill / "prompts" / "verifier.md").write_text(prompt.replace("2. **BBB ふたつめの行です**\n", ""))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-02", "prompts/verifier.md", v02_hiki] + ROWS[1][3:], ROWS[2]]))
        add_eval(root, eval_case("V-01", "#10"))
    def s_reassign_destar(root, skill):
        drop_v01_with_eval(root, skill, PROMPT.replace("1. **AAA ひとつめの行です**", "1. AAA ひとつめの行です"), "AAA ひとつめ")
    scenario("G27 付け替え先の項の頭の飾りを同じ PR で外しても、付け替えは 1（S1）", 1, "付け替えた", s_reassign_destar)
    def s_reassign_raise(root, skill):
        drop_v01_with_eval(root, skill, PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない",
                                                       "1. 入れ子は数えない（旧本文）\n   - **AAA ひとつめの行です**"), "入れ子は数えない")
    scenario("G28 付け替え先の項の本文の文を同じ PR で頭に上げても、付け替えは 1（S2）", 1, "付け替えた", s_reassign_raise)
    def s_reassign_plain(root, skill):
        drop_v01_with_eval(root, skill, PROMPT, "**AAA ひとつめ")
    scenario("G29 言い換えない付け替え（陽性対照。G27・G28 と台帳の差だけ）は 1", 1, "付け替えた", s_reassign_plain)
    def add_v04_near(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT + "- **AAA ひとつおいた行です**\n")
        (skill / "references" / "line-registry.csv").write_text(registry_text(ROWS + [["V-04", "prompts/verifier.md", "**AAA ひとつおいた", "-", "2026-01-01", "", "", "指摘"]]))
    def s_shorten_over_removed(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT)
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "**AAA ひと"] + ROWS[0][3:]] + ROWS[1:]))
        add_eval(root, eval_case("V-04", "x"))
    scenario("G30 縮めた引きが、同じ PR で外した別の項の base の頭に前方一致しても 0（S5）", 0, "問題 0 件", s_shorten_over_removed, pre_base=add_v04_near)
    def s_merge_rephrase(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("2. **BBB ふたつめの行です**\n", "").replace(
            "1. **AAA ひとつめの行です**\n   - 入れ子は数えない", "1. AAA ひとつめの行です（BBB を統合）\n   - 入れ子は数えない\n   - **BBB ふたつめの行です**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "AAA ひとつめ", "#10", "2026-01-01", "t", "V-02", "指摘"], ROWS[2]]))
    scenario("G31 統合（同趣旨 t）と言い換えを同じ PR でしても 0（取り込んだ別の項の頭が本文にあっても、元の項の頭が残る）", 0, "V-02 は V-01 に統合", s_merge_rephrase)
    def s_rename(root, skill):
        (skill / "prompts" / "verifier.md").rename(skill / "prompts" / "verifier-x.md")
        (skill / "references" / "line-registry.csv").write_text(registry_text([r[:1] + ["prompts/verifier-x.md"] + r[2:] for r in ROWS]))
    scenario("G32 prompts のファイルを改名しただけなら 0（R1）", 0, "問題 0 件", s_rename)
    def s_rename_reassign(root, skill):
        text = PROMPT.replace("2. **BBB ふたつめの行です**\n", "")
        (skill / "prompts" / "verifier.md").unlink()
        (skill / "prompts" / "verifier-x.md").write_text(text)
        rows = [["V-02", "prompts/verifier-x.md", "**AAA ひとつめ"] + ROWS[1][3:], ROWS[2][:1] + ["prompts/verifier-x.md"] + ROWS[2][2:]]
        (skill / "references" / "line-registry.csv").write_text(registry_text(rows))
        add_eval(root, eval_case("V-01", "#10"))
    scenario("G33 改名しても、別の項へ付け替えれば 1", 1, "付け替えた", s_rename_reassign)
    def s_rename_rewrite(root, skill):
        (skill / "prompts" / "verifier.md").unlink()
        (skill / "prompts" / "verifier-x.md").write_text("# 別物\n\n---\n\n1. **AAA ひとつめの行です**\n2. **BBB ふたつめの行です**\n- **CCC みっつめの行です**\n"
                                                        + "".join(f"\n段落 {i}: 改名と見られないほど中身を変えた。\n" for i in range(40)))
        (skill / "references" / "line-registry.csv").write_text(registry_text([r[:1] + ["prompts/verifier-x.md"] + r[2:] for r in ROWS]))
    scenario("G34 改名と見られないほど中身を変えたファイルへ移せば、今までどおり 1（止まる向き）", 1, "ファイルを", s_rename_rewrite)
    scenario("G39 改名をコミットする前（索引に載せただけ）に回しても 0（台帳と原文と同じく作業ツリーまで見る）", 0, "問題 0 件", s_rename, commit=False)
    # #1423 の 1 パス目の /code-review（CR1・CR2）
    def s_merge_reword(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("2. **BBB ふたつめの行です**\n", "").replace(
            "1. **AAA ひとつめの行です**\n   - 入れ子は数えない", "1. **AAA と BBB をまとめた行**\n   - 入れ子は数えない\n   - **BBB ふたつめの行です**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "**AAA と BBB", "#10", "2026-01-01", "t", "V-02", "指摘"], ROWS[2]]))
    scenario("G35 統合して頭の文面も変えた（元の頭が残らない）ときも 0——取り込んだ統合元の項の頭は付け替え先と見ない", 0, "V-02 は V-01 に統合", s_merge_reword)
    def s_keep_removed_text(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("2. **BBB ふたつめの行です**\n", "").replace(
            "   - 入れ子は数えない", "   - 入れ子は数えない\n   - **BBB ふたつめの行です**（外した項の文面を残す）"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "**AAA ひ"] + ROWS[0][3:], ROWS[2]]))
        add_eval(root, eval_case("V-02", "x"))
    scenario("G36 外した項の文面を別の項の入れ子に残し、その項の引きを縮めても 0（元の項の頭が残る）", 0, "問題 0 件", s_keep_removed_text)
    def s_demote_reassign(root, skill):
        drop_v01_with_eval(root, skill, PROMPT.replace("2. **BBB ふたつめの行です**\n", "**BBB ふたつめの行です**（項でなくした）\n2. **BBB ふたつめの行です**\n"), "**AAA ひとつめ")
    scenario("G37 元の項を段落にして、すぐ上の項へ付け替えれば 1", 1, "付け替えた", s_demote_reassign)
    def s_demote_reassign_destar(root, skill):
        drop_v01_with_eval(root, skill, PROMPT.replace("1. **AAA ひとつめの行です**", "1. AAA ひとつめの行です").replace(
            "2. **BBB ふたつめの行です**\n", "**BBB ふたつめの行です**（項でなくした）\n2. **BBB ふたつめの行です**\n"), "AAA ひとつめ")
    scenario("G38 元の項を段落にし、すぐ上の付け替え先の頭の飾りも外して付け替えれば 1（項は字下げの無い行で切る）", 1, "付け替えた", s_demote_reassign_destar)
    # #1423 の 2 パス目（Verifier の F1・/code-review の 2）
    def s_merge_swap(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", ""))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "**BBB ふたつめ", "#10", "2026-01-01", "t", "V-02", "指摘"], ROWS[2]]))
    scenario("G40 元の項を消し、ID を同趣旨の別の項へ付け替えて、その項の ID を統合元にしても 1（統合元の除外は言い換えない付け替えに掛けない）", 1, "付け替えた", s_merge_swap)
    def pre_quote_ccc(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", "   - 入れ子は数えない（下の「CCC みっつめの行です」と同じ）"))
    def s_reword_quoting(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", "   - 入れ子は数えない（下の「CCC みっつめの行です」と同じ）").replace(
            "**AAA ひとつめの行です**", "**AAA 一つめの行です**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "**AAA 一つめ"] + ROWS[0][3:]] + ROWS[1:]))
    scenario("G41 本文が base の時点から別の項の頭を引いている項の頭を言い換えても 0", 0, "問題 0 件", s_reword_quoting, pre_base=pre_quote_ccc)
    # #1430: 元の項の本文が base の時点から付け替え先の頭を引いていても、付け替え先の頭の飾りを外した言い換えへの付け替えは 1（#1426 の狭いパスの N1）
    def pre_quote_bbb(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", "   - 入れ子は数えない（下の「BBB ふたつめの行です」と同じ）"))
    def s_reassign_to_quoted(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", "").replace(
            "2. **BBB ふたつめの行です**", "2. BBB ふたつめの行です"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "BBB ふたつめ"] + ROWS[0][3:], ROWS[2]]))
        add_eval(root, eval_case("V-02", "x"))
    scenario("G42 元の項の本文が base の時点から付け替え先の頭を引いていても、元の項を消して付け替え先の頭の飾りを外した言い換えへ付け替えれば 1",
             1, "付け替えた", s_reassign_to_quoted, pre_base=pre_quote_bbb)
    def reassign_to_quoted_as(new_head, hiki):
        def s(root, skill):
            (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", "").replace(
                "2. **BBB ふたつめの行です**", "2. " + new_head))
            (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", hiki] + ROWS[0][3:], ROWS[2]]))
            add_eval(root, eval_case("V-02", "x"))
        return s
    scenario("G43 G42 で、付け替え先の頭に前置きを足した言い換えへ付け替えても 1", 1, "付け替えた",
             reassign_to_quoted_as("要点: BBB ふたつめの行です", "要点: BBB"), pre_base=pre_quote_bbb)
    scenario("G44 G42 で、付け替え先の頭を飾りごと延ばし、引きを元の頭より長くしても 1", 1, "付け替えた",
             reassign_to_quoted_as("**BBB ふたつめの行です**（補足）", "**BBB ふたつめの行です**（補"), pre_base=pre_quote_bbb)
    # #1430 の 2 パス目（/code-review・Verifier）
    scenario("G45 G42 で、付け替え先の頭を字下げした行へ折り返した言い換えへ付け替えても 1", 1, "付け替えた",
             reassign_to_quoted_as("BBB ふたつめ\n   の行です", "BBB ふたつめ"), pre_base=pre_quote_bbb)
    scenario("G46 G42 で、付け替え先に新しい頭を置き、元の頭を本文に下ろして付け替えても 1", 1, "付け替えた",
             reassign_to_quoted_as("**まったく別の頭です**\n   - BBB ふたつめの行です", "**まったく別"), pre_base=pre_quote_bbb)
    def reword_as_hiki(new_a, hiki):
        def s(root, skill):
            (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", new_a))
            (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", hiki] + ROWS[0][3:]] + ROWS[1:]))
        return s
    def reword_quoting_as(new_a):
        def s(root, skill):
            (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", new_a))
            (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "**AAA 一つめ"] + ROWS[0][3:]] + ROWS[1:]))
        return s
    scenario("G47 本文で別の項の頭を引く項が、自分の頭の言い換えにその頭の文面を含めても 0（引いた先の項は残る）", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です（CCC みっつめの行です 参照）**\n   - 入れ子は数えない（下の「CCC みっつめの行です」と同じ）\n"), pre_base=pre_quote_ccc)
    scenario("G48 本文で別の項の頭を引く項が、頭を言い換えて引いた文を頭の行に上げても 0", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です**（下の「CCC みっつめの行です」と同じ）\n   - 入れ子は数えない\n"), pre_base=pre_quote_ccc)
    # #1452: 元の項を、本文で引いていた付け替え先の頭を写した新しい項に差し替えて付け替える（PR #1449 の狭いパスの R1）
    def s_replace_with_quoted(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", "1. 要点: BBB ふたつめの行です\n"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "要点: BBB"] + ROWS[0][3:]] + ROWS[1:]))
    scenario("G49 元の項の本文が base で付け替え先の頭を引いていても、元の項をその頭を写した新しい項に差し替えて付け替えれば 1（付け替え先は残る）",
             1, "付け替えた", s_replace_with_quoted, pre_base=pre_quote_bbb)
    # #1453: 引いた先の項の頭も同じ PR で言い換えた、自分の頭の言い換え（PR #1449 の狭いパスの R2）
    def s_reword_both(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", "   - 入れ子は数えない（下の「CCC みっつめの行です」と同じ）").replace(
            "**AAA ひとつめの行です**", "**AAA 一つめの行です**").replace("- **CCC みっつめの行です**", "- **CCC みっつめの行です。**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text(
            [["V-01", "prompts/verifier.md", "**AAA 一つめ"] + ROWS[0][3:], ROWS[1], ["V-03", "prompts/verifier.md", "**CCC みっつめの行です。"] + ROWS[2][3:]]))
    scenario("G50 本文で別の項の頭を引く項が、引いた先の項の頭も同じ PR で言い換えたうえで自分の頭を言い換えても 0（本文の引用の行は受け継ぐ）",
             0, "問題 0 件", s_reword_both, pre_base=pre_quote_ccc)
    scenario("G51 本文で別の項の頭を引く項が、頭を言い換え、引用の後ろの文面も言い換えても 0（引用の前の文面が頭と続いて残る）", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です**\n   - 入れ子は数えない（下の「CCC みっつめの行です」）\n"), pre_base=pre_quote_ccc)
    def pre_bare_bbb(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", "   - BBB ふたつめの行です"))
    def s_replace_bare(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", "1. 要点: BBB ふたつめの行です\n"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "要点: BBB"] + ROWS[0][3:]] + ROWS[1:]))
    scenario("G52 元の項の本文の行が付け替え先の頭だけ（前にも後ろにも文面が無い）なら、その頭を写した新しい項に差し替えて付け替えれば 1",
             1, "付け替えた", s_replace_bare, pre_base=pre_bare_bbb)
    scenario("G53 G52 の base で、元の項を消し、付け替え先に新しい頭を置いて元の頭を本文の項に下ろして付け替えても 1（行の印は引用の文面に数えない）",
             1, "付け替えた", reassign_to_quoted_as("**まったく別の頭です**\n   - BBB ふたつめの行です", "**まったく別"), pre_base=pre_bare_bbb)
    # #1452 の 1 パス目の /code-review・Verifier: 頭だけ・記号だけを添えた引用の行と、行をまたぐ引用
    def pre_body(line):
        def pre(root, skill):
            (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", line))
        return pre
    scenario("G54 本文の行が別の項の頭だけの項が、本文を残して自分の頭だけを言い換えても 0（引いた先の項は残る）", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です**\n   - CCC みっつめの行です\n"), pre_base=pre_body("   - CCC みっつめの行です"))
    scenario("G55 本文の引用が字下げした続きの行へ折り返された項が、本文を残して自分の頭だけを言い換えても 0", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です**\n   - 入れ子は数えない（下の「CCC みっつめ\n     の行です」と同じ）\n"),
             pre_base=pre_body("   - 入れ子は数えない（下の「CCC みっつめ\n     の行です」と同じ）"))
    for name, line in (("G56 G53 で、下ろす行の印が `・` でも 1（記号は引用の文面に数えない）", "   ・BBB ふたつめの行です"),
                       ("G57 G53 で、下ろす行が引用（`>`）でも 1", "   > BBB ふたつめの行です"),
                       ("G58 G53 で、下ろす行がチェックボックス（`- [ ]`）でも 1", "   - [ ] BBB ふたつめの行です"),
                       ("G59 G53 で、下ろす行が鉤括弧だけを添えた引用（`「…」`）でも 1", "   - 「BBB ふたつめの行です」")):
        scenario(name, 1, "付け替えた", reassign_to_quoted_as("**まったく別の頭です**\n" + line, "**まったく別"), pre_base=pre_body(line))
    def s_replace_kakko(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", "1. 要点: 「BBB ふたつめの行です」\n"))
        (skill / "references" / "line-registry.csv").write_text(registry_text([["V-01", "prompts/verifier.md", "要点: 「BBB"] + ROWS[0][3:]] + ROWS[1:]))
    scenario("G60 元の項の本文の行が鉤括弧だけを添えた付け替え先の頭なら、その行を写した新しい項に差し替えて付け替えれば 1", 1, "付け替えた",
             s_replace_kakko, pre_base=pre_body("   - 「BBB ふたつめの行です」"))
    # #1452 の 2 パス目の /code-review: 引用の両側の言い換え・続きの行の文面・引用の行ごと付け替え先へ移す付け替え・行の印の形
    scenario("G61 本文で別の項の頭を引く項が、頭を言い換え、引用の両側の文面も言い換えても 0（引いた先の項は残る）", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です**\n   - 入れ子は数える（上の「CCC みっつめの行です」を参照）\n"), pre_base=pre_quote_ccc)
    scenario("G62 本文で別の項の頭を引く項が、頭を言い換え、引用の括弧を変えても 0", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です**\n   - 入れ子は数えない（下の“CCC みっつめの行です”と同じ）\n"), pre_base=pre_quote_ccc)
    def s_reword_both_wrapped(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", "   - CCC みっつめの行です\n     と同じに扱う").replace(
            "**AAA ひとつめの行です**", "**AAA 一つめの行です**").replace("- **CCC みっつめの行です**", "- **CCC みっつめの行です。**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text(
            [["V-01", "prompts/verifier.md", "**AAA 一つめ"] + ROWS[0][3:], ROWS[1], ["V-03", "prompts/verifier.md", "**CCC みっつめの行です。"] + ROWS[2][3:]]))
    scenario("G63 G50 で、引用の後ろの文面が字下げした続きの行にあっても 0（引いた先の ID が言い換えた項を引く）", 0, "問題 0 件",
             s_reword_both_wrapped, pre_base=pre_body("   - CCC みっつめの行です\n     と同じに扱う"))
    scenario("G64 元の項を消し、付け替え先に新しい頭を置いて、元の項の引用の行（文面つき）をそのまま付け替え先の本文へ移して付け替えても 1", 1, "付け替えた",
             reassign_to_quoted_as("**まったく別の頭です**\n   - 入れ子は数えない（下の「BBB ふたつめの行です」と同じ）", "**まったく別"), pre_base=pre_quote_bbb)
    scenario("G65 元の項の本文が `要点: <付け替え先の頭>` のとき、元の項を消して付け替え先をその文面に言い換えて付け替えても 1", 1, "付け替えた",
             reassign_to_quoted_as("要点: BBB ふたつめの行です", "要点: BBB"), pre_base=pre_body("   - 要点: BBB ふたつめの行です"))
    scenario("G66 G53 で、下ろす行の印が `（1）` でも 1（文字を含む印でも、引いた先が別の項として残らない）", 1, "付け替えた",
             reassign_to_quoted_as("**まったく別の頭です**\n   （1） BBB ふたつめの行です", "**まったく別"), pre_base=pre_body("   （1） BBB ふたつめの行です"))
    scenario("G67 本文で別の項の頭を引く項が、頭を言い換えて引用の行を頭の行に上げ、引用の後ろの文面を言い換えても 0（前の文面が続く）", 0, "問題 0 件",
             reword_quoting_as("1. **AAA 一つめの行です**——入れ子は数えない（下の「CCC みっつめの行です」）\n"), pre_base=pre_quote_ccc)
    scenario("G68 元の項の本文の行が番号の印だけを添えた付け替え先の頭なら、印ごと写した新しい項に差し替えて付け替えれば 1（行の印は文面に数えない）", 1, "付け替えた",
             reword_as_hiki("1. 要点 1. BBB ふたつめの行です\n", "要点 1. BBB"), pre_base=pre_body("   1. BBB ふたつめの行です"))
    def s_both_ids_on_cur(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", "").replace(
            "2. **BBB ふたつめの行です**", "2. 要点: まったく別の頭です\n   - 入れ子は数えない（下の「BBB ふたつめの行です」と同じ）"))
        (skill / "references" / "line-registry.csv").write_text(registry_text(
            [["V-01", "prompts/verifier.md", "要点: まったく別"] + ROWS[0][3:], ["V-02", "prompts/verifier.md", "要点: まったく別の頭"] + ROWS[1][3:], ROWS[2]]))
    scenario("G69 G64 で、付け替え先の ID も同じ新しい引きの項を引くよう言い換えても 1（引いた先が別の項として残らない。引いた頭は新しい引きの項の本文だけにある）", 1, "付け替えた",
             s_both_ids_on_cur, pre_base=pre_quote_bbb)
    # #1452 の狭いパスの O1: 元の項の頭を付け替え先の頭の写しに差し替え、本文の引用を残し、付け替え先の頭も言い換える
    def s_copy_head_reword_target(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("   - 入れ子は数えない", "   - 入れ子は数えない（下の「BBB ふたつめの行です」と同じ）").replace(
            "**AAA ひとつめの行です**", "要点: BBB ふたつめの行です").replace("2. **BBB ふたつめの行です**", "2. **BBB 二つめの行です**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text(
            [["V-01", "prompts/verifier.md", "要点: BBB ふたつ"] + ROWS[0][3:], ["V-02", "prompts/verifier.md", "**BBB 二つ"] + ROWS[1][3:], ROWS[2]]))
    scenario("G70 元の項の頭を付け替え先の頭の写しに差し替えて本文の引用を残し、付け替え先の頭も言い換えて付け替えれば 1（引いた頭が新しい引きの項の頭の行にある）",
             1, "付け替えた", s_copy_head_reword_target, pre_base=pre_quote_bbb)
    # #1453: 引いた先の項の頭も同じ PR で言い換えた、自分の頭の言い換えのほかの形（G50 の組）
    def reword_both_as(new_a):
        def s(root, skill):
            (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", new_a).replace(
                "- **CCC みっつめの行です**", "- **CCC みっつめの行です。**"))
            (skill / "references" / "line-registry.csv").write_text(registry_text(
                [["V-01", "prompts/verifier.md", "**AAA 一つめ"] + ROWS[0][3:], ROWS[1], ["V-03", "prompts/verifier.md", "**CCC みっつめの行です。"] + ROWS[2][3:]]))
        return s
    scenario("G71 G50 で、引用の行を頭の行に上げても 0（G48 の言い換え。引いた頭は頭の行で引用の後ろの文面と続く）", 0, "問題 0 件",
             reword_both_as("1. **AAA 一つめの行です**（下の「CCC みっつめの行です」と同じ）\n"), pre_base=pre_quote_ccc)
    scenario("G72 本文の行が別の項の頭だけの項が、引いた先の項の頭も言い換えたうえで本文を残して自分の頭を言い換えても 0（G54 の形。#1452 の版から 0——戻りの止め）", 0, "問題 0 件",
             reword_both_as("1. **AAA 一つめの行です**\n   - CCC みっつめの行です\n"), pre_base=pre_body("   - CCC みっつめの行です"))
    scenario("G73 G71 で、引用の後ろの文面を頭の下の折り返しの行に置いても 0", 0, "問題 0 件",
             reword_both_as("1. **AAA 一つめの行です**（下の「CCC みっつめの行です」\n   と同じ）\n"), pre_base=pre_quote_ccc)
    scenario("G81 G71 で、上げた引用の前の括弧を落としても 0（引用の後ろの文面が続き、手前に元の頭の文面がある）", 0, "問題 0 件",
             reword_both_as("1. **AAA 一つめの行です** CCC みっつめの行です」と同じ）\n"), pre_base=pre_quote_ccc)
    # #1453 の 1 パス目の /code-review: 頭を引いた頭の写しで始める・括弧を写さない付け替えは、引用の後ろの文面を添えても 1（G70 の変形）
    def copy_head_with_tail(new_a, hiki):
        def s(root, skill):
            (skill / "prompts" / "verifier.md").write_text((skill / "prompts" / "verifier.md").read_text().replace(
                "**AAA ひとつめの行です**", new_a).replace("2. **BBB ふたつめの行です**", "2. **BBB 二つめの行です**"))
            (skill / "references" / "line-registry.csv").write_text(registry_text(
                [["V-01", "prompts/verifier.md", hiki] + ROWS[0][3:], ["V-02", "prompts/verifier.md", "**BBB 二つ"] + ROWS[1][3:], ROWS[2]]))
        return s
    scenario("G74 元の項の頭を付け替え先の頭と引用の後ろの文面の写しにし、付け替え先を言い換えて付け替えれば 1", 1, "付け替えた",
             copy_head_with_tail("**BBB ふたつめの行です**（上と同じ）", "**BBB ふたつめの行です**（上"), pre_base=pre_body("   - BBB ふたつめの行です（上と同じ）"))
    scenario("G75 G70 で、頭に引用の後ろの文面まで写しても 1", 1, "付け替えた",
             copy_head_with_tail("**BBB ふたつめの行です」と同じ）**", "**BBB ふたつめの行です」"), pre_base=pre_quote_bbb)
    scenario("G76 G75 で、頭に前置きを足しても 1（引用の手前が元の項の頭と関わらない）", 1, "付け替えた",
             copy_head_with_tail("要点: BBB ふたつめの行です」と同じ）", "要点: BBB ふたつめの行です」"), pre_base=pre_quote_bbb)
    scenario("G77 G75 で、頭を元の頭の書き出しと付け替え先の頭の写しと上げた引用の行にしても 1（引用の手前に引いた頭がある）", 1, "付け替えた",
             copy_head_with_tail("AAA BBB ふたつめの行です（下の「BBB ふたつめの行です」と同じ）", "AAA BBB ふたつめの行です（下"), pre_base=pre_quote_bbb)
    # #1453 の 2 パス目の Verifier の F-B と /code-review: 引用の手前を元の項の頭と関わらない文面にした付け替え（1）
    scenario("G78 G75 で、頭を `要点: ` と括弧つきの引用の写しにしても 1（引用の手前が元の項の頭と関わらない）", 1, "付け替えた",
             copy_head_with_tail("要点: 「BBB ふたつめの行です」と同じ）", "要点: 「BBB"), pre_base=pre_quote_bbb)
    scenario("G79 G74 の base で、頭を `要点: ` と付け替え先の頭と引用の後ろの文面の写しにしても 1", 1, "付け替えた",
             copy_head_with_tail("要点: BBB ふたつめの行です（上と同じ）", "要点: BBB"), pre_base=pre_body("   - BBB ふたつめの行です（上と同じ）"))
    scenario("G80 G75 で、頭を付け替え先の新しい頭の縮めと上げた引用の行にしても 1", 1, "付け替えた",
             copy_head_with_tail("BBB 二つめ（下の「BBB ふたつめの行です」と同じ）", "BBB 二つめ（"), pre_base=pre_quote_bbb)
    # #1453 の狭いパスの R1: 引用の手前の文面が元の項の頭と語尾だけ偶然に重なる付け替え（1）
    scenario("G82 G78 で、前置きが元の項の頭と語尾だけ重なっても 1（`この行です:`）", 1, "付け替えた",
             copy_head_with_tail("この行です: 「BBB ふたつめの行です」と同じ）", "この行です: 「BBB"), pre_base=pre_quote_bbb)
    # #1522（#1452 の当て直しの R2-1）: 元の項の頭を、言い換えた付け替え先の頭の写しか `要点: <付け替え先の頭の言い換え>` に差し替え、本文の引用を残す付け替え（1）
    def reword_both_new_name(root, skill):
        (skill / "prompts" / "verifier.md").write_text((skill / "prompts" / "verifier.md").read_text().replace(
            "**AAA ひとつめの行です**", "**AAA 一つめの行です（CCC 三つめの行です 参照）**").replace("- **CCC みっつめの行です**", "- **CCC 三つめの行です**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text(
            [["V-01", "prompts/verifier.md", "**AAA 一つめ"] + ROWS[0][3:], ROWS[1], ["V-03", "prompts/verifier.md", "**CCC 三つめ"] + ROWS[2][3:]]))
    def copy_new_head(new_b, hiki_b):
        def s(root, skill):
            (skill / "prompts" / "verifier.md").write_text((skill / "prompts" / "verifier.md").read_text().replace(
                "**AAA ひとつめの行です**", "要点: BBB 二つめの行です").replace("2. **BBB ふたつめの行です**", "2. " + new_b))
            (skill / "references" / "line-registry.csv").write_text(registry_text(
                [["V-01", "prompts/verifier.md", "要点: BBB 二つ"] + ROWS[0][3:], ["V-02", "prompts/verifier.md", hiki_b] + ROWS[1][3:], ROWS[2]]))
        return s
    scenario("G83 元の項の本文の行が付け替え先の頭だけのとき、元の項の頭を付け替え先の新しい頭の写しに差し替えて本文を残し、付け替え先を言い換えて付け替えれば 1（#1522 の形 1）",
             1, "付け替えた", copy_new_head("**BBB 二つめの行です**", "**BBB 二つ"), pre_base=pre_bare_bbb)
    scenario("G84 元の項の本文の行が鉤括弧だけを添えた付け替え先の頭のとき、元の項の頭を `要点: <付け替え先の頭の言い換え>` に差し替えて本文を残し、付け替え先を `要点: ` の頭に言い換えて付け替えれば 1（#1522 の形 2）",
             1, "付け替えた", copy_new_head("要点: BBB ふたつめの行です", "要点: BBB ふ"), pre_base=pre_body("   - 「BBB ふたつめの行です」"))
    scenario("G85 本文で別の項の頭を引く項が、引いた先の項の頭を言い換え、自分の頭の言い換えに引いた先の新しい頭の文面を含めても 0（頭の行が元の頭の書き出しを持つ）", 0, "問題 0 件",
             reword_both_new_name, pre_base=pre_quote_ccc)
    # #1522: 上の条件（頭の行が元の項の頭の書き出しを持つか）だけでは決まらない、元の項を消して付け替え先に移る形——付け替え先の新しい頭が元の頭の書き出しを持っても、
    # 引いた先が別の項として残らないので 1（lives_on とその中の `x != cur_head` を判別する。G64・G69 は頭が元の頭の書き出しを持たないので、この周の条件だけで止まる）
    scenario("G86 G64 で、付け替え先の新しい頭が元の項の頭の書き出しを持っても 1（引いた先が別の項として残らない）", 1, "付け替えた",
             reassign_to_quoted_as("**AAA まったく別の頭です**\n   - 入れ子は数えない（下の「BBB ふたつめの行です」と同じ）", "**AAA まったく別"), pre_base=pre_quote_bbb)
    def s_both_ids_on_cur_aaa(root, skill):
        (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("1. **AAA ひとつめの行です**\n   - 入れ子は数えない\n", "").replace(
            "2. **BBB ふたつめの行です**", "2. AAA まったく別の頭です\n   - 入れ子は数えない（下の「BBB ふたつめの行です」と同じ）"))
        (skill / "references" / "line-registry.csv").write_text(registry_text(
            [["V-01", "prompts/verifier.md", "AAA まったく別"] + ROWS[0][3:], ["V-02", "prompts/verifier.md", "AAA まったく別の頭"] + ROWS[1][3:], ROWS[2]]))
    scenario("G87 G69 で、新しい引きの項の頭が元の項の頭の書き出しを持っても 1（付け替え先の ID も新しい引きの項を引く）", 1, "付け替えた",
             s_both_ids_on_cur_aaa, pre_base=pre_quote_bbb)
    # #1522 の 1 パス目の /code-review（CR1・CR2）と Verifier: 元の頭の書き出しを言い換える正当な言い換え（0）と、頭の書き出しを共有する項どうしの付け替え（1）
    def reword_both_kou(root, skill):
        (skill / "prompts" / "verifier.md").write_text((skill / "prompts" / "verifier.md").read_text().replace(
            "**AAA ひとつめの行です**", "**甲 一つめの行です**").replace("- **CCC みっつめの行です**", "- **CCC 三つめの行です**"))
        (skill / "references" / "line-registry.csv").write_text(registry_text(
            [["V-01", "prompts/verifier.md", "**甲 一つめ"] + ROWS[0][3:], ROWS[1], ["V-03", "prompts/verifier.md", "**CCC 三つめ"] + ROWS[2][3:]]))
    scenario("G88 G50 で、自分の頭の書き出しも別の語に言い換えても 0（main の版から 0——#1522 の 1 パス目の戻りの止め）", 0, "問題 0 件",
             reword_both_kou, pre_base=pre_quote_ccc)
    def pre_shared(body):
        def pre(root, skill):
            (skill / "prompts" / "verifier.md").write_text(PROMPT.replace("**AAA ひとつめの行です**\n   - 入れ子は数えない", "**計画ファイル甲 ひとつめの行です**\n" + body).replace(
                "**BBB ふたつめの行です**", "**計画ファイル乙 ふたつめの行です**"))
            (skill / "references" / "line-registry.csv").write_text(registry_text(
                [["V-01", "prompts/verifier.md", "**計画ファイル甲 ひ"] + ROWS[0][3:], ["V-02", "prompts/verifier.md", "**計画ファイル乙 ふ"] + ROWS[1][3:], ROWS[2]]))
        return pre
    def shared_edit(new_a, hiki_a):
        def s(root, skill):
            (skill / "prompts" / "verifier.md").write_text((skill / "prompts" / "verifier.md").read_text().replace(
                "**計画ファイル甲 ひとつめの行です**", new_a).replace("2. **計画ファイル乙 ふたつめの行です**", "2. **計画ファイル乙 二つめの行です**"))
            (skill / "references" / "line-registry.csv").write_text(registry_text(
                [["V-01", "prompts/verifier.md", hiki_a] + ROWS[0][3:], ["V-02", "prompts/verifier.md", "**計画ファイル乙 二"] + ROWS[1][3:], ROWS[2]]))
        return s
    scenario("G89 G83 で、元の項と付け替え先の頭が同じ書き出し（`計画ファイル`）を持っても 1", 1, "付け替えた",
             shared_edit("要点: 計画ファイル乙 二つめの行です", "要点: 計画ファイル乙 二"), pre_base=pre_shared("   - 計画ファイル乙 ふたつめの行です"))
    scenario("G90 G50 で、元の項と引いた先の頭が同じ書き出しを持つとき、自分の頭を言い換えても 0", 0, "問題 0 件",
             shared_edit("**計画ファイル甲 一つめの行です**", "**計画ファイル甲 一"),
             pre_base=pre_shared("   - 入れ子は数えない（下の「計画ファイル乙 ふたつめの行です」と同じ）"))
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
    ("候補の線を超えたときだけにする", "effects", 'if s[3] >= window and s[0]["測り方"] == "指摘"]', 'if s[3] > window and s[0]["測り方"] == "指摘"]', "report"),
    ("登録日より前の周を数える", "effects", '>= r["登録日"]', '< r["登録日"]', "report"),
    ("なしと ID の混在を見ない", "effects", "if none and ids:", "if False and ids:", "report"),
    ("形に合わない行を拾わない", "effects", "elif LABEL_RE.match(line):", "elif False and LABEL_RE.match(line):", "report"),
    ("外した行を見ない", "guard", 'if r["ID"] not in head_ids]', 'if r["ID"] in head_ids]', "guard"),
    ("差分でなく全部の eval を見る", "guard", 'changed.stdout.split("\\n")', 'git(root, "ls-files").stdout.split("\\n")', "guard"),
    ("元の事故の番号を見ない", "guard", "if want and not want <= have:", "if False and want and not want <= have:", "guard"),
    ("graders のブロックを見ない", "guard", 'if not block or not re.search(r"^[ \\t]*-[ \\t]+name:",', 'if not block or False and not re.search(r"^[ \\t]*-[ \\t]+name:",', "guard"),
    ("統合の同趣旨を見ない", "guard", 'base_target["同趣旨"] == r["同趣旨"]', "True", "guard"),
    ("1 項に複数の行を許す", "effects", "if len(hit) > 1:", "if len(hit) > 99:", "check"),
    ("統合元が台帳に残っても許す", "effects", 'elif any(x["ID"] == src for x in rows):', "elif False:", "check"),
    ("統合元の形を見ない", "effects", "if not ID_RE.match(src):", "if False:", "check"),
    ("測れない行を候補に出す", "effects", 'if s[3] >= window and s[0]["測り方"] == "指摘"]', "if s[3] >= window]", "report"),
    ("1 行に 2 つの ID を見ない", "effects", 'if m and re.match(r"^[ ,、]+[A-Z]', 'if False and m and re.match(r"^[ ,、]+[A-Z]', "report"),
    ("登録日を UTC の日付で比べる", "effects", "fromtimestamp(c[3])", "fromtimestamp(c[3], datetime.timezone.utc)", "report"),
    ("履歴に無い計画ファイルを最古にする", "effects", 'else float("inf")', 'else float("-inf")', "report"),
    ("外した行の名指しを前方一致にする", "guard", '{re.escape(line_id)}\\s*$"', '{re.escape(line_id)}"', "guard"),
    ("統合先が別のファイルでも許す", "guard", 'and base_target["ファイル"] == r["ファイル"]:', ":", "guard"),
    ("同趣旨が空でも統合と認める", "guard", 'target is not None and r["同趣旨"] and target["ID"]', 'target is not None and target["ID"]', "guard"),
    ("統合先が base に無くても許す", "guard", 'if base_target is not None and base_target["同趣旨"] == r["同趣旨"]', 'if base_target is None or base_target["同趣旨"] == r["同趣旨"]', "guard"),
    ("元の事故が - でも許す", "guard", 'if not want and inc.group(1).strip() in ("", "-"):', "if False:", "guard"),
    ("case.yaml 以外の yaml も数える", "guard", '/[^/]+/case\\.yaml"', '/[^/]+/[^/]+\\.yaml"', "guard"),
    ("ファイルの変更を見ない", "guard", 'if h["ファイル"] != b["ファイル"]:', "if False:", "guard"),
    ("ファイルをまたぐ同趣旨もまとめる候補に出す", "effects", "if len(same) >= 2:", "if True:", "report"),
    ("付け替えを見ない", "guard", "        if clash:\n", "        if False:\n", "guard"),
    ("言い換えも付け替えと見る（部分文字列で照合）", "guard", "        if clash:\n", '        if h["引き"] in old_text.stdout:\n', "guard"),
    ("base の先端と比べる", "guard", "base = mb.stdout.strip()", "pass", "guard"),
    # #1423
    ("改名を追わない", "guard", 'moved = renamed.get(b["ファイル"]) == h["ファイル"]', "moved = False", "guard"),
    ("付け替え先を言い換えた付け替えを見ない（前方一致だけで照らす）", "guard", "            clash += [f for f in others if flat(f) and flat(f) in cur and f not in clash\n", "            clash += [f for f in [] if flat(f) and flat(f) in cur and f not in clash\n", "guard"),
    ("元の項の頭が残っていても別の項の頭を付け替えと見る", "guard", "        if not (prev is not None and flat(prev) in cur):", "        if True:", "guard"),
    ("HEAD に残った項に限らない（外した項の頭も照らす）", "guard", "and f in new_heads]", "]", "guard"),
    ("統合した項の頭も照らす", "guard", "and not any(f.startswith(m) for m in merged)\n", "and True\n", "guard"),
    ("統合元の除外を言い換えない付け替えにも掛ける", "guard", "others = [f for _, f, _ in base_items if f != prev]", "others = [f for _, f, _ in base_items if f != prev and not any(f.startswith(m) for m in merged)]", "guard"),
    ("元の項が base で本文に引いていた頭も照らす", "guard", 'and not (flat(f) in prev_own and lives_on(f, cur_item[0])', "and not (False", "guard"),
    ("項の続きの段落まで項に含める", "guard", "if line.strip() and not line[:1].isspace():", "if False:", "guard"),
    ("改名をコミットした履歴でだけ見る", "guard", '"-M", base, "--"', '"-M", f"{base}...HEAD", "--"', "guard"),
    # #1430（#1452 で除外を書き直したので、その時点の式は除外の節ごと置き換えて再現する）
    ("本文で引いていた頭の除外を、HEAD に頭として残らない頭にも掛ける", "guard", 'and not (flat(f) in prev_own and lives_on(f, cur_item[0])\n                               and (f in new_heads or (flat(f) not in cur_head and not took_head(cur_head, flat(f), flat(prev or ""))) or lifted_quote(flat(f), prev_lines, head_text, flat(prev or "")))\n                               and kept_quote(flat(f), prev_lines, cur, cur_body))]', "and flat(f) not in prev_own]", "guard"),
    ("1 パス目の式に戻す（新しい引きの前方一致の頭だけ照らす）", "guard", 'and not (flat(f) in prev_own and lives_on(f, cur_item[0])\n                               and (f in new_heads or (flat(f) not in cur_head and not took_head(cur_head, flat(f), flat(prev or ""))) or lifted_quote(flat(f), prev_lines, head_text, flat(prev or "")))\n                               and kept_quote(flat(f), prev_lines, cur, cur_body))]',
     'and (flat(f) not in prev_own or flat(f).startswith(flat(h["引き"])))]', "guard"),
    ("2 パス目の前の式に戻す（新しい引きが当たる項の頭の行に入る頭だけ照らす）", "guard", 'and not (flat(f) in prev_own and lives_on(f, cur_item[0])\n                               and (f in new_heads or (flat(f) not in cur_head and not took_head(cur_head, flat(f), flat(prev or ""))) or lifted_quote(flat(f), prev_lines, head_text, flat(prev or "")))\n                               and kept_quote(flat(f), prev_lines, cur, cur_body))]',
     'and (flat(f) not in prev_own or flat(f) in next((flat(x) for _, x, _ in new_items if x.startswith(h["引き"])), ""))]', "guard"),
    ("引いた先が HEAD に残るかを、頭の文面でなく前方一致で見る", "guard", 'and not (flat(f) in prev_own and lives_on(f, cur_item[0])\n                               and (f in new_heads or (flat(f) not in cur_head and not took_head(cur_head, flat(f), flat(prev or ""))) or lifted_quote(flat(f), prev_lines, head_text, flat(prev or "")))\n                               and kept_quote(flat(f), prev_lines, cur, cur_body))]',
     'and (flat(f) not in prev_own or not any(x.startswith(f) for x in new_heads))]', "guard"),
    # #1452・#1453
    ("PR #1449 の式に戻す（引いた先の項が HEAD に頭のまま残れば除外）", "guard", 'and not (flat(f) in prev_own and lives_on(f, cur_item[0])\n                               and (f in new_heads or (flat(f) not in cur_head and not took_head(cur_head, flat(f), flat(prev or ""))) or lifted_quote(flat(f), prev_lines, head_text, flat(prev or "")))\n                               and kept_quote(flat(f), prev_lines, cur, cur_body))]', "and (flat(f) not in prev_own or f not in new_heads)]", "guard"),
    ("引いた先が別の項として HEAD に残るかを見ない", "guard", 'and not (flat(f) in prev_own and lives_on(f, cur_item[0])', "and not (flat(f) in prev_own", "guard"),
    ("引いた先の ID の行き先を見ない（頭のまま残るときだけ残ると見る）", "guard", "            for r in base_rows:\n                hr = head_by_id.get(r[\"ID\"])\n", "            for r in []:\n                hr = None\n", "guard"),
    ("引いた先の ID が新しい引きの項自身を引いても、別の項として残ると見る", "guard", "x.startswith(hr[\"引き\"]) and x != cur_head", "x.startswith(hr[\"引き\"])", "guard"),
    ("頭の文面が新しい引きの項の本文に残るときの受け継ぎを見ない", "guard", "    if head in cur_body:\n        return True\n", "", "guard"),
    ("本文の代わりに項全体で受け継ぎを見る", "guard", 'cur_body = "" if cur_item is None else flat("\\n".join(cur_item[1].split("\\n")[1:]))', "cur_body = cur", "guard"),
    ("引用の受け継ぎを、引用の後ろの文面だけで見る", "guard", 'if (any(c.isalnum() for c in after) and head + after in cur) or (any(c.isalnum() for c in before) and before + head in cur):', "if any(c.isalnum() for c in after) and head + after in cur:", "guard"),
    ("記号だけの前後も、文面で引用を受け継いだと見る", "guard", 'if (any(c.isalnum() for c in after) and head + after in cur) or (any(c.isalnum() for c in before) and before + head in cur):', "if (after and head + after in cur) or (before and before + head in cur):", "guard"),
    ("行の印を引用の文面に数える", "guard", 'prev_lines = next(([flat(LIST_MARK.sub("", x))', 'prev_lines = next(([flat(x)', "guard"),
    # #1452 の狭いパスの O1
    ("ID の行き先で残る引いた先を、新しい引きの項の頭の行に写しても除外する", "guard", "and (f in new_heads or (flat(f) not in cur_head and not took_head(cur_head, flat(f), flat(prev or \"\"))) or lifted_quote(flat(f), prev_lines, head_text, flat(prev or \"\")))", "and True", "guard"),
    # #1453
    ("頭の行の引いた頭が引用の前後の文面と続いていても、頭の写しと見る", "guard", ' or lifted_quote(flat(f), prev_lines, head_text, flat(prev or ""))', "", "guard"),
    ("引用の手前の文面が元の項の頭と関わらなくても、引用を上げた言い換えと見る", "guard", " and shares(head_text[:j], prev_head):", ":", "guard"),
    ("頭の行の下の折り返しの行を頭に数えない", "guard", 'head_text = flat("\\n".join(head_wrap))', 'head_text = flat(head_wrap[0]) if head_wrap else ""', "guard"),
    ("元の項の頭の書き出しでなく、どこかの 3 字が重なれば言い換えと見る", "guard", "return start is not None and start in text",
     "return any(prev_head[i:i + n] in text for i in range(len(prev_head) - n + 1) if any(c.isalnum() for c in prev_head[i:i + n]))", "guard"),
    ("引用の手前に引いた頭の写しがあっても、引用を上げた言い換えと見る", "guard", " and head not in head_text[:j] and", " and", "guard"),
    # #1522
    ("ID の行き先で残る引いた先の頭が頭の行に無ければ、頭の行が引いた先の頭に寄せた差し替えでも除外する", "guard",
     ' and not took_head(cur_head, flat(f), flat(prev or ""))) or lifted_quote(', ") or lifted_quote(", "guard"),
    ("寄せた差し替えの見分けで、元の項の頭の目印が頭の行に残るかを見ない", "guard", " and not (ko is not None and ko in head_line)", "", "guard"),
    ("寄せた差し替えの見分けで、引いた先の頭の目印が頭の行にあるかを見ない", "guard", "kq is not None and kq in head_line and not", "not", "guard"),
    ("目印を、他方の頭に無い 3 字でなく書き出しの 3 字にする", "guard", " and text[i:i + n] not in other), None)", "), None)", "guard"),
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
