#!/usr/bin/env python3
"""`build-mock.py`（screen-spec の UI モックの生成器。#1095）の回帰テスト。

    python3 scripts/test-build-mock.py              # CI で回す部分（文字列の突き合わせ・印・止まること）
    python3 scripts/test-build-mock.py --browser    # 手元で回す部分（ヘッドレスの Chrome で開いて踏む）

**本体はプラグインの中にある**（`plugins/screen-spec/scripts/`）。`check-screens.py` と spec-loop のスクリプトを読み込むので、
一時ディレクトリに `plugins/screen-spec/`（本体）と `plugins/spec-loop/`（本物の spec-loop の `.claude-plugin/` と `scripts/` の写し）を並べて走らせる。
正本は一時ディレクトリの git のリポジトリ（`docs/v1/`・`docs/v2/` と、版の外の `screen-spec/renderers/`）に置く。

**CI で回す部分**（引数なし）が見るもの:

1. **#1095 の受入基準のうち、文字列と印で決まるもの**——生成したモックから埋め込んだ表（JSON）を取り出して表と突き合わせる（画面名・ボタン名）・
   外を指す読み込みが無い・版と表の出どころと生成器の版と描き方のファイルのコミットが出る・描き方のファイルを版の中に置くと止まる・
   `D-` の番号も許可の外の列（パス）も出ない（パスの列は、本体の列を足した写しで作る——表の形にまだパスの列が無いので）。
2. **ほかの決まり**——`--upto`・止まる形（表が揃わない・見出し行・重ね合わせ・引数・spec-loop の版）・書くのは出力の 1 ファイルだけ・同じ入力から同じバイト・
   描き方のファイルの埋め込み（`</script` を閉じない・表に無い画面は警告）・散文の節へのリンク。
3. **本体の定数が `plugins/screen-spec/references/mock.md` の原本と一致する**（崩すと落ちることも見る）。

**手元で回す部分**（`--browser`）は、ヘッドレスの Chrome（`SCREEN_SPEC_CHROME`、無ければ macOS の既定の場所か `PATH` の `google-chrome`・`chromium`）と
`node`（組み込みの WebSocket で DevTools のプロトコルを話す。依存は足さない）で、生成したモックを `file://` で開き、ネットワークを切って次を踏む:
遷移の表から作った手順（遷移元を `#screen=` で開き、きっかけを押し、条件で分かれるなら選び、行き先と履歴を見る）・全画面を `#screen=` で開く
（`dialog` は重ね、`tab` は親の中で選ばれる）・描かれた画面名とボタン名が表の中にある・説明の欄に `D-` が無い・遷移の無いボタンと表に無い遷移と表に無い画面の文言・
カーソルを当てたときの遷移の説明・描き方の差し替え・`file:` のほかの要求が 0 件。道具が無ければ 3 で終わる（回せなかったことを緑にしない）。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME` を一時ディレクトリにし、`CLAUDE_CONFIG_DIR`・`SCREEN_SPEC_SPEC_LOOP` を外す。
Chrome も一時のプロファイルで起こす。

**変異テストを含む**（CI で回す部分）。本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "screen-spec"
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
TARGET = "build-mock.py"
REFS = PLUGIN / "references"

DATA = "requirements/screens/data/"
S_HEAD = "画面ID,画面名,種別,親画面,主たる利用者,ステータス,参考資料,目的と背景,できること,機能,帳票,仕様書,根拠\n"
I_HEAD = "番号,画面ID,まとまり,並び順,項目名,種類,中身,例,必須,入力チェック,エラーメッセージ,並び替え,絞り込み,根拠\n"
T_HEAD = "番号,遷移元,きっかけ,操作,条件,遷移先,結果,根拠\n"
QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"

V1_SCREENS = S_HEAD + (
    "S-001,受注一覧,top,,担当者,記入中,,受注を探す,一覧と絞り込み,F-001,,order-list.md,Q-R-001\n"
    "S-002,受注登録,form,,担当者,記入中,,受注を入れる,入力,F-002,,order-new.md,F-002\n"
    "S-003,受注の詳細,detail,,担当者,記入中,,詳しく見る,詳細を見る,F-001,,order-detail.md,F-001、D-S-001\n"
    "S-004,登録の確認,dialog,S-002,担当者,記入中,,確かめる,内容を確かめる,F-002,,order-confirm.md,F-002\n"
    "S-005,明細,tab,S-003,担当者,記入中,,明細を見る,明細の一覧,F-001,,order-lines.md,F-001\n"
    "S-006,履歴,tab,S-003,担当者,記入中,,履歴を見る,変更の履歴,F-001,,order-history.md,F-001\n")
V1_ITEMS = I_HEAD + (
    "I-010,S-001,一覧,1,受注の一覧,一覧,受注の並び,,,,,,,Q-R-001\n"
    "I-011,S-001,受注の一覧,2,受注日,一覧の列,受注した日,2026/11/16,,,,はい,はい,Q-R-001\n"
    "I-012,S-001,受注の一覧,3,顧客名,一覧の列,顧客の名前,山田商店,,,,いいえ,いいえ,Q-R-001\n"
    "I-013,S-001,操作,4,新規,ボタン,,,,,,,,F-002\n"
    "I-020,S-002,入力,1,顧客名,入力,顧客の名前,山田,はい,30 文字まで,30 文字までで入れてください,,,F-002\n"
    "I-021,S-002,操作,2,保存,ボタン,,,,,,,,F-002\n"
    "I-030,S-003,概要,1,受注番号,表示,受注の番号,A-0001,,,,,,F-001、D-S-001\n"
    "I-031,S-003,操作,2,戻る,ボタン,,,,,,,,F-001\n"
    "I-040,S-004,操作,1,閉じる,ボタン,,,,,,,,F-002\n"
    "I-050,S-005,操作,1,履歴へ,ボタン,,,,,,,,F-001\n"
    "I-060,S-006,操作,1,印刷,ボタン,,,,,,,,F-001\n")
V1_TRANSITIONS = T_HEAD + (
    "T-001,S-001,I-013,受注の登録,,S-002,,F-002\n"
    "T-002,S-001,I-010,,,S-003,,Q-R-001\n"
    "T-003,S-002,I-021,受注の登録,入力チェックが通ったとき,S-001,保存した,F-002\n"
    "T-004,S-002,I-021,,入力に確認の要る値があるとき（D-S-001）,S-004,,F-002、D-S-001\n"
    "T-005,S-003,I-031,,,S-001,,F-001\n"
    "T-006,S-004,I-040,,,S-002,,F-002\n"
    "T-007,S-005,I-050,,,S-006,,F-001\n")
V2_SCREENS = S_HEAD + "S-008,配置図,setting,,管理者,下書き,,配置を見る,機器の配置,F-001,,layout.md,F-001\n"
V2_ITEMS = I_HEAD + ("I-014,S-001,操作,5,配置図,ボタン,,,,,,,,F-001\n"
                     "I-080,S-008,操作,1,一覧へ戻る,ボタン,,,,,,,,F-001\n")
V2_TRANSITIONS = T_HEAD + ("T-008,S-001,I-014,,,S-008,,F-001\n"
                           "T-009,S-008,I-080,,,S-001,,F-001\n")
DOCS = {"S-001": "order-list.md", "S-002": "order-new.md", "S-003": "order-detail.md", "S-004": "order-confirm.md",
        "S-005": "order-lines.md", "S-006": "order-history.md"}
RENDERER = """// 案件に固有の描き方（配置図）。名前とボタンは表から読む
var box = document.createElement("div");
box.className = "custom-layout";
box.textContent = "（配置）" + ctx.screen["画面名"] + "</script><!-- 閉じない -->";
ctx.root.appendChild(box);
ctx.root.appendChild(ctx.button("I-080"));
"""
SECRET_PATH = "/orders/secret-path-1095"


def doc(key: str) -> str:
    return f"# {key}\n\n## 7. 状態\n\nN/A。無い\n"


def base_files() -> dict[str, str]:
    files = {
        "docs/v1/shared/qa.csv": QA_HEAD + "Q-R-001,要求確定,質問,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n",
        "docs/v1/spec/qa-dev.csv": QA_HEAD + "D-S-001,仕様レビュー,質問,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n",
        "docs/v1/requirements/features.csv": "id,名前,種類,関係\nF-001,受注一覧,画面,\nF-002,受注登録,画面,\n",
        "docs/v1/requirements/roles.csv": "操作,担当者\n受注の登録,可\n",
        "docs/v1/" + DATA + "screens.csv": V1_SCREENS,
        "docs/v1/" + DATA + "screen-items.csv": V1_ITEMS,
        "docs/v1/" + DATA + "transitions.csv": V1_TRANSITIONS,
        "docs/v2/" + DATA + "screens.csv": V2_SCREENS,
        "docs/v2/" + DATA + "screen-items.csv": V2_ITEMS,
        "docs/v2/" + DATA + "transitions.csv": V2_TRANSITIONS,
        "docs/v2/requirements/screens/layout.md": doc("S-008"),
        "screen-spec/renderers/S-008.js": RENDERER,
        "screen-spec/renderers/S-999.js": "ctx.root.textContent = 'x';\n",
        "screen-spec/renderers/README.txt": "メモ\n",
    }
    for key, name in DOCS.items():
        files["docs/v1/requirements/screens/" + name] = doc(key)
    return files


def changed(**changes: str | None) -> dict[str, str]:
    files = base_files()
    for path, body in changes.items():
        path = path.replace("__", "/").replace("_DOT_", ".")
        if body is None:
            files.pop(path, None)
        else:
            files[path] = body
    return files


def with_(files: dict[str, str], extra: dict[str, str | None]) -> dict[str, str]:
    out = dict(files)
    for path, body in extra.items():
        if body is None:
            out.pop(path, None)
        else:
            out[path] = body
    return out


# (名前, 正本のファイル, 準備, 引数, 終了コード, 出力の場所（docs の親から）か None, 出力（標準出力と標準エラー）に在る文字列)
# 準備: "git"（全部コミットしてタグ）／ "dirty"（コミットの後で docs を変える）／ "nogit"（git の外）／ "pathcol"（本体の列にパスを足した写し）／
#       ("version", "<版>")（spec-loop の写しの版を変える）
CASES: list[tuple[str, dict, object, list[str], int, str | None, str]] = [
    ("good", base_files(), "git", [], 0, "build/mock/v2/index.html", "書いた:"),
    ("upto-1", base_files(), "git", ["--upto", "1"], 0, "build/mock/v1/index.html", "書いた:"),
    ("dirty", base_files(), "dirty", [], 0, "build/mock/v2/index.html", "書いた:"),
    ("nogit", base_files(), "nogit", [], 0, "build/mock/v2/index.html", "書いた:"),
    ("no-renderers", with_(base_files(), {"screen-spec/renderers/S-008.js": None, "screen-spec/renderers/S-999.js": None,
                                          "screen-spec/renderers/README.txt": None}), "git", [], 0, "build/mock/v2/index.html", "書いた:"),
    ("path-column", with_(base_files(), {
        "docs/v1/" + DATA + "screens.csv": "\n".join(line + ("," + (SECRET_PATH if i else "パス") if line else "")
                                                     for i, line in enumerate(V1_SCREENS.split("\n"))),
        "docs/v2/" + DATA + "screens.csv": "\n".join(line + ("," + (SECRET_PATH if i else "パス") if line else "")
                                                     for i, line in enumerate(V2_SCREENS.split("\n")))}),
     "pathcol", [], 0, "build/mock/v2/index.html", "書いた:"),
    # ---- 止まる（1）
    ("renderers-in-version", with_(base_files(), {"docs/v1/requirements/screens/renderers/S-001.js": "ctx.root.textContent='x';\n"}),
     "git", [], 1, None, "描き方のファイルを版の中に置いている"),
    ("renderers-in-later-version", with_(base_files(), {"docs/v2/renderers/S-001.js": "ctx.root.textContent='x';\n"}),
     "git", ["--upto", "1"], 1, None, "描き方のファイルを版の中に置いている"),
    ("tables-missing", with_(base_files(), {"docs/v1/" + DATA + "transitions.csv": None, "docs/v2/" + DATA + "transitions.csv": None}),
     "git", [], 1, None, "画面の表が揃っていない"),
    ("header-differs-from-rule", with_(base_files(), {
        "docs/v1/" + DATA + "transitions.csv": V1_TRANSITIONS.replace(",結果,", ",成果,"),
        "docs/v2/" + DATA + "transitions.csv": V2_TRANSITIONS.replace(",結果,", ",成果,")}),
     "git", [], 1, None, "見出し行が決まり"),
    ("merge-problem", with_(base_files(), {"docs/v2/" + DATA + "transitions.csv": V2_TRANSITIONS.replace(",根拠\n", ",根拠,備考\n", 1)}),
     "git", [], 1, None, "版の重ね合わせが spec-loop の決まりに反する"),
    # ---- 判定していない（2）・止めた（4）
    ("no-args", base_files(), "git", ["<none>"], 2, None, "usage:"),
    ("upto-missing", base_files(), "git", ["--upto", "9"], 2, None, "作っていない"),
    ("docs-missing", base_files(), "git", ["<missing>"], 2, None, "ディレクトリが無い"),
    ("spec-loop-out-of-range", base_files(), ("version", "1.0.0"), [], 4, None, "対応の範囲の外"),
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


def copy_plugin(source: Path, dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


PATH_COLUMN = ('"機能", "帳票", "仕様書", "根拠"],', '"機能", "帳票", "仕様書", "根拠", "パス"],')


def snapshot(root: Path, skip: str | None = None) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "/.git/" not in f"/{p.relative_to(root).as_posix()}"
            and not (skip and p.relative_to(root).as_posix().startswith(skip))}


def git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(cwd)})
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env, check=True)
    return proc.stdout.strip()


def make_repo(case_dir: Path, files: dict[str, str], how) -> Path:
    repo = case_dir / "repo"
    assert_in_tmp(repo)
    for rel, body in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    if how != "nogit":
        git(repo, "init", "-q")
        git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "add", "-A")
        git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qm", "正本")
        if (repo / "screen-spec").is_dir():
            # 描き方のファイルを最後に変えたコミットは、表のコミット（HEAD）と別にする
            (repo / "screen-spec" / "renderers" / "S-008.js").write_text(RENDERER + "// 後で直した\n", encoding="utf-8")
            git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qam", "描き方")
            git(repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "表")
        git(repo, "tag", "signoff/v2/req-1")
    if how == "dirty":
        (repo / "docs" / "v1" / DATA / "screens.csv").write_text(V1_SCREENS + "\n", encoding="utf-8")
    return repo


def run_one(plugin: Path, sibling: Path, case_dir: Path, case) -> dict:
    name, files, how, args, _, out_rel, _ = case
    assert_in_tmp(case_dir)
    repo = make_repo(case_dir, files, how)
    home = case_dir / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR", "SCREEN_SPEC_SPEC_LOOP")}
    env["HOME"] = str(home)
    script = plugin / "scripts" / TARGET
    extra: list[str] = []
    if isinstance(how, tuple) and how[0] == "version":
        extra = ["--spec-loop", str(copy_spec_loop(case_dir / "alt-spec-loop", version=how[1]))]
    if how == "pathcol":
        copied = copy_plugin(plugin, case_dir / "pathcol" / "screen-spec")
        copy_spec_loop(case_dir / "pathcol" / "spec-loop")
        target = copied / "scripts" / "check-screens.py"
        source = target.read_text(encoding="utf-8")
        assert source.count(PATH_COLUMN[0]) == 1, "パスの列を足す箇所が check-screens.py にちょうど 1 回無い"
        target.write_text(source.replace(*PATH_COLUMN), encoding="utf-8")
        script = copied / "scripts" / TARGET
    if args == ["<none>"]:
        argv: list[str] = []
    elif args == ["<missing>"]:
        argv = [str(case_dir / "nowhere")]
    else:
        argv = [str(repo / "docs"), *args]
    watched = (sibling.parent,)
    before = [snapshot(root) for root in watched] + [snapshot(repo, skip="build/")]
    proc = subprocess.run([sys.executable, "-I", str(script), *argv, *extra], capture_output=True, text=True, cwd=case_dir, env=env)
    after = [snapshot(root) for root in watched] + [snapshot(repo, skip="build/")]
    built = snapshot(repo / "build") if (repo / "build").is_dir() else {}
    out = proc.stdout + proc.stderr
    page = (repo / out_rel).read_text(encoding="utf-8") if out_rel and (repo / out_rel).is_file() else None
    return {"code": proc.returncode, "out": out, "page": page, "built": sorted(built), "wrote_elsewhere": before != after,
            "repo": repo, "stdout": proc.stdout}


def embedded(page: str) -> dict:
    found = re.search(r'<script type="application/json" id="screen-spec-data">(.*?)</script>', page, re.S)
    return json.loads(found.group(1)) if found else {}


def table_rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def merged_rows(files: dict[str, str], upto: int, table: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for version in range(1, upto + 1):
        text = files.get(f"docs/v{version}/{DATA}{table}")
        for row in table_rows(text) if text else []:
            rows[row["画面ID" if table == "screens.csv" else "番号"]] = row
    return rows


def case_problems(case, result: dict) -> list[str]:
    name, files, how, args, code, out_rel, text = case
    problems = []
    if result["code"] != code:
        problems.append(f"終了コード {result['code']}（期待 {code}）")
    if text not in result["out"]:
        problems.append(f"出力に {text!r} が無い")
    if "Traceback" in result["out"]:
        problems.append("Traceback")
    if result["wrote_elsewhere"]:
        problems.append("正本か読み込んだプラグインにファイルを書いた")
    expected_built = [Path(out_rel).relative_to("build").as_posix()] if out_rel and code == 0 else []
    if result["built"] != expected_built:
        problems.append(f"build/ に書いたもの {result['built']}（期待 {expected_built}）")
    if code != 0 or result["page"] is None:
        return problems
    page = result["page"]
    data = embedded(page)
    upto = int(args[1]) if args[:1] == ["--upto"] else 2
    screens = merged_rows(files, upto, "screens.csv")
    items = merged_rows(files, upto, "screen-items.csv")
    transitions = merged_rows(files, upto, "transitions.csv")
    # M1 画面名・ボタン名がすべて表の中にある（表に無いものを作らない・表の行を落とさない）
    shown_screens = [(s.get("画面ID"), s.get("画面名")) for s in data.get("screens", [])]
    if shown_screens != [(k, r["画面名"]) for k, r in screens.items()]:
        problems.append(f"埋め込んだ画面が表と違う: {shown_screens}")
    shown_buttons = sorted((i.get("番号"), i.get("項目名")) for i in data.get("items", []) if i.get("種類") == "ボタン")
    if shown_buttons != sorted((k, r["項目名"]) for k, r in items.items() if r["種類"] == "ボタン"):
        problems.append(f"埋め込んだボタンが表と違う: {shown_buttons}")
    if sorted(t.get("番号") for t in data.get("transitions", [])) != sorted(transitions):
        problems.append("埋め込んだ遷移が表と違う")
    # M3 外を読まない
    for pattern in (r"<script[^>]*\ssrc=", r"<link\b", r"<img\b", r"<iframe\b", r"url\(", r"@import", r"https?://"):
        if re.search(pattern, page, re.I):
            problems.append(f"外を読みうる {pattern!r} がある")
    # M4 何で作ったか
    meta = dict(re.findall(r'<meta name="screen-spec-([a-z]+)" content="([^"]*)">', page))
    if meta.get("version") != f"v{upto}":
        problems.append(f"版の印が違う: {meta.get('version')}")
    generator = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    if meta.get("generator") != f"screen-spec {generator}":
        problems.append(f"生成器の印が違う: {meta.get('generator')}")
    repo = result["repo"]
    if how == "nogit":
        if "git の外" not in meta.get("tables", ""):
            problems.append(f"git の外なのに表の出どころが {meta.get('tables')!r}")
    else:
        head = git(repo, "rev-parse", "HEAD")
        if f"コミット {head}" not in meta.get("tables", ""):
            problems.append(f"表の出どころにコミット {head} が無い: {meta.get('tables')!r}")
        if "signoff/v2/req-1" not in meta.get("tables", ""):
            problems.append(f"表の出どころにタグが無い: {meta.get('tables')!r}")
        if (how == "dirty") != ("未コミットの変更あり" in meta.get("tables", "")):
            problems.append(f"未コミットの変更の印が違う: {meta.get('tables')!r}")
        if "screen-spec/renderers/S-008.js" in files and upto >= 2:
            last = git(repo, "log", "-1", "--format=%H", "--", "screen-spec/renderers")
            if meta.get("renderers") != f"コミット {last}":
                problems.append(f"描き方のファイルの印が違う: {meta.get('renderers')!r}（期待 コミット {last}）")
        elif meta.get("renderers") != "差し替え無し":
            problems.append(f"埋め込んだ描き方が無いのに {meta.get('renderers')!r}")
    for key in ("version", "tables", "generator", "renderers"):
        if meta.get(key) and meta[key] not in page.split("<footer", 1)[-1]:
            problems.append(f"{key} の印が見える文字に無い")
    # M7 D- の番号もパスの列も出ない
    if re.search(r"D-(?:[A-Z]-)?[0-9]{3}", page):
        problems.append("内部の層の番号（D-）が出ている")
    if SECRET_PATH in page or '"パス"' in page:
        problems.append("許可の外の列（パス）が出ている")
    detail = next((s for s in data.get("screens", []) if s.get("画面ID") == "S-003"), {})
    if detail.get("根拠") != "F-001":
        problems.append(f"D- を外した根拠が {detail.get('根拠')!r}")
    branch = next((t for t in data.get("transitions", []) if t.get("番号") == "T-004"), {})
    if branch.get("条件") != "入力に確認の要る値があるとき" or branch.get("根拠") != "F-002":
        problems.append(f"D- を外した条件・根拠が {branch.get('条件')!r}・{branch.get('根拠')!r}")
    # M11 描き方の差し替え
    has_renderer = "screen-spec/renderers/S-008.js" in files and upto >= 2
    if has_renderer != ('window.screenSpecRenderers["S-008"]' in page):
        problems.append("描き方のファイルの埋め込みが違う")
    if has_renderer and ("<\\/script><\\!-- 閉じない -->" not in page):
        problems.append("描き方のファイルの </script・<!-- を閉じない形にしていない")
    if page.count("</script>") != 3:
        problems.append(f"</script> が {page.count('</script>')} 回（埋め込みで閉じている）")
    if 'window.screenSpecRenderers["S-999"]' in page:
        problems.append("表に無い画面の描き方を埋め込んだ")
    if "screen-spec/renderers/S-999.js" in files and "画面 S-999 が表に無いので埋め込まない" not in result["stdout"]:
        problems.append("表に無い画面の描き方の警告が無い")
    if "screen-spec/renderers/README.txt" in files and "README.txt: 描き方のファイル" not in result["stdout"]:
        problems.append(".js でないファイルの警告が無い")
    # M10 散文の節へのリンク
    if data.get("documents", {}).get("S-001") != "../../../docs/v1/requirements/screens/order-list.md":
        problems.append(f"散文の節へのリンクが違う: {data.get('documents', {}).get('S-001')!r}")
    if data.get("proseSections") != ["7. 状態", "9. 他システム連携", "10. 同時編集", "11. 表示ルール", "未決の論点"]:
        problems.append(f"散文の節が違う: {data.get('proseSections')}")
    return problems


def run_cases(plugin: Path, sibling: Path, work: Path, only: str | None = None) -> dict[str, dict]:
    return {case[0]: run_one(plugin, sibling, work / f"case{i}", case) for i, case in enumerate(CASES) if only is None or case[0] == only}


# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("D- を外さない", "        if not self.internal.search(value):\n            return value\n",
     "        return value\n", "good"),
    ("版の中の描き方で止めない", "    if forbidden:\n", "    if False:\n", "renderers-in-version"),
    ("--upto より後の版の描き方を見ない", "    forbidden = forbidden_renderers(versions)\n",
     "    forbidden = forbidden_renderers(versions[:number])\n", "renderers-in-later-version"),
    ("許可の外の列も埋め込む", "for column in SHOWN[name] if column in row}", "for column in row}", "path-column"),
    ("</script を閉じない形にしない", '    return re.sub(r"<(/script|!--)", lambda m: "<\\\\" + m.group(1), text, flags=re.IGNORECASE)\n',
     "    return text\n", "good"),
    ("--upto を無視する", "    number = upto or len(versions)\n", "    number = len(versions)\n", "upto-1"),
    ("タグを書かない", '        out += f"（タグ: {\', \'.join(sorted(tags))}）"\n', "        pass\n", "good"),
    ("未コミットの変更を書かない", '        out += "（docs に未コミットの変更あり）"\n', "        pass\n", "dirty"),
    ("表に無い画面の描き方も埋め込む", "        if key not in screens:\n", "        if False:\n", "good"),
    ("表が揃っていなくても作る", "    if missing:\n", "    if False:\n", "tables-missing"),
    ("見出し行を見ない", "        if whole.headers[path] != screens_check.COLUMNS[path]:\n", "        if False:\n", "header-differs-from-rule"),
    ("描き方のファイルのコミットを書かない", '    out = f"コミット {last}" if last else "コミットが無い"\n', '    out = "コミットが無い"\n', "good"),
]
OO_MUTATIONS = [("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else")]


def oo_problems(plugin: Path, cwd: Path) -> list[str]:
    proc = subprocess.run([sys.executable, "-I", "-OO", str(plugin / "scripts" / TARGET)], capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        return [f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}"]
    return []


# ---- references との突き合わせ

def section(markdown: str, heading: str) -> str:
    level = len(heading) - len(heading.lstrip("#"))
    start = markdown.index(heading)
    rest = markdown[start + len(heading):]
    found = re.search(rf"^#{{1,{level}}} ", rest, flags=re.MULTILINE)
    return rest[:found.start()] if found else rest


def table_cells(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] not in ("決まり", "表", "---"):
            out[cells[0]] = cells[1]
    return out


def reference_mismatches(module, mock: str, tables: str) -> list[str]:
    problems = []

    def same(what: str, ours, theirs) -> None:
        if ours != theirs:
            problems.append(f"{what}: 本体 {ours!r} ／ references {theirs!r}")

    output = table_cells(section(mock, "## 出力"))
    same("出力の置き場所", f"`<docs の親>/{module.OUT_DIR}/v<n>/`", output.get("出力の置き場所"))
    same("出力のファイル", f"`{module.OUT_NAME}`", output.get("出力のファイル"))
    renderers = table_cells(section(mock, "## 描き方の差し替え"))
    same("描き方の置き場所", f"`<docs の親>/{module.RENDERERS}/`（版の外）", renderers.get("置き場所"))
    same("描き方のファイルの名前", f"`<画面ID>{module.RENDERER_SUFFIX}`", renderers.get("ファイルの名前"))
    same("版の中で止める名前", f"`{module.FORBIDDEN_DIR}`", renderers.get("版の中で止める名前"))
    shown = table_cells(section(mock, "## 共有の層だけを出す"))
    for key, label in (("screens", "画面"), ("items", "項目"), ("transitions", "遷移")):
        same(f"埋め込む列（{label}）", module.SHOWN[key], re.findall(r"`([^`]+)`", shown.get(label, "")))
    kinds = re.findall(r"^\| `([^`]+)` \|", section(tables, "### 項目の種類"), flags=re.MULTILINE)
    same("一覧の種類", module.LIST in kinds and f"種類 `{module.LIST}`" in mock, True)
    codes = re.findall(r"^\| ([0-9]) \|", section(mock, "## 終了コード"), flags=re.MULTILINE)
    same("終了コード", codes, ["0", "1", "2", "4"])
    return problems


REFERENCE_MUTATIONS = [
    ("出力の置き場所", "| 出力の置き場所 | `<docs の親>/build/mock/v<n>/` |", "| 出力の置き場所 | `<docs の親>/build/mocks/v<n>/` |"),
    ("描き方の置き場所", "| 置き場所 | `<docs の親>/screen-spec/renderers/`（版の外） |", "| 置き場所 | `<docs の親>/renderers/`（版の外） |"),
    ("版の中で止める名前", "| 版の中で止める名前 | `renderers` |", "| 版の中で止める名前 | `renderer` |"),
    ("埋め込む列", "| 遷移 | `番号`・`遷移元`・`きっかけ`・`操作`・`条件`・", "| 遷移 | `番号`・`遷移元`・`きっかけ`・`条件`・"),
]


def load(path: Path):
    import importlib.util
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("build_mock_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- 手元で回す部分（ヘッドレスの Chrome）

WALKER = r"""
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [chrome, mockPath, planPath, outPath] = process.argv.slice(2);
const plan = JSON.parse(readFileSync(planPath, 'utf8'));
const profile = mkdtempSync(join(tmpdir(), 'mock-walk-'));
const proc = spawn(chrome, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function finish(result, code) {
  writeFileSync(outPath, JSON.stringify(result, null, 1));
  try { proc.kill('SIGKILL'); } catch (e) { /* 止まっている */ }
  try { rmSync(profile, { recursive: true, force: true }); } catch (e) { /* 消せなくても結果は書いた */ }
  process.exit(code);
}
setTimeout(() => finish({ error: '時間切れ（90 秒）' }, 3), 90000);
let port = null;
for (let i = 0; i < 150 && port === null; i++) {
  const file = join(profile, 'DevToolsActivePort');
  if (existsSync(file)) port = readFileSync(file, 'utf8').split('\n')[0].trim() || null;
  if (port === null) await sleep(100);
}
if (port === null) finish({ error: 'Chrome の DevTools の口が開かない' }, 3);
const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const page = targets.find((t) => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let seq = 0;
const pending = new Map();
const requests = [];
const errors = [];
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); return; }
  if (msg.method === 'Network.requestWillBeSent') requests.push(msg.params.request.url);
  if (msg.method === 'Runtime.exceptionThrown') errors.push(JSON.stringify(msg.params.exceptionDetails).slice(0, 400));
};
const send = (method, params = {}) => new Promise((resolve) => { const id = ++seq; pending.set(id, resolve); ws.send(JSON.stringify({ id, method, params })); });
await send('Network.enable');
await send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
await send('Runtime.enable');
await send('Page.enable');
const url = pathToFileURL(mockPath).href;
await send('Page.navigate', { url });
await sleep(1000);
const walker = async function (plan) {
  const wait = () => new Promise((r) => setTimeout(r, 40));
  const app = document.getElementById('app');
  const msg = () => document.getElementById('message').textContent;
  const out = { steps: [], screens: [], names: [], buttons: [], explain: [], unknown: {}, custom: {} };
  async function go(id) { location.hash = '#screen=' + encodeURIComponent(id); await wait(); await wait(); }
  async function reset() { location.hash = '#'; await wait(); }
  out.loaded = { current: app.getAttribute('data-current'), names: [...document.querySelectorAll('[data-role=screen-name]')].map((n) => n.textContent) };
  for (const s of plan.screens) {
    await reset();
    await go(s);
    out.screens.push({ id: s, current: app.getAttribute('data-current'),
      heads: [...document.querySelectorAll('[data-role=screen-name]')].map((n) => n.textContent),
      dialog: document.querySelector(`[data-dialog="${s}"]`) !== null,
      tabSelected: document.querySelector(`[data-tab="${s}"][aria-selected="true"]`) !== null,
      tables: document.querySelectorAll('table.mock-list').length,
      inputs: document.querySelectorAll('input[data-item]').length,
      proseLinks: [...document.querySelectorAll('[data-role=prose-link]')].map((a) => a.getAttribute('href')) });
    out.names.push(...[...document.querySelectorAll('[data-role=screen-name]')].map((n) => n.textContent));
    out.buttons.push(...[...document.querySelectorAll('[data-role=button]')].map((n) => n.textContent));
    out.explain.push(document.getElementById('explain').textContent);
  }
  for (const t of plan.transitions) {
    await reset();
    await go(t.from);
    const before = window.screenSpecMock.history.length;
    const node = document.querySelector(`[data-item="${t.trigger}"]`);
    const step = { id: t.id, found: node !== null };
    if (node) {
      node.click();
      await wait(); await wait();
      const choice = document.querySelector(`button[data-transition="${t.id}"]`);
      if (choice) { step.chose = true; choice.click(); await wait(); await wait(); }
      const hist = window.screenSpecMock.history;
      step.current = app.getAttribute('data-current');
      step.last = hist.length > before ? hist[hist.length - 1]['番号'] : null;
      step.historyShown = [...document.querySelectorAll('[data-role=history] [data-transition]')].map((n) => n.getAttribute('data-transition'));
    }
    out.steps.push(step);
  }
  for (const b of plan.untriggered) {
    await reset();
    await go(b.screen);
    const node = document.querySelector(`[data-item="${b.item}"]`);
    if (node) { node.click(); await wait(); }
    out.unknown[b.item] = { found: node !== null, grey: node ? node.classList.contains('no-transition') : null, message: msg(),
      current: app.getAttribute('data-current') };
  }
  await reset();
  await go(plan.screens[0]);
  window.screenSpecMock.follow('T-NOT-IN-TABLE');
  await wait();
  out.unknown.call = msg();
  location.hash = '#screen=S-NOT-IN-TABLE';
  await wait(); await wait();
  out.unknown.screen = msg();
  await reset();
  await go(plan.hover.screen);
  const hovered = document.querySelector(`[data-item="${plan.hover.item}"]`);
  hovered.dispatchEvent(new MouseEvent('mouseenter'));
  await wait();
  out.hover = document.getElementById('explain').textContent;
  await reset();
  await go(plan.custom.screen);
  out.custom.drawn = document.querySelector(plan.custom.selector) !== null;
  out.custom.text = (document.querySelector(plan.custom.selector) || {}).textContent || null;
  const own = document.querySelector(`[data-item="${plan.custom.item}"]`);
  out.custom.button = own ? own.textContent : null;
  if (own) { own.click(); await wait(); await wait(); }
  out.custom.current = app.getAttribute('data-current');
  out.provenance = document.getElementById('provenance').textContent;
  out.text = document.body.innerText;
  return out;
};
const evaluated = await send('Runtime.evaluate', { expression: `(${walker.toString()})(${JSON.stringify(plan)})`, awaitPromise: true, returnByValue: true });
if (evaluated.result.exceptionDetails) finish({ error: '踏む途中で例外: ' + JSON.stringify(evaluated.result.exceptionDetails).slice(0, 800) }, 3);
const result = evaluated.result.result.value;
result.url = url;
result.requests = requests;
result.errors = errors;
finish(result, 0);
"""


def find_chrome() -> str | None:
    named = os.environ.get("SCREEN_SPEC_CHROME")
    if named:
        return named if Path(named).is_file() else None
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if Path(mac).is_file():
        return mac
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")


# 手元で回す部分の陽性対照: 本体を壊したモックでは、名指しした行が NG になる（踏み方が壊れていれば緑のまま——それを落とす）
BROWSER_MUTATIONS: list[tuple[str, str, str, str]] = [
    ("履歴に積まない", "    history.push(t);\n", "", "遷移 T-001"),
    ("D- を外さない", "        if not self.internal.search(value):\n            return value\n", "        return value\n", "説明の欄に D- の番号が出ない"),
    ("外の画像を読む", '<div id="message" role="status"></div>', '<div id="message" role="status"></div><img src="https://example.invalid/x.png" alt="">',
     "file: のほかの要求が 0 件"),
    ("dialog を重ねない", '      if (screens[k]["種別"] === DATA.tabKind) return;\n', "      return;\n", "#screen=S-004（dialog）"),
    ("遷移の無いボタンで黙る", '      if (!list.length) { say("遷移が表に無い: "', '      if (!list.length) { say("" + ', "遷移の無いボタン I-060"),
]


def walk(plugin: Path, sibling: Path, work: Path, chrome: str, node: str) -> tuple[list[tuple[str, bool, str]] | None, str]:
    files = base_files()
    screens = merged_rows(files, 2, "screens.csv")
    items = merged_rows(files, 2, "screen-items.csv")
    transitions = merged_rows(files, 2, "transitions.csv")
    triggered = {t["きっかけ"] for t in transitions.values()}
    plan = {
        "screens": list(screens),
        "transitions": [{"id": k, "from": t["遷移元"], "trigger": t["きっかけ"], "to": t["遷移先"]} for k, t in transitions.items()],
        "untriggered": [{"screen": i["画面ID"], "item": k} for k, i in items.items() if i["種類"] == "ボタン" and k not in triggered],
        "hover": {"screen": "S-002", "item": "I-021"},
        "custom": {"screen": "S-008", "selector": ".custom-layout", "item": "I-080"},
    }
    result = run_one(plugin, sibling, work, ("browser", files, "git", [], 0, "build/mock/v2/index.html", "書いた:"))
    if result["code"] != 0:
        return None, f"生成に失敗した: {result['out']}"
    mock = result["repo"] / "build" / "mock" / "v2" / "index.html"
    (work / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    (work / "walk.mjs").write_text(WALKER, encoding="utf-8")
    proc = subprocess.run([node, str(work / "walk.mjs"), chrome, str(mock), str(work / "plan.json"), str(work / "out.json")],
                          capture_output=True, text=True, timeout=150)
    try:
        out = json.loads((work / "out.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, f"踏めなかった（node の終了 {proc.returncode}）: {proc.stderr[-800:]}"
    if "error" in out:
        return None, f"踏めなかった: {out['error']}"
    names = {r["画面名"] for r in screens.values()}
    buttons = {r["項目名"] for r in items.values() if r["種類"] == "ボタン"}
    rows: list[tuple[str, bool, str]] = []

    def row(what: str, ok: bool, detail: str = "") -> None:
        rows.append((what, bool(ok), detail))

    row("開いた URL が file:// で、file: のほかの要求が 0 件（ネットワークを切って開いた）",
        out["url"].startswith("file://") and all(u.startswith("file:") for u in out["requests"]),
        f"要求 {len(out['requests'])} 件: " + ", ".join(sorted({u.split(':', 1)[0] for u in out['requests']})))
    row("ページの例外が 0 件", not out["errors"], "; ".join(out["errors"])[:300])
    row("ハッシュ無しで開くと入口（種別 top）の画面が出る", out["loaded"]["current"] == "S-001", str(out["loaded"]))
    for step in out["steps"]:
        t = transitions[step["id"]]
        ok = step["found"] and step.get("current") == t["遷移先"] and step.get("last") == step["id"] and step["id"] in step.get("historyShown", [])
        row(f"遷移 {step['id']}（{t['遷移元']} の {t['きっかけ']} → {t['遷移先']}）を踏めて、履歴に出る"
            + ("（条件で分かれるので選んだ）" if step.get("chose") else ""), ok, json.dumps(step, ensure_ascii=False))
    for screen in out["screens"]:
        kind = screens[screen["id"]]["種別"]
        ok = screen["current"] == screen["id"] and screens[screen["id"]]["画面名"] in screen["heads"]
        if kind == "dialog":
            ok = ok and screen["dialog"]
        if kind == "tab":
            ok = ok and screen["tabSelected"]
        row(f"#screen={screen['id']}（{kind}）で開くとその画面が出る", ok,
            json.dumps({k: screen[k] for k in ("current", "heads", "dialog", "tabSelected")}, ensure_ascii=False))
    by_id = {s["id"]: s for s in out["screens"]}
    row("list の画面（S-001）に一覧の表が描かれる", by_id["S-001"]["tables"] >= 1)
    row("form の画面（S-002）に入力欄が描かれる", by_id["S-002"]["inputs"] >= 1)
    row("描かれた画面名がすべて表の中にある", set(out["names"]) <= names, str(sorted(set(out["names"]) - names)))
    row("描かれたボタン名がすべて表の中にある", set(out["buttons"]) <= buttons, str(sorted(set(out["buttons"]) - buttons)))
    row("説明の欄に D- の番号が出ない", not any(re.search(r"D-(?:[A-Z]-)?[0-9]{3}", e) for e in out["explain"] + [out["text"]]))
    row("説明の欄に目的と背景・できること・主たる利用者・項目の中身・根拠が出る",
        all(w in out["explain"][0] for w in ("受注を探す", "一覧と絞り込み", "担当者", "受注した日", "Q-R-001")))
    row("散文の節へのリンクが出る", "../../../docs/v1/requirements/screens/order-list.md" in by_id["S-001"]["proseLinks"])
    for item, seen in out["unknown"].items():
        if item in ("call", "screen"):
            continue
        row(f"遷移の無いボタン {item} は灰色で、押すと「遷移が表に無い」", seen["found"] and seen["grey"] and "遷移が表に無い" in seen["message"],
            json.dumps(seen, ensure_ascii=False))
    row("表に無い遷移を呼ぶと「遷移が表に無い」", "遷移が表に無い" in out["unknown"]["call"], out["unknown"]["call"])
    row("表に無い画面を #screen= で開くと「画面が表に無い」", "画面が表に無い" in out["unknown"]["screen"], out["unknown"]["screen"])
    row("ボタンにカーソルを当てると遷移の番号・条件・根拠が出る",
        all(w in out["hover"] for w in ("T-003", "T-004", "入力チェックが通ったとき", "F-002")) and "D-S-" not in out["hover"], out["hover"][:200])
    row("描き方の差し替え（S-008）で描かれ、ctx.button のボタンで遷移できる",
        out["custom"]["drawn"] and out["custom"]["button"] == "一覧へ戻る" and out["custom"]["current"] == "S-001",
        json.dumps(out["custom"], ensure_ascii=False))
    row("何で作ったかの印が見える", all(w in out["provenance"] for w in ("v2", "コミット", "signoff/v2/req-1", "screen-spec ")), out["provenance"][:300])
    return rows, ""


def browser() -> int:
    chrome = find_chrome()
    node = shutil.which("node")
    if not chrome or not node:
        print(f"手元で回せない（Chrome: {chrome or '無い'}・node: {node or '無い'}）——回していない")
        return 3
    with tempfile.TemporaryDirectory(prefix="build-mock-browser-") as tmp:
        tmp_path = Path(tmp)
        plugin = copy_plugin(PLUGIN, tmp_path / "plugins" / "screen-spec")
        sibling = copy_spec_loop(tmp_path / "plugins" / "spec-loop")
        rows, why = walk(plugin, sibling, tmp_path / "work", chrome, node)
        if rows is None:
            print(why)
            return 3
        controls = []
        source = (PLUGIN / "scripts" / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, expect) in enumerate(BROWSER_MUTATIONS):
            if source.count(before) != 1:
                controls.append((name, False, f"壊す箇所が {source.count(before)} 回現れる"))
                continue
            root = tmp_path / f"mut{index}" / "plugins"
            mutated = copy_plugin(PLUGIN, root / "screen-spec")
            mutated_sibling = copy_spec_loop(root / "spec-loop")
            (mutated / "scripts" / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            got, why = walk(mutated, mutated_sibling, tmp_path / f"mutwork{index}", chrome, node)
            if got is None:
                controls.append((name, False, why))
                continue
            caught = [what for what, ok, _ in got if not ok and expect in what]
            controls.append((name, bool(caught), "NG にならなかった" if not caught else caught[0]))
    print("| 確かめたこと | 結果 |")
    print("| --- | --- |")
    for what, ok, detail in rows:
        print(f"| {what} | {'OK' if ok else 'NG: ' + detail} |")
    print("\n陽性対照（本体を壊したモックでは、その行が NG になる）:\n")
    print("| 壊し方 | 結果 |")
    print("| --- | --- |")
    for name, ok, detail in controls:
        print(f"| {name} | {'NG になった（' + detail + '）' if ok else '捕まえられなかった: ' + detail} |")
    bad = [r for r in rows if not r[1]] + [c for c in controls if not c[1]]
    print(f"\n{len(rows)} 項目・陽性対照 {len(controls)} 件・失敗 {len(bad)} 件（Chrome: {chrome}・node: {node}）")
    return 1 if bad else 0


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    killers = {killer for *_, killer in MUTATIONS}
    assert killers <= set(names), f"変異の殺す試料が無い: {killers - set(names)}"
    with tempfile.TemporaryDirectory(prefix="build-mock-test-") as tmp:
        tmp_path = Path(tmp)
        plugins = tmp_path / "plugins"
        plugin = copy_plugin(PLUGIN, plugins / "screen-spec")
        sibling = copy_spec_loop(plugins / "spec-loop")
        results = run_cases(plugin, sibling, tmp_path / "work")
        for case in CASES:
            problems = case_problems(case, results[case[0]])
            check(f"試料が期待どおりでない: {case[0]}", not problems, "; ".join(problems) + f" ／ {results[case[0]]['out'][-300:]}")

        # 同じ入力から同じバイト
        again = run_one(plugin, sibling, tmp_path / "again", CASES[0])
        first = run_one(plugin, sibling, tmp_path / "again2", CASES[0])
        check("同じ入力から同じバイトにならない（コミットの SHA を伏せて比べる）",
              again["page"] is not None and _strip_commits(again["page"]) == _strip_commits(first["page"] or ""))

        module = load(plugin / "scripts" / TARGET)
        docs = {"mock": (REFS / "mock.md").read_text(encoding="utf-8"), "tables": (REFS / "tables.md").read_text(encoding="utf-8")}
        problems = reference_mismatches(module, docs["mock"], docs["tables"])
        check("本体の定数が references と一致しない", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if docs["mock"].count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {docs['mock'].count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(module, docs["mock"].replace(before, after), docs["tables"])))

        source = (PLUGIN / "scripts" / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            root = tmp_path / f"mut{index}" / "plugins"
            mutated = copy_plugin(PLUGIN, root / "screen-spec")
            copy_spec_loop(root / "spec-loop")
            (mutated / "scripts" / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            case = next(c for c in CASES if c[0] == killer)
            result = run_cases(mutated, root / "spec-loop", tmp_path / f"mutwork{index}", only=killer)[killer]
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", bool(case_problems(case, result)), result["out"][-300:])

        problems = oo_problems(plugin, tmp_path)
        check("-OO の引数なしで使い方の誤り（2）にならない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(OO_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_plugin(PLUGIN, tmp_path / f"oo-mut{index}" / "screen-spec")
            (mutated / "scripts" / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(oo_problems(mutated, tmp_path)))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(OO_MUTATIONS)} 件・references の崩し {len(REFERENCE_MUTATIONS)} 件")
    return 0


def _strip_commits(page: str) -> str:
    """コミットの SHA（試料のリポジトリごとに違う）を伏せる。"""
    return re.sub(r"[0-9a-f]{40}", "<sha>", page)


if __name__ == "__main__":
    if sys.argv[1:] == ["--browser"]:
        sys.exit(browser())
    if sys.argv[1:]:
        print("usage: python3 scripts/test-build-mock.py [--browser]", file=sys.stderr)
        sys.exit(2)
    sys.exit(main())
