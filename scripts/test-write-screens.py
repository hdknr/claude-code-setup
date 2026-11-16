#!/usr/bin/env python3
"""`write-screens.py`（screen-spec の `init`・`add` のスキルが呼ぶ書き込み。#1093）と雛形の回帰テスト。

    python3 scripts/test-write-screens.py

**本体と雛形はプラグインの中にある**（`plugins/screen-spec/scripts/`・`plugins/screen-spec/templates/`）。
spec-loop のスクリプトを読み込むので、一時ディレクトリに `plugins/screen-spec/`（本体）と `plugins/spec-loop/`（本物の spec-loop の
`.claude-plugin/` と `scripts/` の写し）を並べ、**スキルの手順をスクリプトで再現する**（`hint` → `init` → `add` → `check-screens.py`）。

見るもの:

1. **#1093 の受入基準**——空の案件（`docs/v1/` だけ）に `init` → `add` した直後に `check-screens.py` が 0（U1）。
   `add`（と `init`）が Q&A 表を書き換えない——実行の前後で正本の全ファイルを比べ、変わったのが書くと決めたファイルだけ（U2）。
   表に置いた次元の節は表を出す印だけを持つ——雛形と、`add` が作った仕様書の両方で（U3）。
2. **採番**——前の版の画面・`removed.csv` で消した画面・項目の番号と重ねない。設定の接頭辞を使う。
3. **書けないときは 1 つも書かない**——置き済みの `init`・`init` の前の `add`・引数の誤り・版が無い・重ね合わせの違反・spec-loop の版の範囲の外。
4. **雛形が `references/prose.md` の「雛形」に合う**（節の名前と順・印・未決定の印と Q&A の番号と「決定」「確定」が無い・差し込み）。崩すと落ちることも見る。
5. **本体の定数が `references/tables.md` の原本と一致する**（写しのずれ。崩すと落ちることも見る）。
6. **リポジトリの外で単体で動く**——どの実行も `python3 -I`。spec-loop を隣に置かない形（`--spec-loop`）も当てる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME` を一時ディレクトリにし、`CLAUDE_CONFIG_DIR`・`SCREEN_SPEC_SPEC_LOOP` を外す。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "screen-spec"
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
TARGET = "write-screens.py"
CHECK = "check-screens.py"
REFS = PLUGIN / "references"

SD = "v1/requirements/screens/"
QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
S_HEAD = "画面ID,画面名,種別,親画面,主たる利用者,ステータス,参考資料,目的と背景,できること,機能,帳票,仕様書,根拠\n"
I_HEAD = "番号,画面ID,まとまり,並び順,項目名,種類,中身,例,必須,入力チェック,エラーメッセージ,並び替え,絞り込み,根拠\n"
T_HEAD = "番号,遷移元,きっかけ,操作,条件,遷移先,結果,根拠\n"
SETTINGS = "項目,値\n画面IDの接頭辞,S-\nprofile,未設定\n"
MARK = "<!-- screen-spec: 表 -->"
INIT_FILES = [SD + p for p in ("data/screens.csv", "data/screen-items.csv", "data/transitions.csv", "settings.csv", "common.md", "templates/spec.md")]
DIR = None  # 試料の値が DIR ならディレクトリだけを作る


def add(name: str = "受注一覧", kind: str = "top", **extra: str) -> list[str]:
    values = {"name": name, "kind": kind, "user": "担当者", "purpose": "受注を探す", "can": "一覧と絞り込み", "basis": "業務ルール: 担当者が受注を探す"}
    values.update(extra)
    argv = ["add"]
    for flag, value in values.items():
        argv += [f"--{flag}", value]
    return argv


def added(key: str, version: str = "v1") -> list[str]:
    root = f"{version}/requirements/screens/"
    return [root + "data/screens.csv", f"{root}{key}.md", f"{root}wireframes/{key}.drawio"]


def doc(key: str, name: str) -> str:
    """検査を通る仕様書（雛形の形）。"""
    text = (PLUGIN / "templates" / "spec.md").read_text(encoding="utf-8")
    return text.replace("{{画面ID}}", key).replace("{{画面名}}", name)


V1_TWO = {  # 手で置いた v1（画面 2 つ・項目と遷移つき）
    SD + "data/screens.csv": S_HEAD + "S-001,受注一覧,top,,担当者,記入中,,探す,一覧,,,S-001.md,業務\n"
                             + "S-002,受注登録,form,,担当者,記入中,,入れる,入力,,,S-002.md,業務\n",
    SD + "data/screen-items.csv": I_HEAD + "I-001,S-001,操作,1,新規,ボタン,,,,,,,,業務\n",
    SD + "data/transitions.csv": T_HEAD + "T-001,S-001,I-001,,,S-002,,業務\n",
    SD + "settings.csv": SETTINGS,
    SD + "S-001.md": doc("S-001", "受注一覧"),
    SD + "S-002.md": doc("S-002", "受注登録"),
}
REMOVE_S002 = "種類,対象,理由\n画面,S-002,使わない\n遷移,T-001,使わない\n項目,I-001,使わない\nファイル,requirements/screens/S-002.md,使わない\n"
INFRA = "項目,決定,理由,費用への影響,水準,根拠,状態\nフロントエンド,React（SPA）,既存の資産,無し,,Q-F-001,決定\n"
QA = QA_HEAD + "Q-R-001,要求確定,質問,A: はい / B: いいえ,A,理由,未回答,—,確認中,\nQ-F-001,実現性・コスト,質問,A: はい / B: いいえ,A,理由,A,shared/infra.csv,反映済み,A は安い\n"
QA_DEV = QA_HEAD + "D-S-001,仕様レビュー,質問,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n"

# (名前, 正本のファイル, 手順 [(write-screens の引数, 終了コード, 出力に在る文字列)], 検査（check-screens の終了コード, 出力に在る文字列）か None,
#  書いてよいファイル（全手順の後に変わったファイルの全部。None なら見ない）, 中身 {パス: 在る文字列})
# 手順の引数の "<alone>" は spec-loop を隣に置かずに `--spec-loop` で渡す、"<old>" は範囲の外の版の spec-loop を渡す
CASES: list[tuple] = [
    # ---- U1・U2・U3: 空の案件に init → add
    ("empty-init-add", {"v1": DIR}, [
        (["hint"], 0, "このプラグインにはまだ無い——未設定 にする"),
        (["init"], 0, "画面IDの接頭辞: S-、profile: 未設定"),
        (add(), 0, "画面ID: S-001"),
    ], (0, "違反 0 件・必須の欄が空 0 件・未決定 0 件・警告 0 件・起票の候補 0 件"), INIT_FILES + added("S-001")[1:],
     {SD + "data/screens.csv": "S-001,受注一覧,top,,担当者,下書き,,受注を探す,一覧と絞り込み,,,S-001.md,業務ルール: 担当者が受注を探す\n",
      SD + "settings.csv": SETTINGS, SD + "S-001.md": "# S-001 受注一覧\n"}),
    ("with-qa-features-infra", {"v1/shared/qa.csv": QA, "v1/spec/qa-dev.csv": QA_DEV, "v1/shared/infra.csv": INFRA,
                                "v1/requirements/features.csv": "id,名前,種類,関係\nF-001,受注一覧,画面,\n"}, [
        (["hint"], 0, "フロントエンド: React（SPA）（状態: 決定）"),
        (["init", "--prefix", "SCR-"], 0, "画面IDの接頭辞: SCR-"),
        (add(basis="Q-R-001、F-001", features="F-001"), 0, "画面ID: SCR-001"),
    ], (0, "違反 0 件・必須の欄が空 0 件・未決定 0 件"), INIT_FILES + added("SCR-001")[1:], {}),
    ("tab-with-parent", {"v1": DIR}, [
        (["init"], 0, ""), (add(), 0, "S-001"), (add("明細", "tab", parent="S-001"), 0, "画面ID: S-002"),
    ], (0, "違反 0 件"), INIT_FILES + added("S-001")[1:] + added("S-002")[1:], {}),
    ("second-screen-unreachable", {"v1": DIR}, [
        (["init"], 0, ""), (add(), 0, "S-001"), (add("受注登録", "form"), 0, "画面ID: S-002"),
    ], (1, "S-002: 入口の画面から遷移で辿れない"), None, {}),
    ("undecided-cell-is-candidate", {"v1": DIR}, [
        (["init"], 0, ""), (add(purpose="未定"), 0, "S-001"),
    ], (3, "起票の候補: requirements/screens/data/screens.csv S-001 目的と背景: 未定"), None, {}),
    ("plugin-template-when-none", {**V1_TWO}, [
        (add("設定", "setting"), 0, "仕様書の雛形: " + "<plugin>/templates/spec.md"),
    ], None, added("S-003")[:1] + added("S-003")[1:], {SD + "S-003.md": "# S-003 設定\n"}),
    ("project-template-used", {"v1": DIR}, [
        (["init"], 0, ""),
        (["<edit>", SD + "templates/spec.md", "# {{画面ID}} {{画面名}}\n", "# {{画面ID}} {{画面名}}\n\n案件の雛形の行\n"], 0, ""),
        (add(), 0, "仕様書の雛形: requirements/screens/templates/spec.md"),
    ], (0, "違反 0 件"), None, {SD + "S-001.md": "案件の雛形の行"}),
    ("escapes-drawio-and-csv", {"v1": DIR}, [
        (["init"], 0, ""), (add('A<&>"B, C'), 0, "S-001"),
    ], (0, "違反 0 件"), None, {SD + "wireframes/S-001.drawio": "<xml:S-001 A<&>\"B, C>", SD + "data/screens.csv": '"A<&>""B, C"'}),
    # ---- 採番
    ("numbering-v2-removed", {**V1_TWO, "v2/removed.csv": REMOVE_S002}, [
        (add("設定", "setting"), 0, "画面ID: S-003（版 v2"),
    ], None, ["v2/requirements/screens/data/screens.csv", "v2/requirements/screens/S-003.md", "v2/requirements/screens/wireframes/S-003.drawio"],
     {"v2/requirements/screens/data/screens.csv": S_HEAD + "S-003,設定,setting,"}),
    ("numbering-avoids-item-keys", {**V1_TWO, SD + "data/screen-items.csv": I_HEAD + "I-001,S-001,操作,1,新規,ボタン,,,,,,,,業務\n"
                                    + "S-007,S-001,表示,2,備考,表示,備考,,,,,,,業務\n"}, [
        (add("設定", "setting"), 0, "画面ID: S-008"),
    ], None, None, {}),
    ("numbering-appends-in-v2", {**V1_TWO, "v2/requirements/screens/data/screens.csv": S_HEAD + "S-009,一覧,setting,,担当者,記入中,,a,b,,,S-009.md,業務\n",
                                 "v2/requirements/screens/S-009.md": doc("S-009", "一覧")}, [
        (add("設定", "setting"), 0, "画面ID: S-010"),
    ], None, None, {"v2/requirements/screens/data/screens.csv": "S-009.md,業務\nS-010,設定,setting,"}),
    # ---- 書けないときは書かない
    ("init-twice", {"v1": DIR}, [(["init"], 0, ""), (["init"], 3, "置き済み——init は何も書かない")], None, INIT_FILES, {}),
    ("add-before-init", {"v1": DIR}, [(add(), 3, "requirements/screens/data/screens.csv が無い——先に init を走らせる")], None, [], {}),
    ("no-version", {}, [(["init"], 3, "版（v1 など）が 1 つも無い")], None, [], {}),
    ("broken-merge", {**V1_TWO, "v2/removed.csv": "種類,対象,理由\n画面,S-099,無い\n"}, [(add(), 1, "重ね合わせが決まりに反する")], None, [], {}),
    ("bad-kind", {"v1": DIR}, [(["init"], 0, ""), (add(kind="page"), 2, "種別 'page' は決まった値")], None, INIT_FILES, {}),
    ("tab-without-parent", {"v1": DIR}, [(["init"], 0, ""), (add(kind="tab"), 2, "種別 tab には親画面")], None, INIT_FILES, {}),
    ("parent-missing", {"v1": DIR}, [(["init"], 0, ""), (add(kind="dialog", parent="S-404"), 2, "親画面 S-404 が画面の表に無い")], None, INIT_FILES, {}),
    ("parent-on-top", {"v1": DIR}, [(["init"], 0, ""), (add(parent="S-001"), 2, "種別 top には親画面を書かない")], None, INIT_FILES, {}),
    ("empty-required", {"v1": DIR}, [(["init"], 0, ""), (add(purpose=" "), 2, "目的と背景 が空")], None, INIT_FILES, {}),
    ("missing-arg", {"v1": DIR}, [(["init"], 0, ""), (add()[:-2], 2, "add には --basis が要る")], None, INIT_FILES, {}),
    ("bad-prefix", {"v1": DIR}, [(["init", "--prefix", "s-"], 2, "画面IDの接頭辞 's-'")], None, [], {}),
    ("prefix-collides-feature", {"v1": DIR}, [(["init", "--prefix", "F-"], 2, "成果物の表の番号")], None, [], {}),
    ("prefix-looks-like-qa", {"v1": DIR}, [(["init", "--prefix", "Q-"], 2, "Q&A の番号の形になる"), (["init", "--prefix", "D-"], 2, "Q&A の番号の形になる")],
     None, [], {}),
    ("prefix-has-marker", {"v1": DIR}, [(["init", "--prefix", "TBD-"], 2, "未決定の印を含む"), (["init", "--prefix", "TODO-"], 2, "未決定の印を含む")],
     None, [], {}),
    ("settings-prefix-looks-like-qa", {**V1_TWO, SD + "settings.csv": "項目,値\n画面IDの接頭辞,Q-\nprofile,未設定\n"},
     [(add("設定", "setting"), 3, "Q&A の番号の形になる")], None, [], {}),
    ("place-blocked-writes-nothing", {**V1_TWO, SD + "wireframes": "ファイル\n"},
     [(add("設定", "setting"), 3, "置き場所に書けない——何も書いていない")], None, [], {}),
    ("unknown-profile", {"v1": DIR}, [(["init", "--profile", "web-spa"], 2, "profile 'web-spa' はこのプラグインに無い")], None, [], {}),
    ("settings-bad-prefix", {**V1_TWO, SD + "settings.csv": "項目,値\n画面IDの接頭辞,x\nprofile,未設定\n"}, [(add(), 3, "settings.csv: 画面IDの接頭辞 'x'")], None, [], {}),
    ("spec-file-taken", {**V1_TWO, SD + "S-003.md": doc("S-003", "残り")}, [(add("設定", "setting"), 3, "雛形の置き場所が使われている")], None, [], {}),
    ("spec-loop-out-of-range", {"v1": DIR}, [(["init", "<old>"], 4, "対応の範囲")], None, [], {}),
    ("alone-with-spec-loop-arg", {"v1": DIR}, [(["init", "<alone>"], 0, ""), (add() + ["<alone>"], 0, "S-001")], None, INIT_FILES + added("S-001")[1:], {}),
    ("usage", {"v1": DIR}, [(["nothing"], 2, "usage: python3 write-screens.py hint")], None, [], {}),
]


failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def copy_spec_loop(dest: Path, version: str | None = None) -> Path:
    assert_in_tmp(dest)
    for part in (".claude-plugin", "scripts"):
        shutil.copytree(SPEC_LOOP / part, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
    if version is not None:
        manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        manifest["version"] = version
        (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return dest


def copy_plugin(dest: Path, source: Path = PLUGIN) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def changed(before: dict[str, bytes], after: dict[str, bytes]) -> list[str]:
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def drawio_title(text: str) -> str:
    root = ET.fromstring(text)
    cell = next(c for c in root.iter("mxCell") if c.get("id") == "title")
    return cell.get("value")


def run_case(plugin: Path, case_dir: Path, case) -> tuple[bool, str]:
    """(期待どおりか, 説明)。"""
    name, files, steps, final, allowed, contents = case
    assert_in_tmp(case_dir)
    docs = case_dir / "docs"
    docs.mkdir(parents=True)
    for rel, body in files.items():
        path = docs / rel
        if body is DIR:
            path.mkdir(parents=True, exist_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    home = case_dir / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR", "SCREEN_SPEC_SPEC_LOOP")}
    env["HOME"] = str(home)
    alone = None
    start = snapshot(docs)
    watched = plugin.parent  # 読み込んだプラグインに `__pycache__` を書かない
    plugins_before = snapshot(watched)
    for argv, code, text in steps:
        if argv[0] == "<edit>":
            path = docs / argv[1]
            path.write_text(path.read_text(encoding="utf-8").replace(argv[2], argv[3]), encoding="utf-8")
            start = {**start, argv[1]: path.read_bytes()}  # 手で直したのは書いたファイルに数えない
            continue
        script = plugin / "scripts" / TARGET
        extra: list[str] = []
        args = [a for a in argv if a not in ("<alone>", "<old>")]
        if "<alone>" in argv:
            if alone is None:
                alone = copy_plugin(case_dir / "alone" / "screen-spec", plugin)
                copy_spec_loop(case_dir / "elsewhere" / "spec-loop")
            script = alone / "scripts" / TARGET
            extra = ["--spec-loop", str(case_dir / "elsewhere" / "spec-loop")]
        if "<old>" in argv:
            extra = ["--spec-loop", str(copy_spec_loop(case_dir / "old" / "spec-loop", version="0.92.0"))]
        command = args[:1] + ([str(docs)] if args[0] in ("hint", "init", "add") else []) + args[1:] + extra
        before = snapshot(docs)
        proc = subprocess.run([sys.executable, "-I", str(script), *command], capture_output=True, text=True, cwd=case_dir, env=env)
        out = proc.stdout + proc.stderr
        for where in sorted({str(p) for p in (plugin, plugin.resolve(), *(() if alone is None else (alone, alone.resolve())))}, key=len, reverse=True):
            out = out.replace(where, "<plugin>")
        if "Traceback" in out:
            return False, f"{argv[:2]}: Traceback {out[-400:]}"
        if proc.returncode != code or text not in out:
            return False, f"{argv[:2]}: exit={proc.returncode}（期待 {code}）{out[-400:]}"
        if code != 0 and snapshot(docs) != before:
            return False, f"{argv[:2]}: 0 以外なのに正本を書いた: {changed(before, snapshot(docs))}"
    if snapshot(watched) != plugins_before:
        return False, f"読み込んだプラグインにファイルを書いた: {changed(plugins_before, snapshot(watched))}"
    after = snapshot(docs)
    if allowed is not None and changed(start, after) != sorted(allowed):
        return False, f"書いたファイルが決めたものと違う: {changed(start, after)}"
    for rel, needle in contents.items():
        body = after.get(rel, b"").decode("utf-8")
        if needle.startswith("<xml:"):
            try:
                ok = drawio_title(body) == needle[len("<xml:"):-1]
            except (ET.ParseError, StopIteration):
                ok = False
            if not ok:
                return False, f"{rel}: drawio の見出しが {needle!r} でない"
        elif needle not in body:
            return False, f"{rel}: {needle!r} が無い"
    for rel in after:
        if rel.endswith(".md") and "/requirements/screens/" in rel and rel not in start and Path(rel).name not in ("common.md", "spec.md"):
            problems = section_problems(after[rel].decode("utf-8"))
            if problems:
                return False, f"{rel}: 作った仕様書が雛形の決まりに合わない: {problems}"
    if final is not None:
        proc = subprocess.run([sys.executable, "-I", str(plugin / "scripts" / CHECK), str(docs)], capture_output=True, text=True, cwd=case_dir, env=env)
        out = proc.stdout + proc.stderr
        if proc.returncode != final[0] or final[1] not in out:
            return False, f"check-screens: exit={proc.returncode}（期待 {final[0]}）{out[-400:]}"
    return True, ""


def run_cases(plugin: Path, work: Path, only: str | None = None) -> dict[str, tuple[bool, str]]:
    return {case[0]: run_case(plugin, work / f"case{i}", case) for i, case in enumerate(CASES) if only is None or case[0] == only}


# ---- 雛形の決まり（`references/prose.md` の「雛形」）


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sys.dont_write_bytecode = True
CHECKS = load("check_screens_for_test", PLUGIN / "scripts" / CHECK)
SPEC_EXIT = load("check_spec_exit_for_test", SPEC_LOOP / "scripts" / "check-spec-exit.py")
QA_NUMBER = re.compile(r"(?<![A-Za-z0-9-])[QD]-(?:[A-Z]-)?[0-9]{3,}")


def sections(text: str) -> list[tuple[str, list[str]]]:
    """(`## ` の見出し, 中身の行) の並び。"""
    out: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            out.append((line[3:].strip(), []))
        elif out:
            out[-1][1].append(line)
    return out


def section_problems(text: str) -> list[str]:
    """節の名前と順・表で持つ節は印だけ・散文の節は空でない。"""
    found = sections(text)
    problems = []
    if [h for h, _ in found] != [h for h, _ in CHECKS.SECTIONS]:
        problems.append(f"節が {[h for h, _ in found]}")
    tabled = dict(CHECKS.SECTIONS)
    for heading, lines in found:
        body = [line.strip() for line in lines if line.strip()]
        if tabled.get(heading):
            if body != [MARK]:
                problems.append(f"表で持つ節 {heading} が印だけでない: {body}")
        elif not CHECKS.COMMENT.sub("", "\n".join(lines)).strip():
            problems.append(f"散文の節 {heading} が空")
    return problems


def template_problems(spec: str, common: str) -> list[str]:
    problems = section_problems(spec)
    if not spec.startswith("# {{画面ID}} {{画面名}}\n"):
        problems.append("仕様書の雛形の最初の見出しが # {{画面ID}} {{画面名}} でない")
    if "[TOC]" not in spec:
        problems.append("仕様書の雛形に目次（[TOC]）が無い")
    for label, text in (("仕様書", spec), ("共通仕様", common)):
        if SPEC_EXIT.find_markers(text):
            problems.append(f"{label}の雛形に未決定の印がある: {SPEC_EXIT.find_markers(text)}")
        if QA_NUMBER.search(text):
            problems.append(f"{label}の雛形に Q&A の番号がある")
        for word in ("決定", "確定"):
            if word in text:
                problems.append(f"{label}の雛形に「{word}」がある")
    names = [line[3:].strip() for line in common.splitlines() if line.startswith("## ")]
    prose = (REFS / "prose.md").read_text(encoding="utf-8")
    listed = re.search(r"- 節は、(.+?)。案件で要る節を足してよい", prose)
    if listed is None or names != listed.group(1).split("・"):
        problems.append(f"共通仕様の雛形の節 {names} が references/prose.md の「共通仕様」と違う")
    return problems


# (名前, 雛形, 壊す前, 壊した後)
TEMPLATE_MUTATIONS = [
    ("表で持つ節に散文を書く", "spec", "## 3. レイアウト\n\n<!-- screen-spec: 表 -->\n", "## 3. レイアウト\n\n<!-- screen-spec: 表 -->\n画面の上に検索\n"),
    ("表で持つ節から印を外す", "spec", "## 4. データ表示\n\n<!-- screen-spec: 表 -->\n", "## 4. データ表示\n\n一覧の列\n"),
    ("節を落とす", "spec", "## 9. 他システム連携\n", "## 9. ほか\n"),
    ("散文の節を空にする", "spec", "N/A。この画面は他のシステムとやりとりしない。\n", "\n"),
    ("未決定の印を置く", "spec", "N/A。この画面に未決の論点は無い。", "未定"),
    ("「確定」を置く", "spec", "N/A。この画面に未決の論点は無い。", "確定した。"),
    ("Q&A の番号を置く", "common", "## 用語\n", "## 用語\n\nQ-R-001\n"),
    ("共通仕様の節を落とす", "common", "## 用語\n", "## ことば\n"),
    ("差し込みを外す", "spec", "# {{画面ID}} {{画面名}}\n", "# 画面\n"),
]


# ---- 本体の定数と `references/tables.md`


def section_of(markdown: str, heading: str) -> str:
    start = markdown.index(heading)
    rest = markdown[start + len(heading):]
    found = re.search(r"^#{1,2} ", rest, flags=re.MULTILINE)
    return rest[:found.start()] if found else rest


def reference_mismatches(module, tables: str) -> list[str]:
    problems = []
    try:
        settings = section_of(tables, "## 案件ごとの設定（`settings.csv`）")
        rules = section_of(tables, "## `init` と `add`")
        tree = section_of(tables, "## 置き場所")
    except ValueError as e:
        return [f"references/tables.md の節が無い: {e}"]
    rows = {m.group(1): m.group(2) for m in re.finditer(r"^\| `([^`]+)` \|.*\| `([^`]+)` \|$", settings, flags=re.MULTILINE)}
    if rows != {module.PREFIX_KEY: module.DEFAULT_PREFIX, module.PROFILE_KEY: module.UNSET}:
        problems.append(f"設定の項目と既定 {rows} が本体と違う")
    if f"見出し行は `{','.join(module.SETTINGS_COLUMNS)}`" not in settings:
        problems.append("設定の見出し行が本体と違う")
    for path, where in ((module.SETTINGS, tree), (module.SPEC_TEMPLATE, tree)):
        if Path(path).name not in where:
            problems.append(f"{path} が置き場所に無い")
    if f"`requirements/screens/{Path(module.SETTINGS).name}`" not in settings:
        problems.append("設定のファイルの置き場所が本体と違う")
    if f"{module.ID_DIGITS} 桁以上の 0 埋め" not in rules:
        problems.append("採番の桁が本体と違う")
    if f"`ステータス` は `{module.DRAFT}`" not in rules:
        problems.append("足した行のステータスが本体と違う")
    if "`wireframes/<画面ID>.drawio`" not in rules or module.WIREFRAMES != CHECKS.SCREENS_DIR + "wireframes/":
        problems.append("ワイヤーフレームの置き場所が本体と違う")
    if f"`{'`・`'.join(module.FRONTEND)}`" not in tables:
        problems.append("フロントエンドの行の綴りが本体と違う")
    return problems


REFERENCE_MUTATIONS = [
    ("接頭辞の既定", "| `S-` |", "| `A-` |"),
    ("profile の既定", "| `未設定` |", "| `なし` |"),
    ("設定の見出し行", "見出し行は `項目,値`", "見出し行は `名前,値`"),
    ("採番の桁", "3 桁以上の 0 埋め", "4 桁以上の 0 埋め"),
    ("足した行のステータス", "`ステータス` は `下書き`", "`ステータス` は `記入中`"),
    ("フロントエンドの綴り", "`frontend`・`フロントエンド`", "`front`・`フロントエンド`"),
]


# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("最大の番号の次でなく最大を採る", "max(numbers, default=0) + 1", "max(numbers, default=0)", "numbering-v2-removed"),
    ("項目と遷移の表の鍵を数えない", "            for path in checks.TABLES:\n                file = root / path",
     "            for path in checks.TABLES[:1]:\n                file = root / path", "numbering-avoids-item-keys"),
    ("作業中の版の表に足さず置き直す", "    if own.is_file():", "    if False:", "numbering-appends-in-v2"),
    ("置き済みでも init が書く", "    if there:\n        raise Refused(\"置き済み", "    if False:\n        raise Refused(\"置き済み", "init-twice"),
    ("種別を確かめない", "    if kind not in checks.SCREEN_KINDS:", "    if False:", "bad-kind"),
    ("tab に親画面を求めない", "        if not parent:\n", "        if False:\n", "tab-without-parent"),
    ("親画面が表に在るかを見ない", "        if parent not in screens:", "        if False:", "parent-missing"),
    ("必須の欄の空を見ない", "        if not values[column].strip():", "        if False:", "empty-required"),
    ("ステータスを下書きにしない", '"ステータス": DRAFT,', '"ステータス": "記入中",', "empty-init-add"),
    ("案件の雛形を使わない", "    template = docs.text(SPEC_TEMPLATE)", "    template = None", "project-template-used"),
    ("drawio に差し込む値を XML にしない", "escape(name, {'\"': \"&quot;\"})", "name", "escapes-drawio-and-csv"),
    ("接頭辞の形を見ない", "    if not PREFIX.fullmatch(prefix):", "    if False:", "bad-prefix"),
    ("Q&A の番号の形を見ない", "    if any(shape.fullmatch(sample) for shape in (qa.NUMBER, qa.INTERNAL_NUMBER)):", "    if False:", "prefix-looks-like-qa"),
    ("未決定の印を見ない", "    if docs.design.spec_exit.find_markers(sample):", "    if False:", "prefix-has-marker"),
    ("書けない置き場所を書く前に見ない", "        if blocked:\n", "        if False:\n", "place-blocked-writes-nothing"),
    ("成果物の表の番号と重ねてよい", "    if prefix in taken:", "    if False:", "prefix-collides-feature"),
    ("profile を確かめない", "    if profile != UNSET and profile not in profiles():", "    if False:", "unknown-profile"),
    ("spec-loop の版を確かめない", "        shown = checks.check_version(spec_loop)", "        shown = '?'", "spec-loop-out-of-range"),
    ("版が無いのを見ない", "            if not self.versions.find_versions(docs, []):", "            if False:", "no-version"),
    ("雛形の置き場所が使われていても書く", "    if there:\n        raise Refused(f\"画面ID", "    if False:\n        raise Refused(f\"画面ID", "spec-file-taken"),
    ("init の前の add を止めない", "        if path not in docs.whole.headers:\n            raise Refused", "        if False:\n            raise Refused", "add-before-init"),
    ("重ね合わせの違反でも書く", "        if problems:\n            raise Broken(\"\\n\".join(f\"版の重ね合わせ", "        if False:\n            raise Broken(\"\\n\".join(f\"版の重ね合わせ", "broken-merge"),
    ("設定の接頭辞を使わない", "prefix = check_prefix(settings.get(PREFIX_KEY, \"\"), docs)", "prefix = check_prefix(\"S-\", docs)",
     "with-qa-features-infra"),
]


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    killers = {killer for *_, killer in MUTATIONS}
    assert killers <= set(names), f"変異の殺す試料が無い: {killers - set(names)}"
    with tempfile.TemporaryDirectory(prefix="write-screens-test-") as tmp:
        tmp_path = Path(tmp)
        plugin = copy_plugin(tmp_path / "plugins" / "screen-spec")
        copy_spec_loop(tmp_path / "plugins" / "spec-loop")
        results = run_cases(plugin, tmp_path / "work")
        for case in CASES:
            ok, detail = results[case[0]]
            check(f"試料が期待どおりでない: {case[0]}", ok, detail)

        templates = {"spec": (PLUGIN / "templates" / "spec.md").read_text(encoding="utf-8"),
                     "common": (PLUGIN / "templates" / "common.md").read_text(encoding="utf-8")}
        problems = template_problems(templates["spec"], templates["common"])
        check("雛形が references/prose.md の「雛形」に合わない", not problems, "; ".join(problems))
        for name, which, before, after in TEMPLATE_MUTATIONS:
            if templates[which].count(before) != 1:
                check(f"崩すと落ちる: {name}", False, f"崩す箇所が {templates[which].count(before)} 回現れる")
                continue
            broken = dict(templates)
            broken[which] = templates[which].replace(before, after)
            check(f"崩すと落ちる: {name}", bool(template_problems(broken["spec"], broken["common"])))

        module = load("write_screens_for_test", PLUGIN / "scripts" / TARGET)
        tables = (REFS / "tables.md").read_text(encoding="utf-8")
        problems = reference_mismatches(module, tables)
        check("本体の定数が references/tables.md と一致しない", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if tables.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {tables.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(module, tables.replace(before, after))))

        source = (PLUGIN / "scripts" / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            root = tmp_path / f"mut{index}" / "plugins"
            mutated = copy_plugin(root / "screen-spec")
            copy_spec_loop(root / "spec-loop")
            (mutated / "scripts" / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            ok, detail = run_cases(mutated, tmp_path / f"mutwork{index}", only=killer)[killer]
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not ok, detail)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・雛形の崩し {len(TEMPLATE_MUTATIONS)} 件・references の崩し {len(REFERENCE_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
