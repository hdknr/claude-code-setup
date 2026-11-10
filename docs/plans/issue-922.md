# Issue #922 — spec-review の確かめが Alloy を引数なしで呼び、GUI が開いて止まる

不在の周（`/dev-loop:cruise 916 --absent` の起動・2026-11-08T08:00Z、利用者の確認（起動時・2026-11-08T08:00:42Z、配布を見せて確かめた））。cruise #916 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かない）。従う版は dev-loop 1.103.0（キャッシュ。SKILL.md 1861 行）。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-916`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #916 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認・マージ前の判断: 台帳に線なし（止まる）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.74.0 → 0.75.0。Alloy の確かめのスクリプトを足す——能力の追加。Alloy を `command -v` で探さなくなる壊れる変更を含むので、0.x の決まりどおり minor で上げ、移行を `references/spec-exit.md` に書く）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #922`・`Refs #916`
- 並行する周: #923（spec-loop の版を上げる——版の行が取り合いになりうる。マージの直前の取り込みと上げ直しは親の指示で行う）
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/cruise/scripts/run-serial.py` 越し
- 台帳の決まった判断（確認の Issue）: #928（#908 の周）。閉じない

## 周の在り処

- ブランチ: `issue/922-alloy-cli-probe`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-922`
- 起点コミット: `ad90fbc`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `ad90fbca0e97982991e7a34752c74e4eb6108e54`

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-alloy.py` — 新規。正本の `CLAUDE.md` の `Alloy の呼び方:` の行を読み、`exec` の無い・`gui` の在る呼び方は走らせずに 4、それ以外は小さいモデル 2 つを CLI で検査させて Alloy が在るかを決める。書き方の原本
- `plugins/spec-loop/scripts/check-tlc.py` — 宣言の読み方（コードフェンスを飛ばして行頭の鍵を拾う）を `scan_declarations` に出し、`check-alloy.py` が読み込む（写さない）。振る舞いは変えない
- `plugins/spec-loop/scripts/autopilot-check.py` — `SPEC_REVIEW_SCRIPTS` に `check-alloy.py`（各起動が spec-review の手順 3 で呼ぶ）
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 「はじめに」の表・手順 3 の確かめ（Alloy は `check-alloy.py`。引数なし・`gui` で呼ばない）・用意のしかた・Formal Checker に渡す道具
- `plugins/spec-loop/agents/formal-checker.md` — Alloy は渡された呼び方だけ・引数なし・`gui` で呼ばない・`exec` の出力のディレクトリ
- `plugins/spec-loop/README.md` — 「中身」の表と「前提」の「Alloy の用意」
- `plugins/spec-loop/references/spec-exit.md` — Alloy は呼び方の行だけで使う・0.75.0 の移行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — spec-loop の版
- `docs/plugins/index.md` — 公開ページの spec-loop の節（Alloy の前提・Formal Checker の行）
- `scripts/test-check-alloy.py` — 新規（変異テストを含む）
- `scripts/check-all.py` — 収録
- `.github/workflows/plugins.yml` — CI のステップ
- `CLAUDE.md` — `check-alloy.py` と `test-check-alloy.py` の項
- `docs/plans/issue-922.md` — この計画ファイル

触らない:

- autopilot の起動時の点検に Alloy の項目を足すこと（Alloy は必須ではない。足りなければ spec-review の手順 3 が訊く場面なので、autopilot は止まる）
- Alloy を必須の前提にすること・外す宣言（Issue に無い）
- `scripts/test-fence-copies.py`（フェンスの読み方の写しは増やさず、`check-tlc.py` を読み込む）
- dev-loop

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージで GitHub Pages とプラグインのカタログに入る。マージは親。

## 設計（この周で決めたこと）

- **Issue の推奨（選択肢 1）を採る**——TLC と同じ形。選択肢 2（headless だけ）は呼び方の決め方を残さず、選択肢 3（無い扱い）は使える Alloy を使えなくする。
  選択肢 2 は保険として 1 に重ねる（`JAVA_TOOL_OPTIONS` に `-Djava.awt.headless=true` を足す。GUI の形で走らせて確かめてはいない）。
- **行の形**: `Alloy の呼び方: <コマンド>`——**サブコマンド `exec` まで含めて書く**（Issue の例 `alloy exec`）。後ろにモデルのファイル（`<名前>.als`）を足し、モデルのディレクトリで `sh` に渡す。
  **語 `exec` が無い・語 `gui` が在る呼び方は、確かめのために起こさず 4**（引数なし・`gui` の形を走らせない、を構造で守る）。
- **確かめ方**: 通るモデル（`run someA` が `SAT`——到達できる、`check emptyOrNot` が `UNSAT`——反例なし、終了コード 0）と、
  違反するモデル（`check alwaysEmpty` が `SAT`——反例あり）。Formal Checker の「空振りを疑う」の 2 つ（到達・陽性対照）と同じ形。
- **Alloy は必須ではない**——spec-review の手順 3 が権限・ロールを対象に選んだときだけ呼ぶ。外す宣言・`--autopilot` は持たない。
- **Formal Checker**: Alloy は渡された呼び方だけを使い、渡されなければ権限・ロールは「検査できなかった」。`command -v` で探さない（TLC と同じ）。

### Alloy の CLI の実測（この周。Mac Studio・Alloy 6.2.0・Java 22。引数なし・`gui` の形は走らせていない）

- `java -Djava.awt.headless=true -jar ~/.local/share/formal-tools/alloy.jar help`（60 秒の時間切れつき）: 終了コード 0、サブコマンドの一覧（`exec`・`gui`・`commands`・`version` など）
- `help exec`: `exec` の引数（`-f`・`-o`・`-t`・`-q` など）
- `exec Probe.als`（通るモデル）: 終了コード 0、標準エラーに `00. run   someA … SAT`・`01. check emptyOrNot … UNSAT`、モデルの隣に `Probe/`（`receipt.json`・解の `.md`）
- `exec Broken.als`（違反するモデル）: 終了コード 0、標準エラーに `00. check alwaysEmpty … 1/1 SAT`
- 構文の誤り: 終了コード 1。同じモデルの 2 回目: `The output directory … contains files. Delete them or use the -f option` と終了コード 1。`-f` を足すと 0
- `alloy exec`（利用者のラッパー `exec java -jar …/alloy.jar "$@"`）: headless 無しでも上と同じ結果で、数秒で終わった
- `check-alloy.py` を本物に当てた結果: `Alloy の呼び方: alloy exec`→0、`java -jar <jar> exec`→0、`java -jar /nonexistent/alloy.jar exec`→1、`alloy`→4（走らせない）、`alloy gui`→4（走らせない）、行なし→1。
  正本のディレクトリには `CLAUDE.md` だけが残った

## 受入基準（不変条件 × 経路）

入口: **利用者**（README・公開ページ・`spec-exit.md` の移行を読み、`CLAUDE.md` に行を書く）・**spec-review の手順 3**（1 回目・2 回目の確かめ。権限・ロールを対象に選んだとき）・
**autopilot の各起動**（`round1`・`round2`・`narrow` の段で spec-review の手順 3 を回す——点検の一覧）・**Formal Checker**（呼び方を使う）・**`check-alloy.py` を直に呼ぶ利用者**。

| # | 不変条件 | 経路（入口）と確かめ方 |
| --- | --- | --- |
| 1 | spec-review の起動前の確かめが Alloy を引数なし・`gui` の形で呼ばない（Issue の受入基準 1） | 手順 3 が `check-alloy.py` を呼ぶ（本文）。`check-alloy.py` は語 `exec` の無い・語 `gui` の在る呼び方を走らせずに 4（走ったら印を書く偽物のテスト・本物の `alloy`・`alloy gui` の行で 4） |
| 2 | Formal Checker が Alloy を引数なし・`gui` の形で呼ばない・`command -v` で探さない（同 1） | `formal-checker.md` の本文。テストが本文を見る |
| 3 | 確かめは小さいモデルを CLI で検査させ、GUI を開かずに終わる。陽性対照: 呼び方の行が無い・壊れているとき「無い」（同 2） | 本物の Alloy 6.2.0 で `alloy exec`・`java -jar <jar> exec` が 0、jar の場所が違う呼び方・行なしで 1。偽の Alloy で、何にでも反例なし・何にでも反例あり・到達できない・終了コードが 0 でない呼び方が 1。時間切れで 1 |
| 4 | README の「前提」に、Alloy の入れ方と `CLAUDE.md` に書く呼び方が載る（同 3） | README の「Alloy の用意」。テストが行頭の行（`exec` を含み `gui` を含まない）と `alloy.jar` を見る。書いた例の行を `check-alloy.py` が読む |
| 5 | `PATH` に `alloy` が在っても、呼び方の行が無ければ「無い」（`command -v` で探さない） | テスト（`PATH` の先頭の偽の `alloy`） |
| 6 | 確かめが正本に書かない（`exec` の `<名前>/` を正本に作らない） | テストの正本の写し（前後で同じ）と、本物の Alloy の実行のあとの正本のディレクトリ |
| 7 | `check-tlc.py` の振る舞いが変わらない（読み方を関数に出しただけ） | `test-check-tlc.py` が緑（変異 15 件を全部殺す） |
| 8 | autopilot の点検の一覧に `check-alloy.py` が入る（各起動が spec-review の手順 3 で呼ぶスクリプトの許可を点検する） | `autopilot-check.py` の `SPEC_REVIEW_SCRIPTS`。`test-autopilot-check.py` が緑（実在の確かめを含む） |
| 9 | 写し（README・spec-review・Formal Checker・`spec-exit.md`・公開ページ・リポジトリの `CLAUDE.md`）が原本（`check-alloy.py` の docstring）と食い違わない | `git grep -n 'Alloy' -- plugins docs CLAUDE.md ':!docs/plans'` で全部を並べて読む |
| 10 | 版が 3 種類の箇所で 0.75.0 にそろい、0.x の壊れる変更の移行が `references/` に在る | `check-plugin-versions.py`・`check-version-bump.py`。`spec-exit.md` の「0.75.0 より前から使っている正本の移行」 |

必須要件の掛け算: 受入基準を両方の関門に渡す × 2 パス = 4 つの受け渡し（2 パス目が「該当なし」なら 2 つ）。

### 未証明・BLOCKED

- **未証明**: `JAVA_TOOL_OPTIONS` の headless で GUI が開かなくなるか——GUI を起動する形は走らせない（親の指示と Issue）。保険で、受入基準 1 は「走らせない」で守る。
- **未証明**: Alloy 6.2.0 以外の版の出力の形（結果の行・標準エラーに出ること）。利用者の MacBook の Alloy の版と、#922 で実際に呼んだ行は記録に無い（Issue）。
- **未証明**: 利用者の MacBook で spec-review が確かめを `check-alloy.py` で回したときに止まらないこと——ここで確かめたのは Mac Studio（同じ利用者の別の Mac）の Alloy 6.2.0。
- BLOCKED: なし。

### 生成物

- 該当なし——図・生成ブロック（`skill-metrics.py` は dev-loop の `SKILL.md` だけを測る）・カタログの生成物を触らない。

### 複製の数

Alloy の呼び方と確かめ方を述べるのは **9 箇所**——`check-alloy.py` の docstring（原本）・README（中身の表・Alloy の用意）・spec-review の SKILL（はじめにの表・手順 3・用意のしかた・Formal Checker に渡す道具）・
`formal-checker.md`・`spec-exit.md`・公開ページ・リポジトリの `CLAUDE.md`。**分けない理由**: 1 つの決まりを入口ごとに指すだけで、書き方の細部と終了コードは原本にだけ置き、他は「`check-alloy.py` の docstring を正とする」で指す。

## 未解決の判断・確認待ち

- なし（仕様の穴なし——Issue が推奨を挙げ、それを採った）。

## 関門の進捗（再開点）

- 割り目（手順 4）: 割らない（cruise の周）
- 実装のあとの `check-all.py`（run-serial 越し・2026-11-10）: 70 本のうち 69 本が緑、`test-render-diagrams.py` だけ「変異が生き残った: プロセスグループを止めない」で赤。
  この周はそのテストも本体（`render-diagrams.py`）も触っていない（`git diff ad90fbc` に無い）。同じテストを run-serial 越しに単独で回し直すと緑（試料 60・変異 53）。
  `check-all.py` の中の並列（28）の負荷で時間に依る変異が生き残った形と読むが、確かめてはいない——両方の結果をここに残す
- 1 パス目の関門の起点（先に当てた関門に渡した時点の HEAD）: `2b1b410b965332aaab94d8fdcd3f701a0f31681f`
- Verifier 1 パス目（2026-11-10・`dev-loop:dev-loop-verifier`・sonnet。読んだ委譲文 170 行（`wc -l` は 169）。報告は親に届かず（`SendMessage` で催促し、トランスクリプトから読んだ））: **反証 2 件**（V1・V2）。`git status --porcelain` は開始・終了とも空
- `/code-review` 1 パス目（2026-11-10・high・fork。委譲文は貼った。報告は親に届かず、トランスクリプトから読んだ）: **指摘 8 件**（CR1〜CR8）。`git status --porcelain` は開始・終了とも空
- 差し戻し: 直すとした 3 件（V1・CR1・CR2）を手順 4 で直した——`check_form` がシェルの組み立て（`;&|<>()$` ``#`` `\` と改行）・先頭の組み込み（`exec` など）とシェル（`sh` など）・クォートの中の `gui` を走らせずに 4 にする。
  spec-review は `check-alloy.py` が 0 のときだけ呼び方を Formal Checker に渡し、Formal Checker は渡された呼び方でも形が違えば走らせない。README・`spec-exit.md` に「ラッパーの本文を写さない」。
  CR7 の終了コードの表の 4 は、この直しで行を書き直したときに「語に割れない」も入れた。本物の Alloy 6.2.0 で `alloy exec`・`java -jar <jar> exec` が 0、`exec java -jar <jar>`・`alloy exec || alloy` が 4（走らせていない）
- 1 パス目の指摘対応のコミット: `7e35363bbad7970b266f8d927d0f246ba8d1fca6`（起点 `2b1b410` からの成果物の差分は 6 ファイル——0 行でない。2 パス目を回す）
- 2 パス目: Verifier の当て直しと `/code-review` の 2 パス目の**両方**を当てる（base は同じ `ad90fbc…`）。経路の再導出: 指摘対応が足した入口は spec-review から Formal Checker への受け渡し（`用意せずに進める` の経路）——不変条件 2 の経路に入れて渡す。
  新しい未証明: 先頭より後ろで別のシェルを起こす形（`env sh -c …`）は見分けない（docstring の「守らない」）。生成物の該当は変わらない（なし）
- 割り目（手順 6 の 2 パス目の前）: 割らない（cruise の周）
- 1 パス目の指摘対応のあとの `check-all.py`（run-serial 越し）: 70/70 緑（`test-render-diagrams.py` も緑）
- Verifier 2 パス目（2026-11-10・`dev-loop:dev-loop-verifier`・sonnet。読んだ委譲文 170 行。報告は親に届かず（SubagentHandback が「親はすでに終了」で失敗）、トランスクリプトから読んだ）: **反証 1 件**（V3）。`git status --porcelain` は開始・終了とも ` M docs/plans/issue-922.md`
- `/code-review` 2 パス目（2026-11-10・high・fork。委譲文は貼った。報告はトランスクリプトから読んだ）: **指摘 7 件**（CR2-1〜CR2-7）。`git status --porcelain` は開始・終了とも ` M docs/plans/issue-922.md`
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `b0b654b211aa6d5f922d4c4e7cdcac28223defd1`
- 2 パス目の指摘対応: 直すとした 4 件（V3・CR2-1〜CR2-3）を直した——先頭の拒否の一覧（組み込み・シェル）を許可の一覧（`java` か名前に `alloy` を含むコマンド）に替え、シェルの組み立ての文字にブレースとグロブ（`{}*?[]`）を足した。
  docstring に `-q` を足さないこと（本物の Alloy 6.2.0 で `exec -q` は結果の行が出ず 1）と、`$HOME`・括弧を含むパスはクォートの中でも 4 であることを書いた。本物で `alloy exec`・`java -jar <jar> exec` が 0、`trap alloy EXIT exec` が 4（走らせていない）
- 狭いパスの終点（2 パス目の指摘対応の最後のコミット）: `0736f25e679f779d4c10a8b7a117feb40fd784da`（起点の子孫であることを確かめた）
- 狭いパス（2026-11-10・`dev-loop:dev-loop-verifier`・sonnet。報告は親に届かず（SubagentHandback が「呼び出し元はすでに終了」）、トランスクリプトから読んだ）: **反証 1 件**（F1）。
  変異: 赤 2（`head == HEAD_JAVA or ` の除去・`.lower()` の除去——後者は当て先の行が変わった失敗で振る舞いの判別ではない）・素通り 3（`SHELL_SPECIAL` から `]`・`*`・`}` を単独で外す）。`git status --porcelain` は開始・終了とも空
- **満たしていない受入基準**: 不変条件 1・2——狭いパスの F1（名前に `alloy` を含む環境変数の代入 `ALLOY=1 exec <alloy>` が許可の一覧を素通りし、サブコマンドの無い形を走らせる。偽物で実走）。狭いパスの指摘は直さない（`マージ前の判断` の線なし）——マージするかは人間が決める
- 2 パス目の指摘対応のあとの `check-all.py`（run-serial 越し）: 70/70 緑
- PR を出す前に main（`5bd739f`。#929 が CI の check ジョブを 7 つに分けた）を取り込んだ——`plugins.yml` の衝突を、Alloy のステップを残し main の分け方を取って解いた（取り込みの `8a885a9`）。版は main も 0.74.0 のままなので上げ直していない。取り込んだ後の `check-all.py`（run-serial 越し）: 70/70 緑
- 交絡を潰した手順: 偽の Alloy の試料で、陽性対照（通る呼び方で 0・走ったら印）と陰性（反例なし・反例あり・到達できない・終了コード 0 以外で 1、`exec` の無い・`gui` の在る形で 4 かつ印なし）を並べた。
  偽の Alloy はモデルを読まないので、モデルが本物の Alloy で期待どおりの結果を出すかは本物の Alloy 6.2.0 で当てた（上の「Alloy の CLI の実測」）

## 既知の限界・決着済みの論点

- autopilot の起動時の点検に Alloy の項目は足さない（Alloy は必須ではない。範囲の外）。
- `exec` を語として含むかで形を見る（`shlex` の語）。ラッパーの中で `exec` を足す形は 4——docstring の「守らない」。
- HTML コメントの中の行も読む（`check-tlc.py` の読み方と同じ）。
- `JAVA_TOOL_OPTIONS` の headless は保険で、GUI の形で走らせて確かめていない（未証明）。

### 1 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1: シェルの組み立てで語の判定を素通りする——`<alloy> exec \|\| <alloy>` はサブコマンドの無い `<alloy> Probe.als` を走らせ、`sh -c '<alloy> gui' exec` は `gui` がクォートの中で語に出ない | 示せる（走ったら印を書く偽物で Verifier が実走） | 1（確かめが引数なし・`gui` の形を呼ばない） | 直す |
| CR1: シェルの組み込みの `exec` を先頭に置いた `exec <alloy>`（利用者のラッパーの本文 `exec java -jar … "$@"` を写した形）が語 `exec` で通り、`sh` が `exec <alloy> Probe.als`（サブコマンドなし）を走らせて 0。`<alloy> # exec`・`<alloy>; : exec` も通る | 示せる（偽物で `/code-review` が実走） | 1 | 直す |
| CR2: spec-review は `check-alloy.py` が 0 でなくても（`用意せずに進める`）呼び方の行を Formal Checker に渡し、Formal Checker は `exec` の無い呼び方を断らない——`Alloy の呼び方: alloy` で `alloy perm.als` を走らせる | 示せる（spec-review の SKILL の手順 3 と Formal Checker に渡す道具の文面・`formal-checker.md` の文面） | 2（Formal Checker が引数なし・`gui` の形で呼ばない） | 直す |
| V2: `probe()`・`run_model()` は `check_form` を通らない（`main`→`judge` の経路だけが通る） | 示せない（それらを直に呼ぶ呼び出し元が無い） | 無し | 残課題 |
| CR3: 偽の Alloy はモデルを読まないので、確かめのモデルを壊しても（空のモデルでも）テストが緑 | 示せる（`/code-review` が外の写しで空のモデルにして緑） | 無し（今のモデルは本物の Alloy 6.2.0 で判別することを確かめた。回帰の歯止めの穴） | 残課題 |
| CR4: headless の保険は確かめの中だけで、Formal Checker が走らせるときには掛からない | 示せない（確かめを通り、GUI に入る呼び方の実物が無い） | 無し | 残課題 |
| CR5: `run_model` が `check-tlc.py` の写し（時間切れとプロセスグループの止め方が 2 箇所） | 示せない（写しが食い違って起きた失敗は無い） | 無し | 残課題 |
| CR6: docstring が「BOM を外すのは `check-tlc.py` の読み方と同じ——その関数を読み込んで使う」と読めるが、`scan_declarations` は BOM を外さず、`check-alloy.py` が自分で外す | 示せる（docstring と `check-tlc.py` の文面） | 無し | 残課題 |
| CR7: 終了コードの表の 4 に「語に割れない（閉じないクォート）」が無い | 示せる | 無し | 残課題 |
| CR8: `check-tlc.py` の docstring の「守らない」が「Alloy——#912 の範囲の外」のまま（`scan_declarations` を `check-alloy.py` が読み込むようになった） | 示せる（文面） | 無し | 残課題 |

