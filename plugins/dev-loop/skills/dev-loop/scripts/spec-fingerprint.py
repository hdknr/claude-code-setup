#!/usr/bin/env python3
"""spec-loop から来た Issue の、機能の指紋を手元の中間表現から出す（`references/spec-gap.md`）。

    python3 <このスキルの base ディレクトリ>/scripts/spec-fingerprint.py <spec_ir.json> <機能の id>

本文の先頭が `<!-- spec-loop-handoff: v3 -->` の Issue は、中間表現の**全体**ではなく
**その機能だけ**の指紋を持つ（#290）——全体の sha256 だと、同じ版の関係の無い機能を直しただけで
登録済みの Issue が全部不一致になる。

**式は spec-loop の `scaffold.py` の `fingerprint` の写しである**——dev-loop はプラグインの外を
相対パスで指せないので、ここに置く。**一致はこのリポジトリの `scripts/test-scaffold.py` が、
生成した本文の指紋とこのスクリプトの出力を突き合わせて見る**（片方だけ変えると落ちる）。

終了コード:

- 0: 指紋を 1 行出した
- 3: その機能が中間表現に無い（撤去の Issue は、作業中の版の全体でこれになるのが正しい）
- 2: 引数の誤り・ファイルが読めない・中間表現の形でない（**指紋を比べたことにしない**）
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def fingerprint(feature: dict) -> str:
    text = json.dumps(feature, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: spec-fingerprint.py <spec_ir.json> <機能の id>", file=sys.stderr)
        return 2
    path, feature_id = Path(argv[0]), argv[1]
    try:
        ir = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f"{path}: 読めない: {error}", file=sys.stderr)
        return 2
    features = ir.get("features") if isinstance(ir, dict) else None
    if not isinstance(features, list):
        print(f"{path}: features の一覧が無い（中間表現の形でない）", file=sys.stderr)
        return 2
    found = [f for f in features if isinstance(f, dict) and f.get("id") == feature_id]
    if not found:
        print(f"{path}: 機能 {feature_id} が無い", file=sys.stderr)
        return 3
    if len(found) > 1:
        print(f"{path}: 機能 {feature_id} が {len(found)} 件ある（中間表現の形でない）", file=sys.stderr)
        return 2
    print(fingerprint(found[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
