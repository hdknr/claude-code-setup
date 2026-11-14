# Issue #1015 — 業務フローの形式検査に Quint（ITF のトレース）を使えるかを実験で確かめる

利用者が居る周（2026-11-14 起動）。従う版は dev-loop 1.107.0（キャッシュ）。

- 直す線: **既定**（出所: 手順 3 の回答・2026-11-14）
- Quint の導入: **一時ディレクトリに入れる**（`npm install --prefix <scratchpad>/quint`。グローバルには入れない。出所: 利用者の回答・2026-11-14）。
  Apalache・TLC の本体を `quint verify` が取りに行った先は、下の「記録」に書く
- PR は `Fixes #1015`

## 周の在り処

- ブランチ: `issue/1015-quint-itf-experiment`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1015`
- 起点コミット: `3aa4f0b`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `3aa4f0b70b3bc519871679bfc01ca7614030c7bd`

## 変更範囲

触る:
- `docs/plans/issue-1015.md` — この計画と実験の記録（モデル・変換の全文を含む）

触らない:
- `plugins/spec-loop/` の全部（Formal Checker・spec-ir・scaffold・check-tlc）——この周は採否を決める材料を作るだけ。採ると決めたら別の周
- `scripts/` ——変換のスクリプトは実験の記録として計画に載せるだけで、歯止め・CI に入れない
- 決定表（Z3・総当たり）と権限・ロール（Alloy）
- 「LLM には TLA+ より Quint のほうが書きやすい」の主張

複製の数: 実験の記録は計画ファイル 1 箇所だけ。プラグインの規範には触らないので複製は 0。

## デプロイ経路

`docs/` の変更なので main へのマージで GitHub Pages に載る（計画ファイルはサイトのナビには無いが、ビルドに入る）。プラグインの版は上げない（プラグインに触らない）。

## 生成物

該当なし——図・`skill-metrics.py` の生成ブロック・カタログを触らない。

## 受入基準

不変条件は「記録に書いた主張が、実行した出力で裏づけられている」こと。経路＝記録が述べる主張の 1 つずつ。

| # | 主張（記録が述べること） | 証明の手段 |
| --- | --- | --- |
| A1 | R21-10 と同じ形の合成のモデル（書き手が排他の外の定数から版を取って書き、デプロイで新旧の版の書き手が重なる）を TLA+ で書き、TLC が性質の違反（反例）を出す。直した版では反例が出ず、正常な状態に到達できる（陽性対照の 2 つ） | `tlc` の出力の判別する行 |
| A2 | 同じモデルを Quint で書き、Apalache（`quint verify`）が同じ性質の違反を出す。直した版で違反なし・到達できる（witness）・壊した版で違反あり | `quint` の出力の判別する行 |
| A3 | Apalache が違反を見つけるのに要る `--max-steps` の最小値と、それより小さいと「違反なし」になること（有界の実害） | `--max-steps` を変えた出力 |
| A4 | ITF（`--out-itf`）から spec-ir の trace ケース（`calls`・`steps`・`setup`/`after` の形）への変換が、決まった変換として書ける。**変換の出力が scaffold の trace の検査を通る** | 変換の全文・出力・scaffold の検査の結果 |
| A5 | 記事の主張「`--backend=tlc` は TLC を `-deadlock` 付きで起動する」が、入れた版で成り立つか | 実際の起動の引数（出力・ログ）か、Quint の該当ソース |
| A6 | 結果から「採る（どの範囲で）／採らない／保留」を理由つきで書く | 上の結果だけを根拠にする |
| A7 | Quint・Apalache を入れた場所と、ホームの下に書かれたもの（`~/.quint` など）を記録する | `ls` の出力 |

組み合わせ: A2×A3（違反が出る最小の深さで、陽性対照も出ること）。A1×A2（同じ性質・同じ構成で比べること——構成を変えたら比較にならない）。

未証明（この環境では証明できない）:
- 1 つの合成のモデルの結果が、ほかの業務フローに一般化するか（標本が 1 つ）

## 未解決の判断

- 採るとなったときの前提の確かめ（`check-quint.py` 相当）の形——この周では決めない

## 記録（2026-11-14）

環境: macOS（aarch64）・Java 22.0.1・Node v26.8.2・TLC 2.19（`tlc`＝`~/.local/bin/tlc`。素の TLC はこれ）・Quint 0.33.1・Apalache 0.62.4。
モデルと変換の全文は下の付録。モデルはリポジトリの外（scratchpad）で走らせた。

### 導入（A7）

- Quint は `npm install --prefix <scratchpad>/quint @informalsystems/quint` で入れた（グローバルには入れていない。`quint --version` は `0.33.1`）。
  npm は `protobufjs` の postinstall を走らせずに警告だけ出した（`npm warn install-scripts protobufjs@7.6.6`）——型検査・Apalache・TLC の経路はそのまま動いた。
- **`~/.quint` は周を始める前から在った**（`apalache-dist-0.62.4`・`rust-evaluator-v0.7.1`。日付は 2026-11-09——記事を書いたときの実験の残り。190 MB）。
  この周の実行の前後で `ls ~/.quint` は変わらなかった——**この周は何も取りに行っていない**（初回の取得の挙動はこの周では観測していない）。
- `quint verify` は Apalache をサーバー（`localhost:8822`）として起こす。走り終えた後に `apalache` のプロセスは残っていなかった（`ps`）。
  `--backend=tlc` が `$TMPDIR` に作る `quint-tlc-*` も残っていなかった。
- Apalache の出力には毎回 protobuf の脆弱性の警告（`makeExtensionsImmutable should not be called from protobuf gencode`）が出る。

### A1: TLC（合成のモデル。付録 A）

構成は書き手 2 つ（旧＝版 1・新＝版 2。版は定数）・行 1 つ・排他 1 つ。性質 `NoRollback == rowVer = maxWritten`（書いた最大の版より古い版が残らない）。
`Guard` が版の順序の守り（排他の中で読んだ版より古い版は書かずに `stale`）。

| モデル | 不変条件 | 結果（判別する行） |
| --- | --- | --- |
| 守りなし（壊れた版） | `NoRollback` | `Error: Invariant NoRollback is violated.`（深さ 5 の状態 = 4 遷移: 新が読む→新が書く→旧が読む→旧が書く。最後の `rowVer = 1`・`maxWritten = 2`） |
| 守りなし | `NotReachedGood`（到達の確かめ） | `Error: Invariant NotReachedGood is violated.`——全員が終わり版 2 が残る状態に到達できる |
| 守りあり（直した版） | `NoRollback` | `Model checking completed. No error has been found.`（`9 distinct states`） |
| 守りあり | `NotReachedGood` | `Error: Invariant NotReachedGood is violated.`——直した版でも正常な状態に到達できる（空振りでない） |

TLC の反例は行為の名前（`<Read line 16 …>`）を出すが、**行為の引数（どの書き手か）は出さない**——どの書き手の段かは状態の `pc` の差から読む。

### A2: Quint ＋ Apalache（付録 B。A1 と同じ構成・同じ性質）

`quint typecheck` は通った（rc=0）。`quint verify --max-steps=6`:

| モジュール | 不変条件 | 結果 |
| --- | --- | --- |
| `broken` | `noRollback` | rc=1・`Found 1 error(s)`・ITF を書いた（下の A4 で変換した反例はこれ。段の順は TLC と同じ） |
| `broken` | `notReachedGood` | rc=1——到達できる |
| `fixed` | `noRollback` | rc=0・`The outcome is: NoError`・`[ok] No violation found` |
| `fixed` | `notReachedGood` | rc=1——直した版でも到達できる |

この 1 つのモデルでは、**Apalache は TLC と同じ反例を同じ深さで見つけ、陽性対照の 2 つも通った**。

### A3: Apalache の深さの上限の実害

`broken`・`noRollback` で `--max-steps` を変えた:

| `--max-steps` | 結果 |
| --- | --- |
| 1・2・3 | **rc=0・`[ok] No violation found`** |
| 4 | rc=1・`[violation] Found an issue` |

反例は 4 遷移なので、**上限が 3 以下だと、壊れたモデルに「違反なし」を rc=0 で返す**。出力に「この深さまでしか見ていない」とは出ない（`--max-steps` の既定は 10）。
TLC は同じモデルを全探索して `9 distinct states` で閉じるので、この形の取りこぼしは無い。**Apalache の「違反なし」を判定に使うなら、深さを報告に書き、陽性対照（壊れた版で違反が出る）を同じ深さで取る決まりが要る。**

### A4: ITF から trace ケースへの変換

- **Apalache（`quint verify --out-itf`）の ITF は状態の並びだけで、行為の名前も引数も持たない**（`vars` は 6 つの状態変数だけ）。
  `quint verify` には `--mbt` が無い（`quint verify --help`）。
- **`quint run --mbt`（シミュレータ。網羅しない）の ITF は、状態ごとに `mbt::actionTaken`（`read`・`write`）と `mbt::nondetPicks`（`w` = `new`・`old`）を持つ**
  （種 `0x1`・`--max-samples=10000` で反例が出た）。ただし `vars` に `mbt::actionTaken`・`mbt::nondetPicks` が 2 回ずつ載っていた。
- 変換（付録 C）は 2 つの形を持つ: `mbt` の ITF なら行為の名前と選ばれた呼び出しから、状態だけの ITF なら隣の状態で `pc` が変わった呼び出しを 1 つ探して段を決める。
  2 本の ITF のどちらからも同じ `steps` が出た: `[["new_writer","read"],["new_writer","write"],["old_writer","read"],["old_writer","write"]]`。
- **変換の出力は、本物の `plugins/spec-loop/scripts/scaffold.py` の `check_trace` を通った**（付録 E。入口 3 つを置き、`spec/formal/version-write/README.md` を一時ディレクトリに置いた）。
  陽性対照として段の呼び出しの名前を `calls` に無いものに変えた版は赤（`check_trace` が問題を返す）だった。
- **決まった変換にできたのは `calls` と `steps` だけ**。次は ITF に無いので人が書く（付録 D の対応表）:
  - モデルの書き手と実装の入口・入力の対応（`old` → `write_row {"key": "k", "ver": 1}`）
  - モデルの段（`Read`・`Write`）とトレースの段の名前の対応
  - `setup`・`outcomes`・`after`——**期待は直した仕様の結果で、反例（壊れた版）の最後の状態ではない**ので、反例からは出ない
- 状態から段を決める形は、**モデルが呼び出し → 段の写像（`pc`）を持ち、1 遷移で動く呼び出しが 1 つ**であることに乗っている。
  **同じ決め方は TLC の反例（状態の並び）にも当てはまる**——違いは、ITF が JSON なのに対し、TLC の反例は TLA+ の値の文字列で、読むのに TLA+ の値の構文を解く必要があること。
  手元の TLC 2.19 は `-dumpTrace json` を持たなかった（`Error: unrecognized option: -dumpTrace`）。`-tool`（機械向けの出力）と `-generateSpecTE` は試していない。

### A5: `--backend=tlc` とデッドロック

全員が終わった後の `done` を外した step（`stepNoDone`。終わった状態で行き詰まる）を当てた:

| 検査器 | 結果 |
| --- | --- |
| Apalache（`quint verify --step=stepNoDone`） | rc=1・`Found a deadlock.`・`The outcome is: Deadlock` |
| **Quint 経由の TLC（`--backend=tlc`）** | **rc=0・`Model checking completed. No error has been found.`・`[ok] No violation found`** |
| 素の TLC（同じ形の `NoDone.tla`・既定のオプション） | rc=11・`Error: Deadlock reached.`（対照: 行き詰まりは本物） |
| 素の TLC（`-deadlock`） | rc=0・`No error has been found.` |

**記事の主張は Quint 0.33.1 で成り立った。** 理由はソースにある——`node_modules/@informalsystems/quint/dist/src/tlc.js` の 120〜133 行が
`java … -cp <jar> tlc2.TLC -deadlock -workers … -metadir <tmp> <module>.tla` を固定の引数で起動している（`-deadlock` を外す引数は `quint verify --help` に無い）。
**さらに、起動する TLC は手元の `tla2tools.jar` ではなく、`~/.quint/apalache-dist-0.62.4/apalache/lib/apalache.jar` に入っている TLC だった**
（出力の `TLC2 Version 2026.11.14.050951` と、標準モジュールを `apalache.jar!/tla2sany/StandardModules/` から読んだ行）。
**正本の `CLAUDE.md` の `TLC の呼び方:` は、この経路では使われない。** 不変条件の違反は Quint 経由の TLC でも出た（`broken` で `Invariant q_inv is violated.`）。

### A6: 採否

**採らない（TLC を Quint に置き換えない。Quint を Formal Checker の道具にも足さない）。** 理由（上の結果だけから）:

1. **期待した利点（反例の書き写しを機械にする）は、Quint に乗らなくても取れる形だった。** 決まった変換にできたのは `calls`・`steps` で、
   その決め方（`pc` の差）は TLC の反例にも当てはまる。Quint だけが持つ利点は「行為の名前つきの ITF」だが、それは網羅しない `quint run --mbt` だけにある。
   Apalache の ITF は TLC の反例と同じく状態の並びで、違いは JSON か TLA+ の値の文字列か（読みやすさ）だけ。
2. **Quint の 2 つの検査の経路は、どちらも今の TLC より黙って弱い。** Apalache は深さが足りないと壊れたモデルに rc=0 の「違反なし」を返す（A3）。
   Quint 経由の TLC は行き詰まりを見ず、手元の TLC と違う TLC を、`TLC の呼び方:` を通らずに起動する（A5）。
   どちらも Formal Checker の「反例なしは陽性対照で空振りでないことを示す」で一部は拾えるが、行き詰まりは陽性対照の 2 つ（到達・壊した版）では拾えない。
3. **入れるものが増える**（Node＋npm の包・Apalache の 190 MB・サーバーのポート）のに、TLC の前提（`check-tlc.py`・autopilot の点検）は残る。

**保留にしたもの**: TLC の反例（状態の並び）を `pc` の差で `calls`・`steps` に変換すること自体には値がある（`spec-ir.md` の「トレースのケース」の書き写しが今は手）。
ただし TLC の反例の値を読む手段（`-tool` の出力・`-generateSpecTE`）を試していないので、この周では起票の根拠にしない——起票するかは手順 8 で人間に訊く。

**一般化の限界（未証明）**: 標本は合成のモデル 1 つ（状態 9 つ・反例 4 遷移）。整数の範囲が広く TLC で状態が爆発するモデルでの Apalache の利点（記事が挙げるもの）は、この周では測っていない。

## 関門の進捗（再開点）

- 手順 4: 実験と記録を済ませた（2026-11-14）

- この周の起票: 0 件（保留にした「TLC の反例を `calls`・`steps` に変換する」は、手で書き写していることが失敗として示せない——手順 6 の起票の条件 (a) を満たさない）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| R21-10 の実物のモデルを使わない | 採った（合成で代える） | 実物は他リポジトリにあり残っていない（`docs/plans/issue-923.md`）。#923 の試料も消えている |
| 変換のスクリプトを `scripts/` に置かない | 採った | 採否を決める前に歯止め・テストを足すと、採らなかったときに残骸になる |

## 付録（モデルと変換の全文。走らせたファイルそのもの）

### 付録 A: VersionWrite.tla（TLC）

```tla
---- MODULE VersionWrite ----
\* R21-10 と同じ形の合成のモデル（#1015）。書き手は版を排他の外の定数（起動時に決まる）から取り、
\* デプロイで旧（版 1）と新（版 2）の書き手が重なる。行への読み書きは排他（lock）で守る。
EXTENDS Naturals
CONSTANTS Guard   \* TRUE = 版の順序の守りあり（直した版）、FALSE = 守りなし（壊れた版）
Writers == {"old", "new"}
Ver == [w \in Writers |-> IF w = "old" THEN 1 ELSE 2]
VARIABLES rowVer, maxWritten, lock, pc, seen, result
vars == <<rowVer, maxWritten, lock, pc, seen, result>>

