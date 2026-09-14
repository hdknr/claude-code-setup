# Claude Code Setup

Claude Code のセットアップガイドを mkdocs で構築・公開するプロジェクト。

## プロジェクト構成

- `docs/` - mkdocs ドキュメントソース（Part 1〜3 + 付録リンク集）
- `diagrams/` - drawio ダイアグラムソース（`diagrams/icons/` にブランドアイコン SVG）
  - `exports.json` - source → 書き出しの宣言と、書き出し時点の前提の指紋。
    **指紋は手で書かない**（`scripts/export-diagrams.py` が更新する）
- `.claude-plugin/` - マーケットプレイスカタログ（`marketplace.json`）
- `plugins/` - プラグイン配布用ディレクトリ
  - `workspace-setup/` - ワークスペース初期セットアップの**コマンド**（このプラグインだけスキルを持たない）
  - `cmux/` - cmux ウィンドウで GitHub Issue/PR を扱うスキル
  - `dev-loop/` - 1 Issue = 1 周のループ志向開発スキル
- `scripts/` - CI から呼ぶチェックスクリプト（標準ライブラリのみ・ローカルでも実行可）
  - `check-plugin-versions.py` - カタログ構造と version 一致
  - `check-version-bump.py` - 中身を変えたのに version を上げていない差分（PR 限定）
  - `check-description-sync.py` - description の同期漏れ（PR 限定）
  - `check-diagram-freshness.py` - drawio を編集して書き出しを更新していない乖離
  - `export-diagrams.py` - drawio の書き出しと `diagrams/exports.json` の更新（**CI からは呼ばない**）
  - `diagram_manifest.py` - 上の 2 本が共有する指紋の式と収集規則（**実行しない**。
    式が 2 箇所にあると片方だけ緑になるので 1 箇所に置く）
  - `skill-metrics.py` - `SKILL.md` の節構造を測り、設計ドキュメント §8.2 の
    生成ブロックに書き込む（`--check` で検査のみ）
  - `markdown_fences.py` - コードフェンスの除去と閉じ忘れの検出（**実行しない**。
    `check-plugin-versions.py` と `skill-metrics.py` が共有する。
    式が 2 箇所にあると片方だけ緑になるので 1 箇所に置く）
  - `link-skills.sh` - スキルを `~/.claude/skills` へ素のスキルとして symlink する（bare 呼び出し用）
  - `test-link-skills.py` / `test-check-description-sync.py` /
    `test-check-plugin-versions.py` / `test-check-diagram-freshness.py` /
    `test-export-diagrams.py` / `test-skill-metrics.py` - 上記の回帰テスト。
    **いずれも実環境を対象にしないことをアサートで担保している**
- `mkdocs.yml` - mkdocs 設定
- `pyproject.toml` - Python 依存関係（uv で管理）
- `.github/workflows/docs.yml` - GitHub Pages 自動デプロイ ＋ 図の鮮度チェック
  ＋ `SKILL.md` の測定値の鮮度チェック
- `.github/workflows/plugins.yml` - プラグインカタログの整合チェック

## 開発コマンド

```bash
uv sync --no-install-project    # 依存関係インストール
uv run mkdocs serve              # ローカルプレビュー (http://127.0.0.1:8000)
uv run mkdocs build              # サイトビルド
```

## 図表の更新

drawio ファイルを編集したら、**書き出しスクリプトで書き出す**。生の CLI を直接叩かない:

```bash
python3 scripts/export-diagrams.py <name>    # 例: architecture（拡張子は不要）
python3 scripts/export-diagrams.py           # マニフェストにある全件
```

書き出し先・形式・倍率は `diagrams/exports.json` が持っている（`docs/images/` 直下と
`docs/images/screenshots/` の両方に散っており、PNG も 2 件ある。**推測で書き出さない**）。
スクリプトは**書き出しが成功してから**指紋をマニフェストに書き戻す。成功の判定は
**終了コード・出力の実在・中身が形式として読めること**の 3 つを全部見る。
**書き出しの前に出力を消す**ので、「在ること」がそのまま「今回書いたこと」の証明になる
（mtime は読まない）。**失敗したら書き出しを書き出し前の状態に戻す**——ただし
復元自体が失敗しうる（書き込み不可など）ので、そのときは戻せなかったことを明示して報告する。

