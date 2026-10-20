# Issue #293: spec-loop — init-mkdocs.py がハードリンクを使えないファイルシステムで何も写せない

元の周: #266（PR #292）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/init-mkdocs.py` — `place()` に、リンクが使えないときの退路
- `scripts/test-init-mkdocs.py` — リンクが使えない状況の試料と変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 0.10.1
- `.claude-plugin/marketplace.json` — spec-loop 0.10.1
- `plugins/spec-loop/skills/*/SKILL.md` — 版のバナー（5 本。中身は変えない）
- `docs/plans/issue-293.md` — この計画

触らない:

- フック（`templates/mkdocs/hooks/`）・`references/tree.md`・README・CLAUDE.md——書き込みの仕方は `init-mkdocs.py` の docstring にだけ書いてある（tree.md は「在るファイルは変えない」までで、書き方を述べていない）
- #292 の狭いパスの F2〜F4・FN（PR #292 の残課題。人間が起票しないと決めた）

**周の大きさ（同じことを述べている箇所）**: 書き込みの保証は `init-mkdocs.py` のモジュールの docstring・`place()` の docstring・
`test-init-mkdocs.py` の docstring の **3 箇所**。**分けない**: 1 つの関数の退路で、3 箇所はどれも同じ関数の説明。

## 決めたこと

1. `os.link` が `FileExistsError` 以外の `OSError` で失敗し、その errno が「リンクを作れない」側（`EPERM`・`ENOTSUP`／`EOPNOTSUPP`・`EXDEV`・`EMLINK`・`ENOSYS`）なら、
   **`dest` を排他的に作って（`open(dest, "xb")`）直に書く**。行き先が在れば `FileExistsError` で False（排他は保つ）。
2. 退路で途中で書けなかったら、**自分が作った `dest` を消してから**例外を上げる（自分が排他的に作ったファイルなので、消しても他人のファイルは消えない）。
   これで「切れたファイルを残さない」も退路で保つ。**ただしプロセスが殺された（SIGKILL・電源断）ときと、消すのにも失敗したときは切れたファイルが残りうる**——リンクの経路には無い弱さで、docstring に書く。
   **消せなかったときはそう出力し、上げるのは書けなかった理由のほう**（1 パス目の CR4 で追加）。
3. 上の errno に当たらない `OSError`（`EACCES`・`ENOSPC` など）はこれまでどおり例外（終了コード 2）。

## verify の受入基準

不変条件 × それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方 | 確かめ方 |
| --- | --- | --- | --- | --- |
| A | リンクが使えなくても雛形をすべて写し、終了コード 0 | `os.link` が `ENOTSUP`／`EPERM`／`EXDEV` で失敗（FAT32・exFAT・一部のネットワークファイルシステム） | 退路で `open("xb")` | テスト（`os.link` を差し替えて走らせる）＋**実機: FAT32 のディスクイメージ**（`hdiutil`。macOS のみ） |
| B | 既にあるファイルを 1 つも書き換えない（#266 の A をそのまま） | 退路で行き先が在る（通常のファイル・壊れたリンク）／確かめた後に作られる | 退路も `xb` | テスト（退路の試料＋変異）。バイト一致 |
| C | 途中で書けなくても切れたファイルを残さず、直して再実行すれば残りが写る（#266 の R1 をそのまま） | リンクの経路での失敗（既存）／**退路での失敗** | リンクの経路: 一時ファイル。退路: 自分が作った `dest` を消す | テスト（ファイルの大きさの上限 × リンクの差し替え） |
| D | リンクを作れないのと関係ない失敗は、これまでどおり 2 で止まる | `EACCES` など | errno で分ける | テスト（`os.link` が `EACCES` を出す） |
| E | 写したファイルの権限は素の open と同じ（umask に従う） | リンクの経路・退路 | 退路は素の open なので umask どおり | 実機の FAT32 では権限が意味を持たないので、テストで退路の権限を見る |
| F | 版（3 種）を上げ、歯止めが全部緑 | 版の据え置き | — | `check-all.py`・PR の `gh pr checks` |

掛け算: 受入基準を Verifier と `/code-review` の両方 × 1 パス目・2 パス目（4 つの受け渡し）。

**この環境では証明できないもの（未証明）**:

- macOS 以外の OS、および FAT32・exFAT 以外のファイルシステム（SMB・NFS など）で `os.link` がどの errno を返すか——手元で測れるのは macOS の `hdiutil` の FAT32・exFAT だけ（どちらも `ENOTSUP`）。
  Linux の vfat は **1 カーネルだけ実機で測った**（2 パス目。OrbStack の VM・`7.0.14`・コンテナで FAT32 をループマウント）——`link` は `EPERM`・`chmod` はエラーにならず権限が変わらない・
  修正後は rc=0 で 6 ファイル、修正前は `Operation not permitted` で rc=2（root と、`uid=1000` でマウントした非 root の両方）。**他のカーネル版は測っていない**。**Windows（`EINVAL` になると関門が指摘）は `NO_LINK` に入れていない**——残課題
