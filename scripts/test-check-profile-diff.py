#!/usr/bin/env python3
"""platform-spec の `check-profile-diff.py`（profile の新しい版との差分から、共有の Q&A 表に起票する候補を出す。#1457）の回帰テスト。

    python3 scripts/test-check-profile-diff.py

**本体はプラグインの中にある**（`plugins/platform-spec/scripts/`）。同じ場所の `check-infra-profile.py` と spec-loop の重ね方・`external-profile.py` を読み込むので、
**一時ディレクトリに本物の spec-loop と platform-spec の写しを並べて**走らせる（隣の `spec-loop` を見つける形）。試料の部品（子の環境・git・状態の取り方）は
`scripts/test-check-infra-profile.py` を読み込む（写さない）。

見るもの:

1. **#1457 の受入基準 1**——2 つのタグの profile と `infra.csv` で、`profile の行` が指す行のうち変わった・消えた・新しい版でリンクの切れた行が、表の行・項目・ID・種類つきで
   候補として名指しされ（1）、指していない行の変化と足した行は名指されない。候補の行に Q&A の番号が無い。走らせた前後で正本と clone が変わらない。
2. **新しい版の決め方**——`--new`・profile を持つタグのうち版の順（`v10` は `v9` より後ろ）が最も後ろのもの・profile を持たないタグを数えない・`タグ`／`確かめたタグ` と同じなら比べない。
3. **止まり方**——設定の違反は clone を読む前に 1・古い版に無い ID は 1・profile を持つタグが無い・古い版に層が無い・新しい版の層を読めないは 4・新しい版に層が無ければ全部「消えた」・
   設定も値も無ければ 0。`--upto`・`--project`・`--clone` を渡す。
4. **候補の性質（プロパティテスト）**——標準ライブラリの `random` で古い層・新しい層・切れたリンク・指した ID を生成し、本体の純粋な関数 `candidates` の (ID, 種類) の集合が
   テストの側で別に計算したものと同じこと（500 例。seed を出す）。**性質を破る変異（「消えた」を出さない）でこのテストが落ちる陽性対照つき。**
5. **本体の定数が `plugins/platform-spec/references/infra-profile.md` の「版の差分と関門」と一致する**（崩すと不一致になる陽性対照つき）。
6. **変異テスト**——本体を 1 箇所ずつ壊し、名指しした試料が期待どおりでなくなること（壊さない写しを同じ置き方で置くと期待どおりになる陰性対照つき）。
   **変異の数は docstring の「守ること」の行の数と同じ**（手で数えない）。変異ごとに、壊す箇所が本体にちょうど 1 回現れることを先に確かめる。

**このテストは実環境を触らない。** `HOME`・`CLAUDE_CONFIG_DIR`・`GIT_CONFIG_GLOBAL` を一時ディレクトリに差し替え、`SPEC_PROFILE_CLONE`・`PLATFORM_SPEC_SPEC_LOOP`・`GIT_*` を子に渡さない。
"""
from __future__ import annotations

import importlib.util
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
PLATFORM = REAL_REPO / "plugins" / "platform-spec"
TARGET = "check-profile-diff.py"
SOURCE = PLATFORM / "scripts" / TARGET
REF_INFRA = PLATFORM / "references" / "infra-profile.md"
REPO = "org/guide"

sys.dont_write_bytecode = True


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tip = load(REAL_REPO / "scripts" / "test-check-infra-profile.py", "test_check_infra_profile")
assert_in_tmp, child_env, git = tip.assert_in_tmp, tip.child_env, tip.git

I_HEAD = tip.I_HEAD
I7_HEAD = tip.I7_HEAD


def infra(*refs: str) -> str:
    items = ["言語", "DBMS", "ホスティング環境", "監視", "認証基盤"]
    return I_HEAD + "".join(f"{items[i]},x,y,z,,Q-F-00{i + 1},決定,{ref}\n" for i, ref in enumerate(refs))


def settings(tag: str = "v1", profile: str = "org", extra: str = "") -> str:
    return f"項目,値\nリポジトリ,{REPO}\nprofile,{profile}\nタグ,{tag}\n{extra}"


I = "docs/v1/shared/infra.csv"
S = "docs/v1/shared/platform/settings.csv"
CLAUDE = "CLAUDE.md"
DECL = f"外部の profile の clone: {REPO} {{clone}}\n"
REFS = ("LANG-1", "DB-1", "HOST-1", "MON-1")
OK = {I: infra(*REFS), S: settings(), CLAUDE: DECL}


