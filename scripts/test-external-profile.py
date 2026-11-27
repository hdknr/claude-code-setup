#!/usr/bin/env python3
"""`external-profile.py`（spec-loop の外部の profile を中身を知らずに読む共通の部分。#1455）の回帰テスト。

    python3 scripts/test-external-profile.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-tlc.py` と同じ形。

**このテストは実環境を触らない。** profile のリポジトリ・案件・ほかの clone はテンポラリに本物の git リポジトリで作り、`HOME`・`GIT_CONFIG_GLOBAL` を差し替える。
環境変数 `SPEC_PROFILE_CLONE` は始める前に外す（利用者の値を読まない）。ネットワークには出ない（本体は `gh` を呼ばない）。

試料の profile のリポジトリは 2 つのタグ（`v1`・`v2`）に基盤と画面の 2 つの層を持ち、形の違う表のタグ（`bad-*`）と、タグの無いブランチ `v9` を持つ。
作業ツリーは `work` ブランチ（profile の形式の版を範囲の外にしたコミット）に置き、タグに無いファイルと、書き換えた追跡中のファイルを置く——
**本体がタグではなく作業ツリーか HEAD を読めば、観測が変わる。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測がそろったままなら失格**とする。**陽性対照**: 壊さない本体で全試料が期待どおりであること。
本体の docstring の「守る」の行数と変異の数が等しいことを、テスト自身が数えて見る。終了コードの表と定数、決まりの原本（`references/external-profile.md`）の列・鍵・環境変数も突き合わせる。

**プロパティテスト（A3）**: 形式の版の範囲の判定を、`random` で生成した版の対 2000 組に当て、テストの側で別の作り方（桁を 0 埋めの文字列にして並べる）で出した期待と比べる。
seed は実行ごとに変え、出力に出す（Hypothesis は依存に無い——計画ファイルの表）。
"""
import contextlib
import importlib.util
import io
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPT = PLUGIN / "scripts" / "external-profile.py"
REFERENCE = PLUGIN / "references" / "external-profile.md"

failures: list[str] = []

