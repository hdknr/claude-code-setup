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
  npm は `protobufjs` の postinstall について警告を出した（保存した npm の出力の `npm warn install-scripts 1 package has install scripts not yet covered by allowScripts:`・`protobufjs@7.6.6 (postinstall: node scripts/postinstall)`）。
  postinstall が実際に走らなかったかは確かめていない——型検査・Apalache・TLC の経路は動いた。
- **`~/.quint` は周を始める前から在った**（`apalache-dist-0.62.4`・`rust-evaluator-v0.7.1`。日付は 2026-11-09——記事を書いたときの実験の残り。190 MB）。
  **`find ~/.quint -newerct "2026-11-14 00:00"` と `-newerBt`（作成時刻）はどちらも 0 件**（種別を絞らない。この周の実行はすべて 2026-11-14 の 14 時以降）——この周の実行は `~/.quint` に書いていない（初回の取得の挙動はこの周では観測していない）。
  **1 パス目の根拠にした `-newermt`（更新時刻）は判別しない**（2 パス目の `/code-review` の指摘 2）——展開したファイルはアーカイブの時刻を持つ
  （`apalache.jar` は更新時刻 2026-10-12・変更時刻 2026-11-09）ので、この周に取りに行って展開していても `-newermt` は 0 件を返した。
  （`run-deadlock.sh` の前後の `ls ~/.quint` も比べたが、前の一覧を取ったのは A2・A3 を走らせた後なので、周の全体の根拠にはならない——根拠は上の `find`。）
- `quint verify` は Apalache をサーバー（`localhost:8822`）として起こす。走り終えた後に `apalache` のプロセスは残っていなかった（`ps`）。
  `--backend=tlc` が `$TMPDIR` に作る `quint-tlc-*` も残っていなかった。
- **ほかに書かれたもの**（2 パス目の `/code-review` の指摘 5）: `quint verify` は走らせた cwd に `_apalache-out/server/<時刻>/`（反例の `.tla`・`.itf.json`・`detailed.log`・`log0.smt`）を残す——
  メインの作業ツリーで走らせれば追跡されないディレクトリが残る。`npm install` はホームの下に `~/.npm/_logs/2026-11-14T05_06_09_226Z-debug-0.log` とキャッシュの索引を書いた
  （キャッシュの索引のうち 2026-11-14 に作られたものは 79 件——2 パス目の前に入れ直した分を含み、分けていない）。
- Apalache の出力には毎回 protobuf の脆弱性の警告（`makeExtensionsImmutable should not be called from protobuf gencode`）が出る。

### A1: TLC（合成のモデル。付録 A）

構成は書き手 2 つ（旧＝版 1・新＝版 2。版は定数）・行 1 つ・排他 1 つ。性質 `NoRollback == rowVer = maxWritten`（書いた最大の版より古い版が残らない）。
`Guard` が版の順序の守り（排他の中で読んだ版より古い版は書かずに `stale`）。

| モデル | 不変条件 | 結果（判別する行） |
| --- | --- | --- |
| 守りなし（壊れた版） | `NoRollback` | `Error: Invariant NoRollback is violated.`（深さ 5 の状態 = 4 遷移: 新が読む→新が書く→旧が読む→旧が書く。最後の `rowVer = 1`・`maxWritten = 2`） |
| 守りなし | `NotReachedGood`（到達の確かめ） | `Error: Invariant NotReachedGood is violated.`——全員が終わり版 2 が残る状態に到達できる |
| 守りあり（直した版） | `NoRollback` | `Model checking completed. No error has been found.`（`9 distinct states found, 0 states left on queue`——全探索して閉じた） |
| 守りあり | `NotReachedGood` | `Error: Invariant NotReachedGood is violated.`——直した版でも正常な状態に到達できる（空振りでない） |

**手元の TLC 2.19 の反例は行為の名前（`<Read line 16 …>`）を出すが、行為の引数（どの書き手か）は出さない**——どの書き手の段かは状態の `pc` の差から読む。
**`apalache.jar` に入っている TLC（Quint の `--backend=tlc` が起動するもの。A5）は引数も出す**——`out-tlc-broken.txt` の `State 2: <broken_versionWrite_read("new") …>`。
（1 パス目の `/code-review` の指摘 1。同じ jar の TLC に付録 A の `VersionWrite.tla`（守りなし）を直に当てても、`State 2: <Read("new") …>`・`State 3: <Write("new") …>`・`State 4: <Read("old") …>`・`State 5: <Write("old") …>`（rc=12。`run-jar-tlc.sh`）。）
**どちらの版の TLC が引数を出すようになったかは確かめていない**（その TLC の版は出力から決められない——A5）。

### A2: Quint ＋ Apalache（付録 B。A1 と同じ構成・同じ性質）

`quint typecheck` は通った（rc=0）。`quint verify --max-steps=6`（**判定は結果の行で決める。rc は添えるだけ**——rc=1 はサーバーの起動の失敗でも出る。A3）:

