# Issue #1601 — spec-loop: Formal Checker が $TMPDIR に組んだモデルのディレクトリを、spec/formal に写した後に消す

cruise（親 Issue #1604、`--absent`）の子として回す**不在の周**。
線の出所: 利用者の確認（起動時・2026-11-27T07:31:25Z、配布を見せて確かめた）。不在の周: `/dev-loop:cruise 1604 --absent` の起動・2026-11-27T07:31Z。
確かめた線: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）/ 実機確認 = 書いていない。
台帳は書かない（親が書く）。手順 7 のマージは親がする——この周は PR を作り PR 側の CI の最終結果を見るところまで。

版の上げ方: minor・spec-loop（0.138.1 → 0.139.0。0.x なので能力の追加は minor。並行する周が同じプラグインを上げたら、マージの直前に取り込んで上げ直す——cruise の parallel.md「版とマージの順」）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/formal-baseline.py` — 新しい口 `cleanup`（Formal Checker が報告したモデルのディレクトリを、確かめてから消す）
- `scripts/test-formal-baseline.py` — `cleanup` の試料と変異
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 「モデルを残す」に消す段を足す（原本）・報告に「消せなかったディレクトリ」・版の 2 行
- `plugins/spec-loop/skills/formal-baseline/SKILL.md` — 4 で同じ段を指す・5 の報告・版の 2 行
- `plugins/spec-loop/agents/formal-checker.md` — ディレクトリを `mktemp -d` で作る・消すのは呼び出し元だと書く・判定できなかった対象も作ったなら場所を書く
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/spec-loop.md` — 「モデルの置き場所と次の回」に 1 文
- `CLAUDE.md` — `formal-baseline.py` と `test-formal-baseline.py` の行に `cleanup` を足す
- `docs/plans/issue-1601.md` — この計画

触らない:

- `check-formal-rerun.py`・`formal-statechart.py`・dev-loop の `formal-sync.py`（どれも `TemporaryDirectory` で自分の一時ディレクトリを片付けている——確かめた）
- Formal Checker の図の対応の dump（#1594 で片付け済み）
- `references/tree.md`（置き方の原本。消す手順は spec-review の手順が原本で、tree.md はそこを指している）
- spec-loop の他の判定役（Red Team・Domain Checker・estimate-checker はモデルを組まない）
- 既に溜まった `$TMPDIR` の古いディレクトリの回収（持ち主・用途が分からない。PR に書く）

依存の追加・更新: なし
仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本を持たない——プラグインの原本）
差分テスト: なし（振る舞いを変えない周ではない。足す口と手順）
プロパティテスト: なし（往復・冪等性・等価性・数値の境界の不変条件を持たない。パスの包含の判定は境界の試料で個別に見る）

## 決めたこと（推奨で決めた判断と理由）

1. **手順を足す**（Issue の「足すかを決める」）——足す。`states/` と `-dumpTrace` の JSON が回ごとに溜まり、誰も消さない。
2. **消すのは呼び出し元（spec-review・formal-baseline）で、Formal Checker ではない**——Formal Checker が消すと、写す前にファイルが無くなる（写すのは報告を受けた後）。
3. **消すのはスクリプト（`formal-baseline.py cleanup`）で、スキルが素の `rm -rf` を打たない**——消すパスは判定役の報告（信頼できない入力）から来る。
   報告のパスが一時ディレクトリの外・一時ディレクトリそのもの・リポジトリや `HOME` を含む・symlink なら消さずに名指しする、を機械で決める。
