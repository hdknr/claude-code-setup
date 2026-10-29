#!/usr/bin/env python3
r"""cruise の 1 周を `claude -p` の子プロセスで回す起動口と、その出力の要約（#491）。

    python3 <このスキルの base ディレクトリ>/scripts/child-cycle.py launch <台帳の名前> <番号> \
        --brief <委譲文のファイル> --permission-mode <許可モード> \
        [--model <モデル>] [--max-budget-usd <金額>] [--allowed-tools <道具> …]
    python3 <…>/child-cycle.py status <台帳の名前> <番号>

**いつ使い、何を確かめてから続けるかは `references/child-process.md` を正とする**（このスキルと同じ場所にある）。
**既定の回し方はサブエージェントのままで、これは選べる形である**（cruise の `SKILL.md` の「4. 周を回す」）。
ここにあるのは、起動口と要約が何をし、何で止まるかである。

## launch

メインの作業ツリー（どこから呼んでも同じ。台帳と同じ決め方——`../../dev-loop/scripts/ledger.py` の `main_worktree`）を cwd にして、

    claude -p "/dev-loop:dev-loop <番号>" --output-format stream-json --verbose \
        --permission-mode <許可モード> --append-system-prompt <委譲文の中身> [--model …] [--max-budget-usd …] \
        [--allowedTools <道具> …]

を**親から切り離して**起こし（新しいセッション・標準入力は閉じる）、**終わるのを待たずに**戻る。
親の `/clear`・終了は、切り離した子を道連れにしない（**子のプロセスの寿命の話で、子が周を終えられるかは別**——
`references/child-process.md` の「確かめた範囲」）。

記録は台帳の隣の `.claude/plans/cruise-<名前>-children/` に置く——`<番号>-<UTC の時刻>.jsonl`（標準出力 = stream-json）、
`.err`（標準エラー）、`.json`（pid・引数・パス・起動時刻）。**周の worktree の中には書かない**（周を畳むと消える）。
標準出力の最後の行に、台帳の `agent` に書く値（`claude-p:<記録の .json のパス>`）を出す——**台帳を書くのは親である**（このスクリプトは台帳を書かない）。

## status

その Issue の**いちばん新しい**記録を読み、要約の行だけを出す（出力を丸ごと出さない）:
走っているか・`dev-loop` の版（init の `plugins`）・許可モード（init の `permissionMode`）・セッション・`result` の数と最後の `result`
（種別・誤り・ターン数・費用・API の誤り・拒否された操作）・親に殺された背景の体の数・利用上限の拒否・最後の文（切り詰め）・標準エラーの末尾。

**子は `result` を 2 つ以上出すことがある**——背景の体が走っている間に最初の `result` を出し、終わらずに待って、通知で続ける
（2.1.312 で実測。`references/child-process.md`）。**だから読むのは最後の `result` で、「終わった」はプロセスが居ないことで決める。**

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | launch: 起こした ／ status: 終わっていて、下の 3 の印が 1 つも無い |
| 1 | status: 走っている（それまでの要約を出す） |
| 2 | 引数が違う（名前・番号の形・選べない許可モード） |
| 3 | launch: 起こさなかった（委譲文が無い・空・`{{` が残る・`bypassPermissions`・同じ Issue の子が走っている）／ status: 終わったが要確認（`result` が無い・最後の `result` が成功でない・API の誤り・拒否された操作・殺された体・利用上限の拒否） |
| 4 | 判定できなかった（メインの作業ツリーを決められない・記録が無い・読めない・`claude` を起こせない・プロセスは居るが `ps` で確かめられない）。**「終わった」とも「走っている」とも答えていない** |

## 何を守り、何を守らないか

守る:

- **子を親から切り離す**——新しいセッションで起こし、終わるのを待たずに戻る。
- **子の標準入力を閉じる**——親の標準入力を子に継がせない（端末なら子が親の入力を読み、待ちうる）。
- **cwd はメインの作業ツリー**——worktree の中・サブディレクトリから呼んでも、子はメインの作業ツリーで起きる。
- **許可モードを名指しさせる**——渡さなければ 2。既定に任せると、同じ settings でも子のモードが分かれた（実測）。
- **`bypassPermissions` を拒む**——cruise は権限を広げない（`../../dev-loop/references/absent-lines.md` の「広げても外れないもの」）。
- **委譲文の `{{` の残りと空を拒む**——差し込み忘れの委譲文で子を起こさない。
- **同じ Issue の子が走っている間は、2 体目を起こさない**——同じ worktree を 2 体が触る。
- **記録は台帳の隣に置き、子を起こせなかったら記録を残さない**——残すと、起きていない子を `status` が「判定」する。
- **走っているかは、pid が居て、そのコマンドが `claude`（先頭の 2 語のどちらかの名前）であることで決める**——pid の使い回しを「走っている」と言わない。
- **そのうえで、最初の `-p` の引数がその Issue の `/dev-loop:dev-loop <番号>` であること**——委譲文（`--append-system-prompt` の中身）は `ps` に出るので、
  その中に書かれた別の番号に当たらない。`#5` を `#50` に当てない。
- **最後の `result` を読む**——最初の `result` は背景の体を待つ前のものでありうる。
- **最後の文は子自身の発言から取る**——委譲先の体の発言（`parent_tool_use_id` つき）も同じ出力に流れる。
- **dev-loop の版が途中の init で変わったら、両方を出す**——同じプロセスで init が 2 度以上出て、他のプラグインの版が途中から変わった（実測）。
- **終わったのに `result` が無ければ 3**——落ちた子を「済んだ」と言わない。
- **要確認の印（成功でない・API の誤り・拒否・殺された体・利用上限の拒否）が 1 つでもあれば 3。**
- **`allowed` と `allowed_warning`（上限が近いだけ）を利用上限の拒否と読まない**——拒否と読むのはそれ以外の `status` である。
- **要約の行を切り詰める**——出力を丸ごと親の文脈に積まない。

守らない:

- **子が周を終えられるか**——関門（`/code-review` の fork を含む）が `-p` の中で回りきるか、許可で止まらないかは、このスクリプトの外である
  （確かめた範囲は `references/child-process.md`）。
- **pid のコマンドが別の `claude` か**——同じ pid で、同じ Issue の `/dev-loop:dev-loop <番号>` を持つ別の `claude` が走っていれば「走っている」と読む。
- **stream-json の形の変化**——鍵の名前は 2.1.312 の実測に合わせている。版が変わって鍵が消えたら、その行は「無し」と出る。
- **子が台帳を書かないこと**——委譲文で頼むだけである（`prompts/child-cycle.md`）。
- **記録のディレクトリの後片付け**——消さない。
- **子を起こした後に記録を書けなかったとき**——子は走り続け、記録が無いので `status` も 2 体目の歯止めも見えない（pid は 4 の理由に出す）。
  **読めない古い記録が 1 つでもあれば、その Issue の `launch` は 4 で止まる**（読めない記録を「走っていない」と読まない）。
"""

