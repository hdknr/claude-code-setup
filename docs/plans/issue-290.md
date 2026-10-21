# Issue #290 — scaffold が書く Issue の本文と、spec-gap の照合が噛み合わない

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 本文の指紋を機能単位にし、撤去の本文の再現のパスを直す。印を `v3` に上げる
- `plugins/spec-loop/references/handoff-issue.md` — 本文の形の原本（印・節・指紋）
- `plugins/spec-loop/references/tree.md` — 「本文が sha256 を持つのは」の 1 段落
- `plugins/spec-loop/references/versions.md` — 本文の sha256 を述べる 2 箇所
- `plugins/spec-loop/skills/*/SKILL.md` — 版のバナー（5 本）。scaffold の 40 行目の言い回し
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 照合のしかた（v3 の指紋・撤去・前の形の v2）
- `plugins/dev-loop/skills/dev-loop/scripts/spec-fingerprint.py` — 新規。機能の指紋を出す
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 1 の印（v3 を足す）と版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 2 つのプラグインの版
- `scripts/test-scaffold.py` — 本文の検査・境界の写しの突き合わせ・試料・変異
- `docs/plugins/index.md` — 公開ページの 1 文（sha256 → 機能の指紋）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロックだけ（dev-loop の `SKILL.md` を触ったので
  `skill-metrics.py` で作り直す。手では書かない。受入基準は下の「生成物の該当判定」がそのまま覆う）
- `docs/plans/issue-290.md` — この計画ファイル
- `CLAUDE.md` — 構成の一覧に dev-loop の `spec-fingerprint.py` を足す

触らない:

- 登録済みの Issue の本文（v1・v2 の形のまま残る。dev-loop が読み続ける）
- `merge-versions.py`（出力先を変えれば前の版の全体も作れる——撤去の本文はそれを使う）
- P1-11（同じ版の中で作り直した本文を手順 6 が登録しない）・P1-10・CR6 など #264・#219 の他の残課題
- 指紋に `impl_module` と Q&A 表を入れること（Red テストの sha256 と本文の Q&A の表が受け持つ。下の決めたこと）

### 同じことを述べている箇所の数

「本文が中間表現の sha256 を持ち、dev-loop がそれを当てる」を述べているのは **12 箇所**:
`scaffold.py`（生成と末尾の注意）・`handoff-issue.md`（節の表・「sha256 で固定する」・撤去の項）・`spec-gap.md`（3 箇所）・
`versions.md`（2）・`tree.md`（1）・scaffold の `SKILL.md`（1）・公開ページ（1）。印は `SKILL.md`（dev-loop）にもある。
**分けない理由**: 原本は `handoff-issue.md` と `scaffold.py` だが、dev-loop はプラグインの外を相対パスで指せないので
`spec-gap.md` が写しを持つ（既存の設計。写しの一致は `test-scaffold.py` が見る）。指紋の式も同じ理由で
`scaffold.py` と `spec-fingerprint.py` の 2 箇所に置き、**テストが両者の出力の一致を当てる**。

## 決めたこと

1. **指紋は機能単位にする。** 全体の sha256 のままだと、作り直しの経路（scaffold の手順 7——この版の Issue を
   登録して実装が始まっている）で 1 機能を直すたびに、**関係の無い機能の登録済みの Issue が全部不一致になる**。
   dev-loop は不一致を差し戻すが、scaffold の手順 6 は同じ変化の印を持つ Issue を登録し直さないので、
   **一致する本文を得る道が無い**（「止まる側に倒れる」ではなく行き止まり）。
2. 指紋 = 重ね合わせた全体の `spec_ir.json` の中の、その機能のオブジェクトを
   `json.dumps(…, ensure_ascii=False, sort_keys=True, separators=(",", ":"))` で UTF-8 にした sha256。
   **`impl_module` と Q&A 表は入れない**——`impl_module` は Red テストのファイル（sha256 を本文が持つ）に入り、
   Q&A の回答は本文の表が写しを持ち、表を正とする決まりが spec-gap に既にある。
3. 本文の形の版を **v3** に上げる。v2 の本文は全体の sha256 を持つので、dev-loop は v2 を `shasum` で当て続け、
   **v2 の不一致は関係の無い機能の編集でも起きる**ので、差し戻さずに人間に訊く（止まる側に倒す）。