- SIGKILL・電源断で退路の書き込みが切れたとき（決めたことの 2）——プロセスを殺す実験はできるが、殺す瞬間を書き込みの途中に合わせられない
- 実際に消すのに失敗する状況（抜かれた・読み取り専用になった媒体）——`Path.unlink` の差し替えで当てるだけ

**生成物**: このリポジトリで再生成するものは**該当なし**（図・`skill-metrics.py` の対象〔dev-loop の `SKILL.md`〕を触らない。`check-all.py` が `--check` を回す）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/293-link-fallback`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-293`・
  起点 `e024b98`・base は `origin/main`（`refs/remotes/origin/HEAD`）の merge-base `e024b980f093851d15c4e0ba574ff4ba08fc1043`
- 実装: `07aca86` で完了（手順 4）。`check-all.py` 44/44 緑。次は手順 5（Verifier 1 パス目）と `/code-review` 1 パス目。`test-init-mkdocs.py` 試料 30 件・変異 45 件 OK（足した変異 6 本はどれも「試料が False を返した」で死ぬ——
  例外で死ぬのは既存の「短い行を埋めない」「読めない表で落ちる」の 2 本だけで、どちらも旧い挙動そのもの）
- 割り目（手順 4）: 訊いた → **「ここで割る」**（2026-10-20）。再開は worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-293` の中で `/clear` → `/dev-loop:dev-loop 293`（手順 5 から）
- 再開（2026-10-20）: 肯定的な確認一致（ブランチ・`7a63413`・base は祖先）。1 パス目: **Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件**（注意 W1・M1、未証明の分類に 1 件）・**`/code-review`（high）指摘 7 件**。採否は下の表。
  直す 2 件（CR1・CR4）を対応: `test-init-mkdocs.py` 試料 32 件・変異 48 件 OK。差し戻しあり（手順 4 へ 1 回）
- 実機の exFAT（Verifier の分類の指摘を受けて）: `hdiutil create -fs ExFAT`・5MB・macOS。修正後 rc=0・6 ファイルがバイト一致・再実行は 0 で何も写さない・一時ファイルの残り 0。
  **陽性対照**: 修正前（`e024b98` のプラグインを外へ書き出して）は `Operation not supported` で rc=2。観測窓: 1 環境・各 1 回
- 1 パス目の指摘対応は `6764a13` でコミット（`check-all.py` 44/44 緑）
- 次: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` の 2 パス目（どちらも未）。base は同じ `e024b980…`
- 割り目（手順 6・2 パス目の前）: 訊いた → **「ここで割る」**（2026-10-20）。再開は worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-293` の中で `/clear` → `/dev-loop:dev-loop 293`（Verifier 2 パス目と `/code-review` 2 パス目から。2 パス目の指摘対応を始める前に、その時点の HEAD を狭いパスの起点としてここに書く）
- 再開（2026-10-20・2 回目）: 肯定的な確認一致（ブランチ・`8dbf50e`・base は祖先）。2 パス目: **Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件**・**`/code-review`（high）指摘 6 件**（コマンドはガードに拒否されて読解のみ）。採否は下の表
- **狭いパスの起点: `8dbf50e`**（2 パス目の指摘対応を始める直前の HEAD）
- 2 パス目の指摘対応: P2-3 を `10d3dc5` で直した（直す 1 件・残課題 6 件）
- 狭いパス: **Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件**。Verifier が設計した変異 4 本のうち赤 2・素通り 2
  （`chmod` を `0o644` に固定——umask 022 に固定したので等価変異。陽性対照も Verifier が示した。退路の open の権限の変異はガードの拒否で当てられなかった）。指摘は直さず人間に渡す
- 関門はここで打ち切り（2 パス＋狭いパス）。`check-all.py` 44/44 緑（`10d3dc5` の上で）
- この周の起票: 0 件
- 交絡: 実装中に 2 つ実験した
  - **退路で切れる試料が退路まで届いていなかった**——最初の書き方では、最初のリンクの失敗で大きさの上限を掛けたため、次のファイルの
    **一時ファイルが先に切れて**、退路の書き込みに届かずに 2 で終わっていた（「退路で切れたファイルを残す」の変異が素通りして分かった）。
    512 バイトを超えるファイルでだけ上限を掛けるように直し、**同じ変異で 512 バイトの切れたファイルが残ることを見た**（陽性対照）
  - **実機の FAT32**（`hdiutil create -fs MS-DOS`・5MB・macOS）: 修正後の版で rc=0・6 ファイルが雛形とバイト一致・再実行は「何も写さない」で 0。
    **陽性対照**: 同じイメージで修正前の版（`e024b98`）は `Operation not supported` で rc=2。
    写した先に `._*` が出るが、**素の `open` だけで書いても同じく出る**（別のイメージで対照を取った）ので macOS の AppleDouble で、
    一時ファイル（`.<名前>.xxxx`）の残りは 0 件。観測窓: この 1 環境・各 1 回

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| リンクを使わず最初から `open("xb")` に戻すか | 採らなかった | #266 の R1（切れたファイルが残って再実行で直らない）が戻る。リンクの経路はプロセスが殺されても切れたファイルを残さない |
| 退路を errno で絞るか、`FileExistsError` 以外の全 `OSError` で退路に入るか | 絞る | 権限や容量の不足で退路に入ると、同じ失敗をもう 1 度起こすだけで、失敗の理由が分かりにくくなる |

### 1 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1 | `NO_LINK` の `EPERM`（Linux の vfat）がどのテストにも当たらない | 示せる——`/code-review` が外の複製で `EPERM` を外して 30 件とも緑 | A | 直す（試料「EPERM でも退路に入る」と変異） |
| CR2・V-W1 | Windows の FAT32 では `EINVAL` になり退路に入らない | 示せない（Windows が無い） | 無し（A の経路は ENOTSUP／EPERM／EXDEV） | 残課題 |
| CR3 | 退路では一時ファイルが残ったまま直に書くので、一時的に 2 倍の容量を使う | 示せない（空きが 1〜2 倍の媒体を作っていない） | 無し | 残課題 |
| CR4・V-M1 | 退路で消すのにも失敗すると、切れたファイルが残り、消せなかった理由のほうが出る（docstring の「殺されたときだけ」が偽） | 示せる——`Path.unlink` を EROFS にした外の probe で `raised: EROFS(unlink)`・`left: True 10` | C | 直す（そう出力し、書けなかった理由で 2。docstring 2 箇所を直す。試料と変異 2 本） |
| CR5 | `dest.unlink(missing_ok=True)` の変異が素通り | 示せる | 無し（挙動が変わらない） | 残課題 |
| CR6 | リンクを作れないと分かっても、ファイルごとに一時ファイルを作り直す | 示せない（遅さを測っていない） | 無し | 残課題 |
| CR7 | `others = [rel for rel in template_map(plugin)]` は `list(...)` でよい | — | 無し | 残課題 |
| V-分類 | exFAT は `hdiutil` で作れるのに「未証明」に入っている | 示せる（計画の記述どおり） | 無し（計画の分類） | 測った（上の実機の exFAT）。未証明の記述を直した |
| V-D | `ENOSPC`・`EINVAL` を実の `place()` に通していない | — | D | 対応不要（`/code-review` が `EINVAL`・`EIO` で rc=2 を確かめた） |

### 2 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| P2-1 | Linux の vfat では `os.link` の前の `os.chmod` が `EPERM` で落ち、退路に届かない | **示せない**——実機（Linux 7.0.14 の vfat・root と非 root）で `chmod 0644` は成功し、修正後は rc=0。古いカーネルは測っていない | A | 残課題（このカーネルでは反証された） |
| P2-2 | 退路で書けず、`dest` も一時ファイルも消せない（読み取り専用になった媒体）と、`finally` の `os.unlink(tmp)` の `EROFS` が書けなかった理由を置き換え、一時ファイルも残る——「書けなかった理由のほうを上げる」が偽 | 示せる——外の probe（`os.unlink` と `Path.unlink` を EROFS・書き込みを EIO）で `raised: EROFS`（EIO は `__context__`）・`.a.txt.xxxx` が残る | 無し（A〜F はどの理由を上げるかを決めていない。切れた `dest` が残ることは出力される） | 残課題 |
| P2-3 | umask 077 では、権限を直さない変異が生き残って `test-init-mkdocs.py` が赤になる（E の検査も空振りする） | 示せる——`umask 077` で rc=1・「変異が生き残った: 一時ファイルの権限を直さない」 | E・F | **直す**（テストの `main` で umask を 022 に固定。修正後は umask 077 でも OK） |
| P2-4 | `os.link` の前に fsync しないので、電源断ではリンクの経路でも切れた `dest` が残りうる（docstring の「リンクの経路には無い弱さ」が電源断について偽） | 示せない（電源断を起こしていない） | 無し | 残課題 |
| P2-5 | `dest.open("xb")` と `try` の間の `KeyboardInterrupt` で空の `dest` が残る | 示せない（窓に割り込みを合わせていない） | 無し | 残課題 |
| P2-6 | `NO_LINK` の `EPERM` は「権限の不足は含めない」というコメントと食い違う（TCC・追記専用のディレクトリの拒否も退路に入る）。`EXDEV`・`EMLINK` は同じディレクトリでは起きない | 示せない（拒否の結果がどう変わるかを示していない） | 無し | 残課題 |
| P2-7 | `run_init_no_link` が `run_init` の呼び出しを写している | — | 無し | 残課題 |
