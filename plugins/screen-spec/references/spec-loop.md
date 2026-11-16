# spec-loop との境目

screen-spec は spec-loop の決まりに従い、spec-loop は screen-spec に依存しない（#1081 の「spec-loop との境目」）。

screen-spec が従う spec-loop の決まり: Q&A 表の列と番号の形・ツリーと図の決まり・版の重ね合わせ（行の単位で重ねる表を含む）・未決定の印・文体。
**決まりを写さず、spec-loop のスクリプトを読み込んで使う**——重ね方は `merge-versions.py`、Q&A の番号の形は `check-qa-csv.py`、未決定の印は `check-spec-exit.py`。

## 対応する spec-loop の版

| 下限（この版を含む） | 上限（この版を含まない） |
| --- | --- |
| `0.93.0` | `1.0.0` |

- 下限は、画面の表を行の単位で重ねる重ね方（#1091）が入った版である。
- 上限は spec-loop が安定版（1.0.0）を宣言するまでとする。spec-loop は 0.x のあいだ壊れる変更も minor で上げるが、決まりが変わって食い違えば、
  このプラグインを置いているリポジトリのテスト（test-check-screens.py）が本物の spec-loop で検査を走らせるので CI で分かる。範囲の値は確認の Issue で利用者に確かめる。
- `scripts/check-screens.py` は、検査の前に spec-loop の `.claude-plugin/plugin.json` の `version` を比べ、範囲の外なら何も検査せずに止める（4）。

## spec-loop の見つけ方

`scripts/check-screens.py` は次の順に探し、最初に見つけたものを使う。

1. 引数 `--spec-loop <spec-loop のプラグインの根>`
2. 環境変数 `SCREEN_SPEC_SPEC_LOOP`
3. リポジトリの形——screen-spec のプラグインの根の隣の `spec-loop`（このリポジトリの `plugins/spec-loop/`）
4. プラグインのキャッシュの形——Claude Code の設定のディレクトリ（`CLAUDE_CONFIG_DIR`、無ければ `~/.claude`）の `plugins/installed_plugins.json` の、
   screen-spec と同じマーケットプレイスの `spec-loop@<マーケットプレイス>` の `installPath`（読み込まれている版を名指しする記録）

- どれも見つからなければ止める（4）。プラグインの根は、`.claude-plugin/plugin.json` の `name` が `spec-loop` のディレクトリである（違えば見つからないと同じ）。
- 1・2 で名指ししたものが spec-loop でなければ、3・4 へは進まずに止める（名指しを黙って別のものに替えない）。

## Q&A の番号を振らない

番号は起票したループの印ごとに振る（spec-loop の Q&A 表の「番号の振り方」）ので、ループの外で振ると並行して動くループと番号がぶつかる。
screen-spec の検査は起票の候補を出すだけにし、番号は req-loop・spec-review が振る（`references/tables.md` の「検査」）。