def with_(base: dict, **changes) -> dict:
    out = dict(base)
    for key, value in changes.items():
        rel = {"infra": I, "settings": S, "claude": CLAUDE}.get(key, key)
        if value is None:
            out.pop(rel, None)
        else:
            out[rel] = value
    return out


CHANGED = "shared/infra.csv:2: 言語 の profile の行 LANG-1: 変わった（org/guide の org タグ v1 → v10）——列: 要約"
REMOVED = "shared/infra.csv:3: DBMS の profile の行 DB-1: 消えた（org/guide の org タグ v1 → v10）"
BROKEN = "shared/infra.csv:4: ホスティング環境 の profile の行 HOST-1: リンクが切れた（org/guide の org タグ v1 → v10）——docs/nope.md（ファイルがその時点に無い）"

# (名前, 正本のファイル, 引数（{clone}・{project2} を置き換える）, 期待する終了コード, 含むべき文字列（全部）, 含んではならない文字列（どれも）)
CASES: list[tuple[str, dict, list[str], int, tuple[str, ...], tuple[str, ...]]] = [
    ("候補", OK, [], 1, (CHANGED, REMOVED, BROKEN, "起票の候補 4 件"), ("OTHER-1", "NEW-1", "MON-1", "違反: ")),
    ("--new で名指す", OK, ["--new", "v2"], 1, ("タグ v1 → v2", "起票の候補 4 件"), ("v10",)),
    ("--new がタグと同じ", OK, ["--new", "v1"], 0, ("新しい版 v1 は設定のタグと同じ。比べない",), ("起票の候補: ",)),
    ("確かめたタグ", with_(OK, settings=settings(extra="確かめたタグ,v10\n")), [], 0, ("新しい版 v10 は設定の確かめたタグと同じ。比べない",), ("起票の候補: ",)),
    ("確かめたタグが古い", with_(OK, settings=settings(extra="確かめたタグ,v2\n")), [], 1, ("タグ v1 → v10", "起票の候補 4 件"), ()),
    ("新しい版に層が無い", OK, ["--new", "nolayer"], 1,
     ("LANG-1: 消えた", "DB-1: 消えた", "HOST-1: 消えた", "MON-1: 消えた", "（nolayer に基盤の層が無い）"), ("変わった",)),
    ("新しい版の形式の版", OK, ["--new", "fmt2"], 4, ("受け付ける範囲（1 以上 2 未満）の外",), ()),
    ("古い版に層が無い", with_(OK, settings=settings("nolayer")), ["--new", "v1"], 4, ("基盤の層が無い",), ()),
    ("古い版に無い ID", with_(OK, infra=infra("NOPE-1", "MON-1")), [], 1, ("NOPE-1 が org/guide の org（タグ v1）の基盤の層に無い",), ("起票の候補: ",)),
    ("同じ版でも古い版に無い ID", with_(OK, infra=infra("NOPE-1")), ["--new", "v1"], 1, ("NOPE-1 が org/guide の org（タグ v1）の基盤の層に無い", "比べない"), ()),
    ("同じ版でも古い版に層が無い", with_(OK, settings=settings("nolayer")), ["--new", "nolayer"], 4, ("基盤の層が無い",), ()),
    ("新しい版の層の見出し", OK, ["--new", "badhead"], 4, ("形式の版 1 の `ID,要約,リンク,項目` でない: ID,要約,リンク,項目,備考",), ("起票の候補: ",)),
    ("使っていない", {I: I7_HEAD + "言語,x,y,z,,Q-F-001,決定\n"}, [], 0, ("比べるものが無い（platform-spec を使っていない）",), ("違反: ",)),
    ("設定の違反は clone を読む前", with_(OK, settings=settings("v1~1"), claude=None), [], 1, ("タグ 'v1~1' がタグの名前に使えない形",), ("止めた",)),
    ("profile を持つタグが無い", with_(OK, settings=settings(profile="ghost")), [], 4, ("spec-profile/ghost/profile.csv がその時点に無い",), ()),
    ("前の版の時点", with_(OK, **{"docs/v2/shared/infra.csv": infra("NOPE-3")}), ["--upto", "1"], 1, (CHANGED, "起票の候補 4 件"), ("NOPE-3",)),
    ("--project", with_(OK, claude=None), ["--project", "{project2}"], 1, (CHANGED, "起票の候補 4 件"), ()),
    ("引数の clone", with_(OK, claude=None), ["--clone", "{clone}"], 1, ("出所: 引数 --clone", CHANGED), ()),
    ("引数が足りない", OK, ["--no-docs"], 2, ("usage:",), ()),
]

