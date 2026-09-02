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

# 実リポジトリ。ここを対象にしてしまうテストは実行前に落とす。
REAL_REPO = REPO_ROOT.resolve()

failures: list[str] = []
checks = 0

SRC_ONE = "<mxfile>one</mxfile>\n"
SRC_TWO = "<mxfile>two</mxfile>\n"

# 変異テスト中だけ、偽リポジトリにコピーするスクリプトの中身を差し替える（末尾を参照）。
_MUTATED_SCRIPT: str | None = None


def check(condition: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def check_rejected(proc: subprocess.CompletedProcess[str], expected: str, label: str) -> None:
    """「落ちること」だけでなく、**期待した理由で落ちたこと**まで見る。

    終了コードだけを見ると**クラッシュも合格になる**。`check-plugin-versions.py` の周では、
    そのせいで 22 件の変異がすべてテストを通り抜けた。否定側は全部これを使う。
    """
    check(proc.returncode != 0, f"{label}（落ちなかった）", proc.stdout)
    check(
        expected in proc.stdout,
        f"{label}（落ちたが理由が違う。期待: {expected!r}）",
        (proc.stdout + proc.stderr)[-400:],
    )


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(
    root: Path,
    *,
    manifest: object,
    sources: dict[str, str],
    outputs: dict[str, str],
    extra_files: dict[str, str] | None = None,
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

    if manifest is None:
        return
    text = (
        manifest
        if isinstance(manifest, str)
        else json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    (root / "diagrams" / "exports.json").write_text(text, encoding="utf-8")


def run_case(
    *,
    manifest: object,
    sources: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
    extra_files: dict[str, str] | None = None,
    script_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """偽リポジトリを作り、そこに**スクリプトをコピーして**走らせる。

    `check-diagram-freshness.py` は `REPO_ROOT = Path(__file__).parent.parent` で対象を
    決める（cwd ではない）。実リポジトリの側から呼ぶと**偽リポジトリではなく実リポジトリを
    検査してしまい、テストが常に通る**。コピーして走らせることで、対象が偽リポジトリになる。
    """
    if sources is None:
        sources = {"one.drawio": SRC_ONE}
    if outputs is None:
        outputs = {"docs/images/one.svg": "svg one\n"}
    # 変異テスト中は、ケース関数を書き直さずに変異版を走らせるため、ここで差し込む
    # （ケースの定義を 2 度書くと「テストとケースがずれる」事故が入る）。
    if script_text is None:
        script_text = _MUTATED_SCRIPT if _MUTATED_SCRIPT is not None else SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="cdf-test-") as tmp:
        root = Path(tmp) / "repo"
        (root / "scripts").mkdir(parents=True)
        build(root, manifest=manifest, sources=sources, outputs=outputs, extra_files=extra_files)
        copied = root / "scripts" / SCRIPT.name
        copied.write_text(script_text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(copied)], cwd=root, capture_output=True, text=True
        )


def ok_manifest() -> dict:
    """正常系のマニフェスト（source 1 件・書き出し 1 件）。"""
    return {
        "diagrams/one.drawio": {
            "output": "docs/images/one.svg",
            "sha256": sha(SRC_ONE),
        }
    }


# --- 各経路のケース（変異テストからも呼ぶので関数にしておく） ---------------------


def case_fresh() -> subprocess.CompletedProcess[str]:
    """正常系。"""
    return run_case(manifest=ok_manifest())


def case_stale() -> subprocess.CompletedProcess[str]:
    """経路 1: drawio を編集したのに書き出しを更新していない。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["sha256"] = sha("<mxfile>old</mxfile>\n")
    return run_case(manifest=manifest)


def case_unregistered() -> subprocess.CompletedProcess[str]:
    """経路 2: 新規 drawio を追加してマニフェストに書かない。"""
    return run_case(
        manifest=ok_manifest(),
        sources={"one.drawio": SRC_ONE, "two.drawio": SRC_TWO},
    )


def case_dead_entry() -> subprocess.CompletedProcess[str]:
    """経路 3: drawio を削除してエントリを残す。"""
    manifest = ok_manifest()
    manifest["diagrams/gone.drawio"] = {"output": "docs/images/gone.svg", "sha256": sha("x")}
    return run_case(manifest=manifest)


def case_missing_output() -> subprocess.CompletedProcess[str]:
    """経路 4: 書き出しファイルを削除／改名する。"""
    return run_case(manifest=ok_manifest(), outputs={})


def case_missing_sha() -> subprocess.CompletedProcess[str]:
    """経路 6a: `sha256` キーを落とす。"""
    manifest = ok_manifest()
    del manifest["diagrams/one.drawio"]["sha256"]
    return run_case(manifest=manifest)


def case_typo_required_key() -> subprocess.CompletedProcess[str]:
    """経路 6b: `sha256` の綴りを間違える（黙って無視されると検査が無言で外れる）。"""
    manifest = ok_manifest()
    entry = manifest["diagrams/one.drawio"]
    entry["sha265"] = entry.pop("sha256")
    return run_case(manifest=manifest)


def case_typo_optional_key() -> subprocess.CompletedProcess[str]:
    """経路 6c: **任意キー**の綴り間違い（`scale` → `scal`）。

    必須キーの綴り間違いは「必須キーが無い」でも捕まるが、**任意キーの綴り間違いは
    未知キーの検査だけが捕まえる**。倍率を指定したつもりで既定倍率で書き出され、
    しかも検査は緑になる——これが「落として黙って免除する」形そのもの。
    """
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["scal"] = 2
    return run_case(manifest=manifest)


def case_bad_sha() -> subprocess.CompletedProcess[str]:
    """経路 7: sha256 に短い文字列を入れる。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["sha256"] = "deadbeef"
    return run_case(manifest=manifest)


def case_duplicate_output() -> subprocess.CompletedProcess[str]:
    """経路 8: 2 つの source が同じ書き出しを指す。"""
    manifest = ok_manifest()
    manifest["diagrams/two.drawio"] = {
        "output": "docs/images/one.svg",
        "sha256": sha(SRC_TWO),
    }
    return run_case(
        manifest=manifest,
        sources={"one.drawio": SRC_ONE, "two.drawio": SRC_TWO},
    )


def case_null_without_note() -> subprocess.CompletedProcess[str]:
    """経路 9: `output: null` で検査を免除するのに理由を書かない。"""
    return run_case(
        manifest={"diagrams/one.drawio": {"output": None}},
        outputs={},
    )


def case_bad_toplevel_key() -> subprocess.CompletedProcess[str]:
    """経路 11 の裏: `.drawio` でないキー（パスの綴り間違い）。"""
    manifest = ok_manifest()
    manifest["diagrams/one.drawi"] = {"output": "docs/images/x.svg", "sha256": sha("x")}
    return run_case(manifest=manifest)


def case_nested_unregistered() -> subprocess.CompletedProcess[str]:
    """サブディレクトリの drawio も拾う（`glob` に退行すると素通しになる）。"""
    return run_case(
        manifest=ok_manifest(),
        sources={"one.drawio": SRC_ONE, "sub/deep.drawio": SRC_TWO},
    )


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

    # `scale` と `note` を持つエントリは通る
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["scale"] = 2
    manifest["diagrams/one.drawio"]["note"] = "2 倍で書き出している"
    proc = run_case(manifest=manifest)
    check(proc.returncode == 0, "`scale` / `note` つきのエントリで落ちた", proc.stdout)

    # `_comment` はトップレベルの予約キーなので通る（JSON にコメントが書けないため）
    manifest = ok_manifest()
    manifest["_comment"] = "手で sha256 を書かない"
    proc = run_case(manifest=manifest)
    check(proc.returncode == 0, "`_comment` で落ちた", proc.stdout)
    check("1 件の drawio を検査" in proc.stdout, "`_comment` を検査対象に数えた", proc.stdout)

    # `diagrams/icons/` の素材 SVG は source ではない（未登録扱いにしない）
    proc = run_case(
        manifest=ok_manifest(),
        sources={"one.drawio": SRC_ONE, "icons/github.svg": "<svg/>"},
    )
    check(proc.returncode == 0, "`diagrams/icons/` の素材を source と誤検出した", proc.stdout)

    # --- 否定側: 経路ごとに 1 件以上 --------------------------------------------
    check_rejected(case_stale(), "書き出し直していない", "鮮度の乖離がすり抜けた")
    check_rejected(case_unregistered(), "未登録", "未登録の新規 drawio がすり抜けた")
    check_rejected(case_dead_entry(), "実在しない", "実在しない source のエントリがすり抜けた")
    check_rejected(case_missing_output(), "が存在しない", "書き出しの欠落がすり抜けた")
    check_rejected(case_missing_sha(), "`sha256` が無い", "sha256 の欠落がすり抜けた")
    check_rejected(case_typo_required_key(), "`sha256` が無い", "必須キーの綴り間違いがすり抜けた")
    check_rejected(case_typo_optional_key(), "未知のキー", "任意キーの綴り間違いが黙って無視された")
    check_rejected(case_bad_sha(), "64 桁", "不正な sha256 がすり抜けた")
    check_rejected(case_duplicate_output(), "同じ書き出し", "書き出しの重複がすり抜けた")
    check_rejected(case_null_without_note(), "`note` が無い", "理由なしの免除がすり抜けた")
    check_rejected(case_bad_toplevel_key(), "`.drawio` で終わっていない", "非 drawio キーがすり抜けた")
    check_rejected(case_nested_unregistered(), "未登録", "サブディレクトリの drawio を拾えていない")

    # `output: null` なのに sha256 が同居している（免除と鮮度記録の混在）
    check_rejected(
        run_case(manifest={"diagrams/one.drawio": {"output": None, "note": "x", "sha256": sha(SRC_ONE)}}, outputs={}),
        "なのに `sha256` を持っている",
        "免除と鮮度記録の混在がすり抜けた",
    )

    # `output` が無い（`null` を書き忘れたのか書き出し忘れなのか区別できない状態）
    check_rejected(
        run_case(manifest={"diagrams/one.drawio": {"sha256": sha(SRC_ONE)}}, outputs={}),
        "`output` が無い",
        "`output` の欠落がすり抜けた",
    )

    # エントリがオブジェクトでない
    check_rejected(
        run_case(manifest={"diagrams/one.drawio": "docs/images/one.svg"}),
        "オブジェクトでない",
        "エントリの型がすり抜けた",
    )

    # `output` の拡張子が対象外
    manifest = ok_manifest()
    manifest["diagrams/one.drawio"]["output"] = "docs/images/one.pdf"
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
        run_case(manifest=[{"output": "docs/images/one.svg"}]),
        "オブジェクトである必要がある",
        "トップレベルが配列でもすり抜けた",
    )

    # **2 件目だけ古い**（1 件目しか見ない退行を捕まえる）。
    # 終了コードだけを見ると、別の理由（未登録など）で非 0 になって**テストが通ってしまう**ので、
    # **2 件目の鮮度の指摘そのものが出ているか**を確かめる。
    manifest = ok_manifest()
    manifest["diagrams/two.drawio"] = {
        "output": "docs/images/two.png",
        "sha256": sha("<mxfile>outdated</mxfile>\n"),
    }
    proc = run_case(
        manifest=manifest,
        sources={"one.drawio": SRC_ONE, "two.drawio": SRC_TWO},
        outputs={"docs/images/one.svg": "svg one\n", "docs/images/two.png": "png two\n"},
    )
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
# （例: `sha265` という綴り間違いは「未知のキー」と「`sha256` が無い」の両方で捕まる）、
# 1 つ潰しただけでは緑にならない。**多重であることは望ましい**——だから「緑になること」を
# 要求すると、テストを弱いほうへ書き換える圧力になる。実際、最初はそう書いて
# 4 件が「変異が生き残った」と出た。要求すべきなのは**その分岐が指摘を出していたこと**である。

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
        "sha256 の桁の検査を潰す",
        "    if not isinstance(recorded, str) or not SHA256_RE.fullmatch(recorded):",
        "    if False:",
        case_bad_sha,
        "64 桁",
    ),
    (
        "書き出しの重複検出を潰す",
        "    if output in outputs_seen:",
        "    if False:",
        case_duplicate_output,
        "同じ書き出し",
    ),
    (
        "免除の理由（note）の要求を潰す",
        '        if not entry.get("note"):',
        "        if False:",
        case_null_without_note,
        "`note` が無い",
    ),
    (
        "sha256 キーの必須を潰す",
        '    if "sha256" not in entry:',
        "    if False:",
        case_missing_sha,
        "`sha256` が無い",
    ),
    (
        "収集を再帰なしに退行させる",
        "    found = {rel(path) for path in DIAGRAMS_DIR.rglob(SOURCE_GLOB) if path.is_file()}",
        "    found = {rel(path) for path in DIAGRAMS_DIR.glob(SOURCE_GLOB) if path.is_file()}",
        case_nested_unregistered,
        "未登録",
    ),
    (
        "キーの拡張子の検査を潰す",
        '    if path.suffix != ".drawio":',
        "    if False:",
        case_bad_toplevel_key,
        "`.drawio` で終わっていない",
    ),
]


def check_mutations() -> None:
    original = SCRIPT.read_text(encoding="utf-8")

    for label, old, new, case, expected in MUTATIONS:
        check(original.count(old) == 1, f"変異の対象が一意でない（{label}）: {old!r}")
        if original.count(old) != 1:
            continue
        mutated = original.replace(old, new)

        # 変異させたスクリプトで、対応する否定ケースを**そのまま**走らせ直す。
        global _MUTATED_SCRIPT
        _MUTATED_SCRIPT = mutated
        try:
            proc = case()
        finally:
            _MUTATED_SCRIPT = None

        check(
            expected not in proc.stdout,
            f"変異が生き残った（{label}）——{expected!r} の指摘が別の経路から出ている",
            proc.stdout[-300:],
        )

    # 実スクリプトは読むだけ（偽リポジトリにコピーして変異させる）。念のため固定する。
    check(
        SCRIPT.read_text(encoding="utf-8") == original,
        "変異テストが実スクリプトを書き換えた",
    )


if __name__ == "__main__":
    sys.exit(main())
