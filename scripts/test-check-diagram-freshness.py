#!/usr/bin/env python3
"""scripts/check-diagram-freshness.py の回帰テスト。

    python3 scripts/test-check-diagram-freshness.py

なぜ必要か（#50）: 図の鮮度チェックは**歯止め**であって機能ではない。歯止めは
「置いてあるが何も見ていない」形で死ぬ——**しかも死んだことは緑でしか現れない**。
`check-plugin-versions.py` の周（#62 / #63）で、同じ形の穴が値・キー・収集・テストの各次元で
繰り返し見つかった。だからここでは:

1. **各経路に否定テストを置く**（落ちること）
2. **期待した理由で落ちたことまで見る**（`check_rejected`）——終了コードだけを見ると
   **クラッシュも合格になる**
3. **変異させて、対応するテストが実際に落ちること**を確かめる（末尾の `check_mutations`）。
   変異が生き残るテストは、その分岐を固定できていない

**指紋の式はここで独立に書き直している**（`fp`）。`diagram_manifest.fingerprint` を
import して期待値を作ると、**式が変わってもテストは一緒に変わって通り続ける**——
`scale` を式から落とす退行（#50 のレビューで指摘された経路）がまさにそれで、
共有実装を呼んでいる限り検出できない。**式は 2 度書くのが正しい**数少ない場所である。

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリを作り、そこだけを対象にする。
実リポジトリを対象にしてしまうテストは**実行前にアサートで落とす**
（`test-link-skills.py` / `test-check-plugin-versions.py` と同じ設計方針）。

標準ライブラリのみ。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-diagram-freshness.py"
SHARED = REPO_ROOT / "scripts" / "diagram_manifest.py"

# 実リポジトリ。ここを対象にしてしまうテストは実行前に落とす。
REAL_REPO = REPO_ROOT.resolve()

SRC_ONE = "<mxfile>one</mxfile>\n"
SRC_TWO = "<mxfile>two</mxfile>\n"
OUT_ONE = "docs/images/one.svg"
OUT_TWO = "docs/images/two.png"

# 変異テスト中だけ、偽リポジトリにコピーする中身を差し替える（末尾を参照）。
# 収集規則は共有モジュール側にあるので、**どちらのファイルも**変異させられる必要がある。
_MUTATED: dict[str, str] = {}

failures: list[str] = []
checks = 0


def check(condition: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def check_rejected(proc: subprocess.CompletedProcess[str], expected: str, label: str) -> None:
    """「落ちること」だけでなく、**期待した理由で落ちたこと**まで見る。

    終了コードだけを見ると**クラッシュも合格になる**。`check-plugin-versions.py` の周では、
    そのせいで 22 件の変異がすべてテストを通り抜けた。否定側は全部これを使う。

    **クラッシュも明示的に落とす。** 素の例外で終わると非ゼロにはなるが、理由が読めない
    ——「落ちた」だけを見ていると、診断が消えた退行を合格と数える。
    """
    check(proc.returncode != 0, f"{label}（落ちなかった）", proc.stdout)
    check(
        "Traceback" not in proc.stderr,
        f"{label}（診断ではなくクラッシュで落ちた）",
        proc.stderr[-400:],
    )
    check(
        expected in proc.stdout,
        f"{label}（落ちたが理由が違う。期待: {expected!r}）",
        (proc.stdout + proc.stderr)[-400:],
    )


def fp(source_text: str, output: str, scale: object = None) -> str:
    """`diagram_manifest.fingerprint` と**同じ式を独立に**書いたもの（上の docstring を参照）。"""
    digest = hashlib.sha256()
    digest.update(source_text.encode("utf-8"))
    digest.update(b"\0")
    digest.update(output.encode("utf-8"))
    digest.update(b"\0")
    digest.update(repr(scale).encode("utf-8"))
    return digest.hexdigest()


def build(
    root: Path,
    *,
    manifest: object,
    sources: dict[str, str],
    outputs: dict[str, str],
    extra_files: dict[str, str] | None = None,
    setup=None,
) -> None:
    """偽リポジトリを組み立てる。

    `manifest` は dict なら JSON として書き出し、str ならそのまま書く（壊れた JSON の検査用）。
    `None` を渡すとマニフェストを置かない。
    """
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの作業ディレクトリが実リポジトリの内側にある"
    )

    (root / "diagrams").mkdir(parents=True, exist_ok=True)
    for rel_path, body in sources.items():
        path = root / "diagrams" / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    for rel_path, body in outputs.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    for rel_path, body in (extra_files or {}).items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    if manifest is not None:
        text = (
            manifest
            if isinstance(manifest, str)
            else json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        (root / "diagrams" / "exports.json").write_text(text, encoding="utf-8")

    if setup is not None:
        setup(root)


def run_case(
    *,
    manifest: object,
    sources: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
    extra_files: dict[str, str] | None = None,
    setup=None,
) -> subprocess.CompletedProcess[str]:
    """偽リポジトリを作り、そこに**スクリプトをコピーして**走らせる。

    `check-diagram-freshness.py` は `REPO_ROOT = Path(__file__).parent.parent` で対象を
    決める（cwd ではない）。実リポジトリの側から呼ぶと**偽リポジトリではなく実リポジトリを
    検査してしまい、テストが常に通る**。コピーして走らせることで、対象が偽リポジトリになる。
    共有モジュール（`diagram_manifest.py`）も一緒に持っていく。
    """
    if sources is None:
        sources = {"one.drawio": SRC_ONE}
    if outputs is None:
        outputs = {OUT_ONE: "<svg/>\n"}
    with tempfile.TemporaryDirectory(prefix="cdf-test-") as tmp:
        root = Path(tmp) / "repo"
        (root / "scripts").mkdir(parents=True)
        build(
            root,
            manifest=manifest,
            sources=sources,
            outputs=outputs,
            extra_files=extra_files,
            setup=setup,
        )
        for source_file in (SCRIPT, SHARED):
            body = _MUTATED.get(
                source_file.name, source_file.read_text(encoding="utf-8")
            )
            (root / "scripts" / source_file.name).write_text(body, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(root / "scripts" / SCRIPT.name)],
            cwd=root,
            capture_output=True,
            text=True,
        )


def ok_manifest() -> dict:
    """正常系のマニフェスト（source 1 件・書き出し 1 件）。"""
    return {
        "diagrams/one.drawio": {
            "output": OUT_ONE,
            "fingerprint": fp(SRC_ONE, OUT_ONE),
        }
    }


def two_source_case(second: dict, **kwargs) -> subprocess.CompletedProcess[str]:
    """source 2 件の偽リポジトリ。2 件目のエントリだけ差し替えて使う。"""
    manifest = ok_manifest()
    manifest["diagrams/two.drawio"] = second
    return run_case(
        manifest=manifest,
        sources={"one.drawio": SRC_ONE, "two.drawio": SRC_TWO},
        outputs={OUT_ONE: "<svg/>\n", OUT_TWO: "\x89PNG\r\n\x1a\n"},
        **kwargs,
    )


# --- 各経路のケース（変異テストからも呼ぶので関数にしておく） ---------------------


def case_fresh():
    """正常系。"""
    return run_case(manifest=ok_manifest())


def case_stale():
    """経路 1: drawio を編集したのに書き出しを更新していない。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["fingerprint"] = fp("<mxfile>old</mxfile>\n", OUT_ONE)
    return run_case(manifest=manifest)