4. 撤去の本文は、前の版の全体を **`build/merged-v<n-1>/`** に作るコマンドと、その中のパスを書く
   （`build/merged/` を前の版で上書きさせない）。撤去の機能の指紋はそこに当て、作業中の版の全体には
   **その機能が無いこと**を当てる。

## 乗るデプロイ経路

- `docs/` を含むので、main へのマージが GitHub Pages へのデプロイになる（`CLAUDE.md`「デプロイ」）。
- プラグイン（dev-loop・spec-loop）は版を上げ、利用者が `plugin update` で受け取る。

## verify の受入基準

不変条件:

- **A. 本文の指紋が、dev-loop の照合で再現できる**——v3 の本文（追加・変更）の指紋は、本文のコマンドで作った
  `build/merged/spec/spec_ir.json` に `spec-fingerprint.py` を当てた出力と一致する。Red テストの sha256 は実物と一致する。
- **B. 関係の無い機能を直しても、指紋は変わらない**——同じ版で別の機能だけを変えて作り直すと、その機能の指紋は同じ。
  **陽性対照**: そのとき全体の sha256 は変わる（試料が判別している）。**その機能自身を変えると指紋は変わる。**
- **C. 撤去の本文から辿れる**——本文の仕様の原文のパスと中間表現が、本文のコマンドで作った前の版の全体
  （`build/merged-v<n-1>/`）に実在し、指紋がそこで一致し、作業中の版の全体ではその機能が「無い」と出る。
- **D. 後の版を足しても再現できる**（#262 R2 の回帰）——v3 を足した後も、本文のコマンドで作った全体で指紋が一致する。
  **陽性対照**: 版を指定しないと一致しない（v3 がその機能を変える試料で）。
- **E. 境界の写しが揃う**——印（v3）が `handoff-issue.md`・`spec-gap.md`・dev-loop の `SKILL.md` にあり、前の形の印
  （v2・v1）も `spec-gap.md` と `SKILL.md` に残る。`spec-gap.md` の節の表は `handoff-issue.md` と同じ。
- **F. 指紋の式が 2 箇所で同じ**——`scaffold.py` の指紋と `spec-fingerprint.py` の出力が一致する（A がこれを当てる）。
  式を片方だけ変えると落ちる（変異）。
- **G. 版が揃う**——2 つのプラグインの版を 3 箇所で上げ、`check-all.py` が緑。

経路（本文の照合を破りうる入口）:

| 入口 | 守り方 |
| --- | --- |
| scaffold の生成（追加・変更・撤去の 3 種の本文） | `scaffold.py` ＋ `test-scaffold.py` の試料（A・C） |
| 作り直しの経路（同じ版の別の機能を直す） | 機能単位の指紋（B の試料） |
| 後の版の追加 | `--upto` の指定（D の試料） |
| dev-loop の照合（spec-gap の手順と `spec-fingerprint.py`） | 試料で dev-loop のスクリプトを実際に走らせる（A・C）。写しの突き合わせ（E） |
| 登録済みの v1・v2 の Issue | spec-gap が前の形を読み続ける（E） |
| 手で本文を直す・登録時に書き換える | 規定（scaffold の SKILL.md）。機械では見ない |

証明できないもの（未証明）:

- **dev-loop の周が実際に spec-gap の手順どおり照合するか**（モデルの振る舞い。Eval は無い）——人間レビューに回す。

生成物の該当判定:

- `scaffold/` と Issue の本文は**正本リポジトリの側の生成物**で、このリポジトリには無い——試料の中で作って当てる。
- このリポジトリの生成物（図の書き出し・設計 §8.2 の生成ブロック）: dev-loop の `SKILL.md` を触るので
  **`skill-metrics.py --check` が鮮度を見る**（`check-all.py` に入っている）。行数が変われば再生成する。

## 未解決の判断・確認待ち

