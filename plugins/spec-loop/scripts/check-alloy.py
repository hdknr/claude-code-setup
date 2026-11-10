#!/usr/bin/env python3
r"""Alloy（権限・ロールの検査器）が、正本リポジトリの `CLAUDE.md` に書いた呼び方で使えるかを確かめる（#922）。

    python3 <spec-loop の根>/scripts/check-alloy.py <正本リポジトリの根>

**読むだけ**——正本リポジトリにも設定にも書かない。モデルは一時ディレクトリに書いて走らせ、終わったら消す。

## なぜ在るのか（#922）

spec-review の起動前の確かめが Alloy を**引数なしで呼び、Alloy の画面（GUI）が開いて約 2 分止まった**（利用者の MacBook）。
Alloy 6 の jar（とその薄いラッパー）は、引数なしか `gui` で GUI を起動する。以前の確かめは「呼び方で版かヘルプを出す。無ければ `command -v` で探す」で、
どの形で呼ぶかを決めておらず、出たとしても実際の検査（`exec`）が動くことは言えなかった。
TLC（`check-tlc.py`。#912）と同じ形にした——**呼び方は正本の `CLAUDE.md` に書き**、その呼び方に小さいモデルを CLI（`exec`）で検査させて「在る」を決める。
**Alloy は必須の前提ではない**——権限・ロールを形式検査の対象に選んだときだけ、spec-review の手順 3 がこのスクリプトで確かめる。

## 正本の `CLAUDE.md` に書く行

**正本リポジトリの根の `CLAUDE.md` に、行頭から 1 行で書く**（このスクリプトがここを原本として読む。README・スキル・Formal Checker はここを指す）:

| 行 | 意味 |
| --- | --- |
| `Alloy の呼び方: <コマンド>` | Alloy に**モデルを CLI で検査させる**コマンド。**サブコマンド `exec` まで含めて書く**。**後ろにモデルのファイル（`<名前>.als`）を足し、モデルのディレクトリで `sh` に渡す**。例: `Alloy の呼び方: java -jar /opt/alloy/alloy.jar exec`・`Alloy の呼び方: alloy exec`（`alloy` が jar を起動するラッパーのとき） |

- **引数なし・`gui` の形で呼ばない**——Alloy 6 の jar はどちらでも GUI を起動し、画面が開いたまま検査が止まる。
  **呼び方に語 `exec` が無いか、`gui` が在れば（クォートで 1 語にした中の `gui` も）、走らせずに「判定できない」（4）**——この 2 つの形を確かめのために起こさない。
- **1 つのコマンドの形で書く**——呼び方は `sh` に渡すので、シェルの組み立て（`;`・`&`・`|`・`<`・`>`・`(`・`)`・`$`・`` ` ``・`#`・`\`・改行・
  ブレースとグロブの展開の `{`・`}`・`*`・`?`・`[`・`]`）を含む呼び方と、**先頭が `java` でも名前に `alloy` を含むコマンドでもない呼び方**（シェルの組み込み `exec`・`trap`、
  別のシェル `sh -c`・`tcsh -c`、環境変数の代入 `FOO=1 …`、`!` など）は、語に `exec` が在っても Alloy のサブコマンドになるとは限らないので、**走らせずに 4**。とくに**ラッパーの本文（`exec java -jar … "$@"`）をそのまま写さない**——
  先頭の `exec` はシェルの組み込みで、Alloy のサブコマンドではない。パスに空白があるならクォートで囲めばよい（クォートはシェルの組み立てに数えない。ただし上の文字はクォートの中でも 4）。
- **`exec` はモデルの隣に、モデルの名前のディレクトリ（`<名前>/`。解の `.md` と `receipt.json`）を作り、そのディレクトリに中身が在ると 2 回目を断る**
  （Alloy 6.2.0 で `The output directory … contains files. Delete them or use the -f option` と終了コード 1）。同じモデルを走らせ直すなら、前の `<名前>/` を消すか、
  呼び方の後ろに `-f` を足す。このスクリプトは毎回新しい一時ディレクトリで走らせるので足さない。
- **`exec` の後ろに `-q` を足さない**——結果の行が出なくなり、確かめは「無い」（1）になる（Alloy 6.2.0 で確かめた）。
- **書き方の細部（コードフェンスの中の行は読まない・先頭の BOM を外す・コロンは全角でもよい）は `check-tlc.py` の読み方と同じ**——その関数を読み込んで使う（写さない）。
- **同じ行を 2 行以上書かない・呼び方を空にしない**——どちらも「判定できない」（4）。

## 確かめ方

呼び方で 2 つの小さいモデルを一時ディレクトリで検査させる。`exec` の各コマンドの結果の行（`00. run   someA   0   1/1   SAT` の形。
**Alloy 6.2.0 では標準エラーに出る**ので、標準出力と標準エラーを合わせて読む）で決める:

1. **通るモデル**——終了コードが 0 で、`run someA` が `SAT`（**正常な状態に到達できる**）、`check emptyOrNot` が `UNSAT`（成り立つ性質に反例を出さない）なら通った。
2. **違反するモデル（陽性対照）**——`check alwaysEmpty` が `SAT`（反例を出した）なら通った（終了コードは見ない）。
   **何にでも「反例なし」・何にでも「反例あり」と言う呼び方を「在る」と読まない**ためである。

**`command -v` では探さない**——呼び方の行が無ければ、`PATH` に `alloy` が在っても「無い」（1）。探し方を呼び方の 1 つに揃えるためである。
**走らせるときは、環境変数 `JAVA_TOOL_OPTIONS` に `-Djava.awt.headless=true` を足す**——呼び方が誤って GUI に入っても、画面を開けずに失敗させるためである
（`exec` は headless でも動く。Alloy 6.2.0 で確かめた）。**1 回の検査は `PROBE_TIMEOUT` 秒で止める**（プロセスグループごと）。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 呼び方が通った |
| 1 | Alloy が無い——呼び方の行が無い（`CLAUDE.md` が無いを含む）か、呼び方が通らない（時間切れを含む） |
| 2 | 引数が違う |
| 4 | 判定できなかった——`CLAUDE.md` を読めない、同じ行が 2 行以上、呼び方が空、呼び方が 1 つのコマンドの形でない（シェルの組み立て・シェルの組み込みかシェルで始まる・語に割れない）か、語 `exec` が無いか `gui` が在る（どれも走らせていない） |

## 何を守り、何を守らないか

守る:

- **呼び方の行が無い正本を 0 にしない**——`PATH` に `alloy` が在っても 1（`command -v` で探さない）。
- **呼び方に語 `exec` が無いか語 `gui` が在れば、走らせずに 4**——引数なし・`gui` の形を確かめのために起こさない。
- **クォートで 1 語にした中の `gui` も見る**——`sh -c '… gui'` のように、`gui` を語の中に隠した形を素通りさせない。
- **シェルの組み立てを含む呼び方は、走らせずに 4**——`<alloy> exec || <alloy>`・`<alloy> # exec`・`<alloy>; : exec`・`<alloy> {gui,} exec` は、語 `exec` が在っても `sh` がサブコマンドの無い形か `gui` を起こす。
- **先頭が `java` でも、名前に `alloy` を含むコマンドでもない呼び方は、走らせずに 4**（許可の一覧）——`exec <alloy>`（ラッパーの本文を写した形）・`trap <alloy> EXIT exec`・`sh -c '<alloy>' exec`・`tcsh -c <alloy> exec`・`FOO=1 exec <alloy>`・`! exec <alloy>` は、語 `exec` が Alloy のサブコマンドにならない。
- **通るモデルの終了コードを見る**——0 でなければ 1。
- **通るモデルで到達できない呼び方を 0 にしない**——`run someA` が `SAT` でなければ 1。
- **通るモデルで成り立つ性質に反例を出す呼び方を 0 にしない**——`check emptyOrNot` が `UNSAT` でなければ 1。
- **違反するモデルで反例を出さない呼び方を 0 にしない**——`check alwaysEmpty` が `SAT` でなければ 1（陽性対照）。
- **先頭の BOM を外して読む**——BOM つきで保存した `CLAUDE.md` の 1 行目の行を落とさない。
- **同じ行が 2 行以上なら 4**——どれを使うかを決めない。
- **呼び方が空なら 4。**
- **読めない `CLAUDE.md` を「書いていない」と読まない**——4。
- **走らせる環境の `JAVA_TOOL_OPTIONS` に `-Djava.awt.headless=true` を足す**——前から在る値は残す。
- **時間切れで待ち続けない**——1 回の検査を `PROBE_TIMEOUT` 秒で止め（プロセスグループごと）、1。
- **正本で走らせない**——モデルは一時ディレクトリに書いて、そこで走らせる（`exec` の出力の `<名前>/` も一時ディレクトリにできる）。

守らない:

- **コードフェンス・全角のコロン・HTML コメントの読み方**——`check-tlc.py` の `scan_declarations` を読み込んで使うので、そちらの「守る」「守らない」とテストが持つ。
- **Alloy の版による出力の違い**——判定に使う結果の行の形と 2 つのモデルは、Alloy 6.2.0（`org.alloytools.alloy.dist` 6.2.0.202501090817、Java 22）の
  `exec` で確かめた（#922 の周。通るモデルで `run someA … SAT`・`check emptyOrNot … UNSAT` と終了コード 0、違反するモデルで `check alwaysEmpty … SAT` と終了コード 0）。
  ほかの版は確かめていない。**回帰テストは偽の Alloy で当てる**ので、モデルの中身（Alloy が構文で落とす書き方）はテストでは見えない。
- **`JAVA_TOOL_OPTIONS` で GUI が本当に開かなくなるか**——引数なし・`gui` の形はこの周で走らせていない（4 で走らせない形にした）。headless は保険で、
  語 `exec` が在っても GUI に入る呼び方（ラッパーが引数を捨てるなど）に当たったときに効くかは確かめていない。止めるのは時間切れである。
  `java` を起動しない呼び方（Java 以外で書いた Alloy）には効かない。
- **語の判定は `shlex` で割った語で見る**——`alloy-exec` のような 1 語や、ラッパーの中で `exec` を足す呼び方は「`exec` が無い」（4）。そう書いた利用者は、
  `exec` を語として書き直す（ラッパーの中身は読まない）。
- **先頭の `java`・ラッパーが何を起こすか**——`java` の後ろで別のクラスを起こす形や、名前に `alloy` を含むが中身は別のもの（`alloy-gui` という名前のラッパーなど）は見分けない。
  **呼び方の語が Alloy の何を起こすかは、語の並びからは決まらない**——見分けるのは、#922 とその関門が示した形（引数なし・`gui`・シェルの組み立て・先頭が `java` でもラッパーでもない形）までである。
- **`$HOME` などの変数・括弧を含むパス**——クォートの中でも 4 になる（走らせない側に倒す）。そう書いた利用者は、変数を展開した絶対パスで書き直す。
- **呼び方が、Formal Checker が書く大きいモデルを検査できるか**（メモリ・時間・スコープ）——小さいモデル 2 つを検査できることだけを見る。
- **呼び方の安全**——正本の `CLAUDE.md` に書いた文字列をそのまま `sh` で走らせる（正本の `CLAUDE.md` は利用者が書くもので、Formal Checker も同じ文字列を走らせる）。
- **子孫のプロセスが自分で別のプロセスグループに移ったとき**——時間切れで止めるのはプロセスグループまで。
- **autopilot の起動時の点検**——Alloy は必須の前提ではないので、`autopilot-check.py check` は Alloy を点検しない。autopilot の各起動は spec-review の手順 3 のとおり
  このスクリプトで確かめ、足りなければ止まる（spec-review が訊く場面なので）。
"""

