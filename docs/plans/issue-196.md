# Issue #196 — cmux: タブ再利用の部分一致で、前方一致する別の Issue/PR のタブを上書きする

## 1. 変更範囲

触る:

- `plugins/cmux/skills/cmux/SKILL.md` — 共通手順の一致規則（と版のバナー）
- `plugins/cmux/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — cmux の version
- `docs/plans/issue-196.md` — この計画ファイル

触らない:

- `plugins/orca/` — #194 で直し済み
- 共通手順の手順 1 と手順 2 が別の Bash 呼び出しに分かれている点（orca は 1 ブロックにまとめた）——
  Issue の受入基準の外。残課題
- description（3 箇所）——能力は変わらないので触らない

**範囲の広げ方の決定**: 一致規則を書き直す行で、`target` を Python のソースに `'$TARGET_URL'` で
埋め込む形をやめ、orca と同じく `sys.argv[1]` で渡す。**同じ行を書き換えるので分けない**
（`target` を 2 回使う式になり、埋め込みのままだと引用符を含む URL で式が壊れる）。

**範囲の拡張（実装中に決定）**: 実機（cmux 0.65.1）で測ると、**`cmux --json list-panels` の
ブラウザサーフェスに `url` キーが無い**（`ref`・`title`・`type` などはある）。
**旧規則でも新規則でも一致は 1 度も起きず、毎回 `open-split` で増える**——Issue の
「規則は同じ」の前提は、この版では成り立たない。**一致規則だけ直しても Issue の受入基準 2
（`/pull/N` のほうが再利用される）は満たせない**ので、**`url` が無いサーフェスは
`cmux --json browser --surface <ref> url` で URL を取る**ところまで広げる（同じ Python ブロックの中）。
`list-panels` が `url` を返す版ではそれを使う（追加の呼び出しをしない）。

**複製の数**: タブの一致規則を述べている箇所は `plugins/cmux/skills/cmux/SKILL.md` の 1 箇所だけ
（`docs/` と `plugins/cmux/README.md` を `再利用`・`部分一致` で引いて確認）。
版は 3 箇所（CI が見る）。**分けない理由**: 1 箇所なので分ける対象が無い。

## 2. デプロイ経路

- マーケットプレイス（`plugins/` と `marketplace.json`。利用者が `plugin update` で取る）。
- `docs/` は計画ファイルだけ（GitHub Pages には `docs/plans/` も載るが内容は記録のみ）。
- 破壊的・不可逆な操作は無い。

## 3. 受入基準

**I1. `/cmux` の共通手順は、`TARGET_URL` と同じページ（またはその下位ページ）のブラウザサーフェスだけを再利用し、別の Issue/PR のサーフェスを上書きしない。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 一致するサーフェスが無い | 空 → `open-split` | 空出力 |
| P2 完全一致のサーフェスがある | それを再利用 | `u == target` を先に探す |
| P3 **番号が前方一致する別のサーフェス**（`/issues/194` があって `/issues/19`） | 再利用しない（新規作成） | 前方一致の直後が `/` `#` `?` に限る |
| P4 下位ページ（`/pull/12/files`・`#issuecomment-…`・`?…`）だけがある | 再利用してよい | 同上 |
| P5 `/pull/12/files` と `/pull/12` の 2 枚（並び順はどちらも） | `/pull/12` を再利用 | 完全一致を先に探す |
| P6 ブラウザでないサーフェス（ターミナル）の `url` | 対象にしない | `type == 'browser'` を保持 |
| P7 `list-panels` 失敗・`url` が null | 空 → 新規作成（例外で落ちて再利用と読まない） | `or ''`・`2>/dev/null \|\| echo ""` |
| P8 3 モード（Issue / `-w` / `-r`）| 同じ規則 | どのモードも共通手順を通る |
| P9 `TARGET_URL` に引用符が入る | 式が壊れない | argv で渡す |
| P10 **`list-panels` が `url` を返さない版**（実機 0.65.1） | `browser --surface <ref> url` で取った URL に同じ規則 | 取れなかったサーフェスは対象外（`''`） |
| P11 `browser url` が失敗する・JSON でない | そのサーフェスを対象外にして続ける（全体を落とさない） | 例外を握ってそのサーフェスだけ `''` |

**I2. 版が 3 箇所で揃い、patch で上がっている（1.1.5 → 1.1.6）。** `check-all.py` が緑。

### 証明の手段

- P1〜P7・P9: 抽出した Python を、偽の `list-panels` JSON で走らせる（単体）。
- **Issue の受入基準 2 つ**（`/issues/194` があって `/issues/19` → 新規、`/pull/12/files` と `/pull/12`）:
  **このセッションは cmux の中で動いており、`cmux --json list-panels` が応答する**ので、
  実機でサーフェスを作って共通手順を流す。作ったサーフェスは片付ける。
- **未証明**: **他の cmux の版**（`list-panels` が `url` を返す版）での実機確認。手元は 0.65.1 だけ。
  偽の `cmux` で `url` を返す形（P1〜P9）は単体で当てている。

### 実施した verify（著者）

- **単体**（scratchpad の `unit196.py`。共通手順 1 の bash ブロックを `bash` ごと、偽の `cmux` で流す）:
  **19 件すべて期待どおり**。**陽性対照**: 同じ入力で旧規則のブロックを流すと
  P3（2 件）・P5・P9 で誤り、P10 の一致ケースでは何も返さない——検査は 2 つの規則を判別している。
- **実機**（cmux 0.65.1。scratchpad の `real196.sh` が SKILL.md の共通手順 1・2 を抜き出して流す）:
    - 受入基準 1: `/issues/194` のサーフェスがある状態で `/issues/19` → **新しいサーフェスが作られ**、
      194 は選ばれなかった。
    - 陽性対照: 同じ状態で `/issues/194` → **既存のサーフェスが選ばれ、増えなかった**
      （「選ばれない」が「一致がそもそも起きない」ではないことの対照）。
    - 受入基準 2: `/pull/195/files`（手前）と `/pull/195` の 2 枚 → **`/pull/195` が選ばれた**
      （Issue の `/pull/12` はこのリポジトリに無いので #195 に読み替え。性質は同じ）。
    - 旧規則の対照: 旧ブロックで `/issues/1`（`/issues/194` の前方一致）→ **新規作成**
      ——**旧規則は実機で一度も一致しない**（`url` が無い）ことの確認。
    - **観測窓**: 各回 1 度ずつ。作ったサーフェスは片付けて、開始時の状態（ターミナル 1 枚）に戻した。
- `python3 scripts/check-all.py`: **30/30 本**（失敗 0 / 飛ばし 0）。

### 生成物

**生成物なし**（cmux は図・`skill-metrics` の対象外。`SKILL.md` の測定値は dev-loop だけ）。

### 必須要件の掛け算

受入基準 × {Verifier, /code-review} × {1 パス目, 2 パス目} の 4 受け渡し。

## 4. 未解決・確認待ち

- 無し

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/196-cmux-tab-match`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-196`、
  起点 `2639705`、base 参照 `origin/main` → `2639705e510c25f0a73c586244f692fb0695f28c`
- 関門: 実装完了・著者の verify 済み。Verifier／`/code-review` は未着手（1 パス目から）
- 反証: —
- 交絡を潰した手順: 単体・実機とも旧規則を同じ入力で流す陽性対照、実機で「再利用が起きる」側の対照
- 割り目（手順 4）: （AskUserQuestion の回答をここに書く）

## 6. 既知の限界・決着済みの論点

（無し）
