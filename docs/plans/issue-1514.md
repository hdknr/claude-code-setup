# Issue #1514 — platform-spec: 版の差分の決まりの原本に、区切りが続くタグ名ではほかのタグを数えない 1 文を足す

**不在の周**（出所: `/dev-loop:cruise 1508 --absent` の起動・2026-11-24T02:32Z の再開）。利用者には訊かない。親（cruise #1508）から委譲文で受けた子。
Issue #1514 は #1501（PR #1511。マージ済み）のフォローアップ（`<!-- cruise-followup: #1508 -->`）で、確認の Issue #1512（利用者が「推奨のまま」で閉じた）から来ている。
本文の `作り直しの元: #1512` を PR の本文に写す。後続の #1515（`v2.0.0-beta` の後退。確認の Issue #1513）はこの周では扱わない。

確かめた線（出所: cruise の確かめた線（台帳 `issue-1508`）。利用者の確認（起動時、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
子はマージしない（親の委譲文）。台帳は書かない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1508`））。
版の上げ方: `platform-spec` を **patch**（0.2.1 → 0.2.2。原本の書き漏れの修正）。親は版を割り当てない——マージ直前に main が platform-spec を先に上げていたら、取り込んで次の patch に上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。

## 変更範囲

触る:

- `plugins/platform-spec/references/infra-profile.md` — 「版の差分と関門」の名前の形の文に 1 文を足す（決まりの原本）
- `scripts/test-check-profile-diff.py` — 原本との突き合わせに、本体の「守ること」の該当の行が原本に同じ言い方であることを足す（崩すと不一致になる陽性対照つき）。受入基準 1 を文字列の grep だけでなく回帰テストで守るため（Issue の「直すファイル」の外に広げる——手を動かす前にここに書いた）
- `plugins/platform-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1514.md` — この計画

触らない:

- `plugins/platform-spec/scripts/check-profile-diff.py`（本体。振る舞いも docstring も変えない）
- `v2.0.0-beta` の後退（#1515）
- platform-spec はスキルを持たないので `SKILL.md` の版の行は無い

依存の追加・更新: なし
仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）

同じことを述べている箇所の数: 3（本体の docstring の「守ること」の行・「守らないもの」の表の `v1.0-lts2` の行と、決まりの原本の「版の差分と関門」）。テストは検査側。
分けない理由: 原本に足すのは「守ること」の行と同じ言い方の 1 文だけで、本体の 2 箇所は変えない。

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json` の版）と GitHub Pages（`docs/` の計画ファイル）。`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`。子はマージしない。

## 受入基準

不変条件 × 破りうる経路（入口: 決まりの原本を読む人・`test-check-profile-diff.py` の原本との突き合わせ・版の検査（`check-plugin-versions.py`・`check-version-bump.py`）・CLI `check-profile-diff.py` と spec-loop の `profile-gate.py`（振る舞いを変えないことの確かめ））:

| # | 不変条件 | 経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| 1 | `references/infra-profile.md` の「版の差分と関門」に「設定のタグが自分の名前の形に当たらない（区切りが 2 文字以上続く `v1.0-lts2`）なら、ほかのタグを新しい版に数えない」があり、本体の docstring の「守ること」の行と同じ言い方である | 原本 | `grep -n 'v1.0-lts2' plugins/platform-spec/references/infra-profile.md` が当たる。テストの突き合わせが「守ること」の行の全文（`（比べずに 0）` を含む）を原本の節に求める——周の base の原本の写しで赤・今の原本で緑の陽性対照 |
| 2 | `python3 scripts/test-check-profile-diff.py` が緑（本体の定数と原本の一致も見る） | テスト | `run-serial.py` 越しに走らせる |
| 3 | #1501 の受入基準（`v1.0-lts`・`2024-10-01` でも新しい版を数える・末尾の綴りの違う版は数えない・区切りが続く版はほかを数えない など）を破らない——本体を変えない | CLI・`profile-gate.py` | `git diff <base> -- plugins/platform-spec/scripts/` が空。既存の試料が全部緑（受入基準 2 と同じ走らせ方）。`test-profile-gate.py` も緑 |
| 4 | 版が `plugin.json`・`marketplace.json` で揃って patch で上がる（platform-spec は `SKILL.md` を持たない） | 版 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| 5 | 歯止め全部（`check-all.py`）が緑 | 全体 | `run-serial.py` 越しの `check-all.py` |

必須要件の掛け算: 受入基準を両方の関門（Verifier・`/code-review`）に × 2 パス（1 パス目・2 パス目。1 パス目の指摘対応が 0 行なら 2 パス目は該当なし）= 4 つの受け渡し。2 パス目で直した行があれば狭いパスにも受入基準をまるごと渡す。

証明できないもの（未証明）: なし。
生成物: なし（原本とテストは生成物を持たない。platform-spec は `SKILL.md` を持たない）。
プロパティテスト: なし（文の有無と言い方の一致で、入力の空間を持たない）
差分テスト: なし（本体の振る舞いを変える周ではなく、本体に触れない——受入基準 3 は本体の差分が空であることで確かめる）

## 未解決の判断・確認待ち

- 仕様の穴: なし（Issue が足す文と場所を名指している）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1514-profile-diff-rule-sentence`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1514`・
  起点 `128c2749`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `128c27496b3c46918a8d7864e35f1caa37627e09`
