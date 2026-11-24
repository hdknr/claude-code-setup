#!/usr/bin/env python3
"""案件が `infra.csv` の `profile の行` で指す外部の profile の行について、profile の新しい版（タグ）との差分を、共有の Q&A 表に起票する候補として出す（#1457）。

usage: python3 check-profile-diff.py <docs ディレクトリ> [--upto <n>] [--new <タグ>] [--clone <profile の手元の clone>] [--spec-loop <spec-loop のプラグインの根>] [--project <正本の根>]

**決まりの正は `references/infra-profile.md` の「案件の設定」と「版の差分と関門」である**（このプラグインの中にある）。下の定数はその写しで、
**写しがずれていないかは、このプラグインを置いているリポジトリの `scripts/test-check-profile-diff.py` が突き合わせる。**
spec-loop の関門（spec-loop の `scripts/profile-gate.py`）が、このスクリプトを子のプロセスで呼ぶ（spec-loop は platform-spec に依存しない）。

- **古い版は案件の設定の `タグ`、新しい版は `--new` か**、手元の clone のタグのうち、設定のタグと名前の形（接頭辞（最初の数字より前）と末尾の綴り（最後の数字より後ろ）が文字どおり同じで、
  真ん中が数字を設定のタグの区切りの文字（区切りを持たない `v3` なら `.`）で区切った並び——桁と個数は問わない。`v3`・`v1.0` なら `v10`・`v1.1.0`、`v1.0-lts` なら `v1.1-lts`、`2024-10-01` なら `2025-03-01`）が同じで、
  その profile の `profile.csv` を持つものの中で版の順（git の `v:refname`）が最も後ろのもの。
  **新しい版が `タグ` か任意の項目 `確かめたタグ` と同じなら、比べずに 0**（発注者が見て、採らないと決めた版）。
- **候補**は、`profile の行` が指す ID のうち、2 つの版の間で**変わった**（どの列でも）・**消えた**（新しい版の基盤の層に無い。層ごと無い場合も）・
  **新しい版でリンクの切れた**行。表の行・項目・ID・種類と、比べた 2 つの版を名指す。**足した行・指していない行は出さない。番号を振らない**——
  起票するのは feasibility（`SKILL.md`）で、番号を振るのは正本の Q&A 表に書く人。**profile は案を出すだけで、決めるのは発注者のまま。**
- **写さない**——設定と `profile の行` の読み方・spec-loop の見つけ方と版の確かめ・spec-loop の重ね方は同じ場所の `check-infra-profile.py` を、
  タグの読み出し・層の表・リンク・差分は spec-loop の `external-profile.py` の `find_clone`・`resolve_tag`・`list_files`・`read_layer`・`check_links`・`diff_layers` を読み込む。
- **読むだけ**——ファイルを 1 つも書かない（読み込むスクリプトの `__pycache__` も）。clone はタグの時点を読むだけ（`git for-each-ref` を足す）。
- 標準ライブラリと `git` だけを使う。

終了コード:

- 0: 候補が無い——比べる新しい版が `タグ`・`確かめたタグ` と同じ・指した行が変わっていない・設定も `profile の行` の値も無い（platform-spec を使っていない）
- 1: 候補がある、または違反——`check-infra-profile.py` の違反（設定の形・指しているのに設定が無い・空の ID・重ね合わせ）と、指した ID が古い版（`タグ`）の基盤の層に無い
- 2: 判定していない——引数の誤り・`docs` が無い・表が読めない・想定外の例外
- 4: 止めた（判定できなかった）——spec-loop が見つからない・版が範囲の外か古い・clone が見つからない・タグが無い・古い版に基盤の層が無い・
  形式の版が範囲の外・層の表の形が違う（古い版の層を先に読むので、その profile を持つタグが 1 つも無い形は古い版の読み出しで止まる）

**守ること**:

- 設定も `profile の行` の値も無ければ、clone を探さずに 0
- 指した ID の行が 2 つの版で変わっていれば、表の行・項目・ID と変わった列を名指しして 1
- 指した ID が新しい版に無ければ「消えた」で 1
- 新しい版に基盤の層が無ければ、指した ID を全部「消えた」にする（4 にしない）
- 指した ID のリンクが新しい版で切れていれば「リンクが切れた」で 1
- 指していない ID の変化・足した ID は名指さない
- 候補の行に Q&A の番号を振らない
- `--new` があれば、それを新しい版にする
- `--new` が無ければ、その profile を持つタグのうち版の順が最も後ろのものを新しい版にする
- その profile を持たないタグは、新しい版に数えない
- 設定のタグと名前の形（接頭辞・数字と区切りの並び・末尾の綴り）が違うタグ（別の profile・層の版名・プレリリース）は、新しい版に数えない
- 名前の形が違うので数えなかった、その profile を持つタグを出力に名指す
- 設定のタグの接頭辞は文字どおりに比べる（`.` などを正規表現として読まない）
- 新しい版の数字は区切った並びを、桁と個数を問わずに数える（`v1.0` の次の `v1.1.0`）
- 数字の区切りは設定のタグの区切りの文字で読む（`2024-10-01` なら `-`。区切りを持たない `v3` は `.`）
- 設定のタグの末尾の綴り（最後の数字より後ろ）は文字どおりに比べる（`v1.0-lts` の次の `v1.1-lts`。末尾の違う `v1.2-rc` は数えない）
- 新しい版が `タグ` と同じなら比べずに 0
- 新しい版が `確かめたタグ` と同じなら比べずに 0
- 新しい版が `タグ`・`確かめたタグ` と同じでも、古い版の層と、指した ID が古い版に在るかは照らす
- どちらかの版の基盤の層の表の見出しが形式の版 1 の 4 列（`ID,要約,リンク,項目`）でなければ 4
- 指した ID が古い版の基盤の層に無ければ 1（照合の違反）
- 古い版に基盤の層が無ければ 4
- 新しい版の基盤の層を読めなければ 4（形式の版・表の形）
- `check-infra-profile.py` の設定の違反は、clone を読む前に 1
- `--upto` で前の版の時点の全体を読む
- `--project` を clone の探し方の `CLAUDE.md` の場所にする（無ければ `docs` の親）
- 引数 `--clone` を外部の profile の探し方に渡す

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **接頭辞を変えた版**（`v9` の次を `release-10` にした） | 接頭辞と末尾の綴りが同じで、真ん中が区切った数字だけのタグを新しい版に数える（別の profile・層の版名・プレリリースを拾わないため）。数えなかった profile を持つタグは出力に名指すので、接頭辞を変えたなら設定のタグを上げるか `--new` で名指す |
| **末尾の綴りに数字を持つ名前**（`v1.0-lts2`） | 最初の数字から最後の数字までを真ん中と読み、その間の数字でない文字（`.`・`-`・`l`・`t`・`s`）を 1 文字ずつ区切りの候補にするが、数字の間に置ける区切りは 1 文字だけなので、区切りが 2 文字以上続く名前（`v1.0-lts2`・`v2.0.0-rc1`）は自分自身とも形が合わず、新しい版を数えない（比べずに 0。数えなかったタグは出力に名指す）。そうした付け方は試料に無く、規則を足さない（#1501） |
| **新しい版が古い版より前（タグを下げた）か** | 比べる 2 つを決めるだけで、向きは見ない（`--new` に古いタグを渡せば、その差分が出る） |
| **古い版でリンクが切れていたか** | 新しい版で切れた行だけを候補にする（古い版のリンクは `external-profile.py check` が見る） |
| **基盤の層の `項目` と案件の行の `項目` が合うか** | 照合の段（`check-infra-profile.py`）の守らないものと同じ |
| **候補を Q&A 表に起票したか・発注者が答えたか** | 起票は feasibility がし、答えの状態は spec-loop の関門（抜ける条件 1・サインオフの照合）が見る。このスクリプトは版の差分だけを見る |
| **clone のタグが最新か**（`git fetch --tags` したか） | clone を取り直さない（読むだけ）。新しい版が出たことは、手元の clone のタグでしか分からない |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 読み込むスクリプトの `__pycache__` を書かない（このスクリプトはファイルを 1 つも書かない）
sys.dont_write_bytecode = True

# ---- `references/infra-profile.md` の「版の差分と関門」の写し
KIND_CHANGED = "変わった"
KIND_REMOVED = "消えた"
KIND_BROKEN = "リンクが切れた"
CANDIDATE = "起票の候補: "


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load("platform_spec_check_infra_profile", HERE / "check-infra-profile.py")
Stop, Unreadable = base.Stop, base.Unreadable


def name_shape(tag: str) -> "re.Pattern[str]":
    """タグの名前の形——タグを接頭辞（最初の数字より前）・真ん中（最初の数字から最後の数字まで）・末尾の綴り（最後の数字より後ろ）に分け、
    接頭辞と末尾はそのまま同じで、真ん中が数字を設定のタグの区切りの文字（真ん中の数字でない文字。無ければ `.`）で区切った並びのもの
    （`v1.0-lts` → `v[0-9]+(?:[.][0-9]+)*-lts`、`2024-10-01` → `[0-9]+(?:[-][0-9]+)*`、`v3` → `v[0-9]+(?:[.][0-9]+)*`。数字の桁の数と区切りの数は問わない）。
    別の profile や層の版名（`zz-screen-v1`）・プレリリース（`v10-rc1`）・接頭辞を変えた版（`release-4`）・末尾の違う版（`v1.2-rc`）は当たらない。数字を持たないタグは自分だけに当たる。"""
    digits = [m.start() for m in re.finditer(r"[0-9]", tag)]
    if not digits:
        return re.compile(re.escape(tag))
    prefix, middle, suffix = tag[:digits[0]], tag[digits[0]:digits[-1] + 1], tag[digits[-1] + 1:]
    separators = sorted(set(re.sub(r"[0-9]", "", middle))) or ["."]
    separator = "[" + "".join(re.escape(c) for c in separators) + "]"
    return re.compile(re.escape(prefix) + r"[0-9]+(?:" + separator + r"[0-9]+)*" + re.escape(suffix))


def candidates(refs: list[tuple[str, str, list[str]]], old_rows: dict, new_rows: dict | None, broken: list[tuple[str, str, str]]) -> list[tuple[str, str, str, str, str]]:
    """候補の (場所, 項目, ID, 種類, 詳しく)。`old_rows`・`new_rows` は ID → {列: 値}（`new_rows` が None なら新しい版に基盤の層が無い）。
    `broken` は新しい版の切れたリンク（ID, リンク, 理由）。指した ID ごとに、変わった・消えた・リンクが切れたの順。"""
    new = new_rows or {}
    cut = {}
    for rid, link, why in broken:
        cut.setdefault(rid, f"{link}（{why}）")
    out = []
    for where, item, ids in refs:
        for rid in ids:
            if rid not in old_rows:
                continue
            if rid not in new:
                out.append((where, item, rid, KIND_REMOVED, ""))
                continue
            columns = sorted(set(old_rows[rid]) | set(new[rid]))
            changed = [c for c in columns if old_rows[rid].get(c) != new[rid].get(c)]
            if changed:
                out.append((where, item, rid, KIND_CHANGED, "列: " + "・".join(changed)))
            if rid in cut:
                out.append((where, item, rid, KIND_BROKEN, cut[rid]))
    return out


class Differ(base.Checker):
    def __init__(self, spec_loop: Path, docs: Path, upto: int | None, clone: str | None, new: str | None, project: Path | None) -> None:
        super().__init__(spec_loop, docs, upto, clone)
        self.new = new
        self.project = project if project is not None else docs.resolve().parent

    def newest(self, clone: Path, name: str, old: str) -> tuple[str, list[str]]:
        """(新しい版, 名前の形が違うので数えなかった、その profile を持つタグ)。新しい版は、設定のタグと名前の形が同じで、
        その profile の `profile.csv` を持つタグのうち版の順が最も後ろのもの。無ければ設定のタグ。"""
        ext = self.ext
        shape = name_shape(old)
        proc = ext._git(clone, "for-each-ref", "--sort=-v:refname", "--format=%(refname:strip=2)", "refs/tags/")
        if proc.returncode != 0:
            raise Stop(f"{clone} のタグを並べられない: {proc.stderr.decode('utf-8', 'replace').strip()}")
        want = f"{ext.PROFILE_ROOT}/{name}/{ext.PROFILE_FILE}"
        found, skipped = None, []
        for tag in proc.stdout.decode("utf-8", "surrogateescape").split():
            matches = bool(shape.fullmatch(tag))
            if matches and found is not None:
                continue
            try:
                commit = ext.resolve_tag(clone, tag)
            except ext.Undetermined:
                continue
            if want not in ext.list_files(clone, commit):
                continue
            if matches:
                found = tag
            else:
                skipped.append(tag)
        return (found if found is not None else old), skipped

    def layer(self, clone: Path, commit: str, name: str, tag: str, missing_ok: bool):
        ext = self.ext
        try:
            layer = ext.read_layer(clone, commit, name, base.LAYER, base.FORMAT_LOW, base.FORMAT_HIGH)
            for path in layer.files:
                head = next((row for row in csv.reader(io.StringIO(ext.read_blob(clone, commit, path).decode("utf-8-sig"), newline=""))
                             if any(cell.strip() for cell in row)), [])
                if head != base.LAYER_COLUMNS:
                    raise Stop(f"{path}（タグ {tag}）の見出しが形式の版 1 の `{','.join(base.LAYER_COLUMNS)}` でない: {','.join(head)}")
            return layer
        except ext.LayerMissing as e:
            if missing_ok:
                return None
            raise Stop(f"profile {name}（タグ {tag}）に{base.LAYER}の層が無い: {e}") from None
        except ext.Undetermined as e:
            raise Stop(f"profile {name}（タグ {tag}）を読めない: {e}") from None
        except UnicodeDecodeError as e:
            raise Stop(f"profile {name}（タグ {tag}）の{base.LAYER}の層の表が UTF-8 でない: {e}") from None

    def check(self) -> int:
        try:
            problems, _, whole, _ = self.versions.merge(self.docs, self.upto)
        except self.versions.Unreadable as e:
            raise Unreadable(str(e)) from None
        if problems:
            self.violations.extend(f"版の重ね合わせ: {problem}" for problem in problems)
            return self.finish()
        refs = self.references(whole)
        settings = self.settings(whole)
        if settings is None:
            if not refs:
                print(f"{base.SETTINGS} も {base.INFRA} の {self.column} の値も無い——比べるものが無い（platform-spec を使っていない）")
                return 0
            for where, item, _ in refs:
                self.violations.append(f"{where}: {item} が {self.column} を指しているのに、案件の設定（{base.SETTINGS}）が無い")
            return self.finish()
        for where, item, ids in refs:
            if any(not i for i in ids):
                self.violations.append(f"{where}: {item} の {self.column} に空の ID がある（`{base.ID_SEPARATOR}` で区切った間・前後）")
        if self.violations:
            return self.finish()
        ext = self.ext
        repo, name, old = settings[base.SETTING_REPO], settings[base.SETTING_PROFILE], settings[base.SETTING_TAG]
        checked = settings.get(base.SETTING_CHECKED)
        try:
            clone, source = ext.find_clone(repo, self.clone, self.project)
            old_commit = ext.resolve_tag(clone, old)
        except ext.Undetermined as e:
            raise Stop(f"{repo} の profile {name} を読めない: {e}") from None
        # 古い版の層と、指した ID が古い版に在るかは、比べる新しい版が無くても照らす（#1457 の 1 パス目の指摘）
        old_layer = self.layer(clone, old_commit, name, old, missing_ok=False)
        for where, item, ids in refs:
            for rid in ids:
                if rid not in old_layer.rows:
                    self.violations.append(f"{where}: {item} の {self.column} {rid} が {repo} の {name}（タグ {old}）の{base.LAYER}の層に無い"
                                           "（照合の違反——check-infra-profile.py）")
        try:
            new, skipped = (self.new, []) if self.new is not None else self.newest(clone, name, old)
            if skipped:
                self.notes.append(f"名前の形が設定のタグ {old} と違うので新しい版に数えなかった、profile {name} を持つタグ: {', '.join(skipped)}"
                                  "（版の名前の形を変えたなら、設定のタグを上げるか --new で名指す）")
            if new in (old, checked):
                which = base.SETTING_TAG if new == old else base.SETTING_CHECKED
                what = (f"設定のタグ {old} より後ろの、名前の形が同じタグが無い" if new == old and self.new is None
                        else f"新しい版 {new} は設定の{which}と同じ")
                self.notes.append(f"profile: {repo} の {name}——{what}。比べない（clone {clone}（出所: {source}））")
                return self.finish()
            new_commit = ext.resolve_tag(clone, new)
        except ext.Undetermined as e:
            raise Stop(f"{repo} の profile {name} を読めない: {e}") from None
        new_layer = self.layer(clone, new_commit, name, new, missing_ok=True)
        try:
            broken = ext.check_links(clone, new_commit, new_layer) if new_layer is not None else []
        except ext.Undetermined as e:
            raise Stop(f"{repo} の profile {name}（タグ {new}）のリンクを読めない: {e}") from None
        found = candidates(refs, old_layer.rows, new_layer.rows if new_layer is not None else None, broken)
        self.notes.append(f"profile: {repo} の {name}——タグ {old} → {new}"
                          f"{'' if new_layer is not None else f'（{new} に{base.LAYER}の層が無い）'}。clone {clone}（出所: {source}）")
        for where, item, rid, kind, detail in found:
            self.notes.append(f"{CANDIDATE}{where}: {item} の {self.column} {rid}: {kind}（{repo} の {name} タグ {old} → {new}）"
                              f"{'——' + detail if detail else ''}")
        self.notes.append(f"起票の候補 {len(found)} 件（番号は振らない。feasibility が共有の Q&A 表に起票する）")
        self.found = found
        return self.finish()

    def finish(self) -> int:
        code = super().finish()
        return 1 if code or getattr(self, "found", None) else 0


def main(argv: list[str]) -> int:
    args = list(argv)
    named = {"--spec-loop": None, "--clone": None, "--upto": None, "--new": None, "--project": None}
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
        if named["--new"] is not None and (not named["--new"] or named["--new"].startswith("-")):
            raise ValueError("--new にはタグの名前を 1 つ渡す")
        if len(args) != 1 or args[0].startswith("-"):
            raise ValueError(__doc__.splitlines()[2] if __doc__ else
                             f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）")
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    docs = Path(args[0])
    if not docs.is_dir():
        print(f"{docs}: ディレクトリが無い——判定していない", file=sys.stderr)
        return 2
    upto = int(named["--upto"]) if named["--upto"] is not None else None
    project = Path(named["--project"]) if named["--project"] is not None else None
    try:
        spec_loop = base.find_spec_loop(named["--spec-loop"], docs)
        shown = base.check_version(spec_loop)
        differ = Differ(spec_loop, docs, upto, named["--clone"], named["--new"], project)
        print(f"spec-loop {shown}（{spec_loop}）の重ね方と外部の profile の読み方で、profile の版の差分を見る")
        return differ.check()
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
