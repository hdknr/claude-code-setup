# Issue #633 — cruise: 周の子を背景で起動すると、claude -p ではターン終了後 10 分で子が打ち切られる

spin-dd/tfs-stocks#2427（dev-loop 1.63.6・2026-10-29）で、外側のループが `claude -p "/dev-loop:cruise 2427 --absent"` を起動し直していた。
親は周の子を背景で起こし「待ちます」と書いてターンを閉じ、`-p` はターンの後に背景のタスクを 10 分だけ待って止めた
（`Background tasks still running 10m after the last turn (…); stopping them. Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to wait indefinitely.`）。
cruise `SKILL.md` §4 の 2 は周をサブエージェントに回させるとだけ書き、前景で呼ぶかを決めていない。

**不在の周**である——出所は `/dev-loop:cruise 793 --absent` の起動（2026-11-03）。親からサブエージェントとして委ねられた。
台帳 `issue-793` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: 利用者の確認（起動時・親 Issue #793 の cruise: の行・2026-11-03T03:56:17Z、配布を見せて確かめた））。台帳は書かない（親が書く）。マージしない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（手順の追加）。main の先端 1.75.3 → **1.76.0**（マージの直前に main が進んでいたら、親が子に取り込みと上げ直しを回す）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる:
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 2 に「周の子は前景で呼ぶ」を足す・版の 2 行
- `docs/plugins/dev-loop-cruise.md` — §5 に `claude -p` で外から回すときの節（上限 0・タイマー・`ledger.py status` で回す外側のループの例）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-633.md` — この計画ファイル

触らない:

- `references/child-process.md`・`scripts/child-cycle.py`（子プロセスの周は切り離したプロセスで、背景のタスクではない。上限 0 はもう置いている）
- `prompts/*.md`（子の側に背景のジョブを残させない規則は #168 で在る）
- `launch-with-long-token.sh`（`-p` を渡す形は確かめていないので、例に使わない）
- dev-loop `SKILL.md` の「並列化の指針」（dev-loop の周の中の体の話で、cruise の親が周の子を起こす話ではない）

### 同じことを述べている箇所の数

「周の子をどう起こすか」を述べるのは 2 箇所——cruise `SKILL.md` §4 の 2（規範の原本）と公開ページ §5（利用者向け。`-p` で回すときの設定）。
公開ページは規範を写さず、利用者がする設定（環境変数・外側のループ）だけを持ち、規範は `SKILL.md` を指す。`SKILL.md` は公開ページの節をアンカー付きのリンクで指す
（`check-site-links.py` で見られる）。分けない理由: 親の規範と利用者の設定は読み手が違う。

## 乗るデプロイ経路

main へのマージでプラグインの配布（dev-loop 1.76.0）と公開サイト（`docs/plugins/dev-loop-cruise.md`。main への push で GitHub Pages）。マージは親がする。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | cruise の親が周の子を起こすどの入口でも、既定は前景（同期）で呼ぶと `SKILL.md` に書いてある | §4 の 2 の新しい周・台帳から再開した周の続き・§4 の 5 の操作待ちの続き・§4 の 4 のマージの直前の取り込みと上げ直し（`parallel.md`）・まとめの周（`grouping.md`）・積んだ周の載せ替え | 読んで、規則がそれら全部に掛かる書き方か（§4 の 2 の「子に回させる」すべて）を突き合わせる |
| A2 | 背景で起こしてよい場合（並行に始めてよい周が 2 本以上）と、そのときの決まり（全部の報告を受け取るまで台帳を進めない・`-p` なら上限 0 が要る）が書いてある | 例外の条件が広すぎる・`-p` の注意が抜ける | 読む |
| A3 | `-p` の振る舞いについての記述が事実と合う——既定の上限 10 分と環境変数の名前は観測した標準エラーに拠り、**0 で止めずに待つことは測っていない**と書く（測ったとは書かない） | `SKILL.md`・公開ページの文・`child-process.md` との食い違い | #633 の本文の標準エラー・`child-process.md`「実際の 1 周で観測したこと」と突き合わせる |
| A4 | 公開ページの外側のループの例が、`ledger.py status` の終了コード（0: 進められる・3: 人待ち・4: 判定できない・5: 済んだ）どおりに続け・止まる | 例の `case` の分け方・`ledger.py` の docstring との食い違い・回し続ける形 | 一時のリポジトリに本物の `ledger.py` で台帳を作り、偽の `claude` を `PATH` の先頭に置いて例をそのまま走らせる（todo が残る→上限まで回る／全部 merged→1 回で止まる（5）／台帳が無い→止まる（4）／人待ちだけ→止まる（3）） |
| A5 | 子プロセスの周（`child-cycle.py`）をこの規則の対象に誤って含めない | §4 の 2 の任意の項 | 読む |
| A6 | 指し先が実在する（`SKILL.md` から公開ページのアンカー） | リンク・アンカー | `check-site-links.py`・`check-skill-pointers.py` |
| A7 | 版を 3 箇所で上げる | `marketplace.json`・`plugin.json`・両 `SKILL.md` の 2 行 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A8 | 既存の歯止めを割らない | 太字の flanking・件数の重複・規範マーカー | `check-all.py`（順番待ち越し）が緑・PR の CI が緑 |

**この環境では証明できないもの（未証明）**: なし——`-p` で上限 0 の親が背景の子を最後まで待つかは受入基準にしていない（A3 のとおり「測っていない」と書く。
本物の `claude -p` を起こす測定は費用がかかり、利用者は #491 の測り直しを次に子で回す周のついでにすると決めている——`child-process.md`）。
**落とした主張**: 「上限 0 なら背景の子を最後まで待つ」——測っていないので主張しない（PR コメントに名指しで残す）。

**生成物**: `skill-metrics.py` の生成ブロック（設計 §8.2）は dev-loop の `SKILL.md` の節構造に依る——版の行だけを変えるので `check-all.py` の `--check` で鮮度を見る。図の書き出しは無し。

必須要件の掛け算: 受入基準を Verifier・`/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/633-cruise-foreground-child`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-633`・
  起点 `896667d2`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `896667d2ba7d28a8e417e185e75e9479bfc25918`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 関門: 1 パス目（Verifier・`/code-review`）を起動。1 パス目の指摘対応の起点 `2b16c637`（関門に渡す時点の HEAD）
- 交絡を潰した手順: A4 は公開ページのコードブロックを文字列のまま抜き出して走らせた（写しではない）。陽性対照は S1（todo が残る→0 が続き、上限 20 回まで回る）、陰性は S2〜S4（5・4・3 で 1 回で止まる）。偽の `claude` が受けた `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` は 0 だった。台帳は本物の `ledger.py` で作った。観測窓: 4 つの台帳の状態だけ（`pr`・`blocked`・判断待ちの印は回していない——`status` の判定そのものは `test-ledger.py` が見る）

## 既知の限界・決着済みの論点

- 子プロセスの周（`child-cycle.py`）は対象外——切り離したプロセスで、親の背景のタスクではない。上限 0 は起動口が子の環境に置いている（#491）。
- 複数の `Agent` を 1 つのメッセージで前景に並べると並行に走るかは確かめていない——dev-loop `SKILL.md` は「同期で呼ぶと 1 体ずつ順番」と書いているので、並行は背景で起こす形のままにする。