### 2 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V3: 先頭に環境変数の代入か `!` を置く `FOO=1 exec <alloy>`・`! exec <alloy>` が素通りし、サブコマンドの無い `<alloy> Probe.als` を走らせる | 示せる（Verifier が引数を記録する偽物で実走。`RAN: Probe.als`） | 1 | 直す |
| CR2-1: ブレースの展開 `<alloy> {gui,} exec` が素通りし、`sh` が `gui exec Probe.als` に展開する | 示せる（`/code-review` が偽物で実走） | 1 | 直す |
| CR2-2: 組み込みの `trap` で始まる `trap <alloy> EXIT exec` が素通りし、終わりに引数なしの `<alloy>` を走らせる | 示せる（同上） | 1 | 直す |
| CR2-3: `tcsh -c <alloy> exec`・`csh -c …` が素通りし、引数なしの `<alloy>` を走らせる（先頭のシェルの一覧に無い） | 示せる（同上） | 1 | 直す |
| CR2-4: autopilot の狭いパスの段は別の起動で、`check-alloy.py` の結果を持たない——spec-review の「0 を返したときだけ渡す」と手順 5 の「手順 3 の確かめは引き継ぐ」から、権限・ロールが判定できなかったになりうる | 示せない（autopilot をここで回していない。文面からの推論） | 無し | 残課題（この周が持ち込んだ後退になりうる——振り分けで扱う） |
| CR2-5: README の例の行を `check_form`・`judge` に通すテストが無い（語だけを見る） | 示せる（例を 4 になる形に変えてもテストが緑のはず、という推論。今の例は 0） | 無し（今の例は本物で 0 を確かめた） | 残課題 |
| CR2-6: `$HOME/…`・クォートの中の `(` を含むパスも 4（docstring は「クォートで囲めばよい」と書く） | 示せる（`/code-review` が実走で 4） | 無し（4 は「判定できない」で、走らせない側に倒れる。利用者は絶対パスで書き直す） | 残課題 |
| CR2-7: 根の原因は文字列を `sh` に渡して拒否の一覧で守ること——一覧は毎パス破られる。シェルを通さずに語で走らせる案 | 示せない（設計の提案） | 無し | 残課題（ただし 1〜3 の直しで、先頭の拒否の一覧を許可の一覧（`java` か名前に `alloy` を含むコマンド）に替えた——Formal Checker は `Bash`（シェル）で走らせるので、確かめもシェルの意味に揃える） |