Init == /\ rowVer = 0 /\ maxWritten = 0 /\ lock = "none"
        /\ pc = [w \in Writers |-> "read"]
        /\ seen = [w \in Writers |-> 0]
        /\ result = [w \in Writers |-> "none"]

Read(w) == /\ pc[w] = "read" /\ lock = "none"
           /\ lock' = w /\ seen' = [seen EXCEPT ![w] = rowVer]
           /\ pc' = [pc EXCEPT ![w] = "write"]
           /\ UNCHANGED <<rowVer, maxWritten, result>>

Write(w) == /\ pc[w] = "write"
            /\ IF Guard /\ Ver[w] < seen[w]
                 THEN /\ result' = [result EXCEPT ![w] = "stale"]
                      /\ UNCHANGED <<rowVer, maxWritten>>
                 ELSE /\ rowVer' = Ver[w]
                      /\ maxWritten' = IF Ver[w] > maxWritten THEN Ver[w] ELSE maxWritten
                      /\ result' = [result EXCEPT ![w] = "ok"]
            /\ lock' = "none" /\ pc' = [pc EXCEPT ![w] = "done"]
            /\ UNCHANGED seen

Done == /\ \A w \in Writers : pc[w] = "done"
        /\ UNCHANGED vars

Next == (\E w \in Writers : Read(w) \/ Write(w)) \/ Done

