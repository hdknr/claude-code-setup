# Issue #908 — 形式検査のモデルを `spec/formal/` に残し、次の周に渡す

不在の周（`/dev-loop:cruise 916 --absent` の起動・2026-11-08T08:00Z、利用者の確認（起動時・2026-11-08T08:00:42Z、配布を見せて確かめた））。cruise #916 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かない）。従う版は dev-loop 1.99.0（キャッシュ。SKILL.md 1861 行）。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-916`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #916 -->`。台帳の `decisions` は親が書く）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認・マージ前の判断: 台帳に線なし（止まる）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.73.0 → 0.74.0。spec-review に形式検査のモデルを残して次の回に渡す手順を足す——能力の追加。
  照合・差分・仕様書・条件 1 の走査から `spec/formal/` を外すのは緩める向きで、壊れる変更ではない）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #908`・`Refs #916`
- 並行する周: 無い（親の委譲文）
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.99.0/skills/cruise/scripts/run-serial.py` 越し

## 範囲（親 Issue #916 の「並べ方」）

**この周は Issue の前半（モデルを `spec/formal/` に保存して次の周に渡す）に絞る。** 出所: 親 Issue #916 の本文「#908 は調査コメントの提案のとおり前半……に絞る。
後半（反例のトレースを Red テストにする）は周の途中で別の Issue に切り出す。前半には、サインオフの照合（`check-signoff.py` が `spec/` を丸ごと比べる）と
版の差分（`merge-versions.py`・`diff-versions.py`）での `formal/` の扱いを決めることを含める」（cruise の起動時に利用者が確かめた親 Issue）。

- Issue の受入基準 3（反例が出た対象について `scaffold` の生成物にトレースを再現する Red テスト）は**この周の受入基準に入れない**——切り出した Issue が持つ（下の「切り出し」）。
  **これは受入基準を緩める指示に見えるので疑った**: 出所は Issue 本文ではなく親 Issue（利用者が cruise の起動時に確かめた一覧の本文）で、Issue の調査コメント（2026-11 の着手前の評価）も同じ切り分けを提案している。
  後半は消さずに Issue として残す（下）。

## 周の在り処

- ブランチ: `issue/908-save-formal-models`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-908`
- 起点コミット: `7e42c90`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `7e42c904f83248427572767eaf9eff3f7fd6db9e`

## 変更範囲

