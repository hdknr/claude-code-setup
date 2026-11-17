"""`check-all.py` のキャッシュ（#1151）が、回帰テストの読んだものを集めるための audit hook。

**`check-all.py` だけが使う。手で読み込まない。** `check-all.py` が回帰テストを起こすときに、
このディレクトリを `PYTHONPATH` の先頭に置き、`CHECK_ALL_TRACE_LOG`（書く先）と
`CHECK_ALL_TRACE_ROOT`（作業ツリーの根）を渡す。Python は起動時に `site` が `usercustomize` を読むので、
**テストと、その環境を引き継いだ子の Python の全部**にこの hook が入る。2 つの変数が無ければ何もしない。

**`sitecustomize` ではなく `usercustomize` にしたのは、Homebrew の Python が自前の `sitecustomize` を持つから**——
同じ名前で先に見つかると、それを隠してテストの環境を変える（#1151 の手順 2 で実測）。

書くのは 1 行 1 件の JSON（`["open", 根からの相対パス]`・`["list", …]`・`["spawn", {"argv", "cwd", "env"}]`）だけで、
**どれを依存に数えるかは `check-all.py` が決める**（ここに判断を置かない——hook はすべての子で動くので軽く保つ）。

**ここで起きた例外はすべて握りつぶす**——hook がテストの判定を変えてはならない。

何を見ないか（取りこぼしの本体は `check-all.py` の docstring を正とする）:

- **`os.stat` など、開かずに在るかだけを見る操作**——audit イベントが無い。
- **相対パスの `os.open`（どれも）**——`dir_fd` 基準かどうかがイベントに載らない（`shutil.rmtree` がこの形で一時ディレクトリを消す）ので、
  **`os.chdir` の後に `dir_fd` 無しで開いたものも含めて**数えない。組み込みの `open`（`io.open`）と `io.open_code` の相対パスは cwd で解決して数える。
- **import の仕組みがディレクトリを列挙すること**——`sys.path` のディレクトリにファイルが増えるたびに全部が外れるので数えない。
"""

from __future__ import annotations

import os
import sys

_LOG = os.environ.get("CHECK_ALL_TRACE_LOG")
_ROOT = os.environ.get("CHECK_ALL_TRACE_ROOT")


def _install(log: str, root: str) -> None:
    import json

    seen: set[str] = set()

    def write(item) -> None:
        line = json.dumps(item, ensure_ascii=False)
        if line in seen:
            return
        seen.add(line)
        fd = os.open(log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(fd, (line + "\n").encode("utf-8"))
        finally:
            os.close(fd)

    def inside(path):
        """根の内側の絶対パスなら、根からの相対パスを返す。"""
        if isinstance(path, int) or path is None:
            return None
        p = os.fsdecode(path)
        if not os.path.isabs(p):
            p = os.path.join(os.getcwd(), p)
        p = os.path.normpath(p)
        if p == root:
            return "."
        if p.startswith(root + os.sep):
            return p[len(root) + 1:]
        return None

    def from_import() -> bool:
        """列挙が import の仕組み（`FileFinder._fill_cache`）から来たか。**直接の呼び手だけを見る**——
        `exec_module` で読み込んだモジュールの中の列挙は、スタックの奥に importlib があっても数える。"""
        caller = sys._getframe(2)  # 0: ここ・1: hook・2: os.listdir を呼んだ Python のフレーム
        return "_bootstrap_external" in caller.f_code.co_filename

    def text(x) -> str:
        return x if isinstance(x, str) else os.fsdecode(x) if isinstance(x, (bytes, os.PathLike)) else str(x)

    here = os.path.dirname(os.path.abspath(__file__))

    def env_get(env, key: str):
        v = env.get(key)
        if v is None:
            try:
                v = env.get(key.encode())  # `subprocess` には bytes の鍵の env も渡せる
            except TypeError:  # `os.environ` は bytes の鍵を訊くと TypeError
                v = None
        return os.fsdecode(v) if v is not None else None

    def hooked(env) -> bool:
        """子にこの hook が入るか。**書く先の変数が残っていても、`PYTHONPATH` からこのディレクトリが外れた・
        `PYTHONNOUSERSITE` で `usercustomize` を読まない環境なら入らない**（#1151 の 1 パス目）。"""
        if env_get(env, "CHECK_ALL_TRACE_LOG") is None or env_get(env, "CHECK_ALL_TRACE_ROOT") is None:
            return False
        if env_get(env, "PYTHONNOUSERSITE"):
            return False
        paths = (env_get(env, "PYTHONPATH") or "").split(os.pathsep)
        return any(p and os.path.abspath(p) == here for p in paths)

    def spawn(argv, cwd, env) -> None:
        if isinstance(argv, (str, bytes)):
            argv = [argv]
        argv = [text(a) for a in (argv or [])]
        try:
            env_ok = hooked(os.environ if env is None else env)
        except Exception:
            env_ok = False
        # cwd は相対でも渡せる——ここで絶対にしておく（`check-all.py` は記録を書いた後に読むので、cwd を知らない）。
        where = os.getcwd() if cwd is None else os.path.join(os.getcwd(), text(cwd))
        write(["spawn", {"argv": argv, "cwd": os.path.normpath(where), "env": env_ok}])

    def hook(event: str, args) -> None:
        try:
            if event == "open":
                path, mode = args[0], args[1]
                # `os.open` は mode に None を渡す（組み込みの `open` は文字列）。相対パスなら dir_fd 基準かも
                # しれない（`shutil.rmtree` がこの形で一時ディレクトリの中を消す）ので数えない。
                if not isinstance(mode, str) and not isinstance(path, int) and not os.path.isabs(os.fsdecode(path)):
                    return
                rel = inside(path)
                if rel is not None:
                    write(["open", rel])
            elif event in ("os.listdir", "os.scandir"):
                if from_import():
                    return
                path = args[0] if args and args[0] is not None else "."
                rel = inside(path)
                if rel is not None:
                    write(["list", rel])
            elif event == "subprocess.Popen":
                _exe, argv, cwd, env = args
                spawn(argv, cwd, env)
            elif event in ("os.posix_spawn", "os.exec"):
                _path, argv, env = args
                spawn(argv, None, env)
            elif event == "os.system":
                # シェルが読むので hook は入らない。`env` を False にして「見えない子」に数えさせる。
                write(["spawn", {"argv": ["/bin/sh", "-c", text(args[0])], "cwd": os.getcwd(), "env": False}])
        except Exception:
            pass

    sys.addaudithook(hook)


if _LOG and _ROOT:
    try:
        _install(_LOG, os.path.normpath(_ROOT))
    except Exception:
        pass
