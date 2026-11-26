#!/usr/bin/env python3
"""外部の profile のアーキテクチャの層と開発の進め方の層を、案件の設定のタグの時点から読み、使う側に渡す形にして出す（#1558。#1312 の段 4）。

usage: python3 profile-layers.py <architecture|dev-loop> <docs ディレクトリ> [--upto <n>] [--clone <profile の手元の clone>] [--spec-loop <spec-loop のプラグインの根>]

**決まりの正は `references/layers.md`（2 つの層の表の形・語彙・形式の版の範囲・層ごとの持ち物・出すものの形）である**（このプラグインの中にある）。
下の定数はその写しで、**写しがずれていないかは、このプラグインを置いているリポジトリの `scripts/test-profile-layers.py` が突き合わせる。**

- **`architecture`**——アーキテクチャの層を、Domain Checker に渡す照合先の一覧（Markdown）にして標準出力に出す（本文の読み方のコマンドに手元の clone のパスが入る）。
- **`dev-loop`**——開発の進め方の層から、`.claude/dev-loop.md` の雛形と、正本の `CLAUDE.md` に書く `impl_module` の行を標準出力に出す（手元のパスを書かない）。
- **写さない**——設定の読み方・spec-loop の見つけ方と版の確かめ・spec-loop の重ね方は同じ場所の `check-infra-profile.py` を、
  タグの読み出し・層の表・リンクの検査は spec-loop の `external-profile.py` の `find_clone`・`resolve_tag`・`read_layer`・`check_links` を読み込む。
- **読むだけ**——ファイルを 1 つも書かない（読み込むスクリプトの `__pycache__` も）。出したものをどこに置くかは利用者が決める。
- 標準ライブラリと `git` だけを使う。

終了コード:

- 0: 出した（切れたリンクも無い）
- 1: 出したが切れたリンクがある（出力にその行を書く）、または違反——設定の形・重ね合わせが spec-loop の決まりに反する（このときは何も出さない）
- 2: 判定していない——引数の誤り・`docs` が無い・表が読めない・想定外の例外
- 3: 無い——案件の設定が無い（platform-spec を使っていない）・profile にその層が無い（何も出さない）
- 4: 止めた（判定できなかった）——spec-loop が見つからない・版が範囲の外か古い・clone が見つからない・タグが無い・
  層の形式の版が範囲の外・層の表の形が違う（見出し・語彙の外の `項目`・1 行までの項目が 2 行・空にしない列が空・`値` の改行）

**守ること**:

- 案件の設定が無ければ、clone を探さずに 3
- 設定の形の違反（`check-infra-profile.py` と同じ見方）は、profile を読まずに 1
- 重ね合わせが spec-loop の決まりに反すれば 1
- profile に求めた層が無ければ 3（判定できなかったの 4 にしない）
- アーキテクチャの層の見出しが形式の版 1 の 4 列（`ID,要約,リンク,観点`）でなければ 4
- 開発の進め方の層の見出しが形式の版 1 の 5 列（`ID,要約,リンク,項目,値`）でなければ 4
- 層の表の見出しは、空の行を飛ばした最初の行で読む
- アーキテクチャの層の `観点` が空なら 4
- 開発の進め方の層の `項目` が語彙の外なら 4
- 1 行までの項目（`歯止め`・`impl_module`）が 2 行あれば 4
- `impl_module` の `値` が空なら 4
- `値` が改行を含めば 4
- 照合先の一覧に、行ごとに ID・観点・要約・本文の参照と、タグの時点の本文を読むコマンドを載せる
- 雛形の先頭に印 `<!-- platform-spec: 開発の進め方 <リポジトリ> <profile> <タグ> -->` を置く
- 雛形の行を `- <ID>: <要約>（値: `<値>`）——本文: <リポジトリ>@<タグ>:<パス>` の形で、項目の節の下に置く
- 雛形に手元の clone のパスを書かない
- `impl_module` の行を、雛形の後ろの正本の `CLAUDE.md` に書く行として分けて出す
- 切れたリンクの行は出力に残して理由を書き、1
- `--upto` で前の版の時点の設定を読む
- 引数 `--clone` を外部の profile の探し方に渡す

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **2 つの層の版の差分と起票の候補** | この 2 つの層は発注者が決める値ではない。出したものを毎回タグの時点から作り直す（`references/layers.md` の「守らないもの」） |
| **`観点` の語彙** | 組織ごとに違うので持たない |
| **本文が正しいか・本文の中身** | 本文は profile のリポジトリの文書が正。在るか（リンク）までしか見ない |
| **出したものを置いた後に古くなったか** | 出したものは書かないので、置いた先の鮮度は見ない。タグを上げたら作り直す |
| **基盤の層** | `check-infra-profile.py`・`check-profile-diff.py` が見る |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import re
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # 読み込むスクリプトの `__pycache__` を書かない（このスクリプトはファイルを 1 つも書かない）


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load("platform_spec_check_infra_profile_for_layers", HERE / "check-infra-profile.py")
Stop = base.Stop
Unreadable = base.Unreadable

# ---- `references/layers.md` の写し
ARCH = "アーキテクチャ"
ARCH_COLUMNS = ["ID", "要約", "リンク", "観点"]
PROCESS = "開発の進め方"
PROCESS_COLUMNS = ["ID", "要約", "リンク", "項目", "値"]
FORMAT_RANGES = {ARCH: ("1", "2"), PROCESS: ("1", "2")}  # 層 → (下限（含む）, 上限（含まない）)
# 項目 → (雛形の節, 1 行までか)。順は雛形に出す順
PROCESS_ITEMS = {
    "verify": ("実機検証（verify）の手順", False),
    "deploy": ("デプロイ経路", False),
    "歯止め": ("歯止めを全部回す 1 本のコマンド", True),
    "制約": ("やってはいけない制約", False),
    "リポジトリの構成": ("リポジトリの構成", False),
    "impl_module": ("正本の `CLAUDE.md` に書く行（scaffold が読む）", True),
}
IMPL_MODULE = "impl_module"
TEMPLATE_MARK = "<!-- platform-spec: 開発の進め方 {repo} {profile} {tag} -->"
IMPL_LINE = "- 実装のモジュール名（`impl_module`）: `{value}`"
SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
COMMANDS = ("architecture", "dev-loop")
LAYER_OF = {"architecture": ARCH, "dev-loop": PROCESS}


class Missing(Exception):
    """無い（3）。"""


class Layers(base.Checker):
    """設定と重ね方は `check-infra-profile.py` の `Checker` のまま使い、層だけ読み替える。"""

    def read(self, settings: dict[str, str], layer_name: str):
        ext = self.ext
        repo, name, tag = settings[base.SETTING_REPO], settings[base.SETTING_PROFILE], settings[base.SETTING_TAG]
        columns = ARCH_COLUMNS if layer_name == ARCH else PROCESS_COLUMNS
        low, high = FORMAT_RANGES[layer_name]
        try:
            clone, source = ext.find_clone(repo, self.clone, self.docs.resolve().parent)
            commit = ext.resolve_tag(clone, tag)
            layer = ext.read_layer(clone, commit, name, layer_name, low, high)
            for path in layer.files:
                head = next((row for row in csv.reader(io.StringIO(ext.read_blob(clone, commit, path).decode("utf-8-sig"), newline=""))
                             if any(cell.strip() for cell in row)), [])
                if head != columns:
                    raise Stop(f"{repo} の {path}（タグ {tag}）の見出しが形式の版 1 の `{','.join(columns)}` でない: {','.join(head)}")
            broken = {rid: reason for rid, _, reason in ext.check_links(clone, commit, layer)}
        except ext.LayerMissing as e:
            raise Missing(f"profile {name}（{repo} のタグ {tag}）に{layer_name}の層が無い: {e}") from None
        except ext.Undetermined as e:
            raise Stop(f"{repo} の profile {name}（タグ {tag}）を読めない: {e}") from None
        except UnicodeDecodeError as e:
            raise Stop(f"{repo} の profile {name}（タグ {tag}）の{layer_name}の層の表が UTF-8 でない: {e}") from None
        self.rows_shape(layer_name, layer.rows, f"{repo} の profile {name}（タグ {tag}）の{layer_name}の層")
        self.notes.append(f"profile: {repo} の {name}（タグ {tag}・{layer.version}・{len(layer.rows)} 行。clone {clone}（出所: {source}））")
        return clone, commit, layer, broken

    @staticmethod
    def rows_shape(layer_name: str, rows: dict[str, dict[str, str]], where: str) -> None:
        if layer_name == ARCH:
            for rid, row in rows.items():
                if not row["観点"].strip():
                    raise Stop(f"{where}: {rid} の 観点 が空")
            return
        seen: dict[str, int] = {}
        for rid, row in rows.items():
            item = row["項目"].strip()
            if item not in PROCESS_ITEMS:
                raise Stop(f"{where}: {rid} の 項目 {item!r} は語彙の外（{'・'.join(PROCESS_ITEMS)} のどれか）")
            seen[item] = seen.get(item, 0) + 1
            if PROCESS_ITEMS[item][1] and seen[item] > 1:
                raise Stop(f"{where}: 項目 {item} は 1 行まで（{rid} が 2 行目）")
            if "\n" in row["値"] or "\r" in row["値"]:
                raise Stop(f"{where}: {rid} の 値 が改行を含む")
            if item == IMPL_MODULE and not row["値"].strip():
                raise Stop(f"{where}: {rid} の 値 が空（{IMPL_MODULE} は値を空にしない）")

    @staticmethod
    def reference(repo: str, tag: str, link: str) -> str:
        link = link.strip()
        if not link:
            return "なし"
        if SCHEME_RE.match(link):
            return link
        return f"{repo}@{tag}:{link.lstrip('/')}"

    def run(self, command: str) -> int:
        try:
            problems, _, whole, _ = self.versions.merge(self.docs, self.upto)
        except self.versions.Unreadable as e:
            raise Unreadable(str(e)) from None
        if problems:
            self.violations.extend(f"版の重ね合わせ: {problem}" for problem in problems)
            return self.finish_quiet()
        settings = self.settings(whole)
        if settings is None:
            raise Missing(f"{base.SETTINGS} が無い——platform-spec を使っていない（出すものが無い）")
        if self.violations:
            return self.finish_quiet()
        clone, commit, layer, broken = self.read(settings, LAYER_OF[command])
        out = self.architecture(settings, clone, commit, layer, broken) if command == "architecture" else self.template(settings, layer, broken)
        print(out, end="")
        for note in self.notes:
            print(note, file=sys.stderr)
        for rid, reason in broken.items():
            print(f"切れたリンク: {rid}: {reason}", file=sys.stderr)
        return 1 if broken else 0

    def finish_quiet(self) -> int:
        for violation in self.violations:
            print(f"違反: {violation}", file=sys.stderr)
        print(f"違反 {len(self.violations)} 件——何も出さない", file=sys.stderr)
        return 1

    def architecture(self, settings, clone, commit, layer, broken) -> str:
        repo, name, tag = settings[base.SETTING_REPO], settings[base.SETTING_PROFILE], settings[base.SETTING_TAG]
        lines = [f"# Domain Checker の照合先: アーキテクチャの層（{repo} の profile {name}・タグ {tag}）", "",
                 "platform-spec の `profile-layers.py architecture` が出した一覧。本文は profile のリポジトリの文書が正で、ここには写さない。",
                 f"本文は手元の clone のタグの時点を読む: `git -C {shlex.quote(str(clone))} show {commit}:<パス>`（タグ {tag} のコミット）。",
                 "**この一覧には手元のパスが入るので、正本の版の外に置き、commit しない。**", ""]
        for rid, row in layer.rows.items():
            ref = self.reference(repo, tag, row["リンク"])
            line = f"- {rid}（{row['観点'].strip()}）: {row['要約'].strip()}——本文: {ref}"
            if rid in broken:
                line += f"（リンクが切れている: {broken[rid]}）"
            lines.append(line)
        return "\n".join(lines) + "\n"

    def template(self, settings, layer, broken) -> str:
        repo, name, tag = settings[base.SETTING_REPO], settings[base.SETTING_PROFILE], settings[base.SETTING_TAG]
        lines = [TEMPLATE_MARK.format(repo=repo, profile=name, tag=tag),
                 f"# dev-loop の追補設定（profile {name} の開発の進め方の層から作った雛形）", "",
                 f"行は {repo} の profile {name}（タグ {tag}）の開発の進め方の層の行を指す。本文は profile のリポジトリの文書が正で、ここには写さない。",
                 "本文の読み方は dev-loop の `references/profile-template.md` を正とする。"]
        impl: list[str] = []
        for item, (heading, _) in PROCESS_ITEMS.items():
            rows = [(rid, row) for rid, row in layer.rows.items() if row["項目"].strip() == item]
            if not rows:
                continue
            body = []
            for rid, row in rows:
                value = row["値"].strip()
                line = f"- {rid}: {row['要約'].strip()}{f'（値: `{value}`）' if value else ''}——本文: {self.reference(repo, tag, row['リンク'])}"
                if rid in broken:
                    line += f"（リンクが切れている: {broken[rid]}）"
                body.append(line)
            if item == IMPL_MODULE:
                rid, row = rows[0]
                impl = ["", f"<!-- platform-spec: ここから下は .claude/dev-loop.md ではなく、正本の CLAUDE.md に書く行（{rid}） -->",
                        f"## {heading}", "", IMPL_LINE.format(value=row["値"].strip()), *body]
                continue
            lines.extend(["", f"## {heading}", "", *body])
        return "\n".join(lines + impl) + "\n"


def main(argv: list[str]) -> int:
    args = list(argv)
    named = {"--spec-loop": None, "--clone": None, "--upto": None}
    try:
        for flag in named:
            while flag in args:
                at = args.index(flag)
                if at + 1 >= len(args) or named[flag] is not None:
                    raise ValueError(f"{flag} には値を 1 つ渡す")
                named[flag] = args[at + 1]
                del args[at:at + 2]
        if named["--upto"] is not None and not re.fullmatch(r"[1-9][0-9]*", named["--upto"]):
            raise ValueError("--upto には 1 以上の整数を 1 つ渡す")
        if len(args) != 2 or args[0] not in COMMANDS or args[1].startswith("-"):
            raise ValueError(__doc__.splitlines()[2] if __doc__ else
                             f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）")
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    command, docs = args[0], Path(args[1])
    if not docs.is_dir():
        print(f"{docs}: ディレクトリが無い——判定していない", file=sys.stderr)
        return 2
    upto = int(named["--upto"]) if named["--upto"] is not None else None
    try:
        spec_loop = base.find_spec_loop(named["--spec-loop"], docs)
        shown = base.check_version(spec_loop)
        layers = Layers(spec_loop, docs, upto, named["--clone"])
        print(f"spec-loop {shown}（{spec_loop}）の重ね方と外部の profile の読み方で、{LAYER_OF[command]}の層を読む", file=sys.stderr)
        return layers.run(command)
    except Missing as e:
        print(f"無い: {e}", file=sys.stderr)
        return 3
    except Stop as e:
        print(f"止めた: {e}", file=sys.stderr)
        return 4
    except Unreadable as e:
        print(f"{e}——判定していない", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 や 1 にしない
        print(f"想定外の例外で判定していない: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
