# spec-loop との境目

design-system は spec-loop の決まりに従い、**spec-loop は design-system に依存しない**（#1613）。screen-spec・platform-spec と同じ形である
（screen-spec の `references/spec-loop.md`、platform-spec の `references/spec-loop.md`）。

デザインシステムのリポジトリは、**spec-loop の正本リポジトリでもある**——Q&A の起票と番号・回答の反映・承認・版は spec-loop に任せ、
design-system は表の形と検査・生成・引き渡しを持つ（`references/tree.md`・`references/outputs.md`・`references/review.md`・`references/handoff.md`）。

## 写さずに読み込むもの

決まりを写さず、spec-loop のスクリプトを読み込んで使う。原本は spec-loop の `references/` で、ここには名前だけを置く。

| 使うもの | spec-loop の原本 | 読み込むスクリプト |
| --- | --- | --- |
| Q&A 表の列と番号の形・状態 | spec-loop の `references/qa-csv.md` | spec-loop の `scripts/check-qa-csv.py` |
| 未決定の印 | spec-loop の `references/spec-exit.md` の「未決定の印」 | spec-loop の `scripts/check-spec-exit.py` の `find_markers` |
| 版の置き方・重ね方・削除・凍結 | spec-loop の `references/versions.md` | spec-loop の `scripts/merge-versions.py`・spec-loop の `scripts/check-frozen.py` |
| 版の差分 | spec-loop の `references/versions.md` の「版の差分」 | spec-loop の `scripts/diff-versions.py` |
| サインオフのタグと照合 | spec-loop の `references/signoff-tags.md` | spec-loop の `scripts/check-signoff.py`（利用者が CLI で呼ぶ） |
| 外部のリポジトリの読み出し（使う側が索引を読む形） | spec-loop の `references/external-profile.md` | spec-loop の `scripts/external-profile.py` |
| レビュー会の資料 | spec-loop の `references/tree.md` の「レビュー会の記録」 | spec-loop の `scripts/qa-to-pptx.py`（`--links`・`--groups`） |

## spec-loop のどの段を使うか

| spec-loop の段 | デザインシステムのリポジトリで | 理由 |
| --- | --- | --- |
| req-loop（Q&A 表・レビュー会・回答の反映） | **使う** | design-system の検査が出す起票の候補に番号を振り、レビュー会で回答をもらう（`references/review.md` の「1 周」） |
| 2 つのサインオフ・照合 | **使う** | 承認の運用（記事の「誰が変更を承認するか」。記事は `README.md` の「出所」）。比べる範囲に表が入る（`requirements/` の中——`references/tree.md`）。予算側のタグ（`budget-<k>`）が何に合意するか（feasibility を使わない正本で）は下の「決めていないこと」 |
| リリースのタグと凍結 | **使う** | 使う側が名指すのは `release-v<n>`（`references/outputs.md` の「使う側が読む時点」） |
| spec-review | **使わない**（design-system が自分のレビューを持つ。利用者が #1613 の D4 で選んだ「spec-review も通す」を、この形で代えた——利用者に確かめた。`references/review.md` の「判定役」） | 抜ける条件（`spec/` のチェックリスト・テストケース・形式検査）と中間表現が、デザインシステムの表に合わない。部品の状態とアクセシビリティは design-system の判定役が突く（`references/review.md` の「判定役」） |
| feasibility・proposal | 使わない（使ってもよい） | デザインシステムの成果物は提案書ではなくドキュメントのサイト（`references/outputs.md`）。ただし照合（`check-signoff.py`）は要求確定と予算の 2 つのタグを求める——予算側のタグが何に合意するかは下の「決めていないこと」 |
| scaffold | **使わない** | 引き渡しの相手は UI プロファイルのリポジトリで、design-system が自分で作る（`references/handoff.md`） |
| autopilot | 使わない | 回すのは spec-review と feasibility で、上のとおり使わない |

## Q&A の番号を振らない

design-system の検査と判定役は**起票の候補**を出すだけで、Q&A の番号を振らず、Q&A 表を書かない——番号は spec-loop の req-loop が振る
（screen-spec の `references/spec-loop.md` の「Q&A の番号を振らない」と同じ理由）。

## 対応する spec-loop の版

| 下限（この版を含む） | 上限（この版を含まない） |
| --- | --- |
| `0.138.1` | `1.0.0` |

- 下限はこの原本を書いた時点の版である。**表を行の単位で重ねる登録（下の「spec-loop に要る口」の 1）が入った版に上げる**——その前の spec-loop では、表はファイルの単位で重なる。
- 上限は spec-loop が安定版を宣言するまで（screen-spec と同じ）。
- スクリプト（子の Issue）は、検査の前に spec-loop の `.claude-plugin/plugin.json` の `version` を比べ、範囲の外なら止める（4）。

