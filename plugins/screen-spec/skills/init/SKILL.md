---
name: init
description: "spec-loop の正本リポジトリに、画面設計書の置き場所（作業中の版の requirements/screens/）を用意する。画面・項目・遷移の 3 つの表（見出し行だけ）・案件ごとの設定（画面IDの接頭辞と profile）・共通仕様（common.md）の雛形・画面の仕様書の雛形を同梱のスクリプトで置き、検査（check-screens.py）が通ることを確かめる。profile（いまは web-spa）と、その上に重ねる外部の profile は、基盤の profile（platform-spec の shared/platform/settings.csv）が画面の profile を名指していればそれを、無ければ shared/infra.csv のフロントエンドの行から推して利用者に確かめ、選べば profile の列（外部の profile が足す列も）を表の見出し行に入れ、profile の節の雛形を共通仕様と仕様書の雛形の末尾に足す（profile は最初の版で決まり、後の版で変えられない）。Q&A 表は書かず、番号も振らない。置き済みなら何も書かない。正本が spec-loop の MkDocs の雛形を使うなら、表を仕様書の節に出し版ごとのモックをサイトに置くフックを、spec-loop の登録の口に同梱のスクリプトで登録する（mkdocs.yml は書き換えない）。画面設計書を始めたいときに使う。引数なし。"
---

# init スキル