| モジュール | 不変条件 | 結果 |
| --- | --- | --- |
| `broken` | `noRollback` | `Found 1 error(s)`（rc=1）・ITF を書いた（下の A4 で変換した反例はこれ。段の順は TLC と同じ） |
| `broken` | `notReachedGood` | `Found 1 error(s)`（rc=1）——到達できる |
| `fixed` | `noRollback` | `The outcome is: NoError`・`[ok] No violation found`（rc=0） |
| `fixed` | `notReachedGood` | `Found 1 error(s)`（rc=1）——直した版でも到達できる |

この 1 つのモデルでは、**Apalache は TLC と同じ反例を同じ深さで見つけ、陽性対照の 2 つも通った**。

### A3: Apalache の深さの上限の実害

`broken`・`noRollback` で `--max-steps` を変えた:

| `--max-steps` | 結果 |
| --- | --- |
| 1・2・3 | **rc=0・`[ok] No violation found`** |
| 4 | rc=1・`[violation] Found an issue` |

反例は 4 遷移なので、**上限が 3 以下だと、壊れたモデルに「違反なし」を rc=0 で返す**（`--max-steps` の既定は 10）。
出力は `[ok] No violation found` の直後に `You may increase --max-steps.` の 1 行を出す（`out-steps-1〜3.txt`・`out-fixed-noRollback.txt`。1 パス目の `/code-review` の指摘 2）——
**深さが足りるかは、出力からも rc からも決まらない**（足りていても同じ 1 行が出る）。
TLC は幅優先の全探索で、直した版を `9 distinct states found, 0 states left on queue` で閉じた（A1）——深さの上限で打ち切る形は無い。

**同じ深さで 4 通りを並べた**（A2×A3。1 パス目の Verifier の反証 2 への対応。`run-depth.sh`）:

| `--max-steps` | `broken`・`noRollback` | `broken`・`notReachedGood` | `fixed`・`noRollback` | `fixed`・`notReachedGood`（到達） |
| --- | --- | --- | --- | --- |
| 3 | rc=0・違反なし | rc=0・違反なし | rc=0・違反なし | **rc=0・違反なし（到達できない＝陽性対照が空振り）** |
| 4 | rc=1・`Found 1 error` | rc=1・`Found 1 error` | rc=0・`No violation found` | rc=1・`Found 1 error`（到達できる） |

**深さ 4 で、壊れた版は違反・直した版は違反なし・直した版は到達できる、の対が成り立つ。** 深さ 3 では到達の確かめも空振りになる——
**到達の確かめを同じ深さで取れば、この模型では深さの不足は陽性対照の空振りとして見える**（Formal Checker の「空振りを疑う」の 1 で拾える）。
ただし到達の確かめが見るのは「指定した正常な状態に届くか」で、**反例がその状態より深いときは、到達できても深さが足りないことがある**——この模型では正常な状態と反例が同じ 4 遷移だったので、それは測れていない。

**rc=1 は「違反あり」だけではない。** 関門の Verifier・`/code-review` が同じ時刻に `quint verify` を走らせた回は、2 本が
`Error while starting Apalache server: Failed to bind to address 0.0.0.0/0.0.0.0:8822: Address already in use` で、**結果の行を出さずに rc=1** で終わった。
**rc だけで判定すると「違反あり」と読む。** 結果の行（`No violation found`・`Found … error`・`Found a deadlock`）が無い回は判定できないと読み、
`run-depth.sh` は結果の行が無ければ「判定できない」と出す形で 8 通りを走らせ直した（上の表はその値）。**同じ PC で 2 つの検査を既定のまま並べると、ポート 8822 を取り合う**——cruise の並行する周や、関門と並べた検査で起きる形である。
**ただし `quint verify` には `--server-endpoint`（既定 `localhost:8822`）があり**（`quint verify --help`。2 パス目の `/code-review` の指摘 4）、検査ごとに違うポートを渡せば避けられる見込みがある——**この周では試していない。**

### A4: ITF から trace ケースへの変換

- **Apalache（`quint verify --out-itf`）の ITF は状態の並びだけで、行為の名前も引数も持たない**（`vars` は 6 つの状態変数だけ）。
  `quint verify` には `--mbt` が無い（`quint verify --help`）。
- **`quint run --mbt`（シミュレータ。網羅しない）の ITF は、状態ごとに `mbt::actionTaken`（`read`・`write`）と `mbt::nondetPicks`（`w` = `new`・`old`）を持つ**
  （種 `0x1`・`--max-samples=10000` で反例が出た）。ただし `vars` に `mbt::actionTaken`・`mbt::nondetPicks` が 2 回ずつ載っていた。
- 変換（付録 C）は 2 つの形を持つ: `mbt` の ITF なら行為の名前と選ばれた呼び出しから、状態だけの ITF なら隣の状態で `pc` が変わった呼び出しを 1 つ探して段を決める。
  2 本の ITF のどちらからも同じ `steps` が出た: `[["new_writer","read"],["new_writer","write"],["old_writer","read"],["old_writer","write"]]`。
