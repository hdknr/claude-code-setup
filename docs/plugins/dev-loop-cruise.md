# dev-loop のオートクルーズ（複数 Issue を不在のまま回す）

**依存のある複数の Issue** を、1 つの親セッションで**起票 → 実装 → 関門 → マージ**まで回し、
利用者が席を外していても止まらずに進めるための使い方です。
dev-loop は「1 Issue = 1 周」のスキルなので、オートクルーズは**その周を束ねる運用**です。
回す Issue を**親 Issue のチェックリスト**に書いておき、`/dev-loop:cruise <親 Issue>` で起動します。

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
| 入口 | `../cruise/SKILL.md`・`../cruise/scripts/parent-issue.py` | 親 Issue の一覧を読み、確かめてから台帳を作る。起動し直すと台帳から再開する |
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
入ったのは 1.56.0、起動のコマンド `/dev-loop:cruise`（[#446](https://github.com/hdknr/claude-code-setup/issues/446)）が
入ったのは 1.57.0 です。** それより前の版には、台帳も不在の線も入っていません。

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

## 3. 親 Issue に一覧を書いて起動する

回す Issue を、**親 Issue**（どの Issue でもよい）の本文にチェックリストで並べます。依存は `(depends: …)` で書きます。

```markdown
- [ ] #12
- [ ] #13 ログイン画面 (depends: #12)
- [ ] #14 (depends: #12, #13)
- [x] #11
```

- `[x]` の行は済んだものとして扱い、台帳に入れません。それへの依存は満たされたと読みます。
- `#番号` で始まらないチェックボックス（受入基準など）は台帳に入れず、起動時の確認に「読み飛ばした行」として並びます。
  `#` の書き忘れはここで気づけます。
- 依存の書き方を誤った行（`(depends: …)` の外に「depends」「依存」や `#番号` がある、など）や、閉じていないコードフェンスがあると、台帳を作らずに止まります。
- コードフェンスと HTML コメント（`<!-- … -->`）の中は読みません。引用（`>`）の中の行は「読み飛ばした行」に並びます。
  書式の決まりは
  [`parent-issue.py` の docstring](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/scripts/parent-issue.py)
  を正とします。

メインの作業ツリーで Claude Code を起動し、親 Issue の番号で起動します。

```text
/dev-loop:cruise 50            # 居るとき（途中で訊きながら進む）
/dev-loop:cruise 50 --absent   # 不在で回す
```

1. **取り出した一覧と依存（と読み飛ばした行）が表示されるので、確かめて答えます。** 親 Issue の本文は誰でも書き換えられる入力として扱うので、
   `--absent` を付けても、ここだけは起動の時点で訊かれます。確かめた後に本文が書き換えられていたら、台帳は作られません。
2. **台帳が作られ、着手できる Issue から順に dev-loop の周として回ります。**
   台帳は `<メインの作業ツリー>/.claude/plans/cruise-issue-<親>.json` に置かれます。
   各周は通常の dev-loop と同じで、Verifier と `/code-review` を 2 パスで打ち切るのもオートクルーズでも同じです。
   **台帳は周を束ねる道具で、周を軽くする道具ではありません。**
3. **`--absent` を付けると、途中の問い（直す線・割り目・起票の承認）を訊かずに進みます。**
   進めてよい範囲は「1. 対象リポジトリに宣言を書く」の宣言だけで決まり、`--absent` は範囲を広げません。
   マージは `マージ` の線を宣言していれば行い、無ければ PR を出したところで止まって、依存していない別の Issue へ進みます。

起動の手順の決まりは
[`cruise` スキルの本文](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/SKILL.md)
を正とします。

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

**同じ引数で起動し直せば、台帳から再開します**（台帳は作り直しません）。親 Issue に後から足した Issue は名指しされます——台帳に足すかは利用者が決めます（自動では足しません）。

```text
/dev-loop:cruise 50 --absent   # 前と同じ引数で
```

周を重ねると親セッションの文脈が積み上がるので、周と周の間で `/clear` して起動し直すのも同じ手です。
台帳の中身は `ledger.py show issue-<親>` でも見られます。

- **終了コード 4（判定できなかった）なら再開しません。** 台帳が読めないことを「全部済んだ」と読まないためです。
- 進行中の Issue は、台帳の値ではなく実物（`gh pr view`・`git worktree list`）で確かめてから続けます。
  各周の続きは、その周の計画ファイルの再開点から始めます。
- 着手できるものも進行中のものも無いのに「すべてマージ済みか取り下げ」と出ていなければ、どこかで止まっています。
  止まった Issue の `note` に理由が書かれています。

#389 のもとになった運用では、30 分おきのタイマー（`CronCreate`）に台帳を読ませて再開していました。
**タイマーを張るかどうかは利用者が決めます**（スキルは自分で張りません）。張るなら、タイマーに渡すプロンプトも同じ引数の起動にします。

## 6. 戻ってきたら見るもの

- **台帳**——`ledger.py show issue-<親>` で、どれがマージ済みで、どれが止まっているか（`note` に理由）。
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
