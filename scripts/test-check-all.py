#!/usr/bin/env python3
"""`check-all.py` の回帰テスト。

    python3 scripts/test-check-all.py

**このテストは実環境を書き換えない。** 集約の挙動はテンポラリに作った偽スクリプトだけを
対象にする（`assert_not_real_repo` がそれを担保する）。**収録漏れの検査だけは実リポジトリを
読む**——**そこが検査の対象そのもの**だからで、**読むだけで書かない。**

**変異テストを含む。** 形は「**契約**を 1 組の表明として書き、**本体を 1 箇所ずつ壊して、
その契約が破れることを要求する**」。**壊したのに契約が保たれるなら、その契約は
その箇所を見ていない**ので失格とする。

**この runner の壊れ方は「落とす」である**——登録から 1 本落とす・落ちたのに数えない・
飛ばしたのに黙っている。**契約はその 3 つに対応させてある。**
**並列にしてから（#430）は、壊れ方がもう 3 つ増えた**——並列にならない・`--jobs 1` でも
並列になる・出力が宣言順でなくなる。**契約の 5) 〜 8) がそれに対応する。**
**契約の 10) は #509**——並列で、打ち切られた子（シグナルで止まり、終了コードが負）を表示と集計の両方で
失敗に数え、FAIL の行の数と「失敗 N」が一致することを見る。

**変異は 2 組ある**——`MUTANTS` は `check-all.py`（集約）に、`SCAN_MUTANTS` は
**このファイルの中の判別**（CI の yaml の読み方）に当てる。**後者は自分自身を壊す。**

## CI の走査が、何を守り、何を守らないか（#155）

守る:

- **`check-all.py` に収録したスクリプトが、CI の yaml に `run:` として書かれているか。**
- **コメントアウトされたステップを「走っている」と数えない**——
  **`# - run: …` も `"run:" in l` を満たすので、素の行走査では素通しだった。**
- **「そもそも無い」と「コメントアウトされている」を分けて報告する**
  ——**どちらも「CI では走らない」だが、ステップを足すのと `#` を外すのでは直し方が違う。**
  **分けられるのは、コメントの側に `run:` と名前が*揃っている*ときだけ**（下の「守らない」）。
- **行末コメントの中の名前を、生きた名前として数えない。**
- **`check-X.py` が `test-check-X.py` に覆い隠されない**（#136 で 6 本が隠れていた）。
- **ワークフローファイルごと消しても気づく。** **ファイルの存在を見ているのではなく、
  そこにあったステップの名前がどこにも現れなくなる**ので、
  **結果として「そもそも無い」側に出る**（実測: `plugins.yml` を消すと 12 本が並んで赤）。
  **ここは別の保証ではなく、上の「`run:` として書かれているか」から出る帰結である**
  ——**一度「見ていない」と書いて、`/code-review` の 3 パス目に実測で反証された。**
- **引用された値の中の `#` で切らない**——切ると、その後ろの名前が落ちて「無い」と誤報する。
- **引用された値と見なすのは、*値の先頭に立ち、同じ行で閉じた*引用符だけ。**
  **それ以外の引用符は 1 つも数えない。** この 1 行が、**同じ向きの偽陰性を 3 つ塞いでいる**
  ——**語の途中のアポストロフィ**（`echo don't`。1 パス目の HIGH）、
  **値の途中の引用符でパリティが反転する形**（`--sep=", "`。2 パス目の HIGH）、
  **退避した引用符で反転する形**（`--m "a\\" b "`。2 パス目の MEDIUM）。
  **3 つとも、コメントが丸ごと「生きている」側に入って黙って緑になっていた**
  ——**#155 の欠陥と同じ向きである。** **どちらの穴も、歯止めを足した当人が作った。**
- **閉じない引用符を信じない**（`run: "unterminated  # …`）。
  **信じると行末までが「値」になってコメントを飲み込む。**
  **信じない側に倒すと向きは偽陽性**（在るのに「無い」）——**倒れてよいのはこちら。**
- **収録した回帰テストを、CI が引数なしで（全部を）回しているか**（#687。`full_runs`）——狭める口（`--part` など。#494）を
  CI のステップに書くと、`run:` には在るので上の検査は「走っている」と数えるが、走るのは一部だけである。
  **全部に数えないもの**: 引数が 1 つでもある行・次の行へ折り返した値（**空行を挟んでも**。#752）・
  **`run:` から名前までのあいだに `名前=` の字句がある行**（環境変数で狭める形——`PART=scan python3 …`・`export PART=scan && …`。#750）。
  **深い字下げのコメントの行は続きと読まない**（#753）。詳細は `full_runs` の docstring を正とする。
- **収録したスクリプトの生きた `run:` が、GitHub が無条件に走らせる位置に 1 つはあるか**（#931。`gated_runs`）——
  `jobs:` の下のジョブの `steps:` の下にあり、そのジョブが**ジョブ単位の `if:`・`needs:`** を持たず（`steps:` の後ろに書いても）、
  鍵が重なっていないこと。**ジョブを SKIPPED にしても `run:` の行は残るので、上の検査は緑のままで、`merge-pr.py` は SKIPPED を通過と読む**
  （#930 の `/code-review` が複製で示した）。**ジョブの見出しの字下げを崩した形**（深くして前のジョブの鍵になる・浅くして `jobs:` の外に出る）も赤にする。
  **「そもそも無い」「コメントアウト」とは別の行で、理由（ジョブの `if:`・`needs:`・`steps:` の外・ジョブの外・鍵の重なり）を名指しする。**
  **コンパクトな列**（`steps:` と同じ字下げの `- run:`）も `steps:` の下と読む（#944。#931 では偽の赤だった）。
- **収録した回帰テストを、無条件に走るジョブの*同じ `run:` の行*で引数なしで回しているか**（#945。`full_ungated_runs`）——
  上の 2 つ（`full_runs`・`gated_runs`）は別々に見るので、**無条件のジョブでは狭め、全部を回す行は条件つきのジョブにだけ置く形**は
  両方とも緑になる（無条件に全部を回す行は 1 本も無い）。2 つの判定を行の番号で突き合わせて赤にする。上の 2 つで赤になった名前は重ねて出さない。
- **上の無条件の位置の `run:`（回帰テストは無条件・引数なしの `run:`）が、PR と main への push で起動するワークフローにあるか**（#946。`trigger_reasons`・
  `untriggered_runs`）——`on:` を消す・`pull_request` を外す・`paths:` で狭めると、ワークフローごと PR で起動しないのに、`run:` の行もジョブも残るので
  上の検査は全部緑だった。**ファイルごとに `on:` を読み**、起動しないファイルにしか無い名前を、理由（ファイルの名前と `on:` のどこか）を添えて赤にする。
  **読む範囲**: `on:` のイベントに `pull_request` と `push` の両方があること、その下に `branches:` 以外の鍵（`paths:`・`paths-ignore:`・
  `branches-ignore:`・`types:`・`tags:` など）が無いこと、`branches:` があれば `main` を文字どおり含むこと。**値まで読むのは `branches:` だけ**
  ——ほかの鍵は値を読まずに、あれば赤（理由は `trigger_reasons` の docstring）。読む書き方（フロー列・ブロックの列・引用符つきの `"on":` など）も同じ docstring。

守らない:

- **「CI で実際に走った」の証明ではない。** 見ているのは**記述**だけで、
  **ステップの `if:` 条件・`continue-on-error`・ステップ内での失敗握り潰し**は
  見ていない。**言えるのは「走る形で書かれている」まで。** **ジョブ単位の `if:`・`needs:` は見る**（上の #931）が、
  **YAML のアンカー（`&`・`*`・`<<`）・複合の鍵・フロー形式のジョブ・再利用のワークフロー（`uses:` のジョブ）**は行の読み方の外にあり、
  **タブで始まる行・必ず走る `if:`** は偽の赤になる（`gated_runs` の docstring）。
- **コメントの側に `run:` が無い無効化は、コメント側として拾えない。**
  3 つの形がある——**(a)** `# run:` の次の行に `#   python3 scripts/x.py` と割った形、
  **(b)** コメントアウトした `run: |` のブロック、
  **(c)** **行末で殺した形**（`run: echo skip  # python3 scripts/x.py`。
  `run:` が生きている側に残る）。
  **いずれも「そもそも無い」側に出るので赤にはなるが、案内する直し方が
  「ステップを足す」になる**——**`#` を外せば済むのに。**
  **(c) を「コメントアウト」と数えないのは意図的である**——
  **行末の注記に名前が出ているだけの行と、構文で区別できない**
  （上の「行末コメントの中の名前を、生きた名前として数えない」と同じ行の形）。
- **`run: |` `run: >-` のブロック本文で呼ばれたスクリプトは拾わない**（`run:` を含む行だけを見るため）。
  **向きは偽陽性**（在るのに「無い」と言う）で、**黙って素通しする #155 の欠陥とは逆**。
  **該当は現在 0 件。**
- **`full_runs`（引数なしで回しているか。#687）の守らないもの**——
  **`|| true`**（落ちても通る形。「全部を回している」には数えるが、落ちたことは CI に出ない）、
  **`run:` の行の外で置いた環境変数**（ステップ・ジョブの `env:`・前のステップが `$GITHUB_ENV` に書いた値。全部に数える——**黙って素通しする向き**）、
  **`run:` の行の上でも `名前=` の字句を使わずに読み込む形**（`set -a && . ./env && …`・`--env-file`。同じく全部に数える）、
  **引用した値**（`run: "python3 scripts/x.py"`。引数が無くても「狭めた」と誤って赤）、
  **環境変数の判定の偽陽性**（狭めない変数・変数でない字句——`echo a=b && …`・`-X utf8=1`——でも「狭めた」と数える）、
  **#754 で受け入れた 2 つの偽陽性**（`- run:` の次の行に深い字下げの `name:` を書く形・`&&` で終わる行。どちらも全部を回していても
  「狭めた」と誤って赤にする——黙って素通しはしない）、**`run:` の行より浅い継続行**（PyYAML 6.0.3 では YAML として読めなかった）。
  **`full_ungated_runs`（#945）は 2 つの判定を同じ行で重ねたものなので、両方の守らないものをそのまま持つ**——たとえばステップの `env:` で狭めた行は、
  無条件のジョブにあれば「無条件に全部を回している」に数える（黙って素通しする向き）。
- **`on:` の値の中身**（#946）——**鍵の有無と `branches:` の値だけを見る**ので、**GitHub が実際に起動するかは見ていない。**
  外れる向きは**偽の赤**: `types:` に `synchronize` を含めた・`paths:` が全部に当たる・`branches:` を glob（`'**'`）で書いた、などの
  起動する形も赤にする。**フロー形式のマッピング**（`on: {…}`・`push: {branches: [main]}`）・**読めない行**・**タブで字下げした行**・**YAML のアンカー**・
  **重なる鍵**（`on:`・イベント・`branches:`）・**値と子が両方ある `on:`**・**列とマッピングが混ざる `on:`**・**`branches:` の `!` の除外**・
  **`branches:` の下の、値が空の `branches:` の後ろに 1 つの字下げで並ぶ `- <スカラー>` でない行**（継続行・項より深い行など）も
  読まずに赤で、`pull_request_target`・`workflow_call` などほかのイベントは起動に数えない（これも偽の赤の向き）。
  **黙って素通しする向きに残るもの**: **ワークフロー単位の `concurrency:`（`cancel-in-progress`）で run を止める形**。
- **`*.yaml`（拡張子違い）は読まない。**
- **引用された値の中の `\\"` のような退避は解さない**——そこで閉じたと見なすので、
  **`run: "a \\" b # scripts/x.py"` の後半が値ではなくコメントとして切れる。**
  **向きは偽陽性**（在るのに「無い」と言う）なので、**黙って素通しはしない。**
  **素の値の中に引用符が出てくる形**（`run: echo "a # scripts/x.py"`）**は、
  そもそも引用された値として扱わない**——**yaml 自身がそこで切る**ので、
  **名前を「走っている」と数えないのが正しい。**
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "scripts"
TARGET = SCRIPTS / "check-all.py"

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_not_real_repo(root: Path) -> None:
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの対象が実リポジトリの内側にある"
    )
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert root.resolve().is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_main(mod, argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["check-all.py", *argv]
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    finally:
        sys.argv = old
    return rc, buf.getvalue()


# ------------------------------------------------------------- 偽の scripts/
FLAGS = "flags"
# **待ち合わせの時間切れ（秒）は 2 つある**（#687）。
# - `BARRIER_WAIT`——**作業者が複数のとき**。同時に走るはずなので、相手が来ないのは起動の遅れである。
#   **長く取る**——0.5 秒だった頃、負荷 50 の `check-all.py` の中で、変異の前の本体の「--jobs 2 で同時に走る」が
#   時間切れで落ちた（#494 の周）。**相手が来れば即座に抜けるので、通る回の所要時間には効かない。**
# - `BARRIER_SERIAL_WAIT`——**作業者が 1 つのとき**（偽のプールが `SERIAL` の印を置く。`record_pools`）。
#   同時に走らないはずなので、待つのは「印に反して相手が来るか」を見る間だけで、**毎回ここまで待ち切る**
#   （本体の契約 6 と、直列に戻す変異のたび）。2 秒から縮めた値（#434）のまま。
BARRIER_WAIT = 30.0
BARRIER_SERIAL_WAIT = 0.5
SERIAL = "serial"
# 契約 10 の「遅れて落ちる歯止め」が、打ち切られる子の起動を待つ上限（秒）。通る回は印を見て即座に抜ける。
KILLED_WAIT = 0.2
BARRIER = """\
import pathlib, sys, time
d = pathlib.Path("{flags}")
d.mkdir(exist_ok=True)
(d / "{{me}}").touch()
end = time.time() + ({serial_wait} if (d / "{serial}").exists() else {wait})
while not (d / "{{other}}").exists():
    if time.time() > end:
        print("相手が来ない——同時に走っていない")
        sys.exit(1)
    time.sleep(0.02)
