#!/usr/bin/env python3
"""scripts/check-plugin-versions.py の SKILL.md 版チェックの回帰テスト。

    python3 scripts/test-check-plugin-versions.py

なぜ必要か（#63）: 「version を上げれば届く」は誤りで、利用者のカタログが凍結していると
**version の変化自体が見えない**。リポジトリ側からできる歯止めは、SKILL.md 本文に版を書いて
**古いキャッシュが読まれたら目に入る**ようにすることだけ。その歯止めが効かなくなっていたら
意味が無いので、ここで固定する。

**歯止めは「落として黙って免除する」形で破られる**（#62 の教訓）。この検査は、
レビューのたびに同じ形で穴が見つかった:

| 落としていたもの | どう塞いだか |
| --- | --- |
| 可視テキスト（コメントだけ検査していた） | 両方を検査する。**守りたいのは可視テキストのほう** |
| ルート直下 `SKILL.md`（公式レイアウト） | — |
| `plugin.json` の `skills` フィールド（`impeccable` が実使用） | レイアウトの列挙をやめ、`rglob` で全部拾う |
| 複数行の HTML コメントによる無効化 | 読者に見えない部分を**先に落としてから**探す |
| `~~~` フェンス（``` しか見ていなかった） | 同上。逆に例示フェンスの誤検出も止まる |

**レイアウトや書式を列挙して判定する限り、知らない形が残り続けた。**
「全部拾ってから、見えない部分を落とす」に変えて初めて収束した。ここに固定して再発を止める。

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリを作り、そこだけを対象にする。
実リポジトリを対象にしてしまうテストは**実行前にアサートで落とす**
（`test-link-skills.py` と同じ設計方針）。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-plugin-versions.py"

# 実リポジトリ。ここを対象にしてしまうテストは実行前に落とす。
REAL_REPO = REPO_ROOT.resolve()

failures: list[str] = []
checks = 0


def check(condition: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def check_rejected(proc: subprocess.CompletedProcess[str], expected: str, label: str) -> None:
    """「落ちること」だけでなく、**期待した理由で落ちたこと**まで見る。

    終了コードだけを見ると、**クラッシュも合格になる**。実際、`if not found:` を潰す変異は
    `IndexError` で落ちて stdout が空になるが、`returncode != 0` しか見ていない判定は
    22 件すべて通ってしまった——**fail-closed の保証が固定できていなかった**。
    この周で「別の理由で通るテスト」を踏むのは 3 度目なので、否定側は全部これを使う。
    """
    check(proc.returncode != 0, f"{label}（落ちなかった）", proc.stdout)
    check(
        expected in proc.stdout,
        f"{label}（落ちたが理由が違う。期待: {expected!r}）",
        (proc.stdout + proc.stderr)[-400:],
    )


def skill_md(
    *,
    comment: str | None,
    visible: str | None,
    name: str = "demo",
    extra: str = "",
) -> str:
    """SKILL.md の中身。`None` を渡すとその記載を省く。"""
    lines = [
        "---",
        f"name: {name}",
        "description: テスト用",
        "---",
        "",
        f"# {name} スキル",
        "",
    ]
    if comment is not None:
        lines.append(f"<!-- skill-version: {comment} -->")
    if visible is not None:
        lines.append(f"> **このスキルの版: {visible}**（プラグイン `{name}`）。")
    if extra:
        lines.append(extra)
    lines += ["", "本文。"]
    return "\n".join(lines) + "\n"


def build(root: Path, plugins: dict[str, dict], docs: dict[str, str] | None = None) -> None:
    """偽リポジトリを組み立てる。

    `plugins` は {ディレクトリ名: {"version": str, "skills": {相対パス: 中身}}}。
    相対パスは `SKILL.md`（ルート直下）や `skills/foo/SKILL.md` を取る。
    """
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの作業ディレクトリが実リポジトリの内側にある"
    )

    entries = []
    for name, spec in plugins.items():
        entries.append(
            {
                "name": name,
                "source": f"./plugins/{name}",
                "version": spec["version"],
                "description": f"{name} の説明",
            }
        )
        manifest_dir = root / "plugins" / name / ".claude-plugin"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = {"name": name, "version": spec["version"], "description": f"{name} の説明"}
        manifest.update(spec.get("manifest_extra", {}))
        (manifest_dir / "plugin.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for rel, body in spec.get("skills", {}).items():
            path = root / "plugins" / name / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    for rel_path, body in (docs or {}).items():
        page = root / "docs" / rel_path
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(body, encoding="utf-8")

    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(
            {"name": "test-catalog", "owner": {"name": "tester"}, "plugins": entries},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def run_case(
    plugins: dict[str, dict], docs: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """偽リポジトリを作り、そこに**スクリプトをコピーして**走らせる。

    `check-plugin-versions.py` は `REPO_ROOT = Path(__file__).parent.parent` で対象を
    決める（cwd ではない）。実リポジトリの側から呼ぶと**偽リポジトリではなく実リポジトリを
    検査してしまい、テストが常に通る**——最初に書いたときに実際にそうなっていた。
    コピーして走らせることで、対象が偽リポジトリになる。
    """
    with tempfile.TemporaryDirectory(prefix="cpv-test-") as tmp:
        root = Path(tmp) / "repo"
        (root / "scripts").mkdir(parents=True)
        build(root, plugins, docs)
        copied = root / "scripts" / SCRIPT.name
        copied.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(copied)], cwd=root, capture_output=True, text=True
        )


def main() -> int:
    ok = skill_md(comment="1.0.0", visible="1.0.0")

    # 正常系: コメントも可視テキストも一致 → 通る
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": ok}}})
    check(proc.returncode == 0, "版が揃っているのに落ちた", proc.stdout)

    # SKILL.md を 1 つも持たないプラグインは検査対象なし（workspace-setup がこの形）
    proc = run_case({"demo": {"version": "1.0.0"}})
    check(proc.returncode == 0, "SKILL.md を持たないプラグインで落ちた", proc.stdout)

    # コメントの版がずれる
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {"skills/demo/SKILL.md": skill_md(comment="9.9.9", visible="1.0.0")},
            }
        }
    )
    check_rejected(proc, "版のコメントが 9.9.9", "コメントの版ずれがすり抜けた")

    # **可視テキストの版だけずれる**（初版が見逃していた形）
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {"skills/demo/SKILL.md": skill_md(comment="1.0.0", visible="0.1.0")},
            }
        }
    )
    check_rejected(proc, "版の可視テキストが 0.1.0", "可視テキストの版ずれがすり抜けた（守りたいのはこちら）")

    # 記載が無い（コメント / 可視テキストそれぞれ）
    for missing, label in (("comment", "コメント"), ("visible", "可視テキスト")):
        body = skill_md(
            comment=None if missing == "comment" else "1.0.0",
            visible=None if missing == "visible" else "1.0.0",
        )
        proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": body}}})
        check_rejected(proc, f"版の{label}が無い", f"版の{label}が無いのに通った（fail-open）")

    # 記載が 2 つある
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {
                    "skills/demo/SKILL.md": skill_md(
                        comment="1.0.0", visible="1.0.0", extra="<!-- skill-version: 1.0.0 -->"
                    )
                },
            }
        }
    )
    check_rejected(proc, "版のコメントが 2 個ある", "版の記載が 2 つあるのに通った")

    # **skills/ を持たず、プラグインルート直下に SKILL.md を置く公式レイアウト**
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {"SKILL.md": skill_md(comment=None, visible=None)},
            }
        }
    )
    check_rejected(
        proc, "版のコメントが無い",
        "ルート直下 SKILL.md のプラグインが無検査で免除された（受入基準 2-e）",
    )

    proc = run_case(
        {"demo": {"version": "1.0.0", "skills": {"SKILL.md": ok}}}
    )
    check(proc.returncode == 0, "ルート直下 SKILL.md で版が揃っているのに落ちた", proc.stdout)

    # **`plugin.json` の `skills` フィールドで任意のパスに置いた場合**
    # （この環境の `impeccable` が実際に使っているレイアウト）
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                # 実データ（impeccable）は**文字列**。配列を取る実装もありうるので両方試す
                "manifest_extra": {"skills": "./custom/mine"},
                "skills": {"custom/mine/SKILL.md": skill_md(comment=None, visible=None)},
            }
        }
    )
    check_rejected(proc, "版のコメントが無い", "`skills` フィールドで置いたスキルが無検査で免除された")

    # **可視テキストを HTML コメントで囲って無効化**しても合格させない
    # （読者には見えないのに CI 緑、という状態を作らせない）
    body = skill_md(comment="1.0.0", visible=None)
    body = body.replace("本文。", "<!-- > **このスキルの版: 1.0.0**（無効化） -->\n本文。")
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": body}}})
    check_rejected(proc, "版の可視テキストが無い", "コメントアウトした可視テキストで合格した")

    # **複数行の HTML コメント**で囲って無効化しても合格させない。
    # 実際のマーカーは 5 行のブロック引用なので、**無効化する現実的な方法はこちら**。
    # 単一行の囲みだけ塞いでいたときは、起きにくい側だけを守っていた。
    multiline = skill_md(comment="1.0.0", visible=None)
    multiline = multiline.replace(
        "本文。", "<!--\n> **このスキルの版: 1.0.0**（プラグイン `demo`）。\n-->\n本文。"
    )
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": multiline}}})
    check_rejected(proc, "版の可視テキストが無い", "複数行コメントで囲った可視テキストで合格した")

    # **コードフェンスの中**の記載も、読者には版として見えないので数えない（``` と ~~~ の両方）
    for fence in ("```", "~~~"):
        fenced = skill_md(comment="1.0.0", visible=None)
        fenced = fenced.replace(
            "本文。", f"{fence}\n> **このスキルの版: 1.0.0**\n{fence}\n本文。"
        )
        proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": fenced}}})
        check_rejected(proc, "版の可視テキストが無い", f"`{fence}` フェンス内の可視テキストで合格した")

    # **フェンスは開いたのと同じ文字でしか閉じない。** ``` を `~~~` で閉じたつもりの
    # 壊れた文書では、以降が全部フェンス内のままになり、本物のマーカーも数えられない
    # → 記載なしでエラー（fail-closed）。閉じ文字を見ない実装だと、ここが素通りする。
    mixed = skill_md(comment=None, visible=None)
    mixed = mixed.replace(
        "本文。",
        "```\n例\n~~~\n\n<!-- skill-version: 1.0.0 -->\n"
        "> **このスキルの版: 1.0.0**（プラグイン `demo`）。\n\n本文。",
    )
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": mixed}}})
    check_rejected(
        proc, "版のコメントが無い",
        "``` を `~~~` で閉じた壊れた文書が素通りした（閉じ文字を見ていない）",
    )

    # 逆側: **規約を例示しているだけのフェンス**を「2 個ある」と誤検出しない
    # （CLAUDE.md がまさにこの例を載せているので、SKILL.md に写されうる）
    for fence in ("```", "~~~"):
        documented = skill_md(comment="1.0.0", visible="1.0.0")
        documented = documented.replace(
            "本文。",
            f"版はこう書く:\n\n{fence}markdown\n<!-- skill-version: 9.9.9 -->\n"
            f"> **このスキルの版: 9.9.9**（プラグイン `demo`）。\n{fence}\n\n本文。",
        )
        proc = run_case(
            {"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": documented}}}
        )
        check(
            proc.returncode == 0,
            f"`{fence}` の例示ブロックを数えて誤検出した",
            proc.stdout,
        )

    # **1 行に 2 つ**並べても数える（古い版を同じ行に残せてしまう）
    for extra_line, label in (
        ("<!-- skill-version: 1.0.0 --> <!-- skill-version: 0.0.1 -->", "コメント"),
        ("> **このスキルの版: 1.0.0** 旧 **このスキルの版: 0.0.1**", "可視テキスト"),
    ):
        one_line = skill_md(
            comment=None if label == "コメント" else "1.0.0",
            visible=None if label == "可視テキスト" else "1.0.0",
            extra=extra_line,
        )
        proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": one_line}}})
        check_rejected(proc, f"版の{label}が 2 個ある", f"1 行に 2 つ並べた{label}がすり抜けた")

    # **4 個の ` で開いた囲み**は内側の ``` では閉じない
    # （``` を含む例を載せるときの標準的な書き方。長さを見ないと例が本文に漏れる）
    nested = skill_md(comment="1.0.0", visible="1.0.0")
    nested = nested.replace(
        "本文。",
        "````markdown\n```\n<!-- skill-version: 9.9.9 -->\n"
        "> **このスキルの版: 9.9.9**（プラグイン `demo`）。\n```\n````\n\n本文。",
    )
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": nested}}})
    check(proc.returncode == 0, "4 個の ` で囲った例示が本文に漏れた", proc.stdout)

    # **散文の中のインラインコード**や**字下げの例示**を「本物が 2 個」と誤検出しない
    for label, snippet in (
        ("インラインコード", "版は `<!-- skill-version: 9.9.9 -->` と書く。"),
        ("字下げの例示", "    <!-- skill-version: 9.9.9 -->"),
    ):
        prose = skill_md(comment="1.0.0", visible="1.0.0")
        prose = prose.replace("本文。", snippet + "\n\n本文。")
        proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": prose}}})
        check(proc.returncode == 0, f"{label}を本物として数えた", proc.stdout)

    # **散文の途中**に同じ文字列があっても、可視マーカーとしては数えない
    # （`> ` は行頭にあって初めて引用になる。ここが行頭要求の役目で、
    #  コメントでの無効化を防いでいるのは別の仕組み＝コメント除去のほう）
    midline = skill_md(comment="1.0.0", visible="1.0.0")
    midline = midline.replace("本文。", "以前は > **このスキルの版: 9.9.9** と書いていた。\n\n本文。")
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": midline}}})
    check(proc.returncode == 0, "散文の途中の文字列を可視マーカーとして数えた", proc.stdout)

    # **記載が末尾にある**と、起動しても目に入らないので目的を果たさない
    late = skill_md(comment=None, visible=None)
    late = late.replace(
        "本文。",
        "本文。\n\n## 詳細\n\n<!-- skill-version: 1.0.0 -->\n"
        "> **このスキルの版: 1.0.0**（プラグイン `demo`）。",
    )
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": late}}})
    check_rejected(proc, "最初の見出し節より後ろ", "版の記載が末尾にあっても通った")

    # **複数プラグイン**のうち、2 つ目だけ古い（1 つ目しか見ない退行を捕まえる）。
    #
    # **終了コードだけを見てはいけない。** 1 つ目しか検査しない実装でも、2 つ目が
    # 「カタログに載っていない」扱いになって別の理由で非 0 になり、**テストは通ってしまう**。
    # 実際にその変異が生き残った。**版ずれの指摘そのものが出ているか**を確かめる。
    proc = run_case(
        {
            "first": {"version": "1.0.0", "skills": {"skills/first/SKILL.md": skill_md(
                comment="1.0.0", visible="1.0.0", name="first")}},
            "second": {"version": "2.0.0", "skills": {"skills/second/SKILL.md": skill_md(
                comment="0.0.1", visible="0.0.1", name="second")}},
        }
    )
    check_rejected(proc, "second", "2 つ目のプラグインの版ずれがすり抜けた")
    check(
        "second" in proc.stdout and "0.0.1" in proc.stdout,
        "2 つ目のプラグインの版ずれが、指摘として出ていない",
        proc.stdout,
    )

    # スキルが複数あり、片方だけ記載漏れ
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {
                    "skills/one/SKILL.md": skill_md(comment="1.0.0", visible="1.0.0", name="one"),
                    "skills/two/SKILL.md": skill_md(comment=None, visible=None, name="two"),
                },
            }
        }
    )
    check_rejected(proc, "版のコメントが無い", "複数スキルの片方の記載漏れがすり抜けた")

    # --- 公開サイトへの絶対リンクの検査（check_site_links） ---
    #
    # SKILL.md は docs_dir の外にあり、リンクは絶対 URL なので **mkdocs は検証しない**。
    # #61 / #64 で根拠を設計ドキュメントへ移し、本文にはリンクだけを残したので、
    # ここが切れると移した先に辿り着けなくなる。

    SITE = "https://hdknr.github.io/claude-code-setup/"
    DOC = "# 設計\n\n## 節 { #verify }\n\n本文。\n"

    def with_link(link: str) -> dict:
        body = skill_md(comment="1.0.0", visible="1.0.0")
        return {
            "demo": {
                "version": "1.0.0",
                "skills": {"skills/demo/SKILL.md": body.replace("本文。", f"根拠は {link}。")},
            }
        }

    # 解決するリンクは通る
    proc = run_case(with_link(f"[設計]({SITE}plugins/design/#verify)"), {"plugins/design.md": DOC})
    check(proc.returncode == 0, "解決するリンクで落ちた", proc.stdout)

    # 存在しないアンカー → 落ちる
    proc = run_case(with_link(f"[設計]({SITE}plugins/design/#nope)"), {"plugins/design.md": DOC})
    check_rejected(proc, "アンカー #nope", "存在しないアンカーがすり抜けた")

    # 存在しないページ → 落ちる
    proc = run_case(with_link(f"[設計]({SITE}plugins/missing/#verify)"), {"plugins/design.md": DOC})
    check_rejected(proc, "指すページが docs/ に無い", "存在しないページがすり抜けた")

    # **本文やコード例に書かれただけの `{ #x }` を数えない**（見出し行だけを見る）
    prose_doc = "# 設計\n\n書き方: `{ #ghost }` のように書く。\n\n## 節 { #verify }\n"
    proc = run_case(with_link(f"[設計]({SITE}plugins/design/#ghost)"), {"plugins/design.md": prose_doc})
    check_rejected(proc, "アンカー #ghost", "散文中の `{ #x }` を本物として数えた")

    # **自動 id は認めない**（見出しを足すとずれるため。#66 で実際に踏んだ）
    proc = run_case(with_link(f"[設計]({SITE}plugins/design/#_5)"), {"plugins/design.md": DOC})
    check_rejected(proc, "アンカー #_5", "自動生成 id へのリンクを通した")

    # URL の切れ目: バッククォート・和文の句読点・自動リンクで誤検出しない
    for label, link in (
        ("バッククォート", f"`{SITE}plugins/design/#verify`"),
        ("句点", f"{SITE}plugins/design/#verify。次の文"),
        ("読点", f"{SITE}plugins/design/#verify、続き"),
        ("自動リンク", f"<{SITE}plugins/design/#verify>"),
        ("全角括弧", f"（{SITE}plugins/design/#verify）"),
    ):
        proc = run_case(with_link(link), {"plugins/design.md": DOC})
        check(proc.returncode == 0, f"{label}で囲んだ正しいリンクで落ちた", proc.stdout)

    # `docs/<path>/index.md` 形式のページも解決する
    proc = run_case(with_link(f"[設計]({SITE}plugins/#verify)"), {"plugins/index.md": DOC})
    check(proc.returncode == 0, "index.md 形式のページを解決できなかった", proc.stdout)

    if failures:
        print(f"{len(failures)} 件の失敗（{checks} 判定）:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"check-plugin-versions.py の版チェック: 全 {checks} 判定に合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