触る:
- `plugins/spec-loop/references/tree.md` — `spec/formal/` の置き方（対象ごとのディレクトリ・中身・誰が書くか・写しとして何に入れないか）の原本の節
- `plugins/spec-loop/skills/spec-review/SKILL.md` — Formal Checker に保存したモデルを渡す（手順 3）・報告のモデルを `spec/formal/` に残す（手順 3 の後）・止まるときに報告する（手順 7）
- `plugins/spec-loop/agents/formal-checker.md` — 保存したモデルから始める・前回の置いた前提を確かめ直す・報告にモデルの場所と前回のモデルの扱いを書く
- `plugins/spec-loop/scripts/merge-versions.py` — `spec/formal/` の定数と判別の関数（1 箇所に置く）。重ね方は変えない
- `plugins/spec-loop/scripts/check-signoff.py` — 比べる場所から `spec/formal/` を外す（`removed.csv` の行も）
- `plugins/spec-loop/scripts/diff-versions.py` — 版の差分に `spec/formal/` を出さない
- `plugins/spec-loop/scripts/build-proposal.py` — 仕様書の規模と「仕様と要求のファイル」に `spec/formal/` を入れない
- `plugins/spec-loop/scripts/check-spec-exit.py` — 未決定の印の走査で `formal/` を見ない
- `plugins/spec-loop/references/signoff-tags.md` — `check-signoff.py` の写し（比べる場所）
- `plugins/spec-loop/references/versions.md` — `diff-versions.py` の写し（版の差分）
- `plugins/spec-loop/references/spec-exit.md` — `check-spec-exit.py` の写し（未決定の印）
- `scripts/test-check-signoff.py` — 試料と変異
- `scripts/test-diff-versions.py` — 試料と変異
- `scripts/test-build-proposal.py` — 試料と変異
- `scripts/test-check-spec-exit.py` — 試料と変異
- `scripts/test-merge-versions.py` — 試料と原本の照合
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（6 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-908.md` — この計画
- `CLAUDE.md` — `check-signoff.py` の項の比べる中身の写し（`formal/` を除く）

触らない:
- 反例のトレースを Red テストにすること（`spec_ir.json` の形・`scaffold.py`・dev-loop の写し）——切り出した Issue に残す
- `scaffold.py`・`check-frozen.py`・`merge-versions.py` の重ね方（`spec/formal/` は今のままファイルとして重なる——次の版の Formal Checker が `build/merged/spec/formal/` から前の版のモデルを読む）
- feasibility の数え方（版の差分から `formal/` が消えるので、差分を読む数え方には自動で入らない）
- 綴りだけ違う `spec/Formal/`（大文字小文字）を写しと見なすこと——ふつうのファイルとして数える（既知の限界）
- 保存のスクリプト化（モデルを写すのは spec-review が `cp` で行う）——Issue に無い

複製の数（同じことを述べている箇所）: 「`spec/formal/` は写しなので、重ねるが照合・差分・仕様書・条件 1 の走査に入れない」を述べるのは **9 箇所**——
`tree.md`（原本）・`signoff-tags.md`・`versions.md`・`spec-exit.md`・`merge-versions.py`（定数）と 4 本のスクリプトの docstring（`check-signoff.py`・`diff-versions.py`・`build-proposal.py`・`check-spec-exit.py`）。
**分けない理由**: 1 つの判断（下の「仕様の穴」）の写しで、判別の式は `merge-versions.py` の 1 箇所に置き、他の 4 本はそれを読む。
文書の写しは「`tree.md` の『形式検査のモデル』を正とする」で指す。
「保存したモデルを次の回に渡す」は spec-review の SKILL と `formal-checker.md` の **2 箇所**（呼ぶ側と呼ばれる側で、分けられない）。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージで GitHub Pages とプラグインのカタログに入る。マージは親。

## 仕様の穴（不在の線で推奨により決めた）

**穴 1: `spec/formal/` を、承認の照合・版の差分・提案書の仕様書・抜ける条件 1 の未決定の印の走査に入れるか。**
親 Issue は「決めることを含める」と言うが、決めた値は書いていない。モデルは LLM が書くので、同じ仕様でも保存するたびに文字列が変わる（Issue の調査コメントのリスク 1・2）。

| 選択肢 | 何が起きるか |
| --- | --- |
| **A（推奨）: 写しとして外す。重ね合わせには入れる** | 2 つの承認の間に spec-review がモデルを保存し直しても照合は通る。版の差分・変更の提案書・仕様書の規模と一覧に `.tla` などが出ない。モデルの記録に「未定」と書いても条件 1 を止めない。前の版のモデルは `build/merged/spec/formal/` に重なって次の版に渡る |
| B: ほかの仕様のファイルと同じに扱う（スクリプトを変えない） | 承認の間にモデルを保存し直すと照合が 1（承認を取り直す）。版の差分と変更の提案書に「`spec/formal/…` 変更」が並ぶ。記録の文言で条件 1 が止まりうる |
| C: `docs/` の外（`spec-review/` と同じ置き方）に置く | 照合・差分には入らないが、Issue の受入基準（`spec/formal/` に残る）と `tree.md` の置き場所に反し、版ごとに重ならないので前の版のモデルを渡す仕組みを別に作る |

- **決めた値: A。** 推した理由: `references/spec-exit.md` が既に `formal/` を「仕様から書き起こした写し」として突き合わせの外に置いており、承認する人が見るのは仕様の本文である。
  B は承認と提案書に、承認する人が読まないファイルの揺れを持ち込む。C は Issue の受入基準に反する。
- 使った線と出所: `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線（台帳 `issue-916`））。
- 確認の Issue: （起票後に番号を書く）

