# Issue #933 — plugins.yml のジョブのコメント・#929 の計画の数え・CLAUDE.md の所要時間を実測に合わせる

不在の周（cruise の子）。出所: `/dev-loop:cruise 934 --absent` の起動（2026-11-10T02:38Z）。親 Issue #934・台帳 `issue-934`（台帳は親だけが書く）。
従う版は dev-loop 1.103.0（キャッシュ `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/dev-loop/SKILL.md`）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-934`。利用者の確認・起動時 2026-11-10T02:38:35Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票。実機確認は線が無い（止まる）
- 直す線: **既定**（出所: 上の cruise の確かめた線）
- 版の上げ方: **上げない**——`plugins/` を触らない（`check-version-bump.py` の対象外）
- PR は `Fixes #933`。手順 7 のマージは親がする（子は PR と PR 側の CI まで）
- 備考（委譲文）: #931（ジョブ単位の `if`・`needs` の歯止め）が後で同じ `plugins.yml` を触る。この周はコメント・記述の直しに留め、歯止めは足さない

## 周の在り処

- ブランチ: `issue/933-ci-job-comments-match`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-933`
- 起点コミット: `5bd739f`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `5bd739f6a3db4071a849782d14dbab3f0d8ea175`

## 変更範囲

触る:
- `.github/workflows/plugins.yml` — ジョブの見出しコメントと `check-mutation-claims.py` のステップの上のコメントだけ（ステップ・ジョブ名・`if`・`run` は変えない）
- `docs/plans/issue-929.md` — 「複製の数: 1 箇所」の行だけ
- `CLAUDE.md` — 「CI の 1 往復（約 13 分）」の所要時間だけ
- `docs/plans/issue-933.md` — この計画

触らない:
- ジョブの id（`spec-loop-generate` など）——名前を変えるとジョブの振り分けそのものが変わり、#931 が触る範囲と重なる。中身はコメントで言う
- `CLAUDE.md` の `check-mutation-claims.py` の説明の「1 本だけ重い」と `scripts/check-all.py` の `GUARDS` のコメント——歯止め（`check-*.py`）の中での比較で、手元の直列 166 秒（#430）に基づく。
  CI のステップの上のコメントは CI のジョブの中での比較（テストを含む）なので別の主張
- `docs/plans/issue-929.md` の重さの見積りの表——見積りの記録で、実測は同じ計画の再開点に既にある
- 歯止めの追加（#931 の範囲）・`concurrency`（#932 の範囲）

複製の数（同じことを述べている箇所）:
- ジョブへの振り分けの中身: `plugins.yml` のジョブの見出しコメント 7 つ＋`docs/plans/issue-929.md` の表（過去の見積りの記録で、直さない）の 8 箇所（冒頭のコメントは分け方の方針だけを述べる）。直すのは見出しコメントのうち中身と合わない 4 つ（`check`・`dev-loop`・`spec-loop`・`spec-loop-generate`）。
  分けない理由: 各ジョブのコメントはそのジョブのステップの隣にしか置けない（ステップを足す人がそこを見る）
- 重さの注記: `check-mutation-claims.py` のステップの上の「1 本だけ重い」＋ジョブの見出しの「（1 本で重い）」2 つ
- CI の 1 往復の所要時間: `CLAUDE.md` の 1 箇所（`grep "13 分"` でほかは過去の計画の記録だけ）

## 実測（`gh run view` で読んだ値）

- 分割前の run 42612174778（job `check` 1 本・31 分 45 秒）: `散文の変異主張を当てる（#151）` 25 秒。ステップの上位は `test-autopilot-loop` 350・`test-run-serial` 333・`test-outer-loop` 198・`test-parallel-stop` 131・`test-scaffold` 120 秒
- 分割後の `check` ジョブ（run 42732175841・42736693734・42742968130・42743663412）: `散文の変異主張を当てる（#151）` 24・32・19・20 秒。同じジョブの `check-mutation-claims.py のテスト` は 54・56・50・52 秒
- 分割後の plugins.yml の run（最初のジョブの開始 → 最後のジョブの終了）: 42732175841 6 分 56 秒・42736693734 5 分 44 秒・42742968130 5 分 44 秒・42743663412（main への push）5 分 45 秒

## デプロイ経路

