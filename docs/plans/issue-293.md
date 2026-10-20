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
   これで「切れたファイルを残さない」も退路で保つ。**ただしプロセスが殺された（SIGKILL・電源断）ときは切れたファイルが残りうる**——リンクの経路には無い弱さで、docstring に書く。
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

- FAT32 以外のファイルシステム（exFAT・SMB・NFS など）で `os.link` がどの errno を返すか——手元で作れるのは `hdiutil` の FAT32（と exFAT）だけ。errno の一覧は Python・OS の文書からの推定
- SIGKILL・電源断で退路の書き込みが切れたとき（決めたことの 2）——プロセスを殺す実験はできるが、殺す瞬間を書き込みの途中に合わせられない

**生成物**: このリポジトリで再生成するものは**該当なし**（図・`skill-metrics.py` の対象〔dev-loop の `SKILL.md`〕を触らない。`check-all.py` が `--check` を回す）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/293-link-fallback`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-293`・
  起点 `e024b98`・base は `origin/main`（`refs/remotes/origin/HEAD`）の merge-base `e024b980f093851d15c4e0ba574ff4ba08fc1043`
- 実装: `07aca86` で完了（手順 4）。`check-all.py` 44/44 緑。次は手順 5（Verifier 1 パス目）と `/code-review` 1 パス目。`test-init-mkdocs.py` 試料 30 件・変異 45 件 OK（足した変異 6 本はどれも「試料が False を返した」で死ぬ——
  例外で死ぬのは既存の「短い行を埋めない」「読めない表で落ちる」の 2 本だけで、どちらも旧い挙動そのもの）
- 割り目（手順 4）: 訊いた → **「ここで割る」**（2026-10-20）。再開は worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-293` の中で `/clear` → `/dev-loop:dev-loop 293`（手順 5 から）
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
