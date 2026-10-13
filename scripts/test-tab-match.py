#!/usr/bin/env python3
"""orca・cmux のタブ一致規則の回帰テスト（#202）。

    python3 scripts/test-tab-match.py

**本体はプラグインの `SKILL.md` の中にある**——`plugins/orca/skills/orca/SKILL.md` の
「ブラウザタブの開き方（共通手順）」と、`plugins/cmux/skills/cmux/SKILL.md` の
「ブラウザペインの開き方（共通手順）」の `bash` ブロックである。**写しを作らない**——
ブロックを毎回 `SKILL.md` から抜き出し、1 行目の `TARGET_URL=` だけ置き換えて
**bash ごと流す**。`PATH` の先頭に偽の `orca` / `cmux` を置き、偽のコマンドが記録した
呼び出しで「再利用したか・新規に作ったか」を判定する。

なぜ要るか: #194 ではブロックから規則を抜き出して 9 件のケース表を当てたが、
スクリプトとして残していなかった。しかも狭いパスの Verifier が、変異「境界文字に `-` を足す」
（`/12-x` を下位ページとみなす）は**その 9 件では殺せない**ことを示した。
**この変異を殺すのが C5 だけであることは、下の `ISSUE_MUTANT` の検査が表明している**
——C5 を消すと、その表明が赤になる。

見るもの:

1. **ケース表**（`COMMON_CASES` ＋ cmux だけの `CMUX_CASES`）が**両スキルで**期待どおり。
2. **変異テスト**: ブロックを 1 箇所ずつ壊し、**壊したのに全ケースが期待どおりなら失格**とする。
   変異ごとに、**壊す文字列がブロックにちょうど 1 回現れること**を先に確かめる
   （届いていない変異は、穴が無くても緑になるので）。変異は**両スキル**に当てる。
3. **抜き出しが壊れたら赤**——見出しが無い・その下に `bash` ブロックが無い・
   1 行目が `TARGET_URL=` でない、のどれでも黙ってケース 0 件にならない。

**このテストは実環境を触らない。** 偽のコマンドが `PATH` で先に解決されることを
ケースを流す前に表明し（本物の `orca` / `cmux` を起こさない）、`HOME` も一時ディレクトリに差し替える。

守らないもの:

- **本物の `orca` / `cmux` の出力形との一致。** 偽のコマンドが返すのは、ブロックが前提にしている形
  （orca は `result.tabs[].url`、cmux は `surfaces[].url` と `browser --surface <ref> url` の `url`）
  であって、実機の形を測ってはいない。
- **散文の箇条書きとコードの食い違い。** 実行するのはコードだけ。
- **cmux の 1 枚ずつの取得の時間切れ**（`timeout=10`）。待つと遅いので作っていない。

標準ライブラリのみ。
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent

MISSING = object()  # url キーそのものが無い

FAKE_ORCA = """#!/bin/sh
echo "orca $*" >> "$FAKE_LOG"
if [ "$1 $2" = "tab list" ]; then
    cat "$FAKE_DIR/list.out"
fi
"""

FAKE_CMUX = """#!/bin/sh
echo "cmux $*" >> "$FAKE_LOG"
if [ "$*" = "--json list-panels" ]; then
    cat "$FAKE_DIR/list.out"
elif [ "$1 $2 $3 $5" = "--json browser --surface url" ]; then
    if [ -f "$FAKE_DIR/url-$4.out" ]; then
        cat "$FAKE_DIR/url-$4.out"
    else
        exit 1
    fi
