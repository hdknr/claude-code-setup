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
  ここからは `--jobs` を親の半分（少なくとも 1）にして起こす——`--jobs 1` なら入れ子にも `--jobs 1` を渡す。
  2026-10-27、10 コアの macOS で、他の `check-all.py` が重ならない回の wall と、入れ子の中で最も長かった `red`:
  既定のまま（10）は 217〜262 秒・90〜99 秒、半分（5）は 237・252 秒・77〜79 秒、`1` は 368〜388 秒・約 64 秒。
  **`1` は打ち切りまでの余裕が最も大きいが wall が 6 割延びる**ので、半分にした。
  **別のセッションの `check-all.py` と重なったときの取り合いは、ここでは絞れない**。打ち切りの原因は特定していない
  ——#449 の打ち切りは重なりを記録していない日の値で、#460 で届いた 1 回は別のセッションが `check-all.py` を走らせていた
  時間帯だが、重なっていたかは記録していない。
  **回帰テストのうち変異を別々のプロセスで同時に当てるもの**（`test-check-unattended-env.py`・`test-ledger.py`。#494。
  `test-check-deps-declared.py`。#1021。`test-check-spec-writeback.py`。#1049。`test-run-serial.py`。#1051。`test-parallel-stop.py`。#1050。`test-outer-loop.py`。#1052）にも同じ値を `--jobs` で渡す（#748・#749）——テストの側は自分の上限（4）で切る。
  **`--jobs 1` は「子孫まで直列」ではない**（#749 の 2 パス目）。絞れるのは `check-all.py` の作業者と、`--jobs` を渡す
  `NESTED` の 8 本が**自分で**起こす並列（`check-mutation-claims.py` の主張の作業者・7 本のテストの変異の作業者）だけである。
  その先——`check-mutation-claims.py` が当てる主張の red のコマンドが起こすテスト——と、並列の振る舞いそのものを試すテスト
  （`test-check-all.py`・`test-check-mutation-claims.py`・`test-run-serial.py` の観測・`test-parallel-stop.py` の 1 パスの中のブロックなど。`--jobs 2` の直書き・既定の `--jobs`・
  同時に起こす子プロセス）の中は、`--jobs 1` でも並列に回る。
- **出力は宣言順**（終わった順ではない）。先頭が最も重いので、最初の行が出るまで待つ。
- **1 本ごとの所要時間を `OK` / `FAIL` の行の末尾に出す**（#1040）。集計には、所要時間の長い順の上位
  （`TOP` 本。`OK` と `FAIL` の両方から）と、全体の壁時計の秒を出す。**速くする手を当てる先を数字で決めるため**——
  並列なので全体の時間は最も遅い数本でほぼ決まる。時間の取り方:
    - **1 本の時間は、作業者のスレッドが `run` を呼ぶ直前から、子が終わって出力を読み終えるまでの壁時計**
      （`time.monotonic()`）。**プールの順番待ちは含まない**——`--jobs 1` でも、後ろの 1 本は前の 1 本の時間を背負わない。
      **起動の排他（`_live_lock`）の待ちは含む**——子の起動（`Popen`）はこの排他の中で行うので、
      並列のときは他の作業者が子を起こし終えるのを待つ時間が入る（起動の重さの一部として数える）。
      **CPU 時間ではない**——並列のときは、同時に走っている他の子との取り合いと、子プロセスの起動の重さを含む。
      上位を比べるなら同じ `--jobs` の回どうしで比べ、**他の重い処理（別の `check-all.py` など）と重ねて測らない**。
    - **`SKIP` の行には時間を出さない**（回していない）。上位にも入れない。
    - **全体は、引数を読んだ後から集計を出す直前までの壁時計**（base の解決を含む）。
    - **時間を出しても判定は変えない**——終了コード・「失敗 N」・`FAIL` の行の数・`SKIP` の数え方は時間に依らない。
      上位の行は `  OK  ` / `  FAIL` / `  SKIP` で始めない（行を数える側に混ざらないように）。
- **Ctrl-C で、まだ起動していないものは起動せず、走っているものは止める**
  （親だけに SIGINT が届いた場合も——子を止めるのは親である）。**孫まで止める**——
  子は自分のプロセスグループで起こし、止めるときはグループに SIGINT を送って
  後始末の猶予を与え、残ったら SIGKILL する。**POSIX 専用**（`os.killpg`）。

**入力が変わっていない回帰テストは回さない**（#1151。キャッシュ）。1 回に 15 分前後かかり、そのとき CPU は空きが 0 で、
時間を決めていたのは最も遅い 1 本ではなく CPU の総量だった（#1151 の本文の計測）——並列の詰め方では縮まないので、回す量を減らす。

- **飛ばすかは機械が決める**——「この編集はあの検査に関係ない」を人が判断しない（#117）のは変わらない。
  回帰テストを回すときに、**そのテストと、環境を引き継いだ子の Python に audit hook を差し込み**（`check_all_trace/usercustomize.py`。
  `PYTHONPATH` の先頭に置く）、**緑だった回に読んだもの**を記録する。次の回は、記録した入力の指紋が全部同じなら `CACHED` として回さない。