import argparse
import importlib.util
import os
import re
import shlex
import signal
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CALL_KEY = "Alloy の呼び方:"
PROBE_TIMEOUT = 120
HEADLESS = "-Djava.awt.headless=true"
# `sh` に渡すと語の並びと実際に起こす形が食い違う文字（区切り・パイプ・リダイレクト・置き換え・コメント・改行・ブレースとグロブの展開）
SHELL_SPECIAL = set(";&|<>()$`#\n\\{}*?[]")
# 先頭に置いてよいコマンド（許可の一覧）: `java` か、名前に `alloy` を含むコマンド（jar を起こすラッパー）
HEAD_JAVA = "java"
HEAD_ALLOY = "alloy"

# 通るモデル: 到達できる（run が SAT）・成り立つ性質に反例が無い（check が UNSAT）
GOOD_MODEL = ("Probe", "sig A {}\npred someA { some A }\nrun someA for 3\nassert emptyOrNot { no A or some A }\ncheck emptyOrNot for 3\n")
# 違反するモデル（陽性対照）: 成り立たない性質に反例が出る（check が SAT）
BROKEN_MODEL = ("Broken", "sig A {}\nassert alwaysEmpty { no A }\ncheck alwaysEmpty for 3\n")
GOOD_EXPECT = {("run", "someA"): "SAT", ("check", "emptyOrNot"): "UNSAT"}
BROKEN_EXPECT = {("check", "alwaysEmpty"): "SAT"}
# `exec` の結果の行: `00. run   someA                    0    1/1     SAT`
RESULT_RE = re.compile(r"^\s*\d+\.\s+(run|check)\s+(\S+)\s.*?\b(SAT|UNSAT)\s*$", re.M)

