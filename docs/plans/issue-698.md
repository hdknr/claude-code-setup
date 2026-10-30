# Issue #698 — test-merge-versions.py: 準備の失敗を check に通し、git-alongside の試料に見分ける役を与える

PR #697（#680 の周）の `/code-review` 2 パス目の残課題 2 件（CR2-4・CR2-5）を、テスト 1 本（`scripts/test-merge-versions.py`）で直す。

## 変更範囲

触る:

- `scripts/test-merge-versions.py` — 試料の準備の失敗を `check()` に通す（CR2-4）・`git-alongside` だけが殺す変異を足し、試料のコメントを直す（CR2-5）・docstring
- `docs/plans/issue-698.md` — この計画

触らない:

- `plugins/spec-loop/`（本体 `merge-versions.py` は変えない——直すのはテストだけ。版も上げない）
- `assert_in_tmp` の `AssertionError`（実リポジトリを触ろうとした安全装置——止まるのが正しいので `check()` に通さない）
- 準備のうち `prepare_git` の外の分岐（`run_case` の中の出力先の用意など。単純な FS の操作で、この Issue の示した失敗ではない）

### 同じことを述べている箇所の数

- 「試料を用意できなければ失敗に数えて続ける」: テストの docstring 1 か所・`PrepareFailed`／`attempt` の docstring 2 か所 = 3 か所。分けない理由: どれも同じファイルの、それぞれの関数の振る舞いの記述
- 「`git-alongside` だけが殺す変異」: 試料のコメント 1 か所・変異のコメント 1 か所 = 2 か所。分けない理由: 試料側は試料の役、変異側は変異の意味で、互いを指す

## 乗るデプロイ経路

テストと計画ファイルだけ。`plugins/` を変えないので配布は起きない（版を上げない）。`docs/plans/` は main へのマージで Pages に出る。

## 周の在り処