NoRollback == rowVer = maxWritten
\* 到達の確かめ: 全員が終わり新しい版が残る状態に到達できるなら、この不変条件は破れる
NotReachedGood == ~((\A w \in Writers : pc[w] = "done") /\ rowVer = 2)
====
```

### 付録 B: versionWrite.qnt（Quint）

```
// R21-10 と同じ形の合成のモデル（#1015）。VersionWrite.tla の書き直し。
// 書き手は版を排他の外の定数（起動時に決まる）から取り、デプロイで旧（版 1）と新（版 2）の書き手が重なる。
module versionWrite {
  const GUARD: bool   // true = 版の順序の守りあり（直した版）、false = 守りなし（壊れた版）

  type Phase = Read | Write | Done
  pure val WRITERS = Set("old", "new")
  pure def ver(w: str): int = if (w == "old") 1 else 2

  var rowVer: int
  var maxWritten: int
  var lock: str
  var pc: str -> Phase
  var seen: str -> int
  var result: str -> str

  action init = all {
    rowVer' = 0,
    maxWritten' = 0,
    lock' = "none",
    pc' = WRITERS.mapBy(_ => Read),
    seen' = WRITERS.mapBy(_ => 0),
    result' = WRITERS.mapBy(_ => "none"),
  }

  action read(w: str): bool = all {
    pc.get(w) == Read,
    lock == "none",
    lock' = w,
    seen' = seen.set(w, rowVer),
    pc' = pc.set(w, Write),
    rowVer' = rowVer,
    maxWritten' = maxWritten,
    result' = result,
  }

