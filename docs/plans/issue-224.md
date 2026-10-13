# Issue #224 — 新規プラグインの description の食い違いをどの歯止めも見ていない

## 1. 変更範囲

触る:

- `scripts/check-plugin-versions.py` — `marketplace.json` と `plugin.json` の description の一致を検査（全プラグイン・常時）
- `scripts/test-check-plugin-versions.py` — 上の回帰テスト（変異テストを含む）
- `scripts/check-description-sync.py` — docstring（新規プラグインの JSON 2 箇所は `check-plugin-versions.py` が見る・typo の例）
- `CLAUDE.md` — 「description は 3 箇所にある」の節（JSON 2 箇所は揃える／frontmatter は揃えない）
- `docs/plans/issue-224.md` — この計画ファイル

触らない:

- `plugins/` 配下（現状 5 プラグインすべて JSON 2 箇所が一致しているので直す値が無い。版も上げない）
- `check-description-sync.py` のロジック（新規プラグインを「対象外」にする判定はそのまま。共変は base が無いと定義できない）
- SKILL.md の frontmatter との比較（別目的の文章。一致させるのは誤り——CLAUDE.md）
- `.github/workflows/plugins.yml`（`check-plugin-versions.py` は push・PR とも既に呼ばれている）

**方式の決定**（人間が選択、2026-10-13）: 「JSON 2 箇所は常に一致」。代案「新規プラグインだけ一致を見る」は採らない
（新規と既存でルールが違う）。根拠: `origin/main`（`fe726b1`）の 5 プラグインすべてで JSON 2 箇所が完全一致。

**複製の数**: 「description を揃えるか」を述べている箇所は 3 つ——`CLAUDE.md` の節、
`check-description-sync.py` の docstring（「一致させるほうが誤り」・「新規／削除 → 対象外」・typo の例）、
`check-plugin-versions.py` の docstring の検査項目一覧。**分けない理由**: 規範の変更（JSON 2 箇所を揃える）と
その検査は同じ 1 つの決定で、片方だけ入れると文面と検査が食い違う。

## 2. デプロイ経路

- `scripts/` と `CLAUDE.md`：CI の歯止めの変更。利用者への配布物（`plugins/`）は変わらない。
- `docs/plans/` は GitHub Pages に載るが記録のみ。破壊的・不可逆な操作は無い。

## 3. 受入基準

**I1. `marketplace.json` のエントリと、その `plugin.json` の description が食い違ったら、`check-plugin-versions.py` が赤になる。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 新規プラグイン（base に無い）で marketplace 側だけ別の値（Issue の再現） | 赤 | 全エントリで常時比較（base を見ない） |
| P2 既存プラグインで plugin.json 側だけ別の値 | 赤 | 同上 |
| P3 片側だけ `description` キーが無い | 赤 | キーの有無も値として比較（「無い」を落とさない） |
| P4 型が違う（文字列 vs 数値・null など） | 赤 | 値をそのまま比較 |
| P5 両側とも一致（現状の 5 プラグイン・テストの正常系） | 緑 | — |
| P6 両側とも `description` キーが無い | 緑（ここでは必須にしない） | 一致として扱う |
| P7 空白だけが違う（末尾空白・改行） | 赤 | 正規化しない |
| P8 `plugin.json` が壊れている・無い | 既存のエラーのまま（description の比較で落ちない・クラッシュしない） | 既存の早期 return より後で比較 |

**I2. 実リポジトリが緑**: `check-all.py` が全部緑（現状の 5 プラグインを誤検出しない）。

**I3. 文面が検査と食い違わない**: `CLAUDE.md` と 2 本の docstring が「JSON 2 箇所は揃える／frontmatter は共変」を述べ、
「3 つを同じ値に揃えるのは誤り」「カタログの typo 修正だけなら trailer」のような、新しい検査と矛盾する記述を残さない。

### 証明の手段

- I1: `test-check-plugin-versions.py` に P1〜P8 のケースを足す。**陽性対照**: 修正前のスクリプト（`origin/main`）で
  P1〜P4・P7 のケースが緑（＝検出できていない）ことを見る。
- Issue の再現そのもの: 実リポジトリの複製で spec-loop の marketplace 側だけを変え、`check-plugin-versions.py` が赤になる。
- I2: `python3 scripts/check-all.py`。
- I3: `grep` と目視。
- **未証明**: なし（すべてローカルで判定できる）。

### 生成物

**生成物なし**——図の書き出し・§8.2 の測定値はどちらも触らない（`check-all.py` が鮮度を見る）。

## 4. 未解決の判断

- なし

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/224-description-json-equal`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-224`、
  起点 `fe726b1`、**base: `origin/main` → `fe726b1df5dfc55cf341ccc1a470d61c25e1cad6`**