## 切り出し（親 Issue の指示）

- 後半（反例のトレースを Red テストにする）を別の Issue に起票した: **#923**（2026-11-09。本文の先頭に `<!-- dev-loop: 子 #908 -->`）。受入基準は #908 の受入基準 3 を、競合する実装で赤・正しい実装で緑の陽性対照つきの形にしたもの

## 受入基準（不変条件 × 経路）

入口: **spec-review の手順 3**（1 回目・2 回目のレビューと狭いパスの Formal Checker）・**Formal Checker**（呼ばれる側）・**次の周・次の版の spec-review**・
**`check-signoff.py`**（proposal の関門・`build-proposal.py` が呼ぶ）・**`diff-versions.py`**（spec-review・feasibility・req-loop・`build-proposal.py` の「前の版からの変更」）・
**`build-proposal.py`**（仕様書の規模と一覧）・**`check-spec-exit.py`**（spec-review の手順 6・`scaffold.py` の生成前の確かめ・`build-proposal.py` の前提）・**`merge-versions.py`**（重ね合わせ。`scaffold.py`・spec-review が使う）・
**利用者**（`tree.md` などを読む）。

| # | 不変条件 | 経路（入口）と確かめ方 |
| --- | --- | --- |
| 1 | spec-review を 1 回回すと、Formal Checker が検査器を走らせた対象（結果が `反例なし`・`反例あり`）ごとに、走らせたモデルのファイルそのものと記録（対象・検査器と版・構成の大きさ・結果・陽性対照の壊し方・置いた前提）が作業中の版の `spec/formal/<対象>/` に残る（Issue の受入基準 1）。**確かめたと言うのは「判定役の報告が名指ししたファイルを spec-review の手順どおりに写せば、検査器が走らせたものと同じバイトが残る」まで**——spec-review を読んだ LLM が写す操作をするかは確かめていない（主張を弱めた。下の「実走の結果」。PR コメントに名指しする） | spec-review の SKILL と `formal-checker.md` を読む。**実走**: 本物の TLC と、worktree の `formal-checker.md` の定義で起こした判定役に小さい業務フローを渡し、報告のモデルの場所から手順どおりに写して `spec/formal/<対象>/` に残ることを見る（下の「実走」） |
| 2 | 2 回目（次の周・次の版）の Formal Checker が、保存したモデルを入力として受け取ったことを報告で示す——前回のモデルの扱い（直さず使った／直して使った（差分）／組み直した（理由））と、前回の置いた前提を確かめ直した結果（Issue の受入基準 2） | 同上。実走の 2 回目で、保存したモデルを渡した判定役の報告にその列が出る |
| 3 | 1 回目の Formal Checker が「保存したモデルが無い」ときも今までどおり組んで走らせる（前回のモデルを要求して止まらない） | 実走の 1 回目 |
| 4 | 2 つの承認の間に `spec/formal/` だけが変わっても照合は一致（0）。`removed.csv` で `spec/formal/` のファイルを消した行だけが違っても一致。陽性対照: `spec/` のほかのファイル・`spec/formalx.md`（接頭辞が同じ別のファイル）が違えば 1 | `test-check-signoff.py` の試料（本物の git とタグ） |
| 5 | 版の差分に `spec/formal/` の追加・変更・削除が出ない。陽性対照: 同じ版のほかの `spec/` のファイルの変化は出る | `test-diff-versions.py`（出力の全行を突き合わせる） |
| 6 | 提案書の仕様書の規模（仕様のファイルの数）と「仕様と要求のファイル」の一覧に `spec/formal/` が入らない。変更の提案書の「前の版からの変更」にも出ない | `test-build-proposal.py` |
| 7 | `spec/formal/` の中に未決定の印があっても条件 1 は 1 にならない。陽性対照: `spec/` のほかのファイルの印では 1 | `test-check-spec-exit.py` |
| 8 | 重ね合わせは `spec/formal/` を今までどおり重ねる——v2 の全体に v1 のモデルが出て、v2 の同じパスが置き換える（次の版に前の版のモデルが渡る経路） | `test-merge-versions.py`（試料を足す） |
| 9 | 写し（`tree.md`・`signoff-tags.md`・`versions.md`・`spec-exit.md`・4 本の docstring・spec-review の SKILL・`formal-checker.md`）が食い違わない。判別の式は `merge-versions.py` の 1 箇所で、4 本はそれを読む | `git grep -n 'formal' -- plugins/spec-loop` で並べて読む |
| 10 | 版が 3 種類の箇所で 0.74.0 に揃う。歯止めが全部緑 | `check-all.py`（run-serial 越し）・PR 側の CI |

