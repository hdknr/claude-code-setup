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
- 実装: 未着手
- 交絡を潰した手順: 未

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 新規プラグインだけ一致を見る | 採らない | 人間の選択。新規と既存でルールが分かれる |
| frontmatter も一致させる | 採らない | 別目的の文章（CLAUDE.md）。共変のまま |
| description キーを必須にする | 採らない | Issue の範囲外。両側に無ければ一致として通す（P6） |