- 実装: `check_description()` を `check-plugin-versions.py` に追加、テスト 7 ケース（赤）＋ 2 ケース（緑／クラッシュしない）。
  `CLAUDE.md` と `check-description-sync.py` の docstring を直した。`check-all.py` 32/32 緑。
  PR 限定の 3 本（plan-scope・description-sync・version-bump）も base に対して緑。
- 実装コミット: `afff0aa`
- 関門 1 パス目:
  - Verifier（`dev-loop:dev-loop-verifier`／sonnet）: **回収済み・反証 1 件**（V1。I1〜I3 は充足、`check-all.py` 32/32・生成物の鮮度とも緑）
  - `/code-review`（high）: **回収済み・指摘 9 件**（R1〜R9。R3 は V1 と同じ）。直す 5 件（V1/R3・R1・R4・R5・R8）、残課題 4 件
  - 1 パス目の指摘対応: **済み**（起点 `5dfaa49`）。`load_json` がオブジェクト以外を拒否（R5）、比較を `json.dumps(sort_keys=True)` に（R4）、
    CI メッセージを直した（R1）、テストに「キー無し 対 null」・入れ子 2 件・plugin.json の無い／配列／文字列を追加（V1・R4・R5・R8）。
    テスト 96 判定に合格・`check-all.py` 32/32・PR 限定 3 本とも緑。
    **陽性対照**（scratchpad の `controls.py`、`.git` の無い複製）: 修正前（`5dfaa49`）に当てると入れ子 2 件・配列／文字列の plugin.json で 8 判定が赤（後者は Traceback）。
    番兵を外す変異に当てると「キーが無いのと null」の 2 判定が赤。「無い plugin.json」は修正前も緑（回帰の歯止め）。
  - **残るのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方**
- 関門 2 パス目（2026-10-13）:
  - Verifier（`dev-loop:dev-loop-verifier`／sonnet）: **回収済み・反証 0 件**。ただし**事故**——変異の実験で複製作成がガードに拒否され、
    `sed -i` が本物の worktree に当たって `check-plugin-versions.py:173` を `missing = None` にした（Verifier の復旧コマンドも拒否された）。
    人間の承認を得て著者が `git checkout --` で HEAD に戻し、`git status` が空であることと `check-all.py` 32/32 緑を自分で確かめた。
    **Verifier の報告にある `check-all.py` 32/32 は変異が入った状態の結果なので、HEAD の証拠には使わない。**
  - `/code-review`（high）: **回収済み・指摘 6 件**（C1〜C6）。`git show HEAD:` から作った `.git` の無い複製で当てたと報告しており、
    汚れの影響は受けていない。直す 1 件（C1）、残課題 4 件、対象外 1 件（C4・計画ファイル）
  - **狭いパスの起点: `7129dc8ee270ee4d230ee726edbef4c25b78118d`**（2 パス目の指摘対応を始める直前の HEAD）
  - 2 パス目の指摘対応: C1 を `3266704` で修正。`check-all.py` 32/32 緑
  - 狭いパス（Verifier／sonnet、差分 `7129dc8..3266704`）: **回収済み・反証 0 件**。文面の変更なので変異は当てず読解で判定
    （素通りした変異: なし／当てた変異: なし）。指摘: 「どれかを直したら、残りも点検する」の「どれか」の範囲に曖昧さが残る（矛盾ではない）——人間に渡す。
    検証後の `git status --porcelain` は空（著者も確認）
- この周の起票: 1 件（#233——2 パス目の Verifier が worktree を書き換えた件。手順 8 で人間が承認）
- PR: #232（CI 緑。マージは人間の承認待ち）
  - 割り目（手順 6・2 パス目の前）: 提案済み——**人間の選択は「ここで割る」**（2026-10-13）。
    **次は Verifier 2 パス目から**（base は同じ `fe726b1df5dfc55cf341ccc1a470d61c25e1cad6`）。2 パス目の指摘対応に入る前に、狭いパスの起点 SHA をここに書く
- 割り目（手順 4）: 提案済み——**人間の選択は「ここで割る」**（2026-10-13）
- 交絡を潰した手順（著者の実験。関門ではない）:
  - **陽性対照**: 新しいテストを修正前（`fe726b1`）のスクリプトに当てると、食い違い 7 ケースすべてが緑（＝すり抜け。14 判定が失敗）。
    両側に無い・壊れた `plugin.json` の 2 ケースは修正前も通る（回帰していないことの確認）。
  - **変異**: 型の比較（`type(...) is type(...)`）を外すと「数値と真偽値」だけが赤になる（2 判定）。
  - **Issue の再現**: 実リポジトリの複製（`.git` を除いた `rsync`）で spec-loop の marketplace 側だけ「別の文字列」にすると rc=1。
    変える前は 5 件とも問題なし。
  - スクリプト: scratchpad の `i224/`（`mutate.py`・`old/scripts/`）。

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 新規プラグインだけ一致を見る | 採らない | 人間の選択。新規と既存でルールが分かれる |
| frontmatter も一致させる | 採らない | 別目的の文章（CLAUDE.md）。共変のまま |
| description キーを必須にする | 採らない | Issue の範囲外。両側に無ければ一致として通す（P6） |

