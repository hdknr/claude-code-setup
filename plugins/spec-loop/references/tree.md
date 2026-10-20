# 正本リポジトリのツリー

要求・見積り・提案書の元ファイルは、**1 つの git リポジトリ（正本）**に置く。
spec-loop のスキルはどれも、このツリーを前提に読み書きする。

**`docs/` は版ごとのディレクトリ（`docs/v1/`・`docs/v2/`…）に分け、v2 以降には前の版からの差分だけを置く。**
版の決まり（作業中の版・凍結・重ね合わせ・削除・移し方）は `versions.md` を正とする。
下の `docs/v<n>/` の中の構成は、**どの版でも同じ**（v2 以降は、足した・変えたものだけを置く）。

```
docs/v<n>/
├── shared/                  # 利用者と予算責任者の両方に見せてよいもの
│   ├── qa.csv               # Q&A 表（列は qa-csv.md）
│   ├── decision_table.csv   # 決定表
│   └── nfr.csv              # 非機能要求の回答
├── requirements/            # 利用者向け：業務ルール・画面・業務フロー
├── spec/                    # 開発者向け：入出力・エラー・境界値・状態遷移（spec-review が書き下す）
│   ├── formal/              # 形式検査のモデル（決定表の検査・TLA+・Alloy など）
│   └── spec_ir.json         # 仕様の中間表現（scaffold が書き起こす。形は spec-ir.md）
├── feasibility/             # 予算責任者向け：規模の数え方・開発手法・体制・基盤案・見積り
│   ├── schedule.csv         # スケジュールの正本（列は feasibility-csv.md）
│   └── estimate.csv         # 見積りの正本（同上）
├── proposal/                # 決裁者向け提案書の手書き部分
└── removed.csv              # v2 以降だけ。前の版から消したもの（versions.md）
scaffold/                    # dev-loop に渡す契約（scaffold が生成し、commit する。下の「scaffold の出力」）
├── openapi.json
├── types.py
└── tests/test_<機能>.py     # Red テスト
build/merged/                # 版を重ね合わせた全体（生成物。commit しない。versions.md）
docs/index.md                # 表紙（下の「ドキュメントのツール」。版の外）
docs/qa.md                   # Q&A 表の表示用ページ（同上。正本は各版の shared/qa.csv）
mkdocs.yml                   # MkDocs の設定（同上）
hooks/spec_loop_pages.py     # 表示用ページを CSV から作るフック（同上）
```

以下、`shared/`・`spec/` などは**版のディレクトリの中**（`docs/v<n>/shared/`）を指す。

## 置き方の決まり

- **`shared/` には、両方の読者に見せてよいものだけを置く。** 2 つのサインオフが
  同じ範囲を見ていたかは、`shared/` の中身で確かめる（`signoff-tags.md`）。
- **`requirements/` から `feasibility/` へはリンクしない。** 利用者に見せる費用は、
  `qa.csv` の `費用への影響` の列だけにする。見積りの側は、根拠にした Q&A の番号
  （`Q-005` など）や決定表の行を書く。
- **`spec/` は `requirements/` から書き下す。** 利用者の言葉で決まったこと（`requirements/`・
  `shared/` の決定表）を、開発者が実装とテストに使える形に直す。**`spec/` で新しく決めてよいのは、
  利用者の業務に関わらないこと（リトライ回数・タイムアウトなど）だけ**——利用者の判断が要ることは
  `qa.csv` に起票する。確定の条件は `spec-exit.md`。
- **`proposal/` には、ほかのどこにも無い部分だけを手で書く**（背景と目的・推奨案とその理由・
  比較した代替案・リスクと前提条件）。範囲・費用・期間・主な決定事項の表は、
  `shared/`・`requirements/`・`feasibility/` から生成する。**v2 以降の「前の版からの変更」の表も生成する**
  （`versions.md` の「版の差分」）。手書き部分は `proposal/*.md` に置き、
  **ファイル名の順に**提案書の先頭へ並ぶ（`01-background.md`・`02-recommendation.md` のように番号を付ける）。

## スライドの置き場所

レビュー会のスライド（`req-loop` が作る）は **`qa.csv` から生成するもので、正本ではない**。

- **`shared/` にも、ツリーのどこにも置かない。** `shared/` は 2 つのサインオフが同じ範囲を
  見ていたかを比べる場所なので、生成物を入れると比べる中身が増える。
- 既定の出力先は **`build/req-loop/qa-review.pptx`**（リポジトリ直下の `build/`）。
  **commit しなくてよい**——同梱の生成スクリプトは、同じ `qa.csv` と引数から同じバイトを作るので、
  レビュー会で見せたものは `qa.csv` の履歴から作り直せる。
- 正本リポジトリの `CLAUDE.md` が出力先や形式を決めていれば、そちらに従う（下）。

## 生成物の置き場所