def case_scale_changed():
    """経路 1b: **マニフェストの `scale` だけ**書き換えて書き出さない。

    ソースのハッシュだけを記録していると通ってしまう（#50 のレビュー指摘）。
    `scale` は成果物を変えるので、指紋に入っていなければならない。
    """
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["scale"] = 2  # 指紋は scale=None で作ってある
    return run_case(manifest=manifest)


def case_output_retargeted():
    """経路 1c: **`output` だけ**別の実在ファイルに向け替えて書き出さない。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["output"] = OUT_TWO  # 指紋は OUT_ONE で作ってある
    return run_case(
        manifest=manifest,
        outputs={OUT_ONE: "<svg/>\n", OUT_TWO: "\x89PNG\r\n\x1a\n"},
    )


def case_unregistered():
    """経路 2: 新規 drawio を追加してマニフェストに書かない。"""
    return run_case(
        manifest=ok_manifest(),
        sources={"one.drawio": SRC_ONE, "two.drawio": SRC_TWO},
    )


def case_uppercase_suffix():
    """経路 2b: 拡張子が大文字（`rglob` だと収集から丸ごと落ちる）。"""
    return run_case(
        manifest=ok_manifest(),
        sources={"one.drawio": SRC_ONE, "TWO.DRAWIO": SRC_TWO},
    )


def case_symlink_dir():
    """経路 2c: `diagrams/` 内の symlink ディレクトリ配下（Python 3.13+ の `**` が辿らない）。"""

    def setup(root: Path) -> None:
        (root / "outside").mkdir(exist_ok=True)
        (root / "outside" / "hidden.drawio").write_text(SRC_TWO, encoding="utf-8")
        os.symlink(root / "outside", root / "diagrams" / "linked")

    return run_case(manifest=ok_manifest(), setup=setup)


def case_outside_diagrams():
    """経路 3: `diagrams/` の外に置いた drawio（収集範囲の外は最も静かな抜け道）。"""
    return run_case(
        manifest=ok_manifest(),
        extra_files={"docs/extra.drawio": SRC_TWO},
    )


def case_dead_entry():
    """経路 4: drawio を削除してエントリを残す。"""
    manifest = ok_manifest()
    manifest["diagrams/gone.drawio"] = {"output": "docs/images/gone.svg", "fingerprint": fp("x", "y")}
    return run_case(manifest=manifest)


def case_missing_output():
    """経路 5: 書き出しファイルを削除／改名する。"""
    return run_case(manifest=ok_manifest(), outputs={})


def case_missing_fingerprint():
    """経路 6a: `fingerprint` キーを落とす。"""
    manifest = ok_manifest()
    del manifest["diagrams/one.drawio"]["fingerprint"]
    return run_case(manifest=manifest)


def case_typo_required_key():
    """経路 6b: `fingerprint` の綴りを間違える。"""
    manifest = ok_manifest()
    entry = manifest["diagrams/one.drawio"]
    entry["fingerprnt"] = entry.pop("fingerprint")
    return run_case(manifest=manifest)


def case_typo_optional_key():
    """経路 6c: **任意キー**の綴り間違い（`scale` → `scal`）。

    必須キーの綴り間違いは「必須キーが無い」でも捕まるが、**任意キーの綴り間違いは
    未知キーの検査だけが捕まえる**。倍率を指定したつもりで既定倍率で書き出され、
    しかも検査は緑になる——これが「落として黙って免除する」形そのもの。
    """
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["scal"] = 2
    return run_case(manifest=manifest)


def case_bad_fingerprint():
    """経路 7: 指紋に短い文字列を入れる。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["fingerprint"] = "deadbeef"
    return run_case(manifest=manifest)


