#!/usr/bin/env python3
"""`prepare-worktree.sh` と `check-pr-preconditions.sh` の回帰テスト。

    python3 scripts/test-worktree-scripts.py

**本体は `scripts/` に無い。** `plugins/dev-loop/skills/dev-loop/scripts/` にある
——**`dev-loop` はどのリポジトリでも使うスキル**で、**対象リポジトリの `scripts/` に
在ることを当てにできない**（**段 1 でここを間違えて PR に出し、マージ後に気づいた**）。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリを作り、そこだけを
対象にする（`assert_not_real_repo` がそれを担保する）。
**本体は `git rev-parse` で自分のいるリポジトリを解決する**ので、
**歯止めが無いと、テストがこのリポジトリに worktree を作ってしまう。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**「守る」の行数と変異の数が 1 対 1 か**は、**テスト自身が数える。**

**#148 で 2 つ目の主題が入った**——**周の base をどこから取るか**である。
**`prepare-worktree.sh` の start-point**（変異で当てる）と、
**関門に渡す差分の取り方**（`main()` の末尾。**陽性対照つきの実証**で、
スクリプトの変異とは独立している）の 2 つを見る。

**散文では検証できなかった分岐を、ここで初めて検証している**——
`SKILL.md` 手順 4 の入場手順は **#96 / #110 / #113 で繰り返し穴が見つかった**のに、
**テストが 1 本も無かった**（#136）。
"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts"
PREPARE = SKILL_SCRIPTS / "prepare-worktree.sh"
PRECOND = SKILL_SCRIPTS / "check-pr-preconditions.sh"

failures: list[str] = []


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _build_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    assert_not_real_repo(root)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "t")
    (root / "README.md").write_text("x\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


def run(script: Path, cwd: Path, *args, env=None):
    return subprocess.run(["bash", str(script), *args], cwd=cwd,
                          capture_output=True, text=True, env=env)


def fake_git_dir(base: Path) -> Path:
    """**`rev-parse` は本物に通し、`worktree` と `branch` だけ失敗させる `git`。**

    **これが無いと、exit 6 の守り（既存の一覧を見られなかったときに作らない）に
    専用の観測が無い**——**壊しても全項目 ok のままになる**（3 巡目の Verifier が
    実験で示した。**スクリプト側に「間接的に当たっている」と書いていたのは誤りだった**）。
    """
    d = base / "fakebin"
    d.mkdir(parents=True, exist_ok=True)
    real = subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip()
    (d / "git").write_text(
        "#!/usr/bin/env bash\n"
        'case "$1" in\n'
        "  worktree|branch) echo 'fake: refusing' >&2; exit 1 ;;\n"
        f'  *) exec {real} "$@" ;;\n'
        "esac\n", encoding="utf-8")
    (d / "git").chmod(0o755)
    return d


def _build_ahead_clones(base: Path) -> dict:
    """**origin が、手元より進んでいるクローン**を 2 つ作る（#148）。

    **2 つ要る理由は、変異を*見分ける*ためである。** 「start-point を渡さない」と
    「取り直さない」は、**取得していない側だけを見ると、どちらも同じ出力（古い側で切る）**
    になる。**取得済みの側を併せて見ると、前者は古いまま・後者は新しい側**に分かれる。
    **1 つの場面だけでは、2 つの変異が区別できない。**
    """
    bare = base / "origin.git"
    bare.mkdir(parents=True)
    assert_not_real_repo(bare)
    git(bare, "init", "-q", "--bare", "-b", "main")

    seed = base / "seed"
    seed.mkdir(parents=True)
    assert_not_real_repo(seed)
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "t@example.invalid")
    git(seed, "config", "user.name", "t")
    (seed / "README.md").write_text("A\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "A")
    git(seed, "remote", "add", "origin", str(bare))
    git(seed, "push", "-q", "origin", "main")
    sha_a = git(seed, "rev-parse", "HEAD").stdout.strip()

    clones = {}
    # **「未取得(専用)」は、この場面だけに使う。** **他の観測で 1 度でも走らせると、
    # その実行が取り直してしまい、「まだ取れていない」という前提が壊れる**
    # ——**実際にそうなっており、変異が殺せなかった。**
    for label in ("未取得", "取得済み", "未取得(専用)"):
        work = base / f"work-{ {'未取得': 'stale', '取得済み': 'fresh'}.get(label, 'sibling') }"
        res = subprocess.run(["git", "clone", "-q", str(bare), str(work)],
                             capture_output=True, text=True)
        # **rc を見る。** 見ないと、clone の失敗が次の `git config` の
        # `FileNotFoundError` になり、**変異ループの `except Exception` が
        # 「変異を殺せた」に化けさせる**（`/code-review` の指摘 11）。
        assert res.returncode == 0, f"clone に失敗した: {res.stderr}"
        assert_not_real_repo(work)
        git(work, "config", "user.email", "t@example.invalid")
        git(work, "config", "user.name", "t")
        clones[label] = work

    # **他人の作業**が origin に入る（クローンより後）
    (seed / "OTHER.md").write_text("other\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "B: 他人の作業")
    git(seed, "push", "-q", "origin", "main")
    sha_b = git(seed, "rev-parse", "HEAD").stdout.strip()

    # **クローンより後に origin へ生えたブランチ**（どちらのクローンにも参照が無い）。
    # **名指ししても、取り直さなければ解決できない**——指摘 1 の場面。
    git(seed, "checkout", "-q", "-b", "sibling")
    (seed / "SIB.md").write_text("sib\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "sibling")
    git(seed, "push", "-q", "origin", "sibling")
    sha_sib = git(seed, "rev-parse", "HEAD").stdout.strip()
    git(seed, "checkout", "-q", "main")

    git(clones["取得済み"], "fetch", "-q", "origin")
    return {"clones": clones, "A": sha_a, "B": sha_b, "SIB": sha_sib,
            "bare": bare, "seed": seed}


def _build_dangling_origin_head(base: Path) -> Path:
    """**`refs/remotes/origin/HEAD` が実在しない参照を指しているクローン**を作る（#148）。

    上流で既定ブランチが改名され、こちらの `origin/HEAD` が古い名前を指したまま、
    という形。**`git symbolic-ref` はこれでも成功する**ので、
    **検証しないと `git worktree add` が `fatal` で死ぬ。**
    """
    bare = base / "origin.git"
    bare.mkdir(parents=True)
    assert_not_real_repo(bare)
    git(bare, "init", "-q", "--bare", "-b", "main")
    seed = base / "seed"
    seed.mkdir(parents=True)
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "t@example.invalid")
    git(seed, "config", "user.name", "t")
    (seed / "README.md").write_text("A\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "A")
    git(seed, "remote", "add", "origin", str(bare))
    git(seed, "push", "-q", "origin", "main")

    work = base / "work"
    res = subprocess.run(["git", "clone", "-q", str(bare), str(work)],
                         capture_output=True, text=True)
    assert res.returncode == 0, f"clone に失敗した: {res.stderr}"
    assert_not_real_repo(work)
    git(work, "config", "user.email", "t@example.invalid")
    git(work, "config", "user.name", "t")
    # **実在しない名前を指させる**（上流の改名を模す）
    git(work, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master")
    return work


# **足場は 1 度だけ作り、使うたびに複製する**（#449）。**`observe()` は 21 回走る**
# （正しい版 1 ＋ 変異 20）ので、足場を毎回 `git init`・`commit`・`clone`・`push` で
# 組み直すと、**それだけで子プロセスが 1 回に 50 本ほど増える**——`check-all.py` の中の
# `check-mutation-claims.py` で、この 1 本が打ち切り（300 秒）に届いたことがある（3 回中 2 回。原因は特定していない）。
# **複製は使い捨てで、観測どうしは今までどおり足場を共有しない。**
_templates: dict[str, tuple[Path, object]] = {}
_template_root: tempfile.TemporaryDirectory | None = None


def _from_template(key: str, build, dest: Path):
    """`build` で作った雛形を `dest` に複製し、**複製の中のパスに付け替えた**戻り値を返す。"""
    global _template_root
    if _template_root is None:
        _template_root = tempfile.TemporaryDirectory()
    if key not in _templates:
        src = Path(_template_root.name) / key
        _templates[key] = (src, build(src))
    src, built = _templates[key]
    dest.parent.mkdir(parents=True, exist_ok=True)
    assert_not_real_repo(dest.parent)
    shutil.copytree(src, dest, symlinks=True, dirs_exist_ok=True)
    assert_not_real_repo(dest)
    # **remote は雛形の bare を絶対パスで指している。** **付け替えないと、複製から
    # push した先が雛形になり、次の複製に他の観測の書き込みが見える**
    # （`demonstrate_base_rule` は seed から push する）。
    for config in dest.rglob("config"):
        text = config.read_text(encoding="utf-8")
        if str(src) in text:
            config.write_text(text.replace(str(src), str(dest)), encoding="utf-8")
    left = [c for c in dest.rglob("config") if str(src) in c.read_text(encoding="utf-8")]
    assert not left, f"複製が雛形を指したまま: {left}"

    def moved(value):
        if isinstance(value, Path):
            return dest / value.relative_to(src)
        if isinstance(value, dict):
            return {k: moved(v) for k, v in value.items()}
        return value
    return moved(built)


def make_repo(root: Path) -> Path:
    return _from_template("repo", _build_repo, root)


def make_ahead_clones(base: Path) -> dict:
    return _from_template("ahead", _build_ahead_clones, base)


def make_dangling_origin_head(base: Path) -> Path:
    return _from_template("dangling", _build_dangling_origin_head, base)


def observe(prepare: Path, precond: Path, base: Path) -> dict:
    """両スクリプトの分岐をまとめて観測する。**1 回の観測で 1 つの偽リポジトリを使い切る。**"""
    repo = make_repo(base / "repo")
    first = run(prepare, repo, "42", "sample")
    again = run(prepare, repo, "42", "sample")
    bad_num = run(prepare, repo, "abc", "x")
    wt = repo / ".claude" / "worktrees" / "issue-42"
    out = {
        "新規で作れる": first.returncode,
        # **出力も観測する。** 終了コードとファイルシステムだけ見ていると、
        # **「確認の材料を出す」という約束の変異が殺せない**（最初そうなっていた）。
        "確認の材料が出ている": ("ブランチ: issue/42-sample" in first.stdout
                                and "起点:" in first.stdout),
        "2 回目は断る": again.returncode,
        "数字以外は断る": bad_num.returncode,
        "作られた場所": wt.is_dir(),
        "切られたブランチ": git(wt, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if wt.is_dir() else "",
    }
    if wt.is_dir():
        out["前提条件: 一致"] = run(precond, wt, "issue/42-sample").returncode
        out["前提条件: 不一致"] = run(precond, wt, "issue/999-other").returncode
    out["前提条件: メイン"] = run(precond, repo).returncode
    # **別の worktree の中から走らせる。** 相対パスだと**そこに入れ子で生える**ので、
    # **メインの作業ツリーから走らせる観測だけでは、その変異を殺せない。**
    if wt.is_dir():
        run(prepare, wt, "43", "nested")
        out["入れ子で生えていない"] = not (wt / ".claude" / "worktrees" / "issue-43").exists()
        out["別 worktree からでも規約の場所"] = (
            repo / ".claude" / "worktrees" / "issue-43").is_dir()
    # **サブディレクトリから走らせる。** `--git-dir` は絶対、`--git-common-dir` は
    # **相対で返ることがあり、その相対は cwd を起点にする。**
    # **トップレベルからの観測だけでは、この 2 つの実バグが両方とも素通りした**
    # ——前提条件が**メインの作業ツリーで rc=0** を返し、入場が**リポジトリの外**に
    # worktree を作ろうとしていた（`/code-review` が指摘。#136）。
    deep = repo / "sub" / "deep"
    deep.mkdir(parents=True, exist_ok=True)
    out["前提条件: メインのサブディレクトリ"] = run(precond, deep).returncode
    sub_res = run(prepare, deep, "77", "nested-sub")
    out["サブから作った場所がリポジトリの中"] = (
        repo / ".claude" / "worktrees" / "issue-77").is_dir()
    out["サブから作ってもリポジトリの外に作らない"] = not (
        repo.parent / ".claude").exists()
    out["サブから作った rc"] = sub_res.returncode

    # **git が使えない木では「判定できなかった」と答える**（「メインにいる」ではない）。
    nogit = base / "nogit"
    nogit.mkdir(parents=True, exist_ok=True)
    out["前提条件: git 無し"] = run(precond, nogit).returncode
    # **入場の側も、見られなかったときに作らないことを見る。**
    # **これが無いと「見られなくても作る」変異が殺せない**（観測が無いため）。
    # **この主張は機械で当ててある**（#151）。
    # mutation-claim: {"file": "scripts/test-worktree-scripts.py", "old": "    out[\"入場: git 無しでも作らない\"] = not (nogit / \".claude\").exists()\n", "new": "", "red": "python3 scripts/test-worktree-scripts.py"}
    out["入場: git 無し"] = run(prepare, nogit, "88", "nogit").returncode
    out["入場: git 無しでも作らない"] = not (nogit / ".claude").exists()

    # **`rev-parse` は通るが、既存の一覧だけ取れない木。** exit 6 の守りを直接当てる。
    fake = fake_git_dir(base)
    env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}")
    listless = make_repo(base / "listless")
    res6 = run(prepare, listless, "99", "listless", env=env)
    out["入場: 既存を見られない rc"] = res6.returncode
    out["入場: 既存を見られなければ作らない"] = not (
        listless / ".claude" / "worktrees" / "issue-99").exists()

    # ---- #148: start-point / 取り直し / 黙らないこと / base の出力 ----
    # **`origin` を持たない木**（`make_repo`）での振る舞いは `first` に出ている。
    out["origin が無いことを黙らない"] = "HEAD から切る" in (first.stderr + first.stdout)
    out["base を完全な SHA で出す"] = bool(
        re.search(r"^base:\s+[0-9a-f]{40}\s*$", first.stdout, re.M))
    out["start-point を出力する"] = "start-point:" in first.stdout

    # **origin が手元より進んでいるクローン。** 切った先が A か B かを見る。
    ahead = make_ahead_clones(base / "ahead")
    for label in ("未取得", "取得済み"):
        work = ahead["clones"][label]
        res = run(prepare, work, "55", "ahead")
        wt3 = work / ".claude" / "worktrees" / "issue-55"
        out[f"進んだ origin（{label}）: rc"] = res.returncode
        if wt3.is_dir():
            head = git(wt3, "rev-parse", "HEAD").stdout.strip()
            out[f"進んだ origin（{label}）: 切った先"] = (
                "B（新しい）" if head == ahead["B"]
                else "A（古い）" if head == ahead["A"] else "?")
            # **他人の作業が作業ツリーに入っているか**——B から切っていれば在る。
            out[f"進んだ origin（{label}）: 他人の作業が在る"] = (wt3 / "OTHER.md").exists()
        else:
            out[f"進んだ origin（{label}）: 切った先"] = "-"
            out[f"進んだ origin（{label}）: 他人の作業が在る"] = None

    # **upstream が付いていないこと**（指摘 1）。付くと `git pull` が既定ブランチを
    # この周にマージしうる。**`ahead` の worktree から読む**（追加のクローンは要らない）。
    wt55 = ahead["clones"]["取得済み"] / ".claude" / "worktrees" / "issue-55"
    out["upstream が付いていない"] = (
        git(wt55, "rev-parse", "--abbrev-ref", "HEAD@{upstream}").returncode != 0
        if wt55.is_dir() else None)

    # **まだ取れていない参照を名指ししても、取り直して解決する**（2 パス目の指摘 1）。
    stale = ahead["clones"]["未取得(専用)"]
    sib = run(prepare, stale, "56", "sibling",
              env=dict(os.environ, DEV_LOOP_BASE_REF="origin/sibling"))
    wt56 = stale / ".claude" / "worktrees" / "issue-56"
    out["まだ取れていない参照: rc"] = sib.returncode
    out["まだ取れていない参照: 切った先"] = (
        "sibling" if wt56.is_dir()
        and git(wt56, "rev-parse", "HEAD").stdout.strip() == ahead["SIB"]
        else "別のところ" if wt56.is_dir() else "-")

    # **名指しの base が解決しないなら断る**（2 パス目の指摘 2）。
    bad = run(prepare, repo, "44", "badbase",
              env=dict(os.environ, DEV_LOOP_BASE_REF="refs/nope/nope"))
    out["名指しが解決しない: rc"] = bad.returncode
    out["名指しが解決しなければ作らない"] = not (
        repo / ".claude" / "worktrees" / "issue-44").is_dir()

    # **壊れた `origin/HEAD` でも死なない**（指摘 2）。
    dang = make_dangling_origin_head(base / "dangling")
    dres = run(prepare, dang, "66", "dangling")
    out["壊れた origin/HEAD: rc"] = dres.returncode
    out["壊れた origin/HEAD: 作れた"] = (
        dang / ".claude" / "worktrees" / "issue-66").is_dir()
    out["壊れた origin/HEAD: 黙らない"] = "壊れている" in (dres.stderr + dres.stdout)

    # detached を作って見分けられるか
    if wt.is_dir():
        sha = git(wt, "rev-parse", "HEAD").stdout.strip()
        git(wt, "checkout", "-q", "--detach", sha)
        out["前提条件: detached"] = run(precond, wt, "issue/42-sample").returncode
    return out


MUTATIONS = {
    # 守る 1: 先に見る（再開の周を新規として踏み潰さない）
    "先に見ずに作る": (PREPARE,
        'if [ -n "$EXISTING_WT" ] || [ -n "$EXISTING_BR" ]; then',
        'if false; then'),
    # 守る 2: 絶対パスで作る
    "相対パスで作る": (PREPARE,
        'PATH_ABS="${MAIN}/.claude/worktrees/issue-${NUMBER}"',
        'PATH_ABS=".claude/worktrees/issue-${NUMBER}"'),
    # 守る 3: 規約どおりの名前で切る
    "命名規約を外す": (PREPARE,
        'BRANCH="issue/${NUMBER}-${SLUG}"',
        'BRANCH="worktree-${SLUG}"'),
    # 守る 4: 肯定的な確認の材料を出す
    "確認の材料を出さない": (PREPARE,
        'echo "ブランチ: ${ACTUAL_BRANCH}"',
        'true'),
    # --- check-pr-preconditions.sh の 守る 4 行 ---
    # 守る 1: worktree にいるか
    "worktree 判定をしない": (PRECOND,
        'if [ "$GIT_DIR" = "$COMMON_DIR" ]; then',
        'if false; then'),
    # 守る 2: 正しい worktree にいるか
    "ブランチを突き合わせない": (PRECOND,
        'if [ -n "$EXPECTED" ] && [ "$BRANCH" != "$EXPECTED" ]; then',
        'if false; then'),
    # 守る 3: detached を見分ける
    "detached を見分けない": (PRECOND,
        'if ! git symbolic-ref -q HEAD >/dev/null; then',
        'if false; then'),
    # 守る 4: 終了コードで区別する
    "終了コードを一律にする": (PRECOND,
        '  exit 3\nfi',
        '  exit 1\nfi'),
    # 守る 5: 判定できなかったことを「メインにいる」と答えない
    "判定できなくても答える": (PRECOND,
        '  exit 4\nfi',
        '  GIT_DIR=""; COMMON_DIR=""\nfi'),
    # 守る 6（prepare）: 判定できなかったことを「当たらなかった」と答えない
    # **root の守りを壊すと、背後の守りが終了コード 6 で受け止める**ので観測が変わる。
    "見られなくても作る": (PREPARE,
        '  exit 5\nfi\nMAIN=',
        '  COMMON="$(pwd)/.git"\nfi\nMAIN='),
    # 守る 6b（prepare）: 既存の一覧を見られなかったときに「当たらなかった」と答えない
    # **偽の `git` で直接当てる**（3 巡目まで、この守りには専用の観測が無かった）。
    "既存を見られなくても作る": (PREPARE,
        '  exit 6\nfi',
        '  WT_ALL=""; BR_ALL=""\nfi'),
    # 守る 8（prepare）: start-point を渡して切る（#148）
    # **省略すると HEAD に落ちる**ので、古い既定ブランチの上で周が進む。
    "start-point を渡さない": (PREPARE,
        'set -- "$BASE_REF"',
        'set --'),
    # 守る 9（prepare）: 切る前に取り直す（#148）
    # **「未取得」の場面だけでは上の変異と見分けられない**ので、
    # **「取得済み」の場面を併せて観測している**（`make_ahead_clones`）。
    "切る前に取り直さない": (PREPARE,
        'if [ "$NEED_FETCH" = 1 ] && git remote get-url origin >/dev/null 2>&1; then',
        'if false; then'),
    # 守る 12（prepare）: upstream を付けない（#148 / `/code-review` 指摘 1）
    "upstream を付ける": (PREPARE,
        'git worktree add --no-track "$PATH_ABS" -b "$BRANCH" "$@" >&2',
        'git worktree add "$PATH_ABS" -b "$BRANCH" "$@" >&2'),
    # 守る 14（prepare）: 名指しの base が解決しないなら断る（2 パス目の指摘 2）
    "名指しの base が解決しなくても HEAD で作る": (PREPARE,
        '  if [ -n "${DEV_LOOP_BASE_REF:-}" ]; then',
        '  if false; then'),
    # 守る 15（prepare）: まだ取れていない参照でも、取り直してから解決する（指摘 1）
    "まだ取れていない参照で取り直しを飛ばす": (PREPARE,
        '    NEED_FETCH=1   # 解決できない——取り直せば生えるかもしれない',
        '    NEED_FETCH=0   # 解決できない——取り直せば生えるかもしれない'),
    # 守る 13（prepare）: 壊れた start-point で死なない（#148 / `/code-review` 指摘 2）
    "壊れた start-point をそのまま渡す": (PREPARE,
        'if [ -n "$BASE_REF" ] && ! git rev-parse --verify -q "${BASE_REF}^{commit}" >/dev/null 2>&1; then',
        'if false; then'),
    # 守る 10（prepare）: origin が無ければ HEAD から切ったことを言う（#148）
    "HEAD に落ちたことを黙る": (PREPARE,
        '  echo "**既定ブランチのリモート追跡参照を解決できなかった。HEAD から切る。**" >&2',
        '  true'),
    # 守る 11（prepare）: 関門に渡す base を完全な SHA で出す（#148）
    "base を短縮形で出す": (PREPARE,
        'BASE_SHA="$(git -C "$PATH_ABS" rev-parse HEAD)"',
        'BASE_SHA="$(git -C "$PATH_ABS" rev-parse --short HEAD)"'),
    # 守る 7（prepare）: 相対パスを cwd 起点で解決する（= 絶対で取る）
    "相対のまま root 起点で解決する": (PREPARE,
        'MAIN="$(cd "$(dirname "$COMMON")" && pwd -P)"',
        'MAIN="$(cd "$(git rev-parse --show-toplevel)/$(dirname "$(git rev-parse --git-common-dir)")" && pwd -P)"'),
}


def counting_git_dir(base: Path, log: Path) -> Path:
    """**`fetch` の呼び出しを数える `git`。** 他は本物に通す。"""
    d = base / "countbin"
    d.mkdir(parents=True, exist_ok=True)
    real = subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip()
    (d / "git").write_text(
        "#!/usr/bin/env bash\n"
        f'if [ "$1" = fetch ]; then echo fetch >> "{log}"; fi\n'
        f'exec {real} "$@"\n', encoding="utf-8")
    (d / "git").chmod(0o755)
    return d


def check_no_network_on_reject(base: Path) -> None:
    """**断る周（終了コード 3）でネットワークに出ないこと**（`/code-review` の指摘 3）。

    **順序そのものを当てている**——`fetch` を「先に見る」より前に戻すと、
    **断る周でも `fetch` が増える**ので、この検査が赤くなる。
    """
    env_ahead = make_ahead_clones(base / "clones")
    work = env_ahead["clones"]["取得済み"]
    log = base / "fetchlog"
    d = counting_git_dir(base, log)
    env = dict(os.environ, PATH=f"{d}:{os.environ['PATH']}")

    run(PREPARE, work, "71", "first", env=env)
    n1 = len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0
    again = run(PREPARE, work, "71", "again", env=env)
    n2 = len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0

    check("作る周では取り直す（fetch が 1 回以上）", n1 >= 1)
    check("断る周は rc=3", again.returncode == 3)
    check("断る周では取り直さない（fetch が増えない）", n2 == n1)


def check_norm_shape() -> None:
    """**渡す形そのものを当てる**（`/code-review` の指摘 10）。

    `demonstrate_base_rule` が見ているのは **git の性質**であって、
    **この周が決めた規定ではない**——**委譲文を 3 点に戻しても緑のまま**だった。
    **規定の側を読んで、壊れたら赤くする。**
    """
    skill_dir = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop"
    for name in ("verifier.md", "review-handoff.md"):
        body = (skill_dir / "prompts" / name).read_text(encoding="utf-8")
        # **在る／無いではなく、*形*を当てる。** **禁止文を残したまま
        # `git diff {{base の SHA}}...HEAD` に書き換えても緑のままだった**
        # ——**指摘 10 を直すために書いた検査が、その退行を捕まえていなかった**
        # （`/code-review` の 2 パス目が再現して指摘。**同じ型の 3 度目**）。
        m = re.search(r"git diff \{\{base の SHA\}\}(\.{3})?", body)
        check(f"{name}: 差分の取り方が書いてある", m is not None)
        check(f"{name}: 3 点になっていない（形を当てている）",
              m is not None and m.group(1) is None)
        check(f"{name}: 3 点を禁じている", "3 点（`...`）にしないでください" in body)
        check(f"{name}: 未追跡を見よと書いてある", "git status --porcelain" in body)
    skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    # **式そのものを当てる。** **`merge-base` だけだと、無関係な `--is-ancestor` の行で
    # 満たされてしまい、式の箇条書きを消しても緑のままになる**（同上）。
    check("SKILL.md: base の式が書いてある",
          "git merge-base <その周を切った元の参照> HEAD" in skill)
    check("SKILL.md: DEV_LOOP_BASE_REF が書いてある", "DEV_LOOP_BASE_REF" in skill)
    check("SKILL.md: 祖先であることの確認を要求している",
          "--is-ancestor" in skill)
    agent = (REAL_REPO / "plugins" / "dev-loop" / "agents" / "dev-loop-verifier.md"
             ).read_text(encoding="utf-8")
    # **生の `fetch` では広すぎる**——`WebFetch` を `tools:` に足しただけで赤くなる
    # （`/code-review` の 2 パス目が指摘）。**指示の形だけを当てる。**
    check("同梱 agent 定義に取り直しの指示が無い（不変条件 D）",
          "git fetch" not in agent and "取り直して" not in agent)


def shell_code_and_data(source: str) -> tuple[str, list[tuple[str, bool]]]:
    """シェルの本文を、**実行される字句**と**データ**（引用の中身・heredoc の本文）に分ける（#243）。

    **行をまたいで状態を持つ**——#206 の版は行単位の正規表現で、**複数行の文字列の中の
    `exit 7` を数え**、**`$((a<<b))` を heredoc として開いて以降の行を全部飛ばした**（#243 N1・N3）。
    実行される字句では、引用は `''`・`""` に、算術（`((…))`）は `0` に置き換え、
    コメント（語の頭の `#` から行末）は落とす。**`$#`・`${v#p}`・`${v// #/}`・`"…#…"` は
    コメントではない**（`${…}` の中では語の頭でも落とさない。**`[[ … ]]` の中は bash もコメントにする**
    ——実測で構文エラー）。
    **`\\`⏎ は継続行で何も残さず、`\\exit` は `exit` のまま残す**——`_` に潰すと、
    **bash が実行する `exit` が語として消える**（#243 の 1 パス目。#242 の版より後退していた）。
    **`((` が算術になるのは、最初に深さ 1 へ戻る `)` の直後が `)` のときだけ**——
    それ以外は bash でも入れ子のサブシェルで、`((cd /); exit 9)` は 9 で終わる（実測）。
    heredoc は**終端語の引用を外して**（`<<\\EOF`・`<<'EOF'`・`<<E"OF"` はどれも `EOF`）、
    `<<-` は**行頭のタブを剥がした行**で閉じる。**終端語を引用しない heredoc は、本文の行末の `\\` で
    次の行と繋いでから終端と比べる**（bash の実測）。**1 行の heredoc は書いた順に全部読む。**
    **いちばん内側の括弧が `$(` なら、`EOF)` の行でも閉じ、`)` 以降は実行される字句に戻す**
    ——bash の実測で、`$(` の中だけがそう閉じる（素の `(` の中は構文エラー・括弧の外は閉じない）。
    **終端語の途中の `\\`⏎ は語を割らない**（`<<EO\\`⏎`F` の終端は `EOF`。実測）。
    **`<<<`（here-string）は heredoc ではない。**
    データは `(中身, 展開されて止まりうるか)` の組で返す——**真になるのは `"…"` の中身だけ**
    （`${N:?…}` を拾う範囲。**引用しない heredoc の本文の `${1:?}` は、bash の実測でスクリプトを
    止めなかった**）。
    **追わないもの**: `"…"` の中の `$(…)` に入れ子の引用・`$(…)` 自体（中の `exit` は字句として残る）。
    """
    code: list[str] = []
    data: list[tuple[str, bool]] = []
    pending: list[tuple[str, bool, bool]] = []  # (終端の語, `<<-` か, 終端語を引用したか)
    brace = 0  # `${` の深さ。この中の `#` はコメントではない
    parens: list[bool] = []  # 開いている `(` ごとに、それが `$(` か
    i, n = 0, len(source)

    def skip_quoted(start: int, quote: str, escapes: bool) -> int:
        j = start
        while j < n and source[j] != quote:
            j += 2 if escapes and source[j] == "\\" else 1
        return j

    def next_line(start: int) -> tuple[str, int]:
        j = source.find("\n", start)
        j = n if j < 0 else j
        return source[start:j], j + 1

    while i < n:
        c = source[i]
        if c == "\n":
            code.append("\n")
            i += 1
            rest_pending: list[tuple[str, bool, bool]] = []
            for k, (word, dash, quoted) in enumerate(pending):
                body: list[str] = []
                mid_line = False
                while i < n:
                    start = i
                    line, i = next_line(i)
                    joined = False
                    while (not quoted and i < n
                           and (len(line) - len(line.rstrip("\\"))) % 2):
                        rest, i = next_line(i)
                        line, joined = line[:-1] + rest, True
                    head = line.lstrip("\t") if dash else line
                    if head == word:
                        break
                    if (not joined and parens and parens[-1]
                            and head.startswith(word + ")")):
                        i = start + len(line) - len(head) + len(word)
                        mid_line = True
                        break
                    body.append(line)
                data.append(("\n".join(body), False))
                if mid_line:
                    rest_pending = pending[k + 1:]
                    break
            pending = rest_pending
        elif c == "\\":
            nxt = source[i + 1:i + 2]
            if nxt != "\n":
                code.append(nxt if nxt.isalnum() or nxt == "_" else "_")
            i += 2
        elif c == "#" and not brace and (not code or code[-1] in " \t\n;&|()"):
            j = source.find("\n", i)
            i = n if j < 0 else j
        elif source.startswith("$'", i):
            j = skip_quoted(i + 2, "'", True)
            data.append((source[i + 2:j], False))
            code.append("''")
            i = j + 1
        elif c == "'":
            j = skip_quoted(i + 1, "'", False)
            data.append((source[i + 1:j], False))
            code.append("''")
            i = j + 1
        elif c == '"':
            j = skip_quoted(i + 1, '"', True)
            data.append((source[i + 1:j], True))
            code.append('""')
            i = j + 1
        elif source.startswith("${", i):
            brace += 1
            code.append("${")
            i += 2
        elif c == "}" and brace:
            brace -= 1
            code.append("}")
            i += 1
        elif source.startswith("((", i):
            depth, j, inner = 0, i, -1
            while j < n:
                depth += {"(": 1, ")": -1}.get(source[j], 0)
                if depth == 1 and source[j] == ")" and inner < 0:
                    inner = j
                if depth == 0:
                    break
                j += 1
            if j < n and inner == j - 1:
                code.append("0")
                i = j + 1
            else:
                parens.append(bool(code) and code[-1] == "$")
                code.append("(")
                i += 1
        elif source.startswith("<<<", i):
            code.append("<<<")
            i += 3
        elif source.startswith("<<", i):
            i += 2
            dash = source.startswith("-", i)
            i += dash
            while i < n and source[i] in " \t":
                i += 1
            word: list[str] = []
            quoted = False
            while i < n and source[i] not in " \t\n;&|<>()":
                if source[i] in "'\"":
                    j = source.find(source[i], i + 1)
                    j = n if j < 0 else j
                    word.append(source[i + 1:j])
                    quoted, i = True, j + 1
                elif source.startswith("\\\n", i):
                    i += 2
                elif source[i] == "\\":
                    word.append(source[i + 1:i + 2])
                    quoted, i = True, i + 2
                else:
                    word.append(source[i])
                    i += 1
            pending.append(("".join(word), dash, quoted))
            code.append("<<")
        else:
            if c == "(":
                parens.append(bool(code) and code[-1] == "$")
            elif c == ")" and parens:
                parens.pop()
            code.append(c)
            i += 1
    return "".join(code), data


def script_exit_codes(source: str) -> set[int] | None:
    """**スクリプトが返しうる固定の終了コード**を、本体から集める（#206）。

    明示の `exit N`（**行のどこにあっても数える**——`cmd || exit 8`・`then exit 8; fi`・
    `foo; exit 8`。**行頭だけに絞ると、この形で足した番号が一覧に無くても緑になる**
    ——1 パス目の両関門が実測）・正常終了の 0・**`${N:?…}` の引数不足**（bash の実測で 1）。
    **コメント・引用の中身・heredoc の本文は数えない**——切り分けは `shell_code_and_data`
    （**行をまたいで状態を持つ**。#243）。
    **引用か heredoc の本文に `exit` が現れたら `None`**——**実行されるか
    （`trap 'exit 7' EXIT`・`eval "exit 7"`・`bash -c '…'`）を字句では決めきれない**。
    **数えると `exit 7` を `echo 'exit 7'` に置き換えても一致と言い、落とすと
    `trap 'exit 7' EXIT` を足しても一致と言う**——**どちらに丸めても緑が嘘になる**（#243 N2）。
    **数字の付かない `exit`（`exit "$rc"`・`exit -1`・素の `exit`）も `None`**
    ——**値が読めない形を「無い」に丸めない**（一覧と一致とは言わせない）。
    **番号は 10 進で読む**——`exit 010` は 10（bash の実測。#243）。
    **番号の直後が語の切れ目でなければ `None`**——`exit 7+1` は bash では 255（実測）で、7 ではない。
    **データの中では `\\` の直後を語の切れ目として見て、`\\` を外しただけの形でも見る**
    ——`printf 'true\\nexit 6'` の `n` が `exit` の語の境界を消すと、実行される文字列を見落とす
    （#243 の 1 パス目）。**`\\` の直後の文字ごと落とすと、`trap 'true; \\exit 7' EXIT` の
    `exit` が `xit` に潰れる**（bash の実測で 7。2 パス目）。
    **行は `\\n` だけで割る**——`splitlines` は `\\r` でも割るので、CRLF の `exit 7\\r` を 7 と読む
    （bash では `numeric argument required` で 255。2 パス目）。
    **`${N:?…}` は実行される字句と `"…"` の中身からだけ拾う**——コメントや heredoc の本文に
    書いてあるだけで 1 を足すと、**本当の `${1:?…}` を消しても一致と言う**（同上）。
    **`git worktree add` の失敗は git の終了コードで固定ではない**ので、ここには入らない
    （一覧の「それ以外」がそれを受ける）。
    """
    code, data = shell_code_and_data(source)
    if any(re.search(r"\bexit\b", re.sub(escape, " ", d))
           for d, _ in data for escape in (r"\\.", r"\\")):
        return None
    codes: set[int] = set()
    for line in code.split("\n"):
        for m in re.finditer(r"\bexit\b([ \t]+(\d+)(?=[ \t;&|)]|$))?", line):
            if m.group(2) is None:
                return None
            codes.add(int(m.group(2)))
    codes.add(0)
    if any(re.search(r"\$\{\d+:\?", s) for s in [code, *(d for d, ex in data if ex)]):
        codes.add(1)
    return codes


def exit_paragraph_span(skill: str, script_name: str) -> tuple[int, int] | None:
    """**そのスクリプトを呼ぶコードブロックの、直後の段落**の位置。

    **直後の段落が「終了コードで分岐する」で始まらなければ `None`**——
    **先へ探しに行くと、見出しを改名したときに別のスクリプトの一覧を拾う**。
    """
    call = skill.find(f"scripts/{script_name}")
    if call < 0:
        return None
    fence = skill.find("```", call)
    if fence < 0:
        return None
    start = fence + 3
    while start < len(skill) and skill[start].isspace():
        start += 1
    if not skill.startswith("**終了コードで分岐する**", start):
        return None
    end = skill.find("\n\n", start)
    return start, end if end >= 0 else len(skill)


def listed_exit_codes(skill: str, script_name: str) -> set[int] | None:
    """**`SKILL.md` の、そのスクリプトの終了コード一覧**に挙がる番号。

    **段落が見つからなければ `None`**——**「当てられなかった」を空集合（＝緑の材料）に丸めない。**
    `5・6` のように束ねた書き方は両方を数える。
    """
    span = exit_paragraph_span(skill, script_name)
    if span is None:
        return None
    codes: set[int] = set()
    for group in re.findall(r"\*\*(\d+(?:・\d+)*):", skill[span[0]:span[1]]):
        codes.update(int(n) for n in group.split("・"))
    return codes or None


def exit_lists_agree(skill: str, script_name: str, source: str) -> bool:
    listed = listed_exit_codes(skill, script_name)
    return listed is not None and listed == script_exit_codes(source)


def check_exit_code_lists() -> None:
    """**`SKILL.md` の終了コード一覧が、スクリプトの全終了コードと一致するか**（#206）。

    **一覧に 7 が無く、名指しの base の誤りが「`git worktree add` の失敗」に
    読まれていた**——**一覧とスクリプトを突き合わせるものが何も無かった。**
    **変異は対象の段落の中だけで当て、壊したのに一致と言えば失格とする**
    （**段落の外で当てると、別の一覧を壊して「殺せた」と数えうる**）。
    """
    skill = (REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "SKILL.md"
             ).read_text(encoding="utf-8")
    for script in (PREPARE, PRECOND):
        source = script.read_text(encoding="utf-8")
        listed = listed_exit_codes(skill, script.name)
        actual = script_exit_codes(source)
        check(f"{script.name}: SKILL.md に一覧が在る", listed is not None)
        check(f"{script.name}: スクリプトの終了コードが読める（数字の無い `exit`・引用や heredoc の中の `exit` が無い）",
              actual is not None)
        check(f"{script.name}: 一覧 {sorted(listed or [])} がスクリプト {sorted(actual or [])} と一致",
              listed == actual)
        span = exit_paragraph_span(skill, script.name)
        if span is None or actual is None:
            continue

        def in_para(fn, span=span) -> str:
            return skill[:span[0]] + fn(skill[span[0]:span[1]]) + skill[span[1]:]

        # --- 変異（壊したのに一致と言えば失格） ---
        top = max(actual)
        removed = in_para(lambda t: t.replace(f"**{top}:", "**削除:", 1))
        check(f"{script.name}: 変異の当て先（{top}）が段落に在る", removed != skill)
        check(f"{script.name}: 一覧から {top} を消すと不一致（#206 の再現）",
              not exit_lists_agree(removed, script.name, source))
        for form in ("exit {n}", "git fetch || exit {n}", "if x; then exit {n}; fi",
                     "foo; exit {n}"):
            added = form.format(n=top + 1)
            check(f"{script.name}: スクリプトに `{added}` を足すと不一致",
                  not exit_lists_agree(skill, script.name, source + f"\n{added}\n"))
        for form in ('exit "$rc"', "exit -1", "exit"):
            check(f"{script.name}: 値の読めない `{form}` を足すと一致と言わない",
                  not exit_lists_agree(skill, script.name, source + f"\n{form}\n"))
        extra = in_para(lambda t: t.replace(
            "**終了コードで分岐する**——",
            f"**終了コードで分岐する**——**{top + 2}: 架空** ／ ", 1))
        check(f"{script.name}: 一覧に無い番号 {top + 2} を書くと不一致",
              not exit_lists_agree(extra, script.name, source))
        renamed = in_para(lambda t: t.replace(
            "**終了コードで分岐する**", "**終了コードで分ける**", 1))
        check(f"{script.name}: 段落が見つからなければ一致と言わない",
              not exit_lists_agree(renamed, script.name, source))
        check(f"{script.name}: コメント中の exit は数えない",
              script_exit_codes(source + f"\n# 例: exit {top + 3}\n") == actual)
        check(f"{script.name}: 行末のコメント中の exit は数えない",
              script_exit_codes(source + f"\ngit fetch  # retry would exit {top + 3}\n")
              == actual)
        # --- 引用と heredoc（2 パス目の `/code-review` の CR2-1・CR2-2） ---
        quoted_hash = f'[ -n "$X" ] || {{ echo "see #206" >&2; exit {top + 1}; }}'
        check(f"{script.name}: 引用の中の `#` の後ろの exit も数える（`{quoted_hash}`）",
              not exit_lists_agree(skill, script.name, source + f"\n{quoted_hash}\n"))
        real_exit = re.compile(rf"^([ \t]*)exit {top}\b", re.M)
        check(f"{script.name}: 変異の当て先（`exit {top}`）がスクリプトに在る",
              real_exit.search(source) is not None)
        for repl in (f"echo 'caller should exit {top}'",
                     f'echo "caller should exit {top}"',
                     f"cat <<EOF\nexit {top}\nEOF",
                     f"cat <<-'EOF'\n\texit {top}\n\tEOF"):
            moved = real_exit.sub(lambda m, r=repl: m.group(1) + r, source, count=1)
            shown = repl.replace("\n", "⏎")
            check(f"{script.name}: 実際の `exit {top}` を `{shown}` に置き換えると不一致",
                  not exit_lists_agree(skill, script.name, moved))
        for tail in ("cat <<EOF\nx\nEOF\nexit {n}", "x=$((1<<2)); exit {n}"):
            added = tail.format(n=top + 1)
            shown = added.replace("\n", "⏎")
            check(f"{script.name}: heredoc の後ろ・`<<` 演算の後ろの `exit` は数える（`{shown}`）",
                  not exit_lists_agree(skill, script.name, source + f"\n{added}\n"))
        # --- 行をまたぐ字句（#243） ---
        for tail in ("x=$((a<<b))\nexit {n}", "(( a<<b ))\nexit {n}",
                     "cat <<-EOF\n\techo x\n\tEOF\nexit {n}", "cat <<< foo\nexit {n}",
                     "echo 'a\nb'\nexit {n}"):
            added = tail.format(n=top + 1)
            shown = added.replace("\n", "⏎")
            check(f"{script.name}: 次の行の `exit` を飲み込まない（`{shown}`）",
                  not exit_lists_agree(skill, script.name, source + f"\n{added}\n"))
        for repl in (f"trap 'exit {top}' EXIT", f'eval "exit {top}"',
                     f'echo "a\nexit {top}\nb"', f"cat <<\\EOF\nexit {top}\nEOF",
                     f'cat <<E"OF"\nexit {top}\nEOF', f"cat <<A <<B\nx\nA\nexit {top}\nB"):
            moved = real_exit.sub(lambda m, r=repl: m.group(1) + r, source, count=1)
            shown = repl.replace("\n", "⏎")
            check(f"{script.name}: 実際の `exit {top}` を `{shown}` に置き換えると不一致",
                  not exit_lists_agree(skill, script.name, moved))


def check_shell_lexing() -> None:
    """**`script_exit_codes` を、#243 の経路 E1〜E10 に直接当てる。**

    **一覧との突き合わせ（`check_exit_code_lists`）だけでは、`None` と「違う集合」を
    区別しない**——**どちらも「不一致」で赤**になるので、**`<<-` が閉じずに以降を飲み込む形**
    （集合が小さくなる）と**正しく閉じる形**を見分けられない（#242 の狭いパスで素通りした変異）。
    **だから値そのものを当てる。**
    """
    cases = [
        ("E1 算術のシフト `$((a<<b))`", "x=$((a<<b))\nexit 8", {0, 8}),
        ("E1 算術のシフト `(( a<<b ))`", "(( a<<b ))\nexit 8", {0, 8}),
        ("E1 数字のシフト", "x=$((1<<2)); exit 8", {0, 8}),
        ("E2 `trap '…' EXIT`", "trap 'exit 7' EXIT\nexit 8", None),
        ("E2 `eval \"…\"`", 'eval "exit 7"\nexit 8', None),
        ("E2 `bash -c '…'`", "bash -c 'exit 7'\nexit 8", None),
        ("E3 複数行の二重引用", 'echo "a\nexit 7\nb"\nexit 8', None),
        ("E3 複数行の単引用", "echo 'a\nexit 7\nb'\nexit 8", None),
        ("E3 `$'…'`", "echo $'a\\nexit 7'\nexit 8", None),
        ("E3 複数行の文字列の後ろ", "echo 'a\nb'\nexit 8", {0, 8}),
        ("E4 `<<\\EOF`", "cat <<\\EOF\nx\nEOF\nexit 8", {0, 8}),
        ("E4 `<<'EOF'`", "cat <<'EOF'\nx\nEOF\nexit 8", {0, 8}),
        ("E4 `<<\"EOF\"`", 'cat <<"EOF"\nx\nEOF\nexit 8', {0, 8}),
        ("E4 `<<E\"OF\"`", 'cat <<E"OF"\nx\nEOF\nexit 8', {0, 8}),
        ("E4 本文の `exit`", "cat <<EOF\nexit 7\nEOF\nexit 8", None),
        ("E5 1 行に 2 つ（2 つ目の本文）", "cat <<A <<B\nx\nA\nexit 9\nB\nexit 8", None),
        ("E5 1 行に 2 つ（両方閉じる）", "cat <<A <<B\nx\nA\ny\nB\nexit 8", {0, 8}),
        ("E6 `<<-` はタブ付きの終端で閉じる", "cat <<-EOF\n\tx\n\tEOF\nexit 8", {0, 8}),
        ("E6 `<<` はタブ付きの行では閉じない", "cat <<EOF\n\tEOF\nexit 7\nEOF\nexit 8", None),
        ("E7 here-string", "cat <<< foo\nexit 8", {0, 8}),
        ("E8 先頭が 0 の番号", "exit 010", {0, 10}),
        ("E9 `$#`", "[ $# -eq 0 ] && exit 8", {0, 8}),
        ("E9 `${v#p}`", "x=${v#p}; exit 8", {0, 8}),
        ("E9 引用の中の `#`", 'echo "see #206"; exit 8', {0, 8}),
        ("E9 語の途中の `#`", "echo a#b; exit 8", {0, 8}),
        ("E10 行頭のコメント", "# exit 9\nexit 8", {0, 8}),
        ("E10 行末のコメント", "git fetch  # exit 9\nexit 8", {0, 8}),
        # 1 パス目の両関門の指摘（計画ファイルの採否の表）。期待値は bash の実測か、
        # 決着済みの方針（引用・heredoc の本文に `exit` があれば `None`・`$(…)` の中は数える）
        ("E4 heredoc の後ろの 2 行以上", "cat <<EOF\nx\nEOF\necho a\nexit 8\nexit 9", {0, 8, 9}),
        ("E12 `\\exit` は組み込みの exit", "false || \\exit 7", {0, 7}),
        ("E12 継続行の後ろの `exit`", "git fetch || \\\nexit 8", {0, 8}),
        ("E13 `((…); …)` はサブシェル", "((cd /); exit 9)", {0, 9}),
        ("E13 `$((…) || …)` はサブシェル", "x=$((cd a && pwd) || exit 9)", {0, 9}),
        ("E13 `(( (a+b) ))` は算術", "(( (a+b) ))\nexit 8", {0, 8}),
        ("E14 `${…}` の中の空白の後ろの `#`", "x=${v// #/}; exit 8", {0, 8}),
        ("E15 引用の中の `\\n` の後ろの `exit`", "printf 'true\\nexit 6\\n' | bash\nexit 8", None),
        ("E15 二重引用の中の `\\n` の後ろの `exit`", 'echo -e "a\\nexit 7"\nexit 8', None),
        ("E16 heredoc の本文の継続行", "cat <<EOF\nfoo \\\nEOF\nexit 7\nEOF\nexit 8", None),
        ("E16 引用した終端語は継続しない", "cat <<'EOF'\nfoo \\\nEOF\nexit 7", {0, 7}),
        ("E17 コメントの中の `${1:?`", "# uses ${1:?usage}\nexit 8", {0, 8}),
        ("E17 heredoc の本文の `${1:?`", "cat <<EOF\n${1:?x}\nEOF\nexit 8", {0, 8}),
        ("E17 `\"${1:?…}\"` は 1", 'n="${1:?usage}"\nexit 8', {0, 1, 8}),
        ("E18 `exit 7+1` は読めない", "exit 7+1", None),
        ("E18 `exit 7;`・`(exit 7)` は 7", "exit 7;\n(exit 7)", {0, 7}),
        # 2 パス目の両関門の指摘（同上）
        ("E2 単引用の中の `\\exit`", "trap 'true; \\exit 7' EXIT\nexit 0", None),
        ("E2 二重引用の中の `\\exit`", 'eval "true; \\exit 7"\nexit 0', None),
        ("E4 `$(` の中の `EOF)` で閉じる", "x=$(cat <<EOF\nbody\nEOF); exit 8", {0, 8}),
        ("E4 素の `(` の中の `EOF)` では閉じない", "(cat <<EOF\nbody\nEOF); exit 7\nEOF\nexit 8", None),
        ("E4 終端語の途中の `\\`⏎", "cat <<EO\\\nF\nbody\nEOF\nexit 8", {0, 8}),
        ("E18 CRLF の `exit 7\\r` は読めない", "exit 7\r\n", None),
    ]
    for name, src, want in cases:
        got = script_exit_codes(src)
        check(f"{name}: {sorted(got) if got is not None else None} == "
              f"{sorted(want) if want is not None else None}", got == want)


def demonstrate_base_rule(base: Path) -> None:
    """**選んだ base の形を、実際に当てて確かめる**（#148 の受入条件）。

    決めた形は **`git merge-base <既定ブランチのリモート追跡参照> HEAD` の SHA に対する
    2 点 diff** ＋ **未追跡は `git status --porcelain`** である。

    **陽性対照を取る（必須の作法）。** 「混ざらない」「見える」だけを並べても、
    **もともと出ない値**と区別がつかない。**だから、採らなかった形で実際に壊れること**を
    併せて見る——**先端の SHA では他人の作業が「削除」として出る**／
    **3 点では未コミットの実装が出ない**。
    **この 2 つは #145 の周では区別できなかった**（当時 tip == merge-base だった）。
    """
    env = make_ahead_clones(base)
    work = env["clones"]["取得済み"]

    # 周を切る（origin/main = B の上）
    wt = work / "wt"
    git(work, "worktree", "add", "-q", str(wt), "-b", "issue/1-x", "origin/main")

    # 実装を 3 つの形で置く
    (wt / "IMPL.md").write_text("impl\n", encoding="utf-8")   # コミット済み
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "impl")
    (wt / "README.md").write_text("A\nedited\n", encoding="utf-8")  # 未コミット（追跡済み）
    (wt / "NEW.md").write_text("new\n", encoding="utf-8")            # 未追跡

    # **周を切った後に、他人の作業がさらにマージされる**
    seed = env["seed"]
    (seed / "OTHER2.md").write_text("other2\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "C: 他人の作業（周を切った後）")
    git(seed, "push", "-q", "origin", "main")
    git(work, "fetch", "-q", "origin")

    mb = git(wt, "merge-base", "origin/main", "HEAD").stdout.strip()
    tip = git(wt, "rev-parse", "origin/main").stdout.strip()
    assert mb != tip, "陽性対照が成立していない（tip == merge-base では区別できない）"

    two = git(wt, "diff", "--name-only", mb).stdout.split()
    tip_two = git(wt, "diff", "--name-only", tip).stdout.split()
    # **`mb` を使う。** **`tip` を使うと、点の数と base の 2 つが同時に変わり、
    # 「3 点だから出ない」を分離できない**（`/code-review` の 2 パス目が指摘）。
    three = git(wt, "diff", "--name-only", f"{mb}...HEAD").stdout.split()
    untracked = [l[3:] for l in git(wt, "status", "--porcelain").stdout.splitlines()
                 if l.startswith("??")]

    check("V1 merge-base の 2 点に、他人の作業が混ざらない",
          "OTHER2.md" not in two and "OTHER.md" not in two)
    check("V1 陽性対照: 先端の SHA だと、他人の作業が（削除として）出る",
          "OTHER2.md" in tip_two)
    check("V2 2 点に、未コミットの実装が出る", "README.md" in two)
    check("V2 陽性対照: 3 点だと、未コミットの実装が出ない", "README.md" not in three)
    check("V2 コミット済みの実装も 2 点に出る", "IMPL.md" in two)
    check("V3 未追跡は diff に出ない（2 点でも出ない）", "NEW.md" not in two)
    check("V3 だから status --porcelain を併せて見る", "NEW.md" in untracked)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        correct = observe(PREPARE, PRECOND, base / "correct")

        print("prepare-worktree.sh")
        check("新規の周では作れる（rc=0）", correct["新規で作れる"] == 0)
        check("同じ番号が在れば断る（rc=3）", correct["2 回目は断る"] == 3)
        check("数字以外の番号を断る（rc=2）", correct["数字以外は断る"] == 2)
        check("規約どおりの場所に作る", correct["作られた場所"])
        check("規約どおりの名前で切る", correct["切られたブランチ"] == "issue/42-sample")
        check("確認の材料（ブランチ名と起点）を出力する", correct["確認の材料が出ている"])
        check("別の worktree から走らせても入れ子で生えない", correct["入れ子で生えていない"])
        check("別の worktree から走らせても規約の場所に作る",
              correct["別 worktree からでも規約の場所"])

        print("\nprepare-worktree.sh — 周の base（#148）")
        check("origin が進んでいれば、新しい側の上に切る（手元が未取得でも）",
              correct["進んだ origin（未取得）: 切った先"] == "B（新しい）")
        check("手元が取得済みでも、新しい側の上に切る",
              correct["進んだ origin（取得済み）: 切った先"] == "B（新しい）")
        check("切った先に他人の作業が入っている（= 古い原本の上で進んでいない）",
              correct["進んだ origin（未取得）: 他人の作業が在る"] is True)
        check("origin が無ければ、HEAD から切ったことを言う",
              correct["origin が無いことを黙らない"])
        check("start-point を出力する", correct["start-point を出力する"])
        check("関門に渡す base を完全な SHA で出す", correct["base を完全な SHA で出す"])
        check("切ったブランチに upstream を付けない（指摘 1）",
              correct["upstream が付いていない"] is True)
        check("まだ取れていない参照を名指ししても、取り直して解決する（2 パス目の指摘 1）",
              correct["まだ取れていない参照: 切った先"] == "sibling")
        check("名指しの base が解決しなければ断る（rc=7。2 パス目の指摘 2）",
              correct["名指しが解決しない: rc"] == 7)
        check("名指しの base が解決しなければ何も作らない",
              correct["名指しが解決しなければ作らない"])
        check("壊れた origin/HEAD でも作れる（指摘 2）",
              correct["壊れた origin/HEAD: rc"] == 0 and correct["壊れた origin/HEAD: 作れた"])
        check("壊れた origin/HEAD であることを黙らない",
              correct["壊れた origin/HEAD: 黙らない"])

        print("\ncheck-pr-preconditions.sh")
        check("worktree でブランチも一致なら通す（rc=0）", correct["前提条件: 一致"] == 0)
        check("ブランチが違えば止める（rc=2）", correct["前提条件: 不一致"] == 2)
        check("メインの作業ツリーなら止める（rc=1）", correct["前提条件: メイン"] == 1)
        check("detached を見分ける（rc=3）", correct["前提条件: detached"] == 3)
        check("メインの**サブディレクトリ**でも止める（rc=1）",
              correct["前提条件: メインのサブディレクトリ"] == 1)
        check("判定できなければ「メインにいる」とは答えない（rc=4）",
              correct["前提条件: git 無し"] == 4)
        check("入場も、見られなければ作らない（rc=5）", correct["入場: git 無し"] == 5)
        check("既存の一覧だけ取れない木では rc=6", correct["入場: 既存を見られない rc"] == 6)
        check("既存を見られなければ何も作らない",
              correct["入場: 既存を見られなければ作らない"])
        check("入場は、見られなければ何も作らない", correct["入場: git 無しでも作らない"])
        check("サブディレクトリから作ってもリポジトリの中",
              correct["サブから作った場所がリポジトリの中"])
        check("サブディレクトリから作ってもリポジトリの外に作らない",
              correct["サブから作ってもリポジトリの外に作らない"])

        print("\n変異テスト（壊したのに緑なら失格）")
        mutant_obs: dict[str, dict] = {}
        for name, (script, needle, replacement) in MUTATIONS.items():
            source = script.read_text(encoding="utf-8")
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = base / f"mut-{abs(hash(name))}"
            (d / "scripts").mkdir(parents=True)
            for original in (PREPARE, PRECOND):
                body = original.read_text(encoding="utf-8")
                if original == script:
                    body = body.replace(needle, replacement, 1)
                (d / "scripts" / original.name).write_text(body, encoding="utf-8")
            try:
                mutated = observe(d / "scripts" / PREPARE.name,
                                  d / "scripts" / PRECOND.name, d / "tree")
            except Exception as exc:
                # **例外の型を名前に出す。** **黙って「殺せた」に丸めると、
                # 観測キーの改名・足場の失敗まで緑になる**（`/code-review` の 2 パス目）。
                check(f"変異を殺せる: {name}（例外 {type(exc).__name__}）", True)
                continue
            mutant_obs[name] = mutated
            check(f"変異を殺せる: {name}", mutated != correct)

        # **2 つの変異が互いに区別できるか**（`/code-review` の指摘 9）。
        # **docstring は「見分けるために 2 つ目のクローンを置いた」と主張していたのに、
        # 検査は `correct` としか比べていなかった**——**主張に対応する検査が無かった。**
        print("\n2 つの変異が互いに区別できるか（「取得済み」の場面が要る理由）")
        a = mutant_obs.get("start-point を渡さない")
        b = mutant_obs.get("切る前に取り直さない")
        if a is None or b is None:
            check("2 変異の観測が取れている", False)
        else:
            k_stale = "進んだ origin（未取得）: 切った先"
            k_fresh = "進んだ origin（取得済み）: 切った先"
            check("「未取得」だけでは 2 変異を区別できない（だから 2 つ目を置いている）",
                  a[k_stale] == b[k_stale])
            check("「取得済み」を足すと 2 変異が区別できる", a[k_fresh] != b[k_fresh])

        print("\n渡す形そのもの（規定が壊れたら赤くなるか）")
        check_norm_shape()

        print("\nSKILL.md の終了コード一覧がスクリプトと一致するか（#206）")
        check_exit_code_lists()

        print("\n終了コードを集める字句解析（#243）")
        check_shell_lexing()

        print("\n断る周でネットワークに出ないか")
        check_no_network_on_reject(base / "reject")

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        promises = 0
        for script in (PREPARE, PRECOND):
            body = script.read_text(encoding="utf-8")
            section = body.split("## 何を守るか")[1].split("## 何を守らないか")[0]
            promises += len([l for l in section.splitlines() if l.startswith("# - ")])
        check(f"2 本の「守る」{promises} 行に対して変異が {len(MUTATIONS)} 件",
              promises == len(MUTATIONS))

        print("\n選んだ base の形を、実際に当てて確かめる（#148。陽性対照つき）")
        demonstrate_base_rule(base / "rule")

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
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
    print("worktree スクリプトのテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