""".format(flags=FLAGS, wait=BARRIER_WAIT, serial_wait=BARRIER_SERIAL_WAIT, serial=SERIAL)


def clear_flags(root: Path) -> None:
    assert_not_real_repo(root)
    d = root / FLAGS
    if d.exists():
        for f in d.iterdir():
            f.unlink()


def order(out: str) -> list[str]:
    """OK/FAIL/SKIP の行に出た名前を、出た順に返す。"""
    return [l.split()[1] for l in out.splitlines()
            if l.startswith(("  OK  ", "  FAIL", "  SKIP"))]


def build_fake(root: Path) -> Path:
    """偽の scripts/ を作り、そこに置いた check-all.py のパスを返す。"""
    assert_not_real_repo(root)
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    # **宣言の先頭を遅らせる。** 終わった順に出す本体だと、後ろの行が先に出る（契約 1 の順序）。
    (scripts / "ok-a.py").write_text("import time; time.sleep(0.05); print('a ok')\n")
    (scripts / "ok-b.py").write_text("print('b ok')\n")
    # 回帰テストの側の先頭。**順序を見る契約 1 では、遅延ではなく `hold_head_test` が後に終わらせる**（#437）。
    (scripts / "ok-t.py").write_text("import time; time.sleep(0.05); print('t ok')\n")
    (scripts / "ok-c.py").write_text("print('c ok')\n")
    (scripts / "bad.py").write_text("import sys; print('BOOM-GUARD'); sys.exit(1)\n")
    (scripts / "bad-test.py").write_text("import sys; print('BOOM-TEST'); sys.exit(1)\n")
    (scripts / "needs-base.py").write_text("print('base ok')\n")
    # **#509: 遅れて落ちる歯止めと、シグナルで止まる子。** 打ち切られた子（SIGKILL）は終了コードが負になる。
    # **「遅れて」は時間ではなく印で作る**（#687）——歯止めは、打ち切られる子が起動した印を見てから落ちる。
    # 0.2 秒の眠りだった頃は、契約 10 を回すたびに（本体と変異の数だけ）0.2 秒ずつ足していた。
    # 同時に起動しない（作業者が 1 つの）変異では印が来ないので、`KILLED_WAIT` で待ちを切ってから落ちる。
    (scripts / "slow-bad.py").write_text(
        "import pathlib, sys, time\n"
        f"end = time.time() + {KILLED_WAIT}\n"
        f"while not pathlib.Path('{FLAGS}', 'killed').exists() and time.time() < end:\n"
        "    time.sleep(0.005)\n"
        "print('BOOM-SLOW'); sys.exit(1)\n")
    (scripts / "killed.py").write_text(
        "import os, pathlib, signal\n"
        f"pathlib.Path('{FLAGS}').mkdir(exist_ok=True); pathlib.Path('{FLAGS}', 'killed').touch()\n"
        "print('KILLED', flush=True); os.kill(os.getpid(), signal.SIGKILL)\n")
    # **互いの開始を待ち合わせる 2 本。** 同時に走らなければ、片方が時間切れで落ちる。
    for me, other in (("a", "b"), ("b", "a")):
        (scripts / f"par-{me}.py").write_text(BARRIER.format(me=me, other=other))
    target = scripts / "check-all.py"
    target.write_text(TARGET.read_text())
    return target


def wire(mod, root: Path, *, bad_guard: bool, bad_test: bool) -> None:
    mod.SCRIPTS = root / "scripts"
    mod.GUARDS = [("ok-a.py", [], False), ("ok-c.py", [], False),
                  ("needs-base.py", [], True)]
    mod.TESTS = ["ok-t.py", "ok-b.py"]
    if bad_guard:
        # **ok-c.py より前**に挟む。後ろに通る歯止めが無いと、
        # 「最初の失敗で止める」変異を契約が捕まえられない（実際に一度そうなった）。
        # **この主張は機械で当ててある**（#151）——後ろに回すと、この回帰テストが赤くなる。
        # mutation-claim: {"file": "scripts/test-check-all.py", "old": "GUARDS.insert(1, (\"bad.py\"", "new": "GUARDS.append((\"bad.py\"", "red": "python3 scripts/test-check-all.py --mutant 最初の失敗で止める"}
        mod.GUARDS.insert(1, ("bad.py", [], False))
    if bad_test:
        mod.TESTS.append("bad-test.py")


class RecordingPool(ThreadPoolExecutor):
    """本体の `ThreadPoolExecutor` の代わり。作業者の数と、名前ごとの future を覚える。"""

    def __init__(self, max_workers=None, *args, **kwargs):
        super().__init__(max_workers, *args, **kwargs)
        self.workers = max_workers
        self.futures: dict[str, object] = {}

    def submit(self, fn, /, *args, **kwargs):
        fut = super().submit(fn, *args, **kwargs)
        self.futures[args[0]] = fut
        return fut


def record_pools(mod) -> list[RecordingPool]:
    """本体が作るプールを `RecordingPool` に差し替え、作られたものを返すリストを渡す。

    **作業者が 1 つのプールなら、待ち合わせの `SERIAL` の印を置く**（#687）——待ち合わせる子は、印があれば
    `BARRIER_SERIAL_WAIT` だけ、無ければ `BARRIER_WAIT` だけ相手を待つ。印はプールを作った時点で置くので、
    子の起動より前にある。**`clear_flags` の後で本体を走らせる**（前の回の印を持ち越さない）。"""
    pools: list[RecordingPool] = []

    class Pool(RecordingPool):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            pools.append(self)
            if self.workers is not None and self.workers < 2:
                flags = Path(mod.SCRIPTS).parent / FLAGS
                assert_not_real_repo(flags)
                flags.mkdir(exist_ok=True)
                (flags / SERIAL).touch()

    mod.ThreadPoolExecutor = Pool
    return pools


TESTS_HEADER = "=== 回帰テスト ==="
# **同期が成り立たないとき（本体の形が変わった・作業者が 1 つ）に、待ちを打ち切る秒数。**
# 打ち切っても本体の出力は変わらない——**順序を壊す変異を捕まえる確かさが、時間の競争に戻るだけ。**
HOLD_LIMIT = 5.0


def main_waits(ident: int) -> bool:
    """スレッド `ident` が `threading` の `wait`（`Future.result`・`as_completed` の中）で止まっているか。"""
    frame = sys._current_frames().get(ident)
    return (frame is not None and frame.f_code.co_name == "wait"
            and frame.f_code.co_filename.endswith("threading.py"))


def hold_head_test(mod, pools: list[RecordingPool], head: str, after: str) -> None:
    """回帰テストの先頭 `head` の結果を、次の 3 つが揃うまで返さない（#437）。

    1. `after` の future が終わっている
    2. 本体が回帰テストの見出しを出した（歯止めの結果を待ち終えた）
    3. 本体のスレッドが待ちに入った

    **終わった順に出す変異（`as_completed`）は、歯止めを待ち終えてから回帰テストに入る。**
    **そこで回帰テストが 2 本とも終わっていると、終わった順ではなく集合の順に出て、宣言順と偶然揃う**
    ——先頭を遅い試料（0.3 秒）にしても、`test-check-all.py` を同時に 30 本 × 3 回走らせると 90 回中 6 回
    取りこぼした（歯止めの起動の遅れが、試料の遅延に勝つ）。**時間で競わず、同期で決める**:
    待ちに入った時点で `head` はまだ終わっておらず、`after` は終わっているので、
    `as_completed` は必ず `after` を先に出す。宣言順に待つ本体は `head` を待つので、宣言順のまま出る。
    """
    ident = threading.get_ident()
    real_run = mod.run

    def run(name: str, args: list[str]) -> tuple[bool, str]:
        res = real_run(name, args)
        # **作業者が 1 つなら `after` は `head` の後ろに並ぶ**——待つと詰まるので待たない
        # （そのとき終わった順は宣言順と同じで、順序を壊す変異はもともと判別できない）。
        if name != head or not pools or (pools[0].workers or 0) < 2:
            return res
        end = time.monotonic() + HOLD_LIMIT
        while time.monotonic() < end:
            fut = pools[0].futures.get(after)
            # **`redirect_stdout` は `sys.stdout` を差し替えるので、作業者のスレッドからも本体の出力が見える。**
            out = getattr(sys.stdout, "getvalue", lambda: "")()
            if fut is not None and fut.done() and TESTS_HEADER in out and main_waits(ident):
                break
            time.sleep(0.005)
        return res

    mod.run = run


# ------------------------------------------------------------------- 契約
# **本体を壊したときに、少なくとも 1 つが破れなければならない。**
def contract(target: Path, root: Path, tag: str) -> list[tuple[str, bool]]:
    got: list[tuple[str, bool]] = []

    # 1) 全部通る。base は解決できない → base を要する 1 本は SKIP。
    mod = load(target, f"{tag}_pass")
    wire(mod, root, bad_guard=False, bad_test=False)
    hold_head_test(mod, record_pools(mod), "ok-t.py", after="ok-b.py")
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("全部通れば rc=0", rc == 0),
        ("飛ばしたものを数えて出す", "飛ばし 1" in out),
        ("飛ばしたことを黙らない", "飛ばしたものは回していない" in out),
        ("SKIP でも残りは回る", "OK   ok-b.py" in out),
        # **歯止めの先頭（ok-a.py）は遅く終わり**（build_fake）、**回帰テストの先頭（ok-t.py）は
        # ok-b.py より後に終わる**（hold_head_test）ので、終わった順に出すと崩れる。
        ("出力は宣言順",
         order(out) == ["ok-a.py", "ok-c.py", "needs-base.py", "ok-t.py", "ok-b.py"]),
    ]

    # 2) 歯止めだけが落ちる
    mod = load(target, f"{tag}_badguard")
    wire(mod, root, bad_guard=True, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("歯止めが落ちたら rc=1", rc == 1),
        ("歯止めの失敗を名指しする", "落ちたもの: bad.py" in out),
        ("歯止めが落ちても後続の歯止めを回す", "OK   ok-c.py" in out),
        ("歯止めが落ちても回帰テストを回す", "OK   ok-b.py" in out),
        ("歯止めの失敗の出力を見せる", "BOOM-GUARD" in out),
    ]

    # 3) 回帰テストだけが落ちる（歯止めとは別の経路で数えている）
    mod = load(target, f"{tag}_badtest")
    wire(mod, root, bad_guard=False, bad_test=True)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("回帰テストが落ちたら rc=1", rc == 1),
        ("回帰テストの失敗を名指しする", "落ちたもの: bad-test.py" in out),
        ("回帰テストの失敗の出力を見せる", "BOOM-TEST" in out),
        ("回帰テストの失敗を 1 件と数える", "失敗 1" in out),
    ]

    # 4) --guards-only は回帰テストを飛ばし、そのことを出す
    mod = load(target, f"{tag}_guardsonly")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz", "--guards-only"])
    got += [
        ("--guards-only で回帰テストを回さない", "OK   ok-b.py" not in out),
        ("--guards-only でも飛ばしたことを出す", "飛ばしたものは回していない" in out),
    ]

    # 5) --jobs 2 なら同時に走る（待ち合わせる 2 本が両方通る）
    mod = load(target, f"{tag}_par")
    mod.SCRIPTS = root / "scripts"
    mod.GUARDS = [("par-a.py", [], False), ("par-b.py", [], False)]
    mod.TESTS = []
    record_pools(mod)  # 作業者が 1 つになる変異（直列に戻す）は、待ち合わせを短く切る（#687）
    clear_flags(root)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz", "--jobs", "2"])
    got.append(("--jobs 2 で同時に走る", rc == 0))

    # 6) --jobs 1 なら同時に走らない（待ち合わせる 2 本の先の 1 本が、相手を待って時間切れで落ちる）
    #    **区間の重なりでは見ない**（#431）——**0.1 秒の区間は起動の遅れに負ける。**
    #    `test-check-all.py` を同時に 30 本 × 2 回走らせると、60 回中 7 回、2 本が同時に起動しても
    #    区間が重ならず、「--jobs を無視する」変異を取りこぼした（`check-all.py` の中でも 1 回踏んだ）。
    #    **待ち合わせは相手を待つ**ので、同時に起動していれば、遅れても出会う。
    #    **ただし待ち合わせは「同時に走る」側を時間に依らずには示せない**——相手の起動が待ちの上限より
    #    遅れると、同時に投げても時間切れで落ちる。上限が 0.5 秒だった頃、30 本 × 3 回で 90 回中 2 回、「--jobs を無視する」変異を
    #    取りこぼした（#437）。**だから作業者の数も見る**——時間に依らない。
    #    **いまは上限を作業者の数で分ける**（#687。`BARRIER` の上）——本体（作業者 1）は印を見て `BARRIER_SERIAL_WAIT` で切り、
    #    「--jobs を無視する」変異（作業者 2 以上）は `BARRIER_WAIT` まで待つので、相手の起動の遅れでは取りこぼさない。
    mod = load(target, f"{tag}_ser")
    mod.SCRIPTS = root / "scripts"
    mod.GUARDS = [("par-a.py", [], False), ("par-b.py", [], False)]
    mod.TESTS = []
    pools = record_pools(mod)
    clear_flags(root)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz", "--jobs", "1"])
    got.append(("--jobs 1 で同時に走らない", rc != 0 and "相手が来ない" in out))
    got.append(("--jobs 1 で作業者を 1 つにする", [p.workers for p in pools] == [1]))

    # 7) 既定（--jobs を渡さない）でも同時に走る——既定が直列なら速くならない。
    #    **区間の重なりではなく待ち合わせで見る**——重なりは起動の遅れに負けるが、
    #    待ち合わせは時間切れまで待つので、負荷の高いとき（check-all.py の中）でも揺れない。
    #    **CPU が 1 つの機械では既定が 1 なので、この表明は成り立たない**（そのときは見ない）。
    if (os.cpu_count() or 1) > 1:
        mod = load(target, f"{tag}_default")
        mod.SCRIPTS = root / "scripts"
        mod.GUARDS = [("par-a.py", [], False), ("par-b.py", [], False)]
        mod.TESTS = []
        record_pools(mod)  # 既定を直列にする変異は、待ち合わせを短く切る（#687）
        clear_flags(root)
        rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
        got.append(("既定で同時に走る", rc == 0))

    # 8) --jobs 0 は回さずに断る（argparse の誤り＝終了コード 2）
    mod = load(target, f"{tag}_zero")
    wire(mod, root, bad_guard=False, bad_test=False)
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            rc, out = run_main(mod, ["--base", "no-such-ref-xyz", "--jobs", "0"])
        refused = False
    except SystemExit as exc:
        refused = exc.code == 2
    except Exception:  # noqa: BLE001 — 断らずに別の形で落ちたら、それも失格
        refused = False
    got.append(("--jobs 0 を断る", refused))

    # 9) 入れ子の並列を絞る（#460）——`check-mutation-claims.py` に、親より少ない `--jobs` を渡す。
    #    **実物の `GUARDS` のまま、起動の引数だけを記録する**（`run` を差し替えるので何も走らない）。
    #    **値そのものは見ない**——見るのは「渡すこと」「親が 1 なら 1」「親が 2 以上なら親より少ない」。
    #    **回帰テストのうち変異を同時に当てる 3 本にも渡す**（#748・#749・#1021）——実物の `TESTS` のまま、渡さないものには何も足さない。
    recorded: dict[str, list[tuple[str, list[str]]]] = {}

    def nested_args(jobs: str, script: str = "check-mutation-claims.py") -> list[list[str]]:
        if jobs not in recorded:  # 並列数ごとに 1 回だけ回し、記録を名前で引く
            mod = load(target, f"{tag}_nested{jobs}")
            calls: list[tuple[str, list[str]]] = []
            mod.run = lambda name, args: (calls.append((name, list(args))), (True, ""))[1]
            run_main(mod, ["--base", "no-such-ref-xyz", "--jobs", jobs])
            recorded[jobs] = calls
        return [args for name, args in recorded[jobs] if name == script]

    def inner(args: list[list[str]]) -> int | None:
        if len(args) != 1 or args[0][:-1] != ["--jobs"] or not args[0][-1].isdigit():
            return None
        return int(args[0][-1])

    one, four = inner(nested_args("1")), inner(nested_args("4"))
    got.append(("--jobs 1 なら入れ子も --jobs 1", one == 1))
    got.append(("--jobs 4 なら入れ子は 1 以上 4 未満", four is not None and 1 <= four < 4))
    nested_tests = ("test-check-unattended-env.py", "test-ledger.py", "test-check-deps-declared.py")
    got.append(("--jobs 1 なら変異を同時に当てる回帰テストにも --jobs 1（#749）",
                all(inner(nested_args("1", t)) == 1 for t in nested_tests)))
    got.append(("--jobs 4 なら変異を同時に当てる回帰テストは 1 以上 4 未満（#749）",
                all(1 <= (inner(nested_args("4", t)) or 0) < 4 for t in nested_tests)))
    # **`TESTS` から `NESTED` を除いた全部を見る**（#749 の 2 パス目）——1 本だけでは、ほかのテストに渡す変異が素通りする
    others = [t for t in load(target, f"{tag}_tests").TESTS if t not in nested_tests]
    got.append(("--jobs を受けない回帰テストには何も渡さない（#749）",
                bool(others) and all(nested_args("1", t) == [[]] for t in others)))

    # 10) 並列で、遅れて落ちる子とシグナルで止まった子（打ち切り）を、表示と集計の両方で失敗に数える（#509）。
    #     **FAIL の行の数と「失敗 N」が一致する**ことを見る——表示と集計が別の経路で決まると、ここが割れる。
    mod = load(target, f"{tag}_killed")
    mod.SCRIPTS = root / "scripts"
    mod.GUARDS = [("slow-bad.py", [], False), ("ok-c.py", [], False)]
    mod.TESTS = ["killed.py", "ok-b.py"]
    clear_flags(root)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz", "--jobs", "4"])
    fail_lines = [l for l in out.splitlines() if l.startswith("  FAIL")]
    got += [
        ("打ち切られた子（SIGKILL）を失敗に数える", "  FAIL killed.py" in out),
        ("遅れて落ちた子と打ち切られた子で rc=1", rc == 1),
        ("FAIL の行の数と「失敗 N」が一致する（#509）",
         len(fail_lines) == 2 and "（失敗 2 /" in out),
        ("打ち切られた子も名指しする", "落ちたもの: slow-bad.py, killed.py" in out),
    ]
    return got


def contract_with_base(target: Path, root: Path, tag: str) -> list[tuple[str, bool]]:
    """base が解決できるなら、base を要する検査も回る。"""
    mod = load(target, f"{tag}_base")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "HEAD"])
    return [
        ("base が解決できれば飛ばさない", "飛ばし 0" in out),
        ("base を要する検査が回る", "OK   needs-base.py" in out),
        ("base ありでも全部通れば rc=0", rc == 0),
    ]


# ---------------------------------------------------------------- 収録漏れ
def load_target():
    """`check-all.py` をモジュールとして読む。**宣言そのものを見るため。**"""
    spec = importlib.util.spec_from_file_location("check_all_target", TARGET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_registry_covers_every_script() -> None:
    """実リポジトリを読む。`scripts/` に検査を足して登録し忘れたら落とす。"""
    src = TARGET.read_text()
    guards = sorted(
        p.name for p in SCRIPTS.glob("check-*.py") if p.name != "check-all.py"
    ) + ["skill-metrics.py"]
    tests = sorted(
        p.name for p in SCRIPTS.glob("test-*.py") if p.name != "test-check-all.py"
    )
    missing_g = [n for n in guards if f'"{n}"' not in src]
    missing_t = [n for n in tests if f'"{n}"' not in src]
    check(f"歯止めを全部収録している（{len(guards)} 本）", not missing_g)
    if missing_g:
        print(f"       収録漏れ: {missing_g}")
    check(f"回帰テストを全部収録している（{len(tests)} 本）", not missing_t)
    if missing_t:
        print(f"       収録漏れ: {missing_t}")


# ------------------------------------------------------ yaml のコメント判別
NAME_RE = re.compile(r"scripts/([A-Za-z0-9_.-]+\.py)")


# **値の先頭に立つ引用符**——行頭（空白を除く）か、`- ` の後ろか、`key: ` の後ろ。
VALUE_QUOTE_RE = re.compile(r"""\s*(?:-\s+)?(?:[^\s:#]+:\s+)?(["'])""")


def quoted_span(line: str) -> tuple[int, int] | None:
    """**値の先頭に立つ引用符**が張る範囲 `(開き, 閉じ)` を返す。無ければ `None`。

    **引用符を、行のどこにあっても数えてはならない**——**パリティが途中で反転する。**
    `run: echo skip --sep=", "  # python3 scripts/x.py` では、**`=` の後ろの `"` は開かず、
    空白の後ろの閉じ `"` のほうが「開き」と読まれて**、そこから行末までが「値」になり、
    **コメントが丸ごと「生きている」側に入った**（**偽陰性**。#155 と同じ向き）。
    **`/code-review` の 2 パス目が、実物の `plugins.yml` で rc=0 のままになることを示した**
    ——**1 パス目の修正（語の先頭でだけ開く）では届いていなかった。**

    **同じ行の中で閉じない引用符は信じない**（`None` を返す）。
    **信じると、そこから行末までが「値」になってコメントを飲み込む。**
    **返さなければ `#` の規則がそのまま働き、向きは偽陽性**（在るのに「無い」と言う）
    ——**宣言どおり、倒れてよいのはこちら側である。**
    """
    m = VALUE_QUOTE_RE.match(line)
    if not m:
        return None
    open_i = m.end() - 1
    close_i = line.find(m.group(1), open_i + 1)
    if close_i == -1:
        return None
    return open_i, close_i


def comment_at(line: str, start: int) -> int:
    """`#` が**コメントを始める**位置を `start` 以降から探す。無ければ `-1`。

    **`#` がコメントを始めるのは、行頭か、直前が空白のときだけ**（`a#b` は値の一部）。
    """
    for i in range(start, len(line)):
        if line[i] == "#" and (i == 0 or line[i - 1] in " \t"):
            return i
    return -1


def split_comment(line: str) -> tuple[str, str]:
    """yaml の 1 行を「生きている部分」と「コメントの部分」に割る。

    **引用された値の中の `#` はコメントではない**——そこで切ると、**後ろに書かれた
    スクリプト名が落ちて「CI に無い」と誤報する**（偽陽性）。
    **見るのは「値の先頭に立ち、同じ行で閉じた引用符」だけ**で、
    **それ以外の引用符は 1 つも数えない**（`quoted_span` の docstring が理由を持つ）。
    """
    span = quoted_span(line)
    start = 0
    while True:
        i = comment_at(line, start)
        if i == -1:
            return line, ""
        if span and span[0] < i < span[1]:
            start = span[1] + 1  # 引用された値の中——その先を探す
            continue
        return line[:i], line[i:]


def scan_ci_runs(ci: str) -> tuple[set[str], set[str]]:
    """CI の yaml から `run:` に現れるスクリプト名を拾い、**2 つに分けて**返す。

    返すのは `(生きている, コメントアウトされている)`。**分けるのが要点**で、
    「**そもそも無い**」と「**コメントアウトされている**」は**直し方が違う**
    ——前者はステップを足す、後者は `#` を外す。**どちらも「CI では走らない」。**

    **`run:` を含む行だけを見る**のは元のままで（`- name:` のラベルに名前が出ているだけの
    行を数えないため）、**判定をその行の*生きている部分*に限る**のが #155 の修正である。
    """
    live: set[str] = set()
    commented: set[str] = set()
    for raw in ci.split("\n"):
        code, comment = split_comment(raw)
        if "run:" in code:
            live |= set(NAME_RE.findall(code))
        if "run:" in comment:
            commented |= set(NAME_RE.findall(comment))
    return live, commented


# **引数を付けずに呼んでいる**——名前の後ろが行末か、シェルのつなぎ（`&&`・`||`・`;`・`|`）だけ。
FULL_RE = re.compile(r"scripts/([A-Za-z0-9_.-]+\.py)(?=\s*(?:$|&&|\|\||;|\|))")
# **環境変数を置いて狭める**——`run:` から名前までのあいだに `名前=` の字句がある（#750）。前置き（`PART=scan python3 …`・
# `env PART=scan …`）も、前のコマンドで書き出す形（`export PART=scan && python3 …`）も当たる。
ENV_RE = re.compile(r"(?:^|\s)[A-Za-z_][A-Za-z0-9_]*=")


def full_runs(ci: str) -> set[str]:
    """CI の yaml の**生きている** `run:` の行で、**引数を付けずに**呼んでいるスクリプト名（#687）。

    **回帰テストは引数なしで回さなければ全部を回したことにならない**——`test-check-all.py --part scan` のような
    狭める口（#494）を CI のステップに書くと、`scan_ci_runs` は「走っている」と数えるが、走るのは一部だけである。
    **歯止め（`GUARDS`）には引数が要るものがある**（`skill-metrics.py --check`・base を渡す 3 本）ので、これは回帰テストにだけ掛ける。
    **全部に数えないもの**（どれも「走っているが、全部ではない」側。向きは偽陽性——黙って素通しはしない）:

    - **引数が 1 つでもある**——中身は見ない。
    - **次の行へ折り返した値**（`run:` の行より深く字下げした継続行。YAML では同じ値の続き）——引数が続くものとして数える
      （#687 の 2 パス目の `/code-review`——継続行に `--part scan` を書くと、行だけを見ていた形は「全部」に数えた）。
      **空行を挟んでも続き**と読む（YAML でも続き。#752）。**深い字下げのコメントの行は続きと読まない**（YAML でもコメント。#753）。
    - **`run:` から名前までのあいだに `名前=` の字句がある**——環境変数で狭める形（`PART=scan python3 scripts/x.py`・`env …`・
      `export PART=scan && …`。#750）。**狭めない変数でも、変数でない字句（`echo a=b && …`・`-X utf8=1`）でも当たる。**

    **守らないもの**: `|| true`（落ちても通る）は見ない。**`run:` の行の外で置いた環境変数**——ステップ・ジョブの `env:`・
    前のステップが `$GITHUB_ENV` に書いた値——は見ない（`run:` の行だけを読むので、全部に数える。黙って素通しする向き）。
    **`run:` の行の上でも、`名前=` の字句を使わずに読み込む形**（`set -a && . ./env && …`・`uv run --env-file .env …`）は見ない（全部に数える。同じ向き）。
    **引用した値**（`run: "python3 scripts/x.py"`）は引数が無くても全部に数えない（名前の後ろが閉じ引用符で、`FULL_RE` が当たらない。誤って赤）。**深い字下げの次の行が値の続きでなく別の鍵**（`- run:` の次の行の `name:`）と
    **`&&` で終わる行**（続きを次の行に書く）は、全部を回していても「全部」に数えない（誤って赤——#754 で受け入れた）。
    **`run:` の行より浅い継続行**は見ない（PyYAML 6.0.3 では YAML として読めなかった。GitHub の読み方は確かめていない）。
    **その行がどのジョブにあるかは見ない**——条件つきのジョブ（`if:`・`needs:`）にしか引数なしの行が無くても「全部」に数える。
    **無条件のジョブで全部を回しているかは `full_ungated_runs` が見る**（#945）。
    """
    return set().union(*full_lines(ci).values())


def full_lines(ci: str) -> dict[int, set[str]]:
    """`full_runs` の行ごとの形（#945）——行の番号（`ci.split("\\n")` の 0 始まり）から、その行で引数なしで呼んでいる名前へ。

    判定は `full_runs` の docstring を正とする。`full_ungated_runs` が `gate_records` と同じ行の番号で突き合わせるために分けた。
    """
    full: dict[int, set[str]] = {}
    lines = ci.split("\n")
    for i, raw in enumerate(lines):
        alive, _ = split_comment(raw)
        if "run:" not in alive:
            continue
        indent = len(raw) - len(raw.lstrip())
        nxt = next((l for l in lines[i + 1:] if l.strip()), "")
        if len(nxt) - len(nxt.lstrip()) > indent and not nxt.lstrip().startswith("#"):
            continue  # 次の行に値が続く——その行に引数がありうる
        head = alive.index("run:") + len("run:")
        for m in FULL_RE.finditer(alive.rstrip()):
            if ENV_RE.search(alive[head:m.start()]):
                continue  # 環境変数を置いて狭めている（#750）
            full.setdefault(i, set()).add(m.group(1))
    return full


# **鍵の行**——行の頭の `名前:` の後ろが空か空白（`run: x` も `steps:` も当たる。`- name: x` は `-` で始まるので当たらない）。
# **引用符で囲んだ鍵も、コロンの前に空白を置いた鍵も鍵である**（`"if": false`・`if : false` は YAML で `if` の鍵
# ——読まないと無条件と数える偽の緑。#931 の 1・2 パス目）。
KEY_RE = re.compile(r"""(?:"([^"]*)"|'([^']*)'|([^\s:#'"-][^\s:]*))\s*:(?:\s|$)""")
# **列の項の行**——`- ` か、`-` だけの行（#944。コンパクトな列を見分ける）。`-x` や `--` は列の項ではない。
SEQ_RE = re.compile(r"-(?:\s|$)")
# **ジョブを走らなくする、ジョブ単位の鍵**（#931）——値に依らない。
GATE_KEYS = ("if", "needs")


def key_of(text: str) -> str | None:
    """行の頭の鍵の名前（引用符は外す）。鍵の行でなければ `None`。"""
    m = KEY_RE.match(text)
    if not m:
        return None
    return next(g for g in m.groups() if g is not None)


def gated_runs(ci: str) -> tuple[set[str], dict[str, set[str]]]:
    """CI の yaml の**生きている** `run:` の行を、**GitHub が無条件に走らせる位置にあるか**で分ける（#931）。

    返すのは `(無条件, 理由)`——**無条件**は、`jobs:` の下のジョブの `steps:` の下にあり、そのジョブがジョブ単位の
    `if:`・`needs:` を持たず、鍵が重なっていない `run:` の行に現れる名前。**理由**は、そうでない行に現れる名前ごとの理由の集合。
    **ジョブ単位の `if:` を足すとジョブは SKIPPED になり、`merge-pr.py` は SKIPPED を通過と読む**——`run:` の行は残るので
    `scan_ci_runs` は「走っている」と数え、どこも赤にならなかった（#930 の `/code-review`）。

    **YAML の読み方**——標準ライブラリだけで、行のインデントを数える:

    - **インデント 0 の行**で区切る。`jobs:` の下だけがジョブで、ほかの最上位の鍵（`on:`・`concurrency:`）の下の `run:` は「ジョブの外」。
      ファイルを繋いだ文字列でも、次のファイルの最上位の鍵で区切れる。
    - **`jobs:` の最初の子のインデントがジョブの見出しの段**、**見出しの最初の子の段がジョブ単位の鍵の段**である。
      見出しの段より浅い行が来たら、そこからは「ジョブの外」（YAML としても読めない形）。
    - **`run:` の行は、その手前で最後に出たジョブ単位の鍵が `steps` のときだけ `steps:` の下にある**——見出しを深くすると、
      そのジョブは前のジョブの鍵になり、その `run:` は `steps` 以外の鍵の下に入る（ジョブごと深くした形）か、
      前のジョブの鍵が重なる（見出しだけ深くした形——`runs-on:`・`steps:` が 2 つになる）。
    - **ジョブ単位の `if:`・`needs:` は `steps:` の後ろに書いても効く**ので、ジョブ全体の鍵を集めてから決める。
    - 空行とコメントだけの行は飛ばす（`split_comment` の生きている部分で決める）。ブロックの本文（`run: |` の下）は鍵の段より深いので、鍵とは読まない。

    - **鍵は引用符で囲んでも、コロンの前に空白を置いても鍵と読む**（`"if": false`・`if : false`。#931 の 1・2 パス目）。
    - **鍵の段と同じ字下げの `- ` で始まる行（コンパクトな列）は、前の鍵の値の続きと読む**（#944）——YAML のブロックの列は親の鍵と
      同じ字下げに置ける（`steps:` の次の行の `- run:`）。鍵を読み直さず、鍵の一覧にも足さない（`needs:` の下の `- plain` を重なりに数えない）。
      **前の鍵が `steps` でなければ `steps:` の外のまま**で、**鍵の段より浅い `- `** は今までどおり鍵の段でない行と読む。

    **守らないもの**: ステップ単位の `if:`（PR 限定の歯止めが正しく使っている）・`continue-on-error`・ジョブの `strategy`・
    ワークフローの `on:`（ファイルごとに `trigger_reasons` が見る——ここは繋いだ文字列を読むので見ない。#946）・
    YAML のアンカー（`&`・`*`・`<<`）・複合の鍵（`? if`）・フロー形式で書いたジョブ（`jobs: {a: …}`）・再利用のワークフロー（`uses:` のジョブ）。
    **偽の赤になる書き方**——**タブで始まる行**は字下げ 0 の最上位と読み、そこから先をジョブの外に数える（YAML はタブの字下げを許さない）。
    **値を読まない**ので、必ず走る `if: always()` も、`needs:` も、ジョブ単位にあれば赤にする。
    **その行が引数を付けて狭めているかは見ない**——無条件の位置の行が狭めていても「無条件」に数える。
    **無条件のジョブで全部を回しているかは `full_ungated_runs` が見る**（#945）。
    """
    ok: set[str] = set()
    why: dict[str, set[str]] = {}
    for _, names, reasons in gate_records(ci):
        for n in names:
            if reasons:
                why.setdefault(n, set()).update(reasons)
            else:
                ok.add(n)
    return ok, why


def gate_records(ci: str) -> list[tuple[int, set[str], set[str]]]:
    """`gated_runs` の行ごとの形（#945）——生きている `run:` の行ごとに `(行の番号, 名前, 理由)`。理由が空なら無条件の位置。

    行の番号は `ci.split("\\n")` の 0 始まりで、`full_lines` と同じ。読み方は `gated_runs` の docstring を正とする。
    """
    records: list[tuple[int, set[str], str | None, str | None]] = []
    keys: dict[str, list[str]] = {}
    in_jobs = False
    job_indent: int | None = None
    key_indent: int | None = None
    job: str | None = None
    key: str | None = None
    for i, raw in enumerate(ci.split("\n")):
        code, _ = split_comment(raw)
        if not code.strip():
            continue
        indent = len(code) - len(code.lstrip(" "))
        head = key_of(code.strip())
        if indent == 0:
            in_jobs = head == "jobs"
            job_indent = key_indent = None
            job = key = None
        elif in_jobs:
            if job_indent is None:
                job_indent = indent
            if indent < job_indent:
                in_jobs = False  # 見出しの段より浅い——ここから先はジョブの外
                job = key = None
            elif indent == job_indent:
                # **ファイルを繋いでも、同じ名前のジョブを別のジョブとして数える**（連番を付ける）
                job = f"{len(keys)}:{head if head is not None else code.strip()}"
                keys[job] = []
                key_indent = None
                key = None
            elif job is not None:
                if key_indent is None:
                    key_indent = indent
                if indent == key_indent and SEQ_RE.match(code.lstrip(" ")):
                    pass  # コンパクトな列——前の鍵の値の続き（#944）
                elif indent <= key_indent:
                    key = head if (head is not None and indent == key_indent) else None
                    if key is not None:
                        keys[job].append(key)
        names = set(NAME_RE.findall(code)) if "run:" in code else set()
        if names:
            records.append((i, names, job if in_jobs else None, key if in_jobs else None))
    out: list[tuple[int, set[str], set[str]]] = []
    for i, names, j, k in records:
        reasons: set[str] = set()
        if j is None:
            reasons.add("ジョブの外")
        else:
            if k != "steps":
                reasons.add(f"`steps:` の外（{k}）")
            for g in GATE_KEYS:
                if g in keys[j]:
                    reasons.add(f"ジョブの `{g}:`")
            dup = sorted({x for x in keys[j] if keys[j].count(x) > 1})
            if dup:
                reasons.add(f"ジョブの鍵が重なる（{', '.join(dup)}）")
        out.append((i, names, reasons))
    return out


def full_ungated_runs(ci: str) -> set[str]:
    """**同じ `run:` の行で**、無条件に走るジョブの `steps:` の下にあり、かつ引数なしで呼んでいる名前（#945）。

    `full_runs`（引数なしの行が 1 つはある）と `gated_runs`（無条件の位置に行が 1 つはある）は**別々に見る**ので、
    **無条件のジョブでは狭め、全部を回す行は条件つきのジョブ（`if:`・`needs:`）にだけ置く形**は両方とも緑になる
    ——無条件に全部を回している行は 1 本も無いのに（#942 の `/code-review` C1）。だから 2 つの判定を**行の番号で突き合わせる**。
    名前ごとの集合の積（`full_runs(ci) & gated_runs(ci)[0]`）では、その形が積に入って緑のまま。

    判定の中身（引数・続きの行・環境変数・ジョブの位置）と守らないものは `full_runs` と `gated_runs` の docstring を正とする。
    """
    full = full_lines(ci)
    return {n for i, names, reasons in gate_records(ci) if not reasons for n in names & full.get(i, set())}


# **PR と main への push で起動させる、ワークフローの `on:` のイベント**（#946）——両方要る。
TRIGGER_EVENTS = ("pull_request", "push")
# **イベントの値で、狭めていないと読むもの**——空・`null`・`~`・`{}`。
OPEN_VALUES = ("", "null", "~", "{}")


def scalar(text: str) -> str:
    """スカラーの値（前後の空白と、両端の同じ引用符を外す）。"""
    t = text.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]
    return t


def inline_value(code: str) -> str:
    """鍵の行の、コロンの後ろの値（生きている部分を渡す）。鍵の行でなければ空。"""
    t = code.strip()
    m = KEY_RE.match(t)
    return t[m.end():].strip() if m else ""


def seq_items(value: str) -> list[str]:
    """値を項の並びに読む——フロー形式の列（`[a, "b"]`）は項ごとに、ほかのスカラーは 1 項に。空なら空。"""
    if value.startswith("[") and value.endswith("]"):
        return [scalar(x) for x in value[1:-1].split(",") if x.strip()]
    return [scalar(value)] if value else []


def event_filter_reasons(ev: str, sub: list[tuple[int, str]]) -> set[str]:
    """`on:` のイベント `ev` の下の行（字下げ・生きている部分）から、狭めている理由を返す（#946）。

    **値まで読むのは `branches:` だけ**で、`main` を文字どおり含まなければ赤。**ほかの鍵は値を読まずに、あれば赤**
    （`paths:`・`paths-ignore:`・`branches-ignore:`・`types:`・`tags:` など）。`branches:` の項は、フロー形式の列・
    より深い `- `・`branches:` と同じ字下げの `- `（コンパクトな列）のどれでも読む。
    **`branches:` の下で受け取るのは、値が空の `branches:` の後ろに 1 つの字下げで並ぶ `- <スカラー>` の項だけ**（#946 の 2 パス目）——
    値のある `branches:` の下の行（`branches: main` の継続行は YAML では `main dev` という 1 つの値になる）・項より深い行
    （`- dev` の下の `- main` は `dev - main` になる）・字下げの揃わない項・`- x: y` や `- [a]` の項は読まずに赤。
    """
    out: set[str] = set()
    level = sub[0][0] if sub else None
    key: str | None = None
    branches: list[str] = []
    has_branches = False
    seen: list[str] = []
    inline = ""
    item_level: int | None = None
    for ind, c in sub:
        item = SEQ_RE.match(c) is not None
        if level is not None and ind < level:
            out.add(f"`{ev}` の下の字下げを読めない")
            key = None
        elif ind == level and not (key == "branches" and item and not inline):
            key = key_of(c)
            if key in seen:
                out.add(f"`{ev}` の `{key}:` が重なる")
            if key is not None:
                seen.append(key)
            if key is None:
                out.add(f"`{ev}` の下の行を読めない（`{c}`）")
            elif key == "branches":
                has_branches = True
                inline = inline_value(c)
                item_level = None
                branches += seq_items(inline)
            else:
                out.add(f"`{ev}` の `{key}:` で狭めている")
        elif key == "branches":
            name = c[1:].strip() if item else ""
            if (inline or not item or (item_level is not None and ind != item_level)
                    or not name or name[:1] in "[{" or ": " in name or name.endswith(":")):
                out.add(f"`{ev}` の `branches:` の下の行を読めない（`{c}`）")
            else:
                item_level = ind
                branches.append(scalar(name))
    if has_branches and "main" not in branches:
        out.add(f"`{ev}` の `branches:` に `main` が無い")
    if any(b.startswith("!") for b in branches):
        out.add(f"`{ev}` の `branches:` に `!` の除外がある")
    return out


def trigger_reasons(text: str) -> set[str]:
    """ワークフローの yaml **1 ファイル**の `on:` から、**PR と main への push で起動しない理由**を返す。空なら起動する（#946）。

    **要るもの**——`on:` のイベントに `pull_request` と `push` の両方があり、それぞれの下に `branches:` 以外の鍵が無く、
    `branches:` があれば `main` を文字どおり含むこと（`push` に `branches:` が無ければ全部の branch で起動する）。
    **読み方**——字下げ 0 の `on:` の行を探し（引用符つきの `"on":` も読む）、その値か、次の字下げ 0 の行までの子を読む。
    値は、フロー形式の列（`[pull_request, push]`）・スカラー（`push`）を読み、フロー形式のマッピング（`{…}`）は読まずに赤。
    子は、ブロックのマッピング（鍵がイベント）とブロックの列（`- push`）を読む。イベントの値は空・`null`・`~`・`{}` だけを
    「狭めていない」と読み、ほかの値（`{branches: [main]}` など）は読まずに赤。**読めない形はどれも赤**——読めない行・
    子より浅い行（`on:` の下でもイベントの下でも）・列の項の下の行・フロー列の `{…}`・`[…]` の項・タブで字下げした行（ファイルのどこでも）・
    2 つ目の `on:`・重なるイベント・イベントの下で重なる鍵（`branches:` を 2 つ）・値と子が両方ある `on:`・列とマッピングが混ざる `on:`・
    `branches:` の下の、項として読めない行（`event_filter_reasons` の docstring）。
    `branches:` に `!` で始まる項（除外）があれば、`main` を含んでいても赤（後ろの `!` が `main` を外しうる——値の照合はしない）。
    コメントは `split_comment` で切ってから読む。

    **値を読まない理由**——`paths:` が変更に当たるか・`types:` に `synchronize` が入るか・glob が `main` に当たるかを決めるのは
    GitHub の照合規則の写しになり、写し損ねると黙って緑になる向きに外れる。鍵があるだけで赤にすれば、外れる向きは
    **偽の赤**（`types: [opened, synchronize, reopened]`・`branches: ['**']` など、起動するのに赤）だけになる。
    **偽の赤になる書き方**: `pull_request_target`・`workflow_call` などほかのイベント（起動の代わりに数えない）・YAML のアンカー
    （`on: *x` はイベントの名前 `*x` に、`<<: *x` は鍵の名前 `<<` に読む——イベントの下なら狭める鍵）・複数行に折ったフロー列。
    **見ないもの**: ワークフロー単位の `concurrency:`（走っている run を止めうる。黙って素通しする向き）。
    **GitHub が実際に起動するかは主張しない**——書いてある `on:` の形だけを見る。
    """
    lines: list[tuple[int, str]] = []
    reasons: set[str] = set()
    for raw in text.split("\n"):
        code, _ = split_comment(raw)
        if code.strip():
            if "\t" in code[:len(code) - len(code.lstrip())]:
                reasons.add("タブで字下げした行がある")
            lines.append((len(code) - len(code.lstrip(" ")), code.strip()))
    starts = [i for i, (ind, c) in enumerate(lines) if ind == 0 and key_of(c) == "on"]
    if not starts:
        return reasons | {"`on:` が無い"}
    if len(starts) > 1:
        reasons.add("`on:` が重なる")
    start = starts[0]
    events: dict[str, tuple[str, list[tuple[int, str]]]] = {}
    value = inline_value(lines[start][1])
    if value.startswith("{"):
        return reasons | {"`on:` の値を読めない（フロー形式のマッピング）"}
    for name in seq_items(value):
        if name[:1] in "{[":
            reasons.add(f"`on:` の項を読めない（`{name}`）")
        events[name] = ("", [])
    body: list[tuple[int, str]] = []
    for ind, c in lines[start + 1:]:
        if ind == 0:
            break
        body.append((ind, c))
    if value and body:
        reasons.add("`on:` に値と子が両方ある")
    level = body[0][0] if body else 0
    cur: str | None = None
    kinds: set[str] = set()
    for ind, c in body:
        if ind < level:
            reasons.add("`on:` の字下げを読めない")
            cur = None
        elif ind == level:
            if SEQ_RE.match(c):
                kinds.add("列")
                name = scalar(c[1:])
                if name in events:
                    reasons.add(f"`on:` の `{name}` が重なる")
                events[name] = ("", [])
                cur = "- "
            else:
                kinds.add("マッピング")
                cur = key_of(c)
                if cur is None:
                    reasons.add(f"`on:` の行を読めない（`{c}`）")
                else:
                    if cur in events:
                        reasons.add(f"`on:` の `{cur}:` が重なる")
                    events[cur] = (inline_value(c), [])
        elif cur == "- ":
            reasons.add(f"`on:` の列の項の下の行を読めない（`{c}`）")
        elif cur is not None:
            events[cur][1].append((ind, c))
    if len(kinds) > 1:
        reasons.add("`on:` に列とマッピングが混ざる")
    for ev in TRIGGER_EVENTS:
        if ev not in events:
            reasons.add(f"`{ev}` で起動しない")
            continue
        val, sub = events[ev]
        if val not in OPEN_VALUES:
            reasons.add(f"`{ev}` の値を読めない（`{val}`）")
        else:
            reasons |= event_filter_reasons(ev, sub)
    return reasons


def untriggered_runs(files: list[str]) -> tuple[set[str], set[str]]:
    """ワークフローの yaml（1 ファイル 1 項）から、**PR と main への push で起動するファイルに無い**名前を 2 つ返す（#946）。

    返すのは `(無条件の位置, 無条件・引数なし)`——**全部を繋いだ文字列では `gated_runs` の無条件（・`full_ungated_runs`）に入るのに、
    起動するファイル（`trigger_reasons` が空）だけを繋いだ文字列では入らない名前**。ファイルを繋いだ文字列には `on:` の境界が
    残らないので、ファイルごとに決めてから繋ぎ直す。**起動しないファイルにだけ全部を回す行を置き、起動するファイルでは狭める形**も、
    後ろの集合で赤になる（#945 の組と同じ形）。
    """
    ci = "\n".join(files)
    live_ci = "\n".join(t for t in files if not trigger_reasons(t))
    return (gated_runs(ci)[0] - gated_runs(live_ci)[0],
            full_ungated_runs(ci) - full_ungated_runs(live_ci))


def test_ci_runs_every_registered_script() -> None:
    """実リポジトリを読む。**`check-all.py` に在るのに CI の yaml に無い**なら落とす。

    **`check-all.py` は CI から呼ばない**（`CLAUDE.md` のとおり、どれが落ちたか UI に
    出すため各スクリプトを個別ステップにしている）。**だから収録と CI 登録は別の作業**で、
    **片方だけ済ませると、そのテストは手元でしか走らない。**

    **照合は名前単位で行う（必須の注意）。** **素の部分文字列一致では、`check-X.py` が
    `test-check-X.py` に覆い隠される**——**最初そう書いて、2 パス目の Verifier に
    「6 本が隠れる」と反証された。** **歯止めを足した当人が、同じ型の盲点を作っていた。**

    **上の `test_registry_covers_every_script` はこの向きを見ていなかった**——
    「`scripts/` に在るのに `check-all.py` に無い」は見るが、
    「`check-all.py` に在るのに CI に無い」は見ない。**実際に 2 本が漏れていた**
    （`test-find-cycle.py` は #136 段 1 から、`test-collect-guard-rejections.py` は
    #122 から。**どちらも手元では緑、CI では 1 度も走っていなかった**）。
    **手順 5 の Verifier が見つけた**（#136 の全段に掛けた回）。

    **コメントアウトされたステップを「走っている」と数えない（#155）。**
    元の実装は `"run:" in l` を満たす行から名前を拾っていたので、
    **`# - run: python3 scripts/check-foo.py` も条件を満たしていた**
    ——**CI のステップをコメントアウトしても、この検査は緑のまま**だった。
    **コメントアウトは、上の 2 本が出荷された状態に戻る最短経路である。**

    **この主張は、実際に当てて確かめる**——`plugins.yml` の生きたステップを 1 つ
    コメントアウトすると、このテストが赤になる（**陽性対照は、変異の前に緑であることで取る**）:

    mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "        run: python3 scripts/check-duplicate-counts.py", "new": "        # run: python3 scripts/check-duplicate-counts.py", "red": "python3 scripts/test-check-all.py --part registry"}
    """
    workflows = REAL_REPO / ".github" / "workflows"
    # **ファイルの境界に改行を挟む。** **素の連結では、末尾に改行の無い yaml が
    # 1 本混ざった時点で、そのファイルの最終行と次のファイルの先頭行が 1 行に繋がる**
    # ——**判別は行単位なので、繋がった側のコメントが生きた側を飲み込む。**
    # **いまは全ファイルが改行で終わっているので実害は無い**（手順 5 の Verifier が確認）。
    texts = {f.name: f.read_text() for f in sorted(workflows.glob("*.yml"))}
    ci = "\n".join(texts.values())
    # **正規表現でソースから拾わない。** **名前に数字や下線が入る・引用符が変わる・
    # 変数から組み立てる**といった変更で `registered` が静かに空になり、
    # **「0 本を検査して OK」**になる（`/code-review` が指摘。#136）。
    # **モジュールを読んで、宣言そのものを見る。**
    mod = load_target()
    registered = sorted({name for name, _, _ in mod.GUARDS} | set(mod.TESTS))
    check("収録の一覧が空でない（空振りしない）", len(registered) > 0)
    # **素の部分文字列一致にしない。** `check-X.py` は **`test-check-X.py` の部分文字列**
    # なので、**`check-X.py` の CI ステップを消しても、`test-` 版が残っていれば隠れる**
    # ——**実測で 6 本が覆い隠されていた**（#136 の 2 パス目で Verifier が指摘）。
    # **`scripts/` の直後から行末・空白までを 1 つの名前として照合する**（`NAME_RE`）。
    live, commented = scan_ci_runs(ci)
    # **2 つに分けて報告する（#155）。** どちらも「CI では走らない」だが、
    # **ステップを足すのと `#` を外すのでは直し方が違う。**
    absent = [n for n in registered if n not in live and n not in commented]
    disabled = [n for n in registered if n not in live and n in commented]
    check(f"収録したものが CI の yaml に在る（{len(registered)} 本）", not absent)
    if absent:
        print(f"       CI の yaml に無い: {absent}")
        print("       **ステップを足す。** 手元では緑でも、CI では 1 度も走らない。")
    check("収録したものの CI ステップが生きている（コメントアウトされていない）", not disabled)
    if disabled:
        print(f"       コメントアウトされている: {disabled}")
        print("       **`#` を外す。** 手元では緑でも、CI では 1 度も走らない。")
    # **ジョブ単位の `if:`・`needs:` で走らなくしたジョブ**（#931）——`run:` の行は生きているので上の 2 つは緑のまま。
    # ジョブは SKIPPED になり、`merge-pr.py` は SKIPPED を通過と読む。実物の `plugins.yml` で当てる——ジョブに `if: false` を足すと赤:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "  cruise-run-serial:\n    runs-on: ubuntu-latest\n", "new": "  cruise-run-serial:\n    if: false\n    runs-on: ubuntu-latest\n", "red": "python3 scripts/test-check-all.py --part registry"}
    # `needs:` を足しても赤（前のジョブが落ちると SKIPPED になる）:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "  cruise-loops:\n    runs-on: ubuntu-latest\n", "new": "  cruise-loops:\n    runs-on: ubuntu-latest\n    needs: [check]\n", "red": "python3 scripts/test-check-all.py --part registry"}
    # ジョブの見出しを深くすると（前のジョブの鍵になる）赤:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "\n  dev-loop:\n", "new": "\n    dev-loop:\n", "red": "python3 scripts/test-check-all.py --part registry"}
    # ジョブの見出しを最上位に出すと（`jobs:` の外になる）赤:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "\n  spec-loop-autopilot-loop:\n", "new": "\nspec-loop-autopilot-loop:\n", "red": "python3 scripts/test-check-all.py --part registry"}
    ok, why = gated_runs(ci)
    gated = [n for n in registered if n in live and n not in ok]
    check("収録したものの CI ステップが、無条件に走るジョブの `steps:` の下にある（#931）", not gated)
    if gated:
        for n in gated:
            print(f"       {n}: {'・'.join(sorted(why.get(n, {'(理由なし)'})))}")
        print("       **ジョブ単位の `if:`・`needs:` を外し、ジョブの字下げを直す。** SKIPPED は失敗に数えられない。")
    # **回帰テストは引数なしで回す**（#687）——狭める口を付けたステップは、テストの一部しか回さない。
    # 実物の `plugins.yml` で当てる——狭める引数を足すと、このテストが赤になる:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "        run: python3 scripts/test-check-duplicate-counts.py\n", "new": "        run: python3 scripts/test-check-duplicate-counts.py --only-scan\n", "red": "python3 scripts/test-check-all.py --part registry"}
    full = full_runs(ci)
    narrowed = [n for n in sorted(mod.TESTS) if n in live and n not in full]
    check("収録した回帰テストを CI が引数なしで回している（狭めていない）", not narrowed)
    if narrowed:
        print(f"       引数を付けて回している: {narrowed}")
        print("       **引数を外す。** 狭めた回は、全部を回す回の代わりにならない。")
    # **無条件のジョブで、引数なしで回しているか**（#945）——上の 2 つ（ジョブの位置・引数）は別々に見るので、無条件のジョブでは狭め、
    # 全部を回す行は条件つきのジョブにだけ置く形は両方とも緑になる。上の 2 つのどちらかで赤になった名前はここに重ねて出さない。
    # 実物の `plugins.yml` で当てる——無条件のジョブの行を狭め、全部を回す行を `if: false` のジョブにだけ置くと赤:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "        run: python3 scripts/test-run-serial.py\n\n", "new": "        run: python3 scripts/test-run-serial.py --narrow\n\n  run-serial-whole:\n    if: false\n    runs-on: ubuntu-latest\n    steps:\n      - run: python3 scripts/test-run-serial.py\n\n", "red": "python3 scripts/test-check-all.py --part registry"}
    both = full_ungated_runs(ci)
    split = [n for n in sorted(mod.TESTS) if n in full and n in ok and n not in both]
    check("収録した回帰テストを、無条件に走るジョブの同じ `run:` の行で引数なしで回している（#945）", not split)
    if split:
        print(f"       無条件のジョブでは狭め、全部を回す行は条件つきのジョブにだけある: {split}")
        print("       **引数なしの `run:` を無条件のジョブに置く。** 条件つきのジョブは SKIPPED になりうる。")
    # **ワークフローの `on:`**（#946）——`on:` を消す・`pull_request` を外す・`paths:` で狭めると、ワークフローごと PR で起動しないのに、
    # `run:` の行もジョブも残るので上の検査は全部緑のまま。起動しないファイルにだけある名前を赤にする（上で赤の名前は重ねて出さない）。
    # 実物の `plugins.yml` で当てる——`pull_request:` を外すと赤:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "on:\n  pull_request:\n  push:\n", "new": "on:\n  push:\n", "red": "python3 scripts/test-check-all.py --part registry"}
    # `paths:` で狭めても赤:
    # mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "on:\n  pull_request:\n  push:\n", "new": "on:\n  pull_request:\n    paths:\n      - docs/**\n  push:\n", "red": "python3 scripts/test-check-all.py --part registry"}
    idle_ok, idle_full = untriggered_runs(list(texts.values()))
    idle = [n for n in registered if n in idle_ok]
    idle += [n for n in sorted(mod.TESTS) if n in idle_full and n not in idle]
    check("収録したものの無条件の `run:` が、PR と main への push で起動するワークフローにある（#946）", not idle)
    if idle:
        for fname, text in texts.items():
            reasons = trigger_reasons(text)
            hit = sorted(set(idle) & gated_runs(text)[0])
            if reasons and hit:
                print(f"       {fname}: {'・'.join(sorted(reasons))} — {hit}")
        print("       **`on:` に `pull_request:` と `push:`（`branches:` に `main`）を置いて狭める鍵を外すか、その `run:`（全部を回す行）を起動するワークフローに移す。**"
              " 起動しないワークフローは PR に検査を出さない。")


# ------------------------------------------------------------------ 変異
MUTANTS = {
    "歯止めが落ちても failed に積まない": (
        "            failed.append(label)\n", "            pass\n"),
    "回帰テストが落ちても failed に積まない": (
        "                failed.append(name)\n", "                pass\n"),
    "失敗があっても 0 を返す": ("        return 1\n", "        return 0\n"),
    "落ちたものの出力を見せない": (
        "        print(out.rstrip())\n", "        pass\n"),
    "飛ばしたことを黙る": (
        '        print("**飛ばしたものは回していない。** '
        '手元の緑をそのまま「全部緑」と報告しない。")\n',
        "        pass\n"),
    "最初の失敗で止める": ("                logs.append((label, out))\n",
                           "                logs.append((label, out))\n                break\n"),
    # 以下は #430（並列）
    "直列に戻す": ("ThreadPoolExecutor(max_workers=opts.jobs)",
                   "ThreadPoolExecutor(max_workers=1)"),
    "--jobs を無視する": ("ThreadPoolExecutor(max_workers=opts.jobs)",
                          "ThreadPoolExecutor(max_workers=os.cpu_count())"),
    "既定を直列にする": ("default=os.cpu_count() or 1,", "default=1,"),
    "宣言順に出さない": ("        for label, fut in guard_runs:\n",
                         "        for label, fut in reversed(guard_runs):\n"),
    "回帰テストを宣言順に出さない": ("            for name, fut in test_runs:\n",
                                     "            for name, fut in reversed(test_runs):\n"),
    "--jobs 0 を通す": ("    if opts.jobs < 1:\n", "    if False:\n"),
    # 以下は #509（打ち切られた子を集計で失敗に数える）
    "シグナルで止まった子を通ったと数える": (
        "    return proc.returncode == 0, (out + err)\n",
        "    return proc.returncode <= 0, (out + err)\n"),
    # **FAIL の行が集計と別の経路で増える**（#509 の症状——FAIL の行と「失敗 N」が食い違う——の形）。
    # **これを捕まえるのは契約 10 の「FAIL の行の数と『失敗 N』が一致する」だけ**である（#687。ほかの変異は
    # どれも、その表明のほかに別の表明も破る——表明ごとに破れた変異を数えて確かめた）。
    "落ちたものの出力の見出しを FAIL の行の形で出す": (
        '        print(f"\\n----- {label} の出力 -----")\n',
        '        print(f"  FAIL {label}")\n'),
    # 以下は #460（入れ子の並列）
    "入れ子に --jobs を渡さない": ('                args = [*args, "--jobs", str(nested_jobs(opts.jobs))]\n',
                                   "                pass\n"),
    "回帰テストの入れ子に --jobs を渡さない（#749）": (
        '["--jobs", str(nested_jobs(opts.jobs))] if name in NESTED else []',
        '[]'),
    "--jobs を受けない回帰テストの 1 本にも --jobs を渡す（#749 の 2 パス目）": (
        '["--jobs", str(nested_jobs(opts.jobs))] if name in NESTED else []',
        '["--jobs", str(nested_jobs(opts.jobs))] if name in NESTED or name == "test-check-all.py" else []'),
    "回帰テストの全部に --jobs を渡す（#749）": (
        '["--jobs", str(nested_jobs(opts.jobs))] if name in NESTED else []',
        '["--jobs", str(nested_jobs(opts.jobs))]'),
    "入れ子に親と同じ並列数を渡す": ("    return max(1, jobs // 2)\n", "    return jobs\n"),
    "入れ子を 0 にしうる": ("    return max(1, jobs // 2)\n", "    return jobs // 2\n"),
    # **終わった順に出す**本体を写した変異（`as_completed`。#430 の 2 パス目）。`reversed()` だけでは、
    # 受入基準 P11 が挙げる「終わった順」を表す変異が無かった。歯止めの側は SKIP（すぐ終わる）が先に出るので
    # 試料の遅延に依らず崩れる——**遅延を外しても 2 本とも捕まえた**ので、遅延が要るとは言えない。
    "歯止めを終わった順に出す": (
        "        for label, fut in guard_runs:\n",
        "        import concurrent.futures as _cf\n"
        "        _m = {f: (l, f) for l, f in guard_runs if f is not None}\n"
        "        for label, fut in [r for r in guard_runs if r[1] is None]"
        " + [_m[f] for f in _cf.as_completed(_m)]:\n"),
    "回帰テストを終わった順に出す": (
        "            for name, fut in test_runs:\n",
        "            import concurrent.futures as _cf\n"
        "            _m = {f: (n, f) for n, f in test_runs}\n"
        "            for name, fut in [_m[f] for f in _cf.as_completed(_m)]:\n"),
}


# ------------------------------------------------- 判別の契約（合成試料）
# **実物の yaml では、この経路は永久に空振りする**——`.github/workflows/` に
# **コメントアウトされたステップは 1 件も無い**（#155 の時点で 0 件）。
# **試料のほうに、経路を全部踏ませる。**
SAMPLE_CI = """\
jobs:
  probe:
    steps:
      - name: 生きたステップ
        run: python3 scripts/check-live.py

      # - name: 止めたステップ
      #   run: python3 scripts/check-dead.py

      - name: scripts/check-label-only.py のラベルにだけ名前がある
        run: echo ok

      - name: 行末にコメント
        run: python3 scripts/check-live2.py  # scripts/check-trailing.py は別

      - name: 名前が覆い隠される
        run: python3 scripts/test-check-mask.py

      - name: 引用符の中の `#`
        run: "echo 'PR #155' && python3 scripts/check-quoted.py"

      - name: 語の途中のアポストロフィ
        run: echo don't  # python3 scripts/check-apostrophe.py

      - name: 値の途中の引用符（パリティが反転しうる形）
        run: echo skip --sep=", "  # python3 scripts/check-midquote.py

      - name: 値の先頭の引用符が閉じない（安全側＝コメント扱いに倒す）
        run: "unterminated  # python3 scripts/check-unterminated.py

      - name: 素の値の中の引用符（yaml はここで切る）
        run: echo "a # python3 scripts/check-plainhash.py"

      # - name: 名前と run: を別の行に割って止めたステップ（**守らない**）
      #   run:
      #     python3 scripts/check-dead-split.py

      - name: 常に偽の条件（**守らない**——記述しか見ていない）
        if: false
        run: python3 scripts/check-killed-by-if.py

      - name: ブロックで呼ぶ（**守らない**——`run:` を含む行だけを見る）
        run: |
          python3 scripts/check-in-block.py

      - name: 狭める引数を付けて呼ぶ（#687——走っているが、全部ではない）
        run: python3 scripts/test-check-narrowed.py --part scan

      - name: 引数なしで後ろにつなぐ（#687——全部を回している）
        run: python3 scripts/test-check-chained.py && echo done

      - name: 次の行へ折り返して狭める（#687 の 2 パス目——YAML では同じ値の続き）
        run: python3 scripts/test-check-folded.py
          --part scan

      - name: 空行を挟んで折り返して狭める（#752——YAML では空行を挟んでも同じ値の続き）
        run: python3 scripts/test-check-folded-blank.py

          --part scan

      - name: 次の行が深い字下げのコメント（#753——YAML ではコメントで、値の続きではない）
        run: python3 scripts/test-check-deep-comment.py
          # 注記

      - name: 環境変数を前に置いて狭める（#750——走っているが、全部ではない）
        run: PART=scan python3 scripts/test-check-env-prefixed.py

      - name: 環境変数を書き出してからつなぐ（#750）
        run: export PART=scan && python3 scripts/test-check-env-exported.py

      - name: 小文字の変数で狭める（#750 の 2 パス目——変数名の大小で判定を変えない）
        run: part=scan python3 scripts/test-check-env-lower.py

      - name: 名前より後ろの変数（#750 の 2 パス目——そのスクリプトは狭めていない）
        run: python3 scripts/test-check-env-after.py && export X=1
"""
# **この試料そのものについての主張も、機械で当てる**——
# **コメントアウトされたステップを抜くと、「それと分かる形で拾う」契約が空振りする**
# （#151 が言う「試料についての主張」。**書いた時点から一度も実行されない**のを避ける）:
# mutation-claim: {"file": "scripts/test-check-all.py", "old": "      #   run: python3 scripts/check-dead.py\n", "new": "", "red": "python3 scripts/test-check-all.py --part scan"}
# **ラベルだけの行は、消しても緑になる**（`not in seen` が名前ごと消えて恒真になり、
# `run:` の行に限らない 変異は別の行が殺す）。**`/code-review` の 2 パス目が数えて見つけた。**
# **だから「消す」ではなく「`run:` に変える」で留める**——**消されたらマーカーの当て先が
# 無くなり、`check-mutation-claims.py` が「当てられなかった」で赤にする**（緑ではない）:
# mutation-claim: {"file": "scripts/test-check-all.py", "old": "      - name: scripts/check-label-only.py のラベルにだけ名前がある", "new": "        run: scripts/check-label-only.py のラベルにだけ名前がある", "red": "python3 scripts/test-check-all.py --part scan"}


# **ジョブの位置の試料**（#931）——`gated_runs` の経路を全部踏ませる。ファイルを繋いだ形（2 つ目の `name:` から）も含める。
SAMPLE_JOBS = """\
name: one
on:
  push:
    run: python3 scripts/job-under-on.py
jobs:
  plain:
    runs-on: ubuntu-latest
    steps:
      - name: 無条件
        run: python3 scripts/job-plain.py
      - name: ステップの if は見ない
        if: github.event_name == 'pull_request'
        run: python3 scripts/job-step-if.py
      - name: 両方にある（無条件の側があれば赤にしない）
        run: python3 scripts/job-both.py
      # - run: python3 scripts/job-if.py
      - name: scripts/job-label-only.py のラベルにだけ名前がある
        run: echo ok
  gated:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-if.py
      - run: python3 scripts/job-both.py
  waits:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-needs-after.py
    needs:
      - plain
  # コメントだけの行は鍵の段を決めない
  deep:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-before-deep.py
    nested:
      runs-on: ubuntu-latest
      steps:
        - run: python3 scripts/job-nested.py
  dup:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-dup-first.py
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-dup.py
  keyrun:
    runs-on: ubuntu-latest
    run: python3 scripts/job-keyrun.py
    steps:
      - run: python3 scripts/job-after-keyrun.py
toplevel:
  steps:
    - run: python3 scripts/job-toplevel.py
name: two
jobs:
  second:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-second-file.py
name: three
jobs:
    wide:
      runs-on: ubuntu-latest
      steps:
        - run: python3 scripts/job-wide.py
  shallow:
    steps:
      - run: python3 scripts/job-shallow.py
name: four
jobs:
  twin:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-twin-gated.py
  flat:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-flat.py
  deeper:
      "if": false
      runs-on: ubuntu-latest
      steps:
        - run: python3 scripts/job-deeper.py
  "quoted":
    runs-on: ubuntu-latest
    'needs': [flat]
    steps:
      - run: python3 scripts/job-quoted-needs.py
name: five
jobs:
  twin:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-twin-plain.py
  spaced:
    if : false
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-spaced-if.py
  gap:
    if: false
  # 見出しと同じ字下げのコメント
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-comment-gap.py
  odd:
      runs-on: ubuntu-latest
    steps:
        - run: python3 scripts/job-odd.py
  compact:
    runs-on: ubuntu-latest
    steps:
    - run: python3 scripts/job-compact-a.py
    - name: 名前の次の行の run
      run: python3 scripts/job-compact-b.py
    -
      run: python3 scripts/job-compact-dash.py
  compact-needs:
    runs-on: ubuntu-latest
    steps:
    - run: python3 scripts/job-compact-needs.py
    needs:
    - compact
  compact-gated:
    runs-on: ubuntu-latest
    steps:
    - run: python3 scripts/job-compact-gated.py
    if: false
  compact-other:
    runs-on: ubuntu-latest
    services:
    - run: python3 scripts/job-compact-services.py
    steps:
    - run: python3 scripts/job-compact-after-services.py
  compact-shallow:
      runs-on: ubuntu-latest
      steps:
    - run: python3 scripts/job-compact-shallow.py
    - run: python3 scripts/job-compact-shallow-2.py
  dash-key:
    runs-on: ubuntu-latest
    steps:
    - run: python3 scripts/job-before-dash-key.py
    -weird:
      run: python3 scripts/job-dash-key.py
x-jobs:
  build:
    steps:
      - run: python3 scripts/job-under-jobsish.py
"""


# **ジョブの位置と引数の組の試料**（#945）——`full_runs` と `gated_runs` は別々に見ると両方とも緑になる形。
SAMPLE_SPLIT = """\
jobs:
  narrow:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/test-split.py --part scan
      - run: python3 scripts/test-whole.py
      - run: python3 scripts/test-split-needs.py --part scan
      - run: python3 scripts/test-pair-a.py --part scan && python3 scripts/test-pair-b.py
  gated:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/test-split.py
      - run: python3 scripts/test-whole.py --part scan
      - run: python3 scripts/test-pair-a.py
  waits:
    runs-on: ubuntu-latest
    needs: [narrow]
    steps:
      - run: python3 scripts/test-split-needs.py
"""

# #946: ワークフローの `on:`。各試料の後ろにジョブを置く——`on:` の子が次の字下げ 0 の行で終わることも見る。
ON_JOB = "jobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: python3 scripts/x.py\n"
SAMPLE_ON = {
    # 起動する（陽性対照）
    "block": "on:\n  pull_request:\n  push:\n    branches:\n      - main\n",
    "flow-branches": 'on:\n  pull_request:\n    branches: [main]\n  push:\n    branches: ["main", dev]\n',
    "compact-branches": "on:\n  pull_request:\n  push:\n    branches:\n    - main\n    - 'dev'\n",
    "seq": "on:\n  - pull_request\n  - push\n",
    "flow-seq": "on: [pull_request, push]  # 両方\n",
    "quoted-key": '"on":\n  pull_request: {}\n  push: null  # 全部の branch\n',
    # 起動しない
    "no-on": "name: x\n",
    "nested-on": "name: x\nx:\n  on:\n    pull_request:\n    push:\n",
    "commented-pr": "on:\n  # pull_request を外した\n  # pull_request:\n  push:\n    branches: [main]\n",
    "push-only": "on:\n  push:\n    branches: [main]\n",
    "pr-scalar": "on: pull_request\n",
    "flow-seq-push": "on: [push]\n",
    "dispatch": "on:\n  workflow_dispatch:\n",
    "pr-target": "on:\n  pull_request_target:\n  push:\n    branches: [main]\n",
    "paths": "on:\n  pull_request:\n    paths:\n      - docs/**\n  push:\n    branches: [main]\n",
    "paths-ignore": "on:\n  pull_request:\n  push:\n    branches: [main]\n    paths-ignore: ['**.md']\n",
    "branches-other": "on:\n  pull_request:\n  push:\n    branches:\n      - release\n",
    "branches-mainish": "on:\n  pull_request:\n  push:\n    branches: [maintenance, '\"main\"']\n",
    "branches-ignore": "on:\n  pull_request:\n    branches-ignore: [main]\n  push:\n",
    "types": "on:\n  pull_request:\n    types: [closed]\n  push:\n",
    "tags": "on:\n  pull_request:\n  push:\n    tags: ['v*']\n",
    "flow-map": "on: {pull_request: {}, push: {branches: [main]}}\n",
    "event-flow-map": "on:\n  pull_request:\n  push: {branches: [main]}\n",
    "odd-line": "on:\n  pull_request:\n  push:\n  ???\n",
    "event-odd": "on:\n  pull_request:\n    ???\n  push:\n",
    "shallow": "on:\n    pull_request:\n    push:\n  odd:\n",
    # #946 の 1 パス目（Verifier の軽微・/code-review の CR1・CR2・CR4・CR5）——読めない・重なる形も赤（黙って緑にしない）
    "tab-child": "on:\n  pull_request:\n  push:\n\tbranches: [dev]\n",
    "negated": "on:\n  pull_request:\n    branches: [main, '!main']\n  push:\n    branches:\n      - main\n      - '!ma*'\n",
    "dup-event": "on:\n  pull_request:\n    paths: [docs/**]\n  pull_request:\n  push:\n",
    "dup-branches": "on:\n  pull_request:\n  push:\n    branches: [dev]\n    branches: [main]\n",
    "dup-on": "on:\n  pull_request:\n  push:\non:\n  workflow_dispatch:\n",
    "value-and-body": "on: workflow_dispatch\n  pull_request:\n  push:\n",
    "mixed": "on:\n  pull_request:\n    paths: [x]\n  - pull_request\n  - push\n",
    "seq-deeper": "on:\n  - pull_request\n  - push\n      paths: [x]\n",
    "event-shallow": "on:\n  pull_request:\n      branches: [main]\n    paths: [docs]\n  push:\n",
    "flow-odd-item": "on: [pull_request, push, {x: 1}]\n",
    # #946 の 2 パス目（/code-review・Verifier）——`branches:` の下の YAML どおりでない読み方
    "branches-cont": "on:\n  pull_request:\n    branches: main\n      dev\n  push:\n",
    "branches-value-item": "on:\n  pull_request:\n  push:\n    branches: dev\n      - main\n",
    "branches-item-deeper": "on:\n  pull_request:\n  push:\n    branches:\n      - dev\n        - main\n",
    "branches-item-map": "on:\n  pull_request:\n  push:\n    branches:\n      - main\n      - paths: [x]\n",
    "branches-flow-item": "on:\n  pull_request:\n  push:\n    branches: [dev]\n    - main\n",
}
# `untriggered_runs`——起動するファイルでは狭め・位置は条件つき、起動しないファイルにだけ全部を回す行と無条件の行を置く。
ON_FILES = [
    "on: [pull_request, push]\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n"
    "      - run: python3 scripts/test-on-split.py --part scan\n      - run: python3 scripts/on-both.py\n"
    "  b:\n    if: false\n    runs-on: ubuntu-latest\n    steps:\n      - run: python3 scripts/on-idle-only.py\n",
    "on:\n  workflow_dispatch:\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n"
    "      - run: python3 scripts/test-on-split.py\n      - run: python3 scripts/on-both.py\n"
    "      - run: python3 scripts/on-idle-only.py\n",
]


def scan_contract(scan, full_of, gate_of, both_of, on_of, idle_of) -> list[tuple[str, bool]]:
    """**判別の契約。** 各行が `SAMPLE_CI`・`SAMPLE_JOBS`・`SAMPLE_SPLIT`・`SAMPLE_ON`・`ON_FILES` のどれかの経路に対応している。

    **陽性側も取る**——「拾わない」だけを並べると、**もともと空の集合**と区別がつかない
    （**陰性だけの対照は対照ではない**）。
    """
    live, commented = scan(SAMPLE_CI)
    seen = live | commented
    full = full_of(SAMPLE_CI)
    ok, why = gate_of(SAMPLE_JOBS)
    gated = set(why) - ok
    split_full = full_of(SAMPLE_SPLIT)
    split_ok, _ = gate_of(SAMPLE_SPLIT)
    both = both_of(SAMPLE_SPLIT)
    on = {k: on_of(v + ON_JOB) for k, v in SAMPLE_ON.items()}
    on_after = on_of(ON_JOB + SAMPLE_ON["block"])
    idle_ok, idle_full = idle_of(ON_FILES)
    return [
        # #946: ワークフローの `on:`（陽性側も取る——起動する形を「起動する」と読む）
        ("ブロックのマッピング・列・フロー列・`branches:` の列（フロー・深い・コンパクト）・引用符つきの `\"on\":` を起動すると読む（陽性対照）",
         all(not on[k] for k in ("block", "flow-branches", "compact-branches", "seq", "flow-seq", "quoted-key"))),
        ("`on:` がジョブの後ろにあっても読む", not on_after),
        ("`on:` が無いと赤", on["no-on"] == {"`on:` が無い"}),
        ("字下げした `on:` は `on:` と読まない", on["nested-on"] == {"`on:` が無い"}),
        ("コメントアウトした `pull_request:` を数えない", on["commented-pr"] == {"`pull_request` で起動しない"}),
        ("`pull_request` が無いと赤（`push` だけ・`pull_request_target`）",
         on["push-only"] == {"`pull_request` で起動しない"} and on["pr-target"] == {"`pull_request` で起動しない"}),
        ("`push` が無いと赤（スカラー・フロー列）",
         on["pr-scalar"] == {"`push` で起動しない"} and on["flow-seq-push"] == {"`pull_request` で起動しない"}),
        ("`workflow_dispatch` だけなら両方が無いと赤",
         on["dispatch"] == {"`pull_request` で起動しない", "`push` で起動しない"}),
        ("`paths:`・`paths-ignore:`・`branches-ignore:`・`types:`・`tags:` で狭めると赤",
         on["paths"] == {"`pull_request` の `paths:` で狭めている"}
         and on["paths-ignore"] == {"`push` の `paths-ignore:` で狭めている"}
         and on["branches-ignore"] == {"`pull_request` の `branches-ignore:` で狭めている"}
         and on["types"] == {"`pull_request` の `types:` で狭めている"}
         and on["tags"] == {"`push` の `tags:` で狭めている"}),
        ("`branches:` に `main` が文字どおり無いと赤（`maintenance`・引用符を残した `\"main\"`）",
         on["branches-other"] == {"`push` の `branches:` に `main` が無い"}
         and on["branches-mainish"] == {"`push` の `branches:` に `main` が無い"}),
        ("フロー形式のマッピングは読まずに赤（`on:` の値・イベントの値）",
         on["flow-map"] == {"`on:` の値を読めない（フロー形式のマッピング）"}
         and on["event-flow-map"] == {"`push` の値を読めない（`{branches: [main]}`）"}),
        ("読めない行・`on:` の子より浅い行は赤",
         on["odd-line"] == {"`on:` の行を読めない（`???`）"} and on["shallow"] == {"`on:` の字下げを読めない"}
         and on["event-odd"] == {"`pull_request` の下の行を読めない（`???`）"}),
        ("タブで字下げした行は赤（`on:` の子がそこで切れても緑にしない）", on["tab-child"] == {"タブで字下げした行がある"}),
        ("`branches:` の `!` の除外は赤", on["negated"] == {"`pull_request` の `branches:` に `!` の除外がある",
                                                        "`push` の `branches:` に `!` の除外がある"}),
        ("重なる鍵は赤（イベント・`branches:`・`on:`）",
         on["dup-event"] == {"`on:` の `pull_request:` が重なる"}
         and on["dup-branches"] == {"`push` の `branches:` が重なる"}
         and on["dup-on"] == {"`on:` が重なる"}),
        ("値と子が両方・列とマッピングが混ざる・列の項の下の行・イベントの下の浅い行・フロー列の読めない項は赤",
         on["value-and-body"] == {"`on:` に値と子が両方ある"}
         and on["mixed"] == {"`on:` に列とマッピングが混ざる", "`on:` の `pull_request` が重なる"}
         and on["seq-deeper"] == {"`on:` の列の項の下の行を読めない（`paths: [x]`）"}
         and on["event-shallow"] == {"`pull_request` の下の字下げを読めない"}
         and on["flow-odd-item"] == {"`on:` の項を読めない（`{x: 1}`）"}),
        ("`branches:` の下の継続行・値の後ろの項・項より深い行・マッピングの項は赤（黙って `main` と読まない）",
         on["branches-cont"] == {"`pull_request` の `branches:` の下の行を読めない（`dev`）"}
         and on["branches-value-item"] == {"`push` の `branches:` の下の行を読めない（`- main`）", "`push` の `branches:` に `main` が無い"}
         and on["branches-item-deeper"] == {"`push` の `branches:` の下の行を読めない（`- main`）", "`push` の `branches:` に `main` が無い"}
         and on["branches-item-map"] == {"`push` の `branches:` の下の行を読めない（`- paths: [x]`）"}
         and "`push` の `branches:` に `main` が無い" in on["branches-flow-item"] and len(on["branches-flow-item"]) == 2),
        ("起動しないファイルにだけある無条件の行を数える（起動するファイルでは条件つき）",
         "on-idle-only.py" in idle_ok and "on-both.py" not in idle_ok and "test-on-split.py" not in idle_ok),
        ("起動しないファイルにだけ全部を回す行を置き、起動するファイルでは狭める形を数える",
         "test-on-split.py" in idle_full and "on-both.py" not in idle_full),
    ] + [
        # #945: ジョブの位置と引数を同じ行で突き合わせる（陽性側も取る）
        ("無条件のジョブで引数なしの行を、両方を満たすと数える（陽性対照）",
         {"test-whole.py", "test-pair-b.py"} <= both),
        ("無条件のジョブでは狭め、全部を回すのは `if:` のジョブだけの形を数えない（別々には両方とも満たす）",
         "test-split.py" in split_full and "test-split.py" in split_ok and "test-split.py" not in both),
        ("全部を回すのが `needs:` のジョブだけの形も数えない",
         "test-split-needs.py" in split_full and "test-split-needs.py" in split_ok
         and "test-split-needs.py" not in both),
        ("同じ行の別の名前が引数なしでも、狭めた名前は数えない",
         "test-pair-a.py" in split_full and "test-pair-a.py" in split_ok and "test-pair-a.py" not in both),
    ] + [
        # #931: ジョブの位置（陽性側も取る——無条件の位置を「無条件」に数える）
        ("無条件のジョブの `steps:` の下を無条件に数える（陽性対照）",
         {"job-plain.py", "job-step-if.py", "job-before-deep.py", "job-after-keyrun.py",
          "job-second-file.py", "job-wide.py", "job-flat.py", "job-twin-plain.py"} <= ok),
        ("ステップ単位の `if:` は見ない（守らない）", "job-step-if.py" in ok),
        ("ジョブの `if:` の下を条件つきに数える", "job-if.py" in gated and "ジョブの `if:`" in why["job-if.py"]),
        ("`steps:` の後ろの `needs:` も効かせる", "job-needs-after.py" in gated
         and "ジョブの `needs:`" in why["job-needs-after.py"]),
        ("無条件の側があれば条件つきに数えない", "job-both.py" in ok),
        ("深くした見出しの下（前のジョブの鍵）を条件つきに数える", "job-nested.py" in gated),
        ("鍵が重なるジョブを条件つきに数える", {"job-dup.py", "job-dup-first.py"} <= gated),
        ("`steps:` の外の `run:` を条件つきに数える", "job-keyrun.py" in gated),
        ("`jobs:` の外の `run:` を条件つきに数える",
         {"job-under-on.py", "job-toplevel.py"} <= gated and "ジョブの外" in why["job-toplevel.py"]),
        ("見出しの段より浅い行から先をジョブの外に数える", "ジョブの外" in why.get("job-shallow.py", set())),
        # #931 の 1 パス目（V1・V4）
        ("引用符つきの鍵（`\"if\":`・`\'needs\':`）も鍵と読む",
         "ジョブの `if:`" in why.get("job-deeper.py", set())
         and "ジョブの `needs:`" in why.get("job-quoted-needs.py", set())),
        ("前のジョブより深い段の鍵も、そのジョブの鍵と読む（ジョブごとに鍵の段を決め直す）",
         "ジョブの `if:`" in why.get("job-deeper.py", set()) and "job-deeper.py" not in ok),
        ("別のファイルの同じ名前のジョブを、別のジョブとして数える",
         "ジョブの `if:`" in why.get("job-twin-gated.py", set()) and "job-twin-plain.py" not in why),
        ("試料の名前を全部どちらかに分ける（落とさない。ラベルにだけある名前は数えない）",
         ok | set(why) == set(NAME_RE.findall(SAMPLE_JOBS)) - {"job-label-only.py"}),
        # #931 の 2 パス目（VA・VB・R6）
        ("コロンの前に空白を置いた鍵も鍵と読む", "ジョブの `if:`" in why.get("job-spaced-if.py", set())),
        ("見出しと同じ字下げのコメントの行で、ジョブを区切らない",
         "job-comment-gap.py" in gated and "ジョブの `if:`" in why["job-comment-gap.py"]),
        ("コメントアウトしたステップを、無条件の位置に数えない", "job-if.py" not in ok),
        ("`- name:` のラベルにだけある名前を拾わない", "job-label-only.py" not in ok | set(why)),
        ("最上位の鍵は `jobs` に完全に一致するときだけジョブにする",
         "ジョブの外" in why.get("job-under-jobsish.py", set()) and "job-under-jobsish.py" not in ok),
        ("鍵の段でない行を鍵と読まない", "job-odd.py" in gated),
        # #944: コンパクトな列（`steps:` と同じ字下げの `- `）
        ("コンパクトな列を `steps:` の下と読む（`- run:`・名前の次の行・`-` だけの行）",
         {"job-compact-a.py", "job-compact-b.py", "job-compact-dash.py",
          "job-compact-after-services.py"} <= ok
         and not {"job-compact-a.py", "job-compact-b.py", "job-compact-dash.py"} & set(why)),
        ("コンパクトな列で書いた `needs:` を効かせ、鍵の重なりに数えない",
         why.get("job-compact-needs.py") == {"ジョブの `needs:`"}),
        ("コンパクトな列の後ろのジョブの `if:` を効かせる",
         why.get("job-compact-gated.py") == {"ジョブの `if:`"}),
        ("`steps:` でない鍵の下のコンパクトな列は `steps:` の外のまま",
         why.get("job-compact-services.py") == {"`steps:` の外（services）"}),
        ("鍵の段より浅い `- ` は鍵の段でない（`steps:` の外）",
         why.get("job-compact-shallow.py") == {"`steps:` の外（None）"}),
        ("`-` で始まる鍵（`-weird:`）は列の項と読まない（`steps:` の外）",
         "job-before-dash-key.py" in ok and why.get("job-dash-key.py") == {"`steps:` の外（None）"}),
    ] + [
        ("生きたステップを拾う（陽性対照）", "check-live.py" in live),
        ("コメントアウトされたステップを、生きている側に数えない",
         "check-dead.py" not in live),
        ("コメントアウトされたステップを、それと分かる形で拾う",
         "check-dead.py" in commented),
        ("`- name:` のラベルだけの名前は拾わない", "check-label-only.py" not in seen),
        ("行末コメントの中の名前は拾わない（その行の生きた名前は拾う）",
         "check-trailing.py" not in seen and "check-live2.py" in live),
        ("`check-X.py` が `test-check-X.py` に覆い隠されない",
         "check-mask.py" not in seen and "test-check-mask.py" in live),
        ("引用符の中の `#` で切らない", "check-quoted.py" in live),
        # **こちらは逆向き**——上は「早く切りすぎない」、これは「切り損ねない」。
        # **片側だけ試料に置くと、切り損ねる欠陥を契約が判別できない**
        # （`/code-review` 1 パス目の指摘。**実際にこの向きの穴が残っていた**）。
        ("語の途中のアポストロフィで引用符を開かない", "check-apostrophe.py" not in seen),
        # **2 パス目の HIGH の回帰止め**——**値の途中の引用符でパリティが反転すると、
        # そこから行末までが「値」になってコメントを飲み込んだ**（偽陰性）。
        ("値の途中の引用符でパリティを反転させない", "check-midquote.py" not in seen),
        ("値の先頭の引用符が閉じないなら信じない（安全側に倒す）",
         "check-unterminated.py" not in seen),
        # **素の値（引用符で始まらない値）の中の引用符は、yaml でも値を守らない**
        # ——`run: echo "a # x"` は ` #` で切れる。**`live` に入れてはならない。**
        ("素の値の中の引用符は、引用された値として扱わない",
         "check-plainhash.py" not in seen),
        # **守らないものも契約に書く**——**限界を機械で見える形に留める**ため。
        # **黙って射程が変わったら、docstring の「守らない」と食い違ったまま緑になる。**
        ("名前と `run:` が別の行に割れたコメントアウトは、コメント側として拾えない（守らない）",
         "check-dead-split.py" not in seen),
        ("`if:` で止めたステップは、生きているものとして数える（守らない）",
         "check-killed-by-if.py" in live),
        ("`run: |` のブロック本文は拾わない（守らない）", "check-in-block.py" not in seen),
        # #687: 引数の有無（陽性側も取る——引数なしの行を「全部」に数える）
        ("引数なしの行は全部を回している側に数える（陽性対照）",
         {"check-live.py", "test-check-chained.py"} <= full),
        ("狭める引数を付けた行は、走っているが全部を回している側に数えない",
         "test-check-narrowed.py" in live and "test-check-narrowed.py" not in full),
        ("コメントアウトされた行は全部を回している側に数えない", "check-dead.py" not in full),
        ("次の行へ折り返した値は、全部を回している側に数えない", "test-check-folded.py" not in full),
        ("空行を挟んで折り返した値も、全部を回している側に数えない（#752）",
         "test-check-folded-blank.py" in live and "test-check-folded-blank.py" not in full),
        # 陽性側（#753）——深い字下げのコメントの行を続きと読むと、引数なしの行を「狭めた」と誤って赤にする
        ("次の行が深い字下げのコメントなら、続きと読まずに全部に数える（#753）", "test-check-deep-comment.py" in full),
        ("環境変数を前に置いた行は、走っているが全部を回している側に数えない（#750）",
         "test-check-env-prefixed.py" in live and "test-check-env-prefixed.py" not in full),
        ("環境変数を書き出してからつないだ行も、全部を回している側に数えない（#750）",
         "test-check-env-exported.py" in live and "test-check-env-exported.py" not in full),
        ("小文字の変数で狭めた行も、全部を回している側に数えない（#750）",
         "test-check-env-lower.py" in live and "test-check-env-lower.py" not in full),
        # 陽性側——判定の範囲は `run:` から名前まで。行全体で探すと、名前より後ろの変数で誤って赤にする
        ("名前より後ろの変数は、その名前を全部に数える（#750）", "test-check-env-after.py" in full),
    ]


# ------------------------------------------------------------ 判別の変異
# **この battery は*自分自身*を壊す**ので、**当て先を数える範囲から辞書自身を外す**
# ——**辞書に書いた文字列も「その文字列の出現」なので、素に数えると必ず 2 箇所になり、
# 「当て先が 1 箇所」の検査が全件落ちる。**
SELF_SRC = Path(__file__).resolve().read_text()
CODE_ONLY = SELF_SRC.split("\nSCAN_MUTANTS")[0]

SCAN_MUTANTS = {
    "コメントの始まりを見ない": (
        '        if line[i] == "#" and (i == 0 or line[i - 1] in ',
        '        if False and (i == 0 or line[i - 1] in '),
    "引用された値を見ない": ("    span = quoted_span(line)", "    span = None"),
    "閉じない引用符も信じる": (
        "    if close_i == -1:\n        return None",
        "    if close_i == -1:\n        close_i = len(line)"),
    "引用符を行のどこでも開く": (
        '    m = VALUE_QUOTE_RE.match(line)', '    m = VALUE_QUOTE_RE.search(line)'),
    "生きている側とコメント側を取り違える": (
        "        return line[:i], line[i:]",
        "        return line[i:], line[:i]"),
    "`run:` の行に限らない": ('        if "run:" in code:', "        if True:"),
    "コメント側を集めない": ('        if "run:" in comment:', "        if False:"),
    # #687: 引数を見ない（狭めたステップも全部を回していると数える）
    "引数があっても全部を回していると数える": (
        '(?=\\s*(?:$|&&|\\|\\||;|\\|))")', '")'),
    "コメントの中の引数なしも全部に数える": (
        "        alive, _ = split_comment(raw)\n",
        "        alive = raw\n"),
    "折り返した値を見ない": (
        "            continue  # 次の行に値が続く", "            pass  # 次の行に値が続く"),
    "すぐ次の行だけを見る（空行を挟んだ続きを見落とす。#752）": (
        '        nxt = next((l for l in lines[i + 1:] if l.strip()), "")',
        '        nxt = lines[i + 1] if i + 1 < len(lines) else ""'),
    "深い字下げのコメントの行も続きと読む（#753）": (
        ' and not nxt.lstrip().startswith("#"):', ':'),
    "環境変数を置いた形も全部に数える（#750）": (
        "            if ENV_RE.search(alive[head:m.start()]):", "            if False:"),
    "環境変数を行全体で探す（#750 の 2 パス目）": (
        "            if ENV_RE.search(alive[head:m.start()]):", "            if ENV_RE.search(alive):"),
    "大文字の変数だけを見る（#750 の 2 パス目）": (
        'ENV_RE = re.compile(r"(?:^|\\s)[A-Za-z_][A-Za-z0-9_]*=")',
        'ENV_RE = re.compile(r"(?:^|\\s)[A-Z_][A-Z0-9_]*=")'),
    # #931: ジョブの位置（`gated_runs`）
    "ジョブの `if:` を見ない": ('GATE_KEYS = ("if", "needs")', 'GATE_KEYS = ("needs",)'),
    "ジョブの `needs:` を見ない": ('GATE_KEYS = ("if", "needs")', 'GATE_KEYS = ("if",)'),
    "`jobs:` の外を見ない": (
        '            reasons.add("ジョブの外")', '            pass'),
    "`steps:` の外を見ない": (
        '            if k != "steps":', '            if False:'),
    "鍵の重なりを見ない": ("            if dup:", "            if False:"),
    "最上位の鍵で区切らない": (
        '            in_jobs = head == "jobs"',
        '            in_jobs = in_jobs or head == "jobs"'),
    "見出しの段より浅い行で区切らない": (
        "                in_jobs = False  # 見出しの段より浅い", "                pass  # 見出しの段より浅い"),
    "鍵の段より深い行も鍵と読む": ("                elif indent <= key_indent:", "                elif True:"),
    # #931 の 1 パス目（V1・V4）
    "引用符つきの鍵を読まない": (
        '''KEY_RE = re.compile(r"""(?:"([^"]*)"|\'([^\']*)\'|([^\\s:#\'"-][^\\s:]*))\\s*:(?:\\s|$)""")''',
        '''KEY_RE = re.compile(r"""([^\\s:#\'"-][^\\s:]*)\\s*:(?:\\s|$)""")'''),
    "コロンの前の空白を許さない": (
        '''KEY_RE = re.compile(r"""(?:"([^"]*)"|\'([^\']*)\'|([^\\s:#\'"-][^\\s:]*))\\s*:(?:\\s|$)""")''',
        '''KEY_RE = re.compile(r"""(?:"([^"]*)"|\'([^\']*)\'|([^\\s:#\'"-][^\\s:]*)):(?:\\s|$)""")'''),
    # #931 の 2 パス目（VB）
    "空行とコメントだけの行も飛ばさない": ("        if not code.strip():\n            continue\n        indent", "        if not code:\n            continue\n        indent"),
    "コメントを切らずに読む": ("        code, _ = split_comment(raw)\n        if not code.strip():", "        code = raw\n        if not code.strip():"),
    "`run:` の行に限らず名前を拾う": (
        '        names = set(NAME_RE.findall(code)) if "run:" in code else set()',
        '        names = set(NAME_RE.findall(code))'),
    "`jobs` を部分一致で読む": ('            in_jobs = head == "jobs"', '            in_jobs = "jobs" in code'),
    "鍵の段でない行も鍵と読む": (
        "                    key = head if (head is not None and indent == key_indent) else None",
        "                    key = head"),
    "鍵でない行も鍵に数える": (
        "                    if key is not None:\n                        keys[job].append(key)",
        "                    if True:\n                        keys[job].append(key)"),
    "ジョブの識別子に連番を付けない": (
        '                job = f"{len(keys)}:{head if', '                job = f"{head if'),
    "ジョブごとに鍵の段を戻さない": (
        "                keys[job] = []\n                key_indent = None\n", "                keys[job] = []\n"),
    # #944: コンパクトな列
    "コンパクトな列を `steps:` の外と読む（#944 の前に戻す）": (
        '                if indent == key_indent and SEQ_RE.match(code.lstrip(" ")):',
        '                if False:'),
    "コンパクトな列を `steps` と決め打ちする": (
        "                    pass  # コンパクトな列——前の鍵の値の続き（#944）",
        '                    key = "steps"  # コンパクトな列——前の鍵の値の続き（#944）'),
    "コンパクトな列を字下げに依らず続きと読む": (
        '                if indent == key_indent and SEQ_RE.match(code.lstrip(" ")):',
        '                if indent <= key_indent and SEQ_RE.match(code.lstrip(" ")):'),
    "コンパクトな列を鍵の一覧に足す": (
        "                    pass  # コンパクトな列——前の鍵の値の続き（#944）",
        "                    keys[job].append(key)  # コンパクトな列——前の鍵の値の続き（#944）"),
    "`-` だけの行を列の項と読まない": ('SEQ_RE = re.compile(r"-(?:\\s|$)")', 'SEQ_RE = re.compile(r"-\\s")'),
    "`-x` も列の項と読む": ('SEQ_RE = re.compile(r"-(?:\\s|$)")', 'SEQ_RE = re.compile(r"-")'),
    # #945: ジョブの位置と引数を同じ行で突き合わせる（`full_ungated_runs`）
    "名前ごとの集合の積で決める（#945 の前の 2 つの検査に戻す）": (
        "    return {n for i, names, reasons in gate_records(ci) if not reasons for n in names & full.get(i, set())}",
        "    return full_runs(ci) & gated_runs(ci)[0]"),
    "条件つきの位置の行も数える": (" if not reasons for n in names & full", " for n in names & full"),
    "狭めた行も数える": ("for n in names & full.get(i, set())}", "for n in names}"),
    # #946: ワークフローの `on:`（`trigger_reasons`・`untriggered_runs`）
    "`pull_request` を要らない側にする": ('TRIGGER_EVENTS = ("pull_request", "push")', 'TRIGGER_EVENTS = ("push",)'),
    "`push` を要らない側にする": ('TRIGGER_EVENTS = ("pull_request", "push")', 'TRIGGER_EVENTS = ("pull_request",)'),
    "`branches:` 以外の鍵で狭めても見ない": (
        '                out.add(f"`{ev}` の `{key}:` で狭めている")', '                pass'),
    "`branches:` の `main` を見ない": ('    if has_branches and "main" not in branches:', '    if False:'),
    "`main` を部分一致で見る": (
        '    if has_branches and "main" not in branches:',
        '    if has_branches and not any("main" in b for b in branches):'),
    "引用符を外さない": ("        return t[1:-1]\n    return t", "        return t\n    return t"),
    "コンパクトな列を `branches:` の項と読まない": (
        '        elif ind == level and not (key == "branches" and item and not inline):', '        elif ind == level:'),
    "深い `- ` を `branches:` の項と読まない": (
        "                item_level = ind\n                branches.append(scalar(name))",
        "                item_level = ind"),
    "`branches:` の下の読めない行を飛ばす（#946 の 2 パス目）": (
        '                out.add(f"`{ev}` の `branches:` の下の行を読めない（`{c}`）")', '                pass'),
    "値のある `branches:` の下の行も項と読む": (
        "            if (inline or not item or (item_level", "            if (not item or (item_level"),
    "項の字下げの揃いを見ない": (" or (item_level is not None and ind != item_level)", ""),
    "マッピング・列の項も `branches:` の項と読む": (
        ' or name[:1] in "[{" or ": " in name or name.endswith(":")):', "):"),
    "`branches:` のフロー列を読まない": ("                branches += seq_items(inline)", "                pass"),
    "イベントの下の読めない行を飛ばす": (
        '                out.add(f"`{ev}` の下の行を読めない（`{c}`）")', '                pass'),
    "字下げ 0 でない `on:` も読む": ('if ind == 0 and key_of(c) == "on"]', 'if key_of(c) == "on"]'),
    "`on:` の子を字下げ 0 の行で切らない": (
        "        if ind == 0:\n            break\n        body.append", "        if False:\n            break\n        body.append"),
    "コメントを切らずに `on:` を読む": (
        "        code, _ = split_comment(raw)\n        if code.strip():\n            if \"\\t\"",
        "        code = raw\n        if code.strip():\n            if \"\\t\""),
    "フロー列を読まない": ('    if value.startswith("[") and value.endswith("]"):', '    if False:'),
    "フロー形式のマッピングを読んだことにする": (
        '        return reasons | {"`on:` の値を読めない（フロー形式のマッピング）"}', '        pass'),
    "イベントの値を何でも狭めていないと読む": ("        if val not in OPEN_VALUES:", "        if False:"),
    "イベントの値に `{}`・`null` を許さない": ('OPEN_VALUES = ("", "null", "~", "{}")', 'OPEN_VALUES = ("",)'),
    "読めない `on:` の行を飛ばす": ('                    reasons.add(f"`on:` の行を読めない（`{c}`）")', '                    pass'),
    "`on:` の子より浅い行を飛ばす": ('            reasons.add("`on:` の字下げを読めない")', '            pass'),
    "起動するかを見ずに全部を繋ぐ": (
        '    live_ci = "\\n".join(t for t in files if not trigger_reasons(t))', '    live_ci = "\\n".join(files)'),
    "全部を回す行の側を見ない": ("            full_ungated_runs(ci) - full_ungated_runs(live_ci))", "            set())"),
    # #946 の 1 パス目
    "タブの字下げを見ない": ('                reasons.add("タブで字下げした行がある")', '                pass'),
    "`!` の除外を見ない": ('    if any(b.startswith("!") for b in branches):', '    if False:'),
    "イベントの下の重なる鍵を見ない": ('            if key in seen:', '            if False:'),
    "重なるイベントを見ない": ('                    if cur in events:', '                    if False:'),
    "2 つ目の `on:` を見ない": ('    if len(starts) > 1:', '    if False:'),
    "値と子が両方でも見ない": ('    if value and body:', '    if False:'),
    "列とマッピングが混ざっても見ない": ('    if len(kinds) > 1:', '    if False:'),
    "列の項の下の行を飛ばす": (
        '            reasons.add(f"`on:` の列の項の下の行を読めない（`{c}`）")', '            pass'),
    "イベントの下の浅い行を飛ばす": ('        if level is not None and ind < level:', '        if False:'),
    "フロー列の読めない項を見ない": ('        if name[:1] in "{[":', '        if False:'),
    "`test-` を剥がして照合する（覆い隠しが戻る）": (
        r'NAME_RE = re.compile(r"scripts/([A-Za-z0-9_.-]+\.py)")',
        r'NAME_RE = re.compile(r"scripts/(?:test-)?([A-Za-z0-9_.-]+\.py)")'),
}


PARTS = ("registry", "contract", "scan", "mutants")


def parse_args(argv: list[str]) -> tuple[set[str], set[str] | None]:
    """**狭く回す口**（#494）。`mutation-claim:` の `red` が、主張に関係する部分だけを回すために使う。

        python3 scripts/test-check-all.py                      # 全部（check-all.py と CI はこれ）
        python3 scripts/test-check-all.py --part registry      # 収録漏れと CI の走査だけ
        python3 scripts/test-check-all.py --part scan          # CI の yaml の判別（合成試料と SCAN_MUTANTS）だけ
        python3 scripts/test-check-all.py --part contract      # 本体そのままの契約（base ありの契約を含む）だけ
        python3 scripts/test-check-all.py --part mutants       # 本体そのままの契約と、`MUTANTS` の全部
        python3 scripts/test-check-all.py --mutant <名前>      # 本体そのままの契約と、`MUTANTS` のその 1 件を契約が捕まえるか
                                                               # （--mutant は重ねて渡せる。渡した全部を当てる）

    **変異を当てる回（`--part mutants`・`--mutant`）は、いつも本体そのままの契約も回して、通ることを要求する**（陽性対照）——回さないと、負荷で待ち合わせが
    時間切れになったとき「契約が破れた＝捕まえた」と数え、主張の変異を当てた後も緑になる（#494 の 1 パス目の `/code-review`）。

    **狭めた回は、全部を回す回の代わりにならない**——`check-all.py` と CI は引数なしで全部を回す
    （CI のステップに引数を付けていないことは `test_ci_runs_every_registered_script` が見る。#687）。
    **知らない部分・知らない変異の名前は断る**（綴り間違いで「何も回さずに緑」にしない）——`argparse` の `choices` で断り、
    終了コードは 2（#687。手書きの読み取りだった頃は 1）。
    """
    parser = argparse.ArgumentParser(allow_abbrev=False, add_help=False, prog="test-check-all.py", description="check-all.py の回帰テスト（引数なしで全部）")
    parser.add_argument("--part", action="append", choices=PARTS, default=[],
                        help="回す部分（重ねて渡せる）")
    parser.add_argument("--mutant", action="append", choices=list(MUTANTS), default=[],
                        help="当てる MUTANTS の名前（重ねて渡せる。本体そのままの契約も回す）")
    opts = parser.parse_args(argv)
    parts, mutants = set(opts.part), set(opts.mutant)
    if mutants and "mutants" in parts:
        parser.error("--part mutants（全部）と --mutant（一部）は一緒に渡せない")
    if mutants:
        return parts | {"mutants"}, mutants
    return (parts or set(PARTS)), None


def main(argv: list[str] | None = None) -> int:
    parts, only_mutant = parse_args(sys.argv[1:] if argv is None else argv)
    if "registry" in parts:
        print("収録漏れ（実リポジトリを読むだけ）:")
        test_registry_covers_every_script()
        test_ci_runs_every_registered_script()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # **変異を当てる回は、いつも本体そのままの契約も回す**（陽性対照。`--part mutants` でも `--mutant` でも）。
        if parts & {"contract", "mutants"}:
            print("契約（本体そのまま——全部通らなければならない）:")
            target = build_fake(root / "real")
            for name, ok in contract(target, root / "real", "real"):
                check(name, ok)
        if "contract" in parts:
            run_contract_with_base(root)
        if "scan" in parts:
            run_scan(root)
        if "mutants" in parts:
            run_mutants(root, only_mutant)

    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


def run_contract_with_base(root: Path) -> None:
    repo = root / "withbase"
    target = build_fake(repo)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "--allow-empty", "-m", "init"], check=True)
    for name, ok in contract_with_base(target, repo, "wb"):
        check(name, ok)