def case_duplicate_output():
    """経路 8: 2 つの source が同じ書き出しを指す。"""
    return two_source_case({"output": OUT_ONE, "fingerprint": fp(SRC_TWO, OUT_ONE)})


def case_noncanonical_output():
    """経路 8b: `output` を別表記で書いて重複検出をすり抜ける。"""
    return two_source_case(
        {"output": "docs/images/./one.svg", "fingerprint": fp(SRC_TWO, "docs/images/./one.svg")}
    )


def case_symlinked_output():
    """経路 8c: 書き出しの片方を symlink にして重複検出をすり抜ける。"""

    def setup(root: Path) -> None:
        os.symlink(root / OUT_ONE, root / "docs" / "images" / "alias.svg")

    return two_source_case(
        {"output": "docs/images/alias.svg", "fingerprint": fp(SRC_TWO, "docs/images/alias.svg")},
        setup=setup,
    )


def case_null_without_note():
    """経路 9: `output: null` で検査を免除するのに理由を書かない。"""
    return run_case(manifest={"diagrams/one.drawio": {"output": None}}, outputs={})


def case_duplicate_keys():
    """経路 10: JSON のキーを 2 回書く（`json` の既定は後勝ちで先が黙って消える）。"""
    raw = (
        "{\n"
        f'  "diagrams/one.drawio": {{"output": "{OUT_ONE}", "fingerprint": "{fp("stale", OUT_ONE)}"}},\n'
        f'  "diagrams/one.drawio": {{"output": "{OUT_ONE}", "fingerprint": "{fp(SRC_ONE, OUT_ONE)}"}}\n'
        "}\n"
    )
    return run_case(manifest=raw)


