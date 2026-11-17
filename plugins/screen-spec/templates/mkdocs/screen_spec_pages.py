"""screen-spec の MkDocs のフック（正本に登録する薄いフック。screen-spec の雛形）。

spec-loop の MkDocs のフックの登録の口（`hooks/spec_loop_plugins/`）に置く——`write-screens.py mkdocs` が spec-loop の `init-mkdocs.py --hook` で写す。
**`mkdocs.yml` を書き換えない。** ここがするのは、screen-spec のプラグインを探して、その本体（`scripts/mkdocs-pages.py`）にイベントを渡すことだけである
——表の出し方とモックの作り方は screen-spec の更新で届く（このファイルを写し直さない）。決まりは screen-spec の `references/mkdocs.md`。

**screen-spec の見つけ方**（この順。最初に見つけたものを使う）:

1. 環境変数 `SCREEN_SPEC_PLUGIN`（screen-spec のプラグインの根）——screen-spec でなければ（`.claude-plugin/plugin.json` の `name`）、2 へ進まずに止める
2. Claude Code の設定のディレクトリ（`CLAUDE_CONFIG_DIR`、無ければ `~/.claude`）の `plugins/installed_plugins.json` の `screen-spec@<マーケットプレイス>` の `installPath`
   （正本を `projectPath` に含む `project` の記録を先に、無ければ `user`。1 つに決まらなければ見つからないと同じ）

**見つからない・読み込めないときは、警告し（`mkdocs build --strict` は落ちる）、仕様書の表の印とモックのページに注意書きを置く**——黙って空にしない。
Claude Code の入っていない環境（正本の CI）でビルドするなら、claude-code-setup を取得して `SCREEN_SPEC_PLUGIN` に `plugins/screen-spec` を渡す
（spec-loop は `SCREEN_SPEC_SPEC_LOOP` に `plugins/spec-loop`）。標準ライブラリだけで動く（正本へ写されて単独で動く）。
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.screen_spec_pages")

# screen-spec の references/mkdocs.md の写し（テストが突き合わせる）
ENV = "SCREEN_SPEC_PLUGIN"
NAME = "screen-spec"
INSTALLED = "plugins/installed_plugins.json"
IMPL = "scripts/mkdocs-pages.py"
MARK = "<!-- screen-spec: 表 -->"
SCREENS = re.compile(r"v[1-9][0-9]*/requirements/screens/[^/]+\.md")
TABLES = ("requirements/screens/data/screens.csv", "requirements/screens/data/screen-items.csv",
          "requirements/screens/data/transitions.csv")

_found: dict[str, tuple[object | None, str]] = {}
_warned: set[str] = set()


def is_screen_spec(root: Path) -> bool:
    try:
        data = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get("name") == NAME


def installed(docs: Path) -> Path | None:
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        data = json.loads((config / INSTALLED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return None
    entries = [e for key, value in plugins.items() if isinstance(key, str) and key.startswith(NAME + "@") and isinstance(value, list)
               for e in value if isinstance(e, dict)]
    here = docs.resolve()
    project = [e for e in entries if e.get("scope") == "project" and isinstance(e.get("projectPath"), str)
               and (here == Path(e["projectPath"]) or Path(e["projectPath"]) in here.parents)]
    user = [e for e in entries if e.get("scope") == "user"]
    chosen = project if project else user
    if len(chosen) != 1 or not isinstance(chosen[0].get("installPath"), str):
        return None
    return Path(chosen[0]["installPath"])


def find(docs: Path) -> tuple[Path | None, str]:
    named = os.environ.get(ENV)
    if named:
        root = Path(named)
        return (root, "") if is_screen_spec(root) else (None, f"{ENV} が指す {root} は screen-spec のプラグインの根でない")
    root = installed(docs)
    if root is not None and is_screen_spec(root):
        return root, ""
    return None, f"screen-spec が見つからない——環境変数 {ENV} に screen-spec のプラグインの根を渡す（references/mkdocs.md）"


def impl(config) -> tuple[object | None, str]:
    """screen-spec の本体（`scripts/mkdocs-pages.py`）。読み込めなければ (None, 理由)。ビルドの間は覚えておく。"""
    docs = Path(config["docs_dir"])
    key = str(docs.resolve())
    if key not in _found:
        root, reason = find(docs)
        module = None
        if root is not None:
            try:
                spec = importlib.util.spec_from_file_location("screen_spec_mkdocs_pages", root / IMPL)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:  # noqa: BLE001 — 読み込めないことを注意書きにする（spec-loop のページまで止めない）
                module, reason = None, f"{root / IMPL} を読み込めない（{type(e).__name__}: {e}）"
        _found[key] = (module, reason)
    module, reason = _found[key]
    if module is None and key not in _warned:
        _warned.add(key)
        log.warning("screen-spec: %s", reason)
    return module, reason


def notice(reason: str) -> str:
    return f'!!! warning "表示できない"\n\n    screen-spec の表を出せない（{reason.replace("|", "&#124;")}）\n'


def on_files(files, config):
    _found.clear()
    _warned.clear()
    module, _ = impl(config)
    if module is None:
        return files
    return module.on_files(files, config=config)


def on_page_markdown(markdown: str, page, config, files):
    if MARK not in markdown:
        return markdown
    module, reason = impl(config)
    if module is not None:
        return module.on_page_markdown(markdown, page=page, config=config, files=files)
    src = getattr(page.file, "src_uri", page.file.src_path).replace("\\", "/")
    if not SCREENS.fullmatch(src):
        return markdown
    return "\n".join(notice(reason) if line.strip() == MARK else line for line in markdown.split("\n"))


def spec_loop_mocks(docs_dir) -> list[dict]:
    """spec-loop のフックの口——`docs/mocks.md` の版ごとの節に足す、生成したモックの行。"""
    docs = Path(docs_dir)
    module, reason = impl({"docs_dir": str(docs)})
    if module is not None:
        return module.spec_loop_mocks(docs)
    out = []
    for entry in sorted(docs.iterdir()) if docs.is_dir() else []:
        if re.fullmatch(r"v[1-9][0-9]*", entry.name) and any((entry / path).is_file() for path in TABLES):
            out.append({"version": int(entry.name[1:]), "problem": f"画面モックを作れない（{reason}）"})
    return out
