#!/usr/bin/env python3
"""scripts/link-skills.sh の回帰テスト。

    python3 scripts/test-link-skills.py

なぜ必要か（#57）: 同じ symlink 手順を README と docs に手で複製していたところ、
4 ラウンド連続で実バグが出た。しかも毎回「前ラウンドの修正が次の穴を開ける」形だった。
手続きをスクリプトに集めたので、壊れ方をテストで固定する。

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリと偽 HOME を作り、
`HOME` を差し替えたうえで `-d` でも置き場所を明示する。#56 の周では「実環境を触るな」と
指示したサブエージェントが指示を破って本物の `~/.claude/skills/` を壊したので、
**指示ではなく構造で不可能にする**のがこのテストの設計方針。

判定は 3 条件（#56 で決めた I6）:

  (i)   元データが失われない
  (ii)  対象が古い中身や壊れた symlink を指したままにならない
  (iii) 失敗が黙って通らない（stderr にメッセージ、終了コードが非 0）

標準ライブラリのみ。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "link-skills.sh"

NEW = "NEW-FROM-REPO"
OLD = "OLD-WORKING-PERSONAL-SKILL"

# 実環境の置き場所。ここを対象にしてしまうテストは実行前に落とす。
#
# この歯止めは実害があってから入れた: 「HOME 未設定なら失敗するはず」というケースを
# `-d` 無しで書いたところ、**zsh は HOME が環境変数に無くてもパスワードデータベースから
# 補う**ため、そのケースだけが実際の ~/.claude/skills を書き換えた。
# 「実環境を触らない」は方針を書くだけでは守られないので、アサートで担保する。
REAL_SKILLS = (Path.home() / ".claude" / "skills").resolve()

failures: list[str] = []
checks = 0


def assert_sandboxed(skills_dir: Path) -> None:
    """対象が実環境なら即座に止める。"""
    resolved = skills_dir.resolve() if skills_dir.exists() else skills_dir.absolute()
    if resolved == REAL_SKILLS or REAL_SKILLS in resolved.parents:
        raise SystemExit(
            f"テストを中止しました: 対象が実環境を指しています ({resolved})。\n"
            "テストは必ず一時ディレクトリを対象にしてください。"
        )


def shells() -> list[str]:
    """使えるシェルを返す。dash は環境によって無いのでその場合は飛ばす。"""
    found = []
    for name in ("sh", "bash", "zsh", "dash"):
        path = shutil.which(name)
        if path:
            found.append(path)
    return found


def make_repo(root: Path, names: list[str], *, manifest: set[str] = frozenset(),
              no_skill_md: set[str] = frozenset()) -> Path:
    """偽リポジトリを作る（scripts/link-skills.sh は本物をコピーする）。"""
    (root / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT, root / "scripts" / "link-skills.sh")
    for name in names:
        d = root / "plugins" / name / "skills" / name
        d.mkdir(parents=True)
        if name not in no_skill_md:
            (d / "SKILL.md").write_text(NEW, encoding="utf-8")
        if name in manifest:
            (d / ".claude-plugin").mkdir()
            (d / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    return root / "scripts" / "link-skills.sh"


def run(script: Path, home: Path, *, args: list[str] | None = None,
        shell: str = "/bin/sh", skills_dir: Path | None = None
        ) -> subprocess.CompletedProcess:
    """スクリプトを一時環境で走らせる。

    **HOME は必ず一時ディレクトリに差し替える**（未設定にはしない —— zsh は HOME を
    自前で補うので、未設定にすると実環境が対象になる）。`skills_dir` を省略した場合は
    スクリプト側の既定 `$HOME/.claude/skills` を使う経路をテストすることになるが、
    その HOME も一時ディレクトリなので実害は無い。
    """
    assert_sandboxed(skills_dir if skills_dir is not None else home / ".claude" / "skills")
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "en_US.UTF-8",
        "HOME": str(home),
    }
    argv = [shell, str(script)]
    if skills_dir is not None:
        argv += ["-d", str(skills_dir)]
    argv += args or []
    return subprocess.run(argv, capture_output=True, text=True, env=env)


def check(label: str, condition: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}: {detail}")


def resolves_to_new(target: Path) -> bool:
    skill = target / "SKILL.md"
    return target.is_symlink() and skill.is_file() and skill.read_text(encoding="utf-8") == NEW


def old_survives(skills: Path) -> bool:
    if not skills.is_dir():
        return False
    return any(
        p.is_file() and p.read_text(encoding="utf-8", errors="ignore") == OLD
        for p in skills.rglob("*")
    )


# --------------------------------------------------------------------- 成功すべき状態

TARGET_STATES = [
    "absent",
    "real-dir",
    "empty-dir",
    "regular-file",
    "symlink",
    "dangling-symlink",
    "bak-is-dir",
    "bak-is-file",
    "skills-dir-missing",
]


def build_target(skills: Path, name: str, state: str) -> bool:
    """宛先の初期状態を作る。元データを置いたかを返す。"""
    if state != "skills-dir-missing":
        skills.mkdir(parents=True, exist_ok=True)
    t = skills / name
    if state == "real-dir":
        t.mkdir(); (t / "SKILL.md").write_text(OLD, encoding="utf-8"); return True
    if state == "empty-dir":
        t.mkdir(); return False
    if state == "regular-file":
        t.write_text(OLD, encoding="utf-8"); return True
    if state == "symlink":
        t.symlink_to("/tmp"); return False
    if state == "dangling-symlink":
        t.symlink_to(str(skills / "nowhere")); return False
    if state == "bak-is-dir":
        t.mkdir(); (t / "SKILL.md").write_text(OLD, encoding="utf-8")
        b = skills / f"{name}.bak"; b.mkdir(); (b / "x").write_text("pre", encoding="utf-8")
        return True
    if state == "bak-is-file":
        t.mkdir(); (t / "SKILL.md").write_text(OLD, encoding="utf-8")
        (skills / f"{name}.bak").write_text("pre", encoding="utf-8")
        return True
    return False


for shell in shells():
    tag_shell = Path(shell).name
    for state in TARGET_STATES:
        for spacey in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp) / ("my repo 日本語" if spacey else "repo")
                script = make_repo(base, ["cmux"])
                home = Path(tmp) / ("my home 日本語" if spacey else "home")
                skills = home / ".claude" / "skills"
                had_old = build_target(skills, "cmux", state)

                proc = run(script, home, shell=shell, skills_dir=skills)
                label = f"{tag_shell}/{'spacey' if spacey else 'plain'}/{state}"

                check(f"{label}: 終了コード 0", proc.returncode == 0,
                      f"rc={proc.returncode} err={proc.stderr.strip()[:90]!r}")
                check(f"{label}: symlink が解決する", resolves_to_new(skills / "cmux"),
                      f"out={proc.stdout.strip()[:90]!r} err={proc.stderr.strip()[:90]!r}")
                if had_old:
                    check(f"{label}: 元データが保全されている", old_survives(skills),
                          f"skills={[p.name for p in skills.iterdir()]}")

# ------------------------------------------------------- 冪等性（2 回連続で .bak が増えない）

for shell in shells():
    tag_shell = Path(shell).name
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"])
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "cmux").mkdir()
        (skills / "cmux" / "SKILL.md").write_text(OLD, encoding="utf-8")

        run(script, home, shell=shell, skills_dir=skills)
        run(script, home, shell=shell, skills_dir=skills)
        baks = [p.name for p in skills.iterdir() if ".bak" in p.name]
        check(f"{tag_shell}/idempotent: symlink が解決する", resolves_to_new(skills / "cmux"))
        check(f"{tag_shell}/idempotent: .bak が増えない", len(baks) == 1, f"baks={baks}")

# ------------------------------------------------------------------- 失敗すべき状態

for shell in shells():
    tag_shell = Path(shell).name

    # 1) skills ディレクトリが通常ファイル
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"])
        home = Path(tmp) / "home"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "skills").write_text("FILE", encoding="utf-8")
        proc = run(script, home, shell=shell)
        check(f"{tag_shell}/skills-is-file: 非 0 で終わる", proc.returncode != 0, f"rc={proc.returncode}")
        check(f"{tag_shell}/skills-is-file: stderr に理由", bool(proc.stderr.strip()))
        check(f"{tag_shell}/skills-is-file: 元ファイル健在",
              (home / ".claude" / "skills").read_text(encoding="utf-8") == "FILE")

    # 2) 退避先に書けない
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"])
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "cmux").mkdir()
        (skills / "cmux" / "SKILL.md").write_text(OLD, encoding="utf-8")
        os.chmod(skills, 0o500)
        try:
            proc = run(script, home, shell=shell, skills_dir=skills)
            check(f"{tag_shell}/readonly: 非 0 で終わる", proc.returncode != 0, f"rc={proc.returncode}")
            check(f"{tag_shell}/readonly: stderr に理由", bool(proc.stderr.strip()))
            check(f"{tag_shell}/readonly: 元データ健在", old_survives(skills))
            check(f"{tag_shell}/readonly: symlink を作っていない",
                  not (skills / "cmux").is_symlink())
        finally:
            os.chmod(skills, 0o700)

    # 3) ソースに SKILL.md が無い
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"], no_skill_md={"cmux"})
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "cmux").mkdir()
        (skills / "cmux" / "SKILL.md").write_text(OLD, encoding="utf-8")
        proc = run(script, home, shell=shell, skills_dir=skills, args=["cmux"])
        check(f"{tag_shell}/no-skill-md: 非 0 で終わる", proc.returncode != 0, f"rc={proc.returncode}")
        check(f"{tag_shell}/no-skill-md: 元データを触らない",
              (skills / "cmux" / "SKILL.md").read_text(encoding="utf-8") == OLD)

    # 4) ソースがマニフェストを持つ（素のスキルとして置くと名前空間が付いてしまう）
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"], manifest={"cmux"})
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        proc = run(script, home, shell=shell, skills_dir=skills, args=["cmux"])
        check(f"{tag_shell}/has-manifest: 非 0 で終わる", proc.returncode != 0, f"rc={proc.returncode}")
        check(f"{tag_shell}/has-manifest: symlink を作らない", not (skills / "cmux").exists())

    # 5) -d を省略したら $HOME/.claude/skills を使う
    #
    # 「HOME 未設定なら失敗する」を直接テストすることはできない。**zsh は HOME が環境変数に
    # 無くてもパスワードデータベースから補う**ので、未設定にすると実環境が対象になってしまう
    # （実際に一度やって、利用者の ~/.claude/skills を壊した）。既定パスの解決だけを見る。
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"])
        home = Path(tmp) / "home"
        home.mkdir()
        proc = run(script, home, shell=shell)  # -d を渡さない
        default_target = home / ".claude" / "skills" / "cmux"
        check(f"{tag_shell}/home-default: 終了コード 0", proc.returncode == 0,
              f"rc={proc.returncode} err={proc.stderr.strip()[:90]!r}")
        check(f"{tag_shell}/home-default: $HOME 配下に張られる", resolves_to_new(default_target),
              f"out={proc.stdout.strip()[:90]!r}")

    # 6) 不明なオプション
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"])
        proc = run(script, Path(tmp) / "home", shell=shell, args=["--nope"])
        check(f"{tag_shell}/bad-opt: 非 0 で終わる", proc.returncode != 0, f"rc={proc.returncode}")

# ------------------------------------------------ 相対パスで呼んでも壊れない（#56 の HIGH 相当）

for shell in shells():
    tag_shell = Path(shell).name
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "repo"
        make_repo(base, ["cmux"])
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "cmux").mkdir()
        (skills / "cmux" / "SKILL.md").write_text(OLD, encoding="utf-8")

        # clone の中から相対パスで起動する。#56 ではこれが壊れた symlink を作っていた。
        # run() を通さない直接呼び出しなので、歯止めを明示的にかける。
        assert_sandboxed(skills)
        proc = subprocess.run(
            [shell, "./scripts/link-skills.sh", "-d", str(skills)],
            cwd=str(base), capture_output=True, text=True,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home)},
        )
        check(f"{tag_shell}/relative-invocation: 終了コード 0", proc.returncode == 0,
              f"rc={proc.returncode} err={proc.stderr.strip()[:90]!r}")
        check(f"{tag_shell}/relative-invocation: symlink が解決する",
              resolves_to_new(skills / "cmux"),
              f"link={os.readlink(skills / 'cmux') if (skills / 'cmux').is_symlink() else 'not a symlink'}")
        check(f"{tag_shell}/relative-invocation: 元データが保全されている", old_survives(skills))

# ------------------------------------------------------------- 複数スキル・部分的な失敗

for shell in shells():
    tag_shell = Path(shell).name
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux", "dev-loop"], no_skill_md={"dev-loop"})
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        proc = run(script, home, shell=shell, skills_dir=skills, args=["cmux", "dev-loop"])
        check(f"{tag_shell}/partial: 非 0 で終わる", proc.returncode != 0, f"rc={proc.returncode}")
        check(f"{tag_shell}/partial: 健全な方は張られる", resolves_to_new(skills / "cmux"),
              f"err={proc.stderr.strip()[:90]!r}")
        check(f"{tag_shell}/partial: 壊れた方は張らない", not (skills / "dev-loop").exists())

# ------------------------------------------------------------------------- 引数なし = 全件

for shell in shells()[:1]:
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux", "dev-loop"])
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        proc = run(script, home, shell=shell, skills_dir=skills)
        check("all-plugins: 終了コード 0", proc.returncode == 0, f"rc={proc.returncode}")
        for n in ("cmux", "dev-loop"):
            check(f"all-plugins: {n} が張られる", resolves_to_new(skills / n))

# -------------------------------------------------------------------------- dry run

for shell in shells()[:1]:
    with tempfile.TemporaryDirectory() as tmp:
        script = make_repo(Path(tmp) / "repo", ["cmux"])
        home = Path(tmp) / "home"
        skills = home / ".claude" / "skills"
        proc = run(script, home, shell=shell, skills_dir=skills, args=["-n"])
        check("dry-run: 終了コード 0", proc.returncode == 0, f"rc={proc.returncode}")
        check("dry-run: 何も作らない", not skills.exists(), f"skills exists={skills.exists()}")
        check("dry-run: 予定を表示する", "cmux" in proc.stdout)


# -------------------------------------------------------------------------- 集計

print(f"link-skills.sh のテスト: {checks} 件の判定")
if failures:
    print(f"\n{len(failures)} 件失敗:\n")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print(f"シェル: {', '.join(Path(s).name for s in shells())}")
print("すべて合格")
