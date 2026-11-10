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
- 実装: 未
- 関門: 未
- 交絡を潰した手順: 実験なし（所要時間は `gh run view` の値を読んで並べるだけ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| ジョブ id `spec-loop-generate` を中身に合わせて改名するか | 採らない | ジョブの振り分けが変わる。この周はコメントの直しに留める（委譲文） |
| `CLAUDE.md`・`check-all.py` の「1 本だけ重い」も直すか | 採らない | 歯止めの中での比較（手元・直列 166 秒）で、CI のジョブの中での比較とは別の主張 |
| CI の所要時間を 1 つの run の値で書くか | 採らない | ランナーの混み具合で揺れる（5 分 44 秒〜6 分 56 秒）。範囲と run を書く |
