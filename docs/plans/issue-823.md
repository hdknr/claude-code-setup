# Issue #823 — cruise の周を閉じるたびに、その周で作った worktree とブランチを片付ける

- **不在の周**（cruise #887 の子。`/dev-loop:cruise 887 --absent` の起動・2026-11-06T01:37:35Z、利用者の確認・配布を見せて確かめた）。
  この周は利用者の指示（2026-11-06）で台帳に足した（依存なし・#884 と並行）。
  台帳の確かめた線（出所: cruise の確かめた線（台帳 `issue-887`））:
  仕様の穴 = 推奨で決めて起票、直す線 = 既定、マージ = 関門を通ればマージ、周の途中の課題 = 台帳に足して直す。
  実機確認の線は台帳に無く、`.claude/dev-loop.md` にも無い——既定（止まる）。
  割り目では訊かずに続ける（割らない（cruise の周））。マージは親がする（子は PR 側の CI まで）。
- 直す線: **既定**（出所: cruise #887 の台帳の確かめた線）
- 版の上げ方: **minor（`dev-loop`）**——cruise に新しい手順とスクリプトを足す。マージの直前に上げ直すなら、main の先端の版から minor で 1 つ上げる
  （`plugins/dev-loop/skills/cruise/references/parallel.md` の「版とマージの順」）。
- 並行する周: #884（PR #888・`.claude/worktrees/issue-884`・`issue/884-confirm-result-line`）。その worktree・ブランチには触らない。
  #884 も `plugins/dev-loop/skills/cruise/SKILL.md` と dev-loop の版を変える——取り込みで衝突しうる。

## 変更範囲