**掛け算**: 受入基準を両方の関門 × 2 パス（2 パス目が無ければ 1 パス目の 2 つ）。

### 実走（受入基準 1〜3）

spec-review そのものを正本で回すのではなく、**Formal Checker の部分を本物で回す**: 一時ディレクトリに小さい正本（業務フロー 1 つの仕様）を作り、worktree の `formal-checker.md` の定義を `claude -p --agents` で渡した判定役に、
本物の TLC（利用者が入れた `~/.local/share/formal-tools/tla2tools.jar`）の呼び方で検査させる。1 回目の報告のモデルの場所から、spec-review の SKILL の手順どおりに
`spec/formal/<対象>/` に写し、2 回目はその保存したモデルを渡して報告に前回のモデルの扱いが出ることを見る。
**spec-review の Planner の部分（写す操作）は著者が SKILL の手順どおりに手で行う**——SKILL を読んだ LLM が同じことをするかは、この実走では確かめていない（下の「未証明・BLOCKED」）。

### 未証明・BLOCKED

- **未証明・BLOCKED なし。** 受入基準 1〜3 は下の実走で確かめた。**受入基準 1 は確かめた範囲まで主張を弱めた**（上の表の 1 の行。spec-review の Planner の写す操作を LLM がするかは、
  手段はある（`claude -p` と TLC で正本ごと回す）が回していないので、未証明にも BLOCKED にも入れず、主張から外した）。受入基準 4〜10 はテストと読みで確かめる。

### 実走の結果（2026-11-09）

試料の正本: `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/f7631199-07c6-418e-a902-1e3ccac0123f/scratchpad/fc908/repo`（在庫の引当の業務フロー 1 つ。
`CLAUDE.md` に `TLC の呼び方: java -cp /Users/hdknr/.local/share/formal-tools/tla2tools.jar tlc2.TLC`）。判定役は `claude -p --agents` で worktree の `formal-checker.md` の本文を定義にし、
ツールは `Read, Grep, Glob, Bash`、`model` は opus（呼ぶ側は sonnet）。委譲文は spec-review の手順 3 の Formal Checker の分（保存したモデルの行を含む）。

| 回 | 渡した保存したモデル | 報告（モデルの場所・前回のモデル） | 写した結果 |
| --- | --- | --- | --- |
| 1 | 無い | `$TMPDIR/formal-stock-alloc/`・`無かった`。反例なし（12 distinct states）・到達 2・陽性対照（読みと減らしを分けた版で `NonNeg` が破れる）。条件 4 は満たす | ディレクトリの 6 ファイル（`.tla` 2・`.cfg` 4）を `docs/v1/spec/formal/stock-reserve/` に `cp`。写した元と `diff -r` で差分なし。`README.md` に記録を書いて試料の正本に commit |
| 2 | `docs/v1/spec/formal/stock-reserve/` | `直さず使った`（保存版との `diff -u` で差分なし）。前回の置いた前提 4 つを 1 つずつ確かめ直し、(2)「1 回だけ受け付ける」を外した版で `Balance` が破れる反例を新しい指摘にした（条件 4 は満たさない） | ——（作業ディレクトリに TLC の `states/` と出力が残った。これを見て、写すファイルを一覧で名指しさせる形に直した——下） |
| 3（直した定義） | 同上 | `直さず使った`（保存した 6 ファイルを写して同じ 12 distinct states・反例なし）。**写すファイルの一覧**（8 ファイル。`states/` は消して一覧に入れない）。前提 (1) を外した版の反例を新しい指摘にした | 一覧の 8 ファイルを `cp`。8 つとも元と `cmp` で同じ |

