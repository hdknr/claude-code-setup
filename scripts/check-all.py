#!/usr/bin/env python3
"""歯止めと回帰テストを**全部**回す。1 本ずつ選ばせないための入口。

    python3 scripts/check-all.py                    # base は origin/main を既定で使う
    python3 scripts/check-all.py --base origin/main # 明示する
    python3 scripts/check-all.py --guards-only      # 回帰テストを飛ばす
    python3 scripts/check-all.py --jobs 1           # 直列に回す（既定は CPU の数だけ並列）

なぜ必要か（#117 の 1）: #110 の周で、**直前の編集のあと 7 本のうち 2 本しか回さずに
コミットし、CI を割った**。**落ちたのは回さなかったほう**で、しかも計画ファイルの
2 行上には「`check-norm-markers` OK」という**自己申告**が残っていて、申告と実測が
食い違っていた。

**原因は「この編集はあの検査に関係ない」という判断である**——**関係の有無を判断する側が
間違える。** だから**まとめて、判断の余地を無くす。**

**CI からは呼ばない。** CI（`.github/workflows/plugins.yml` / `docs.yml`）は各スクリプトを
**個別のステップ**として呼ぶ——そのほうが**どれが落ちたかが GitHub の UI に出る**。
このスクリプトは**手元でコミットする前に回すためのもの**である。

判定:

- **1 本でも落ちたら非ゼロ終了。**
- **落ちても残りを回す**（最初の 1 本で止めない）。**全体像が出ないと、
  「1 本直してはまた回す」を繰り返すことになる。**
- **飛ばしたものは、黙って飛ばさず SKIP として数えて出す。**

**並列に回す**（#430）。直列では 1 回に 842 秒かかっていた（2026-10-26、10 コアの macOS）。
**スクリプトを分けて別々に回す形にはしない**——入口が複数になると、また選ぶ余地ができる。

- **既定は CPU の数だけ並列**（`--jobs`）。**`--jobs 1` で直列**になる。
- **起動は宣言順。** いちばん重い `check-mutation-claims.py` を `GUARDS` の先頭に置いてある
  ——並列のとき、律速になる 1 本が最後に起動されないように。
- **入れ子は親の半分**（#460）。`check-mutation-claims.py` は自分も `--jobs`（既定は CPU の数）で並列に当てるので、
  ここからは `--jobs` を親の半分（少なくとも 1）にして起こす——`--jobs 1` なら入れ子まで直列になる。
  2026-10-27、10 コアの macOS で、他の `check-all.py` が重ならない回の wall と、入れ子の中で最も長かった `red`:
  既定のまま（10）は 217〜262 秒・90〜99 秒、半分（5）は 237・252 秒・77〜79 秒、`1` は 368〜388 秒・約 64 秒。
  **`1` は打ち切りまでの余裕が最も大きいが wall が 6 割延びる**ので、半分にした。
  **別のセッションの `check-all.py` と重なったときの取り合いは、ここでは絞れない**。打ち切りの原因は特定していない
  ——#449 の打ち切りは重なりを記録していない日の値で、#460 で届いた 1 回は別のセッションが `check-all.py` を走らせていた
  時間帯だが、重なっていたかは記録していない。
  **回帰テストのうち変異を別々のプロセスで同時に当てるもの**（`test-check-unattended-env.py`・`test-ledger.py`。#494）にも
  同じ値を `--jobs` で渡す（#748・#749）——テストの側は自分の上限（4）で切る。
  **「入れ子まで直列」が効くのは `--jobs` を渡すこの 3 本（`NESTED`）だけである。** 並列の振る舞いそのものを試すテスト
  （`test-check-mutation-claims.py`・`test-check-all.py`）は、`--jobs` を受けず、中で本体を並列に回す（`--jobs 2` の直書きや
  `check-mutation-claims.py` の既定の `--jobs`）——親が `--jobs 1` でも、その中は直列にならない。
- **出力は宣言順**（終わった順ではない）。先頭が最も重いので、最初の行が出るまで待つ。
- **Ctrl-C で、まだ起動していないものは起動せず、走っているものは止める**
  （親だけに SIGINT が届いた場合も——子を止めるのは親である）。**孫まで止める**——
  子は自分のプロセスグループで起こし、止めるときはグループに SIGINT を送って
  後始末の猶予を与え、残ったら SIGKILL する。**POSIX 専用**（`os.killpg`）。

**この検査が守らないもの**——**何を守らないかを書いておかないと、緑であることが
安心の根拠に化ける**:

| 守らないもの | なぜ |
| --- | --- |
| **`git push` したかどうか** | 手元で緑にしても**PR は赤のまま**でありうる（#117 の 2）。**PR 側は `gh pr checks` で見る**。このスクリプトはネットワークに出ない |
| **CI が回すもののうち、ここに無いもの** | 収録は下の `GUARDS` / `TESTS` が正。**`scripts/` に検査を足してここへ登録し忘れると落ちる**（`test-check-all.py` がそれを見る）が、**CI のワークフローに直接書かれたステップ**（`mkdocs build` など）は**見ていない** |
| **検査そのものの正しさ** | 各検査の回帰テストが見る。**このスクリプトは「全部回したか」だけを見る** |
| **出力を落としたファイルが、この 1 回の出力だけであること** | **FAIL の行と集計は同じ分岐で決まる**（`main` の `if not ok` で、表示と `failed` への積み上げが一緒に動く。打ち切られた子——シグナルで止まり終了コードが負——も失敗に数える。`test-check-all.py` の契約 10）。だが**2 つの実行が同じファイルへ `>` で落とすと、互いの行が上書きで混ざる**——#509 の「FAIL の行があるのに『失敗 0』・失敗の中身が無い」は、**片方が FAIL の行を書いたあと残りを書く前に止められ、もう片方と同じファイルに落としている**形で 5 回中 5 回再現した（同じく止めて別々のファイルに落とした対照では 10 本中 0 本、止めずに同じファイルに落とした形では 5 回中 0 回）。**#509 の当時に何が起きたかは確かめていない**——言えるのは、この形で症状が出ることまで。**出力は実行ごとに別のファイル（`mktemp` など）に落とす。** 共有の scratchpad の決まった名前（`checkall.txt`）を使わない |
| **並列に回して安全であること** | **各スクリプトが一時ディレクトリで作業する（実リポジトリと固定のパスに書かない）ことを前提にしている。** #430 の時点の 49 本は、並列で回して全部通り、作業ツリーに変化が無かった（確かめたのはそこまで）が、**後から足した 1 本が実リポジトリに書けば、並列のときだけ壊れうる**。疑わしいときは `--jobs 1` で回して比べる |

標準ライブラリのみ。
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

# 歯止め。(スクリプト名, 追加引数, base-ref を要するか)
GUARDS: list[tuple[str, list[str], bool]] = [
    # **他の歯止めを子プロセスで回すので、1 本だけ重い**（直列で 166 秒。#430 の時点）。
    # **起動は宣言順なので先頭に置く**——後ろに置くと、並列のとき律速の 1 本が遅れて起動される。
    # **中の並列数は `NESTED` が決める**（#460）。
    ("check-mutation-claims.py", [], False),
    ("check-plugin-versions.py", [], False),
    ("check-norm-markers.py", [], False),
    ("check-duplicate-counts.py", [], False),
    ("check-bold-flanking.py", [], False),
    ("check-skill-pointers.py", [], False),
    ("check-plan-counts.py", [], False),
    ("check-site-links.py", [], False),
    ("check-diagram-freshness.py", [], False),
    ("skill-metrics.py", ["--check"], False),
    ("check-version-bump.py", [], True),
    ("check-description-sync.py", [], True),
    ("check-plan-scope.py", [], True),
]

# 中で自分も `--jobs` で並列に回すもの（#460。回帰テストの 2 本は #748・#749）。親の並列数から決めた `--jobs` を渡す——
# 渡さないと入れ子の既定（CPU の数・テストは 4）で起き、親の作業者と同じ CPU を取り合い、`--jobs 1` でも直列にならない。
NESTED = ("check-mutation-claims.py", "test-check-unattended-env.py", "test-ledger.py")


def nested_jobs(jobs: int) -> int:
    """入れ子に渡す `--jobs`。親の半分で、少なくとも 1（親が 1 なら入れ子も直列）。"""
    return max(1, jobs // 2)


# 回帰テスト（歯止め自体が何も見ていない状態に退化していないかを見る）
TESTS: list[str] = [
    "test-check-plugin-versions.py",
    "test-check-norm-markers.py",
    "test-check-site-links.py",
    "test-check-diagram-freshness.py",
    "test-check-description-sync.py",
    "test-check-version-bump.py",
    "test-skill-metrics.py",
    "test-export-diagrams.py",
    "test-token-metrics.py",
    "test-link-skills.py",
    "test-check-all.py",
    "test-check-plan-scope.py",
    "test-collect-guard-rejections.py",
    "test-count-resume-recreations.py",
    "test-count-usage-limit-resumes.py",
    "test-record-stop-failure.py",
    "test-find-cycle.py",
    "test-check-unattended-env.py",
    "test-launch-with-long-token.py",
    "test-ledger.py",
    "test-parent-issue.py",
    "test-child-cycle.py",
    "test-run-serial.py",
    "test-check-duplicate-counts.py",
    "test-check-bold-flanking.py",
    "test-worktree-scripts.py",
    "test-check-skill-pointers.py",
    "test-check-mutation-claims.py",
    "test-run-dev-loop-evals.py",
    "test-check-qa-csv.py",
    "test-qa-to-pptx.py",
    "test-check-spec-exit.py",
    "test-check-feasibility-csv.py",
    "test-schedule-to-gantt.py",
    "test-check-signoff.py",
    "test-build-proposal.py",
    "test-scaffold.py",
    "test-merge-versions.py",
    "test-diff-versions.py",
    "test-check-frozen.py",
    "test-init-mkdocs.py",
    "test-tab-match.py",
    "test-check-plan-counts.py",
    "test-merge-pr.py",
]


# **走っている子。** 中断したときに親が自分で止める——ワーカーのスレッドは
# KeyboardInterrupt を受けないので、`subprocess.run` の「例外で子を kill する」が働かない。
# **子は 1 本ずつ自分のプロセスグループで起こし、止めるときはグループごと止める**——
# 子だけを kill すると、子が起こした孫（`check-mutation-claims.py` の配下）が孤児として残る（#430 の 2 パス目）。
# 端末の Ctrl-C は親のグループにしか届かなくなるので、子への SIGINT は親が送る。
_live: set[subprocess.Popen] = set()
_live_lock = threading.Lock()
_stopping = False
# 子が自分の後始末（一時ディレクトリの削除など）を済ませるのを待つ秒数。過ぎたら SIGKILL。
GRACE = 3.0


def run(name: str, args: list[str]) -> tuple[bool, str]:
    """スクリプトを回して (通ったか, 出力) を返す。出力は落ちたときだけ見せる。"""
    with _live_lock:
        # **止めると決めたあとに起動しない**——kill の一覧を取ったあとに生まれた子は止められない。
        if _stopping:
            return False, "中断したので回していない"
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPTS / name), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=SCRIPTS.parent,
            process_group=0,
        )
        _live.add(proc)
    try:
        out, err = proc.communicate()
    finally:
        with _live_lock:
            _live.discard(proc)
    return proc.returncode == 0, (out + err)


def signal_group(proc: subprocess.Popen, sig: int) -> None:
    try:
        os.killpg(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        pass  # グループにもう誰もいない


def stop_all() -> None:
    """これ以上起動せず、走っている子のグループに SIGINT を送り、
    `GRACE` 秒待ってから残ったグループを SIGKILL する。刈り取りは各ワーカーの `communicate()` が行う。"""
    global _stopping
    with _live_lock:
        _stopping = True
        procs = list(_live)
    for proc in procs:
        signal_group(proc, signal.SIGINT)
    deadline = time.monotonic() + GRACE
    while time.monotonic() < deadline and any(p.poll() is None for p in procs):
        time.sleep(0.05)
    # **子が終わっていても送る**——子が先に終わり、孫だけがグループに残っていることがある。
    for proc in procs:
        signal_group(proc, signal.SIGKILL)


def base_resolves(ref: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
        check=False,
        cwd=SCRIPTS.parent,
    )
    return proc.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="歯止めと回帰テストを全部回す")
    parser.add_argument(
        "--base",
        default="origin/main",
        help="PR 限定の検査に渡す base ref（既定: origin/main）",
    )
    parser.add_argument(
        "--guards-only",
        action="store_true",
        help="回帰テストを飛ばす（飛ばしたことは出力に出る）",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=os.cpu_count() or 1,
        help="同時に回す本数（既定: CPU の数。1 で直列）",
    )
    opts = parser.parse_args()
    if opts.jobs < 1:
        parser.error(f"--jobs は 1 以上: {opts.jobs}")

    have_base = base_resolves(opts.base)

    failed: list[str] = []
    skipped: list[str] = []
    logs: list[tuple[str, str]] = []

    pool = ThreadPoolExecutor(max_workers=opts.jobs)
    try:
        # **全部を先に投げてから、宣言順に結果を待つ。** 出力は終わった順ではなく宣言順。
        guard_runs = []
        for name, extra, needs_base in GUARDS:
            label = name if not extra else f"{name} {' '.join(extra)}"
            if needs_base and not have_base:
                guard_runs.append((label, None))
                continue
            args = [*extra, opts.base] if needs_base else extra
            if name in NESTED:
                args = [*args, "--jobs", str(nested_jobs(opts.jobs))]
            guard_runs.append((label, pool.submit(run, name, args)))
        test_runs = ([] if opts.guards_only
                     else [(name, pool.submit(run, name, ["--jobs", str(nested_jobs(opts.jobs))] if name in NESTED else []))
                           for name in TESTS])

        print(f"=== 歯止め === （{opts.jobs} 並列）")
        for label, fut in guard_runs:
            if fut is None:
                print(f"  SKIP {label:<40} base `{opts.base}` が解決できない")
                skipped.append(label)
                continue
            ok, out = fut.result()
            print(f"  {'OK  ' if ok else 'FAIL'} {label}", flush=True)
            if not ok:
                failed.append(label)
                logs.append((label, out))

        if opts.guards_only:
            print("=== 回帰テスト === SKIP（--guards-only）")
            skipped.extend(TESTS)
        else:
            print("=== 回帰テスト ===")
            for name, fut in test_runs:
                ok, out = fut.result()
                print(f"  {'OK  ' if ok else 'FAIL'} {name}", flush=True)
                if not ok:
                    failed.append(name)
                    logs.append((name, out))
    except KeyboardInterrupt:
        # **まだ起動していないものを起動せず、走っている子を止める。**
        pool.shutdown(wait=False, cancel_futures=True)
        stop_all()
        raise
    pool.shutdown()

    for label, out in logs:
        print(f"\n----- {label} の出力 -----")
        print(out.rstrip())

    total = len(GUARDS) + len(TESTS)
    ran = total - len(skipped)
    print(f"\n{ran}/{total} 本を回した（失敗 {len(failed)} / 飛ばし {len(skipped)}）")
    if skipped:
        print("飛ばしたもの: " + ", ".join(skipped))
        print("**飛ばしたものは回していない。** 手元の緑をそのまま「全部緑」と報告しない。")
    if failed:
        print("落ちたもの: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