`CI 定義` と `CLAUDE.md`・計画——main へのマージでプラグインのカタログには何も配布しない（`plugins/` を触らない）。`docs/plans/` は mkdocs の `docs/` の下なのでサイトの再ビルドに乗る。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **各ジョブの見出しコメントが、そのジョブのステップの中身を覆い、他のジョブと入れ替わっていない。**
   経路: 7 つのジョブの見出しコメント（`check`・`dev-loop`・`cruise-run-serial`・`cruise-loops`・`spec-loop`・`spec-loop-generate`・`spec-loop-autopilot-loop`）と冒頭のコメント。
   守り方: 各ジョブのステップの `name`・`run` を読み、コメントの語がどのステップを指すかを 1 つずつ当てる。
2. **重さを言うコメントが実測と合う。** 経路: `check-mutation-claims.py` のステップの上のコメント・ジョブの見出しの「（1 本で重い）」2 つ・冒頭の「約 32 分」。
   守り方: 上の「実測」の run の値と突き合わせる。
3. **CI の挙動を変えない。** 経路: ジョブ id・`runs-on`・`steps` の `name`・`if`・`run`・`with` のどれかが変わる、YAML として読めなくなる。
   守り方: コメント行（`#` で始まる行）を除いた行が base と一致することを機械で比べる。PR 側の CI で 7 ジョブが走って緑。
4. **`docs/plans/issue-929.md` の複製の数が、振り分けを述べている箇所の実数を書いている**（ジョブごとのコメント 7 つ・計画の表の 8 箇所）。
   経路: その行だけ。件数の行（`- この周の起票: 3 件`）は変えない（`check-plan-counts.py` が緑）。
5. **`CLAUDE.md` の「CI の 1 往復」の所要時間が、#929 の後の run の実測と合い、run を名指しする。** 経路: `CLAUDE.md` の該当行と、同じ数を述べる他の箇所（`grep` で無いことを確かめた）。
6. `python3 scripts/check-all.py` が緑（run-serial 越し）で、PR 側の CI も全部緑。

検証で証明できるもの: 1〜6 すべて。
未証明: なし。
生成物: なし（`plugins.yml`・`CLAUDE.md`・計画は手で書く。`skill-metrics.py` の生成ブロックは `SKILL.md` から作るので触らない。図の書き出しも触らない）。

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パス（1 パス目の指摘対応の差分が 0 行なら 2 パス目は該当なし）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 手順 4 の割り目: 割らない（cruise の周）
- 実装: 済み・コミット済み（`5b8187a`）。`plugins.yml` のコメント行を除いた行が base と一致（`diff` で確かめた）
- 関門: 1 パス目を通した（Verifier → `/code-review`。2026-11-10）。1 パス目の指摘対応の起点: `5b8187a`（Verifier に渡した時点の HEAD。成果物はコミット済み）
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet。meta.json で確かめた）1 パス目: **反証 1 件**（V1 件数の行が無い）。不変条件 1〜5 は `gh run view` と diff で一致、6 は未確認（check-all を回していない）
    ——報告の通知は届かず、サブエージェントのトランスクリプトの `SubagentHandback` の入力から読んだ
  - `/code-review`（high）1 パス目: **指摘 9 件**（下の採否の表）。報告の通知は届かず、トランスクリプトの最後の応答から読んだ
  - 著者の `check-all.py`（run-serial 越し。約 60 分待って枠を取った）: 69 本中 68 OK・`check-plan-counts.py` だけ FAIL（V1 と同じ）。件数の行を足したあと `check-plan-counts.py` 単独で緑
  - 差し戻し: なし（1 パス目の指摘対応は手順 6 の指摘対応として行う）
  - 指摘対応: 「直す」の 5 行（V1/CR1・CR3・CR4・CR7・CR8）を直した。成果物の差分は 0 行ではない → 2 パス目を回す
  - 手順 6 の割り目: 割らない（cruise の周）
  - PR: #938（`899d0c0` を push）
  - 2 パス目: 通した（base は同じ `5bd739f`）。2 パス目の指摘対応の起点（狭いパスの起点）: `899d0c0`
    - Verifier（`dev-loop:dev-loop-verifier`・sonnet。meta.json で確かめた）2 パス目: **反証 0 件**。不変条件 1〜5 一致、6 は PR の CI が走っている途中で未確認。
      `skill-metrics.py --check`・`check-diagram-freshness.py`・`check-duplicate-counts.py`・`check-plan-counts.py` は緑（Verifier が走らせた）。報告はトランスクリプトの `SubagentHandback` から読んだ
    - `/code-review`（high）2 パス目: **指摘 7 件・正しさのバグ 0 件**（下の採否の表）。報告はトランスクリプトの最後の応答から読んだ
    - PR #938 の CI（run 42755677055・HEAD `899d0c0`）: 7 ジョブと docs.yml の build が緑
  - 2 パス目の指摘対応: 「直す」の 1 行（P2-5）を直した。狭いパスの起点 `899d0c0`・終点 `4b28521`（`git diff 899d0c0 4b28521`）
  - 狭いパス: 通した。Verifier（`dev-loop:dev-loop-verifier`・sonnet）**反証 0 件**。変異は当てていない（変更がコメント 1 行で、機械が読む対象が無い——Verifier の判断）ので、素通りした変異も無い。
    `skill-metrics.py --check`・`check-diagram-freshness.py`・`check-duplicate-counts.py`・`check-plan-counts.py`・`check-plugin-versions.py` は緑（Verifier が走らせた）。狭いパスの指摘: 0 件
  - 著者の `check-all.py`（2 回目。run-serial 越し、342 秒待って枠を取った）: **69/69 緑**。枠を取った時点の木は `899d0c0`＋計画の未コミットの追記で、走っている途中に P2-5 の 1 行（コメント）を直した——
    その 1 行を含む先端は PR 側の CI で見る