## spec-loop の見つけ方

screen-spec の `references/spec-loop.md` の「spec-loop の見つけ方」と同じ順の写しにする（design-system は screen-spec に依存しない）。環境変数の名前だけが違う。

1. 引数 `--spec-loop <spec-loop のプラグインの根>`
2. 環境変数 `DESIGN_SYSTEM_SPEC_LOOP`
3. リポジトリの形——design-system のプラグインの根の隣の `spec-loop`
4. プラグインのキャッシュの形——`installed_plugins.json` の `spec-loop@<同じマーケットプレイス>` の `installPath`

名指したものが spec-loop でなければ下へ進まずに止める——screen-spec と同じ。

## spec-loop に要る口

screen-spec を足したときも、spec-loop に中身を知らない口を足した（spec-loop の `references/tree.md` の「画面の表」・spec-loop の `scripts/screen-gate.py`（#1097）・`init-mkdocs.py --hook`（#1098））。
design-system でも次の口が要る。**どれも spec-loop の側の Issue で入れる**——この原本は形の案を置くだけで、決めるのはその Issue である。

| # | 口 | 要る理由 | 案 |
| --- | --- | --- | --- |
| 1 | **行の単位で重ねる表の登録** | 利用者と決めた（#1613 の D2）——v2 以降に変えた行だけを置き、版の差分に「どのトークン・部品が変わったか」を出す。サイトの変更の印と引き渡しの Issue がこれに乗る | `versions.md` の「行の単位で重ねる表」と `merge-versions.py` の `KINDS`・`ROW_TABLES` に、`references/tree.md` の 5 つの表を種類（`トークン`・`部品`・`部品の仕様`・`パターン`・`規則`）つきで足す。今ある種類と重ねない。`ROW_TABLES` を読むスクリプト（`diff-versions.py`・`check-signoff.py`・`build-proposal.py`・`screen-gate.py` と、screen-spec の `build-mock.py`）も見直す（`versions.md` が求める）。**`screen-gate.py`（`TABLES = tuple(versions.ROW_TABLES)`）と `build-mock.py` は一覧の表を全部画面の表として読む**ので、そのまま足すとデザインシステムの表を画面の表として扱う——画面の表の意味で読む箇所を種類で絞る。部品を消したらその部品の仕様の行も消したものとして扱うか（画面と項目の前例）を決める |
| 2 | **「見た目」の線** | spec-loop の `references/spec-scope.md` の「見た目」は、色・余白・フォントの指摘を共有の Q&A 表に起票しない。デザインシステムの表のセル（トークンの値・部品の状態）の質問がこれに当たって見送られる | 「表に列のある決定は見た目でない」と読める線にする——画面の表の項目が見た目でないのと同じ理屈（`spec-scope.md` の「見た目」は「画面の表にも仕様にも列や性質の無い描き方」と定義している）。表の名前は design-system の原本を指す |
| 3 | **関門** | req-loop とサインオフの前の確かめが、デザインシステムの表の未決定の印と design-system の検査の結果を入れる（検査を飛ばしたまま承認しない） | `screen-gate.py` と同じ形——表があれば design-system の検査を子のプロセスで呼び、見つからなければ止める。spec-loop で design-system の名前を持つのはこのスクリプトだけにする（platform-spec の `profile-gate.py` と同じ形。テストが見る） |
| 4 | **レビュー会の資料** | 質問の頁に、生成したサイトの該当の頁を載せる `qa-to-pptx.py --links`・`--groups`（JSON を外から受ける）に design-system が JSON を渡す。**ただし今の `qa-to-pptx.py` は `--links` か `--groups` を渡すと表紙に「見た目は確かめる対象ではない」（`APPEARANCE_NOTE`）を必ず出す**——デザインシステムの会では見た目が範囲の中なので逆を伝える。注記を出さない口が要り、2 の「見た目」の線と一緒に決める。`review-meeting.py groups` は画面の表の逆引きなので使わない |

## 決めていないこと

| 事項 | どこで決めるか |
| --- | --- |
| feasibility を使わない正本で、予算側のサインオフのタグ（`budget-<k>`。spec-loop の `references/signoff-tags.md` では範囲・開発費・運用費・期間の合意）が何に合意するか——照合は 2 つのタグを求める | レビューのスキルの子の Issue（承認の運用を決めるところ） |

## 依存の向き

- spec-loop の `scripts/`・`references/` は design-system の名前を持たない（上の 3 の関門だけが例外になる見込み）。
- design-system は screen-spec・platform-spec を読み込まない。screen-spec が design-system の生成物を読む向きはある（`references/outputs.md` の「使う側」）が、それも生成物を git で読むだけで、design-system のスクリプトを読み込まない。