レビュー会のスライドと同じく、**ガントチャートと提案書も生成物で、正本ではない**。ツリーには置かない。

| 生成物 | 既定の出力先 | 作るスキル |
| --- | --- | --- |
| ガントチャート | `build/feasibility/gantt.svg` | `feasibility` |
| 提案書 | `build/proposal/proposal.md`（と同じ場所の `gantt.svg`） | `proposal` |
| Issue の本文 | `build/scaffold/issues/<機能の id>.md`（と同じ場所の `issues.json`） | `scaffold` |
| サイト | `site/`（MkDocs の出力。下の「ドキュメントのツール」） | `mkdocs build` |

**commit しなくてよい**——同梱の生成スクリプトは、同じ入力から同じバイトを作る。
提案書は**サインオフのタグの時点の中身**から作るので、タグがあれば作り直せる（`signoff-tags.md`）。

Issue の本文は**登録すれば GitHub に残る**ので、commit しなくてよい。**作れなかったときは前の本文を消す**
（古い本文を登録させない）。

## scaffold の出力

**`scaffold/`（リポジトリ直下）は生成物だが、commit する。** Issue が指す受け渡しの契約で、dev-loop は
このファイルに対して実装するからである。**手で直さない**——直したいところは `spec_ir.json` を直して作り直す。
同梱の生成スクリプトは同じ入力から同じバイトを作り、**`--check` で、置いてあるものが古くないかを確かめる**。

| ファイル | 中身 |
| --- | --- |
| `scaffold/openapi.json` | OpenAPI 3.1（JSON） |
| `scaffold/types.py` | 入出力の型（Python の `TypedDict`） |
| `scaffold/tests/test_<機能>.py` | Red テスト（Python の `unittest`。実装が無ければ失敗する） |

**正本と開発のリポジトリが別なら**、`scaffold/` を開発のリポジトリへどう写すかは正本リポジトリの `CLAUDE.md` に
書いてもらう。**Issue の本文が sha256 を持つのは、中間表現（重ね合わせた全体の `build/merged/spec/spec_ir.json`）と
Red テストだけ**——`openapi.json`・`types.py` は指紋を持たず、中間表現は `scaffold/` の外にあり、commit もしない。
dev-loop は本文の sha256 を手元の中間表現と Red テストに当てるので、**開発のリポジトリにも正本の版を写して
重ね合わせるか、どこで当てるかを決めて書く**。

## ドキュメントのツール

**既定は MkDocs。** `docs/` を最初から閲覧できるように、プラグインは雛形（`templates/mkdocs/`）を持ち、
同梱のスクリプトで正本リポジトリへ写す（**手で写さない**）:

```bash
python3 <spec-loop の base ディレクトリ>/scripts/init-mkdocs.py [<正本リポジトリの根>] [--dry-run]
```

- **写すのは、正本リポジトリの `CLAUDE.md` がドキュメントのツールを決めておらず、MkDocs の設定（`mkdocs.yml`・`mkdocs.yaml`）も
  無いときだけ。** 設定が在ればスクリプトは何も写さない。**在るファイルは 1 バイトも変えない**——`pyproject.toml`・`.gitignore` が
  在れば触らず、足りない依存・行を示すので、足すかどうかは利用者が決める。
- 写すもの: `mkdocs.yml`（Material・`use_directory_urls: false`・nav は書かず自動）・`pyproject.toml`（uv。
  **MkDocs は 2 未満に固定**——2.0 は非互換の変更が予告されている）・`.gitignore`（`build/`・`site/`・`.venv/`・`__pycache__/`）・
  `hooks/spec_loop_pages.py`・`docs/index.md`・`docs/qa.md`。閲覧は `uv run mkdocs serve`。
- **CSV は Markdown に写さない。** 表示用のページに印（`<!-- spec-loop: qa -->`）を書き、フックが CSV から描く。
  `qa` の印は、各版の `docs/v<n>/shared/qa.csv` を**版ごとの節**に描く（重ね合わせない。アンカーは `v<n>-q-001`）。
  CSV の文字は表のセルにだけ置く（段落に置くと、行頭の `!!! ` や字下げがブロックの記法に読まれる）。
  ほかの CSV を描くときは、フックに描画関数を足す。
- **表示用のページは `shared/` に置かない**（`docs/qa.md` のように版の外に置く）。`shared/` は 2 つのサインオフが比べる範囲
  （`signoff-tags.md`）なので、表示用のファイルを入れると比べる中身が増える。版の外の名前は重ね合わせにも入らない（`versions.md`）。
- **フックはサーバーの起動時にしか読まれない**——直したら `mkdocs serve` を起動し直す。

## プロジェクトに任せること

MkDocs 以外のドキュメントのツール・サイトの分け方・スライドの形式は、**正本リポジトリの `CLAUDE.md` に書いてもらう**。
書いてあれば、そちらが上の既定より先に立つ。
