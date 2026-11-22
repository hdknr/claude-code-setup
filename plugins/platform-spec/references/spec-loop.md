# spec-loop との境目

platform-spec は spec-loop の決まりに従い、spec-loop は platform-spec に依存しない（#1312 の「提案」）。
platform-spec を置かない案件では、spec-loop は今の `infra.csv` と `check-infra-csv.py` のまま動く。

platform-spec が従う spec-loop の決まり: 版の重ね合わせ・基盤要件の表（`shared/infra.csv`）の列・外部の profile の置き場所と読み方（探し方・タグの時点の読み出し・形式の版の比べ方）。
**決まりを写さず、spec-loop のスクリプトを読み込んで使う**——重ね方は `merge-versions.py`、任意の列の名前は `check-infra-csv.py` の `PROFILE_COLUMN`、外部の profile は `external-profile.py`。

## 対応する spec-loop の版

| 下限（この版を含む） | 上限（この版を含まない） |
| --- | --- |
| `0.133.0` | `1.0.0` |

- 下限は、`check-infra-csv.py` が末尾の任意の列 `profile の行` を受ける（`PROFILE_COLUMN` を持つ）版である（#1456）。外部の profile の読み方（`external-profile.py`）はその前の版（#1455）から在る。
- 上限は spec-loop が安定版（1.0.0）を宣言するまでとする（screen-spec と同じ）。
- `scripts/check-infra-profile.py` は、照らす前に spec-loop の `.claude-plugin/plugin.json` の `version` を比べ、範囲の外なら何も照らさずに止める（4）。

## spec-loop の見つけ方

`scripts/check-infra-profile.py` は次の順に探し、最初に見つけたものを使う（screen-spec の見つけ方と同じ順）。

1. 引数 `--spec-loop <spec-loop のプラグインの根>`
2. 環境変数 `PLATFORM_SPEC_SPEC_LOOP`
3. リポジトリの形——platform-spec のプラグインの根の隣の `spec-loop`（このリポジトリの `plugins/spec-loop/`）
4. プラグインのキャッシュの形——Claude Code の設定のディレクトリ（`CLAUDE_CONFIG_DIR`、無ければ `~/.claude`）の `plugins/installed_plugins.json` の、
   platform-spec と同じマーケットプレイスの `spec-loop@<マーケットプレイス>` の `installPath`

- どれも見つからなければ止める（4）。プラグインの根は、`.claude-plugin/plugin.json` の `name` が `spec-loop` のディレクトリである。
- 1・2 で名指ししたものが spec-loop でなければ、3・4 へは進まずに止める（名指しを黙って別のものに替えない）。