4. **消す時点は「モデルを残す」の 4（`check`）が 0 になった後**——`check` が違反を出したら写し直すので、その前に元を消さない。
5. **報告が名指ししたディレクトリは全部消す**——写した対象の分も、残せなかった・判定できなかった対象の分も（走らせていないモデルは残さない決まりなので、元も要らない）。
6. **Formal Checker はディレクトリを `mktemp -d "${TMPDIR:-/tmp}/formal-<対象>-XXXXXX"` で作る**——作り主の決まった専用のディレクトリにし、消すものに他人の物が混ざらないようにする。判定できなかった対象でも作ったなら場所を報告する。
   **テンプレートを省かない**: macOS の素の `mktemp -d` は `TMPDIR` を読まず `_CS_DARWIN_USER_TEMP_DIR` に作る（`man mktemp`。`TMPDIR` を差し替えて走らせ、`/var/folders/…/T/` に出来たのを見た）——
   `cleanup` は `tempfile.gettempdir()`（`TMPDIR` を読む）で判定するので、`TMPDIR` が差し替わった環境では外として消さない（受入基準 6 の初回の実測で出た）。
7. 消せなかったものは、スキルが別の手段で消さず、報告で名指しする（利用者が見る）。

## 乗るデプロイ経路

main へのマージでプラグイン（spec-loop）の配布と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。マージは親。

## 受入基準（不変条件 × 経路）

経路（モデルのディレクトリができ、消える入口）: (a) spec-review の 1 回目・2 回目のレビュー、(b) spec-review の手順 5 の狭いパス、(c) formal-baseline、(d) autopilot（spec-review の段を回す——spec-review の手順に従う）、
(e) `formal-baseline.py cleanup` の直接の呼び出し（渡すパスの形: 在る・無い・相対・symlink・ファイル・一時ディレクトリそのもの・外・リポジトリや `HOME` を含む・消せない）。
モデルのディレクトリを作らない入口: `check-formal-rerun.py`・`formal-statechart.py`・`formal-sync.py`（`TemporaryDirectory`）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | `cleanup` は一時ディレクトリ（`tempfile.gettempdir()` の実体）の真下より深い（注: 書き誤り。意味は「一時ディレクトリそのものを除く下」——CR1-6）、symlink でない、リポジトリ（`--repo`、既定は cwd の git の根か cwd）と `HOME` を含まず、その中にもないディレクトリだけを消し、0 を返す | e | 本体 | 試料（`TMPDIR` を試料ごとのディレクトリに差し替える） |
| 2 | 上に当たらないパス（相対・symlink・ファイル・一時ディレクトリそのもの・外・リポジトリや `HOME` を含む・リポジトリの中）は消さずに名指しして 1。ほかの渡したパスは消す | e | 本体 | 試料（消さないパスの中身が残ることを見る） |
| 3 | 無いパスは「無かった」で 0（消すものが無い）。消せなかった（権限）は名指しして 1 | e | 本体 | 試料（書けない親の下のディレクトリ） |
| 4 | 引数が無ければ 2。想定外の例外は 2 | e | 本体 | 試料 |
| 5 | spec-review の「モデルを残す」が、`check` が 0 になった後に、報告が名指ししたディレクトリを全部 `cleanup` に渡し、1 なら手順 7 で名指しすると書く。formal-baseline がそれを指し、報告に載せる | a・b・c・d | 手順の文面 | 文面を読む・指し先が実在する（`check-skill-pointers.py`） |
| 6 | 文面のコマンドを、写した後の形で走らせると、モデルのディレクトリ（`states/` を含む）が消え、正本の `spec/formal/<対象>/` は変わらない（文面の事実の真偽） | a・c | 手順の文面 | 一時の正本で、偽の報告のディレクトリを作って文面どおりに `check` → `cleanup` を当てる |
| 7 | Formal Checker の手順が、`$TMPDIR` を含むテンプレートの `mktemp -d` で作る・消すのは呼び出し元・判定できなかった対象も作ったなら場所を書く、と書き、「走らせ終えたディレクトリを消さず」と食い違わない | a〜d | 文面 | 文面を読む |
| 8 | スキル（LLM）が実際にその手順どおりに消す | a〜d | 文面 | **未証明**——LLM の振る舞い。PR で人間のレビューに回す |
| 9 | 既存の `target`・`check` の試料と変異が全部通る（後退なし） | — | 変えない | `scripts/test-formal-baseline.py` |
| 10 | 版が 3 か所で揃い、歯止めが全部通る | — | 0.139.0 | `python3 scripts/check-all.py`・PR 側の CI |
| 11 | 両方の関門に受入基準を渡す × 2 パス（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | — | 手順 5・6 | 関門の記録 |

