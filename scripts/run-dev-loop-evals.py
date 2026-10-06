#!/usr/bin/env python3
"""dev-loop の Eval を、陽性対照と一緒に 1 コマンドで回し、貼れる要約を出す（#190）。

usage:
    python3 scripts/run-dev-loop-evals.py [--max-cost-usd N] [--out DIR]
    python3 scripts/run-dev-loop-evals.py --dry-run [--out DIR]     # 組むだけ（課金しない）
    python3 scripts/run-dev-loop-evals.py --summarize <aggregate-result.json> [--cases A,B]

**CI からは呼ばない**——`claude` を起こすので課金される（1 回およそ $1.5）。
**worktree 隔離セッションからも起動できない**——ガードが `claude plugin eval` を shell の `eval` と
読んで拒否する（#181）。**別の端末で、このファイルの絶対パスを渡して回す。**
`--dry-run` と `--summarize` は `claude` を起こさないので、どこからでも走る。

何をするか:

1. `plugins/dev-loop` を**リポジトリの外の一時領域**に複製する（`results/` は写さない）。
   **`--out` を渡さなければ一時ディレクトリを作り、消さない**（`--dry-run` でも残る。パスは出力に出る）
2. 複製の `evals/` に、`CONTROLS` の対照を組む——**本物のケースのディレクトリを写し、
   `case.yaml` の `name` と `prompt` の行だけを差し替える**。grader・scaffold・設定は本物のまま
3. 複製に `claude plugin eval … --keep-temp` を 1 回当てる（本物のケースと対照が一緒に回る）
4. 出来た `aggregate-result.json` と、各実行の trace から要約を出す

**対照を `plugins/` の下に置かない理由**: grader と scaffold の複製ができて片方だけ古くなる・
ハーネスは eval dir の下の `case.yaml` を入れ子まで拾う（2.1.291 の `plugin eval` の説明文が
`<eval dir>/**/case.yaml` と書いており、#183 では `evals-control/created-worktree` が拾われた）ので
本物の実行に混ざる・`plugins/` の中身を変えると版の bump が要る。複製の中で組めば、どれも起きない。

要約が示すもの:

- grader ごとの合否と**期待**と一致したか。期待は、本物のケースは全部合格、対照は `CONTROLS` の `expect`
  （`None` は目的外で、一致に数えない）
- 子が走らせた Bash のコマンドと、その出力の末尾の行——**既知の雑音（`NOISE`）は除き、除いた行数を出す**
- **測定不成立の候補**（`SUSPECT` に当たる行・`is_error` の結果。実例: 子の `git` が `can't exec`——#181）
- `claude plugin eval` の終了コード（**判定には使わない**——対照は不合格が期待なので、正常でも非ゼロになりうる）

終了コード:

- **0**: 全部期待どおり
- **1**: 期待と違う grader がある
- **2**: 判定できなかった。**判定できなかったことは緑ではない**——1 と分けるのは、直すものが違うから
  （ケースではなく実行）。条件は下の「守る」
- **3**: 対照を組めなかった・`claude` を起動できなかった

守る:

- 対照は、本物のケースのディレクトリを丸ごと写す（grader・scaffold・設定は本物のまま）
- 差し替える `name` / `prompt` の行がちょうど 1 つでなければ、組まない
- 差し替える値がブロックスカラー（`>`・`|`）なら、組まない（1 行目だけ差し替えると壊れた YAML になる）
- 複製をこの作業ツリーの中に作らない（`results/` も含め、リポジトリを 1 つも変えない）
- worktree から走らせたとき、同じリポジトリのメインの作業ツリーの中にも作らない
- 期待と違う grader があれば 1
- 期待したケースが報告に無ければ 2
- 期待が定義されていないケースが報告にあれば 2（採点を黙って捨てない）
- run が 0 件のケースは 2
- grader が 0 件の run は 2
- 期待した grader が報告に無ければ 2（対照が何も見なくなるのを緑にしない）
- `partial: true` は 2（打ち切られた実行を緑にしない）
- `skippedPaidGraders` は 2
- `scored: false` の grader は 2
- aggregate の構造が想定と違えば 2（Traceback の 1 と取り違えない）
- trace を読めなければ 2（赤・緑の理由を示せない）
- 実行エラーがあれば 2
- 目的外（期待 `None`）の grader は一致に数えない
- 既知の雑音は除き、除いた行数を出す
- 測定不成立の候補は、表示する行に印を付ける
- `is_error` の結果には印を付ける（拒否された Bash は「作らなかった」と同じに見える）

守らない:

- **本物のケースの緑が「探して正しく再開した」か「何もせず止まった」かは、機械で判定しない。**
  要約は Bash の回数とコマンドを出すだけで、読むのは人間（#183 の B で trace を読んで確かめた形）
- **Agent に委譲した先の Bash は数えない**——trace に出るのは親の道具呼び出しだけ。Agent の回数は出す
- **trace の形はハーネスの内部形式である**——`message.content` の `tool_use` / `tool_result` を読む。
  変わったら「Bash 0 回」と出るので、**0 回は trace の形が変わった可能性も含む**
- **`--keep-temp` の一時領域（`/private/tmp/e-*`）は消さない**——中の `home/`・`tmp/` はハーネスが
  封じている（mode 000）。消すのは人間
- **`claude plugin eval` の終了コードの意味は確かめていない**（上のとおり判定に使わない）

標準ライブラリのみ。**`git` は呼ばない**（メインの作業ツリーは `.git` ファイルを読んで辿る）。
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
    re.compile(r"has been denied"),
]

TAIL = 3  # Bash の出力から出す末尾の行数
CMD_WIDTH = 200


def protected_roots() -> list[Path]:
    """複製を置いてはならない場所。この作業ツリーと、worktree ならメインの作業ツリー。"""
    roots = [REPO.resolve()]
    dotgit = REPO / ".git"
    try:
        if dotgit.is_file():
            m = re.match(r"gitdir:\s*(.+)", dotgit.read_text(encoding="utf-8").strip())
            if m:
                gitdir = (REPO / m.group(1)).resolve()
                common = gitdir
                if (gitdir / "commondir").is_file():
                    common = (gitdir / (gitdir / "commondir").read_text(encoding="utf-8").strip()).resolve()
                roots.append(common.parent)
    except OSError:
        pass
    return roots


def build(out: Path) -> Path:
    """複製を組み、複製したプラグインのパスを返す。組めなければ ValueError。"""
    out = out.resolve()  # 両側を解決する（片側だけだと symlink 越しに素通りする）
    for root in protected_roots():
        if out == root or root in out.parents:
            raise ValueError(f"{out} はリポジトリ（{root}）の中——外を指すこと")
    if out.exists() and not out.is_dir():
        raise ValueError(f"{out} はディレクトリではない")
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"{out} が空でない——二重に組まないため断る")
    plugin = out / "dev-loop"
    shutil.copytree(PLUGIN, plugin, ignore=shutil.ignore_patterns("results"))
    for c in CONTROLS:
        src = plugin / "evals" / c["source"]
        dst = plugin / "evals" / c["name"]
        if not (src / "case.yaml").is_file():
            raise ValueError(f"対照の元のケース {c['source']} が無い")
        if dst.exists():
            raise ValueError(f"対照と同じ名前のディレクトリ {c['name']} が既にある")
        shutil.copytree(src, dst)
        text = (dst / "case.yaml").read_text(encoding="utf-8")
        text = replace_one(text, r"^name:[ \t]*(.*)$", f"name: {c['name']}", "name")
        text = replace_one(text, r"^  prompt:[ \t]*(.*)$",
                           "  prompt: " + json.dumps(c["prompt"], ensure_ascii=False), "prompt")
        (dst / "case.yaml").write_text(text, encoding="utf-8")
    return plugin


def replace_one(text: str, pattern: str, new: str, what: str) -> str:
    rx = re.compile(pattern, re.M)
    hits = rx.findall(text)
    if len(hits) != 1:
        raise ValueError(f"case.yaml の {what} の行が {len(hits)} 個——1 個でなければ組まない")
    if hits[0].lstrip().startswith((">", "|")):
        raise ValueError(f"case.yaml の {what} がブロックスカラー——1 行だけ差し替えると壊れるので組まない")
    return rx.sub(lambda _m: new, text)


def expectations(case_names: list[str]) -> dict[str, dict[str, bool | None] | None]:
    """ケース名 → grader 名 → 期待。None（ケース全体）は「全 grader が合格」。"""
    exp: dict[str, dict[str, bool | None] | None] = {n: None for n in case_names}
    for c in CONTROLS:
        exp[c["name"]] = c["expect"]
    return exp


def real_case_names(plugin: Path) -> list[str]:
    """本物のケース名。入れ子も拾い（ハーネスと同じ）、`results/` の下は除く。"""
    names = []
    evals = plugin / "evals"
    for y in sorted(evals.rglob("case.yaml")):
        if "results" in y.relative_to(evals).parts:
            continue
        m = re.search(r"^name:[ \t]*[\"']?([^\"'\s]+)", y.read_text(encoding="utf-8"), re.M)
        names.append(m.group(1) if m else y.parent.name)
    return names


def tool_calls(trace: Path) -> tuple[list[tuple[str, str, bool]], int]:
    """trace から Bash の (コマンド, 出力, is_error) を順に返す。2 つ目は Agent の回数。"""
    uses: dict[str, str] = {}
    order: list[str] = []
    results: dict[str, tuple[str, bool]] = {}
    agents = 0
    for line in trace.read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = o.get("message") if isinstance(o, dict) else None
        content = m.get("content") if isinstance(m, dict) else None
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("name") == "Bash":
                uses[b.get("id")] = str((b.get("input") or {}).get("command", ""))
                order.append(b.get("id"))
            elif b.get("type") == "tool_use" and b.get("name") == "Agent":
                agents += 1
            elif b.get("type") == "tool_result":
                r = b.get("content")
                if isinstance(r, list):
                    r = "\n".join(x.get("text", "") for x in r if isinstance(x, dict))
                results[b.get("tool_use_id")] = (str(r or ""), bool(b.get("is_error")))
    return [(uses[i], *results.get(i, ("", False))) for i in order], agents


def split_noise(output: str) -> tuple[list[str], int]:
    kept, dropped = [], 0
    for ln in output.splitlines():
        if any(p.search(ln) for p in NOISE):
            dropped += 1
        elif ln.strip():
            kept.append(ln)
    return kept, dropped


def summarize(aggregate: Path, expect: dict[str, dict[str, bool | None] | None],
              returncode: int | None = None) -> tuple[str, int]:
    """要約（Markdown）と終了コードを返す。"""
    try:
        data = json.loads(aggregate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return f"**判定できなかった**: {aggregate} を読めない（{e}）\n", 2
    try:
        return _summarize(data, expect, returncode)
    except (AttributeError, TypeError, KeyError, ValueError) as e:
        return f"**判定できなかった**: aggregate の構造が想定と違う（{type(e).__name__}: {e}）\n", 2


def _summarize(data: dict, expect: dict[str, dict[str, bool | None] | None],
               returncode: int | None) -> tuple[str, int]:
    out: list[str] = []
    code = 0
    out.append(f"## dev-loop の Eval（claude {data.get('claudeVersion', '?')}・"
               f"${data.get('costUsd', 0):.2f}・{data.get('durationSeconds', '?')}s）\n")
    if returncode is not None:
        out.append(f"`claude plugin eval` の終了コード: {returncode}（判定には使わない）\n")
    if data.get("partial"):
        out.append("**判定できなかった**: 実行が打ち切られている（`partial: true`）\n")
        code = 2  # partial
    seen = set()
    for case in data.get("cases", []):
        name = case.get("name")
        seen.add(name)
        if name not in expect:
            out.append(f"### {name}\n\n**判定できなかった**: 期待が定義されていないケース\n")
            code = 2  # 未定義のケース
            continue
        runs = (case.get("arms") or {}).get("with") or []
        if not runs:
            out.append(f"### {name}\n\n**判定できなかった**: run が 0 件\n")
            code = 2  # run 0 件
        for i, run in enumerate(runs, 1):
            out.append(f"### {name}（run {i}）\n")
            graders = run.get("graders") or []
            if not graders:
                out.append("**判定できなかった**: grader が 0 件\n")
                code = 2  # grader 0 件
            e = expect[name]
            missing = [k for k, v in (e or {}).items()
                       if v is not None and k not in {g.get("name") for g in graders}]
            if missing:
                out.append(f"**判定できなかった**: 期待した grader が報告に無い（{', '.join(missing)}）\n")
                code = 2  # 期待した grader が無い
            if run.get("skippedPaidGraders"):
                out.append("**判定できなかった**: 課金される grader が飛ばされた（`skippedPaidGraders`）\n")
                code = 2  # skippedPaidGraders
            out.append("| grader | 結果 | 期待 | 一致 |\n| --- | --- | --- | --- |")
            for g in graders:
                want = True if e is None else e.get(g["name"], True)
                got = bool(g.get("passed"))
                if g.get("scored") is False:
                    mark = "**採点されていない**"
                    code = 2  # 採点されていない
                elif want is None:
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
                code = 2  # 実行エラー
            tp = run.get("tracePath")
            try:
                calls, agents = tool_calls(Path(tp)) if tp else (None, 0)
            except OSError:
                calls, agents = None, 0
            if calls is None:
                out.append(f"\n**trace を読めない**（{tp}）——赤・緑の理由を示せない")
                code = 2  # trace を読めない
                continue
            out.append(f"\nBash {len(calls)} 回・Agent {agents} 回（trace: `{tp}`。Agent の中の Bash は数えない）\n")
            for n, (cmd, res, is_error) in enumerate(calls, 1):
                kept, dropped = split_noise(res)
                first = cmd.splitlines()[0] if cmd else ""
                if len(first) > CMD_WIDTH or "\n" in cmd:
                    first = first[:CMD_WIDTH] + " …"
                err = " ← **is_error（測定不成立の候補）**" if is_error else ""
                out.append(f"{n}. `{first}`{err}")
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
            code = 2  # 報告に無いケース
    verdict = {0: "全部期待どおり", 1: "期待と違う grader がある", 2: "判定できなかったものがある"}[code]
    out.append(f"\n**判定: {verdict}**（終了コード {code}）")
    return "\n".join(out) + "\n", code


def newest_aggregate(plugin: Path, since: float) -> Path | None:
    found = [p for p in (plugin / "evals" / "results").glob("*/aggregate-result.json")
             if p.stat().st_mtime >= since]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, help="複製を組む場所（空か存在しない。既定は一時ディレクトリで、消さない）")
    ap.add_argument("--dry-run", action="store_true", help="組んで、回すコマンドを出すだけ")
    ap.add_argument("--max-cost-usd", default="6")
    ap.add_argument("--summarize", type=Path, metavar="AGGREGATE", help="既存の結果を要約するだけ")
    ap.add_argument("--cases", help="期待するケースをカンマ区切りで絞る（--summarize 用。片方だけ回した結果に当てる）")
    a = ap.parse_args()

    names = real_case_names(PLUGIN)
    expect = expectations(names)
    if a.cases:
        wanted = a.cases.split(",")
        unknown = [w for w in wanted if w not in expect]
        if unknown:
            print(f"知らないケース: {', '.join(unknown)}（知っているもの: {', '.join(expect)}）", file=sys.stderr)
            return 3
        expect = {k: v for k, v in expect.items() if k in wanted}
    if a.summarize:
        text, code = summarize(a.summarize, expect)
        print(text, end="")
        return code

    out = a.out or Path(tempfile.mkdtemp(prefix="dev-loop-evals-"))
    try:
        plugin = build(out)
    except (ValueError, OSError) as e:
        print(f"組めなかった: {e}", file=sys.stderr)
        return 3
    cmd = ["claude", "plugin", "eval", str(plugin), "--scaffold", "--allow-tools", "Bash",
           "--ablation", "none", "--no-publish", "--keep-temp", "--max-cost-usd", a.max_cost_usd]
    print(f"組んだ: {plugin}（本物 {len(names)} 件・対照 {len(CONTROLS)} 件。この複製は消さない）")
    print("回すコマンド: " + " ".join(cmd))
    if a.dry_run:
        return 0
    start = time.time()
    try:
        proc = subprocess.run(cmd, check=False)
    except OSError as e:
        print(f"`claude` を起動できなかった: {e}", file=sys.stderr)
        return 3
    agg = newest_aggregate(plugin, start)
    if agg is None:
        print("**判定できなかった**: aggregate-result.json が出来ていない")
        return 2
    text, code = summarize(agg, expect, proc.returncode)
    print("\n" + text, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
