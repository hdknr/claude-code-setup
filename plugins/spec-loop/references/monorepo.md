# モノレポのレイアウト

正本リポジトリ（spec-loop）と開発のリポジトリ（dev-loop）を **1 つのリポジトリ（モノレポ）** に置くときの推奨の形（#994）。
scaffold の既定は「同じリポジトリとして扱う」（`skills/scaffold/SKILL.md` の「はじめに」）なので、`scaffold/` を写す手順も
Issue の指紋を当てる場所も決めずに済む——**仕組みとしてはモノレポのほうが素直である。**

ただし `tree.md` のツリーは、**リポジトリの直下を spec-loop とドキュメントの道具が占める**前提で書いてある。
実装を同じリポジトリに足すときは、この文書の形に揃え、**決めたことを直下の `CLAUDE.md` に書く**（下の「CLAUDE.md の分担」）。
**この文書は推奨である**——正本リポジトリの `CLAUDE.md` に別の置き方を書いたなら、それに従う。

## 推奨のレイアウト

```
<リポジトリの根>/
├── docs/                    # MkDocs の docs_dir（tree.md のとおり）
│   ├── v<n>/                # 仕様の版（shared/・requirements/・spec/……）
│   ├── dev/                 # 開発用の文書（ADR・手順書）。版の外（下の「開発用の文書」）
│   └── index.md・qa.md……    # 表示用のページ（版の外）
├── scaffold/                # scaffold の生成物（commit する。Red テストは scaffold/tests/）
├── spec-review/             # 仕様レビューの記録
├── build/                   # spec-loop の生成物（commit しない。下の「build/ を分けない」）
├── mkdocs.yml・hooks/       # ドキュメントのツール（init-mkdocs.py が写す）
├── pyproject.toml           # MkDocs の依存だけ（package = false。下の「pyproject.toml と .gitignore」）
├── .gitignore               # build/・site/・.venv/・__pycache__/
├── CLAUDE.md                # 置き場所の表と、spec-loop・dev-loop の両方が読む項目
├── .claude/dev-loop.md      # dev-loop の verify・deploy（任意）
├── backend/                 # 実装（Python）。自分の pyproject.toml・CLAUDE.md を持ってよい
│   └── app/spec_impl.py     # Red テストが読み込むモジュール（impl_module。下の「Red テストを走らせる」）
└── frontend/                # 実装（フロントエンド）。ビルドの出力は frontend/ の中に置く
```

- **実装は直下に置かず、サブディレクトリ（`backend/`・`frontend/` など）に置く。** 直下には `init-mkdocs.py` が
  `pyproject.toml`・`.gitignore`・`mkdocs.yml`・`hooks/`・`docs/` を写す（`tree.md` の「ドキュメントのツール」）。
  実装を直下に置くと、`pyproject.toml` を共有するかどうかを最初に決めることになる。
- **名前は例である。** `backend/`・`frontend/` でなくてよいが、**spec-loop が直下で使う名前**（`docs/`・`scaffold/`・
  `spec-review/`・`build/`・`site/`・`hooks/`）は実装に使わない。

## build/ を分けない

spec-loop の生成物（`build/merged/`・`build/merged-v<n>/`（撤去の Issue の本文が作らせる前の版の全体）・`build/scaffold/`・
`build/feasibility/`・`build/proposal/`・`build/req-loop/`。置き場所は `tree.md` の「生成物の置き場所」と各スキルの `SKILL.md`）は、
**モノレポでも `build/spec-loop/` に寄せない。** 理由:

- **実装をサブディレクトリに置けば、ぶつからない。** フロントエンドのビルド道具が慣習で使う `build/` は
  `frontend/build/` になり、直下の `build/` とは別のディレクトリである。
- **寄せると壊れる変更になる。** 出力先はスクリプト（`scaffold.py`・`build-proposal.py` など）・Issue の本文
  （`build/merged/spec/spec_ir.json` を指す）・dev-loop が spec-loop の Issue を読む手順・各スキルの `SKILL.md` に書いてあり、
  すでにある正本の手順と CI も変わる。名前空間を分けることで得るものは、上の形では無い。

