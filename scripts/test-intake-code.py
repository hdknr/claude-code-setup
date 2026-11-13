#!/usr/bin/env python3
"""`intake-code.py`（spec-loop の、持ち込まれた動くコードから要求の候補を起こす取り込みの段。#998）の回帰テスト。

    python3 scripts/test-intake-code.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-infra-csv.py` と同じ形。

**このテストは実環境を触らない。** 正本・取り込む元・`origin`（bare）はすべて一時ディレクトリに本物の git リポジトリで作り
（PR は bare の `origin` の `refs/pull/7/head` に置く）、`HOME`・`GIT_CONFIG_GLOBAL` を一時ディレクトリに差し替える——本物の GitHub には届かない。
**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる**（正本リポジトリで単体で動くこと）。
足した表には、写した**本物の `check-qa-csv.py`** を CLI で走らせる。

**守ること**（各行に変異が 1 つ以上ある——下の `MUTATIONS`）:

- `snapshot` は PR（`refs/pull/<n>/head`）・ブランチ・ディレクトリのどれも写し、写した前後で正本の参照・HEAD・`git status` が変わらない（マージしない）
- `snapshot` はディレクトリの `.git` を写さない
- `snapshot` は出力先が正本の中（`build/` の下でない）か空でなければ 2 で止まり、何も写さない
- `rows` の行は `確認中`・`未回答`・`—` で、回答・状態・反映先の鍵を書いた JSON は 1 で何も書かない
- `rows` の行の質問には「コードではこうなっていた」と該当箇所（パス:行）が付き、在らないファイル・範囲の外の行は 1
- `rows` の起票元は `要求確定（取り込み・<種類>。<出所>）`
- `rows` の番号は `Q-R-` の、全部の版を通した最大の次（ほかの印は数えない）で、作業中の版の表に書く
- `rows` が書いた表は本物の `check-qa-csv.py` を通る。`--dry-run` は書かない
- スキルが書いた食い違いは、正本のファイルに在る引用だけを通す（無い引用・無いファイルは 1）
- 基盤要件のホスティング環境・DBMS・言語は、決定と違う種類の目印があれば食い違い（3）、同じ種類だけなら 0 件（0）。読み飛ばすディレクトリ（`node_modules`）は照らさない

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import ast
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "intake-code.py"
HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
QA_V1 = HEADER + "Q-R-004,要求確定,既存の質問ですか？,A: はい / B: いいえ,A,理由,A（業務部が回答）,決定表 1 行目,反映済み,\n" \
                 "Q-S-009,仕様レビュー,別の印の質問ですか？,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n"
INFRA = "項目,決定,理由,費用への影響,水準,根拠,状態\n言語,{lang},保守,なし,,Q-R-004,決定\nDBMS,{db},費用,なし,,Q-R-004,決定\n" \
        "ホスティング環境,{host},既存,なし,,Q-R-004,決定\n"
DECISION = "会員,金額,割引\nゴールド,10000 円以上,5%\n"
MAIN_PY = 'import boto3\nimport psycopg2\n\ndef discount(member, amount):\n    if member == "gold" and amount >= 5000:\n        return 0.05\n    return 0\n'

GOOD = {
    "candidates": [{
        "kind": "業務ルール", "question": "ゴールド会員の割引は、いくら以上の注文から付けますか？", "options": ["5000 円以上", "10000 円以上"],
        "recommend": "B", "reason": "正本の決定表が 10000 円以上", "code_behavior": "5000 円以上で 5% 割引していた",
        "code": [{"path": "app/main.py", "line": 5}]}],
    "findings": [{
        "summary": "ゴールド会員の割引の下限が違う", "canon": "shared/decision_table.csv", "canon_quote": "ゴールド,10000 円以上",
        "code_behavior": "5000 円以上で割引", "code": [{"path": "app/main.py", "line": 5}]}],
}


def variant(**change) -> dict:
    data = json.loads(json.dumps(GOOD))
    for key, value in change.items():
        if key.startswith("c_"):
            data["candidates"][0][key[2:]] = value
        elif key.startswith("f_"):
            data["findings"][0][key[2:]] = value
        else:
            data[key] = value
    return data


failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


class Env:
    def __init__(self, work: Path, scripts: Path):
        self.work, self.scripts = work, scripts
        home = work / "home"
        home.mkdir(exist_ok=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update({"HOME": str(home), "GIT_CONFIG_GLOBAL": str(home / "gitconfig"), "GIT_CONFIG_NOSYSTEM": "1",
                         "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"})
        (home / "gitconfig").write_text("[init]\n\tdefaultBranch = main\n", encoding="utf-8")
        self.n = 0

    def git(self, cwd: Path, *args: str) -> str:
        proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=self.env)
        if proc.returncode != 0:
            raise RuntimeError(f"git {args}: {proc.stderr}")
        return proc.stdout

    def run(self, *args: str) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, "-I", str(self.scripts / TARGET), *args], capture_output=True, text=True,
                              env=self.env, cwd=self.work)
        return proc.returncode, proc.stdout + proc.stderr

    def fresh(self, name: str) -> Path:
        self.n += 1
        return self.work / f"{name}-{self.n}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixtures(e: Env) -> dict[str, Path]:
    """取り込む元（proto。node_modules は commit しない）・bare の origin（refs/pull/7/head・feature/x）・正本の雛形。"""
    proto = e.work / "proto"
    write(proto / "app" / "main.py", MAIN_PY)
    write(proto / ".gitignore", "node_modules/\n")
    e.git(proto.parent, "init", "-q", str(proto))
    e.git(proto, "add", "-A")
    e.git(proto, "commit", "-qm", "proto")
    write(proto / "node_modules" / "@google-cloud" / "storage" / "index.js", "require('@google-cloud/storage')\n")
    origin = e.work / "origin.git"
    e.git(e.work, "init", "-q", "--bare", str(origin))
    e.git(proto, "push", "-q", str(origin), "HEAD:refs/pull/7/head", "HEAD:refs/heads/feature/x")
    canon = e.work / "canon"
    write(canon / "docs" / "v1" / "shared" / "qa.csv", QA_V1)
    write(canon / "docs" / "v1" / "shared" / "infra.csv", INFRA.format(lang="Python 3.12", db="PostgreSQL 16", host="Google Cloud（東京）"))
    write(canon / "docs" / "v1" / "shared" / "decision_table.csv", DECISION)
    e.git(canon.parent, "init", "-q", str(canon))
    e.git(canon, "add", "-A")
    e.git(canon, "commit", "-qm", "canon")
    e.git(canon, "remote", "add", "origin", str(origin))
    e.git(canon, "push", "-q", "origin", "main")
    e.git(canon, "fetch", "-q", "origin")
    return {"proto": proto, "canon": canon}


def state(e: Env, repo: Path) -> str:
    return "\n".join([e.git(repo, "for-each-ref"), e.git(repo, "rev-parse", "HEAD"), e.git(repo, "symbolic-ref", "HEAD"),
                      e.git(repo, "status", "--porcelain", "--untracked-files=all")])


def canon_copy(e: Env, fx: dict[str, Path], infra: dict[str, str] | None = None, v2: str | None = None) -> Path:
    canon = e.fresh("canon")
    shutil.copytree(fx["canon"], canon, symlinks=True)
    if infra is not None:
        write(canon / "docs" / "v1" / "shared" / "infra.csv", INFRA.format(**infra))
    if v2 is not None:
        write(canon / "docs" / "v2" / "shared" / "qa.csv", v2)
    return canon


def snap_of(e: Env, fx: dict[str, Path], source: str = "pr:7") -> Path:
    out = e.fresh("snap")
    code, text = e.run("snapshot", str(fx["canon"]), source, str(out))
    if code != 0:
        raise RuntimeError(f"試料の snapshot が失敗した: {text}")
    return out


def rows_case(e: Env, fx: dict[str, Path], data, *, infra=None, v2=None, source="pr:7", dry=False, snap=None):
    canon = canon_copy(e, fx, infra, v2)
    snap = snap or snap_of(e, fx, source)
    path = e.fresh("c").with_suffix(".json")
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False), encoding="utf-8")
    target = canon / "docs" / ("v2" if v2 is not None else "v1") / "shared" / "qa.csv"
    before = target.read_text(encoding="utf-8")
    code, out = e.run("rows", str(canon), str(path), str(snap), *(["--dry-run"] if dry else []))
    after = target.read_text(encoding="utf-8")
    added = [r for r in csv.DictReader(io.StringIO(after)) if r["No"] not in {x["No"] for x in csv.DictReader(io.StringIO(before))}]
    return code, out, before, after, added, target


def qa_check(e: Env, target: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-I", str(e.scripts / "check-qa-csv.py"), str(target)], capture_output=True, text=True, env=e.env)
    return proc.returncode, proc.stdout + proc.stderr


# ---------------------------------------------------------------- 試料（問題があれば文字列を返す）

def case_snapshot_pr(e, fx):
    out = e.fresh("snap")
    before = state(e, fx["canon"])
    code, text = e.run("snapshot", str(fx["canon"]), "pr:7", str(out))
    if code != 0:
        return f"exit={code}: {text}"
    if state(e, fx["canon"]) != before:
        return "正本の参照・HEAD・status が変わった"
    meta = json.loads((out / ".intake-source.json").read_text(encoding="utf-8"))
    if not (out / "app" / "main.py").is_file() or not meta["label"].startswith("PR #7（"):
        return f"写せていない: {sorted(p.name for p in out.iterdir())} {meta}"
    if (out / "node_modules").exists():
        return "commit していない node_modules が PR の写しにある"
    return None


def case_snapshot_branch(e, fx):
    out = e.fresh("snap")
    before = state(e, fx["canon"])
    code, text = e.run("snapshot", str(fx["canon"]), "branch:origin/feature/x", str(out))
    if code != 0:
        return f"exit={code}: {text}"
    if state(e, fx["canon"]) != before:
        return "正本の参照・HEAD・status が変わった"
    meta = json.loads((out / ".intake-source.json").read_text(encoding="utf-8"))
    return None if (out / "app" / "main.py").is_file() and meta["label"].startswith("ブランチ origin/feature/x（") else f"写せていない: {meta}"


def case_snapshot_dir(e, fx):
    out = e.fresh("snap")
    before = state(e, fx["canon"])
    code, text = e.run("snapshot", str(fx["canon"]), f"dir:{fx['proto']}", str(out))
    if code != 0:
        return f"exit={code}: {text}"
    if state(e, fx["canon"]) != before:
        return "正本の参照・HEAD・status が変わった"
    if (out / ".git").exists():
        return ".git を写した"
    return None if (out / "app" / "main.py").is_file() else "写せていない"


def case_snapshot_build(e, fx):
    canon = canon_copy(e, fx)
    out = canon / "build" / "intake" / "x"
    code, text = e.run("snapshot", str(canon), "pr:7", str(out))
    return None if code == 0 and (out / "app" / "main.py").is_file() else f"exit={code}: {text}"


def case_snapshot_into_docs(e, fx):
    canon = canon_copy(e, fx)
    out = canon / "docs" / "v1" / "intake"
    code, text = e.run("snapshot", str(canon), "pr:7", str(out))
    if code != 2 or out.exists():
        return f"exit={code}・作った={out.exists()}: {text}"
    return None if "正本の中に置かない" in text else text


def case_snapshot_nonempty(e, fx):
    out = e.fresh("snap")
    write(out / "old.txt", "前の取り込み\n")
    code, text = e.run("snapshot", str(fx["canon"]), "pr:7", str(out))
    if code != 2 or (out / "app").exists():
        return f"exit={code}: {text}"
    return None if "空でない" in text else text


def case_snapshot_bad_source(e, fx):
    for source in ("pr:abc", "branch:-x", "zip:a", "pr:"):
        code, text = e.run("snapshot", str(fx["canon"]), source, str(e.fresh("snap")))
        if code != 2:
            return f"{source}: exit={code}: {text}"
    return None


def case_rows_good(e, fx):
    code, out, before, after, added, target = rows_case(e, fx, GOOD)
    if code != 3:
        return f"exit={code}（期待 3）: {out}"
    if len(added) != 1:
        return f"足した行が {len(added)}: {after}"
    row = added[0]
    expect = {"No": "Q-R-005", "回答": "未回答", "反映先": "—", "状態": "確認中", "推奨": "B",
              "選択肢": "A: 5000 円以上 / B: 10000 円以上"}
    for k, v in expect.items():
        if row[k] != v:
            return f"{k} が {row[k]!r}（期待 {v!r}）"
    if not row["起票元"].startswith("要求確定（取り込み・業務ルール。PR #7（") or not row["起票元"].endswith("））"):
        return f"起票元が {row['起票元']!r}"
    if "（コードではこうなっていた: 5000 円以上で 5% 割引していた。app/main.py:5）" not in row["質問"]:
        return f"質問が {row['質問']!r}"
    rc, text = qa_check(e, target)
    if rc != 0:
        return f"check-qa-csv.py が通らない: {text}"
    for needle in ("食い違い: 2 件", "持ち込まれたコードは AWS を前提にしている（boto3: app/main.py:1）",
                   "正本 shared/decision_table.csv「ゴールド,10000 円以上」"):
        if needle not in out:
            return f"出力に {needle!r} が無い: {out}"
    return None


def case_rows_control(e, fx):
    """陽性対照の相手: 基盤要件がコードと同じ種類で、スキルの食い違いも無ければ 0 件。ディレクトリの写しの node_modules も照らさない。"""
    snap = snap_of(e, fx, f"dir:{fx['proto']}")
    code, out, *_ = rows_case(e, fx, variant(findings=[]), infra={"lang": "Python 3.12", "db": "PostgreSQL 16", "host": "AWS（東京）"}, snap=snap)
    if code != 0 or "食い違い: 0 件" not in out:
        return f"exit={code}（期待 0）: {out}"
    return None


def case_rows_db(e, fx):
    code, out, *_ = rows_case(e, fx, variant(findings=[]), infra={"lang": "Python 3.12", "db": "MySQL 8", "host": "AWS"})
    return None if code == 3 and "基盤要件のDBMS: 正本は「MySQL 8」" in out and "PostgreSQL を前提" in out else f"exit={code}: {out}"


def case_rows_language(e, fx):
    code, out, *_ = rows_case(e, fx, variant(findings=[]), infra={"lang": "Ruby 3.3", "db": "PostgreSQL 16", "host": "AWS"})
    return None if code == 3 and "基盤要件の言語: 正本は「Ruby 3.3」" in out and "Python で書かれている" in out else f"exit={code}: {out}"


def case_rows_unreadable_value(e, fx):
    code, out, *_ = rows_case(e, fx, variant(findings=[]), infra={"lang": "Python", "db": "PostgreSQL", "host": "自社のデータセンター"})
    return None if code == 0 and "「自社のデータセンター」から種類を読めない——照らしていない" in out else f"exit={code}: {out}"


def case_rows_answer(e, fx):
    for key in ("answer", "状態", "反映先"):
        code, out, before, after, *_ = rows_case(e, fx, variant(**{f"c_{key}": "B"}))
        if code != 1 or before != after or "書けない" not in out:
            return f"{key}: exit={code}・書いた={before != after}: {out}"
    return None


def case_rows_bad_code(e, fx):
    for loc, needle in (({"path": "app/none.py", "line": 1}, "スナップショットに無いファイル"),
                        ({"path": "app/main.py", "line": 99}, "は 7 行しかない"),
                        ({"path": "../canon/docs/v1/shared/qa.csv", "line": 1}, "`..` を使わない")):
        code, out, before, after, *_ = rows_case(e, fx, variant(c_code=[loc]))
        if code != 1 or before != after or needle not in out:
            return f"{loc}: exit={code}: {out}"
    code, out, *_ = rows_case(e, fx, variant(c_code=[]))
    return None if code == 1 and "1 つも無い" in out else f"code が空: exit={code}: {out}"


def case_rows_bad_finding(e, fx):
    code, out, before, after, *_ = rows_case(e, fx, variant(f_canon_quote="ゴールド,3000 円以上"))
    if code != 1 or before != after or "`canon_quote` が shared/decision_table.csv に無い" not in out:
        return f"引用: exit={code}: {out}"
    code, out, *_ = rows_case(e, fx, variant(f_canon="shared/none.csv"))
    return None if code == 1 and "正本（重ね合わせた全体）に無いファイル" in out else f"ファイル: exit={code}: {out}"


def case_rows_bad_option(e, fx):
    code, out, before, after, *_ = rows_case(e, fx, variant(c_options=["5000 円 / 以上", "10000 円以上"]))
    return None if code == 1 and before == after and "` / ` を含めない" in out else f"exit={code}: {out}"


def case_rows_duplicate(e, fx):
    code, out, *_ = rows_case(e, fx, variant(c_question="既存の質問ですか？"))
    return None if code == 1 and "同じ質問が既にある" in out else f"exit={code}: {out}"


def case_rows_dry(e, fx):
    code, out, before, after, *_ = rows_case(e, fx, GOOD, dry=True)
    return None if code == 3 and before == after and "書いていない（--dry-run）" in out and "Q-R-005" in out else f"exit={code}: {out}"


def case_rows_v2(e, fx):
    code, out, before, after, added, target = rows_case(
        e, fx, variant(findings=[]), v2=HEADER + "Q-R-002,要求確定,v2 の質問ですか？,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n")
    if code != 3 or [r["No"] for r in added] != ["Q-R-005"]:
        return f"exit={code}・足した={[r['No'] for r in added]}: {out}"
    return None if qa_check(e, target)[0] == 0 else "check-qa-csv.py が通らない"


def case_rows_broken_table(e, fx):
    canon = canon_copy(e, fx)
    write(canon / "docs" / "v1" / "shared" / "qa.csv", HEADER + "Q-R-001,要求確定,壊れた行,A のみ,A,理由,未回答,—,確認中,\n")
    path = e.fresh("c").with_suffix(".json")
    path.write_text(json.dumps(GOOD, ensure_ascii=False), encoding="utf-8")
    code, out = e.run("rows", str(canon), str(path), str(snap_of(e, fx)))
    # 壊れた表は版の重ね合わせ（merge-versions.py）か、作業中の版の表の検査のどちらかが止める——どちらでも 2 で何も書かない
    return None if code == 2 and "選択肢が 2 つ未満" in out and "何も書いていない" in out else f"exit={code}: {out}"


def case_rows_not_snapshot(e, fx):
    code, out, *_ = rows_case(e, fx, GOOD, snap=fx["proto"])
    return None if code == 2 and "スナップショットでない" in out else f"exit={code}: {out}"


CASES = {f.__name__[5:]: f for f in [
    case_snapshot_pr, case_snapshot_branch, case_snapshot_dir, case_snapshot_build, case_snapshot_into_docs, case_snapshot_nonempty,
    case_snapshot_bad_source, case_rows_good, case_rows_control, case_rows_db, case_rows_language, case_rows_unreadable_value,
    case_rows_answer, case_rows_bad_code, case_rows_bad_finding, case_rows_bad_option, case_rows_duplicate, case_rows_dry,
    case_rows_v2, case_rows_broken_table, case_rows_not_snapshot,
]}

# (名前, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("PR を正本のブランチにして取る", 'f"refs/pull/{ref}/head")', 'f"refs/pull/{ref}/head:refs/heads/pr-{ref}")', "snapshot_pr"),
    ("ディレクトリの .git も写す", 'ignore=shutil.ignore_patterns(".git")', "ignore=None", "snapshot_dir"),
    ("正本の中にも写す", "if inside(out, root) and not inside(out, root / BUILD):", "if False:", "snapshot_into_docs"),
    ("build/ の下も断る", "if inside(out, root) and not inside(out, root / BUILD):", "if inside(out, root):", "snapshot_build"),
    ("空でなくても写す", "if out.exists() and (not out.is_dir() or any(out.iterdir())):", "if False:", "snapshot_nonempty"),
    ("行を反映済みにする", '"状態": PENDING', '"状態": "反映済み"', "rows_good"),
    ("推奨を回答に写す", '"回答": qa.NO_ANSWER', '"回答": recommend', "rows_good"),
    ("回答の鍵を黙って受ける", "    confirming = sorted(k for k in obj if k in CONFIRMING)", "    confirming = []", "rows_answer"),
    ("質問に該当箇所を足さない", '"質問": f"{question}（コードではこうなっていた: {behavior}。{\'、\'.join(places)}）"', '"質問": question', "rows_good"),
    ("無いファイルを見ない", "        if path.is_symlink() or not path.is_file():", "        if False:", "rows_bad_code"),
    ("行の範囲を見ない", "        if line > len(lines):", "        if False:", "rows_bad_code"),
    ("起票元に取り込みと書かない", 'f"{SOURCE_NAME}（取り込み・{kind}。{label}）"', "SOURCE_NAME", "rows_good"),
    ("ほかの印の番号も数える", 'if m and m["mark"] == MARK:', "if m:", "rows_good"),
    ("作業中の版だけ数える", "    for _, root in versions:", "    for _, root in versions[-1:]:", "rows_v2"),
    ("--dry-run でも書く", "    if dry_run:", "    if False:", "rows_dry"),
    ("引用を確かめない", "    elif quote and squash(quote) not in squash(canon[path].decode(\"utf-8\", \"replace\")):", "    elif False:", "rows_bad_finding"),
    ("正本に無いファイルを見ない", "    if not isinstance(path, str) or path not in canon:", "    if False:", "rows_bad_finding"),
    ("選択肢の区切りを見ない", ' or qa.OPTION_SEPARATOR in option:', ":", "rows_bad_option"),
    ("重複を見ない", "                if squash(c[\"question\"]) in asked:", "                if False:", "rows_duplicate"),
    ("決定と同じ種類も食い違いにする", "            if name == mine[0]:\n                continue\n", "", "rows_control"),
    ("決定の値を読まずに AWS とする", "mine = [name for name, word, _ in families if word.search(value)]", "mine = [families[0][0]]", "rows_good"),
    ("node_modules も照らす", 'if d not in SKIP_DIRS and not d.startswith(".")', 'if not d.startswith(".")', "rows_control"),
    ("言語を照らさない", "        elif not any(rel.suffix in mine[0] for rel in files):", "        elif False:", "rows_language"),
    ("食い違いがあっても 0", "    return (3 if findings else 0), report", "    return 0, report", "rows_db"),
    ("DBMS の目印を持たない", '         re.compile(r"\\bpsycopg2?\\b|\\basyncpg\\b|', '         re.compile(r"\\bnever-matches\\b|', "rows_db"),
    ("出所の印が無くても読む", '        raise Stop(f"{snap}: スナップショットでない（{SOURCE_FILE} が読めない——snapshot で作る）") from None', '        label = "?"', "rows_not_snapshot"),
]


def docstring_rules() -> int:
    doc = ast.get_docstring(ast.parse(Path(__file__).read_text(encoding="utf-8"))) or ""
    block = doc.split("**守ること**", 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


def main() -> int:
    if shutil.which("git") is None:
        print("git が無い——判定していない", file=sys.stderr)
        return 2
    work = Path(tempfile.mkdtemp(prefix="test-intake-code-")).resolve()
    assert REAL_REPO not in work.parents
    real_state = subprocess.run(["git", "-C", str(REAL_REPO), "status", "--porcelain"], capture_output=True, text=True).stdout
    try:
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        e = Env(work, scripts)
        fx = build_fixtures(e)

        print("正しい本体")
        for name, case in CASES.items():
            try:
                problem = case(e, fx)
            except Exception as ex:  # noqa: BLE001
                problem = f"例外: {type(ex).__name__}: {ex}"
            check(f"試料: {name}", problem is None, problem or "")

        print("変異テスト")
        pristine = (scripts / TARGET).read_text(encoding="utf-8")
        for name, old, new, target in MUTATIONS:
            count = pristine.count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            (scripts / TARGET).write_text(pristine.replace(old, new), encoding="utf-8")
            try:
                try:
                    problem = CASES[target](e, fx)
                except Exception as ex:  # noqa: BLE001
                    problem = f"例外: {ex}"
            finally:
                (scripts / TARGET).write_text(pristine, encoding="utf-8")
            check(f"変異が素通りした: {name}（試料: {target}）", problem is not None)
        rules = docstring_rules()
        check("docstring の「守ること」の各行に変異がある（変異の数 ≥ 行の数）", len(MUTATIONS) >= rules, f"変異 {len(MUTATIONS)}・行 {rules}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    after = subprocess.run(["git", "-C", str(REAL_REPO), "status", "--porcelain"], capture_output=True, text=True).stdout
    check("このリポジトリの作業ツリーを変えていない", real_state == after)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
