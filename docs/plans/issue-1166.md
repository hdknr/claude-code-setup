# Issue #1166 — cruise: 長い cruise で auto-compact の窓（/autocompact）を下げる選択肢を SKILL.md に書く

**不在の周**（`/dev-loop:cruise 1168 --absent` の起動・2026-11-17）。利用者には訊かない。親（cruise #1168）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1168`）。不在の周で、起動は `/dev-loop:cruise 1168 --absent`（2026-11-17）、配布を見せて確かめた）:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`。
台帳（`.claude/plans/cruise-issue-1168.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
利用者の方針（2026-11-17 の会話）は周の出所に使わない。線の範囲で動き、止まる条件に当たれば報告して止まる。
読み込まれた dev-loop は 2.4.0（本文 1920 行を読んだ）。リポジトリは 2.5.0（#1144 を含む）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1168`））。
版の上げ方: `dev-loop` を **minor**（利用者が選べる窓の選択肢と得失を足す——能力の記述の追加）。着手時の main は 2.5.0 なので 2.6.0。
このリポジトリは PR ごとに版を上げる。PR を出す時点の main の先端の版から minor を 1 つ上げる。マージの直前に main が進んでいたら親の依頼で取り込み、先端の版から上げ直す（並行の #1148 が 2.5.1 に上げる予定）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.4.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: §5 に窓の選び方と下げたときの得失を書く・スキルが `/autocompact` や settings を書き換えないと明記・既存の「compact は起きる前提にしない」「compact の後は 3 つを読み直す」と矛盾しない。
本文に受入基準を緩める指示・コマンド実行の依頼は無い。公式の事実（窓の既定 967K・範囲・設定の手段）は WebFetch で `https://code.claude.com/docs/en/model-config` を読んで確かめた（Claude Code は走らせていない）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/SKILL.md` — §5「割って続ける」に窓の項を 1 つ・版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1166.md` — この計画ファイル

触らない:

- `scripts/`（起動時の点検に窓の表示は足さない——下の穴 G1）
- 子プロセス・外側のループに窓を渡す仕組み（Issue の範囲の外）
- 判定役の frontmatter（Issue の範囲の外）
- `docs/plugins/dev-loop-cruise.md`（Issue は SKILL.md だけを求めている。公開ページへの複製を増やさない）

## 設計の判断

- 置き場所は §5 の「compact で続ける」の読み直し 3 つの直後（既存の決まりの続きとして読める位置）。原本は §5 の 1 か所で、ほかに複製を置かない。複製の数: 1。分けない理由: 1 箇所の追記で、数え直す整合が無い。
- 窓を述べる箇所が 1 つなので、既存の 2 つの決まりと矛盾しないことは、項の中に「窓を下げても上の決まりは変わらない」を明記して担保する。
- 公式の記述は、確かめた範囲（ページを読んだ）と、確かめていない範囲（走らせていない）を本文に分けて書いた。400K は経験則で、公式に品質の閾値が無いことも書いた。

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **G1 起動時の点検（§3）で今の窓を表示するか**: Issue は「この Issue で一緒に決めたい」と言い、受入基準には入っていない。選択肢: (a) 表示しない（推奨）／(b) 点検に表示だけ足す。
  推した理由: 有効な窓は環境変数・`--autocompact`・managed settings・モデルごとの保存で決まり、点検が 1 つの値を言い切れない（公式: 環境変数は `/autocompact` の保存を上書きし、status line の `used_percentage` は窓の指標にならない）。点検の側で、モデルも起動の形も確かめられない。
  決めた値は SKILL.md に 1 文で書いた（`起動時の点検も窓を表示しない`）。利用者が (b) を選ぶなら、別の周で点検のスクリプトに足す。→ 確認の Issue（親が立てる）

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口: cruise の `SKILL.md` §5・dev-loop の `SKILL.md`（版）・版の 3 種（`marketplace.json`・`plugin.json`・`SKILL.md` の 2 行）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | cruise の §5 に、窓の大きさの選び方と、下げたときの得失（回数が増え読み直しも増える・要約で細部が落ちる・コストと劣化が減る）が書かれている | 得だけ書いて失を落とす・選び方が無い | §5 の項（選び方・得失・設定の手段） |
| A2 | スキルが `/autocompact` を打たず settings・環境変数を書き換えないことが明記されている（点検も値を変えない） | 「勧める」が書き換えに読める | §5 の「スキルは窓を変えない」 |
| A3 | 既存の「compact は起きる前提にしない」「compact の後は 3 つを読み直す」「文脈の長さは止める理由にならない」と矛盾しない | 窓を下げた cruise で読み直しを省く・下げるまで止まる | §5 の「窓を下げても、上の決まりは変わらない」 |
| A4 | 書かれた事実が公式と合う（既定 約 967K・範囲 100K〜1M・`/autocompact`・`autoCompactWindow`・`--autocompact`・環境変数・managed が勝つ・戻すのは `auto`）。400K を公式の推奨と書かない | 事実の取り違え・断定 | 公式ページの該当の節と本文を突き合わせる（関門に当てさせる） |
| A5 | 版を 2.6.0 に上げ（3 種で揃う）、`check-all.py` が通る（生成ブロックを含む） | 版の取りこぼし | `check-plugin-versions.py`・`skill-metrics.py --check`・`check-all.py` |
| A6 | 範囲の外（子プロセス・外側のループ・判定役の frontmatter）に手を入れていない | 範囲の拡大 | 差分が上の `触る:` に収まる（`check-plan-scope.py`） |