- **変換の出力は、本物の `plugins/spec-loop/scripts/scaffold.py` の `check_trace` を通った**（付録 E。入口 3 つを置き、`spec/formal/version-write/README.md` を一時ディレクトリに置いた）。
  陽性対照として段の呼び出しの名前を `calls` に無いものに変えた版は赤（`check_trace` が問題を返す）だった。
  **ただし `check_trace` は形だけを見て、段の順の正しさは見ない**（1 パス目の `/code-review` の指摘 3。旧が先の順・書くが先の順に変えても通る）。
- **段の順の誤りのうち、下の 2 つの変異は生成した Red テストで判別した**（付録 G）。変換の出力から本物の `scaffold.py` の `red_test` で Red テストを作り、
  守りの無い実装（モデルの `broken`）と守りのある実装（`fixed`）に当てた。どちらも 1 つの排他の中で読むと書くをまとめ、その直前に `checkpoint("read")`・`checkpoint("write")` を続けて呼ぶ（`spec-ir.md` の「実装に求める口」）:

  | 段の順 | 実装 | 結果 |
  | --- | --- | --- |
  | 変換した順（新が先） | 守りなし | **赤**——`old_writer が {'ok': True} を返した（期待の残り [{'error': 'STALE_VERSION'}]。トレースの 4/4 段まで順に進めた）` |
  | 変換した順 | 守りあり | **緑**（`OK`） |
  | 旧が先の順（変異） | 守りあり | **赤**——期待（直した仕様のこの順での結果）と合わない |
  | 書くが先の順（変異） | 守りあり | **赤**——`段 write の前で checkpoint を呼ばずに段 read に来た` |

  **試した 2 つの変異は正しい実装まで赤にし、変換した順だけが「守りなしを赤・守りありを緑」に分けた。**
  **ただし段の順の誤りを全部判別するわけではない**（2 パス目の `/code-review` の指摘 1）——モデルでは到達できない交互の順
  （`[new_writer, read]`・`[old_writer, read]`・`[new_writer, write]`・`[old_writer, write]`。2 つの書き手が同時に排他を持つ）を変換が出しても、
  **守りなしは赤・守りありは緑（`OK`）で、変換した順と同じに分かれた**（2 パス目に走らせた）。どちらの実装も `checkpoint("read")` と `checkpoint("write")` を
  1 つの操作の直前に続けて呼ぶので、読む段の位置が観測されない。**読む段の位置の誤りは、この Red テストでは判別できない。**
- **ITF から決まった変換で出たのは `steps` だけ**（1 パス目の `/code-review` の指摘 4。`calls` は付録 D の対応表をそのまま写している）。次は ITF に無いので人が書く:
  - モデルの書き手と実装の入口・入力の対応（`old` → `write_row {"key": "k", "ver": 1}`）
  - モデルの段（`Read`・`Write`）とトレースの段の名前の対応
  - `setup`・`outcomes`・`after`——**期待は直した仕様の結果で、反例（壊れた版）の最後の状態ではない**ので、反例からは出ない
- 状態から段を決める形は、**モデルが呼び出し → 段の写像（`pc`）を持ち、1 遷移で動く呼び出しが 1 つ**であることに乗っている。
- **同じ決め方を TLC の反例（テキスト）に当てて確かめた**（1 パス目の Verifier の反証 1 への対応。付録 F）。TLC の出力の `/\ pc = [old |-> "read", new |-> "write"]` の行だけを
  正規表現で読み（TLA+ の値の構文は解かない）、`pc` が変わった呼び出しから段を決めた。**出た `steps` は Apalache の ITF から出したものと同じ**（上の Red テストで判別した順）で、本物の `scaffold.py` の `check_trace` も通った。 ただしこの読み方は `pc` の値が文字列から文字列への関数の形であることに乗っている
  ——値がレコードや入れ子になると、正規表現では読めない（そこでは TLA+ の値の構文を解く必要がある。JSON の ITF なら要らない）。
  手元の TLC 2.19 は `-dumpTrace json` を持たなかった（`Error: unrecognized option: -dumpTrace`）。`-tool`（機械向けの出力）と `-generateSpecTE` は試していない。
- **`apalache.jar` に入っている TLC は `-dumpTrace json` を持ち、反例を JSON で出す**（2 パス目の Verifier の反証 1。付録 A の守りなしに当てた）——
  段ごとに行為の名前と引数（`"name":"Read",…,"context":{"w":"new"},"parameters":["w"]`）と前後の状態（`"pc":{"old":"read","new":"write"}` など）を持つ。
  **つまり網羅する検査器（TLC）の反例から、行為の名前・引数・状態を JSON で取れる道が手元にあった**——1 パス目の記録はこれを試さずに「確かめていない」としていた。
- **Apalache（`quint verify`）も、ITF とは別に書く反例の `.tla`（`_apalache-out/server/<時刻>/violation1.tla`）に、各状態を起こした遷移の番号を残す**
  （`(* State1 [_transition(1)] *)`・`State2 [_transition(3)]`・…。2 パス目の `/code-review` の指摘 9）——番号から行為は決まるが、引数（どの書き手か）は持たない。
  上の「ITF は行為の名前も引数も持たない」は ITF について言ったもので、Apalache の出力の全部についてではない。