EXIT_OK = 0
EXIT_MISSING = 1
EXIT_USAGE = 2
EXIT_UNKNOWN = 4


class Unknown(Exception):
    """判定できなかった（4）。"""


def load_tlc():
    """同じプラグインの `check-tlc.py`（宣言の読み方と、走らせ方の部品。写さずに読む）。"""
    spec = importlib.util.spec_from_file_location("spec_loop_check_tlc", HERE / "check-tlc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TLC = load_tlc()


def read_call(root):
    """正本の `CLAUDE.md` の呼び方。(呼び方 or None, 注記)。"""
    path = Path(root) / "CLAUDE.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None, f"{path} が無い"
    except (OSError, ValueError) as e:
        raise Unknown(f"{path} を読めない: {e}")
    text = text.removeprefix("\ufeff")
    calls = TLC.scan_declarations(text, (CALL_KEY,))[CALL_KEY]
    if len(calls) > 1:
        raise Unknown(f"`{CALL_KEY}` の行が {len(calls)} 行ある（どれを使うか決めない）")
    if calls and not calls[0]:
        raise Unknown(f"`{CALL_KEY}` の呼び方が空")
    if not calls:
        return None, f"{path} に `{CALL_KEY}` の行が無い"
    return calls[0], ""


def check_form(call):
    """引数なし・`gui` の形を走らせない。形が決まらない・語 `exec` が無い・`gui` が在れば Unknown。"""
    special = sorted(set(call) & SHELL_SPECIAL)
    if special:
        raise Unknown(f"呼び方 `{call}` にシェルの組み立て（{' '.join(special)}）がある——`sh` で走らせると、どの形で Alloy を起こすかが語だけで決まらないので走らせない")
    try:
        words = shlex.split(call)
    except ValueError as e:
        raise Unknown(f"呼び方 `{call}` を語に割れない: {e}")
    head = Path(words[0]).name if words else ""
    if not (head == HEAD_JAVA or HEAD_ALLOY in head.lower()):
        raise Unknown(f"呼び方 `{call}` の先頭 `{words[0] if words else ''}` が `java` でも、名前に `alloy` を含むコマンドでもない"
                      f"——シェルの組み込み・別のシェル・環境変数の代入などを先に置くと、語 `exec` が Alloy のサブコマンドにならないので走らせない")
    if any("gui" in word.split() for word in words):
        raise Unknown(f"呼び方 `{call}` に `gui` がある——GUI を起動する形なので走らせない（`exec` で検査させる形を書く）")
    if "exec" not in words:
        raise Unknown(f"呼び方 `{call}` に `exec` が無い——引数なしや `gui` の形は GUI を起動するので走らせない"
                      f"（例: `{CALL_KEY} java -jar <alloy.jar の場所> exec`）")


def probe_env():
    env = dict(os.environ)
    env["JAVA_TOOL_OPTIONS"] = " ".join(v for v in (env.get("JAVA_TOOL_OPTIONS", ""), HEADLESS) if v)
    return env


def run_model(call, workdir, name, timeout):
    """呼び方でモデル 1 つを検査させる。(終了コード or None（時間切れ・起動できない）, 出力)。"""
    try:
        proc = subprocess.Popen(["/bin/sh", "-c", f"{call} {name}.als"], cwd=workdir, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, errors="replace",
                                start_new_session=True, env=probe_env())
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        TLC.with_group(proc, signal.SIGKILL)
        out, _ = proc.communicate()
        return None, (out or "") + f"\n（{timeout} 秒で時間切れ）"
    except OSError as e:
        return None, f"起動できない: {e}"


def results(out):
    """{(run|check, 名前): SAT|UNSAT}。"""
    return {(m.group(1), m.group(2)): m.group(3) for m in RESULT_RE.finditer(out or "")}


def unmet(expect, out):
    got = results(out)
    return [f"{kind} {name} が {want} でない（{got.get((kind, name), '結果の行なし')}）"
            for (kind, name), want in expect.items() if got.get((kind, name)) != want]


def probe(call, timeout=None):
    """呼び方が Alloy として通るか。(通ったか, 説明)。"""
    timeout = PROBE_TIMEOUT if timeout is None else timeout
    with tempfile.TemporaryDirectory(prefix="spec-loop-check-alloy-") as tmp:
        for name, body in (GOOD_MODEL, BROKEN_MODEL):
            (Path(tmp) / f"{name}.als").write_text(body, encoding="utf-8")
        rc, out = run_model(call, tmp, GOOD_MODEL[0], timeout)
        if rc != 0:
            return False, f"通るモデルを検査できなかった（終了コード {rc}）: {TLC.tail(out)}"
        missed = unmet(GOOD_EXPECT, out)
        if missed:
            return False, f"通るモデルの結果が違う（{'・'.join(missed)}）: {TLC.tail(out)}"
        rc, out = run_model(call, tmp, BROKEN_MODEL[0], timeout)
        missed = unmet(BROKEN_EXPECT, out)
        if missed:
            return False, f"違反するモデルで反例を出さなかった（{'・'.join(missed)}。終了コード {rc}。Alloy として検査していない）: {TLC.tail(out)}"
    return True, "通るモデルで到達でき反例を出さず、違反するモデルで反例を出した"


def judge(root):
    """(終了コード, 出力の行)。"""
    try:
        call, note = read_call(root)
        if call is not None:
            check_form(call)
    except Unknown as e:
        return EXIT_UNKNOWN, [f"判定できなかった: {e}"]
    if call is None:
        return EXIT_MISSING, [f"Alloy が無い: {note}（`command -v` では探さない）",
                              f"用意のしかた: Java と Alloy の jar を置き、正本の `CLAUDE.md` に `{CALL_KEY} <コマンド> exec` を書く"
                              f"（例: `{CALL_KEY} java -jar /opt/alloy/alloy.jar exec`。引数なし・`gui` の形は書かない）"]
    ok, detail = probe(call)
    if not ok:
        return EXIT_MISSING, [f"Alloy が無い: 呼び方 `{call}` が通らない——{detail}"]
    return EXIT_OK, [f"Alloy が在る: 呼び方 `{call}`——{detail}"]


def main(argv=None):
    p = argparse.ArgumentParser(description="Alloy が正本の CLAUDE.md の呼び方で使えるかを確かめる（読むだけ）")
    p.add_argument("root", type=Path, help="正本リポジトリの根（CLAUDE.md の在る場所）")
    try:
        args = p.parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    code, lines = judge(args.root)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