- **入力に数えるもの**:
    - **開いたファイルの中身**（無かったことも——無いファイルが現れれば回る）。**import が `__pycache__` の `.pyc` だけを開いた
      モジュールは、元の `.py` を読んだと数える**（`.pyc` が新しければ `.py` は開かれない）。
    - **列挙したディレクトリの名前の一覧**（`os.listdir`・`os.scandir`。中のファイルの中身ではない）。**import の仕組み（`FileFinder`）が
      `sys.path` を列挙するのは数えない**——数えると `scripts/` にファイルを足すたびに全部が回る。
    - **hook の入らない子**——`-I`・`-E`・`-s`・`-S` で起こした Python（`-W`・`-X` の値は飛ばして読む）・環境を組み直して起こした子
      （**書く先の変数が残っていても、`PYTHONPATH` から hook のディレクトリが外れたか `PYTHONNOUSERSITE` を付けたなら入らないと見る**）・
      Python でない子（`sh`・`node` など）。その子が読むものは見えないので、**引数に現れた作業ツリーの中のパスを粗い単位にする**
      ——`plugins/<名前>/` の下ならそのプラグインの全体、`scripts/` の下なら `scripts/` の全体、ほかはそのパス。
      引数は子の cwd（相対の cwd も、起こした側の cwd で絶対にする）で解決する。**空白を含む引数**（`sh -c "<コマンド>"`・`shell=True`・
      `os.system`）は語に割って同じように見て、語に `git` があれば git の状態も入力にする。
    - **作業ツリーに当てた git**（`-C`・`--git-dir`・cwd で決まる先が作業ツリーの中か、引数が作業ツリーの中を指す）——**git の状態**
      （HEAD のコミットと、`git status` に出たパスとその中身）を入力にする。**どのファイルを変えても回る。**
      例外は配置だけを訊く `git rev-parse`（`--show-toplevel` など。`GIT_LAYOUT_ARGS`）と、リポジトリを読まないサブコマンド（`GIT_READ_FREE`）。
    - **キー**——Python の版と実行ファイル・OS・記録の形式（`CACHE_FORMAT`）・テストの名前と引数（`--jobs` は除く）・
      **`check-all.py` と hook の中身**（集め方と比べ方を直したら、古い記録を当たりにしない）。
- **入力に数えないもの**: `.git/` の下（git の中身は git コマンドの側で見る）・`__pycache__`・`.pyc`・`.DS_Store`・
  作業ツリーの外（一時ディレクトリなど）。
- **記録するのは緑だけ。** 落ちた回は記録を消す（入力が同じでも次は回る）。中断した回は書きも消しもしない。
  **テスト自身（`scripts/<名前>`）を読んだ跡が無い回は記録しない**——hook が入らなかった（`usercustomize` を読まない Python など）。
  空の依存を記録すると、何を変えても当たりになる。
  **回している間に入力が書き換わった回は記録しない**（`check-all.py` を始めた時刻より新しい mtime・git の状態の変化）。
  **依存のファイルが無いときは、在る最も近い祖先のディレクトリの mtime で見る**（回している間に消えた——親ごとでも）。
  **列挙したディレクトリの中のサブディレクトリはその mtime で見る**（回している間に作られた）。それ以外でディレクトリそのものの mtime は見ない
  ——Python が `__pycache__` を書くだけで動く。
- **歯止め（`GUARDS`）は載せない——毎回回す。** 実リポジトリの中身を広く読む（指し先・リンク・版）ので当たらず、
  重いのは `check-mutation-claims.py` だけである。
- **記録の置き場所**は `git rev-parse --git-common-dir` の下の `check-all-cache/`——**worktree の間で共有する**（中身で引くので安全）。
  一時ファイルに書いてから `os.replace` で置き、読めない記録は「無い」と扱う。**git のリポジトリでなければキャッシュを使わず、今までどおり全部回す。**
- **出力**: 当たったものは `  CACHED <名前>` の行（所要時間を出さず、上位にも入れない）。**`OK` に数えない**——集計の
  「N/M 本を回した」から外し、「キャッシュ: K 本」と別に出す。**`--no-cache` で記録を読まずに全部回す**（緑の記録は書く）。

**この検査が守らないもの**——**何を守らないかを書いておかないと、緑であることが
安心の根拠に化ける**:

| 守らないもの | なぜ |
| --- | --- |
| **`git push` したかどうか** | 手元で緑にしても**PR は赤のまま**でありうる（#117 の 2）。**PR 側は `gh pr checks` で見る**。このスクリプトはネットワークに出ない |
| **CI が回すもののうち、ここに無いもの** | 収録は下の `GUARDS` / `TESTS` が正。**`scripts/` に検査を足してここへ登録し忘れると落ちる**（`test-check-all.py` がそれを見る）が、**CI のワークフローに直接書かれたステップ**（`mkdocs build` など）は**見ていない** |
| **検査そのものの正しさ** | 各検査の回帰テストが見る。**このスクリプトは「全部回したか」だけを見る** |
| **出力を落としたファイルが、この 1 回の出力だけであること** | **FAIL の行と集計は同じ分岐で決まる**（`main` の `if not ok` で、表示と `failed` への積み上げが一緒に動く。打ち切られた子——シグナルで止まり終了コードが負——も失敗に数える。`test-check-all.py` の契約 10）。だが**2 つの実行が同じファイルへ `>` で落とすと、互いの行が上書きで混ざる**——#509 の「FAIL の行があるのに『失敗 0』・失敗の中身が無い」は、**片方が FAIL の行を書いたあと残りを書く前に止められ、もう片方と同じファイルに落としている**形で 5 回中 5 回再現した（同じく止めて別々のファイルに落とした対照では 10 本中 0 本、止めずに同じファイルに落とした形では 5 回中 0 回）。**#509 の当時に何が起きたかは確かめていない**——言えるのは、この形で症状が出ることまで。**出力は実行ごとに別のファイル（`mktemp` など）に落とす。** 共有の scratchpad の決まった名前（`checkall.txt`）を使わない |
| **キャッシュが入力を取りこぼさないこと**（#1151） | **集めるのは Python の audit イベントと子の引数だけである。** OS の読み取りを全部見る手段（`fs_usage`・DTrace）は root が要る。見えない形: **開かずに在るかだけを見る**（`os.stat`・`Path.exists`。イベントが無い）・**相対パスの `os.open`**（`dir_fd` 基準かどうかがイベントに載らないので、`os.chdir` の後に `dir_fd` 無しで開いたものも数えない）・**hook が入ると見えて入らない子**（`PYTHONPATH` と `PYTHONNOUSERSITE` は見るが、`usercustomize` を読まない Python——venv の Python など——は見分けない。テスト自身は上の「読んだ跡」で止める）・**hook の入らない子が、粗い単位の外を読む**（引数に無いプラグインの外のファイルなど）・**hook の入らない子の、さらに子**・**作業ツリーの外**（worktree から回したときのメインの作業ツリーなど）・**回している間に一覧から名前が消えた**（消えた名前には mtime が無い）。**ほかの `usercustomize` を隠す**（`PYTHONPATH` の先頭に置くので）。**テストが作業ツリーの外の状態に依る**（時刻・ネットワーク・`git`・`node` の版・`~/.claude`）——外が変わっても回さない。**取りこぼしの砦は PR 側の CI である**——CI は `check-all.py` を通さず全部回す。疑わしいときは `--no-cache` で回す |
| **並列に回して安全であること** | **各スクリプトが一時ディレクトリで作業する（実リポジトリと固定のパスに書かない）ことを前提にしている。** #430 の時点の 49 本は、並列で回して全部通り、作業ツリーに変化が無かった（確かめたのはそこまで）が、**後から足した 1 本が実リポジトリに書けば、並列のときだけ壊れうる**。疑わしいときは `--jobs 1` で回して比べる |

標準ライブラリのみ。
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
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
    ("check-prompt-lines.py", [], True),
]

# 中で自分も `--jobs` で並列に回すもの（#460。回帰テストの 7 本は #748・#749・#1021・#1049・#1051・#1050・#1052）。親の並列数から決めた `--jobs` を渡す——
# 渡さないと入れ子の既定（CPU の数・テストは 4）で起き、親の作業者と同じ CPU を取り合い、`--jobs 1` でも直列にならない。
NESTED = ("check-mutation-claims.py", "test-check-unattended-env.py", "test-ledger.py", "test-check-deps-declared.py",
          "test-check-spec-writeback.py", "test-run-serial.py", "test-parallel-stop.py", "test-outer-loop.py")


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
    "test-check-deps-declared.py",
    "test-check-spec-writeback.py",
    "test-formal-sync.py",
    "test-artifact-reads.py",
    "test-line-effects.py",
    "test-external-reviews.py",
    "test-commit-gate.py",
    "test-check-unattended-env.py",
    "test-launch-with-long-token.py",
    "test-ledger.py",
    "test-parent-issue.py",
    "test-child-cycle.py",
    "test-run-serial.py",
    "test-parallel-stop.py",
    "test-outer-loop.py",
    "test-cleanup-cycle.py",
    "test-fence-copies.py",
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
    "test-check-design-csv.py",
    "test-check-infra-csv.py",
    "test-check-screens.py",
    "test-screen-gate.py",
    "test-scaffold-screens.py",
    "test-write-screens.py",
    "test-build-mock.py",
    "test-screen-spec-pages.py",
    "test-check-findings-csv.py",
    "test-check-review-record.py",
    "test-findings-by-feature.py",
    "test-check-formal-rerun.py",
    "test-formal-statechart.py",
    "test-schedule-to-gantt.py",
    "test-render-diagrams.py",
    "test-check-signoff.py",
    "test-build-proposal.py",
    "test-proposal-pptx.py",
    "test-check-pptx-render.py",
    "test-scaffold.py",
    "test-rebuild-scope.py",
    "test-rework-metrics.py",
    "test-rework-report.py",
    "test-intake-code.py",
    "test-review-meeting.py",
    "test-parent-checklist.py",
    "test-green-list.py",
    "test-scaffold-estimate.py",
    "test-merge-versions.py",
    "test-diff-versions.py",
    "test-check-frozen.py",
    "test-autopilot-ledger.py",
    "test-autopilot-check.py",
    "test-formal-baseline.py",
    "test-check-tlc.py",
    "test-tlc-trace.py",
    "test-check-alloy.py",
    "test-autopilot-loop.py",
    "test-init-mkdocs.py",
    "test-tab-match.py",
    "test-check-plan-counts.py",
    "test-merge-pr.py",
    "test-check-gates.py",
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
# 集計に出す、所要時間の長い順の上位の本数（#1040）。
TOP = 5


