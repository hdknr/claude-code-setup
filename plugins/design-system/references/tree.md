# ガイドのリポジトリの木と表

デザインシステムを含めるガイドのリポジトリに何を置くかの原本である（#1613）。表の列はこの設計の周で決めた**初めの形**で、検査（子の Issue）を書く周がこの原本を直して確定させる。

## ガイドのリポジトリ

**デザインシステムを置くリポジトリは、組織のシステム構築ガイドの文書のリポジトリである**（利用者の求め。#1613、2026-11-27）。
ガイドの文書が開発の世界観——どう決め、どう作り、何を使うか——を説明し、その**構成要素**を持つ。**どの構成要素も任意で、ガイドに何を含めるかで決まる**——デザインシステムだけを定義するガイドも、profile だけのガイドもある。

| 構成要素 | 置き場所 | 書く人・道具 | ガイドの文書との関係 |
| --- | --- | --- | --- |
| ガイドの文書（必ずある） | `docs/`（ガイドの MkDocs の `docs_dir`）と `mkdocs.yml` | 人 | 世界観と、含めた構成要素の使い方を説明する。**人が読む入口はガイドのサイト 1 つ** |
| デザインシステム | spec-loop の正本（`design-system/v<n>/requirements/design/`）と生成物（`spec-profile/<デザインシステムの名前>/`・`tokens/`・`kit/`） | design-system と spec-loop | ガイドのサイトに頁を差し込む（`references/outputs.md` の「ドキュメントのサイト」） |
| UI プロファイル | `spec-profile/<名前>/` の層 `画面`（#1612 で層を足す） | 人 | 層の表の `リンク` がガイドの文書の節を指す（本文はガイドに書く） |
| 基盤・アーキテクチャ・開発の進め方の profile | `spec-profile/<名前>/` の層 `基盤` など | 人 | 同上 |
| プラグイン（組織のスキルなど） | 任意 | 人 | ガイドの文書が使い方を説明する |

```text
<ガイドのリポジトリ>/
├── CLAUDE.md                       # ガイドのリポジトリの CLAUDE.md（デザインシステムを含めるなら spec-loop の正本の CLAUDE.md を兼ねる）
├── mkdocs.yml                      # ガイドのサイトの設定（ガイドのもの）
├── docs/                           # ガイドの文書（MkDocs の docs_dir）——世界観と各構成要素の説明。手で書く profile の本文もここ
├── design-system/                  # デザインシステムの正本の根（spec-loop の正本。根の名前を変える口が入ってから——下）
│   └── v<n>/                       # spec-loop の版のディレクトリ（spec-loop の `references/versions.md`）
│       ├── shared/qa.csv           # 共有の Q&A 表（spec-loop。番号は req-loop が振る）
│       ├── spec/qa-dev.csv         # 内部の Q&A 表（spec-loop。実装だけに効く決定）
│       └── requirements/design/
│           ├── settings.csv        # デザインシステムの設定（下の「設定」）
│           ├── data/               # 表（下の「表」。行の単位で重ねる）
│           │   ├── tokens.csv
│           │   ├── components.csv
│           │   ├── component-specs.csv
│           │   ├── patterns.csv
│           │   └── rules.csv
│           └── *.md                # 散文（原則・部品・パターンの説明。下の「散文」）
├── spec-profile/
│   ├── <デザインシステムの名前>/  # 生成物（コミット）——使う側が読む索引（`references/outputs.md`）
│   └── <束の名前>/                 # 手で書く——基盤・画面などの層（下の「モノレポで共存させる」）
├── tokens/                         # 生成物（コミット）——DTCG のトークン
├── kit/                            # 生成物（コミット）——描画キット
└── build/design-system/            # 生成物（コミットしない）——ガイドのサイトに差し込む頁の作業場所
```

含めない構成要素の行は木に現れない（デザインシステムだけのガイドなら `spec-profile/` の下は `<デザインシステムの名前>/` だけ）。

- **ガイドの `docs/` と spec-loop の正本の `docs/` はぶつかる。** spec-loop は正本の根を `docs/` と決め打ちしている（spec-loop の `references/versions.md`。決め打ちの箇所は `references/spec-loop.md` の「spec-loop に要る口」の 5）ので、
  今のままでは正本の版（`docs/v<n>/`）がガイドの `docs/` の中に入り、ガイドのサイトに Q&A 表や版のディレクトリがそのまま写る。
  **正本の根を `design-system/` にする口 5 が、design-system を使う前提である**——口 5 が入るまで、ガイドにデザインシステムを含めない。