- 交絡を潰した手順: 実験なし（所要時間は `gh run view` の値を読んで並べるだけ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| ジョブ id `spec-loop-generate` を中身に合わせて改名するか | 採らない | ジョブの振り分けが変わる。この周はコメントの直しに留める（委譲文） |
| `CLAUDE.md`・`check-all.py` の「1 本だけ重い」も直すか | 採らない | 歯止めの中での比較（手元・直列 166 秒）で、CI のジョブの中での比較とは別の主張 |
| CI の所要時間を 1 つの run の値で書くか | 採らない | ランナーの混み具合で揺れる（5 分 44 秒〜6 分 56 秒）。範囲と run を書く |

### 1 パス目の指摘の採否（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1・CR1 | 計画ファイルに件数の行（`- この周の起票: N 件`）が無く `check-plan-counts.py` が落ちる | 示せる（`check-all.py` の FAIL・`check-plan-counts.py` の ERROR） | 6 | 直す（件数の行を足した。`check-plan-counts.py` 緑） |
| CR2 | 受入基準 4 の「`check-plan-counts.py` が緑」が #929 の件数の行を指し、この計画の行を見ていない | 示せない（受入基準 4 は #929 の件数の行を変えないことを言っており、この計画の行は 6 が見る） | 無し | 残課題 |
| CR3 | `dev-loop` の見出しが `test-fence-copies` を cruise の道具に入れているが、写しの 1 つは dev-loop の `check-unattended-env.py` | 示せる（`test-fence-copies.py` の docstring・`plugins.yml` 135 行） | 1 | 直す（写し 3 つの持ち主を名指しした） |
| CR4 | `spec-loop` の見出しが casefold を「版の重ね合わせと差分」に付けているが、casefold で回るのは版の重ね合わせと MkDocs のフック | 示せる（casefold のステップの `run:`） | 1 | 直す（casefold のステップを別に名指しした） |
| CR5 | 「約 6 分」は待ちの無い run の値で、並行の cruise で run が重なると待ちが入る | 示せない（4 つの run はどれも待ちが無く、待ちの入った run は手元に無い） | 無し（5 は実測と合う） | 残課題 |
| CR6 | 受入基準 3 の確かめ方（`#` の行を除いて比べる）は `run: \|` の中の `#` の行の変更を見落とす | 示せない（この差分の塊は 16・121・133・204・281 行で、`run: \|` の中に無い。`git diff -U0` で確かめた） | 無し | 捨てる（この差分では成り立たない） |
| CR7 | `docs/plans/issue-929.md` の「この計画の下の表の 8 箇所」が「表に 8 箇所」と読める | 示せる（その行の文） | 4 | 直す（「表 1 つの、計 8 箇所」） |
| CR8 | `spec-loop-generate` の見出しが `test-check-spec-exit` を「表の検査」に入れているが、仕様のディレクトリの未決定の印も走査する抜ける条件の判定 | 示せる（CLAUDE.md の `check-spec-exit.py` の説明） | 1 | 直す（「仕様レビューを抜ける条件の判定」として分けた） |
| CR9 | dev-loop のテストが `check` と `dev-loop` の 2 つの見出しに分かれ、互いを指していない | 示せない（どちらの見出しも自分のステップを正しく述べている） | 無し | 残課題 |

