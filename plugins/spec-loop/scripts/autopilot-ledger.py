#!/usr/bin/env python3
r"""spec-loop の autopilot（#789）の台帳を、ファイルに持って読み書きする（#848）。

    python3 <spec-loop の根>/scripts/autopilot-ledger.py init <版> [--phase spec-review] [--cycle 1] [--stage planner]
    python3 <…>/autopilot-ledger.py set      <版> 鍵=値 [鍵=値 …]
    python3 <…>/autopilot-ledger.py lines    <版> [項目=値 …] --source 出所
    python3 <…>/autopilot-ledger.py show     <版>
    python3 <…>/autopilot-ledger.py status   <版>
    python3 <…>/autopilot-ledger.py progress <版>
    python3 <…>/autopilot-ledger.py path     <版>

`<版>` は autopilot で回している版の番号（`docs/v<n>/` の `n`。正の整数で、先頭に 0 を付けない）。
**いつ書き、どう再開するか（入口のスキル）と、外側のループの止め方は、このスクリプトの外で決める**（入口は #849・ループは #850）。
ここにあるのは台帳の形と、このスクリプトが守るものである。

## なぜ在るのか（#789・#790）

#789 の試作では、手作りの台帳（state.json）で止まったことを `status` に書き、外側のループは `phase` を見ていた。
前進はファイルのハッシュで見ていたので、エージェントが「再確認したが止まったまま」と時刻と回数を書き換えるだけで「前進」と数えられ、
**約 15 時間・約 1,900 回 `claude -p` を空回りさせた**（#790）。周の途中の再開点（1 回目のレビューが済んだ・直しが済んだ・狭いパスの前に控えた本文）は
会話の中にしか無く、`claude -p` で起動し直すと失われた。この台帳はその 2 つを塞ぐ——**止まったかは `status` の 1 欄だけで表し、前進は進捗の欄
（`progress`）だけで比べる。**

## 台帳の場所

`<メインの作業ツリー>/.claude/plans/spec-autopilot-v<版>.json`。メインの作業ツリーの決め方は dev-loop の `ledger.py`（cruise の台帳）と同じで、
**worktree の中やサブディレクトリから走らせても同じファイルを指す**（worktree の `.claude/plans/` は畳むと一緒に消える）。
**`main_worktree`・`_git`・`exists` は `ledger.py` の写しである**——spec-loop だけを入れた利用者に dev-loop が在るとは限らず、プラグインをまたいで
相対パスで指せない。写しが元とずれないことは `scripts/test-autopilot-ledger.py`（リポジトリの根）が関数のソースを突き合わせて見る。

## 台帳の形

```json
{"format": 1, "version": 3,
 "phase": "spec-review", "cycle": 3, "stage": "round1", "commit": "",
 "status": "running", "reason": "", "next": "",
 "triage": "", "held": "",
 "updated": "<UTC>",
 "lines": {"values": {"<項目>": "<値>"}, "source": "<出所>", "updated": "<UTC>"}}
```

| 欄 | 中身 |
| --- | --- |
| `format` | int の 1 |
| `version` | 版の番号（ファイル名の `v<版>` と同じ値） |
| `phase` | `spec-review`・`feasibility`・`done` のどれか |
| `cycle` | 周の番号（1 以上の整数。spec-review の周。feasibility では回数に使ってよい） |
| `stage` | 周の中の段——`planner`・`round1`・`fix1`・`round2`・`narrow`・`judge`・`commit` か、空 |
| `commit` | 最後に台帳を進めたコミット（空か、16 進の 7〜40 桁） |
| `status` | **状態の欄はこれ 1 つ**——`running`・`stopped`・`done` |
| `reason` | 止まった理由（`stopped` のときだけ。要る） |
| `next` | 利用者に頼むこと（`stopped` のときだけ。要る） |
| `triage` | 周の途中の振り分けの表を指すパス（空か、メインの作業ツリーからの相対パス） |
| `held` | 狭いパスの前に控えた本文を指すパス（同上） |
| `updated` | 最後に書いた時刻（UTC）。**`progress` には出さない** |
| `lines` | 起動時に利用者が確かめた線（無くてもよい）。**項目と値の一覧は持たない**——中身は入口のスキル（#849）で決める |

**`status` の整合**（`set` でも、手で直した台帳でも）:

- `status` が `done` なのは `phase` が `done` のときだけ（逆も同じ）——「止まった・済んだ」を 2 つの欄に分けて書かない（#790 はここで食い違った）。
- `stopped` は `reason` と `next` を持つ（空白だけは空と読む）——止まった理由と利用者に頼むことの無い停止を書かない。
- `running` と `done` は `reason` と `next` を空にする——再開した台帳に古い理由が残らない。**消すのは呼ぶ側**（`set status=running reason= next=`）。

**`set` に渡せる鍵**: `phase` `cycle` `stage` `commit` `status` `reason` `next` `triage` `held`。`version`・`format`・`updated` は書けない。
**`lines` は置き換え**で、渡さなかった項目は消える（渡さずに呼べば値は空になる）。出所（`--source`）が要る。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 通った。**`status` では `running`（ループは起動してよい）** |
| 2 | 引数が違う（版の形・`鍵=値` の形・`init` の `--cycle` の形。桁が `int()` の上限を超える番号を含む） |
| 3 | 操作を拒んだ——**台帳は 1 バイトも変えていない**（在る台帳への `init`・決まった一覧に無い鍵や値・`cycle`・`commit`・`triage`・`held` の形・`status` の整合を崩す書き込み・`lines` の出所や項目の誤り）。**`status` では `stopped`（ループは起動しない）** |
| 4 | 判定できなかった（git の外・メインの作業ツリーを決められない・台帳が無い・JSON が読めない・形が違う・**中身が崩れている**・台帳を書けなかった）。**`status` でも「動いている」「止まった」「済んだ」とは答えていない** |
| 5 | `status` だけ: `done`（ループは起動しない） |

`status` は 1 行目に状態を出し、`stopped` なら理由と頼むことを続けて出す。**判定は `status` の欄だけで決める**——`phase`・`stage` は見ない。

### `progress` が出すもの

**外側のループが「1 回の起動で台帳が進んだか」を比べるための要約である**——1 行で `phase=<…> cycle=<…> stage=<…> commit=<…>`（空は `-`）。
**出すのは `PROGRESS_KEYS` の欄だけ**で、`updated`・`status`・`reason`・`next`・`triage`・`held`・`lines` は出さない——エージェントが「確かめたが変わらず」と
時刻や理由を書き直すだけの起動でも `set` は `updated` を書き換えるので、ファイルのまま比べると前進に見える（#790）。台帳は変えない。

## 何を守り、何を守らないか

守る:

- **台帳の場所は cwd に依らない**——メインの作業ツリーでも、worktree の中やそのサブディレクトリでも、同じ絶対パスを指す。
- **版の名前は正の整数だけ**（先頭の 0・符号・区切り・空白と、桁が `int()` の上限を超える値を 2 で拒む）——`.claude/plans/` の外に書かず、`3` と `03` を別の台帳にしない。
- **在る台帳を `init` で上書きしない。**
- **決まった一覧に無い鍵を `set` で拒む**——`version`・`updated` も書けない。
- **決まった一覧に無い `phase`・`stage`・`status` の値を拒む**——綴りを誤った値を書くと、読み手の判定から黙って外れる。
- **`cycle` は 1 以上の整数だけ**——真偽値・0・数でない値を拒む。
- **`commit` は空か 16 進の 7〜40 桁だけ。**
- **`triage`・`held` は空か、メインの作業ツリーからの相対パスだけ**（絶対パスと `..` を拒む）——scratchpad のようにセッションと一緒に消える場所を指さない。
- **`status` が `done` なのは `phase` が `done` のときだけ（逆も）**——止まった・済んだを 2 つの欄に分けて書かない（#790）。
- **`stopped` には `reason` と `next` が要る**——空白だけも拒む。
- **`running`・`done` では `reason` と `next` を空にする**——古い理由を残したまま動かない。
- **`lines` は出所の無い値を書かない**——`--source` が空・空白だけなら拒む。項目・値の空も拒む。
- **`lines` は置き換えで、渡さなかった項目は消える**——前の確認の値が、確かめ直した後に黙って残らない。
- **拒んだ操作では台帳を変えない**——全体を検査してから一時ファイルに書き、`os.replace` で置き換える。
- **`status`・`progress`・`show` は台帳を書き換えない**——入口が「`stopped` なら何もせず台帳も書き換えずに終える」（#790）を、読むだけで壊さない。
- **読めない台帳（無い・壊れた JSON・桁が `int()` の上限を超える整数・深すぎる入れ子）を `running` と読まない**——4 で止まり、例外（1）で終えない。
- **形の違う台帳（知らない欄・欄が足りない・型の違い・ファイル名と違う `version`・`format` が int の 1 でない）は 4**——真偽値の `cycle` も。
- **ファイルの上で中身の崩れた台帳（一覧に無い値・`status` の整合を崩す組み合わせ）は 4 で、「拒んだ」（3）とは言わない**——`status` が 3 と答えると
  崩れた台帳を「止まった」と読む。
- **`status` は `status` の欄だけで終了コードを決める**——`running` は 0、`stopped` は 3、`done` は 5。`phase` を見ない（#790 は `phase` を見て止まった台帳を見落とした）。
- **`progress` は `PROGRESS_KEYS` だけを出す**——`updated`・`status`・`reason`・`next`・`triage`・`held`・`lines` の書き換えでは変わらない。
- **`progress` は `phase`・`cycle`・`stage`・`commit` のどれかが変われば変わる**——段だけ・コミットだけ進んだ起動も前進と読める。
- **書けなかったときに、表に無い終了コードで終えない**——書けない・`.claude/plans` がファイル・UTF-8 で書けない文字（対になっていないサロゲート）なら 4。

守らない:

- **線（`lines`）の項目と値が正しいか**——一覧は入口のスキル（#849）で決める。ここは文字列の対と出所があることだけを見る。
- **`lines` の出所が本当に利用者か**——`--source` の文字列を残すだけで、確かめない。
- **段の遷移の順序と、`phase` と `stage` の組み合わせ**——やり直しで逆行が正当に起きる。段の名前は spec-review の周のもので、feasibility で何を書くかは入口が決める。
- **`stopped` の台帳への書き込み**——拒まない（利用者が再開するとき `status=running` に書く道を残す）。「`stopped` なら書き換えない」は入口の決まりである。
- **`triage`・`held` が指すファイルが在るか、`commit` が実在するか**——書いてある値を出すだけで、ファイルも git も見ない。
- **複数のプロセスからの同時書き込み**——`os.replace` なので半端なファイルは残らないが、後勝ちで片方の更新が消えうる。
- **`--separate-git-dir` の先が `.git` という名前のリポジトリ**——`ledger.py` と同じく、worktree の中からその親をメインの作業ツリーと読む。
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

PHASES = ("spec-review", "feasibility", "done")
STAGES = ("planner", "round1", "fix1", "round2", "narrow", "judge", "commit")
STATUSES = ("running", "stopped", "done")
# `set` に渡せる鍵
KEYS = ("phase", "cycle", "stage", "commit", "status", "reason", "next", "triage", "held")
TEXT_KEYS = ("phase", "stage", "commit", "status", "reason", "next", "triage", "held")
FIELDS = {"format", "version", "updated", *KEYS}
# 外側のループが前進を比べる欄（#790）。`updated`・`status`・`reason`・`next` などは入れない
PROGRESS_KEYS = ("phase", "cycle", "stage", "commit")
COMMIT_RE = re.compile(r"[0-9a-f]{7,40}")
VERSION_RE = re.compile(r"[1-9][0-9]*")
FORMAT = 1

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REJECTED = 3
EXIT_UNKNOWN = 4
# `status` だけの値。3 は EXIT_REJECTED と同じ値——`status` は台帳を変えないので拒む場面が無く、重ならない（`ledger.py` と同じ読み方）
EXIT_STOPPED = 3
EXIT_DONE = 5
STATUS_CODES = {"running": EXIT_OK, "stopped": EXIT_STOPPED, "done": EXIT_DONE}


class Refused(Exception):
    """操作を拒んだ（台帳は変えていない）。"""


class Unknown(Exception):
    """判定できなかった。"""


class Usage(Exception):
    """引数が違う。"""


# ここから dev-loop の `ledger.py` の写し（`scripts/test-autopilot-ledger.py` が突き合わせる）
def _git(cwd, *args):
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise Unknown(f"git を起動できなかった: {exc}") from exc
    return proc.stdout.strip() if proc.returncode == 0 else ""


def main_worktree(cwd=None):
    """メインの作業ツリーの絶対パス。**worktree の中からでも同じ値を返す。**

    **共通ディレクトリの親を無条件に使わない**——`--separate-git-dir` のリポジトリとサブモジュールでは、
    共通ディレクトリが作業ツリーの直下に無い（`git worktree list` の先頭も同じ誤りを返す）。
    """
    lines = _git(cwd, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir").splitlines()
    if len(lines) != 2:
        raise Unknown("git のリポジトリの中ではない（場所を決められない）")
    git_dir, common = Path(lines[0]), Path(lines[1])
    if _git(cwd, "--git-dir", str(common), "config", "--bool", "core.bare") == "true":
        # bare の worktree: 共通ディレクトリが `<dir>/.git` でも、その親は作業ツリーではない
        raise Unknown(f"bare リポジトリで、メインの作業ツリーが無い（共通ディレクトリ: {common}）")
    if git_dir == common:  # メインの作業ツリーにいる
        top = _git(cwd, "rev-parse", "--show-toplevel")
        if not top:
            raise Unknown("作業ツリーの外にいる（場所を決められない）")
        return Path(top)
    if common.name == ".git":
        return common.parent
    worktree = _git(cwd, "--git-dir", str(common), "config", "--get", "core.worktree")
    if worktree:  # サブモジュール: 共通ディレクトリの設定が作業ツリーを持つ
        return (common / worktree).resolve()
    raise Unknown(f"worktree の中から、メインの作業ツリーを決められない（共通ディレクトリ: {common}）")


def exists(path):
    """**`Path.exists()`／`is_file()` を使わない**——Python 3.13 以前は権限・名前の長さの誤りを例外で返し、
    3.14 は False を返す（権限の無いことを「無い」と言う）。無いときだけ False、他は判定できなかった。"""
    try:
        path.stat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise Unknown(f"台帳の在り処を確かめられない: {path}: {exc}") from exc
    return True
# 写しはここまで


def parse_version(text):
    if not VERSION_RE.fullmatch(text):
        raise Usage(f"版の番号が違う: {text!r}（正の整数。先頭に 0 を付けない）")
    try:
        return int(text)
    except ValueError as exc:  # 桁が `int()` の上限（既定 4300）を超える
        raise Usage(f"版の番号の桁が多すぎる（{len(text)} 桁）") from exc


def ledger_path(version, cwd=None):
    return main_worktree(cwd) / ".claude" / "plans" / f"spec-autopilot-v{version}.json"


def is_cycle(value):
    # bool は int の部分型なので、`true` を周の番号として通さないよう分けて見る
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def check_pointer(key, value):
    if not value:
        return
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("~") or ".." in path.parts:
        raise Refused(f"{key} はメインの作業ツリーからの相対パスだけ（絶対パス・`..` は不可）: {value!r}")


def check_lines(values, source):
    if not source.strip():
        raise Refused("線の出所が空（--source に、誰がいつ確かめたかを書く）")
    for key, value in values.items():
        if not key.strip() or not value.strip():
            raise Refused(f"線の項目か値が空: {key!r}={value!r}")


def validate(data):
    """台帳全体の整合。**書き込む前に必ず通す。**"""
    if data["phase"] not in PHASES:
        raise Refused(f"決まった一覧に無い phase {data['phase']!r}（{', '.join(PHASES)}）")
    if data["stage"] and data["stage"] not in STAGES:
        raise Refused(f"決まった一覧に無い stage {data['stage']!r}（{', '.join(STAGES)} か空）")
    if data["status"] not in STATUSES:
        raise Refused(f"決まった一覧に無い status {data['status']!r}（{', '.join(STATUSES)}）")
    if not is_cycle(data["cycle"]):
        raise Refused(f"cycle は 1 以上の整数だけ: {data['cycle']!r}")
    if data["commit"] and not COMMIT_RE.fullmatch(data["commit"]):
        raise Refused(f"commit は空か 16 進の 7〜40 桁だけ: {data['commit']!r}")
    for key in ("triage", "held"):
        check_pointer(key, data[key])
    if (data["status"] == "done") != (data["phase"] == "done"):
        raise Refused(f"status が done なのは phase が done のときだけ（逆も）: status={data['status']} phase={data['phase']}")
    if data["status"] == "stopped":
        if not data["reason"].strip() or not data["next"].strip():
            raise Refused("stopped には reason（止まった理由）と next（利用者に頼むこと）が要る")
    elif data["reason"] or data["next"]:
        raise Refused(f"{data['status']} では reason と next を空にする（set … reason= next=）")
    if "lines" in data:
        check_lines(data["lines"]["values"], data["lines"]["source"])


def load(path, version):
    if not exists(path):
        raise Unknown(f"台帳が無い: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    # `ValueError` は壊れた JSON（`JSONDecodeError`）と `int()` の上限を超える桁の整数、`RecursionError` は深すぎる入れ子（Python 3.12）
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Unknown(f"台帳を読めない: {path}: {exc}") from exc
    # `format` は int の 1 だけ——`true == 1`・`1.0 == 1` が通るので型も見る
    if (not isinstance(data, dict) or not FIELDS <= set(data) <= FIELDS | {"lines"}
            or type(data["format"]) is not int or data["format"] != FORMAT
            or type(data["version"]) is not int or data["version"] != version
            or not isinstance(data["cycle"], int) or isinstance(data["cycle"], bool)
            or not all(isinstance(data[k], str) for k in (*TEXT_KEYS, "updated"))):
        raise Unknown(f"台帳の形が違う: {path}")
    if "lines" in data:
        lines = data["lines"]
        if (not isinstance(lines, dict) or set(lines) != {"values", "source", "updated"}
                or not isinstance(lines["values"], dict)
                or not all(isinstance(k, str) and isinstance(v, str) for k, v in lines["values"].items())
                or not all(isinstance(lines[k], str) for k in ("source", "updated"))):
            raise Unknown(f"台帳の線の形が違う: {path}: {lines!r}")
    # **ファイルの上で既に崩れている台帳は、拒んだ（3）ではなく判定できなかった（4）**——
    # `status` の 3 は「止まった」なので、3 と答えると崩れた台帳を止まったと読む
    try:
        validate(data)
    except Refused as exc:
        raise Unknown(f"台帳の中身が崩れている: {path}: {exc}") from exc
    return data


def save(path, data):
    validate(data)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    except OSError as exc:  # 書けない・名前が長すぎる・`.claude/plans` がファイル
        raise Unknown(f"台帳を書けなかった（台帳は変えていない）: {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except (OSError, UnicodeError) as exc:  # UnicodeError: 対になっていないサロゲート（UTF-8 で書けない引数）
        Path(tmp).unlink(missing_ok=True)
        raise Unknown(f"台帳を書けなかった（台帳は変えていない）: {path}: {exc}") from exc
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_init(path, version, phase, cycle, stage):
    if exists(path):
        raise Refused(f"台帳は既に在る: {path}（上書きしない）")
    data = {"format": FORMAT, "version": version, "phase": phase, "cycle": cycle, "stage": stage, "commit": "",
            "status": "done" if phase == "done" else "running", "reason": "", "next": "",
            "triage": "", "held": "", "updated": now()}
    save(path, data)
    print(f"作った: {path}")


def cmd_set(path, version, pairs):
    data = load(path, version)
    for pair in pairs:
        if "=" not in pair:
            raise Usage(f"鍵=値 の形でない: {pair!r}")
        key, value = pair.split("=", 1)
        if key not in KEYS:
            raise Refused(f"決まった一覧に無い鍵 {key!r}（{', '.join(KEYS)}）")
        if key == "cycle":
            if not re.fullmatch(r"[1-9][0-9]*", value):
                raise Refused(f"cycle は 1 以上の整数だけ: {value!r}")
            try:
                data[key] = int(value)
            except ValueError as exc:  # 桁が `int()` の上限を超える
                raise Refused(f"cycle の桁が多すぎる（{len(value)} 桁）") from exc
        else:
            data[key] = value
    data["updated"] = now()
    save(path, data)


def cmd_lines(path, version, pairs, source):
    data = load(path, version)
    values = {}
    for pair in pairs:
        if "=" not in pair:
            raise Usage(f"項目=値 の形でない: {pair!r}")
        key, value = pair.split("=", 1)
        if key in values:
            raise Refused(f"同じ項目を 2 度渡した: {key!r}")
        values[key] = value
    data["lines"] = {"values": values, "source": source, "updated": now()}
    data["updated"] = now()
    save(path, data)


def cmd_show(path, version):
    data = load(path, version)
    print(f"台帳: {path}")
    print(f"状態: {data['status']}")
    if data["status"] == "stopped":
        print(f"  止まった理由: {data['reason']}")
        print(f"  利用者に頼むこと: {data['next']}")
    print(f"進捗: phase={data['phase']} 周={data['cycle']} 段={data['stage'] or '-'} commit={data['commit'] or '-'}")
    print(f"振り分けの表: {data['triage'] or '-'}")
    print(f"控えた本文: {data['held'] or '-'}")
    if "lines" in data:
        values = data["lines"]["values"]
        print("確かめた線: " + ("、".join(f"{k} = {v}" for k, v in values.items()) or "（項目なし）")
              + f"（出所: {data['lines']['source']}）")
    else:
        print("確かめた線: なし")
    print(f"更新: {data['updated']}")


def cmd_status(path, version):
    data = load(path, version)
    status = data["status"]
    if status == "stopped":
        print(f"stopped: 止まった理由: {data['reason']} / 利用者に頼むこと: {data['next']}")
    else:
        print(f"{status}: phase={data['phase']} 周={data['cycle']} 段={data['stage'] or '-'}")
    return STATUS_CODES[status]


def progress_line(data):
    return " ".join(f"{k}={data[k] if data[k] != '' else '-'}" for k in PROGRESS_KEYS)


def cmd_progress(path, version):
    print(progress_line(load(path, version)))


def build_parser():
    p = argparse.ArgumentParser(description="spec-loop の autopilot の台帳")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("show", "status", "progress", "path"):
        sub.add_parser(name).add_argument("version")
    i = sub.add_parser("init")
    i.add_argument("version")
    i.add_argument("--phase", default="spec-review")
    i.add_argument("--cycle", default="1")
    i.add_argument("--stage", default="planner")
    s = sub.add_parser("set")
    s.add_argument("version")
    s.add_argument("pairs", nargs="+")
    ln = sub.add_parser("lines")
    ln.add_argument("version")
    ln.add_argument("pairs", nargs="*")
    ln.add_argument("--source", required=True)
    return p


def main(argv=None, cwd=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    try:
        version = parse_version(args.version)
        path = ledger_path(version, cwd)
        if args.cmd == "init":
            if not re.fullmatch(r"[1-9][0-9]*", args.cycle):
                raise Usage(f"--cycle は 1 以上の整数だけ: {args.cycle!r}")
            try:
                cycle = int(args.cycle)
            except ValueError as exc:  # 桁が `int()` の上限を超える
                raise Usage(f"--cycle の桁が多すぎる（{len(args.cycle)} 桁）") from exc
            cmd_init(path, version, args.phase, cycle, args.stage)
        elif args.cmd == "set":
            cmd_set(path, version, args.pairs)
        elif args.cmd == "lines":
            cmd_lines(path, version, args.pairs, args.source)
        elif args.cmd == "show":
            cmd_show(path, version)
        elif args.cmd == "status":
            return cmd_status(path, version)
        elif args.cmd == "progress":
            cmd_progress(path, version)
        elif args.cmd == "path":
            print(path)
    except Usage as exc:
        print(f"引数が違う: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except Refused as exc:
        print(f"拒んだ（台帳は変えていない）: {exc}", file=sys.stderr)
        return EXIT_REJECTED
    except Unknown as exc:
        print(f"判定できなかった: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