- **spec-loop の MkDocs の雛形は使わない**——ガイドに `mkdocs.yml` が在れば spec-loop の `init-mkdocs.py` は何も写さない（その docstring）。
  `--hook` の登録だけはするが、登録を呼ぶ spec-loop のフック（`hooks/spec_loop_pages.py`）が写らないので、登録しても呼ばれない（screen-spec はこの口で頁を足す——screen-spec の `references/mkdocs.md`）。
  design-system がガイドのサイトに頁を差し込む形（ガイドの `mkdocs.yml` の `hooks:` に登録するフックなど）は #1611 で決める。
- **ガイドの文書は design-system の外**——design-system は読まず、書き換えない。手で書く profile の本文もガイドの文書に書き、層の表の `リンク` で指す（spec-loop の `references/external-profile.md` の「`リンク` の書き方」）。
- **版の中のディレクトリの名前にプラグインの名前を入れない**（`requirements/design/`）——spec-loop に表を行の単位で登録すると、spec-loop の `merge-versions.py` と `versions.md` が表のパスを持つ（今ある `requirements/screens/data/` と同じ。`references/spec-loop.md` の「spec-loop に要る口」の 1）。
  パスに `design-system` を入れると、spec-loop が design-system の名前を持つことになる（`references/spec-loop.md` の「依存の向き」）。正本の根の名前（`design-system/`）は spec-loop の設定から読むので、spec-loop に名前を持ち込まない。
- **表と散文は `requirements/` の中に置く**——spec-loop の 2 つのサインオフが比べる範囲（spec-loop の `references/signoff-tags.md` の「2 つの承認が同じ範囲を見ていたか」）に入り、承認の対象になる。
- **生成物は版のディレクトリの外**（リポジトリの根）——承認の対象ではなく、表から作り直せる。コミットする 3 つは `--check` で鮮度を見る（`references/outputs.md`）。
- `spec/` には spec-loop の `qa-dev.csv` だけを置く。spec-loop の spec-review は使わない（`references/spec-loop.md` の「spec-loop のどの段を使うか」）ので、`spec/` に仕様は書かない。

## 設定（`requirements/design/settings.csv`）

見出し行は `項目,値`。ファイルの単位で重なる（screen-spec の `settings.csv` と同じ扱い）。

| 項目 | 値 |
| --- | --- |
| `名前` | デザインシステムの名前。英小文字・数字・`-`（`acme-ds`）。生成物の `spec-profile/<名前>/` と `tokens/<名前>.tokens.json` の名前になる。**最初の版で決め、変えない**（使う側が名前で名指す） |
| `表示名` | サイトの題などに出す名前 |

## 表

5 つの表を `data/` に置く。Issue #1613 の一覧（トークン・部品・パターン・原則と規則・文言）から 2 つ変えた——
**文言は表を分けず、規則の区分 `文言` にした**（文言の規則も対象の部品・パターンと確かめ方を規則と同じ列で持つので、置き場所を 2 つにしない）。
**部品の仕様（`component-specs.csv`）を足した**（部品の状態とアクセシビリティを行で持ち、判定役と引き渡しの受入基準の単位にする——#1613 の D4・`references/handoff.md`）。どれも次を守る:

- 1 行目は見出し行で、下の列名と同じ文字列・同じ順。**見出し行は版の間で変えない**（spec-loop の `references/versions.md` の「行の単位で重ねる表」が求める）。
- **鍵の列は 1 つ**。鍵の値は空にせず、版をまたいで重ねない（同じ鍵は「変更」の意味——spec-loop の決まり）。
- **`根拠` はどの行でも空にしない**——Q&A の番号（形は spec-loop の `references/qa-csv.md`）か、規則の `規則ID`。
- **未決定のセルには spec-loop の未決定の印と、その件の Q&A の番号を書く**（印は spec-loop の `references/spec-exit.md` の「未決定の印」）。印のあるセルは値の決まりに当てない。
- 複数の値を書くセルは `、` で区切る。
- 行の単位で重ねるための spec-loop 側の登録（`references/spec-loop.md` の「spec-loop に要る口」の 1）が入るまで、表はファイルの単位で重なる。

### トークン（`tokens.csv`）