### 2 パス目の指摘の採否（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| P2-1 | `CLAUDE.md` の「CI の 1 往復（約 6 分）を省く速さだけで」は、数を変えたのに論証を当て直していない | 示せない（CI が短くなったので、ローカルの `check-all.py` が省く時間はさらに小さく、文の結論「順番待ちの損のほうが大きい」は弱まらない） | 無し（5 は実測と合う） | 残課題 |
| P2-2 | `docs/plans/issue-929.md` の表の `spec-loop-generate` の行が `test-check-spec-exit` を「表の検査」に入れたまま（CR8 で見出しだけ直した）。計画の「過去の見積りの記録」という理由は秒数の列にしか当たらない | 示せる（`issue-929.md` 39 行） | 無し（4 は数えの行だけ） | 残課題 |
| P2-3 | `cruise-loops` も重いのに「（1 本で重い）」が付いていない | 示せない（「1 本で重い」は重い 1 本だけのジョブの印で、`cruise-loops` は 2 本。付いている 2 つは実測と合う） | 無し | 残課題 |
| P2-4 | `spec-loop-generate` の「（ジョブの名前より広い）」は片側だけで、生成のテストは `spec-loop` にもある | 示せない（`spec-loop` の見出しが自分の生成のテストを名指ししている） | 無し | 残課題 |
| P2-5 | `dev-loop` の見出しの「コードブロックの読み方の写し」がステップ名（「コードブロックとコメントの読み方の写し」）より狭い（CR3 の直しで入れた文） | 示せる（`plugins.yml` 136 行と 170 行のステップ名） | 1 | 直す（「コードブロックとコメントの読み方の写し」） |
| P2-6 | `check` の見出しが `test-check-mutation-claims.py`（ジョブで最も重い 50〜56 秒）を名指ししない | 示せない（「歯止めとそのテスト」が覆っている） | 無し | 残課題 |
| P2-7 | `dev-loop` の見出しの「worktree」が `check-pr-preconditions.sh` のテストを言わない | 示せない（ステップ名「worktree スクリプトのテスト」と同じ語で、2 本とも worktree スクリプト） | 無し | 残課題 |

### 振り分け（`references/found-lines.md`。手順 8）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| CR2 受入基準 4 の「`check-plan-counts.py` が緑」の指し先 | #933 `/code-review` 1 パス目 | 示せない | 記録だけ（計画の文言） |
| CR5 「約 6 分」は待ちの無い run の値 | #933 `/code-review` 1 パス目 | 示せない | 記録だけ（性能の推測） |
| CR6 `#` の行を除く比較は `run: \|` の中を見落とす | #933 `/code-review` 1 パス目 | 示せない（この差分では成り立たない） | 捨てる |
| CR9 dev-loop のテストが 2 つの見出しに分かれる | #933 `/code-review` 1 パス目 | 示せない | 記録だけ（文言） |
| P2-1 `CLAUDE.md` の論証を当て直していない | #933 `/code-review` 2 パス目 | 示せない（結論は弱まらない） | 記録だけ（文言） |
| P2-2 `issue-929.md` の表の `spec-exit` の分類 | #933 `/code-review` 2 パス目 | 示せる（39 行） | 記録だけ（過去の計画の表の文言。スキル・スクリプトの利用者が受け取る結果ではない） |
| P2-3 `cruise-loops` に重さの印が無い | #933 `/code-review` 2 パス目 | 示せない | 記録だけ（文言） |
| P2-4 「ジョブの名前より広い」が片側だけ | #933 `/code-review` 2 パス目 | 示せない | 記録だけ（文言） |
| P2-6 `check` の見出しが `test-check-mutation-claims` を名指ししない | #933 `/code-review` 2 パス目 | 示せない | 記録だけ（文言） |
| P2-7 `dev-loop` の見出しの「worktree」が PR 前提条件を言わない | #933 `/code-review` 2 パス目 | 示せない | 記録だけ（文言） |

直すの行: 0 件（台帳に足す行・`要確認` の Issue は無い）。狭いパスの指摘: 0 件。マージ前に人が判断するもの: 無し。

- この周の起票: 0 件（起票の承認は不在のため訊いていない。仕様の穴の確認の Issue・台帳に足した Issue も無い）