- **受入基準 3（無いときも組む）**: 1 回目で確かめた。
- **受入基準 2（受け取ったことを報告で示す）**: 2・3 回目の報告に `前回のモデル` の列と前提の確かめ直しが出た。前回の前提を確かめ直したことで、1 回目が置いた前提に依る見落としを 2・3 回目が指摘にした（Issue の調査コメントのリスク 3 の手当てが効いた形）。
- **受入基準 1（残る）**: 報告が名指ししたファイルを手順どおりに写すと、検査器が走らせたものと同じバイトが `spec/formal/<対象>/` に残る。
- **確かめた範囲**: 判定役の側（定義と委譲文）は本物で回した。**spec-review の Planner の側（写す操作と `README.md`）は著者が手順を読んで手で行った**——spec-review の
  `SKILL.md` を読んだ別の LLM が同じ操作をするかは、この実走では確かめていない（正本の要求・仕様・Q&A 表を揃えて spec-review を丸ごと回す実走は回していない）。
  受入基準 1 の主張は「手順どおりに写せば残る」までに弱め、手順が読めば分かる形かは 2 つの関門に見せる（PR コメントにも名指しで残す）。
- **実走の途中で直したこと**: 2 回目の作業ディレクトリに TLC の `states/` と出力が残った。「ディレクトリのファイルをそのまま写す」だと、検査器の作業ファイルまで正本に入る。
  `formal-checker.md` に「写すファイルの一覧を報告に書き、作業ファイルと出力は入れない」、spec-review の手順と `tree.md` に「一覧のファイルだけ写す」を足し、3 回目で確かめた。

### 生成物

- 該当なし——図・生成ブロック（`skill-metrics.py` は dev-loop の `SKILL.md` だけを測る）・カタログの生成物を触らない。`scaffold/` も触らない。

## 関門の進捗（再開点）

- 割り目（手順 4・手順 6）: 割らない（cruise の周）
- 実装のコミット: `47c7061`（実走で直した 3 ファイルは次のコミット）
- 1 パス目の関門の起点（先に当てた関門に渡した時点の HEAD）: `2392902ade15338239736f48e0309189e6b50b4c`
- Verifier 1 パス目（2026-11-09・`dev-loop:dev-loop-verifier`・sonnet。読んだ委譲文 170 行（`wc -l` は 169）。報告は親に届かず、トランスクリプトから読んだ）: **反証 2 件**（V1・V2）。`git status` は開始・終了とも空。受入基準 4〜8 はテストで一致、1〜3 は弱めた範囲で一致
- `/code-review` 1 パス目（2026-11-09・high・fork）: **指摘 8 件**（CR1〜CR8）。差し戻し: 直すとした 3 件（CR1・CR5・CR6）を手順 4 で直す。CR4 は計画ファイルの記述（関門の対象外）だが、受入基準 1 の書き方を弱めた範囲に合わせて直す
- 交絡を潰した手順: 実走では、判定役が保存したモデルを本当に読んだかを、報告の言葉ではなく `diff -u`・`cmp` の結果（保存版と同じバイト・同じ 12 distinct states）と、
- 1 パス目の指摘対応のコミット: `7767ff93950c176e7a605e94ff955df5180fca81`（起点 `2392902` からの成果物の差分は 7 ファイル・0 行でない——2 パス目を回す）
- 割り目（手順 6 の 2 パス目の前）: 割らない（cruise の周）。残っているのは Verifier の当て直しと `/code-review` の 2 パス目の両方
- 2 パス目の経路の再導出: 指摘対応が足した入口は spec-review の手順 3 の「v2 以降の前の版の残りを `removed.csv` で消す」（`removed.csv` を書く入口）——
  `check-signoff.py` はその行を比べない（受入基準 4 の試料）、`merge-versions.py` は消す（受入基準 8 に試料を足した）。生成物の該当は変わらない（なし）。新しい未証明は無い
  1 回目に無かったファイル名（2 回目 `StockAllocResubmit`・3 回目 `StockAllocCancelSplit`）で見た。陽性対照: 1 回目（保存したモデル無し）の報告は `無かった` を返した。