| 列 | 書くもの |
| --- | --- |
| `トークン` | 鍵。英小文字・数字・`-` の語を `.` で区切った名前（`color.text.primary`・`color.blue.600`）。DTCG のグループの道筋になる |
| `層` | `基本`・`意味`・`部品` のどれか（primitive・semantic・component）。`意味` と `部品` の層は値に別名（下）を書くのを基本にする |
| `種類` | DTCG の型（`color`・`dimension`・`fontFamily`・`fontWeight`・`duration`・`cubicBezier`・`number` など。DTCG の仕様の型の名前のまま） |
| `値` | 値そのもの（`#0055ff`・`16px`）か、別のトークンへの別名（`{color.blue.600}`） |
| `説明` | 何に使うか |
| `根拠` | 上の決まり |

### 部品（`components.csv`）

| 列 | 書くもの |
| --- | --- |
| `部品ID` | 鍵。`CMP-` と数字（`CMP-001`）——spec-loop と screen-spec の番号の頭（`F-`・`S-`・`Q-`・`D-` など）と重ねない |
| `名前` | 英字の識別名（`Button`・`DataTable`）。**使う側（screen-spec の項目の `部品` の値・UI プロファイルの対応）はこの名前か `部品ID` で指す**（#1606・#1612 で決める）。版をまたいで変えない |
| `表示名` | 日本語の名前 |
| `項目の種類` | screen-spec の項目の種類（screen-spec の `references/tables.md` の「項目の種類」）のうち、この部品で描けるもの。複数可 |
| `目的` | 何のための部品か |
| `使う場面`・`使わない場面` | 使い分け（記事の「NG 例」。記事は `README.md` の「出所」） |
| `根拠` | 上の決まり |

### 部品の仕様（`component-specs.csv`）

部品のバリエーションと状態ごとの見た目・操作・読み上げ。**アクセシビリティの判定役と機械の検査が見る表**（`references/review.md`）。

| 列 | 書くもの |
| --- | --- |
| `番号` | 鍵。`CS-` と数字 |
| `部品ID` | どの部品の行か |
| `バリエーション` | `primary`・`secondary` など（無ければ `標準`） |
| `状態` | `通常`・`ホバー`・`フォーカス`・`押下`・`無効`・`エラー`・`読み込み中`・`選択` のどれか |
| `文字色`・`背景色`・`枠線` | トークンの名前（`{…}` で包まない素の名前）。無いなら空 |
| `ほかのトークン` | 余白・角丸・影などのトークンの名前。複数可 |
| `キーボード操作` | その状態でのキーの振る舞い（`Enter・Space で押す`）。操作を受けない状態なら `なし` |
| `読み上げ` | ロールとアクセシブルな名前・状態の伝え方（`button。無効を伝える`） |
| `根拠` | 上の決まり |

### パターン（`patterns.csv`）

| 列 | 書くもの |
| --- | --- |
| `パターンID` | 鍵。`PAT-` と数字 |
| `名前` | `確認ダイアログ`・`一覧の送り方` など |
| `場面` | どんなときに使うか |
| `使う部品` | `部品ID`。複数可 |
| `振る舞い` | パターンの決まり（`モーダル。Esc と外側のクリックで閉じる`） |
| `screen-spec の項目` | このパターンが既定の答えを持つ screen-spec の「誰が決めるか」の項目（screen-spec の `references/profiles.md` の `web-spa` の「誰が決めるか」。`ダイアログの実体` など）。無ければ空。**利用者が決める部分だけに答える**（開発者が決める部分は UI プロファイル——#1612） |
| `根拠` | 上の決まり |

### 規則（`rules.csv`）

原則・使い方の規則・文言の規則・アクセシビリティの規則（記事の「デザイン原則」「ドキュメント・運用ルール」。記事は `README.md` の「出所」）。

| 列 | 書くもの |
| --- | --- |
| `規則ID` | 鍵。`RUL-` と数字 |
| `区分` | `原則`・`使い方`・`文言`・`アクセシビリティ` のどれか |
| `対象` | `全体` か、`部品ID`・`パターンID`。複数可 |
| `規則` | 規則の文（`1 画面に主ボタンは 1 つまで`） |
| `確かめ方` | `機械`（design-system の検査が見る）・`判定役`（レビューの判定役が見る）・`人`（レビュー会で人が見る）のどれか |
| `根拠` | Q&A の番号（規則そのものの根拠なので、ほかの `規則ID` は書かない） |

## 散文

`requirements/design/` の直下の Markdown——原則の説明・部品とパターンの説明・使い方の例。サイトの頁の本文になる（`references/outputs.md` の「ドキュメントのサイト」）。

