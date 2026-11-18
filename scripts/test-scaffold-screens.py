#!/usr/bin/env python3
"""`scaffold.py` の画面の表の参考資料（#1099）と、照合が画面の表の変更を拾うことの回帰テスト。

    python3 scripts/test-scaffold-screens.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/scaffold.py`）。一時ディレクトリに `plugins/spec-loop/`（本物の `.claude-plugin/` と `scripts/` の写し）と
`plugins/screen-spec/`（本物の写し。生成器の版を変えるときは写しの `plugin.json` だけを書き換える）を並べ、画面の表を持つ正本を置いて、
本物の `scaffold.py` を走らせる——画面の関門（screen-spec の `check-screens.py`）も生成したモック（screen-spec の `build-mock.py`）も本物が走る。
正本の試料は `scripts/test-screen-gate.py` の `reflected()`（screen-spec のテストの正しい画面の表を、Q&A を全部反映済みにしたもの）を読み込んで使う（試料の形を写さない）。

見るもの:

1. **#1099 の受入基準 1**——生成器の版だけを変えた例（v1 を screen-spec 0.3.0 の写しで、v2 を版だけ 9.9.9 にした写しで作る。v2 は仕様の文章だけを直す）で、
   v2 の scaffold が機能を「変更」と数えない（本文 0 件）。写しのモックは新しい版の印を持つ（生成器の版が実際に違ったことの確かめ）。
   **陽性対照**: 同じ試料で v2 の中間表現の F-001 の題を直せば、F-001 は「変更」になる。
2. **#1099 の受入基準 2**——画面の表を持つ正本で、本文の `## 参考資料` に、機能を挙げる画面ごとの仕様書・svg（在るものだけ）・生成したモックが載り、
   写しが `scaffold/refs/` に元のバイト（モックは生成器の出力のまま）で在り、目録に載る。2 つの画面に挙がる機能は 2 つの画面を並べる。
   中間表現の `refs` と重なるパスは 2 度並べない。**照合（`check-signoff.py`）は 2 つのタグの間で `screens.csv` だけが違えば一致と言わない**（陽性対照: 同じなら 0）。
3. **`--check` は生成し直さない**——書いた直後は 0（`build/mock/` を消しても作らない）・生成器の版だけを変えても 0・写しを手で直せば 1・写しを消せば 1（「無い」と名指す）。
   `--dry-run` はモックも `scaffold/` も作らない。
4. **書く生成でモックを作れなければ何も書かない**——偽の生成器が 1 なら 1、4 なら 2。`scaffold/` は前のまま、前の Issue の本文は消す。
5. **回帰**——画面の表が無い正本と、画面の表はあるがどの画面も機能を挙げない正本で、`scaffold/` と本文が同じバイト（モックも `scaffold/refs/` も作らない）。
   画面が機能を挙げなくなった（v2 で `機能` を空にした）画面の写しは消える。
6. **写し**——本文の文言の定数が `references/handoff-issue.md` に原文のまま在る。生成したモックの置き場所と生成器の名前が screen-spec の `build-mock.py` の定数と同じ。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME` を一時ディレクトリにし、`CLAUDE_CONFIG_DIR`・`SPEC_LOOP_SCREEN_SPEC`・
`SCREEN_SPEC_SPEC_LOOP`・`PYTHONDONTWRITEBYTECODE` を外す。git は一時のリポジトリにだけ使い、`HOME`・`GIT_CONFIG_GLOBAL` を差し替える。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。壊す箇所が本体にちょうど 1 回現れることを先に確かめる。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
SCREEN_SPEC = REAL_REPO / "plugins" / "screen-spec"
TARGET = "scaffold.py"
HANDOFF_REF = SPEC_LOOP / "references" / "handoff-issue.md"
TREE_REF = SPEC_LOOP / "references" / "tree.md"
SPEC_GAP_REF = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "references" / "spec-gap.md"

sys.dont_write_bytecode = True


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate_test = load(REAL_REPO / "scripts" / "test-screen-gate.py", "test_screen_gate")
t = gate_test.t  # screen-spec の `test-check-screens.py`（表の試料の部品）
assert_in_tmp = gate_test.assert_in_tmp

failures: list[str] = []

# ---- 正本の試料

IR = {"spec_ir_version": 1, "title": "受注", "features": [
    {"id": "F-001", "title": "受注を探す", "source": ["spec/rules.md"], "qa": [],
     "operation": {"id": "find_orders", "method": "GET", "path": "/orders", "input": {"q": {"type": "string"}},
                   "output": {"n": {"type": "integer"}}},
     "cases": [{"id": "F-001-C1", "title": "探す", "input": {"q": "a"}, "expected": {"n": 0}}]},
    {"id": "F-002", "title": "受注を入れる", "source": ["spec/rules.md"], "qa": [],
     "operation": {"id": "add_order", "method": "POST", "path": "/orders/new", "input": {"name": {"type": "string"}},
                   "output": {"ok": {"type": "boolean"}}},
     "cases": [{"id": "F-002-C1", "title": "入れる", "input": {"name": "a"}, "expected": {"ok": True}}]}]}
SVG = "<svg xmlns=\"http://www.w3.org/2000/svg\"><text>S-001</text></svg>\n"
WIRE = "v1/requirements/screens/wireframes/S-001.svg"
# S-002 は F-001 と F-002 を挙げる（1 つの画面が複数の機能を持つ。#1081 の決めること 8）。svg は S-001 だけ
S2_BOTH = t.S2.replace(",入力,F-002,,", ",入力,F-001、F-002,,")
assert S2_BOTH != t.S2
RECORD = "回,日付,結果,条件2〜4,要求の行,決定表の行,テストケース,仕様の行,判断,機能\n1,2026-11-02,抜けた,満たす,10,5,9,44,-,-\n"


def base(ir: dict | None = None) -> dict[str, object]:
    files = gate_test.reflected()
    files[t.S] = t.S_HEAD + t.S1 + S2_BOTH
    files[WIRE] = SVG
    files["v1/spec/spec_ir.json"] = json.dumps(ir or IR, ensure_ascii=False, indent=2)
    return files


def unlinked() -> dict[str, object]:
    """画面の表はあるが、どの画面も機能を挙げない。"""
    files = base()
    s1, s2 = t.S1.replace(",一覧と絞り込み,F-001,,", ",一覧と絞り込み,,,"), t.S2.replace(",入力,F-002,,", ",入力,,,")
    assert s1 != t.S1 and s2 != t.S2
    files[t.S] = t.S_HEAD + s1 + s2
    return files


def no_screens() -> dict[str, object]:
    files = {k: v for k, v in base().items() if "requirements/screens/" not in k}
    return files


def with_refs(files: dict[str, object], refs: list[str]) -> dict[str, object]:
    ir = json.loads(files["v1/spec/spec_ir.json"])
    ir["features"][0]["refs"] = refs
    files["v1/spec/spec_ir.json"] = json.dumps(ir, ensure_ascii=False, indent=2)
    return files


# ---- 置き方と走らせ方

def set_version(root: Path, version: str) -> None:
    manifest = root / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["version"] = version
    manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def fake_mock(root: Path, code: int) -> None:
    (root / "scripts" / "build-mock.py").write_text(f"import sys\nprint('偽の生成器')\nraise SystemExit({code})\n", encoding="utf-8")


class World:
    def __init__(self, work: Path, files: dict[str, object], source: str | None = None) -> None:
        assert_in_tmp(work)
        self.work = work
        self.plugins = work / "plugins"
        self.spec_loop = gate_test.copy_spec_loop(self.plugins / "spec-loop")
        if source is not None:
            (self.spec_loop / "scripts" / TARGET).write_text(source, encoding="utf-8")
        self.screen_spec = gate_test.copy_screen_spec(self.plugins / "screen-spec")
        self.repo = work / "repo"
        gate_test.write_docs(self.repo / "docs", files)
        self.record(1)
        self.home = work / "home"
        self.home.mkdir()

    def record(self, number: int) -> None:
        folder = self.repo / "spec-review"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"v{number}.csv").write_text(RECORD, encoding="utf-8")

    def env(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_CONFIG_DIR", "SPEC_LOOP_SCREEN_SPEC", "SCREEN_SPEC_SPEC_LOOP", "PYTHONDONTWRITEBYTECODE")}
        env["HOME"] = str(self.home)
        return env

    def scaffold(self, *args: str) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, str(self.spec_loop / "scripts" / TARGET), "--repo", str(self.repo), *args],
                              capture_output=True, text=True, env=self.env())
        return proc.returncode, proc.stdout + proc.stderr

    def body(self, fid: str) -> str:
        return (self.repo / "build" / "scaffold" / "issues" / f"{fid}.md").read_text(encoding="utf-8")

    def bodies(self) -> list[str]:
        folder = self.repo / "build" / "scaffold" / "issues"
        return sorted(p.stem for p in folder.glob("F-*.md")) if folder.is_dir() else []

    def design(self, data: str | bytes | None) -> None:
        """正本の根の `design/sources.csv`（#1156。版の外）を置く（None なら消す）。"""
        path = self.repo / "design" / "sources.csv"
        if data is None:
            if path.exists():
                path.unlink()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))

    def snapshot(self, *parts: str) -> dict[str, bytes]:
        found = {}
        for part in parts:
            root = self.repo / part
            if root.is_dir():
                found.update({f"{part}/{p.relative_to(root).as_posix()}": p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()})
        return found


