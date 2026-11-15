#!/usr/bin/env python3
r"""cruise を外から繰り返し起こすループ（外側のループ）。`claude -p "/dev-loop:cruise <親> [--absent]"` を、進められる周があり、
起動のたびに周が進んでいるあいだだけ起こし直す（#791）。

    python3 <このスキルの base ディレクトリ>/scripts/outer-loop.py <親 Issue の番号> [--absent] \
        [--max-launches 20] [--max-stalls 2] [--max-total-usd <ドル>] [--claude claude] [-- <claude に足す引数> …]

**cruise の既定の回し方は、対話のセッションで 1 度起動して台帳から再開する形である**（cruise の `SKILL.md`）。これは、利用者が
その起動を自分で繰り返す代わりに、決まった条件で止まるループを同梱したもの——プロジェクトごとに手で書いたループは、前進を台帳の
ファイルのハッシュで見て、親が `note` を書き直すだけの起動を前進と読みうる（`ledger.py set` は `updated` を毎回書き換える）。
spec-loop の autopilot（#789）では、止まったことを見落とした外側のループが `claude -p` を約 1,900 回空回りさせた（#790）。

## 1 回の起動

台帳 `issue-<親>`（`../dev-loop/scripts/ledger.py`。このスキルの base ディレクトリからの相対）について、

1. `ledger.py status issue-<親>` を走らせる。**0（親が進められる周がある）のときだけ続ける**——3（人を待つ周だけ）・5（親 Issue の一覧の行が
   すべて済んだ）・4（判定できなかった）・表に無い値では起こさずに止まる。判定の順は `ledger.py` の docstring の「`status` が見るもの」を正とする。
2. `ledger.py progress issue-<親>`（行ごとの番号・`state`・`pr`・`group`。`updated`・`note` を含まない）を控える。
3. 起動の総数が `--max-launches` に達していれば、起こさずに止まる。**`--max-total-usd` を渡したなら**、費用を取れなかった起動・子が
   1 つでもあれば（12）、取れた分の合計が上限以上なら（11）、起こさずに止まる（下の「費用の数え方」）。
4. メインの作業ツリー（台帳と同じ決め方——`ledger.py path` の場所から）を cwd に、標準入力を閉じて

       <--claude> -p "/dev-loop:cruise <親>[ --absent]" --output-format stream-json --verbose --append-system-prompt <追記> [<足す引数> …]

   を起こし、終わるのを待つ。標準出力と標準エラーは台帳の隣の `cruise-issue-<親>-loop/` に起動ごとのファイル（`<NNN>-<UTC の時刻>.out`・`.err`）で残す
   （費用を読むため。#992）。環境には **`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`** を置く——`-p` はターンを閉じた後の背景のタスクを
   上限の時間（既定 10 分）しか待たずに止める（#633。標準エラーの `Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to wait indefinitely.`
   の文言による。0 で止めずに待つことは測っていない）。**利用者の環境に別の値があっても 0 で上書きし、上書きしたことを出す**（`child-cycle.py` と同じ）。
   **追記（`APPEND`）は、非対話の起動の決まりを親に渡す**——権限の判定に拒まれたら周を `await` にして次へ進み、「止まった」と書いて
   ターンを終えない（cruise `SKILL.md` §4 の 5）。進められる周が無いなら台帳を書き換えずにターンを終える（同 §4 の 6）。原本は `SKILL.md` で、追記はそこを指す。
5. その起動の費用と、子プロセスの周の費用を数え直し（下の「費用の数え方」）、`費用:` の行に出す。
6. `claude` が 0 以外で終わった・起こせなかったら止まる（ログインの期限切れなどで、何も進めずにすぐ終わる起動を繰り返さない）。
7. もう一度 `progress` を取り、2 と同じなら「前進なし」を 1 つ数える。**続けて `--max-stalls` 回になったら止まる**。変わっていれば数を 0 に戻す。

止まるときは、理由と費用（`費用: 取れた分の合計 …`）を標準出力の最後の行に出し、**通知する**（`osascript` が在れば macOS の通知。本文は argv で渡し、AppleScript の文字列に埋め込まない）。

既定の「前進なし 2 回」は、1 回の起動が周を最後まで進めない（関門の途中で compact した、など）のを 1 度だけ許すためである。

## 費用の数え方（#992）

- **親の起動**: 出力（stream-json）の**最後の** `result` の `total_cost_usd`。`result` が無い・その値が無い・数でない（真偽値・文字列）・負・有限でない・
  float に収まらない整数なら、**取れなかった起動**として数え、0 と数えない。`claude` を起こせなかった起動は費用を使っていないので数えない。
- **子プロセスの周**（`child-cycle.py`。台帳の隣の `cruise-issue-<親>-children/`）: **このループを起こした時に無かった記録だけ**を見る。
  走っている子は合計にも取れなかった数にも入れない（走りきってから数える。止めない）。終わった子は、出力の最後の `result` の `total_cost_usd` を
  合計に足し、読めなければ（記録・出力を読めない・`result` が無い・値が読めない）**取れなかった子**として数える。読み方は `child-cycle.py` の
  `read_meta`・`is_running`・`summarize` を読み込む（写さない）。
- **合計は、このループの起動の中だけ**——ループを起こし直すと 0 から数える（起動ごとの出力と子の記録は残る）。**台帳には書かない**——
  `ledger.py progress` に費用の欄は無く、前進の判定に混ざらない。
- **上限（`--max-total-usd`）は目安である**——`total_cost_usd` は API の料金に換算した推定で、サブスクリプションの利用枠そのものではなく、
  1 回の起動の途中では止めないので、最後の起動の分だけ上限を超えうる。
- **止まった行（通知の本文）には、上限を渡していなくても毎回費用を出す**——取れた分の合計・起動の回数と取れなかった回数（何回目か）、
  子が 1 体でもあれば子の数と取れなかった数・走っている数。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 済んだ——`status` が 5（親 Issue の一覧の行がすべてマージ済みか取り下げ） |
| 2 | 引数が違う（親の番号の形——先頭の 0 を外した桁数が `int()` の上限を超えるものを含む・上限が 1 未満・`--max-total-usd` が正の有限の数でない・`--claude` を語に分けられない）。**通知しない**（引数を読む前に止まる） |
| 3 | 人を待つ周だけ——`status` が 3。台帳の `show` の「利用者の判断待ち」「利用者の操作待ち」を見る |
| 4 | 判定できなかった——`status` が 4 か表に無い値・`progress` が 0 以外・`ledger.py` を起こせない・出力の置き場を作れない・ループの中の予期しない例外。**「済んだ」とも「人待ち」とも答えていない** |
| 6 | 前進なし——`progress` の変わらない起動が続けて `--max-stalls` 回 |
| 7 | 起動の上限——`--max-launches` 回起こした後も `status` が 0 |
| 8 | `claude` が 0 以外で終わった・起こせなかった |
| 11 | 費用の上限——取れた分の合計が `--max-total-usd` 以上で、`status` は 0 のまま |
| 12 | 費用を取れない——`--max-total-usd` を渡したのに、費用を取れなかった起動か終わった子がある（上限を守れると言えない） |
| 130 | 中断された（Ctrl-C・SIGTERM・SIGHUP。起動時に無視させられていたシグナルは除く） |

## 何を守り、何を守らないか

守る:

- **`status` が 0 のときだけ `claude` を起こす**——起動の前に毎回見て、3・4・5・表に無い値では起こさずに止まる。
- **前進は `progress` で比べる**——台帳のファイルのまま比べない（`updated`・`note` だけの書き換えを前進に数えない）。
- **`progress` を読めなければ止まる（4）**——読めない要約を「前進なし」「前進あり」のどちらにも数えない。
- **前進なしの起動が続けて `--max-stalls` 回になったら止まる。**
- **前進があったら、前進なしの数を 0 に戻す**——続けてでない前進なしで止めない。
- **起動の総数が `--max-launches` に達したら、起こさずに止まる。**
- **`claude` が 0 以外で終わった・起こせなかったら止まる。**
- **引数を読めた後の止まるすべての経路で通知する**——済んだ・人待ち・判定できない・前進なし・上限・`claude` の失敗・費用の上限・費用を取れない・中断（Ctrl-C・SIGTERM・SIGHUP）・ループの中の予期しない例外。
- **`claude` の cwd はメインの作業ツリー**——worktree の中・サブディレクトリから呼んでも同じ（cruise の親はメインの作業ツリーで起動する。#466）。
- **`claude` の環境に `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` を置く**——利用者の環境に無くても、別の値があっても（上書きしたと出す）。
- **`--append-system-prompt` で追記（`APPEND`）を渡す**——非対話の起動の決まり（拒まれたら `await`・進めないなら台帳を書かない）。
- **親の番号は先頭の 0 を外して読み、桁数で狭めない**——19 桁以上も受ける（`int()` の上限の桁数まで）。
- **0 を外した桁数が `int()` の上限を超える番号は 2 で拒む**——例外（1）で終わらせない。
- **`--absent` は渡されたときだけ `/dev-loop:cruise` に付ける**——席を外すかは利用者が決める（cruise `SKILL.md` §3）。
- **起動時に無視させられていた SIGTERM・SIGHUP（`nohup` の SIGHUP など。SIG_IGN）にはハンドラを置かない**——無視したまま回り続ける
  （`spec-loop` の `render-diagrams.py` と同じ。#820）。
- **中断されたら、`claude` にまず SIGTERM を送って `GRACE` 秒（既定 10）終わるのを待つ**——いきなり SIGKILL にしない（後始末の機会を残す）。
- **`GRACE` 秒で終わらなければ SIGKILL で止める**——`claude` を残したまま終わらない。
- **`--output-format stream-json --verbose` で起こし、出力を台帳の隣の `cruise-issue-<親>-loop/` に起動ごとに残す**——費用を読むため（#992）。
- **起動の費用は、出力の最後の `result` で読む**——前の `result` の値を使わない。
- **費用の読めない起動を 0 と数えない**——取れなかった起動として数える。
- **真偽値を費用と読まない**——Python の `bool` は `int` の仲間なので、`isinstance` だけでは `true` が 1 ドルになる。
- **負・有限でない値を費用と読まない。**
- **float に収まらない整数で落ちず、取れなかったと数える。**
- **起こせなかった起動は、費用を数える起動に入れない。**
- **取れた分の合計が `--max-total-usd` 以上なら、次を起こさずに止まる（11）**——ちょうど上限でも起こさない。
- **`--max-total-usd` を渡したなら、費用を取れなかった起動・終わった子があれば、次を起こさずに止まる（12）。**
- **`--max-total-usd` を渡さなければ、費用を取れなくても止めない**——止まった行に数を出すだけ。
- **子プロセスの周の費用を合計に入れる**（`cruise-issue-<親>-children/` の記録の最後の `result`）。
- **ループを起こした時に在った子の記録は数えない**——前のループ・前の cruise の子の費用を足さない。
- **走っている子は、合計にも取れなかった数にも入れない**——止めずに、止まった行に数を出す。
- **止まった行（通知の本文）に、費用の合計と取れなかった起動の数を出す**——上限を渡していなくても・費用で止まったのでなくても。
- **中断・例外で終わった起動を、取れなかった起動として数える**——走った起動を数えずに合計を少なく見せない（#992 の 1 パス目）。
- **上限を見る直前に子の記録を数え直す**——前の起動の後に走りきった子の費用を、次を起こす判定に入れる（#992 の 1 パス目）。
- **済んだ・人待ちの判定は、費用の上限より先**——最後の起動で済んだのに「上限」と言わない。

守らない:

- **親が追記に従うか**——`--append-system-prompt` で渡すまでで、本物の `claude -p` で親が拒まれた周を `await` にするか・台帳を書かずに終えるかは測っていない。
- **台帳と実物（PR・worktree）が一致しているか**——`status` も `progress` も台帳の値だけで決める（`ledger.py` の「守らない」）。
- **通知が見えること**——`osascript` が 0 で終わったかも見ない。`osascript` の無い環境（macOS 以外）では通知を出さない（理由は標準出力に出る）。
- **1 回の起動の長さ**——`claude` を待つだけで、時間で打ち切らない。
- **`claude` の版・許可モード・モデル・認証**——足す引数（`--` の後ろ）と `--claude` で利用者が決める（cruise `SKILL.md` §3 の点検）。
  長期トークンの起動口（`../dev-loop/scripts/launch-with-long-token.sh`）に `-p` を渡す形は確かめていない。
- **同じ台帳を回すループ・対話の cruise が他に走っていないか**——台帳を書くのは親 1 体である（`../dev-loop/references/ledger.md`）。
- **本物の `total_cost_usd` が何を含むか**——1 回だけ測った（2026-11-15・Claude Code 2.1.325・haiku・背景の `Agent` 1 体）——`result` は 3 つで、`total_cost_usd` はどれも同じ値、`modelUsage` の累計は親の 2 ターンと背景の体の分を足した量だった（背景の体の分を含み、最後の `result` は累計）。
  `/code-review` の fork・実際の cruise の長い起動では測っていない。使用量の上限・中断で終わった起動の `result` に費用が載るかも測っていない（載らなければ取れなかった起動になる）。
- **上限を超えないこと**——判定は起動と起動の間だけで、起動の途中では止めない。値は API の料金に換算した推定で、利用枠そのものではない。
- **ループを起こし直した後の合計**——このループの起動の中だけを数える（台帳に書かないので、前のループの分を数える出所が無い）。
- **子の記録が子プロセスの周のものか**——`cruise-issue-<親>-children/` の `.json` を子の記録として読む。走っているかの判定は `child-cycle.py` の `is_running` の「守らない」を引き継ぐ。
- **出力の置き場（`cruise-issue-<親>-loop/`）を消すこと・大きさ**——起動ごとにファイルが増える。
"""