fi
"""


class Tool:
    def __init__(self, name: str, skill: str, heading: str, fake: str) -> None:
        self.name = name
        self.skill = REAL_REPO / skill
        self.heading = heading
        self.fake = fake

    def listing(self, tabs: list[dict]) -> str:
        if self.name == "orca":
            out = []
            for t in tabs:
                d = {"browserPageId": t["id"]}
                if t["url"] is not MISSING:
                    d["url"] = t["url"]
                out.append(d)
            return json.dumps({"result": {"tabs": out}})
        out = []
        for t in tabs:
            d = {"ref": t["id"], "type": t.get("type", "browser")}
            if t["url"] is not MISSING:
                d["url"] = t["url"]
            out.append(d)
        return json.dumps({"surfaces": out})

    def outcome(self, calls: list[str], target: str):
        """偽のコマンドの呼び出し記録を ('reuse', id) / ('create',) / ('unknown', calls) に読む。"""
        if self.name == "orca":
            acts = [c for c in calls if c != "orca tab list --json"]
            if acts == [f"orca tab create --url {target} --json"]:
                return ("create",)
            if (
                len(acts) == 2
                and acts[0].startswith("orca goto --page ")
                and acts[0].endswith(f" --url {target} --json")
            ):
                page = acts[0][len("orca goto --page "):-len(f" --url {target} --json")]
                if acts[1] == f"orca tab switch --page {page} --json":
                    return ("reuse", page)
            return ("unknown", acts)
        acts = [
            c for c in calls
            if c != "cmux --json list-panels" and not (c.startswith("cmux --json browser --surface ") and c.endswith(" url"))
        ]
        if acts == [f"cmux browser open-split {target}"]:
            return ("create",)
        if len(acts) == 1 and acts[0].startswith("cmux browser --surface ") and acts[0].endswith(f" navigate {target}"):
            return ("reuse", acts[0][len("cmux browser --surface "):-len(f" navigate {target}")])
        return ("unknown", acts)


TOOLS = [
    Tool("orca", "plugins/orca/skills/orca/SKILL.md", "## ブラウザタブの開き方（共通手順）", FAKE_ORCA),
    Tool("cmux", "plugins/cmux/skills/cmux/SKILL.md", "## ブラウザペインの開き方（共通手順）", FAKE_CMUX),
]

B = "https://github.com/o/r"


def tab(id_: str, url, **kw) -> dict:
    return {"id": id_, "url": url, **kw}


# (名前, TARGET_URL, タブ, 一覧の生の出力（None ならタブから作る）, 1 枚ずつの url（cmux）, 期待)
# 期待: ("reuse", id) / ("create",) / ("reject",)
COMMON_CASES = [
    ("C1 完全一致", f"{B}/pull/12", [tab("p1", f"{B}/pull/12")], None, {}, ("reuse", "p1")),
    ("C2 完全一致を下位ページより優先", f"{B}/pull/12",
     [tab("p1", f"{B}/pull/12/files"), tab("p2", f"{B}/pull/12")], None, {}, ("reuse", "p2")),
    ("C3 番号の前方一致は別物", f"{B}/issues/19", [tab("p1", f"{B}/issues/194")], None, {}, ("create",)),
    ("C4/ 境界 /", f"{B}/pull/12", [tab("p1", f"{B}/pull/12/files")], None, {}, ("reuse", "p1")),
    ("C4# 境界 #", f"{B}/issues/7", [tab("p1", f"{B}/issues/7#issuecomment-1")], None, {}, ("reuse", "p1")),
    ("C4? 境界 ?", f"{B}/pull/12", [tab("p1", f"{B}/pull/12?w=1")], None, {}, ("reuse", "p1")),
    ("C5 - は境界ではない", f"{B}/pull/12", [tab("p1", f"{B}/pull/12-x")], None, {}, ("create",)),
    ("C6 タブ 0 枚", f"{B}/pull/12", [], None, {}, ("create",)),
    ("C7 url 欠落のタブがあっても", f"{B}/pull/12",
     [tab("p1", MISSING), tab("p2", f"{B}/pull/12/files")], None, {}, ("reuse", "p2")),
    ("C8 url が null のタブがあっても", f"{B}/pull/12",
     [tab("p1", None), tab("p2", f"{B}/pull/12/files")], None, {}, ("reuse", "p2")),
    ("C9 一覧が JSON でない", f"{B}/pull/12", [], "not json\n", {}, ("create",)),
    ("C10 完全一致が 2 枚なら先頭", f"{B}/pull/12",
     [tab("p1", f"{B}/pull/12"), tab("p2", f"{B}/pull/12")], None, {}, ("reuse", "p1")),
    ("C11a TARGET_URL が空", "", [tab("p1", MISSING), tab("p2", "")], None, {}, ("reject",)),
    ("C11b https:// でない", "github.com/o/r/pull/12",
     [tab("p1", "github.com/o/r/pull/12")], None, {}, ("reject",)),
]

CMUX_CASES = [
    ("X1 list-panels に url が無く、1 枚ずつ取って一致", f"{B}/pull/12",
     [tab("s1", MISSING)], None, {"s1": json.dumps({"url": f"{B}/pull/12"})}, ("reuse", "s1")),
    ("X2 1 枚ずつの取得が JSON でない", f"{B}/pull/12",
     [tab("s1", MISSING)], None, {"s1": "oops"}, ("create",)),
    ("X3 ブラウザでないサーフェスは見ない", f"{B}/pull/12",
     [tab("s1", f"{B}/pull/12", type="terminal")], None, {}, ("create",)),
    ("X4 1 枚ずつの url が null でも落ちない", f"{B}/pull/12",
     [tab("s1", MISSING), tab("s2", f"{B}/pull/12/files")], None, {"s1": json.dumps({"url": None})},
     ("reuse", "s2")),
]


def cases_for(tool: Tool) -> list:
    return COMMON_CASES + (CMUX_CASES if tool.name == "cmux" else [])


# (名前, 置き換え前, 置き換え後, 対象のツール（None なら両方）)
CASE_LINE = 'case "$TARGET_URL" in https://*) ;; *) echo "URL を決められない: $TARGET_URL" >&2; exit 1 ;; esac'
ISSUE_MUTANT = ("境界に - を足す（#194 の実物）", "in '/#?'", "in '/#?-'", None)
MUTANTS = [
    ISSUE_MUTANT,
    ("境界から / を外す", "in '/#?'", "in '#?'", None),
    ("境界から # を外す", "in '/#?'", "in '/?'", None),
    ("境界から ? を外す", "in '/#?'", "in '/#'", None),
    ("素の前方一致", "u.startswith(target) and u[len(target)] in '/#?'", "u.startswith(target)", None),
    ("完全一致の優先を外す", "if u == target] or",
     "if u == target or (u.startswith(target) and u[len(target)] in '/#?')] or", None),
    ("先頭ではなく末尾を取る", "hit[0]", "hit[-1]", None),
    ("https:// の拒否を外す", CASE_LINE, ":", None),
    ("url 欠落を空文字にしない", "t.get('url') or ''", "t.get('url')", "orca"),
    ("url を添字で引く", "t.get('url') or ''", "t['url']", "orca"),
    ("ブラウザに絞らない", " if s.get('type') == 'browser'", "", "cmux"),
    ("1 枚ずつ取らない", "return json.loads(out).get('url') or ''", "return ''", "cmux"),
    ("1 枚ずつの null を空文字にしない", "return json.loads(out).get('url') or ''",
     "return json.loads(out).get('url')", "cmux"),
]
# ISSUE_MUTANT を殺すケースの名前の接頭辞。**これ以外で殺せたら、C5 が要らない形になっている。**
ISSUE_KILLERS = {"C5"}


def extract_block(tool: Tool) -> str:
    """見出しの下の最初の ```bash ブロックを返す。見つからなければ例外。"""
    lines = tool.skill.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(tool.heading)
    except ValueError:
        raise AssertionError(f"{tool.skill}: 見出し {tool.heading!r} が無い") from None
    i = start + 1
    while i < len(lines) and not lines[i].startswith("## "):
        if lines[i] == "```bash":
            body = []
            for line in lines[i + 1:]:
                if line == "```":
                    break
                body.append(line)
            else:
                raise AssertionError(f"{tool.skill}: bash ブロックが閉じていない")
            if not body or not body[0].startswith("TARGET_URL="):
                raise AssertionError(f"{tool.skill}: ブロックの 1 行目が TARGET_URL= でない")
            if "python3 -I -c" not in "\n".join(body):
                raise AssertionError(f"{tool.skill}: ブロックに python3 -I -c が無い")
            return "\n".join(body) + "\n"
        i += 1
    raise AssertionError(f"{tool.skill}: {tool.heading!r} の下に bash ブロックが無い")