  action write(w: str): bool = all {
    pc.get(w) == Write,
    if (GUARD and ver(w) < seen.get(w)) all {
      result' = result.set(w, "stale"),
      rowVer' = rowVer,
      maxWritten' = maxWritten,
    } else all {
      rowVer' = ver(w),
      maxWritten' = if (ver(w) > maxWritten) ver(w) else maxWritten,
      result' = result.set(w, "ok"),
    },
    lock' = "none",
    pc' = pc.set(w, Done),
    seen' = seen,
  }

  action done = all {
    WRITERS.forall(w => pc.get(w) == Done),
    rowVer' = rowVer, maxWritten' = maxWritten, lock' = lock,
    pc' = pc, seen' = seen, result' = result,
  }

  action step = any {
    nondet w = oneOf(WRITERS)
    any { read(w), write(w) },
    done,
  }

  // デッドロックの確かめ用: 全員が終わった後に何もしない done を外した step（終わった状態で行き詰まる）
  action stepNoDone = {
    nondet w = oneOf(WRITERS)
    any { read(w), write(w) }
  }

  val noRollback = rowVer == maxWritten
  // 到達の確かめ: 全員が終わり新しい版が残る状態に到達できるなら、この不変条件は破れる
  val notReachedGood = not(WRITERS.forall(w => pc.get(w) == Done) and rowVer == 2)
}