### 狭いパスの指摘の採否（採否は人間が決める）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| F1: `check_form` が先頭の語を `alloy` を含むかで許すので、`ALLOY=1 exec <alloy>`・`alloy=1 exec <alloy>`・`X=alloy exec <alloy>`（環境変数の代入）が素通りし、`sh` がサブコマンドの無い `<alloy> Probe.als` を走らせる。`FOO=1 exec <alloy>`・`! exec <alloy>` は 4 | 示せる（Verifier が引数を記録する偽物を `/bin/sh -c` で実走。`RAN: Probe.als`） | 1・2（V3 の直しの穴） | 人間が決める（満たしていない受入基準。直すなら先頭の語に `=` を含むものを許さない） |
| 素通りした変異: `SHELL_SPECIAL` から `]`・`*`・`}` を単独で外してもテストが緑 | 示せる（Verifier の変異）。陽性対照: 確かめの cwd は新しい一時ディレクトリなので、グロブは展開する名前を持たない | 無し | 人間が決める（記録だけ——試料の穴。`}` は `{` が残る限り等価に近い） |

### 振り分け（`references/found-lines.md`。cruise の周・`周の途中の課題 = 台帳に足して直す`）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け | 仕様の穴か | 行き先 |
| --- | --- | --- | --- | --- | --- |
| V2: `probe()`・`run_model()` が `check_form` を通らない | #922 Verifier 1 パス目 | 示せない | 記録だけ（呼び出し元が無い） | — | — |
| CR3: 偽の Alloy がモデルを読まない（モデルを壊してもテストが緑） | #922 /code-review 1 パス目 | 示せる（外の写し） | 記録だけ（試料の穴） | — | — |
| CR4: headless の保険が Formal Checker の実行に掛からない | #922 /code-review 1 パス目 | 示せない | 記録だけ | — | — |
| CR5: `run_model` が `check-tlc.py` の写し | #922 /code-review 1 パス目 | 示せない | 記録だけ | — | — |
| CR6: docstring の BOM の書き方が実装と食い違う | #922 /code-review 1 パス目 | 示せる（文面） | 記録だけ（文言） | — | — |
| CR7: 終了コードの表の 4 に「語に割れない」が無い | #922 /code-review 1 パス目 | 示せる | 捨てる（1 パス目の直しで表の 4 を書き直したときに入れた） | — | — |
| CR8: `check-tlc.py` の docstring の「Alloy——範囲の外」が古い | #922 /code-review 1 パス目 | 示せる（文面） | 記録だけ（文言） | — | — |
| CR2-4: autopilot の狭いパスの段が `check-alloy.py` の結果を持たず、権限・ロールが判定できなかったになりうる | #922 /code-review 2 パス目 | 示せない（autopilot を回していない。文面からの推論） | 記録だけ（迷った——この周が持ち込んだ後退でありうる。親がマージの前に読み直す） | — | — |
| CR2-5: README の例の行を `check_form` に通すテストが無い | #922 /code-review 2 パス目 | 示せない（今の例は本物で 0） | 記録だけ（試料の穴） | — | — |
| CR2-6: `$HOME`・クォートの中の括弧を含むパスも 4 | #922 /code-review 2 パス目 | 示せる（実走で 4） | 記録だけ（走らせない側に倒れる。docstring の「守らない」に書いた） | — | — |
| CR2-7: 文字列を `sh` に渡して拒否の一覧で守る設計 | #922 /code-review 2 パス目 | 示せない（設計の提案） | 記録だけ | — | — |
| 狭いパスの素通りした変異（`]`・`*`・`}`） | #922 狭いパス | 示せる | 記録だけ（試料の穴） | — | — |

（F1 はこの周の受入基準を破る行なので振り分けに来ない——上の「満たしていない受入基準」。）

- この周の起票: 0 件（起票の承認は不在のため訊いていない）
