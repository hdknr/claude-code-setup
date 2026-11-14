# Issue #1028 — test-check-deps-declared の雛形の複製が git の自動メンテナンスの maintenance.lock と競合する

## 変更範囲

触る:

- `scripts/test-check-deps-declared.py` — 偽のリポジトリ（雛形）を作るときに自動メンテナンスを止める
- `docs/plans/issue-1028.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/check-deps-declared.py`（テストの対象。変えない）
- `plugins/` 全体（版は上げない）

## デプロイ経路

`scripts/` のテストだけ。反映経路なし。

## 受入基準

不変条件:

- I1: **偽のリポジトリ（雛形とその複製）で、コミットの後に git の自動メンテナンス（`git maintenance run --auto`）が走らない**——
  雛形を作った直後に `.git/objects/maintenance.lock` が現れず、並列の負荷のもとで雛形を作った直後に複製しても落ちない。
- I2: テストの判定は変わらない——契約のケースと変異の結果が直す前と同じ（`test-check-deps-declared.py` が緑）。
- I3: 実環境に触らない——設定は偽のリポジトリの `.git/config` にだけ書く（利用者の `~/.gitconfig`・実リポジトリは触らない）。

I1 を破りうる経路（偽のリポジトリでコミットする・git を走らせる入口）:

| 経路 | 守り方 |
| --- | --- |
| `repo()` の `commit`（雛形の base と計画のコミット） | `git init` の直後に雛形の `.git/config` へ `maintenance.auto=false`・`gc.auto=0` を書く |
| 複製した後の `put(..., commit=True)` のコミット | 設定は `.git/config` に在るので複製にも写る |
| 対象のスクリプト（`check-deps-declared.py`）が中で走らせる git | 読むだけの git（diff 等）。同じ設定が効く |
| 変異の作業者（別プロセス）が作る雛形 | 同じ `repo()` を通る |
| `repo()` を直接呼ぶケース（雛形を経ない） | 同じ `repo()` を通る |

検証の手段:

- 直す前: 雛形を作った直後に複製する形を並列 28 本 × 40 回（`repro1028.py`）——下に再現の結果。
- 直した後: 同じ形で失敗 0・直後の lock 0。
- 陽性対照: 同じ台本で直す前の版は落ちる（上の再現そのもの）。直した版で、設定を外した写しを当てると再び lock が出る。
- `check-all.py` で `test-check-deps-declared.py` が緑。

未証明: 並列の負荷は確率的なので「直した後に 0 回」は 1120 回の窓での 0 回で、起きないことの証明ではない。
ただし機構（自動メンテナンスが走らない）は、直後の lock の有無と設定の値で見る。

生成物: なし。

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1028-deps-test-maintenance-lock`、worktree `.claude/worktrees/issue-1028`、
  起点 `d5f1563`、base `origin/main` → `d5f1563c0e59f8b28a38d2e67e08bc0fc77a2ada`
- 直す線: 既定（`.claude/dev-loop.md` に宣言なし。#1024 の周で訊いたが回答なし——この周でも既定とする）
- 再現（直す前、git 2.56.0・macOS 28 コア）: 単独 100 回では複製の失敗 0・直後の lock 2 回。並列 28 本 × 40 回では
  1 回目 6 回・2 回目 19 回の失敗で、消えたファイルはどれも `maintenance.lock`（2 回目で理由を記録）
- 直した後: 並列 28 本 × 40 回を 2 回とも失敗 0・直後の lock 0。単独 300 回で直後の lock 0。`test-check-deps-declared.py` 単独で緑
- 陽性対照: 直す前の版（`git show d5f1563:` で写した版）を同じ単独 300 回に当てると直後の lock 27 回（同じ台本・同じ機械）
- 関連: #1034（#1024 の周で同じ欠陥を重複して起票し、#1028 の重複として閉じた）

## 既知の限界・決着済みの論点

（関門の指摘はここに 1 件 1 行で畳む）