触る:
- `plugins/dev-loop/skills/cruise/scripts/cleanup-cycle.py` — 周の片付け（`cycle <PR>`）とリモートのブランチの内訳（`remotes`）（新規）
- `scripts/test-cleanup-cycle.py` — 上の回帰テスト（新規。一時のリポジトリと偽の `gh`。変異を含む）
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 4（マージの後に片付ける）・§6（残した木とリモートの内訳を渡す）・版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/check-all.py` — 新しいテストの収録
- `.github/workflows/plugins.yml` — 新しいテストのステップ
- `CLAUDE.md` — プロジェクト構成に新しいスクリプトとテストの行
- `docs/plugins/dev-loop-cruise.md` — 部品の一覧と「戻ってきたら見るもの」
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない。変わる場合だけ）
- `docs/plans/issue-823.md` — この計画

触らない:
- `merge-pr.py`（周の作業木の撤去はそのまま。ブランチを消さない決まりも変えない——片付けは別のスクリプトが持つ）
- リモートのブランチ・PR（読むだけ。`git fetch` もしない）
- 台帳の形（`ledger.py`）——残した木は既存の `note` に項として書く
- #884 の worktree・ブランチ・ファイル

## デプロイ経路

main へのマージ → GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。マージは cruise の親がする。

## 設計（この周で決めたこと）

1. **スクリプト `cleanup-cycle.py cycle <PR 番号>` を、マージを確かめた後・台帳に `merged` を書く手前で、親がメインの作業ツリーから呼ぶ。**
   PR が `MERGED` でなければ何もしない。
2. **周のものと決める式（仕様の穴——推奨で決めた。確認の Issue を立てる）**: Issue は「周で作った worktree を記録しておき」「台帳で分かるもの」と書くが、
   Verifier・`/code-review` の隔離木はハーネスが作り、子はパスを知らないことがある（`/code-review` の内部のフォーク）。そこで**台帳の `pr` の PR から決める**:
   - worktree: `<メインの作業ツリー>/.claude/worktrees/` の下にあり、ブランチが PR の head のブランチか、HEAD が PR のコミットの 1 つ。
   - ローカルブランチ: PR の head のブランチ・消した worktree のブランチと `worktree-<その worktree の名前>`・先端が PR のコミットの `worktree-agent-*`。
   - 選択肢: (A) PR から決める（推奨）／(B) 周の体が作った worktree のパスを台帳に記録する（`ledger.py` に欄を足す）。
     推した理由: (B) は隔離木のパスを子が報告できない経路で漏れ、漏れた木は残る。(A) は PR のコミットが周ごとに別なので、他の周の木を拾わない。
3. **消す条件**: worktree は `git status --porcelain --untracked-files=all` が空で、HEAD が PR のコミットか既定ブランチ（`origin/HEAD`→`origin/main`→`origin/master`）に含まれる。
   ロックは外してから `git worktree remove`（`--force` は使わない）。ブランチは先端が PR のコミットか既定ブランチに含まれるものだけ `git branch -D`。
   木を消した後・ブランチを消す前に `git worktree prune`。
4. **残したものは終了コード 4 と出力で名指しする**——親は台帳のその行の `note` に `片付けで残した: <パス>（<理由>）` の項を足し、§6 で渡す。
5. **`cleanup-cycle.py remotes`**: `origin` のリモート追跡ブランチ（最後に取った時点）を数え、`gh pr list --state all` の head のブランチで
   OPEN・MERGED・CLOSED・PR なしに分ける。§6 の終える報告に載せる。

## verify の受入基準

### 検証で証明できるもの（不変条件 × 経路）

| # | 不変条件 | 経路 | 守り方 | 確かめ方 |
| --- | --- | --- | --- | --- |
| A1 | 完了した周の木が `.claude/worktrees/` に残らない | 周の作業木（merge-pr が撤去していない）・detached の隔離木・ロックされた隔離木・ディレクトリを手で消した木（prunable）・2 周続けて | 帰属の式・unlock・prune | 一時リポジトリ＋偽の `gh` の試料（2 周を順に片付けて、両周の木が無い） |
| A2 | 未コミットの変更がある木は消さず、名指しする | 未追跡だけ・変更だけ・`status.showUntrackedFiles=no`・ロックつき | `status --porcelain --untracked-files=all` を消す前に見る・rc 4 と「未コミット」の名指し | 試料（木が残る・rc 4・出力にパス） |
| A3 | 完了した周の `issue/*`・`worktree-agent-*` が残らない | head のブランチ（squash で `--merged` に出ない）・消した木の `worktree-<名前>`・木の無い `worktree-agent-*`（先端が PR のコミット） | 候補の式・先端の条件・prune の後に消す | 試料 |
| A4 | リモートのブランチを 1 本も消さない | `cycle`・`remotes` | `push`・`fetch` を呼ばない | 試料（bare の origin の heads と、手元の `refs/remotes` が前後で同じ） |
| A5 | 他の周・他のセッションの木とブランチ、`.claude/worktrees/` の外の木を消さない | 別の PR のコミットにいる隔離木・main の先端にいる隔離木・先端が main の `worktree-agent-*`・外に置いた木 | 帰属の式・場所の条件 | 試料 |
| A6 | 消してよいかを決められないときは消さない | PR が MERGED でない・メインの作業ツリーの外から・`gh` の失敗・HEAD が PR にも main にも無い（push していないコミット） | rc 3・5・7・4 | 試料 |
| A7 | 終える報告にリモートのブランチの本数と PR の状態ごとの内訳が載る | `remotes`（1 本に複数の PR・PR の無いブランチ・既定ブランチ） | 内訳の式・§6 の手順 | 試料・§6 の文面 |
| A8 | cruise の手順がスクリプトを呼ぶ位置と、残した木の台帳・終える報告への載せ方を書いている | cruise `SKILL.md` §4 の 4・§6・公開ページ | 文面 | 読んで確かめる（関門） |
| A9 | 版 3 か所・収録・CI のステップ・CLAUDE.md の構成の行 | `check-plugin-versions.py`・`test-check-all.py` | 歯止め | `check-all.py`（順番待ち越し） |
| A10 | 必須の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | — | 委譲文 | 再開点の記録 |

### この環境では証明できないもの・BLOCKED

- **BLOCKED（実機の cruise が要る）**: Issue の受入基準 1・3 の「**2 周以上回した cruise の後**」と、受入基準 2 の「**台帳と終了時の報告に載る**」は、
  親（LLM）が §4・§6 の手順どおりにスクリプトを呼び台帳に書くことに寄りかかる。
  - **隔離木の形は測った**（2026-11-06。`/code-review` 1 パス目の指摘を受けて、このセッションで `isolation: worktree` の Agent を 1 回起動）:
    `.claude/worktrees/agent-<id>`・ブランチ `worktree-agent-<id>`・HEAD は origin/main の先端（`88e85fab`。detached ではない）。
    **何も変えずに終わった木は、ハーネスが木もブランチも消した**（終わった後の `git worktree list`・`git branch --list 'worktree-agent-<id>*'` に無い）。
    残るのは中で HEAD を動かした木で、#823 の現場（tfs-stocks）の 28 本は PR の版に detached だった——式（PR のコミット）が拾う形。
    **観測窓**: 1 体・変更なしの 1 回だけ。ロックの形（理由の文字列）と、PR の版に detached した木が残るかは、このセッションでは見ていない。
  **何が無いか: 環境**——新しい版が配られた後の実際の cruise（2 周以上）。次善として回したのは、一時リポジトリで 2 周分の試料を順に片付ける試験だけ。
  起票の代わりに、この周の元の Issue を開けたまま残すかは親が決める（`実機確認` の線は台帳に無い——既定は止まる）。
- **未証明だったが確かめた**: `gh pr view --json state,headRefName,headRefOid,commits` の形——`/code-review` 1 パス目が読むだけの `gh pr view 882` で確かめ、試料の鍵（`commits[].oid` など）と一致した。
  **未証明のまま**: `gh pr list --state all --json headRefName,state` の形（偽の `gh` のみ）・`commits` の上限（gh 2.92.0 のクエリは `commits(first: 100)`。ページングは見ていない）。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）——cruise の `SKILL.md` を測るかで該当が決まる。`--check` で確かめる。
- 図: 触らない（該当なし）。

## 未解決の判断・確認待ち

- 設計 2 の帰属の式（仕様の穴）——確認の Issue を立てる（番号は下の再開点）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/823-cleanup-cycle-worktrees`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-823`・
  起点 `88e85fab`・base `88e85fab0d5615e79da5e4a43b8a3157079c4737`（参照 `origin/main`）
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目を通した——Verifier 反証 2 件・`/code-review` 指摘 10 件。1 パス目の指摘対応の起点 `f74fc4e16f4161624a3b852f4fdaad9055de0626`。
  指摘対応で直した（下の採否の表の「直す」）。2 パス目: まだ（指摘対応の差分があるので回す）。割り目（手順 6）: 割らない（cruise の周）
- 反証と差し戻し: Verifier 2 件（R1・R2）→ 手順 4 へ差し戻して直した
- 交絡: テストの観測の側（`state_of`）も `refname:short` でブランチを読んでおり、変異「refname:short で読む」が同じ読み違いで緑になった——観測を `lstrip=2` に直して赤を確かめた（CR5 の直しの中）。隔離木の形の測定（1 回）——陽性側の対照は、同じ観測点（`git worktree list`）で周の作業木 issue-823 が見えていること。観測窓は上の BLOCKED の項

## 既知の限界・決着済みの論点

### 1 パス目の採否の表（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1（Verifier）fork の PR の head が `main` で、メインの作業ツリーが `main` を開いていないと、手元の `main` を消す | 示せる（Verifier の試料で `消した: ブランチ main`） | A5 | 直す——既定ブランチとメインの作業ツリーのブランチを候補から外す（試料・変異を足した） |
| R2（Verifier）＝ CR1（/code-review）ロックされた木のディレクトリが手で消えていると、記録が残るのに「片付けた」rc 0 | 示せる（両者の試料） | A1・A6 | 直す——prune の前に unlock し、prune の後に記録が残れば「残した」（試料・変異） |
| CR2 積んだ周（PR の head から切った別のブランチ）の木とブランチを消す | 示せる（EXP2） | A5 | 直す——HEAD で帰属を決めるのは detached か `worktree-<木の名前>` の木だけ（試料・変異）。設計 2 の式の言い直しで、PR のコミットから決める選択は変えない |
| CR3 rc 7 の経路で「残した」を出さない | 示せない（読んだだけ） | — | 直した（CR8 の文面と組。7 でも「残した:」を出す 2 行。変異は足していない） |
| CR4 unlock の後 remove が失敗すると、ロックを戻さない | 示せる（submodule の木） | 無し | 残課題 |
| CR5 同じ名前のタグがあるとブランチが黙って残る（`refname:short`） | 示せる（EXP4） | A3 | 直す——`refname:lstrip`（試料・変異） |
| CR6 変異「リモートのブランチを消す」が A4 の検査を判別していない | 示せる（3 つの理由で赤） | A4（の証明） | 直す——`branch -D` に `push --delete` を足す変異にした |
| CR7 未証明・BLOCKED の分類が甘い | 示せる（`gh pr view 882`・隔離木は測れた） | — | 直す——gh の形は確かめた側へ移し、隔離木の形を測って BLOCKED を親の振る舞いだけに絞った（上） |
| CR8 cruise SKILL の「3・5・7 は何も消していない」が 7 と矛盾 | 示せる（文面） | A8 | 直す——3・5 と 7 を分けた |
| CR9 docstring の「250 件」は確かめていない | 示せる（gh 2.92.0 のクエリは first: 100） | A8（文面の事実） | 直す——「gh が返す範囲まで（上限は確かめていない）」 |
| CR10 merge-pr.py・ledger.py の再実装 | 示せない（整理） | 無し | 残課題 |
| Verifier の補足: §4 の 4 で片付けの段落が「マージの直前」の段落より前にあり、時系列が逆に読める | 示せない（読みやすさ） | 無し | 残課題 |
| CR の記録だけ: `git worktree prune` はディレクトリの消えた他の周の木の記録も消す | 示せない | 無し | 残課題（データは失わない） |

- 設計 2（PR のコミットから決める）は確認の Issue #891 のまま。CR2 の直しは式を狭める言い直し（#891 にコメントで書く）。

- この周の起票: 1 件（#891——仕様の穴を推奨で決めた確認の Issue）