この環境で証明できないもの: 8（未証明）。

生成物: 設計ドキュメントの生成ブロック（`scripts/skill-metrics.py`）——dev-loop の `SKILL.md` は触らないので変わらない見込み。`python3 scripts/skill-metrics.py --check` で鮮度を見る。図（drawio）は触らない。

複製の数: 「写した後に消す」を述べる箇所は 4 つ（spec-review の「モデルを残す」＝原本、formal-baseline の 4、formal-checker.md、公開ページ `docs/plugins/spec-loop.md`）と、`cleanup` の守るものの原本の docstring 1 つ。分けない理由: 原本は spec-review と docstring で、他は指すか 1 文だけ。

## 未解決・確認待ち

- なし（判断は「決めたこと」に推奨で決めた）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1601-formal-model-dir-cleanup`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1601`、起点 `0c824eac`、base（`origin/main` → `0c824eace80033e869325f8fd757fb58bc766376`）
- 直す線: 既定（出所: cruise の台帳の確かめた線）
- 割り目（手順 4）: 割らない（cruise の周）——このまま続ける
- 1 パス目の指摘対応の起点: `dd669a9d`（1 パス目の関門に渡した時点の HEAD）
- 関門の報告のファイル: Verifier 1 パス目 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1601-verifier-1-20261127T080049Z.md`、/code-review 1 パス目 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1601-code-review-1-20261127T080049Z.md`
- 関門: Verifier 1 パス目 通した——反証 4 件（A〜D。`dev-loop:dev-loop-verifier`・sonnet。テンプレート 260 行は一致。`test-formal-baseline.py` は順番待ちの時間切れで走らせていない、と報告。終点 dd669a9d）。/code-review 1 パス目（high）通した——指摘 7 件（終点 dd669a9d）
- 手順 5 の反証による手順 4 への差し戻し: V1-B（CR1-1 と同じ）を直した。ほかの直す: CR1-2・CR1-3・CR1-6（下の採否の表）
- 1 パス目の指摘対応の差分: `dd669a9d..2221cfb3`（0 行でない——2 パス目を回す）
- 割り目（手順 6・2 パス目の前）: 割らない（cruise の周）——このまま続ける。残っているのは Verifier の当て直し（2 パス目）と /code-review 2 パス目の両方
- 関門の報告のファイル（2 パス目）: Verifier `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1601-verifier-2-20261127T090344Z.md`、/code-review `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1601-code-review-2-20261127T090344Z.md`
- 関門: Verifier 2 パス目 通した——反証 0 件（テンプレート 260 行は一致。`test-formal-baseline.py` を run-serial 越しに走らせ OK。終点 2221cfb3）。/code-review 2 パス目（high）通した——指摘 6 件（終点 2221cfb3）
- 2 パス目の指摘対応: 起点 `2221cfb3`（指摘対応を始める直前の HEAD）・終点 `5be8bd9d`。直したのは CR2-2 だけ（試料「辿れない」は直す前の本体で赤 rc 0「無かった」、直した後に緑）
- 狭いパス: `2221cfb3..5be8bd9d` に別ティアの Verifier を 1 回。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1601-narrow-1-20261127T093757Z.md`
- 狭いパス: 通した——反証 0 件・観察 1 件（O1）・素通りした変異 2 件（M4・M2）。O1（通常ファイルの下の実在しないパスが「消せなかった」で rc 1）は示せて受入基準 3（無いパスは 0）を破る——
  `マージ前の判断 = 推奨で決めて起票（後退・未達を含む）` の線の「満たしていない受入基準は、推奨を決める前にまず周が直す」で直す。起点 `5be8bd9d`・終点 `bac8d63e`
  陽性対照 `bash /private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/t1601/pc-enotdir.sh <formal-baseline.py> <作業場所>`: 起点 `5be8bd9d` で `消せなかった: …/tmp/file/m（辿れない: Not a directory）` rc=1（赤）、終点で `無かった: …` rc=0（緑）
- 当て直し: `5be8bd9d..bac8d63e` に別ティアの Verifier を 1 回。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1601-redo-1-20261127T103620Z.md`
- 当て直し: 通した——反証 0 件（`dev-loop:dev-loop-verifier`・sonnet。テンプレート 260 行は一致。陽性対照を走らせ直し、起点 rc 1・終点「無かった」rc 0。基準 3 を満たすと判定。`test-formal-baseline.py` は `OK: 試料 87 件・変異 70 件`）。
  受入基準 3 は満たした（満たしていない受入基準を直した——当て直しで消えた）