def check(name: str, problem: str | None) -> None:
    if problem:
        failures.append(f"{name}: {problem}")


def refs_section(body: str) -> str:
    return body.split("\n## 参考資料\n\n", 1)[1].split("\n\n## 作らないもの\n", 1)[0]


# 本文の文言（`references/handoff-issue.md` の「参考資料」の写し——下の 6 で突き合わせる）
NOTE = ("**参考資料は受入基準ではない**——受入基準は上の Red テストの表である。参考資料（UI モック・業務フロー・画面遷移の図など）は、"
        "見た目・配置・機能どうしのつながりを読むためのもの。参考資料が Red テスト・仕様の原文と食い違うと読めたら、"
        "実装で決めず、仕様の穴として Q&A 表に起票する（下の「仕様の穴を見つけたら」）。")
SCREENS_NOTE = ("画面の表（`requirements/screens/data/screens.csv` の `機能` の列）がこの機能を挙げる画面——仕様書・ワイヤーフレームの書き出し・生成したモック。"
                "**生成したモックは画面の表から作った生成物で、承認の対象は画面の表である**——機能の変更の判定には使わない。モックのコードを実装に流用しない。")
DESIGN_NOTE = ("**デザインの正本**（`design/sources.csv`。版の外にあり、承認の対象ではない）——この機能の画面の見た目（色・余白・フォント・大きさ・飾り）は、ここを正とする。"
               "dev-loop は、この段落があれば、Red テストの表とは別に、見た目がデザインの正本と合うことを受入基準に足し、比べる手段が無ければ BLOCKED にする"
               "（dev-loop の `spec-gap.md` の「デザインの正本」）。デザインの正本が Red テスト・仕様の原文・画面の表と食い違うと読めたら、"
               "実装で決めず、仕様の穴として Q&A 表に起票する（下の「仕様の穴を見つけたら」）。")
TAIL = "（`build/merged/` は上の `## 仕様` のコマンドで作る。写しは `scaffold/` の契約で、正本と開発のリポジトリが別でも `scaffold/` を写せば届く。）"