### 関門の指摘（採否）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | 番兵 `missing` を外して `.get("description")` にしても、テストが 1 件も落ちない（片側欠落の相手がいつも文字列） | 示せる——Verifier が変異を当てて「すり抜けた」0 件（著者が当て直して確かめる） | I1／P3（キー無し 対 `null` の組がテストで守られていない） | 直す |
| R1 | `check-description-sync.py:474` の CI メッセージが「3 箇所は一致させる必要はありません」のまま | 示せる——該当行 | I3（同じ変更範囲のファイルの文面が新しい検査と食い違う） | 直す |
| R2 | `test-check-description-sync.py:272` / 652-656 の trailer の試料が「カタログだけの typo」 | 示せる——該当行 | 無し（trailer の挙動を試す試料で規範の記述ではない。I3 が名指すのは CLAUDE.md と 2 本の docstring） | 残課題 |
| R3 | = V1（番兵の変異が素通り） | V1 と同じ | I1／P3 | 直す（V1 と同じ） |
| R4 | 型の比較が最上位だけ——`[1]` 対 `[true]`、`{"a":1}` 対 `{"a":1.0}` が緑 | 示せる——レビューが複製で rc=0 を再現（著者が当て直す） | I1／P4 | 直す |
| R5 | `plugin.json` が JSON としては正しいがオブジェクトでない（`[]`）と `AttributeError` でクラッシュ | 示せる——レビューが複製で Traceback を再現（既存の欠陥） | I1／P8（壊れた plugin.json でクラッシュしない） | 直す |
| R6 | 一致しないのに表示が同じに見える（NFC/NFD・不可視文字） | 示せる | 無し（検査は赤になる。表示の問題） | 残課題 |
| R7 | 壊れた plugin.json のテストが `run_case` の準備を手で複製（依存の一覧） | 示せない（いまは壊れていない） | 無し | 残課題のはずだったが、R5/R8 のテストを足すのに同じ準備が要るので `run_case` に `mutate` を足して解消（副次。採否の基準で選んだのではない） |
| R8 | P8 の「無い」（plugin.json が存在しない）の形がテストに無い | 示せる——計画 §3 は P8 をテストで当てると書いたが該当ケースが無い（grep） | I1／P8 の証明手段 | 直す |
| R9 | `CLAUDE.md:34`・`:363`・`docs/plugins/index.md:236`・`plugins.yml` が `check-plugin-versions.py` の新しい検査に触れない | 示せる | 無し（食い違いではなく記載漏れ。I3 は矛盾する記述を禁じる） | 残課題 |
| C1 | `CLAUDE.md:693`「揃えるべきなのは値ではなく更新のタイミング」が frontmatter に限られておらず、JSON 2 箇所を揃える新しい規則と矛盾 | 示せる——該当行 | I3 | 直す |
| C2 | `sort_keys=True` を外してもテスト 96/96 緑（キー順違いの一致を守るテストが無い） | 示せる——レビューが変異を当てた | 無し（実装は正しい。キー順違いは P1〜P8 に無い） | 残課題 |
| C3 | 片割れのサロゲート（`"\ud800"`）で `show()` の `print` が `UnicodeEncodeError`（rc=1 だがメッセージが消える） | 示せる——レビューが再現 | 無し（I1 は赤のまま。P8 は plugin.json が壊れている・無い形） | 残課題 |
| C4 | 計画 §5 の変異の記録（`type(...) is type(...)`）と P4 の守り方が `f84bb18` 後のコードと合わない | 示せる | — | 対象外（関門は計画ファイルを検査しない） |
| C5 | `load_json` が marketplace.json の非オブジェクトも拒否するようになったが、そのテストが無い | 示せない（いまは正しく動く） | 無し | 残課題 |
| C6 | `check-description-sync.py` は非文字列の description を NO_KEY に畳むが、`check-plugin-versions.py` は型まで区別する（1→true で食い違う） | 示せる | 無し（I3 は文面。I1 は守られる） | 残課題 |
| V2 | （Verifier 2 パス目）反証 0 件。入れ子の型の変異は当てられず未確認——`/code-review` が `json.dumps`→`==` の変異で 6 判定が赤を確認 | — | — | — |
