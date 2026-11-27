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
| 1 | `cleanup` は一時ディレクトリ（`tempfile.gettempdir()` の実体）の真下より深い、symlink でない、リポジトリ（`--repo`、既定は cwd の git の根か cwd）と `HOME` を含まず、その中にもないディレクトリだけを消し、0 を返す | e | 本体 | 試料（`TMPDIR` を試料ごとのディレクトリに差し替える） |
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
- 交絡を潰した手順: 受入基準 6 の実測（`scratchpad/t1601/ac6.sh`。一時の正本で 写す → `check` → `cleanup`）は、初回に素の `mktemp -d` で作った場所が `TMPDIR` を差し替えた試料で「外」になり消えなかった——
  macOS の `mktemp` が `TMPDIR` を読まないことが原因と `man mktemp` と単独の実行で確かめ、文面をテンプレートつきに直して同じ試料で消えることを見た（陽性・陰性の両側）。
  差し替えない実際の `TMPDIR`（末尾が `/`）でも、テンプレートつきで作った場所が消えることを見た

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 判定役の報告のパスを信じて消すか | 機械で確かめてから消す | 決めたこと 3 |
| 既に溜まった古いディレクトリを回収するか | しない | 持ち主・用途が分からない |
| `TMPDIR` が変わった（判定役と呼び出し元で違う）とき | 一時ディレクトリの外として消さずに名指しする | 消し過ぎより残すほうに倒す |

## 手順 8 の記録

- この周の起票: 0 件（不在の周。起票の候補は PR コメントと親への報告に書く）
