# Issue #466 — cruise: 起動時に周で使う操作の権限を点検し、権限の拒否で cruise が止まらないようにする

着手の順序は Issue のコメント（owner、2026-10-27）に従う: **#464 のマージまでは手順 2・3 で止める**。
#464 と同じ箇所（cruise `SKILL.md`・`ledger.py`・起動時の確かめ・`dev-loop` の版）を触るため。

スキルの版: 読み込まれていたのは 1.37.0（キャッシュ）。この周はリポジトリの `SKILL.md`（main の 1.58.0、取り込み後は #464 の版）に従う。

## 利用者が決めたこと（2026-10-27・AskUserQuestion）

- **周の範囲**: 案 ①（操作の数え上げと起動時の点検を `--absent` 以外にも広げる）・③（「利用者の操作待ち」で依存しない次の周へ進む）・
  ④（親の起動場所の既定）を**この周に入れる**。**② 分類器・ガードを実際に試すことは分けて起票する**（手順 8 で承認を訊く）
- **親の起動場所の既定**: **隔離しない場所から起動する**——cruise の親はメインの作業ツリーから、worktree 隔離なしで起動する。
  周ごとの作業はこれまでどおり各周の worktree で行う

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 起動時の許可の点検を居る周でも回せる形（不在に限る項目と分ける）・`.claude/dev-loop.md` の操作の宣言を点検するコマンドに足す・settings で判定できない操作を「止まりうる操作」として出す
- `scripts/test-check-unattended-env.py` — 回帰テスト（変異を含む）
- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — 「利用者の操作待ち」の状態（名前は未決定。下の「未解決」）
- `scripts/test-ledger.py` — 同上
- `plugins/dev-loop/skills/cruise/SKILL.md` — §3（起動時の点検を `--absent` 以外にも）・§4（止まりうる操作に当たったら台帳に書いて次へ）・§6（操作待ちの行を渡す）・親の起動場所
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 状態の追加に伴う書く時点
- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — cruise §4 の番号の指し先（2 パス目の S1 で広げた）
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — `本番反映 = しない` の「利用者待ち」と新しい状態の関係（要るなら）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行（中身を変えるなら最小限）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（minor）・description
- `.claude-plugin/marketplace.json` — 同上（2 つを揃える）
- `docs/plugins/dev-loop-cruise.md` — 起動場所・起動時の点検・操作待ちの説明
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `CLAUDE.md` — `check-unattended-env.py` の行の「`--absent` の起動時だけ」が偽になるなら直す
- `docs/plans/issue-466.md` — この計画

触らない:

- 分類器・worktree 隔離のガードを実際に試すこと（② として分ける。#464 の周と拒否の記録が混ざるのも避ける）
- 利用者の settings を書き換える道具（`check-unattended-env.py` は読むだけ、を崩さない。`--fix` を置かない）
- `本番反映` を広げる手段（どこにも作らない）
- #464 が足した `周の途中の課題` の線と `origin`（その上に乗るだけ）
- #461（周の合間の `/clear`）

## 乗るデプロイ経路

main への push で GitHub Pages が自動デプロイする（`docs/` の変更が公開される）。プラグインはマージで配布され、利用者側は `plugin update` で届く。

## 設計の要点（#464 の差分の上に乗る形）

1. **操作の数え上げ**: 既定の 5 つ（`git push`・`gh pr create`・`gh pr merge`・`gh pr comment`・`gh issue create`）に、
   対象リポジトリの `.claude/dev-loop.md` が宣言する操作を足す。**いまの `.claude/dev-loop.md` には機械で読める操作の宣言が無い**
   （`不在の線:` だけ）ので、宣言の行を足す（例: `cruise の操作: gh workflow run infra-apply.yml`。書式は未決定）。
   宣言の無いリポジトリでは既定の 5 つだけを見て、宣言が無いことを出す
2. **起動時の点検**: cruise §2 で台帳を作った後、**`--absent` に依らず**許可の項目を回して利用者に見せる。
   自動継続・質問の待ち・通知・スリープは不在に限る（居る周では出さないか、参考として出す）
3. **settings で判定できない操作**（自動モードの分類器・worktree 隔離のガード）は「止まりうる操作」として一覧で見せ、
   (a) 許可を足す（`/permissions`・`update-config`）／(b) その操作だけ利用者が打つと決めて台帳に書く／(c) その周を cruise の外に出す、を
   `AskUserQuestion` で選んでもらう。(b) は台帳の線ではなく Issue 行に残す（線は全周に効くものなので）
4. **止まりうる操作に当たったら**: cruise 全体を止めずに、その周を「利用者の操作待ち」（コマンドを `note` に）として台帳に書き、
   `next` が出す依存しない次の周へ進む。操作待ちの周に依存する周は待つ（`merged` でないので `next` に出ない——既存の判定のまま）。
   §4-5 の「まとめて 1 度だけ訊く」（#464）と同じ場所で、操作待ちの行も利用者に渡す
