# platform-spec

spec-loop の基盤要件（`shared/infra.csv`）を、組織の開発ガイドのような**外部の設計パターン（profile）** とつなぐプラグインです（[#1312](https://github.com/hdknr/claude-code-setup/issues/1312)）。
profile の中身はパターンの持ち主のリポジトリ（非公開でもよい）に置いたまま写さず、案件の `infra.csv` の行が profile の行 ID を指します。

**spec-loop は platform-spec に依存しません**——置かなければ、今の `infra.csv` と `check-infra-csv.py` のまま動きます。
profile の読み方（手元の clone の探し方・タグの時点の読み出し・形式の版）は spec-loop の `scripts/external-profile.py` を読み込んで使います。

いまは基盤の層の形と、`infra.csv` の `profile の行` との照合（#1312 の段 1）と、profile の新しい版との差分から起票の候補を出す口（段 2。#1457——spec-loop の `scripts/profile-gate.py` がこれを proposal・scaffold の前の関門にします）までです。スキルはまだ持ちません。

## 中身

| 場所 | 何があるか |
| --- | --- |
| `references/infra-profile.md` | 基盤の層の表の形・受け付ける形式の版の範囲・案件の設定（`shared/platform/settings.csv`）・`profile の行` の書き方・照合・版の差分の決まり（原本） |
| `references/spec-loop.md` | spec-loop との境目・対応する spec-loop の版の範囲・spec-loop の見つけ方 |
| `scripts/check-infra-profile.py` | 案件の `infra.csv` の `profile の行` が、設定のタグの時点の基盤の層に在るかを照らす（読むだけ。標準ライブラリと `git`） |
| `scripts/check-profile-diff.py` | 設定のタグと profile の新しい版を比べ、`profile の行` が指す行のうち変わった・消えた・リンクの切れた行を起票の候補として出す（読むだけ。番号は振らない） |
