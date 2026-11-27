# Issue #1600 — spec-loop: check-formal-rerun.py・check-alloy.py の一時ディレクトリも、シグナルと SIGKILL の残りを片付ける

cruise（親 Issue #1604）の子として回す**不在の周**（`/dev-loop:cruise 1604 --absent` の起動・2026-11-27T07:31Z）。
台帳の確かめた線（出所: 利用者の確認（起動時・2026-11-27T07:31:25Z、配布を見せて確かめた））:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）/ 実機確認 = 書いていない。
マージは親がする（子は PR 側の CI の最終結果を見るところまで）。割り目では訊かずに「このまま続ける」。

- 直す線: 既定（出所: cruise の確かめた線）
- 版の上げ方: spec-loop を patch で上げる（0.138.1 → 0.138.2。不具合の修正——#1594 と同じ刻み）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-tlc.py` — 一時ディレクトリと信号の共通の部品（信号を例外にする・持ち主の居ない残りの回収・自分の残りの消し直し・ツールのプロセスグループの記録）を足す
- `plugins/spec-loop/scripts/check-formal-rerun.py` — 部品を当てる（pid つきの一時ディレクトリ・信号で 128+信号・起動時の回収・TLC のグループの記録）
- `plugins/spec-loop/scripts/check-alloy.py` — 部品を当てる（同上）。`run_model` の例外の枝でプロセスグループを止める・`started` を受ける
- `scripts/test-check-formal-rerun.py` — 信号・回収の試料と変異（`check-tlc.py` の部品の変異も）
- `scripts/test-check-alloy.py` — 信号・回収の観測と変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1600.md` — この計画

触らない:

- `plugins/spec-loop/scripts/formal-statechart.py`（#1594 の自前の写しを持ったまま。部品へ寄せるのは「減らす変更」で、この周の「増やす変更」と分ける——手順 3。下の「決めたこと」1）
- `check-tlc.py` の CLI（`probe` の一時ディレクトリ）・dev-loop の `formal-sync.py` の自前の一時ディレクトリ——Issue の範囲の外
- 古い形（pid の無い）`spec-loop-formal-rerun-*`・`spec-loop-check-alloy-*` の回収（持ち主が分からない）

依存の追加・更新: なし
仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本を持たない——プラグインの原本）
差分テスト: なし（機能の追加・不具合の修正の周。振る舞いを変えないのは「信号を受けない回」の判定と出力で、既存の試料を全部通すことを受入基準 6 にする。部品へ寄せ直すリファクタリング（statechart）はこの周でしない）
プロパティテスト: なし（往復・冪等性・等価性・数値の境界の不変条件を持たない。名前の形の判定は #1594 の正規表現の写しで、境界の名前は例の試料で当てる）

## 決めたこと（推奨で決めた判断と理由）

1. **共通の部品は `check-tlc.py` に置き、`check-formal-rerun.py`・`check-alloy.py` が使う。** 3 つとも既に `check-tlc.py` を読み込み、`run_model`・`with_group` を共有している。
   新しいファイルにすると、配布・CI・CLAUDE.md の登録が増える。**`formal-statechart.py` はこの周で部品に寄せない**——寄せるのは複製を減らすリファクタリングで、
   この周の追加と同じ周に混ぜると、片方が他方を打ち消して試料の結果の出所が分からなくなる（手順 3 の「増やす変更と減らす変更を同時にやらない」）。寄せる周は残課題に書く。
2. **名前の形と判定は #1594 と同じ**——`<頭><pid>-<乱字 8 文字>`、起動時に名前がこの形どおりで pid のプロセスが居ないものだけ消す。記録したツールのプロセスグループが居れば・記録が読めなければ消さずに言う。
   頭は `spec-loop-formal-rerun-`・`spec-loop-check-alloy-`（今の頭のまま pid を足す）。**各スクリプトは自分の頭だけを回収する**。
3. **信号のハンドラは `main` の間だけ入れ、抜けたら元に戻す**（statechart は戻さない）——`check-alloy.py` のテストは `main` を同じプロセスで呼ぶ。
   親が無視にした信号は無視のまま。2 回目の信号は無視（片付けの途中で止めない）。片付けの後に自分の pid の残りを消し直してから戻す。
4. **信号で止められたら 128+信号の番号で終わる**（statechart と同じ）。終了コードの表に足す。

## 乗るデプロイ経路

main へのマージでプラグイン（spec-loop）の配布と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。マージは親がする。

## 受入基準（不変条件 × 経路）

経路（2 つのスクリプトの入口と終わり方）: (a) 判定して 0・1・4 で終わる、(b) 引数の誤り 2、(c) 想定外の例外 2、(d) SIGTERM・SIGINT・SIGHUP、(e) SIGKILL（片付けが走らない）、(f) 時間切れ（`run_model` の内側）、
(g) dev-loop の `formal-sync.py` が `check-formal-rerun.py` の `rerun` を読み込んで呼ぶ（信号のハンドラは入らない）、(h) `check-alloy.py` の `main` を同じプロセスで呼ぶ（テスト）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | SIGTERM・SIGINT・SIGHUP を受けたら、一時ディレクトリが残らず、ツールのプロセス（グループ）も残らず、128+信号で終わる（両スクリプト） | d | 決めたこと 3・4 | 試料（眠る偽のツールに信号を送り、その pid が居ないこと・`$TMPDIR` が空を見る）。本物の TLC・Alloy でも SIGTERM を 1 回ずつ（直す前に残ることを見た陽性対照と並べる） |
| 2 | 親が無視にした信号は無視のまま（`nohup` の SIGHUP など） | d | 決めたこと 3 | 試料 |
| 3 | SIGKILL で残った（持ち主の居ない）自分の頭の pid つきのディレクトリを次の起動で消し、持ち主の居るもの・この形でない名前・ほかの頭のものは消さない。ツールのグループがまだ走っていれば・記録が読めなければ消さずに言う | e | 決めたこと 2 | 試料 |
| 4 | `check-alloy.py` の `run_model` が待っている間の例外でも Alloy のプロセスグループを止める | d・f | `run_model` の例外の枝 | 試料（信号のときに偽の Alloy の pid が居ない） |
| 5 | 片付け（`TemporaryDirectory` の削除）の途中に信号が届いても残さない | d | 決めたこと 3 | 試料（`check-formal-rerun.py`） |
| 6 | 信号を受けない回の判定・終了コード・出力は今までどおり（既存の試料と変異が全部通る） | a・b・c・f・g・h | 変えない | `scripts/test-check-formal-rerun.py`・`scripts/test-check-alloy.py`・`scripts/test-formal-sync.py`・`scripts/test-check-tlc.py`・`scripts/test-formal-statechart.py` |
| 7 | `main` を同じプロセスで呼んだ後、信号の扱いが元に戻る | h | 決めたこと 3 | 試料（`check-alloy.py` を読み込んで `main` を呼び、前後の `signal.getsignal` を比べる） |
| 8 | 版が 3 か所（`marketplace.json`・`plugin.json`・`SKILL.md` の 2 行）で揃い、歯止めが全部通る | — | 0.138.2 | `python3 scripts/check-all.py`・PR 側の CI |
| 9 | 両方の関門に受入基準を渡す × 2 パス（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | — | 手順 5・6 | 関門の記録 |

この環境で証明できないもの: なし。

生成物: `docs/` の設計ドキュメントの生成ブロック（`scripts/skill-metrics.py`）——spec-loop の `SKILL.md` の版の行だけを変える。`python3 scripts/skill-metrics.py --check` で鮮度を見る。図（drawio）は触らない。

複製の数: 信号と回収の決まりを述べる箇所は 3 つ（`check-tlc.py` の部品の節が原本、`check-formal-rerun.py`・`check-alloy.py` の docstring は自分の頭と終了コードだけを書いて原本を指す）。
`formal-statechart.py` の docstring は #1594 の自前の写しを述べたまま（決めたこと 1）。分けない理由: 原本は 1 つで、ほかは指すだけ。

## 陽性対照（直す前に残ることを本物で見た）

2026-11-27、base（`0c824eac`）の木を `git archive` でリポジトリの外に取り出し、本物の TLC（tla2tools v1.7.4）・Alloy 6.2.0 で、`TMPDIR` を空の一時ディレクトリにして走らせ、SIGTERM を送った:

- `check-formal-rerun.py`（16M 状態のモデルを本体に、8 秒後に SIGTERM）: 終了コード 143、`spec-loop-formal-rerun-pnjy2d0_` が残り、cwd がその下の java（TLC）が 1 秒後も居た。
- `check-alloy.py`（0.5 秒後に SIGTERM）: 終了コード 143、`spec-loop-check-alloy-45rbeyoi` が残り、cwd がその下の java（`alloy.jar exec Broken.als`）が居た。
- 観測窓: 各 1 回、信号の 0.2〜1 秒後の `ls` と `lsof` の cwd。手元の `$TMPDIR` にも古い形の `spec-loop-formal-rerun-*` が 4 つ残っていた（2026-11-24・25。出所は確かめていない）。

## 未解決・確認待ち

- なし（判断は「決めたこと」に推奨で決めた）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1600-tempdir-signal-cleanup`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1600`・起点 `0c824eac`・base は `origin/main`（`refs/remotes/origin/HEAD`）の merge-base `0c824eace80033e869325f8fd757fb58bc766376`
- 実装: 済（`c757bbc4`）。歯止め `check-all.py`（run-serial 越し）: 緑（19 本を回し 87 本 CACHED、失敗 0）
- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目の指摘対応の起点: `c757bbc4a0b17bb2951839be2c18e44b41edf282`
- Verifier 1 パス目: 起動（dev-loop:dev-loop-verifier・sonnet）。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1600-verifier-1-20261127T082846Z.md`
- /code-review 1 パス目: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1600-code-review-1-20261127T082846Z.md`
- Verifier 1 パス目: 反証 0 件（観察 2 件。採否の表）。終点 `c757bbc4`
- /code-review 1 パス目: 指摘 5 件（important 2・nit 3）。終点 `c757bbc4`
- 1 パス目の指摘対応: `31f421f9`（直す 3 行）。`check-all.py`（run-serial 越し）: 緑（59 本を回し失敗 0）。指摘対応の差分は 0 行でない（`git diff c757bbc4 -- ':(top)' ':(top,exclude)docs/plans/issue-1600.md'` が空でない）ので 2 パス目を回す
- 割り目（手順 6）: 割らない（cruise の周）
- Verifier 2 パス目・/code-review 2 パス目: 報告のファイル `…/scratchpad/gate-1600-verifier-2-<時刻>.md`・`…/scratchpad/gate-1600-code-review-2-<時刻>.md`（下に書き足す）
- 1 回目の `check-all.py` は `( … ) &` で起こしたので SIGINT が無視の状態で走り、既存の `test-formal-statechart.py` の「信号: SIGINT」が落ちた（交絡。前景で回すと緑、`run_in_background` では SIGINT は既定のまま——実測）。2 回目は `run_in_background` で回して緑
- 交絡を潰した手順: 陽性対照は base の木をリポジトリの外に取り出して走らせた（新しい実装と同じ試料・同じ手順で比べる）

```dev-loop-gates
周の base: 0c824eace80033e869325f8fd757fb58bc766376
関門: Verifier 1 c757bbc4a0b17bb2951839be2c18e44b41edf282 反証=0
関門: /code-review 1 c757bbc4a0b17bb2951839be2c18e44b41edf282 指摘=5
```

## 既知の限界・決着済みの論点

### 1 パス目の指摘と採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-観察1: `catch_signals()` の後から `try` までに届いた信号を取りこぼす（Verifier は反証に数えず） | 示せる——1 つ目を入れた直後に SIGTERM を送る形（`signal.signal` を包む）で `check-formal-rerun.py` が `Interrupted: 15` の未捕捉で終了コード 1 | 1 | 直す（`current_signals()` を取ってから、入れるのを `try` の中に移す） |
| V1-観察2: `except Interrupted` の中の標準エラーへの出力が SIGHUP の後に `OSError` になりうる | 示せない（実験していない） | 無し | 残課題 |
| CR1-1: 信号が `Popen` の中・`Popen` と `try` の間に届くと検査器を止めずに抜ける | 示せる——`run_model` を直に呼び、`Popen` の子を起こした後に SIGTERM を送ると、偽の検査器（`sleep`）が `Interrupted` の後も居た。CLI からの再現では偽物が自分で死んで残らなかった（起きる前に作業ディレクトリが消えると、偽物の sh が閉じた管に書いて SIGPIPE で死ぬ——実測の交絡。試料は偽物が pid を書くまで待ってから送る形にした） | 1・4 | 直す（`run_model` は起こしてから `try` の中まで信号を待たせ、子には `preexec_fn` で待たせた分を引き継がない。両スクリプト） |
| CR1-2: `restore_signals` の途中（1 つ目を戻した後）の信号で `Interrupted` が `finally` から上がり終了コード 1 | 示せる——1 つ目を戻した直後に SIGHUP を送る形で `Interrupted: 1` の未捕捉・終了コード 1 | 1 | 直す（戻す間は信号を待たせ、戻した後の扱いで受ける——既定なら信号で終わる） |
| CR1-3: `check-formal-rerun.py` の守らないの表の「次のこのスクリプトの起動が回収する」は、dev-loop の周で `formal-sync.py` だけを回す限り回収されない | 示せない（文面の読み方。`formal-sync.py` は走らせていない） | 無し（経路 g は受入基準 6 だけ） | 残課題 |
| CR1-4: `check-alloy.py` の `__main__` に想定外の例外を 2 にする枝が無く、`.tool-group` が書けないとトレースバックで 1 | 示せない（実験していない） | 無し | 残課題 |
| CR1-5: 持ち主の pid が再使用されている間は回収されないことが、部品の節の守らないに無い | 示せない（文面の欠け） | 無し | 残課題 |

- 1 パス目の指摘対応のコミット: 下の「関門の進捗」。直した 3 行（V1-観察1・CR1-1・CR1-2）には試料を足した（「信号: 入れる途中」「信号: 起こした直後（Popen の中）」「信号: 戻す途中」と、検査器が待たされたまま起きないことの観測）と変異（`check-tlc.py` の 3 件・`check-formal-rerun.py` の 1 件・`check-alloy.py` の 2 件）。

### 決着済み

- `formal-statechart.py` は部品に寄せない（決めたこと 1）。寄せるまでは同じ規則の写しが 2 つある。
- 古い形（pid の無い名前）の残りは回収しない——持ち主が分からない。手で消す。
- SIGKILL の直後は片付けが走らない（次の起動で回収する）。ツールが走り続けていれば消さずに言うだけで、止めるのは人。

## 手順 8（経験の還元）

- この周の起票: 0 件（不在の周で、起票の候補は親に渡す。確認の Issue は親が立てる）