import argparse
import datetime
import importlib.util
import json
import math
import os
import re
import signal
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent.parent / "dev-loop" / "scripts" / "ledger.py"
# 子プロセスの周の記録の読み方（#992）。写しを作らずに読み込む
CHILD_CYCLE = Path(__file__).resolve().parent / "child-cycle.py"
BG_CEILING = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"
GRACE = 10  # 中断のとき claude の後始末を待つ秒数（過ぎたら SIGKILL）
# 非対話の起動の決まり（#791）。原本は cruise の SKILL.md §4 の 5・6——ここはそれを指す 2 文だけ
APPEND = (
    "この起動は cruise の外側のループ（outer-loop.py）が起こした非対話の起動で、利用者は応答しない（#791）。"
    "権限の判定（自動モードの分類器・許可リスト・ガード）に操作を拒まれたら、cruise の SKILL.md の「4. 周を回す」の 5 のとおり、"
    "その周を `state=await` にして（`note` の書き方もその 5 に従う）依存しない次の周へ進む——「止まった」と書いてターンを終えない。"
    "進められる周が無いなら、台帳を書き換えずにターンを終える——確かめた回数・時刻・「変わらず」を `note` に書かない（同じ「4. 周を回す」の 6）。"
)
TITLE = "cruise の外側のループが止まりました"