# docstring の「守ること」の行と同じ順の変異。(名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("設定も値も無いのに比べに行く", "            if not refs:\n                print(f\"{base.SETTINGS} も", "            if False:\n                print(f\"{base.SETTINGS} も", "使っていない"),
    ("変わったを出さない", "            if changed:", "            if False:", "候補"),
    ("消えたを出さない", "            if rid not in new:\n                out.append((where, item, rid, KIND_REMOVED, \"\"))\n                continue",
     "            if rid not in new:\n                continue", "候補"),
    ("新しい版に層が無いのを 4 にする", "new_layer = self.layer(clone, new_commit, name, new, missing_ok=True)",
     "new_layer = self.layer(clone, new_commit, name, new, missing_ok=False)", "新しい版に層が無い"),
    ("切れたリンクを出さない", "            if rid in cut:", "            if False:", "候補"),
    ("指していない ID も比べる", "    for where, item, ids in refs:\n        for rid in ids:\n            if rid not in old_rows:",
     "    for where, item, ids in refs + [(\"x\", \"x\", sorted(old_rows))]:\n        for rid in ids:\n            if rid not in old_rows:", "候補"),
    ("候補に番号を振る", "self.notes.append(f\"{CANDIDATE}{where}:", "self.notes.append(f\"{CANDIDATE}Q-F-901 {where}:", "候補"),
    ("--new を使わない", "new = self.new if self.new is not None else self.newest(clone, name)", "new = self.newest(clone, name)", "--new で名指す"),
    ("版の順で並べない", "\"--sort=-v:refname\"", "\"--sort=-refname\"", "候補"),
    ("profile を持たないタグも数える", "            if want in ext.list_files(clone, commit):\n                return tag", "            return tag", "候補"),
    ("タグと同じでも比べる", "            if new in (old, checked):", "            if new == checked:", "--new がタグと同じ"),
    ("確かめたタグと同じでも比べる", "            if new in (old, checked):", "            if new == old:", "確かめたタグ"),
    ("同じ版なら古い版を照らさない", "        old_layer = self.layer(clone, old_commit, name, old, missing_ok=False)\n        for where, item, ids in refs:",
     "        if self.new in (old, checked):\n            return self.finish()\n        old_layer = self.layer(clone, old_commit, name, old, missing_ok=False)\n        for where, item, ids in refs:",
     "同じ版でも古い版に無い ID"),
    ("層の見出しを見ない", "                if head != base.LAYER_COLUMNS:", "                if False:", "新しい版の層の見出し"),
    ("古い版に無い ID を通す", "                if rid not in old_layer.rows:", "                if False:", "古い版に無い ID"),
    ("古い版に層が無いのを 4 にしない", "old_layer = self.layer(clone, old_commit, name, old, missing_ok=False)",
     "old_layer = self.layer(clone, old_commit, name, old, missing_ok=True)", "古い版に層が無い"),
    ("新しい版の層を読めなくても通す", "        except ext.Undetermined as e:\n            raise Stop(f\"profile {name}（タグ {tag}）を読めない: {e}\") from None",
     "        except ext.Undetermined as e:\n            return None", "新しい版の形式の版"),
    ("設定の違反でも clone を読む", "        if self.violations:\n            return self.finish()\n        ext = self.ext", "        ext = self.ext",
     "設定の違反は clone を読む前"),
    ("--upto を渡さない", "problems, _, whole, _ = self.versions.merge(self.docs, self.upto)", "problems, _, whole, _ = self.versions.merge(self.docs, None)", "前の版の時点"),
    ("--project を使わない", "self.project = project if project is not None else docs.resolve().parent", "self.project = docs.resolve().parent", "--project"),
    ("--clone を渡さない", "ext.find_clone(repo, self.clone, self.project)", "ext.find_clone(repo, None, self.project)", "引数の clone"),
]

failures: list[str] = []
# 候補の行に Q&A の番号（`Q-F-001`・`D-S-001` の形）が無いこと（番号を振らない）
NUMBER = re.compile(r"\b[QD]-[A-Z0-9]+-\d+")
CANDIDATE_HEAD = "起票の候補: "


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