- 割り目（手順 4）: 割らない（cruise の周）
- 陽性対照（受入基準 1）: worktree の `scripts/`・`plugins/` を `.git` なしで scratchpad に写し、原本だけ周の base（`128c2749`）のものに戻して `test-check-profile-diff.py` を走らせた——rc=1、
  「本体の『守ること』の『…（比べずに 0）』が、原本の『版の差分と関門』に同じ言い方で無い（#1514）」と「崩す箇所が 1 回でない」の 2 件。今の原本では下の歯止めのとおり。
- 歯止め（実装後）: `run-serial.py` 越しの `test-check-profile-diff.py` が `OK: 試料 26 件・変異 29 件（守ること 29 行）・references の崩し 5 件`。`run-serial.py` 越しの `check-all.py` が `22/105 本を回した（失敗 0 / 飛ばし 0）`・83 本は CACHED・rc=0
- 関門: 1 パス目に渡した（Verifier・/code-review。成果物 `287c42cf8465520f6143ff6b7def33ab5372d0fe`）。1 パス目の指摘対応の起点: `287c42cf8465520f6143ff6b7def33ab5372d0fe`
- 割り目（手順 6）: 2 パス目が該当なしなので置かない
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 反証 0 件。`test-check-profile-diff.py`・版の検査は run-serial の順番待ち（約 22 分）で走らせられず未確認と報告——同じ体に続きを頼んだ（結果は下）
- Verifier 1 パス目の続き（同じ体）: 反証 0 件。`check-plugin-versions.py` 問題なし・`check-version-bump.py origin/main` 0.2.1 -> 0.2.2 OK・run-serial 越しの `test-check-profile-diff.py` が `OK: 試料 26 件・変異 29 件（守ること 29 行）・references の崩し 5 件`・著者の陽性対照を `.git` の無い写しで独立に再現（base の原本で赤 2 件）。`test-profile-gate.py` は Verifier では走らせていない（本体の差分 0 行。著者の `check-all.py` の中では CACHED）
- /code-review 1 パス目（high）: 指摘 5 件（全部 nit。採否は下の表）。陽性対照（base の原本の写しで rc=1・今の原本で rc=0）・本体の差分 0 行・`check-plugin-versions.py` rc=0・`check-version-bump.py origin/main` OK を独立に確かめた
- 1 パス目の指摘対応: 直す 0 件。判定 `git diff 287c42cf8465520f6143ff6b7def33ab5372d0fe -- ':(top)' ':(top,exclude)docs/plans/issue-1514.md'` が空・`git status --porcelain` は計画ファイルだけ
- 2 パス目: 該当なし（1 パス目の指摘対応の差分 0 行。起点 `287c42cf`）
- 狭いパス: 該当なし
- 外部レビュー: PR の後に `external-reviews.py` で見る

```dev-loop-gates
周の base: 128c27496b3c46918a8d7864e35f1caa37627e09
関門: Verifier 1 287c42cf8465520f6143ff6b7def33ab5372d0fe 反証=0
関門: /code-review 1 287c42cf8465520f6143ff6b7def33ab5372d0fe 指摘=5
関門: 2 パス目 該当なし 287c42cf8465520f6143ff6b7def33ab5372d0fe
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- テストの突き合わせは「守ること」の該当の 1 行が原本の節に部分文字列として在ることだけを見る——原本の言い換えのほかの文（「守らないもの」の表の行）との一致は見ない（決着: 採る。理由: Issue の受入基準は「守ること」と同じ言い方）。
- `v2.0.0-beta` の後退と、「守らないもの」の表が `v2.0.0-rc1` を「自分自身とも形が合わない」に挙げる点は #1515 の範囲（決着: この周では触らない。理由: Issue #1514 の範囲の外で、後続の周がある）。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 | 振り分け |
| --- | --- | --- | --- | --- |
| CR1-1: 足した文の「（比べずに 0）」は言い過ぎ——指した ID が古い版の層に無ければ `newest()` の前に照合の違反で 1、`--new` なら別のタグを使う | 示せない（走らせていない。読解の指摘）。本体の docstring の「守ること」の行も同じ言い方で、原本の次の文「比べない（候補は 0 件）」も同じ形 | 無し——言い換えると受入基準 1（同じ言い方）と食い違う | 残課題 | 記録だけ（実際の利用でまず起きない組み合わせ・#1514 の受入基準が言い方を決めている） |
| CR1-2: テストの OK の行が「references の崩し 5 件」のまま（実際は 7 件当てる） | 示せる——出力の行 | 無し（テストは緑で、件数の表示だけ。`確かめたタグ` の崩しが数えられていないのは周の前から） | 残課題 | 記録だけ |
| CR1-3: 「守ること」の行が折り返されると、`self_shape_rule` は 1 行目だけを見る | 示せない——今の行は 1 行 | 無し | 残課題 | 記録だけ |
| CR1-4: `module.__doc__ or ""` は効かない（docstring が無いと `guarded_lines` が IndexError） | 示せない——`-OO` で読み込む経路はテストに無い | 無し | 残課題 | 記録だけ |
| CR1-5: 崩しが `（比べずに 0）` を消す 1 形だけで、節の外へ動かす崩しが無い | 示せない（今の検査は節で絞っている。/code-review が写しで確かめた） | 無し | 残課題 | 記録だけ |

- 効いた行: R-02
- 効いた行: なし
- 効いた行: なし
- 効いた行: なし
- 効いた行: R-04

- この周の起票: 0 件（不在の周で利用者に訊かない。起票は親が振り分けで決める）