- ブランチ: `issue/698-merge-versions-test-check`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-698`
- 起点: `745bb1c`（start-point `origin/main`）
- base: `745bb1c2f1e50b6d2bdba68327073c287b81ccd7`（`git merge-base origin/main HEAD`）

## 線（出所）

- 不在の周: `/dev-loop:cruise 474 --absent`（再開 2026-10-31）の子として回す
- 直す線: `既定`・仕様の穴 = 推奨で決めて起票・マージ = 関門を通ればマージ・周の途中の課題 = 台帳に足して直す
  （cruise の確かめた線（台帳 `issue-474`）。出所: 利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））
- 利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る行（狭いパスの指摘を含む）は推奨で決めて `要確認` の Issue を立てる
- 台帳は書かない（親が書く）。マージは親。周の途中の課題はファイルごとに 1 件にまとめて親に渡す
- `実機確認` の線は台帳に無い——既定の `止まる`（この周に実機の要る受入基準は無い）

## 確認待ち

なし（Issue の 2 行はどちらも直し方が 2 択で、CR2-5 は「見分ける役を与える」を選んだ——外すと、区別する FS の
「中身のある並ぶ綴り違い」を見る試料が無くなるため。仕様の穴ではない）。

## 受入基準（不変条件 × 経路）

入口: `python3 scripts/test-merge-versions.py`（手元・`check-all.py`・CI の Linux の 2 段（区別する FS／casefold））。
試料を走らせる経路は 3 つ——`run_all`（全試料）・決定論の 2 本（`twice`・`shifted`）・変異の殺す試料。FS は 2 種。

| # | 不変条件 | 破りうる経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| B1 | **試料の準備（`build`・`prepare_git`）が `RuntimeError`・`OSError`・`CalledProcessError` で失敗しても traceback で全体を止めず、その試料の名前つきで失敗に数え、他の試料・変異を続け、終了は 1（緑にしない）**（CR2-4） | 3 つの経路のどれか 1 つでも `run_case` を素で呼ぶ | 3 経路とも `attempt` を通す。陽性対照: `git-both` の `git checkout` を外すと、直す前は traceback で要約が出ない／直した後は 1 件の失敗が名前つきで出る（区別する FS）。変異の経路は `git-renamed-sensitive` の準備で失敗させて 2 件（試料・変異）が出る |
| B2 | **`git-alongside` の試料が、他のどの試料も殺さない変異を殺す**（CR2-5） | 足した変異を他の試料も殺す・`git-alongside` が殺さない | 区別する FS で、変異ごとに git の全試料を当てて殺す試料を数える（`同じ項目かを見ない`→`足していない改名…` だけ、`並ぶ綴り違いの名前も…`→`綴りだけ違う名前のハードリンク…` だけ、足した変異→`git-alongside` だけ） |
| B3 | **既存の試料・変異の答えが変わらない** | `attempt` に寄せたことで判定が落ちる・数が変わる | 両 FS で緑。区別しない FS: 試料 103・変異 98（前と同じ）、区別する FS: 試料 96・変異 87（前の 86 に足した 1） |
| B4 | **書いた主張が実物と一致する**（試料・変異のコメント「2 つの守りはどちらも単独でこの形を守る」、docstring の「失敗に数えて続ける」） | 主張の書き違い | B1・B2 の実走 |
| B5 | **歯止めが全部緑**（手元 `check-all.py`、PR 側 CI の Linux と casefold の両段） | — | `check-all.py`・`gh pr checks` |

組み合わせ: B1・B2 × 2 つの FS = 両方で `test-merge-versions.py` が緑（手元で両方、CI で両方）。B1 × 3 経路 = 3 経路とも `attempt`。
受入基準 × 2 つの関門 × 2 パス = 4 つの受け渡し（2 パス目が「該当なし」なら 2 つ）。

### 証明できないもの（未証明）

- なし。区別する FS は手元のディスクイメージ（Case-sensitive APFS を `TMPDIR` に）と CI の Linux の両方で回せる。

### 生成物

- 生成物なし（テストに生成物は無い。`skill-metrics.py` の対象外）

## 関門の進捗（再開点）

- 実装: 済み。手元で両 FS 緑——区別しない: 試料 103・変異 98、区別する: 試料 96・変異 87。B1・B2 の陽性対照は上の表のとおり実走で確かめた
- 交絡を潰した手順: CR2-4 は直す前のテスト（`745bb1c`）と直した後のテストに同じ壊し方（`git-both` の書き出しを外す）を当て、前は traceback・後は名前つきの失敗（同じ FS・同じ本体）。
  CR2-5 は変異ごとに git の試料を全部当てた——区別する FS で、`spelled` の守りを片方ずつ外す 2 本は `git-alongside` を赤にしない（Issue の主張の再現）、2 つとも外すと 4 試料が赤、足した変異は `git-alongside` だけが赤。区別しない FS ではどの変異も git の試料を赤にしない（`git-alongside` はそこでは飛ばす）
- 割り目（手順 4・6）: 不在のため訊かず続ける
- Verifier 1 パス目: 済み——反証 0 件（sonnet・`dev-loop:dev-loop-verifier`。テンプレート 170 行を読んだと報告、`wc -l` は 169——最後の行に改行が無い）。両 FS で 103/98・96/87、B1・B2 を実走で一致
- /code-review 1 パス目: 済み——指摘 6 件（直す 1（CR1-1 と CR1-2 は同じ B4 の破れで 1 か所を直す）・残課題 4。下の採否の表）
- 1 パス目の指摘対応の起点: `180e46b0719c459b82496bf1ee450f35e686d75b`（2 つの関門に渡した時点の HEAD。`180e46b` で全部コミット済み）
- 1 パス目の指摘対応: docstring を直した範囲に合わせて狭めた（B4）。区別しない FS で 103/98 緑
- 割り目（2 パス目の前）: 不在のため訊かず続けた
- 2 パス目: 済み——Verifier 反証 0 件（170 行を読んだ。両 FS で 103/98・96/87、直した docstring の後段の主張を `git archive` を壊して実走で一致）／/code-review（high）指摘 4 件（直す 1・残課題 3。下の採否の表）
- 2 パス目の指摘対応の起点（狭いパスの起点）: `8b00a7d62bccd6d20cb859b15f5c518383fc55e7`
- 2 パス目の指摘対応の終点（狭いパスの終点）: `2d28ac3862ebdfffd4ffac350962dcb478b8d40b`（CR2-1。docstring の 2 行だけ）
- 狭いパス: 済み——指摘 0 件（sonnet・`dev-loop:dev-loop-verifier`。170 行を読んだ）。Verifier の変異: `merge` の `subprocess.run` に `check=True` を足す→赤（本体が落ちるとテストが止まる形を判別）。素通りした変異なし。区別する FS で 96/87
- 手元の歯止め: `check-all.py` 56/56 緑（`180e46b` で）。最終のコミットでも回す
- main は動いていない（2026-10-31 に `git fetch` で確かめた。`HEAD..origin/main` が空）
- 関門: 2 パスと狭いパスを通した。満たしていない受入基準・狭いパスの指摘・BLOCKED・未証明: どれも無し
- 反証と差し戻し: なし

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `assert_in_tmp` の `AssertionError` も `check()` に通すか | 通さない | 実リポジトリを触ろうとした安全装置で、止まるのが正しい |
| 準備の失敗に `OSError`・`CalledProcessError` も含めるか | 含める | Issue の `RuntimeError` と同じく準備の失敗で、どれも traceback で全体を止めていた（`git(...)` は `check=True`） |
| CR2-5: 外すか、役を与えるか | 役を与える（変異を足す） | 外すと、区別する FS で「追跡していないが中身のある並ぶ綴り違い」を見る試料が無くなる。`git-stale`（`.DS_Store` だけ）と対になって「古い残りは捨て、中身があれば断る」を見分ける |
| 足した変異は区別しない FS で走らない | そのまま | 殺す試料が区別する FS でしか作れない（既存の枠組みどおり `skipped(killer)` で飛ばし、当て先の数は両 FS で見る） |

### 1 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1: `run_case` の `git archive`（`check=True`）が準備の try の外で、git の失敗でまだ traceback。docstring の「git の呼び出しの失敗は数えて続ける」と食い違う | 示せる（レビューが `HEAD`→`NOPE` で traceback・要約 0 行を再現） | B4（docstring の主張） | 直す——docstring を `build`・`prepare_git` に狭め、後の段は traceback のままと書く |
| CR1-2: docstring は準備全体と言うが、except は `build`・`prepare_git` だけ（出力先の用意・`copy_scripts`） | 示せる（コードの範囲と文面の食い違い。CR1-1 と同じ） | B4 | 直す（CR1-1 と同じ 1 か所） |
| CR1-3: `StopIteration`・`UnicodeDecodeError` は捕まえる型に無い | 示せない（再現していない） | 無し | 残課題 |
| CR1-4: `locked` の戻しが finally でなく、後段の例外で chmod 0 が残る | 示せない | 無し | 残課題 |
| CR1-5: `CalledProcessError` の stderr が bytes の repr で出る | 示せる（B1 の対照で `b"..."`） | 無し（名前つきで失敗に数える点は満たす） | 残課題 |
| CR1-6: 足した変異は守りを外す形でなく振る舞いを足す形で、`git-alongside` の役は紙の上。本当の分け目は `misnamed` の `has_content` | 示せない（判断。足した変異が `git-alongside` だけに殺されることは確かめた） | 無し | 残課題 |
| V1 軽微: except の中の `chmod` が `OSError` を出すと traceback に戻る | 示せない | 無し | 残課題 |

### 2 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1: 直した docstring の「本体の実行」の失敗も traceback で止まる、は偽（本体は子プロセスで、落ちても終了コードと出力として判定に入る） | 示せる（著者が本体を `raise RuntimeError` に差し替えて `attempt` を呼び、終了コード 1・失敗 0 件・テストは続いた） | B4 | 直す（`2d28ac3`）——「本体の実行」を外し、本体が落ちたときの扱いを書いた |
| CR2-2: 「それより後」の順序が誤り（変異の写しは `attempt` より前）で、列挙に抜け（`check_reference`・`snapshot` ほか） | 示せない（コード読解。CR2-1 の書き直しで順序を言う文は無くなり、列挙は「など」にした） | 無し | 残課題 |
| CR2-3: docstring の `prepare_git` の括弧（git の呼び出し・index からの書き出し）は、捕まえる FS の操作（`rename`・`os.link` ほか）を言わず狭い | 示せない（コード読解） | 無し | 残課題 |
| CR2-4: 「殺すのは `git-alongside` だけ」は機械で当てていない（ほかの試料が後で殺すようになっても緑） | 示せない（将来の話。いまは変異ごとに当てて `git-alongside` だけと確かめた） | 無し | 残課題 |

### 振り分け（手順 8。周の途中の課題 = 台帳に足して直す）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| CR1-5: `PrepareFailed` の詳細が `CalledProcessError` の stderr を bytes の repr で出す（日本語のメッセージは `\\xe3…` になる） | #698 /code-review 1 パス目 | 示せる（B1 の対照で `b"..."` が出た） | 直す——親に起票を提案（`scripts/test-merge-versions.py` の 1 件） |
| CR1-3・CR1-4・V1・CR2-2・CR2-3・CR2-4・CR1-6 | #698 の各関門 | 示せない | 外に出す（PR コメントの残課題） |

- この周の起票: 0 件（この周で立てた Issue は無い。CR1-5 は親への起票の提案）