PROFILE = "層,形式の版,ファイル,重ねる先\n基盤,1,infra.csv,\n"
HEAD = "ID,要約,リンク,項目\n"
LAYER_A = (HEAD + "LANG-1,Python 3.12,docs/guide.md,言語\nDB-1,PostgreSQL 16,,DBMS\nHOST-1,AWS ECS,docs/guide.md,ホスティング環境\n"
           "MON-1,CloudWatch,,監視\nOTHER-1,なにか,,認証基盤\n")
# A から: LANG-1 の要約・DB-1 を消す・HOST-1 のリンクを切る・OTHER-1（指していない）を変える・NEW-1 を足す
LAYER_B = (HEAD + "LANG-1,Python 3.13,docs/guide.md,言語\nHOST-1,AWS ECS,docs/nope.md,ホスティング環境\n"
           "MON-1,CloudWatch,,監視\nOTHER-1,べつの,,認証基盤\nNEW-1,新しい,,DBMS\n")


def make_profile(root: Path, env: dict) -> Path:
    """タグ v1（A）・v2（B）・v9（A）・v10（B）・nolayer・fmt2・badhead（見出しに列を足した B）・zz-noprofile（profile を持たない）。"""
    assert_in_tmp(root)
    root.mkdir(parents=True)
    git(root, env, "init", "-q", "-b", "main")
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text("# 言語\n", encoding="utf-8")
    base = root / "spec-profile" / "org"

    def commit(tag: str, profile: str | None, layer: str | None) -> None:
        if profile is None:
            shutil.rmtree(root / "spec-profile", ignore_errors=True)
        else:
            base.mkdir(parents=True, exist_ok=True)
            (base / "profile.csv").write_text(profile, encoding="utf-8")
            if layer is not None:
                (base / "infra.csv").write_text(layer, encoding="utf-8")
        git(root, env, "add", "-A")
        git(root, env, "commit", "-q", "--allow-empty", "-m", tag)
        git(root, env, "tag", tag)

    commit("v1", PROFILE, LAYER_A)
    commit("v2", PROFILE, LAYER_B)
    commit("v9", PROFILE, LAYER_A)
    commit("v10", PROFILE, LAYER_B)
    commit("nolayer", "層,形式の版,ファイル,重ねる先\n画面,1,infra.csv,web-spa\n", LAYER_A)
    commit("fmt2", PROFILE.replace("基盤,1,", "基盤,2,"), LAYER_B)
    commit("badhead", PROFILE, LAYER_B.replace("ID,要約,リンク,項目\n", "ID,要約,リンク,項目,備考\n").replace(",言語\n", ",言語,x\n")
           .replace(",ホスティング環境\n", ",ホスティング環境,x\n").replace(",監視\n", ",監視,x\n").replace(",認証基盤\n", ",認証基盤,x\n")
           .replace(",DBMS\n", ",DBMS,x\n"))
    commit("zz-noprofile", None, None)
    git(root, env, "checkout", "-q", "v1")
    return root


def lay_out(plugins: Path, spec_loop: Path, source: str | None = None) -> Path:
    assert_in_tmp(plugins)
    plugins.mkdir(parents=True)
    root = plugins / "platform-spec"
    shutil.copytree(PLATFORM, root, ignore=shutil.ignore_patterns("__pycache__"))
    if source is not None:
        (root / "scripts" / TARGET).write_text(source, encoding="utf-8")
    (plugins / "spec-loop").symlink_to(spec_loop, target_is_directory=True)
    return root