それでも実装のビルドを直下の `build/` に出す道具を使うなら、**出力先を実装のディレクトリの中に変える**。
**直下の `build/` の下は spec-loop に任せ、実装の出力を置かない**——上に挙げた名前（`build/merged-v1/` のような版つきの名前を含む）と
ぶつけないためで、名前を 1 つずつ避けるより確かである。

**`.gitignore` の `build/` はどの階層にも効く**（`/` を末尾にしか持たないパターンなので、`frontend/build/` も
`backend/build/` も無視される）。実装のビルドの出力を commit しないなら、そのままでよい。
**実装の中に commit したい `build/` という名前のディレクトリがあるなら**、実装のディレクトリの `.gitignore` に例外（`!build/`）を書く
（`backend/.gitignore` に `!build/` を書くと `backend/build/` は無視されなくなり、`frontend/build/` と直下の `build/` は無視されたままだった。
雛形の `.gitignore` で `git check-ignore` と `git status` で確かめた）。

## pyproject.toml と .gitignore

**直下の `pyproject.toml` は MkDocs の依存だけにし（雛形のまま。`package = false`）、実装は自分の `pyproject.toml` を
`backend/` に持つ。** 2 つの形がある——どちらでも Red テストは走らせられる（下の「Red テストを走らせる」）:

| 形 | やること | 向いているとき |
| --- | --- | --- |
| **別々のプロジェクト** | 直下で `uv run mkdocs serve`、実装は `cd backend && uv run …` | ドキュメントと実装の依存を混ぜたくない |
| **uv の workspace** | 直下の `pyproject.toml` に下の 1 節を足す | 1 つの `.venv` で両方を回したい |

```toml
[tool.uv.workspace]
members = ["backend"]
```

- **雛形を変えずに足せる。** 雛形の `pyproject.toml` にこの節を足し、`backend/pyproject.toml` を置くと `uv lock` が通る
  （uv 0.11.14 で確かめた）。**`uv lock` が通ることは、member を作れることを意味しない**——作れるかは次の `uv sync --all-packages` で分かる。
- **確かめた member の形は `backend/src/app/`**（hatchling で `[tool.hatch.build.targets.wheel]` に `packages = ["src/app"]`）である。
  **上の「推奨のレイアウト」の `backend/app/` のまま、`packages` を書かずに hatchling で作らせると、`uv sync --all-packages` が失敗した**
  （作るものが見つからないと止まり、`import app` は `ModuleNotFoundError`）。workspace にするなら、member が作れる形
  （`src/` に置いて `packages` を書く、など）にしてから下の確かめ方で読み込めることを見る。**`src/` の形では `PYTHONPATH` の値も
  `backend/src` になる**（下の「Red テストを走らせる」の `backend` を読み替える）。
- **`uv sync` だけでは member は入らない**——`uv sync --all-packages` で `backend` が直下の `.venv` に入り、
  直下から `import app` できるようになる（同上。`uv sync` の後は `ModuleNotFoundError` だった）。
- **`--all-packages` の後に素の `uv sync` を走らせると、member は消える**（同上。`Uninstalled 1 package - backend` と出て、
  `import app` が `ModuleNotFoundError` に戻った）。ドキュメントの依存を更新するときも `uv sync --all-packages` を使う。
  **消えても Red テストは「未実装」で失敗するだけ**なので、下の「付け忘れは『未実装』と同じに見える」と同じ形で黙って通りうる。
- **`init-mkdocs.py` の前から直下に `pyproject.toml` があれば、スクリプトはそれを変えずに足りない依存を示す**
  （`tree.md` の「ドキュメントのツール」）。実装の `pyproject.toml` を直下に置いていたなら、`backend/` に移してから
  `init-mkdocs.py` を走らせると、雛形がそのまま写る。

**`.gitignore` は直下の 1 本（雛形）で spec-loop の分は足りる**（`build/`・`site/`・`.venv/`・`__pycache__/`）。
実装だけが要る行（`node_modules/` など）は、実装のディレクトリの `.gitignore` に書く。