def run_scan(root: Path) -> None:
    print("判別（合成試料——全部通らなければならない）:")
    for name, ok in scan_contract(scan_ci_runs, full_runs, gated_runs, full_ungated_runs,
                                  trigger_reasons, untriggered_runs):
        check(name, ok)

    print("判別の変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
    # **切れていなければ、当て先は必ず 2 箇所になって全件落ちる。**
    # **6 件の「当て先が 1 箇所」より、切れていないことを 1 行で言うほうが速い。**
    check("当て先を数える範囲が、辞書の手前で切れている", CODE_ONLY != SELF_SRC)
    for i, (name, (old, new)) in enumerate(SCAN_MUTANTS.items()):
        if CODE_ONLY.count(old) != 1:
            check(f"変異 `{name}` の当て先が 1 箇所", False)
            continue
        d = root / f"scan{i}"
        assert_not_real_repo(d)
        d.mkdir()
        p = d / "scanned.py"
        # **辞書より前に 1 箇所しか無いことを上で確かめてある**ので、
        # **最初の 1 件だけ置き換えれば、当たるのは判別の本体である。**
        p.write_text(SELF_SRC.replace(old, new, 1))
        scanned = load(p, f"scanned{i}")
        try:
            broken = [n for n, ok in scan_contract(scanned.scan_ci_runs, scanned.full_runs,
                                                   scanned.gated_runs, scanned.full_ungated_runs,
                                                   scanned.trigger_reasons, scanned.untriggered_runs)
                      if not ok]
        except Exception as e:  # 壊した判別が落ちた——契約は破れている（緑ではない）
            broken = [f"例外: {e!r}"]
        check(f"変異 `{name}` を契約が捕まえる", bool(broken))
        if not broken:
            print("       壊したのに契約が全部通った")


def run_mutants(root: Path, only: set[str] | None) -> None:
    print("変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
    src = TARGET.read_text()
    for i, (name, (old, new)) in enumerate(MUTANTS.items()):
        if only is not None and name not in only:
            continue
        if src.count(old) != 1:
            check(f"変異 `{name}` の当て先が 1 箇所", False)
            continue
        d = root / f"mut{i}"
        t = build_fake(d)
        t.write_text(src.replace(old, new))
        broken = [n for n, ok in contract(t, d, f"m{i}") if not ok]
        check(f"変異 `{name}` を契約が捕まえる", bool(broken))
        if not broken:
            print("       壊したのに契約が全部通った")


if __name__ == "__main__":
    sys.exit(main())