def run_case(platform: Path, work: Path, files: dict, args: list[str], tokens: dict, env: dict) -> tuple[int, str]:
    assert_in_tmp(work)
    project = work / "project"
    (project / "docs").mkdir(parents=True)
    for rel, body in files.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.replace("{clone}", tokens["clone"]), encoding="utf-8")
    other = work / "project2"  # `--project` が指す、CLAUDE.md だけを置いた場所
    other.mkdir()
    (other / CLAUDE).write_text(DECL.replace("{clone}", tokens["clone"]), encoding="utf-8")
    argv = [a.format(clone=tokens["clone"], project2=str(other)) for a in args]
    argv = [] if "--no-docs" in argv else [str(project / "docs"), *argv]
    elsewhere = work / "elsewhere"
    elsewhere.mkdir()
    proc = subprocess.run([sys.executable, "-I", str(platform / "scripts" / TARGET), *argv], capture_output=True, text=True, cwd=elsewhere, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def as_expected(name: str, result: tuple[int, str]) -> bool:
    _, _, _, code, present, absent = next(case for case in CASES if case[0] == name)
    numbered = [line for line in result[1].splitlines() if line.startswith(CANDIDATE_HEAD) and NUMBER.search(line)]
    return (result[0] == code and all(p in result[1] for p in present) and not any(a in result[1] for a in absent)
            and "Traceback" not in result[1] and not numbered)


# ---- プロパティテスト（候補の集合）

def model(refs, old_rows, new_rows, broken) -> set[tuple[str, str]]:
    """テストの側で別に計算した候補の (ID, 種類)。"""
    new = new_rows or {}
    cut = {rid for rid, _, _ in broken}
    out = set()
    for _, _, ids in refs:
        for rid in ids:
            if rid not in old_rows:
                continue
            if rid not in new:
                out.add((rid, "消えた"))
                continue
            if old_rows[rid] != new[rid]:
                out.add((rid, "変わった"))
            if rid in cut:
                out.add((rid, "リンクが切れた"))
    return out


def property_candidates(module, examples: int = 500, seed: int | None = None) -> tuple[int, list[str]]:
    seed = random.randrange(2 ** 32) if seed is None else seed
    rng = random.Random(seed)
    problems = []
    ids = [f"X-{i}" for i in range(10)]
    for n in range(examples):
        def layer() -> dict:
            rows = {}
            for rid in rng.sample(ids, rng.randint(0, 8)):
                rows[rid] = {"ID": rid, "要約": rng.choice(["a", "b"]), "リンク": rng.choice(["", "docs/a.md", "docs/b.md"]),
                             "項目": rng.choice(["言語", "DBMS"])}
            return rows
        old = layer()
        new = None if rng.random() < 0.1 else layer()
        broken = [(rid, "docs/x.md", "ファイルがその時点に無い") for rid in (new or {}) if rng.random() < 0.3]
        pointed = [rid for rid in rng.sample(ids, rng.randint(0, 6)) if rid in old]
        refs = [(f"shared/infra.csv:{i + 2}", "項目", [rid]) for i, rid in enumerate(pointed)]
        got = {(rid, kind) for _, _, rid, kind, _ in module.candidates(refs, old, new, broken)}
        want = model(refs, old, new, broken)
        if got != want:
            problems.append(f"例 {n}: 得た {sorted(got - want)} 足りない {sorted(want - got)}")
            break
        if any(rid not in pointed for rid, _ in got):
            problems.append(f"例 {n}: 指していない ID が候補に出た")
            break
    return seed, problems


# ---- 原本との突き合わせ

def reference_mismatches(module, infra_md: str) -> list[str]:
    problems = []
    try:
        diff = tip.section(infra_md, "## 版の差分と関門")
    except ValueError as e:
        return [f"原本の見出しが無い: {e}"]
    kinds = tip.first_cells(diff)
    if kinds != [module.KIND_CHANGED, module.KIND_REMOVED, module.KIND_BROKEN]:
        problems.append(f"候補の種類が違う（原本 {kinds} ／ 本体 {module.KIND_CHANGED}・{module.KIND_REMOVED}・{module.KIND_BROKEN}）")
    if f"`{module.CANDIDATE}` で始まる行" not in diff:
        problems.append(f"候補の行の頭 {module.CANDIDATE!r} が原本に無い")
    if "`v:refname`" not in diff:
        problems.append("版の順（v:refname）が原本に無い")
    if f"`{module.base.SETTING_CHECKED}`" not in diff:
        problems.append(f"任意の項目 {module.base.SETTING_CHECKED} が原本の「版の差分と関門」に無い")
    return problems


REFERENCE_MUTATIONS = [
    "| `変わった` |", "| `消えた` |", "| `リンクが切れた` |", "`起票の候補: ` で始まる行", "（git の `v:refname`。",
]


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    source = SOURCE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="profile-diff-test-") as tmp_name:
        tmp = Path(tmp_name)
        env = child_env(tmp)
        clone = make_profile(tmp / "profile", env)
        spec_loop = tmp / "spec-loop-copy"
        shutil.copytree(SPEC_LOOP, spec_loop, ignore=shutil.ignore_patterns("__pycache__"))
        tokens = {"clone": str(clone)}
        platform = lay_out(tmp / "plugins", spec_loop)
        before_clone = tip.clone_state(clone, env)
        for index, (name, files, args, _, _, _) in enumerate(CASES):
            result = run_case(platform, tmp / f"case{index}", files, args, tokens, env)
            check(f"試料が期待どおりでない（番号の無い候補の行を含む）: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-700:]}")

        # 読むだけ: clone と正本が変わらない・__pycache__ ができない
        check("clone の状態が変わった", tip.clone_state(clone, env) == before_clone)
        work = tmp / "readonly"
        run_case(platform, work, OK, [], tokens, env)
        project = work / "project"
        before_tree = tip.tree_state(project)
        proc = subprocess.run([sys.executable, "-I", str(platform / "scripts" / TARGET), str(project / "docs")], capture_output=True, text=True,
                              cwd=work / "elsewhere", env=env)
        check("読むだけの確かめの試料が 1 でない", proc.returncode == 1, proc.stdout + proc.stderr)
        check("正本のファイルが変わった", tip.tree_state(project) == before_tree)
        caches = [str(p) for p in list((tmp / "plugins").rglob("__pycache__")) + list(spec_loop.rglob("__pycache__"))]
        check("写したプラグインに __pycache__ ができた", not caches, ", ".join(caches))

        # プロパティテストと、性質を破る変異で落ちる陽性対照
        module = load(platform / "scripts" / TARGET, "check_profile_diff_under_test")
        seed, problems = property_candidates(module)
        check(f"候補の性質が破れた（seed {seed}）", not problems, "; ".join(problems))
        print(f"プロパティテスト: 500 例・seed {seed}")
        broken_src = source.replace(MUTATIONS[2][1], MUTATIONS[2][2])
        check("性質を破る変異の写しが作れない", broken_src != source)
        mutant_dir = tmp / "property-mutant"
        lay_out(mutant_dir, spec_loop, broken_src)
        mutant = load(mutant_dir / "platform-spec" / "scripts" / TARGET, "check_profile_diff_mutant")
        _, mutant_problems = property_candidates(mutant, seed=seed)
        check("性質を破る変異（消えたを出さない）でプロパティテストが落ちない", bool(mutant_problems))

        # 原本との突き合わせ
        infra_md = REF_INFRA.read_text(encoding="utf-8")
        problems = reference_mismatches(module, infra_md)
        check("本体の定数が references と一致しない", not problems, "; ".join(problems))
        for before in REFERENCE_MUTATIONS:
            if infra_md.count(before) != 1:
                check(f"崩す箇所が 1 回でない: {before}", False, f"{infra_md.count(before)} 回")
                continue
            check(f"崩しても不一致にならない: {before}", bool(reference_mismatches(module, infra_md.replace(before, before.replace("`", "")))))
        head, _, rest = infra_md.partition("## 版の差分と関門")
        check("崩しても不一致にならない: 版の差分と関門の `確かめたタグ`",
              bool(reference_mismatches(module, head + "## 版の差分と関門" + rest.replace("`確かめたタグ`", "確かめたタグ"))))

        # 変異
        guarded = tip.guarded_lines(source)
        check("変異の数が「守ること」の行の数と違う", len(guarded) == len(MUTATIONS), f"守ること {len(guarded)} 行・変異 {len(MUTATIONS)} 件")
        killers = {killer for _, _, _, killer in MUTATIONS}
        check("変異の殺す試料が試料に無い", killers <= set(names), ", ".join(sorted(killers - set(names))))
        control = lay_out(tmp / "control", spec_loop, source)
        for index, killer in enumerate(sorted(killers)):
            files, args = next((f, a) for n, f, a, _, _, _ in CASES if n == killer)
            result = run_case(control, tmp / f"controlwork{index}", files, args, tokens, env)
            check(f"壊さない写しで殺す試料が期待どおりでない: {killer}", as_expected(killer, result), result[1][-300:])
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = lay_out(tmp / f"mut{index}", spec_loop, source.replace(before, after))
            files, args = next((f, a) for n, f, a, _, _, _ in CASES if n == killer)
            result = run_case(mutated, tmp / f"mutwork{index}", files, args, tokens, env)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result[1][-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件（守ること {len(guarded)} 行）・references の崩し {len(REFERENCE_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