- Verifier 2 パス目（2026-11-09・`dev-loop:dev-loop-verifier`・sonnet。読んだ委譲文 170 行。報告は親に届かず、トランスクリプトから読んだ）: **反証 0 件**。`git status` は開始・終了とも空。CR6 の pathspec を一時の git リポジトリで実測して一致
- `/code-review` 2 パス目（2026-11-09・high・fork）: **指摘 6 件**（P2-1〜P2-6）。直すとした 3 件（P2-1〜P2-3。どれも 1 パス目の CR1 の直し方から来た）を直す
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `daa42a538b78a90d10c8e66ea7ecee9701ad895b`
  テストは各スクリプトの試料に陽性対照（`spec/formalx.md`——接頭辞だけ同じ別のファイルは今までどおり数える）を置き、除外を外す・接頭辞で外す変異で赤になることを見た

### 1 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1 = CR2: `scaffold.py` の `check_source` は `source` が `spec/formal/` を指すのを断らない。`check-spec-exit.py` が `formal/` を見なくなったので、そこを指すと未決定の印が関門を素通りする（`.` で始まる場所を断るのと同じ穴） | 示せない（合成の試料でだけ出る——中間表現の `source` に形式検査のモデルの記録を書く形は、scaffold がふつうに作らない） | 無し | 残課題（記録だけ） |
| V2 = CR7: `<対象>` の名前を誰が決め、次の回にどう同じ対象を見つけるかが `SKILL.md` に無い。`README.md` の対象は `ファイル:行` で、仕様を直すと動く | 示せない（名前が揺れた実例は無い。実走は 3 回とも同じ名前で渡した） | 無し | 残課題 |
| CR1: v2 以降、前の版の同じ対象に今回写さなかったファイルが残り、重ね合わせた全体で新旧が混ざる（「前のファイルは消してから写す」は作業中の版にしか効かない） | 示せる——v1 に `Stock.tla`・`MC.cfg`、v2 に `Stock.tla`・`MC2.cfg` を置いて `merge-versions.py docs out` を走らせると、`out/spec/formal/stock/` に `MC.cfg`・`MC2.cfg`・`Stock.tla` の 3 つが残る | 1（走らせたモデルのファイルそのものが残る）・2（保存したモデルを受け取る） | 直す（前の版の残りは作業中の版の `removed.csv` に種類 `ファイル` で書いて消す、を手順と `tree.md` に足す。`test-merge-versions.py` に試料） |
| CR3: autopilot の権限の点検（`autopilot-check.py`）が、モデルを写す `cp` を見ていない | 示せない（autopilot で拒否された実例は無い。`claude -p` の起動は回していない） | 無し | 残課題 |
| CR4: 計画の受入基準 1 が弱めた範囲と食い違い、「未証明・BLOCKED なし」と「実走」の節が矛盾する | 示せる（計画ファイルの行） | 無し（計画ファイルは関門の対象外） | 直す（計画の記述。受入基準 1 の行に、弱めた範囲を書く） |
| CR5: `check-spec-exit.py` は `is_formal` を読まず `parts[0] == FORMAL_NAME` で外すので、`spec/formal` という名前のファイル（拡張子なし）も外す。`is_formal('spec/formal')` は偽 | 示せる——`a.md` と、`TBD` を書いた `formal`（ファイル）の仕様のディレクトリで `check-spec-exit.py` が 0 | 9（判別は 1 箇所で 4 本がそれを読む） | 直す（`is_formal` を読む。試料と変異） |
| CR6: `check-signoff.py` の `:(exclude)docs/vN/spec/formal`（末尾の `/` なし）は `spec/formal` という名前のファイルも外す | 示せる（同じ形。試料を足して当てる） | 9 | 直す（末尾の `/` を付けたディレクトリの形で外す。試料と変異） |
| CR8: `build-proposal.py` は `is_formal` を `signoff.versions`（別に読み込んだ `merge-versions.py`）から読み、`whole` は `diffs.merge_versions` から来る | 示せない（同じファイルを 2 度読み込むだけで、答えは同じ） | 無し | 残課題 |

