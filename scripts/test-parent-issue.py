#!/usr/bin/env python3
"""`parent-issue.py`（親 Issue の一覧から台帳を作る）の回帰テスト。

    python3 scripts/test-parent-issue.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/`）。
`test-ledger.py` と同じ形——**`dev-loop` はどのリポジトリでも使えるプラグイン**なので、
本体は対象リポジトリの `scripts/` に在ることを当てにできない。

**このテストは実環境を触らない。** 毎回テンポラリに本物の git リポジトリを作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。本体は台帳を cwd のメインの作業ツリーの `.claude/plans/` に書くので、
**歯止めが無いと、テストがこのリポジトリ自身に台帳を書く。** 本文は `--body-file` で渡し、
`gh` を通る経路は `PATH` の先頭に置いた偽の `gh` で当てる——**本物の GitHub には届かない。**
台帳は**本物の `ledger.py`** を子プロセスで呼んで作る（台帳の形を写さない）。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が緑であること。本体の docstring の「守る」の行数だけ変異を当て
（**テスト自身に数えさせる**）、終了コードも docstring の表と突き合わせる。
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "parent-issue.py"
LEDGER = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "ledger.py"

failures: list[str] = []

BASIC = """説明の段落（ここは読まない）。
- [ ] #14 (depends: #12, #13)
- [ ] #13 ログイン画面 (depends: #12)
* [ ] #12
- [x] #11
+ [ ] #15 (depends: #11)
- [ ] 受入基準: 依存の順に回る
- [ ] 16 (depends: #12)
- [ ] #0

```markdown
- [ ] #77
```
"""

# 拒む形（C3・C4）。どれも 3 で、台帳を作らない
REJECTED = {
    "依存の中身が #番号 でない": "- [ ] #12\n- [ ] #13 (depends: 12)\n",
    "依存の中身が空": "- [ ] #12\n- [ ] #13 (depends: )\n",
    "(depends:) が 2 つ": "- [ ] #12\n- [ ] #14\n- [ ] #13 (depends: #12) (depends: #14)\n",
    "同じ番号が 2 行": "- [ ] #12\n- [ ] #12\n",
    "未チェックと済みで同じ番号": "- [ ] #12\n- [x] #12\n",
    "自己依存": "- [ ] #12 (depends: #12)\n",
    "一覧に無い依存先": "- [ ] #13 (depends: #12)\n",
    "循環": "- [ ] #12 (depends: #13)\n- [ ] #13 (depends: #12)\n",
    "未チェックが 0 件": "- [x] #12\n本文だけ\n",
    "チェックリストの行が無い": "本文だけ\n- 箇条書き\n",
    "線の項目が一覧に無い": "- [ ] #12\ncruise: 速さ = 速い\n",
    "線の値が一覧に無い": "- [ ] #12\ncruise: 仕様の穴 = 決める\n",
    "線の値が空": "- [ ] #12\ncruise: 直す線 =\n",
    "同じ線が 2 行": "- [ ] #12\ncruise: 直す線 = 既定\ncruise: 直す線 = 広げる\n",
    "depends（括弧なし）": "- [ ] #12\n- [ ] #13 depends #12\n",
    "依存:（日本語）": "- [ ] #12\n- [ ] #13 依存: #12\n",
    "Depends（大文字）": "- [ ] #12\n- [ ] #13 (Depends: #12)\n",
    "依存の語だけ（#番号 なし）": "- [ ] #12\n- [ ] #13 ログイン画面に依存する\n",
    "題に #番号（blocked by）": "- [ ] #12\n- [ ] #13 (blocked by #12)\n",
    "閉じていないコードフェンス": "- [ ] #12\n```\n- [ ] #13\n",
    "閉じていない HTML コメント": "- [ ] #12\n<!--\n- [ ] #13\n",
}

# 線（C13・#458）。フェンス・コメントの中は読まない。引用・形の違う行は読み飛ばした行に出る
LINED = """cruise: 仕様の穴 = 推奨で決めて起票
  cruise: 直す線 = 既定
cruise: 本番反映 = する
> cruise: マージ = 関門を通ればマージ
- cruise: 実機確認 = Refs でマージ
Cruise: マージ
```
cruise: マージ = 関門を通ればマージ
```
<!--
cruise: 実機確認 = Refs でマージ
-->
"""

# 読む範囲（C3・C5）: 違う印で閉じないフェンス・インデントされたフェンス・長いフェンスの中の短い印・
# 番号つきリスト・引用・HTML コメント・- で始まる題
EXTRA = """```
~~~
- [ ] #99
```
- [ ] #12
- 例:
    ```
    - [ ] #98
    ```
````markdown
```
- [ ] #97
```
````
1. [ ] #13 (depends: #12)
> - [ ] #96
<!--
- [ ] #95
-->
- [ ] #14 -wip <!-- - [ ] #94 -->
```markdown
    ```
    - [ ] #93
    ```
```
```gh``` を使う
- [ ] #15
```
- [ ] #92
```
- [ ] #16 `<!--` と `-->`
- [ ] #17
- [ ] #19 a <!-- b
```<!--
x
```
- [ ] #20
<!--
- [ ] #91
-->
```
- [ ] #90
\t```
- [ ] #89
```
<!-->
- [ ] #22
<!--
`-->`
- [ ] #23
"""


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"parent_{id(script)}_{script.stat().st_mtime_ns}", script)
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


def isolate_env(home: Path) -> None:
    """`GIT_*` を外し、`HOME` と git の設定を差し替える（`test-ledger.py` と同じ理由）。
    偽の `gh` を置く `bin` を `PATH` の先頭に足す——**本物の `gh` には届かない。**"""
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[key]
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    (home / "bin").mkdir()
    os.environ.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
                      PATH=f"{home / 'bin'}{os.pathsep}{os.environ['PATH']}")


def fake_gh(home: Path, body: str | None) -> None:
    """偽の `gh`。`body` が None なら失敗し、そうでなければ受けた引数を記録して本文を出す。"""
    gh = home / "bin" / "gh"
    (home / "gh-args").unlink(missing_ok=True)
    if body is None:
        gh.write_text("#!/bin/sh\necho 'gh: 偽の失敗' >&2\nexit 1\n", encoding="utf-8")
    else:
        (home / "gh-body").write_text(body, encoding="utf-8")
        gh.write_text(f'#!/bin/sh\necho "$@" > "{home}/gh-args"\ncat "{home}/gh-body"\n', encoding="utf-8")
    gh.chmod(0o755)


def run(mod, argv, cwd, ledger_script=LEDGER):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = mod.main(argv, cwd=str(cwd), ledger_script=ledger_script)
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            return ("例外", type(exc).__name__, "")
    return (rc, out.getvalue(), err.getvalue())


def ledger(cwd, *args):
    proc = subprocess.run([sys.executable, str(LEDGER), *args], cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.split()


def scenario(mod, tmp: Path, tag: str) -> dict:
    """全試料を 1 本のリポジトリで走らせ、観測を辞書で返す。**変異の前後で同じ関数を使う。**"""
    home = tmp / "home"
    root = tmp / f"repo-{tag}"
    assert_not_real_repo(root)
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    plans = root / ".claude" / "plans"
    o = {}

    def body(name, text):
        p = tmp / f"{tag}-{name}.md"
        p.write_text(text, encoding="utf-8")
        return str(p)

    def show(name, text):
        rc, out, err = run(mod, ["show", "50", "--body-file", body(name, text)], root)
        m = re.search(r"^指紋: ([0-9a-f]+)$", str(out), re.M)
        return rc, out, m.group(1) if m else ""

    def ledgers():
        return sorted(p.name for p in plans.glob("*")) if plans.is_dir() else []

    # C1・C2・C5: 取り出し
    rc, out, dig = show("basic", BASIC)
    o["show"] = (rc, out)
    o["指紋"] = dig

    # C3・C4: 拒む形。show も apply も 3 で、台帳を作らない。**apply は書式で拒んだこと**を見る
    # ——指紋は 0…0 なので、書式を通してしまっても指紋の不一致で 3 になる（それと見分ける）
    for name, text in REJECTED.items():
        rc_show = show(name, text)[0]
        rc_apply, _, err = run(mod, ["apply", "51", "--body-file", body(name, text), "--digest", "0" * 12], root)
        o[f"拒む {name}"] = (rc_show, rc_apply, "指紋が違う" in str(err), ledgers())

    # C3・C5: 読む範囲。apply で台帳の題まで見る（- で始まる題が ledger.py に値として届く）
    rc, out, dig_extra = show("extra", EXTRA)
    o["読む範囲"] = (rc, re.findall(r"^#(\d+)\t依存: ([^\t]*)\t(.*)$", str(out), re.M),
                   str(out).split("読み飛ばした行（#番号 で始まらない）:\n")[-1].split("線（cruise: の行）:")[0].strip())
    o["読む範囲の apply"] = run(mod, ["apply", "53", "--body-file", body("extra2", EXTRA), "--digest", dig_extra],
                              root)[0]
    try:
        data = json.loads((plans / "cruise-issue-53.json").read_text(encoding="utf-8"))
        o["読む範囲の台帳"] = [(i["number"], i["deps"], i["title"]) for i in data["issues"]]
    except (OSError, ValueError, KeyError):
        o["読む範囲の台帳"] = None
    (plans / "cruise-issue-53.json").unlink(missing_ok=True)

    # C6: 指紋が違えば作らない（show の後に本文を書き換えた）
    changed = BASIC.replace("#13 ログイン画面", "#13 書き換えた題")
    o["指紋の不一致"] = (run(mod, ["apply", "50", "--body-file", body("changed", changed), "--digest", dig], root)[0],
                       ledgers())

    # C8: 作った台帳に ledger.py が依存どおりに答える。本文の順は依存先が後（#14 が先頭）
    o["apply"] = run(mod, ["apply", "50", "--body-file", body("basic2", BASIC), "--digest", dig], root)[0]
    o["台帳"] = ledgers()
    o["next(初め)"] = ledger(root, "next", "issue-50")
    ledger(root, "set", "issue-50", "12", "state=merged")
    o["next(#12 がマージ済み)"] = ledger(root, "next", "issue-50")
    try:
        data = json.loads((plans / "cruise-issue-50.json").read_text(encoding="utf-8"))
        o["台帳の中身"] = [(i["number"], i["deps"], i["title"]) for i in data["issues"]]
    except (OSError, ValueError, KeyError):
        o["台帳の中身"] = None

    # C7: 2 度目は作り直さず、親 Issue にあって台帳に無いものを名指しする
    before = (plans / "cruise-issue-50.json").read_bytes() if o["台帳"] else None
    grown = BASIC + "- [ ] #16 (depends: #15)\n"
    _, _, dig2 = show("grown", grown)
    rc, _, err = run(mod, ["apply", "50", "--body-file", body("grown2", grown), "--digest", dig2], root)
    o["2 度目"] = (rc, "#16" in str(err), before is not None and (plans / "cruise-issue-50.json").read_bytes() == before)

    # C9: ledger.py が add で失敗したら、作った台帳を消す（path と init は本物に任せる）
    fake = tmp / f"{tag}-ledger.py"
    fake.write_text(
        "import importlib.util, subprocess, sys\n"
        f"spec = importlib.util.spec_from_file_location('real_ledger', {str(LEDGER)!r})\n"
        "real = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(real)\nLINES = real.LINES\n"
        "if __name__ == '__main__':\n"
        "    if sys.argv[1] == 'add' and sys.argv[3] == '13':\n        sys.exit(1)\n"
        f"    sys.exit(subprocess.run([sys.executable, {str(LEDGER)!r}, *sys.argv[1:]]).returncode)\n",
        encoding="utf-8")
    o["add の失敗"] = (run(mod, ["apply", "52", "--body-file", body("basic3", BASIC), "--digest", dig], root,
                          ledger_script=fake)[0],
                      "cruise-issue-52.json" in ledgers())

    # C13（#458）: 線。show に出る・指紋に入る・apply で台帳に残る・本番反映は無視・形の違う行は読み飛ばす
    lined = BASIC + LINED
    rc, out, dig_l = show("lined", lined)
    o["線の show"] = (rc, [l.strip() for l in str(out).split("線（cruise: の行）:\n")[-1].split("指紋:")[0].splitlines()
                          if l.strip()],
                    str(out).split("読み飛ばした行（#番号 で始まらない）:\n")[-1].split("線（cruise: の行）:")[0].strip())
    o["線は指紋に入る"] = dig_l != dig
    flipped = lined.replace("仕様の穴 = 推奨で決めて起票", "仕様の穴 = 止まる")
    o["線だけ書き換えた apply"] = (run(mod, ["apply", "54", "--body-file", body("flipped", flipped), "--digest", dig_l],
                                     root)[0], "cruise-issue-54.json" in ledgers())
    o["線の apply"] = run(mod, ["apply", "54", "--body-file", body("lined2", lined), "--digest", dig_l], root)[0]
    try:
        data = json.loads((plans / "cruise-issue-54.json").read_text(encoding="utf-8"))
        o["線の台帳"] = (data.get("lines", {}).get("values"), "指紋 " + dig_l in data.get("lines", {}).get("source", ""))
    except (OSError, ValueError, KeyError):
        o["線の台帳"] = None
    o["線なしの台帳"] = "lines" in json.loads((plans / "cruise-issue-50.json").read_text(encoding="utf-8")) \
        if (plans / "cruise-issue-50.json").is_file() else None
    # 2 度目: 本文の線が台帳と違えば名指しし、台帳は変えない
    before = (plans / "cruise-issue-54.json").read_bytes() if (plans / "cruise-issue-54.json").is_file() else None
    _, _, dig_f = show("flipped2", flipped)
    rc, _, err = run(mod, ["apply", "54", "--body-file", body("flipped3", flipped), "--digest", dig_f], root)
    o["線の 2 度目"] = (rc, "仕様の穴 = 止まる（台帳: 推奨で決めて起票）" in str(err),
                     before is not None and (plans / "cruise-issue-54.json").read_bytes() == before)
    rc, _, err = run(mod, ["apply", "54", "--body-file", body("lined3", lined), "--digest", dig_l], root)
    o["線が同じ 2 度目"] = (rc, "線が台帳の確かめた線と違う" in str(err))
    # チェックリストが無い・全部済み は別の言葉
    o["空の言い分け"] = (run(mod, ["show", "55", "--body-file", body("none", REJECTED["チェックリストの行が無い"])], root)[2],
                       run(mod, ["show", "55", "--body-file", body("alldone", REJECTED["未チェックが 0 件"])], root)[2])

    # C10: gh の失敗は 4。gh が通れば同じ本文から同じ指紋（陽性対照）
    fake_gh(home, None)
    o["gh の失敗"] = run(mod, ["show", "50"], root)[0]
    fake_gh(home, BASIC)
    rc, out, _ = run(mod, ["show", "50"], root)
    args = (home / "gh-args").read_text(encoding="utf-8").split() if (home / "gh-args").is_file() else []
    o["gh を通す"] = (rc, f"指紋: {dig}" in str(out), args)
    # git の外: apply は 4 で、何も書かない
    outside = tmp / f"outside-{tag}"
    outside.mkdir()
    o["git の外"] = (run(mod, ["apply", "50", "--body-file", body("basic4", BASIC), "--digest", dig], outside)[0],
                    sorted(p.name for p in outside.rglob("*")))
    # 引数
    o["引数"] = (run(mod, ["show", "x"], root)[0], run(mod, ["show", "0", "--body-file", body("b5", BASIC)], root)[0],
                run(mod, ["apply", "50", "--body-file", body("b6", BASIC)], root)[0])
    return o


# 1 件ずつ (探す文字列, 置き換え) の組。docstring の「守る」の順に 1 行 1 件。
MUTATIONS = {
    "読み飛ばした行を出さない": [
        ('            skipped.append(f"{lineno} 行目: {line.strip()}")', "            pass")],
    "引用の中も読む": [
        ('        if m.group("quote"):', "        if False:")],
    "依存の中身を見ない": [
        ("            if not DEP_LIST_RE.match(text):", "            if False:")],
    "(depends:) の外の依存らしい語を見ない": [
        ("        if SUSPECT_RE.search(outside):", "        if False:")],
    "題の #番号 を見ない": [
        ("        if REF_RE.search(outside):", "        if False:")],
    "フェンスの閉じを開きと突き合わせない": [
        ('m.group("fence")[0] == fence[0] and len(m.group("fence")) >= len(fence)', "True")],
    "閉じの深さを見ない": [
        (' and width(m.group("indent")) <= indent + 3', "")],
    "タブを 1 桁と数える": [
        ("    return len(indent.expandtabs(4))", "    return len(indent)")],
    "インラインコードの ``` を開きと読む": [
        ('    if not m or (m.group("fence")[0] == "`" and "`" in m.group("info")):', "    if not m:")],
    "閉じていないフェンスを通す": [
        ("    if fence:\n        raise", "    if False:\n        raise")],
    "HTML コメントの中も読む": [
        ("        line, in_comment = visible(line, in_comment)", "        pass")],
    "インラインコードの <!-- をコメントと読む": [
        ('    masked = CODE_RE.sub(lambda m: " " * len(m.group(0)), line)', "    masked = line")],
    "開いたコメントの --> をインラインコードの形では閉じと読まない": [
        ('        return "", line.find("-->") < 0', '        return "", masked.find("-->") < 0')],
    "行の途中で閉じない <!-- をコメントと読む": [
        ('                if line[:start].strip() == "":', "                if True:")],
    "閉じていない HTML コメントを通す": [
        ("    if in_comment:\n        raise", "    if False:\n        raise")],
    "同じ番号を通す": [
        ('        if number in done or any(i["number"] == number for i in items):', "        if False:")],
    "一覧に無い依存先を通す": [
        ("            if d not in listed and d not in done:", "            if False:")],
    "済んだ依存先を外さない": [
        ('        i["deps"] = [d for d in dict.fromkeys(i["deps"]) if d in listed]',
         '        i["deps"] = list(dict.fromkeys(i["deps"]))')],
    "本文の順のまま足す": [
        ("    return order(items)", "    return items")],
    "指紋を比べない": [
        ("    if digest(items, lines) != expected:", "    if False:")],
    "在る台帳を見ない": [
        ("    if path.exists():", "    if False:")],
    "失敗した台帳を残す": [
        ("            path.unlink(missing_ok=True)\n            raise Unknown(f\"ledger.py add", "            pass\n            raise Unknown(f\"ledger.py add")],
    "一覧に無い線を通す": [
        ("            if key not in table or value not in table[key]:", "            if key not in table:")],
    "同じ線の 2 行を通す": [
        ("            if key in lines:\n", "            if False:\n")],
    "本番反映の線を黙って落とす": [
        ('                ignored.append(f"{lineno} 行目（本番反映は広げられない）: {line.strip()}")', "                pass")],
    "形の違う cruise: の行を黙って落とす": [
        ('                skipped.append(f"{lineno} 行目（cruise: の線の形ではない）: {line.strip()}")', "                pass")],
    "指紋に線を含めない": [
        ("sorted(lines.items())]", "[]]")],
    "確かめた線を台帳に残さない": [
        ("    if lines:\n        proc = ledger(", "    if False:\n        proc = ledger(")],
    "本文の線の違いを名指ししない": [
        ("        if differ:\n", "        if False:\n")],
    "チェックリストが無いことを全部済んだと言う": [
        ("        if done:\n", "        if True:\n")],
}


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        isolate_env(tmp / "home")
        mod = load()
        o = scenario(mod, tmp, "correct")

        print("取り出し（C1・C2・C5）")
        rc, out = o["show"]
        rows = re.findall(r"^#(\d+)\t依存: ([^\t]*)\t(.*)$", str(out), re.M)
        check("show は 0", rc == 0)
        check("依存先が先に来る順・[x] は入らない・コードフェンスの #77 は入らない",
              [int(r[0]) for r in rows] == [12, 15, 13, 14])
        check("依存と題", rows == [("12", "-", ""), ("15", "-", ""), ("13", "#12", "ログイン画面"), ("14", "#12, #13", "")])
        check("指紋は 12 桁", re.fullmatch(r"[0-9a-f]{12}", o["指紋"]) is not None)
        skipped = str(out).split("読み飛ばした行（#番号 で始まらない）:\n")[-1].split("線（cruise: の行）:")[0].splitlines()
        check("#番号 で始まらない行（受入基準・# の書き忘れ・#0）は読み飛ばした行として出る（「依存」を含んでも拒まない）",
              [l.strip() for l in skipped] == ["7 行目: - [ ] 受入基準: 依存の順に回る",
                                              "8 行目: - [ ] 16 (depends: #12)", "9 行目: - [ ] #0"])

        print("\n拒む形（C3・C4）: show も apply も 3 で、台帳を作らない")
        for name in REJECTED:
            check(f"{name}（apply は指紋ではなく書式で拒む）", o[f"拒む {name}"] == (3, 3, False, []))

        print("\n読む範囲（C3・C5）")
        rc, rows, skipped_extra = o["読む範囲"]
        check("show は 0", rc == 0)
        check("フェンス（違う印・インデント・長い印・中の深い印・タブの字下げ）とコメントの中は読まない・番号つきリストと"
              "インラインコードの ```・インラインコードの <!--・行の途中で閉じない <!--・開きの行の <!-- の後ろ・<!--> の後ろは読む",
              rows == [("12", "-", ""), ("14", "-", "-wip"), ("15", "-", ""), ("16", "-", "`<!--` と `-->`"), ("17", "-", ""),
                       ("19", "-", "a <!-- b"), ("20", "-", ""), ("22", "-", ""), ("23", "-", ""), ("13", "#12", "")])
        check("引用の中の行は読み飛ばした行として出る", skipped_extra == "16 行目（引用の中）: > - [ ] #96")
        check("- で始まる題も台帳に入る（apply は 0）",
              o["読む範囲の apply"] == 0 and o["読む範囲の台帳"] == [(12, [], ""), (14, [], "-wip"), (15, [], ""), (16, [], "`<!--` と `-->`"), (17, [], ""),
                                          (19, [], "a <!-- b"), (20, [], ""), (22, [], ""), (23, [], ""), (13, [12], "")])

        print("\n指紋（C6）")
        check("書き換えた本文は 3 で、台帳を作らない", o["指紋の不一致"] == (3, []))

        print("\n台帳（C8）")
        check("apply は 0 で cruise-issue-50.json を作る", o["apply"] == 0 and o["台帳"] == ["cruise-issue-50.json"])
        check("台帳の中身（依存先が先・[x] への依存は外れる・題）",
              o["台帳の中身"] == [(12, [], ""), (15, [], ""), (13, [12], "ログイン画面"), (14, [12, 13], "")])
        check("next は依存の無い #12 と #15", o["next(初め)"] == (0, ["12", "15"]))
        check("#12 がマージ済みなら #13 も（並びは台帳に足した順）", o["next(#12 がマージ済み)"] == (0, ["15", "13"]))

        print("\n2 度目（C7）")
        check("3 で、#16 を名指しし、台帳を書き換えない", o["2 度目"] == (3, True, True))

        print("\nledger.py の失敗（C9）")
        check("4 で、作った台帳を残さない", o["add の失敗"] == (4, False))

        print("\n線（C13・#458）")
        n = BASIC.count("\n")
        check("show は 0 で、線を項目の順に出す（書いていない項目も出す）・本番反映は無視した行",
              o["線の show"][:2] == (0, ["直す線 = 既定", "仕様の穴 = 推奨で決めて起票",
                                         "実機確認: 書いていない（.claude/dev-loop.md の宣言、無ければ既定）",
                                         "マージ: 書いていない（.claude/dev-loop.md の宣言、無ければ既定）",
                                         f"無視した行: {n + 3} 行目（本番反映は広げられない）: cruise: 本番反映 = する"]))
        check("引用・リストの中・形の違う cruise: の行は読み飛ばした行に出る（フェンス・コメントの中は出ない）",
              o["線の show"][2].splitlines()[-3:] == [
                  f"  {n + 4} 行目（cruise: の線の形ではない）: > cruise: マージ = 関門を通ればマージ",
                  f"  {n + 5} 行目（cruise: の線の形ではない）: - cruise: 実機確認 = Refs でマージ",
                  f"  {n + 6} 行目（cruise: の線の形ではない）: Cruise: マージ"])
        check("線は指紋に入る", o["線は指紋に入る"])
        check("線だけ書き換えた本文の apply は 3 で、台帳を作らない", o["線だけ書き換えた apply"] == (3, False))
        check("apply は 0 で、確かめた線と指紋を出所として台帳に残す",
              o["線の apply"] == 0 and o["線の台帳"] == ({"仕様の穴": "推奨で決めて起票", "直す線": "既定"}, True))
        check("線の無い本文の台帳には lines を書かない", o["線なしの台帳"] is False)
        check("2 度目に本文の線が違えば 3 で名指しし、台帳を変えない", o["線の 2 度目"] == (3, True, True))
        check("2 度目に本文の線が同じなら名指ししない", o["線が同じ 2 度目"] == (3, False))
        none, alldone = o["空の言い分け"]
        check("チェックリストが無いことと、全部済んだことを別の言葉で言う",
              "1 本も無い" in none and "/dev-loop:dev-loop" in none and "すべて [x]" in alldone)

        print("\n判定できない（C10）・引数")
        check("gh の失敗は 4", o["gh の失敗"] == 4)
        check("gh を通しても同じ指紋（陽性対照）・gh issue view 50 --json body",
              o["gh を通す"][:2] == (0, True) and o["gh を通す"][2][:5] == ["issue", "view", "50", "--json", "body"])
        check("git の外の apply は 4 で、何も書かない", o["git の外"] == (4, []))
        check("番号でない・0・--digest なしは 2", o["引数"] == (2, 2, 2))

        print("\n終了コードが docstring の表と一致する（C11）")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_USAGE, mod.EXIT_REJECTED, mod.EXIT_UNKNOWN}
        check(f"表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)

        print("\n変異テスト（壊したのに緑なら失格。C11）")
        for name, pairs in MUTATIONS.items():
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement, 1)
            d = tmp / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "parent-issue.py"
            broken.write_text(mutated, encoding="utf-8")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**（test-ledger.py と同じ）
            try:
                mutant = load(broken)
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, tmp, f"mut-{abs(hash(name))}")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", got != o)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め（C12）")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("親 Issue の取り出しのテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
