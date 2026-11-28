#!/usr/bin/env python3
"""画面の入力の項目と、その画面が呼ぶ入口（spec-loop の中間表現の `operation`）の入力を照らし、食い違いと対応の引けない箇所を件数と種類で出す（#1596）。

usage: python3 survey-input-contract.py <docs ディレクトリ> [--upto <n>] [--map <対応の CSV>] [--detail] [--spec-loop <spec-loop のプラグインの根>]

**調べる道具であって、関門ではない**——案件の正本に当てて、画面の入力の項目と API の入力の契約がどれだけ食い違うか・対応をどれだけ機械で引けるかを数える。
関門をどこに置くか（screen-spec か scaffold か）と対応の持たせ方は、この道具で調べた結果を見てから決める（#1596）。

**決まりの正は `references/input-contract.md` である**（このプラグインの中にある）。下の定数（対応の CSV の見出し・`保存しない`・数える種類の名前）はその写しで、
**写しがずれていないかは、このプラグインを置いているリポジトリの `scripts/test-survey-input-contract.py` が突き合わせる。**

- **表の置き場所・列・項目の種類・区切り・親画面を持つ種別と、spec-loop の見つけ方・版の範囲は `check-screens.py` を読み込む**（写さない）。
  重ね方は spec-loop の `merge-versions.py` の `merge`、中間表現のパスは同じファイルの `SPEC_PATH`（どちらも `check-screens.py` の `Checker` 経由）。
- v1〜v<n>（`--upto` を省くと作業中の版まで）を重ねた全体の `screens.csv`・`screen-items.csv`・`spec/spec_ir.json` を読む。
- **画面 → 入口**: `--map` の画面の行があればそれ。無ければ画面の `機能` の列の機能（`tab`・`dialog` で空なら親の画面の `機能`）のうち、
  中間表現に在り、入力の項目を 1 つ以上持つ入口が 1 つだけなら決まる。
- **項目 → フィールド**: 種類が `入力` の項目。`--map` の項目の行（フィールドのパスか `保存しない`）があればそれ。無ければ項目名が入口の入力のパスか
  パスの末尾の名前と同じ文字列のもの（1 つだけなら引ける）。
- **順向き**: 引けたパスが入口の入力に無ければ食い違い。**逆向き**: 照らした入口（`保存しない` でない入力の項目を持つ画面から決まった入口）の入力の葉のうち、
  どの項目からも指されず、`--map` でシステムが埋めると宣言されてもいないもの。パスの変数（入口の `path` の `{…}`）は別に数え、
  名前で引けない項目のある入口の「指されない」も別に数える（その項目が指すはずの葉かもしれない）。
- **既定の出力は件数と種類だけ**——画面は表の行の順の番号と種別（決まった値でなければ `種別が決まりの外`）で示し、名前・画面ID・項目の番号・入口の id・パスを出さない（案件の名前・業務の中身を公開の報告に持ち出さない）。
  `--detail` を付けたときだけ、画面ID・項目の番号・入口の id・パスを出す（項目名・画面名・機能の題は `--detail` でも出さない）。
- 標準ライブラリだけを使う。

終了コード:

- 0: 照らした（食い違い・引けない箇所が何件あっても 0——関門ではない）
- 3: 照らすものが無い——重ねた全体に画面の表か項目の表が無い・中間表現が無い
- 2: 判定していない——引数の誤り・`docs` が無い・`--upto` の版が無い・読めない・見出し行が決まりと違う・対応の CSV の誤り・重ね合わせが spec-loop の決まりに反する・想定外の例外
- 4: 照らす前に止めた——spec-loop が見つからない・spec-loop の版が読めない・対応の範囲の外（`check-screens.py` と同じ）

**守ること**:

- 照らすのは重ねた全体の行だけ（版の生の行を読まない）。種類が `入力` の項目だけを順向きに数える
- 画面 → 入口は、対応の CSV の画面の行を `機能` の列より先に使う。`機能` が空の `tab`・`dialog` は親の画面を辿り（循環したら辿るのをやめて「機能が空」）、入力を持つ入口が 1 つに決まらなければ決めない
- 入口が決まらない画面の項目は、`保存しない` と書いたものを除いて「画面の入口が決まらない」に数える（対応の CSV にパスがあっても照らさない）
- 項目名で引くのは、パス全体か末尾の名前と同じ文字列のときだけ（言い換え・推定をしない）。当たったパスのうち、ほかの当たったパスの下にあるもの（`m` に対する `m[]`）は外し、それでも 2 つ以上なら引かない
- 入れ子（`a.b`・`rows[].x`・配列の配列 `m[]`）を葉のパスで照らす。項目が親のパス（オブジェクト・配列）を指せば、その下の葉を全部指したとする
- 逆向きは、`保存しない` でない入力の項目を 1 つ以上持つ画面から決まった入口だけを照らし、照らさなかった入力のある入口の数を出す。パスの変数とシステムが埋めると宣言した葉は「指されない」に数えない。
  名前で引けない項目（当たるフィールドが無い・2 つ以上）のある入口の指されない葉は、「指されない」と分けて数える
- 対応の CSV の誤り（見出し・空のセル・対象がどれにも無い・2 つの種類に当たる・入力でない項目・同じ画面か項目が 2 行・パスの形・宣言したパスが入口の入力に無い）は、照らす前に全部出して 2
- 既定の出力に名前・画面ID・項目の番号・入口の id・パスを出さない。`種別` は決まった値のときだけ出す。`--detail` でも項目名・画面名・機能の題を出さない
- ファイルを書かない（正本・対応の CSV・プラグインを書かない。読み込むスクリプトの `__pycache__` も書かない）
- 形の崩れた機能・入口（`operation` が無い・`id` が文字列でない）は飛ばして数を出す（黙って落とさない）

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **型・桁・必須の食い違い** | 名前（パス）の対応だけを見る。#1596 の決定が範囲の外にした |
| **画面の表示の項目と API の出力の対応・出力と振る舞いの食い違い** | 同上 |
| **表の決まり**（辿れない画面・根拠・未決定の印） | `check-screens.py` が見る。この道具は表の検査の結果に依らず照らす（見出し行だけは見る——列が無ければ読めない） |
| **日本語の項目名と英語のフィールド名の対応** | 機械で引けないことを数えるのが目的の 1 つで、推定すると誤った対応を一致に数える。対応は `--map` で渡す |
| **画面設計書を Markdown で書いた正本** | 読むのは screen-spec の表（CSV）だけ。Markdown の画面設計書は表へ移してから当てる |
| **中間表現の決まり** | `scaffold.py` が見る。形の崩れた機能・入口は飛ばして数だけ出す |
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # 読み込むスクリプトの `__pycache__` を書かない（`-I` では環境変数が効かない）


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


screens_check = _load("screen_spec_check_screens", HERE / "check-screens.py")

# ---- `references/input-contract.md` の写し
MAP_COLUMNS = ["対象", "値"]  # 対応の CSV の見出し行
NOT_SAVED = "保存しない"  # 項目の行の値: 保存・送信しない入力（選択のチェックボックスなど）
PATH = re.compile(r"[a-z][a-z0-9_]*(?:\[\])*(?:\.[a-z][a-z0-9_]*(?:\[\])*)*")  # フィールドのパス

# 画面の入口の決まり方
BY_MAP = "対応の CSV"
BY_FEATURE = "機能の列"
BY_PARENT = "親の画面の機能の列"
# 画面の入口が引けない理由
NO_FEATURE = "機能が空"
FEATURE_NOT_IN_IR = "機能が中間表現に無い"
NO_INPUT_OPERATION = "入力を持つ入口が無い"
AMBIGUOUS_OPERATION = "入口が 1 つに決まらない"
MAP_OPERATION_NOT_IN_IR = "対応の CSV の入口が中間表現に無い"
SCREEN_REASONS = (NO_FEATURE, FEATURE_NOT_IN_IR, NO_INPUT_OPERATION, AMBIGUOUS_OPERATION, MAP_OPERATION_NOT_IN_IR)
# 項目の結果
MATCHED = "一致"
MISMATCHED = "食い違い"
SAVED_NOT = NOT_SAVED
UNRESOLVED = "引けない"
# 項目が引けない理由
SCREEN_UNRESOLVED = "画面の入口が決まらない"
NO_FIELD = "当たるフィールドが無い"
MANY_FIELDS = "当たるフィールドが 2 つ以上"
SCREEN_NOT_IN_TABLE = "画面が表に無い"
ITEM_REASONS = (SCREEN_UNRESOLVED, NO_FIELD, MANY_FIELDS, SCREEN_NOT_IN_TABLE)
# 逆向き
UNPOINTED = "どの項目からも指されない"
UNPOINTED_UNSURE = "指されない（引けない項目のある入口）"
SYSTEM_FILLED = "システムが埋めると宣言"
PATH_VARIABLE = "パスの変数"
KIND_OUTSIDE = "種別が決まりの外"  # 既定の出力で、決まった値でない `種別` のセルの代わりに出す

EXIT_OK, EXIT_UNJUDGED, EXIT_NOTHING, EXIT_STOPPED = 0, 2, 3, 4


class Unjudged(Exception):
    """判定していない（2）。"""


class Nothing(Exception):
    """照らすものが無い（3）。"""


# ---- 入口の入力のパス

def walk(path: str, field, out: dict[str, bool]) -> None:
    """`out[パス] = 葉か`。オブジェクトは `.名前`、配列の要素は `[]` で降りる。"""
    out[path] = True
    if not isinstance(field, dict):
        return
    kind = field.get("type")
    if kind == "object" and isinstance(field.get("properties"), dict) and field["properties"]:
        out[path] = False
        for name, sub in field["properties"].items():
            if isinstance(name, str):
                walk(f"{path}.{name}", sub, out)
    elif kind == "array" and isinstance(field.get("items"), dict):
        item = field["items"]
        if item.get("type") == "object" and isinstance(item.get("properties"), dict) and item["properties"]:
            out[path] = False
            for name, sub in item["properties"].items():
                if isinstance(name, str):
                    walk(f"{path}[].{name}", sub, out)
        elif item.get("type") == "array":
            out[path] = False
            walk(f"{path}[]", item, out)


def field_paths(op: dict) -> dict[str, bool]:
    fields = op.get("input")
    out: dict[str, bool] = {}
    if isinstance(fields, dict):
        for name, field in fields.items():
            if isinstance(name, str):
                walk(name, field, out)
    return out


def path_variables(op: dict) -> set[str]:
    path = op.get("path")
    return set(re.findall(r"\{([^{}]+)\}", path)) if isinstance(path, str) else set()


def last_name(path: str) -> str:
    return path.rsplit(".", 1)[-1].replace("[]", "")


def covers(pointer: str, leaf: str) -> bool:
    return leaf == pointer or leaf.startswith(pointer + ".") or leaf.startswith(pointer + "[]")


# ---- 読む

def read_csv(raw: bytes, where: str, required: list[str]) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as e:
        raise Unjudged(f"{where}: CSV として読めない（{e}）") from None
    missing = [column for column in required if column not in (reader.fieldnames or [])]
    if missing:
        raise Unjudged(f"{where}: 見出し行に {'・'.join(missing)} が無い（check-screens.py で直す）")
    return [{key: (value or "").strip() for key, value in row.items() if isinstance(key, str)} for row in rows]


class Survey:
    def __init__(self, spec_loop: Path, docs: Path, upto: int | None, map_path: Path | None) -> None:
        self.checker = screens_check.Checker(spec_loop, docs, upto)  # spec-loop の `merge-versions.py` を読み込む
        self.versions = self.checker.versions
        self.docs = docs
        self.upto = upto
        self.map_path = map_path
        self.skipped = 0  # 形の崩れた機能・入口

    # 重ねた全体
    def load(self) -> None:
        try:
            problems, _, _, rendered = self.versions.merge(self.docs, self.upto)
        except self.versions.Unreadable as e:
            raise Unjudged(str(e)) from None
        if problems:
            raise Unjudged("重ね合わせが spec-loop の決まりに反する:\n" + "\n".join(f"  {p}" for p in problems))
        screens_path, items_path = screens_check.SCREENS, screens_check.ITEMS
        missing = [p for p in (screens_path, items_path) if p not in rendered]
        if missing:
            raise Nothing(f"重ねた全体に {'・'.join(missing)} が無い——照らす画面が無い")
        ir_path = self.versions.SPEC_PATH
        if ir_path not in rendered:
            raise Nothing(f"重ねた全体に {ir_path} が無い——照らす入口が無い（scaffold の前の正本）")
        self.screens = read_csv(rendered[screens_path], screens_path, ["画面ID", "種別", "親画面", "機能"])
        self.items = read_csv(rendered[items_path], items_path, ["番号", "画面ID", "項目名", "種類"])
        try:
            ir = json.loads(rendered[ir_path].decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError) as e:
            raise Unjudged(f"{ir_path}: 中間表現を読めない（{type(e).__name__}）") from None
        features = ir.get("features") if isinstance(ir, dict) else None
        if not isinstance(features, list):
            raise Unjudged(f"{ir_path}: features が配列でない")
        self.ops: dict[str, dict] = {}  # 入口の id → 入口
        self.feature_op: dict[str, str] = {}  # 機能の id → 入口の id
        for feature in features:
            op = feature.get("operation") if isinstance(feature, dict) else None
            if not (isinstance(feature, dict) and isinstance(feature.get("id"), str)
                    and isinstance(op, dict) and isinstance(op.get("id"), str)) or op["id"] in self.ops:
                self.skipped += 1
                continue
            self.ops[op["id"]] = op
            self.feature_op[feature["id"]] = op["id"]
        self.paths = {oid: field_paths(op) for oid, op in self.ops.items()}

    # 対応の CSV
    def read_map(self) -> None:
        self.map_screen: dict[str, str] = {}
        self.map_item: dict[str, str] = {}
        self.map_system: dict[str, set[str]] = {}
        if self.map_path is None:
            return
        try:
            raw = self.map_path.read_bytes()
        except OSError as e:
            raise Unjudged(f"{self.map_path}: 読めない（{e.strerror}）") from None
        try:
            rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
        except (UnicodeDecodeError, csv.Error) as e:
            raise Unjudged(f"{self.map_path}: CSV として読めない（{e}）") from None
        if not rows or rows[0] != MAP_COLUMNS:
            raise Unjudged(f"{self.map_path}: 見出し行が {','.join(MAP_COLUMNS)} でない")
        screen_ids = {row["画面ID"] for row in self.screens if row["画面ID"]}
        inputs = {row["番号"] for row in self.items if row["番号"] and row["種類"] == screens_check.INPUT}
        item_ids = {row["番号"] for row in self.items if row["番号"]}
        problems: list[str] = []
        for line, row in enumerate(rows[1:], start=2):
            where = f"{self.map_path}:{line}"
            if len(row) != len(MAP_COLUMNS):
                problems.append(f"{where}: 列が {len(MAP_COLUMNS)} つでない")
                continue
            target, value = (cell.strip() for cell in row)
            if not target or not value:
                problems.append(f"{where}: 空のセルがある")
                continue
            kinds = [kind for kind, known in (("画面", screen_ids), ("項目", item_ids), ("入口", set(self.ops))) if target in known]
            if not kinds:
                problems.append(f"{where}: 対象が画面の表・項目の表・中間表現の入口のどれにも無い")
            elif len(kinds) > 1:
                problems.append(f"{where}: 対象が {'と'.join(kinds)} の 2 つに当たる")
            elif kinds == ["画面"]:
                if target in self.map_screen:
                    problems.append(f"{where}: 同じ画面の行が 2 つある")
                self.map_screen[target] = value
            elif kinds == ["項目"]:
                if target not in inputs:
                    problems.append(f"{where}: 種類が {screens_check.INPUT} の項目でない")
                elif target in self.map_item:
                    problems.append(f"{where}: 同じ項目の行が 2 つある")
                elif value != NOT_SAVED and not PATH.fullmatch(value):
                    problems.append(f"{where}: 値がフィールドのパスの形でも {NOT_SAVED} でもない")
                self.map_item[target] = value
            else:
                if not PATH.fullmatch(value):
                    problems.append(f"{where}: 値がフィールドのパスの形でない")
                elif value not in self.paths[target]:
                    problems.append(f"{where}: システムが埋めると宣言したフィールドが入口の入力に無い")
                self.map_system.setdefault(target, set()).add(value)
        if problems:
            raise Unjudged("対応の CSV が決まりに反する:\n" + "\n".join(f"  {p}" for p in problems))

    # 画面 → 入口
    def features_of(self, row: dict[str, str]) -> tuple[list[str], str]:
        by_id = {r["画面ID"]: r for r in self.screens if r["画面ID"]}
        seen: set[str] = set()
        how = BY_FEATURE
        while True:
            named = [part.strip() for part in row["機能"].split(screens_check.SEPARATOR) if part.strip()]
            if named or row["種別"] not in screens_check.CHILD_KINDS:
                return named, how
            seen.add(row["画面ID"])
            parent = by_id.get(row["親画面"])
            if parent is None or parent["画面ID"] in seen:
                return [], how
            row, how = parent, BY_PARENT

    def screen_operation(self, row: dict[str, str]) -> tuple[str | None, str]:
        """(入口の id か None, 決まり方か引けない理由)。"""
        sid = row["画面ID"]
        if sid in self.map_screen:
            oid = self.map_screen[sid]
            return (oid, BY_MAP) if oid in self.ops else (None, MAP_OPERATION_NOT_IN_IR)
        named, how = self.features_of(row)
        if not named:
            return None, NO_FEATURE
        known = [fid for fid in named if fid in self.feature_op]
        if not known:
            return None, FEATURE_NOT_IN_IR
        with_input = sorted({self.feature_op[fid] for fid in known if self.paths[self.feature_op[fid]]})
        if not with_input:
            return None, NO_INPUT_OPERATION
        if len(with_input) > 1:
            return None, AMBIGUOUS_OPERATION
        return with_input[0], how

    # 照らす
    def run(self) -> list[str]:
        self.load()
        self.read_map()
        screen_ids = [row["画面ID"] for row in self.screens if row["画面ID"]]
        resolved = {row["画面ID"]: self.screen_operation(row) for row in self.screens if row["画面ID"]}
        inputs = [row for row in self.items if row["種類"] == screens_check.INPUT]
        per_screen: dict[str, dict[str, int]] = {}
        item_counts = {MATCHED: 0, MISMATCHED: 0, SAVED_NOT: 0}
        reasons = {reason: 0 for reason in ITEM_REASONS}
        pointers: dict[str, set[str]] = {}
        saving: set[str] = set()  # `保存しない` でない入力の項目を持つ画面
        unsure: set[str] = set()  # 名前で引けない項目のある入口（逆向きの「指されない」が確かでない）
        detail: list[str] = []
        for row in inputs:
            sid, number = row["画面ID"], row["番号"]
            counts = per_screen.setdefault(sid, {MATCHED: 0, MISMATCHED: 0, SAVED_NOT: 0, UNRESOLVED: 0})
            mapped = self.map_item.get(number)

            def unresolved(reason: str) -> None:
                counts[UNRESOLVED] += 1
                reasons[reason] += 1
                detail.append(f"{UNRESOLVED}: {sid} {number}（{reason}）")

            if sid not in resolved:
                unresolved(SCREEN_NOT_IN_TABLE)
                continue
            if mapped == NOT_SAVED:
                counts[SAVED_NOT] += 1
                item_counts[SAVED_NOT] += 1
                continue
            saving.add(sid)
            oid, _ = resolved[sid]
            if oid is None:
                unresolved(SCREEN_UNRESOLVED)
                continue
            paths = self.paths[oid]
            if mapped is None:
                hits = sorted({p for p in paths if p == row["項目名"] or last_name(p) == row["項目名"]})
                hits = [h for h in hits if not any(o != h and covers(o, h) for o in hits)]  # `m` と `m[]` は同じ入力——上のパスだけ
                if not hits:
                    unresolved(NO_FIELD)
                    unsure.add(oid)
                    continue
                if len(hits) > 1:
                    unresolved(MANY_FIELDS)
                    unsure.add(oid)
                    continue
                mapped = hits[0]
            if mapped in paths:
                counts[MATCHED] += 1
                item_counts[MATCHED] += 1
                pointers.setdefault(oid, set()).add(mapped)
            else:
                counts[MISMATCHED] += 1
                item_counts[MISMATCHED] += 1
                detail.append(f"{MISMATCHED}: {sid} {number} → {oid} {mapped}")

        # 逆向き: `保存しない` でない入力の項目を持つ画面から決まった入口
        checked = sorted({resolved[sid][0] for sid in saving if resolved[sid][0] is not None})
        reverse = {UNPOINTED: 0, UNPOINTED_UNSURE: 0, SYSTEM_FILLED: 0, PATH_VARIABLE: 0}
        leaves_total = 0
        for oid in checked:
            variables = path_variables(self.ops[oid])
            system = self.map_system.get(oid, set())
            for leaf in sorted(p for p, is_leaf in self.paths[oid].items() if is_leaf):
                leaves_total += 1
                if leaf in variables:
                    reverse[PATH_VARIABLE] += 1
                elif any(covers(p, leaf) for p in pointers.get(oid, ())):
                    continue
                elif any(covers(p, leaf) for p in system):
                    reverse[SYSTEM_FILLED] += 1
                elif oid in unsure:
                    reverse[UNPOINTED_UNSURE] += 1
                    detail.append(f"{UNPOINTED_UNSURE}: {oid} {leaf}")
                else:
                    reverse[UNPOINTED] += 1
                    detail.append(f"{UNPOINTED}: {oid} {leaf}")
        unchecked = sum(1 for oid in self.ops if self.paths[oid] and oid not in checked)

        lines = [f"画面の表: 画面 {len(screen_ids)}・入力の項目 {len(inputs)}（種類が {screens_check.INPUT} の行）",
                 f"中間表現: 入口 {len(self.ops)}（入力を持つもの {sum(1 for oid in self.ops if self.paths[oid])}）"
                 + (f"・形の崩れた機能・入口を飛ばした {self.skipped}" if self.skipped else ""),
                 f"対応: {'対応の CSV あり' if self.map_path else '対応の CSV なし（画面は機能の列、項目は名前の一致で引く）'}",
                 "", "画面ごと（名前は出さない。番号は画面の表の行の順）:"]
        order = {sid: at for at, sid in enumerate(screen_ids, start=1)}
        # `種別` のセルは決まった値のときだけ出す（表の決まりを見ないので、名前や業務の言葉が入っていても既定の出力に持ち出さない）
        kinds = {row["画面ID"]: (row["種別"] if row["種別"] in screens_check.SCREEN_KINDS else KIND_OUTSIDE) for row in self.screens if row["画面ID"]}
        for sid in sorted(per_screen, key=lambda s: (order.get(s, len(order) + 1), s)):
            counts = per_screen[sid]
            total = sum(counts.values())
            label = f"画面 {order[sid]}（{kinds[sid]}）" if sid in order else "画面の表に無い画面"
            if sid in resolved:
                oid, how = resolved[sid]
                operation = f"入口: 決まった（{how}）" if oid is not None else f"入口: {UNRESOLVED}（{how}）"
            else:
                operation = f"入口: {UNRESOLVED}（{SCREEN_NOT_IN_TABLE}）"
            lines.append(f"  {label}: 入力 {total} — {operation} — "
                         + "・".join(f"{name} {counts[name]}" for name in (MATCHED, MISMATCHED, SAVED_NOT, UNRESOLVED)))
        if not per_screen:
            lines.append("  （入力の項目を持つ画面が無い）")

        screen_how = [how for oid, how in resolved.values() if oid is not None]
        screen_why = [how for oid, how in resolved.values() if oid is None]
        lines += ["", "集計:",
                  f"  画面の入口: 決まった {len(screen_how)}（"
                  + "・".join(f"{how} {screen_how.count(how)}" for how in (BY_MAP, BY_FEATURE, BY_PARENT)) + "）"
                  + f"・{UNRESOLVED} {len(screen_why)}（"
                  + "・".join(f"{why} {screen_why.count(why)}" for why in SCREEN_REASONS) + "）",
                  f"  入力の項目（順向き）: {MATCHED} {item_counts[MATCHED]}・{MISMATCHED} {item_counts[MISMATCHED]}（パスが入口の入力に無い）"
                  + f"・{SAVED_NOT} {item_counts[SAVED_NOT]}・{UNRESOLVED} {sum(reasons.values())}（"
                  + "・".join(f"{why} {reasons[why]}" for why in ITEM_REASONS) + "）",
                  f"  入口の入力（逆向き）: 照らした入口 {len(checked)}・葉 {leaves_total} — "
                  + "・".join(f"{name} {reverse[name]}" for name in (UNPOINTED, UNPOINTED_UNSURE, SYSTEM_FILLED, PATH_VARIABLE))
                  + f"・照らさなかった入力のある入口 {unchecked}"]
        self.detail = sorted(detail) + [f"入口が{UNRESOLVED}画面: {sid}（{how}）" for sid, (oid, how) in resolved.items() if oid is None]
        return lines


def main(argv: list[str]) -> int:
    args = list(argv)
    named = upto = map_path = None
    detail = False
    try:
        for flag in ("--spec-loop", "--map"):
            while flag in args:
                at = args.index(flag)
                if at + 1 >= len(args) or (named if flag == "--spec-loop" else map_path) is not None:
                    raise ValueError(f"{flag} には値を 1 つ渡す")
                if flag == "--spec-loop":
                    named = args[at + 1]
                else:
                    map_path = Path(args[at + 1])
                del args[at:at + 2]
        while "--upto" in args:
            at = args.index("--upto")
            if at + 1 >= len(args) or upto is not None or not re.fullmatch(r"[1-9][0-9]*", args[at + 1]):
                raise ValueError("--upto には 1 以上の整数を 1 つ渡す")
            upto = int(args[at + 1])
            del args[at:at + 2]
        if "--detail" in args:
            if args.count("--detail") > 1:
                raise ValueError("--detail は 1 度だけ渡す")
            detail = True
            args.remove("--detail")
        if len(args) != 1 or args[0].startswith("-"):
            raise ValueError(__doc__.splitlines()[2] if __doc__ else
                             f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）")
    except ValueError as e:
        print(e, file=sys.stderr)
        return EXIT_UNJUDGED
    docs = Path(args[0])
    if not docs.is_dir():
        print(f"{docs}: ディレクトリが無い——判定していない", file=sys.stderr)
        return EXIT_UNJUDGED
    try:
        spec_loop = screens_check.find_spec_loop(named, docs)
        shown = screens_check.check_version(spec_loop)
        survey = Survey(spec_loop, docs, upto, map_path)
    except screens_check.Stop as e:
        print(f"止めた: {e}", file=sys.stderr)
        return EXIT_STOPPED
    print(f"spec-loop {shown} の重ね方で読む（調べる道具。関門ではない——件数に依らず 0）")
    try:
        lines = survey.run()
    except Nothing as e:
        print(f"{e}", file=sys.stderr)
        return EXIT_NOTHING
    except Unjudged as e:
        print(f"{e}\n——判定していない", file=sys.stderr)
        return EXIT_UNJUDGED
    print("\n".join(lines))
    if detail:
        print("\n詳細（画面ID・項目の番号・入口の id・パスを出す。案件の中身を含みうるので、公開の場に貼らない）:")
        print("\n".join(f"  {line}" for line in survey.detail) if survey.detail else "  （無い）")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 や 3 にしない
        print(f"想定外の例外で判定していない: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(EXIT_UNJUDGED)