def case_bad_toplevel_key():
    """経路 11 の裏: `.drawio` でないキー（パスの綴り間違い）。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawi"] = {"output": "docs/images/x.svg", "fingerprint": fp("x", "y")}
    return run_case(manifest=manifest)


def case_key_outside_diagrams():
    """キーが `diagrams/` の外を指している。"""
    manifest = ok_manifest()
    manifest["docs/elsewhere.drawio"] = {"output": "docs/images/x.svg", "fingerprint": fp("x", "y")}
    return run_case(manifest=manifest)


def case_key_absolute():
    """キーが絶対パス。"""
    manifest = ok_manifest()
    manifest["/etc/evil.drawio"] = {"output": "docs/images/x.svg", "fingerprint": fp("x", "y")}
    return run_case(manifest=manifest)


def case_key_noncanonical():
    """キーが正規形でない（照合から外れて「実在するのに検査されない」を作る）。"""
    manifest = ok_manifest()
    manifest["diagrams/./one.drawio"] = manifest.pop("diagrams/one.drawio")
    return run_case(manifest=manifest)


def case_empty_key():
    """空のキー。"""
    manifest = ok_manifest()
    manifest[""] = {"output": "docs/images/x.svg", "fingerprint": fp("x", "y")}
    return run_case(manifest=manifest)


def case_output_not_string():
    """`output` が文字列でない。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["output"] = 123
    return run_case(manifest=manifest)


