#!/usr/bin/env python3
"""形式検査のモデル（spec-loop の `spec/formal/<対象>/`）と実装を揃えておく——周が触れたモデルを引き、今のコードに当てて走らせ直し、PR の前に記録を見る（#1178）。

usage:
    python3 formal-sync.py touched <周の base の SHA> --spec-loop <dir> [--canon <dir>]
    python3 formal-sync.py rerun <保存したモデルの対象のディレクトリ> --code-model <dir> --spec-loop <dir> [--canon <dir>] [--intended] [--timeout <秒>]
    python3 formal-sync.py check <計画ファイル> <周の base の SHA> [--spec-loop <dir>] [--canon <dir>]

**周の手順の原本は `references/formal-sync.md` である**（このスキルと同じ場所にある）。ここにあるのは、機械で決まる部分の決まりだけ。
cwd は周の worktree（実装のリポジトリ）。`--spec-loop` は spec-loop プラグインの base ディレクトリ（`scripts/check-formal-rerun.py` を持つ）で、
**記録の読み方（`formal-baseline.py` の `read_records`・`parse_mapping`）・TLC の呼び方と判定（`check-formal-rerun.py` の `rerun`）はそこから読み込む——写さない。**
`--canon` は spec-loop の正本の根（既定は実装のリポジトリの根。正本が別のリポジトリなら、その写しの根）——モデルは `<canon>/docs/v<n>/spec/formal/<対象>/README.md`
（同じ対象が 2 つ以上の版にあれば番号が最大の版）、TLC の呼び方は `<canon>/CLAUDE.md` の `TLC の呼び方:` の行。

## touched — 周が触れたモデル

記録の `実装の対応`（`` `<行為>` → `<ファイル>::<関数>` ``。ファイルは実装のリポジトリの根からのパス）のファイルが、周の差分
（`git diff --name-only --no-renames <base>`——2 点なので未コミットも入る——と未追跡のファイル）に入るモデルを出す。対応が `未実装` か行の無いモデルは「対応の無いモデル」として名前だけ出す。
対応のファイルが今の木に無いモデルは「対応が古い」と出す（触れたモデルには数えない——周が消したファイルは差分に入るので触れたに数える）。

## rerun — 今のコードに当てて走らせ直す

周が書いた**コードのモデル**（保存したモデルのディレクトリを写し、`実装の対応` の行為の定義だけを今のコードがすることに書き直したもの）と、保存したモデルの両方を
`check-formal-rerun.py` の `rerun` で走らせる（本体と陽性対照。一時ディレクトリで走るので、どちらのディレクトリにも書かない）。

**弱めて通さない**——走らせる前に、コードのモデルが保存したモデルと次で同じかを見る。違えば `判定できなかった`:

- 記録の `モデルのファイル`・`陽性対照のファイル` の一覧と、`実装の対応`
- 一覧の `.cfg` と陽性対照のファイル（バイトで）
- 本体の `.tla` の、**対応に挙げた行為の定義のほか**のすべて——行頭から始まる定義（`<名前> ==`・`<名前>(…) ==`・`LOCAL` つき）は名前ごとに本文で、
  定義の外の行（`MODULE` の行・`EXTENDS`・`VARIABLES`・`CONSTANTS`・`ASSUME`・行頭の注釈・`====`）は順に。行為の定義は書き直してよく、新しい定義を足してよい（書き直した行為が使う）。
  保存したモデルの定義を消す・対応に無い定義（性質・`Init`・`Spec`）を変えるのは違い。
  **比べる前に注釈（`(* … *)`・`\\*`）を除く**——注釈で行頭の定義を隠して行頭でない位置に弱めた定義を置く形を、TLC と同じに読むため。
- **対応に挙げても書き直してはならない定義**——本体の `.cfg` が名指す名前（`Init`・`Next`・性質など）と、性質（`INVARIANT`・`PROPERTY`）の定義がたどって使う定義。

**渡す保存したモデルは、正本の対象の記録（番号が最大の版）そのもの**——別の版・写しを渡すと 2。

| 結果 | 条件 | 終了コード |
| --- | --- | --- |
| `反例なし` | 保存したモデルもコードのモデルも `満たす`（本体で反例なし・陽性対照で反例あり） | 0 |
| `反例あり（コードの不具合）` | 保存したモデルが `満たす` で、コードのモデルの本体が反例を出す（既定） | 1 |
| `反例あり（モデルのずれ）` | 同じで、`--intended`（周の Issue が求める意図した変更と周が判断した）を付けた | 1 |
| `判定できなかった` | 弱めた違いがある・保存したモデルが `満たす` でない（基準が壊れている——spec-loop で直す）・コードのモデルが走らない・空振り・TLC の呼び方が無い | 4 |

出力の最後の行が、計画ファイルに写す行（`形式検査の再検査: <対象> <結果>`）である。

## check — PR の前に計画を見る

`touched` と同じに触れたモデルを引き、計画ファイルの行頭（`- ` を前に置いてよい。コードフェンスの中は数えない）の `形式検査の再検査: <対象> <結果>` を見る。

- **触れたモデルの行が無い・結果が上の 4 つでない・同じ対象の行が 2 本ある**——1
- **`反例あり（コードの不具合）`**——1（コードを直して走らせ直し、行を書き直してから PR を作る）
- **`反例あり（モデルのずれ）` なのに、計画に中身のある `正本に起票する行:` の行と `仕様の振る舞い: 変える` の申告（`references/spec-writeback.md`）がそろわない**——1
- **周の差分が、保存したモデルのファイルを変えた・記録（`README.md`）の `実装の対応`・`対応を確かめたコミット` のほかの行を変えた**——1（モデルは spec-loop で直す。正本が別のリポジトリなら見ない）
- `判定できなかった`——0（PR コメントで渡す。止めないが緑ではない）・`反例なし`——0
- モデルが 1 つも無い——何も求めずに 0（`--spec-loop` も要らない）

## 終了コード

| コード | `touched` | `rerun` | `check` |
| --- | --- | --- | --- |
| 0 | 引けた（触れたモデルが 0 件でも） | 反例なし | 求めるものが揃っている |
| 1 | — | 反例あり | 上の 1 のどれか |
| 2 | 判定できない——引数の誤り・git が失敗した・base が HEAD の祖先でない・`--spec-loop` が無い（モデルがあるとき）・記録が読めない・対応の形が違う・想定外の例外 | 同じ | 同じ |
| 4 | — | 判定できなかった | — |

## 何を守り、何を守らないか

守る:

| 守ること | 破る形 |
| --- | --- |
| 触れたモデルの再検査の行が無ければ PR の前に 1 | 対応のファイルを変えた周が、モデルを走らせずに PR を作る（Issue の受入基準 2） |
| コードのモデルの反例を既定で `コードの不具合` にし、`check` が 1 | 性質を破るコードを PR に載せる（受入基準 3） |
| `モデルのずれ` は `正本に起票する行:` を要る | 性質を変えたことを正本に残さずに、モデルのずれと言って通す |
| 対応の行為の定義のほかが保存したモデルと違えば `判定できなかった` | 性質・`Init`・設定・陽性対照を弱めて「反例なし」にする |
| 保存したモデルが `満たす` でなければ `判定できなかった` | 壊れた基準と比べて「反例なし」と読む |
| 未コミット・未追跡の変更も触れたに数える | 2 点の差分の外にある実装を見落とす |
| 差分の名前を `-z` で読む | ASCII でない名前が引用符つきの 8 進で出て、対応の名前と合わない |
| 注釈を除いてから比べる | 注釈で行頭の性質を隠し、行頭でない位置の弱めた定義を TLC に読ませる |
| 設定が名指す名前と性質が使う定義は、対応に挙げても書き直しを許さない | 対応に性質を挙げて書き直し、弱めて「反例なし」にする |
| 渡す保存したモデルを正本の記録に限り、周の差分が保存したモデルを変えたら `check` が 1 | 古い版・写し・周の中で弱めたモデルを基準にする |
| 記録の読み方・TLC の呼び方と判定は spec-loop から読み込む | 写しがずれて片方だけ緑になる |

守らない:

| 守らないもの | なぜ |
| --- | --- |
| **コードのモデルが今のコードを正しく写しているか** | 周（LLM）が書く。機械が見るのは、対応の行為のほかを変えていないことと、TLC の結果だけ。Verifier に確かめさせる（`references/formal-sync.md`） |
| **計画の行が本当に `rerun` の結果か** | 行の申告の真偽は機械で決まらない（`check-spec-writeback.py` と同じ） |
| **`--intended` の判断が正しいか** | 意図は機械で決まらない。既定を不具合の側に倒し、ずれには正本に戻す行を課す |
| **対応に挙げていないファイルの変更**（対応の外で性質を破る） | 対応が網羅しているかは決まらない。対応を書く周が見る |
| **TLC でないモデル**（Alloy など） | `check-formal-rerun.py` が走らせ直さない（`判定できなかった`） |
| **定義の区切りの読み方** | 行頭から始まる行で区切る。行頭に置いた式の続き・中置の演算子の定義は、別の定義の外の行として比べる（違えば止まる側に倒れる） |
| **正本が別のリポジトリのときの写しの時点** | `--canon` に渡した写しを読むだけ。写しが古いかは見ない |

標準ライブラリだけを使う（`git` が要る）。
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

LINE_KEY = "形式検査の再検査:"
NO_COUNTEREXAMPLE = "反例なし"
CODE_BUG = "反例あり（コードの不具合）"
MODEL_DRIFT = "反例あり（モデルのずれ）"
UNKNOWN = "判定できなかった"
RESULTS = (NO_COUNTEREXAMPLE, CODE_BUG, MODEL_DRIFT, UNKNOWN)
WRITEBACK_KEY = "正本に起票する行:"
SYNC_ITEMS = ("実装の対応", "対応を確かめたコミット")
COMPARED_ITEMS = ("モデルのファイル", "陽性対照のファイル", "実装の対応")
VERSION = re.compile(r"v([1-9][0-9]*)")
DEFINITION = re.compile(r"(?:LOCAL\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*==")
PLAN_LINE = re.compile(r"^(?:[-*]\s+)?" + re.escape(LINE_KEY) + r"\s*(\S+)\s+(.+?)\s*$")
# `check-spec-writeback.py` の DECLARE・ROW_LINE と同じ形（前置きの `- `・`* ` を許す）
WRITEBACK_LINE = re.compile(r"^(?:[-*]\s+)?" + re.escape(WRITEBACK_KEY) + r"\s*(.*?)\s*$")
DECLARE_LINE = re.compile(r"^(?:[-*]\s+)?仕様の振る舞い:\s*(.*?)\s*$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CFG_KEYWORDS = {"INIT", "NEXT", "SPECIFICATION", "INVARIANT", "INVARIANTS", "PROPERTY", "PROPERTIES", "CONSTANT", "CONSTANTS",
                "CONSTRAINT", "CONSTRAINTS", "ACTION_CONSTRAINT", "ACTION_CONSTRAINTS", "SYMMETRY", "VIEW", "CHECK_DEADLOCK",
                "POSTCONDITION", "ALIAS", "TRUE", "FALSE"}
PROPERTY_KEYWORDS = {"INVARIANT", "INVARIANTS", "PROPERTY", "PROPERTIES"}


class Unjudged(Exception):
    """判定できない（終了コード 2）。"""


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise Unjudged(f"git {' '.join(args)} が失敗した: {proc.stderr.strip()}")
    return proc.stdout


def repo_root() -> Path:
    return Path(git("rev-parse", "--show-toplevel").strip())


def find_models(canon: Path) -> dict[str, Path]:
    """対象の名前 → 記録を持つディレクトリ（同じ対象は番号が最大の版）。"""
    found: dict[str, tuple[int, Path]] = {}
    docs = canon / "docs"
    if not docs.is_dir():
        return {}
    for version in docs.iterdir():
        m = VERSION.fullmatch(version.name)
        formal = version / "spec" / "formal"
        if not m or not formal.is_dir():
            continue
        for target in formal.iterdir():
            if (target / "README.md").is_file():
                number = int(m.group(1))
                if target.name not in found or found[target.name][0] < number:
                    found[target.name] = (number, target)
    return {name: path for name, (_, path) in sorted(found.items())}


def load_spec_loop(directory: Path | None):
    """spec-loop の `check-formal-rerun.py` を読み込む（`baseline`・`tlc` もそこが読み込む）。"""
    if directory is None:
        raise Unjudged("--spec-loop（spec-loop プラグインの base ディレクトリ）が無い——記録の読み方と TLC の呼び方を写さないので、渡されなければ判定しない")
    script = directory / "scripts" / "check-formal-rerun.py"
    if not script.is_file():
        raise Unjudged(f"{script}: 無い——--spec-loop は spec-loop プラグインの base ディレクトリ（scripts/check-formal-rerun.py を持つ）")
    spec = importlib.util.spec_from_file_location("check_formal_rerun", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module.baseline, "parse_mapping"):
        raise Unjudged(f"{directory}: spec-loop が古い（formal-baseline.py に parse_mapping が無い——#1178 より前の版）")
    return module


def records(rerun_module, directory: Path) -> dict[str, str]:
    try:
        found, problems = rerun_module.baseline.read_records(directory / "README.md")
    except rerun_module.baseline.Unjudged as e:
        raise Unjudged(str(e))
    if problems:
        raise Unjudged("; ".join(problems))
    return found


def mapping(rerun_module, directory: Path, found: dict[str, str]) -> list[tuple[str, str, str]]:
    value = found.get(SYNC_ITEMS[0])
    if value is None:
        return []
    entries = rerun_module.baseline.parse_mapping(value)
    if entries is None:
        raise Unjudged(f"{directory}/README.md: 実装の対応の形が違う（formal-baseline.py check を当てる）: {value!r}")
    return entries


def changed_files(base: str) -> set[str]:
    if subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"], capture_output=True).returncode != 0:
        raise Unjudged(f"{base}: HEAD の祖先でない——周の base を渡す（SKILL.md 手順 4。main を取り込んだ後は式を当て直す）")
    # -z で読む——既定の core.quotePath では ASCII でない名前が引用符つきの 8 進で出て、対応の名前と合わない
    names = git("diff", "--name-only", "--no-renames", "-z", base).split("\0")
    names += git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    return {n for n in names if n}


def touched(base: str, spec_loop: Path | None, canon: Path | None) -> tuple[list[tuple[str, Path, list[str]]], list[str]]:
    """(触れたモデル [(対象, ディレクトリ, 触れたファイル)], 説明の行)。"""
    root = repo_root()
    models = find_models(canon or root)
    if not models:
        return [], [f"形式検査のモデルが無い（{(canon or root) / 'docs'}/v<n>/spec/formal/<対象>/README.md）——何も求めない"]
    module = load_spec_loop(spec_loop)
    changed = changed_files(base)
    hits, notes = [], []
    unmapped = []
    for name, directory in models.items():
        entries = mapping(module, directory, records(module, directory))
        if not entries:
            unmapped.append(name)
            continue
        files = sorted({path for _, path, _ in entries})
        hit = [f for f in files if f in changed]
        stale = [f for f in files if f not in changed and not (root / f).is_file()]
        if stale:
            notes.append(f"対応が古い: {name}——対応のファイルが今の木に無い: {', '.join(stale)}")
        if hit:
            hits.append((name, directory, hit))
    if unmapped:
        notes.append(f"対応の無いモデル（未実装・行が無い）: {', '.join(unmapped)}——触れたかを決められない")
    return hits, notes


def strip_comments(text: str) -> str:
    """TLA+ の注釈（入れ子の `(* … *)` と行の `\\*` から行末まで）を除く。文字列 `"…"` の中は除かない。改行は残す（行の区切りを変えない）。

    注釈で定義を隠す形（行為の本文で `(*` を開き、行頭の性質の定義を注釈に入れて、行頭でない位置に弱めた定義を置く）を、
    比べる前に TLC と同じに読むため（#1178 の 1 パス目の反証）。
    """
    out: list[str] = []
    i, depth, quoted = 0, 0, False
    while i < len(text):
        ch, two = text[i], text[i:i + 2]
        if depth:
            if two == "(*":
                depth, i = depth + 1, i + 2
            elif two == "*)":
                depth, i = depth - 1, i + 2
            else:
                if ch == "\n":
                    out.append(ch)
                i += 1
        elif quoted:
            out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            quoted = ch != '"'
            i += 1
        elif two == "(*":
            depth, i = 1, i + 2
        elif two == "\\*":
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
        else:
            quoted = ch == '"'
            out.append(ch)
            i += 1
    return "".join(out)


def split_module(text: str) -> tuple[dict[str, str], list[str]]:
    """TLA+ の本文を (定義の名前 → 定義の本文, 定義の外の行) に分ける。定義は行頭から始まり、次に行頭から始まる行の前まで。"""
    definitions: dict[str, str] = {}
    others: list[str] = []
    current: str | None = None
    for line in text.splitlines():
        starts = bool(line) and not line[0].isspace()
        if starts:
            m = DEFINITION.match(line)
            current = m.group(1) if m else None
            if current is not None:
                if current in definitions:
                    raise Unjudged(f"定義「{current}」が 2 つある")
                definitions[current] = line + "\n"
                continue
        if current is not None:
            definitions[current] += line + "\n"
        elif line.strip():
            others.append(line)
    return definitions, others


def weakened(module, saved: Path, code: Path, saved_records: dict[str, str]) -> list[str]:
    """コードのモデルが、対応の行為の定義のほかで保存したモデルと違う点。"""
    problems = []
    try:
        code_records = records(module, code)
    except Unjudged as e:
        return [f"コードのモデルの記録が読めない: {e}"]
    for item in COMPARED_ITEMS:
        if code_records.get(item) != saved_records.get(item):
            problems.append(f"記録の「{item}」が保存したモデルと違う")
    actions = {action for action, _, _ in mapping(module, saved, saved_records)}
    controls = module.baseline.FILE.findall(saved_records.get("陽性対照のファイル", ""))
    models = module.baseline.FILE.findall(saved_records.get("モデルのファイル", ""))
    named, properties = cfg_names(saved, [n for n in models if n.endswith(".cfg") and n not in controls])
    for name in dict.fromkeys(models + controls):
        a, b = saved / name, code / name
        if not b.is_file():
            problems.append(f"コードのモデルに {name} が無い")
            continue
        if not a.is_file():
            continue  # 保存したモデルの欠けは rerun が出す
        if name in controls or not name.endswith(".tla"):
            if a.read_bytes() != b.read_bytes():
                problems.append(f"{name} が保存したモデルと違う（設定と陽性対照は変えない）")
            continue
        try:
            saved_defs, saved_others = split_module(strip_comments(a.read_text(encoding="utf-8")))
            code_defs, code_others = split_module(strip_comments(b.read_text(encoding="utf-8")))
        except (Unjudged, UnicodeDecodeError) as e:
            problems.append(f"{name} を読めない: {e}")
            continue
        if saved_others != code_others:
            problems.append(f"{name} の定義の外の行（MODULE・EXTENDS・VARIABLES・CONSTANTS・ASSUME など）が保存したモデルと違う")
        # 書き直してよいのは、対応の行為のうち、設定が名指さず性質の定義が（たどって）使わないものだけ（#1178 の 1 パス目の指摘）
        protected = named | closure(saved_defs, properties)
        for action in sorted(actions & protected & set(saved_defs)):
            if code_defs.get(action) != saved_defs[action]:
                problems.append(f"{name} の定義「{action}」は設定（.cfg）が名指すか性質の定義が使う——実装の対応に挙げても書き直さない")
        for definition, body in saved_defs.items():
            if definition not in code_defs:
                problems.append(f"{name} から定義「{definition}」が消えた")
            elif definition not in actions and code_defs[definition] != body:
                problems.append(f"{name} の定義「{definition}」が保存したモデルと違う（書き直してよいのは実装の対応に挙げた行為だけ）")
    return problems


def cfg_names(directory: Path, cfgs: list[str]) -> tuple[set[str], set[str]]:
    """本体の `.cfg` が名指す名前の全部と、そのうち性質（INVARIANT・PROPERTY）として名指す名前。"""
    named: set[str] = set()
    properties: set[str] = set()
    for cfg in cfgs:
        try:
            text = strip_comments((directory / cfg).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        keyword = None
        for word in IDENT.findall(text):
            if word in CFG_KEYWORDS:
                keyword = word
                continue
            named.add(word)
            if keyword in PROPERTY_KEYWORDS:
                properties.add(word)
    return named, properties


def closure(definitions: dict[str, str], roots: set[str]) -> set[str]:
    """roots の定義が（たどって）使う定義の名前（roots を含む）。"""
    seen: set[str] = set()
    todo = [r for r in roots if r in definitions]
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        body = definitions[name].split("==", 1)[1] if "==" in definitions[name] else ""
        todo += [w for w in IDENT.findall(body) if w in definitions and w not in seen]
    return seen


def rerun(target: Path, code: Path, spec_loop: Path | None, canon: Path | None, intended: bool, timeout: int) -> tuple[int, list[str]]:
    module = load_spec_loop(spec_loop)
    root = canon or repo_root()
    if not target.is_dir() or not code.is_dir():
        raise Unjudged(f"{target if not target.is_dir() else code}: ディレクトリでない")
    models = find_models(root)
    if target.name not in models or models[target.name].resolve() != target.resolve():
        where = models[target.name] if target.name in models else "（無い）"
        raise Unjudged(f"{target}: 正本の対象「{target.name}」の記録（番号が最大の版）でない——{where} を渡す（#1178 の 1 パス目の指摘）")
    saved_records = records(module, target)
    if not mapping(module, target, saved_records):
        raise Unjudged(f"{target}: 実装の対応が無い（未実装・行が無い）——どの行為をコードに当てるか決まらない")
    lines: list[str] = []
    problems = weakened(module, target, code, saved_records)
    try:
        call, _, note = module.tlc.read_declarations(root)
    except module.tlc.Unknown as e:
        call, note = None, str(e)
    if call is None:
        lines.append(f"注記: {note}")
    if problems:
        lines += [f"弱めた違い: {p}" for p in problems]
        result = UNKNOWN
    else:
        saved_verdict, saved_lines = module.rerun(call, target, timeout)
        lines += [f"保存したモデル: {line}" for line in saved_lines]
        if saved_verdict != module.PASS:
            lines.append(f"保存したモデルが「{module.PASS}」でない（{saved_verdict}）——比べる基準が壊れている。spec-loop で直す")
            result = UNKNOWN
        else:
            code_verdict, code_lines = module.rerun(call, code, timeout)
            lines += [f"コードのモデル: {line}" for line in code_lines]
            if code_verdict == module.PASS:
                result = NO_COUNTEREXAMPLE
            elif code_verdict == module.COUNTEREXAMPLE:
                result = MODEL_DRIFT if intended else CODE_BUG
            else:
                result = UNKNOWN
    lines.append(f"{LINE_KEY} {target.name} {result}")
    return {NO_COUNTEREXAMPLE: 0, CODE_BUG: 1, MODEL_DRIFT: 1, UNKNOWN: 4}[result], lines


def plan_lines(plan: Path) -> tuple[dict[str, list[str]], bool]:
    """計画ファイルの (対象 → 結果の並び, `正本に起票する行:` があるか)。コードフェンスの中は数えない。"""
    try:
        text = plan.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Unjudged(f"{plan}: 読めない（{e}）")
    found: dict[str, list[str]] = {}
    rows, declares = [], []
    fenced = False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = PLAN_LINE.match(line)
        if m:
            found.setdefault(m.group(1), []).append(m.group(2))
        w = WRITEBACK_LINE.match(line)
        if w and w.group(1):
            rows.append(w.group(1))
        d = DECLARE_LINE.match(line)
        if d:
            declares.append(d.group(1))
    # モデルのずれは性質を変える——中身のある起票の行と、`仕様の振る舞い: 変える` の申告がそろうときだけ戻したと読む
    return found, bool(rows) and declares == ["変える"]


def saved_model_changes(base: str, canon: Path | None) -> list[str]:
    """周の差分が、保存したモデル（README.md の 2 行のほか）を変えていないか。正本が別のリポジトリなら見ない。"""
    root = repo_root()
    if canon is not None and canon.resolve() != root.resolve():
        return []
    changed = changed_files(base)
    problems = []
    for name, directory in find_models(root).items():
        rel = directory.resolve().relative_to(root.resolve()).as_posix()
        for path in sorted(p for p in changed if p.startswith(rel + "/")):
            if path != f"{rel}/README.md":
                problems.append(f"{name}: 周の差分が保存したモデルのファイル {path} を変えた——モデルは spec-loop で直す（周が書いてよいのは README.md の {'・'.join(SYNC_ITEMS)} だけ）")
            elif not readme_rows_kept(base, path, root / path):
                problems.append(f"{name}: 周の差分が {path} の {'・'.join(SYNC_ITEMS)} のほかの行を変えた——モデルは spec-loop で直す")
    return problems


def readme_rows_kept(base: str, rel: str, now: Path) -> bool:
    """base の時点の記録の表と今の表が、2 行のほかで同じか（base に無ければ新しく足したモデル——変えたと読む）。"""
    proc = subprocess.run(["git", "show", f"{base}:{rel}"], capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    def rows(text: str) -> list[str]:
        return [line.strip() for line in text.splitlines()
                if line.strip().startswith("|") and line.strip().split("|")[1].strip() not in SYNC_ITEMS]
    try:
        return rows(proc.stdout) == rows(now.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return False


def check(plan: Path, base: str, spec_loop: Path | None, canon: Path | None) -> tuple[int, list[str]]:
    hits, notes = touched(base, spec_loop, canon)
    if not hits:
        return 0, notes + ["触れたモデルは無い——再検査の行は求めない"]
    found, writeback = plan_lines(plan)
    problems, lines = [], list(notes)
    problems += saved_model_changes(base, canon)
    for name, _, files in hits:
        results = found.get(name, [])
        where = f"{name}（触れた対応のファイル: {', '.join(files)}）"
        if not results:
            problems.append(f"{where}: 計画に「{LINE_KEY} {name} <結果>」の行が無い——formal-sync.py rerun で走らせ直して写す（references/formal-sync.md）")
        elif len(results) > 1:
            problems.append(f"{where}: 再検査の行が {len(results)} 本ある——1 本にする")
        elif results[0] not in RESULTS:
            problems.append(f"{where}: 結果「{results[0]}」が {'・'.join(RESULTS)} のどれでもない")
        elif results[0] == CODE_BUG:
            problems.append(f"{where}: {CODE_BUG}——コードを直して走らせ直し、行を書き直してから PR を作る")
        elif results[0] == MODEL_DRIFT and not writeback:
            problems.append(f"{where}: {MODEL_DRIFT} なのに計画に中身のある「{WRITEBACK_KEY}」の行と「仕様の振る舞い: 変える」の申告がそろっていない——性質を変えたことを正本に戻す（references/spec-writeback.md）")
        elif results[0] == UNKNOWN:
            lines.append(f"{where}: {UNKNOWN}——PR コメントで渡す（緑ではない）")
        else:
            lines.append(f"{where}: {results[0]}")
    if problems:
        return 1, lines + problems
    return 0, lines


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="形式検査のモデルと実装を揃えておく（#1178）")
    sub = parser.add_subparsers(dest="command")
    t = sub.add_parser("touched")
    t.add_argument("base")
    r = sub.add_parser("rerun")
    r.add_argument("target", type=Path)
    r.add_argument("--code-model", type=Path, required=True)
    r.add_argument("--intended", action="store_true")
    r.add_argument("--timeout", default="600")
    c = sub.add_parser("check")
    c.add_argument("plan", type=Path)
    c.add_argument("base")
    for p in (t, r, c):
        p.add_argument("--spec-loop", type=Path)
        p.add_argument("--canon", type=Path)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        if args.command == "touched":
            hits, notes = touched(args.base, args.spec_loop, args.canon)
            code, lines = 0, notes + [f"触れたモデル: {name}（{', '.join(files)}）——{directory}" for name, directory, files in hits]
            if not hits:
                lines.append("触れたモデルは無い")
        elif args.command == "rerun":
            if not args.timeout.isdigit() or int(args.timeout) < 1:
                raise Unjudged(f"--timeout は 1 以上の整数: {args.timeout!r}")
            code, lines = rerun(args.target, args.code_model, args.spec_loop, args.canon, args.intended, int(args.timeout))
        elif args.command == "check":
            code, lines = check(args.plan, args.base, args.spec_loop, args.canon)
        else:
            parser.print_usage(sys.stderr)
            return 2
    except Unjudged as e:
        print(f"判定できない: {e}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も 2（判定できない）。トレースバックの 1 に化けさせない
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定できない", file=sys.stderr)
        sys.exit(2)
