# Issue #1100 — spec-loop: req-loop が画面の表を検査して起票し、PPTX にモックへのリンクを載せる（#1081 段 4）

**不在の周である**——cruise（親 Issue #1081）の子として回す。出所: `/dev-loop:cruise 1081 --absent` の起動（2026-11-16T04:38Z）。
確かめた線（台帳 `issue-1081`。出所: 利用者の確認（起動時・2026-11-16、配布を見せて確かめた））:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。実機確認の線は無い。
#1100 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。
この周はマージしない（親がする）——PR を作り、PR 側の CI が通るのを見るところまで。
依存先 #1096（PR #1136）・#1097（PR #1119）は main にマージ済み（`6f815ea`）。**#1098（PR #1124）は利用者の判断待ちで、その中身を前提にしない。**
前提の確認の Issue（閉じない・閉じるキーワードで指さない）: #1104・#1105（承認済み）、#1109〜#1138 のうち推奨で決めて確認待ちのもの（親の委譲文の一覧）。
重い検査は run-serial 越し（枠 1 本）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/qa-to-pptx.py` — `--links <JSON>`（質問の番号 → リンク）を受け、その質問の頁にリンクを載せる。渡さなければ今と同じバイト
- `plugins/spec-loop/scripts/screen-gate.py` — docstring だけ（req-loop が出力の `screen-spec: 起票の候補: ` の行を起票の候補として読む）
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 手順の順（回答の反映 → 起票 → 検査 → モックの生成 → PPTX）・画面の表の起票の候補を起票する・モックの生成・リンクの表・PPTX に `--links`
- `plugins/spec-loop/references/tree.md` — 「スライドの置き場所」に、`--links` を渡したときはリンクの表も入力であること
- `plugins/spec-loop/skills/*/SKILL.md` — 全スキルの版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — spec-loop の版
- `.claude-plugin/marketplace.json` — spec-loop の版
- `scripts/test-qa-to-pptx.py` — `--links` の試料・拒む形・渡さないときに今と同じ形・変異
- `scripts/test-screen-gate.py` — 番号の無い印が起票の候補として出る試料（陽性・陰性）と変異
- `CLAUDE.md` — プロジェクト構成の `qa-to-pptx.py` の行に `--links`
- `docs/plans/issue-1100.md` — この計画

触らない:

- `plugins/screen-spec/` — 検査（`check-screens.py`）は前から起票の候補を出している。生成器（`build-mock.py`）の「書くのは 1 ファイルだけ」も変えない（下の穴 1）
- レビュー会の運用（会で出た指摘の受け皿・見せたモックの記録・見た目の指摘・画面ごとのまとめ・回答の書き写し）——#1082
- MkDocs のフック（#1098）・scaffold（#1099）
- `qa-csv.md`・`spec-scope.md` などほかの原本
- 公開ページ（`docs/` のうち計画のほか）

複製の数: 「画面の表の起票の候補を req-loop が起票する」を述べる箇所——req-loop `SKILL.md`（手順）、screen-gate の docstring（指す 1 行）、screen-spec の `tables.md`・`spec-loop.md`・`prose.md`・`add` の `SKILL.md`（前から「req-loop・spec-review が番号を振る」と書いている——触らない）で 6 箇所。
「PPTX の質問にモックへのリンクを載せる」は qa-to-pptx の docstring（原本）・req-loop `SKILL.md`（呼び方）・`tree.md`（入力が増えること）・CLAUDE.md（1 行）で 4 箇所。
**分けない理由**: 起票の手順は req-loop の本文に 1 つだけ置き、screen-gate とスクリプトは「何を出すか」だけを書く。リンクの口の決まり（形式・拒む形）は qa-to-pptx の docstring に 1 つだけ置き、ほかは指すだけにする。

依存の追加・更新: なし

仕様の振る舞い: 対象外（このリポジトリに spec-loop の正本は無い）

## 決めたこと（実装で決めてよいもの）

- **`--links` の形式は JSON のオブジェクト**（鍵が質問の番号、値がリンクの文字列）。読めない・オブジェクトでない・資料に載る行に無い番号・値が空か文字列でない・`--links` を 2 度書いた、はどれも 2 で、出力を作らず既存の出力に触らない（`--focus` と同じ扱い）。
- **リンクは質問の頁（1 問 1 枚）にだけ載せる**——「モック: <リンク>」の 1 段落で、文字にハイパーリンク（スライドの関係に `TargetMode="External"`）を付ける。表紙・一覧・今回の会で決めたい問の枚には載せない。
- **渡さないときは今と同じバイト**——関係のファイル（`slide<n>.xml.rels`）も今と同じ。
- **モックを作れなかった（`build-mock.py` が 0 以外）なら、`--links` を渡さずに PPTX を作り、作れなかったことを報告する**（レビュー会の資料は Q&A 表だけでも作れる）。
- **req-loop は画面の関門を手順 3（起票の候補を読む）と手順 4（検査）の 2 回当てる**——起票した番号を印に添えた後の表で、候補が 0 になったことを手順 4 で見る。

## 決めたこと（仕様の穴。`仕様の穴 = 推奨で決めて起票` の線で推奨により決めた）

- **穴 1: 質問ごとのリンクの表を誰が作るか**——#1100・#1081 は「`qa-to-pptx.py` に質問ごとのリンクを外から渡す口を足す」と書くが、外で誰が「質問 → 画面」を決めて表を作るかを決めていない。
  - 選択肢: A) req-loop（スキル）が、重ね合わせた全体（`build/merged`）の画面の表から screen-spec の `references/mock.md` の「その質問の画面」（質問の番号がセルにある最初の画面）を引いて書く（推奨）／ B) screen-spec の `build-mock.py` がモックと一緒にリンクの表を書き出す（screen-spec の「書くのは出力の 1 ファイルだけ」を変える）／ C) spec-loop に同じ逆引きを写したスクリプトを置く（spec-loop が screen-spec の表の列を知る）
  - 推奨 A。理由: #1100 の範囲（req-loop と `qa-to-pptx.py`）に収まり、screen-spec の決まりも spec-loop の依存の向きも変えない。誤ったときに起きるのは PPTX のリンクが別の画面を開くことだけで、表・仕様・モックは変わらない。手で引く手間が重いと分かったら B に移せる（`--links` の形はそのまま使える）。
- **穴 2: リンクの行き先の形**——#1081 は「PPTX の質問ごとに `#screen=S-004` などのリンクを載せる」とだけ書き、どこのモックを指すか（相対のパス・絶対のパス・公開した URL）を決めていない。
  - 選択肢: A) PPTX の置き場所からモックへの相対のパス（既定の置き場所なら `../mock/v<n>/index.html#screen=<画面ID>`）（推奨）／ B) `file://` の絶対のパス／ C) MkDocs で公開したモックの URL
  - 推奨 A。理由: PPTX（`build/req-loop/`）もモック（`build/mock/v<n>/`）も同じリポジトリの `build/` に作るので、リポジトリをどこに置いても同じリンクで開ける。B は作った人の手元でしか開けない。C は公開の仕組み（#1098）が利用者の判断待ちで、決まっていない。
- 決めた値は受入基準を足さない（`absent-lines.md`）。確認の Issue は PR を作った後に穴ごとに 1 件立てる。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ。spec-loop の版が上がる）。公開ページ（`docs/`）は触らない（計画のほか）。

## 版の上げ方

spec-loop を **minor** で上げる（能力の追加。0.x なので壊れる変更も minor。main の先端の版から 1 つ上げる——`0.96.0` → `0.97.0`）。`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行。
マージの直前に main が進んでいたら、main の先端の spec-loop の版から minor で 1 つ上げた値に上げ直し、
`check-plugin-versions.py`・`skill-metrics.py --check` だけ回して push し、PR 側の CI を見る（cruise の `references/parallel.md` の「版とマージの順」・CLAUDE.md の「並行する周は、同じ版に上げて衝突する」の 5）。

## 受入基準（不変条件 × 経路）

入口: `qa-to-pptx.py` の CLI（`--links` あり・なし・`--focus` と一緒）と、それを読む `build-proposal.py`（`package`・`write`・`markdown_slides`）・`check-spec-exit.py`（`read_rows`）、
`screen-gate.py` の CLI（req-loop の手順 3・4、spec-review の手順 1、`check-spec-exit.py --docs`・`scaffold.py` が関数として読む）、req-loop の手順の本文。
画面の表は v1 にも v2 以降にも置け、印は表のセルにも散文の仕様書にも書ける。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| U1 | 画面の表の本文に未決定の印があって Q&A の番号が添えていない例で、req-loop の手順の機械の部分（`screen-gate.py`）がそれを起票の候補（`screen-spec: 起票の候補: <場所>: <値>`）として出す。番号を添えた印は候補に出ない | 表のセル・散文の行、`screen-gate.py` の出力の写し | screen-spec の検査の出力を全部写す（今のまま）。テストで陽性・陰性と変異 |
| U2 | リンクを渡した質問の PPTX の頁に、そのリンクが載る（文字とハイパーリンクの関係） | `--links` のファイル・`--focus` との組み合わせ | `question_slide` が段落を足し、`package` が関係を足す。テストで頁と関係を見る |
| U3（回帰） | `--links` を渡さないときの PPTX は今（main）と同じバイト | `qa-to-pptx.py` の CLI・`build-proposal.py --pptx`（`package` を読む） | 渡さないときは関係も段落も足さない。main の版と同じ入力で作って `cmp`（実機確認）。テストは関係と段落が無いこと |
| U4 | `--links` の拒む形（読めない・オブジェクトでない・載らない番号・空の値・2 度書いた）は 2 で、出力を作らず既存の出力に触らない | CLI | `--focus` と同じ扱い |
| U5（回帰） | 画面の表が無い案件で、req-loop の手順と PPTX が今と変わらない——画面の関門は何も出さずに 0、手順の追加は画面の表があるときだけ、PPTX は `--links` を渡さない | req-loop の本文・`screen-gate.py`・`qa-to-pptx.py` | 本文の条件の書き方を読む。`screen-gate.py` の既存の試料（画面の表が無い: 何も出さずに 0）と U3 |
| U6 | req-loop の手順の順が「回答の反映 → 起票 → 検査 → モックの生成 → PPTX」に固定され、起票の候補を番号つきで起票し印に番号を添えると書く。本文が指すスクリプト・引数・出力の行頭・パスが実物と合う | req-loop の本文 | 読んで確かめる（**書かれた内容が事実と合うか**——`build-mock.py` の引数・出力先、`screen-gate.py` の出力の行頭——を実物で見る） |
| U7 | リンクの値が XML を壊さない（`&`・`<`・`"` と制御文字） | `--links` の値 | 段落の文字と関係の `Target` を逃がす。テスト |
| U8 | 版・カタログ・歯止めが全部緑 | `check-all.py` | 順番待ち越しに回す |
| X1 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目に渡す（2 パス目が「該当なし」の周は 1 パス目の 2 つ） | — | 再開点で記録 |

**証明できないもの（未証明）**: PowerPoint・LibreOffice で PPTX を開いてリンクを押すとモックのその画面が開くこと——CI と手元にアプリを動かす手段が無い（`qa-to-pptx.py` の「守らないもの」と同じ）。相対のリンクがアプリでどう解決されるかもここに入る。

**BLOCKED の候補（手順 5 で判定）**: スキル（req-loop）が本文どおりの順で動くか——モデルの振る舞いで、確かめる手段は `claude plugin eval`（このセッションからは起こせない。周の中で `claude` を起こさない）。本文が書いていることと、スクリプトが本文どおりに動くことは証明できる。

**生成物**: 無し——`SKILL.md` の測定値（設計 §8.2）は dev-loop の `SKILL.md` だけを測る。図の書き出しも無し。`skill-metrics.py --check` で変わらないことを確かめる。

## 実機確認

一時ディレクトリで、(1) 試料の Q&A 表から main の `qa-to-pptx.py` と周の `qa-to-pptx.py` で PPTX を作って `cmp`（`--focus` あり・なし）、(2) `--links` を渡した PPTX の頁と関係を `unzip` で見る、
(3) 画面の表に番号の無い `未定` を置いた正本で `screen-gate.py` を走らせて起票の候補の行を見る（陽性対照: 番号を添えた正本では出ない）、(4) その正本で `build-mock.py` を走らせて `build/mock/v1/index.html` ができ、リンクの表のとおりの `#screen=` がモックの画面ID と合うこと。

## 未解決の判断

- 上の穴 2 つ——確認の Issue で利用者に渡す（閉じるのは利用者）。

## 起票

- この周の起票: 2 件（仕様の穴 2 つ——リンクの表を誰が作るか・リンクの行き先の形——を `仕様の穴 = 推奨で決めて起票` の線で推奨により決めた確認の Issue。起票の承認は不在のため訊いていない）

## 直す線

`既定`（出所: cruise の台帳の確かめた線。不在の周）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1100-req-loop-screens-pptx`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1100`・起点 `6f815ea`・base `origin/main` → `6f815ea1312d55c28d0d74405d4971f1f9f81422`
- 割り目（手順 4）: 割らない（cruise の周）
- 交絡を潰した手順: （実機確認の後に書く）

## 既知の限界・決着済みの論点

- レビュー会の運用（会で出た指摘・見せたモックの記録・見た目の指摘・画面ごとのまとめ・回答の書き写し）は #1082 で、この周の外。
- モックの差分の印の基準の時点（`build-mock.py --since`。前回の会のコミットかタグ）を req-loop が渡すかは決めない——前回の会の時点を表から読む決まりが無い（#1082 の範囲）。
- #1098（MkDocs のフックと版ごとのモック）は利用者の判断待ちで、その中身を前提にしない。リンクは公開した URL を指さない（穴 2）。
- 「質問 → 画面」を機械で引く道（穴 1 の B・C）は置かない。