### A5: `--backend=tlc` とデッドロック

全員が終わった後の `done` を外した step（`stepNoDone`。終わった状態で行き詰まる）を当てた。
**モジュールは `fixed`**（1 パス目の記録は名指ししておらず、2 パス目の `/code-review` が `fixed` で同じ行を再現した（指摘 7）。
`broken` に `--invariant=noRollback` で当てると、深さ 4 の不変条件の違反が先に出て `The outcome is: Error` になり、行き詰まりは出ない）:

| 検査器 | 結果 |
| --- | --- |
| Apalache（`quint verify --main=fixed --step=stepNoDone`） | rc=1・`Found a deadlock.`・`The outcome is: Deadlock` |
| **Quint 経由の TLC（`--main=fixed --backend=tlc`）** | **rc=0・`Model checking completed. No error has been found.`・`[ok] No violation found`** |
| 素の TLC（同じ形の `NoDone.tla`・既定のオプション） | rc=11・`Error: Deadlock reached.`（対照: 行き詰まりは本物） |
| 素の TLC（`-deadlock`） | rc=0・`No error has been found.` |

**記事の主張は Quint 0.33.1 で成り立った。** 理由はソースにある——`node_modules/@informalsystems/quint/dist/src/tlc.js` の 120〜133 行が
`java … -cp <jar> tlc2.TLC -deadlock -workers … -metadir <tmp> <module>.tla` を固定の引数で起動している（`-deadlock` を外す引数は `quint verify --help` に無い）。
**さらに、起動する TLC は手元の `tla2tools.jar` ではなく、`~/.quint/apalache-dist-0.62.4/apalache/lib/apalache.jar` に入っている TLC だった**
（標準モジュールを `apalache.jar!/tla2sany/StandardModules/` から読んだ行。出力の `TLC2 Version 2026.11.14.050951` は走らせた時刻（UTC）で、版の証拠にならない——1 パス目の `/code-review` の指摘 9）。
**正本の `CLAUDE.md` の `TLC の呼び方:` は、この経路では使われない。** 不変条件の違反は Quint 経由の TLC でも出た（`broken` で `Invariant q_inv is violated.`）。

### A6: 採否

**採らない（TLC を Quint に置き換えない。Quint を Formal Checker の道具にも足さない）。** 理由（上の結果だけから）:

1. **期待した利点（反例の書き写しを機械にする）は、Quint に乗らなくても取れた。** 反例から決まった変換で出たのは `steps` で、
   その決め方（`pc` の差）を手元の TLC 2.19 の反例のテキストに当てても、同じ `steps` が出た（A4。試した 2 つの順の変異は Red テストで判別した——読む段の位置の誤りは判別しない）。
   行為の名前と引数を持つ反例は、Quint では網羅しない `quint run --mbt` の ITF にしか無かった（Apalache の反例の `.tla` は遷移の番号だけ。A4）。
   **一方 `apalache.jar` の TLC（網羅する）は、`-dumpTrace json` で行為の名前・引数・状態を JSON で出す**（A4。2 パス目の Verifier の反証 1）——
   **JSON の反例は Quint に乗らなくても TLC から取れる**ので、入れ子の値の読み方も Quint の利点にならない。
2. **この模型では、Quint の 2 つの検査の経路はどちらも今の TLC より弱かった。** Apalache は深さが足りないと壊れたモデルに rc=0 の「違反なし」を返し、足りるかは出力からも決まらない（A3。`You may increase --max-steps.` は足りていても出る）。
   ポートを既定のまま並べると結果を出さずに rc=1 を返す（A3。`--server-endpoint` で避けられる見込みは試していない）。Quint 経由の TLC は行き詰まりを見ず、手元の TLC と違う TLC を、`TLC の呼び方:` を通らずに起動する（A5）。
   深さの不足はこの模型では同じ深さの到達の確かめで拾えた（A3）が、行き詰まりは陽性対照の 2 つ（到達・壊した版）では拾えない。
   **「弱い」はこの模型（状態 9 つの有限のモデル）に限る**（2 パス目の `/code-review` の指摘 3）——TLC が深さで打ち切らないのは状態空間が小さく有限だからで、
   状態が爆発するモデルでは TLC も終わらない。Apalache の深さに依らない検査（`quint verify --inductive-invariant`）は試していない。
3. **入れるものが増える**（Node＋npm の包・Apalache の 190 MB・サーバーのポート・cwd に残る `_apalache-out/`。A7）のに、TLC の前提（`check-tlc.py`・autopilot の点検）は残る。

