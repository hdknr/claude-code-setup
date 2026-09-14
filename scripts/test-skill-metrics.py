#!/usr/bin/env python3
"""`skill-metrics.py` 自体のテスト。変異テストを含む。

usage: python3 scripts/test-skill-metrics.py

**実環境を対象にしない。** すべて一時ディレクトリに作った偽のリポジトリに対して走らせ、
**そのことをアサートで担保する**（このリポジトリの既存テストの約束。#57 で、
実環境を触ったサブエージェントが「触っていない」と報告した事故がある）。

## 変異テストで何を見ているか

「落ちるべきときに落ちるか」だけでは足りない。**判定そのものが壊れていたら、
どの入力でも落ちる／落ちない**ので、テストが素通りする。そこで:

- **正常系で通ること**（常に落ちるだけの実装を弾く）
- **変異ごとに落ちること**（常に通るだけの実装を弾く）
- **落ちた理由が変異に対応していること**（メッセージまで見る）

の 3 つを見る。
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "skill-metrics.py"
REPO_ROOT = SCRIPT.parent.parent

SKILL_REL = Path("plugins/dev-loop/skills/dev-loop/SKILL.md")
DOC_REL = Path("docs/plugins/dev-loop-design.md")

BEGIN = "<!-- skill-metrics:begin -->"
END = "<!-- skill-metrics:end -->"

SKILL_BODY = """---
name: sample
---

# サンプル

<!-- skill-version: 1.0.0 -->
> **このスキルの版: 1.0.0**（プラグイン `sample`）。

前書きはここまで。

## 原則

- 何かを守る（必須）。
- もう 1 つ守る。

## サイクル

### 1. 最初

本文。

### 2. 次

**必須**の要件がある。
本文がもう 1 行。
"""

DOC_BODY = f"""# 設計

## 8. コスト

### 8.2 記録 {{ #no-split }}

前置き。

{BEGIN}
{END}