- PR: #1616（2026-11-27 作成）。PR 側の CI（`301fc52d`）: 全部 pass（deploy は skipping）
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い。`external-reviews.py` が 3）
- 再開点: PR を作り CI を見たところまで。マージは親（`マージ = 関門を通ればマージ`）

```dev-loop-gates
周の base: 0c824eace80033e869325f8fd757fb58bc766376
関門: Verifier 1 dd669a9d 反証=4
関門: /code-review 1 dd669a9d 指摘=7
関門: Verifier 2 2221cfb3 反証=0
関門: /code-review 2 2221cfb3 指摘=6
関門: 狭いパス 2221cfb3 5be8bd9d 反証=1
関門: 当て直し 5be8bd9d bac8d63e 反証=0
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
受入基準: 8 未証明
受入基準: 9 満たす
受入基準: 10 満たす
受入基準: 11 満たす
マージの反映: ドキュメントとプラグインの配布
```
（狭いパスの `反証=1` は観察 O1——Verifier は観察として挙げたが、受入基準 3 を破るので著者が反証に数えた。）
- 交絡を潰した手順: 受入基準 6 の実測（`scratchpad/t1601/ac6.sh`。一時の正本で 写す → `check` → `cleanup`）は、初回に素の `mktemp -d` で作った場所が `TMPDIR` を差し替えた試料で「外」になり消えなかった——
  macOS の `mktemp` が `TMPDIR` を読まないことが原因と `man mktemp` と単独の実行で確かめ、文面をテンプレートつきに直して同じ試料で消えることを見た（陽性・陰性の両側）。
  差し替えない実際の `TMPDIR`（末尾が `/`）でも、テンプレートつきで作った場所が消えることを見た

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 判定役の報告のパスを信じて消すか | 機械で確かめてから消す | 決めたこと 3 |
| 既に溜まった古いディレクトリを回収するか | しない | 持ち主・用途が分からない |
| `TMPDIR` が変わった（判定役と呼び出し元で違う）とき | 一時ディレクトリの外として消さずに名指しする | 消し過ぎより残すほうに倒す |