**保留にしたもの**: TLC の反例から `steps` を変換すること自体には値がある（`spec-ir.md` の「トレースのケース」の書き写しが今は手）。
`apalache.jar` の TLC の `-dumpTrace json` なら行為の名前と引数で段を読める（A4）が、正本の `TLC の呼び方:` の TLC（手元は 2.19）はこれを持たず、
TLC の版を上げる判断と JSON からの変換はこの周で書いていないので、この周では起票の根拠にしない。

**一般化の限界（未証明）**: 標本は合成のモデル 1 つ（直した版の状態 9 つ・反例 4 遷移）。整数の範囲が広く TLC で状態が爆発するモデルでの Apalache の利点（記事が挙げるもの）は、この周では測っていない。

## 関門の進捗（再開点）

- 手順 4: 実験と記録を済ませた（2026-11-14）。割り目: 「このまま続ける」（`AskUserQuestion` の回答・2026-11-14）
- 1 パス目の指摘対応の起点: `fe7b3e1`（1 パス目の関門に渡した時点の HEAD）
- 1 パス目: Verifier（sonnet）反証 3 件・`/code-review`（high）指摘 10 件。採否は下の表——直す 12 件・残課題 1 件。手順 4 への差し戻し: あり（V1〜V3・C1〜C9 を直した）
- 2 パス目の前の割り目: 「ここで割る」（`AskUserQuestion` の回答・2026-11-14）。2026-11-14 に新しいセッションで再開した（前のセッションの scratchpad は消えていたので、付録 A〜G を抜き出し、Quint 0.33.1 を新しい scratchpad に入れ直して関門に渡した）
- 2 パス目（base は周の base `3aa4f0b` のまま。関門は 1 つずつ走らせた）: 手順 5 の当て直し（Verifier・sonnet）反証 2 件・`/code-review`（high）2 パス目 指摘 10 件。
  採否は下の「2 パス目の指摘の採否」——直す 10 件・残課題 2 件。振る舞いについての指摘は著者が走らせて確かめた（P1・P3・P4・P6・P7・P9 など）
- 2 パス目の指摘対応の起点（狭いパスの起点）: `e46576b`（再開点を書いたコミット。2 パス目の指摘対応はこの後から）
- 狭いパス: 通した。差分は `e46576b`（起点）→ `50b885e`（終点）。Verifier（sonnet）反証 1 件・注意 2 件（下の「狭いパスの指摘の採否」）。直した 10 行のうち 9 行は事実と一致。素通りした変異は交互の順×守りあり（P3 が認めた素通り）。
  N1 は A7 を破るので「満たしていない受入基準」として PR コメントで名指しする
- `check-all.py`: `fe7b3e1` の時点でバックグラウンドで起動した結果は前のセッションと一緒に消えた。再開後（`6d78b9d`）にもう 1 度起動した。PR の前に指摘対応の後で回す
- 関門で使った検査の注意: 2 つの関門と著者が同時に `quint verify` を走らせるとポート 8822 を取り合う——2 パス目は関門を 1 つずつ走らせるか、関門に `quint verify` を走らせ直さないよう頼む
- 交絡を潰した手順: 到達の確かめ（`NotReachedGood`）と壊した版（`Guard = FALSE`）を TLC・Apalache の両方で取った。
  A5 は行き詰まりが本物であることを素の TLC（既定のオプション）で示した。A3 の「違反なし」は深さで変わることを 1〜4 で並べた

- この周の起票: 1 件（#1020「TLC の反例の JSON から trace ケースの steps を作る」。起票の条件 (a) は満たさないが、手順 8 で利用者が起票を選んだ・2026-11-14）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| R21-10 の実物のモデルを使わない | 採った（合成で代える） | 実物は他リポジトリにあり残っていない（`docs/plans/issue-923.md`）。#923 の試料も消えている |
| 変換のスクリプトを `scripts/` に置かない | 採った | 採否を決める前に歯止め・テストを足すと、採らなかったときに残骸になる |