- なし（粒度は上の「決めたこと」で決めた。人間が覆すなら v2 のまま spec-gap に止まる側を書く形に戻す）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/290-feature-fingerprint`・worktree `.claude/worktrees/issue-290`・
  起点 `21bb63b`・base の参照 `origin/main`・base の SHA `21bb63b6974db9698574c924e08b1790d7f1afab`
- 実装: 済み（コミット済み）。`test-scaffold.py` は試料 149 件・変異 101 件で緑。`check-all.py` は 44 本のうち
  `skill-metrics.py --check` だけが落ち、生成ブロックを作り直して `--check` が 0 になった（**直したあと全部は回し直していない**）
- 割り目（手順 4）: 使用量の上限に達したので止めた（`AskUserQuestion` では訊いていない）。人間が「継続」と指示して同じセッションで続けた
- 関門の 1 パス目: Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件 ／ `/code-review`（high）9 件。採否は下の表——直す 4 件（CR1・CR4・CR5・CR8）・残課題 5 件
- 1 パス目の指摘対応: 済み（`test-scaffold.py` は緑。dev-loop 側の変異を 1 件足した）
- 1 パス目の指摘対応の後の `check-all.py`: 44 本のうち `skill-metrics.py --check` だけが落ち（`references/spec-gap.md` も測る）、
  生成ブロックを作り直して `--check` が 0。**作り直した後に全部は回し直していない**——再開したらまず `check-all.py`
- 割り目（2 パス目の前）: `AskUserQuestion` で訊き、**「ここで割る」が選ばれた**
- 次: 2 パス目（Verifier と `/code-review` の両方。差分は周の base `21bb63b6974db9698574c924e08b1790d7f1afab` から。
  受入基準・既知の限界・1 パス目の採否の表をまるごと渡す）。2 パス目の指摘対応の起点 SHA は、2 パス目の報告を受けてから書く
- 反証と差し戻し: 1 パス目の反証 0 件（Verifier）。手順 4 への差し戻しは指摘対応の 1 回
- 交絡: 実験なし（試料の陽性対照はテストの中にある）

## 既知の限界・決着済みの論点

- 指紋は Q&A 表と `impl_module` を覆わない——決めたこと 2。Q&A は表を正とする決まり（spec-gap）、`impl_module` は Red テストの sha256 が覆う。
  **撤去の本文は Red テストを持たないので `impl_module` を覆わない**（撤去する関数は本文が名指しする）。
- P1-11（同じ版の作り直しで、直した機能自身の本文が登録し直されない）は範囲外。機能単位にしても直した機能は不一致で止まる。

### 1 パス目の指摘（Verifier 反証 0 件・`/code-review` 9 件）

Verifier の軽い所見（空の `features` でも 3）は反証ではないとされたので表に載せない（前の版の全体での一致を併せて見るので、空の全体でも誤って通らない）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1 | HEAD で `check-plan-scope.py` が落ちる（`dev-loop-design.md` が範囲の外） | 示せる（`check-all.py` で 1/44 失敗） | G | 直す（計画の範囲に足した） |
| CR2 | 撤去の本文の Q&A の表が「v1 の時点の `build/merged/shared/qa.csv`」と書き、前の版の全体（`build/merged-v1/`）を指さない | 示せる（本文の文言） | 無し（C は仕様の原文と中間表現。Q&A は決めたこと 2 で指紋の外） | 残課題 |
| CR3 | scaffold 手順 6 は handoff の版を比べないので、v2 で登録済みの Issue を v3 の本文で置き換えられない | 示せない（`gh` の登録を当てていない。筋書き） | 無し（P1-11 と同じ登録側の問題。範囲外） | 残課題 |
| CR4 | 撤去の本文の末尾「上のコマンドで作った中間表現の指紋が違うなら差し戻す」が、2 つのコマンドのどちらか決まらない（`build/merged` では正しく 3 になる） | 示せる（本文の文言） | C（本文だけから正しい照合が辿れない） | 直す |
| CR5 | spec-gap の一般則が「中間表現と仕様の原文は `build/merged/` の中」と言い、v3 の撤去と食い違う | 示せる（`spec-gap.md` の文言） | C（dev-loop の照合の経路） | 直す |
| CR6 | 孤立サロゲートを含む中間表現で `spec-fingerprint.py` が exit 1 で落ちる（0・2・3 以外） | 示せる（再現） | 無し（scaffold は孤立サロゲートを拒むので、生成した本文の照合では起きない） | 残課題 |
| CR7 | `scaffold.py` の docstring が「機能の指紋で固定する」を指すが、見出しは「機能の指紋と sha256 で固定する」 | 示せる | 無し | 残課題 |
| CR8 | F の「片方だけ変えると落ちる」は scaffold 側の変異しか当てていない。撤去の前の版のコマンドは文言だけで、本文のコマンドを走らせていない | 示せる（変異の一覧・`v2_removed` のコード） | F・C（証明の主張） | 直す（dev-loop 側の変異を足し、本文のコマンドを走らせる） |
| CR9 | `if change.kind == REMOVE:` が 2 つ続く・`old_dir` を全種で計算する（v1 で `merged-v0`） | 示せない（不具合は起きない） | 無し | 残課題 |
