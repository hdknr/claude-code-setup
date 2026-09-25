#!/usr/bin/env python3
"""ローカルのトランスクリプトからトークン使用量を集計する。

**CI からは呼ばない**（`export-diagrams.py` と同じ扱い）——入力が
`~/.claude/projects/` にあり、**リポジトリの外**で、利用者ごとに違うため。
手で実行する:

    python3 scripts/token-metrics.py                 # 週次の推移
    python3 scripts/token-metrics.py --per-cycle     # dev-loop の周ごと
    python3 scripts/token-metrics.py --per-issue     # 周を Issue で束ねる（割った周を 1 周に）
    python3 scripts/token-metrics.py --elapsed       # 周の経過時間を区分と関門に分ける（#169）
    python3 scripts/token-metrics.py --since 2026-09-01 --repo taihei-epm-server

なぜ必要か（#95）: #92 で「1 周の重さ（ターン数 × 文脈）を減らす」規範を入れたが、
**効果を測る手段がリポジトリに無かった**。#92 の計測は手作業で、**再現手順が散文でしか
残っていない**。受入基準のうち「トークンが実際に減ること」は**未証明**として人間レビューに
回したが、**データが溜まった時点で測れる状態を作っておかないと、未証明が回収されない**。

**このスクリプトが出すのは今の値**で、
[設計 §8.3](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#session-split)
の表を書き換えるものではない（あちらは 2026-09-15 時点の記録）。
**ただし、突き合わせた結果あちらの誤りが分かった**——下の「§8.3 の表は…」を見ること。

## 数え方

**加重トークン ＝ `in + cacheW×1.25 + cacheR×0.1 + out×5`。**
#92 が使った換算をそのまま置いている。**請求と突き合わせていない**ので、
**保証されるのは「#92 と同じ式である」ことだけ**で、**それが課金と一致するかは別問題**。

**この式は 3 箇所にある。** 数えると:

1. **実装** — このファイルの `WEIGHTS`
2. **この段落** — 読む人のための再掲
3. **設計 §8.3** — #92 時点の記録。「#92 の数字がどう作られたか」なので消せない
   （消すと表の意味が読めなくなる）

ほかに `test-token-metrics.py` の検算コメントにも係数が出るが、あれは
**係数を変えればテストが落ちる**ので、黙って古くなる類ではない。

**比率が変わったら 1〜3 を全部直すこと。**「1 箇所だけに置いた」と書きたくなるが、
**実際には 3 箇所あるので、そう書けば嘘になる**（#94 で同じ形を 6 回やり、
**この docstring でも一度「2 箇所」と数え違えた**——レビューが 3 箇所目を見つけた）。

## 落とし穴（どれも実測で確かめた）

| 落とし穴 | どうしているか |
| --- | --- |
| **1 応答が複数行に書かれる** | 各行が**同じ `message.id` と同じ `usage`** を再掲する。**行ごとに足すと 7 割ほど膨らむ**（率は設計 §8.3 の訂正を見ること）。`message.id` ごとに畳んで**最大を採る**（`output_tokens` が育っていく形があるため） |
| **同じ応答が複数ファイルに入る** | セッションを fork / resume すると**履歴がコピーされる**。`message.id` は API が採番するので**ファイルを跨いでも同一の応答**である。ファイル単位で畳むと数 % 過大になるので、**走査全体で畳む**。**消費量は最大、帰属は最も古いレコード**（コピーではなく最初に消費した側に計上する。**走査順では決められない**——セッション id は UUID で時刻を持たない） |
| **サブエージェントの取りこぼし** | 使用量は `<project>/<session>/subagents/*.jsonl` に分かれて入る。`*/*.jsonl` だけ見ると落ちる（割合は設計 §8.3 を見ること——**ここに数字を書かない**） |
| **`usage.iterations` の二重計上** | 各要素が**トップレベルと同じ数字を再掲**している。**足すと倍になる**ので、既定ではトップレベルだけ読む |
| **その逆——`iterations` にしか実数が無い** | **トップレベルが 0 のレコードが実在する**（全件走査で 2 件。**同じリクエストの重複**で、cache read だけで約 100 万トークン）。**トップレベルだけ読むと丸ごと落ちる**ので、**キーごとに大きいほうを採る**（`effective_usage`） |
| **`<synthetic>` モデル** | 実測で**全件 0 トークン**。足しても数は変わらないが**件数の分母が狂う**ので除外する |
| **レコードはあるのに加重が 0** | 上の 0 トークンのレコードだけが絞り込みに残ると起きる。**割り算にガードを置く**（置き忘れて落ちた） |
| **`grep dev-loop` で周を判定する** | **使えない**——`MEMORY.md` の記載に当たって全件ヒットする。`Skill` の `skill`、`Agent` の `subagent_type`、**スラッシュ起動の `<command-name>`** の 3 つを見る |
| **スラッシュ起動は `Skill` の tool_use として残らない** | **これがいちばん多い起動形**。`Skill` と `subagent_type` の 2 つだけを見ていた時期、**dev-loop の周 120 本のうち 60 本が丸ごと欠けていた**（加重 608M——**当時数えていた 1,328M の 46%**）——`dev-loop-verifier` を呼ぶ**手順 5 に着くまで周が存在しなかった**（#108）。**本文で判定してはいけない**のは上の行のとおりで、`<command-name>` タグを持つ `role=user` のテキストだけを見る |
| **1 周が複数セッションに割れる** | `/clear` で割ると**セッション id が変わる**。`--per-cycle` は `(repo, session)` で数えるので、**割った周は per-session の会計で必ず「軽くなった」と出る**（会計上の分割で、節約ではない）。**割った周は `--per-issue` で見る**——`<command-args>` の Issue 番号で束ねる。**番号が取れない周は束ねず、件数だけ別に出す** |
| **親の起点をサブエージェントのリクエストに課金する** | 委譲先は**自分の起点**を持ち、**親の起点を払わない**。含めると**1.65 倍の過大**になる——実測で中央値 29.3% 対 17.8%（サブエージェントが加重の 24%）。**`floor_share` には親の req だけを渡す**。**「周の 30%」として #101 / #102 / #103 の根拠にした数字はこの誤りを含む**（#108 で訂正） |
| **読めないファイル・壊れた行** | どちらも件数を**報告に出す**。黙って 0 にしない。**読めないファイルは走査を止めない**（1 つで全体が落ちていた）。なお**行ごとに読むと壊れた行は出なくなった**——以前 46 行あったのは `splitlines()` が**JSON 文字列の中の U+2028 などで切っていた**ためで、**その 7 行は本物の `usage` を含んでいた**（つまり取りこぼしていた） |
| **`--repo` の部分一致が広すぎる** | `--list-repos` で**実際に何にマッチするかを先に見る**——短い名前は**思っているより多くに当たる**。**値が `-` で始まるなら `--repo=...` と書く**（そうしないと argparse が引数として解釈する） |
| **worktree が別プロジェクトとして記録される** | `<repo>--claude-worktrees-<name>` という別ディレクトリになる。**同じリポジトリの作業なのに別々に数えられる**。寄せたいなら `--merge-worktrees` |
| **日と週の境目が UTC** | タイムスタンプは全件 `…Z`。`--since` と ISO 週の境界は **UTC で切られる**ので、JST の朝 9 時前の作業は**前日**に入る。週単位の before/after を見るときに効く |
| **1 つの会話が複数の「周」に見える** | 周はセッション id で数えるが、**worktree を移ると別セッションになる**。`/dev-loop` を 1 本の会話で複数 Issue に回すと、**`--per-cycle` の行数が実際の周より多く出る**。`--merge-worktrees` はリポジトリ名を寄せるだけで、**セッションは寄せない**（寄せると別々の周まで 1 つになる）。**「1 周あたり req」は上限ではなく下限として読むこと** |

**`usage` の在処を型で絞らない。** 実測では `assistant` にしか無いが、
`message.usage` の有無で拾えば、将来ほかの型に付いても落ちない。

**具体的な件数をここに書かない。** データは増えるので、**書いた瞬間から古くなる**
（#94 で同じ形を繰り返した）。**数えたければ走らせること**——落とし穴の形は変わらないが、
**母数は毎回変わる**。上の表で数字を出しているのは「2 件」だけで、これは
**性質が変わる境目**（0 件なら規則が要らない）なので残してある。

## 設計 §8.3 の表は過大である

**このスクリプトを作る過程で、#92 の数字の誤りが分かった。**
**どの数字がどれだけ影響を受けるかは
[§8.3 の訂正](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#miscounted-rows)
を正とする**（ここに再掲しない）。

**対照を取って確かめた。** 同じ母集団に対して**畳むかどうかだけを変えて**比べると、
**畳まない側が §8.3 の表とほぼ一致する**。つまり **#92 の集計も 1 応答を複数行として
数えていた**。期間・リポジトリの絞り方・式の違いでは、**セッション数が一致したまま
行数に比例する量だけがずれる**という形を説明できない。

**§8.3 の表は書き換えない**（2026-09-15 時点の記録なので）。訂正はあちらに置く。

**言えることと言えないことを分ける。** 「1 周が重い」という #92 の結論は**比率の話**で、
比率はほとんど動かないのでそのまま成り立つ。誤っていたのは**絶対値のほう**である。

標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import statistics
import pathlib
import re
import sys

# 加重の式。**実装はここだけだが、式そのものは 3 箇所にある**
# （docstring の「数え方」に一覧がある）。**変えるなら全部。**
WEIGHTS = {
    "input_tokens": 1.0,
    "cache_creation_input_tokens": 1.25,
    "cache_read_input_tokens": 0.1,
    "output_tokens": 5.0,
}

# 実消費ではないモデル。実測で全件 0 トークンだった。
SYNTHETIC_MODELS = {"<synthetic>"}

# `/dev-loop` を回した周の判定に使う印。**名前の部分一致で見る**
# （プラグイン経由だと `dev-loop:dev-loop`、素のスキルだと `dev-loop`）。
DEV_LOOP_SKILL = "dev-loop"
DEV_LOOP_AGENT = "dev-loop-verifier"

AGENT_TOOLS = ("Agent", "Task")

# **スラッシュ起動の形。** スキルは `Skill` の tool_use ではなく
# **スラッシュコマンドとして呼ばれることのほうが多い**——実測で、
# dev-loop を呼んだ 120 周のうち **`Skill` の tool_use は使われていない周が半分**あり、
# それらは `dev-loop-verifier` を呼ぶ**手順 5 に着くまで存在しなかった**（#108）。
# **`<command-name>` タグを持つ user テキストだけを見る**——スキル本文も
# `role=user` として載るので、本文を見ると「起動された」と誤判定する（#101 と同じ落とし穴）。
SLASH_NAME = re.compile(r"<command-name>\s*/?([^<\s]+)")
SLASH_ARGS = re.compile(r"<command-args>([^<]*)</command-args>")


# worktree はプロジェクトディレクトリとして**別扱いで記録される**
# （`<repo>--claude-worktrees-<name>`）。同じリポジトリの作業なのに別々に数えられる。
WORKTREE_MARKER = "--claude-worktrees-"
# worktree のディレクトリ名から Issue 番号を拾う**補助の**経路。
# 起動形が取れないときだけ使う（`--claude-worktrees-issue-10856-costcustomer-sheet`）。
WORKTREE_ISSUE = re.compile(re.escape(WORKTREE_MARKER) + r"issue-(\d+)")



class Record:
    """1 レコード分の集計値。"""

    __slots__ = ("day", "repo", "session", "is_sub", "model", "weighted", "cache_read",
                 "timestamp", "context", "issue")

    def __init__(self, day, repo, session, is_sub, model, weighted, cache_read,
                 timestamp="", context=0):
        self.timestamp = timestamp
        self.day = day
        self.repo = repo
        self.session = session
        self.is_sub = is_sub
        self.model = model
        self.weighted = weighted
        self.cache_read = cache_read
        # **そのリクエストが抱えていた文脈**。cache read だけでは足りない——
        # **1 回目は cache write として課金される**ので、起点を cache read だけで
        # 取ると**周の最初のリクエストで 0 になる**。
        self.context = context
        # **どの Issue の周か。** `scan` が**走査を終えてから**入れる
        # ——起動形は先頭にあるとはいえ、fork / resume で**順序は保証できない**。
        # 取れなければ `None` のまま（**近い値で代用しない**）。
        self.issue = None


def _from_iterations(usage: dict) -> dict:
    """`iterations` から 1 件分の数字を取り出す（要素が無ければ空）。

    **足さない。** `iterations` の各要素は**同じ応答のスナップショット**で、
    トップレベルと同じ数字を再掲している。足すと倍になる——
    実測では要素が 2 つ以上のものは 0 件だが、**形として再掲だと分かっているものを
    足す実装にしておくと、要素が増えた瞬間に静かに倍になる**（#95 のレビュー）。
    だから**キーごとに最大を採る**（育っていく形なら最後が最大になる）。
    """
    its = usage.get("iterations")
    if not isinstance(its, list) or not its:
        return {}
    out = {}
    for key in WEIGHTS:
        best = 0
        for item in its:
            if not isinstance(item, dict):
                continue
            value = item.get(key) or 0
            if isinstance(value, (int, float)) and value > best:
                best = value
        out[key] = best
    return out


def effective_usage(usage: dict) -> dict:
    """実際に消費された数字を返す。

    **既定はトップレベル。`iterations` は足さない**——各要素がトップレベルと同じ数字を
    再掲しているので、足すと二重計上になる。

    **ただし「トップレベルが 0 で `iterations` には実数がある」レコードが実在する。**
    実測で 2 件（2026-08-17）あり、cache read だけで約 100 万トークンあった
    （**2 件は同じリクエストの重複**で、別々の消費ではない）。
    **トップレベルだけ読むと丸ごと取りこぼす**——#95 のレビューが見つけた。
    **二重計上を避ける規則が、逆向きに取りこぼしを作っていた**ことになる。

    **キーごとに大きいほうを採る。** 最初は「トップレベルが*全部* 0 のときだけ
    `iterations` を見る」にしていたが、**1 フィールドでも実数があると残りを落とした**
    （`output` だけ埋まっていて `cache_read` が `iterations` にしか無い形）。
    現データに該当は無いが、**「全部 0」という条件は形の保証ではない**。
    """
    top = {}
    for key in WEIGHTS:
        value = usage.get(key) or 0
        top[key] = value if isinstance(value, (int, float)) else 0
    nested = _from_iterations(usage)
    if not nested:
        return top
    return {key: max(top.get(key, 0), nested.get(key, 0)) for key in WEIGHTS}


def context_tokens(usage: dict) -> int:
    """そのリクエストが抱えていた文脈（cache read + cache write）を返す。

    **`weighted_tokens` と別に置く。** あちらは**課金の重み**を掛けた値で、
    こちらは**素の大きさ**である。同じ数から作れるが、**混ぜると
    「重み付き文脈」という無意味な量が生まれる**（#103 の実装で一度やった）。

    **`input_tokens` は足さない。** 起点として見たいのは
    **キャッシュに載る繰り返し部分**で、そのリクエスト固有の入力ではない。
    """
    effective = effective_usage(usage)
    return int((effective.get("cache_read_input_tokens") or 0)
               + (effective.get("cache_creation_input_tokens") or 0))


def weighted_tokens(usage: dict) -> tuple[float, int]:
    """(加重, cache read) を返す。"""
    effective = effective_usage(usage)
    weighted = 0.0
    for key, factor in WEIGHTS.items():
        weighted += (effective.get(key) or 0) * factor
    return weighted, int(effective.get("cache_read_input_tokens") or 0)


def session_of(path: pathlib.Path, projects_root: pathlib.Path,
                merge_worktrees: bool = False) -> tuple[str, str, bool]:
    """(リポジトリ名, セッション id, サブエージェントか) を返す。

    レイアウトは 2 通り:
      <projects>/<repo>/<session>.jsonl
      <projects>/<repo>/<session>/subagents/<name>.jsonl
    """
    rel = path.relative_to(projects_root)
    parts = rel.parts
    repo = parts[0] if parts else "?"
    if merge_worktrees and WORKTREE_MARKER in repo:
        repo = repo.split(WORKTREE_MARKER, 1)[0]
    is_sub = "subagents" in parts
    if is_sub:
        session = parts[1] if len(parts) > 2 else path.stem
    else:
        session = path.stem
    return repo, session, is_sub


def tool_uses(message: dict):
    """message の content から tool_use ブロックを取り出す。"""
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            yield block


def user_texts(message: dict):
    """user メッセージのテキストを 1 つずつ返す。

    **`role` を見る。** アシスタントの応答にも `text` ブロックがあり、
    そちらに起動形の話が書かれていることがある（この会話が実際にそうだった）。
    """
    if message.get("role") != "user":
        return
    content = message.get("content")
    if isinstance(content, str):
        yield content
        return
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            yield block.get("text") or ""


def slash_command(text: str) -> tuple[str, str] | None:
    """スラッシュ起動なら `(コマンド名, 引数)`、そうでなければ `None`。

    **`<command-name>` タグが無いテキストは見ない。** スキル本文も `role=user` で
    載るので、本文に `dev-loop` があるだけで「起動された」と数えると
    **本文を読んだだけの周まで dev-loop になる**（#101 で同じ落とし穴を踏んだ）。

    **この要求は `SLASH_NAME` の正規表現だけが持つ。** 最初は `in` による
    早期 return も置いていたが、**2 箇所が同じことを言うと片方への変異が
    もう片方に隠される**——実際に「タグの条件を外す」変異が生き残った。
    **歯止めを 1 箇所にする**（このリポジトリが繰り返し踏んでいる型）。
    """
    name = SLASH_NAME.search(text)
    if not name:
        return None
    args = SLASH_ARGS.search(text)
    return name.group(1), (args.group(1) if args else "")


def issue_number(args: str) -> str | None:
    """引数から Issue 番号を取る。最初の数字の連なりだけを見る。

    **番号が取れなければ `None`。** `/dev-loop` は引数 1 件が前提だが、
    実測では**引数の無い起動が 120 周のうち 2 件**あった。
    **`0` を返したり近い周に寄せたりしない**——束ねられなかったことを
    呼び出し側が判別できる必要がある（#103 の「先頭が範囲外」と同じ判断）。
    """
    found = re.search(r"\d+", args or "")
    return found.group(0) if found else None


def worktree_issue(repo_dir: str) -> str | None:
    """worktree のディレクトリ名から Issue 番号を取る（**補助の経路**）。

    起動形が取れないときだけ使う。**ディレクトリ名は人間が付けるので、
    Issue 番号とは限らない**——`issue-<数字>` の形に限って拾う。
    """
    found = WORKTREE_ISSUE.search(repo_dir or "")
    return found.group(1) if found else None


# --- 経過時間（`--elapsed`、#169） ---

# 関門の印。**周の印（`DEV_LOOP_AGENT`）と同じ部分一致で見る。**
REVIEW_SKILL = "code-review"
# **裏で起動したことを示す結果の印**（実物で数えた 3 形）。これ以外の結果は
# 前景の完了として扱う——**`forked` でも `background` が偽なら前景**（実物に 2 件）。
BACKGROUND_STATUSES = {"async_launched", "teammate_spawned"}
NOTIFY_TOOL_USE = re.compile(r"<tool-use-id>([^<]+)</tool-use-id>")
TEAMMATE = re.compile(r'<teammate-message teammate_id="([^"]+)"[^>]*>(.*?)(?:</teammate-message>|$)',
                      re.S)
# 区分。**この順で列に出す。合計がセッションの長さに等しい**（`partition`）。
CATEGORIES = ("model", "tool", "human", "notify", "other")


def _is_background(result) -> bool:
    if not isinstance(result, dict):
        return False
    status = result.get("status")
    return status in BACKGROUND_STATUSES or (status == "forked" and bool(result.get("background")))


def _notified(text: str) -> tuple[set, set]:
    """テキストから (tool-use-id の集合, 報告した teammate の集合) を返す。

    **teammate の idle 通知は、`result` を持つときだけ報告である。**
    #168 の周では報告が別の発言で先に届き、idle 通知は空だった。**一方で #92 の周では
    報告の本文が idle 通知の `result` にしか無かった**——一律に捨てると、その周の
    Verifier は全部「報告なし」になる（最初そう書いて、実データの「報告なし」40 件を
    調べて見つけた。#169）。
    """
    ids = set(NOTIFY_TOOL_USE.findall(text)) if "<task-notification>" in text else set()
    mates = {name for name, body in TEAMMATE.findall(text) if _reports(body)}
    return ids, mates


def _reports(body: str) -> bool:
    if '"idle_notification"' not in body:
        return True
    try:
        notice = json.loads(body.strip())
    except ValueError:
        return False
    return isinstance(notice, dict) and bool(notice.get("result"))


def elapsed_event(row: dict):
    """親の 1 行を、経過時間の境界にする。境界にならない行は `None`。

    返すのは `(時刻, 種類, 中身)`。種類は:

    - `assistant` — 中身は `{"end_turn": bool, "starts": [(id, 道具名, 関門, teammate 名)]}`
    - `result` — 道具の結果。中身は `{"ids": {id: 裏で起動したか}}`
    - `notify` — 通知（task-notification / teammate-message）。中身は `{"ids", "mates"}`
    - `human` — 人間の発言（スラッシュ起動を含む）

    **`isMeta` の行は境界にしない**——スキル本文の注入などで、人間の発言ではない。
    **通知は 2 つの経路で届く**——user 行と `attachment`（`queued_command`）。
    実物では**片方にしか出ないものがどちらの側にも多い**ので、両方を拾う。
    """
    timestamp = row.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        return None
    kind = row.get("type")
    if kind == "attachment":
        attachment = row.get("attachment")
        if not isinstance(attachment, dict) or attachment.get("type") != "queued_command":
            return None
        # **`prompt` の文字列に当てる。** `json.dumps` してから当てると
        # `teammate_id="…"` の引用符がエスケープされて一致しない（最初そう書いて試料で落ちた）。
        # 実物の `prompt` は全件が文字列。**通知でない `queued_command`**（人間の入力の
        # 待ち行列など）は境界にしない——その区間は前後の行のどちらかに入る。
        prompt = attachment.get("prompt")
        ids, mates = _notified(prompt) if isinstance(prompt, str) else (set(), set())
        if ids or mates:
            return timestamp, "notify", {"ids": ids, "mates": mates}
        return None
    message = row.get("message")
    if not isinstance(message, dict) or row.get("isMeta"):
        return None
    if kind == "assistant":
        starts = []
        for block in tool_uses(message):
            args = block.get("input") if isinstance(block.get("input"), dict) else {}
            name = block.get("name") or ""
            gate = None
            if name in AGENT_TOOLS and DEV_LOOP_AGENT in str(args.get("subagent_type") or ""):
                gate = "verifier"
            elif name == "Skill" and REVIEW_SKILL in str(args.get("skill") or ""):
                gate = "review"
            starts.append((block.get("id"), name, gate, args.get("name")))
        return timestamp, "assistant", {"end_turn": message.get("stop_reason") == "end_turn",
                                        "starts": starts}
    if kind != "user":
        return None
    content = message.get("content")
    results = {}
    if isinstance(content, list):
        background = _is_background(row.get("toolUseResult"))
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                results[block.get("tool_use_id")] = background
    if results:
        return timestamp, "result", {"ids": results}
    ids, mates = set(), set()
    for text in user_texts(message):
        found_ids, found_mates = _notified(text)
        ids |= found_ids
        mates |= found_mates
    if ids or mates or any("<teammate-message" in t or t.lstrip().startswith("<task-notification>")
                           for t in user_texts(message)):
        return timestamp, "notify", {"ids": ids, "mates": mates}
    return timestamp, "human", {}


def _seconds(start: str, end: str) -> float:
    parse = dt.datetime.fromisoformat
    return (parse(end.replace("Z", "+00:00")) - parse(start.replace("Z", "+00:00"))).total_seconds()


def partition(events) -> dict:
    """1 セッションの境界の列を、区分ごとの秒数に分ける。**合計はセッションの長さに等しい。**

    **区間は、それを終わらせた行で分類する**（前の行が end_turn かどうかも見る）:

    | 前 | 後 | 区分 |
    | --- | --- | --- |
    | 何でも | `AskUserQuestion` の結果 | `human` |
    | end_turn | 人間の発言 | `human` |
    | end_turn | 通知 | `notify`（**親が手を止めて、裏の仕事を待っていた**） |
    | end_turn 以外 | assistant | `model` |
    | end_turn 以外 | 道具の結果 | `tool` |
    | 上のどれでもない | | `other` |

    **関門の時間はここに入らない**——関門は裏で走り、親の区間と重なる（`gates`）。
    **並べ替えてから数える**——実物に、時刻が逆順の行がある。
    """
    ordered = sorted(events, key=lambda e: e[0])
    asked = {tool_id for _, kind, body in ordered if kind == "assistant"
             for tool_id, name, _, _ in body["starts"] if name == "AskUserQuestion"}
    totals = dict.fromkeys(CATEGORIES, 0.0)
    for prev, cur in zip(ordered, ordered[1:]):
        gap = _seconds(prev[0], cur[0])
        ended = prev[1] == "assistant" and prev[2]["end_turn"]
        if cur[1] == "result" and asked & set(cur[2]["ids"]):
            category = "human"
        elif ended and cur[1] in ("human", "notify"):
            category = cur[1]
        elif not ended and cur[1] == "assistant":
            category = "model"
        elif not ended and cur[1] == "result":
            category = "tool"
        else:
            category = "other"
        totals[category] += gap
    return totals


def gates(events) -> list[tuple[str, float | None]]:
    """関門ごとに `(種類, 起動から最初の報告までの秒数)` を返す。報告が無ければ `None`。

    **終わりは 3 つの形のどれか**——前景の結果 ／ `<tool-use-id>` が一致する通知 ／
    `Agent` の `name` と `teammate_id` が一致する報告（idle 通知は除く）。
    **最初に届いたものを採る**——同じ id が 2 度通知されることがある（途中の報告かもしれない）。
    **報告が無い関門を落とさず、0 秒にもしない**（`None` のまま返す）。
    """
    ordered = sorted(events, key=lambda e: e[0])
    found = {}
    for timestamp, kind, body in ordered:
        if kind == "assistant":
            for tool_id, _, gate, mate in body["starts"]:
                if gate and tool_id and tool_id not in found:
                    found[tool_id] = (gate, mate, timestamp)
    out = []
    for tool_id, (gate, mate, start) in found.items():
        end = None
        for timestamp, kind, body in ordered:
            if timestamp < start:
                continue
            if kind == "result" and body["ids"].get(tool_id) is False:
                end = timestamp
            elif kind == "notify" and (tool_id in body["ids"] or (mate and mate in body["mates"])):
                end = timestamp
            if end:
                break
        out.append((gate, _seconds(start, end) if end else None))
    return out


def _iter_rows(path: pathlib.Path):
    """`(row, 問題)` を 1 行ずつ返す。問題は `None` / `"broken"` / `"unreadable"`。

    **開く失敗を呼び出し側の `try` で捕まえられない。** これはジェネレータなので、
    `path.open()` は**最初の `next()` まで動かない**——`rows = _iter_rows(path)` を
    `try` で囲んでも、その `try` を抜けた後の `for` で例外が出る。
    **実際に、読めないファイルが 1 つあるだけで全体が落ちた**（#95 の 3 パス目）。
    だから**ここで捕まえて、問題として返す**。

    **読み取り中の失敗も捕まえる。** 走査の最中にトランスクリプトが消えることがある
    （レビュー中に実際に `FileNotFoundError` を踏んだ）。`yield` を囲む `try` で拾う。

    **`read_text()` ＋ `splitlines()` にしない。** ファイル 1 つ分のテキストと
    全行のリストが**同時にメモリに載る**——同じ走査の前後で測って
    **1,672MB → 107MB**（ピーク RSS。15 分の 1）、**12.8 秒 → 8.8 秒**だった。
    トランスクリプトは 1 ファイルが大きいので、ここが支配的だった。
    （**前後を別の実験から取らない**。「空ループなら 42MB」は*別の測定*で、
    出荷する実装のピークではない——最初その 2 つを並べて書いた。）

    **壊れた行は黙って落とさず、印をつけて返す。**
    """
    try:
        handle = path.open(encoding="utf-8", errors="replace")
    except OSError:
        yield None, "unreadable"
        return
    try:
        with handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except (ValueError, TypeError):
                    yield None, "broken"
                    continue
                if not isinstance(row, dict):
                    yield None, "broken"
                    continue
                yield row, None
    except OSError:
        # 走査中に消えた・読めなくなった。**黙って打ち切らない。**
        yield None, "unreadable"


def scan(projects_root: pathlib.Path, merge_worktrees: bool = False, events=None,
         issues=None):
    """(レコード列, dev-loop を回したセッション, 読めなかったファイル数, 壊れた行数) を返す。

    **1 応答が複数行に書かれ、各行が同じ `usage` を再掲する。**
    `message.id` が同じ行を 1 リクエストとして畳まないと、**加重が 7 割ほど膨らむ**
    （率は設計 §8.3 の訂正を見ること）。**#95 のレビューが見つけた**——
    実装の初版は行ごとに足しており、**出した数字がすべて過大だった**。

    畳むときは**最大を採る**。再掲は同じ値のこともあるが、**`output_tokens` が
    `1 → 1 → 207` のように育っていく形**もある。
    最後の行が最大になるので、最大を採れば最終状態を拾える。
    （実測では「最後 ≠ 最大」は 0 件なので、どちらでも同じ値になる。
    **最大のほうが安全側**なので最大にしてある。）

    **`events` に辞書を渡すと、親の行の境界（`elapsed_event`）を
    `(repo, session)` ごとに集める**（`--elapsed`。#169）。**周の検出はこの関数の
    ものをそのまま使う**——経過時間のために周を数え直すと、片方だけ変わってずれる。
    """
    records: list[Record] = []
    dev_loop_sessions: set[tuple[str, str]] = set()
    unreadable = 0
    broken_lines = 0
    # **`message.id` は API が採番するので、ファイルを跨いでも同一の応答を指す。**
    # セッションを fork / resume すると履歴がコピーされ、**同じ応答が別ファイルにも入る**
    # （モデルが食い違うものは 0 件）。ファイル単位で畳むと**数 % 過大**になる
    # ——#95 の 2 パス目のレビューが見つけた。
    # **帰属の決め方は下の畳み込みを正とする**（同じ関数の中で 2 回説明すると、
    # 片方だけ古くなる。**実際にそうなった**: #95 の 4 パス目で、ここと 50 行下が
    # **逆のことを言っている**状態が見つかった）。
    by_id: dict[str, Record] = {}

    # **(repo, session) -> Issue 番号。** 走査中に集め、**最後に Record へ入れる**。
    # **2 つに分けて持つ。** 起動形（`<command-args>`）が正で、
    # worktree のディレクトリ名は**それが取れないときだけ**使う補助の経路。
    # 1 つの辞書に混ぜると、**走査順でどちらが勝つかが変わる**。
    session_issue: dict[tuple[str, str], str] = {}
    session_issue_fallback: dict[tuple[str, str], str] = {}
    session_issue_skill: dict[tuple[str, str], str] = {}
    seen_rows: set[str] = set()
    for path in sorted(projects_root.rglob("*.jsonl")):
        repo, session, is_sub = session_of(path, projects_root, merge_worktrees)
        rel_parts = path.relative_to(projects_root).parts
        repo_dir = rel_parts[0] if rel_parts else ""
        # **補助の経路（#108）。** 別の辞書に入れておき、
        # 起動形が取れなかった周にだけ使う。
        fallback = worktree_issue(repo_dir)
        if fallback:
            session_issue_fallback.setdefault((repo, session), fallback)
        for row, problem in _iter_rows(path):
            if problem == "unreadable":
                unreadable += 1
                continue
            if problem == "broken":
                broken_lines += 1
                continue
            if events is not None and not is_sub:
                # **fork / resume で履歴がコピーされた行を 2 度数えない。** コピーは
                # **`uuid` も時刻も元と同じ**なので、時刻では帰属を決められない。
                # **最初に見た側に 1 度だけ入れる**——どちらに入っても和集合は 1 回ずつになる。
                # 実物で、同じ Issue の 2 セッションが 933 行を共有し、
                # **セッションの長さの合計が壁時計の 2 倍**になっていた（#169）。
                row_id = row.get("uuid")
                if not (isinstance(row_id, str) and row_id in seen_rows):
                    event = elapsed_event(row)
                    if event is not None:
                        events.setdefault((repo, session), []).append(event)
                    if isinstance(row_id, str):
                        seen_rows.add(row_id)
            message = row.get("message")
            if not isinstance(message, dict):
                continue

            for text in user_texts(message):
                invocation = slash_command(text)
                if invocation is None:
                    continue
                name, args = invocation
                if DEV_LOOP_SKILL not in name:
                    continue
                # **スラッシュ起動も dev-loop の周である（#108）。**
                # これが無いと、手順 5 で Verifier を呼ぶまで周が存在しない。
                dev_loop_sessions.add((repo, session))
                number = issue_number(args)
                if number:
                    session_issue.setdefault((repo, session), number)

            for block in tool_uses(message):
                name = block.get("name")
                args = block.get("input")
                if not isinstance(args, dict):
                    continue
                if name == "Skill":
                    skill = args.get("skill") or args.get("command") or ""
                    if isinstance(skill, str) and DEV_LOOP_SKILL in skill:
                        dev_loop_sessions.add((repo, session))
                        # **起動形が素のテキストのとき、番号は `Skill` の引数にしか無い**
                        # （#168 の周が実際にそうで、`--per-issue` から落ちていた。#169）。
                        # **`<command-args>` の番号より後に置く**——`setdefault` なので先に
                        # 入ったほうが勝つが、走査順は保証されないので辞書を分ける。
                        number = issue_number(str(args.get("args") or ""))
                        if number:
                            session_issue_skill.setdefault((repo, session), number)
                elif name in AGENT_TOOLS:
                    subagent = args.get("subagent_type") or ""
                    if isinstance(subagent, str) and DEV_LOOP_AGENT in subagent:
                        dev_loop_sessions.add((repo, session))

            usage = message.get("usage")
            if not isinstance(usage, dict):
                continue
            model = message.get("model") or "?"
            if model in SYNTHETIC_MODELS:
                continue
            weighted, cache_read = weighted_tokens(usage)
            context = context_tokens(usage)
            timestamp = row.get("timestamp") or ""
            day = timestamp[:10]
            record = Record(day, repo, session, is_sub, model, weighted, cache_read,
                            timestamp, context)
            message_id = message.get("id")
            if not isinstance(message_id, str) or not message_id:
                # id が無ければ畳めない。**そのまま数える**（落とすより過大のほうがまし）。
                records.append(record)
                continue
            previous = by_id.get(message_id)
            if previous is None:
                by_id[message_id] = record
                continue
            # **消費量と帰属で採る基準が違う。**
            # 消費量は**最大**（途中経過の行があるので、育ちきった値を採る）。
            # 帰属は**最も古いレコード**——コピーではなく**最初に消費した側**に計上する。
            #
            # **この帰属の規則は、いまのデータでは何も変えていない。** 実測すると、
            # 複数セッションに跨るグループ **1,915 件すべてで、走査順の先頭が
            # 最も古いレコードでもあった**（分岐は 4 回発火するが、帰属を変えたのは 0 回）。
            # **つまり保険である。** `sorted()` はリポジトリ名とセッション UUID の順で、
            # **時刻の情報を持たない**——いま一致しているのは**そういうデータだから**で、
            # 保証ではない。
            #
            # **一度、逆の実測を書いた**（「走査順の先頭が最も古いファイルだった例は
            # 0 件」）。測り方が壊れていたのに気づかず、**その誤った数字を根拠にして
            # この規則を入れた**。#95 の 4 パス目のレビューが再測して見つけた。
            if record.weighted > previous.weighted:
                previous.weighted = record.weighted
                previous.cache_read = record.cache_read
                previous.context = record.context
            if record.timestamp and (not previous.timestamp
                                     or record.timestamp < previous.timestamp):
                previous.timestamp = record.timestamp
                previous.day = record.day
                previous.repo = record.repo
                previous.session = record.session
                previous.is_sub = record.is_sub

    records.extend(by_id.values())
    # **Issue 番号は走査を終えてから入れる。** 起動形は先頭にあるとはいえ、
    # **畳み込みが帰属を書き換える**（同じ応答が別セッションのファイルにも入る）ので、
    # レコードの `session` が決まるのはここである。
    #
    # **優先順はここ 1 箇所**——起動形 → `Skill` の引数 → worktree 名。
    def issue_for(key):
        return (session_issue.get(key) or session_issue_skill.get(key)
                or session_issue_fallback.get(key))

    for record in records:
        record.issue = issue_for((record.repo, record.session))
    # **経過時間はレコードからではなく、セッションから番号を引く**——
    # usage を持たないセッションでも周の境界は持つ（`--elapsed`。#169）。
    if issues is not None:
        for key in set(session_issue) | set(session_issue_skill) | set(session_issue_fallback):
            issues[key] = issue_for(key)
    return records, dev_loop_sessions, unreadable, broken_lines


def iso_week(day: str) -> str:
    try:
        d = dt.date.fromisoformat(day)
    except ValueError:
        return "?"
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def fmt_m(value: float) -> str:
    return f"{value / 1_000_000:.0f}"


def render_weekly(records, dev_loop_sessions) -> str:
    weeks = collections.defaultdict(lambda: {
        "weighted": 0.0, "sessions": set(), "dev": set(), "requests": 0, "ctx": 0,
    })
    for r in records:
        bucket = weeks[iso_week(r.day)]
        bucket["weighted"] += r.weighted
        bucket["sessions"].add((r.repo, r.session))
        bucket["requests"] += 1
        bucket["ctx"] += r.cache_read
        if (r.repo, r.session) in dev_loop_sessions:
            bucket["dev"].add((r.repo, r.session))

    lines = ["| ISO週 | セッション | うち dev-loop | 加重(M) | dev-loop 比 | 平均文脈 |",
             "|---|---|---|---|---|---|"]
    for week in sorted(weeks):
        b = weeks[week]
        n_sessions = len(b["sessions"])
        n_dev = len(b["dev"])
        dev_weighted = sum(r.weighted for r in records
                           if iso_week(r.day) == week
                           and (r.repo, r.session) in dev_loop_sessions)
        ratio = f"{100 * dev_weighted / b['weighted']:.0f}%" if b["weighted"] else "–"
        ctx = b["ctx"] // b["requests"] if b["requests"] else 0
        lines.append(f"| {week} | {n_sessions} | {n_dev} | {fmt_m(b['weighted'])} "
                     f"| {ratio} | {ctx // 1000}k |")
    return "\n".join(lines)


def render_split(records, dev_loop_sessions) -> str:
    """dev-loop を回した周とそれ以外に分ける（設計 §8.3 の表と同じ形）。

    **この形で出すのは、before/after を同じ切り口で比べるため**である。
    §8.3 の表は 2026-09-15 時点の記録なので、**同じ範囲・同じ式で取り直して初めて
    比較になる**。
    """
    groups = {"dev-loop を回した周": [], "それ以外": []}
    for r in records:
        key = ("dev-loop を回した周" if (r.repo, r.session) in dev_loop_sessions
               else "それ以外")
        groups[key].append(r)

    lines = ["| 区分 | セッション | 加重(M) | 比率 | リクエスト/セッション |",
             "|---|---|---|---|---|"]
    total = sum(r.weighted for r in records) or 1
    for name, rows in groups.items():
        sessions = {(r.repo, r.session) for r in rows}
        weighted = sum(r.weighted for r in rows)
        per_session = len(rows) // len(sessions) if sessions else 0
        lines.append(f"| {name} | {len(sessions)} | {fmt_m(weighted)} "
                     f"| {100 * weighted / total:.0f}% | {per_session} |")
    return "\n".join(lines)


def session_floors(records) -> dict:
    """周ごとの**起点**を返す（`(repo, session) -> (最初の時刻, トークン数)`）。

    **起点 ＝ その周の最初の応答が既に抱えていた文脈。**
    system prompt・道具定義・`CLAUDE.md`・メモリ・スキル本文が入る——
    **1 ターンも仕事をしていない時点の文脈**である。

    **サブエージェントのレコードから取らない。** 委譲先は**親と別の起点**を持つので、
    混ぜると周の起点が委譲先の値に置き換わりうる。

    **最も古いレコードを採る。走査順では決められない**——セッション id は UUID で
    **時刻を持たない**（`scan` の帰属と同じ理由）。**タイムスタンプを持たないレコードは
    候補にしない**（空文字は文字列順で最小になり、黙って先頭に立つ）。

    **時刻も返す。** 呼び出し側が「その周の先頭が絞り込みで切られていないか」を
    判定できないと、**周の途中のレコードを起点と呼んでしまう**——実測で、
    `--since` を周の途中に置くと**起点 470k・起点比 104%** という値が出た。
    **絞り込む前のレコードから作って渡すこと**（`main` がそうしている）。
    """
    best: dict = {}
    for r in records:
        if r.is_sub or not r.timestamp:
            continue
        key = (r.repo, r.session)
        current = best.get(key)
        if current is None or r.timestamp < current[0]:
            best[key] = (r.timestamp, r.context)
    return best


def floor_share(floor: int, parent_requests: int, weighted: float) -> float | None:
    """親の起点が周の加重に占める割合（%）。分からなければ `None`。

    **`parent_requests` は親のリクエスト数である。サブエージェントを含めてはいけない。**
    委譲先は**自分の起点**を持っており、**親の起点を払わない**。含めると
    **親の起点を、それを払っていないリクエストにまで課金する**ことになる
    ——実測で**中央値 29.3% 対 17.8%、1.65 倍の過大**だった（#108）。
    サブエージェントが加重の 24% を占めるのが出所である。

    **初版はここを間違えていた。** `render_per_cycle` が全レコードを渡しており、
    **「周の 30%」として #101 / #102 / #103 の根拠に使った数字は 1.65 倍**だった。
    引数の名前を `requests` から変えてあるのは、**基準を取り違えたまま呼べないようにする**ため。

    **残る近似は 1 つで、向きは小さめ。** 起点は**最初のリクエストだけ
    cache write（×1.25）として課金される**のに、ここでは全リクエストを
    cache read（×0.1）として数えている。
    **以前この docstring は「だから安全側」と書いていたが、それは誤りだった**
    ——上のリクエスト基準の誤り（1.65 倍の過大）のほうが大きく、**向きは逆だった**。

    **分母は周の加重の全部**（サブエージェントを含む）である。
    したがってこれは**「親の起点が周全体のコストに占める割合」**で、
    **委譲先の起点は数に入っていない**——周全体の「起点の総額」はこれより大きい。

    **割り算にガードを置く。** レコードはあるのに加重が 0 のことがある
    （トップレベルの usage が全部 0 のレコードが実在する）。
    """
    if not floor or not parent_requests or not weighted:
        return None
    return 100 * (floor * parent_requests * WEIGHTS["cache_read_input_tokens"]) / weighted


def floor_share_summary(shares) -> str | None:
    """起点比の集計行。**中央値を出す。平均にしない。**

    起点比は 1 周の req が少ないほど跳ねるので、**短い周 1 つで平均が動く**
    （実測で 128 req の周が 39% を出している）。

    **`--per-cycle` と `--per-issue` が共有する。** 式を 2 箇所に置くと
    **片方だけ直して緑になる**——このリポジトリが繰り返し踏んでいる型である。
    """
    if not shares:
        return None
    return (f"**起点が占める割合: 中央値 {statistics.median(shares):.0f}%**"
            f"（{len(shares)} 周で算出）")


def render_per_issue(records, dev_loop_sessions, floors=None) -> str:
    """Issue 番号で束ねた周を返す（`--per-issue`）。

    **`--per-cycle` は周を `(repo, session)` で数えている。** `/clear` で割ると
    **セッション id が変わるので 1 周が 2 周になる**——per-session の会計では、
    **割った周は必ず「軽くなった」と出る**（#108）。ここは `(repo, Issue 番号)` で束ねる。

    **起点はセッションごとに合計する。** 割った後のセッションは
    **起点（実測で約 90k）を払い直す**ので、周全体の起点は 1 セッション分ではない。
    **これが「割ると得か」の答えを決める量**である。

    **Issue 番号が取れなかった周は束ねない。** 行に出さず、**件数だけ別に示す**
    ——近い周に寄せると、束ねられなかったことが数字から見えなくなる
    （#103 の「先頭が範囲外」と同じ判断）。

    **セッション数を列に出す。** 出さないと、**割れた周と割れていない周が
    見分けられない**——この表を作った目的そのものが見えなくなる。
    """
    if floors is None:
        floors = session_floors(records)

    # セッション単位の集計が先に要る（起点はセッションごとに払う）。
    per_session = collections.defaultdict(lambda: {"weighted": 0.0, "requests": 0,
                                                   "ctx": 0, "day": "", "first": ""})
    for r in records:
        key = (r.repo, r.session)
        if key not in dev_loop_sessions:
            continue
        b = per_session[key]
        if r.timestamp and not r.is_sub and (not b["first"] or r.timestamp < b["first"]):
            b["first"] = r.timestamp
        b["weighted"] += r.weighted
        if not r.is_sub:
            b["requests"] += 1
            b["ctx"] += r.cache_read
        if r.day and (not b["day"] or r.day < b["day"]):
            b["day"] = r.day

    issue_of = {}
    for r in records:
        if r.issue:
            issue_of[(r.repo, r.session)] = r.issue

    per_issue = collections.defaultdict(lambda: {"weighted": 0.0, "requests": 0,
                                                 "ctx": 0, "day": "", "sessions": 0,
                                                 "floor_req": 0.0, "truncated": False})
    unmerged = 0
    for key, b in per_session.items():
        number = issue_of.get(key)
        if not number:
            unmerged += 1
            continue
        g = per_issue[(key[0], number)]
        g["weighted"] += b["weighted"]
        g["requests"] += b["requests"]
        g["ctx"] += b["ctx"]
        g["sessions"] += 1
        if b["day"] and (not g["day"] or b["day"] < g["day"]):
            g["day"] = b["day"]
        first_seen, floor = floors.get(key, ("", 0))
        cut = bool(first_seen) and bool(b["first"]) and b["first"] > first_seen
        if cut or not floor:
            g["truncated"] = True
        else:
            g["floor_req"] += floor * b["requests"]

    if not per_issue:
        return "Issue 番号で束ねられた周は見つかりませんでした。"

    lines = ["| 日 | Issue | セッション | req | 加重(M) | 平均文脈 | 起点×req | 起点比 |",
             "|---|---|---|---|---|---|---|---|"]
    shares = []
    for (repo, number), g in sorted(per_issue.items(), key=lambda kv: kv[1]["day"]):
        ctx = g["ctx"] // g["requests"] if g["requests"] else 0
        if g["truncated"] or not g["weighted"]:
            floor_cell, share_cell = "–（先頭が範囲外）", "–"
        else:
            weighted_floor = g["floor_req"] * WEIGHTS["cache_read_input_tokens"]
            share = 100 * weighted_floor / g["weighted"]
            shares.append(share)
            floor_cell = f"{g['floor_req'] / 1e6:.1f}M"
            share_cell = f"{share:.0f}%"
        lines.append(f"| {g['day']} | #{number} | {g['sessions']} | {g['requests']} "
                     f"| {fmt_m(g['weighted'])} | {ctx // 1000}k "
                     f"| {floor_cell} | {share_cell} |")

    split = sum(1 for g in per_issue.values() if g["sessions"] > 1)
    lines.append("")
    lines.append(f"**{len(per_issue)} 周**（うち**割れている周 {split} 件**——"
                 f"2 セッション以上）")
    summary = floor_share_summary(shares)
    if summary:
        lines.append(summary)
    if unmerged:
        # **束ねられなかったものを黙って落とさない。** 落とすと、
        # 表の「周」が母集団の全部だと読めてしまう。
        lines.append(f"**Issue 番号が取れず束ねられなかったセッション: {unmerged} 件**"
                     f"（この表には出していない）")
    return "\n".join(lines)


def fmt_minutes(seconds: float) -> str:
    return f"{seconds / 60:.0f}"


def render_elapsed(issue_of, dev_loop_sessions, events, since=None) -> str:
    """Issue で束ねた周の経過時間を返す（`--elapsed`、#169）。

    **答える問い**: 1 周の経過時間のうち、どれだけが待ちで、どれだけがどの関門に使われたか。

    **区分（モデル／道具／人間待ち／通知待ち／その他）の合計は、セッションの長さに等しい**
    （`partition`）。**セッション外**は、Issue の最初から最後までのうちどのセッションにも
    入らない時間で、`/clear` で割った周の割り目の間などがここに入る。

    **関門の列は壁時計に足さない。** 関門は裏で走り、親の区間と重なる。
    **並列に走った関門も足すと壁時計を超える**ので、関門ごとの合計として読む。

    **束ね方は `render_per_issue` と同じ**（`scan` の周と Issue 番号を使う）。
    番号が取れないセッションは行に出さず、件数だけ出す。
    **番号はレコードではなくセッションから引く**（`scan` の `issues`）。

    **`--since` が周の途中に落ちたら、その周は出さない**——残った行は周の途中から始まり、
    近い値で代用すると短く出る（起点と同じ判断）。件数だけ出す。
    """
    cycles = collections.defaultdict(lambda: {"sessions": 0, "span": 0.0,
                                                 "first": "", "last": "",
                                                 "parts": dict.fromkeys(CATEGORIES, 0.0),
                                                 "gates": collections.defaultdict(list),
                                                 "truncated": False})
    unmerged = 0
    for key, session_events in events.items():
        if key not in dev_loop_sessions or not session_events:
            continue
        first = min(e[0] for e in session_events)
        last = max(e[0] for e in session_events)
        # **範囲外は、集計の枠を作る前に落とす**——先に枠を作ると、空の枠が
        # 行として残る（最初そう書いて `--since` で落ちた）。
        if since and last[:10] < since:
            continue  # 丸ごと範囲外。
        number = issue_of.get(key)
        if not number:
            unmerged += 1
            continue
        g = cycles[(key[0], number)]
        if since and first[:10] < since:
            g["truncated"] = True
        g["sessions"] += 1
        g["span"] += _seconds(first, last)
        g["first"] = min(g["first"], first) if g["first"] else first
        g["last"] = max(g["last"], last)
        for category, seconds in partition(session_events).items():
            g["parts"][category] += seconds
        for gate, seconds in gates(session_events):
            g["gates"][gate].append(seconds)

    shown = {k: g for k, g in cycles.items() if not g["truncated"]}
    truncated = len(cycles) - len(shown)
    if not shown:
        message = "Issue 番号で束ねられた周は見つかりませんでした。"
        if truncated:
            message += f"（先頭が範囲外の周 {truncated} 件は出していない）"
        return message

    def gate_cell(values):
        done = [v for v in values if v is not None]
        missing = len(values) - len(done)
        cell = f"{len(done)} 回 / {fmt_minutes(sum(done))}" if values else "–"
        return cell + (f"（報告なし {missing}）" if missing else "")

    lines = ["| 日 | Issue | セッション | 壁時計 | セッション外 | モデル | 道具 | 人間待ち "
             "| 通知待ち | その他 | Verifier | レビュー |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (repo, number), g in sorted(shown.items(), key=lambda kv: kv[1]["first"]):
        wall = _seconds(g["first"], g["last"])
        parts = g["parts"]
        outside = wall - g["span"]
        # **並行して動いたセッションは重なる**（コピーではない。`uuid` を共有しない実物がある）。
        # **負の「セッション外」を出さない**——読み手は引き算の結果を時間と読む。
        outside_cell = fmt_minutes(outside) if outside >= 0 else f"重なり {fmt_minutes(-outside)}"
        lines.append(f"| {g['first'][:10]} | #{number} | {g['sessions']} | {fmt_minutes(wall)} "
                     f"| {outside_cell} "
                     + " ".join(f"| {fmt_minutes(parts[c])}" for c in CATEGORIES)
                     + f" | {gate_cell(g['gates']['verifier'])} "
                     f"| {gate_cell(g['gates']['review'])} |")
    lines.append("")
    lines.append(f"**{len(shown)} 周**。単位は分。**モデル〜その他の合計が、セッションの長さの合計**"
                 f"（壁時計 − セッション外）に等しい。")
    lines.append("**Verifier・レビューの列は壁時計に足さない**——裏で走り、親の区間と重なる"
                 "（回数 / 起動から最初の報告までの合計）。")
    if truncated:
        lines.append(f"**先頭が範囲外で出していない周: {truncated} 件**（`--since` が周の途中に落ちた）")
    if unmerged:
        lines.append(f"**Issue 番号が取れず束ねられなかったセッション: {unmerged} 件**"
                     f"（この表には出していない）")
    return "\n".join(lines)


def render_per_cycle(records, dev_loop_sessions, floors=None) -> str:
    per = collections.defaultdict(lambda: {"weighted": 0.0, "requests": 0, "ctx": 0,
                                           "day": "", "first": "", "parent": 0})
    for r in records:
        key = (r.repo, r.session)
        if key not in dev_loop_sessions:
            continue
        b = per[key]
        if r.timestamp and not r.is_sub and (not b["first"] or r.timestamp < b["first"]):
            b["first"] = r.timestamp
        b["weighted"] += r.weighted
        b["requests"] += 1
        # **起点比には親のリクエストだけを渡す。** 委譲先は自分の起点を持つので、
        # 混ぜると親の起点を 1.65 倍に課金する（#108。`floor_share` を正とする）。
        if not r.is_sub:
            b["parent"] += 1
        b["ctx"] += r.cache_read
        if not b["day"] or (r.day and r.day < b["day"]):
            b["day"] = r.day

    if not per:
        return "dev-loop を回した周は見つかりませんでした。"

    if floors is None:
        floors = session_floors(records)
    lines = ["| 日 | リポジトリ | req | 加重(M) | 平均文脈 | 起点 | 起点比 |",
             "|---|---|---|---|---|---|---|"]
    shares = []
    for key, b in sorted(per.items(), key=lambda kv: kv[1]["day"]):
        repo, _session = key
        ctx = b["ctx"] // b["requests"] if b["requests"] else 0
        first_seen, floor = floors.get(key, ("", 0))
        # **先頭が絞り込みで切られた周は、起点も起点比も出さない。**
        # 残っている最古のレコードは**周の途中**なので、そこを起点と呼べば
        # 100% を超える割合が出る（実測で 104% が出た）。**近い値で代用しない。**
        truncated = bool(first_seen) and bool(b["first"]) and b["first"] > first_seen
        share = None if truncated else floor_share(floor, b["parent"], b["weighted"])
        if share is not None:
            shares.append(share)
        floor_cell = "–（先頭が範囲外）" if truncated else f"{floor // 1000}k"
        lines.append(f"| {b['day']} | {repo} | {b['requests']} "
                     f"| {fmt_m(b['weighted'])} | {ctx // 1000}k "
                     f"| {floor_cell} | {f'{share:.0f}%' if share is not None else '–'} |")

    total_req = sum(b["requests"] for b in per.values())
    total_ctx = sum(b["ctx"] for b in per.values())
    lines.append("")
    lines.append(f"**{len(per)} 周・平均 {total_req // len(per)} req/周・"
                 f"平均文脈 {(total_ctx // total_req) // 1000 if total_req else 0}k**")
    summary = floor_share_summary(shares)
    if summary:
        lines.append(summary)
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--projects", default=None,
                        help="走査するディレクトリ（既定: ~/.claude/projects）")
    parser.add_argument("--since", default=None, help="この日以降だけ（YYYY-MM-DD）")
    parser.add_argument("--repo", default=None, help="この文字列を含むリポジトリだけ")
    parser.add_argument("--per-cycle", action="store_true",
                        help="週次ではなく dev-loop の周ごとに出す")
    parser.add_argument("--per-issue", action="store_true",
                        help="周を Issue 番号で束ねて出す（割った周を 1 周として数える）")
    parser.add_argument("--elapsed", action="store_true",
                        help="周を Issue 番号で束ね、経過時間を区分と関門に分けて出す（#169）")
    parser.add_argument("--split", action="store_true",
                        help="dev-loop を回した周とそれ以外に分けて出す（設計 §8.3 と同じ形）")
    parser.add_argument("--merge-worktrees", action="store_true",
                        help="worktree を元のリポジトリに寄せる")
    parser.add_argument("--list-repos", action="store_true",
                        help="--repo が実際に何にマッチするかを見る（集計しない）")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.projects) if args.projects else (
        pathlib.Path(os.path.expanduser("~")) / ".claude" / "projects")
    if not root.is_dir():
        print(f"ERROR: 走査先が見つからない: {root}", file=sys.stderr)
        return 1

    # **絞る前に、何に当たるかを見せる。** 部分一致は広すぎることがあり、
    # 短い名前は**思っているより多くに当たる**。**気づかないまま集計すると、
    # 数字が合わない理由が分からなくなる**（#95 の周で実際に踏んだ）。
    if args.list_repos:
        names = sorted({p.name for p in root.iterdir() if p.is_dir()})
        if args.merge_worktrees:
            # **集計と同じ粒度で見せる。** 見せる粒度が集計と違うと、
            # 「絞る前に何に当たるか見る」ための機能が用を成さない（#95 のレビュー）。
            names = sorted({n.split(WORKTREE_MARKER, 1)[0] for n in names})
        if args.repo:
            names = [n for n in names if args.repo in n]
        for name in names:
            mark = " ← worktree" if WORKTREE_MARKER in name else ""
            print(f"{name}{mark}")
        print(f"\n{len(names)} 件が一致"
              + (f"（`{args.repo}` で絞った）" if args.repo else ""))
        return 0

    events = {} if args.elapsed else None
    issues = {}
    records, dev_loop_sessions, unreadable, broken = scan(root, args.merge_worktrees, events,
                                                          issues)
    # **起点は絞り込みの前に作る。** `--since` が周の途中に落ちると、
    # 残ったレコードの先頭は**周の途中**になる。そこを起点と呼ぶと
    # **100% を超える起点比**が出る（実測で 104%）。
    floors = session_floors(records)
    if args.since:
        records = [r for r in records if r.day >= args.since]
    if args.repo:
        records = [r for r in records if args.repo in r.repo]
        dev_loop_sessions = {k for k in dev_loop_sessions if args.repo in k[0]}

    if not records:
        print("該当するレコードがありませんでした。")
        return 0

    sub = sum(1 for r in records if r.is_sub)
    sub_weighted = sum(r.weighted for r in records if r.is_sub)
    total_weighted = sum(r.weighted for r in records)

    if args.split:
        print(render_split(records, dev_loop_sessions))
    elif args.elapsed:
        print(render_elapsed(issues, dev_loop_sessions, events, args.since))
    elif args.per_issue:
        print(render_per_issue(records, dev_loop_sessions, floors))
    elif args.per_cycle:
        print(render_per_cycle(records, dev_loop_sessions, floors))
    else:
        print(render_weekly(records, dev_loop_sessions))
    print()
    # **割り算にガードを置く。** レコードはあるのに加重が 0 のことがある——
    # 実測で、トップレベルの usage が全部 0 のレコードが実在した。絞り込みの結果
    # それだけが残ると、ガードが無ければ ZeroDivisionError で落ちる（#95 のレビューが
    # 実データで再現させた）。`render_*` の割り算は守ってあったのに、ここだけ抜けていた。
    sub_ratio = f"{100 * sub_weighted / total_weighted:.0f}%" if total_weighted else "–"
    print(f"レコード {len(records)} 件（うちサブエージェント {sub} 件＝"
          f"加重の {sub_ratio}）。加重合計 {fmt_m(total_weighted)}M。")
    # **読めなかったものは黙って 0 にしない。** ファイルだけでなく**行**も数える
    # ——実データに壊れた行が実在し、そのうち何行かは `"usage"` を含んでいた（#95）。
    if unreadable:
        print(f"⚠ 読めなかったファイル: {unreadable} 件（集計から落ちている）")
    if broken:
        print(f"⚠ JSON として読めなかった行: {broken} 行（集計から落ちている）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
