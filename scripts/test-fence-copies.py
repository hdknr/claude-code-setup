#!/usr/bin/env python3
r"""コードブロック（フェンス）と HTML コメントの読み方の写し 3 つを、同じ試料の表で突き合わせる（#758・#759・#760）。

    python3 scripts/test-fence-copies.py

## なぜ在るのか

同じ規則の写しが 3 つある:

| 写し | 読むもの | 読み口 |
| --- | --- | --- |
| `plugins/dev-loop/skills/cruise/scripts/run-serial.py` | `.claude/dev-loop.md` の `並行の検査:` | `declaration` → `declared_lines` |
| `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` | 同じ `.claude/dev-loop.md` の `cruise の操作:` ほか | `read_dev_loop_md` → `visible_lines` |
| `plugins/dev-loop/skills/cruise/scripts/parent-issue.py` | 親 Issue の本文のチェックリスト | `read_body` → `visible_lines` |

#739 の周（PR #757）で run-serial を CommonMark に合わせたとき、残る 2 つは古い読み方のまま食い違った——
同じ `.claude/dev-loop.md` を、run-serial は宣言 2 つと読み、check-unattended-env は 0 と読む形があった（#759・#760）。

**1 つのモジュールにまとめず、写しのままここで突き合わせる。** 3 つはプラグインのキャッシュから単独で動く（cruise から dev-loop は
`../` で指せるが、run-serial は重い検査すべての入口で、読み込みの失敗が全部の検査を止める）。parent-issue の読み方は、
チェックリストの行が段落を切るので意図して違える箇所があり、GitHub の描画と合わないまま後続の Issue に回した箇所もある
（どちらも parent-issue の `visible_lines` の docstring が挙げる。表の parent-issue の列）。
各写しの回帰テストは自分の本体の文字列を壊して当てる（変異テスト）ので、本体を動かすと 3 本の変異が全部付け替えになる。

## 何をするか

試料ごとに、各写しの宣言の行（run-serial: `並行の検査: 3`、check-unattended-env: `cruise の操作: gh pr merge`、
parent-issue: `- [ ] #12`）を `{D}` に入れてファイルに書き、**各写しの本物の読み口**で読んで、宣言の行が見えるかを期待値と比べる。
**期待値は試料ごとに 1 つ**で、parent-issue だけ違えてよい試料は、表に parent-issue の値と理由を書く。理由は
parent-issue の `visible_lines` の docstring が挙げるものだけで、docstring に無い理由は落ちる。

**陽性対照**: 壊さない写しで全部の判定が緑であることを先に見る。続けて各写しを一時ディレクトリに写し、
#758・#759・#760 が名指しした食い違い（写しが古いまま残った形）を 1 つずつ戻して、**その写しの判定が 1 つ以上落ちる**ことを見る。

## 守る／守らない

守る:
- 3 つの写しが、表の試料で期待値（parent-issue は違えてよい試料の値）と同じに読む
- parent-issue だけ違えてよい理由は、parent-issue の docstring が挙げるものに限る
- 写しの 1 つを古い読み方に戻すと落ちる（陽性対照）
- 実リポジトリのファイルを書かない（試料は一時ディレクトリに書き、写しは読み込むだけ）

守らない:
- 表に無い形——表は #739・#743・#745・#758・#759・#760 で名指しされた形と、その陰性・陽性の対で、CommonMark の全部ではない
- 宣言の行の書式の違い（`並行の検査:` の値の検査・`cruise の操作` の崩れた行）——それぞれの回帰テストが見る
- 各写しの回帰テストの代わり——ここは読み方の一致だけを見る

標準ライブラリのみ。
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parents[1]
PLUGIN = REAL_REPO / "plugins" / "dev-loop" / "skills"
COPIES = {
    "run-serial": PLUGIN / "cruise" / "scripts" / "run-serial.py",
    "check-unattended-env": PLUGIN / "dev-loop" / "scripts" / "check-unattended-env.py",
    "parent-issue": PLUGIN / "cruise" / "scripts" / "parent-issue.py",
}
DECL = {"run-serial": "並行の検査: 3", "check-unattended-env": "cruise の操作: gh pr merge", "parent-issue": "- [ ] #12"}

# parent-issue だけ違えてよい理由（parent-issue.py の `visible_lines` の docstring にある語句）
INDENT = "開きの字下げを数えない"
DEPTH = "閉じの深さを開きの幅から数える"
INLINE = "行の途中で同じ行に閉じない `<!--` を文字と読む"
CLOSING = "行頭のコメントを閉じる行の `-->` の後ろを読まない"

# (試料, 宣言が見えるか, parent-issue だけ違えるなら (値, 理由))
SAMPLES = {
    "宣言だけ": ("{D}", True, None),
    "コードブロックの中": ("```\n{D}\n```", False, None),
    "~~~ のコードブロックの中": ("~~~\n{D}\n~~~", False, None),
    # 閉じ行（#740・#741・#743・#745・#759・#760）
    "空白 4 つで字下げした閉じ行": ("```\n    ```\n{D}\n```", False, None),
    "別の文字の閉じ行": ("```\n~~~\n{D}\n```", False, None),
    "タブで字下げした閉じ行": ("```\n\t```\n{D}\n```", False, None),
    "全角の空白で字下げした閉じ行": ("```\n\u3000```\n{D}\n```", False, None),
    "空白 3 つで字下げした閉じ行": ("```\n   ```\n{D}", True, None),
    "開いた印と同じ数の閉じ行": ("````\n````\n{D}", True, None),
    "開いた印より短い閉じ行": ("````\n```\n{D}\n````", False, None),
    "後ろに文字のある閉じ行": ("```\n``` x\n{D}\n```", False, None),
    "後ろに空白とタブのある閉じ行": ("```\n```  \t\n{D}", True, None),
    "後ろに全角の空白のある閉じ行": ("```\n```\u3000\n{D}\n```", False, None),
    "後ろに \\x0b のある閉じ行": ("```\n```\x0b\n{D}\n```", False, None),
    "後ろに \\x0c のある閉じ行": ("```\n```\x0c\n{D}\n```", False, None),
    # 行の分け方（改行でだけ分ける）
    "\\x0b の後ろの宣言": ("```\n```\x0b{D}\n```", False, None),
    "\\x0c の後ろの宣言": ("```\n```\x0c{D}\n```", False, None),
    "\\u2028 の後ろの宣言": ("```\n```\u2028{D}\n```", False, None),
    "\\r で分けた閉じ行": ("```\r```\r{D}", True, None),
    # 開き行
    "全角の空白で字下げした印": ("\u3000```\n{D}\n\u3000```", True, None),
    "バッククォートを含む情報文字列": ("```a`b\n{D}", True, None),
    "~~~ の情報文字列のバッククォート": ("~~~a`b\n{D}\n~~~", False, None),
    "行の途中の印": ("メモ ```\n{D}", True, None),
    "空白 4 つで字下げした印": ("    ```\n{D}", True, (False, INDENT)),
    "タブで字下げした印": ("\t```\n{D}\n\t```", True, (False, INDENT)),
    "空白 2 つで開き、5 つで字下げした閉じ行": ("  ```\n     ```\n{D}\n```", False, (True, DEPTH)),
    # コメントと開き行（#739・#758・#759）
    "行頭のコメントの中の印": ("<!--\n```\n-->\n{D}", True, None),
    "コメントの中で閉じる行の印": ("<!--\n```-->\n{D}", True, None),
    "コメントの後ろの印": ("<!-- -->```\n{D}", True, None),
    "コメントで区切ったバッククォートの情報文字列": ("```a<!--`-->\n{D}", True, None),
    "情報文字列の <!--": ("```<!--\n-->\n{D}\n```", False, None),
    "情報文字列の <!-- で始めたコードブロックの後ろ": ("```<!--\n```\n{D}", True, None),
    "行末のコメント": ("{D} <!-- メモ -->", True, None),
    "行頭のコメントの中": ("<!--\n{D}\n-->", False, None),
    "段落の中のコメントの後ろの印": ("memo <!--\n```\n-->\n{D}", False, None),
    # GitHub の描画（`gh api -X POST /markdown`。2026-11-01）: 宣言の行は段落の続きで隠れ、チェックリストの行は段落を切って見える
    "段落の中で閉じないコメント": ("memo <!--\n{D}\n-->", False, (True, INLINE)),
    # GitHub の描画では宣言の行もチェックリストの行も隠れる——parent-issue が読むのは parent-issue の不具合で、後続の Issue で直す
    # （#758 の周で見つけた。ここは今の写しの読み方を固定しているだけで、正しいと言っていない）
    "閉じたコメントの後ろで開き直したコメント": ("<!-- a --> b <!--\n{D}\n-->", False, (True, INLINE)),
    # #758 の周の /code-review 1 パス目。GitHub の描画: 1 つ目は ` x ` だけで後ろを隠す・2 つ目は宣言が見える・3 つ目は宣言が <pre> の中
    # （1 つ目・2 つ目の parent-issue の読み方は GitHub と合わない——後続の Issue で直す。ここは今の読み方を固定しているだけ）
    "行頭のコメントを閉じた行で開き直したコメント": ("<!--\n--> x <!--\n```\n```\n{D}\n-->", False, (True, CLOSING)),
    "行頭のコメントを閉じた行の後ろの宣言": ("<!--\nx -->{D}", True, (False, CLOSING)),
    "段落の中のコメントを閉じた行で開き直したコメント": ("memo <!--\nfoo --> x <!--\n```\n{D}\n```", False, None),
    # #758 の周の /code-review 2 パス目。GitHub の描画: 1・2 つ目は宣言が見える（コードブロックが段落の中のコメントを終わらせる）、
    # 3〜5 つ目は後ろを隠す（行頭のコメント・リストや引用の印の直後のコメント）。parent-issue の 3〜5 つ目は GitHub と合わない——後続の Issue
    "段落の中のコメントの後ろの閉じたコードブロック": ("memo <!--\n```\n```\n{D}", True, None),
    "段落の中のコメントを閉じた行で開き直し、閉じたコードブロック": ("memo <!--\nfoo --> x <!--\n```\n```\n{D}", True, None),
    "閉じたコメントの後ろで開き直したコメントの中のコードブロック": ("<!-- a --> b <!--\n```\n```\n{D}\n-->", False, (True, INLINE)),
    "リストの印の直後のコメント": ("- <!--\n```\n```\n{D}\n-->", False, (True, INLINE)),
    "引用の印の直後のコメント": ("> <!--\n```\n```\n{D}\n-->", False, (True, INLINE)),
    # BOM（読み口ごと。check-unattended-env は読む側で外す）
    "先頭の BOM": ("\ufeff{D}", True, None),
    "BOM が 2 つ": ("\ufeff\ufeff{D}", False, None),
}

# 写しが古い読み方のまま残った形（#758・#759・#760 が名指ししたもの）。(探す文字列, 置き換え)
DRIFTS = {
    "run-serial": {
        "改行以外でも行を分ける": (
            "    for line in NEWLINE.split(text.removeprefix(\"\\ufeff\")):",
            "    for line in text.removeprefix(\"\\ufeff\").splitlines():"),
        "続く BOM も外す": (
            "    for line in NEWLINE.split(text.removeprefix(\"\\ufeff\")):",
            "    for line in NEWLINE.split(text.lstrip(\"\\ufeff\")):"),
        "段落の中のコメントの後ろの印で始めない": (
            "        opened = None if comment and not inline else opens(line)",
            "        opened = None if comment else opens(line)"),
        "閉じ行の後ろの全角の空白を許す": (
            "    return run >= width and not body[run:].strip(\" \\t\")",
            "    return run >= width and not body[run:].strip()"),
        "開き直したコメントの種類を行頭かだけで決める": (
            "                    inline = inline if started else not COMMENT_BLOCK.match(line)",
            "                    inline = not COMMENT_BLOCK.match(line)"),
        "リストや引用の印の後ろのコメントを段落の中と読む": (
            "COMMENT_BLOCK = re.compile(r\"(?: {0,3}(?:[-*+]|[0-9]{1,9}[.)])[ \\t]+| {0,3}>[ \\t]?)* {0,3}<!--\")",
            "COMMENT_BLOCK = re.compile(r\" {0,3}<!--\")"),
    },
    "check-unattended-env": {
        "改行以外でも行を分ける": (
            "    for line in NEWLINE.split(text):",
            "    for line in text.splitlines():"),
        "開き行をコメントを外した残りで見る": [  # 旧い visible_lines に寄せた形: 元の行では見ず、コメントを外した残りで見る（旧い字下げ `\s*` と、コメントの中で終わる行の扱いは戻していない）
            ("        opened = None if comment and not inline else opens(line)", "        opened = None"),
            ("        yield kept\n",
             "        if not comment and opens(kept):\n            fence = opens(kept)\n            continue\n        yield kept\n")],
        "字下げをタブ・全角の空白でも数える": (
            "    body = line.lstrip(\" \")",
            "    body = line.lstrip()"),
        "閉じ行の後ろの全角の空白を許す": (
            "    return run >= width and not body[run:].strip(\" \\t\")",
            "    return run >= width and not body[run:].strip()"),
        "段落の中のコメントの後ろの印で始めない": (
            "        opened = None if comment and not inline else opens(line)",
            "        opened = None if comment else opens(line)"),
        "開き直したコメントの種類を行頭かだけで決める": (
            "inline = inline if started else not COMMENT_BLOCK.match(line)",
            "inline = not COMMENT_BLOCK.match(line)"),
        "リストや引用の印の後ろのコメントを段落の中と読む": (
            "COMMENT_BLOCK = re.compile(r\"(?: {0,3}(?:[-*+]|[0-9]{1,9}[.)])[ \\t]+| {0,3}>[ \\t]?)* {0,3}<!--\")",
            "COMMENT_BLOCK = re.compile(r\" {0,3}<!--\")"),
    },
    "parent-issue": {
        "改行以外でも行を分ける": (
            "NEWLINE.split(body.removeprefix(\"\\ufeff\"))",
            "body.removeprefix(\"\\ufeff\").splitlines()"),
        "BOM を外さない": (
            "NEWLINE.split(body.removeprefix(\"\\ufeff\"))",
            "NEWLINE.split(body)"),
        "字下げを全角の空白でも数える": (
            "(?P<indent>[ \\t]*)",
            "(?P<indent>\\s*)"),
        "閉じ行の後ろの全角の空白を許す": (
            "and not m.group(\"info\").strip(\" \\t\") and",
            "and not m.group(\"info\").strip() and"),
        # #760 が名指しした残りの 3 形（parent-issue は前から守っていたので「戻す」先は無いが、崩した形で落ちることを見る）
        "タブを 1 桁と数える": (
            "    return len(indent.expandtabs(4))",
            "    return len(indent)"),
        "バッククォートを含む情報文字列でも開く": (
            "    if not m or (m.group(\"fence\")[0] == \"`\" and \"`\" in m.group(\"info\")):",
            "    if not m:"),
        "開き行をコメントを外した残りで見る": (
            "        opened = None if in_comment else opens(line)",
            "        opened = None if in_comment else opens(visible(line, in_comment)[0])"),
    },
}

failures: list[str] = []


def check(name: str, cond: bool, sink: list[str] | None = None, quiet: bool = False) -> None:
    if not quiet:
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        (failures if sink is None else sink).append(name)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(f"fence_copies_{name.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_repo(path: Path) -> None:
    assert REAL_REPO.resolve() not in [path.resolve(), *path.resolve().parents], f"実リポジトリを対象にしている: {path}"


def read(copy: str, mod, root: Path, text: str) -> list[str]:
    """写し `copy` の本物の読み口で `text` を読み、宣言として読む行（コメントを外した残り）を返す。"""
    assert_not_real_repo(root)
    (root / ".git").mkdir(parents=True)
    (root / ".claude").mkdir()
    (root / ".claude" / "dev-loop.md").write_bytes(text.encode("utf-8"))
    if copy == "run-serial":
        body, said = mod.declaration(root / ".git")
        assert said is None, said
        return mod.declared_lines(body)
    if copy == "check-unattended-env":
        return list(mod.visible_lines(mod.read_dev_loop_md(root)))
    found = []
    try:
        for _, line in mod.visible_lines(mod.read_body(None, str(root / ".claude" / "dev-loop.md"), root)):
            found.append(line)
    except mod.Refused:
        pass  # 閉じていないフェンス・コメントは拒む——それまでに出した行が読んだ行
    return found


def expected(copy: str, label: str) -> bool:
    _, seen, pi = SAMPLES[label]
    return pi[0] if copy == "parent-issue" and pi else seen


def judge(copy: str, mod, tmp: Path, tag: str, sink: list[str] | None = None, quiet: bool = False) -> None:
    for i, (label, (template, _, _)) in enumerate(SAMPLES.items()):
        decl = DECL[copy]
        lines = read(copy, mod, tmp / f"{tag}-{i}", template.replace("{D}", decl))
        got = any(line.strip() == decl for line in lines)
        want = expected(copy, label)
        check(f"{copy}: {label}: {'見える' if want else '見えない'}", got == want, sink, quiet)


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        assert_not_real_repo(tmp)
        mods = {copy: load(copy, path) for copy, path in COPIES.items()}

        print("3 つの写しを同じ試料の表で読む（壊さない写し）")
        for copy, mod in mods.items():
            judge(copy, mod, tmp, f"ok-{copy}")

        print("\nparent-issue だけ違えてよい理由は、parent-issue の visible_lines の docstring にある")
        doc = mods["parent-issue"].visible_lines.__doc__ or ""
        for reason in sorted({pi[1] for _, _, pi in SAMPLES.values() if pi}):
            check(f"「{reason}」", reason in doc)

        print("\n陽性対照: 写しの 1 つを古い読み方に戻すと、その写しの判定が落ちる")
        for copy, drifts in DRIFTS.items():
            source = COPIES[copy].read_text(encoding="utf-8")
            for i, (name, pairs) in enumerate(drifts.items()):
                pairs = pairs if isinstance(pairs, list) else [pairs]
                missing = [needle for needle, _ in pairs if source.count(needle) != 1]
                if missing:
                    check(f"{copy}: 戻す先がそれぞれ 1 か所ある: {name}", False)
                    continue
                text = source
                for needle, replacement in pairs:
                    text = text.replace(needle, replacement, 1)
                mdir = tmp / f"drift-{copy}-{i}"
                mdir.mkdir()
                mutated = mdir / COPIES[copy].name
                mutated.write_text(text, encoding="utf-8")
                fell: list[str] = []
                try:
                    judge(copy, load(f"{copy}_{i}", mutated), tmp, f"m-{copy}-{i}", fell, quiet=True)
                except Exception as exc:  # 例外は判定の失敗ではない——落ちたと数えず、当てられなかったとして落とす
                    check(f"{copy}: 戻した写しを当てられた: {name}（{exc.__class__.__name__}）", False)
                    continue
                check(f"{copy}: {name}" + (f"（落ちた判定 {len(fell)} 件。最初: {fell[0]}）" if fell else ""), bool(fell))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO / "x")
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("フェンスの読み方の写しの突き合わせ: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