macOS 以外、あるいは draw.io を別の場所に入れている場合は `DRAWIO` で差し替える
（`DRAWIO=drawio`、`xvfb-run` 越しなら `DRAWIO="xvfb-run -a drawio"`）。
**動作確認は macOS でしか取れていない。**

### 書き出し忘れは差分では見えない

**ソースだけ直して書き出しを忘れると、差分を見ても気づけない**——書き出しは差分に現れないので
「変えていない」と見える。`makemigrations --check` に相当するものが無いことが、そもそも
見落としの原因になる（#50）。そこで `diagrams/exports.json` に**書き出し時点の前提の指紋**を
記録し、CI（`docs.yml`）で現在の前提と突き合わせている:

```bash
python3 scripts/check-diagram-freshness.py       # 乖離を検出して非ゼロ終了（--check 相当）
python3 scripts/test-check-diagram-freshness.py  # 歯止め自体のテスト（変異テストを含む）
python3 scripts/test-export-diagrams.py          # 書き出し側のテスト（偽の CLI で失敗を作る）
```

**指紋は 4 つを混ぜている**——ソースの内容・`output`・`scale`・**書き出しの内容**。
式は `scripts/diagram_manifest.py` に**1 箇所だけ**置く（検査側と書き出し側で式がずれると
片方だけ緑になる）。どれが欠けても、次が見えなくなる:

| 混ぜるもの | これが無いと何が見えなくなるか |
| --- | --- |
| ソースの内容 | 図を編集して書き出し忘れた（本来の目的） |
| `output` | 書き出し先を別の実在ファイルに向け替えた |
| `scale` | **マニフェストの倍率だけ書き換えた**（2 → 4 でも指紋が変わらない） |
| **書き出しの内容** | **書き出しそのものが壊れた・書き換えられた**（マニフェストを 1 文字も触らずに起きる） |

**バイト比較（書き出し直して `git diff --exit-code`）は採れない。** 実測で、書き出しのある
12 件を書き出し直したら **6 件しかバイト一致しなかった**——`architecture.svg` は 922x642 で
寸法が一致して 453602B vs 453646B、`mobile-remote-control.png` は 1646x763 で一致して 3 バイト差。
**原因は特定していない**（drawio の版・環境・埋め込む資源のどれが効いているかは確かめていない）。
確かめたのは「**同じソースから同じ引数で書き出してもバイトは一致しない**」という事実だけで、
それだけでバイト比較は偽陽性になると言える。CI に draw.io CLI（+ xvfb）を入れても解決しない。

**残る限界は 2 つ**。どちらも方式の原理的なもので、検出手段が無い:

1. **マニフェストの指紋だけ手で書き換えて実際には書き出さない。** だから**手で指紋を
   書かない**（`export-diagrams.py` を使うことが、この限界に対する実際の歯止め）。
2. **`output: null` のエントリは、ソースを編集しても何も言わない。** 指紋を持たないので
   比較する相手が無い。いま該当するのは `diagrams/clt-dialog.drawio` の 1 件で、
   **書き出しを持たない図はこの仕組みの外にある**。書き出しを作ると決めた時点で
   マニフェストに `output` を書けば、そこから先は見られるようになる。

逆に、**書き出しが壊れた・書き換えられた場合は検出できる**（指紋に書き出しの内容が
入っているので、マニフェストを触らない改変はすべて乖離として出る）。

**新しい図を足すときは、まずマニフェストにエントリを作る**（`output` と、書き出さないなら
`output: null` と `note`）。未登録の drawio は CI でエラーになる——「書き出し忘れ」と
「書き出さないと決めた」を区別できない状態を残さないため。**`fingerprint` は書かなくてよい**——
初回の `export-diagrams.py` が書き込む（書くまでは検査が「`fingerprint` が無い」で落ちる）。