### 1 パス目の関門の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-A `cleanup` が名前（`formal-` の接頭辞）を縛らず、一時ディレクトリの下の他人のディレクトリを渡されたら消す。docstring の「守らないもの」の理由が弱い | 示せない（渡すのは報告の `モデルの場所` だけ。誤ったパスの報告は実物として無い） | 無し（1 は一時ディレクトリの下を消すと決めている） | 残課題 |
| V1-B・CR1-1 `HOME` が一時ディレクトリの下にある（`TMPDIR` が `HOME` かその祖先）と、`HOME` の中のディレクトリを消して 0 | 示せる（関門 2 体が `HOME=T/h` で `T/h/.ssh`・`T/h/Documents` を消して rc 0 を実行で示した） | 1（「`HOME` を含まず、その中にもない」） | 直す——`HOME` の中も消さずに名指しする。試料「HOME の中」と変異 |
| V1-C 変異の不足（`消した後も残っている` の分岐・git を起動できないときの戻り・`..` を含むパス） | 示せない（素通りする変異を当てていない） | 無し | 残課題 |
| V1-D 全対象が `判定できなかった` で 4 が空のとき、5 を回すかが文面で明示されていない | 示せない | 無し | 残課題 |
| CR1-2 文面（spec-review の 5・docstring）が「モデルのディレクトリには `-dumpTrace` の JSON が残る」と書くが、formal-checker.md は JSON をモデルのディレクトリの外の一時ファイルに書かせている | 示せる（`agents/formal-checker.md:62`「モデルのディレクトリの外の一時ファイル」） | 6（文面の事実の真偽——`cleanup` が消すものの主張） | 直す——文面から JSON の主張を外す（JSON と対応表の一時ファイルが残ることは残課題） |
| CR1-3 手順 5 が「`モデルの場所` を全部」渡せと言い、`作っていない` を渡すと偽の「消せなかった」（rc 1）が手順 7 に載る | 示せる（`cleanup /T/x 作っていない` で `消さなかった: 作っていない（絶対パスでない）` rc 1 を関門が実行） | 5（1 なら名指し——偽の名指しになる） | 直す——欄のうちディレクトリの絶対パスだけを渡し、`作っていない` の対象は渡さないと書く（formal-baseline も） |
| CR1-4 片付けに届かない経路（判定役の再実行・autopilot の段のやり直し・`check` が 0 にならない対象） | 示せない（起きた記録は無い） | 無し | 残課題 |
| CR1-5 formal-checker.md の状態グラフ（.dot）の作業場所がテンプレートなしの `mktemp -d` のまま | 示せない（判定役が自分で消す場所。残った記録は無い） | 無し | 残課題 |
| CR1-6 docstring と計画の「一時ディレクトリの実体の真下より深い」は字義では孫以下だが、実装は真下も消す | 示せる（docstring の文と `temp not in real.parents` の判定） | 1（原本の docstring が実装と違う規則を述べる） | 直す——docstring を「一時ディレクトリの実体の下（そのものは除く）」に直す。計画の基準 1 の文は変えず注記だけ足す |
| CR1-7 プラグインの README の表に `cleanup` が無い | 示せる（`plugins/spec-loop/README.md:59`） | 無し | 残課題 |

### 2 パス目の関門の指摘の採否（直す線: 既定）

Verifier 2 パス目: 反証 0 件（観察 2 点——HOME が TMPDIR の祖先だと全部を名指しする・V1-A の再掲。反証ではない）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1 `TMPDIR` が `HOME` の中（`TMPDIR=$HOME/tmp`）だと、V1-B の直しで足した「HOME の中」の判定が全部を止め、1 つも消さずに毎回 rc 1 | 示せる（関門が `TMPDIR=$S/home/.tmp/ HOME=$S/home` で rc 1 を実行） | 無し（基準 1 は「`HOME` を含まず、その中にもない」ものだけを消すと決めており、実装はそのとおり。main との比では消さないのは前と同じで後退ではない） | 残課題 |
| CR2-2 在るのに辿れない（親が `chmod 000`）ディレクトリを渡すと `lexists` が False になり「無かった」で rc 0、ディレクトリは残る | 示せる（関門が実行して rc 0・残ったのを示した） | 3（消せなかったものは名指しして 1） | 直す——`os.lstat` が `FileNotFoundError` のときだけ「無かった」、ほかの `OSError` は「消せなかった」で 1。消した後の確かめも同じ形。試料と変異 |
| CR2-3 `TMPDIR` が無い・書けないと `gettempdir()` が `/tmp`・cwd などに切り替わり、消してよい範囲が広がる | 示せる（`TMPDIR=<無いパス>` で `/tmp` を出した） | 無し（基準 1 は `gettempdir()` の実体と決めている） | 残課題 |
| CR2-4 autopilot の権限の点検（`autopilot-check.py` の `SPEC_REVIEW_SCRIPTS`）に `formal-baseline.py` が無い（前からの穴に `cleanup` が載った） | 示せない（拒まれた記録は無い） | 無し | 残課題 |
| CR2-5 手順の文面が `cleanup` の 2 の扱いを書かず、本体は例外のときそれまでの行を出さない | 示せない | 無し（基準 4 は 2 を返すこと） | 残課題 |
| CR2-6 CLAUDE.md の `formal-baseline.py` の要約が「その中のもの」に直っていない | 示せる（`CLAUDE.md:265` と docstring） | 無し（要約で、原本は docstring） | 残課題 |

