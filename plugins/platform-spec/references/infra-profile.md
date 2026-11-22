# 基盤の層の profile と、案件の基盤要件の表との照合

組織の開発ガイドのような外部の設計パターンを、パターンの持ち主のリポジトリに profile として置き、案件の基盤要件の表（spec-loop の `shared/infra.csv`）の行がその行を指す（#1312）。
**この文書は、platform-spec が持つ決まり——基盤の層の表の形・受け付ける形式の版の範囲・案件の設定・`profile の行` の書き方・照合——の原本である。**
照合の本体 `scripts/check-infra-profile.py` の定数はここの写しで、写しがずれていないかは、このプラグインを置いているリポジトリ（hdknr/claude-code-setup）のテスト test-check-infra-profile.py が突き合わせる。
**何を守り何を守らないか・終了コードは、スクリプトの docstring を正とする。**

profile の置き場所・`profile.csv` の列・層の表の先頭 3 列・形式の版の比べ方・リンクの書き方・手元の clone の探し方は spec-loop の決まり（spec-loop の `references/external-profile.md`）で、ここでは写さない。
platform-spec は spec-loop の `scripts/external-profile.py` を読み込んで profile を読む（`references/spec-loop.md`）。

## 基盤の層の表

profile の `profile.csv` に、層の名前は `基盤` で 1 行置き、`ファイル` が基盤の層の表を指す（例: `infra.csv`）。

| 列 | 書くもの |
| --- | --- |
| `ID` | 行の鍵。案件の `infra.csv` の `profile の行` がこれを指す。層の中で重ねない |
| `要約` | 選択の短い要約（例: 「AWS（東京リージョン）・ECS」）。本文は写さない |
| `リンク` | 本文（ガイドのページの節）を指す。書き方は spec-loop の決まり |
| `項目` | 案件の `infra.csv` のどの項目の案か（`言語`・`DBMS`・`ホスティング環境` など。綴りは案件の表と同じ） |

- 見出しの行は、この 4 列をこの順・この綴りで置く。違えば読まない（判定できなかった）。
- profile は案を出すだけで、決めるのは発注者のまま——案件の基盤要件は spec-loop の共有の Q&A 表で発注者が決める（spec-loop の `references/tree.md` の「基盤要件」）。

## 形式の版の範囲

基盤の層の `形式の版` は、次の範囲のものだけを読む（比べ方は spec-loop の決まり）。

| 下限（この版を含む） | 上限（この版を含まない） |
| --- | --- |
| `1` | `2` |

- 形式の版 1 の表は、上の 4 列である。列を変えるときは形式の版を上げ、この範囲と照合を同じ周で直す。

## 案件の設定

使う profile とその版を、正本の版の中の `shared/platform/settings.csv` に置く。見出しの行は `項目,値` で、1 項目 1 行。

| 項目 | 値 |
| --- | --- |
| `リポジトリ` | profile を置いたリポジトリ（`<持ち主>/<名前>`）。手元の clone の探し方はこの名前で引く |
| `profile` | `spec-profile/` の下の profile の名前 |
| `タグ` | 読む版（profile のリポジトリのタグ） |

- 3 つの項目は全部置き、値を空にしない。ほかの項目を置かない。
- `shared/` に置くので、spec-loop の 2 つのサインオフが比べる範囲に入る——タグを変えれば、`infra.csv` の `profile の行` が指す中身が変わるので、承認を取り直す。
- spec-loop の版の重ね方ではファイルの単位で重なる——v2 以降で値を変えるなら、ファイルごと置く。
- 設定を置かない案件は platform-spec を使っていない（spec-loop は今までどおり動く）。

## `profile の行` の書き方

案件の `infra.csv` の末尾の任意の列 `profile の行`（列の名前の原本は spec-loop の `references/tree.md` の「基盤要件」）に、基盤の層の `ID` を書く。

- 複数は `・` で区切る（例: `HOST-1・HOST-2`）。区切った間・前後を空にしない。
- 空のセルは「profile の行を指さない」（標準から外れた行・profile に無い項目）。
- `profile の行` を書いたら、上の案件の設定も置く。

## 照合

```bash
python3 <platform-spec の base ディレクトリ>/scripts/check-infra-profile.py <正本の docs> [--upto <n>] [--clone <profile の手元の clone>] [--spec-loop <spec-loop のプラグインの根>]
```

- spec-loop の重ね方で重ねた全体の `shared/infra.csv` と案件の設定を読み、設定のタグの時点の基盤の層に、`profile の行` の ID が在るかを照らす。
  無い ID（別のタグにだけ在る ID も）は、表の行と ID を名指しする。
- 手元の clone は spec-loop の探し方で探す——引数 `--clone`・環境変数・正本の根の `CLAUDE.md` の行。正本の根は `docs` の親である。
- 読むだけで、正本にも clone にも書かない。
