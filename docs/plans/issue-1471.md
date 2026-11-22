# Issue #1471 — external-profile.py: CLAUDE.md の行の ~/… をホームに展開する

**不在の周**（`/dev-loop:cruise 1461 --absent` の起動・2026-11-22T03:12Z）。利用者には訊かない。親（cruise #1461）から委譲文で受けた子。
Issue #1471 は #1455 の周の途中の課題（`<!-- cruise-found: #1461 -->`）として親が起票したもの。

確かめた線（出所: cruise の確かめた線（台帳 `issue-1461`）。利用者の確認 2026-11-22T03:12:23Z・03:19:55Z）:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
子はマージしない（親の委譲文）。台帳は書かない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1461`））。
版の上げ方: `spec-loop` を **patch**（0.132.0 → 0.132.1。探し方の入口の食い違いを直す不具合の修正）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/external-profile.py` — `find_clone` で `CLAUDE.md` の行のパスを `expanduser()` してから相対かを見る。docstring の「守る」に 1 行
- `plugins/spec-loop/references/external-profile.md` — 「探し方」の 3 に `~` の展開を書く（決まりの原本）
- `scripts/test-external-profile.py` — `~/` の試料と、「守る」に対応する変異 1 件
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1471.md` — この計画

触らない:

- 引数 `--clone`・環境変数 `SPEC_PROFILE_CLONE` の扱い（もともと `_named` で `expanduser()` している）
- `$HOME` など環境変数の展開（`expandvars`）——Issue は `~` だけを求めている。引数・環境変数側もしていない
- platform-spec・screen-spec（まだこのスクリプトを読み込んでいない）

依存の追加・更新: なし
仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）

同じことを述べている箇所の数: 2（本体の docstring の「守る」と、決まりの原本 `references/external-profile.md` の「探し方」）。テストの試料と変異は検査側。
分けない理由: 原本が決まり、docstring は何を守るかの表で、テストが docstring の行数と変異の数を突き合わせる——どちらかだけ直すと片方が古くなるので同じ周で直す。

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json` の版）と GitHub Pages（`docs/` の計画ファイル）。`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`。子はマージしない。

## 受入基準

不変条件 × 破りうる経路（入口は `find_clone` の 3 つの探し方と、読み込んで使う関数 `find_clone` の直接呼び出し）:

| # | 不変条件 | 経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| 1 | `CLAUDE.md` の行 `外部の profile の clone: <リポジトリ> ~/…` の `~` はホームに展開され、展開した先が git のリポジトリの根なら 0 で、その clone を返す | CLI `find`・`check`・`diff`（どれも `find_clone` を通る）・読み込んだ側の `find_clone(repo, project=…)` | `find_clone` で `Path(hits[0]).expanduser()`。テストの試料「行（~/）」と、直す前の本体で 4・直した後で 0 の再現（`--project` に `~/prof` の行） |
| 2 | 行の `~/…` は、引数 `--clone ~/…`・環境変数 `SPEC_PROFILE_CLONE=~/…` と同じ clone を指す（探し方の入口の間で食い違わない） | 3 つの探し方 | テストの試料「引数（~/）」「環境変数（~/）」と「行（~/）」が同じパスを返す |
| 3 | 行の `~/…` が git のリポジトリでなければ、今までどおり次の探し方に落ちずに 4 で、メッセージは展開した先を名指す（`<案件>/~/…` を名指さない） | 行の探し方 | テストの試料「行（~/ が git でない）」 |
| 4 | 既存の振る舞い（相対パスは案件の根から・絶対パス・全角のコロン・ほかのリポジトリの行・2 行・フェンス・引数と環境変数の優先）を変えない | 既存の試料 | 既存のテストが全部緑（変異テストを含む）。`~` で始まらない値は `expanduser()` で変わらない |
| 5 | docstring の「守る」の行数と変異の数が 1 対 1（新しい「守る」の行に変異が 1 つあり、殺せる） | テスト | `本体の「守る」45 行に対して変異が 45 件`・`変異を殺せる: 行の ~ をホームに展開しない` |
| 6 | 決まりの原本（`references/external-profile.md` の「探し方」）が `~` の展開を書き、本体の振る舞いと食い違わない | 原本 | 原本の 3 の文と本体の docstring を読み比べる |
| 7 | 版が 3 種類（`marketplace.json`・`plugin.json`・各 `SKILL.md` の 2 行）で揃って上がっている | 版 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| 8 | 歯止めを全部回して緑（`check-all.py`） | 全体 | `run-serial.py` 越しの `check-all.py` |

必須要件の掛け算: 受入基準を両方の関門（Verifier・`/code-review`）に × 2 パス（1 パス目・2 パス目。1 パス目の指摘対応が 0 行なら 2 パス目は該当なし）= 4 つの受け渡し。2 パス目で直した行があれば狭いパスにも受入基準をまるごと渡す。

証明できないもの（未証明）: なし——どれも一時ディレクトリの本物の git リポジトリで走らせて確かめられる。
`~<名前>`（ほかの利用者のホーム）の展開は Python の `Path.expanduser()` の振る舞いに任せ、テストでは試さない（利用者の実ホームを読むことになる）——受入基準には入れていない。

生成物: なし（このスクリプトと原本は生成物を持たない。`SKILL.md` の測定値（設計 §8.2）は spec-loop の `SKILL.md` を測らない——版の行だけ変えるので `skill-metrics.py --check` で確かめる）。
プロパティテスト: なし（`~` の展開は入力の空間が広い不変条件ではない——`~` で始まるか否かの 2 通りで、例の試料で覆える）
差分テスト: なし（振る舞いを変えない周ではない——行の `~` の扱いを変える修正）

## 未解決の判断・確認待ち

- 仕様の穴: なし（Issue に「穴でない」とあり、引数・環境変数と揃える直しで利用者の答えに依らない——自分でも確かめた）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1471-profile-clone-tilde`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1471`・
  起点 `b37059d0`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `b37059d0d0f6ff317fddadfd2cd866eab10e5cd9`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: まだ
- 交絡を潰した手順: 直す前の本体（`git show b37059d0:…`）と直した後の本体を、同じ一時 HOME・同じ `CLAUDE.md`（`外部の profile の clone: o/r ~/prof`）で走らせ、前は 4（`<案件>/~/prof は git のリポジトリ（の根）でない`）・後は 0（`<HOME>/prof`）。陽性対照は引数 `--clone ~/prof` が同じ HOME で 0

```dev-loop-gates
周の base: b37059d0d0f6ff317fddadfd2cd866eab10e5cd9
```

## 既知の限界・決着済みの論点

- `$HOME` などの環境変数の展開はしない（決着: 採らない。理由: Issue は `~` だけを求め、引数・環境変数の側も `expandvars` をしていない——入口の間で揃えるのが目的）。
- `~<名前>` はテストしない（決着: 採らない。理由: 試すと利用者の実ホームを読む。展開は `Path.expanduser()` が引数・環境変数と同じ形でする）。
- `~` を展開できない環境（HOME も passwd も無い）では `Path.expanduser()` が `RuntimeError` を投げ、本体の想定外の例外として 4 になる（決着: 採る。引数・環境変数の側と同じ）。

## 手順 8 の記録

- この周の起票: 0 件（確認の Issue も周の途中の課題の起票も無い）