### 狭いパスの指摘（`2221cfb3..5be8bd9d`）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| O1 通常ファイルの下の実在しないパスが「消せなかった（辿れない: Not a directory）」で rc 1 | 示せる（Verifier と著者の陽性対照。起点 `5be8bd9d` で rc 1） | 3（無いパスは 0） | 直した（`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）` の線の「まず周が直す」。`bac8d63e`・当て直しで消えた） |
| M4 変異「`FileNotFoundError` と `NotADirectoryError` を無いに数える」が素通り（ENOTDIR の試料が無い） | 示せる（陽性対照つき） | 無し | O1 の直しが正しい形そのものになり、試料「ファイルの下のパス」が逆向きの変異を殺す——解消 |
| M2 消した後の確かめの `except OSError: gone = False` を `True` にする変異が素通り | 示せない（到達させる入力を作れない——rmtree が成功した直後に lstat が ENOENT 以外で落ちる形） | 無し | 人間が決める（記録だけを推奨） |

### 周の途中の課題の振り分け（`周の途中の課題 = 外に出す`。found-lines の「振り分け」）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| V1-A `cleanup` が名前の接頭辞（`formal-`）を縛らない | #1601 Verifier 1 パス目 | 示せない | 記録だけ |
| V1-C 変異の不足（消した後の分岐・git を起動できないときの戻り・`..`） | #1601 Verifier 1 パス目 | 示せない | 記録だけ |
| V1-D 全対象が判定できなかったときの手順 5 の文面 | #1601 Verifier 1 パス目 | 示せない | 記録だけ |
| CR1-4 片付けに届かない経路（判定役の再実行・autopilot のやり直し・`check` が 0 にならない） | #1601 /code-review 1 パス目 | 示せない | 記録だけ |
| CR1-5 .dot の作業場所がテンプレートなしの `mktemp -d` | #1601 /code-review 1 パス目 | 示せない | 記録だけ |
| CR1-7 プラグインの README の表に `cleanup` が無い | #1601 /code-review 1 パス目 | 示せる（README の表） | 記録だけ（載っていないだけで、誤った結果を返す記述ではない） |
| `-dumpTrace` の JSON と対応表の一時ファイル（モデルのディレクトリの外）は誰も消さない | #1601 /code-review 1 パス目（CR1-2 の派生） | 示せない（溜まった実物を見ていない。この周の前からの形） | 記録だけ |
| CR2-1 `TMPDIR` が `HOME` の中だと全部を名指しして 1 つも消さない | #1601 /code-review 2 パス目 | 示せる（関門の試料） | 記録だけ（基準 1 どおりの安全側。main では何も消さないのと同じで後退ではない。`TMPDIR=$HOME/…` の利用者から実際に溜まると報告が来たら起票） |
| CR2-3 `TMPDIR` が無い・書けないと `gettempdir()` が `/tmp` などに切り替わる | #1601 /code-review 2 パス目 | 示せる（`TMPDIR=<無いパス>`） | 記録だけ（ふつうには作らない環境） |
| CR2-4 autopilot の権限の点検に `formal-baseline.py` が無い | #1601 /code-review 2 パス目 | 示せない | 記録だけ（この周の前からの穴） |
| CR2-5 手順の文面が `cleanup` の 2 の扱いを書かない | #1601 /code-review 2 パス目 | 示せない | 記録だけ |
| CR2-6 CLAUDE.md の要約が「その中のもの」に直っていない | #1601 /code-review 2 パス目 | 示せる（`CLAUDE.md:265`） | 記録だけ（原本の docstring は正しい。要約の言い落とし） |
| M2（上の狭いパスの表） | #1601 狭いパス | 示せない | 記録だけ |

直すの行: 0 件（起票の候補なし）。後退を示す指摘: なし。

## 手順 8 の記録

- この周の起票: 0 件（不在の周。起票の候補は PR コメントと親への報告に書く）