<!-- skill-version: 0.12.5 -->
> **このスキルの版: 0.12.5**（プラグイン `screen-spec`）。
> 手元で読まれている版がリポジトリの最新より古いなら、
> `/plugin marketplace update` → `/plugin update screen-spec@claude-code-setup` の順に実行し、
> Claude Code を再起動する（[#63](https://github.com/hdknr/claude-code-setup/issues/63)）。

spec-loop の正本リポジトリに、画面設計書の置き場所を用意するスキル。
**書くのは同梱のスクリプトで、スキルは置く値（画面IDの接頭辞と profile）を利用者に確かめるだけ**——表と雛形を手で書かない。

**呼び出し形**: `/screen-spec:init`（プラグイン提供のスキルは常にプラグイン名で名前空間化される）。
**素のスキルとしては置けない**——決まりとスクリプトをプラグイン直下に置いて `../../` で指しているため。

## 決まり

**置き場所・3 つの表・案件ごとの設定は `../../references/tables.md`、仕様書と共通仕様の雛形の決まりは `../../references/prose.md`、
実現方式の profile は `../../references/profiles.md`、spec-loop との境目は `../../references/spec-loop.md` を正とする**（このスキルと同じプラグインの中にある）。

## 守ること

- **Q&A 表を書かない。Q&A の番号を振らない**——番号は spec-loop の req-loop・spec-review が振る（`../../references/spec-loop.md` の「Q&A の番号を振らない」）。
- **表と雛形を手で書かない**——下の手順のスクリプトが置く。スクリプトが 0 以外で終わったら、手で置き直さずに出力を利用者に見せて止まる。
- **profile と外部の profile を推測で決めない**——下の手順 2 で利用者に確かめ、手順 3 で 2 つとも明示で渡す（省くと基盤の profile の名指しが初期値になる——確かめずに省かない）。
- **commit しない**——置いたファイルを利用者に見せて終える。

## 手順

### 1. 正本の `docs` を決める

spec-loop の正本リポジトリの `docs`（版のディレクトリ `v1/`・`v2/`… の親）を決める。カレントのリポジトリに `docs/v1/` があればそこを使い、
無ければ利用者に訊く。**版が 1 つも無ければ止まる**——版を作るのは spec-loop（スクリプトも 3 で止まる）。

### 2. 置く値を確かめる

```bash
python3 <このスキルの base ディレクトリ>/../../scripts/write-screens.py hint <docs>
```

出力の `基盤の profile:` の行・`shared/infra.csv` のフロントエンドの行・このプラグインにある profile の一覧から、次の 3 つを決める。

- **profile と外部の profile**: 出力に `init の初期値（--profile と --external を省いたとき）: profile <p>、外部の profile <…>` の行があれば
  （基盤の profile が画面の profile を名指している。`../../references/profiles.md` の「基盤の profile から引く初期値」）、それを推す。
  無ければ、一覧にある profile のうち、フロントエンドの行に合うものを推し、外部の profile は `なし`。**一覧が空なら `未設定`・外部の profile は `なし`**（訊かない）。
  一覧があるなら `AskUserQuestion` で、推したもの（理由は基盤の profile の名指しか、フロントエンドの行）・ほかの profile・`未設定` を選択肢にして訊く
  （外部の profile は、推したものを選べばそれ、ほかを選べば `なし`。外部の profile は組み込みの profile の上にしか重ねられない）。
  **profile と外部の profile は表を置く最初の版で決まり、後の版で変えられない**（表の見出し行に profile の列と外部の profile が足す列が入る。`../../references/profiles.md` の「選び方」）ことも添えて訊く。
  方式がまだ決まっていなくても、使う見込みの profile を選べる——列と節に `N/A。実現方式が未定` と書いておける。
  **`基盤の profile: 読めない（…）` の行が出たら**、理由（clone が手元に無いなど）を利用者に見せ、直してから `hint` を走らせ直すか、値を決めて手順 3 で明示で渡す。
  **`基盤の profile: 画面の層が決まりに合わない（…）` か `基盤の profile: profile.csv が決まりに合わない（…）` の行が出たら**、同じ外部の profile は明示しても止まる——理由を利用者に見せ、次の 3 つのどれにするかを `AskUserQuestion` で訊く（`../../references/profiles.md` の「基盤の profile から引く初期値」。#1582・#1590・#1597）:
  外部の profile を直してタグを付け、基盤の profile の設定のタグをそれにしてから `hint` を走らせ直す（設定は `shared/` に在るので 2 つの承認を取り直すことになり、基盤の層もそのタグの時点で読むことになる——訊くときに添える）・
  `shared/` を触らずに、直したタグを行の案内のとおり `--external "<リポジトリ> <名前> <新しいタグ>"` で明示して手順 3 で渡す（外部の profile を直してタグを付けるのは利用者）・
  行の案内のとおり外部の profile を `なし` にする（どちらも `--profile` は行が名指す profile。`profile.csv` の行は `重ねる先` を読めないので `<画面の profile>` と出る——このプラグインにある profile の一覧から、上の推し方で利用者に選ばせる）。
- **画面IDの接頭辞**: 既定は `S-`。案件ですでに使っている画面ID の形があれば、それに合わせるかを `AskUserQuestion` で訊く。
  形は英大文字で始まり英大文字と数字が続き `-` で終わる（`../../references/tables.md` の「案件ごとの設定」）。

### 3. 置く

```bash
python3 <このスキルの base ディレクトリ>/../../scripts/write-screens.py init <docs> --prefix <接頭辞> --profile <profile> --external "<持ち主>/<リポジトリ> <名前> <タグ>"
```

外部の profile を使わないなら `--external なし`。終了コードと意味はスクリプトの docstring を正とする。**0 以外なら、何も書かれていない**——出力を利用者に見せて止まる
（3: 置き済み・版が無い、4: 外部の profile を読めない・`profile` に重ねられない）。

### 4. 確かめる

```bash
python3 <このスキルの base ディレクトリ>/../../scripts/check-screens.py <docs>
```

置いた直後は 0 になる（画面の行がまだ無い。profile の節の雛形は `N/A。実現方式が未定` で、検査を通る）。**0 以外なら、出力を利用者に見せて止まる**——置いたものを手で直さない。

### 5. MkDocs のフックを登録する（正本が spec-loop の MkDocs の雛形を使うときだけ）

正本の根（`docs` の親）に `hooks/spec_loop_pages.py` が在るなら、表を仕様書の節に出し版ごとのモックをサイトに置くフックを登録する（`mkdocs.yml` は書き換えない）:

```bash
python3 <このスキルの base ディレクトリ>/../../scripts/write-screens.py mkdocs <docs>
```

書くのは spec-loop の `init-mkdocs.py --hook` で、在れば変えない。**出力に `注意:` の行があれば**（フックが登録の口を持たない前の版の写し・`mkdocs.yml` がフックを指していない）、
利用者に見せる——取り込む手順は spec-loop の `references/tree.md` の「ドキュメントのツール」。決まり（このプラグインの見つけ方・正本の CI でビルドするとき）は `../../references/mkdocs.md` を正とする。
`hooks/spec_loop_pages.py` が無ければ飛ばす（MkDocs を使うかは spec-loop の側で決める）。

### 6. 終える

置いたファイル（スクリプトの出力の `書いた:` の行）と、次に画面を足すのは `/screen-spec:add` であることを利用者に伝える。
共通仕様（`common.md`）の節は利用者と埋める——書き方は `../../references/prose.md` の「共通仕様」。
