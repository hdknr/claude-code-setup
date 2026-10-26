# dev-loop のオートクルーズ（複数 Issue を不在のまま回す）

**依存のある複数の Issue** を、1 つの親セッションで**起票 → 実装 → 関門 → マージ**まで回し、
利用者が席を外していても止まらずに進めるための使い方です。
dev-loop は「1 Issue = 1 周」のスキルなので、オートクルーズは**その周を束ねる運用**です。
専用のコマンドは無く、親セッションへの指示と、スキルに入っている部品を組み合わせて使います。

!!! warning "規範はスキルのディレクトリにあります"
    このページは**部品の場所と使う順番の案内**です。各部品の決まり（いつ書くか・どこで止まるか・何を守らないか）は
    [スキル本文](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/SKILL.md)と
    [`references/`](https://github.com/hdknr/claude-code-setup/tree/main/plugins/dev-loop/skills/dev-loop/references)、
    スクリプトの docstring を正とします。**ここに書き写すと片方だけが古くなる**ので、要点しか書いていません。

!!! note "部品をそろえて通しで回した実績は、まだありません"
    部品は [#389](https://github.com/hdknr/claude-code-setup/issues/389) から分けた Issue で入りました
    （台帳・実装役の委譲文・積んだ周・マージ・不在の線・環境点検・直す線）。
    ただし、**入った部品だけで複数の Issue を最後まで回したことは、まだありません**。
    #389 のもとになった運用は、部品が入る前に親セッションが手で組み立てたものです。
    最初は依存の少ない 2〜3 件で試し、台帳と計画ファイルを見ながら進めてください。

## 部品の一覧

| 部品 | 置き場所（スキルの base ディレクトリから） | 役割 |
| --- | --- | --- |
| 台帳 | `scripts/ledger.py`・`references/ledger.md` | Issue の依存と状態をファイルに持つ。再開の入口 |
| 実装役の委譲文 | `prompts/implementer.md` | 実装役（`Agent`）に渡す文面のテンプレート |
| 積んだ周（stacked） | `references/stacked.md` | 未マージの下の周の上で、上の周を先に始める |
| マージ | `scripts/merge-pr.py` | CI 待ち → squash → worktree の撤去 → Issue が閉じたかの確認 |
| 不在の線 | `references/absent-lines.md` | 利用者がいないとき、止まる代わりに進んでよい範囲 |
| 環境点検 | `scripts/check-unattended-env.py` | 席を外す前に、許可・自動継続・通知などを読むだけで点検する |
| 直す線 | `references/fix-line.md` | 関門の指摘をどこまで周の中で直すか |

**スキルの base ディレクトリ**は、プラグインで入れていれば
`~/.claude/plugins/cache/claude-code-setup/dev-loop/<版>/skills/dev-loop`、
`scripts/link-skills.sh` で張っていれば `~/.claude/skills/dev-loop` です。
キャッシュには古い版も残るので、`<版>` は下の「版を確かめる」で読み込まれている版にします。
スキルを起動すると、親セッションには base ディレクトリが渡されます。
## 0. 版を確かめる

**部品がそろうのは dev-loop 1.55.0 からで、積んだ周のマージの歯止め（[#426](https://github.com/hdknr/claude-code-setup/issues/426)）が
入ったのは 1.56.0 です。** それより前の版には、台帳も不在の線も入っていません。

```bash
claude plugin list --json                                 # 読み込まれる版を確かめる
claude plugin update dev-loop@claude-code-setup           # 古ければ上げる（そのあと再起動）
```

更新が届かない形と確かめ方は、[プラグイン一覧の「更新のしかた」](index.md#updating)を正とします。

## 1. 対象リポジトリに宣言を書く（席を外す前）

不在のあいだに進めてよい範囲は、**対象リポジトリの `.claude/dev-loop.md`** に書きます。
PR を通る場所なので、許可の範囲が利用者の目を通ります。

```text
不在の線: 仕様の穴 = 推奨で決めて起票
不在の線: 実機確認 = Refs でマージ
不在の線: マージ = 関門を通ればマージ
直す線: 既定
```

- **書かなければ、どの線も「止まる」です。** マージも宣言が無ければしません（PR を出して止まります）。
  必要な線だけを書きます。
- **本番反映（デプロイ・migrate・本番の設定値）は広げられません。** main への push で自動デプロイする
  リポジトリでは、マージ自体が本番反映に数えられるので、`マージ` の線も効きません。
- 値の一覧と、それぞれの線で何が起きるかは
  [`references/absent-lines.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/references/absent-lines.md)
  を、`直す線` は
  [`references/fix-line.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/references/fix-line.md)
  を正とします。

## 2. 環境を点検する（席を外す前に 1 度）

```bash
python3 <スキルの base ディレクトリ>/scripts/check-unattended-env.py
```

許可ルール（`git push`・`gh pr create`・`gh pr merge` など）、利用上限での自動継続、質問の待ち、通知、スリープを読み、
足りないものと直し方を出します。**直すのは利用者です**（スクリプトは書き換えません）。

通知は、設定が正しくても届かない形があります。iPhone を**いまのセッション**につなぎ（`/remote-control`）、
端末を操作していない状態で試しに送って確かめます。手順は
[リモートコントロールの設定手順（不在中の運用）](../usage/advanced-remote-control.md)と、
スキル本文の「待ち時間・定時処理は別スキル」を正とします。

## 3. 親セッションに指示する

メインの作業ツリーで Claude Code を起動し、dev-loop を読み込んだうえで、**回す Issue と依存、不在であること**を伝えます。
たとえば次のように指示します。

```text
/dev-loop:dev-loop 12

続けて #13 と #14 も回してください。#13 は #12 に、#14 は #13 に依存します。
台帳の名前は sprint-a。私はこれから不在なので、.claude/dev-loop.md の不在の線に従ってください。
```

**「不在」と明示するのが大事です。** スキルは、利用者が「居ないあいだに回せ」と指示した周だけを不在の周として扱い、
そのときだけ途中の問い（直す線・割り目・起票の承認）を訊かずに進めます。
言わなければ通常どおり `AskUserQuestion` で訊き、答えを待って止まります。

親セッションは、おおむね次の順で進めます（決まりは各 `references/` を正とします）。

1. **台帳を作る**——`ledger.py init` → `ledger.py add <名前> <番号> --deps …`。依存先から先に足します。
   台帳は `<メインの作業ツリー>/.claude/plans/cruise-<名前>.json` に置かれ、worktree の中から読んでも同じファイルを指します。
2. **着手できる Issue を選ぶ**——`ledger.py next <名前>` が「未着手で、依存がすべてマージ済み」のものだけを出します。
   互いに依存していないものは並行に始めてよいです。
3. **周ごとに実装役を起動する**——worktree を切り、`prompts/implementer.md` を使って実装を委譲します。
   その周の受入基準と再開点は、周ごとの計画ファイルに書かれます（台帳には写しません）。
4. **関門を回す**——Verifier と `/code-review` を 2 パスで打ち切るのは、オートクルーズでも同じです。
   **台帳は周を束ねる道具で、周を軽くする道具ではありません。**
5. **マージする**——`マージ` の線を宣言していれば `merge-pr.py <PR 番号>` で squash します。
   宣言が無ければ PR を出したところで止まり、台帳上で依存していない別の Issue へ進みます。
6. **状態が動くたびに台帳を書く**——書くのは親だけです。子が「マージした」と報告しても、親が `gh pr view` で確かめてから書きます。

## 4. 依存先がマージ待ちのうちに始める（積んだ周）

依存先の PR がまだマージされていなくても、上の周が使う部分（API・型など）が下の関門を通っていれば、
**下のブランチの上に積んで**先に始められます。

- **積むかどうかは人間が決めます。** 不在のあいだに積んでよいかは、スキルは決めていません。
  積ませたいなら、指示の中で「#14 は #13 の PR に積んで始めてよい」と明示してください。
- 下の周がマージされたら、上の周を既定ブランチの上に**載せ替えてから**マージします。
  `merge-pr.py` は載せ替えていない積んだ周の PR を止めますが、見分けられない形があります。
- 手順は [`references/stacked.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/references/stacked.md)
  を正とします。

## 5. 再開する（タイマー・`/clear`・別セッション）

入口はいつも台帳です。

```bash
python3 <スキルの base ディレクトリ>/scripts/ledger.py show <名前>
```

- **終了コード 4（判定できなかった）なら再開しません。** 台帳が読めないことを「全部済んだ」と読まないためです。
- 進行中の Issue は、台帳の値ではなく実物（`gh pr view`・`git worktree list`）で確かめてから続けます。
  各周の続きは、その周の計画ファイルの再開点から始めます。
- 着手できるものも進行中のものも無いのに「すべてマージ済みか取り下げ」と出ていなければ、どこかで止まっています。
  止まった Issue の `note` に理由が書かれています。

#389 のもとになった運用では、30 分おきのタイマー（`CronCreate`）に台帳を読ませて再開していました。
**タイマーの張り方はスキルの決まりに入っていない**ので、使うなら指示の中で頼んでください。

## 6. 戻ってきたら見るもの

- **台帳**——`ledger.py show <名前>` で、どれがマージ済みで、どれが止まっているか（`note` に理由）。
- **各 PR のコメント**——関門の残課題、名指しの未証明、訊かずに進めた箇所が書かれています。
  `マージ` の線でマージした PR も、戻ってから PR コメントで確かめる前提です。
- **`要確認` ラベルの Issue**（ラベルが無いリポジトリでは題の先頭が `要確認:`）——`仕様の穴` の線で、
  推奨で決めて進めた判断です。閉じずに残してあります。
- **開いたままの元の Issue**——`実機確認` の線で `Refs` のままマージした Issue です。実機で確かめてから閉じます。

## 関連

- [プラグイン一覧 — dev-loop](index.md#dev-loop)
- [dev-loop の設計（ループ志向開発）](dev-loop-design.md)
- [リモートコントロールの設定手順（不在中の運用）](../usage/advanced-remote-control.md)
- [#389 オートクルーズ](https://github.com/hdknr/claude-code-setup/issues/389)（要件の出所と、部品への分け方）