5. **親の起動場所**: cruise `SKILL.md` の冒頭と公開ページに「親はメインの作業ツリーから worktree 隔離なしで起動する」を既定として書く。
   **隔離されたセッションで起動されたことを検出したら、その旨を利用者に見せる**（止めない——下の「未解決」で決めた）

## verify の受入基準

不変条件 × 破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | 居る cruise でも、起動時に周で使う操作の許可が利用者に見せられる | cruise §3 が `--absent` の中だけに書かれたまま／§1 の再開の経路で点検が抜ける／`check-unattended-env.py` が居る周で不在の項目を出して要対処が埋もれる | `SKILL.md` の §（新規・再開の両方）と、スクリプトの出し分け（テスト） |
| B | 対象リポジトリが宣言した操作（本番反映の口など）が点検に入る | 宣言の読み取り漏れ（書式の揺れ・フェンスの中・コメント）／`--project` が worktree の root を指す／宣言が無いときに黙って既定だけ見る | スクリプトのテスト（宣言あり・なし・崩れた宣言）。宣言が無いことを出力に出す |
| C | settings で判定できない操作を「良い」と出さない | 分類器・ガードの対象を `allow` に当たるから良いと判定する | 出力で別区分（止まりうる）にする。テスト |
| D | 止まりうる操作で cruise 全体が止まらず、依存しない周へ進む | 新しい状態を `next`／`show` が知らない／操作待ちの周に依存する周が `next` に出る／§6 で操作待ちが残っても「済んだ」と報告する | `ledger.py` の状態の表とテスト・cruise §4・§6 |
| E | 台帳は壊れない（既存の守るもの） | 新しい状態の追加で、古い台帳の読み込み・`load` の検査・`STATES` の突き合わせが崩れる | `test-ledger.py` を全部回す |
| F | 読むだけ（利用者の設定を書き換えない） | 点検の拡張で書き込みが入る | 差分とテスト（設定ファイルの前後のバイト一致） |
| G | `本番反映` は広げられない | (b) の「利用者が打つ」が本番反映を自律に寄せる道になる | (b) は「利用者が打つ」を記録するだけで、cruise が打つ道は作らない |
| H | 版と description が 3 箇所で揃い、生成ブロックが新しい | 版の上げ忘れ・#464 と同じ版への衝突・§8.2 の生成ブロックの古さ | `check-all.py`（`check-plugin-versions.py`・`skill-metrics.py --check`・`check-version-bump.py`） |
| I | 親の起動場所の既定が、cruise の入口の全箇所で同じことを言う | `SKILL.md` と公開ページと `CLAUDE.md` の 1 箇所だけ直す | 名前の grep でなく「親をどこで起動するか」を述べる箇所を開いて探す |

組み合わせ（必須要件の掛け算）: Verifier × 1 パス目／2 パス目、`/code-review` × 1 パス目／2 パス目の 4 つの受け渡しに、この表と下の「既知の限界」を渡す。

**この環境では証明できないもの（未証明）**:

- 自動モードの分類器が実際にどの操作を拒むか（サーバ側の判定。② に分けた）
- 権限の**確認ダイアログ**（`ask`）が出た場合は、会話が利用者の応答で止まる——cruise は「拒否された」ときにしか次へ進めない。
  確認ダイアログで止まらないことは、この周の変更では保証できない（起動時の点検で事前に見せることが手当て）
- 親を隔離しない場所から起動したときに、Issue の表の拒否（`git -C`・`git archive` のパイプ・URL に `git` を含む `curl` など）が消えること
- 「次へ進む」は `SKILL.md` の散文で決まる LLM の振る舞いで、`ledger.py` のテストは状態の判定までしか見ない

