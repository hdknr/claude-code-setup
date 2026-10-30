# Issue #646 — dev-loop SKILL.md と cruise §6: 確認の Issue の書き方への指し先と、親が立てた確認の Issue の取りこぼし

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-10-30）の周（親から受けた）。#646 は #557（PR #642）の周の途中の課題を、
  同じファイルごとに 1 件のチェックリストにまとめたもの（`<!-- cruise-found: #474 -->`）。
  **不在の周**である——訊く場面は `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める（`AskUserQuestion` は使わない）。
- 使った線（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋
  （再開時・2026-10-28T23:56:17Z、配布を見せて確かめた）。親から受けた）:
  `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`。
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-474`））。
- **利用者の直接の指示（2026-10-29、親から受けた）**: 人間の判断が要る行（狭いパスの指摘を含む）は推奨で決め、要確認の Issue（ラベル `要確認`、#557 の形）を立てる——この周が自分で立てる。
- 2 つの行の決定の出所: N2 は要確認 #645（**利用者 hdknr が「承認」とコメントして閉じた**）、CR1-3 は要確認 #647（同じく「承認」。推奨＝**両方やる**——親が `decisions` に足す決まり＋終えるときに `要確認` ラベルでも探して突き合わせる）。
- 親の指示（この周に固有）: `EnterWorktree` を呼ばず、worktree の絶対パスを cwd にして作業する。**マージしない**——PR・PR 側の CI・
  2 つの関門の 2 パスと狭いパス・手順 8 の計画ファイルまで。台帳は書かない（周の途中の課題は親に報告する）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 6 の「新しい Issue を起票するのは」の括弧に、確認の Issue の書き方を指す 1 文（N2）。「待ち時間・定時処理は別スキル」の `absent-lines.md` の「読まなくてよい」に、確認の Issue を立てる周の例外を足す（指す先と食い違わないため）。版の 2 行
- `plugins/dev-loop/skills/cruise/SKILL.md` — §6（終える）: 親が立てた確認の Issue を台帳の `decisions` に足す決まりと、終えるときに `要確認` ラベルの開いた Issue を探して `decisions` と突き合わせる手順（CR1-3）。版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — dev-loop の版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない）
- `docs/plans/issue-646.md` — この計画ファイル

触らない:

- `references/absent-lines.md` の「確認の Issue の書き方」の中身——#557 で決めた。指す側だけ足す
- `scripts/ledger.py` の `decisions` の扱い（鍵・検査）——行ごとの番号の一覧のまま。親の決まりは散文で足す
- cruise `SKILL.md` §1・§2（並行する #665 のまとめの周が触る）
- `docs/plugins/dev-loop-cruise.md`——「台帳の列に番号が載り、終えるときに開いているものが一覧で渡されます」は変更後も真（ラベルの検索は拾う側を増やすだけ）

## 乗るデプロイ経路

プラグイン（dev-loop）の中身の変更——マージで配布が起きる（`マージの反映: ドキュメントとプラグインの配布`）。マージは親がする。

## 周の大きさ（同じことを述べている箇所の数）

- 「確認の Issue を立てるなら書き方を読む」を述べる箇所: `absent-lines.md` の冒頭（原本）・cruise §6（親が立てるとき）・dev-loop `SKILL.md` 手順 6（今回）・
  dev-loop `SKILL.md` の「待ち時間」の項（今回、例外として指すだけ）の **4 箇所**。分けない理由: 指し先は入口ごとに要る（入口が無いのが N2 そのもの）。
  中身の列挙は原本だけに置き、他は指すだけにする。
- 「終えるときに開いた確認の Issue を集める」を述べる箇所: cruise §6（原本）・`absent-lines.md` の「仕様の穴」の手順 3（`decisions` に足す・§6 で集める）・
  公開ページ（利用者向け）の **3 箇所**。集め方の手順は §6 だけに置く。

## 受入基準（不変条件 × 経路）

不変条件:

- **I1（N2）** dev-loop `SKILL.md` の本文から、**利用者が居る周・台帳の無い周**でも `references/absent-lines.md` の「確認の Issue の書き方」に辿り着く 1 文がある（手順 6 か 8）。
  その 1 文は、同じファイルの他の記述（「利用者が居る周では読まなくてよい」）と食い違わない。
- **I2（CR1-3 の決まり）** cruise `SKILL.md` に、**親が自分で立てた確認の Issue を、台帳の `decisions` に足す**決まりがある。どの行に足すか・足す行が無い判断の扱いが書いてある。
  書いてある `ledger.py` の呼び方が実物の `ledger.py` で通る（前の値に足して渡す形）。
- **I3（CR1-3 の突き合わせ）** cruise §6 に、終えるときに **`要確認` ラベルの開いた Issue を探して `decisions` と突き合わせる**手順がある。
  この cruise の分だけを拾う絞り方（印 `<!-- cruise-decision: #<親> -->`）と、`decisions` に無かったものも渡すことが書いてある。
  書いてあるコマンドが実物の `gh` で、この cruise の開いた確認の Issue を返す（実データ: #474）。ラベルが無いリポジトリでの扱いが書いてあり、`absent-lines.md` の「ラベルが無ければ作らない」と食い違わない。
- **I4（版）** dev-loop の版が 3 種類（`marketplace.json`・`plugin.json`・両 `SKILL.md` の 2 行）で揃い、main より上。
- **I5（生成物）** 設計 §8.2 の生成ブロックが `skill-metrics.py --check` で新しい。
- **I6（指し先）** 足した指し先（`references/absent-lines.md` の「確認の Issue の書き方」など）が実在する（`check-skill-pointers.py`）。

経路（各不変条件を破りうる入口）:

- I1: dev-loop `SKILL.md` を読む周の入口——手順 1 から読む新規の周（居る／不在）・`references/resume.md` から入る再開の周・cruise の子・
  利用者の指示で周の外で確認の Issue を立てるセッション（スキル本文の手順 6・8 を読む）。手順 8 の「起票」の項も確認の Issue に触れうる。
- I2: 親が確認の Issue を立てる場面——§4 の周の合間（子の報告の狭いパスの指摘を推奨で決める）・§6 の終える時・再開時。立てた判断が台帳の行に紐づかない場合（cruise 全体の判断）。
- I3: 終える条件の 2 形（全部済み／着手できる周が無い）。ラベルの有無。他の cruise・cruise 外の `要確認` Issue が混ざる場合。
  `decisions` にあるがラベルが無い古い Issue（ラベルを足す前の分）。
- I4〜I6: CI（`check-plugin-versions.py`・`check-version-bump.py`・`skill-metrics.py --check`・`check-skill-pointers.py`）。

組み合わせ（必須要件の掛け算）: 受入基準を Verifier と /code-review の両方に × 1 パス目・2 パス目 = 4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

証明できないもの（未証明）: cruise の親が実際の cruise で決まりどおりに `decisions` に足すか（振る舞い。Eval は無い）——規定の存在と、コマンドが実データで通ることまでを確かめる。

生成物: **該当あり**——設計ドキュメント §8.2 の生成ブロック（`skill-metrics.py`）。図の書き出しは触らないので該当なし。

## 未解決の判断・確認待ち

（実装中に出たら書く）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/646-confirm-issue-pointers`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-646`・
  起点 `e450e90`・base 参照 `origin/main` → `e450e90efcf91ba23952d8ab14da4a38ee54ce0f`
- 割り目（手順 4）: 不在のため訊かず続けた
- 交絡: 実験なし（コマンドの実データ確認のみ）

## 既知の限界・決着済みの論点

- `ledger.py` の `decisions` は行ごとで、cruise 全体の判断を置く行が無い——鍵を足さない（範囲の外）。行に紐づかない判断はラベルの突き合わせで拾う（#647 の推奨「両方やる」の理由そのもの）。
- 公開ページ（`docs/plugins/dev-loop-cruise.md`）は直さない——記述は変更後も真。

## 手順 8

- この周の起票: 0 件（確認の Issue も周の途中の課題の起票も無い。周の途中の課題は親に報告し、親が起票して台帳に足す）