def copied(rel: str) -> str:
    return f"  - `build/merged/{rel}`（写し: `scaffold/refs/{rel}`）"


def mocked(screen: str, number: int = 1) -> str:
    return f"  - `build/mock/v{number}/index.html#screen={screen}`（生成したモック。写し: `scaffold/refs/mock/index.html#screen={screen}`）"


def generated_note(number: int = 1) -> str:
    return (f"（`build/mock/v{number}/index.html` は scaffold の書く生成が screen-spec の `scripts/build-mock.py` で作り、commit しない"
            "——写しは `scaffold/` の契約である。）")


LIST_MD = "requirements/screens/order-list.md"
NEW_MD = "requirements/screens/order-new.md"
WIRE_REL = "requirements/screens/wireframes/S-001.svg"

EXPECTED = {
    "F-001": "\n".join([NOTE, "", SCREENS_NOTE, "",
                        "- 画面 `S-001`（受注一覧）", copied(LIST_MD), copied(WIRE_REL), mocked("S-001"),
                        "- 画面 `S-002`（受注登録）", copied(NEW_MD), mocked("S-002"),
                        "", generated_note(), "", TAIL]),
    "F-002": "\n".join([NOTE, "", SCREENS_NOTE, "",
                        "- 画面 `S-002`（受注登録）", copied(NEW_MD), mocked("S-002"),
                        "", generated_note(), "", TAIL]),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---- 試料（work → 問題か None）

def case_refs_listed(work: Path, source: str | None) -> str | None:
    """受入基準 2 の後半: 本文の参考資料・写し・目録。"""
    w = World(work, base(), source)
    code, out = w.scaffold()
    if code != 0:
        return f"exit={code}: {out[-600:]}"
    for fid, want in EXPECTED.items():
        got = refs_section(w.body(fid))
        if got != want:
            return f"{fid} の参考資料の節が違う:\n{got}\n---- 期待:\n{want}"
    docs = w.repo / "docs" / "v1"
    for rel in (LIST_MD, NEW_MD, WIRE_REL):
        copy = w.repo / "scaffold" / "refs" / rel
        if not copy.is_file() or copy.read_bytes() != (docs / rel).read_bytes():
            return f"写し scaffold/refs/{rel} が無いか、元のバイトと違う"
    mock = w.repo / "build" / "mock" / "v1" / "index.html"
    copy = w.repo / "scaffold" / "refs" / "mock" / "index.html"
    if not mock.is_file() or not copy.is_file() or copy.read_bytes() != mock.read_bytes():
        return "生成したモックの写しが無いか、生成器の出力と違う"
    index = (w.repo / "scaffold" / "refs" / "index.md").read_text(encoding="utf-8").splitlines()
    for rel, data in ((LIST_MD, (docs / LIST_MD).read_bytes()), (NEW_MD, (docs / NEW_MD).read_bytes()),
                      (WIRE_REL, SVG.encode("utf-8")), ("mock/index.html", copy.read_bytes())):
        line = f"- `{rel}`（sha256: `{sha(data)}`）"
        if line not in index:
            return f"目録に {line!r} が無い"
    return None


def case_overlap(work: Path, source: str | None) -> str | None:
    """中間表現の `refs` と重なるパスは 2 度並べない。"""
    w = World(work, with_refs(base(), [LIST_MD]), source)
    code, out = w.scaffold()
    if code != 0:
        return f"exit={code}: {out[-600:]}"
    section = refs_section(w.body("F-001"))
    count = section.count(f"`build/merged/{LIST_MD}`")
    if count != 1:
        return f"中間表現の refs と画面の表で重なる {LIST_MD} が {count} 回並んだ:\n{section}"
    return None if f"- `build/merged/{LIST_MD}`（写し: `scaffold/refs/{LIST_MD}`）" in section.splitlines() else f"refs の行が無い:\n{section}"


def v2_files(retitle: bool) -> dict[str, object]:
    files = {"v2/spec/rules.md": "# 業務ルール\n\n受注は登録できる。直した。\n"}
    if retitle:
        feature = json.loads(json.dumps(IR["features"][0]))
        feature["title"] = "受注を探す（v2）"
        files["v2/spec/spec_ir.json"] = json.dumps({"features": [feature]}, ensure_ascii=False, indent=2)
    return files


def generator_only(retitle: bool) -> Callable[[Path, str | None], str | None]:
    def run(work: Path, source: str | None) -> str | None:
        """受入基準 1: v1 は 0.3.0 の写し、v2 は版だけ 9.9.9 の写しで作る。"""
        w = World(work, base(), source)
        first = json.loads((w.screen_spec / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        code, out = w.scaffold()
        if code != 0:
            return f"v1 の生成: exit={code}: {out[-600:]}"
        before = (w.repo / "scaffold" / "refs" / "mock" / "index.html").read_text(encoding="utf-8")
        gate_test.write_docs(w.repo / "docs", v2_files(retitle))
        w.record(2)
        set_version(w.screen_spec, "9.9.9")
        code, out = w.scaffold()
        if code != 0:
            return f"v2 の生成: exit={code}: {out[-600:]}"
        after = (w.repo / "scaffold" / "refs" / "mock" / "index.html").read_text(encoding="utf-8")
        if f"screen-spec {first}" not in before or "screen-spec 9.9.9" not in after or "screen-spec 9.9.9" in before:
            return "生成器の版が v1 と v2 で違わない（試料が判別していない）"
        found = w.bodies()
        if retitle:
            if found != ["F-001"]:
                return f"陽性対照: 中間表現の題を直した F-001 だけが本文になるはず: {found}"
            body = w.body("F-001")
            return None if "<!-- spec-loop-change: modify; base=v1 -->" in body and mocked("S-001", 2) in body else f"F-001 が変更の本文でない:\n{body[:400]}"
        if found:
            return f"生成器の版だけを変えたのに本文を作った: {found}（{out[-400:]}）"
        return None if "Issue の本文 0 件" in out else f"出力に本文 0 件が無い: {out[-400:]}"
    return run


def case_check(work: Path, source: str | None) -> str | None:
    """`--check` は生成し直さない。"""
    w = World(work, base(), source)
    code, out = w.scaffold()
    if code != 0:
        return f"exit={code}: {out[-600:]}"
    shutil.rmtree(w.repo / "build")
    code, out = w.scaffold("--check")
    if code != 0:
        return f"書いた直後の --check が 0 でない: exit={code}: {out[-600:]}"
    if (w.repo / "build").exists():
        return "--check が build/ を書いた（モックを生成し直した）"
    set_version(w.screen_spec, "9.9.9")
    code, out = w.scaffold("--check")
    if code != 0:
        return f"生成器の版だけを変えた --check が 0 でない: exit={code}: {out[-600:]}"
    copy = w.repo / "scaffold" / "refs" / "mock" / "index.html"
    original = copy.read_bytes()
    copy.write_bytes(original.replace("受注一覧".encode("utf-8"), "受注いちらん".encode("utf-8")))
    code, out = w.scaffold("--check")
    if code != 1 or "scaffold/refs/index.md: 今の入力から作るものと違う" not in out:
        return f"手で直したモックの写しを古いと言わない: exit={code}: {out[-600:]}"
    copy.unlink()
    code, out = w.scaffold("--check")
    if code != 1 or "scaffold/refs/mock/index.html: 無い（生成したモックの写し" not in out:
        return f"消したモックの写しを無いと言わない: exit={code}: {out[-600:]}"
    return None


def case_dry_run(work: Path, source: str | None) -> str | None:
    w = World(work, base(), source)
    code, out = w.scaffold("--dry-run")
    if code != 0:
        return f"exit={code}: {out[-600:]}"
    written = [p for p in ("build", "scaffold") if (w.repo / p).exists()]
    return f"--dry-run が {written} を書いた" if written else None


def failing_mock(mock_code: int, expected: int) -> Callable[[Path, str | None], str | None]:
    def run(work: Path, source: str | None) -> str | None:
        w = World(work, base(), source)
        code, out = w.scaffold()
        if code != 0:
            return f"前段の生成: exit={code}: {out[-600:]}"
        before = w.snapshot("scaffold")
        fake_mock(w.screen_spec, mock_code)
        code, out = w.scaffold()
        if code != expected:
            return f"生成器が {mock_code} のとき exit={code}（期待 {expected}）: {out[-600:]}"
        if w.snapshot("scaffold") != before:
            return "モックを作れなかったのに scaffold/ を書き換えた"
        if (w.repo / "build" / "scaffold" / "issues").exists():
            return "前の Issue の本文を消していない"
        return None if "偽の生成器" in out else f"生成器の出力を写していない: {out[-400:]}"
    return run


def case_unlinked(work: Path, source: str | None) -> str | None:
    """回帰: 画面の表が無い正本と、どの画面も機能を挙げない正本で同じバイト。"""
    plain = World(work / "plain", no_screens(), source)
    code, out = plain.scaffold()
    if code != 0:
        return f"画面の表の無い正本: exit={code}: {out[-600:]}"
    screens = World(work / "screens", unlinked(), source)
    code, out = screens.scaffold()
    if code != 0:
        return f"機能を挙げない画面の正本: exit={code}: {out[-600:]}"
    for world in (plain, screens):
        if (world.repo / "scaffold" / "refs").exists() or (world.repo / "build" / "mock").exists():
            return "機能を挙げる画面が無いのに参考資料の写しかモックを作った"
    a = plain.snapshot("scaffold", "build/scaffold")
    b = screens.snapshot("scaffold", "build/scaffold")
    if a != b:
        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        return f"画面の表の無い正本と、機能を挙げない画面の正本で出力が違う: {diff}"
    return None


def case_unlinked_in_v2(work: Path, source: str | None) -> str | None:
    """v2 で S-002 の `機能` を空にしたら、S-002 の仕様書の写しを消す（S-001 は残る）。"""
    w = World(work, base(), source)
    code, out = w.scaffold()
    if code != 0:
        return f"v1 の生成: exit={code}: {out[-600:]}"
    gate_test.write_docs(w.repo / "docs", {"v2/requirements/screens/data/screens.csv": t.S_HEAD + t.S2.replace(",入力,F-002,,", ",入力,,,")})
    w.record(2)
    code, out = w.scaffold()
    if code != 0:
        return f"v2 の生成: exit={code}: {out[-600:]}"
    refs = w.repo / "scaffold" / "refs"
    if (refs / NEW_MD).exists():
        return "機能を挙げなくなった画面の仕様書の写しが残っている"
    if not (refs / LIST_MD).is_file() or not (refs / "mock" / "index.html").is_file():
        return "まだ機能を挙げる画面の写しかモックを消した"
    return None


def git(repo: Path, env: dict[str, str], *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com",
                    "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args], check=True, capture_output=True, env=env)


def signoff(changed: bool) -> Callable[[Path, str | None], str | None]:
    def run(work: Path, source: str | None) -> str | None:
        """受入基準 2 の前半: 照合（`check-signoff.py`）が画面の表の変更を拾う。"""
        w = World(work, base(), source)
        env = {k: v for k, v in w.env().items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL=str(w.home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")
        git(w.repo, env, "init", "-q", "-b", "main")
        git(w.repo, env, "add", "-A")
        git(w.repo, env, "commit", "-q", "-m", "v1")
        git(w.repo, env, "tag", "signoff/v1/req-1")
        if changed:
            table = w.repo / "docs" / t.S
            table.write_text(table.read_text(encoding="utf-8").replace("受注一覧", "受注の一覧"), encoding="utf-8")
            git(w.repo, env, "commit", "-q", "-am", "画面名を直した")
        git(w.repo, env, "tag", "signoff/v1/budget-1")
        proc = subprocess.run([sys.executable, str(w.spec_loop / "scripts" / "check-signoff.py"), "--repo", str(w.repo), "--version", "1"],
                              capture_output=True, text=True, env=env)
        out = proc.stdout + proc.stderr
        if changed:
            return None if proc.returncode == 1 and "screens.csv" in out else f"画面の表だけが違うのに exit={proc.returncode}: {out[-600:]}"
        return None if proc.returncode == 0 else f"陽性対照: 同じ中身で exit={proc.returncode}: {out[-600:]}"
    return run


# ---- デザインの正本の参照（#1156）

DESIGN_HEAD = "対象,参照,メモ\n"
DESIGN = (DESIGN_HEAD + "全体,tokens/colors.json,色と余白のトークン\n"
          "S-002,https://www.figma.com/design/abc?node-id=2-1,\n"
          "S-001,https://www.figma.com/design/abc?node-id=1-1,一覧のフレーム\n")
DESIGN_LINES = {
    "F-001": ["- 全体: `tokens/colors.json`（色と余白のトークン）",
              "- 画面 `S-002`: `https://www.figma.com/design/abc?node-id=2-1`",
              "- 画面 `S-001`: `https://www.figma.com/design/abc?node-id=1-1`（一覧のフレーム）"],
    "F-002": ["- 全体: `tokens/colors.json`（色と余白のトークン）",
              "- 画面 `S-002`: `https://www.figma.com/design/abc?node-id=2-1`"],
}


def without_design(body: str) -> str:
    """本文からデザインの正本の段落（段落・行・後ろの空行）を外したもの。"""
    if DESIGN_NOTE not in body:
        return body
    head, tail = body.split(DESIGN_NOTE + "\n\n", 1)
    rest = tail.split("\n\n", 1)
    return head + (rest[1] if len(rest) > 1 else "")


def case_design_listed(work: Path, source: str | None) -> str | None:
    """画面を持つ機能の本文に、`全体` とその機能を挙げる画面の行が表の順で載る。契約と、段落の外の本文は、ファイルの無い正本と同じバイト。"""
    plain = World(work / "plain", base(), source)
    code, out = plain.scaffold()
    if code != 0:
        return f"ファイルの無い正本: exit={code}: {out[-600:]}"
    w = World(work / "design", base(), source)
    w.design(DESIGN)
    code, out = w.scaffold()
    if code != 0:
        return f"exit={code}: {out[-600:]}"
    for fid, rows in DESIGN_LINES.items():
        want = EXPECTED[fid].replace("\n\n" + TAIL, "\n\n" + "\n".join([DESIGN_NOTE, ""] + rows) + "\n\n" + TAIL)
        got = refs_section(w.body(fid))
        if got != want:
            return f"{fid} の参考資料の節が違う:\n{got}\n---- 期待:\n{want}"
        if without_design(w.body(fid)) != plain.body(fid):
            return f"{fid}: 段落の外の本文が、ファイルの無い正本と違う"
    if w.snapshot("scaffold") != plain.snapshot("scaffold"):
        return "scaffold/ の契約が、ファイルの無い正本と違う（参照は本文にだけ載るはず）"
    if "どの Issue の本文にも載らない" in out:
        return f"全部の行が載るのに、載らないと知らせた: {out[-400:]}"
    return None


def case_design_unlinked(work: Path, source: str | None) -> str | None:
    """どの本文にも載らない行は、止めずに知らせる——画面の表が無い正本・機能を挙げない画面の行。"""
    plain = World(work / "plain", no_screens(), source)
    code, out = plain.scaffold()
    if code != 0:
        return f"画面の表の無い正本（参照なし）: exit={code}: {out[-600:]}"
    w = World(work / "noscreens", no_screens(), source)
    w.design(DESIGN_HEAD + "全体,tokens/colors.json,\n")
    code, out = w.scaffold()
    if code != 0:
        return f"画面の表の無い正本（全体の行）: exit={code}: {out[-600:]}"
    if "画面の表がどの機能も挙げない——どの Issue の本文にも載らない" not in out:
        return f"画面の表の無い正本で、載らないことを知らせない: {out[-400:]}"
    if w.snapshot("scaffold", "build/scaffold") != plain.snapshot("scaffold", "build/scaffold"):
        return "画面の表の無い正本で、参照を置いたら出力が変わった"
    files = base()
    files[t.S] = t.S_HEAD + t.S1 + t.S2.replace(",入力,F-002,,", ",入力,,,")
    w = World(work / "partial", files, source)
    w.design(DESIGN)
    code, out = w.scaffold()
    if code != 0:
        return f"S-002 が機能を挙げない正本: exit={code}: {out[-600:]}"
    if "画面 S-002 は、画面の表でどの機能にも挙げられていない" not in out:
        return f"機能を挙げない画面の行を知らせない: {out[-400:]}"
    if "node-id=2-1" in w.body("F-001"):
        return "機能を挙げない画面の行が本文に載った"
    return None


DESIGN_BAD = [
    ("見出しが違う", "対象,参照\n全体,a\n", "見出しの行"),
    ("列の数が違う", DESIGN_HEAD + "全体,a\n", "列の数が 2"),
    ("対象が画面の表に無い", DESIGN_HEAD + "S-999,a,\n", "対象 'S-999'"),
    ("参照が空", DESIGN_HEAD + "全体, ,\n", "参照が空"),
    ("参照にバッククォート", DESIGN_HEAD + "全体,a`b,\n", "参照にバッククォート"),
    ("参照に \\", DESIGN_HEAD + "全体,a\\b,\n", "参照にバッククォート"),
    ("参照に改行", DESIGN_HEAD + "全体,\"a\nb\",\n", "参照にバッククォート"),
    ("メモに改行", DESIGN_HEAD + "全体,a,\"x\ny\"\n", "メモに改行"),
    ("組の重複", DESIGN_HEAD + "全体,a,x\n全体,a,y\n", "組が重複"),
    ("UTF-8 でない", (DESIGN_HEAD + "全体,色,\n").encode("cp932"), "読めない"),
]


def case_design_bad(work: Path, source: str | None) -> str | None:
    """決まりに反するファイルなら 1 で何も作らない（`--dry-run` も 1）。"""
    w = World(work, base(), source)
    for name, data, said in DESIGN_BAD:
        w.design(data)
        for args in ((), ("--dry-run",)):
            code, out = w.scaffold(*args)
            if code != 1 or said not in out or "デザインの正本の参照（design/sources.csv" not in out:
                return f"{name}（{' '.join(args) or '書く生成'}）: exit={code}: {out[-400:]}"
            if (w.repo / "scaffold").exists() or (w.repo / "build" / "scaffold").exists():
                return f"{name}: 決まりに反するのに何か書いた"
    w.design(None)
    (w.repo / "design" / "sources.csv").mkdir(parents=True)
    code, out = w.scaffold()
    if code != 1 or "ファイルでない" not in out:
        return f"ファイルでない: exit={code}: {out[-400:]}"
    shutil.rmtree(w.repo / "design")
    plain = World(work / "noscreens", no_screens(), source)
    plain.design(DESIGN_HEAD + "S-001,a,\n")
    code, out = plain.scaffold()
    if code != 1 or "対象 'S-001'" not in out:
        return f"画面の表の無い正本で画面ID の行: exit={code}: {out[-400:]}"
    return None


def case_design_previous(work: Path, source: str | None) -> str | None:
    """前の版の時点（`--upto` が作業中の版より前）を見るときは、版の外のファイルを読まない——作業中の版では読む（陽性対照）。"""
    w = World(work, base(), source)
    gate_test.write_docs(w.repo / "docs", v2_files(False))
    w.record(2)
    w.design(DESIGN_HEAD + "S-999,a,\n")
    code, out = w.scaffold("--dry-run", "--upto", "1")
    if code != 0:
        return f"前の版の時点で読んだ: exit={code}: {out[-400:]}"
    code, out = w.scaffold("--dry-run")
    if code != 1 or "対象 'S-999'" not in out:
        return f"陽性対照: 作業中の版で読まない: exit={code}: {out[-400:]}"
    return None


def case_design_signoff(work: Path, source: str | None) -> str | None:
    """`design/` は照合の範囲に入らない——`design/sources.csv` だけが違う 2 つのタグで一致と言う（陽性対照は「照合: 画面の表だけが違えば一致と言わない」）。"""
    w = World(work, base(), source)
    w.design(DESIGN)
    env = {k: v for k, v in w.env().items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=str(w.home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")
    git(w.repo, env, "init", "-q", "-b", "main")
    git(w.repo, env, "add", "-A")
    git(w.repo, env, "commit", "-q", "-m", "v1")
    git(w.repo, env, "tag", "signoff/v1/req-1")
    w.design(DESIGN.replace("node-id=1-1", "node-id=9-9"))
    git(w.repo, env, "commit", "-q", "-am", "デザインの参照を差し替えた")
    git(w.repo, env, "tag", "signoff/v1/budget-1")
    proc = subprocess.run([sys.executable, str(w.spec_loop / "scripts" / "check-signoff.py"), "--repo", str(w.repo), "--version", "1"],
                          capture_output=True, text=True, env=env)
    return None if proc.returncode == 0 else f"design/sources.csv だけが違うのに exit={proc.returncode}: {(proc.stdout + proc.stderr)[-600:]}"


CASES: list[tuple[str, Callable[[Path, str | None], str | None]]] = [
    ("参考資料: 画面ごとの仕様書・svg・生成したモックが並び、写しと目録が在る", case_refs_listed),
    ("参考資料: 中間表現の refs と重なるパスは 2 度並べない", case_overlap),
    ("受入基準 1: 生成器の版だけを変えた v2 は機能を変更と数えない", generator_only(False)),
    ("受入基準 1 の陽性対照: 中間表現を直せば変更になる", generator_only(True)),
    ("--check はモックを生成し直さず、写しの欠けと手直しを古いと言う", case_check),
    ("--dry-run は何も書かない", case_dry_run),
    ("生成器が 1 なら 1 で何も書かない", failing_mock(1, 1)),
    ("生成器が 4 なら 2 で何も書かない", failing_mock(4, 2)),
    ("回帰: 機能を挙げる画面が無ければ、画面の表の無い正本と同じバイト", case_unlinked),
    ("v2 で機能を挙げなくなった画面の写しを消す", case_unlinked_in_v2),
    ("照合: 画面の表だけが違えば一致と言わない", signoff(True)),
    ("照合の陽性対照: 同じ中身なら 0", signoff(False)),
    ("デザインの正本: 画面を持つ機能の本文に、全体とその画面の行が載り、契約は変わらない", case_design_listed),
    ("デザインの正本: どの本文にも載らない行は止めずに知らせる", case_design_unlinked),
    ("デザインの正本: 決まりに反すれば 1 で何も作らない", case_design_bad),
    ("デザインの正本: 前の版の時点では読まない", case_design_previous),
    ("デザインの正本: 照合の範囲に入らない", case_design_signoff),
]

# 本体を壊す変異: (名前, 壊す箇所, 置き換え, 赤になるはずの試料の名前)
MUTATIONS = [
    ("生成したモックを機能のオブジェクトに入れる", "        loaded.mock = out.read_bytes()\n",
     "        loaded.mock = out.read_bytes()\n        [f.__setitem__(\"mock\", sha256(loaded.mock)) for f in features_of(loaded.ir)]\n",
     "受入基準 1: 生成器の版だけを変えた v2 は機能を変更と数えない"),
    ("画面の表の機能の列を見ない", "        named = {part.strip() for part in (row.get(\"機能\") or \"\").split(SCREEN_SEPARATOR)} & ids\n",
     "        named = set()\n", "参考資料: 画面ごとの仕様書・svg・生成したモックが並び、写しと目録が在る"),
    ("在らない svg も並べる", "if rel and rel in rendered and \"`\" not in rel", "if rel and \"`\" not in rel",
     "参考資料: 画面ごとの仕様書・svg・生成したモックが並び、写しと目録が在る"),
    ("refs と重なるパスを 2 度並べる", "for rel in paths if rel not in refs]", "for rel in paths]",
     "参考資料: 中間表現の refs と重なるパスは 2 度並べない"),
    ("--check で写しの欠けを名指さない", "            if loaded.mock is None:\n                mock_missing =",
     "            if False:\n                mock_missing =", "--check はモックを生成し直さず、写しの欠けと手直しを古いと言う"),
    ("--check でもモックを生成し直す", "        if writing:\n            code, lines = build_mock(repo, loaded)",
     "        if writing or args.check:\n            code, lines = build_mock(repo, loaded)",
     "--check はモックを生成し直さず、写しの欠けと手直しを古いと言う"),
    ("--dry-run でもモックを作る", "        if writing:\n            code, lines = build_mock(repo, loaded)",
     "        if True:\n            code, lines = build_mock(repo, loaded)", "--dry-run は何も書かない"),
    ("生成器の失敗を見ない", "    if proc.returncode != 0:\n        return (1 if proc.returncode == 1 else 2)",
     "    if False:\n        return (1 if proc.returncode == 1 else 2)", "生成器が 1 なら 1 で何も書かない"),
    ("生成器の 1 を 2 と読む", "return (1 if proc.returncode == 1 else 2)", "return (2 if proc.returncode == 1 else 2)",
     "生成器が 1 なら 1 で何も書かない"),
    ("機能を挙げない画面でもモックを作る", "    if loaded.screens:\n        # 生成したモック",
     "    if True:\n        # 生成したモック", "回帰: 機能を挙げる画面が無ければ、画面の表の無い正本と同じバイト"),
    ("デザインの正本の行を載せない", '        design = design_rows(loaded, change.feature["id"])\n', "        design = []\n",
     "デザインの正本: 画面を持つ機能の本文に、全体とその画面の行が載り、契約は変わらない"),
    ("画面に依らず全部の行を載せる", "    return [row for row in loaded.design if row[0] == DESIGN_WHOLE or row[0] in linked]",
     "    return list(loaded.design)", "デザインの正本: 画面を持つ機能の本文に、全体とその画面の行が載り、契約は変わらない"),
    ("全体の行を載せない", "if row[0] == DESIGN_WHOLE or row[0] in linked]", "if row[0] in linked]",
     "デザインの正本: 画面を持つ機能の本文に、全体とその画面の行が載り、契約は変わらない"),
    ("メモを載せない", '(f"（{memo}）" if memo else "")', '""',
     "デザインの正本: 画面を持つ機能の本文に、全体とその画面の行が載り、契約は変わらない"),
    ("ファイルを読まない", "    if not path.exists() and not path.is_symlink():\n", "    if True:\n",
     "デザインの正本: 画面を持つ機能の本文に、全体とその画面の行が載り、契約は変わらない"),
    ("載らない行を知らせない", "        loaded.notes += design_notes(loaded)\n", "",
     "デザインの正本: どの本文にも載らない行は止めずに知らせる"),
    ("機能を挙げない画面の行を知らせない", "for target, ref, _ in loaded.design if target != DESIGN_WHOLE and target not in linked]",
     "for target, ref, _ in loaded.design if False]", "デザインの正本: どの本文にも載らない行は止めずに知らせる"),
    ("見出しを見ない", "    if not rows or tuple(cell.strip() for cell in rows[0]) != DESIGN_COLUMNS:\n", "    if not rows:\n",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("列の数を見ない", "        if len(fields) != len(DESIGN_COLUMNS):\n", "        if False:\n",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("対象を画面の表と照らさない", "        if target != DESIGN_WHOLE and target not in screens:\n", "        if False:\n",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("参照が空でも通す", "        if not ref:\n", "        if False:\n", "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("参照の形を見ない", '        elif "`" in ref or "\\\\" in ref or ref.splitlines() != [ref]:\n', "        elif False:\n",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("メモの改行を見ない", "        if memo.splitlines() not in ([memo], []):\n", "        if False:\n",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("組の重複を見ない", "        if not bad and (target, ref) in seen:\n", "        if False:\n",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("ファイルでないものを無いと読む", "    if not path.is_file():\n        return [f\"{DESIGN_PATH}: ファイルでない", "    if False:\n        return [f\"{DESIGN_PATH}: ファイルでない",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("違反でも止めない", "        if problems:\n            return 1, problems + [f\"デザインの正本の参照", "        if False:\n            return 1, problems + [f\"デザインの正本の参照",
     "デザインの正本: 決まりに反すれば 1 で何も作らない"),
    ("前の版の時点でも読む", "    if design_gate:\n        problems, loaded.design", "    if True:\n        problems, loaded.design",
     "デザインの正本: 前の版の時点では読まない"),
]


def run_cases(work: Path, names: list[str] | None = None, source: str | None = None) -> dict[str, str | None]:
    results = {}
    for index, (name, fn) in enumerate(CASES):
        if names is not None and name not in names:
            continue
        place = work / f"case{index}"
        place.mkdir(parents=True)
        try:
            results[name] = fn(place, source)
        except subprocess.CalledProcessError as e:
            results[name] = f"試料を作れなかった: {' '.join(e.cmd[-3:])}: {e.stderr.decode(errors='replace') if isinstance(e.stderr, bytes) else e.stderr}"
    return results


def constant(source: str, name: str) -> str | None:
    found = re.search(rf'^{name} = "([^"]*)"', source, flags=re.MULTILINE)
    return found.group(1) if found else None


def check_copies() -> None:
    """本文の文言の写しが `handoff-issue.md` に原文のまま在る。モックの置き場所と生成器の名前が screen-spec と同じ。"""
    handoff = HANDOFF_REF.read_text(encoding="utf-8")
    for label, text in (("画面の表の段落", SCREENS_NOTE),):
        if text not in handoff:
            failures.append(f"写し: {label} が {HANDOFF_REF.name} に原文のまま無い")
    source = (SPEC_LOOP / "scripts" / TARGET).read_text(encoding="utf-8")
    scaffold_note = re.search(r'^REFS_SCREENS = \((.*?)\)\n', source, flags=re.MULTILINE | re.DOTALL)
    joined = "".join(re.findall(r'"([^"]*)"', scaffold_note.group(1))) if scaffold_note else None
    if joined != SCREENS_NOTE:
        failures.append(f"写し: scaffold.py の REFS_SCREENS がテストの文言と違う: {joined!r}")
    # デザインの正本（#1156）——段落の文言は handoff-issue.md と scaffold.py に、印は dev-loop の spec-gap.md にも、置き場所と列は tree.md に
    if DESIGN_NOTE not in handoff:
        failures.append(f"写し: デザインの正本の段落が {HANDOFF_REF.name} に原文のまま無い")
    design_note = re.search(r'^REFS_DESIGN = \((.*?)\)\n', source, flags=re.MULTILINE | re.DOTALL)
    joined = "".join(re.findall(r'"([^"]*)"', design_note.group(1))) if design_note else None
    if joined != DESIGN_NOTE:
        failures.append(f"写し: scaffold.py の REFS_DESIGN がテストの文言と違う: {joined!r}")
    mark = constant(source, "DESIGN_MARK")
    if not mark or not DESIGN_NOTE.startswith(mark):
        failures.append(f"写し: scaffold.py の DESIGN_MARK {mark!r} が段落の頭でない")
    gap = SPEC_GAP_REF.read_text(encoding="utf-8")
    if f"`{mark}` で始まる段落" not in gap or "### デザインの正本（#1156）" not in gap:
        failures.append(f"写し: dev-loop の spec-gap.md に印 `{mark}` で始まる段落の決まり（「デザインの正本」の節）が無い")
    if f"`{mark}`" not in handoff:
        failures.append(f"写し: {HANDOFF_REF.name} に段落の印 `{mark}` が無い")
    tree = TREE_REF.read_text(encoding="utf-8")
    columns = re.findall(r'^DESIGN_COLUMNS = \(([^)]*)\)', source, flags=re.MULTILINE)
    names = re.findall(r'"([^"]*)"', columns[0]) if columns else []
    if constant(source, "DESIGN_PATH") != "design/sources.csv" or "design/sources.csv" not in tree:
        failures.append(f"写し: scaffold.py の DESIGN_PATH {constant(source, 'DESIGN_PATH')!r} が tree.md の置き場所と違う")
    if not names or f"見出し `{','.join(names)}`" not in tree or any(f"| `{name}` |" not in tree for name in names):
        failures.append(f"写し: scaffold.py の DESIGN_COLUMNS {names!r} が tree.md の「デザインの正本の参照」の列と違う")
    if constant(source, "DESIGN_WHOLE") != "全体" or "`全体`（どの画面にも掛かる" not in tree:
        failures.append(f"写し: scaffold.py の DESIGN_WHOLE {constant(source, 'DESIGN_WHOLE')!r} が tree.md と違う")
    mock = (SCREEN_SPEC / "scripts" / "build-mock.py").read_text(encoding="utf-8")
    want = f"{constant(mock, 'OUT_DIR')}/v{{}}/{constant(mock, 'OUT_NAME')}"
    if constant(source, "MOCK_OUT") != want:
        failures.append(f"写し: scaffold.py の MOCK_OUT {constant(source, 'MOCK_OUT')!r} が build-mock.py の置き場所 {want!r} と違う")
    if not (SCREEN_SPEC / (constant(source, "MOCK_SCRIPT") or "-")).is_file():
        failures.append(f"写し: scaffold.py の MOCK_SCRIPT {constant(source, 'MOCK_SCRIPT')!r} が screen-spec に無い")


def main() -> int:
    original = (SPEC_LOOP / "scripts" / TARGET).read_text(encoding="utf-8")
    check_copies()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        results = run_cases(work / "base")
        for name, problem in results.items():
            check(name, problem)
        mutated = 0
        for index, (name, old, new, case) in enumerate(MUTATIONS):
            if original.count(old) != 1:
                failures.append(f"変異「{name}」: 壊す箇所が本体に {original.count(old)} 回ある（ちょうど 1 回のはず）")
                continue
            if case not in dict(CASES):
                failures.append(f"変異「{name}」: 試料「{case}」が無い")
                continue
            if results.get(case):
                failures.append(f"変異「{name}」: 試料「{case}」が元の本体で緑でない（陽性対照）")
                continue
            got = run_cases(work / f"mutation{index}", [case], original.replace(old, new))
            if not got.get(case):
                failures.append(f"変異「{name}」: 試料「{case}」が赤にならない（変異が素通りした）")
            mutated += 1
    if failures:
        for line in failures:
            print(f"FAIL {line}")
        print(f"失敗 {len(failures)} 件（試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件）")
        return 1
    print(f"OK（試料 {len(CASES)} 件・変異 {mutated} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