class Sandbox:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.bin = root / "bin"
        self.bin.mkdir()
        for tool in TOOLS:
            p = self.bin / tool.name
            p.write_text(tool.fake, encoding="utf-8")
            p.chmod(0o755)
        (self.bin / "python3").symlink_to(sys.executable)
        bash = shutil.which("bash")
        assert bash, "bash が無い"
        self.bash = bash
        self.path = os.pathsep.join([str(self.bin), "/usr/bin", "/bin"])
        # 実環境を触らない: 偽のコマンドが先に解決されることを表明する。
        for tool in TOOLS:
            found = shutil.which(tool.name, path=self.path)
            assert found == str(self.bin / tool.name), f"{tool.name} が偽物に解決されない: {found}"
        assert shutil.which("python3", path=self.path) == str(self.bin / "python3")
        self.home = root / "home"
        self.home.mkdir()

    def run(self, tool: Tool, block: str, case) -> tuple:
        name, target, tabs, raw, per_url, _ = case
        d = Path(tempfile.mkdtemp(dir=self.root))
        (d / "list.out").write_text(raw if raw is not None else tool.listing(tabs), encoding="utf-8")
        for ref, out in per_url.items():
            (d / f"url-{ref}.out").write_text(out, encoding="utf-8")
        log = d / "log"
        log.touch()
        first, rest = block.split("\n", 1)
        script = d / "block.sh"
        script.write_text(f"TARGET_URL={shlex.quote(target)}\n{rest}", encoding="utf-8")
        env = {"PATH": self.path, "HOME": str(self.home), "FAKE_LOG": str(log), "FAKE_DIR": str(d), "LANG": "C.UTF-8"}
        proc = subprocess.run([self.bash, str(script)], env=env, cwd=d, capture_output=True, text=True, timeout=60)
        calls = log.read_text(encoding="utf-8").splitlines()
        if proc.returncode != 0:
            return ("reject",) if proc.returncode == 1 and not calls else ("unknown", proc.returncode, calls)
        return tool.outcome(calls, target)