### 1 パス目の指摘の採否（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | A4・A6「同じ決め方は TLC の反例にも当てはまる」が測っていない断定 | 示せる——変換を TLC のテキストに当てたものが付録に無かった | A4・A6 | 直す（付録 F で当てて同じ `steps`） |
| V2 | A2×A3 の対が最小の深さで取れていない | 示せる——深さ 4 の `fixed` の出力が無かった | 組み合わせ A2×A3 | 直す（`run-depth.sh` で 8 通り） |
| V3 | A7「何も取りに行っていない」の根拠が上の階層の `ls` だけ | 示せる——記録の根拠が `ls` の名前だけ | A7 | 直す（`find -newermt` の 0 件。protobufjs の行は保存した npm の出力から引用） |
| C1 | 「TLC は行為の引数を出さない」と A6 の理由 1 が、Quint が起動する TLC の出力と食い違う | 示せる——`out-tlc-broken.txt` の `read("new")`、`run-jar-tlc.sh` の `Read("new")` | A1・A6 | 直す（2.19 に限る記述にし、A6 の理由 1 を書き直した） |
| C2 | 「出力に深さの上限が出ない」が誤り（`You may increase --max-steps.` が出る） | 示せる——`out-steps-1〜3.txt` | A3・A6 | 直す |
| C3 | `check_trace` は段の順を見ないので、A4 の証拠が変換の正しさを判別しない | 示せる——順を変えても通る | A4 | 直す（付録 G の Red テストで判別した） |
| C4 | `calls` は対応表の写しで、ITF から出たのは `steps` だけ | 示せる——付録 C の `calls = {…table["calls"]…}` | A4・A6 | 直す |
| C5 | A2×A3 の対が無い（V2 と同じ） | 示せる | 組み合わせ A2×A3 | 直す（V2 と同じ対応） |
| C6 | A2・A3 が rc で判定しているが、rc=1 はサーバーの起動の失敗でも出る | 示せる——ポートの取り合いの `Address already in use` で rc=1 | A2・A3 | 直す（判定を結果の行にし、rc の曖昧さを A3 に書いた） |
| C7 | `~/.quint` の「前」の一覧が A2・A3 の後に取られている | 示せる——`quint-home-before.txt` は `run-deadlock.sh` が作った | A7 | 直す（根拠を `find -newermt` に替えた） |
| C8 | 「同じモデルを全探索して 9 状態で閉じる」の出典が直した版 | 示せる——`out-FALSE-NoRollback.txt` は `1 states left on queue` | A1・A3 | 直す |
| C9 | `TLC2 Version 2026.11.14.050951` は時刻で、版の証拠ではない | 示せる——走らせ直すと `…052122` | A5 | 直す |
| C10 | 変換は `pc` の変わらない遷移・引数の無い行為を黙って落とす。「決まった変換」はこの模型に限る | 示せない——この周の模型にそういう遷移は無い（仮定の模型での話） | 無し | 残課題（記録は `pc` の前提を書いてあり、採否は「採らない」なので変換を使う周で扱う） |

### 2 パス目の指摘の採否（直す線: 既定）

P1・P2 は Verifier、P3〜P12 は `/code-review`（P3 = 指摘 1 … P12 = 指摘 10）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| P1 | `apalache.jar` の TLC の `-dumpTrace json` を試さずに、A6 理由 1 が「JSON の利点は ITF の側」と書いている | 示せる——著者が残ったファイルで確かめた（`trace.json` に `"name":"Read"`・`"context":{"w":"new"}`・`"pc":{…}`） | A4・A6 | 直す（A4 に足し、A6 理由 1 と保留を書き直した。結論「採らない」は変わらない） |
| P2 | 付録が再現に要るファイルを欠く（`.cfg`・`NoDone.tla`・`run-*.sh`・`check_with_scaffold_ops.py`） | 示せる——付録 G は `check_with_scaffold_ops` を読み込むが付録に無い | A4 | 直す（付録の見出しの「走らせたファイルそのもの」を外し、載っていないものを名指しした。消えたファイルは作り直さない） |
| P3 | Red テストが段の順の誤りを判別すると言い過ぎ——到達できない交互の順は守りなし赤・守りあり緑に分かれる | 示せる——著者が走らせて `守りあり: 緑（OK）` | A4 | 直す（判別したのは試した 2 つの変異だけで、読む段の位置の誤りは判別しないと書いた） |
| P4 | A7 の根拠 `-newermt` は展開したファイルのアーカイブの時刻を見るので判別しない | 示せる——`stat`: `apalache.jar` は更新時刻 10-12・変更時刻 11-09 | A7 | 直す（`-newerct`・`-newerBt` の 0 件に替えた。結論は変わらない） |
| P5 | A6 理由 2「どちらの経路も TLC より弱い」は、有限の小さい模型で `--inductive-invariant` も試していないので判別しない | 示せる——`quint verify --help` に `--inductive-invariant`、A3 の模型は状態 9 つ | A6 | 直す（「この模型では」に限り、試していないことを書いた） |
| P6 | ポート 8822 の取り合いは `--server-endpoint` で避けられうるのに、Quint の弱さに数えている | 示せる——`quint verify --help` に `--server-endpoint` | A3・A6 | 直す（「既定のまま並べると」に限り、避けられる見込みは試していないと書いた） |
| P7 | A7 が `_apalache-out/`（cwd）と `~/.npm` のログ・キャッシュを記録していない | 示せる——`~/.npm/_logs/2026-11-14T05_06_09_226Z-debug-0.log`・関門の作業場所の `_apalache-out/server/` | A7 | 直す |
| P8 | 付録 F に付録 D の表を渡すと `KeyError: 'read'`。A4 は表を変えたことを書いていない | 示せる——著者が走らせて `KeyError: 'read'`、小文字の鍵の表で同じ `steps` | A4 | 直す（付録の冒頭に書いた） |
| P9 | A5 の表がモジュールを名指ししておらず、`broken` では行き詰まりではなく不変条件の違反が出る | 示せる——関門の `q-dl-apa.txt`（`broken`）は `The outcome is: Error`、`q-dl-apa-fixed.txt` は `Deadlock` | A5 | 直す（`--main=fixed` を書いた） |
| P10 | 付録 F の正規表現は単語でない `pc` の値（`in-flight`）と 1 変数のモデル（`/\ ` が無い）を黙って落とす | 示せない——この周の模型にそういう値は無い（関門が別の小さいモデルで確かめた形で、この周の主張の反例ではない） | 無し | 残課題（C10 と同じく、変換を使う周で扱う） |
| P11 | Apalache の反例の `.tla` は遷移の番号を持つのに、A4・A6 が見ていない | 示せる——`violation1.tla` の `State1 [_transition(1)]` | A4・A6 | 直す（A4 に足し、A6 理由 1 を書き直した） |
| P12 | 周のコミットに `Fixes #1015` が無い（リポジトリの `CLAUDE.md` の Git ワークフロー） | 示せる——`git log 3aa4f0b..HEAD` | 無し（記録の受入基準ではない） | 残課題（成果物の直しではない。PR の本文に `Fixes #1015` を書き、この指摘対応のコミットメッセージにも入れた） |

