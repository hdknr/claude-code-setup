#!/usr/bin/env python3
"""platform-spec の `profile-layers.py`（外部の profile のアーキテクチャの層と開発の進め方の層を、Domain Checker の照合先の一覧と `.claude/dev-loop.md` の雛形にして出す。#1558）の回帰テスト。

    python3 scripts/test-profile-layers.py

**本体はプラグインの中にある**（`plugins/platform-spec/scripts/`）。同じ場所の `check-infra-profile.py` と、spec-loop の重ね方と外部の profile の読み方（`external-profile.py`）を読み込むので、
**一時ディレクトリに本物の spec-loop と platform-spec の写しを並べて**走らせる（隣の `spec-loop` を見つける形。`test-check-infra-profile.py` と同じ置き方）。

見るもの:

1. **出すものの形**（#1558 の受入基準）——照合先の一覧に行ごとの ID・観点・要約・本文の参照と読むコマンド、雛形に印・項目ごとの節・行の形・`impl_module` の行を分けて出すこと、
   **雛形（標準出力）に手元の clone のパスが出ないこと**。profile は一時の git リポジトリにタグを付けて作る。ネットワークには出ない。
2. **止まり方を分ける**——設定が無い・層が無いは 3、設定の形・重ね合わせ・切れたリンクは 1、層の形（見出し・語彙・1 行まで・空・改行）と clone・タグ・形式の版は 4、引数は 2。
3. **読むだけ**——走らせた前後で、profile の clone の `git status --porcelain`・HEAD・`git for-each-ref` と、正本のファイル（中身まで）が変わらない。写したプラグインに `__pycache__` ができない。
4. **本体の定数が `plugins/platform-spec/references/layers.md` の原本と一致し、雛形の印と行の形が dev-loop の `references/profile-template.md`（読み方の原本）・`SKILL.md` と一致し、
   `impl_module` の行が spec-loop の `references/monorepo.md` の例と一致する**（崩すと不一致になる陽性対照つき）。
5. **変異テスト**——本体を 1 箇所ずつ壊し、名指しした試料が期待どおりでなくなること（壊さない写しを同じ置き方で置くと期待どおりになる陰性対照つき）。**変異の数は docstring の「守ること」の行の数と同じ**（手で数えない）。
   変異ごとに、壊す箇所が本体にちょうど 1 回現れることを先に確かめる。

**このテストは実環境を触らない。** `HOME`・`CLAUDE_CONFIG_DIR`・`GIT_CONFIG_GLOBAL` を一時ディレクトリに差し替え、`SPEC_PROFILE_CLONE`・`PLATFORM_SPEC_SPEC_LOOP`・`GIT_*` を子に渡さない。
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

REAL_REPO = Path(__file__).resolve().parent.parent
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
PLATFORM = REAL_REPO / "plugins" / "platform-spec"
TARGET = "profile-layers.py"
SOURCE = PLATFORM / "scripts" / TARGET
REF_LAYERS = PLATFORM / "references" / "layers.md"
REF_TEMPLATE = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "references" / "profile-template.md"
DEV_LOOP_SKILL = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "SKILL.md"
REF_MONOREPO = SPEC_LOOP / "references" / "monorepo.md"
REPO = "org/guide"
TMP_PREFIX = "profile-layers-test-"  # 一時ディレクトリの名前の頭（手元のパスが出たかを、/var と /private/var の違いに依らずに見る）


def settings(tag: str = "v1", head: str = "項目,値") -> str:
    return f"{head}\nリポジトリ,{REPO}\nprofile,org\nタグ,{tag}\n"


S = "docs/v1/shared/platform/settings.csv"
CLAUDE = "CLAUDE.md"
DECL = f"外部の profile の clone: {REPO} {{clone}}\n"
OK = {S: settings(), CLAUDE: DECL}


def with_(base: dict, **changes) -> dict:
    out = dict(base)
    for key, value in changes.items():
        rel = {"settings": S, "claude": CLAUDE}.get(key, key)
        if value is None:
            out.pop(rel, None)
        else:
            out[rel] = value
    return out


ARCH_LINE = "- ARCH-1（API の方式）: 書き込みは command の API に分ける——本文: org/guide@v1:docs/guide.md#api"
VERIFY_LINE = "- VERIFY-1: 画面を確かめる（値: `make verify`）——本文: org/guide@v1:docs/guide.md#verify"
IMPL_BLOCK = ("- REPO-1: モノレポ——本文: なし\n\n<!-- platform-spec: ここから下は .claude/dev-loop.md ではなく、正本の CLAUDE.md に書く行（IMPL-1） -->\n"
              "## 正本の `CLAUDE.md` に書く行（scaffold が読む）\n\n- 実装のモジュール名（`impl_module`）: `app.spec_impl`\n")

# (名前, 正本のファイル, 引数（先頭はコマンド。{clone}・{docs} を置き換える）, 期待する終了コード, 含むべき文字列（標準出力と標準エラー）, 標準出力に含んではならない文字列)
CASES: list[tuple[str, dict, list[str], int, str, str]] = [
    ("照合先の一覧", OK, ["architecture"], 0, ARCH_LINE, "切れている"),
    ("照合先の読み方", OK, ["architecture"], 0, "本文は手元の clone のタグの時点を読む: `git -C ", ""),
    ("雛形", OK, ["dev-loop"], 0, "<!-- platform-spec: 開発の進め方 org/guide org v1 -->\n# dev-loop の追補設定", "観点"),
    ("雛形の行", OK, ["dev-loop"], 0, "## 実機検証（verify）の手順\n\n" + VERIFY_LINE, ""),
    ("雛形に手元のパスを書かない", OK, ["dev-loop"], 0, "## デプロイ経路", TMP_PREFIX),
    ("impl_module を分けて出す", OK, ["dev-loop"], 0, IMPL_BLOCK, ""),
    ("設定が無い", {CLAUDE: "なし\n", "docs/v1/requirements/x.md": "x\n"}, ["dev-loop"], 3, "platform-spec を使っていない", ""),
    ("設定の形", with_(OK, settings=settings(head="key,value")), ["architecture"], 1, "見出しの行が `項目,値` でない", "ARCH-1"),
    ("重ね合わせの違反", with_(OK, **{"docs/v2/removed.csv": "種類,対象\nファイル,shared/x.csv\n"}), ["architecture"], 1, "版の重ね合わせ: ", "ARCH-1"),
    ("アーキテクチャの層が無い", with_(OK, settings=settings("nolayers")), ["architecture"], 3, "アーキテクチャの層が無い", ""),
    ("開発の進め方の層が無い", with_(OK, settings=settings("nolayers")), ["dev-loop"], 3, "開発の進め方の層が無い", ""),
    ("アーキテクチャの見出し", with_(OK, settings=settings("archhead")), ["architecture"], 4, "形式の版 1 の `ID,要約,リンク,観点` でない", ""),
    ("開発の進め方の見出し", with_(OK, settings=settings("prochead")), ["dev-loop"], 4, "形式の版 1 の `ID,要約,リンク,項目,値` でない", ""),
    ("見出しの前の空の行", with_(OK, settings=settings("blankhead")), ["architecture"], 0, ARCH_LINE.replace("@v1:", "@blankhead:"), ""),
    ("観点が空", with_(OK, settings=settings("noview")), ["architecture"], 4, "ARCH-1 の 観点 が空", ""),
    ("語彙の外の項目", with_(OK, settings=settings("baditem")), ["dev-loop"], 4, "項目 'build' は語彙の外", ""),
    ("歯止めが 2 行", with_(OK, settings=settings("twoguard")), ["dev-loop"], 4, "項目 歯止め は 1 行まで", ""),
    ("impl_module が 2 行", with_(OK, settings=settings("twoimpl")), ["dev-loop"], 4, "項目 impl_module は 1 行まで", ""),
    ("impl_module の値が空", with_(OK, settings=settings("emptyimpl")), ["dev-loop"], 4, "IMPL-1 の 値 が空", ""),
    ("値の改行", with_(OK, settings=settings("newline")), ["dev-loop"], 4, "VERIFY-1 の 値 が改行を含む", ""),
    ("要約の改行", with_(OK, settings=settings("archnewline")), ["architecture"], 4, "ARCH-1 の 要約 が改行を含む", ""),
    ("値のバッククォート", with_(OK, settings=settings("backtick")), ["dev-loop"], 4, "GUARD-1 の 値 がバッククォートを含む", ""),
    ("符号化したリンク", with_(OK, settings=settings("encoded")), ["architecture"], 0,
     "- ARCH-2（オブジェクト権限）: 権限はオブジェクトごと——本文: org/guide@encoded:docs/a b.md#手順", "a%20b"),
    ("行の区切りの文字", with_(OK, settings=settings("u85")), ["dev-loop"], 4, "RULE-1 の 要約 が改行を含む", ""),
    ("正規化したリンク", with_(OK, settings=settings("dotted")), ["architecture"], 0,
     "- ARCH-2（オブジェクト権限）: 権限はオブジェクトごと——本文: org/guide@dotted:docs/guide.md#api", "x/.."),
    ("符号化した節", with_(OK, settings=settings("anchor")), ["architecture"], 0,
     "- ARCH-2（オブジェクト権限）: 権限はオブジェクトごと——本文: org/guide@anchor:docs/guide.md#手順", "%E6"),
    ("切れたリンク", with_(OK, settings=settings("broken")), ["architecture"], 1, "（リンクが切れている: ファイルがその時点に無い）", ""),
    ("前の版の時点", with_(OK, **{"docs/v2/shared/platform/settings.csv": settings("v2")}), ["architecture", "--upto", "1"], 0, ARCH_LINE, "@v2:"),
    ("後の版の時点", with_(OK, **{"docs/v2/shared/platform/settings.csv": settings("v2")}), ["architecture"], 0, ARCH_LINE.replace("@v1:", "@v2:"), ""),
    ("引数の clone", with_(OK, claude=None), ["dev-loop", "--clone", "{clone}"], 0, "出所: 引数 --clone", ""),
    ("clone が見つからない", with_(OK, claude=None), ["dev-loop"], 4, "手元の clone が見つからない", ""),
    ("タグが無い", with_(OK, settings=settings("v9")), ["architecture"], 4, "v9", ""),
    ("形式の版が範囲の外", with_(OK, settings=settings("fmt2")), ["architecture"], 4, "受け付ける範囲（1 以上 2 未満）の外", ""),
    ("知らないコマンド", OK, ["infra"], 2, "usage:", ""),
    ("引数が足りない", OK, ["--no-docs"], 2, "usage:", ""),
]

# docstring の「守ること」の行と同じ順の変異。(名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("設定が無いのに読みに行く", "        if settings is None:\n            raise Missing(", "        if False:\n            raise Missing(", "設定が無い"),
    ("設定の形の違反を通す", "        if self.violations:\n            return self.finish_quiet()", "        if False:\n            return self.finish_quiet()", "設定の形"),
    ("重ね合わせの違反を通す", "        if problems:\n            self.violations.extend", "        if False:\n            self.violations.extend", "重ね合わせの違反"),
    ("層が無いのを 4 にする", '            raise Missing(f"profile {name}（{repo} のタグ {tag}）に{layer_name}の層が無い: {e}") from None',
     '            raise Stop(f"profile {name}（{repo} のタグ {tag}）に{layer_name}の層が無い: {e}") from None', "アーキテクチャの層が無い"),
    ("アーキテクチャの見出しを見ない", "                if head != columns:", "                if head != columns and layer_name != ARCH:", "アーキテクチャの見出し"),
    ("開発の進め方の見出しを見ない", "                if head != columns:", "                if head != columns and layer_name != PROCESS:", "開発の進め方の見出し"),
    ("見出しの前の空の行を飛ばさない", "if any(cell.strip() for cell in row)), [])", "if True), [])", "見出しの前の空の行"),
    ("観点の空を通す", '                if not row["観点"].strip():', "                if False:", "観点が空"),
    ("語彙の外を通す", "            if item not in PROCESS_ITEMS:", "            if False:", "語彙の外の項目"),
    ("1 行までを見ない", "            if PROCESS_ITEMS[item][1] and seen[item] > 1:", "            if False:", "歯止めが 2 行"),
    ("impl_module の空を通す", '            if item == IMPL_MODULE and not row["値"].strip():', "            if False:", "impl_module の値が空"),
    ("改行を \\n と \\r だけで見る", '                if len((value + "x").splitlines()) > 1:', '                if "\\n" in value or "\\r" in value:', "行の区切りの文字"),
    ("バッククォートを通す", '            if "`" in row["値"]:', "            if False:", "値のバッククォート"),
    ("照合先に観点を載せない", "            line = f\"- {rid}（{row['観点'].strip()}）: {row['要約'].strip()}——本文: {ref}\"",
     "            line = f\"- {rid}: {row['要約'].strip()}——本文: {ref}\"", "照合先の一覧"),
    ("雛形に印を置かない", "        lines = [TEMPLATE_MARK.format(repo=repo, profile=name, tag=tag),", "        lines = [", "雛形"),
    ("雛形の本文の参照を崩す", "——本文: {self.reference(repo, tag, row['リンク'], self.tag_files, self.ext._safe_rel)}\"", "——本文: {row['リンク']}\"", "雛形の行"),
    ("雛形に手元のパスを書く", "self.template(settings, layer, broken)", "(self.template(settings, layer, broken) + str(clone))", "雛形に手元のパスを書かない"),
    ("impl_module を分けない", "            if item == IMPL_MODULE:\n                rid, row = rows[0]", "            if False:\n                rid, row = rows[0]",
     "impl_module を分けて出す"),
    ("符号化を戻さない", "            if decoded in files:", "            if False:", "符号化したリンク"),
    ("正規化しない", "        norm = safe_rel or (lambda path: path)", "        norm = (lambda path: path)", "正規化したリンク"),
    ("節を戻さない", "{sharp}{unquote(anchor)}\"", "{sharp}{anchor}\"", "符号化した節"),
    ("切れたリンクで 0", "        return 1 if broken else 0", "        return 0", "切れたリンク"),
    ("--upto を渡さない", "self.versions.merge(self.docs, self.upto)", "self.versions.merge(self.docs, None)", "前の版の時点"),
    ("--clone を渡さない", "ext.find_clone(repo, self.clone, self.docs.resolve().parent)", "ext.find_clone(repo, None, self.docs.resolve().parent)", "引数の clone"),
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


PROFILE = "層,形式の版,ファイル,重ねる先\n基盤,1,infra.csv,\nアーキテクチャ,1,architecture.csv,\n開発の進め方,1,process.csv,\n"
INFRA = "ID,要約,リンク,項目\nLANG-1,Python 3.12,,言語\n"
ARCH = "ID,要約,リンク,観点\nARCH-1,書き込みは command の API に分ける,docs/guide.md#api,API の方式\nARCH-2,権限はオブジェクトごと,,オブジェクト権限\n"
PROCESS = ("ID,要約,リンク,項目,値\n"
           "VERIFY-1,画面を確かめる,docs/guide.md#verify,verify,make verify\n"
           "DEPLOY-1,main へのマージで反映,https://example.com/deploy,deploy,\n"
           "GUARD-1,全部の検査,,歯止め,make check\n"
           "RULE-1,本番の DB を直に触らない,,制約,\n"
           "REPO-1,モノレポ,,リポジトリの構成,\n"
           "IMPL-1,Red テストの窓口,docs/guide.md#impl,impl_module,app.spec_impl\n")
GUIDE = "# ガイド\n\n## API\n\n## verify\n\n## impl\n"


def make_profile(root: Path, env: dict) -> Path:
    """タグ v1・v2 と、形の違う試料のタグを持つ profile のリポジトリ。"""
    assert_in_tmp(root)
    root.mkdir(parents=True)
    git(root, env, "init", "-q", "-b", "main")
    base = root / "spec-profile" / "org"
    base.mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text(GUIDE, encoding="utf-8")

    def commit(tag: str, profile: str = PROFILE, arch: str = ARCH, process: str = PROCESS, guide: str = GUIDE, extra: dict | None = None) -> None:
        (base / "profile.csv").write_text(profile, encoding="utf-8")
        (base / "infra.csv").write_text(INFRA, encoding="utf-8")
        (base / "architecture.csv").write_text(arch, encoding="utf-8")
        (base / "process.csv").write_text(process, encoding="utf-8")
        (root / "docs" / "guide.md").write_text(guide, encoding="utf-8")
        for rel, body in (extra or {}).items():
            (root / rel).write_text(body, encoding="utf-8")
        git(root, env, "add", "-A")
        git(root, env, "commit", "-q", "--allow-empty", "-m", tag)
        git(root, env, "tag", tag)

    commit("v1")
    commit("v2", arch=ARCH.replace("ARCH-2,権限はオブジェクトごと", "ARCH-2,読み取りは query の API"))
    commit("nolayers", profile="層,形式の版,ファイル,重ねる先\n基盤,1,infra.csv,\n")
    commit("archhead", arch=ARCH.replace("ID,要約,リンク,観点", "ID,要約,リンク,分類"))
    commit("prochead", process=PROCESS.replace("ID,要約,リンク,項目,値", "ID,要約,リンク,項目,コマンド"))
    commit("blankhead", arch="\n\n" + ARCH)
    commit("noview", arch=ARCH.replace(",API の方式\n", ",\n"))
    commit("baditem", process=PROCESS.replace("REPO-1,モノレポ,,リポジトリの構成,", "REPO-1,モノレポ,,build,"))
    commit("twoguard", process=PROCESS + "GUARD-2,もう 1 本,,歯止め,make all\n")
    commit("twoimpl", process=PROCESS + "IMPL-2,別の窓口,,impl_module,app.other\n")
    commit("emptyimpl", process=PROCESS.replace("impl_module,app.spec_impl", "impl_module,"))
    commit("newline", process=PROCESS.replace("verify,make verify", 'verify,"make\nverify"'))
    commit("broken", guide=GUIDE, arch=ARCH.replace("docs/guide.md#api", "docs/gone.md"))
    commit("archnewline", arch=ARCH.replace("ARCH-1,書き込みは command の API に分ける", 'ARCH-1,"書き込みは command の API\n## 注入"'))
    commit("backtick", process=PROCESS.replace("歯止め,make check", "歯止め,make`check"))
    commit("encoded", arch=ARCH.replace("ARCH-2,権限はオブジェクトごと,", "ARCH-2,権限はオブジェクトごと,docs/a%20b.md#手順"),
           extra={"docs/a b.md": "# 手順\n"})
    commit("u85", process=PROCESS.replace("RULE-1,本番の DB を直に触らない", "RULE-1,本番の DB を直に触らない\x85検証の関門: off"))
    commit("dotted", arch=ARCH.replace("ARCH-2,権限はオブジェクトごと,", "ARCH-2,権限はオブジェクトごと,./docs/x/..//guide.md#api"))
    commit("anchor", arch=ARCH.replace("ARCH-2,権限はオブジェクトごと,", "ARCH-2,権限はオブジェクトごと,docs/guide.md#%E6%89%8B%E9%A0%86"),
           guide=GUIDE + "\n## 手順\n")
    commit("fmt2", profile=PROFILE.replace("アーキテクチャ,1,", "アーキテクチャ,2,"))
    git(root, env, "checkout", "-q", "v1")  # 作業ツリーはどれかのタグ。読むのはタグの時点
    return root


def lay_out(plugins: Path, platform_source: str | None = None) -> Path:
    assert_in_tmp(plugins)
    plugins.mkdir(parents=True)
    root = plugins / "platform-spec"
    shutil.copytree(PLATFORM, root, ignore=shutil.ignore_patterns("__pycache__"))
    if platform_source is not None:
        (root / "scripts" / TARGET).write_text(platform_source, encoding="utf-8")
    return root


def run_case(platform: Path, work: Path, files: dict, args: list[str], tokens: dict, env: dict) -> tuple[int, str, str]:
    assert_in_tmp(work)
    project = work / "project"
    (project / "docs").mkdir(parents=True)
    for rel, body in files.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.replace("{clone}", tokens["clone"]), encoding="utf-8")
    argv = [a.format(**tokens) for a in args]
    if "--no-docs" in argv:
        argv = ["architecture"]
    else:
        argv = [argv[0], str(project / "docs"), *argv[1:]]
    elsewhere = work / "elsewhere"  # cwd は正本の外（CLAUDE.md は正本の根のものを読む）
    elsewhere.mkdir()
    proc = subprocess.run([sys.executable, "-I", str(platform / "scripts" / TARGET), *argv], capture_output=True, text=True, cwd=elsewhere, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def as_expected(name: str, result: tuple[int, str, str], tokens: dict) -> bool:
    _, _, _, code, text, absent = next(case for case in CASES if case[0] == name)
    text, absent = text.replace("{clone}", tokens["clone"]), absent.replace("{clone}", tokens["clone"])
    both = result[1] + result[2]
    return result[0] == code and text in both and not (absent and absent in result[1]) and "Traceback" not in both


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


def template_line(module, value: str, link: str) -> str:
    """本体の雛形の作り方で、1 行だけの開発の進め方の層から雛形の行を作る。"""
    layer = SimpleNamespace(rows={"VERIFY-1": {"ID": "VERIFY-1", "要約": "開発サーバを起動して画面を確かめる", "リンク": link, "項目": "verify", "値": value}})
    out = module.Layers.template(SimpleNamespace(reference=module.Layers.reference, tag_files=frozenset(), ext=SimpleNamespace(_safe_rel=None)),
                                 {"リポジトリ": "org/guide", "profile": "org", "タグ": "v3"}, layer, {})
    return next(line for line in out.splitlines() if line.startswith("- VERIFY-1:"))


def reference_mismatches(module, layers_md: str, template_md: str, skill_md: str, monorepo_md: str) -> list[str]:
    problems = []
    try:
        arch = section(layers_md, "## アーキテクチャの層の表")
        if first_cells(arch) != module.ARCH_COLUMNS:
            problems.append(f"アーキテクチャの層の列が違う（原本 {first_cells(arch)} ／ 本体 {module.ARCH_COLUMNS}）")
        if f"層の名前は `{module.ARCH}`" not in arch:
            problems.append(f"層の名前 {module.ARCH} が原本に無い")
        proc = section(layers_md, "## 開発の進め方の層の表")
        if f"層の名前は `{module.PROCESS}`" not in proc:
            problems.append(f"層の名前 {module.PROCESS} が原本に無い")
        cells = first_cells(proc)
        if cells[:len(module.PROCESS_COLUMNS)] != module.PROCESS_COLUMNS:
            problems.append(f"開発の進め方の層の列が違う（原本 {cells} ／ 本体 {module.PROCESS_COLUMNS}）")
        items = re.findall(r"^\| `([^`]+)` \| (.+?) \| (.+?) \|$", proc, flags=re.MULTILINE)
        shown = {item: (heading, once.startswith("1 行まで")) for item, heading, once in items if item not in module.PROCESS_COLUMNS}
        if shown != module.PROCESS_ITEMS:
            problems.append(f"項目の語彙・節・1 行までが違う（原本 {shown} ／ 本体 {module.PROCESS_ITEMS}）")
        ranges = dict((m.group(1), (m.group(2), m.group(3))) for m in
                      re.finditer(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$", section(layers_md, "## 形式の版の範囲"), flags=re.MULTILINE))
        if ranges != module.FORMAT_RANGES:
            problems.append(f"形式の版の範囲が違う（原本 {ranges} ／ 本体 {module.FORMAT_RANGES}）")
        placeholder = module.TEMPLATE_MARK.format(repo="<リポジトリ>", profile="<profile>", tag="<タグ>")
        if placeholder not in section(layers_md, "## 雛形"):
            problems.append(f"雛形の印 {placeholder} が layers.md の「雛形」に無い")
        if placeholder not in template_md:
            problems.append(f"雛形の印 {placeholder} が dev-loop の profile-template.md に無い")
        prefix = placeholder.split("<リポジトリ>")[0]
        if prefix not in skill_md:
            problems.append(f"雛形の印の頭 {prefix} が dev-loop の SKILL.md に無い")
        example = re.search(r"^(- VERIFY-1: .+)$", template_md, flags=re.MULTILINE)
        built = template_line(module, "make verify", "docs/dev/verify.md#手順")
        if not example or example.group(1) != built:
            problems.append(f"profile-template.md の例の行が本体の行と違う（原本 {example.group(1) if example else None} ／ 本体 {built}）")
        form = "- <ID>: <要約>（値: `<値>`）——本文: <リポジトリ>@<タグ>:<パス>#<節>"
        if form not in section(layers_md, "## 雛形"):
            problems.append("雛形の行の形が layers.md の「雛形」に無い")
        if module.IMPL_LINE.format(value="app.spec_impl") not in monorepo_md:
            problems.append("impl_module の行が spec-loop の monorepo.md の例と違う")
    except ValueError as e:  # 見出しが無い
        problems.append(f"原本の見出しが無い: {e}")
    return problems


REFERENCE_MUTATIONS = [  # (どれ, 崩す前, 崩した後)
    ("layers", "| `観点` | どの観点の規約か", "| 観点 | どの観点の規約か"),
    ("layers", "層の名前は `アーキテクチャ` で 1 行置き", "層の名前は `アーキ` で 1 行置き"),
    ("layers", "層の名前は `開発の進め方` で 1 行置き", "層の名前は `進め方` で 1 行置き"),
    ("layers", "| `値` | 雛形にそのまま載せる", "| `コマンド` | 雛形にそのまま載せる"),
    ("layers", "| `歯止め` | 歯止めを全部回す 1 本のコマンド | 1 行まで |", "| `歯止め` | 歯止めを全部回す 1 本のコマンド | 何行でも |"),
    ("layers", "| `制約` | やってはいけない制約 |", "| `禁止` | やってはいけない制約 |"),
    ("layers", "| `開発の進め方` | `1` | `2` |", "| `開発の進め方` | `1` | `3` |"),
    ("layers", "- <ID>: <要約>（値: `<値>`）——本文: <リポジトリ>@<タグ>:<パス>#<節>", "- <ID>: <要約>（値: `<値>`）——本文: <パス>#<節>"),
    ("template", "（値: `make verify`）——本文: org/guide@v3:docs/dev/verify.md#手順", "（値: `make verify`）——本文: docs/dev/verify.md#手順"),
    ("template", "<!-- platform-spec: 開発の進め方 <リポジトリ> <profile> <タグ> -->", "<!-- platform-spec: 進め方 <リポジトリ> <profile> <タグ> -->"),
    ("skill", "<!-- platform-spec: 開発の進め方 … -->", "<!-- platform-spec: … -->"),
    ("monorepo", "- 実装のモジュール名（`impl_module`）: `app.spec_impl`", "- 実装のモジュール（`impl_module`）: `app.spec_impl`"),
]


def load(path: Path):
    spec = importlib.util.spec_from_file_location("profile_layers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    source = SOURCE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix=TMP_PREFIX) as tmp_name:
        tmp = Path(tmp_name)
        env = child_env(tmp)
        clone = make_profile(tmp / "profile", env)
        spec_loop = tmp / "spec-loop-copy"
        shutil.copytree(SPEC_LOOP, spec_loop, ignore=shutil.ignore_patterns("__pycache__"))
        tokens = {"clone": str(clone), "docs": ""}

        def layout(where: Path, platform_source: str | None = None) -> Path:
            platform = lay_out(where, platform_source)
            (where / "spec-loop").symlink_to(spec_loop, target_is_directory=True)
            return platform

        platform = layout(tmp / "plugins")
        before_clone = clone_state(clone, env)
        for index, (name, files, args, _, _, _) in enumerate(CASES):
            result = run_case(platform, tmp / f"case{index}", files, args, tokens, env)
            check(f"試料が期待どおりでない: {name}", as_expected(name, result, tokens), f"exit={result[0]} {(result[1] + result[2])[-600:]}")

        # 読むだけ: clone と正本が変わらない・__pycache__ ができない
        check("clone の状態が変わった", clone_state(clone, env) == before_clone)
        work = tmp / "readonly"
        run_case(platform, work, dict(OK), ["dev-loop"], tokens, env)
        project = work / "project"
        before_tree = tree_state(project)
        for command in ("architecture", "dev-loop"):
            proc = subprocess.run([sys.executable, "-I", str(platform / "scripts" / TARGET), command, str(project / "docs")], capture_output=True, text=True,
                                  cwd=work / "elsewhere", env=env)
            check(f"読むだけの確かめの試料が 0 でない: {command}", proc.returncode == 0, proc.stdout + proc.stderr)
        check("正本のファイルが変わった", tree_state(project) == before_tree)
        caches = [str(p) for p in list(tmp.joinpath("plugins").rglob("__pycache__")) + list(spec_loop.rglob("__pycache__"))]
        check("写したプラグインに __pycache__ ができた", not caches, ", ".join(caches))

        # 原本との突き合わせ
        module = load(platform / "scripts" / TARGET)
        texts = {"layers": REF_LAYERS.read_text(encoding="utf-8"), "template": REF_TEMPLATE.read_text(encoding="utf-8"),
                 "skill": DEV_LOOP_SKILL.read_text(encoding="utf-8"), "monorepo": REF_MONOREPO.read_text(encoding="utf-8")}
        order = ("layers", "template", "skill", "monorepo")
        problems = reference_mismatches(module, *(texts[k] for k in order))
        check("本体の定数が原本と一致しない", not problems, "; ".join(problems))
        for which, before, after in REFERENCE_MUTATIONS:
            if texts[which].count(before) != 1:
                check(f"崩す箇所が 1 回でない: {before}", False, f"{texts[which].count(before)} 回")
                continue
            broken = dict(texts, **{which: texts[which].replace(before, after)})
            check(f"崩しても不一致にならない: {before}", bool(reference_mismatches(module, *(broken[k] for k in order))))

        # 変異
        guarded = guarded_lines(source)
        check("変異の数が「守ること」の行の数と違う", len(guarded) == len(MUTATIONS), f"守ること {len(guarded)} 行・変異 {len(MUTATIONS)} 件")
        killers = {killer for _, _, _, killer in MUTATIONS}
        check("変異の殺す試料が試料に無い", killers <= set(names), ", ".join(sorted(killers - set(names))))
        control = layout(tmp / "control", source)
        for index, killer in enumerate(sorted(killers)):
            files, args = next((f, a) for n, f, a, _, _, _ in CASES if n == killer)
            result = run_case(control, tmp / f"controlwork{index}", files, args, tokens, env)
            check(f"壊さない写しで殺す試料が期待どおりでない: {killer}", as_expected(killer, result, tokens), (result[1] + result[2])[-300:])
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = layout(tmp / f"mut{index}", source.replace(before, after))
            files, args = next((f, a) for n, f, a, _, _, _ in CASES if n == killer)
            result = run_case(mutated, tmp / f"mutwork{index}", files, args, tokens, env)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result, tokens), (result[1] + result[2])[-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件（守ること {len(guarded)} 行）・原本の崩し {len(REFERENCE_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
