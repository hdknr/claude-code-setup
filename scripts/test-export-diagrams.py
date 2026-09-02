#!/usr/bin/env python3
"""scripts/export-diagrams.py の回帰テスト。

    python3 scripts/test-export-diagrams.py

なぜ必要か（#50）: 鮮度チェックは**ソースのハッシュを書き出しの記録として**持つ方式で、
「記録は新しいのに書き出しは古い／壊れている」状態だけは原理的に検出できない。
その状態を作らないことは**書き出しスクリプトの側の責任**であり、
`check-diagram-freshness.py` のテストでは一切カバーされない。

実際、#50 の周の検証で**この経路の不具合が見つかった**——`export_one` が
`proc.returncode` を見ておらず、**書き出してから非ゼロで終了する CLI**（部分書き込み後の
クラッシュ、壊れた／空のファイルを吐いて落ちる）を成功と誤判定して、
記録だけを進めていた。しかもアドバーサリアルな操作は不要で、CLI の実クラッシュで起こりうる。
ここに固定して再発を止める。

**draw.io CLI は呼ばない。** `DRAWIO` に**偽の CLI**（Python スクリプト）を差し込み、
「成功する」「書いてから落ちる」「書かずに 0 を返す」「空／壊れたファイルを書く」を
作り分けて、記録が進む条件を固定する。実際の draw.io に依存しないので CI でも走る。

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリを作り、そこだけを対象にする。
実リポジトリを対象にしてしまうテストは**実行前にアサートで落とす**。

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
SCRIPT = REPO_ROOT / "scripts" / "export-diagrams.py"
SHARED = REPO_ROOT / "scripts" / "diagram_manifest.py"

# 実リポジトリ。ここを対象にしてしまうテストは実行前に落とす。
REAL_REPO = REPO_ROOT.resolve()

SRC = "<mxfile>one</mxfile>\n"
GOOD_SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>\n'
KEY = "diagrams/one.drawio"
OUT = "docs/images/one.svg"

failures: list[str] = []
checks = 0


def check(condition: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def fp(
    source_text: str,
    output: str,
    scale: object = None,
    output_text: str = GOOD_SVG,
) -> str:
    """`diagram_manifest.fingerprint` と**同じ式を独立に**書いたもの。

    共有実装を import して期待値を作ると、**式が変わってもテストは一緒に変わって
    通り続ける**（`test-check-diagram-freshness.py` と同じ理由）。
    `output_text` の既定は**偽 CLI が成功時に書く中身**——書き出し後の指紋を期待するため。
    """
    digest = hashlib.sha256()
    digest.update(source_text.encode("utf-8"))
    digest.update(b"\0")
    digest.update(output.encode("utf-8"))
    digest.update(b"\0")
    if isinstance(scale, float) and scale.is_integer():
        scale = int(scale)
    digest.update(repr(scale).encode("utf-8"))
    digest.update(b"\0")
    digest.update(output_text.encode("utf-8"))
    return digest.hexdigest()


# 変異テスト中だけ、偽リポジトリにコピーするスクリプトの中身を差し替える（末尾を参照）。
_MUTATED_SCRIPT: str | None = None


# 偽の draw.io CLI。`--output <path>` を拾って、behaviour に応じた振る舞いをする。
FAKE_CLI = '''#!/usr/bin/env python3
import sys, os
behaviour = os.environ["FAKE_BEHAVIOUR"]
out = sys.argv[sys.argv.index("--output") + 1]

if behaviour == "success":
    open(out, "w").write({good!r})
    sys.exit(0)
if behaviour == "write_then_fail":
    # **最重要のケース**: 書き出しを潰してから非ゼロで終了する
    open(out, "w").write("")
    sys.exit(1)
if behaviour == "broken_then_ok":
    # 壊れたものを書いて 0 を返す（終了コードだけでは弾けない）
    open(out, "w").write("not an svg at all")
    sys.exit(0)
if behaviour == "nothing_but_ok":
    # 何も書かずに 0 を返す
    sys.exit(0)
if behaviour == "fail_only":
    sys.exit(3)
if behaviour == "hang":
    # タイムアウトさせる（テストは DRAWIO_TIMEOUT=1 を渡す）
    import time
    time.sleep(10)
    sys.exit(0)
raise SystemExit("unknown behaviour: " + behaviour)
'''.replace("{good!r}", repr(GOOD_SVG))


def run_case(
    behaviour: str,
    *,
    manifest: dict | None = None,
    args: list[str] | None = None,
    output_body: str | None = GOOD_SVG,
) -> tuple[subprocess.CompletedProcess[str], dict, str | None]:
    """偽リポジトリを作り、偽 CLI で `export-diagrams.py` を走らせる。

    戻り値は (プロセス, 走らせた後のマニフェスト, 走らせた後の書き出しの中身 or None)。
    """
    if manifest is None:
        manifest = {KEY: {"output": OUT, "fingerprint": fp("<mxfile>OLD</mxfile>\n", OUT)}}
    with tempfile.TemporaryDirectory(prefix="ted-test-") as tmp:
        root = Path(tmp) / "repo"
        assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
        assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
            "テストの作業ディレクトリが実リポジトリの内側にある"
        )

        (root / "scripts").mkdir(parents=True)
        (root / "diagrams").mkdir(parents=True)
        (root / "diagrams" / "one.drawio").write_text(SRC, encoding="utf-8")
        (root / "diagrams" / "exports.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        out_path = root / OUT
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if output_body is not None:
            out_path.write_text(output_body, encoding="utf-8")

        # `export-diagrams.py` は `REPO_ROOT = Path(__file__).parent.parent` で対象を決める。
        # 実リポジトリから呼ぶと実リポジトリを書き換えるので、必ずコピーして走らせる。
        copied = root / "scripts" / SCRIPT.name
        copied.write_text(
            _MUTATED_SCRIPT
            if _MUTATED_SCRIPT is not None
            else SCRIPT.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / "scripts" / SHARED.name).write_text(
            SHARED.read_text(encoding="utf-8"), encoding="utf-8"
        )

        fake = root / "fake-drawio.py"
        fake.write_text(FAKE_CLI, encoding="utf-8")

        env = dict(os.environ)
        env["DRAWIO"] = f"{sys.executable} {fake}"
        env["FAKE_BEHAVIOUR"] = behaviour
        # タイムアウト経路を通すため。既定（600 秒）のままではその分岐を検証できない。
        env["DRAWIO_TIMEOUT"] = "1" if behaviour == "hang" else "60"

        proc = subprocess.run(
            # `args=[]`（全件モード）と `args=None`（既定）を区別する。
            # `args or ["one"]` と書くと空リストが既定に化けて、全件モードを検査できない。
            [sys.executable, str(copied), *(["one"] if args is None else args)],
            cwd=root,
            capture_output=True,
            text=True,
            env=env,
        )
        after = json.loads((root / "diagrams" / "exports.json").read_text(encoding="utf-8"))
        body = out_path.read_text(encoding="utf-8") if out_path.is_file() else None
        return proc, after, body


def recorded(manifest: dict) -> str | None:
    return manifest[KEY].get("fingerprint")


def main() -> int:
    fresh = fp(SRC, OUT)

    # --- 成功したときだけ記録が進む -------------------------------------------
    proc, after, body = run_case("success")
    check(proc.returncode == 0, "成功したのに非ゼロ終了した", proc.stdout + proc.stderr)
    check(recorded(after) == fresh, "成功したのに記録が進まなかった", str(recorded(after)))
    check(body == GOOD_SVG, "成功したのに書き出しが置き換わっていない", str(body))

    # 書き戻す指紋に **`scale` が織り込まれている**こと。落ちていると、マニフェストの
    # `scale` を書き換えても検査が緑のままになる（#50 のレビューで指摘された経路）。
    proc, after, _ = run_case(
        "success",
        manifest={KEY: {"output": OUT, "scale": 2, "fingerprint": fp("old", OUT, 2)}},
    )
    check(proc.returncode == 0, "`scale` つきの書き出しで落ちた", proc.stdout + proc.stderr)
    check(
        recorded(after) == fp(SRC, OUT, 2),
        "書き戻した指紋に `scale` が織り込まれていない",
        f"{recorded(after)} != {fp(SRC, OUT, 2)}",
    )
    check(
        recorded(after) != fp(SRC, OUT, None),
        "`scale` の有無で指紋が変わっていない",
        str(recorded(after)),
    )

    # --- **書いてから非ゼロで終了**（この周で実際に踏んだ不具合） ----------------
    proc, after, body = run_case("write_then_fail")
    check(proc.returncode != 0, "書き出しが失敗したのにゼロ終了した", proc.stdout)
    check(
        recorded(after) != fresh,
        "**書き出しが失敗したのに記録が進んだ**（検出できない状態を自分で作っている）",
        proc.stdout,
    )
    check(
        body == GOOD_SVG,
        "失敗したのに書き出しが元に戻っていない（壊れたファイルが残った）",
        str(body),
    )

    # --- 壊れたものを書いて 0 を返す（終了コードだけでは弾けない） ---------------
    proc, after, body = run_case("broken_then_ok")
    check(proc.returncode != 0, "壊れた書き出しを成功と判定した", proc.stdout)
    check(recorded(after) != fresh, "壊れた書き出しで記録が進んだ", proc.stdout)
    check(body == GOOD_SVG, "壊れた書き出しが残った", str(body))

    # --- 何も書かずに 0 を返す ---------------------------------------------------
    # 既存の書き出しが**無い**場合
    proc, after, body = run_case("nothing_but_ok", output_body=None)
    check(proc.returncode != 0, "書き出しが作られていないのに成功と判定した", proc.stdout)
    check(recorded(after) != fresh, "書き出しが無いのに記録が進んだ", proc.stdout)
    check(body is None, "作られていないはずの書き出しが存在する", str(body))

    # **既存の書き出しが有効なまま残っている場合**（#50 の 2 パス目のレビューで、
    # mtime の 1 秒許容がこの窓を開けていたことが実測された）。既存ファイルは
    # `looks_like` を通ってしまうので、**「今回書いたか」を確定させる判定が要る**。
    # 書き出しの前に消す設計にしたので、在るかどうかを見るだけで確定する。
    proc, after, body = run_case("nothing_but_ok", output_body=GOOD_SVG)
    check(
        proc.returncode != 0,
        "**何も書かない CLI を、既存の有効な書き出しがあると成功と判定した**",
        proc.stdout,
    )
    check(
        recorded(after) != fresh,
        "**何も書かなかったのに記録が進んだ**（検出できない状態を自分で作っている）",
        proc.stdout,
    )
    check(body == GOOD_SVG, "既存の書き出しが復元されていない", str(body))

    # --- タイムアウト -----------------------------------------------------------
    proc, after, body = run_case("hang")
    check(proc.returncode != 0, "タイムアウトを成功と判定した", proc.stdout)
    check("タイムアウト" in proc.stdout, "タイムアウトの理由が報告されていない", proc.stdout)
    check(recorded(after) != fresh, "タイムアウトしたのに記録が進んだ", proc.stdout)
    check(body == GOOD_SVG, "タイムアウトで既存の書き出しが失われた", str(body))

    # --- 既存の書き出しが無い状態で失敗したら、中途半端なファイルを残さない -------
    proc, after, body = run_case("broken_then_ok", output_body=None)
    check(proc.returncode != 0, "壊れた書き出しを成功と判定した（新規）", proc.stdout)
    check(body is None, "失敗したのに壊れたファイルが残った（新規作成の経路）", str(body))

    # --- 書かずに非ゼロ ---------------------------------------------------------
    proc, after, body = run_case("fail_only")
    check(proc.returncode != 0, "CLI の失敗を成功と判定した", proc.stdout)
    check(recorded(after) != fresh, "CLI が失敗したのに記録が進んだ", proc.stdout)
    check(body == GOOD_SVG, "CLI の失敗で既存の書き出しが失われた", str(body))

    # --- CLI が存在しない -------------------------------------------------------
    with tempfile.TemporaryDirectory(prefix="ted-missing-") as tmp:
        root = Path(tmp) / "repo"
        assert root.resolve() != REAL_REPO
        (root / "scripts").mkdir(parents=True)
        (root / "diagrams").mkdir(parents=True)
        (root / "diagrams" / "one.drawio").write_text(SRC, encoding="utf-8")
        manifest = {KEY: {"output": OUT, "fingerprint": fp("old", OUT)}}
        (root / "diagrams" / "exports.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (root / "docs" / "images").mkdir(parents=True)
        (root / OUT).write_text(GOOD_SVG, encoding="utf-8")
        (root / "scripts" / SCRIPT.name).write_text(
            SCRIPT.read_text(encoding="utf-8"), encoding="utf-8"
        )
        (root / "scripts" / SHARED.name).write_text(
            SHARED.read_text(encoding="utf-8"), encoding="utf-8"
        )
        env = dict(os.environ)
        env["DRAWIO"] = "/nonexistent/drawio"
        proc = subprocess.run(
            [sys.executable, str(root / "scripts" / SCRIPT.name), "one"],
            cwd=root, capture_output=True, text=True, env=env,
        )
        after = json.loads((root / "diagrams" / "exports.json").read_text(encoding="utf-8"))
        check(proc.returncode != 0, "CLI が無いのに成功と判定した", proc.stdout)
        check(recorded(after) != fp(SRC, OUT), "CLI が無いのに記録が進んだ", proc.stdout)
        check("見つからない" in proc.stdout, "CLI が無い理由が報告されていない", proc.stdout)
        check(
            (root / OUT).read_text(encoding="utf-8") == GOOD_SVG,
            "CLI が無いのに既存の書き出しが失われた",
        )

    # --- 宣言と要求の食い違いは黙って飛ばさない ---------------------------------
    proc, after, _ = run_case(
        "success",
        manifest={KEY: {"output": None, "note": "使っていない"}},
        output_body=None,
    )
    check(proc.returncode != 0, "`output: null` を名指しで書き出そうとして通った", proc.stdout)
    check("output: null" in proc.stdout, "`output: null` の理由が報告されていない", proc.stdout)

    # 引数なし（全件モード）では `output: null` を黙って飛ばす（宣言済みなので）
    proc, after, _ = run_case(
        "success",
        manifest={KEY: {"output": None, "note": "使っていない"}},
        args=[],
        output_body=None,
    )
    check(proc.returncode == 0, "全件モードで `output: null` を飛ばせなかった", proc.stdout)
    check("書き出す対象がない" in proc.stdout, "全件モードの報告が想定と違う", proc.stdout)

    # 知らない名前
    proc, _, _ = run_case("success", args=["nope"])
    check(proc.returncode != 0, "知らない名前で通った", proc.stdout)
    check("に無い" in proc.stdout, "知らない名前の理由が報告されていない", proc.stdout)

    # エントリの形が不正なら check スクリプトに回す
    proc, _, _ = run_case("success", manifest={KEY: "docs/images/one.svg"})
    check(proc.returncode != 0, "エントリの型が不正なのに通った", proc.stdout)
    check("形が不正" in proc.stdout, "エントリの型の理由が報告されていない", proc.stdout)

    check_mutations()

    if failures:
        print(f"{len(failures)} 件の失敗（{checks} 判定）:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"export-diagrams.py: 全 {checks} 判定に合格")
    return 0


# --- 変異テスト ----------------------------------------------------------------
#
# 失敗判定は 3 つ（終了コード・実在・中身）。1 つずつ潰して、
# **その判定が出していた理由が消えること**を確かめる。
#
# **mtime の判定は無い。** 以前は時刻と比べていたが、粒度の粗い環境向けに 1 秒の許容を
# 入れた結果、**何も書かない CLI を 1 秒の窓で見逃す**穴になっていた（2 パス目のレビューで
# 実測）。書き出しの前に出力を消す設計にして、判定を 1 つ減らした——
# **テストできない判定を足すより、判定を減らすほうが強い。**
#
# **判定は「記録が進むこと」ではなく「その理由が消えること」。** 4 つは重なっているので
# （空ファイルを書いて非ゼロ終了するケースは「非ゼロ終了」と「空のファイル」の両方で
# 捕まる）、1 つ潰しただけでは記録は進まない。**重なっていることは望ましい**——だから
# 「記録が進むこと」を要求すると、テストを弱いほうへ書き換える圧力になる。
# 要求すべきなのは**その判定が理由を出していたこと**である。
# なお「失敗したら記録が進まない」ほうは、変異なしのケースで全 behaviour について見ている。

MUTATIONS = [
    (
        "終了コードの判定を潰す",
        "    if proc.returncode != 0:",
        "    if False:",
        "write_then_fail",
        GOOD_SVG,
        "非ゼロ終了した",
    ),
    (
        "中身の検査を潰す",
        "    if broken is not None:",
        "    if False:",
        "broken_then_ok",
        GOOD_SVG,
        "壊れている",
    ),
    (
        # 条件を潰すと下流の `stat()` が存在しないファイルでクラッシュする
        # （実在確認がそれを防いでいる証拠だが、クラッシュは「指摘が消えた」と区別できない）。
        # **診断の行だけ**を消す形にする。
        "実在の確認を潰す",
        '        return reject("書き出しが作られなかった（rc=0）", proc)',
        "        return False",
        "nothing_but_ok",
        None,
        "作られなかった",
    ),
]


def check_mutations() -> None:
    original = SCRIPT.read_text(encoding="utf-8")

    for label, old, new, behaviour, body, expected in MUTATIONS:
        check(original.count(old) == 1, f"変異の対象が一意でない（{label}）: {old!r}")
        if original.count(old) != 1:
            continue
        global _MUTATED_SCRIPT
        _MUTATED_SCRIPT = original.replace(old, new)
        try:
            proc, _, _ = run_case(behaviour, output_body=body)
        finally:
            _MUTATED_SCRIPT = None
        check(
            expected not in proc.stdout,
            f"変異が生き残った（{label}）——{expected!r} の指摘が別の判定から出ている",
            proc.stdout[-300:],
        )
        check(
            "Traceback" not in proc.stderr,
            f"変異でクラッシュした（{label}）——指摘が消えたのではなく落ちている",
            proc.stderr[-300:],
        )

    check(
        SCRIPT.read_text(encoding="utf-8") == original,
        "変異テストが実スクリプトを書き換えた",
    )


if __name__ == "__main__":
    sys.exit(main())
