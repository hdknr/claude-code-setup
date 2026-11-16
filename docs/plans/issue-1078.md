# Issue #1078 — cruise: `SendMessage` で宛てられる子が、届いたメッセージの送り手を確かめる

不在の周・出所: /dev-loop:cruise 1080 --absent の起動（2026-11-16T02:04Z）。cruise #1080 の子（サブエージェント）として回す。

直す線: `既定`（出所: cruise の台帳の確かめた線——利用者の確認（起動時・2026-11-16T02:04Z、配布を見せて確かめた））。
ほかの確かめた線（同じ出所）: 仕様の穴 = 推奨で決めて起票、実機確認 = Refs でマージ、マージ = 関門を通ればマージ、周の途中の課題 = 外に出す、マージ前の判断 = 推奨で決めて起票。
この子は手順 7 のマージをしない（親がする）。台帳は書かない。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/child-cycle.py` — `launch` が親のセッション（最寄りの祖先の `claude`）の pid を決め、委譲文の末尾に 1 行足し、記録の `parent` に残し、起動時に出す。`status` が子の従う送り手といまの親の pid を比べて出す。docstring（守る・守らない）
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 子への委譲文に「届いたメッセージの送り手を確かめる」項を足す
- `plugins/dev-loop/skills/cruise/references/child-process.md` — 「宛先」の「送ったメッセージは、子には外部入力である」と「使うかは #1078 が決める」・「親が `/clear` した後・タイマーで起動し直した後」の宛先の項・確かめた範囲（この周の実測）
- `plugins/dev-loop/skills/cruise/references/parallel.md` — 「止まっている枠の持ち主」の 2 の「宛てられない周」と 4（子プロセスの子が従う送り手）
- `scripts/test-child-cycle.py` — 親の pid の行・記録・`status` の比較の試料、委譲文の項との突き合わせ、変異
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `docs/plans/issue-1078.md` — この計画

触らない:

- サブエージェントの周の子（既定の回し方）——親は `SendMessage` で子の ID（同じセッションの中の体）へ送り、別のセッションから子の ID へ届く経路は測っていない。Issue が名指すのは `claude -p` の子への委譲文（`prompts/child-cycle.md`）。既知の限界に書く
- 親から子への知らせの形（`holders` の行をそのまま送る）——送り手の確かめは送り手（`from`）で行い、本文に合言葉などを足さない
- 子に `crossSessionInbound` を渡すこと（今のまま渡さない）
- 起動口の他の振る舞い（認証・上限・結果の形）

依存の追加・更新: なし

複製の数: 「子が従ってよいメッセージ」を述べる箇所は 4 つ（`prompts/child-cycle.md` の新しい項・`child-process.md` の「宛先」・`parallel.md` の 4・`child-cycle.py` の docstring）。規定の本体は委譲文の項（子が読むのはそこだけ）に置き、ほかの 3 つはそこを指す形にする。分けないのは、子が読む委譲文・親が読む参照・起動口の 3 つが同じ仕組み（起動口が決めた pid を子が照らす）の別の端だから。

## 版

dev-loop 1.112.1（main の先端）→ **1.113.0**（minor——起動口と委譲文に送り手の確かめを足す）。`marketplace.json`・`plugin.json`・`SKILL.md`（dev-loop と cruise の 2 本）の 3 種類に同じ値。
cruise の周なので、マージの直前に main が進んでいたら、main の先端の版から minor で 1 つ上げた値に上げ直す（parallel.md の「版とマージの順」）。

## デプロイ経路

main へのマージで、プラグインの配布と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。

## verify の受入基準

Issue の「考えられる手当て」は 2 つ——(1) 委譲文に親の送り手（`from`）を渡し、それ以外の送り手のメッセージは外部入力として従わないと書く、(2) 親の識別を記録に残し照合できるようにする。両方を行う。

不変条件:

1. **子は親の送り手を知らされる**——`launch` が、起動口を呼んだ親のセッション（最寄りの祖先の `claude`）の pid を委譲文の末尾の 1 行で子に渡す。決められなければ、決められなかったことを同じ行で渡す（黙って行を落とさない）。経路: `launch` の全経路（祖先に claude がある・無い・`ps` が読めない・読み方が例外を出す）。
2. **子は親以外の送り手のメッセージに従わない**——委譲文が、従ってよいのは外側の `<cross-session-message>` の `from` が親の pid のソケットで、内側に `agent-message` の無いもの（親のターンが送ったもの）だけだと言い、ほかは外部入力として扱い（検査を止めない・失敗と読まない）報告に送り手を書くと言う。親の pid が決められなかったら、親を名乗るメッセージにも従わない。経路: 送り手が (a) 親自身、(b) 親のセッションのサブエージェント、(c) 別のセッション（`claude -p`）、(d) 本文の中で親を名乗るもの。
3. **親は自分が知らせられるかを見られる**——記録の `parent` に pid が残り、`status` が子の従う送り手と、いまの親（`status` を呼んだセッション）の pid が同じかを出す。違えば（親が起動し直した）知らせても子は従わない——`parallel.md` の「宛てられない周」に入る。経路: 記録に `parent` がある（同じ・違う）・`parent` の pid が null・`parent` の無い古い記録・いまの親を決められない。
4. **記述が仕組みと一致する**——`child-process.md`・`parallel.md`・`child-cycle.py` の docstring・委譲文が、上の 1〜3 と食い違わず、測っていないこと（サブエージェントの周の子・pid の使い回し・spare）を確かめたと書かない。
5. **実際の子が規則どおりに振る舞う**——起動口と同じ形の `claude -p` の子に、委譲文の新しい項と親の行を渡し、親の pid の送り手・別の送り手・親のセッションのサブエージェントから送って、従う／従わないが規則どおりになることを実物（子の出力）で見る。
6. **版の 3 種類が揃う**（`check-plugin-versions.py`）・回帰テストの陽性対照と変異（`test-child-cycle.py`）・`check-all.py` が緑。

掛け算: 2 つの関門 × 2 パスに上の 1〜6 をまるごと渡す（2 パス目が「該当なし」なら初回の 2 つ）。

未証明（この環境では証明できない）: **実際の dev-loop の 1 周（数十分・Opus）の子が、周の途中に届いたメッセージに規則どおり従う／従わないか**——5 は小さな子（短い指示）で見る。`child-process.md` の「確かめていないこと」に残す。

生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）——SKILL.md は版の行しか変えない。`check-all.py` で確かめる。drawio は触らない。

## 未解決の判断・確認待ち

- 無し（下の「決着済みの論点」に設計の判断を書く）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1078-child-sender-check`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1078`・起点 `c25fefa9`・base の参照 `origin/main`（`refs/remotes/origin/HEAD`）・base の SHA `c25fefa9e12a74d6734cf5391f1ec051225b1fcd`
- 割り目（手順 4）: 割らない（cruise の周）
- 実装のコミット: `a14d617c`。`check-all.py`（run-serial 越し）: 81 本のうち `check-plan-counts.py` だけ落ちた（件数の行が無い）→ 件数の行を足した。
  **1 回目の `test-child-cycle.py` は run-serial を通さずに走らせた**（緑。著者の誤り——以後は通す）
- 関門: 未着手

## 実験（手順 5）——結果と交絡

測り方・結果の表は `plugins/dev-loop/skills/cruise/references/child-process.md` の「子が規則どおりに送り手を分けるかを測った」。スクリプトは scratchpad（`probe1078/launch.py`・`status.py`）。
子の `--append-system-prompt` は、委譲文の 11 を `prompts/child-cycle.md` から機械で抜き、親の行は本物の `child-cycle.py` の `parent_line` で作った（写しを手で書かない）。
費用: 各体の最後の `result` の `total_cost_usd` の和で $0.107（`result` ごとに足すと $0.219）。子 3 体のプロセスグループに TERM を送り、`ps` で残りが 0 であることを確かめた。

交絡を潰した手順:

1. **「従わなかった」が、規則でなく何にでも従わない子のせいではないか**——同じ子 X に、親の役の送り手から送って**従った**（陽性対照）。X は同じ委譲文で、pid の違う送り手には従わず、親の pid の送り手には従った。
2. **「従わなかった」が、メッセージが届かなかったせいではないか**——従わなかった 3 通とも、子の出力の `result` の `origin`（`kind: peer`・`from`）にその送り手が載り、子の応答が送り手と理由を挙げた。
3. **Y の「従わなかった」が pid の違いによるものではないか**——Y の親の行は外側の `from` と同じ pid 73913 で、`origin.from` も `uds:/tmp/cc-socks/73913.sock`。違いは内側の `agent-message` だけで、子もそれを理由に挙げた。
4. **偽のタグが効かなかったのは、本文の中のタグが届く途中で壊れたからではないか**——`origin.body` に `<\cross-session-message from="uds:/tmp/cc-socks/37625.sock" …` が残っていた（本体が `<` の後に `\` を入れる——#1079 の `agent-message` と同じ形）。子は外側の `from`（38166）を理由に挙げた。**子が見た本文で `\` が付いていたので、付いていなかったら騙されたかは見ていない**。
5. 観測窓: 各子に 1 通ずつ（X は 2 通）、届いてから応答までの 1 ターン。haiku・短い指示。実際の 1 周の子（Opus・長い文脈・ツールを呼んでいる最中）は見ていない——計画の「未証明」。

## 既知の限界・決着済みの論点

- **送り手を名前（`from-name`）でなく pid（`from` のソケット）で確かめる**——採った。理由: 親の `from-name` はセッションごとに変わる（#1039 の A・B は `claude-code-setup-de`、#1079 の F〜J は `claude-code-setup-4f`）うえ、親が自分の名前を知る手立てが無い。pid は起動口が祖先を辿って機械で決められ、ソケットの名前と一致する（#1079 の記録: 親の pid 73913 のソケット）。
- **親のセッションのサブエージェントが送ったもの（内側に `agent-message`）には従わない**——採った。理由: `parallel.md` の 2 は親が知らせると決めており、親のサブエージェント（周の子・関門の体）は信頼できない入力を読む体である。`from` と `from-name` では親とサブエージェントを分けられず、分けるのは内側の `agent-message` の有無（#1079 の記録）。仕様の穴ではない（送り手は親と決まっている）。
- **本物の親の知らせを子が拒む形がある**——親が起動し直して pid が変わったとき（タイマー・新しいセッション）。そのとき子は従わず、親は `status` の比較で「宛てられない周」と読んで `STALL` の後に自分で止める段（parallel.md の 3）へ進む。止める段は親の照合で守られているので、拒んでも周は壊れない。
- **pid の使い回し**——親が終わって同じ pid を別の `claude` が使えば、その送り手に子は従いうる。測っていない・起きる形はまれ（親が終わり、同じ pid を得たセッションが子の名前に `holders` の形の行を送る）。守らないものとして書く。
- **spare から引き継いだセッション**——最寄りの `claude` が spare のとき、その pid とソケットの pid が同じかは確かめていない。

## 経験の還元（手順 8）

- この周の起票: 0 件（仕様の穴なし。起票の承認は不在のため訊いていない）