def failing(sb: Sandbox, tool: Tool, block: str, stop_first: bool) -> list[str]:
    bad = []
    for case in cases_for(tool):
        got = sb.run(tool, block, case)
        if got != case[5]:
            bad.append(f"{case[0]}: 期待 {case[5]} / 実際 {got}")
            if stop_first:
                break
    return bad


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        sb = Sandbox(Path(tmp))
        blocks = {}
        for tool in TOOLS:
            try:
                blocks[tool.name] = extract_block(tool)
            except AssertionError as e:
                errors.append(str(e))
        if errors:
            for e in errors:
                print(f"FAIL {e}")
            return 1

        # 1. ケース表（陽性対照: 壊していないブロックで全部が期待どおり）
        for tool in TOOLS:
            bad = failing(sb, tool, blocks[tool.name], stop_first=False)
            n = len(cases_for(tool))
            if bad:
                errors.extend(f"{tool.name} {b}" for b in bad)
            print(f"{'ok  ' if not bad else 'FAIL'} {tool.name}: ケース {n - len(bad)}/{n}")
        if errors:
            for e in errors:
                print(f"  {e}")
            return 1

        # 2. 変異テスト
        for mname, old, new, only in MUTANTS:
            for tool in TOOLS:
                if only and tool.name != only:
                    continue
                block = blocks[tool.name]
                if block.count(old) != 1:
                    errors.append(f"変異 {mname!r}（{tool.name}）: 壊す文字列が {block.count(old)} 回現れる（1 回でなければ届かない）")
                    continue
                mutated = block.replace(old, new)
                is_issue = (mname, old, new, only) == ISSUE_MUTANT
                bad = failing(sb, tool, mutated, stop_first=not is_issue)
                if not bad:
                    errors.append(f"変異 {mname!r}（{tool.name}）が生き残った")
                    print(f"FAIL 変異 {mname}（{tool.name}）: 生存")
                    continue
                if is_issue:
                    killers = {b.split(" ", 1)[0] for b in bad}
                    if killers != ISSUE_KILLERS:
                        errors.append(f"変異 {mname!r}（{tool.name}）を殺したケースが {sorted(killers)}（期待 {sorted(ISSUE_KILLERS)}）")
                print(f"ok   変異 {mname}（{tool.name}）: {bad[0].split(':', 1)[0]} で死んだ")

        # 3. 抜き出しが壊れたら赤
        broken = {
            "見出しが無い": lambda s, h: s.replace(h, h + "X"),
            "1 行目が TARGET_URL= でない": lambda s, h: s.replace('\nTARGET_URL="', '\nTARGET="', 1),
            "bash ブロックが無い": lambda s, h: s.replace("```bash\nTARGET_URL", "```sh\nTARGET_URL", 1),
        }
        for tool in TOOLS:
            text = tool.skill.read_text(encoding="utf-8")
            for bname, fn in broken.items():
                mutated = fn(text, tool.heading)
                assert mutated != text, f"抜き出しの変異 {bname!r}（{tool.name}）が届いていない"
                p = Path(tmp) / f"{tool.name}-SKILL.md"
                p.write_text(mutated, encoding="utf-8")
                fake = Tool(tool.name, str(p), tool.heading, tool.fake)
                try:
                    extract_block(fake)
                except AssertionError:
                    print(f"ok   抜き出し {bname}（{tool.name}）: 赤")
                else:
                    errors.append(f"抜き出し {bname!r}（{tool.name}）で赤にならない")

    if errors:
        for e in errors:
            print(f"FAIL {e}")
        return 1
    print("ok: タブ一致規則の回帰テスト")
    return 0


if __name__ == "__main__":
    sys.exit(main())