ブランドアイコンは Simple Icons (simpleicons.org) から取得し、base64 で drawio に埋め込んでいる
（`diagrams/icons/` の SVG は素材で、書き出しの source ではない）。

### 同じ形がもう 1 つある — `SKILL.md` の測定値

設計ドキュメント §8.2 は**判断を測定値だけで正当化している節**で、その数字は
`SKILL.md` の節構造に依存する。**`SKILL.md` を編集すると黙って古くなり、差分にも現れない**
——図の書き出しとまったく同じ形（#78）。

**ただし対処は変えている。指紋を突き合わせるのではなく、数字そのものを生成する。**
直近 3 か月に `SKILL.md` を触った 15 コミットのうち **13 が行数を動かしている**ので、
「ずれたら手で直せ」では**税が重すぎる**（20 個以上の数字がある）。

```bash
python3 scripts/skill-metrics.py           # 生成ブロックを書き直す
python3 scripts/skill-metrics.py --check   # 古ければ非ゼロ終了（CI がこれを呼ぶ）
python3 scripts/test-skill-metrics.py      # 歯止め自体のテスト（変異テストを含む）
```

**生成ブロックを手で書き換えない。** **何が守られ、何が守られないかは
[設計ドキュメント §8.2](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#no-split)
の冒頭を正とする**（ここに再掲しない——列挙を 2 箇所に置くと片方だけ古くなる）。

**この「再掲しない」は、実際に破って確かめた。** 最初はここに列挙と件数を書いており、
**その 2 行上で「再掲しない」と宣言していながら**、2 周後に**両方とも古くなった**。

## プラグインの更新

`plugins/` 配下の `SKILL.md` やコマンド定義を変更したら、**バージョンを必ず上げる**。

- `plugins/<name>/.claude-plugin/plugin.json` の `version`
- `.claude-plugin/marketplace.json` の該当プラグインの `version`

**この 2 つの JSON は同じ値に揃える。** バージョンを据え置いたまま中身だけ変えると、インストール済み
クライアントのキャッシュが更新を検知できず、旧い内容のスキルを使い続ける（#33 で実際に発生した）。

さらに **そのプラグインが持つ `SKILL.md` すべての本文にも同じ版を書く**。
**揃える箇所は合わせて 3 種類**（`marketplace.json` / `plugin.json` / `SKILL.md`）で、
CI のエラーメッセージもそう案内する。
**2 行 1 組**で、見出しの直後に置く（理由は下の「version を上げるだけでは届かない」）:

```markdown
<!-- skill-version: 1.2.3 -->
> **このスキルの版: 1.2.3**（プラグイン `<name>`）。
```

1 行目は機械が読む印、**2 行目が利用者の目に入る側**で、こちらが本体。
`check-plugin-versions.py` は**両方**を検査する（片方だけだとエラー）。
可視テキストは**行頭が `> **このスキルの版: `** であることまで見る（散文の途中に同じ
文字列があっても数えないため）。**コメントやコードフェンスで囲って無効化した記載は
そもそも数えない**——「読者には見えないのに CI は緑」を防ぐのはこちらの仕組み。

刻み方は semver に従う。

| 変更の性質 | 上げ方 | 例 |
| --- | --- | --- |
| 能力・手順の追加 | **minor** | 手順に新しい任意ステップを足す |
| 不具合・記述の修正 | **patch** | 指示の誤りを直す・typo |
| 既存の使い方が壊れる変更 | **major** | 引数や必須前提の変更 |

### version を上げるだけでは届かない

**version bump は必要条件であって十分条件ではない。** 利用者側のマーケットプレイスのクローンが
導入時のコミットで**凍結したままになる**——実測では、**カタログを読み直すまで
`list --available` が返す版も説明文も古いまま**だった。

実測（#63 / #74 / #77）: `dev-loop` は **1.0.0 のまま 6 週間以上**使われていた。
インストールは **2026-07-29**（`installedAt`）、クローンは **`0b22552` / 2026-07-21** で凍結。
その間に **1.9.1** まで上げていたが、**1 度も届いていなかった**。
#33 の対策（version bump）だけでは防げていなかったことになる。

**2 つの日付は別のものを指す。** `installedAt` が **07-29**、クローンのコミット日が **07-21**。
#63 は「2026-07-29 の**コミット**のまま」と書いており、**誤っていたのは日付ではなく「コミット」
という語のほう**だった（#76 で「07-29 は誤り」としたのは言い過ぎ）。**どちらの日付か明示する。**

**#63 の対策（本文に版のバナーを刻む）は、この経路では効かなかった。** バナーを入れたのは
**1.7.1**（`ff8920d` / #67）で、凍結しているのは 1.0.0 なので、**バナー自体が届いていない**——
**対策が届くには対策より後の版が届いている必要がある**という循環になる。
代わりに **`claude plugin list --json`**（入っている版を返す。バナーを持たない版にも効く）を
第一の確認手段として案内する。

**2026-09-11（#77）に、解除できることを初めて実証した**——`claude plugin marketplace update` →
`claude plugin update` で **1.0.0 → 1.9.1**。#63 も #74 も「凍結している」ことしか
確かめていなかった。

**手順・確認方法・確かめていないことの範囲は公開ページを正とする**（ここに再掲しない）:
<https://hdknr.github.io/claude-code-setup/plugins/#updating>

要点だけ:

- **更新は `claude plugin update` で足りる**（2026-09-13 に実測）。
  **取り直しは必須ではない**——`plugin update` が**自分でカタログを取り直す**。
  ただし `marketplace update` を先に走らせても害は無いので、案内は 2 段階のままにしてある。
  **判定と更新は分けられない**——最新でなければその場で更新される。
  なお `--available` に **`dev-loop` は現れない**（理由は不明。「入っているから」ではない——
  入っている 12 件のうち 7 件は出る）ので、少なくとも `dev-loop` については比較に使えない。
- **`autoUpdate` の設定手段は複数ある**（`/plugin` の画面・`known_marketplaces.json` の
  直接編集・settings の `extraKnownMarketplaces`）。**実測したのは 2 番目と 3 番目**で、
  **非対話の `claude plugin` には項目が見当たらない**（`marketplace` 配下を含む 18 枚の
  `--help` を確認）。**`known_marketplaces.json` は真の出所ではない**
  ——settings の宣言が最優先で、**そこへ実際に書き戻される**（2026-09-14 に両方向で実測）。
  **未設定でも名前で既定が決まる**分岐があり、**`claude-code-setup` はその一覧に入っていない**
  ので、設定しなければ自動更新されない。
  **有効にすると掃引の対象に入る**（2026-09-13 に実測。有効 5 件が一斉に進み、無効 4 件は
  動かなかった。`claude-code-setup` は 2 日止まっていたのがフラグを立てた直後に加わった）。
  **ただし確かめたのは「取り直しに行く」ところまで**——新しいコミットを引くところ・
  走る間隔は測っていない。**発火条件は特定できていない**——2026-09-14 に
  `claude plugin list` でも `-p` の起動でも**観測できなかった**（`--debug-file` のログ 38 行に
  更新関連は 0 行）。**ただしこれは「発火しない」の証拠ではない**——そのログが覆うのは
  プロセスの生存 0.13 秒だけで、条件も #80 とは違う。**発火を「必ず起きる」と書かない。**
- **リポジトリ側からできるのは「気づける材料を置くこと」まで**——**`autoUpdate` は例外で、
  リポジトリの `.claude/settings.json` から宣言できる**（2026-09-14 に実測。一度「できない」と
  書いて撤回し、次に「試していないので書かない」に退き、今回動かして決着させた）。
  **条件は workspace が信頼済みであること**——未信頼だと届かない（確かめたのは
  `permissions.allow` / `env` / `extraKnownMarketplaces` の **3 キーだけ**。`enabledPlugins` は未確認）。
  **書き込み先は利用者全体の `known_marketplaces.json` で、宣言を消しても残る**——
  つまり**リポジトリが利用者のクライアント状態を恒久的に書き換えられる**。
  **未登録のマーケットプレイスの新規登録もできる**（`directory` 形式で実測。`github` 形式は未確認。
  増えるのは登録簿の 1 行までで、クローンもプラグインも入らなかった）。
  **`claude plugin marketplace list` では宣言が当たらない**——登録済みの値を変える宣言を
  信頼済みディレクトリで置いても動かなかった（他のサブコマンドは試していない）。
  **`--settings` フラグは信頼の関門の外**で、未信頼のディレクトリでも値が当たる。
  更新の実行と再起動はクライアント側で確定。

**常に最新を使いたい場合は、プラグインではなく symlink 経路を選ぶ**——
`scripts/link-skills.sh` で `~/.claude/skills/` に張れば、リポジトリを `git pull` した時点で
反映される（キャッシュを経由しないため、構造的に古くならない）。
**ただしスクリプトは自分の位置からリポジトリを解決して絶対パスで張る**ので、
**worktree から実行するとその worktree に固定される**。メインの作業ツリーから実行すること。

この整合は CI（`.github/workflows/plugins.yml`）で機械的にチェックしている。ローカルでも確認できる:

```bash
python3 scripts/check-plugin-versions.py            # version の一致（3 箇所）・カタログ構造
python3 scripts/check-version-bump.py origin/main   # bump 漏れ（PR の差分に対して）
python3 scripts/check-description-sync.py origin/main   # description の同期漏れ（同上）
python3 scripts/test-check-plugin-versions.py       # 版チェックの歯止め自体のテスト
```

### description は 3 箇所にある

`version` と同じく、`description` も **3 箇所**に複製されている。ただし**揃え方が違う**。

| 箇所 | 役割 |
| --- | --- |
| `.claude-plugin/marketplace.json` | カタログの紹介文 |
| `plugins/<name>/.claude-plugin/plugin.json` | マニフェスト |
| `plugins/<name>/skills/<skill>/SKILL.md` の frontmatter | **常時ロードされる要約** |

**version と違い、3 つを同じ値に揃えるのは誤り。** frontmatter は「いつこのスキルを起動するか」を
書く別目的の文章で、カタログの紹介文より長く引数の説明も含む（`dev-loop` は frontmatter が
JSON の 2 倍ほどある）。**具体的な文字数はここに書かない**——本文を直すたびに古くなり、
実際 #62 の周で、古い実測値をそのまま書いて事実誤りを出した。

**揃えるべきなのは値ではなく更新のタイミング。どれかを直したら、残りも点検する。**
とくに frontmatter は**本文を読む前の判断材料**なので、置き去りにすると**古い規範が先に読まれる**。
#59 / PR #60 の周では、本文が「達成不能だから」と否定した文言を要約が掲げ続ける状態が生じ、
同じ同期漏れが**向きを変えて 2 回**起きた（本文＋frontmatter を直して JSON が残る →
JSON を直して frontmatter が残る）。

`check-description-sync.py` はこの**共変**を base との diff で見る。片側だけ直すのが正しい場合
（カタログの typo 修正など）は、コミットメッセージに理由つきの trailer を書く:

```
Skip-description-sync: カタログの typo 修正のみ。要約の内容は変わらない
```

## Git ワークフロー

- Issue 対応はブランチを切って PR 経由でマージ（ブランチ名: `issue/<番号>-<説明>`）
- main への直接プッシュはしない
- コミットメッセージに `Fixes #<番号>` を含めて Issue を自動クローズ

## デプロイ

- リポジトリ: github.com/hdknr/claude-code-setup（公開）
- サイト: https://hdknr.github.io/claude-code-setup/
- main への push で GitHub Actions が自動デプロイ