def main() -> int:
    # --- 正常系 -----------------------------------------------------------------
    proc = case_fresh()
    check(proc.returncode == 0, "正常系で落ちた", proc.stdout)
    check("1 件の drawio を検査" in proc.stdout, "検査件数が報告されていない", proc.stdout)

    # `output: null` + `note` は通る（宣言された「書き出さない」）
    proc = run_case(
        manifest={"diagrams/one.drawio": {"output": None, "note": "使っていない"}},
        outputs={},
    )
    check(proc.returncode == 0, "宣言された `output: null` で落ちた", proc.stdout)

    # `scale` を指紋に織り込んだエントリは通る
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["scale"] = 2
    manifest["diagrams/one.drawio"]["fingerprint"] = fp(SRC_ONE, OUT_ONE, 2)
    manifest["diagrams/one.drawio"]["note"] = "2 倍で書き出している"
    proc = run_case(manifest=manifest)
    check(proc.returncode == 0, "`scale` / `note` つきの正しいエントリで落ちた", proc.stdout)

    # `_comment` はトップレベルの予約キーなので通る（JSON にコメントが書けないため）
    manifest = ok_manifest()
    manifest["_comment"] = "手で指紋を書かない"
    proc = run_case(manifest=manifest)
    check(proc.returncode == 0, "`_comment` で落ちた", proc.stdout)
    check("1 件の drawio を検査" in proc.stdout, "`_comment` を検査対象に数えた", proc.stdout)

    # `diagrams/icons/` の素材 SVG は source ではない（未登録扱いにしない）
    proc = run_case(
        manifest=ok_manifest(),
        sources={"one.drawio": SRC_ONE, "icons/github.svg": "<svg/>"},
    )
    check(proc.returncode == 0, "`diagrams/icons/` の素材を source と誤検出した", proc.stdout)

    # PNG の書き出しも通る
    manifest = {"diagrams/one.drawio": {"output": OUT_TWO, "fingerprint": fp(SRC_ONE, OUT_TWO)}}
    proc = run_case(manifest=manifest, outputs={OUT_TWO: "png"})
    check(proc.returncode == 0, "PNG の書き出しで落ちた", proc.stdout)

    # --- 否定側: 経路ごとに 1 件以上 --------------------------------------------
    for case, expected, label in (
        (case_stale, "書き出し直していない", "鮮度の乖離"),
        (case_scale_changed, "書き出し直していない", "`scale` だけの書き換え"),
        (case_output_retargeted, "書き出し直していない", "`output` だけの向け替え"),
        (case_unregistered, "未登録", "未登録の新規 drawio"),
        (case_uppercase_suffix, "未登録", "大文字拡張子の drawio"),
        (case_symlink_dir, "未登録", "symlink ディレクトリ配下の drawio"),
        (case_outside_diagrams, "の外にある", "`diagrams/` の外の drawio"),
        (case_dead_entry, "実在しない", "実在しない source のエントリ"),
        (case_missing_output, "が存在しない", "書き出しの欠落"),
        (case_missing_fingerprint, "`fingerprint` が無い", "指紋の欠落"),
        (case_typo_required_key, "`fingerprint` が無い", "必須キーの綴り間違い"),
        (case_typo_optional_key, "未知のキー", "任意キーの綴り間違い"),
        (case_bad_fingerprint, "64 桁", "不正な指紋"),
        (case_duplicate_output, "同じ書き出し", "書き出しの重複"),
        (case_noncanonical_output, "正規形でない", "`output` の別表記"),
        (case_symlinked_output, "同じ書き出し", "symlink による書き出しの重複"),
        (case_null_without_note, "`note` が無い", "理由なしの免除"),
        (case_duplicate_keys, "2 回ある", "JSON のキーの重複"),
        (case_bad_toplevel_key, "`.drawio` で終わっていない", "非 drawio キー"),
        (case_key_outside_diagrams, "の外を指している", "`diagrams/` 外を指すキー"),
        (case_key_absolute, "は不正", "絶対パスのキー"),
        (case_key_noncanonical, "正規形でない", "正規形でないキー"),
        (case_empty_key, "空のキー", "空のキー"),
        (case_output_not_string, "`output` が文字列でない", "`output` の型"),
    ):
        check_rejected(case(), expected, f"{label}がすり抜けた")

    # `output: null` なのに指紋が同居している（免除と鮮度記録の混在）
    check_rejected(
        run_case(
            manifest={
                "diagrams/one.drawio": {
                    "output": None,
                    "note": "x",
                    "fingerprint": fp(SRC_ONE, OUT_ONE),
                }
            },
            outputs={},
        ),
        "なのに `fingerprint` を持っている",
        "免除と鮮度記録の混在がすり抜けた",
    )

    # `output` が無い（`null` を書き忘れたのか書き出し忘れなのか区別できない状態）
    check_rejected(
        run_case(
            manifest={"diagrams/one.drawio": {"fingerprint": fp(SRC_ONE, OUT_ONE)}}, outputs={}
        ),
        "`output` が無い",
        "`output` の欠落がすり抜けた",
    )

    # エントリがオブジェクトでない
    check_rejected(
        run_case(manifest={"diagrams/one.drawio": OUT_ONE}),
        "オブジェクトでない",
        "エントリの型がすり抜けた",
    )

    # `output` の拡張子が対象外
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["output"] = "docs/images/one.pdf"
    manifest["diagrams/one.drawio"]["fingerprint"] = fp(SRC_ONE, "docs/images/one.pdf")
    check_rejected(
        run_case(manifest=manifest, outputs={"docs/images/one.pdf": "pdf"}),
        "拡張子が",
        "対象外の拡張子がすり抜けた",
    )

    # `output` に絶対パス・親参照
    for label, bad in (("絶対パス", "/etc/passwd.svg"), ("親参照", "../outside.svg")):
        manifest = ok_manifest()
        manifest["diagrams/one.drawio"]["output"] = bad
        check_rejected(
            run_case(manifest=manifest, outputs={}),
            "は不正",
            f"`output` の{label}がすり抜けた",
        )

    # `scale` が正の数でない
    for bad in (0, -1, "2", True):
        manifest = ok_manifest()
        manifest["diagrams/one.drawio"]["scale"] = bad
        check_rejected(
            run_case(manifest=manifest),
            "`scale` が正の数でない",
            f"`scale`={bad!r} がすり抜けた",
        )

    # マニフェストが無い / 壊れている / 形が違う（fail-closed）
    check_rejected(run_case(manifest=None), "書き出しの宣言が無い", "マニフェストの欠落がすり抜けた")
    check_rejected(run_case(manifest="{ broken"), "JSON として不正", "壊れた JSON がすり抜けた")
    check_rejected(
        run_case(manifest=[{"output": OUT_ONE}]),
        "オブジェクトである必要がある",
        "トップレベルが配列でもすり抜けた",
    )

    # **2 件目だけ古い**（1 件目しか見ない退行を捕まえる）。
    # 終了コードだけを見ると、別の理由（未登録など）で非 0 になって**テストが通ってしまう**ので、
    # **2 件目の鮮度の指摘そのものが出ているか**を確かめる。
    proc = two_source_case({"output": OUT_TWO, "fingerprint": fp("<mxfile>outdated</mxfile>\n", OUT_TWO)})
    check_rejected(proc, "diagrams/two.drawio", "2 件目の鮮度の乖離がすり抜けた")
    check(
        "書き出し直していない" in proc.stdout and "two.png" in proc.stdout,
        "2 件目の鮮度の乖離が、鮮度の指摘として出ていない",
        proc.stdout,
    )

    check_mutations()

    if failures:
        print(f"{len(failures)} 件の失敗（{checks} 判定）:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"check-diagram-freshness.py: 全 {checks} 判定に合格")
    return 0


# --- 変異テスト ----------------------------------------------------------------
#
# **否定テストが「別の理由で」通っていないことを確かめる。** 検査の分岐を 1 つ潰したとき、
# 対応する否定ケースから**その理由の指摘が消える**なら、そのケースはその分岐を固定できている。
# 消えないなら、そのケースは何か別の理由で落ちていたということ。
#
# **判定は「緑になること」ではなく「その理由が消えること」。** 検査は多重になっているので
# （例: `fingerprnt` という綴り間違いは「未知のキー」と「`fingerprint` が無い」の両方で
# 捕まる）、1 つ潰しただけでは緑にならない。**多重であることは望ましい**——だから
# 「緑になること」を要求すると、テストを弱いほうへ書き換える圧力になる。実際、最初はそう書いて
# 4 件が「変異が生き残った」と出た。要求すべきなのは**その分岐が指摘を出していたこと**である。
#
# **変異はクラッシュさせない形にする。** 素の例外で落ちると指摘は消えるので、
# 「理由が消えた」だけを見ていると**クラッシュを合格と数える**（#50 のレビュー指摘）。
# 判定側では `Traceback` を落とし、変異側でも診断の行だけを消す形を選ぶ。

MUTATIONS = [
    (
        "鮮度の比較を潰す",
        "    if actual != recorded:",
        "    if False:",
        case_stale,
        "書き出し直していない",
    ),
    (
        "未登録の検出を潰す",
        "    for key in sorted(found - declared):",
        "    for key in sorted(set()):",
        case_unregistered,
        "未登録",
    ),
    (
        "収集の大文字小文字対応を潰す",
        '            if name.lower().endswith(SOURCE_SUFFIX):',
        "            if name.endswith(SOURCE_SUFFIX):",
        case_uppercase_suffix,
        "未登録",
    ),
    (
        "収集の symlink 追跡を潰す",
        "    for dirpath, dirnames, filenames in os.walk(top, followlinks=True):",
        "    for dirpath, dirnames, filenames in os.walk(top):",
        case_symlink_dir,
        "未登録",
    ),
    (
        "収集範囲の外の検出を潰す",
        "    check_sources_outside_diagrams(found)",
        "    pass",
        case_outside_diagrams,
        "の外にある",
    ),
    (
        "死んだエントリの検出を潰す",
        "    for key in sorted(declared - found):",
        "    for key in sorted(set()):",
        case_dead_entry,
        "実在しない",
    ),
    (
        "書き出しの実在確認を潰す",
        "    if not output_path.is_file():",
        "    if False:",
        case_missing_output,
        "が存在しない",
    ),
    (
        "未知キーの検出を潰す",
        "    if unknown:",
        "    if False:",
        case_typo_optional_key,
        "未知のキー",
    ),
    (
        "指紋の桁の検査を潰す",
        "    if not isinstance(recorded, str) or not FINGERPRINT_RE.fullmatch(recorded):",
        "    if False:",
        case_bad_fingerprint,
        "64 桁",
    ),
    (
        "書き出しの重複検出を潰す",
        "    if identity in outputs_seen:",
        "    if False:",
        case_duplicate_output,
        "同じ書き出し",
    ),
    (
        "書き出しの実パス照合を潰す（symlink 経由の重複）",
        "    identity = os.path.realpath(output_path)",
        "    identity = output",
        case_symlinked_output,
        "同じ書き出し",
    ),
    (
        "`output` の正規形の検査を潰す",
        "    if output != os.path.normpath(output):",
        "    if False:",
        case_noncanonical_output,
        "正規形でない",
    ),
    (
        "免除の理由（note）の要求を潰す",
        '        if not entry.get("note"):',
        "        if False:",
        case_null_without_note,
        "`note` が無い",
    ),
    (
        "指紋キーの必須の診断を潰す",
        '        fail(f"{key} のエントリに `fingerprint` が無い（書き出し時点の前提の指紋）")',
        "        pass",
        case_missing_fingerprint,
        "`fingerprint` が無い",
    ),
    (
        "JSON のキーの重複検出を潰す",
        "        if key in seen:",
        "        if False:",
        case_duplicate_keys,
        "2 回ある",
    ),
    (
        "キーの拡張子の検査を潰す",
        '    if path.suffix.lower() != SOURCE_SUFFIX:',
        "    if False:",
        case_bad_toplevel_key,
        "`.drawio` で終わっていない",
    ),
    (
        "キーが diagrams/ の内側かの検査を潰す",
        "        path.relative_to(DIAGRAMS_DIR)",
        "        pass",
        case_key_outside_diagrams,
        "の外を指している",
    ),
    (
        "キーの絶対パス・親参照の検査を潰す",
        '    if key.startswith("/") or ".." in Path(key).parts:',
        "    if False:",
        case_key_absolute,
        "は不正",
    ),
    (
        "キーの正規形の検査を潰す",
        "    if key != os.path.normpath(key):",
        "    if False:",
        case_key_noncanonical,
        "正規形でない",
    ),
    (
        "空のキーの検査を潰す",
        "    if not key:",
        "    if False:",
        case_empty_key,
        "空のキー",
    ),
    (
        # 条件そのものを潰すと下流が `int.startswith` でクラッシュする（型検査が
        # 素通しを防いでいる証拠ではあるが、クラッシュは「指摘が消えた」と区別できない）。
        # **診断の行だけ**を消す形にする。
        "`output` の型の検査を潰す",
        '        fail(f"{key} の `output` が文字列でない: {output!r}")',
        "        pass",
        case_output_not_string,
        "`output` が文字列でない",
    ),
]


MUTATION_TARGETS = (SCRIPT, SHARED)


def locate(old: str) -> Path | None:
    """変異の対象文字列を含むファイルを 1 つに特定する。

    どのファイルを変異させるかを表に書かずに済ませる——**書けばずれる**ので、
    「その文字列がちょうど 1 箇所にある」ことを毎回確かめるほうを選ぶ。
    """
    hits = [
        path
        for path in MUTATION_TARGETS
        if path.read_text(encoding="utf-8").count(old) == 1
    ]
    total = sum(
        path.read_text(encoding="utf-8").count(old) for path in MUTATION_TARGETS
    )
    return hits[0] if len(hits) == 1 and total == 1 else None


def check_mutations() -> None:
    originals = {path.name: path.read_text(encoding="utf-8") for path in MUTATION_TARGETS}

    for label, old, new, case, expected in MUTATIONS:
        target = locate(old)
        check(target is not None, f"変異の対象が一意に定まらない（{label}）: {old!r}")
        if target is None:
            continue

        # 変異させた版で、対応する否定ケースを**そのまま**走らせ直す。
        _MUTATED[target.name] = originals[target.name].replace(old, new)
        try:
            proc = case()
        finally:
            _MUTATED.clear()

        check(
            expected not in proc.stdout,
            f"変異が生き残った（{label}）——{expected!r} の指摘が別の経路から出ている",
            proc.stdout[-300:],
        )
        check(
            "Traceback" not in proc.stderr,
            f"変異でクラッシュした（{label}）——指摘が消えたのではなく落ちている",
            proc.stderr[-300:],
        )

    # 実ファイルは読むだけ（偽リポジトリにコピーして変異させる）。念のため固定する。
    for path in MUTATION_TARGETS:
        check(
            path.read_text(encoding="utf-8") == originals[path.name],
            f"変異テストが {path.name} を書き換えた",
        )


if __name__ == "__main__":
    sys.exit(main())