- 部品・パターンの頁は `<部品ID か パターンID>.md`（`CMP-001.md`）にし、サイトは表の行と並べて描く。表の中身を散文に写さない——サイトが表から描く。
- 見出しの id は GitHub の付け方で読まれる（使う側の索引のリンクが節を指す——`references/outputs.md` の「索引」）。

## モノレポで共存させる

**デザインシステム・UI プロファイル・基盤の profile を 1 つのリポジトリに置いてよい**（利用者の求め。#1613）。
外部の profile はもともと 1 つのリポジトリに複数置け、1 つのタグに基盤と画面の層をまとめられる（spec-loop の `references/external-profile.md` の「置き場所」）。
デザインシステムの索引もその形で書くので、同じ `spec-profile/` の下に並ぶ。

木は上の「ガイドのリポジトリ」のとおりで、束の形で描いてある。

UI プロファイルと基盤の profile は、spec-loop の決まりでは 1 つの `<名前>` に層をまとめても、別の `<名前>` に分けてもよい。
**ただし下の「ガイドラインとして一括で渡す」の束にするなら、基盤・アーキテクチャ・開発の進め方・画面の層を基盤の profile と同じ `<名前>` に置く**——
screen-spec の初期値は基盤の profile 自身の `profile.csv` の層 `画面` の `重ねる先` を読み、外部の profile を同じリポジトリ・同じ名前・同じタグにする（screen-spec の `references/profiles.md` の「基盤の profile から引く初期値」）。
`profile-layers.py` も、案件の設定の `profile` の名前からアーキテクチャと開発の進め方の層を読む。名前を分ける形は、束を使わない場合に限る。

| 決まり | 理由 |
| --- | --- |
| **`spec-profile/` の下の名前を重ねない**——`settings.csv` の `名前` は、手で書く profile の名前と違うものにする | 生成器は `spec-profile/<名前>/` を丸ごと作り直す |
| **生成器は自分の印のある `spec-profile/<名前>/` だけを書き、`--check` もそこだけを比べる。印の無いディレクトリが同じ名前で在れば、書かずに止める** | 手で書いた profile を上書きしない（spec-loop の `build-proposal.py` の印 `.build-proposal` と同じ考え方。印の名前は生成物の子の Issue で決める） |
| **タグの接頭辞を、版を出すものごとに分ける**——デザインシステムは spec-loop の決まりで `release-v<n>`、ほかは `ui-v<n>`・`infra-v<n>` など。**束（下の「ガイドラインとして一括で渡す」）では、基盤・アーキテクチャ・開発の進め方・画面の層は 1 つの系列（`guide-v<n>` など）になる**——screen-spec は画面の層を基盤の profile と同じタグで読む（screen-spec の `references/profiles.md` の「基盤の profile から引く初期値」）ので、画面の層だけ別の系列にすると届かない | 版を別々に出せる。platform-spec の版の差分は、設定のタグと同じ名前の形（接頭辞・区切り・末尾が同じ）のタグだけを新しい版の候補にする（platform-spec の `scripts/check-profile-diff.py` の `name_shape`）ので、接頭辞の違うタグは混ざらない |
| 1 つのタグで全部を出してもよい——UI プロファイルの設定のタグを `release-v<n>` にする | 版を揃えたいとき。デザインシステムを上げるたびに UI プロファイルも同じタグになる |
| **手で書く profile の本文はガイドの文書に書く** | 本文は人が読む世界観の一部で、ガイドのサイトに載る。`spec-profile/` の層の表は `リンク` で指すだけ（上の「ガイドのリポジトリ」） |
| **直下の名前を分ける**——ガイドが `docs/`・`mkdocs.yml`・`site/`（MkDocs の出力）を使い、デザインシステムの正本は `design-system/`、spec-loop の生成物は spec-loop の決まりの名前（`build/merged/` など）、コミットしない design-system の生成物は `build/design-system/` に置く | ガイドのサイトの出力と spec-loop の正本・生成物を混ぜない。`build/design-system/` の前例は screen-spec（UI モックの出力が `build/mock/`——screen-spec の `references/mock.md`）。spec-loop の `references/monorepo.md` の「build/ を分けない」が直下の `build/` から締め出すのは**実装のビルドの出力**で、spec-loop を使うプラグインの出力の置き場所は決めていない——`build/design-system/` は同じ節が挙げる spec-loop の名前と重ならない |
| **承認の範囲は版のディレクトリだけ**——2 つのサインオフはデザインシステムの表と散文を比べ、UI プロファイルと基盤の profile は比べない | spec-loop の照合は版のディレクトリの中しか見ない（spec-loop の `references/signoff-tags.md` の「2 つの承認が同じ範囲を見ていたか」）。profile の変更は PR とタグで出す |
| 使う側の手元の clone は 1 つでよい——案件の `CLAUDE.md` の `外部の profile の clone:` の行は、リポジトリごとに 1 行 | spec-loop の `references/external-profile.md` の「探し方」 |