import argparse
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_RUNNING = 1
EXIT_USAGE = 2
EXIT_REJECTED = 3
EXIT_UNKNOWN = 4

# --permission-mode の値（2.1.312）。本体の文字列の選べる値は acceptEdits・auto・bypassPermissions・default・dontAsk・plan で、
# `claude --help` は default の代わりに manual を出す。**どちらも起動して確かめてはいない**ので両方を通す
# （CLI が拒めば子はすぐ終わり、status が「result が無い」と標準エラーの末尾を出す）
PERMISSION_MODES = ("acceptEdits", "auto", "bypassPermissions", "default", "manual", "dontAsk", "plan")
REFUSED_MODES = ("bypassPermissions",)
MAX_TEXT = 300
LEDGER = Path(__file__).resolve().parent.parent.parent / "dev-loop" / "scripts" / "ledger.py"


class Usage(Exception):
    pass


class Refused(Exception):
    pass


class Unknown(Exception):
    pass


def load_ledger(path=None):
    spec = importlib.util.spec_from_file_location("cruise_child_ledger", path or LEDGER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def children_dir(name, cwd=None, ledger=None):
    ledger = ledger or load_ledger()
    try:
        path = ledger.ledger_path(name, cwd)
    except ledger.Usage as exc:
        raise Usage(str(exc)) from exc
    except ledger.Unknown as exc:
        raise Unknown(str(exc)) from exc
    return path.parent / f"cruise-{name}-children", path.parent.parent.parent


def parse_number(text):
    if not re.fullmatch(r"[1-9][0-9]*", text):
        raise Usage(f"Issue 番号が違う: {text!r}")
    return int(text)


def clip(text, limit=MAX_TEXT):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def records(directory, number):
    if not directory.is_dir():
        return []
    return sorted(directory.glob(f"{number}-*.json"))


def is_running(pid, number):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    except OSError as exc:
        raise Unknown(f"プロセス {pid} を確かめられない: {exc}") from exc
    try:
        proc = subprocess.run(["ps", "-ww", "-p", str(pid), "-o", "command="], capture_output=True, text=True, check=False)
    except OSError as exc:
        raise Unknown(f"ps を起こせない: {exc}") from exc
    if proc.returncode != 0:
        # kill(0) は通ったのに ps が確かめられない——「走っていない」と読まない（終わった直後の競合でも 4 に倒す）
        raise Unknown(f"プロセス {pid} は居るが、ps で確かめられない（終了コード {proc.returncode}）")
    # 実物は `claude -p …`、スクリプトの claude なら `<インタプリタ> <…>/claude -p …`。
    # **部分一致にしない**——パスに claude を含む別のプロセス（このリポジトリ自身の名前など）を拾う
    tokens = proc.stdout.split()
    if not any(Path(t).name == "claude" for t in tokens[:2]):
        return False
    # 最初の `-p` の引数だけを見る——委譲文は後ろの `--append-system-prompt` の値で、別の番号を書いていてもよい
    at = tokens.index("-p") if "-p" in tokens else -1
    return at >= 0 and tokens[at + 1:at + 3] == ["/dev-loop:dev-loop", str(number)]


def read_meta(path):
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Unknown(f"記録を読めない: {path}: {exc}") from exc
    if not isinstance(meta, dict) or not isinstance(meta.get("pid"), int) or not isinstance(meta.get("out"), str):
        raise Unknown(f"記録の形が違う: {path}")
    return meta


def cmd_launch(args, cwd=None):
    number = parse_number(args.number)
    if args.permission_mode not in PERMISSION_MODES:
        raise Usage(f"許可モードが違う: {args.permission_mode!r}（{', '.join(PERMISSION_MODES)}）")
    if args.permission_mode in REFUSED_MODES:
        raise Refused(f"{args.permission_mode} では起こさない——cruise は権限を広げない")
    brief_path = Path(args.brief)
    try:
        brief = brief_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Refused(f"委譲文を読めない: {brief_path}: {exc}") from exc
    if not brief.strip():
        raise Refused(f"委譲文が空: {brief_path}")
    if "{{" in brief:
        raise Refused(f"委譲文に差し込んでいない {{{{ }}}} が残っている: {brief_path}")
    directory, main_tree = children_dir(args.name, cwd)
    for record in records(directory, number):
        meta = read_meta(record)
        if is_running(meta["pid"], number):
            raise Refused(f"#{number} の子がまだ走っている（pid {meta['pid']}・{record}）——2 体目は起こさない")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    base = directory / f"{number}-{stamp}"
    out, err, meta_path = base.with_suffix(".jsonl"), base.with_suffix(".err"), base.with_suffix(".json")
    command = ["claude", "-p", f"/dev-loop:dev-loop {number}", "--output-format", "stream-json", "--verbose",
               "--permission-mode", args.permission_mode, "--append-system-prompt", brief]
    if args.model:
        command += ["--model", args.model]
    if args.max_budget_usd:
        command += ["--max-budget-usd", args.max_budget_usd]
    if args.allowed_tools:
        command += ["--allowedTools", *args.allowed_tools]  # 可変長なので最後に置く
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as out_f, open(err, "wb") as err_f:
            proc = subprocess.Popen(command, cwd=main_tree, stdin=subprocess.DEVNULL, stdout=out_f, stderr=err_f,
                                    start_new_session=True)
    except OSError as exc:
        for leftover in (out, err):
            leftover.unlink(missing_ok=True)
        raise Unknown(f"claude を起こせない: {exc}") from exc
    shown = [c if c != brief else f"<委譲文: {brief_path.resolve()}>" for c in command]
    meta = {"format": 1, "name": args.name, "number": number, "pid": proc.pid, "cwd": str(main_tree),
            "command": shown, "brief": str(brief_path.resolve()), "out": str(out), "err": str(err),
            "started": stamp}
    try:
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except OSError as exc:
        raise Unknown(f"子（pid {proc.pid}）は起きたが、記録を書けない: {exc}") from exc
    print(f"起こした: #{number}（pid {proc.pid}・cwd {main_tree}）")
    print(f"出力: {out}")
    print(f"標準エラー: {err}")
    print(f"台帳の agent: claude-p:{meta_path}")
    return EXIT_OK


def summarize(out_path):
    init, last_init, results, limit, last_text, broken = None, None, [], None, "", 0
    try:
        lines = Path(out_path).read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        lines = []
    except OSError as exc:
        raise Unknown(f"出力を読めない: {out_path}: {exc}") from exc
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            broken += 1
            continue
        if not isinstance(event, dict):
            broken += 1
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            # 同じプロセスで init が 2 度以上出て、途中から他のプラグインの版が変わった（probe2）——最初と最後の両方を持つ
            init = init or event
            last_init = event
        elif kind == "result":
            results.append(event)
        elif kind == "rate_limit_event":
            info = event.get("rate_limit_info") or {}
            if info.get("status") not in (None, "allowed", "allowed_warning"):
                limit = info
        elif kind == "assistant" and not event.get("parent_tool_use_id"):  # 委譲先の体の発言は子の文ではない
            for block in (event.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text" and block.get("text", "").strip():
                    last_text = block["text"]
    return {"init": init, "last_init": last_init, "results": results, "limit": limit, "last_text": last_text, "broken": broken}


def concerns(summary):
    found = []
    if not summary["results"]:
        return ["result が無い"]
    last = summary["results"][-1]
    if last.get("subtype") != "success" or last.get("is_error"):
        found.append(f"最後の result が成功でない（{last.get('subtype')}・is_error={last.get('is_error')}）")
    if last.get("api_error_status"):
        found.append(f"API の誤り {last.get('api_error_status')}")
    if last.get("permission_denials"):
        found.append(f"拒否された操作 {len(last['permission_denials'])} 件")
    killed = ((last.get("subagent_stats") or {}).get("killed") or {})
    if sum(v for v in killed.values() if isinstance(v, int)):
        found.append(f"殺された背景の体 {killed}")
    if summary["limit"]:
        found.append("利用上限の拒否")
    return found


def cmd_status(args, cwd=None):
    number = parse_number(args.number)
    directory, _ = children_dir(args.name, cwd)
    found = records(directory, number)
    if not found:
        raise Unknown(f"#{number} の子の記録が無い（{directory}）")
    meta = read_meta(found[-1])
    running = is_running(meta["pid"], number)
    summary = summarize(meta["out"])
    init = summary["init"] or {}
    def dev_loop_of(event):
        return [p.get("version") for p in (event or {}).get("plugins") or [] if isinstance(p, dict) and p.get("name") == "dev-loop"]
    dev_loop = dev_loop_of(init)
    later = dev_loop_of(summary["last_init"])
    if later != dev_loop:
        dev_loop = dev_loop + [f"→ 途中から {', '.join(map(str, later)) or '無し'}"]
    print(f"#{number}: {'走っている' if running else '終わった'}（pid {meta['pid']}・記録 {found[-1]}）")
    print(f"dev-loop の版: {', '.join(map(str, dev_loop)) or '無し'} ／ 許可モード: {init.get('permissionMode', '無し')}"
          f" ／ セッション: {init.get('session_id', '無し')}")
    results = summary["results"]
    if results:
        last = results[-1]
        denials = [clip(d.get("tool_name", d), 60) if isinstance(d, dict) else clip(d, 60)
                   for d in last.get("permission_denials") or []]
        stats = last.get("subagent_stats") or {}
        print(f"result: {len(results)} 個 ／ 最後: {last.get('subtype')}・is_error={last.get('is_error')}・"
              f"ターン {last.get('num_turns')}・費用 ${last.get('total_cost_usd')}・API の誤り {last.get('api_error_status')}")
        print(f"拒否された操作: {', '.join(denials[:10]) or 'なし'} ／ 背景の体: 起こした {stats.get('spawned')}・"
              f"終えた {stats.get('completed')}・殺された {stats.get('killed')}")
    else:
        print("result: 0 個")
    if summary["limit"]:
        info = summary["limit"]
        print(f"利用上限: {info.get('status')}（{info.get('rateLimitType')}・resetsAt {info.get('resetsAt')}）")
    if summary["broken"]:
        print(f"読めなかった行: {summary['broken']}")
    print(f"最後の文: {clip(summary['last_text']) or '無し'}")
    try:
        err_tail = [l for l in Path(meta.get("err", "")).read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    except OSError:
        err_tail = []
    if err_tail:
        print(f"標準エラーの末尾: {clip(' / '.join(err_tail[-3:]))}")
    if running:
        return EXIT_RUNNING
    problems = concerns(summary)
    if problems:
        print(f"要確認: {'・'.join(problems)}")
        return EXIT_REJECTED
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(description="cruise の周を claude -p の子プロセスで回す（#491）")
    sub = parser.add_subparsers(dest="command", required=True)
    launch = sub.add_parser("launch")
    launch.add_argument("name")
    launch.add_argument("number")
    launch.add_argument("--brief", required=True)
    launch.add_argument("--permission-mode", required=True)
    launch.add_argument("--model")
    launch.add_argument("--max-budget-usd")
    launch.add_argument("--allowed-tools", nargs="+")
    status = sub.add_parser("status")
    status.add_argument("name")
    status.add_argument("number")
    return parser


def main(argv=None, cwd=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE
    try:
        if args.command == "launch":
            return cmd_launch(args, cwd)
        return cmd_status(args, cwd)
    except Usage as exc:
        print(f"引数が違う: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except Refused as exc:
        print(f"起こさない: {exc}", file=sys.stderr)
        return EXIT_REJECTED
    except Unknown as exc:
        print(f"判定できない: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN


if __name__ == "__main__":
    raise SystemExit(main())