# 本体の docstring の「守る」の各行に 1 つずつ（順も同じ）。(探す文字列, 置き換え) の組
MUTATIONS = {
    "引数があっても環境変数を先に見る": [("    if clone:\n", "    if clone and not env.get(ENV_CLONE):\n")],
    "環境変数があっても CLAUDE.md を先に見る": [
        ("    if env.get(ENV_CLONE):\n", "    if env.get(ENV_CLONE) and not (Path(project) if project else Path.cwd()).joinpath(\"CLAUDE.md\").exists():\n")],
    "名指しが git のリポジトリでなくても使う": [("    if not path.is_dir() or not _is_repo(path):\n", "    if False:\n")],
    "サブディレクトリも clone とする": [("    return top.returncode == 0 and os.path.samefile(top.stdout.strip(), path)\n", "    return top.returncode == 0\n")],
    "bare を根として読まない": [('    key = "--absolute-git-dir" if bare.stdout.strip() == "true" else "--show-toplevel"\n', '    key = "--show-toplevel"\n')],
    "GIT_DIR などを子の git に渡す": [("    return {k: v for k, v in os.environ.items() if k not in drop}\n", "    return dict(os.environ)\n")],
    "置き換えを効かせる": [('["git", "--no-replace-objects", "-C", str(clone), *args]', '["git", "-C", str(clone), *args]')],
    "どこにも無ければ案件の根を使う": [("    raise Undetermined(\n        f\"{repo} の手元の clone が見つからない",
                                  "    return root.resolve(), \"無し\"\n    raise Undetermined(\n        f\"{repo} の手元の clone が見つからない")],
    "ほかのリポジトリの行も使う": [("parts[0] == repo", "True")],
    "同じリポジトリの行が 2 行でも先頭を使う": [("    if len(hits) > 1:\n", "    if False:\n")],
    "フェンスの中の行も宣言と読む": [("tlc.scan_declarations(text, (DECL_KEY,))[DECL_KEY]",
                                 "[l[len(DECL_KEY):] for l in text.splitlines() if l.startswith(DECL_KEY)]")],
    "行の ~ をホームに展開しない": [("        path = _expand(Path(hits[0]), source)", "        path = Path(hits[0])")],
    "行の ~ で始まらない値も展開する": [(' if hits[0].startswith("~") else Path(hits[0])', "")],
    "~ を展開できないと RuntimeError のまま投げる": [("    except RuntimeError as e:\n        raise Undetermined(", "    except ZeroDivisionError as e:\n        raise Undetermined(")],
    "タグが無ければブランチに落ちる": [('f"refs/tags/{tag}^{{commit}}"', 'f"{tag}^{{commit}}"')],
    "版の記法をたどる": [('    if _git(clone, "check-ref-format", f"refs/tags/{tag}").returncode != 0:\n', "    if False:\n")],
    "HEAD の中身を読む": [('f"{commit}:{path}"', 'f"HEAD:{path}"')],
    "タグを checkout する": [("    return proc.stdout.decode().strip()\n",
                           "    _git(clone, \"checkout\", \"-q\", \"--detach\", tag)\n    return proc.stdout.decode().strip()\n")],
    "上限を含む": [("    return lo <= v < hi\n", "    return lo <= v <= hi\n")],
    "足りない桁を 0 で揃えない": [("    v, lo, hi = _pad(v, n), _pad(lo, n), _pad(hi, n)\n", "")],
    "ASCII でない数字を受け付ける": [('VERSION_RE = re.compile(r"[0-9]+(?:\\.[0-9]+)*")', 'VERSION_RE = re.compile(r"\\d+(?:\\.\\d+)*")')],
    "数字の後ろの文字を見ない": [('    if not VERSION_RE.fullmatch(text or ""):\n', '    if not VERSION_RE.match(text or ""):\n')],
    "層が無いのを判定できなかったにする": [('raise LayerMissing(f"層 {layer} が', 'raise Undetermined(f"層 {layer} が')],
    "profile.csv の見出しを見ない": [("if not rows or tuple(rows[0]) != PROFILE_COLUMNS:", "if not rows:")],
    "同じ層が 2 行でも読む": [("        if layer in out:\n", "        if False:\n")],
    "層の表の先頭 3 列を見ない": [("tuple(rows[0][:3]) != LAYER_HEAD", "False")],
    "見出しの同じ名前を許す": [("        if len(set(head)) != len(head):\n", "        if False:\n")],
    "ID が空でも読む": [("            if not rid:\n", "            if False:\n")],
    "ID が重なっても読む": [("            if rid in result.rows:\n", "            if False:\n")],
    "profile の中身の欠陥を ProfileContent にしない": [("raise ProfileContent(", "raise Undetermined("), ("where, ProfileContent)", "where)"),
                                                ("stop = ProfileContent if below(row.version, low) else Undetermined", "stop = Undetermined")],
    "タグが無いのも ProfileContent にする": [('        raise Undetermined(f"{clone} にタグ {tag} が無い', '        raise ProfileContent(f"{clone} にタグ {tag} が無い')],
    "上限と同じか上の形式の版も ProfileContent にする": [("stop = ProfileContent if below(row.version, low) else Undetermined", "stop = ProfileContent")],
    "層のファイルの中身の欠陥を LayerContent にしない": [("raise LayerContent(f", "raise Undetermined(f"), ("path, LayerContent)", "path)")],
    "列の数を見ない": [("            if len(r) != len(head):\n", "            if False:\n")],
    "ファイルが当たらなくても読む": [("    if not matched:\n", "    if False:\n")],
    "ファイルが profile の外でも読む": [('rel = _safe_rel(row.file) if row.file and not row.file.startswith("/") else None', "rel = posixpath.normpath(row.file)"),
                                    ('    pattern = f"{base_dir}/{rel}"\n', '    pattern = posixpath.normpath(f"{base_dir}/{rel}")\n')],
    "後ろの列の値を整える": [("result.rows[rid] = dict(zip(head, r))", "result.rows[rid] = {k: v.strip().lower() for k, v in zip(head, r)}")],
    "先頭 3 列だけを比べる": [("cols = sorted(set(o[rid]) | set(n[rid]))", "cols = list(LAYER_HEAD)")],
    "消えた行を出さない": [('"消えた": sorted(set(o) - set(n)),', '"消えた": [],')],
    "足した行を出さない": [('"足した": sorted(set(n) - set(o)),', '"足した": [],')],
    "作業ツリーに在るファイルを在るとする": [("        if rel not in files and rel not in dirs:\n",
                                     "        if rel not in files and rel not in dirs and not (clone / rel).exists():\n")],
    "節を見ない": [("            if not anchors & cache[rel]:\n", "            if False:\n")],
    "フェンスの中の見出しから id を作る": [("                fence = None\n            continue\n        h = HEADING_RE", "                fence = None\n        h = HEADING_RE")],
    "BOM つきの .md の先頭の見出しを落とす": [('.decode("utf-8", "replace").removeprefix("\\ufeff"))', '.decode("utf-8", "replace"))')],
    "リポジトリの外を指すリンクを切れたにしない": [("        if rel is None:\n            broken.append(", "        if rel is None:\n            continue\n            broken.append(")],
    "外の URL も見る": [("if not link or SCHEME_RE.match(link):", "if not link:")],
    "百分率の符号化を戻さない": [("else unquote(raw_path)\n", "else raw_path\n"), ("anchors = {raw_anchor, unquote(raw_anchor)}", "anchors = {raw_anchor}")],
    "書いたままの名前を見ない": [("path = raw_path if raw_rel is not None and (raw_rel in files or raw_rel in dirs) else unquote(raw_path)", "path = unquote(raw_path)")],
    "diff の切れたを古いタグで見る": [("broken = check_links(clone, new_commit, new) if new else []", "broken = check_links(clone, old_commit, new) if new else []")],
    "BOM を外さない": [('text = raw.decode("utf-8").removeprefix("\\ufeff")', 'text = raw.decode("utf-8")')],
    "想定外の例外を 1 にする": [("        return EXIT_UNKNOWN\n\n\ndef _main(", "        raise\n\n\ndef _main(")],
}

