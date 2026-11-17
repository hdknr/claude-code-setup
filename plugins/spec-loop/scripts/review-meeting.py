#!/usr/bin/env python3
"""モックと Q&A 表で進めるレビュー会の、機械で決まる部分（req-loop の手順 1・3・4。#1082）。

usage:
  python3 review-meeting.py notes <正本の根> <reviews/<日付> のディレクトリ>
  python3 review-meeting.py rows <正本の根> <reviews/<日付> のディレクトリ> [--dry-run]
  python3 review-meeting.py groups <正本の根> <Q&A 表> <テーマの JSON> <出力の JSON>

**決まりの正は `references/tree.md` の「レビュー会の記録」である**（このプラグインの中にある）。下の定数（置き場所・ファイルの名前・
記録の列・種類・見送りの種類・起票元の詳細・質問の添え書き・画面のまとまりの名前）はそこに書いた決まりの写しで、
写しがずれていないかは、このプラグインを置いているリポジトリ（hdknr/claude-code-setup）のテスト test-review-meeting.py が突き合わせる。

3 つの口がある:

- **`notes`**——会の記録（`reviews/<日付>/notes.csv`）を検査し、指摘（起票済みか）と回答の候補（いまの Q&A の行と並べて）を出す。**何も書かない**——
  回答の候補を `回答` に書くのは、req-loop が利用者に確かめた後である（手順 1。書くのはスキルで、このスクリプトではない）。
- **`rows`**——スキル（LLM）が会の記録の指摘から書いた振り分けのファイル（`reviews/<日付>/triage.json`。指摘ごとに質問の候補か見送り）を検査し、
  質問の候補を**作業中の版（`docs/` の版で番号が最大のもの）の `shared/qa.csv`** に `確認中`・`未回答`・`—` の行として足す。
  足した後の表全体を `check-qa-csv.py` に当て、通らなければ書かない。`--dry-run` は書かずに行を出す。
- **`groups`**——資料に載る質問（`qa-to-pptx.py` の `read_pending`）を、画面の表（重ね合わせた全体）の「質問 → 画面」の逆引きで画面ごとにまとめ、
  画面に掛からない質問はスキルが決めたテーマ（テーマの JSON。`{"<テーマ>": ["Q-R-001", …], …}`）に入れて、`qa-to-pptx.py --groups` に渡す JSON を書く。

**守ること**:

- `notes` も `rows` も `groups` も、Q&A 表の `回答`・`状態`・`反映先` を書き換えない——`notes` は何も書かず、`rows` は行を足すだけ（既にある行のバイトを変えない）
- 会の記録は `<正本の根>/reviews/<YYYY-MM-DD>/notes.csv` だけを読む——ディレクトリが `reviews/` の下の日付の名前でなければ 2
- 会の記録の見出しは `NOTE_COLUMNS` と同じ文字列・同じ順。`種類` は `指摘`・`回答`。`メモ` は空にしない。**指摘の `No` は空**（番号は req-loop が振る——ループの外で振らない）。
  **回答の `No` は共有の層の番号で、重ね合わせた全体の共有の表に在る行**、`発言者` は空にしない（誰が答えたか）。`対象` は改行を含まない。反すれば 1
- `rows` の行は必ず `回答 = 未回答`・`反映先 = —`・`状態 = 確認中`——振り分けのファイルに回答・状態・反映先の鍵があれば 1 で、何も書かない
- `rows` の起票元は `要求確定（レビュー会 <日付>）`、質問の文の後ろに `（レビュー会 <日付> の指摘 <行>。対象: <対象>）`（`対象` が空なら `。対象: …` を付けない）
- 記録の行の番号（`指摘 <行>`・振り分けの `note`）は、見出しと空行を除いて上から 1 から数える
- `rows` は会の記録の指摘をどれも落とさない——まだ起票していない指摘の行は、質問の候補（1 つ以上）か見送り（ちょうど 1 つ）のどちらかに入る。入らない・両方に入る・
  指摘でない行や無い行を指す・起票済み（質問の文に上の添え書きの頭がある行が全部の版を通して在る）の指摘を見送りにする・起票済みの指摘に起票した質問と違う質問を足す、はどれも 1 で何も書かない。
  **起票済みの指摘の候補で、作った質問の文が既にある行と同じものは、足さずに通す**——振り分けのファイルは会の記録として残し、末尾に足した指摘のために同じファイルで当て直すため
- 見送りの種類は `見た目`（範囲の外——`references/spec-scope.md` の「見た目」）・`既にある`（`detail` に、重ね合わせた全体の共有の表に在る番号を書く）・`質問にしない`。`detail` は空にしない
- `rows` は同じ質問の行を足さない——候補から作った質問の文が、既にある行（全部の版を重ねた全体）の質問と同じなら 1
- 番号は `Q-R-` の、全部の版の `shared/qa.csv` を通した最大の次から振る（`intake-code.py` の `next_number` を読み込む——写さない）
- `rows` は既にある作業中の版の表の BOM と改行（CRLF か LF。最初の行で決める）を保って書く。足す行が無ければ書かない
- `groups` の「その質問の画面」は screen-spec の `references/mock.md` の「レビュー会の進め方」の逆引き——画面の行・その画面の項目（`画面ID`）・その画面を遷移元にする遷移（`遷移元`）の
  どれかのセルにその質問の番号がある画面のうち、画面の表の順で最初のもの。画面ごとのまとまりの名前は `画面 <画面ID> <画面名>`、並びは画面の表の順
- `groups` のテーマは、画面に掛からない質問だけを、どれも落とさずちょうど 1 つずつ入れる——画面に掛かる質問・資料に載らない番号・どのテーマにも無い画面に掛からない質問・
  2 つのテーマに入る質問・空のテーマ・画面のまとまりと同じ名前のテーマは、どれも 1 で書かない
- `groups` は出力先が入力の Q&A 表と同じファイルなら 2 で書かない。セルの中の番号は screen-spec の `check-screens.py` と同じ境界で読む（`FAQ-001` の中の `Q-001` を番号と読まない）
- `groups` の出力は JSON のオブジェクト（鍵がまとまりの名前、値が質問の番号の並び。並びは鍵の順——画面のまとまりが先で画面の表の順、続けてテーマを渡した順。中の質問は Q&A 表の順）

終了コード:

- 0: `notes` は出した。`rows` は書いた（`--dry-run` なら出した。足す行が無ければ書かない）。`groups` は書いた
- 1: 会の記録・振り分けのファイル・テーマの JSON が決まりに反する（全部を出す）。何も書いていない
- 2: 判定していない——引数の誤り・正本や表が読めない・版を重ねられない・作業中の版の Q&A 表や資料の表が検査を通らない・内部の層の表を渡した・書けない・想定外の例外

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。Q&A 表の列・印・検査は `check-qa-csv.py`、
版の重ね合わせと画面の表のパスと鍵の列は `merge-versions.py`、番号の振り方は `intake-code.py`、資料に載る行は `qa-to-pptx.py` を読む（写さない）。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **記録の中身が会で実際に出たことと合うか**（言い漏れ・聞き違い） | 記録は人が書く。口が見るのは形と、記録の指摘を振り分けから落とさないことだけ |
| **`対象` の番号が画面の表に在るか** | 写すだけ。画面の表の参照の検査は screen-spec の `check-screens.py` |
| **質問の候補が指摘の意味を写しているか・見送りの理由が正しいか**（見た目でないものを `見た目` で見送る） | 判断であって一意に決まらない。スキルが書き、利用者が資料と振り分けのファイルで確かめる |
| **質問が既にある質問と同じ意味か** | 見るのは質問の文がそのまま一致する行だけ（`既にある` の見送りは番号が在ることだけを見る） |
| **回答の候補のメモが、どの選択肢を選んだか一意に読めるか** | 手順 2 の「選択肢のどれを選んだか一意に読めるか」はスキルが利用者と確かめる |
| **テーマの名前の付け方** | 資料の並べ方の判断で、スキルが決める |
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


qa = _load("check_qa_csv", "check-qa-csv.py")
mv = _load("merge_versions", "merge-versions.py")
ic = _load("intake_code", "intake-code.py")
pp = _load("qa_to_pptx", "qa-to-pptx.py")

# ---- `references/tree.md` の「レビュー会の記録」の写し
REVIEWS = "reviews"
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
NOTES_NAME = "notes.csv"
TRIAGE_NAME = "triage.json"
MOCK_NAME = "mock.html"
NOTE_COLUMNS = ["種類", "No", "対象", "メモ", "発言者"]
KIND_FINDING, KIND_ANSWER = "指摘", "回答"
NOTE_KINDS = (KIND_FINDING, KIND_ANSWER)
SKIP_KINDS = ("見た目", "既にある", "質問にしない")
SKIP_EXISTING = "既にある"
SOURCE_NAME = "要求確定"  # 起票元（印は qa.MARKS から引く）
MARK = qa.MARKS[SOURCE_NAME]
SOURCE_DETAIL = "レビュー会 {date}"          # 起票元 = 要求確定（レビュー会 2026-11-20）
NOTE_HEAD = "（レビュー会 {date} の指摘 {line}"  # 質問の後ろの添え書きの頭（起票済みの判定にも使う）
SCREEN_GROUP = "画面 {id} {name}"
# ---- 写しここまで

CANDIDATE_KEYS = {"note", "question", "options", "recommend", "reason"}
CANDIDATE_OPTIONAL = {"cost"}
SKIP_KEYS = {"note", "kind", "detail"}
TOP_KEYS = {"candidates", "skipped"}
CONFIRMING = ("answer", "回答", "state", "状態", "target", "反映先")
PENDING = "確認中"
QA_PATH = "shared/qa.csv"
SCREENS = mv.SCREENS_DATA + "screens.csv"
ITEMS = mv.SCREENS_DATA + "screen-items.csv"
TRANSITIONS = mv.SCREENS_DATA + "transitions.csv"
# セルの中の共有の層の番号。境界は screen-spec の `check-screens.py` の `qa_number`（モックの逆引きが使う）と同じ——
# 画面ID `FAQ-001` の中の `Q-001` を番号と読まない（spec-loop は screen-spec を読み込まないので、境界だけ写す）
SHARED_NUMBER = re.compile(rf"(?<![A-Za-z0-9-]){qa.NUMBER.pattern}(?![0-9])")


class Stop(Exception):
    """判定していない（終了コード 2）。"""


# ---------------------------------------------------------------- 共通

def merged(root: Path):
    docs = root / "docs"
    if not docs.is_dir():
        raise Stop(f"{docs}: 正本の docs/ が無い")
    try:
        problems, versions, _, canon = mv.merge(docs)
    except mv.Unreadable as e:
        raise Stop(str(e)) from None
    if problems:
        raise Stop("版を重ねられない:\n" + "\n".join(f"  {p}" for p in problems))
    return versions, canon


def csv_rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline="")))


def meeting_dir(root: Path, directory: Path) -> str:
    """会のディレクトリが `<正本の根>/reviews/<YYYY-MM-DD>` なら日付を返す。"""
    try:
        relative = directory.resolve().relative_to(root.resolve())
    except ValueError:
        raise Stop(f"{directory}: 正本の中の {REVIEWS}/<日付>/ でない") from None
    parts = relative.parts
    if len(parts) != 2 or parts[0] != REVIEWS or not DATE.fullmatch(parts[1]):
        raise Stop(f"{directory}: 会のディレクトリは {REVIEWS}/<YYYY-MM-DD>/（正本の根の直下）")
    return parts[1]


def one_line(value, where: str, key: str, problems: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        problems.append(f"{where}: `{key}` が空か文字列でない")
        return ""
    if "\n" in value or "\r" in value:
        problems.append(f"{where}: `{key}` に改行を入れない")
        return ""
    return value.strip()


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def raised(question: str, date: str, line: int) -> bool:
    """質問の文に、その会のその行の指摘の添え書きがあるか（`指摘 1` が `指摘 10` に当たらないよう、後ろの区切りまで見る）。"""
    head = NOTE_HEAD.format(date=date, line=line)
    return (head + "。") in question or (head + "）") in question


def read_notes(root: Path, directory: Path, shared: dict[str, dict[str, str]]) -> tuple[str, list[dict[str, str]], list[str]]:
    """(日付, 記録の行, 決まりに反する点)。行には 1 から数えた `行` を足す。"""
    date = meeting_dir(root, directory)
    path = directory / NOTES_NAME
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except FileNotFoundError:
        raise Stop(f"{path}: 会の記録が無い") from None
    except OSError as e:
        raise Stop(f"{path}: 読めない（{e.strerror}）") from None
    except UnicodeDecodeError:
        raise Stop(f"{path}: UTF-8 として読めない") from None
    problems: list[str] = []
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader, None)
    if header != NOTE_COLUMNS:
        return date, [], [f"{path}: 見出しが決まりと違う（{','.join(NOTE_COLUMNS)} の順）: {header}"]
    rows: list[dict[str, str]] = []
    for fields in reader:
        if not any(f.strip() for f in fields):
            continue
        line = len(rows) + 1
        where = f"{path} の {line} 行目"
        if len(fields) != len(NOTE_COLUMNS):
            problems.append(f"{where}: 列の数が {len(NOTE_COLUMNS)} でない")
            continue
        row = dict(zip(NOTE_COLUMNS, (f.strip() for f in fields)))
        row["行"] = str(line)
        rows.append(row)
        kind = row["種類"]
        if kind not in NOTE_KINDS:
            problems.append(f"{where}: `種類` が {'・'.join(NOTE_KINDS)} のどれでもない: {kind!r}")
            continue
        if not row["メモ"]:
            problems.append(f"{where}: `メモ` が空")
        if "\n" in row["対象"] or "\r" in row["対象"]:
            problems.append(f"{where}: `対象` に改行を入れない")
        if kind == KIND_FINDING and row["No"]:
            problems.append(f"{where}: 指摘の `No` は空にする（番号は req-loop が振る）: {row['No']!r}")
        if kind == KIND_ANSWER:
            if row["No"] not in shared:
                problems.append(f"{where}: 回答の `No` {row['No']!r} が共有の Q&A 表（全部の版を重ねた全体）の質問の番号でない")
            if not row["発言者"]:
                problems.append(f"{where}: 回答の `発言者`（誰が答えたか）が空")
    return date, rows, problems


def shared_rows(canon: dict[str, bytes]) -> dict[str, dict[str, str]]:
    return {r["No"].strip(): r for r in csv_rows(canon.get(QA_PATH, b""))}


# ---------------------------------------------------------------- notes

def notes(root: Path, directory: Path) -> tuple[int, list[str]]:
    _, canon = merged(root)
    shared = shared_rows(canon)
    date, rows, problems = read_notes(root, directory, shared)
    if problems:
        return 1, ["会の記録が決まりに反する:"] + [f"  {p}" for p in problems]
    findings = [r for r in rows if r["種類"] == KIND_FINDING]
    answers = [r for r in rows if r["種類"] == KIND_ANSWER]
    out = [f"レビュー会 {date} の記録（{directory / NOTES_NAME}）: 指摘 {len(findings)} 件・回答の候補 {len(answers)} 件"]
    out.append("指摘:")
    for r in findings:
        done = [no for no, q in shared.items() if raised(q.get("質問", ""), date, int(r["行"]))]
        state = f"起票済み: {'・'.join(done)}" if done else "まだ起票していない"
        target = f"対象: {r['対象']}" if r["対象"] else "対象なし"
        out.append(f"  指摘 {r['行']}（{target}）: {squash(r['メモ'])} — {state}")
    out.append("回答の候補（Q&A 表は書き換えていない——利用者に確かめてから `回答` に書く）:")
    for r in answers:
        q = shared[r["No"]]
        out.append(f"  {r['No']}（いまの状態: {q['状態'].strip()}・回答: {q['回答'].strip()}）: {squash(q['質問'])}")
        out.append(f"    選択肢: {q['選択肢'].strip()}")
        out.append(f"    メモ: {squash(r['メモ'])}（{r['発言者']}）")
    return 0, out


# ---------------------------------------------------------------- rows

def check_keys(obj, allowed: set[str], required: set[str], where: str, problems: list[str]) -> bool:
    if not isinstance(obj, dict):
        problems.append(f"{where}: オブジェクトで書く")
        return False
    confirming = sorted(k for k in obj if k in CONFIRMING)
    if confirming:
        problems.append(f"{where}: {'・'.join(confirming)} は書けない——会の指摘から起こした行は利用者が回答するまで `確認中`・`未回答` で起票する")
    unknown = sorted(k for k in obj if k not in allowed and k not in CONFIRMING)
    if unknown:
        problems.append(f"{where}: 知らない鍵: {'・'.join(unknown)}")
    missing = sorted(required - set(obj))
    if missing:
        problems.append(f"{where}: 鍵が足りない: {'・'.join(missing)}")
    return not (confirming or unknown or missing)


def note_of(value, findings: dict[int, dict[str, str]], where: str, problems: list[str]) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool) or value not in findings:
        problems.append(f"{where}: `note` が会の記録の指摘の行（{'・'.join(map(str, findings)) or '無し'}）でない: {value!r}")
        return None
    return value


def build_row(c: dict, where: str, date: str, findings: dict[int, dict[str, str]], problems: list[str]) -> tuple[int, dict[str, str]] | None:
    before = len(problems)
    if not check_keys(c, CANDIDATE_KEYS | CANDIDATE_OPTIONAL, CANDIDATE_KEYS, where, problems):
        return None
    line = note_of(c["note"], findings, where, problems)
    question = one_line(c["question"], where, "question", problems)
    reason = one_line(c["reason"], where, "reason", problems)
    cost = c.get("cost", "")
    if not isinstance(cost, str) or "\n" in cost or "\r" in cost:
        problems.append(f"{where}: `cost` は 1 行の文字列")
        cost = ""
    options = c["options"]
    labels: list[str] = []
    if not isinstance(options, list) or len(options) < qa.MIN_OPTIONS:
        problems.append(f"{where}: `options` は {qa.MIN_OPTIONS} つ以上の文字列の並び")
    elif len(options) > 26:
        problems.append(f"{where}: `options` が多すぎる（26 まで）")
    else:
        for i, option in enumerate(options):
            if not isinstance(option, str) or not option.strip() or "\n" in option or qa.OPTION_SEPARATOR in option:
                problems.append(f"{where}.options[{i}]: 空でない 1 行の文字列で、` / ` を含めない: {option!r}")
        labels = [chr(ord("A") + i) for i in range(len(options))]
    recommend = c["recommend"]
    if labels and recommend not in labels + [qa.NO_RECOMMENDATION]:
        problems.append(f"{where}: `recommend` が選択肢のラベル（{'・'.join(labels)}）でも `{qa.NO_RECOMMENDATION}` でもない: {recommend!r}")
    if len(problems) != before or line is None:
        return None
    target = findings[line]["対象"]
    tail = NOTE_HEAD.format(date=date, line=line) + (f"。対象: {target}）" if target else "）")
    return line, {
        "No": "", "起票元": f"{SOURCE_NAME}（{SOURCE_DETAIL.format(date=date)}）",
        "質問": question + tail,
        "選択肢": qa.OPTION_SEPARATOR.join(f"{l}: {o.strip()}" for l, o in zip(labels, options)),
        "推奨": recommend, "推奨の理由": reason,
        "回答": qa.NO_ANSWER, "反映先": qa.NO_TARGET, "状態": PENDING, "費用への影響": cost.strip(),
    }


def check_skip(s, where: str, findings: dict[int, dict[str, str]], shared: dict[str, dict[str, str]],
               problems: list[str]) -> tuple[int, str, str] | None:
    before = len(problems)
    if not check_keys(s, SKIP_KEYS, SKIP_KEYS, where, problems):
        return None
    line = note_of(s["note"], findings, where, problems)
    kind = s["kind"]
    if kind not in SKIP_KINDS:
        problems.append(f"{where}: `kind` が {'・'.join(SKIP_KINDS)} のどれでもない: {kind!r}")
    detail = one_line(s["detail"], where, "detail", problems)
    if kind == SKIP_EXISTING and detail:
        numbers = [m.group(0) for m in SHARED_NUMBER.finditer(detail)]
        if not numbers or any(n not in shared for n in numbers):
            problems.append(f"{where}: `{SKIP_EXISTING}` の `detail` に、共有の Q&A 表（全部の版を重ねた全体）に在る番号を書く: {detail!r}")
    if len(problems) != before or line is None:
        return None
    return line, kind, detail


def rows(root: Path, directory: Path, dry_run: bool) -> tuple[int, list[str]]:
    versions, canon = merged(root)
    shared = shared_rows(canon)
    date, notes_rows, problems = read_notes(root, directory, shared)
    if problems:
        return 1, ["会の記録が決まりに反する（何も書いていない）:"] + [f"  {p}" for p in problems]
    target = versions[-1][1] / QA_PATH
    if target.exists():
        code, out = qa.check(target)
        if code != 0:
            raise Stop("作業中の版の Q&A 表が検査を通らない——先に直す:\n" + "\n".join(f"  {line}" for line in out))
        # 既にある表の BOM と改行を保つ（`intake-code.py` の `rows` と同じ読み方——BOM は文字のまま先頭に残す）
        existing = target.read_bytes().decode("utf-8")
    else:
        existing = ",".join(qa.COLUMNS) + "\n"
    eol = "\r\n" if existing.split("\n", 1)[0].endswith("\r") else "\n"
    triage_path = directory / TRIAGE_NAME
    try:
        data = json.loads(triage_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Stop(f"{triage_path}: 振り分けのファイルが無い（会の記録の指摘ごとに、質問の候補か見送りを書く）") from None
    except (OSError, ValueError) as e:
        raise Stop(f"{triage_path}: JSON として読めない（{e}）") from None

    findings = {int(r["行"]): r for r in notes_rows if r["種類"] == KIND_FINDING}
    done = {line for line in findings if any(raised(q.get("質問", ""), date, line) for q in shared.values())}
    errors: list[str] = []
    new_rows: list[dict[str, str]] = []
    skipped: list[tuple[int, str, str]] = []
    covered: dict[int, list[str]] = {}
    filed: list[str] = []  # 起票済みの指摘の候補で、同じ質問が既にあるもの（当て直し。足さない）
    if check_keys(data, TOP_KEYS, TOP_KEYS, "振り分けのファイル", errors):
        if not isinstance(data["candidates"], list) or not isinstance(data["skipped"], list):
            errors.append("振り分けのファイル: `candidates` と `skipped` は並び（無ければ []）")
        else:
            asked = [squash(r.get("質問", "")) for r in shared.values()]
            for i, c in enumerate(data["candidates"]):
                built = build_row(c, f"candidates[{i}]", date, findings, errors)
                if built is None:
                    continue
                line, row = built
                covered.setdefault(line, []).append("候補")
                if line in done:
                    # 振り分けのファイルは会の記録として残す（commit する）ので、末尾に足した指摘のために当て直すと、
                    # 起票済みの指摘の候補もそのまま来る——同じ質問が既にあれば足さずに通し、違う質問なら止める
                    if squash(row["質問"]) in asked:
                        filed.append(row["質問"])
                    else:
                        errors.append(f"candidates[{i}]: 指摘 {line} はもう起票してある（質問の文に {NOTE_HEAD.format(date=date, line=line)}… の行がある）"
                                      "——起票した質問と違う質問を足さない")
                    continue
                if squash(row["質問"]) in asked:
                    errors.append(f"candidates[{i}]: 同じ質問が既にある: {row['質問']!r}")
                    continue
                asked.append(squash(row["質問"]))
                new_rows.append(row)
            for i, s in enumerate(data["skipped"]):
                got = check_skip(s, f"skipped[{i}]", findings, shared, errors)
                if got is None:
                    continue
                covered.setdefault(got[0], []).append("見送り")
                skipped.append(got)
    if not errors:
        for line in findings:
            kinds = covered.get(line, [])
            if line in done:
                if "見送り" in kinds:
                    errors.append(f"指摘 {line}: もう起票してある（質問の文に {NOTE_HEAD.format(date=date, line=line)}… の行がある）——見送りに書かない")
            elif not kinds:
                errors.append(f"指摘 {line}: 質問の候補にも見送りにも無い（会の指摘を落とさない）: {squash(findings[line]['メモ'])}")
            elif "見送り" in kinds and len(kinds) > 1:
                errors.append(f"指摘 {line}: 見送りと質問の候補の両方にあるか、見送りが 2 つある")
    if errors:
        return 1, ["振り分けのファイルが決まりに反する（何も書いていない）:"] + [f"  {e}" for e in errors]

    start = ic.next_number(versions)
    for offset, row in enumerate(new_rows):
        row["No"] = f"Q-{MARK}-{start + offset:03d}"
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator=eol)
    for row in new_rows:
        writer.writerow([row[c] for c in qa.COLUMNS])
    text = existing if existing.endswith("\n") else existing + eol
    text += buffer.getvalue()
    payload = text.encode("utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "qa.csv"
        probe.write_bytes(payload)
        code, out = qa.check(probe)
    if code != 0:
        return 1, ["足した後の表が check-qa-csv.py を通らない（何も書いていない）:"] + [f"  {line}" for line in out]

    report = []
    if dry_run:
        report.append(f"書いていない（--dry-run）。{target} に足すはずの行 {len(new_rows)} 件:")
        report.append(buffer.getvalue().replace("\r\n", "\n").rstrip("\n"))
    elif not new_rows:
        report.append(f"{target} に足す行は無い（書いていない）")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".review-tmp")
        tmp.write_bytes(payload)
        os.replace(tmp, target)
        report.append(f"{target} に {len(new_rows)} 行を足した（{'・'.join(r['No'] for r in new_rows)}。"
                      "どれも `確認中`・`未回答`——利用者が回答するまで確定しない）")
    if filed:
        report.append(f"起票済みの指摘の候補 {len(filed)} 件は、同じ質問が既にあるので足していない（当て直し）")
    report.append(f"見送り: {len(skipped)} 件（Q&A 表に起票しない）")
    report.extend(f"  - 指摘 {line}: {kind}——{detail}" for line, kind, detail in skipped)
    return 0, report


# ---------------------------------------------------------------- groups

def numbers_in(row: dict[str, str]) -> list[str]:
    found: list[str] = []
    for value in row.values():
        for m in SHARED_NUMBER.finditer(value or ""):
            if m.group(0) not in found:
                found.append(m.group(0))
    return found


def screen_of(canon: dict[str, bytes]) -> tuple[dict[str, str], list[str]]:
    """(質問の番号 → 画面のまとまりの名前, 画面のまとまりの名前の並び)。画面の表が無ければ空。"""
    screens = csv_rows(canon[SCREENS]) if SCREENS in canon else []
    items = csv_rows(canon[ITEMS]) if ITEMS in canon else []
    transitions = csv_rows(canon[TRANSITIONS]) if TRANSITIONS in canon else []
    owner: dict[str, str] = {}
    names: list[str] = []
    for screen in screens:
        sid = (screen.get("画面ID") or "").strip()
        name = SCREEN_GROUP.format(id=sid, name=(screen.get("画面名") or "").strip()).strip()
        names.append(name)
        cells = [screen] + [r for r in items if (r.get("画面ID") or "").strip() == sid] \
            + [r for r in transitions if (r.get("遷移元") or "").strip() == sid]
        for row in cells:
            for number in numbers_in(row):
                owner.setdefault(number, name)
    return owner, names


def groups(root: Path, qa_path: Path, themes_path: Path, out: Path) -> tuple[int, list[str]]:
    if qa.is_internal(qa_path):
        raise Stop(f"{qa_path}: 内部の層の表——資料に載せるのは共有の表 shared/qa.csv だけ")
    if out.exists() and qa_path.exists() and out.samefile(qa_path):
        raise Stop(f"{out}: 入力の Q&A 表と同じファイルなので書かない")
    code, lines, pending = pp.read_pending(qa_path)
    if code:
        raise Stop(f"{qa_path}: 検査を通らない:\n" + "\n".join(f"  {line}" for line in lines))
    _, canon = merged(root)
    owner, names = screen_of(canon)
    try:
        themes = json.loads(themes_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise Stop(f"{themes_path}: JSON として読めない（{e}）") from None
    shown = [r["No"].strip() for r in pending]
    errors: list[str] = []
    placed: dict[str, str] = {}
    if not isinstance(themes, dict):
        errors.append(f"{themes_path}: JSON のオブジェクトで書く（鍵がテーマ、値が質問の番号の並び）")
        themes = {}
    for name, numbers in themes.items():
        where = f"テーマ {name!r}"
        if not name.strip() or "\n" in name or "\r" in name:
            errors.append(f"{where}: 名前が空か改行を含む")
        if name.strip() in names:
            errors.append(f"{where}: 画面のまとまりと同じ名前")
        if not isinstance(numbers, list) or not numbers:
            errors.append(f"{where}: 値は質問の番号の空でない並び")
            continue
        for number in numbers:
            if not isinstance(number, str) or number.strip() not in shown:
                errors.append(f"{where}: {number!r} は資料に載る質問の番号でない（反映済みか、表に無い）")
            elif number.strip() in owner:
                errors.append(f"{where}: {number} は画面に掛かる（{owner[number.strip()]}）——テーマに入れない")
            elif number.strip() in placed:
                errors.append(f"{where}: {number} は既に {placed[number.strip()]!r} に入れた")
            else:
                placed[number.strip()] = name.strip()
    missing = [n for n in shown if n not in owner and n not in placed]
    if missing:
        errors.append(f"画面に掛からない質問がテーマに無い: {'・'.join(missing)}")
    if errors:
        return 1, ["テーマの JSON が決まりに反する（何も書いていない）:"] + [f"  {e}" for e in errors]
    result: dict[str, list[str]] = {}
    for name in names:
        members = [n for n in shown if owner.get(n) == name]
        if members:
            result[name] = members
    for name in themes:
        result[name.strip()] = [n for n in shown if placed.get(n) == name.strip()]
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, out)
    except OSError as e:
        raise Stop(f"{out}: 書けない（{e.strerror}）") from None
    report = [f"{out} に {len(result)} のまとまりを書いた（質問 {len(shown)} 件）:"]
    report.extend(f"  {name}: {'・'.join(members)}" for name, members in result.items())
    return 0, report


# ---------------------------------------------------------------- 入口

def main(argv: list[str]) -> int:
    usage = (__doc__ or "").split("\n\n", 2)[1] if __doc__ else "usage: review-meeting.py notes|rows|groups …"
    args = list(argv)
    try:
        if args[:1] == ["notes"] and len(args) == 3:
            code, report = notes(Path(args[1]).resolve(), Path(args[2]))
        elif args[:1] == ["rows"]:
            dry_run = "--dry-run" in args
            args = [a for a in args if a != "--dry-run"]
            if len(args) != 3:
                raise Stop(usage)
            code, report = rows(Path(args[1]).resolve(), Path(args[2]), dry_run)
        elif args[:1] == ["groups"] and len(args) == 5:
            code, report = groups(Path(args[1]).resolve(), Path(args[2]), Path(args[3]), Path(args[4]))
        else:
            raise Stop(usage)
        print("\n".join(report), file=sys.stderr if code == 1 else sys.stdout)
        return code
    except Stop as e:
        print(f"{e}\n判定していない（何も書いていない）", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 — 想定外の例外はトレースバックの 1 にしない
        print(f"想定外の例外: {type(e).__name__}: {e}\n判定していない", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
