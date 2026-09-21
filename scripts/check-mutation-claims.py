#!/usr/bin/env python3
r"""「この変異を入れると赤になる」という散文の主張を、機械で当てて確かめる。

    python3 scripts/check-mutation-claims.py          # リポジトリ全体
    python3 scripts/check-mutation-claims.py <root>   # 別のツリー（テスト用）

なぜ必要か（#151）: このリポジトリは**「この行を外すと落ちる」「X を Y にすると赤」を
docstring・計画ファイル・コミットメッセージに書く作法**を持っている。
**だがその主張は、書いた時点から一度も実行されない。**
**設計が変われば黙って偽になる**——**死んだコードについての主張**・
**旧い欠陥を表していない変異**・**単独では挙動が変わらない等価変異**は、
どれも「赤になる」と書かれたまま緑である。

**`scripts/test-*.py` は各テストの中に変異を埋め込んでいる**が、
**埋め込まれていない主張**——とくに**試料そのものについての主張**
（「この試料が無いと、あの変異が殺せない」）——は**どこからも当てられていなかった。**

## マーカーの書式

**散文はそのまま書く。** その隣に、機械が読む 1 行を足す:

```text
mutation-claim: {"file": "scripts/x.py", "old": "a == b", "new": "True", "red": "python3 scripts/test-x.py"}
```

- `file` — 変異を当てるファイル（root からの相対パス）
- `old` — 置き換える文字列。**ちょうど 1 箇所**に現れること。改行は JSON の `\n` で書ける。
  **マーカー自身が載っている行は数えない**ので、`old` に自分の書いた文字列がそのまま
  現れても構わない
- `new` — 置き換え後（空文字列でよい＝削除）
- `red` — 走らせるコマンド。**変異の前は緑、変異の後は赤**でなければならない

**キーはこの 4 つだけ。** 余計なキーがあれば**拒否する**（typo で黙って別の意味にならないため）。
**書式は `dup-counts-ok:` と同じ形**——**行の中に 1 つ置くだけでよく、行末である必要はない。**
**コメント記号や注記で囲っても拾う**（`# … （#151）` も `<!-- … -->` も通る）。

## 判定 — 3 つに分ける

| 判定 | 条件 | 意味 |
| --- | --- | --- |
| **確認** | 陽性対照が緑 → 変異を当てる → **赤** | 主張どおり |
| **緑のまま** | 陽性対照が緑 → 変異を当てる → **緑** | **主張が偽か、変異が届いていない** |
| **当てられなかった** | 上に至らなかった | **緑ではない** |

**「当てられなかった」を緑と混ぜない**のが、この歯止めの要点である。
**#145 の 3 パス目で、`git` に依る検査が退避先で SKIP したのを「変異が届いていない」と読み、
確信をもって誤答した**——**走らなかった検査は緑ではない。**

**確認以外が 1 件でもあれば非ゼロ終了する。**

## 退避先 — リポジトリの外に出す

**複製に `.git` を持ち込まない。** **worktree の `.git` は本体を指す*ファイル***なので、
**素の `cp -R` で複製しても、複製の中の `git` は本物の index・ブランチ・共有 stash を触る**
（#145 の 4 パス目に実物で再現した）。**「外に出したつもりで出ていない」形である。**

だから**`.git` を丸ごと除外して複製し、複製の中に `.git` が 1 つも無いことを確かめてから**
当てる。**原本は 1 バイトも書き換えない。**

## 何を守り、何を守らないか

守る:

- **散文の主張を機械で当てる**——マーカーを収集し、変異を当て、赤になることを要求する。
- **退避先に `.git` を持ち込まない**——複製から除外し、**残っていないことを確かめてから**当てる。
- **陽性対照を必須にする**——**変異の前に緑でなければ「当てられなかった」**。
- **変異はちょうど 1 箇所に当てる**——0 箇所・2 箇所以上は「当てられなかった」。
- **「当てられなかった」を緑と区別する**——確認できたものだけが緑で、欠ければ非ゼロ終了。
- **フェンスの中のマーカーは拾わない**——**書式の例が主張として数えられない**（この docstring 自身がそう）。
- **未知のキーを拒否する**——キー名の typo で黙って別の意味にならない。
- **書き込む先が退避先の内側であることを確かめる**——`file` に `../` を書いても外へ出ない。
- **行のどこに置いたマーカーも拾う**——**行末に注記やコメントの閉じ記号が続いても落とさない。**
- **マーカーに触れているファイルに閉じ忘れたフェンスがあれば、黙って落とさず
  「読めない」と報告する**——**閉じ忘れは以降を全部飲み込むので、
  マーカーが「無かった」ことにされる。**
  **見るのは `mutation-claim:` という語を含むファイルだけ**で、
  **フェンスの平衡を一般に検査するものではない**
  （語に触れただけの散文も、この検査の対象に入る）。
- **マーカー自身の行は、変異の当たり先として数えない**——**マーカーは主張の*記述*であって、
  主張の*対象*ではない。**
- **対象の木が無ければ落とす**——**綴り間違いや置き場所の変更を「主張 0 件」で通さない。**
- **出力が変わらない緑を「主張が偽」と断定しない**——**「当てられなかった」に倒す。**
  **陽性対照は「非ゼロで落ちる SKIP」しか捕まえない。**

守らない:

- **マーカーを書いていない主張は見えない。** **`殺せない` のような決まった言い回しは
  `grep` で数えられるので、「機械で見つけようが無い」わけではない**
  ——**いま印を付けているのはその一部にすぎない。**
  **どれをマーカー化するかは人間が決める。** **この歯止めは網羅性を一切主張しない。**
- **「緑のまま」の理由は決められない。** **検査に穴があるのか、その変異が旧い欠陥を
  表していない（＝届いていない）のか**は区別できない。**`SKILL.md` 手順 5 の
  「緑を砦の穴と読む前に、変異が届いているかを疑う」は、ここでは自動化できない。**
- **`git` に依る主張は当てられない。** 退避先に `.git` が無いので、base を要する検査を
  `red` に置くと**当てられない。** **倒れ方は 2 通りあり、どちらも実測した**——
  `check-version-bump.py` / `check-description-sync.py` は **rc=2 で落ちる**ので
  陽性対照が捕まえ、`check-plan-scope.py` は**「判定していない」と言って rc=0 で終わる**ので
  **陽性対照を通過する。** **後者を捕まえているのは上の「出力が変わらない」のほう**だが、
  **これは*たまたま*出力が一致するから効くのであって、
  「0 で終わる SKIP を一般に見分けられる」わけではない。**
  **黙っては通らないが、当てられもしない。**
- **シェルの機能は使えない。** `red` は `shlex.split` で分割して直接起動する
  （パイプ・リダイレクト・変数展開は無い）。**シェルを噛ませると、書式のミスが
  黙って別の意味になる。**
- **マーカーはリポジトリの中身なので、信頼できる入力として扱っている。**
  **`red` は任意のコマンドを起動する**——**外から持ち込んだツリーに対して回さないこと。**
- **マーカーが 1 件も無い状態は、ここでは緑になる。** 「主張が無い」と「マーカーを消した」を
  区別できないため。**実リポジトリに 1 件以上あることは、回帰テストの側が見る。**

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from markdown_fences import strip_fences, unclosed_fence  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "site", ".venv", "node_modules", "__pycache__", ".claude"}
SUFFIXES = {".md", ".py", ".sh", ".json", ".yml", ".yaml", ".toml"}

# **行末に錨を打たない。** 打つと、**注記やコメントの閉じ記号が 1 つ続いただけで
# マーカーが黙って消える**——**しかも「壊れている」ですらなく「無かった」になる。**
# **`dup-counts-ok:` も錨を持たない**ので、書式を揃える意味でもこちらが正しい。
# **末尾に `}` を含む注記が続いた場合は貪欲一致が行きすぎて JSON が壊れる**が、
# **そのときは「読めない」として報告される**（黙って消えるのとは違う）。
MARKER = re.compile(r"mutation-claim:\s*(\{.*\})")
KEYS = {"file", "old", "new", "red"}

TIMEOUT = 300

VERIFIED = "確認"
STILL_GREEN = "緑のまま"
NOT_APPLIED = "当てられなかった"


class Claim:
    def __init__(self, source: str, lineno: int, spec: dict):
        self.source = source
        self.lineno = lineno
        self.file = spec["file"]
        self.old = spec["old"]
        self.new = spec["new"]
        self.red = spec["red"]

    @property
    def where(self) -> str:
        return f"{self.source}:{self.lineno}"


def targets(root: pathlib.Path):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file() and path.suffix in SUFFIXES:
            yield rel, path


def collect(root: pathlib.Path) -> tuple[list[Claim], list[tuple[str, str]]]:
    """マーカーを集める。(読めた主張, (場所, 理由) の並び) を返す。

    **フェンスの中は拾わない。** 書式を例示しているだけの行を主張として数えると、
    **この docstring 自身が主張になる。**
    """
    claims: list[Claim] = []
    broken: list[tuple[str, str]] = []
    for rel, path in targets(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # **閉じ忘れたフェンスは、以降を全部飲み込む**（`markdown_fences` の docstring）。
        # **そのファイルにマーカーが書かれているなら、どれが生きているか決められない**
        # ので、**黙って 0 件にせず「読めない」と言う。**
        # **マーカーを一切含まないファイルには口を出さない**——ここは
        # フェンスの閉じ忘れ一般を見る検査ではない。
        if "mutation-claim:" in text:
            fence = unclosed_fence(text)
            if fence is not None:
                broken.append((str(rel),
                               f"閉じ忘れたフェンス（{fence}）がある。"
                               "以降のマーカーが飲み込まれるので判定できない"))
                continue
        for lineno, line in enumerate(strip_fences(text).split("\n"), 1):
            m = MARKER.search(line)
            if not m:
                continue
            where = f"{rel}:{lineno}"
            try:
                spec = json.loads(m.group(1))
            except json.JSONDecodeError as exc:
                broken.append((where, f"JSON として読めない: {exc}"))
                continue
            if not isinstance(spec, dict):
                broken.append((where, "オブジェクトではない"))
                continue
            missing = KEYS - set(spec)
            unknown = set(spec) - KEYS
            if missing or unknown:
                # **未知のキーを拒否する。** `red` を `redd` と書いた主張が、
                # **「`red` が無い」ではなく「黙って別の意味」になってはならない。**
                detail = []
                if missing:
                    detail.append(f"足りないキー: {sorted(missing)}")
                if unknown:
                    detail.append(f"知らないキー: {sorted(unknown)}")
                broken.append((where, "／".join(detail)))
                continue
            if not all(isinstance(spec[k], str) for k in KEYS):
                broken.append((where, "値が文字列でない"))
                continue
            claims.append(Claim(str(rel), lineno, spec))
    return claims, broken


def _ignore(_dir, names):
    return [n for n in names if n in SKIP_DIRS]


def make_sandbox(root: pathlib.Path) -> pathlib.Path:
    """`.git` を持ち込まずに退避先を作る。**原本の外**であることまで確かめる。

    **`assert` を使わない。** `python3 -O` では `assert` が消えるので、
    **退避先を作って書き込み、任意のコマンドを走らせる歯止めの安全弁**が
    実行の仕方ひとつで無くなってしまう。
    """
    box = pathlib.Path(tempfile.mkdtemp(prefix="mutation-claims-")).resolve()
    real_root = root.resolve()
    # **退避先が原本の内側にあってはならない。** 内側だと、原本の側の検査や
    # `git` が複製を拾いうる。
    if box == real_root or str(box).startswith(str(real_root) + "/"):
        raise RuntimeError(f"退避先が原本の内側にある: {box}")
    shutil.copytree(real_root, box, dirs_exist_ok=True, symlinks=True, ignore=_ignore)
    # **`.git` が 1 つも無いことを確かめる。** worktree の `.git` は本体を指す
    # *ファイル*なので、残っていれば複製の中の `git` が本物を触る。
    leftover = list(box.rglob(".git"))
    if leftover:
        raise RuntimeError(f"退避先に .git が残っている: {leftover[:3]}")
    return box


def run(command: str, cwd: pathlib.Path) -> tuple[int | None, str]:
    """`red` を走らせる。**シェルは噛ませない。** タイムアウトは `None` を返す。"""
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return None, f"コマンドを分割できない: {exc}"
    if not argv:
        return None, "コマンドが空"
    # **バイトコードを残さない。** 退避先は主張をまたいで使い回すので、
    # **変異 → 復元が同じ秒に収まると、復元後も変異後の `.pyc` が残りうる**
    # （CPython は mtime の秒とサイズで妥当性を見る）。
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                              check=False, timeout=TIMEOUT, env=env)
    except FileNotFoundError:
        return None, f"コマンドが見つからない: {argv[0]}"
    except subprocess.TimeoutExpired:
        return None, f"{TIMEOUT} 秒で打ち切った"
    return proc.returncode, (proc.stdout + proc.stderr)


def _marker_spans(text: str) -> list[tuple[int, int]]:
    """マーカーが載っている行の範囲（開始, 終了）を返す。"""
    spans = []
    pos = 0
    for line in text.split("\n"):
        if "mutation-claim:" in line:
            spans.append((pos, pos + len(line)))
        pos += len(line) + 1
    return spans


def occurrences(text: str, old: str) -> list[int]:
    """`old` の出現位置。**マーカー自身の行に載っているものは数えない。**

    **マーカーは主張の*記述*であって、主張の*対象*ではない。** 数えてしまうと、
    **`old` に自分が書いた文字列がそのまま現れる主張**——たとえば同じファイルの
    中の行を指す主張——が、**常に「2 箇所にある」で弾かれる。**
    """
    spans = _marker_spans(text)
    out = []
    i = text.find(old)
    while i != -1:
        if not any(start <= i < end for start, end in spans):
            out.append(i)
        i = text.find(old, i + 1)
    return out


def judge(claim: Claim, box: pathlib.Path, baselines: dict) -> tuple[str, str]:
    """1 件の主張を判定して (判定, 理由) を返す。"""
    target = (box / claim.file).resolve()
    # **書き込む先が退避先の内側か。** `file` に `../` を書いても外へ出さない。
    if target != box and not str(target).startswith(str(box) + "/"):
        return NOT_APPLIED, f"`file` が退避先の外を指している: {claim.file}"
    if not target.is_file():
        return NOT_APPLIED, f"`file` が無い: {claim.file}"
    try:
        original = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return NOT_APPLIED, f"`file` を読めない: {exc}"

    at = occurrences(original, claim.old)
    if len(at) != 1:
        return NOT_APPLIED, (f"`old` が {len(at)} 箇所にある"
                             "（マーカー自身の行を除いて、ちょうど 1 箇所を要求する）")

    # **陽性対照。** 変異の前に緑でなければ、その後の緑には意味が無い。
    if claim.red not in baselines:
        baselines[claim.red] = run(claim.red, box)
    base_rc, base_out = baselines[claim.red]
    if base_rc != 0:
        tail = base_out.strip().splitlines()[-1:]
        why = f"（変異の前から緑でない: rc={base_rc}）"
        return NOT_APPLIED, "陽性対照が通らない" + why + (f": {tail[0]}" if tail else "")

    cut = at[0]
    mutated = original[:cut] + claim.new + original[cut + len(claim.old):]
    target.write_text(mutated, encoding="utf-8")
    try:
        rc, out = run(claim.red, box)
    finally:
        target.write_text(original, encoding="utf-8")

    if rc is None:
        return NOT_APPLIED, "変異を当てた側が走らなかった"
    if rc != 0:
        return VERIFIED, f"陽性対照 rc=0 → 変異 rc={rc}"
    # **出力が 1 バイトも変わらないなら、「主張が偽」と断定してはならない。**
    # **陽性対照は「非ゼロで落ちる SKIP」しか捕まえない**——**0 で終わる SKIP**
    # （`check-plan-scope.py` は base が解決できないと「判定していない」と言って 0 で終わる）
    # **は素通りする。** そのとき変異の前後で出力は完全に同じになる。
    # **ここで「緑のまま＝主張が偽」と書くと、走らなかった検査を
    # 「変異が届いていない」と読む #145 の 3 パス目の誤読を、この歯止め自身が出力する。**
    if out == base_out:
        return NOT_APPLIED, ("変異の前後で出力が 1 バイトも変わらない"
                             "（検査がその変異を見ていない——走らなかった可能性がある）")
    return STILL_GREEN, "変異を当てても rc=0 のまま（主張が偽か、変異が届いていない）"


def main(argv=None) -> int:
    root = pathlib.Path(argv[0]) if argv else REPO_ROOT
    # **綴り間違いや置き場所の変更を「主張 0 件」で通さない。**
    if not root.is_dir():
        print(f"ERROR: 対象の木が無い: {root}", file=sys.stderr)
        return 1
    claims, broken = collect(root)

    results: list[tuple[Claim, str, str]] = []
    if claims:
        box = make_sandbox(root)
        try:
            baselines: dict[str, tuple[int | None, str]] = {}
            for claim in claims:
                verdict, reason = judge(claim, box, baselines)
                results.append((claim, verdict, reason))
        finally:
            shutil.rmtree(box, ignore_errors=True)

    counts = {VERIFIED: 0, STILL_GREEN: 0, NOT_APPLIED: len(broken)}
    for _, verdict, _ in results:
        counts[verdict] += 1

    for claim, verdict, reason in results:
        print(f"  {verdict:<8} {claim.where} → {claim.file}: {reason}")
    for where, reason in broken:
        print(f"  {NOT_APPLIED:<8} {where}: マーカーを読めない（{reason}）")

    total = len(claims) + len(broken)
    print(f"変異の主張: {total} 件"
          f"（{VERIFIED} {counts[VERIFIED]} / "
          f"{STILL_GREEN} {counts[STILL_GREEN]} / "
          f"{NOT_APPLIED} {counts[NOT_APPLIED]}）")

    if counts[STILL_GREEN] or counts[NOT_APPLIED]:
        print("ERROR: 確認できなかった主張がある（#151）。", file=sys.stderr)
        print(f"ERROR: **「{NOT_APPLIED}」は緑ではない。** "
              "走らなかった検査を「変異が届いていない」と読まないこと。", file=sys.stderr)
        return 1
    if total == 0:
        print("**マーカーが 1 件も無い。** 「主張が無い」のか「消した」のかは、ここでは分からない。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