### 狭いパスの指摘の採否（直さない。人間が決める）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | A7 の `-newerBt`（作成時刻）の 0 件も判別しない——展開したファイルの作成時刻もアーカイブの時刻（`apalache.jar` は 10-12） | 示せる——`stat` の作成時刻 10-12（著者が 2 パス目の採否の前に取った出力にも `B=Oct 12` がある）。閾値 2026-11-01 で `newerct` 11 件・`newerBt` 3 件 | A7 | 人間が決める（満たしていない受入基準として PR コメントで名指しする。結論は `-newerct` の 0 件だけで支えられるが、その判別力の対照は取っていない） |
| N2 | A4 の「（上の Red テストで判別した順）」の括弧が、P3 で弱めた後も残っている | 示せない——直前の「読む段の位置は判別できない」と矛盾しない（読み違えの余地の指摘） | 無し | 人間が決める |
| N3 | P11 の「番号から行為は決まる」は `_transition(n)` と行為の対応の表が無く推定 | 示せない——対応を取っていない | 無し | 人間が決める |

注（Verifier の注意。反証ではない）: 直した版の到達の確かめが届いたのは旧が先の正常な順で、守りが `stale` を返す枝（新が先）に到達できるかは見ていない。

## 付録（モデルと変換の全文）

**載せたのは A〜G だけで、実験に使ったファイルの全部ではない**（2 パス目の Verifier の反証 2・`/code-review` の指摘 6）。
次は載っておらず、走らせた scratchpad はセッションと一緒に消えた——**ここからは再現できない**:
TLC の `.cfg`（`CONSTANT Guard`・`INIT Init`・`NEXT Next`・`INVARIANT …`）、A5 の `NoDone.tla`、`run-depth.sh`・`run-deadlock.sh`・`run-jar-tlc.sh`、
付録 G が読み込む `check_with_scaffold_ops.py`（付録 E の `OPS` を切り出したもの。2 パス目の関門が切り出して再現した）。
**付録 F に付録 D の表をそのまま渡すと `KeyError: 'read'` で落ちる**——F は状態の `pc` の値（小文字の `read`・`write`）で `phases` を引くので、
鍵を小文字にした表が要る（`{"read": "read", "write": "write"}`。2 パス目に組み直した表で、A4 と同じ `steps` が出た。1 パス目に F に渡した表は残っていない）。

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

### 付録 F: tlc_to_trace.py（TLC の反例のテキスト → `calls`・`steps`。1 パス目の反証 1 への対応）

```python
"""TLC の反例（テキスト）から trace ケースの `calls`・`steps` を作る（#1015 の実験。Verifier の反証 1 への対応）。

itf_to_trace.py の「状態だけ」の決め方（隣の状態で pc が変わった呼び出しを 1 つ探す）を、TLC の出力の
`/\\ pc = [old |-> "read", new |-> "write"]` の行に当てる。TLA+ の値の構文は解かない——pc の行の形（文字列から文字列への関数）だけを正規表現で読む。

使い方: python3 tlc_to_trace.py <TLC の出力> <対応表の JSON>
対応表は itf_to_trace.py と同じ。ただし phases の鍵は TLC のモデルの段の文字列（"read"・"write"）。
"""
import json
import re
import sys

STATE = re.compile(r"^State \d+:")
PC = re.compile(r'^/\\ pc = \[(.*)\]$')
ENTRY = re.compile(r'(\w+) \|-> "(\w+)"')


def pcs(text: str, name: str = "pc") -> list[dict]:
    states, current = [], None
    for line in text.splitlines():
        if STATE.match(line):
            current = {}
            states.append(current)
        m = PC.match(line)
        if m and current is not None:
            current.update(dict(ENTRY.findall(m.group(1))))
    return states


def convert(text: str, table: dict) -> dict:
    states = pcs(text)
    if not states or any(not s for s in states):
        raise SystemExit("pc の行が無い状態がある")
    steps = []
    for a, b in zip(states, states[1:]):
        moved = [who for who in a if a[who] != b[who]]
        if not moved:
            continue
        if len(moved) > 1:
            raise SystemExit(f"1 つの遷移で 2 つ以上の呼び出しが動いた: {moved}")
        who = moved[0]
        steps.append([table["calls"][who]["name"], table["phases"][a[who]]])
    calls = {c["name"]: {"operation": c["operation"], "input": c["input"]} for c in table["calls"].values()}
    trace = {"formal": table["formal"], "calls": calls, "steps": steps}
    trace.update(table.get("rest", {}))
    return {"mode": "tlc-text", "trace": trace}


if __name__ == "__main__":
    print(json.dumps(convert(open(sys.argv[1]).read(), json.load(open(sys.argv[2]))), ensure_ascii=False))
```