module broken { import versionWrite(GUARD = false).* }
module fixed { import versionWrite(GUARD = true).* }
```

### 付録 C: itf_to_trace.py（ITF → trace ケースの `calls`・`steps`）

```python
"""ITF（Quint・Apalache の反例）から spec-ir のトレースのケースの `calls`・`steps` を作る（#1015 の実験）。

使い方: python3 itf_to_trace.py <ITF> <対応表の JSON>

対応表（モデルと実装の入口の対応。ITF には無いので人が書く）:
  {"pc": "pc",                                  # 呼び出し → 段の変数の名前（モジュールの接頭辞を除く）
   "calls": {"old": {"name": "old_writer", "operation": "write_row", "input": {...}}, ...},
   "phases": {"Read": "read", "Write": "write"},  # 遷移の前の段 → トレースの段の名前
   "rest": {"setup": [...], "outcomes": [...], "after": [...]}}   # 期待（直した仕様から）。写すだけ

段の決め方は 2 つ:
- ITF に `mbt::actionTaken` と `mbt::nondetPicks` がある（`quint run --mbt`）なら、行為の名前と選ばれた呼び出しから決める。
  行為の名前は `phases` の値と同じ（小文字）であること。
- 無い（`quint verify` = Apalache の ITF）なら、隣り合う状態で `pc` が変わった呼び出しをちょうど 1 つ探し、変わる前の段を `phases` で引く。
  0 なら止まっている遷移（全員が終わった後）として飛ばし、2 以上なら決められないので止める。
"""
import json
import sys