PROFILE = "spec-profile/org"
GUIDE = "# ガイド\n\n## 認証\n\n## データベース\n\n## データベース\n\n```text\n# 偽の見出し\n```\n"
V1 = {
    f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,infra.csv,\n画面,1,screens/*.csv,web-spa\n",
    f"{PROFILE}/infra.csv": "\ufeffID,要約,リンク,言語,備考\n"
                            "I-1,言語,docs/guide.md#認証,Python,\n"
                            "I-2,DB,docs/guide.md#データベース-1,PostgreSQL,\" =SUM(A1)\"\n"
                            "I-3,外,https://example.com/x,,\n"
                            "I-4,無し,,,\n"
                            "I-6,外へ,../outside.md,,\n"
                            "I-7,手元だけ,docs/untracked.md,,\n"
                            "I-8,BOM,docs/bom.md#先頭,,\n"
                            "I-9,符号化,docs/%E6%97%A5%E6%9C%AC.md#%E8%AA%8D%E8%A8%BC,,\n"
                            "I-10,百分率の名前,docs/a%20b.md,,\n",
    "docs/a%20b.md": "# 名前に百分率\n",
    "docs/日本.md": "# 認証\n",
    "docs/bom.md": "\ufeff# 先頭\n",
    f"{PROFILE}/screens/a.csv": "ID,要約,リンク,種類\nS-1,一覧,/docs/guide.md,一覧\n",
    f"{PROFILE}/screens/b.csv": "ID,要約,リンク,幅,高さ\nS-2,詳細,docs/old.md,100,\"2\n00\"\n",
    "docs/guide.md": GUIDE,
    "docs/old.md": "# 古い\n",
}
V2 = dict(V1)
V2[f"{PROFILE}/infra.csv"] = ("\ufeffID,要約,リンク,言語,備考\n"
                              "I-1,言語,docs/guide.md#認証,Python,注記\n"
                              "I-3,外,https://example.com/x,,\n"
                              "I-4,無し,,,\n"
                              "I-5,偽,docs/guide.md#偽の見出し,,\n"
                              "I-6,外へ,../outside.md,,\n"
                              "I-7,手元だけ,docs/untracked.md,,\n"
                              "I-8,BOM,docs/bom.md#先頭,,\n"
                              "I-9,符号化,docs/%E6%97%A5%E6%9C%AC.md#%E8%AA%8D%E8%A8%BC,,\n"
                              "I-10,百分率の名前,docs/a%20b.md,,\n")
V2[f"{PROFILE}/screens/a.csv"] = "ID,要約,リンク,種類\nS-1,一覧,/docs/guide.md,一覧 \n"
del V2["docs/old.md"]

BAD = {
    "bad-wide-digit": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,１.2,infra.csv,\n画面,1,screens/*.csv,\n"},
    "bad-version": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1a,infra.csv,\n画面,1,screens/*.csv,\n"},
    "bad-profile-head": {f"{PROFILE}/profile.csv": "層,版,ファイル,重ねる先\n基盤,1.2,infra.csv,\n"},
    "bad-dup-layer": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,infra.csv,\n基盤,1.2,infra.csv,\n"},
    "bad-layer-head": {f"{PROFILE}/screens/a.csv": "id,要約,リンク,種類\nS-1,一覧,,一覧\n"},
    "bad-dup-id": {f"{PROFILE}/screens/b.csv": "ID,要約,リンク,幅,高さ\nS-1,重なり,,1,2\n"},
    "bad-cols": {f"{PROFILE}/screens/a.csv": "ID,要約,リンク,種類\nS-1,一覧,,一覧,余り\n"},
    "bad-dup-col": {f"{PROFILE}/screens/a.csv": "ID,要約,リンク,リンク\nS-1,一覧,docs/guide.md,docs/missing.md\n"},
    "bad-layer-utf8": {f"{PROFILE}/screens/a.csv": "ID,要約,リンク,種類\nS-1,\udcff,,x\n"},
    "bad-layer-csv": {f"{PROFILE}/screens/a.csv": "ID,要約,リンク,種類\nS-1," + "x" * 200000 + ",,x\n"},  # csv の既定の上限（131072 字）を超える欄——CSV として読めない
    "bad-profile-utf8": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,infra.csv,\udcff\n画面,1,screens/*.csv,\n"},
    "bad-empty-id": {f"{PROFILE}/screens/a.csv": "ID,要約,リンク,種類\n,空,,x\n"},
    "bad-outside-file": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,../shared.csv,\n画面,1,screens/*.csv,\n",
                         "spec-profile/shared.csv": "ID,要約,リンク\nZ-1,外,\n"},
    "bad-missing-file": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,missing.csv,\n"},
    # 形式の版の範囲（1 以上 2 未満）の外（#1597）——下限より下は profile の欠陥、上限と同じは使う側を上げれば読める
    # profile.csv の中身の欠陥（#1597 の 1 パス目 CR1-3）——列の数・空の層・CSV として読めない
    "bad-profile-cols": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,infra.csv\n画面,1,screens/*.csv,\n"},
    "bad-profile-empty-layer": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,infra.csv,\n,1,screens/*.csv,\n"},
    "bad-profile-csv": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,1.2,infra.csv," + "x" * 200000 + "\n画面,1,screens/*.csv,\n"},
    "bad-version-low": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,0.9,infra.csv,\n画面,1,screens/*.csv,\n"},
    "bad-version-high": {f"{PROFILE}/profile.csv": "層,形式の版,ファイル,重ねる先\n基盤,2,infra.csv,\n画面,1,screens/*.csv,\n"},
}


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


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr}")
    return proc.stdout


def write_tree(root: Path, files: dict) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", errors="surrogateescape", newline="")  # 試料の \udcff は UTF-8 でないバイト（#1589）


def commit_tree(root: Path, files: dict, msg: str) -> None:
    for p in list(root.iterdir()):
        if p.name != ".git":
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    write_tree(root, files)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", msg)


def init_repo(root: Path) -> None:
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")


def build_template(base: Path) -> Path:
    """試料を 1 度だけ作る。scenario は写しを使う。"""
    t = base / "template"
    prof = t / "profile"
    init_repo(prof)
    commit_tree(prof, V1, "v1")
    git(prof, "tag", "v1")
    commit_tree(prof, V2, "v2")
    git(prof, "tag", "-a", "v2", "-m", "v2")  # 注釈つきのタグも読む
    for tag, change in BAD.items():
        git(prof, "checkout", "-q", "-b", f"b-{tag}", "v1")
        commit_tree(prof, {**V1, **change}, tag)
        git(prof, "tag", tag)
    git(prof, "branch", "v9", "v1")  # タグの無いブランチ
    git(prof, "checkout", "-q", "-b", "work", "v2")
    work = dict(V2)
    work[f"{PROFILE}/profile.csv"] = "層,形式の版,ファイル,重ねる先\n基盤,9,infra.csv,\n画面,9,screens/*.csv,\n"
    commit_tree(prof, work, "work")
    subprocess.run(["git", "clone", "-q", "--bare", str(prof), str(t / "bare.git")], check=True, capture_output=True)
    # clone の置き換え: v1 の profile.csv の blob を、形式の版 9 の blob に差し替える（タグの中身は版 1.2 のまま）
    old = git(prof, "rev-parse", f"v1:{PROFILE}/profile.csv").strip()
    new = subprocess.run(["git", "-C", str(prof), "hash-object", "-w", "--stdin"], input="層,形式の版,ファイル,重ねる先\n基盤,9,infra.csv,\n画面,9,screens/*.csv,\n",
                         capture_output=True, text=True, check=True).stdout.strip()
    git(prof, "replace", old, new)
    for name in ("envclone", "declclone"):
        init_repo(t / name)
        commit_tree(t / name, {"README.md": name}, name)
    (t / "plain").mkdir()
    (t / "project").mkdir()
    return t


def state(root: Path):
    return (subprocess.run(["git", "-C", str(root), "symbolic-ref", "-q", "HEAD"], capture_output=True, text=True).stdout,
            git(root, "rev-parse", "HEAD"), git(root, "status", "--porcelain", "--untracked-files=all"), git(root, "for-each-ref"))


def run(mod, argv, tmp: Path):
    """(終了コード, 標準出力)。テンポラリのパスは出力から伏せる。"""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            rc = mod.main(argv)
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            return ("例外", type(exc).__name__)
    return rc, out.getvalue().replace(str(tmp), "<tmp>")


def expected_in_range(v: str, lo: str, hi: str) -> bool:
    """本体を使わない期待: 4 桁に 0 で揃え、各桁を 6 桁の 0 埋めの文字列にして文字列で並べる。"""
    def key(s):
        parts = s.split(".") + ["0"] * (6 - len(s.split(".")))
        return "".join(p.rjust(6, "0") for p in parts)
    return key(lo) <= key(v) < key(hi)


def gen_version(rng: random.Random) -> str:
    parts = [str(rng.randint(0, 12)) for _ in range(rng.randint(1, 4))]
    if rng.random() < 0.3:
        parts.append("0")  # 末尾の .0 の有無を混ぜる
    return ".".join(parts)


def property_range_A3(mod, seed: int, n: int = 2000) -> list:
    rng = random.Random(seed)
    bad = []
    for _ in range(n):
        v, lo, hi = gen_version(rng), gen_version(rng), gen_version(rng)
        try:
            got = mod.in_range(v, lo, hi)
        except Exception as exc:
            got = type(exc).__name__
        if got != expected_in_range(v, lo, hi):
            bad.append((v, lo, hi, got))
    return bad[:3] + [len(bad)]


def scenario(mod, base: Path, tag: str, template: Path, seed: int) -> dict:
    """1 つの本体に全試料を当て、観測を辞書で返す。**観測にはテンポラリのパスを入れない。**"""
    work = base / tag
    assert_not_real_repo(work.parent)
    shutil.copytree(template, work, symlinks=True)
    prof, project = work / "profile", work / "project"
    md = project / "CLAUDE.md"
    env_key = mod.ENV_CLONE if hasattr(mod, "ENV_CLONE") else "SPEC_PROFILE_CLONE"
    os.environ.pop(env_key, None)
    o = {}
    R = "org/guide"

    def find(*extra, decl=None, env=None):
        md.unlink(missing_ok=True)
        if decl is not None:
            md.write_text(decl, encoding="utf-8")
        os.environ.pop(env_key, None)
        if env:
            os.environ[env_key] = env
        try:
            return run(mod, ["find", "--repo", R, "--project", str(project), *extra], base)
        finally:
            os.environ.pop(env_key, None)

    line = f"外部の profile の clone: {R} {work / 'declclone'}\n"
    o["引数・環境変数・行"] = find("--clone", str(prof), decl=line, env=str(work / "envclone"))
    o["環境変数・行"] = find(decl=line, env=str(work / "envclone"))
    o["行だけ"] = find(decl="# 案件\n" + line)
    o["行（相対パス）"] = find(decl=f"外部の profile の clone： {R} ../declclone\n")
    o["引数が git でない（環境変数は在る）"] = find("--clone", str(work / "plain"), env=str(work / "envclone"))
    o["行が git でない"] = find(decl=f"外部の profile の clone: {R} {work / 'plain'}\n")
    o["どこにも無い"] = find()
    o["環境変数が git でない（行は在る）"] = find(decl=line, env=str(work / "plain"))
    o["引数がリポジトリの中のサブディレクトリ"] = find("--clone", str(prof / "docs"))
    o["引数の大文字・小文字が実体と違う"] = find("--clone", str(work / "PROFILE")) if (work / "PROFILE").exists() else "大文字・小文字を区別するファイルシステム"
    o["bare の clone"] = find("--clone", str(work / "bare.git"))
    o["bare の中のサブディレクトリ"] = find("--clone", str(work / "bare.git" / "refs"))
    o["ほかのリポジトリの行だけ"] = find(decl=f"外部の profile の clone: other/repo {work / 'declclone'}\n")
    o["同じリポジトリの行が 2 行"] = find(decl=line + f"外部の profile の clone: {R} {work / 'envclone'}\n")
    o["フェンスの中の行だけ"] = find(decl="```text\n" + line + "```\n")
    # `./~declclone`（#1471 の 2 パス目 CR2-1）: 案件の根の下の `~declclone` で、利用者のホームと読まない
    (project / "~declclone").symlink_to(work / "declclone")
    o["行（./~ は案件の根の下）"] = find(decl=f"外部の profile の clone: {R} ./~declclone\n")
    # 行の `~`（#1471）: HOME を試料の置き場所に向け、`~/declclone` が引数・環境変数と同じくホームに展開されるか（`~<名前>` は利用者のホームを読むので試さない）
    saved_home = os.environ.get("HOME")
    os.environ["HOME"] = str(work)
    try:
        o["行（~/）"] = find(decl=f"外部の profile の clone: {R} ~/declclone\n")
        o["引数（~/）"] = find("--clone", "~/declclone")
        o["環境変数（~/）"] = find(env="~/declclone")
        o["行（~/ が git でない）"] = find(decl=f"外部の profile の clone: {R} ~/plain\n")
        # 無い利用者の名前（`~<名前>`）は passwd を引くだけで、利用者の実ホームを読まない
        o["行（~<無い名前>/）"] = find(decl=f"外部の profile の clone: {R} ~nosuchuser-1471zz/prof\n")
        o["引数（~<無い名前>/）"] = find("--clone", "~nosuchuser-1471zz/prof")
        md.write_text(f"外部の profile の clone: {R} ~nosuchuser-1471zz/prof\n", encoding="utf-8")
        try:
            mod.find_clone(R, project=str(project), env={})
            o["find_clone（~<無い名前>/）"] = "例外なし"
        except Exception as exc:
            o["find_clone（~<無い名前>/）"] = type(exc).__name__
    finally:
        if saved_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = saved_home

    def ck(tag_, *layers):
        return run(mod, ["check", "--repo", R, "--clone", str(prof), "--profile", "org", "--tag", tag_,
                         *sum((["--layer", x] for x in layers), [])], base)

    def df(old, new, *layers):
        return run(mod, ["diff", "--repo", R, "--clone", str(prof), "--profile", "org", "--old", old, "--new", new,
                         *sum((["--layer", x] for x in layers), [])], base)

    # 作業ツリー: タグに無いファイル（I-7 のリンク先）を置く。清い状態で checkout しないことを見る
    write_tree(prof, {"docs/untracked.md": "# 手元だけ\n"})
    before = state(prof)
    o["check v1（基盤）"] = ck("v1", "基盤=1,2")
    o["check v1 の前後で clone が変わらない"] = state(prof) == before
    # 追跡中のファイルを書き換える（作業ツリーの中身はタグと違う）
    write_tree(prof, {f"{PROFILE}/infra.csv": "ID,要約,リンク\nX-1,書き換え,,\n"})
    o["check v1（基盤・作業ツリーを書き換えた）"] = ck("v1", "基盤=1,2")
    o["check v2（画面）"] = ck("v2", "画面=1,2")
    o["check v1（画面・範囲 1.0,2）"] = ck("v1", "画面=1.0,2")
    o["check v1（基盤・下限より小さい）"] = ck("v1", "基盤=1.3,2")
    o["check v1（基盤・上限ちょうど）"] = ck("v1", "基盤=1,1.2")
    o["check タグが無い（ブランチ v9 は在る）"] = ck("v9", "基盤=1,2")
    o["check 版の記法 v2~1"] = ck("v2~1", "基盤=1,2")
    os.environ["GIT_DIR"] = str(work / "envclone" / ".git")
    try:
        o["check v1（基盤・GIT_DIR がほかを指す）"] = ck("v1", "基盤=1,2")
    finally:
        os.environ.pop("GIT_DIR", None)
    os.environ["GIT_OBJECT_DIRECTORY"] = str(work / "envclone" / ".git" / "objects")
    try:
        o["check v1（基盤・GIT_OBJECT_DIRECTORY がほかを指す）"] = ck("v1", "基盤=1,2")
    finally:
        os.environ.pop("GIT_OBJECT_DIRECTORY", None)
    o["check bare v1（基盤）"] = run(mod, ["check", "--repo", R, "--clone", str(work / "bare.git"), "--profile", "org", "--tag", "v1", "--layer", "基盤=1,2"], base)
    saved_path = os.environ.get("PATH", "")
    os.environ["PATH"] = str(work / "plain")
    try:
        o["git が無い"] = run(mod, ["find", "--repo", R, "--clone", str(prof)], base)[0]
    finally:
        os.environ["PATH"] = saved_path
    o["check 層が無い"] = ck("v1", "運用=1,2")
    o["check 層が無い・切れた層"] = ck("v1", "運用=1,2", "基盤=1,2")
    for t in BAD:
        o[f"check {t}"] = ck(t, "基盤=1,2", "画面=1,2")
    # 読み込む口の例外の種類（#1589）——層のファイルの中身の欠陥だけが LayerContent（Undetermined の下位）
    for t in BAD:
        kinds = []
        for layer in ("基盤", "画面"):
            try:
                mod.read_layer(prof, mod.resolve_tag(prof, t), "org", layer, "1", "2")
                kinds.append("読めた")
            except Exception as exc:
                kinds.append(type(exc).__name__ + ("（Undetermined の下位）" if isinstance(exc, getattr(mod, "Undetermined", ())) else ""))
        o[f"read_layer {t}"] = tuple(kinds)
    # 名指しを直せば進む余地がある不在は素の Undetermined（#1597 の 1 パス目 CR1-2）——タグが無い・profile.csv がその時点に無い・profile の名前の形
    for label, call in (("タグが無い", lambda: mod.resolve_tag(prof, "nope")),
                        ("profile.csv がその時点に無い", lambda: mod.read_profile(prof, mod.resolve_tag(prof, "v1"), "other")),
                        ("profile の名前の形", lambda: mod.read_profile(prof, mod.resolve_tag(prof, "v1"), "a/b"))):
        try:
            call()
            o[f"不在 {label}"] = "読めた"
        except Exception as exc:
            o[f"不在 {label}"] = type(exc).__name__
    o["LayerContent は ProfileContent の下位"] = issubclass(getattr(mod, "LayerContent", object), getattr(mod, "ProfileContent", ()) or ZeroDivisionError)
    o["diff v1 v2"] = df("v1", "v2", "基盤=1,2", "画面=1,2")
    o["diff v1 v1"] = df("v1", "v1", "画面=1,2")
    o["diff 層が無い"] = df("v1", "v2", "運用=1,2")
    o["diff タグが無い"] = df("v1", "nope", "基盤=1,2")
    o["引数の --layer が違う"] = run(mod, ["check", "--repo", R, "--clone", str(prof), "--profile", "org", "--tag", "v1", "--layer", "基盤"], base)[0]
    o["引数なし"] = run(mod, [], base)[0]
    # 読み込む関数（使う側の口）——後ろの列の値をそのまま持つ
    try:
        commit = mod.resolve_tag(prof, "v1")
        lay = mod.read_layer(prof, commit, "org", "基盤", "1", "2")
        o["read_layer の行"] = {k: dict(v) for k, v in lay.rows.items()}
        scr = mod.read_layer(prof, commit, "org", "画面", "1", "2")
        o["read_layer の画面のファイル"] = [p.replace(str(prof), "") for p in scr.files]
        o["read_layer の画面の行"] = {k: dict(v) for k, v in scr.rows.items()}
    except Exception as exc:
        o["read_layer"] = type(exc).__name__
    o["プロパティ A3"] = property_range_A3(mod, seed)
    o["clone の参照が変わらない（最後）"] = git(prof, "for-each-ref") == before[3] and \
        subprocess.run(["git", "-C", str(prof), "symbolic-ref", "-q", "HEAD"], capture_output=True, text=True).stdout == before[0]
    return o


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test-external-profile-")).resolve()
    saved_env = dict(os.environ)
    cwd = os.getcwd()
    seed = random.SystemRandom().randrange(2 ** 32)
    try:
        home = tmp / "home"
        home.mkdir()
        os.environ.update({"HOME": str(home), "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"), "GIT_CONFIG_NOSYSTEM": "1",
                           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"})
        os.environ.pop("SPEC_PROFILE_CLONE", None)
        os.chdir(tmp)
        template = build_template(tmp)
        mod = load_module(SCRIPT, "extprof")
        print(f"プロパティテストの seed: {seed}")
        print("正しい本体")
        o = scenario(mod, tmp, "correct", template, seed)
        src = lambda key: o[key][1].splitlines()[0] if isinstance(o[key][1], str) and o[key][1] else ""
        check("引数・環境変数・行が全部あれば引数（A1）", o["引数・環境変数・行"][0] == 0 and "出所: 引数 --clone" in src("引数・環境変数・行")
              and "<tmp>/correct/profile" in src("引数・環境変数・行"))
        check("環境変数と行なら環境変数（A1）", o["環境変数・行"][0] == 0 and "envclone（出所: 環境変数 SPEC_PROFILE_CLONE）" in src("環境変数・行"))
        check("行だけなら行（A1）", o["行だけ"][0] == 0 and "declclone（出所: CLAUDE.md の" in src("行だけ"))
        check("行の相対パスは案件の根から・全角のコロンも読む", o["行（相対パス）"][0] == 0 and "<tmp>/correct/declclone（" in src("行（相対パス）"))
        check("引数が git のリポジトリでなければ、環境変数に落ちず 4（A1）", o["引数が git でない（環境変数は在る）"][0] == 4
              and "次の探し方には進まない" in o["引数が git でない（環境変数は在る）"][1])
        check("行が git のリポジトリでなければ 4", o["行が git でない"][0] == 4)
        check("環境変数が git のリポジトリでなければ、行に落ちず 4（A1）", o["環境変数が git でない（行は在る）"][0] == 4)
        check("リポジトリの中のサブディレクトリは clone にしない: 4（A1）", o["引数がリポジトリの中のサブディレクトリ"][0] == 4)
        k = o["引数の大文字・小文字が実体と違う"]
        check("パスの大文字・小文字が実体と違っても同じ根なら 0（区別するファイルシステムでは確かめない）", isinstance(k, str) or k[0] == 0)
        check("bare の clone は根として読む: 0（A1）", o["bare の clone"][0] == 0)
        check("bare の中のサブディレクトリは 4（A1）", o["bare の中のサブディレクトリ"][0] == 4)
        check("どこにも無ければ 4 で、gh では取りに行かないと言う（A1・A7）", o["どこにも無い"][0] == 4 and "gh では取りに行かない" in o["どこにも無い"][1])
        check("ほかのリポジトリの行だけなら 4", o["ほかのリポジトリの行だけ"][0] == 4)
        check("同じリポジトリの行が 2 行なら 4", o["同じリポジトリの行が 2 行"][0] == 4)
        check("フェンスの中の行だけなら 4", o["フェンスの中の行だけ"][0] == 4)
        check("行の ~/ はホームに展開する（#1471）", o["行（~/）"][0] == 0 and "<tmp>/correct/declclone（出所: CLAUDE.md の" in src("行（~/）"))
        check("行の ~/ は引数・環境変数と同じ clone を指す（#1471）",
              o["引数（~/）"][0] == 0 and o["環境変数（~/）"][0] == 0
              and all("<tmp>/correct/declclone（" in src(k) for k in ("引数（~/）", "環境変数（~/）")))
        check("行の ./~… は展開せず案件の根の下を読む（#1471 CR2-1）", o["行（./~ は案件の根の下）"][0] == 0
              and "<tmp>/correct/declclone（出所: CLAUDE.md の" in src("行（./~ は案件の根の下）"))
        check("行の ~<無い名前>/ は出所とパスを名指して 4（#1471）", o["行（~<無い名前>/）"][0] == 4
              and "CLAUDE.md の `外部の profile の clone:` の行 のパス ~nosuchuser-1471zz/prof の `~` をホームに展開できない" in o["行（~<無い名前>/）"][1])
        check("引数の ~<無い名前>/ も出所を名指して 4（#1471）", o["引数（~<無い名前>/）"][0] == 4
              and "引数 --clone のパス ~nosuchuser-1471zz/prof の `~` をホームに展開できない" in o["引数（~<無い名前>/）"][1])
        check("find_clone を直に呼ぶと ~<無い名前>/ は Undetermined（RuntimeError ではない。#1471）", o["find_clone（~<無い名前>/）"] == "Undetermined")
        check("行の ~/ が git でなければ、展開した先を名指して 4（#1471）",
              o["行（~/ が git でない）"][0] == 4 and "<tmp>/correct/plain は git" in o["行（~/ が git でない）"][1]
              and "project/~" not in o["行（~/ が git でない）"][1])

        c1 = o["check v1（基盤）"]
        check("check v1 の基盤: 切れたリンクがあって 1（A4）", c1[0] == 1)
        check("在る節（#認証）と重なった見出しの -1（#データベース-1）は切れない（A4）", "I-1 " not in c1[1] and "I-2 " not in c1[1])
        check("BOM つきの .md の先頭の見出しへのリンクは切れない（A4）", "I-8 " not in c1[1])
        check("百分率で符号化したパスと節は戻して照らす（I-9 は切れない）（A4）", "I-9 " not in c1[1])
        check("% を含む名前のファイルを書いたままの名前で指したリンクは切れない（I-10）（A4）", "I-10 " not in c1[1])
        check("外の URL と空のリンクは見ない（A4）", "I-3 " not in c1[1] and "I-4 " not in c1[1])
        check("リポジトリの外を指すリンクは切れた（A4）", "切れた: I-6 ../outside.md（リポジトリの外を指す）" in c1[1])
        check("作業ツリーにだけ在るファイルへのリンクは切れた（A2・A4）", "切れた: I-7 docs/untracked.md（ファイルがその時点に無い）" in c1[1])
        check("BOM つきの CSV を読む・9 行（A8 の陽性対照）", "形式の版 1.2・9 行" in c1[1])
        check("check の前後で clone の HEAD・作業ツリー・参照が変わらない（A2）", o["check v1 の前後で clone が変わらない"] is True)
        check("作業ツリーの中身がタグと違っても、別のブランチに居ても、タグの中身を読む（A2）",
              o["check v1（基盤・作業ツリーを書き換えた）"] == c1)
        check("最後まで clone の参照と HEAD が変わらない（A2）", o["clone の参照が変わらない（最後）"] is True)
        c2 = o["check v2（画面）"]
        check("v2 の画面: タグの時点で消えたファイルへのリンクは切れた（A4）", c2[0] == 1 and "切れた: S-2 docs/old.md" in c2[1])
        check("先頭の / のリンクは根から読む（S-1 は切れない）", "S-1 " not in c2[1])
        check("足りない桁は 0（1 は 1.0 以上 2 未満）（A3）", o["check v1（画面・範囲 1.0,2）"][0] == 0 and "形式の版 1・2 行" in o["check v1（画面・範囲 1.0,2）"][1])
        check("下限より小さい形式の版は 4（A3・A7）", o["check v1（基盤・下限より小さい）"][0] == 4)
        check("上限ちょうどの形式の版は 4（A3）", o["check v1（基盤・上限ちょうど）"][0] == 4)
        check("タグが無ければ、同じ名前のブランチがあっても 4（A7）", o["check タグが無い（ブランチ v9 は在る）"][0] == 4)
        check("タグの名前の版の記法（v2~1）はたどらず 4（A7）", o["check 版の記法 v2~1"][0] == 4)
        check("GIT_DIR がほかのリポジトリを指していても、名指しの clone を読む（A1・A2）", o["check v1（基盤・GIT_DIR がほかを指す）"] == c1)
        check("GIT_OBJECT_DIRECTORY がほかを指していても、名指しの clone を読む（A2）", o["check v1（基盤・GIT_OBJECT_DIRECTORY がほかを指す）"] == c1)
        check("clone の置き換え（refs/replace）を効かせず、タグの中身を読む（A2）", "形式の版 1.2" in c1[1])
        check("bare の clone でタグを読む: 1（切れたリンク）", o["check bare v1（基盤）"][0] == 1 and "形式の版 1.2・9 行" in o["check bare v1（基盤）"][1])
        check("git が無ければ 4（想定外の例外を 1 にしない）（A7）", o["git が無い"] == 4)
        check("求めた層が無ければ 3（無い）（A7）", o["check 層が無い"][0] == 3 and "無い:" in o["check 層が無い"][1])
        check("無い層と切れた層を一緒に求めると 1（1 が 3 より強い）", o["check 層が無い・切れた層"][0] == 1)
        check("読めない形式の版（1a）は 4（A3）", o["check bad-version"][0] == 4 and "[基盤] 判定できなかった" in o["check bad-version"][1])
        for t in ("bad-wide-digit", "bad-profile-head", "bad-dup-layer", "bad-layer-head", "bad-dup-col", "bad-empty-id", "bad-dup-id", "bad-cols", "bad-missing-file", "bad-outside-file",
                  "bad-layer-utf8", "bad-layer-csv", "bad-profile-utf8", "bad-version-low", "bad-version-high", "bad-profile-cols", "bad-profile-empty-layer", "bad-profile-csv"):
            check(f"表の形が違う {t} は 4（A8）", o[f"check {t}"][0] == 4)
        content = "LayerContent（Undetermined の下位）"
        for t in ("bad-layer-head", "bad-dup-col", "bad-empty-id", "bad-dup-id", "bad-cols", "bad-layer-utf8", "bad-layer-csv"):
            check(f"層のファイルの中身の欠陥 {t} は LayerContent（Undetermined の下位）を投げる（#1589）: {o[f'read_layer {t}']}", content in o[f"read_layer {t}"])
        profile_content = "ProfileContent（Undetermined の下位）"
        for t in ("bad-wide-digit", "bad-version", "bad-profile-head", "bad-dup-layer", "bad-missing-file", "bad-outside-file", "bad-profile-utf8", "bad-version-low",
                  "bad-profile-cols", "bad-profile-empty-layer", "bad-profile-csv"):
            check(f"profile.csv の中身・形式の版の読めない形か下限より下・ファイルの当たり先の {t} は ProfileContent で、LayerContent にしない（#1589・#1597）: {o[f'read_layer {t}']}",
                  content not in o[f"read_layer {t}"] and profile_content in o[f"read_layer {t}"])
        check(f"形式の版が上限と同じ bad-version-high は素の Undetermined（ProfileContent にしない。#1597）: {o['read_layer bad-version-high']}",
              "Undetermined（Undetermined の下位）" in o["read_layer bad-version-high"] and profile_content not in o["read_layer bad-version-high"])
        check("LayerContent は ProfileContent の下位（#1597）", o["LayerContent は ProfileContent の下位"] is True)
        for label in ("タグが無い", "profile.csv がその時点に無い", "profile の名前の形"):
            check(f"{label} は素の Undetermined（ProfileContent にしない。#1597）: {o[f'不在 {label}']}", o[f"不在 {label}"] == "Undetermined")
        check("画面の層の後ろの列が違っても、層ごとに読める・改行入りの値も読む（A6）",
              o.get("read_layer の画面の行", {}).get("S-2", {}).get("高さ") == "2\n00"
              and o.get("read_layer の画面のファイル") == [f"{PROFILE}/screens/a.csv", f"{PROFILE}/screens/b.csv"]
              and set(o["read_layer の画面の行"]["S-1"]) == {"ID", "要約", "リンク", "種類"})
        check("後ろの列の値（数式・前の空白・空）をそのまま持つ（A6）", o.get("read_layer の行", {}).get("I-2", {}).get("備考") == " =SUM(A1)"
              and o["read_layer の行"]["I-4"]["言語"] == "")
        d = o["diff v1 v2"]
        check("diff v1 v2: 差分があって 1（A5）", d[0] == 1)
        check("後ろの列だけが違う行も変わった（I-1 の備考・S-1 の種類の末尾の空白）（A5・A6）",
              "変わった: I-1（備考）" in d[1] and "変わった: S-1（種類）" in d[1])
        check("消えた行（I-2）・足した行（I-5）を出す（A5）", "消えた: I-2" in d[1] and "足した: I-5" in d[1])
        check("切れたは新しいタグで見る——S-2（v2 で old.md が消えた）とフェンスの中の見出し #偽の見出し（I-5）（A4・A5）",
              "切れた: S-2 docs/old.md" in d[1] and "切れた: I-5 docs/guide.md#偽の見出し（節 #偽の見出し" in d[1])
        check("diff v1 v1 の画面: 差分なしで 0", o["diff v1 v1"][0] == 0 and "変わった 0・消えた 0・足した 0・切れた 0" in o["diff v1 v1"][1])
        check("diff の層が両方に無ければ 3（A7）", o["diff 層が無い"][0] == 3)
        check("diff のタグが無ければ 4（A7）", o["diff タグが無い"][0] == 4)
        check("--layer の形が違えば 2", o["引数の --layer が違う"] == 2)
        check("引数なしは 2", o["引数なし"] == 2)
        check(f"プロパティ A3: 生成した 2000 組で範囲の判定が別の作り方の期待と一致（seed {seed}）", o["プロパティ A3"] == [0])

        print("\n終了コードの表・決まりの原本と、本体の定数が一致する（A10）")
        source = SCRIPT.read_text(encoding="utf-8")
        exits = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", exits, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_FOUND, mod.EXIT_USAGE, mod.EXIT_ABSENT, mod.EXIT_UNKNOWN}
        check(f"終了コードの表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)
        ref = REFERENCE.read_text(encoding="utf-8")
        pcols = re.findall(r"^\| `([^`]+)` \|", ref.split("## `profile.csv`")[1].split("## ")[0], re.M)
        check(f"原本の profile.csv の列 {pcols} と定数", tuple(pcols) == mod.PROFILE_COLUMNS)
        lcols = re.findall(r"^\| `([^`]+)` \|", ref.split("## 層の表")[1].split("### ")[0], re.M)
        check(f"原本の層の表の先頭の列 {lcols} と定数", tuple(lcols) == mod.LAYER_HEAD)
        check("原本が環境変数の名前を挙げる", f"環境変数 `{mod.ENV_CLONE}`" in ref)
        check("原本が宣言の行を行頭で書く", re.search(rf"^\s*{re.escape(mod.DECL_KEY)} <持ち主>/<名前> ", ref, re.M) is not None)
        check("原本が置き場所の profile.csv を挙げる", f"{mod.PROFILE_ROOT}/<名前>/" in ref and mod.PROFILE_FILE in ref)
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        check("README の中身の表が本体と原本を挙げる", "| `scripts/external-profile.py` |" in readme and "| `references/external-profile.md` |" in readme)

        print("\n変異テスト（壊したのに観測がそろったままなら失格）")
        # 出力の中のテンポラリのパスは、試料の置き場所（<tmp>/correct と、変異の <tmp>/s）で違う——置き場所を揃えて比べる
        norm = lambda obs: repr(obs).replace("<tmp>/correct/", "<w>/").replace("<tmp>/s/", "<w>/")
        # 陰性対照: 壊さない写しは「殺せない」——比べ方が何でも違うと言うなら、変異を殺せたことにならない
        ident = tmp / "identity"
        ident.mkdir()
        shutil.copy(SCRIPT, ident / "external-profile.py")
        shutil.copy(SCRIPT.parent / "check-tlc.py", ident / "check-tlc.py")
        same = scenario(load_module(ident / "external-profile.py", "ident"), ident, "s", template, seed)
        check("陰性対照: 壊さない写しの観測は正しい本体と同じ（比べ方が判別している）", norm(same) == norm(o))
        for i, (name, pairs) in enumerate(MUTATIONS.items()):
            mutated = source
            absent = [n for n, _ in pairs if n not in mutated]
            if absent:
                check(f"変異を当てる先がある: {name}: {absent}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d_ = tmp / f"mut-{i}"
            d_.mkdir()
            broken = d_ / "external-profile.py"
            broken.write_text(mutated, encoding="utf-8")
            shutil.copy(SCRIPT.parent / "check-tlc.py", d_ / "check-tlc.py")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
            try:
                mutant = load_module(broken, "mut")
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, d_, "s", template, seed)
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            # 出力の中のテンポラリのパスは、試料の置き場所（correct と s）で違う——置き場所を揃えて比べる
            check(f"変異を殺せる: {name}", norm(got) != norm(o))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [ln for ln in body.splitlines() if ln.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(saved_env)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件（seed {seed}）")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("外部の profile を読む共通の部分のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