**生成物**: 該当あり——`docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を触れば `skill-metrics.py` で書き直し、`--check` が 0）。
drawio の書き出しは該当なし（図を触らない予定。触るなら `export-diagrams.py`）。

## 未解決の判断・確認待ち

実装の前に決めた（2026-10-27。#464 のマージ後）:

- 「利用者の操作待ち」は**新しい状態 `await`**（`blocked` と分け、`show` と cruise §6 で打ってほしいコマンドを周ごとに渡せるようにする）
- `.claude/dev-loop.md` の宣言は **`cruise の操作: <コマンド>`**（1 行 1 コマンド。フェンスの中は読まない）
- (b) の「利用者が打つ」は**台帳の最上位の `user_ops`**（`ledger.py user-ops`。`lines` と同じく置き換え・出所必須）。操作はリポジトリ単位で、Issue 単位ではないため
- worktree の中からの起動は**要対処として見せるだけで止めない**（起動し直すかは利用者が決める）

残る確認待ち: なし

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/466-cruise-permission-check`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-466`・
  起点 `bd8fa53`・base の参照 `origin/main`（解決した SHA `bd8fa5385ce161f25e581d35d226b548cf0de809`）。
  **#464 のマージ後に main を取り込むので、base は取り込んだ後に `git merge-base origin/main HEAD` で当て直す**
- **#464 のマージ後に main（`e7c36c6`）を fast-forward で取り込んだ**。取り込みで増えた検査は無し。**base を当て直した: `e7c36c6859e5d756f6bf47d54b286ad2546fdd7d`**（`origin/main` との merge-base）
- **進んだところ**: 手順 4（実装）済み。版 1.59.0 → 1.60.0（minor。能力の追加）。`check-all.py` 51/51 緑（初回は 3 本落ちた——cruise `SKILL.md` の指し先の形・dev-loop の frontmatter の共変（trailer で免除）・計画の変更範囲の書式。直して緑）。次は手順 5（Verifier 1 パス目）と手順 6（`/code-review` 1 パス目）
- 関門（1 パス目・2026-10-27・再開したセッション）: **Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 2 件**・
  **`/code-review`（high）指摘 10 件**（うち 2 件は Verifier と同じ）。採否は下の「1 パス目の指摘の採否」——直す 4 件・残課題 6 件
- **1 パス目の指摘対応: 済み**（`3fc9b37`。成果物の差分あり——`check-unattended-env.py`・そのテスト・`references/ledger.md`・§8.2 の生成ブロック）。
  足した変異 3 本（種類の違うフェンスで閉じる・崩れた行を見ない・起動場所の案内を `.git` にする）はどれも赤。`check-all.py` 51/51 緑
- 関門（2 パス目・2026-10-27・再開したセッション）: **Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 1 件**・
  **`/code-review`（high）指摘 10 件**。採否は下の「2 パス目の指摘の採否」——直す 8 件・残課題 3 件
- **2 パス目の後に main（`9b562d0`。#468）を取り込んだ**（merge `9b8782a`。衝突は公開ページ §2 の見出し 1 塊——この周の見出しに main の `{ #env-check }` を付けた）。
  取り込みで増えた検査は `test-record-stop-failure.py`。`check-all.py` 52/52 緑。版の衝突なし（main は 1.59.0 のまま）。
  **base を当て直した: `9b562d0f72947fe5f0f140ec5a835ca564ecafa5`**
- **残っている関門: 2 パス目の指摘対応と、その差分だけへの狭いパス**。**狭いパスの起点: `9b8782a`**（指摘対応を始める直前の HEAD）
- 手順 5 の反証と差し戻し: 1 パス目に 2 件（V1・V2）→ 手順 4 に差し戻して直した
- 交絡を潰した手順: 実験なし
- 割り目の選択（手順 4・2026-10-27・AskUserQuestion）: **ここで割る**——worktree の中で `/clear` して `/dev-loop:dev-loop 466`、手順 5 から
- 割り目の選択（手順 6 の 2 パス目の前・2026-10-27・AskUserQuestion）: **ここで割る**——worktree の中で `/clear` して `/dev-loop:dev-loop 466`、
  **Verifier 2 パス目と `/code-review` 2 パス目から**（base は `e7c36c6859e5d756f6bf47d54b286ad2546fdd7d` のまま。
  2 パス目の差分を指摘対応に絞るなら、指摘対応は `e1bcb9f..3fc9b37`——既存コードの改変を含むので周辺も対象に入れる）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| ② 分類器・ガードを実際に試す | この周に入れない（分けて起票） | 利用者の決定（2026-10-27）。#464 の周と同じ時間帯に拒否を出すと記録が混ざる |
| 親の起動場所 | 隔離しない場所から起動するのを既定にする | 利用者の決定（2026-10-27） |
| 確認ダイアログでの停止 | この周では防げない（未証明に回す） | 会話が利用者の応答で止まるのはハーネスの挙動で、スキルから避けられない |

### 1 パス目の指摘の採否（Verifier 2 件・`/code-review` 10 件。V1=R5・V2=R4 は同じ指摘）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1/R5 | フェンスの開閉を ``` と `~~~` の種類・長さを見ずに反転させる。異種のフェンスの入れ子で、外の宣言を落とし中を読む | 示せる（Verifier が一時 project で `--cruise --present`、出力 `2 件: gh workflow run a.yml, gh mixedfence`。`check-unattended-env.py:656`） | B（フェンスの中） | 直す |
| V2/R4 | 全角コロン・字下げ・箇条書きの `cruise の操作` の行を黙って読み飛ばす（他に有効な行があれば「良い」） | 示せる（Verifier の同じ実行で 3 行とも出力に現れず警告なし） | B（書式の揺れ・崩れた宣言） | 直す |
| R1 | 起動場所のテストが `str(repo) in detail` で、案内（→ の行）を判別していない | 示せる（`/code-review` が案内を無関係な文・`.git` に変える変異で緑のまま。scratchpad の `mut/drive.py`） | I（起動場所の案内） | 直す |
| R3 | `show` が `await` を進行中に数えるのに、`references/ledger.md` の再開の手順 2・5 が `await` を知らず、cruise §6 と食い違う | 示せる（`references/ledger.md` の手順 2「進行中は実物で確かめて続ける」と cruise §6 の「await だけなら終える」） | D（操作待ちの扱い） | 直す |
| R2 | 起動時の (c)「その周を cruise の外に出す」は周の番号が要るが、操作から周への対応が無い | 示せない（文面からの推論。起きた記録は無い） | 無し | 残課題 |
| R6 | 宣言した完全なコマンドにも ` <引数>` を付けて照合するので、完全な形の allow の規則が当たらない | 示せる（`rule_matches` の式） | 無し（保守的な向き——「良い」と誤判定しない。C は守られる） | 残課題 |
| R7 | サブモジュール・bare の worktree で起動場所の案内が git ディレクトリを指す | 示せない（走らせていない） | 無し | 残課題 |
| R8 | `user-ops` に空白を含むコマンドを引用せずに渡すと単語ごとに記録される | 示せない（この周で起きた記録は無い） | 無し | 残課題 |
| R9 | `--present` を `--cruise` 無しでも受け付け、不在の点検の要対処を消せる | 示せない（誤って回した記録は無い） | 無し（受入基準は cruise の点検） | 残課題 |
| R10 | `show` が空の `user_ops` と未設定を区別しない | 示せない | 無し | 残課題 |

### 2 パス目の指摘の採否（Verifier 1 件・`/code-review` 10 件。2026-10-27）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V3 | UTF-8 BOM 付きの `.claude/dev-loop.md` で先頭行の宣言を黙って落とし、「行が無い」と出す | 示せる（Verifier が `printf '\xef\xbb\xbf…'` のファイルで `--cruise --present`） | B（書式の揺れ・宣言が無いときに黙って既定だけ） | 直す |
| S1 | `references/found-lines.md` の「訊く場所は §4 の 5 だけ」が、§4 に 5 を挿したため操作待ちの項を指す | 示せる（`found-lines.md:86` と cruise §4 の番号） | D（§4 のまとめて訊く場所で操作待ちを渡す） | 直す |
| S2 | (c) で `dropped` にした周に依存する `todo` の周に、終わる条件も渡し方も無い | 示せる（`ledger.py` の `ready()` は依存が `merged` であることを要る・cruise §6 の終わる条件は `await`／`blocked` とその依存だけ） | D（§6 で残った周を「済んだ」と報告しない） | 直す |
| S3 | 再開のたびに止まりうる操作を `AskUserQuestion` で訊く——`--absent` の再開では利用者が居ない | 示せる（cruise §1 の再開で §3 を回し直す・§3 の質問は `--absent` でも出る） | D（cruise 全体が止まらない） | 直す |
| S4 | コロンの無い散文・字下げのコード例の `cruise の操作…` を崩れた宣言として要対処にする | 示せる（`/code-review` の probe） | 無し（過検出で安全側。B は守られる） | 残課題 |
| S5 | HTML コメントの中の宣言を読む（複数行）／黙って落とす（1 行） | 示せる（probe で `<!--\ncruise の操作: gh disabled\n-->` → 「良い」） | B（経路に「コメント」と挙げてある） | 直す |
| S6 | 情報文字列にバッククォートを含む行をフェンスとして開き、後ろの宣言を全部落とす | 示せる（probe で `` ```x` `` の後の宣言が `commands=[]`） | B（フェンス） | 直す |
| S7 | §4-4 の `merge-pr.py` は `gh pr merge` を子プロセスで呼ぶので、`user_ops` の (b) を素通りし、点検も実際に Bash に渡すコマンドを見ていない | 示せる（cruise §4-4・§4-5 の文面と `merge-pr.py` の `gh pr merge`） | A・G（(b) を選んだ操作を cruise が打つ） | 直す |
| S8 | §4-5 が拒否を即 `await` にし、`guard-rejections.md` の「割って打ち直す」を経ない | 示せる（文面） | 無し（周を余計に待たせるが、cruise 全体は止まらない） | 残課題 |
| S9 | `references/ledger.md` の手順 5 は `blocked` を進行中に数え、cruise §6 は `blocked`＋`await` だけなら終えると言う | 示せる（`references/ledger.md:76` と cruise §6） | D | 直す |
| S10 | 公開ページ §0 の版の段落が 1.59.0 で止まり、`--cruise --present` が 1.60.0 からだと書いていない | 示せる（`docs/plugins/dev-loop-cruise.md:44`） | 無し | 残課題 |

- この周の起票: 0 件
