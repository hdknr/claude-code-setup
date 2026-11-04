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
| マージ | `scripts/merge-pr.py` | CI 待ち → squash → worktree の撤去 → Issue が閉じたかの確認。台帳でその PR の行が利用者の判断を待っていればマージしない（#631） |
| 不在の線 | `references/absent-lines.md` | 利用者がいないとき、止まる代わりに進んでよい範囲 |
| 環境点検 | `scripts/check-unattended-env.py` | 起動時に、周で使う操作の許可・止まりうる操作・親の起動場所を読むだけで点検する。席を外すなら自動継続・通知なども（席を外したあとの再開の `--since-last` だけは、前回の結果を台帳の隣に残す） |
| 直す線 | `references/fix-line.md` | 関門の指摘をどこまで周の中で直すか |
| まとめの周 | `../cruise/references/grouping.md`・`scripts/ledger.py`（`group`） | 周の途中で足した、同じファイルを触る行を 1 周・1 PR にまとめる（[#641](https://github.com/hdknr/claude-code-setup/issues/641)） |
| 長期トークンの起動口 | `scripts/launch-with-long-token.sh` | 対話ログインの 8 時間の期限で止めないよう、キーチェーンの長期トークンで `claude` を起動する（[cruise を長期トークンで起動する](../usage/cruise-long-lived-token.md)） |
| 子プロセスの周（任意） | `../cruise/scripts/child-cycle.py`・`../cruise/references/child-process.md` | 周を `claude -p` の子プロセスで回す起動口と要約。親の `/clear` の道連れにならない。**既定はサブエージェントのまま**（[#491](https://github.com/hdknr/claude-code-setup/issues/491)） |
| 順番待ちと並行の周 | `../cruise/scripts/run-serial.py`・`../cruise/references/parallel.md` | 周の重い検査・アプリの起動を、同じリポジトリでは順番待ちにする（既定は 1 本ずつ）。単独で回す周と、版をマージの直前に上げ直す決まりも（[#493](https://github.com/hdknr/claude-code-setup/issues/493)・[#531](https://github.com/hdknr/claude-code-setup/issues/531)） |

**スキルの base ディレクトリ**は、プラグインで入れていれば
`~/.claude/plugins/cache/claude-code-setup/dev-loop/<版>/skills/dev-loop`、
`scripts/link-skills.sh` で張っていれば `~/.claude/skills/dev-loop` です。
キャッシュには古い版も残るので、`<版>` は下の「版を確かめる」で読み込まれている版にします。
スキルを起動すると、親セッションには base ディレクトリが渡されます。

## 0. 版を確かめる

**部品がそろうのは dev-loop 1.55.0 からで、積んだ周のマージの歯止め（[#426](https://github.com/hdknr/claude-code-setup/issues/426)）が
入ったのは 1.56.0、起動のコマンド `/dev-loop:cruise`（[#446](https://github.com/hdknr/claude-code-setup/issues/446)）が
入ったのは 1.57.0、親 Issue の線（`cruise:` の行。[#458](https://github.com/hdknr/claude-code-setup/issues/458)）が入ったのは 1.58.0、周の途中で見つかった課題を台帳に足す線（[#464](https://github.com/hdknr/claude-code-setup/issues/464)）が入ったのは 1.59.0、同じファイルを触る足した行を 1 周にまとめる手順（[#641](https://github.com/hdknr/claude-code-setup/issues/641)）が入ったのは 1.67.0 です。**
1.55.0 より前の版には、台帳も不在の線も入っていません。

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
cruise の操作: gh workflow run infra-apply.yml
```

- **書かなければ、どの線も「止まる」です。** マージも宣言が無ければしません（PR を出して止まります）。
  必要な線だけを書きます。
- **本番反映（デプロイ・migrate・本番の設定値）は広げられません。** main への push で自動デプロイする
  リポジトリでは、マージ自体が本番反映に数えられるので、`マージ` の線も効きません。
  **マージが起こす反映が公開ドキュメントのサイトの再ビルドだけなら**、`マージの反映: ドキュメントのみ` の 1 行を書けます。
  各周はマージの前に `CLAUDE.md`・deploy runbook・ワークフローの定義と、既定ブランチそのものが配布元になっていないか
  （利用者が main から取るプラグインのカタログなど）をこの宣言と照らし合わせ、宣言の外の反映（サイトの公開のほかのデプロイ・
  パッケージの公開・利用者が取りに来る配布物の更新など）が無いときだけ、`マージ` の線を効かせます。
  周が自分の PR で足した宣言は、その周のマージには効きません。
  **マージがプラグインの中身も利用者に配る**（main がプラグインのカタログの配布元で、`git pull` して `link-skills.sh` で張る利用者もいる）リポジトリは、
  `マージの反映: ドキュメントとプラグインの配布` を書けます（このリポジトリはこれを置いています）。この値ではプラグインの中身の配布は宣言の中で、
  照合はそれ以外について上と同じに見ます。加えてその周の差分が、カタログの版と説明のほか・プラグインの hooks や MCP サーバの定義・`.claude/settings.json`・
  利用者が clone のパスで hook などに登録させているスクリプトを変えていればマージしません。
  **配布は revert しても取った利用者の状態が戻らないので、`マージ` の線は cruise ごとに確かめたもの**（起動時か再開時の確認で配布を起こすと見せて確かめ、
  台帳の線の出所に印 `配布を見せて確かめた` を区切った形で書いて `ledger.py show` の「配布の確認」が `あり` になったものか、その周の利用者の直接の指示）**でしか効きません**——
  `.claude/dev-loop.md` の `不在の線: マージ` だけでは、配布を起こすマージはしません。
  `マージ` の線が効かないリポジトリでは、`--absent` の起動時の確認にそう出ます。
- **`並行の検査: N` は、周が同じリポジトリで同時に走らせる重い検査・アプリの起動の本数**です（書かなければ 1——順番待ちで 1 本ずつ）。
  検査が互いに干渉せず、ポート・データベースを奪い合わないと分かっているリポジトリだけ増やします。**利用者が居る cruise にも効きます。**
  書式は [`run-serial.py` の docstring](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/scripts/run-serial.py) を正とします。
- **`cruise の操作:` は、周で打つ操作のうち既定の点検（`git push`・`gh pr create`・`gh pr merge`・`gh pr comment`・`gh issue create`）に
  無いもの**を 1 行 1 コマンドで書きます（本番反映の口など）。起動時の点検がその許可を見ます。**利用者が居る cruise でも書いておきます。**
- 値の一覧と、それぞれの線で何が起きるかは
  [`references/absent-lines.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/references/absent-lines.md)
  を、`直す線` は
  [`references/fix-line.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/references/fix-line.md)
  を正とします。

## 2. 環境を点検する（起動時に 1 度） { #env-check }

```bash
python3 <スキルの base ディレクトリ>/scripts/check-unattended-env.py --cruise --ledger issue-<親>            # 席を外すとき
python3 <スキルの base ディレクトリ>/scripts/check-unattended-env.py --cruise --present --ledger issue-<親>  # 居るとき
python3 <スキルの base ディレクトリ>/scripts/check-unattended-env.py --cruise --ledger issue-<親> --since-last  # 席を外したあとの再開
```

**席を外したあとの再開では `--since-last` を付けます**——前回の点検と同じ項目を 1 行（区分ごとの件数・前回の時刻・要対処と判定できないの項目の名前）に縮め、変わった項目だけを全文で出します。
前回の結果は台帳の隣の `cruise-issue-<親>.env-check` に残ります（[#635](https://github.com/hdknr/claude-code-setup/issues/635)）。
`claude -p` で起動した cruise では、通知の設定の 2 項目は「人が見る」の 1 行になります——人を呼ぶ経路は起動した側で用意します。

**cruise は台帳を作ったあと、`--absent` に依らずこれを回して結果を見せます。** 利用者が居ても、権限の拒否や確認で
周が止まり、操作を待つことになるためです（[#466](https://github.com/hdknr/claude-code-setup/issues/466)）。

- **許可ルール**——既定の操作と `cruise の操作:` で宣言した操作が `allow` に当たるか。
- **止まりうる操作**——自動モードの分類器と worktree 隔離のガードは settings に現れないので、許可があっても止まりえます。
  起動時に操作ごとに選びます: 許可を足す／**その操作だけ自分で打つ**（台帳に残り、周はその操作の手前で「操作待ち」になって
  依存しない次の周へ進みます）／その周を cruise の外に出す。
- **親の起動場所**——**cruise の親は、メインの作業ツリーから worktree に入らずに起動するのが既定です。**
  worktree の中から起動すると、別の worktree・別のリポジトリへの操作がガードに拒まれます。
- **不在の間にどこまで進めるか**（[#490](https://github.com/hdknr/claude-code-setup/issues/490)）——台帳の済んでいない周ごとに、
  マージまで進む見込みか・PR で止まるか・始まらないか（依存先と、止まる元）・止まっているかと、その理由を出します。
  理由は、`マージ` の線がこのリポジトリで効かない・PR が main と衝突している・同じプラグインの版を上げる PR が 2 本ある・
  マージの前に利用者の判断が要る（台帳の `note` が `利用者の判断待ち:` で始まる）・利用者の操作待ち、などです。
  **見込みです**——関門・CI・利用上限で止まる周は数えず、`マージ` の線の照合（ワークフロー・`CLAUDE.md`・周の差分）は各周がマージの前に行います。
  止まる周を片づけてから離れるかは利用者が決めます。
- **席を外すとき**（`--present` なし）は、利用上限での自動継続・質問の待ち・通知・スリープも読みます。
- **認証**——長期トークンで起動したか、対話ログイン（8 時間で切れる）かを出します。対話ログインなら、起動時に長期トークンで回すかを訊きます
  （[cruise を長期トークンで起動する](../usage/cruise-long-lived-token.md)。**長期トークンでは claude.ai のコネクタ・claude.ai から届くスキル・Remote Control・Claude in Chrome が使えません**——2.1.316 で測り、エラーは出ず黙って無い形でした。通知は判定できていません）。

足りないものと直し方を出します。**直すのは利用者です**（スクリプトは書き換えません）。
点検と同じ場面で、**再開タイマーを張るかも 1 度だけ訊きます**（張れる範囲の限界と一緒に。下の「5. 再開する」。[#472](https://github.com/hdknr/claude-code-setup/issues/472)）。

通知は、設定が正しくても届かない形があります。iPhone を**いまのセッション**につなぎ（`/remote-control`）、
端末を操作していない状態で試しに送って確かめます。手順は
[リモートコントロールの設定手順（不在中の運用）](../usage/advanced-remote-control.md)と、
スキル本文の「待ち時間・定時処理は別スキル」を正とします。

利用上限で止まったことをその場で記録・通知したいなら、`StopFailure` の hook を user の settings に足します
（[利用上限の停止をその場で記録する](../usage/usage-limit-stop-hook.md)。登録は利用者が行います。
**上限で実際に発火するかは確かめていません**）。下の「利用上限で止まったとき」の自動継続の確認
（[#456](https://github.com/hdknr/claude-code-setup/issues/456)）を取りこぼさないためのものです。

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
- 依存の書き方を誤った行（`(depends: …)` の外に「depends」「依存」や `#番号` がある、など）や、閉じていないコードフェンス・行頭から始まって閉じない HTML コメントがあると、台帳を作らずに止まります。
- コードフェンスと HTML コメント（`<!-- … -->`）の中は読みません。引用（`>`）の中の行は「読み飛ばした行」に並びます。
- チェックリストの行が 1 本も無い Issue は親 Issue として扱いません（1 件だけなら `/dev-loop:dev-loop <番号>` で回します）。

### 周の途中で訊く判断を、親 Issue に書いておく（線）

同じ親 Issue に `cruise:` の行を書くと、**周ごとに訊かれる判断を起動時に 1 度だけ確かめて**、各周へ渡せます（再開したときに確かめ直せば、その値に書き直します）。

```markdown
cruise: 仕様の穴 = 推奨で決めて起票
cruise: 直す線 = 既定
```

- **起動時の確認に、書いた線と「書いていない」線が並びます。** 書いていない線は台帳に残らず、`--absent` の周なら「1. 対象リポジトリに宣言を書く」の `不在の線:` の宣言、無ければ既定（止まる）になります（`直す線` は下のとおり起動時に訊かれます）。
  確かめた線は台帳に残り、Issue の本文をあとで書き換えても、確かめ直すまでは台帳の値が使われます。
- **確かめた `仕様の穴` と `直す線` は、利用者が居る周（`--absent` なし）でも効きます**——`仕様の穴 = 推奨で決めて起票` なら、
  訊かずに推奨で決めて確認の Issue を立てて進みます（`直す線` は周ごとに訊かなくなるだけです）。
  `実機確認` と `マージ` は `--absent` の周だけに効きます。`.claude/dev-loop.md` の `不在の線:` の宣言も `--absent` の周だけに効きます。
- **`直す線` をどこにも書いていなければ、起動時に 1 度だけ訊かれます**（周ごとには訊きません）。
- **`周の途中の課題 = 台帳に足して直す` にすると、周の途中で見つかった課題も同じ cruise の中で直します**（親 Issue の一覧の課題が済むまで。済んだら、まだ始めていない課題は回さずに渡されます。書いていなければ起動時に訊かれます。既定は `外に出す`）。
  各周はマージの前に、関門の残課題・狭いパスの指摘・仕様の穴・範囲の外にした機能・利用者の判断が要る行を振り分け、
  **実物で失敗を示せて、受入基準を破る・利用者に見える誤り・その周が持ち込んだ後退のどれかに当たる行**（実際の利用でまず起きない形を除く）だけを Issue にして台帳に足します
  （依存は元の周。台帳の「出所」の列に、どの周のどの関門の行かが残ります）。それ以外（テストの試料の穴・まれな書き方・文言・性能の推測）は PR コメントにだけ残ります。
  この振り分けは `外に出す` の周でも同じで、起票の候補と `要確認:` の Issue も、当たる行だけに絞られます（[#774](https://github.com/hdknr/claude-code-setup/issues/774)）。
  利用者の判断が要る行は止めておき、居るときは周の合間にまとめて訊かれます。`--absent` なら訊かずに、終えるときに渡されます。
  狭いパスの指摘も同じ線で振り分けられ、各周は指摘ごとに振り分けと理由を PR コメントに書きます。`マージ = 関門を通ればマージ` の周で、狭いパスの指摘を理由にマージを止めるのは、
  受入基準を破る・利用者に見える誤り・その周が持ち込んだ後退に当たる指摘（後退は振り分けに依らず止まります）・振り分けと理由が PR コメントに無い指摘と、周が「マージ前に人が判断」と報告したものだけです。
  親はマージの前にその PR コメントを読み直し、記録だけ・捨てるの理由が上の 3 つに当たりうる・迷うなら止めます（CI が緑でない・満たしていない受入基準があるなど、ほかの止まる条件はそのままです）。試料の穴・テストの無い分岐・文言の曖昧さだけ（従うと誤った操作になる記述は除く）なら、指摘を PR コメントに残したままマージされます（[#821](https://github.com/hdknr/claude-code-setup/issues/821)）。振り分けの決まりは
  [`references/found-lines.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/references/found-lines.md)
  を正とします。
  **直す行は触るファイルごとに 1 件の Issue（チェックリスト）で起票され、同じファイルを触る足した行は、次の周を選ぶ前に 1 周・1 PR にまとめられます**
  （2〜5 件。訊かずにまとめ、居るときは報告に並びます。PR に `Fixes` が並び、マージの後に閉じなかった元の Issue は PR を名指しして閉じます）。
  いつ・何をまとめるかは
  [`references/grouping.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/references/grouping.md)
  を正とします。
- **`本番反映` の行は無視されます**（広げられません）。書けない値や同じ線の 2 行は、台帳を作らずに止まります。
- 線の意味と、各周がどの順で読むか（台帳 → `.claude/dev-loop.md` → 既定）は
  [`references/absent-lines.md` の「cruise で確かめた線」](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/dev-loop/references/absent-lines.md)
  を正とします。
  書式の決まりは
  [`parent-issue.py` の docstring](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/scripts/parent-issue.py)
  を正とします。

メインの作業ツリーで Claude Code を起動し、親 Issue の番号で起動します。

```text
/dev-loop:cruise 50            # 居るとき（途中で訊きながら進む）
/dev-loop:cruise 50 --absent   # 不在で回す
```

1. **取り出した一覧と依存（と読み飛ばした行・線）が表示されるので、確かめて答えます。** 親 Issue の本文は誰でも書き換えられる入力として扱うので、
   `--absent` を付けても、ここだけは起動の時点で訊かれます。確かめた後に本文が書き換えられていたら、台帳は作られません。
2. **台帳が作られ、着手できる Issue から順に dev-loop の周として回ります。**
   台帳は `<メインの作業ツリー>/.claude/plans/cruise-issue-<親>.json` に置かれます。
   各周は通常の dev-loop と同じで、Verifier と `/code-review` を 2 パスで打ち切るのもオートクルーズでも同じです。
   **台帳は周を束ねる道具で、周を軽くする道具ではありません。**
   周の途中の割り目（dev-loop の手順 4・6 で「ここで割るか」を訊く場面）は、`--absent` を付けなくても訊きません——
   周は子（サブエージェントか、任意の子プロセス）が回し、利用者の `/clear` が割るのは親の文脈だからです（[#461](https://github.com/hdknr/claude-code-setup/issues/461)）。
3. **`--absent` を付けると、途中の問い（直す線・起票の承認）を訊かずに進みます。**
   進めてよい範囲は確かめた線と「1. 対象リポジトリに宣言を書く」の宣言だけで決まり、`--absent` は範囲を広げません。
   マージは `マージ` の線を宣言していれば行い、無ければ PR を出したところで止まって、依存していない別の Issue へ進みます。

起動の手順の決まりは
[`cruise` スキルの本文](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/SKILL.md)
を正とします。

### 周を並行に回すとき

- **各周の重い検査・アプリの起動は、同じリポジトリでは順番待ちになります**（上の `並行の検査:`。既定は 1 本ずつ）。待たされた周は、待っていることと、いま走っているものを出力に出します。
  周の数ではなく検査を絞るのは、検査を起こすのが周の実装役だけでなく、検証とレビューの体でもあるからです。
- **負荷・所要時間を測る周と、わざと負荷を作る周は単独で回します。** 親は台帳の `note` に `単独: <理由>` の項を書くので、再開した親にも分かります。
- **親は版を割り当てません。** 各周は PR で版を上げ、マージの直前に PR が main より古ければ、main を取り込んで main より上に上げ直してからマージします。
  利用者の判断を待つ PR があっても、同じプラグインを触る他の周を先にマージできます。
- 決まりは
  [`references/parallel.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/references/parallel.md)
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

周を重ねると親セッションの文脈が積み上がりますが、**文脈が長くなったことは止める理由になりません**（[#583](https://github.com/hdknr/claude-code-setup/issues/583)）。
Claude Code が文脈を要約（compact）したら、親は次の操作の前にスキル本文・台帳・進行中の周の実物を読み直してから続けます。
読み直すものと、親が止めてよい条件は cruise の [`SKILL.md`](https://github.com/hdknr/claude-code-setup/blob/main/plugins/dev-loop/skills/cruise/SKILL.md) §5 を正とします。
周と周の間で `/clear` して起動し直すのも同じ手です（自動の compact を切っているなら、こちらで割ってください）。
ただし `/clear` は利用者が打つ操作なので、**割ると、打って起動し直すまで cruise は止まります**。親は、続けられるのに周の合間で `/clear` を案内して止まることはせず、compact で続けます（割るかは利用者が決めます）
（[#461](https://github.com/hdknr/claude-code-setup/issues/461)。タイマーは同じセッションにプロンプトを注入するだけで、文脈は軽くなりません）。
台帳の中身は `ledger.py show issue-<親>` でも見られます。

- **終了コード 4（判定できなかった）なら再開しません。** 台帳が読めないことを「全部済んだ」と読まないためです。
- 進行中の Issue は、台帳の値ではなく実物（`gh pr view`・`git worktree list`）で確かめてから続けます。
  各周の続きは、その周の計画ファイルの再開点から始めます。
- まとめの PR のマージの後、直せなかった行を台帳に戻す前に止まっていたら、`show` が「落ちたのにまとめの中で merged のまま」の行を名指しします。
  親は Issue と PR を実物で確かめてから、その行を戻します（[#665](https://github.com/hdknr/claude-code-setup/issues/665)）。
  名指しされた行が残るあいだ、`next` はその行に依存する行（先に戻した行・まとめの外の行）を着手できるものとして出しません（[#711](https://github.com/hdknr/claude-code-setup/issues/711)）。
- 着手できるものも進行中のものも無いのに「すべてマージ済みか取り下げ」と出ていなければ、どこかで止まっています。
  止まった Issue の `note` に理由が書かれています。

#389 のもとになった運用では、30 分おきのタイマー（`CronCreate`）に台帳を読ませて再開していました。
**タイマーを張るかどうかは利用者が決めます**——**新規の起動で、台帳を作ったあとに 1 度だけ訊きます**（「30 分おきに張る（推奨）」か「張らない」。
[#472](https://github.com/hdknr/claude-code-setup/issues/472)）。張ると答えたら、親が同じ引数の起動をプロンプトにして張り、張った時刻・間隔・次の発火・失効・ジョブ ID を伝えて、
答えを台帳に残します（`ledger.py timer`）。

- **タイマーはそのセッションの中にしか無く、セッションが終われば消えます**（Claude Code 2.1.317 の道具の説明。既定のタイマーの場合）。
  **セッションが落ちたら、メインの作業ツリーで同じ引数で起動し直してください**——利用者が居る再開では、タイマーが無ければもう一度訊きます
  （前に「張らない」と答えていれば訊きません）。
- **発火するのは親が応答していないときだけで、繰り返しは既定で 7 日で失効します**（本体の既定値。設定で変わりうるので、張ったときに伝える値を正とします）。
- **タイマーで入った親は、完了の通知が来ていない実装役・関門の体（タイマーを張った後に台帳が更新された進行中の周の体）を起こし直しません**——動いている前提で台帳と worktree の実物だけを見て、
  続けられる周が無ければ何もせずに戻ります。
- **タイマーは同じ引数に印 `--timer` を付けて起動します（人は打ちません）。この印のある起動（タイマーの発火）では、居る cruise でも起動時の問いを出しません。** `/clear` して自分で打ち直した再開では、これまでどおり訊きます。 不在の再開でも訊かず、2 本目のタイマーも張りません。

- **親は周の worktree に入りません**（#484）。各周はサブエージェントが worktree の絶対パスで回し、親はメインの作業ツリーに留まります。
  #484 では、周の worktree に入った親が `/clear` してもその worktree に隔離されたままになり、次の周を始められなくなりました。
- **会話の中で決めた、進めてよい範囲を広げる方針は、台帳に残りません。** 線の項目（`仕様の穴` など）に当たるなら、親 Issue の `cruise:` の行に書き、
  起動し直したときに確かめてください（席を外したままの再開では、台帳の線は書き換わりません）。
  「#N はマージしないで」「#M は回さないで」のような止める指示は、親がその場で台帳のその行に書くので、compact の後も残ります。
- **着手できる周が残っているのに親が次の周を始めないと決めたら**、親はこの cruise を再開するタイマーを止め、
  `/clear` してメインの作業ツリーから起動し直すよう通知して止まります。タイマーは `/clear` できないので、放っておくと同じ判断を繰り返すだけになります
  （#484 では 23 回・約 11.5 時間、周が 0 本でした）。タイマーを使い続けるなら、起動し直すときに張り直してください。
- **周を `claude -p` の子プロセスで回すこともできます（任意。[#491](https://github.com/hdknr/claude-code-setup/issues/491)）。**
  子は親から切り離して起きるので、親が `/clear` しても走り続け、起動の時点で入っている版を読み込みます。
  再開した親は、走っている子の周に 2 体目を起こしません。**既定はサブエージェントのままです**——関門が子の中で回りきるかと、
  利用上限で何が起きるかを、実際の周ではまだ確かめていません。回し方と確かめた範囲は `../cruise/references/child-process.md` を正とします。
- **前の版の親が worktree の中に残っていたら**、再開時の点検がそう言います。親は `ExitWorktree`（`keep`）を 1 度だけ試しますが、
  戻れた例は 1 件しか観測していません。戻れたかは `cd <メインの作業ツリー> && git worktree list` を打って確かめ、拒まれたら戻れなかったものとします
  （`claude -w` と `EnterWorktree(name)` で隔離したセッションではこの形が拒まれ、`ExitWorktree` で戻った後は通ることを測ってあります。
  **#484 の形——`EnterWorktree(path)` で入って `/clear` した隔離——では測っていません。**
  `cd` の無い `git worktree list` は隔離中でも通るので確かめになりません。[#504](https://github.com/hdknr/claude-code-setup/issues/504)）。
  戻れなければ、メインの作業ツリーで新しいセッションを開いて起動し直してください。

### `claude -p` で外から回すとき { #print-mode }

cruise を対話のセッションではなく、外側のループ（シェルのスクリプトなど）から `claude -p "/dev-loop:cruise <親> --absent"` で起動し直して回すときの注意です
（[#633](https://github.com/hdknr/claude-code-setup/issues/633)）。

- **`-p` は、ターンが閉じた後の背景のタスクを上限の時間しか待たず、過ぎると止めます。** spin-dd/tfs-stocks#2427 では、周の子を背景で起こして
  「待ちます」と書いてターンを閉じた親の子が、10 分で関門の途中で止められ、次の起動が周をやり直しました。標準エラーには
  `Background tasks still running 10m after the last turn (…); stopping them. Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to wait indefinitely.` と出ます。
  親は周の子を前景で呼ぶ決まりですが（スキル本文の「4. 周を回す」の 2）、並行に始めてよい周を 2 本以上回すときは背景で起こします。
  **外側のループは `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` を置いて起動してください。**
  0 で止めずに待つことは、上の標準エラーの文言によるだけで、測っていません。
- **タイマー（`CronCreate`）は要りません**——起動し直すのは外側のループです。タイマーはそのセッションの中にしか無く（上の「5. 再開する」）、
  `-p` のプロセスが終わった後に発火するかは確かめていません。外側のループは `--absent` で起動し直すので、再開でタイマーを訊き直しません（[#472](https://github.com/hdknr/claude-code-setup/issues/472)）。
- **続けるかは `ledger.py status` の終了コードで決めます**（[#632](https://github.com/hdknr/claude-code-setup/issues/632)）——0 なら進められる周がある、
  3 なら人を待つ周だけ、5 なら親 Issue の一覧の行がすべて済んだ、4 なら判定できなかった（済んだとは答えていません）。文面（`show`）で決めないでください。
  判定の順は `ledger.py` の docstring を正とします。
- **0 でも、1 回の起動で台帳の中身（更新時刻 `updated` を除く）が変わらなければ止めます。** マージの線が無く親がマージせずに止まった PR の行などは、
  `status` が 0 のまま残り、起動し直しても進みません（親が同じ `note` を書き直すと更新時刻だけが変わるので、ファイルのままでは比べません）。
  `claude` が 0 以外で終わったときも止めます（ログインの期限切れなどで、何も進めずにすぐ終わる起動を繰り返さないため）。

```bash
cd <メインの作業ツリー>
ledger=<dev-loop の base ディレクトリ>/scripts/ledger.py
digest() {  # 台帳から更新時刻を除いた中身の要約（台帳が無ければ空の要約）
  python3 - "$(python3 "$ledger" path issue-50)" 2>/dev/null <<'PY' | cksum
import json, sys
def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k != "updated"}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o
print(json.dumps(strip(json.load(open(sys.argv[1]))), sort_keys=True))
PY
}
for i in $(seq 1 20); do      # 回す回数の上限
  before=$(digest)
  CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude -p "/dev-loop:cruise 50 --absent" || { echo "claude が失敗した"; break; }
  python3 "$ledger" status issue-50
  rc=$?
  [ "$rc" -eq 0 ] || { echo "status: $rc"; break; }    # 3・4・5 は止まる。ほかの値も止まる
  [ "$before" != "$(digest)" ] || { echo "台帳が変わらなかった"; break; }
done
```

`<dev-loop の base ディレクトリ>` は、入っている版のスキルのディレクトリです（`~/.claude/plugins/cache/claude-code-setup/dev-loop/<版>/skills/dev-loop`）。
許可モード・モデルなどの引数は、上の「2. 環境を点検する」で決めたものを足してください。

### 利用上限で止まったとき

**`autoContinueAtUsageLimit: true` だけで続くとは、記録からは言えません。** 下の表のとおり、待ちを張らなかった停止（理由は記録に残りません）と、
Claude Code が終わって消えた待ちがあります。一方で、張った待ちが予告の時刻まで放っておかれたのに自動継続しなかった例のうち、
**理由が分かるのは取り消された 2 件だけ**で、残る 1 件は理由が分かりません——**根拠は数件です。**
**不在で回すなら、タイマーを保険として張るかを考えてください**（張るかは利用者が決めます）。

手元 1 台のトランスクリプト（2026-08-27〜10-23・main-chain）を `scripts/count-usage-limit-resumes.py` で数えた結果です（#454）:

| | 待ち |
| --- | --- |
| 上限で止まった待ち | 68 |
| うち自動継続の待ちを張った（`continuing automatically at …` の予告が出た） | 65 |
| 　予告の時刻の 1 分後に自動継続した | 8 |
| 　予告の時刻より前に、人間の入力かローカルコマンドが来た | 51 |
| 　予告の時刻の後、自動継続より先に人間が来た | 3 |
| 　Claude Code が待ちの間に終わって取り消された | 2 |
| 　何も来ずに記録が終わった | 1 |
| うち待ちを張らなかった（3 件とも週の上限 `seven_day`） | 3 |

- **張った待ちで、人間が予告の時刻まで来なかったものは 14 件**で、自動継続したのは 8 件です。
  残りは人間が数十秒先に来た 3 件・取り消された 2 件・理由の分からない 1 件です
- **待ちを張らなかった停止があります**——張らなかった 3 件は、どれも週の上限（`seven_day`）でした。
  ただし週の上限で止まった 4 件のうち 1 件は張っているので、**週の上限なら張らない、とは言えません**
  （張らなかった理由は記録に残りません）
- **Claude Code が終わると待ちは消えます**（`Automatic continue cancelled · Claude Code exited during the wait`）
- **どの層の設定から待ちを張ったのかは分かりません**——設定の履歴は記録に残りません。
  数えた日（2026-10-27）の手元の user の settings に `autoContinueAtUsageLimit` はありませんでしたが、
  それぞれの停止の時点の値は分かりません。数え方と、数えないものはスクリプトの docstring を正とします
- 上限を狙って起こす手段が無いので、**user の層に `true` を明示したうえで自動継続した例は、まだ取れていません**（#454）

## 6. 戻ってきたら見るもの

- **台帳**——`ledger.py show issue-<親>` で、どれがマージ済みで、どれが止まっているか（`note` に理由）。
- **利用者の操作待ち**——台帳の「利用者の操作待ち」に、打ってほしいコマンドが周ごとに載っています。
  打ったあとで同じ引数で起動し直すと、cruise が実物を確かめてからその周の続きを回します。
- **各 PR のコメント**——関門の残課題、名指しの未証明、訊かずに進めた箇所が書かれています。
  `マージ` の線でマージした PR も、戻ってから PR コメントで確かめる前提です。
  Issue にしなかった指摘は「記録だけ（起票しない。#774）」の見出しに並びます——実際に問題が起きたら、そのときに起票します。
- **cruise が終わるのは、親 Issue の一覧にある課題が済んだときです**——周の途中で足した課題が残っていれば、回さずに一覧で渡されます。
- **題の先頭が `要確認:` の Issue**（ラベル `要確認` も付きます。ラベルが無いリポジトリでは題だけです）——`仕様の穴` の線で、
  推奨で決めて進めた判断です。閉じずに残してあります。cruise から立てたものは台帳の「要確認」の列に番号が載り、
  終えるときに開いているものが一覧で渡されます。
    - **1 件に判断は 1 つです。** 本文の冒頭の 3 行（何が起きたか・選べること・何もしなければどうなるか）と、
      その下の「重さ」（済んだことか、PR にあってまだマージしていないことか、まだしていないことか）を読めば、何を判断すればよいかが分かるように書いてあります
      （書き方の決まりは dev-loop の `references/absent-lines.md` の「確認の Issue の書き方」）。
    - **承認するなら、その Issue を閉じます。**
    - **直すなら**、本文の「別の値を選んだら」から実装の Issue を立てて親 Issue のチェックリストに足し、
      確認の Issue はその番号を書いて閉じます。同じ引数で起動し直すと、足した Issue が名指しされます（台帳に足すかは利用者が決めます）。
- **開いたままの元の Issue**——`実機確認` の線で `Refs` のままマージした Issue です。実機で確かめてから閉じます。
- **起動時の点検の到達で止まると出た周**——PR が main と衝突している・同じプラグインの版を上げる PR が重なっている・
  マージの前の判断待ち・`マージ` の線が効かない、など。台帳の状態は `pr` のままで、上のどこにも出ないことがあるので、
  cruise は終えるときに点検を回し直して理由ごと渡します（[#490](https://github.com/hdknr/claude-code-setup/issues/490)）。

## 関連

- [プラグイン一覧 — dev-loop](index.md#dev-loop)
- [dev-loop の設計（ループ志向開発）](dev-loop-design.md)
- [リモートコントロールの設定手順（不在中の運用）](../usage/advanced-remote-control.md)
- [#389 オートクルーズ](https://github.com/hdknr/claude-code-setup/issues/389)（要件の出所と、部品への分け方）