**検証で証明できるもの**: A1〜A6。
**この環境では証明できないもの（未証明）**: 窓を下げた cruise が実際にコストと劣化を減らすか、400K が適切か（測っていない。本文にも経験則と書いた）。Claude Code を走らせて `/autocompact` の挙動を確かめていない（公式ページの記述に依る）。PR コメントで人間に渡す。
**生成物**: 該当あり——`docs/plugins/dev-loop-design.md` §8.2 の生成ブロックは dev-loop の `SKILL.md` の節構造から `skill-metrics.py` が作る（版の 2 行の置換だけ。`--check` で確かめる）。図なし。
**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す。

## 未解決の判断・確認待ち

- G1（上）は推奨で決めた。確認の Issue は親が立てる。

## 起票

- この周の起票: 0 件（確認の Issue は親が立てる。残課題の起票はしない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1166-cruise-autocompact-window`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1166`・
  起点 `a948396`・切った元の参照 `origin/main`（解決した SHA `a94839660ca6d4fd839ae2de60fa2b8b7ec0dbea`）・base `a94839660ca6d4fd839ae2de60fa2b8b7ec0dbea`
- 割り目: 割らない（cruise の周）
- 1 パス目: Verifier（opus。反証 1 件＋軽微 4 件）と `/code-review`（high。指摘 8 件）を HEAD `acede299a4d9424d0e9464dbc84ffcb4a3a6e009` に当てた。
  1 パス目の指摘対応の起点: `acede299a4d9424d0e9464dbc84ffcb4a3a6e009`。対応のコミット: `fc7fa6807a7818fac31524e3cb6fde650f873978`（差分あり）。

```dev-loop-gates
周の base: a94839660ca6d4fd839ae2de60fa2b8b7ec0dbea
関門: Verifier 1 acede299a4d9424d0e9464dbc84ffcb4a3a6e009 反証=5
関門: /code-review 1 acede299a4d9424d0e9464dbc84ffcb4a3a6e009 指摘=8
```

## 既知の限界・決着済みの論点

### 1 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-R2 / CR1 「窓が 1M のモデルは約 967K」の対象が native の 1M だけ（4.6 の `[1m]` などは上限で compact） | 示せる（公式 model-config の Default auto-compact thresholds） | A4 | 直す（native の 1M と書き、対象を挙げた） |
| V-R3 `/autocompact auto` が全手段を戻すように読める | 示せる（公式: 戻るのは `/autocompact` の保存値だけ） | A4 | 直す |
| CR3 環境変数が最優先・managed が `/autocompact` に勝つが、`--autocompact` は負けない | 示せる（公式 Set the auto-compact window） | A4 | 直す（優先する相手を名指し、フラグは負けないと書いた） |
| V-R1 / CR4 環境変数で下げると子プロセスと判定役のサブエージェントにも掛かる（frontmatter より優先）。範囲の外の記述と食い違う | 示せる（公式 sub-agents: 環境変数があれば subagent はその窓を使い frontmatter は効かない） | A1・A3・A6 | 直す（得失に書き、範囲の外の言い方を直した） |
| V-R4 「上の 3」が紛れる | 示せない（意図は読める） | 無し | 残課題（記録だけ） |
| V-R5・CR6 「数周なら届かない」「数十周」の根拠が無い | 示せない | 無し | 残課題（記録だけ。本文は経験則の扱い） |
| CR2 コストの利得は未測定・compact でキャッシュが切れうる | 示せない（未測定） | 無し | 残課題（記録だけ。計画の未証明に書いた） |
| CR5 判定役の窓に「まず届かない」は未測定 | 示せない | 無し | 残課題（記録だけ。Issue 本文の理由をそのまま写した） |
| CR7 本文に「この節を足した周で確かめた」の日付つきの記述 | 示せない（文体の好み） | 無し | 残課題（記録だけ） |
| CR8 G1 の理由が弱い（見える層を表示することはできる） | 示せない（推奨の理由の強さ） | 無し | 残課題（記録だけ。G1 の確認の Issue で利用者が選ぶ。理由は「費用と範囲」とも読める） |