### 付録 G: red_with_scaffold.py（変換の出力から本物の `scaffold.py` の `red_test` で Red テストを作り、実装に当てる。1 パス目の `/code-review` の指摘 3 への対応。入口の定義 `OPS` は付録 E と同じものを `check_with_scaffold_ops.py` に写して読む）

```python
"""変換の出力から本物の scaffold.py の red_test で Red テストを作り、実装に当てる（#1015。/code-review の指摘 3 への対応）。

check_trace は形しか見ない（段の順の正しさを見ない）。順の正しさは、生成した Red テストが
  - 変換した順で: 守りの無い実装（モデルの broken）を赤、守りのある実装（fixed）を緑にし、
  - 順を変えた版（旧が先・書くが読むより先）で: 守りのある実装を赤にする
ことで判別する（期待（outcomes・after）は直した仕様のこの順での結果なので、順が違えば正しい実装でも合わない）。

使い方: python3 red_with_scaffold.py <scaffold.py のあるディレクトリ> <変換の出力の JSON>
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location("scaffold", Path(sys.argv[1]) / "scaffold.py")
scaffold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaffold)
sys.path.insert(0, str(Path(__file__).parent))
from check_with_scaffold_ops import OPS  # noqa: E402

STATE = '''
import threading

_rows = {}
_lock = threading.Lock()


def reset_state():
    _rows.clear()


def set_row(key, ver):
    _rows[key] = ver
    return {"ver": ver}


def get_row(key):
    return {"ver": _rows.get(key, 0)}

'''
# 1 つの排他の中で読むと書くをまとめる実装。口の約束どおり、その操作の直前に段を続けて呼ぶ（spec-ir.md の「実装に求める口」）
UNGUARDED = STATE + '''
def write_row(key, ver, checkpoint=lambda name: None):
    checkpoint("read")
    checkpoint("write")
    with _lock:
        _seen = _rows.get(key, 0)
        _rows[key] = ver
        return {"ok": True}
'''
GUARDED = STATE + '''
def write_row(key, ver, checkpoint=lambda name: None):
    checkpoint("read")
    checkpoint("write")
    with _lock:
        seen = _rows.get(key, 0)
        if ver < seen:
            return {"error": "STALE_VERSION"}
        _rows[key] = ver
        return {"ok": True}
'''


def feature(trace: dict) -> dict:
    return {"id": "F-001", "title": "版を書く", "operation": OPS["write_row"],
            "cases": [{"id": "F-001-C1", "title": "空の行に書く", "input": {"key": "x", "ver": 1}, "expected": {"ok": True}},
                      {"id": "F-001-C2", "title": "旧と新の書き手が重なっても古い版が残らない", "trace": trace}]}


def run(trace: dict, impl: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "impl_mod.py").write_text(impl)
        (tmp / "test_f_001.py").write_text(scaffold.red_test(feature(trace), "impl_mod", OPS))
        done = subprocess.run([sys.executable, "-m", "unittest", "test_f_001"], cwd=tmp, capture_output=True, text=True, timeout=180)
        last = [line for line in done.stderr.splitlines() if line.startswith(("OK", "FAILED"))]
        why = [line for line in done.stderr.splitlines() if line.startswith(("AssertionError", "FAIL:"))]
        return done.returncode, " / ".join(why[:2] + last[-1:]) if last else done.stderr[-300:]


trace = json.load(open(sys.argv[2]))["trace"]
old_first = copy.deepcopy(trace)
old_first["steps"] = [s for s in trace["steps"] if s[0] == "old_writer"] + [s for s in trace["steps"] if s[0] == "new_writer"]
write_first = copy.deepcopy(trace)
write_first["steps"] = [[who, {"read": "write", "write": "read"}[name]] for who, name in trace["steps"]]
rows = [("変換した順", trace, "守りなし", UNGUARDED, "赤"), ("変換した順", trace, "守りあり", GUARDED, "緑"),
        ("旧が先の順", old_first, "守りあり", GUARDED, "赤"), ("書くが先の順", write_first, "守りあり", GUARDED, "赤")]
status = 0
for label, t, name, impl, want in rows:
    rc, last = run(t, impl)
    got = "緑" if rc == 0 else "赤"
    print(f"{label} × {name}: {got}（期待 {want}）steps={t['steps']} — {last}")
    status |= got != want
sys.exit(status)
```