## Red テストを走らせる

Red テスト（`scaffold/tests/test_<機能>.py`）は**リポジトリの根から** `importlib.import_module(IMPL_MODULE)` で実装を読み込む。
実装が `backend/` にあるなら、**`backend/` を読み込みの経路に入れる。**

1. **`impl_module` を、最初の scaffold の前に決める。** 実装のディレクトリ（`backend/`）から見たモジュール名を書く
   （`backend/app/spec_impl.py` なら `app.spec_impl`）。**後から変えると、機能が同じでも全部の機能が `変更` になる**
   （`handoff-issue.md`）。書く場所は中間表現の `impl_module`（`spec-ir.md` の「全体」）。
2. **`PYTHONPATH` で読み込む**:

   ```bash
   PYTHONPATH=backend python3 -m unittest discover -s scaffold/tests
   PYTHONPATH=backend python3 <spec-loop の base ディレクトリ>/scripts/scaffold.py --repo . --red-check
   ```

   - **`--red-check` も同じ `PYTHONPATH` で走らせる**——Red テストを走らせる子のプロセスは環境を引き継ぐ。
   - **確かめた範囲**: `backend/app/spec_impl.py` に正しい実装を置いた試料で、1 行目は緑、実装を誤ったものに替えると失敗した。
     2 行目は正しい実装で「もう緑 3 件」と出て 0 だった——**ただし v1 の `--red-check` は、誤った実装でも `PYTHONPATH` の付け忘れでも 0 を返す**
     （下の「付け忘れは『未実装』と同じに見える」）。**`--red-check` の終了コードは、読み込めているかを決めない**——見分け方は下の同じ節。
   - **走らせる Python は、実装の依存を読み込めるものにする。** 試料の実装は標準ライブラリだけだった。実装がほかのパッケージに依存するなら、
     素の `python3` ではその依存が読み込めず、Red テストはエラーになる——実装の環境の Python（`backend/.venv/bin/python` など）で走らせる
     （**この形は確かめていない**）。`--red-check` は `scaffold.py` を走らせた Python で Red テストを走らせる。
3. **workspace の形なら**、member を作れたうえで（上の「pyproject.toml と .gitignore」）、`uv sync --all-packages` の後は
   `PYTHONPATH` を付けずに直下の `.venv` で読み込める（`uv run python -m unittest discover -s scaffold/tests`）。
   **確かめたのは `src/` の形での `import` までで、この形で Red テストと `--red-check` を走らせることは確かめていない。**
   読み込めることの確かめ方は `uv run python -c "import app.spec_impl"`——**素の `uv sync` の後は失敗する**（member が消える）。
4. **Issue の本文に書かれた `unittest` のコマンドは、どれも読み込み方を持たない。** scaffold が作る本文は、Red テストの「回し方」
   （`python3 -m unittest discover -s scaffold/tests -p <ファイル>`）・変更と撤去の本文の回帰（`-p` 無しで `scaffold/tests` 全部）・
   性能テストの「回し方」（`-s scaffold/perf`。性能テストも同じ読み込み方で実装を探す）を「正本リポジトリの根で」と書き、
   実装の場所はモジュール名（`app.spec_impl`）だけを書く。dev-loop はこの本文を受入基準として写すので、
   **直下の `CLAUDE.md`（か `.claude/dev-loop.md`）に「Issue の本文の `unittest` のコマンドはどれも `PYTHONPATH=backend` を付けて走らせる」
   「`impl_module` のモジュールは `backend/` の下に置く」と書く**（下の「CLAUDE.md の分担」）。書かなければ、dev-loop の周は付け忘れたまま
   「未実装」の失敗を数えるか（撤去の回帰は前も後も全部が「未実装」で、「前に緑だったものが後も緑」が中身なしに通る）、モジュールを根に作って緑にしうる。