def strip(name: str) -> str:
    return name.rsplit("::", 1)[-1]


def state_vars(state: dict) -> dict:
    return {strip(k): v for k, v in state.items() if not k.startswith("#") and not k.startswith("mbt::")}


def tag(value) -> str:
    return value["tag"] if isinstance(value, dict) and "tag" in value else value


def pc_of(state: dict, pc_name: str) -> dict:
    return {who: tag(phase) for who, phase in state_vars(state)[pc_name]["#map"]}


def steps_from_mbt(states: list, table: dict) -> list:
    steps = []
    for state in states[1:]:
        action = state["mbt::actionTaken"]
        picks = state["mbt::nondetPicks"]
        pick = next((p["value"] for p in picks.values() if p.get("tag") == "Some"), None)
        if pick is None:
            continue  # 引数の無い行為（全員が終わった後の done など）
        steps.append([table["calls"][pick]["name"], action])
    return steps


def steps_from_states(states: list, table: dict) -> list:
    steps = []
    for before, after in zip(states, states[1:]):
        a, b = pc_of(before, table["pc"]), pc_of(after, table["pc"])
        moved = [who for who in a if a[who] != b[who]]
        if not moved:
            continue
        if len(moved) > 1:
            raise SystemExit(f"1 つの遷移で 2 つ以上の呼び出しが動いた: {moved}（段を決められない）")
        who = moved[0]
        steps.append([table["calls"][who]["name"], table["phases"][a[who]]])
    return steps


