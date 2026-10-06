#!/usr/bin/env python3
"""dev-loop の Eval を、陽性対照と一緒に 1 コマンドで回し、貼れる要約を出す（#190）。

usage:
    python3 scripts/run-dev-loop-evals.py [--max-cost-usd N] [--out DIR]
    python3 scripts/run-dev-loop-evals.py --dry-run [--out DIR]     # 組むだけ（課金しない）
    python3 scripts/run-dev-loop-evals.py --summarize <aggregate-result.json>

**CI からは呼ばない**——`claude` を起こすので課金される（1 回およそ $1.5）。
**worktree 隔離セッションからも起動できない**——ガードが `claude plugin eval` を shell の `eval` と
読んで拒否する（#181）。**別の端末で、このファイルの絶対パスを渡して回す。**
`--dry-run` と `--summarize` は `claude` を起こさないので、どこからでも走る。

何をするか:

1. `plugins/dev-loop` を**リポジトリの外の一時領域**に複製する（`results/` は写さない）
2. 複製の `evals/` に、`CONTROLS` の対照を組む——**本物のケースのディレクトリを写し、
   `case.yaml` の `name` と `prompt` の行だけを差し替える**。grader・scaffold・設定は本物のまま。
   差し替える行がちょうど 1 つずつ見つからなければ、組まずに止まる
3. 複製に `claude plugin eval … --keep-temp` を 1 回当てる（本物のケースと対照が一緒に回る）
4. 出来た `aggregate-result.json` と、各実行の trace から要約を出す

**対照を `plugins/` の下に置かない理由**: grader と scaffold の複製ができて片方だけ古くなる・
ハーネスは `<eval dir>/**/case.yaml` を全部ケースとして拾うので本物の実行に混ざる・
`plugins/` の中身を変えると版の bump が要る。複製の中で組めば、どれも起きない。

要約が示すもの:

- grader ごとの合否と**期待**と一致したか。期待は、本物のケースは全部合格、対照は `CONTROLS` の `expect`
  （`None` は目的外で、一致に数えない）
- 子が走らせた Bash のコマンドと、その出力の末尾の行——**既知の雑音（`NOISE`）は除き、除いた行数を出す**
- **測定不成立の候補**（`SUSPECT`。実例: 子の `git` が `can't exec`——#181）

終了コード:

- **0**: 全部期待どおり
- **1**: 期待と違う grader がある
- **2**: 判定できなかった（`aggregate-result.json` が無い・期待したケースが報告に無い・trace が読めない）。
  **判定できなかったことは緑ではない**——1 と分けるのは、直すものが違うから（ケースではなく実行）
- **3**: 対照を組めなかった・`claude` を起動できなかった

守る:

- 対照は、本物のケースのディレクトリを丸ごと写す（grader・scaffold・設定は本物のまま）
- 差し替える `name` / `prompt` の行がちょうど 1 つでなければ、組まない
- 複製をリポジトリの中に作らない（`results/` も含め、リポジトリを 1 つも変えない）
- 期待と違う grader があれば 1
- 期待したケースが報告に無ければ 2
- trace を読めなければ 2（赤・緑の理由を示せない）
- 実行エラーがあれば 2
- 目的外（期待 `None`）の grader は一致に数えない
- 既知の雑音は除き、除いた行数を出す
- 測定不成立の候補は、表示する行に印を付ける

守らない:

- **本物のケースの緑が「探して正しく再開した」か「何もせず止まった」かは、機械で判定しない。**
  要約は Bash の回数とコマンドを出すだけで、読むのは人間（#183 の B で trace を読んで確かめた形）
- **trace の形はハーネスの内部形式である**——`message.content` の `tool_use` / `tool_result` を読む。
  変わったら「Bash 0 回」と出るので、**0 回は trace の形が変わった可能性も含む**
- **`--keep-temp` の一時領域（`/private/tmp/e-*`）は消さない**——中の `home/`・`tmp/` はハーネスが
  封じている（mode 000）。消すのは人間

標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "dev-loop"

# 陽性対照。**grader を持たせない**——持たせると本物と食い違える。差し替えるのは name と prompt だけ
CONTROLS = [
    {
        "source": "resume-no-new-worktree",
        "name": "control-created-worktree",
        "prompt": "Bash で次の 1 行をそのまま実行して、終わったら止まれ。他には何もするな: "
                  "git worktree add .claude/worktrees/issue-7-again -b issue/7-again",
        # True: 合格を期待 / False: 不合格を期待 / None: 目的外
        "expect": {"ran-find-cycle": None, "no-new-worktree": False, "no-new-branch": False},
    },
]

# 既知の雑音。**失敗の印ではない**——#183 の実行で、この行が出ても `git` は成功していた
NOISE = [
    re.compile(r"couldn't create cache file '.*xcrun_db"),
    re.compile(r"xcodebuild\[\d+:\d+\]\s+DVTFilePathFSEvents"),
]
# 測定不成立の候補。**出たら、その実行の緑は「作らなかった」ではなく「作れなかった」かもしれない**
SUSPECT = [
    re.compile(r"can't exec"),
    re.compile(r"command not found"),
]

TAIL = 3  # Bash の出力から出す末尾の行数
CMD_WIDTH = 200


def build(out: Path) -> Path:
    """複製を組み、複製したプラグインのパスを返す。組めなければ ValueError。"""
    out, repo = out.resolve(), REPO.resolve()  # 両側を解決する（片側だけだと symlink 越しに素通りする）
    if out == repo or repo in out.parents:
        raise ValueError(f"{out} はリポジトリの中——外を指すこと")
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"{out} が空でない——二重に組まないため断る")
    plugin = out / "dev-loop"
    shutil.copytree(PLUGIN, plugin, ignore=shutil.ignore_patterns("results"))
    for c in CONTROLS:
        src = plugin / "evals" / c["source"]
        dst = plugin / "evals" / c["name"]
        if not (src / "case.yaml").is_file():
            raise ValueError(f"対照の元のケース {c['source']} が無い")
        shutil.copytree(src, dst)
        text = (dst / "case.yaml").read_text(encoding="utf-8")
        text = replace_one(text, r"^name:[^\n]*$", f"name: {c['name']}", "name")
        text = replace_one(text, r"^  prompt:[^\n]*$",
                           "  prompt: " + json.dumps(c["prompt"], ensure_ascii=False), "prompt")
        (dst / "case.yaml").write_text(text, encoding="utf-8")
    return plugin


def replace_one(text: str, pattern: str, new: str, what: str) -> str:
    rx = re.compile(pattern, re.M)
    hits = rx.findall(text)
    if len(hits) != 1:
        raise ValueError(f"case.yaml の {what} の行が {len(hits)} 個——1 個でなければ組まない")
    return rx.sub(lambda _m: new, text)


def expectations(case_names: list[str]) -> dict[str, dict[str, bool | None] | None]:
    """ケース名 → grader 名 → 期待。None（ケース全体）は「全 grader が合格」。"""
    exp: dict[str, dict[str, bool | None] | None] = {n: None for n in case_names}
    for c in CONTROLS:
        exp[c["name"]] = c["expect"]
    return exp


def real_case_names(plugin: Path) -> list[str]:
    """本物のケース名（複製を組む前の `plugins/dev-loop/evals` から）。"""
    names = []
    for y in sorted((plugin / "evals").glob("*/case.yaml")):
        m = re.search(r"^name:\s*(\S+)", y.read_text(encoding="utf-8"), re.M)
        names.append(m.group(1) if m else y.parent.name)
    return names


def bash_calls(trace: Path) -> list[tuple[str, str]]:
    """trace から (コマンド, 出力) を順に返す。"""
    uses: dict[str, str] = {}
    order: list[str] = []
    results: dict[str, str] = {}
    for line in trace.read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = o.get("message")
        content = m.get("content") if isinstance(m, dict) else None
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("name") == "Bash":
                uses[b.get("id")] = str((b.get("input") or {}).get("command", ""))
                order.append(b.get("id"))
            elif b.get("type") == "tool_result":
                r = b.get("content")
                if isinstance(r, list):
                    r = "\n".join(x.get("text", "") for x in r if isinstance(x, dict))
                results[b.get("tool_use_id")] = str(r or "")
    return [(uses[i], results.get(i, "")) for i in order]


def split_noise(output: str) -> tuple[list[str], int]:
    kept, dropped = [], 0
    for ln in output.splitlines():
        if any(p.search(ln) for p in NOISE):
            dropped += 1
        elif ln.strip():
            kept.append(ln)
    return kept, dropped


def summarize(aggregate: Path, expect: dict[str, dict[str, bool | None] | None]) -> tuple[str, int]:
    """要約（Markdown）と終了コードを返す。"""
    out: list[str] = []
    code = 0
    try:
        data = json.loads(aggregate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return f"**判定できなかった**: {aggregate} を読めない（{e}）\n", 2
    out.append(f"## dev-loop の Eval（claude {data.get('claudeVersion', '?')}・"
               f"${data.get('costUsd', 0):.2f}・{data.get('durationSeconds', '?')}s）\n")
    seen = set()
    for case in data.get("cases", []):
        name = case.get("name")
        seen.add(name)
        if name not in expect:
            out.append(f"### {name}\n\n期待が定義されていないケース——採点の一致は数えない\n")
            continue
        for i, run in enumerate((case.get("arms") or {}).get("with", []), 1):
            out.append(f"### {name}（run {i}）\n")
            out.append("| grader | 結果 | 期待 | 一致 |\n| --- | --- | --- | --- |")
            for g in run.get("graders", []):
                e = expect[name]
                want = True if e is None else e.get(g["name"], True)
                got = bool(g.get("passed"))
                if want is None:
                    mark = "目的外"
                elif want == got:
                    mark = "✓"
                else:
                    mark = "**✗ 期待と違う**"
                    code = max(code, 1)
                out.append(f"| {g['name']} | {'合格' if got else '不合格'} | "
                           f"{'—' if want is None else ('合格' if want else '不合格')} | {mark} |")
            if run.get("error"):
                out.append(f"\n**実行エラー**: {run['error']}")
                code = 2
            tp = run.get("tracePath")
            try:
                calls = bash_calls(Path(tp)) if tp else None
            except OSError:
                calls = None
            if calls is None:
                out.append(f"\n**trace を読めない**（{tp}）——赤・緑の理由を示せない")
                code = 2
                continue
            out.append(f"\nBash {len(calls)} 回（trace: `{tp}`）\n")
            for n, (cmd, res) in enumerate(calls, 1):
                kept, dropped = split_noise(res)
                first = cmd.splitlines()[0] if cmd else ""
                if len(first) > CMD_WIDTH or "\n" in cmd:
                    first = first[:CMD_WIDTH] + " …"
                out.append(f"{n}. `{first}`")
                for ln in kept[-TAIL:]:
                    flag = " ← **測定不成立の候補**" if any(p.search(ln) for p in SUSPECT) else ""
                    out.append(f"    - {ln[:CMD_WIDTH]}{flag}")
                if dropped:
                    out.append(f"    - （既知の雑音 {dropped} 行を除いた）" if kept
                               else f"    - （雑音のみ {dropped} 行）")
                if any(p.search(ln) for ln in kept[:-TAIL] for p in SUSPECT):
                    out.append("    - **測定不成立の候補が、表示しなかった行にもある**")
            out.append("")
    for name in expect:
        if name not in seen:
            out.append(f"**判定できなかった**: ケース `{name}` が報告に無い")
            code = 2
    verdict = {0: "全部期待どおり", 1: "期待と違う grader がある", 2: "判定できなかったものがある"}[code]
    out.append(f"\n**判定: {verdict}**（終了コード {code}）")
    return "\n".join(out) + "\n", code


def newest_aggregate(plugin: Path, since: float) -> Path | None:
    found = [p for p in (plugin / "evals" / "results").glob("*/aggregate-result.json")
             if p.stat().st_mtime >= since]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, help="複製を組む場所（空か存在しない。既定は一時ディレクトリ）")
    ap.add_argument("--dry-run", action="store_true", help="組んで、回すコマンドを出すだけ")
    ap.add_argument("--max-cost-usd", default="6")
    ap.add_argument("--summarize", type=Path, metavar="AGGREGATE", help="既存の結果を要約するだけ")
    a = ap.parse_args()

    names = real_case_names(PLUGIN)
    expect = expectations(names)
    if a.summarize:
        text, code = summarize(a.summarize, expect)
        print(text, end="")
        return code

    out = a.out or Path(tempfile.mkdtemp(prefix="dev-loop-evals-"))
    try:
        plugin = build(out)
    except ValueError as e:
        print(f"組めなかった: {e}", file=sys.stderr)
        return 3
    cmd = ["claude", "plugin", "eval", str(plugin), "--scaffold", "--allow-tools", "Bash",
           "--ablation", "none", "--no-publish", "--keep-temp", "--max-cost-usd", a.max_cost_usd]
    print(f"組んだ: {plugin}（本物 {len(names)} 件・対照 {len(CONTROLS)} 件）")
    print("回すコマンド: " + " ".join(cmd))
    if a.dry_run:
        return 0
    start = time.time()
    try:
        subprocess.run(cmd, check=False)
    except OSError as e:
        print(f"`claude` を起動できなかった: {e}", file=sys.stderr)
        return 3
    agg = newest_aggregate(plugin, start)
    if agg is None:
        print("**判定できなかった**: aggregate-result.json が出来ていない")
        return 2
    text, code = summarize(agg, expect)
    print("\n" + text, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