**付け忘れは「未実装」と同じに見える。** `PYTHONPATH` を付けずに走らせると、Red テストは
**「未実装: app.spec_impl.<関数> が無い」で失敗する**——読み込めないことと、実装が無いことが同じ出力になる。
**回帰のケース（前の版から変わらないケース）が 1 つも無い版の `--red-check` は、「全部が失敗」を期待どおりとして 0 を返す**ので、
付け忘れが黙って通る。v1 はいつもこれにあたり、`impl_module` だけを変えた版もこれにあたる（全部のケースが `変更` になる）。
**回帰はケースごとに決まる**——変更の機能でも変わらないケースは回帰なので、回帰のケースのある版で全部が「未実装」なら、
`--red-check` は回帰のケースを判定していないと言って 2 を返す（`scaffold.py` の `red_check`。v1 と、変更の機能 2 つに変わらないケースの残る v2 を試料で確かめた）。

**見分け方は 2 段に分ける**——どちらか一方では足りない:

1. **置き場所**: 実装のモジュールを置いたら、そこから読み込めることを確かめる。この 1 行は自分で `PYTHONPATH` を付けるので、
   **テストのコマンドに付けたかは見分けない**——見分けるのは、モジュールが `backend/` の下の正しい名前にあることまで。

   ```bash
   PYTHONPATH=backend python3 -c "import app.spec_impl"
   ```

2. **テストのコマンド**: 実装に関数を 1 つでも置いたあとは、Red テスト（か `--red-check`）の出力の失敗が**全部「未実装: …」で始まっていないか**を見る。
   置いた関数のテストまで「未実装」で落ちるなら、そのコマンドは実装を読み込んでいない（付け忘れ・workspace の member が消えたなど）。
   **実装がまだ 1 つも無いあいだは、この形でも見分けられない**——1 の行と、コマンドに `PYTHONPATH` があることを目で見て確かめる。

**実装が Python でないなら、この文書の形は使えない。** 基盤要件の言語が Python で始まらない決定なら、`scaffold.py` は止まる
（`tree.md` の「基盤要件」の「ゲート」）。

## CLAUDE.md の分担

**scaffold が読むのは直下の `CLAUDE.md` である**（`skills/scaffold/SKILL.md` の「はじめに」）。だから `impl_module` と読み込み方は、
サブディレクトリの `CLAUDE.md` ではなく**直下に書く**。分担の推奨:

| ファイル | 書くこと |
| --- | --- |
| 直下の `CLAUDE.md` | 置き場所の表（上の「推奨のレイアウト」のうち、このリポジトリで使うもの）・spec-loop の事情（scaffold の「はじめに」の項目）・実装の場所への指し先 |
| `.claude/dev-loop.md` | dev-loop の verify・deploy・「歯止めを全部回す 1 本のコマンド」（dev-loop はここを追補設定として最優先で読む） |
| `backend/CLAUDE.md` など | その実装だけのコーディング規約・依存の入れ方 |

直下の `CLAUDE.md` に書く項目の雛形（scaffold の「はじめに」の表と同じ項目）:

```markdown
## 置き場所

- 仕様: `docs/v<n>/`（spec-loop の `references/tree.md`）。開発用の文書は `docs/dev/`
- 実装: `backend/`（Python）・`frontend/`

## spec-loop（scaffold）

- 実装のモジュール名（`impl_module`）: `app.spec_impl`（`backend/` から見た名前。モジュールは `backend/app/spec_impl.py` に置く——根に作らない）
- Red テストの走らせ方: 根で `PYTHONPATH=backend python3 -m unittest discover -s scaffold/tests`
  （Issue の本文の `unittest` のコマンド——回し方・回帰・性能テスト——にも、どれも `PYTHONPATH=backend` を付けて走らせる。
  先に `PYTHONPATH=backend python3 -c "import app.spec_impl"` で置き場所を確かめ、実装を置いたあとは失敗が全部「未実装」でないかを見る）
- 正本と開発のリポジトリ: 同じリポジトリ
- Issue を登録するリポジトリ・ラベル: <owner>/<repo>・<ラベル>
- commit・push の決まり: <決まり>
```

**サブディレクトリの `CLAUDE.md` がいつ読み込まれるかは、Claude Code の動きによる**（ここでは確かめていない）。
spec-loop・dev-loop のどちらも頼る項目（Red テストの走らせ方・verify のコマンド）を、サブディレクトリの `CLAUDE.md` だけに書かない。