def convert(itf: dict, table: dict) -> dict:
    states = itf["states"]
    mbt = "mbt::actionTaken" in states[0]
    steps = steps_from_mbt(states, table) if mbt else steps_from_states(states, table)
    calls = {c["name"]: {"operation": c["operation"], "input": c["input"]} for c in table["calls"].values()}
    trace = {"formal": table["formal"], "calls": calls, "steps": steps}
    trace.update(table.get("rest", {}))
    return {"mode": "mbt" if mbt else "states", "trace": trace}


if __name__ == "__main__":
    itf = json.load(open(sys.argv[1]))
    table = json.load(open(sys.argv[2]))
    print(json.dumps(convert(itf, table), ensure_ascii=False))
```

### 付録 D: 対応表（table.json）

```json
{"formal": "version-write",
 "pc": "pc",
 "calls": {"old": {"name": "old_writer", "operation": "write_row", "input": {"key": "k", "ver": 1}},
           "new": {"name": "new_writer", "operation": "write_row", "input": {"key": "k", "ver": 2}}},
 "phases": {"Read": "read", "Write": "write"},
 "rest": {"setup": [{"operation": "set_row", "input": {"key": "k", "ver": 0}, "expected": {"ver": 0}}],
          "outcomes": [{"ok": true}, {"error": "STALE_VERSION"}],
          "after": [{"operation": "get_row", "input": {"key": "k"}, "expected": {"ver": 2}}]}}
```

### 付録 E: check_with_scaffold.py（本物の `scaffold.py` の `check_trace` に当てる）

```python
"""変換の出力を、本物の scaffold.py の check_trace に当てる（#1015 の実験）。

使い方: python3 check_with_scaffold.py <scaffold.py のあるディレクトリ> <変換の出力の JSON>...
入口（write_row・set_row・get_row）は下の OPS。形式検査の記録（spec/formal/version-write/README.md）は一時ディレクトリに置く。
陽性対照: 段の呼び出しの名前を calls に無いものに変えた版が赤になることも見る。
"""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location("scaffold", Path(sys.argv[1]) / "scaffold.py")
scaffold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaffold)

OPS = {
    "write_row": {"id": "write_row", "input": {"key": {"type": "string"}, "ver": {"type": "integer"}},
                  "output": {"ok": {"type": "boolean"}}, "errors": ["STALE_VERSION"]},
    "set_row": {"id": "set_row", "input": {"key": {"type": "string"}, "ver": {"type": "integer"}},
                "output": {"ver": {"type": "integer"}}, "errors": []},
    "get_row": {"id": "get_row", "input": {"key": {"type": "string"}},
                "output": {"ver": {"type": "integer"}}, "errors": []},
}

with tempfile.TemporaryDirectory() as tmp:
    whole = Path(tmp)
    record = whole / "spec/formal/version-write/README.md"
    record.parent.mkdir(parents=True)
    record.write_text("# version-write\n")
    status = 0
    for path in sys.argv[2:]:
        out = json.load(open(path))
        problems = scaffold.check_trace("trace", out["trace"], OPS, whole)
        print(f"{path} ({out['mode']}): steps={out['trace']['steps']}")
        print(f"  check_trace: {'通った' if not problems else problems}")
        status |= bool(problems)
        broken = copy.deepcopy(out["trace"])
        broken["steps"][0][0] = "nobody"
        control = scaffold.check_trace("trace", broken, OPS, whole)
        print(f"  陽性対照（段の呼び出しを calls に無い名前にした）: {'赤' if control else '緑（対照が効いていない）'}")
        status |= not control
    sys.exit(status)
```