### 2 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P2-1: CR1 で足した「前の版の残りを `removed.csv` で消す」は、同じ版の前の回が足した行を消す・見直すと言わない。次の回の一覧に同じファイルが戻ると「置きつつ消す」、同じ行をもう一度足すと「2 度消す」で重ね合わせが 1 | 示せる（P2-3 と同じ仕組み。下） | 1（spec-review を回すと残る——重ね合わせが止まり、手順 3 の判定役を起動できない） | 直す（下の 3 件まとめて） |
| P2-2: 「前の版の同じ対象（重ね合わせた全体）」は作業中の版まで重ねた全体なので、作業中の版の前の回が置いたファイルまで消す行が書かれ、「前の版までに無いものを消す」で 1 | 示せる（同上） | 1 | 直す |
| P2-3: `README.md` は判定役の写すファイルの一覧に入らないので、前の版の `README.md` も「今回写さなかったファイル」に当たり、消す行を書いた後に同じ版で `README.md` を書くと「置きつつ消す」で 1 | 示せる——v1・v2 に `spec/formal/stock/{Stock.tla,README.md}` を置き、v2 の `removed.csv` に `ファイル,spec/formal/stock/README.md` を書いて `merge-versions.py docs out` を走らせると「同じ版で置きつつ消している: spec/formal/stock/README.md」で作らない | 1 | 直す——**`removed.csv` で消す手順をやめ、`README.md` の記録に「モデルのファイル」の一覧を足し、次の回はその一覧のファイルだけを使う**（前の版の残りのファイルは重ね合わせに残っても使わない）。`removed.csv` を書く入口が無くなるので P2-1〜P2-3 は起きない |
| P2-4: `check-signoff.py` が `spec/formal/` を消す行を比べないので、予算側のタグにだけ `merge` が拒否する形式検査のモデルの行があっても一致になる（#372 の B の保証が `spec/formal/` の行で抜ける） | 示せない（合成の試料でだけ出る——予算側のタグにだけ、前の版に無いモデルのファイルを消す行を手で書く形は、ふつうに作られない。P2-3 の直しで spec-review は `removed.csv` にモデルの行を書かなくなる） | 無し | 残課題（記録だけ） |
| P2-5: `references/spec-exit.md` の実行の記録の「仕様の行」（`spec/` の Markdown の行数）が `spec/formal/<対象>/README.md` を外していない | 示せない（記録の数え方は LLM が数える決まりで、走らせて示す実物が無い） | 無し | 残課題 |
| P2-6: モデルをファイルで写すようになっても、判定役の報告に「モデルの全文」を含めさせており、親の文脈に積まれる | 示せない（失敗ではなく重さ） | 無し | 残課題 |

## 手順 8

- この周の起票: 2 件（確認の Issue 1 件（仕様の穴。不在の線で推奨により決めた）と、親 Issue #916 の指示で後半を切り出した #923）

## 既知の限界・決着済みの論点

- 後半（トレースを Red テストにする）はこの周の範囲の外（親 Issue の指示。切り出した Issue が持つ）。
- `spec/formal/` を写しとして外すのは推奨で決めた値（上の「仕様の穴」。確認の Issue が持つ）。
- 綴りだけ違う `spec/Formal/` は写しと見なさない（ふつうの仕様のファイルとして数える）。
- モデルを `spec/formal/` に写すのは spec-review（LLM）が手順に従って行う——スクリプトで強制しない（Issue に無い）。