## 開発用の文書

**ADR・手順書は `docs/dev/` のような版の外のディレクトリに置く。** `docs/v<n>/` の下には置かない——
`docs/v<n>/` は重ね合わせの対象で（`versions.md`）、その中の `shared/`・`requirements/`・`spec/` はサインオフで比べる範囲である
（`signoff-tags.md`）。

- **`merge-versions.py` は、`v` と数字で始まらない名前を読まない**——`docs/dev/` は重ね合わせの全体に入らない
  （試料で確かめた）。**`docs/v1-notes/` のように `v` と数字で始まる名前は、版の名前の誤りとして名指しされる**——付けない。
- `docs/dev/` は MkDocs の `docs_dir` の中なので、サイトにも載る。載せたくないなら `docs/` の外（`dev-docs/` など）に置く。
- 開発用のスクリプトの置き場所は spec-loop は決めない——spec-loop のスクリプトはプラグインの中から呼ぶので、直下の
  `scripts/` を使わない。実装のディレクトリの中に置くと、仕様と実装の境目が分かりやすい。

## 2 つの「版」

モノレポでは、**仕様の版**（`docs/v<n>/`）と**アプリのリリース**が同じリポジトリに並ぶ。タグの名前で分ける:

| タグ | 意味 | 付ける人 |
| --- | --- | --- |
| `signoff/v<n>/req-<k>`・`signoff/v<n>/budget-<k>` | 仕様の版の承認（`signoff-tags.md`） | 人間 |
| `release-v<n>` | **仕様の版の凍結**（`versions.md` の「凍結」。`check-frozen.py` が見る） | 人間 |
| `v1.0.0` など | アプリのリリース | 開発の決まり |

- **アプリのリリースに `release-v<数字>` の形を使わない。** `check-frozen.py` は `release-v` と数字だけの名前（`release-v1`）を
  **仕様の版の凍結**として数える——アプリの `release-v1` を付けると、`docs/v1/` が凍結したと読まれる。
  `v1.0.0`・`app-v1.0.0` のような名前にする。
- 素の `v<n>`・`v1.0.0` のタグは、承認のタグ（`signoff/` の下）とぶつからない（`signoff-tags.md`）。

## CI のパスの分け方

仕様の変更と実装の変更で、走らせる検査を分けてよい。**`scaffold/` の変更は両方に入れる**——Red テストは実装に当てる契約なので、
仕様が変わって `scaffold/` が作り直されたら実装のテストも回す。GitHub Actions の例:

```yaml
on:
  pull_request:
    paths: ["docs/**", "scaffold/**", "spec-review/**", "mkdocs.yml", "hooks/**"]
# 仕様の検査（例）:
#   python3 <spec-loop の base ディレクトリ>/scripts/check-qa-csv.py docs/v<n>/shared/qa.csv
#   python3 <spec-loop の base ディレクトリ>/scripts/scaffold.py --repo . --check
#   python3 <spec-loop の base ディレクトリ>/scripts/check-frozen.py   # fetch-depth: 0 で取る（versions.md）
#   uv run mkdocs build --strict
```

```yaml
on:
  pull_request:
    paths: ["backend/**", "scaffold/**"]
# 実装の検査（例）:
#   PYTHONPATH=backend python3 -m unittest discover -s scaffold/tests
#   （実装自身のテスト）
```

**Red テストを全部回す検査は、版の機能を実装し終えるまで赤い**——Red テストは、まだ実装していない機能と、足した・変えたケースで失敗するように作る。
**マージの条件にするのは、実装が緑にしたケースだけを見る検査**（`green-list.py check`）である——選び方・一覧の書き直し・性能テストの扱い・雛形のジョブは
`tree.md` の「Red テストを CI で走らせ続ける」を正とする（`PYTHONPATH` は上の「Red テストを走らせる」と同じに付ける）。

CI でプラグインのスクリプトをどこから取るかは、正本リポジトリの `CLAUDE.md` に書いてもらう（この文書は決めない）。