EXIT_DONE = 0
EXIT_USAGE = 2
EXIT_WAITING = 3
EXIT_UNKNOWN = 4
EXIT_STALLED = 6
EXIT_LIMIT = 7
EXIT_CLAUDE = 8
EXIT_BUDGET = 11
EXIT_COST_UNKNOWN = 12
EXIT_INTERRUPTED = 130


def ledger(*args):
    """(終了コード, 標準出力)。起こせなければ (None, 理由)。"""
    try:
        r = subprocess.run([sys.executable, str(LEDGER), *args], capture_output=True, text=True)
    except OSError as exc:
        return None, f"ledger.py を起こせない: {exc}"
    if r.stderr:
        sys.stderr.write(r.stderr)
    return r.returncode, r.stdout


def progress(name):
    code, out = ledger("progress", name)
    return out if code == 0 else None


def notify(body):
    if not shutil.which("osascript"):
        return
    # 値は argv で渡す（AppleScript の文字列に埋め込まない）
    script = ("on run argv\n"
              "display notification (item 1 of argv) with title (item 2 of argv)\n"
              "end run")
    try:
        subprocess.run(["osascript", "-e", script, body, TITLE],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def cost_of(value):
    """費用の値を float で。読めなければ None——数でない・真偽値・負・有限でない・float に収まらない整数を 0 と読まない。"""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except OverflowError:  # 桁の多すぎる整数——例外にせず読めないものとして扱う
        return None
    return value if math.isfinite(value) and value >= 0 else None


def read_cost(path):
    """その起動の費用（出力の最後の `result` の `total_cost_usd`）。`result` が無い・値が読めなければ None。"""
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    last = None
    for line in lines:
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            last = event
    return cost_of(last.get("total_cost_usd")) if last is not None else None


def child_cycle():
    spec = importlib.util.spec_from_file_location("child_cycle_for_outer_loop", CHILD_CYCLE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def child_costs(directory, seen):
    """ループを起こした後に起きた子（`seen` に無い記録）の (取れた合計, 数えた子の数, 取れなかった子, 走っている子)。"""
    known, counted, missing, running = 0.0, 0, [], []
    if not directory.is_dir():
        return known, counted, missing, running
    cc = None
    for meta_path in sorted(directory.glob("*.json")):
        if meta_path.name in seen:
            continue
        label = meta_path.stem
        try:
            cc = cc or child_cycle()
            meta = cc.read_meta(meta_path)
            if cc.is_running(meta["pid"], meta.get("number")):
                running.append(label)
                continue
            results = cc.summarize(meta["out"])["results"]
        except Exception:  # noqa: BLE001 — 読めない記録・確かめられないプロセスを 0 と読まない
            missing.append(label)
            continue
        cost = cost_of(results[-1].get("total_cost_usd")) if results else None
        if cost is None:
            missing.append(label)
        else:
            known += cost
            counted += 1
    return known, counted, missing, running


class Costs:
    """このループの起動の中の費用（#992）。台帳には書かない——`progress` に混ぜない。"""

    def __init__(self):
        self.known = 0.0  # 親の起動の取れた分
        self.launches = 0  # 費用を数えた起動（起こせなかった起動は入れない）
        self.missing = []  # 取れなかった起動の番号
        self.children = (0.0, 0, [], [])  # child_costs の戻り値

    def add(self, n, cost):
        self.launches += 1
        if cost is None:
            self.missing.append(n)
        else:
            self.known += cost

    def total(self):
        return self.known + self.children[0]

    def unknown(self):
        return bool(self.missing or self.children[2])

    def summary(self):
        line = f"取れた分の合計 ${self.total():.2f}・起動 {self.launches} 回のうち取れなかった {len(self.missing)} 回"
        if self.missing:
            line += "（" + "・".join(f"{n} 回目" for n in self.missing) + "）"
        _, counted, missing, running = self.children
        if counted or missing or running:
            line += f"・子 {counted + len(missing) + len(running)} 体のうち取れなかった {len(missing)} 体・走っている {len(running)} 体（合計に入れていない）"
        return line


def launch(args, main_tree, logs, n):
    """(終了コード か None, 標準出力のファイル)。"""
    prompt = f"/dev-loop:cruise {args.parent}" + (" --absent" if args.absent else "")
    cmd = [*args.claude_cmd, "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--append-system-prompt", APPEND, *args.extra]
    env = dict(os.environ)
    if env.get(BG_CEILING) not in (None, "0"):
        print(f"{BG_CEILING}={env[BG_CEILING]} を 0 で上書きした")
    env[BG_CEILING] = "0"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out, err = logs / f"{n:03d}-{stamp}.out", logs / f"{n:03d}-{stamp}.err"
    print(f"起こす: {shlex.join(cmd[:3])} …（cwd: {main_tree}・出力: {out}）", flush=True)
    proc = None
    try:
        with open(out, "wb") as fo, open(err, "wb") as fe:
            proc = subprocess.Popen(cmd, cwd=main_tree, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe, env=env)
            return proc.wait(), out
    except OSError as exc:
        print(f"claude を起こせない: {exc}", file=sys.stderr)
        return None, out
    except BaseException:  # 中断（Ctrl-C・SIGTERM・SIGHUP）——`subprocess.run` のようにいきなり SIGKILL にしない
        if proc is not None:
            stop_child(proc)
        raise


def stop_child(proc):
    """claude に SIGTERM を送り、`GRACE` 秒待っても終わらなければ SIGKILL。"""
    try:
        proc.terminate()
    except OSError:
        pass
    try:
        proc.wait(timeout=GRACE)
    except BaseException:  # 時間切れ・待つあいだの 2 度目の中断——claude を残して終わらない
        proc.kill()
        proc.wait()


def run_loop(args):
    """(終了コード, 理由)。"""
    name = f"issue-{args.parent}"
    code, out = ledger("path", name)
    if code != 0:
        return EXIT_UNKNOWN, f"台帳の場所を決められない（ledger.py path: {code}）"
    path = Path(out.strip())
    main_tree = path.parent.parent.parent
    logs = path.parent / f"cruise-{name}-loop"
    children = path.parent / f"cruise-{name}-children"
    try:
        logs.mkdir(parents=True, exist_ok=True)
        seen = {p.name for p in children.glob("*.json")} if children.is_dir() else set()
    except OSError as exc:
        return EXIT_UNKNOWN, f"出力の置き場を作れない（{logs}: {exc}）"
    costs = args.costs
    launches = stalls = 0
    while True:
        code, out = ledger("status", name)
        print(f"status: {code} {out.strip()}", flush=True)
        if code == 5:
            return EXIT_DONE, f"済んだ（{out.strip()}）"
        if code == 3:
            return EXIT_WAITING, f"人を待つ周だけ（{out.strip()}）"
        if code != 0:
            return EXIT_UNKNOWN, f"判定できなかった（status: {code}）"
        before = progress(name)
        if before is None:
            return EXIT_UNKNOWN, "判定できなかった（progress を読めない）"
        if launches >= args.max_launches:
            return EXIT_LIMIT, f"起動の上限 {args.max_launches} 回に達した（status は 0 のまま）"
        if args.max_total_usd is not None:
            costs.children = child_costs(children, seen)  # 前の起動の後に走りきった子も入れて判定する
            if costs.unknown():
                return EXIT_COST_UNKNOWN, f"費用を取れない起動か子がある——上限 ${args.max_total_usd:.2f} を守れると言えないので起こさない"
            if costs.total() >= args.max_total_usd:
                return EXIT_BUDGET, f"費用の上限 ${args.max_total_usd:.2f} に達した（status は 0 のまま）"
        launches += 1
        try:
            rc, out = launch(args, main_tree, logs, launches)
        except BaseException:  # 中断・例外——走った起動の費用を読めないので、取れなかったと数える
            costs.add(launches, None)
            raise
        if rc is not None:
            costs.add(launches, read_cost(out))
        costs.children = child_costs(children, seen)
        print(f"費用: {costs.summary()}", flush=True)
        if rc != 0:
            return EXIT_CLAUDE, f"claude が失敗した（{rc if rc is not None else '起こせない'}・{launches} 回目の起動）"
        after = progress(name)
        if after is None:
            return EXIT_UNKNOWN, "判定できなかった（progress を読めない）"
        if after == before:
            stalls += 1
            print(f"前進なし（続けて {stalls} 回）", flush=True)
            if stalls >= args.max_stalls:
                return EXIT_STALLED, f"前進なしが続けて {stalls} 回（{launches} 回目の起動）"
        else:
            stalls = 0


def build_parser():
    p = argparse.ArgumentParser(description="cruise を外から繰り返し起こすループ（#791）")
    p.add_argument("parent", help="親 Issue の番号")
    p.add_argument("--absent", action="store_true", help="/dev-loop:cruise に --absent を付ける")
    p.add_argument("--max-launches", type=int, default=20, help="起動の総数の上限（既定 20）")
    p.add_argument("--max-stalls", type=int, default=2, help="前進なしが続けてこの回数で止まる（既定 2）")
    p.add_argument("--max-total-usd", type=float, default=None, help="費用の合計の上限（ドル。既定なし——上限なし）")
    p.add_argument("--claude", default="claude", help="claude を起こすコマンド（既定 claude）")
    return p


class Interrupted(Exception):
    """SIGTERM・SIGHUP を受けた。"""


def _on_signal(signum, _frame):
    raise Interrupted(signal.Signals(signum).name)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # `--` の後ろは claude に足す引数。argparse に任せない——Python 3.11 以前は、位置引数の後に選択肢があると `--` の後ろを拒む
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    head = argv[:argv.index("--")] if "--" in argv else argv
    try:
        args = build_parser().parse_args(head)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else 0
    args.extra = extra
    try:
        args.claude_cmd = shlex.split(args.claude)
    except ValueError:
        args.claude_cmd = []
    # ASCII の数字だけ——`str.isdigit()` は `²` も真にし、`int()` が読めずに例外で終わる。先頭の 0 は読み飛ばす（`050` は 50）。
    # 0 を外した残りの桁数が `int()` の上限（Python 3.11 以降の `sys.get_int_max_str_digits()`。0 は上限なし）を超えるものだけ拒む
    number = re.fullmatch(r"0*([1-9][0-9]*)", args.parent)
    limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
    if (not number or (limit and len(number.group(1)) > limit) or args.max_launches < 1 or args.max_stalls < 1
            or (args.max_total_usd is not None and not (math.isfinite(args.max_total_usd) and args.max_total_usd > 0))
            or not args.claude_cmd):
        print("引数が違う: 親は正の番号、上限は 1 以上、--max-total-usd は正の有限の数、--claude は語に分けられるコマンド", file=sys.stderr)
        return EXIT_USAGE
    args.costs = Costs()
    args.parent = str(int(number.group(1)))
    # **起動時に無視させられていたら（`nohup` の SIGHUP など。SIG_IGN）置かない**——上書きすると、無視させて起動した側の意図を破って止まる（#820 と同じ）
    saved = {s: signal.signal(s, _on_signal) for s in (signal.SIGTERM, signal.SIGHUP)
             if signal.getsignal(s) != signal.SIG_IGN}
    try:
        code, reason = run_loop(args)
    except KeyboardInterrupt:
        code, reason = EXIT_INTERRUPTED, "中断された"
    except Interrupted as exc:
        code, reason = EXIT_INTERRUPTED, f"中断された（{exc}）"
    except Exception as exc:  # noqa: BLE001 — どの経路でも通知する（守る）
        code, reason = EXIT_UNKNOWN, f"判定できなかった（予期しない例外: {type(exc).__name__}: {exc}）"
    finally:
        for s, h in saved.items():
            signal.signal(s, h)
    line = f"外側のループ: 止まった（issue-{args.parent}: {reason}）"
    line += f" 費用: {args.costs.summary()}"
    print(line, flush=True)
    notify(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