# ------------------------------------------------------------ キャッシュ（#1151）
# 記録の形の版。**記録の読み方・指紋の取り方を変えたら上げる**——古い記録を当たりにしない。
CACHE_FORMAT = 1
# 記録の置き場所（`git rev-parse --git-common-dir` の下。worktree の間で共有する——中身で引くので共有して安全）。
CACHE_DIRNAME = "check-all-cache"
# 子の Python に差し込む hook のディレクトリ（`PYTHONPATH` の先頭に置く）。
TRACE_DIRNAME = "check_all_trace"
TRACE_LOG = "CHECK_ALL_TRACE_LOG"
TRACE_ROOT = "CHECK_ALL_TRACE_ROOT"
# 一覧・粗い単位で数えない名前（実行のたびに現れる・消える）。
LISTING_NOISE = {"__pycache__", ".DS_Store"}
# 配置だけを訊く `git rev-parse` の引数。中身に依らないので、git の状態を依存にしない。
GIT_LAYOUT_ARGS = {
    "--show-toplevel", "--git-dir", "--git-common-dir", "--absolute-git-dir", "--show-prefix",
    "--show-cdup", "--is-inside-work-tree", "--is-inside-git-dir", "--is-bare-repository",
    "--path-format=absolute", "--path-format=relative",
}
# リポジトリを読まない git のサブコマンド（引数に作業ツリーの中のパスが無ければ、git の状態を依存にしない）。
GIT_READ_FREE = {"init", "clone", "version", "--version", "help"}
# git の大域オプションのうち、次の引数を値に取るもの（サブコマンドを見つけるために飛ばす）。
GIT_VALUE_OPTS = {"-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}


def cache_root(repo: Path) -> Path | None:
    """記録の置き場所。git のリポジトリでなければ None（キャッシュを使わない）。"""
    proc = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, check=False, cwd=repo,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return Path(proc.stdout.strip()) / CACHE_DIRNAME


def cache_key(name: str, args: list[str]) -> str:
    """テストの名前・引数（`--jobs` を除く）と、結果を左右する環境の指紋。"""
    h = hashlib.sha256()
    plain = []
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a == "--jobs":
            skip = True
            continue
        plain.append(a)
    for part in (str(CACHE_FORMAT), sys.version, sys.executable, platform.platform(), name, "\0".join(plain)):
        h.update(part.encode() + b"\0")
    # **集め方と比べ方そのもの**——`check-all.py` と hook を直したら、古い記録は当たりにしない。
    for f in (SCRIPTS / "check-all.py", SCRIPTS / TRACE_DIRNAME / "usercustomize.py"):
        h.update(f.read_bytes() if f.is_file() else b"<absent>")
        h.update(b"\0")
    return h.hexdigest()


def trace_env(log: Path, repo: Path) -> dict[str, str]:
    env = dict(os.environ)
    trace = str(SCRIPTS / TRACE_DIRNAME)
    env["PYTHONPATH"] = trace + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env[TRACE_LOG] = str(log)
    env[TRACE_ROOT] = str(repo)
    return env


def _rel(repo: Path, path: str, cwd: str) -> str | None:
    """`path`（`cwd` 基準）が作業ツリーの中なら根からの相対パス。"""
    p = os.path.normpath(os.path.join(cwd, path))
    root = str(repo)
    if p == root:
        return "."
    if p.startswith(root + os.sep):
        return p[len(root) + 1:]
    return None


def _ignored(rel: str) -> bool:
    """依存に数えないパス——`.git/` の下（git の中身は git コマンドの側で見る）と `__pycache__`。"""
    parts = rel.split("/")
    return parts[0] == ".git" or "__pycache__" in parts or rel.endswith(".pyc")


PYC = re.compile(r"^(?:(?P<dir>.*)/)?__pycache__/(?P<mod>[^/.]+)\.[^/]+\.pyc$")


def pyc_source(rel: str) -> str | None:
    """`<dir>/__pycache__/<mod>.<tag>.pyc` を `<dir>/<mod>.py` に戻す。**import は `.pyc` が新しければ `.py` を開かない**
    （stat で鮮度を見るだけ）ので、`.pyc` を開いたことを、その元の `.py` を読んだことと数える（#1151 の 1 パス目）。"""
    m = PYC.match(rel)
    if not m:
        return None
    return f"{m.group('dir')}/{m.group('mod')}.py" if m.group("dir") else f"{m.group('mod')}.py"


def coarse_unit(rel: str) -> str:
    """hook の入らない子が読みうる範囲。プラグインならその全体、`scripts/` ならその全体、ほかはそのパス。"""
    parts = rel.split("/")
    if parts[0] == "plugins" and len(parts) >= 2:
        return "/".join(parts[:2])
    if parts[0] == "scripts":
        return "scripts"
    return rel


def _is_python(prog: str) -> bool:
    return os.path.basename(prog).lower().startswith("python") or prog == sys.executable


PYTHON_VALUE_OPTS = {"-W", "-X", "--check-hash-based-pycs"}


def _python_untraced_flags(argv: list[str]) -> bool:
    """`-I`・`-E`・`-s`・`-S` を渡した Python には hook が入らない。**値を取る `-W`・`-X` の値はスクリプトの名前と読まない。**"""
    args = argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if not a.startswith("-") or a in ("-c", "-m", "-"):
            return False
        if a in PYTHON_VALUE_OPTS:
            i += 2
            continue
        if a.startswith("--"):
            i += 1
            continue
        if a[1] in "WX":  # `-Wignore`・`-Xdev` の形——値が続けて書いてある
            i += 1
            continue
        if any(ch in a[1:] for ch in "IEsS"):
            return True
        i += 1
    return False


def _git_reads_repo(repo: Path, argv: list[str], cwd: str) -> bool:
    """この git が作業ツリーの中身（コミット・索引・作業中のファイル）に依るか。"""
    where = cwd
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "-C" and i + 1 < len(argv):
            where = os.path.join(where, argv[i + 1])
            i += 2
            continue
        if a in GIT_VALUE_OPTS and i + 1 < len(argv):
            if a in ("--git-dir", "--work-tree"):
                where = os.path.join(where, argv[i + 1])
            i += 2
            continue
        if a.startswith(("--git-dir=", "--work-tree=")):
            where = os.path.join(where, a.split("=", 1)[1])
            i += 1
            continue
        if a.startswith("-"):
            i += 1
            continue
        break
    sub = argv[i] if i < len(argv) else ""
    rest = argv[i + 1:]
    # 引数が作業ツリーの中を指す（`git clone <作業ツリー> …` など）——読む。**相対の引数は `-C` を反映した先で解決する**
    # （`git -C <一時ディレクトリ> add README.md` の `README.md` を cwd 基準で読むと、作業ツリーの同名のファイルに当たる）。
    for a in rest:
        if a.startswith("-"):
            a = a.split("=", 1)[1] if "=" in a else ""
        if a and _rel(repo, a, where) is not None and os.path.exists(os.path.join(where, a)):
            return True
    if sub in GIT_READ_FREE:
        return False
    if _rel(repo, ".", where) is None:
        return False
    if sub == "rev-parse" and rest and all(r in GIT_LAYOUT_ARGS for r in rest):
        return False
    return True


def collect_deps(log: Path, repo: Path) -> dict:
    """hook の書いた記録から、依存（ファイル・一覧・粗い単位・git の状態）を組む。"""
    files: set[str] = set()
    dirs: set[str] = set()
    coarse: set[str] = set()
    git = False
    lines = log.read_text(encoding="utf-8").splitlines() if log.is_file() else []
    for line in lines:
        try:
            kind, val = json.loads(line)
        except ValueError:
            continue
        if kind == "open":
            src = pyc_source(val)
            if src is not None and not _ignored(src):
                files.add(src)
            elif not _ignored(val):
                files.add(val)
        elif kind == "list" and not _ignored(val):
            dirs.add(val)
        elif kind == "spawn":
            argv = [a for a in val.get("argv", []) if isinstance(a, str)]
            cwd = val.get("cwd") or str(repo)
            if not argv:
                continue
            prog = argv[0]
            if os.path.basename(prog) == "git":
                git = git or _git_reads_repo(repo, argv, cwd)
                continue
            traced = _is_python(prog) and val.get("env") is True and not _python_untraced_flags(argv)
            if traced:
                continue  # 子の hook が自分で書く
            # **hook の入らない子**——引数に現れた作業ツリーの中のパスを、粗い単位で依存にする。
            words = argv  # 先頭も見る——作業ツリーの中のスクリプトを直に起こす子（`plugins/x/run.sh arg`）
            for w in words:
                cands = [w, w.split("=", 1)[1] if "=" in w else None]
                if any(ch.isspace() for ch in w):
                    # `sh -c "<コマンド>"`・`shell=True`・`os.system` は、コマンドが 1 つの引数に入る——語に割って見る。
                    # その中の git は中身に依ると見なす（どの git かを割った語から決めない）。
                    try:
                        toks = shlex.split(w)
                    except ValueError:
                        toks = w.split()
                    cands += toks
                    git = git or any(os.path.basename(t) == "git" for t in toks)
                for cand in cands:
                    if not cand or cand.startswith("-"):
                        continue
                    rel = _rel(repo, cand, cwd)
                    if rel is None or rel == "." or _ignored(rel):
                        continue
                    if not os.path.exists(os.path.join(cwd, cand)):
                        continue
                    coarse.add(coarse_unit(rel))
    return {"files": sorted(files), "dirs": sorted(dirs), "coarse": sorted(coarse), "git": git}


class Hasher:
    """指紋の計算。同じファイルを何本ものテストが読むので、1 回の実行の中では覚えておく。"""

    def __init__(self, repo: Path):
        self.repo = repo
        self.memo: dict[str, str] = {}
        self.git_state_memo: str | None = None

    def file(self, rel: str) -> str:
        if rel not in self.memo:
            p = self.repo / rel
            try:
                if p.is_dir():
                    self.memo[rel] = "dir"
                else:
                    self.memo[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
            except FileNotFoundError:
                self.memo[rel] = "absent"
            except OSError as e:
                self.memo[rel] = f"error:{e.errno}"
        return self.memo[rel]

    def listing(self, rel: str) -> str:
        p = self.repo / rel
        try:
            names = sorted(n for n in os.listdir(p) if n not in LISTING_NOISE)
        except FileNotFoundError:
            return "absent"
        except OSError as e:
            return f"error:{e.errno}"
        return hashlib.sha256("\0".join(names).encode()).hexdigest()

    def unit(self, rel: str) -> str:
        p = self.repo / rel
        if not p.is_dir():
            return self.file(rel)
        h = hashlib.sha256()
        for d, subdirs, names in os.walk(p):
            subdirs[:] = sorted(s for s in subdirs if s not in LISTING_NOISE)
            for n in sorted(names):
                if n in LISTING_NOISE or n.endswith(".pyc"):
                    continue
                r = os.path.relpath(os.path.join(d, n), self.repo)
                h.update(r.encode() + b"\0" + self.file(r).encode() + b"\0")
        return h.hexdigest()

    def git_state(self) -> str:
        """HEAD のコミットと、作業中の変更——`git status` に出たパスと、**その中身**。
        木ではなくコミットで見る——木が同じコミット（空のコミット・メッセージの直し）でも、`git log` を読むテストは変わる。

        パスだけでは、変更済みのファイルをさらに書き換えても同じになる。`__pycache__`・`.pyc`・`.DS_Store` は
        数えない（回したテストが作るので、数えると回すたびに変わる）。"""
        if self.git_state_memo is None:
            h = hashlib.sha256()
            tree = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, check=False, cwd=self.repo)
            h.update(tree.stdout if tree.returncode == 0 else b"<error>")
            st = subprocess.run(["git", "status", "--porcelain=v1", "-uall", "-z"],
                                capture_output=True, check=False, cwd=self.repo)
            if st.returncode != 0:
                h.update(b"<error>")
            else:
                for entry in sorted(e for e in os.fsdecode(st.stdout).split("\0") if e):
                    path = entry[3:] if len(entry) > 3 and entry[2] == " " else entry
                    parts = path.split("/")
                    if "__pycache__" in parts or path.endswith(".pyc") or parts[-1] in LISTING_NOISE:
                        continue
                    h.update(entry.encode() + b"\0" + self.file(path).encode() + b"\0")
            self.git_state_memo = h.hexdigest()
        return self.git_state_memo

    def digests(self, deps: dict) -> dict[str, str]:
        got = {f"file:{r}": self.file(r) for r in deps["files"]}
        got.update({f"list:{r}": self.listing(r) for r in deps["dirs"]})
        got.update({f"unit:{r}": self.unit(r) for r in deps["coarse"]})
        if deps["git"]:
            got["git"] = self.git_state()
        return got


def changed_during(repo: Path, deps: dict, since_ns: int) -> list[str]:
    """`since_ns` より後に書き換わった依存（mtime で見る）。回している間の編集を記録に入れないため。

    **ディレクトリそのものの mtime は見ない**——Python が `__pycache__` を書くだけで親の mtime が動き、
    回したテストのほとんどが「変わった」になる（#1151 の 1 回目の実走で 15 本）。一覧はその中の名前
    （`LISTING_NOISE` と `.pyc` を除く）の mtime で、粗い単位はその下のファイルの mtime で見る。
    **回している間に名前が消えたことは、ここでは見えない**（消えた名前には mtime が無い）。
    **例外は 2 つ**——依存のファイルが無いときは、在る最も近い祖先のディレクトリの mtime で見る（消すと親が動く。
    親ごと消えたなら、その親の親が動く）。一覧の中の名前がディレクトリなら、その mtime も見る（回している間に作られた
    サブディレクトリは、作られた時刻を持つ）。"""
    paths = list(deps["files"])
    entries: set[str] = set()
    for rel in deps["dirs"]:
        try:
            names = [f"{rel}/{n}" if rel != "." else n for n in os.listdir(repo / rel)
                     if n not in LISTING_NOISE and not n.endswith(".pyc")]
        except OSError:
            continue
        names = [n for n in names if not _ignored(n)]  # 根の一覧の `.git` は回すたびに動く
        paths.extend(names)
        entries.update(names)
    for rel in deps["coarse"]:
        p = repo / rel
        if p.is_dir():
            for d, subdirs, names in os.walk(p):
                subdirs[:] = [s for s in subdirs if s not in LISTING_NOISE]
                paths.extend(os.path.relpath(os.path.join(d, n), repo) for n in names
                             if n not in LISTING_NOISE and not n.endswith(".pyc"))
        else:
            paths.append(rel)
    hits = []
    for rel in paths:
        p = repo / rel
        try:
            if p.is_dir() and rel not in entries:
                continue
            if os.stat(p).st_mtime_ns >= since_ns:
                hits.append(rel)
        except OSError:
            # 無い——回している間に消えたかもしれない。**在る最も近い祖先の mtime で見る**（消すと親が動き、
            # 親ごと消えたなら親の親が動く）。初めから無かったものも、その祖先の中で何かが書かれた回は
            # 「変わった」になる（記録しないだけで、判定は変えない）。
            up = p.parent
            while up != repo and not up.exists() and repo in up.parents:
                up = up.parent
            try:
                if os.stat(up).st_mtime_ns >= since_ns:
                    hits.append(rel)
            except OSError:
                pass
    return hits


def record_path(root: Path, name: str) -> Path:
    return root / f"{name}.json"


def load_record(root: Path, name: str) -> dict | None:
    """読めない記録は「無い」と同じに扱う（並行する書き込みの途中・壊れた記録で当たりにしない）。"""
    try:
        rec = json.loads(record_path(root, name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(rec, dict) or rec.get("format") != CACHE_FORMAT:
        return None
    return rec


def save_record(root: Path, name: str, rec: dict) -> None:
    """一時ファイルに書いてから `os.replace` で置く——並行する `check-all.py` が半端な記録を読まない。"""
    root.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=root, prefix=f".{name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False)
        os.replace(tmp, record_path(root, name))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def drop_record(root: Path, name: str) -> None:
    with contextlib.suppress(OSError):
        record_path(root, name).unlink()


def is_cached(root: Path, name: str, args: list[str], hasher: Hasher) -> bool:
    """記録があり、キーが同じで、記録した依存の指紋が今も同じなら当たり。"""
    rec = load_record(root, name)
    if rec is None or rec.get("key") != cache_key(name, args):
        return False
    deps, want = rec.get("deps"), rec.get("digests")
    if not isinstance(deps, dict) or not isinstance(want, dict):
        return False
    try:
        return hasher.digests(deps) == want
    except (KeyError, TypeError):
        return False


def traced_run(name: str, args: list[str], ctx: dict) -> tuple[bool, str, float]:
    """hook を差し込んで回し、緑なら依存を記録する。落ちた回は記録を消す。"""
    log = ctx["logdir"] / f"{name}.jsonl"
    ok, out, secs = timed(name, args, trace_env(log, ctx["repo"]))
    if ctx["stopping"]():
        return ok, out, secs  # 中断した回は記録を書きも消しもしない
    if not ok:
        drop_record(ctx["root"], name)
        return ok, out, secs
    deps = collect_deps(log, ctx["repo"])
    if f"scripts/{name}" not in deps["files"]:
        # **テスト自身を読んだ跡が無い——hook が入らなかった**（`usercustomize` を読まない Python・中断の途中で記録が消えた）。
        # 空の依存を記録すると、何を変えても当たりになる（#1151 の 1 パス目）。
        drop_record(ctx["root"], name)
        ctx["unrecorded"].append((name, "読んだものを集められなかった（hook が入っていない）"))
        return ok, out, secs
    moved = changed_during(ctx["repo"], deps, ctx["since_ns"])
    if deps["git"] and Hasher(ctx["repo"]).git_state() != ctx["git_at_start"]:
        moved.append("<git の状態>")
    if moved:
        drop_record(ctx["root"], name)
        ctx["unrecorded"].append((name, "回している間に入力が変わった: " + ", ".join(moved[:3])))
        return ok, out, secs
    try:
        save_record(ctx["root"], name, {
            "format": CACHE_FORMAT, "key": cache_key(name, args),
            "deps": deps, "digests": Hasher(ctx["repo"]).digests(deps),
        })
    except OSError as e:
        ctx["unrecorded"].append((name, f"記録を書けない: {e}"))
    return ok, out, secs


def run(name: str, args: list[str], env: dict[str, str] | None = None) -> tuple[bool, str]:
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
            env=env,
        )
        _live.add(proc)
    try:
        out, err = proc.communicate()
    finally:
        with _live_lock:
            _live.discard(proc)
    return proc.returncode == 0, (out + err)


def timed(name: str, args: list[str], env: dict[str, str] | None = None) -> tuple[bool, str, float]:
    """`run` を回し、(通ったか, 出力, 所要秒) を返す（#1040）。

    **作業者のスレッドの中で測る**——プールに投げた時点から測ると、順番待ちの時間が入る。
    `run` の中の起動の排他（`_live_lock`）の待ちは含む（docstring の「時間の取り方」）。
    判定（通ったか）は `run` の返り値をそのまま返す——時間で変えない。"""
    t0 = time.monotonic()
    ok, out = run(name, args) if env is None else run(name, args, env)
    return ok, out, time.monotonic() - t0


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
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="キャッシュの記録を読まずに回帰テストを全部回す（緑の記録は書く）",
    )
    opts = parser.parse_args()
    if opts.jobs < 1:
        parser.error(f"--jobs は 1 以上: {opts.jobs}")

    started = time.monotonic()
    since_ns = time.time_ns()
    have_base = base_resolves(opts.base)
    repo = SCRIPTS.parent
    # **記録の置き場所が無ければ（git のリポジトリでない）、キャッシュを使わず今までどおり全部回す。**
    store = None if opts.guards_only else cache_root(repo)

    failed: list[str] = []
    skipped: list[str] = []
    logs: list[tuple[str, str]] = []
    timings: list[tuple[float, str, bool]] = []  # (所要秒, 名前, 通ったか)。SKIP は入れない
    cached: list[str] = []  # 記録が当たって回さなかった回帰テスト。**OK にも SKIP にも数えない**
    unrecorded: list[tuple[str, str]] = []
    logdir = Path(tempfile.mkdtemp(prefix="check-all-trace-")) if store is not None else None

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
            guard_runs.append((label, pool.submit(timed, name, args)))
        test_args = {name: ["--jobs", str(nested_jobs(opts.jobs))] if name in NESTED else [] for name in TESTS}
        hits: set[str] = set()
        ctx: dict = {}
        if store is not None:
            hasher = Hasher(repo)
            if not opts.no_cache:
                hits = {name for name in TESTS if is_cached(store, name, test_args[name], hasher)}
            ctx = {"repo": repo, "root": store, "logdir": logdir, "since_ns": since_ns,
                   "git_at_start": hasher.git_state(), "unrecorded": unrecorded,
                   "stopping": lambda: _stopping}
        test_runs = ([] if opts.guards_only
                     else [(name, None if name in hits
                            else pool.submit(traced_run, name, test_args[name], ctx) if store is not None
                            else pool.submit(timed, name, test_args[name]))
                           for name in TESTS])

        print(f"=== 歯止め === （{opts.jobs} 並列）")
        for label, fut in guard_runs:
            if fut is None:
                print(f"  SKIP {label:<40} base `{opts.base}` が解決できない")
                skipped.append(label)
                continue
            ok, out, secs = fut.result()
            timings.append((secs, label, ok))
            print(f"  {'OK  ' if ok else 'FAIL'} {label:<40} {secs:7.1f} 秒", flush=True)
            if not ok:
                failed.append(label)
                logs.append((label, out))

        if opts.guards_only:
            print("=== 回帰テスト === SKIP（--guards-only）")
            skipped.extend(TESTS)
        else:
            print("=== 回帰テスト ===")
            if store is not None:
                print(f"キャッシュ: {'記録を読まない（--no-cache）' if opts.no_cache else '使う'}（{store}）")
            for name, fut in test_runs:
                if fut is None:
                    print(f"  CACHED {name}", flush=True)
                    cached.append(name)
                    continue
                ok, out, secs = fut.result()
                timings.append((secs, name, ok))
                print(f"  {'OK  ' if ok else 'FAIL'} {name:<40} {secs:7.1f} 秒", flush=True)
                if not ok:
                    failed.append(name)
                    logs.append((name, out))
    except KeyboardInterrupt:
        # **まだ起動していないものを起動せず、走っている子を止める。**
        pool.shutdown(wait=False, cancel_futures=True)
        stop_all()
        raise
    finally:
        if logdir is not None:
            shutil.rmtree(logdir, ignore_errors=True)
    pool.shutdown()

    for label, out in logs:
        print(f"\n----- {label} の出力 -----")
        print(out.rstrip())

    total = len(GUARDS) + len(TESTS)
    ran = total - len(skipped) - len(cached)
    elapsed = time.monotonic() - started
    if timings:
        print(f"\n所要時間の長い順（上位 {min(TOP, len(timings))} 本）:")
        for secs, label, ok in sorted(timings, key=lambda t: t[0], reverse=True)[:TOP]:
            print(f"  {secs:9.1f} 秒  {label}{'' if ok else '（FAIL）'}")
    print(f"全体: {elapsed:.1f} 秒（壁時計）")
    print(f"\n{ran}/{total} 本を回した（失敗 {len(failed)} / 飛ばし {len(skipped)}）")
    if cached:
        print(f"キャッシュ: {len(cached)} 本は、記録した入力が前回の緑から変わっていないので回していない"
              "（`--no-cache` で全部回す。PR 側の CI は全部回す）")
    for name, why in unrecorded:
        print(f"記録しなかった: {name}（{why}）")
    if skipped:
        print("飛ばしたもの: " + ", ".join(skipped))
        print("**飛ばしたものは回していない。** 手元の緑をそのまま「全部緑」と報告しない。")
    if failed:
        print("落ちたもの: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
