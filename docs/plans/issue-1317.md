# Issue #1317 — spec-loop: acceptance の source の綴りが大文字小文字だけ違うとき、表の見出しが付くようにする

利用者が居る周（`/dev-loop:dev-loop 1317` の直接の起動）。spec-loop から来た Issue ではない（`spec-loop-handoff` の印は無い）。
本文に `作り直しの元: #1316` の行がある——PR の本文に写す。
直す線: `既定`（出所: 手順 3 の回答・2026-11-20）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — `load` の `loaded.spec_texts` を、`check_source` と同じ解決（ファイルシステムに解決させる）で全体の鍵を決める関数 `spec_texts` にする
- `scripts/test-scaffold.py` — 大文字小文字だけ違う `source` の試料（`spec/Order.md`）・区別するファイルシステムでの期待の差し替え（`FOLDING_CASES`）・変異 2 本（うち 1 本は `FOLDING_ONLY`）
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json`・`plugins/spec-loop/skills/*/SKILL.md` — 版（0.127.1 → 0.127.2。不具合の修正なので patch）
- `docs/plans/issue-1317.md` — この計画

触らない:

- `check_source` の判定（大文字小文字だけ違う綴りを止めるかどうか）——Issue の「直すこと」は原文の引き方だけ。止める形にすると #1301 の決めた「検査が通すなら原文に届く」を変える
- `references/spec-ir.md`——`acceptance` の `source` の綴りについての決まりは書いていない（`refs` の大文字小文字の行は別の項目）

複製の数: 原文の引き方は `load` の 1 箇所（`acceptance_section` は `loaded.spec_texts` を読むだけ）。解決の仕方は `check_source`・`source_lines` と同じ形の 3 箇所目になる——
分けない理由: `check_source` は一時ディレクトリの全体に当てる検査で、`load` の時点ではその一時ディレクトリが閉じている。`read_whole` の返り値を変えると呼び出し元が 4 箇所動くので、`spec_texts` で `spec/` だけを置き直す。

## デプロイ経路

main へのマージでプラグインの配布（カタログ・link-skills の利用者）。`docs/` は計画ファイルだけ（サイトの再ビルドは起きるが中身の変化は計画のページだけ）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | `check_source` が通す `source` の綴りは、どれも原文に届き、`acceptance` の行に表の見出しが付く | 大文字小文字だけ違う綴り（区別しない FS）・`./` を含む綴り・正しい綴り・複数の `source`・v2 以降の重ね合わせ（鍵は重ねた全体） | `spec_texts` がファイルシステムに解決させ、デバイスと inode で全体の鍵を引く。試料「source が大文字小文字だけ違う綴りでも…」（区別しない FS で 0 と見出し）・「source が ./ を含む綴りでも…」 |
| A2 | 試料の `source` を `spec/Order.md` にした `acceptance_dot_source` 相当の検査が、直す前は赤・直した後は緑（Issue の受入基準 1。陽性対照） | — | 直す前の `scaffold.py`（b1ad57b4）に新しいテストを当てて赤、直した後で緑（実測は下の「実機確認」） |
| A3 | 正しい綴りの生成物は直す前と同じバイト（Issue の受入基準 2） | `spec_texts` の値・`acceptance_section` の本文・ほかの生成物 | 値は `rendered[key]` のまま。既存の試料（本文をバイトで比べるもの）が緑のまま。直す前後で同じ正本から作った `scaffold/` を比べる |
| A4 | 大文字小文字を区別する FS（Linux の CI）では、綴りの違う `source` は今までどおり `check_source` が止め（1）、テストも緑 | CI | `FOLDING_CASES` で期待を `1`・`F-001.source: spec/Order.md が無い` に差し替え、`FOLDING_ONLY` の変異は当てない |
| A5 | `spec/` の外のファイルを読まない | `source` に `../` を含む綴り・`spec` の外の鍵 | `spec_texts` は `spec/` の鍵だけを置き、解決したパスが `spec/` の中にあるときだけ引く（`check_source` が先に止めるので二重） |
| A6 | 版が 3 種類で 0.127.2・歯止めが緑 | `check-all.py` | `check-all.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目に渡す | — | 再開点で記録 |

**証明できないもの（未証明）**: なし。区別しない FS（macOS の APFS）と、区別する FS（大文字小文字を区別する APFS のディスクイメージを `TMPDIR` にして代用）の両方で走らせた。
**ただし Linux の実機ではない**——Linux の CI で回る PR 側の CI で確かめる。

**生成物**: `SKILL.md` の測定値（設計 §8.2）は dev-loop の `SKILL.md` だけを測る——spec-loop の変更では動かない（`skill-metrics.py --check` で確かめる）。図の書き出しは無し。scaffold の生成物はテストの一時ディレクトリの中だけ。

## 実機確認

- 直した後: `python3 scripts/test-scaffold.py` → `OK: 試料 647 件・変異 524 件`（macOS・区別しない FS）
- 直す前（陽性対照）: 作業ツリーを scratchpad へ `.git` を除いて写し、`scaffold.py` を b1ad57b4 の版に戻して同じテストを当てる → rc=1。
  `試料が期待どおりでない: 受入基準: source が大文字小文字だけ違う綴りでも表の見出しが付く`（本文に見出しが無い）。ほかに出たのは新しい変異 2 本の「届いていない」だけ（直す前の本体に当てる箇所が無いので当然）
- 区別する FS: 大文字小文字を区別する APFS のディスクイメージを作って `TMPDIR` に向け、直した後のテストを当てる → `OK: 試料 647 件・変異 521 件（ほかに当てなかった変異 3 件 …）`。
  `case_folding` の探りが「区別する」を返したことを、当てなかった変異の行で確かめた

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1317-acceptance-source-case`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1317`・
  起点 `b1ad57b4`・base は `origin/main`（refs/remotes/origin/HEAD）を解決した `b1ad57b4bbc582ed7b38d05cc9028f67b32f1038`
- 交絡を潰した手順: 「区別する FS で緑」が探りの誤りで出ていないか——当てなかった変異 3 件の行（`case_folding` が False を返した印）と、ディスクイメージで `a` を作って `A` が無いことを見た。
  陽性対照「直す前で赤」は、写しの中で `scaffold.py` だけを差し替えた（テストは同じ版）
- 実装のコミット: `66660e79`（`check-all.py`: 98 本のうち 97 本 OK。落ちた `test-check-pptx-render.py` は実機の LibreOffice の 300 秒の時間切れで、
  同時に別の worktree（issue-1361）のテストが走っていた。この周は PPTX に触れていない。単独で回し直して `OK: 観測 30 件・変異 20 件`）
- 割り目（手順 4 の後）: 利用者の選択「ここで割る」（2026-11-20）——再開は worktree の中で `/clear` してから `/dev-loop:dev-loop 1317`、手順 5 から
- 関門: 未着手（次は 1 パス目。起点（1 パス目の関門に渡す時点の HEAD）は渡すときに書く）

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| （まだ無い） | | | |

- この周の起票: 0 件
