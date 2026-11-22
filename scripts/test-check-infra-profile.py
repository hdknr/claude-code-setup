#!/usr/bin/env python3
"""platform-spec の `check-infra-profile.py`（案件の `infra.csv` の `profile の行` を外部の profile の基盤の層と照らす。#1456）の回帰テスト。

    python3 scripts/test-check-infra-profile.py

**本体はプラグインの中にある**（`plugins/platform-spec/scripts/`）。spec-loop の重ね方と外部の profile の読み方（`external-profile.py`）を読み込むので、
**一時ディレクトリに本物の spec-loop と platform-spec の写しを並べて**走らせる（隣の `spec-loop` を見つける形）。

見るもの:

1. **在る ID は通り、無い ID・そのタグに無い（別のタグにだけ在る）ID は表の行と ID を名指しして 1**（#1456 の受入基準）——profile は一時の git リポジトリに
   タグを付けて作る（`v1`・`v2`・形式の版が範囲の外・見出しが違う・基盤の層が無い）。ネットワークには出ない。
2. **止まり方を分ける**——設定が無い・設定の形・空の ID は 1、clone が見つからない・タグが無い・層が無い・形式の版・層の見出し・spec-loop の見つけ方と版は 4、
   読めない表は 2、設定も `profile の行` の値も無ければ clone を探さずに 0。
3. **読むだけ**——走らせた前後で、profile の clone の `git status --porcelain`・HEAD・`git for-each-ref` と、正本のファイル（中身まで）が変わらない。
   写したプラグインに `__pycache__` ができない。
4. **本体の定数が `plugins/platform-spec/references/` の原本と一致する**（崩すと不一致になる陽性対照つき）。
5. **変異テスト**——本体を 1 箇所ずつ壊し、名指しした試料が期待どおりでなくなること（壊さない写しを同じ置き方で置くと期待どおりになる陰性対照つき）。**変異の数は docstring の「守ること」の行の数と同じ**（手で数えない）。
   変異ごとに、壊す箇所が本体にちょうど 1 回現れることを先に確かめる。

**このテストは実環境を触らない。** `HOME`・`CLAUDE_CONFIG_DIR`・`GIT_CONFIG_GLOBAL` を一時ディレクトリに差し替え、`SPEC_PROFILE_CLONE`・`PLATFORM_SPEC_SPEC_LOOP`・`GIT_*` を子に渡さない。
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

REAL_REPO = Path(__file__).resolve().parent.parent
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
PLATFORM = REAL_REPO / "plugins" / "platform-spec"
TARGET = "check-infra-profile.py"
SOURCE = PLATFORM / "scripts" / TARGET
REF_INFRA = PLATFORM / "references" / "infra-profile.md"
REF_SPEC_LOOP = PLATFORM / "references" / "spec-loop.md"
REPO = "org/guide"

I_HEAD = "項目,決定,理由,費用への影響,水準,根拠,状態,profile の行\n"
I7_HEAD = "項目,決定,理由,費用への影響,水準,根拠,状態\n"


def infra(*refs: str) -> str:
    """`profile の行` の値を並べた基盤要件の表（行ごとに 1 つ）。中身はこの検査に関係ない。"""
    items = ["言語", "DBMS", "ホスティング環境", "認証基盤", "監視"]
    return I_HEAD + "".join(f"{items[i]},x,y,z,,Q-F-00{i + 1},決定,{ref}\n" for i, ref in enumerate(refs))


def settings(tag: str = "v1", profile: str = "org", repo: str = REPO, extra: str = "") -> str:
    return f"項目,値\nリポジトリ,{repo}\nprofile,{profile}\nタグ,{tag}\n{extra}"


I = "docs/v1/shared/infra.csv"
S = "docs/v1/shared/platform/settings.csv"
CLAUDE = "CLAUDE.md"
DECL = f"外部の profile の clone: {REPO} {{clone}}\n"
OK = {I: infra("LANG-1", "HOST-1・DB-1"), S: settings(), CLAUDE: DECL}


def with_(base: dict, **changes) -> dict:
    out = dict(base)
    for key, value in changes.items():
        rel = {"infra": I, "settings": S, "claude": CLAUDE}.get(key, key)
        if value is None:
            out.pop(rel, None)
        else:
            out[rel] = value
    return out


# (名前, 正本のファイル（正本の根からのパス → 中身。None は置かない）, 引数（{docs}・{clone}・{fake}・{old}・{stale} を置き換える）, 期待する終了コード, 含むべき文字列, 含んではならない文字列)
CASES: list[tuple[str, dict, list[str], int, str, str]] = [
    ("在る ID", OK, [], 0, "照らした ID 3 件", "違反: "),
    ("無い ID", with_(OK, infra=infra("LANG-1", "NOPE-1")), [], 1,
     "shared/infra.csv:3: DBMS の profile の行 NOPE-1 が org/guide の org（タグ v1）の基盤の層に無い", "LANG-1 が"),
    ("タグの外の ID", with_(OK, infra=infra("HOST-9")), [], 1, "profile の行 HOST-9 が org/guide の org（タグ v1）の基盤の層に無い", ""),
    ("別のタグなら在る", with_(OK, infra=infra("HOST-9"), settings=settings("v2")), [], 0, "照らした ID 1 件", "違反: "),
    ("区切った ID を 1 つずつ", with_(OK, infra=infra("HOST-1・NOPE-2")), [], 1, "profile の行 NOPE-2 が", "profile の行 HOST-1"),
    ("空の ID", with_(OK, infra=infra("HOST-1・")), [], 1, "空の ID がある", ""),
    ("設定が無い", with_(OK, settings=None), [], 1, "言語 が profile の行 を指しているのに、案件の設定（shared/platform/settings.csv）が無い", ""),
    ("使っていない", {I: I7_HEAD + "言語,x,y,z,,Q-F-001,決定\n"}, [], 0, "照らすものが無い（platform-spec を使っていない）", "違反"),
    ("profile の行が全部空", {I: infra("", "")}, [], 0, "照らすものが無い", "違反"),
    ("設定の見出し", with_(OK, settings="key,value\nリポジトリ,org/guide\nprofile,org\nタグ,v1\n"), [], 1,
     "shared/platform/settings.csv:1: 見出しの行が `項目,値` でない", ""),
    ("設定の外の項目", with_(OK, settings=settings(extra="版,1\n")), [], 1, "項目 '版' は決まりの外", ""),
    ("設定の同じ項目", with_(OK, settings=settings(extra="タグ,v2\n")), [], 1, "項目 タグ が 2 行ある", ""),
    ("設定の空の値", with_(OK, settings=settings(profile="")), [], 1, "profile の値が空", ""),
    ("設定の足りない項目", with_(OK, settings="項目,値\nリポジトリ,org/guide\nprofile,org\n"), [], 1, "項目 タグ の行が無い", ""),
    ("設定のリポジトリの形", with_(OK, settings=settings(repo="guide")), ["--clone", "{clone}"], 1, "リポジトリ 'guide' が `<持ち主>/<名前>` の形でない", ""),
    ("設定の profile の形", with_(OK, settings=settings(profile="a/b")), [], 1, "profile 'a/b' が profile の名前の形でない", ""),
    ("設定のタグの形", with_(OK, settings=settings("v1~1")), [], 1, "タグ 'v1~1' がタグの名前に使えない形", ""),
    ("設定のリポジトリの点", with_(OK, settings=settings(repo="org/..")), ["--clone", "{clone}"], 1, "リポジトリ 'org/..' の持ち主か名前が", ""),
    ("設定のタグがハイフンで始まる", with_(OK, settings=settings("-v1")), [], 1, "タグ '-v1' がタグの名前に使えない形（", ""),
    ("設定のタグが HEAD", with_(OK, settings=settings("HEAD")), [], 1, "タグ 'HEAD' がタグの名前に使えない形（", ""),
    ("基盤要件の表の先頭が空の行", with_(OK, infra="\n" + infra("LANG-1", "NOPE-1")), [], 1, "profile の行 NOPE-1 が", ""),
    ("設定があれば値が無くても読む", {I: infra("", ""), S: settings("nope"), CLAUDE: DECL}, [], 4, "タグ", ""),
    ("clone が見つからない", with_(OK, claude=None), [], 4, "手元の clone が見つからない", ""),
    ("タグが無い", with_(OK, settings=settings("v9")), [], 4, "v9", ""),
    ("基盤の層が無い", with_(OK, settings=settings("nolayer")), [], 4, "基盤の層が無い", ""),
    ("形式の版が範囲の外", with_(OK, settings=settings("fmt2")), [], 4, "受け付ける範囲（1 以上 2 未満）の外", ""),
    ("層の見出しが違う", with_(OK, settings=settings("badhead")), [], 4, "形式の版 1 の `ID,要約,リンク,項目` でない", ""),
    ("層の表の先頭が空の行", with_(OK, settings=settings("blankhead")), [], 0, "照らした ID 3 件", "違反: "),
    ("名指した spec-loop が違う", OK, ["--spec-loop", "{fake}"], 4, "spec-loop のプラグインの根でない", ""),
    ("spec-loop の版が範囲の外", OK, ["--spec-loop", "{old}"], 4, "対応の範囲の外", ""),
    ("spec-loop が古い", OK, ["--spec-loop", "{stale}"], 4, "PROFILE_COLUMN", ""),
    ("重ね合わせの違反", with_(OK, **{"docs/v2/removed.csv": "種類,対象\nファイル,shared/x.csv\n"}), [], 1, "版の重ね合わせ: ", ""),
    ("前の版の時点", with_(OK, **{"docs/v2/shared/infra.csv": infra("NOPE-3")}), ["--upto", "1"], 0, "照らした ID 3 件", "NOPE-3"),
    ("後の版の時点", with_(OK, **{"docs/v2/shared/infra.csv": infra("NOPE-3")}), [], 1, "NOPE-3", ""),
    ("引数の clone", with_(OK, claude=None), ["--clone", "{clone}"], 0, "出所: 引数 --clone", "違反: "),
    ("表が UTF-8 でない", with_(OK, infra=infra("LANG-1").encode("cp932")), [], 2, "UTF-8 として読めない", ""),
    ("引数が足りない", OK, ["--no-docs"], 2, "usage:", ""),
]

# docstring の「守ること」の行と同じ順の変異。(名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("設定も値も無いのに clone を探す", "        if settings is None:\n", "        if settings is None and refs:\n", "使っていない"),
    ("在る ID も名指す", "                if rid not in known:", "                if True:", "在る ID"),
    ("無い ID を通す", "                if rid not in known:", "                if False:", "無い ID"),
    ("区切らずに照らす", "[part.strip() for part in value.split(ID_SEPARATOR)]", "[value]", "区切った ID を 1 つずつ"),
    ("空の ID を見ない", "            if any(not i for i in ids):", "            if False:", "空の ID"),
    ("設定が無いのを通す", '                self.violations.append(f"{where}: {item} が {self.column} を指しているのに、案件の設定（{SETTINGS}）が無い")',
     "                pass", "設定が無い"),
    ("設定の見出しを見ない", "        if not rows or rows[0][1] != SETTINGS_COLUMNS:", "        if not rows:", "設定の見出し"),
    ("設定の外の項目を通す", "            if key not in SETTING_KEYS:", "            if False:", "設定の外の項目"),
    ("設定の同じ項目を通す", "            if key in found:", "            if False:", "設定の同じ項目"),
    ("設定の空の値を通す", "            if not value:\n                self.violations.append(f\"{where}: {key} の値が空\")",
     "            if False:\n                self.violations.append(f\"{where}: {key} の値が空\")", "設定の空の値"),
    ("設定の足りない項目を通す", "        for key in SETTING_KEYS:\n            if key not in found:", "        for key in ():\n            if key not in found:",
     "設定の足りない項目"),
    ("リポジトリの形を見ない", "        if repo and not REPO_FORM.fullmatch(repo):", "        if False:", "設定のリポジトリの形"),
    ("リポジトリの点を見ない", '        elif repo and any(part in (".", "..") for part in repo.split("/")):', "        elif False:", "設定のリポジトリの点"),
    ("profile の形を見ない", '        if name and ("/" in name or name in (".", "..")):', "        if False:", "設定の profile の形"),
    ("タグの形を見ない", '        if tag and subprocess.run(["git", "check-ref-format", f"refs/tags/{tag}"], capture_output=True).returncode != 0:',
     "        if False:", "設定のタグの形"),
    ("タグのハイフンと HEAD を見ない", '        elif tag and (tag.startswith("-") or tag == "HEAD"):', "        elif False:", "設定のタグがハイフンで始まる"),
    ("値が無ければ profile を読まない", "        known = self.layer_ids(settings)", "        known = self.layer_ids(settings) if refs else set()",
     "設定があれば値が無くても読む"),
    ("層が無いのを 4 にしない", '        except ext.LayerMissing as e:\n            raise Stop(f"profile {name}（{repo} のタグ {tag}）に{LAYER}の層が無い: {e}") from None\n',
     "", "基盤の層が無い"),
    ("層の見出しを見ない", "                if head != LAYER_COLUMNS:", "                if False:", "層の見出しが違う"),
    ("見出しの前の空の行を飛ばさない", "if any(cell.strip() for cell in row)), [])", "if True), [])", "層の表の先頭が空の行"),
    ("基盤要件の表の見出しの前の空の行を飛ばさない", "        while rows and not any(f.strip() for f in rows[0][1]):", "        while False:",
     "基盤要件の表の先頭が空の行"),
    ("名指しが違っても使う", "            if not is_spec_loop(root):\n                raise Stop(", "            if False:\n                raise Stop(",
     "名指した spec-loop が違う"),
    ("spec-loop の版を見ない", "    if not (SPEC_LOOP_MIN <= version < SPEC_LOOP_BELOW):", "    if False:", "spec-loop の版が範囲の外"),
    ("重ね合わせの違反を通す", "        if problems:\n            self.violations.extend", "        if False:\n            self.violations.extend", "重ね合わせの違反"),
    ("--upto を渡さない", "self.versions.merge(self.docs, self.upto)", "self.versions.merge(self.docs, None)", "前の版の時点"),
    ("--clone を渡さない", "ext.find_clone(repo, self.clone, self.docs.resolve().parent)", "ext.find_clone(repo, None, self.docs.resolve().parent)", "引数の clone"),
    ("CLAUDE.md を cwd で探す", "ext.find_clone(repo, self.clone, self.docs.resolve().parent)", "ext.find_clone(repo, self.clone, None)", "在る ID"),
    ("読めない表を読む", '            return whole.files[path].decode("utf-8-sig")', '            return whole.files[path].decode("utf-8-sig", "replace")',
     "表が UTF-8 でない"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def child_env(tmp: Path) -> dict:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_") and k not in ("SPEC_PROFILE_CLONE", "PLATFORM_SPEC_SPEC_LOOP", "CLAUDE_CONFIG_DIR")}
    (tmp / "home").mkdir(exist_ok=True)
    (tmp / "gitconfig").touch()
    env.update(HOME=str(tmp / "home"), CLAUDE_CONFIG_DIR=str(tmp / "config"), GIT_CONFIG_GLOBAL=str(tmp / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
    return env


def git(cwd: Path, env: dict, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


PROFILE_V1 = "層,形式の版,ファイル,重ねる先\n基盤,1,infra.csv,\n"
LAYER_V1 = "ID,要約,リンク,項目\nLANG-1,Python 3.12,docs/guide.md,言語\nDB-1,PostgreSQL 16,,DBMS\nHOST-1,AWS ECS,,ホスティング環境\n"


def make_profile(root: Path, env: dict) -> Path:
    """タグ v1・v2・fmt2・badhead・blankhead・nolayer を持つ profile のリポジトリ。"""
    assert_in_tmp(root)
    root.mkdir(parents=True)
    git(root, env, "init", "-q", "-b", "main")
    base = root / "spec-profile" / "org"
    base.mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text("# 言語\n", encoding="utf-8")

    def commit(tag: str, profile: str, layer: str | None, extra: dict | None = None) -> None:
        (base / "profile.csv").write_text(profile, encoding="utf-8")
        if layer is not None:
            (base / "infra.csv").write_text(layer, encoding="utf-8")
        for rel, body in (extra or {}).items():
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            (base / rel).write_text(body, encoding="utf-8")
        git(root, env, "add", "-A")
        git(root, env, "commit", "-q", "-m", tag)
        git(root, env, "tag", tag)

    commit("v1", PROFILE_V1, LAYER_V1)
    commit("v2", PROFILE_V1, LAYER_V1 + "HOST-9,AWS Lambda,,ホスティング環境\n")
    commit("fmt2", PROFILE_V1.replace("基盤,1,", "基盤,2,"), LAYER_V1)
    commit("badhead", PROFILE_V1, LAYER_V1.replace("ID,要約,リンク,項目", "ID,要約,リンク,決定"))
    commit("blankhead", PROFILE_V1, "\n" + LAYER_V1)
    commit("nolayer", "層,形式の版,ファイル,重ねる先\n画面,1,screens/*.csv,web-spa\n", LAYER_V1,
           {"screens/a.csv": "ID,要約,リンク\nS-1,一覧,\n"})
    git(root, env, "checkout", "-q", "v1")  # 作業ツリーはどれかのタグ。読むのはタグの時点
    return root


def lay_out(plugins: Path, platform_source: str | None = None) -> Path:
    """`plugins/` の下に spec-loop と platform-spec を並べる（spec-loop は写した根への symlink でもよい）。platform-spec の根を返す。"""
    assert_in_tmp(plugins)
    plugins.mkdir(parents=True)
    root = plugins / "platform-spec"
    shutil.copytree(PLATFORM, root, ignore=shutil.ignore_patterns("__pycache__"))
    if platform_source is not None:
        (root / "scripts" / TARGET).write_text(platform_source, encoding="utf-8")
    return root


def run_case(platform: Path, work: Path, files: dict, args: list[str], tokens: dict, env: dict) -> tuple[int, str]:
    assert_in_tmp(work)
    project = work / "project"
    (project / "docs").mkdir(parents=True)
    for rel, body in files.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            path.write_bytes(body)
        else:
            path.write_text(body.replace("{clone}", tokens["clone"]), encoding="utf-8")
    argv = [a.format(**tokens) for a in args]
    if "--no-docs" in argv:
        argv = []
    else:
        argv = [str(project / "docs"), *argv]
    elsewhere = work / "elsewhere"  # cwd は正本の外（CLAUDE.md は正本の根のものを読む）
    elsewhere.mkdir()
    proc = subprocess.run([sys.executable, "-I", str(platform / "scripts" / TARGET), *argv], capture_output=True, text=True, cwd=elsewhere, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def as_expected(name: str, result: tuple[int, str]) -> bool:
    _, _, _, code, text, absent = next(case for case in CASES if case[0] == name)
    return result[0] == code and text in result[1] and not (absent and absent in result[1]) and "Traceback" not in result[1]


def tree_state(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "<dir>"
            for p in sorted(root.rglob("*"))}


def clone_state(clone: Path, env: dict) -> tuple[str, str, str]:
    return (git(clone, env, "status", "--porcelain", "--ignored"), git(clone, env, "rev-parse", "HEAD"), git(clone, env, "for-each-ref"))


def guarded_lines(source: str) -> list[str]:
    body = source.split("**守ること**:", 1)[1].split("**守らないもの**:", 1)[0]
    return [line for line in body.splitlines() if line.startswith("- ")]


# ---- 原本との突き合わせ


def section(markdown: str, heading: str) -> str:
    level = len(heading) - len(heading.lstrip("#"))
    start = markdown.index(heading)
    rest = markdown[start + len(heading):]
    found = re.search(rf"^#{{1,{level}}} ", rest, flags=re.MULTILINE)
    return rest[:found.start()] if found else rest


def first_cells(text: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"^\| `([^`]+)` \|", text, flags=re.MULTILINE)]


def range_cells(text: str) -> tuple[str, str] | None:
    m = re.search(r"^\| `([^`]+)` \| `([^`]+)` \|$", text, flags=re.MULTILINE)
    return (m.group(1), m.group(2)) if m else None


def reference_mismatches(module, infra_md: str, spec_loop_md: str) -> list[str]:
    problems = []
    try:
        layer = section(infra_md, "## 基盤の層の表")
        if first_cells(layer) != module.LAYER_COLUMNS:
            problems.append(f"基盤の層の列が違う（原本 {first_cells(layer)} ／ 本体 {module.LAYER_COLUMNS}）")
        if f"層の名前は `{module.LAYER}`" not in layer:
            problems.append(f"層の名前 {module.LAYER} が原本に無い")
        if range_cells(section(infra_md, "## 形式の版の範囲")) != (module.FORMAT_LOW, module.FORMAT_HIGH):
            problems.append(f"形式の版の範囲が違う（原本 {range_cells(section(infra_md, '## 形式の版の範囲'))} ／ 本体 {module.FORMAT_LOW}・{module.FORMAT_HIGH}）")
        setting = section(infra_md, "## 案件の設定")
        if f"`{module.SETTINGS}` に置く" not in setting:
            problems.append(f"設定の置き場所 {module.SETTINGS} が原本に無い")
        if f"見出しの行は `{','.join(module.SETTINGS_COLUMNS)}`" not in setting:
            problems.append("設定の見出しが原本と違う")
        if tuple(first_cells(setting)) != module.SETTING_KEYS:
            problems.append(f"設定の項目が違う（原本 {first_cells(setting)} ／ 本体 {module.SETTING_KEYS}）")
        if f"複数は `{module.ID_SEPARATOR}` で区切る" not in section(infra_md, "## `profile の行` の書き方"):
            problems.append(f"区切り {module.ID_SEPARATOR} が原本に無い")
        shown = tuple(".".join(map(str, v)) for v in (module.SPEC_LOOP_MIN, module.SPEC_LOOP_BELOW))
        if range_cells(section(spec_loop_md, "## 対応する spec-loop の版")) != shown:
            problems.append(f"spec-loop の版の範囲が違う（本体 {shown}）")
        if f"2. 環境変数 `{module.SPEC_LOOP_ENV}`" not in spec_loop_md:
            problems.append(f"環境変数 {module.SPEC_LOOP_ENV} が原本に無い")
    except ValueError as e:  # 見出しが無い
        problems.append(f"原本の見出しが無い: {e}")
    return problems


REFERENCE_MUTATIONS = [  # (ファイル, 崩す前, 崩した後)
    ("infra", "| `項目` | 案件の `infra.csv` のどの項目の案か", "| 項目 | 案件の `infra.csv` のどの項目の案か"),
    ("infra", "層の名前は `基盤` で 1 行置き", "層の名前は `インフラ` で 1 行置き"),
    ("infra", "| `1` | `2` |", "| `1` | `3` |"),
    ("infra", "`shared/platform/settings.csv` に置く", "`shared/platform.csv` に置く"),
    ("infra", "見出しの行は `項目,値`", "見出しの行は `キー,値`"),
    ("infra", "| `タグ` | 読む版", "| `版` | 読む版"),
    ("infra", "複数は `・` で区切る", "複数は `,` で区切る"),
    ("spec-loop", "| `0.133.0` | `1.0.0` |", "| `0.132.0` | `1.0.0` |"),
    ("spec-loop", "2. 環境変数 `PLATFORM_SPEC_SPEC_LOOP`", "2. 環境変数 `PLATFORM_SPEC_LOOP`"),
]


def load(path: Path):
    spec = importlib.util.spec_from_file_location("check_infra_profile_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    source = SOURCE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="infra-profile-test-") as tmp_name:
        tmp = Path(tmp_name)
        env = child_env(tmp)
        clone = make_profile(tmp / "profile", env)
        # spec-loop の写し（本物）と、範囲の外の版・古い版・spec-loop でないもの
        spec_loop = tmp / "spec-loop-copy"
        shutil.copytree(SPEC_LOOP, spec_loop, ignore=shutil.ignore_patterns("__pycache__"))
        old = tmp / "old-spec-loop"
        shutil.copytree(spec_loop, old)
        manifest = json.loads((old / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        manifest["version"] = "0.132.0"
        (old / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
        stale = tmp / "stale-spec-loop"
        shutil.copytree(spec_loop, stale)
        infra_src = (stale / "scripts" / "check-infra-csv.py").read_text(encoding="utf-8")
        line = 'PROFILE_COLUMN = "profile の行"\n'
        check("古い spec-loop の試料が作れない", infra_src.count(line) == 1)
        (stale / "scripts" / "check-infra-csv.py").write_text(infra_src.replace(line, ""), encoding="utf-8")
        fake = tmp / "fake"
        (fake / ".claude-plugin").mkdir(parents=True)
        (fake / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "not-spec-loop", "version": "0.133.0"}), encoding="utf-8")
        tokens = {"clone": str(clone), "fake": str(fake), "old": str(old), "stale": str(stale), "docs": ""}

        def layout(where: Path, platform_source: str | None = None) -> Path:
            platform = lay_out(where, platform_source)
            (where / "spec-loop").symlink_to(spec_loop, target_is_directory=True)
            return platform

        platform = layout(tmp / "plugins")
        before_clone = clone_state(clone, env)
        results = {}
        for index, (name, files, args, _, _, _) in enumerate(CASES):
            results[name] = run_case(platform, tmp / f"case{index}", files, args, tokens, env)
            check(f"試料が期待どおりでない: {name}", as_expected(name, results[name]), f"exit={results[name][0]} {results[name][1][-500:]}")

        # 読むだけ（受入基準 B6）: clone と正本が変わらない・__pycache__ ができない
        check("clone の状態が変わった", clone_state(clone, env) == before_clone)
        project = tmp / "readonly" / "project"
        work = tmp / "readonly"
        files = {rel: body for rel, body in OK.items()}
        run_case(platform, work, files, [], tokens, env)  # 正本を作って 1 度走らせる
        before_tree = tree_state(project)
        proc = subprocess.run([sys.executable, "-I", str(platform / "scripts" / TARGET), str(project / "docs")], capture_output=True, text=True,
                              cwd=work / "elsewhere", env=env)
        check("読むだけの確かめの試料が 0 でない", proc.returncode == 0, proc.stdout + proc.stderr)
        check("正本のファイルが変わった", tree_state(project) == before_tree)
        caches = [str(p) for p in list(tmp.joinpath("plugins").rglob("__pycache__")) + list(spec_loop.rglob("__pycache__"))]
        check("写したプラグインに __pycache__ ができた", not caches, ", ".join(caches))

        # 原本との突き合わせ
        module = load(platform / "scripts" / TARGET)
        infra_md = REF_INFRA.read_text(encoding="utf-8")
        spec_loop_md = REF_SPEC_LOOP.read_text(encoding="utf-8")
        problems = reference_mismatches(module, infra_md, spec_loop_md)
        check("本体の定数が references と一致しない", not problems, "; ".join(problems))
        for which, before, after in REFERENCE_MUTATIONS:
            text = infra_md if which == "infra" else spec_loop_md
            if text.count(before) != 1:
                check(f"崩す箇所が 1 回でない: {before}", False, f"{text.count(before)} 回")
                continue
            broken = (text.replace(before, after), spec_loop_md) if which == "infra" else (infra_md, text.replace(before, after))
            check(f"崩しても不一致にならない: {before}", bool(reference_mismatches(module, *broken)))

        # 変異
        guarded = guarded_lines(source)
        check("変異の数が「守ること」の行の数と違う", len(guarded) == len(MUTATIONS), f"守ること {len(guarded)} 行・変異 {len(MUTATIONS)} 件")
        killers = {killer for _, _, _, killer in MUTATIONS}
        check("変異の殺す試料が試料に無い", killers <= set(names), ", ".join(sorted(killers - set(names))))
        # 陰性対照: 壊さない写しを同じ置き方で置けば、殺す試料はどれも期待どおり（変異の置き方が結果を決めていない）
        control = layout(tmp / "control", source)
        for index, killer in enumerate(sorted(killers)):
            files, args = next((f, a) for n, f, a, _, _, _ in CASES if n == killer)
            result = run_case(control, tmp / f"controlwork{index}", files, args, tokens, env)
            check(f"壊さない写しで殺す試料が期待どおりでない: {killer}", as_expected(killer, result), result[1][-300:])
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = layout(tmp / f"mut{index}", source.replace(before, after))
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
