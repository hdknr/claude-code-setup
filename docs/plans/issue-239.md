# Issue #239 — test-tab-match.py を #201 の orca 共通手順に追従させる

## 1. 変更範囲

触る:

- `scripts/test-tab-match.py` — 偽 orca の `tab create` と、orca の呼び出し記録の分類
- `docs/plans/issue-239.md` — この計画ファイル

触らない:

- `plugins/orca/skills/orca/SKILL.md`（#201 でマージ済みの本体。テストが本体に合わせる）
- cmux 側のケース・偽 cmux（#201 は cmux を変えていない）
- 新しいケースの追加（`goto` 失敗のフォールバックなど。#201 の残課題の範囲）

**複製の数**: 期待する呼び出し列は `Tool.outcome` の 1 箇所。偽 orca の出力は `FAKE_ORCA` の 1 箇所。分けない。

## 2. デプロイ経路

反映経路なし（`scripts/` のテストだけ。公開サイトにもプラグインにも載らない。版は上げない）。

## 3. 受入基準

**J1. main の `test-tab-match.py` が緑に戻る**——orca・cmux の全ケースと、変異テストのすべてが期待どおり。

**J2. 判定が緩まない。** 分類は、本体が呼ぶべき呼び出し列と**完全一致**したときだけ `reuse`／`create` を返す。

| 経路 | 守り方 |
| --- | --- |
| 再利用（`goto` 成功） | `goto --page X` の直後が `tab switch --page X --focus --json` であること（`--focus` が無ければ unknown） |
| 新規作成 | `tab create` の直後が、偽 orca が返した id への `tab switch --page <id> --focus --json` であること |
| 変異テスト | 既存の変異が両スキルでまだ届き（壊す文字列が 1 回だけ現れる）、殺されること |
| CI | `plugins.yml` が `test-tab-match.py` を呼んでいる（変えない） |

**J3. 実環境を触らない**（偽 orca が PATH で先に解決される表明はそのまま）。

### 証明の手段

- J1〜J3: `python3 scripts/test-tab-match.py` と `check-all.py`。
- J2 の陽性対照: `--focus` を外した本体（一時コピー）で再利用ケースが unknown になることを当てる。

### 生成物

生成物なし（`check-all.py` で確かめる）。

## 4. 未解決

なし。

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/239-tab-match-focus`・worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-239`・
  起点 `53d06c3`・base 参照 `origin/main` → `53d06c35b1c94561dae32203f20adf57f03d43fa`
- 元の周: #201（PR #237）と #202（PR #238）。マージの組み合わせで main が赤になった（run 38484185853）
- 実装: 済。`test-tab-match.py` 全緑（orca 15/15・cmux 19/19・変異すべて死亡）、`check-all.py` 33/33 緑
- J2 の陽性対照: リポジトリの外の複製で本体の `--focus` を外すと orca 3/15 に落ちる（赤）。リポジトリの `git status` は意図した 2 ファイルだけ
- 交絡: 実験は陽性対照の 1 つだけ（上）
- 実装コミット: `fix(test): test-tab-match.py を …`（周の最初のコミット）
- 割り目（手順 4 の後）: AskUserQuestion で提案 → **「ここで割る」が選ばれた**（2026-10-14）
- 次: 関門 1 パス目（Verifier と `/code-review` の両方。どちらも未着手）。base は `53d06c35`

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `goto` 失敗から新規作成に落ちる経路（P4）のケースが無い | 足さない | この周は main を緑に戻すだけ。#201 の残課題の範囲 |

この周の起票: 0 件（#239 自体は main の赤への対処として人間の承認を得て起票）