### ガイドラインとして一括で渡す

**このリポジトリを組織のガイドラインの束にし、spec-loop と dev-loop でシステムを開発する案件に一括で渡せるようにする**（利用者の求め。#1613）。
束の中身と、それを使う側:

| 束の中身 | 使う側 | 今ある口 |
| --- | --- | --- |
| 基盤の層 | spec-loop の `shared/infra.csv`（platform-spec が照らす） | platform-spec の案件の設定 |
| アーキテクチャの層 | spec-review の Domain Checker の照合先 | platform-spec の `profile-layers.py architecture` |
| 開発の進め方の層 | dev-loop の `.claude/dev-loop.md` の雛形 | platform-spec の `profile-layers.py dev-loop` |
| 画面の層（UI プロファイル） | screen-spec の外部の profile | screen-spec の `init` が基盤の profile の画面の層の `重ねる先` から初期値を引く（screen-spec の `references/profiles.md` の「基盤の profile から引く初期値」） |
| デザインシステム | screen-spec の項目の部品（#1606）・UI モック（#1614）・案件の `design/sources.csv`（#1607）・dev-loop の見た目の確かめ | **まだ無い**（下の案） |

**入口は 1 つ**——案件は platform-spec の案件の設定（spec-loop の版の中の `shared/platform/settings.csv`。リポジトリ・profile・タグ）に基盤の profile を書くだけにし、
ほかは**その profile が名指すものを初期値として引く**（今ある画面の層の連鎖と同じ形。初期値は利用者に確かめて決める——screen-spec の `init` と同じ）。

**案**（決めるのは使う側の子の Issue——#1606）:

- 基盤の profile（の `profile.csv`）が、束のデザインシステムを**名前と `release-v<n>` のタグ**で名指す。名指す形（層か行か）はそこで決める。
- **デザインシステムはタグで名指す**——束のタグ（`guide-v<n>` など）の時点のデザインシステムの生成物は作業中の版かもしれないので、束のタグでは読まない。
  束の 1 つのタグの中で、基盤・画面の層は束のタグの時点を、デザインシステムは名指した `release-v<n>` の時点を読む。
  束のタグを `release-v<n>` に揃える（上の表の「1 つのタグで全部を出してもよい」）なら、2 つは同じ時点になる。
- 束を使わない案件（デザインシステムだけ・UI プロファイルだけを使う）は、今までどおりそれぞれを名指せる——束は入口を 1 つにする道で、ほかの道を塞がない。

- **UI プロファイルが同じリポジトリのデザインシステムを名指す**形（#1612）は、別のリポジトリを名指すときと同じ書き方にする——リポジトリを分けたくなったときに書き換えずに済む。
- リポジトリの CI は、デザインシステムの検査と生成物の `--check` に加えて、手で書く profile の層の表とリンクを確かめる（spec-loop の `external-profile.py` のリンクの検査）。雛形の CI（#1610）で決める。

## 決めていないこと

| 事項 | どこで決めるか |
| --- | --- |
| テーマ・モード（ライト・ダーク・高コントラスト）——`tokens.csv` を鍵 1 列のまま持つ形（モードごとに列を足す・鍵にモードを入れる・表を分ける） | 表と検査の子の Issue |
| 部品を消したとき、その部品の仕様の行も消したものとして扱うか | spec-loop の行の単位の表の登録の Issue（`references/spec-loop.md` の「spec-loop に要る口」の 1） |
| `状態` の語彙を足す方法（部品に固有の状態） | 表と検査の子の Issue |
| アイコン・画像・フォントのファイルの置き場所 | 生成物の子の Issue |
| 機械の検査が使う基準の値（コントラスト比の閾値など）を置く場所——`rules.csv` に値の列を足すか、`settings.csv` の項目にするか（`規則` は自由な文なので、検査は文から数を読まない） | 表と検査の子の Issue（`references/review.md` の「機械の検査」） |