あとがき。
"""

def _snapshot() -> dict[Path, str] | None:
    """実リポジトリの監視対象を控える。**1 つでも読めなければ None。**"""
    paths = (REPO_ROOT / DOC_REL, REPO_ROOT / SKILL_REL)
    if not all(path.is_file() for path in paths):
        return None
    return {path: path.read_text(encoding="utf-8") for path in paths}


# **決め打ちしない。** フィクスチャを直すたびに落ちるテストにしない——
# 実際、`**必須**` を数えるのをやめたときに決め打ちが 3 箇所空振りした
# （空振り検査が捕まえた）。
#
# **マーカーの定義は本体から読む。** ここに `（必須）` と書くと、
# **式がテスト側にも複製される**——本体の `MARKERS` を変えてもテストは
# 古い定義で数え続け、片方だけ緑になる（`diagram_manifest.py` を分けた理由と同じ）。
# ファイル名にハイフンがあるので通常の import はできず、パスから読み込む。
_spec = importlib.util.spec_from_file_location("skill_metrics", SCRIPT)
assert _spec and _spec.loader
_skill_metrics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_skill_metrics)

FIXTURE_MARKERS = sum(SKILL_BODY.count(marker) for marker in _skill_metrics.MARKERS)


def _fixture_sections() -> list[tuple[str, int, int]]:
    """フィクスチャの節を**テスト側で独立に**数える。

    **本体の `sections()` を呼ばない。** 呼ぶと式が変わったときにテストも一緒に変わり、
    退行を検出できなくなる（#50 の協調変異）。ここは素朴に上から数えるだけでよい
    ——フィクスチャは小さく、`##`/`###` しか出てこない。
    """
    lines = SKILL_BODY.rstrip("\n").split("\n")
    heads = [i for i, line in enumerate(lines) if line.startswith(("## ", "### "))]
    out = []
    for k, i in enumerate(heads):
        # **見出し行を含み、次の見出しの直前まで**（末尾の空行も節に属する）。
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        body = "\n".join(lines[i:end])
        name = lines[i].lstrip("# ").strip()
        m = sum(body.count(marker) for marker in _skill_metrics.MARKERS)
        out.append((name, end - i, m))
    return out


_FIXTURE_ROWS = _fixture_sections()
_FIXTURE_TOTAL = len(SKILL_BODY.rstrip("\n").split("\n"))
FIXTURE_TOP2 = [name for name, _, _ in sorted(_FIXTURE_ROWS, key=lambda r: -r[1])[:2]]
FIXTURE_WITHOUT_PCT = "{:.1f}".format(
    sum(n for _, n, m in _FIXTURE_ROWS if not m) / _FIXTURE_TOTAL * 100
)

_REPO_BEFORE = _snapshot()


def _repo_unchanged() -> tuple[bool, str]:
    """(変わっていないか, 理由) を返す。

    **「読めないから OK」を返さない。** 初版は対象が無いとき無条件に True を
    返しており、**スクリプトを別ディレクトリへコピーして走らせると中身を何も
    見ずに合格した**（`/code-review` に指摘されて実測で確認）。
    **「無い」を落とすと検査が消える**——このリポジトリが繰り返し踏んでいる形。

    監視は `DOC` だけでなく **`SKILL.md` も**見る。初版は `DOC` しか見ておらず、
    測定対象を書き換えても気づけなかった。
    """
    if _REPO_BEFORE is None:
        return False, "実リポジトリの監視対象を読めなかった（ガードが空振りしている）"
    after = _snapshot()
    if after is None:
        return False, "実行後に監視対象が読めなくなった"
    for path, before in _REPO_BEFORE.items():
        if after[path] != before:
            return False, f"{path} が変わった"
    return True, ""


failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def make_repo(root: Path) -> None:
    (root / SKILL_REL).parent.mkdir(parents=True, exist_ok=True)
    (root / DOC_REL).parent.mkdir(parents=True, exist_ok=True)
    (root / SKILL_REL).write_text(SKILL_BODY, encoding="utf-8")
    (root / DOC_REL).write_text(DOC_BODY, encoding="utf-8")


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


def _swap_markers(doc: str) -> str:
    """開始と終了のマーカー**行だけ**を入れ替える。

    **生成後のブロックは `BEGIN` と `END` が隣接していない**ので、
    文字列の単純な置換では空振りする——この周で実際に踏んだ
    （空振りしたまま「落ちなかった」と報告され、script のバグかと疑った）。
    """
    lines = doc.split("\n")
    b = next(i for i, line in enumerate(lines) if line.strip() == BEGIN)
    e = next(i for i, line in enumerate(lines) if line.strip() == END)
    lines[b], lines[e] = lines[e], lines[b]
    return "\n".join(lines)


def block_of(root: Path) -> str:
    doc = (root / DOC_REL).read_text(encoding="utf-8")
    return doc[doc.index(BEGIN) : doc.index(END) + len(END)]


def main() -> int:
    print("skill-metrics.py のテスト")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # **実環境を対象にしていないことを担保する。**
        assert not str(root).startswith(str(REPO_ROOT)), (
            f"一時ディレクトリがリポジトリ内にある: {root}"
        )
        assert root.resolve() != REPO_ROOT.resolve()

        make_repo(root)

        # --- 正常系 ---
        print("\n[正常系]")
        result = run(root, "--check")
        check("生成前は --check が落ちる", result.returncode != 0, result.stdout + result.stderr)

        result = run(root)
        check("生成が成功する", result.returncode == 0, result.stderr)

        result = run(root, "--check")
        check("生成後は --check が通る", result.returncode == 0, result.stderr)

        result = run(root)
        check("2 回目の生成は「変更なし」", "変更なし" in result.stdout, result.stdout)

        block = block_of(root)
        # 前書き 9 行（`---` から「前書きはここまで。」の次の空行まで）を含む総行数。
        # **具体値ではなく関係で確かめる**——本文を直すたびに落ちるテストにしない。
        check("総行数が本文と一致", f"は {len(SKILL_BODY.rstrip(chr(10)).splitlines())} 行" in block, block)
        check("節名が入っている", "原則" in block and "1. 最初" in block, block)
        check(
            "マーカー数が入っている",
            f"`（必須）` は {FIXTURE_MARKERS} 個" in block,
            block,
        )
        check("必須を持たない節は — で出る", "| — |" in block, block)

        # **式はここで独立に書き直す。** 本体の関数から期待値を作ると、
        # 式が変わってもテストが一緒に変わって通り続ける（#50 の協調変異）。
        top2 = "と".join(f"「{h}」" for h in FIXTURE_TOP2)

        def named_sections(text: str) -> list[str]:
            """生成文が名指しした節名を取り出す。

            **部分一致で見ない。** 件数を増やす変異は先頭 2 つが一致するので、
            `in` で見ると素通りする（実際にこの周で 1 度素通りさせた）。
            """
            head = re.search(r"行数が最も大きい[^「]*((?:「[^」]+」(?:と)?)+)", text)
            return re.findall(r"「([^」]+)」", head.group(1)) if head else []

        check(
            f"最も大きい 2 節が過不足なく名指しされる（{top2}）",
            named_sections(block) == FIXTURE_TOP2,
            block,
        )
        check(
            f"マーカー無しの割合が出る（{FIXTURE_WITHOUT_PCT}）",
            f"{FIXTURE_WITHOUT_PCT}%" in block,
            block,
        )
        # **節名を 1 つずつ括る。** 区切りが「・」だと、節名自体が「・」を含むときに
        # 境界が消える（実データに「待ち時間・定時処理は別スキル」がある）。
        check("節名が 1 つずつ括られている", "」と「" in block, block)

        # --- 変異: skill-metrics.py 側（生成の式を壊す） ---
        print("\n[変異: 生成の式を壊す]")
        script_src = SCRIPT.read_text(encoding="utf-8")
        formula_mutations = {
            "並び順を逆にする": lambda t: t.replace(
                "key=lambda r: r[1], reverse=True", "key=lambda r: r[1]"
            ),
            "件数を 3 つにする": lambda t: t.replace("ranked[:2]", "ranked[:3]"),
            "割合の分子を取り違える": lambda t: t.replace(
                "{without_marker / total * 100:.1f}", "{with_marker / total * 100:.1f}"
            ),
            "節名を括らない": lambda t: t.replace(
                """"と".join(f"「{head.lstrip('# ').strip()}」" for head, _, _ in top)""",
                """"・".join(head.lstrip("# ").strip() for head, _, _ in top)""",
            ),
        }
        mutant = root / "mutant.py"
        for name, mutate in formula_mutations.items():
            mutated_src = mutate(script_src)
            check(f"{name} → 変異が実際に適用される", mutated_src != script_src)
            mutant.write_text(mutated_src, encoding="utf-8")
            # **生成し直してから、テスト側の期待と突き合わせる。**
            # `--check` は「生成物と再生成が一致するか」しか見ないので、
            # **式の誤りは原理的に検出できない**——ここでしか捕まらない。
            # **`markdown_fences` は `scripts/` にある。** 変異版は一時ディレクトリに
            # 置くので、`PYTHONPATH` で元の場所を渡さないと import で落ちる。
            env = {**os.environ, "PYTHONPATH": str(SCRIPT.parent)}
            result = subprocess.run(
                [sys.executable, str(mutant), "--root", str(root)],
                capture_output=True,
                text=True,
                env=env,
            )
            check(f"{name} → 変異版でも生成は成功する", result.returncode == 0, result.stderr)
            bad = block_of(root)
            wrong = named_sections(bad) != FIXTURE_TOP2 or (
                f"{FIXTURE_WITHOUT_PCT}%" not in bad
            )
            check(f"{name} → 生成物がテスト側の期待とずれる", wrong, bad)
            # 本物で書き戻す（次の変異に持ち越さない）。
            run(root)
        mutant.unlink()

        # --- 変異: SKILL.md 側 ---
        print("\n[変異: SKILL.md を変える]")
        mutations = {
            "行を足す": lambda s: s + "\n追記。\n",
            "（必須）を足す": lambda s: s.replace("- もう 1 つ守る。", "- もう 1 つ守る（必須）。"),
            "（必須）を消す": lambda s: s.replace("- 何かを守る（必須）。", "- 何かを守る。"),
            # **両方向を試す。** 片方だけだと、逆向きの回帰を守れない
            # （Verifier に指摘されて足した）。
            "節を足す": lambda s: s + "\n## 追加の節\n\n本文。\n",
            "節を消す": lambda s: s.replace("## サイクル\n\n", ""),
            "見出しの文言だけ変える": lambda s: s.replace("## 原則", "## 原則（改題）"),
            "前書きに行を足す": lambda s: s.replace("前書きはここまで。", "前書き。\n前書きはここまで。"),
        }
        original = (root / SKILL_REL).read_text(encoding="utf-8")
        for name, mutate in mutations.items():
            mutated = mutate(original)
            # **空振りを黙って通さない。** 3 つの変異ループすべてで同じ検査をする
            # ——最初は 2 つにしか入れておらず、それ自体が
            # 「次元を落とすことで破られる」形だった。
            check(f"{name} → 変異が実際に適用される", mutated != original)
            (root / SKILL_REL).write_text(mutated, encoding="utf-8")
            result = run(root, "--check")
            check(f"{name} → --check が落ちる", result.returncode != 0, result.stdout)
            (root / SKILL_REL).write_text(original, encoding="utf-8")

        # **偽陽性を出さないこと。** 行数もマーカー数も節名も変えない編集では落ちない。
        no_ops = {
            "誤字直し": original.replace("本文。", "本文！"),
            # `**必須**` は**数えない印**である（実 SKILL.md に 0 回しか現れない）。
            # 足しても消しても測定値は動かない——**それを固定する**。
            "**必須** を消す": original.replace("**必須**の要件がある。", "要件がある。"),
            "**必須** を足す": original.replace("本文がもう 1 行。", "本文がもう 1 行（**必須**）。"),
        }
        for name, mutated in no_ops.items():
            check(f"{name} → 変異が実際に適用される", mutated != original)
            (root / SKILL_REL).write_text(mutated, encoding="utf-8")
            result = run(root, "--check")
            check(f"{name} → 落ちない（偽陽性なし）", result.returncode == 0, result.stderr)
            (root / SKILL_REL).write_text(original, encoding="utf-8")

        # --- フェンスの中は数えない ---
        print("\n[コードフェンス]")
        before_block = block_of(root)
        fenced = original + "\n```bash\necho 例（必須）\n```\n\n```markdown\n## 例の節\n```\n"
        (root / SKILL_REL).write_text(fenced, encoding="utf-8")
        run(root)  # 行数が増えるので作り直す
        after_block = block_of(root)
        check(
            "フェンス内の （必須） を数えない",
            f"`（必須）` は {FIXTURE_MARKERS} 個" in after_block,
            after_block,
        )
        check("フェンス内の見出しで幻の節を作らない", "例の節" not in after_block, after_block)
        check("フェンスの外の節は残る", "原則" in after_block and "原則" in before_block)
        (root / SKILL_REL).write_text(original, encoding="utf-8")
        run(root)

        # --- 変異: ドキュメント側 ---
        print("\n[変異: 生成ブロックを触る]")
        doc_original = (root / DOC_REL).read_text(encoding="utf-8")
        doc_mutations = {
            "表の数字を書き換える": lambda s: re.sub(r"\| 原則 \| \d+ \|", "| 原則 | 999 |", s),
            "段落の数字を書き換える": lambda s: s.replace(
                f"は {FIXTURE_MARKERS} 個", "は 99 個"
            ),
            # **行数を決め打ちしない。** 決め打ちは空振りの原因になる
            # （最初 `| 原則 | 6 | 1 |` と書いて、実際は 5 行だったため何も置換されなかった）。
            "行を 1 つ消す": lambda s: re.sub(r"\n\| 原則 \|[^\n]*", "", s),
            "注記を消す": lambda s: s.replace("**手で書き換えない**", ""),
        }
        for name, mutate in doc_mutations.items():
            mutated = mutate(doc_original)
            # **空振りを黙って飛ばさない。** 置換が効かなければ、その変異は
            # 「落ちるか」を何も試していない。飛ばすとテストが嘘をつく
            # （このリポジトリが繰り返し踏んでいる「落とすことで破られる」形）。
            check(f"{name} → 変異が実際に適用される", mutated != doc_original)
            if mutated == doc_original:
                continue
            (root / DOC_REL).write_text(mutated, encoding="utf-8")
            result = run(root, "--check")
            check(f"{name} → --check が落ちる", result.returncode != 0, result.stdout)
            (root / DOC_REL).write_text(doc_original, encoding="utf-8")

        # --- マーカーの扱い ---
        print("\n[マーカー]")
        for name, mutated in {
            "開始マーカーを消す": doc_original.replace(BEGIN + "\n", ""),
            "終了マーカーを消す": doc_original.replace(END + "\n", ""),
            "両方消す": doc_original.replace(BEGIN + "\n", "").replace(END + "\n", ""),
            "開始マーカーを 2 つにする": doc_original.replace(BEGIN, BEGIN + "\n" + BEGIN, 1),
            "順序を逆にする": _swap_markers(doc_original),
        }.items():
            # ここでも空振りを黙って飛ばさない。
            check(f"{name} → 変異が実際に適用される", mutated != doc_original)
            (root / DOC_REL).write_text(mutated, encoding="utf-8")
            result = run(root, "--check")
            check(f"{name} → 落ちる", result.returncode != 0, result.stdout)
            check(
                f"{name} → 理由がマーカーだと分かる",
                "マーカー" in (result.stdout + result.stderr),
                result.stdout + result.stderr,
            )
            (root / DOC_REL).write_text(doc_original, encoding="utf-8")

        # **散文でマーカーに言及しても壊れない**（この周で実際に踏んだ）。
        (root / DOC_REL).write_text(
            doc_original.replace("前置き。", f"前置き。`{BEGIN}` について説明する。"),
            encoding="utf-8",
        )
        result = run(root, "--check")
        check("散文でマーカーに言及しても落ちない", result.returncode == 0, result.stdout + result.stderr)
        (root / DOC_REL).write_text(doc_original, encoding="utf-8")

        # **ドキュメント側のフェンス内にマーカーを例示しても壊れない。**
        # §8.2 は生成ブロックそのものを説明する節なので、例示はありうる。
        (root / DOC_REL).write_text(
            doc_original.replace(
                "前置き。",
                f"前置き。例:\n\n```markdown\n{BEGIN}\n{END}\n```\n",
            ),
            encoding="utf-8",
        )
        result = run(root, "--check")
        check(
            "ドキュメント側のフェンス内の例示で壊れない",
            result.returncode == 0,
            result.stdout + result.stderr,
        )
        (root / DOC_REL).write_text(doc_original, encoding="utf-8")

        # **ドキュメント側の閉じ忘れも落ちる（保護の対称性）。**
        # §8.2 より前でフェンスを閉じ忘れると本物のマーカーごと飲み込まれ、
        # 「消してしまったなら戻すこと」という誤誘導が出ていた。
        (root / DOC_REL).write_text(
            "```bash\necho 閉じ忘れ\n\n" + doc_original, encoding="utf-8"
        )
        result = run(root, "--check")
        check("ドキュメント側の閉じ忘れで落ちる", result.returncode != 0, result.stdout)
        check(
            "落ちた理由がドキュメント側のフェンスだと分かる",
            "フェンス" in (result.stdout + result.stderr)
            and str(DOC_REL) in (result.stdout + result.stderr),
            result.stdout + result.stderr,
        )
        (root / DOC_REL).write_text(doc_original, encoding="utf-8")

        # --- 入力が無い場合 ---
        print("\n[入力が無い]")
        missing = Path(tmp) / "empty"
        missing.mkdir()
        result = run(missing, "--check")
        check("ファイルが無ければ落ちる", result.returncode != 0, result.stdout + result.stderr)

        # **閉じ忘れたフェンスの上では測らない。** 閉じていないと以降の節が
        # 表から消えるので、`--check` の赤／緑より前に落とす
        # （作り直せば緑になってしまうため、鮮度では守れない）。
        unclosed = Path(tmp) / "unclosed"
        (unclosed / SKILL_REL).parent.mkdir(parents=True)
        (unclosed / DOC_REL).parent.mkdir(parents=True)
        (unclosed / DOC_REL).write_text(DOC_BODY, encoding="utf-8")
        (unclosed / SKILL_REL).write_text(
            SKILL_BODY + "\n```bash\necho 閉じ忘れ\n", encoding="utf-8"
        )
        # **「落ちること」だけを見るアサーションはここでは置かない。**
        # フェンスを足せば行数が変わるので、**検出が壊れていても「ブロックが古い」で
        # 必ず落ちる**——判別しないアサーションは、無いのと同じ。
        # （Verifier が `unclosed_fence` を常に `None` に壊して実証した。
        # その後「先に正常生成してから注入する」に変えたが、**それでも判別しなかった**
        # ので、消した。）**判別するのは下の 2 つ**——落ちた理由と、生成側も落ちること。
        result = run(unclosed, "--check")
        check(
            "閉じ忘れなら、落ちた理由がフェンスだと分かる",
            "フェンス" in (result.stdout + result.stderr),
            result.stdout + result.stderr,
        )
        # **生成側でも落ちる。** 検査だけ落として生成が通ると、
        # 「作り直したら緑になった」で誤った表が出荷される。
        result = run(unclosed)
        check("フェンスの閉じ忘れでは生成もしない", result.returncode != 0, result.stdout)

        no_heading = Path(tmp) / "noheading"
        (no_heading / SKILL_REL).parent.mkdir(parents=True)
        (no_heading / DOC_REL).parent.mkdir(parents=True)
        (no_heading / SKILL_REL).write_text("見出しのない本文だけ。\n", encoding="utf-8")
        (no_heading / DOC_REL).write_text(DOC_BODY, encoding="utf-8")
        result = run(no_heading, "--check")
        check("見出しが 1 つも無ければ落ちる", result.returncode != 0, result.stdout + result.stderr)

        # --- 実環境を触っていないことの確認 ---
        print("\n[実環境]")
        unchanged, reason = _repo_unchanged()
        check("リポジトリの監視対象が変わっていない", unchanged, reason)

        # **ガードの陽性側も確かめる。** 上は「変わっていない」しか見ておらず、
        # **変わったときに検出するか**は誰も試していなかった（Verifier が
        # 「追跡ファイルを書き換えられないので読解で代替した」と申告した箇所）。
        # 実ファイルは触らず、**控えた内容のほうを差し替えて**確かめる。
        global _REPO_BEFORE
        saved = _REPO_BEFORE
        try:
            # **空振りを黙って飛ばさない。** `if saved:` だけだと、控えが取れないとき
            # 2 つの check が**一言も出さずに消える**——このファイルが他の 3 ループで
            # 明示的に禁じている形そのものだった（`/code-review` の指摘）。
            check("実環境の控えが取れている", saved is not None, "控えが None")
            if saved:
                _REPO_BEFORE = {path: text + "\n改変" for path, text in saved.items()}
                detected, why = _repo_unchanged()
                check("監視対象が変わったら検出する", not detected, "変化を見逃した")
                check("検出理由にファイル名が出る", "SKILL.md" in why or "design.md" in why, why)
            _REPO_BEFORE = None
            empty, why = _repo_unchanged()
            check("控えが取れていなければ失敗する（空振りしない）", not empty, why)
        finally:
            _REPO_BEFORE = saved

    print()
    if failures:
        print(f"失敗 {len(failures)} 件: " + ", ".join(failures))
        return 1
    print("すべて通った")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
