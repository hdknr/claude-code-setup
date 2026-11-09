#!/usr/bin/env python3
r"""TLC（TLA+ のモデル検査器）が、正本リポジトリの `CLAUDE.md` に書いた呼び方で使えるかを確かめる（#912）。

    python3 <spec-loop の根>/scripts/check-tlc.py <正本リポジトリの根> [--autopilot]

**読むだけ**——正本リポジトリにも設定にも書かない。モデルは一時ディレクトリに書いて走らせ、終わったら消す。

## なぜ在るのか（#912）

業務フロー（並行・リトライ・取り消し）を形式検査の対象に選んだのに TLC が無いと、spec-review は判定役を 1 体も起動せず、
用意してから呼び直すか、用意せずに進める（業務フローは判定できなかったになり、その回は抜けない）かを訊く。
TLC はふつう `tla2tools.jar` で入れるので `command -v` では見つからず（#368 の残課題 CR4）、入っているのに「無い」として止まりえた。
**TLC は spec-loop の既定で必須の前提**であり（README の「前提」）、**呼び方は正本の `CLAUDE.md` に書く**。
spec-review の確かめ（手順 3）と autopilot の起動時の点検はこのスクリプトで確かめ、Formal Checker は同じ呼び方を使う。

## 正本の `CLAUDE.md` に書く行

**正本リポジトリの根の `CLAUDE.md` に、行頭から 1 行ずつ書く**（このスクリプトがここを原本として読む。README・スキルはここを指す）:

| 行 | 意味 |
| --- | --- |
| `TLC の呼び方: <コマンド>` | TLC を起動するコマンド。**後ろにモデルのファイル（`<名前>.tla`。設定は同じ名前の `.cfg`）を足し、モデルのディレクトリで `sh` に渡す**。例: `TLC の呼び方: java -cp /opt/tla/tla2tools.jar tlc2.TLC` |
| `業務フローの形式検査: しない` | 業務フローを一度も形式検査しない案件が、TLC を必須から外す宣言。値は `しない` だけ |

- **コードフェンス（` ``` `・`~~~`）の中の行は読まない**——例として書いた行を宣言と読まない。フェンスの開け閉めは CommonMark のとおり
  （同じ文字の 3 つ以上で開き、同じ文字で、開きと同じか長い、info string の無い行で閉じる。4 つのバッククォートの中の 3 つは閉じない）。
- **先頭の BOM は外して読む。**
- **コロンは半角（`:`）でも全角（`：`）でもよい**——日本語の入力で全角になりやすい。
- **同じ行を 2 行以上書かない・外す宣言の値は `しない` だけ・呼び方を空にしない**——どれも「判定できない」（4）。
- **外す宣言が古くなっても（後の版で業務フローを対象に選んだ）守らせる仕組みは無い**——spec-review が対象を選んだときに
  このスクリプトを（`--autopilot` なしで）呼び、TLC が無ければ今のとおり判定役を起動せずに訊く。

## 確かめ方

呼び方で 2 つの小さいモデルを一時ディレクトリで検査させる:

1. **通るモデル**——終了コードが 0 で、出力に `No error has been found` が出れば通った。
2. **違反するモデル（陽性対照）**——出力に `is violated` が出れば通った（終了コードは見ない）。
   **何にでも「エラーなし」と言う呼び方を「在る」と読まない**ためである。

**`command -v` では探さない**——呼び方の行が無ければ、`PATH` に `tlc` が在っても「無い」（1）。探し方を呼び方の 1 つに揃えるためである。

- **`--autopilot` なし**（spec-review の手順 3。業務フローを対象に選んだときに呼ぶ）: 外す宣言が有っても呼び方を確かめる（宣言が古いと出す）。
- **`--autopilot`**（autopilot の各起動）: 外す宣言が有れば確かめずに 0（呼び方を走らせない）。無ければ確かめる。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 呼び方が通った（`--autopilot` では、外す宣言が有って確かめなかったときも） |
| 1 | TLC が無い——呼び方の行が無い（`CLAUDE.md` が無いを含む）か、呼び方が通らない（時間切れを含む） |
| 2 | 引数が違う |
| 4 | 判定できなかった——`CLAUDE.md` を読めない、同じ宣言が 2 行以上、外す宣言の値が `しない` でない、呼び方が空 |

## 何を守り、何を守らないか

守る:

- **呼び方の行が無い正本を 0 にしない**——`--autopilot` でも、外す宣言が無ければ 1。
- **通るモデルを通さない呼び方を 0 にしない**——終了コードが 0 でないか、`No error has been found` が出なければ 1。
- **違反するモデルで違反を出さない呼び方を 0 にしない**——何にでも「エラーなし」と言う呼び方は 1（陽性対照）。
- **`command -v` で探さない**——呼び方の行が無ければ、`PATH` に `tlc` が在っても 1。
- **コードフェンスの中の行を宣言と読まない。**
- **フェンスを閉じるのは、同じ文字で開きと同じか長い、info string の無い行だけ**——4 つのバッククォートの中の 3 つや、` ```bash ` の行で閉じない。
- **先頭の BOM を外して読む**——BOM つきで保存した `CLAUDE.md` の 1 行目の宣言を落とさない。
- **全角のコロンの行も読む**——`TLC の呼び方：`・`業務フローの形式検査：` を「行が無い」と読まない。
- **同じ宣言が 2 行以上なら 4**——どれを使うかを決めない。
- **外す宣言の値が `しない` でなければ 4**——近い値（`無し`・`しない（v2 から）`）で外さない。
- **`--autopilot` で外す宣言が有れば、呼び方を走らせずに 0。**
- **`--autopilot` が無ければ、外す宣言が有っても呼び方を確かめる**——spec-review は対象を選んだときに呼ぶ。
- **読めない `CLAUDE.md` を「書いていない」と読まない**——4。
- **時間切れで待ち続けない**——1 回の検査を `PROBE_TIMEOUT` 秒で止め（プロセスグループごと）、1。
- **正本リポジトリに書かない**——モデルは一時ディレクトリに書いて、そこで走らせる。

守らない:

- **HTML コメント（`<!-- -->`）の中の行も読む**——コメントで消した宣言を消えたと読まない。
- **TLC の版による出力の違い**——判定に使う 2 つの文字列（`No error has been found`・`is violated`）と 2 つのモデルは、
  TLC 2.19（`tla2tools.jar` v1.7.4）で確かめた（#912 の周。モデルが通り、違反するモデルで `Error: Invariant Inv is violated.` と終了コード 12）。
  ほかの版は確かめていない。**回帰テストは偽の TLC で当てる**ので、モデルの中身（TLC が意味解析で落とす書き方）はテストでは見えない。
- **呼び方が、Formal Checker が書く大きいモデルを検査できるか**（メモリ・時間・モジュール）——小さいモデル 2 つを検査できることだけを見る。
- **呼び方の安全**——正本の `CLAUDE.md` に書いた文字列をそのまま `sh` で走らせる（正本の `CLAUDE.md` は利用者が書くもので、Formal Checker も同じ文字列を走らせる）。
- **子孫のプロセスが自分で別のプロセスグループに移ったとき**——時間切れで止めるのはプロセスグループまで。
- **Alloy**——#912 の範囲の外。
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

# CommonMark のコードフェンス: 字下げ 3 つまで・同じ文字（` か ~）が 3 つ以上・後ろは info string
FENCE_RE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
CALL_KEY = "TLC の呼び方:"
OPT_OUT_KEY = "業務フローの形式検査:"
OPT_OUT_VALUE = "しない"
PROBE_TIMEOUT = 120

# 標準モジュール（Naturals など）を EXTENDS しない形にする——算術の `-` は Naturals が無いと意味解析で落ちる（本物の TLC 2.19 で確かめた）
GOOD_MODEL = ("Probe", "---- MODULE Probe ----\nVARIABLE x\nInit == x = FALSE\nNext == x' = ~x\nInv == x \\in BOOLEAN\n====\n")
BROKEN_MODEL = ("Broken", "---- MODULE Broken ----\nVARIABLE x\nInit == x = FALSE\nNext == x' = ~x\nInv == x = FALSE\n====\n")
MODEL_CFG = "INIT Init\nNEXT Next\nINVARIANT Inv\n"
GOOD_MARK = "No error has been found"
BROKEN_MARK = "is violated"

EXIT_OK = 0
EXIT_MISSING = 1
EXIT_USAGE = 2
EXIT_UNKNOWN = 4


class Unknown(Exception):
    """判定できなかった（4）。"""


def read_declarations(root):
    """正本の `CLAUDE.md` の宣言。(呼び方 or None, 外すか, 注記)。`CLAUDE.md` が無ければ (None, False, 注記)。"""
    path = Path(root) / "CLAUDE.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None, False, f"{path} が無い"
    except (OSError, ValueError) as e:
        raise Unknown(f"{path} を読めない: {e}")
    text = text.removeprefix("\ufeff")
    calls, opt_outs = [], []
    fence = None  # 開いているフェンスの (文字, 長さ)
    for line in text.splitlines():
        m = FENCE_RE.fullmatch(line)
        if fence is None:
            # バッククォートのフェンスの info string にバッククォートは置けない（CommonMark）
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence = (m.group(1)[0], len(m.group(1)))
                continue
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and not m.group(2).strip():
                fence = None
            continue
        call, opt_out = after_key(line, CALL_KEY), after_key(line, OPT_OUT_KEY)
        if call is not None:
            calls.append(call.strip())
        elif opt_out is not None:
            opt_outs.append(opt_out.strip())
    if len(calls) > 1:
        raise Unknown(f"`{CALL_KEY}` の行が {len(calls)} 行ある（どれを使うか決めない）")
    if len(opt_outs) > 1:
        raise Unknown(f"`{OPT_OUT_KEY}` の行が {len(opt_outs)} 行ある")
    if opt_outs and opt_outs[0] != OPT_OUT_VALUE:
        raise Unknown(f"`{OPT_OUT_KEY}` の値が `{OPT_OUT_VALUE}` でない: {opt_outs[0]!r}")
    if calls and not calls[0]:
        raise Unknown(f"`{CALL_KEY}` の呼び方が空")
    note = "" if calls else f"{path} に `{CALL_KEY}` の行が無い"
    return (calls[0] if calls else None), bool(opt_outs), note


def after_key(line, key):
    """行頭が `key`（コロンは半角か全角）なら、その後ろ。違えば None。"""
    for k in (key, key[:-1] + "："):
        if line.startswith(k):
            return line[len(k):]
    return None


def run_model(call, workdir, name, timeout):
    """呼び方でモデル 1 つを検査させる。(終了コード or None（時間切れ・起動できない）, 出力)。"""
    try:
        proc = subprocess.Popen(["/bin/sh", "-c", f"{call} {name}.tla"], cwd=workdir, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, errors="replace",
                                start_new_session=True)
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        with_group(proc, signal.SIGKILL)
        out, _ = proc.communicate()
        return None, (out or "") + f"\n（{timeout} 秒で時間切れ）"
    except OSError as e:
        return None, f"起動できない: {e}"


def with_group(proc, sig):
    try:
        os.killpg(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def probe(call, timeout=None):
    """呼び方が TLC として通るか。(通ったか, 説明)。"""
    timeout = PROBE_TIMEOUT if timeout is None else timeout
    with tempfile.TemporaryDirectory(prefix="spec-loop-check-tlc-") as tmp:
        for name, body in (GOOD_MODEL, BROKEN_MODEL):
            (Path(tmp) / f"{name}.tla").write_text(body, encoding="utf-8")
            (Path(tmp) / f"{name}.cfg").write_text(MODEL_CFG, encoding="utf-8")
        rc, out = run_model(call, tmp, GOOD_MODEL[0], timeout)
        if rc != 0 or GOOD_MARK not in out:
            return False, f"通るモデルを通さなかった（終了コード {rc}）: {tail(out)}"
        rc, out = run_model(call, tmp, BROKEN_MODEL[0], timeout)
        if BROKEN_MARK not in out:
            return False, f"違反するモデルで違反を出さなかった（終了コード {rc}。TLC として検査していない）: {tail(out)}"
    return True, "通るモデルを通し、違反するモデルで違反を出した"


def tail(out, n=3):
    lines = [line for line in (out or "").splitlines() if line.strip()]
    return " / ".join(lines[-n:]) if lines else "（出力なし）"


def judge(root, autopilot=False):
    """(終了コード, 出力の行, 外す宣言で確かめなかったか)。"""
    try:
        call, opt_out, note = read_declarations(root)
    except Unknown as e:
        return EXIT_UNKNOWN, [f"判定できなかった: {e}"], False
    if opt_out and autopilot:
        return EXIT_OK, [f"`{OPT_OUT_KEY} {OPT_OUT_VALUE}` の宣言がある——TLC を確かめていない（必須から外している）"], True
    lines = []
    if opt_out:
        lines.append(f"注記: `{OPT_OUT_KEY} {OPT_OUT_VALUE}` と宣言しているが、業務フローを対象に選んだなら宣言が古い")
    if call is None:
        return EXIT_MISSING, lines + [f"TLC が無い: {note}（`command -v` では探さない）",
                                      f"用意のしかた: Java と `tla2tools.jar` を置き、正本の `CLAUDE.md` に `{CALL_KEY} <コマンド>` を書く"
                                      f"（業務フローを形式検査しない案件なら `{OPT_OUT_KEY} {OPT_OUT_VALUE}`）"], False
    ok, detail = probe(call)
    if not ok:
        return EXIT_MISSING, lines + [f"TLC が無い: 呼び方 `{call}` が通らない——{detail}"], False
    return EXIT_OK, lines + [f"TLC が在る: 呼び方 `{call}`——{detail}"], False


def main(argv=None):
    p = argparse.ArgumentParser(description="TLC が正本の CLAUDE.md の呼び方で使えるかを確かめる（読むだけ）")
    p.add_argument("root", type=Path, help="正本リポジトリの根（CLAUDE.md の在る場所）")
    p.add_argument("--autopilot", action="store_true", help="外す宣言が有れば確かめない（autopilot の各起動）")
    try:
        args = p.parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    code, lines, _ = judge(args.root, args.autopilot)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
