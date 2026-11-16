#!/usr/bin/env python3
"""`check-screens.py`（screen-spec の画面・項目・遷移の表と散文の仕様書の検査。#1092）の回帰テスト。

    python3 scripts/test-check-screens.py

**本体はプラグインの中にある**（`plugins/screen-spec/scripts/`）。spec-loop のスクリプトを読み込むので、
一時ディレクトリに `plugins/screen-spec/`（本体）と `plugins/spec-loop/`（本物の spec-loop の `.claude-plugin/` と `scripts/` の写し）を並べて走らせる。

見るもの:

1. **#1092 の受入基準の陽性対照**——1 つずつ崩した正本で検査が非 0 で止まる: 表に無い画面を指す遷移・入口から辿れない画面・遷移の無いボタン・
   Q&A 表に無い根拠の番号・N/A の理由が無い節・`features.csv` に無い機能と `roles.csv` に無い操作・表に残った `未定`（`⚠️` だけは警告）・
   対応の範囲の外の spec-loop の版（起動のときに 4 で止まる）。
2. **陰性対照**——正しく書いた小さな例（v1 だけ・v2 で行を足した例・タブ・内部の Q&A）で 0。
3. **検査が Q&A の番号を振らない**——どの試料でも、実行の前後で正本のファイルのバイトが変わらず、出力の Q&A の番号はどれも正本に書いてある。
4. **ほかの検査**（表どうし・形・散文・重ね合わせ・spec-loop の見つけ方・引数と読めない入力の 2・`-OO`）。
5. **本体の定数が `plugins/screen-spec/references/` の原本と一致する**（写しのずれ。崩すと落ちることも見る）。
   profile の定数は `references/profiles.md` と、profile の名前は `profiles/` のディレクトリと突き合わせ、各項目を誰が決めるかが書いてあることも見る（#1094）。
7. **#1094 の受入基準**——profile が `web-spa` で `## 実現方式: web-spa` の節が無い仕様書を止める（1）・profile が `未設定` なら profile の節と列を求めない（0）・
   方式が未定で `N/A。実現方式が未定` と書いた節（とセル）を通す（0。未決定にも起票の候補にもしない）。profile の列と節のほかの検査も当てる。
6. **リポジトリの外で単体で動く**——プラグインを一時ディレクトリに写し、`python3 -I` で走らせる。プラグインのキャッシュの形
   （`installed_plugins.json` が名指しする spec-loop）も一時の設定のディレクトリに作って当てる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME` を一時ディレクトリにし、`CLAUDE_CONFIG_DIR`・`SCREEN_SPEC_SPEC_LOOP` を外す
（試料が名指すときだけ一時ディレクトリの値を渡す）。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "screen-spec"
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
TARGET = "check-screens.py"
REFS = PLUGIN / "references"

S = "v1/requirements/screens/data/screens.csv"
I = "v1/requirements/screens/data/screen-items.csv"
T = "v1/requirements/screens/data/transitions.csv"
QA = "v1/shared/qa.csv"
QA_DEV = "v1/spec/qa-dev.csv"
FEATURES = "v1/requirements/features.csv"
ROLES = "v1/requirements/roles.csv"
LIST_MD = "v1/requirements/screens/order-list.md"
NEW_MD = "v1/requirements/screens/order-new.md"

QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
S_HEAD = "画面ID,画面名,種別,親画面,主たる利用者,ステータス,参考資料,目的と背景,できること,機能,帳票,仕様書,根拠\n"
I_HEAD = "番号,画面ID,まとまり,並び順,項目名,種類,中身,例,必須,入力チェック,エラーメッセージ,並び替え,絞り込み,根拠\n"
T_HEAD = "番号,遷移元,きっかけ,操作,条件,遷移先,結果,根拠\n"

S1 = "S-001,受注一覧,top,,担当者,記入中,,受注を探す,一覧と絞り込み,F-001,,order-list.md,Q-R-002\n"
S2 = "S-002,受注登録,form,,担当者,記入中,,受注を入れる,入力,F-002,,order-new.md,F-002\n"
I1 = "I-001,S-001,一覧,1,受注日,一覧の列,受注した日,2026/11/16,,,,はい,いいえ,Q-R-002\n"
I2 = "I-002,S-001,操作,2,新規,ボタン,,,,,,,,F-002\n"
I3 = "I-003,S-002,入力,1,顧客名,入力,顧客の名前,山田,はい,30 文字まで,30 文字までで入れてください,,,F-002\n"
I4 = "I-004,S-002,操作,2,保存,ボタン,,,,,,,,F-002\n"
T1 = "T-001,S-001,I-002,受注の登録,,S-002,,F-002\n"
T2 = "T-002,S-002,I-004,受注の登録,入力チェックが通ったとき,S-001,保存した,F-002\n"

SECTIONS = [("1. 基本情報", True), ("2. 画面概要", True), ("3. レイアウト", True), ("4. データ表示", True),
            ("5. 操作とアクション", True), ("6. 入力とバリデーション", True), ("7. 状態", False),
            ("8. 権限とデータの見える範囲", True), ("9. 他システム連携", False), ("10. 同時編集", False),
            ("11. 表示ルール", False), ("12. 一覧・表の能力", True), ("13. 画面遷移", True), ("未決の論点", False)]
MARK = "<!-- screen-spec: 表 -->"


def doc(key: str, name: str, bodies: dict[str, str] | None = None, order: list[str] | None = None, title: str | None = None) -> str:
    bodies = bodies or {}
    out = [title if title is not None else f"# {key} {name}", ""]
    for heading, tabled in SECTIONS if order is None else [(h, dict(SECTIONS)[h]) for h in order]:
        out += [f"## {heading}", "", bodies.get(heading, MARK if tabled else "N/A。この画面には無い"), ""]
    return "\n".join(out)


def qa_row(number: str, source: str, answer: str, target: str, state: str) -> str:
    return f"{number},{source},質問 {number},A: はい / B: いいえ,A,理由,{answer},{target},{state},\n"


def base() -> dict[str, object]:
    return {
        QA: QA_HEAD + qa_row("Q-R-001", "要求確定", "A（業務部が確認）", "requirements/screens/data/screen-items.csv", "反映済み")
        + qa_row("Q-R-002", "要求確定", "未回答", "—", "確認中")
        + qa_row("Q-R-003", "要求確定", "B（業務部 2026-11-10）", "—", "確認中"),
        QA_DEV: QA_HEAD + qa_row("D-S-001", "仕様レビュー", "未回答", "—", "確認中"),
        FEATURES: "id,名前,種類,関係\nF-001,受注一覧,画面,\nF-002,受注登録,画面,\n",
        ROLES: "操作,管理者,担当者\n受注の登録,可,可\n",
        S: S_HEAD + S1 + S2,
        I: I_HEAD + I1 + I2 + I3 + I4,
        T: T_HEAD + T1 + T2,
        LIST_MD: doc("S-001", "受注一覧"),
        NEW_MD: doc("S-002", "受注登録"),
    }


def good(**changes) -> dict[str, object]:
    files = base()
    for key, value in changes.items():
        path = {"S": S, "I": I, "T": T, "QA": QA, "FEATURES": FEATURES, "ROLES": ROLES, "LIST_MD": LIST_MD, "NEW_MD": NEW_MD}[key]
        if value is None:
            files.pop(path)
        else:
            files[path] = value
    return files


def with_files(files: dict[str, object], **extra: object) -> dict[str, object]:
    merged = dict(files)
    merged.update(extra)
    return merged


# ---- profile（#1094）
SETTINGS_CSV = "v1/requirements/screens/settings.csv"
COMMON_MD = "v1/requirements/screens/common.md"
WEB_SPA = "項目,値\n画面IDの接頭辞,S-\nprofile,web-spa\n"
UNSET_SETTINGS = "項目,値\n画面IDの接頭辞,S-\nprofile,未設定\n"
SUBSECTIONS = ["ディープリンク・別タブ", "戻る・進む・再読み込み", "ダイアログの実体", "一覧の送り方", "ファイル出力・印刷", "認証と権限の外れ"]
COMMON_SUBSECTIONS = ["アプリの外枠", "対象デバイスと画面幅"]
UNDECIDED = "N/A。実現方式が未定"
SW_HEAD = S_HEAD.replace(",根拠\n", ",根拠,パス\n")
TW_HEAD = T_HEAD.replace(",根拠\n", ",根拠,種類\n")


def subsections(names: list[str], bodies: dict[str, str] | None = None) -> str:
    bodies = bodies or {}
    return "\n".join(f"### {name}\n\n{bodies.get(name, 'N/A。この画面には無い')}\n" for name in names)


def profile_section(body: str | None = None) -> str:
    return "\n## 実現方式: web-spa\n\n" + (subsections(SUBSECTIONS) if body is None else body) + "\n"


def web_spa(**changes) -> dict[str, object]:
    """profile web-spa の正しい正本（列・仕様書の末尾の節・共通仕様の節）。"""
    files = base()
    files[SETTINGS_CSV] = WEB_SPA
    files[S] = SW_HEAD + S1.replace("\n", ",/orders\n") + S2.replace("\n", ",/orders/new\n")
    files[T] = TW_HEAD + T1.replace("\n", ",\n") + T2.replace("\n", ",同じタブ\n")
    files[LIST_MD] = doc("S-001", "受注一覧") + profile_section()
    files[NEW_MD] = doc("S-002", "受注登録") + profile_section()
    files[COMMON_MD] = "# 共通仕様\n\n## 用語\n\n" + profile_section(subsections(COMMON_SUBSECTIONS))
    for key, value in changes.items():
        path = {"S": S, "T": T, "LIST_MD": LIST_MD, "NEW_MD": NEW_MD, "COMMON": COMMON_MD, "SETTINGS": SETTINGS_CSV}[key]
        if value is None:
            files.pop(path)
        else:
            files[path] = value
    return files


WS1 = S1.replace("\n", ",/orders\n")
WS2 = S2.replace("\n", ",/orders/new\n")
WT1 = T1.replace("\n", ",\n")
WT2 = T2.replace("\n", ",同じタブ\n")

V2_S = "v2/requirements/screens/data/screens.csv"
V2_I = "v2/requirements/screens/data/screen-items.csv"
V2_T = "v2/requirements/screens/data/transitions.csv"
V2_REMOVED = "v2/removed.csv"
V3_T = "v3/requirements/screens/data/transitions.csv"
SETTING_MD = "v2/requirements/screens/setting.md"

# (名前, 正本のファイル, spec-loop の渡し方, 追加の引数, 終了コード, 出力に在る文字列, 出力に無い文字列)
# spec-loop の渡し方: None（隣の spec-loop）／ ("version", "<版>")・("name", "<名前>")（写しを --spec-loop で渡す）／
# ("env-name", "<名前>")（写しを環境変数で渡す）／ ("alone",)（隣に spec-loop を置かない）／ ("cache", "<版>")（プラグインのキャッシュの形）
CASES: list[tuple[str, dict, object, list[str], int, str, str]] = [
    # ---- 陰性対照（U9）
    ("good", base(), None, [], 0, "違反 0 件・必須の欄が空 0 件・未決定 0 件・警告 0 件・起票の候補 0 件", "違反:"),
    ("good-v2-adds-screen", with_files(
        base(),
        **{V2_S: S_HEAD + "S-003,設定,setting,,管理者,下書き,,設定を変える,既定の値を変える,,,setting.md,F-001\n",
           V2_I: I_HEAD + "I-005,S-001,操作,3,設定,ボタン,,,,,,,,F-001\n",
           V2_T: T_HEAD + "T-003,S-001,I-005,,,S-003,,F-001\n",
           SETTING_MD: doc("S-003", "設定")}), None, [], 0, "違反 0 件", "違反:"),
    ("good-tab-reached-by-parent", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,受注の明細,tab,S-002,担当者,記入中,,明細を見る,明細の一覧,F-002,,order-tab.md,F-002\n"),
        **{"v1/requirements/screens/order-tab.md": doc("S-003", "受注の明細")}), None, [], 0, "違反 0 件", "辿れない"),
    ("good-internal-qa", good(S=S_HEAD + S1 + S2.replace(",F-002\n", ",F-002、D-S-001\n")), None, [], 0, "違反 0 件", "違反:"),
    ("no-tables", {QA: QA_HEAD}, None, [], 0, "画面の表が無い", "違反:"),
    ("heading-in-fence", good(LIST_MD=doc("S-001", "受注一覧", {"9. 他システム連携": "N/A。無い\n\n```text\n## 10. 同時編集\n```"})),
     None, [], 0, "違反 0 件", "2 つある"),
    ("upto-ignores-later", with_files(base(), **{V2_T: T_HEAD + "T-009,S-001,I-002,,,S-999,,F-002\n"}), None, ["--upto", "1"], 0, "違反 0 件", "S-999"),
    # ---- U1 表に無い画面を指す遷移・項目
    ("transition-to-missing", good(T=T_HEAD + T1 + T2 + "T-003,S-001,I-002,,,S-999,,F-002\n"), None, [], 1, "T-003 遷移先: S-999 が画面の表に無い", ""),
    ("transition-from-missing", good(T=T_HEAD + T1 + T2 + "T-003,S-998,I-002,,,S-001,,F-002\n"), None, [], 1, "T-003 遷移元: S-998 が画面の表に無い", ""),
    ("item-on-missing-screen", good(I=I_HEAD + I1 + I2 + I3 + I4 + "I-005,S-999,表示,1,備考,表示,備考,,,,,,,F-002\n"), None, [], 1,
     "I-005 画面ID: S-999 が画面の表に無い", ""),
    ("later-version-points-to-removed-screen", with_files(
        base(),
        **{V2_REMOVED: "種類,対象,理由\n画面,S-002,使わなくなった\n", V2_T: T_HEAD,
           "v2/requirements/screens/data/screens.csv": S_HEAD, V2_I: I_HEAD + "I-006,S-001,操作,3,削除,ボタン,,,,,,,,F-001\n",
           V3_T: T_HEAD + "T-010,S-001,I-006,,,S-002,,F-001\n"}), None, [], 1, "T-010 遷移先: S-002 が画面の表に無い", ""),
    # ---- U2 入口から辿れない画面
    ("unreachable-screen", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,受注の詳細,detail,,担当者,記入中,,詳しく見る,詳細,F-001,,order-detail.md,F-001\n"),
        **{"v1/requirements/screens/order-detail.md": doc("S-003", "受注の詳細")}), None, [], 1, "S-003: 入口の画面から遷移で辿れない", ""),
    ("no-entry", good(S=S_HEAD + S1.replace(",top,", ",list,") + S2), None, [], 1, "入口の画面（種別 top）が無い", ""),
    ("dialog-needs-transition", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,確認,dialog,S-002,担当者,記入中,,確かめる,確認,F-002,,order-confirm.md,F-002\n"),
        **{"v1/requirements/screens/order-confirm.md": doc("S-003", "確認")}), None, [], 1, "S-003: 入口の画面から遷移で辿れない", ""),
    # ---- U3 遷移の無いボタン
    ("button-without-transition", good(I=I_HEAD + I1 + I2 + I3 + I4 + "I-005,S-002,操作,3,取消,ボタン,,,,,,,,F-002\n"), None, [], 1,
     "I-005: ボタン '取消' を きっかけ にする遷移が無い", ""),
    ("trigger-on-other-screen", good(T=T_HEAD + T1.replace(",I-002,", ",I-004,") + T2), None, [], 1,
     "T-001 きっかけ: 項目 I-004 は遷移元 S-001 の項目でない", ""),
    ("trigger-missing-item", good(T=T_HEAD + T1 + T2 + "T-003,S-001,I-099,,,S-002,,F-002\n"), None, [], 1, "T-003 きっかけ: I-099 が項目の表に無い", ""),
    # ---- U4 Q&A 表に無い根拠の番号
    ("qa-missing", good(S=S_HEAD + S1.replace(",Q-R-002\n", ",Q-R-099\n") + S2), None, [], 1, "Q&A Q-R-099 が Q&A 表に無い", ""),
    ("qa-missing-in-prose", good(LIST_MD=doc("S-001", "受注一覧", {"7. 状態": "空のときは何も出さない（Q-R-098）"})), None, [], 1,
     "order-list.md:", ""),
    ("qa-missing-internal", good(S=S_HEAD + S1 + S2.replace(",F-002\n", ",D-S-009\n")), None, [], 1, "Q&A D-S-009 が Q&A 表に無い", ""),
    ("qa-removed-warns", with_files(base(), **{V2_REMOVED: "種類,対象,理由\nQ&A,Q-R-002,取り下げた\n",
                                               V2_S: S_HEAD + S2.replace(",F-002\n", ",Q-R-002\n")}), None, [], 0,
     "removed.csv で消した Q&A Q-R-002 を指す（反映を確かめる）", "違反:"),
    ("qa-answered-warns", good(S=S_HEAD + S1 + S2.replace(",F-002\n", ",Q-R-003\n")), None, [], 0,
     "Q&A Q-R-003 は回答がある（反映を確かめる）", "違反:"),
    ("qa-reflected-warns", good(S=S_HEAD + S1 + S2.replace(",F-002\n", ",Q-R-001\n")), None, [], 0,
     "Q&A Q-R-001 は回答がある（反映を確かめる）", "違反:"),
    ("feature-number-in-basis-missing", good(T=T_HEAD + T1 + T2.replace(",F-002\n", ",F-009\n")), None, [], 1,
     "根拠: 機能 F-009 が requirements/features.csv に無い", ""),
    # ---- U5 散文
    ("prose-empty-section", good(LIST_MD=doc("S-001", "受注一覧", {"7. 状態": ""})), None, [], 1, "節 ## 7. 状態 が空", ""),
    ("prose-na-without-reason", good(LIST_MD=doc("S-001", "受注一覧", {"9. 他システム連携": "N/A。"})), None, [], 1,
     "節 ## 9. 他システム連携 が N/A だけで理由が無い", ""),
    ("prose-mark-in-prose-section", good(LIST_MD=doc("S-001", "受注一覧", {"10. 同時編集": MARK})), None, [], 1, "節 ## 10. 同時編集 が空", ""),
    ("prose-comment-only", good(LIST_MD=doc("S-001", "受注一覧", {"11. 表示ルール": "<!-- あとで -->"})), None, [], 1, "節 ## 11. 表示ルール が空", ""),
    ("prose-missing-section", good(LIST_MD=doc("S-001", "受注一覧", order=[h for h, _ in SECTIONS if h != "9. 他システム連携"])), None, [], 1,
     "節 ## 9. 他システム連携 が無い", ""),
    ("prose-order", good(LIST_MD=doc("S-001", "受注一覧", order=[h for h, _ in SECTIONS[:6]] + ["8. 権限とデータの見える範囲", "7. 状態"]
                                     + [h for h, _ in SECTIONS[8:]])), None, [], 1, "節の順が決まり", ""),
    ("prose-duplicate-section", good(LIST_MD=doc("S-001", "受注一覧") + "\n## 7. 状態\n\n二度目\n"), None, [], 1, "節 ## 7. 状態 が 2 つある", ""),
    ("prose-title-without-id", good(LIST_MD=doc("S-001", "受注一覧", title="# 受注一覧")), None, [], 1, "最初の # の見出しに画面ID S-001", ""),
    ("prose-file-missing", good(NEW_MD=None), None, [], 1, "仕様書: requirements/screens/order-new.md が無い", ""),
    ("prose-orphan", with_files(base(), **{"v1/requirements/screens/old.md": doc("S-009", "古い")}), None, [], 1,
     "requirements/screens/old.md: どの画面の 仕様書 からも指されていない", ""),
    ("prose-common-not-orphan", with_files(base(), **{"v1/requirements/screens/common.md": "# 共通仕様\n\n日付は YYYY/MM/DD（Q-R-001）\n"}), None, [], 0,
     "違反 0 件", "common.md: どの画面"),
    ("prose-common-missing-qa", with_files(base(), **{"v1/requirements/screens/common.md": "# 共通仕様\n\n日付（Q-R-097）\n"}), None, [], 1,
     "common.md:3: Q&A Q-R-097 が Q&A 表に無い", ""),
    ("doc-shared", good(S=S_HEAD + S1 + S2.replace("order-new.md", "order-list.md"), NEW_MD=None), None, [], 1,
     "仕様書: order-list.md を画面 S-001 も指している", ""),
    ("doc-not-plain-name", good(S=S_HEAD + S1 + S2.replace("order-new.md", "sub/order-new.md")), None, [], 1, "の直下の <slug>.md でない", ""),
    # ---- U6 成果物の表
    ("feature-missing", good(S=S_HEAD + S1.replace(",F-001,", ",F-001、F-009,") + S2), None, [], 1,
     "S-001 機能: 機能 F-009 が requirements/features.csv に無い", ""),
    ("features-absent", good(FEATURES=None), None, [], 1, "機能 F-001 を指すが requirements/features.csv が無い", ""),
    ("role-missing", good(T=T_HEAD + T1.replace(",受注の登録,", ",受注の削除,") + T2), None, [], 1,
     "T-001 操作: 操作 受注の削除 が requirements/roles.csv に無い", ""),
    ("roles-absent", good(ROLES=None), None, [], 1, "操作 受注の登録 を指すが requirements/roles.csv が無い", ""),
    ("report-missing", good(S=S_HEAD + S1 + S2.replace(",F-002,,", ",F-002,RP-001,")), None, [], 1,
     "帳票 RP-001 を指すが requirements/reports.csv が無い", ""),
    ("report-present", with_files(good(S=S_HEAD + S1 + S2.replace(",F-002,,", ",F-002,RP-001,")),
                                  **{"v1/requirements/reports.csv": "id,帳票名,順番,項目,意味,書式\nRP-001,受注票,1,受注日,受注した日,\n"}),
     None, [], 0, "違反 0 件", "違反:"),
    # ---- U7 未決定の印
    ("marker-in-table", good(S=S_HEAD + S1.replace(",受注を探す,", ",未定（Q-R-002）,") + S2), None, [], 3,
     "未決定: requirements/screens/data/screens.csv S-001 目的と背景: 未決定の印 '未定'", "起票の候補:"),
    ("marker-without-number", good(S=S_HEAD + S1.replace(",受注を探す,", ",未定,") + S2), None, [], 3,
     "起票の候補: requirements/screens/data/screens.csv S-001 目的と背景: 未定", ""),
    ("marker-fullwidth", good(S=S_HEAD + S1.replace(",受注を探す,", ",ＴＢＤ（Q-R-002）,") + S2), None, [], 3, "未決定の印 'TBD'", ""),
    ("warning-sign-only", good(S=S_HEAD + S1.replace(",受注を探す,", ",⚠️ 受注を探す,") + S2), None, [], 0,
     "警告: requirements/screens/data/screens.csv S-001 目的と背景: ⚠️ だけで未決定の印が無い", "違反:"),
    ("marker-in-prose", good(LIST_MD=doc("S-001", "受注一覧", {"7. 状態": "空のときの表示は TODO"})), None, [], 3,
     "起票の候補: requirements/screens/order-list.md:", ""),
    ("marker-skips-reference", good(T=T_HEAD + T1 + T2.replace(",S-001,保存した,", ",未定（Q-R-002）,保存した,")), None, [], 3,
     "未決定: requirements/screens/data/transitions.csv T-002 遷移先", "違反:"),
    ("marker-and-violation", good(S=S_HEAD + S1.replace(",受注を探す,", ",未定（Q-R-002）,") + S2,
                                  T=T_HEAD + T1 + T2 + "T-003,S-001,I-002,,,S-999,,F-002\n"), None, [], 1, "未決定: ", ""),
    ("marker-cell-bad-qa", good(S=S_HEAD + S1 + S2.replace(",F-002\n", ",未定（Q-R-999）\n")), None, [], 1,
     "S-002 根拠: Q&A Q-R-999 が Q&A 表に無い", ""),
    ("marker-on-reach-target", good(T=T_HEAD + T1.replace(",S-002,,", ",未定（Q-R-002）,,") + T2), None, [], 3,
     "S-002: 入口の画面から遷移で辿れないかもしれない", "違反:"),
    ("marker-on-reach-source", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,受注の詳細,detail,,担当者,記入中,,詳しく見る,詳細,F-001,,order-detail.md,F-001\n",
             T=T_HEAD + T1 + T2 + "T-003,未定（Q-R-002）,I-002,,,S-003,,F-001\n"),
        **{"v1/requirements/screens/order-detail.md": doc("S-003", "受注の詳細")}), None, [], 3, "S-003: 入口の画面から遷移で辿れないかもしれない", "違反:"),
    ("marker-on-trigger", good(T=T_HEAD + T1.replace(",I-002,", ",未定（Q-R-002）,") + T2), None, [], 3,
     "ボタン '新規' を きっかけ にする遷移が無いかもしれない（きっかけが未決定", "違反:"),
    ("marker-on-entry-kind", good(S=S_HEAD + S1.replace(",top,", ",未定（Q-R-002）,") + S2), None, [], 3,
     "入口の画面（種別 top）が無いかもしれない（種別が未決定", "違反:"),
    ("marker-on-tab-parent", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,受注の明細,tab,未定（Q-R-002）,担当者,記入中,,明細を見る,明細の一覧,F-002,,order-tab.md,F-002\n"),
        **{"v1/requirements/screens/order-tab.md": doc("S-003", "受注の明細")}), None, [], 3, "S-003: 入口の画面から遷移で辿れないかもしれない", "違反:"),
    ("prose-heading-in-comment", good(LIST_MD=doc("S-001", "受注一覧", order=[h for h, _ in SECTIONS if h != "9. 他システム連携"])
                                      + "\n<!--\n## 9. 他システム連携\n\nあとで\n-->\n"), None, [], 1, "節 ## 9. 他システム連携 が無い", ""),
    ("prose-subheading-only", good(LIST_MD=doc("S-001", "受注一覧", {"7. 状態": "### 補足"})), None, [], 1, "節 ## 7. 状態 が空", ""),
    ("prose-na-lowercase", good(LIST_MD=doc("S-001", "受注一覧", {"9. 他システム連携": "n/a"})), None, [], 1, "が N/A だけで理由が無い", ""),
    ("prose-na-decorated", good(LIST_MD=doc("S-001", "受注一覧", {"9. 他システム連携": "N/A -"})), None, [], 1, "が N/A だけで理由が無い", ""),
    ("reach-list-with-undecided-parent", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,受注の詳細,list,未定（Q-R-002）,担当者,記入中,,詳しく見る,詳細,F-001,,order-detail.md,F-001\n"),
        **{"v1/requirements/screens/order-detail.md": doc("S-003", "受注の詳細")}), None, [], 1, "S-003: 入口の画面から遷移で辿れない\n", ""),
    ("reach-own-undecided-target", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,受注の詳細,detail,,担当者,記入中,,詳しく見る,詳細,F-001,,order-detail.md,F-001\n",
             I=I_HEAD + I1 + I2 + I3 + I4 + "I-005,S-003,操作,1,戻る,ボタン,,,,,,,,F-001\n",
             T=T_HEAD + T1 + T2 + "T-003,S-003,I-005,,,未定（Q-R-002）,,F-001\n"),
        **{"v1/requirements/screens/order-detail.md": doc("S-003", "受注の詳細")}), None, [], 1, "S-003: 入口の画面から遷移で辿れない\n", ""),
    ("reach-undecided-propagates", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,受注の詳細,未定（Q-R-002）,,担当者,記入中,,詳しく見る,詳細,F-001,,order-detail.md,F-001\n"
             + "S-004,受注の履歴,list,,担当者,記入中,,履歴を見る,履歴,F-001,,order-history.md,F-001\n",
             I=I_HEAD + I1 + I2 + I3 + I4 + "I-005,S-003,操作,1,履歴,ボタン,,,,,,,,F-001\n",
             T=T_HEAD + T1 + T2 + "T-003,S-003,I-005,,,S-004,,F-001\n"),
        **{"v1/requirements/screens/order-detail.md": doc("S-003", "受注の詳細"),
           "v1/requirements/screens/order-history.md": doc("S-004", "受注の履歴")}), None, [], 3,
     "S-004: 入口の画面から遷移で辿れないかもしれない", "違反:"),
    ("button-more-than-undecided-triggers", good(
        I=I_HEAD + I1 + I2 + I3 + I4 + "I-020,S-001,操作,3,印刷,ボタン,,,,,,,,F-001\nI-021,S-001,操作,4,削除,ボタン,,,,,,,,F-001\n",
        T=T_HEAD + T1 + T2 + "T-020,S-001,未定（Q-R-002）,,,S-001,,F-001\n"), None, [], 1, "少なくとも 1 個は遷移が無い", ""),
    ("button-undecided-screen", good(I=I_HEAD + I1 + I2 + I3 + I4.replace(",S-002,", ",未定（Q-R-002）,"),
                                     T=T_HEAD + T1 + T2.replace(",I-004,", ",未定（Q-R-002）,")), None, [], 3,
     "ボタン '保存' を きっかけ にする遷移が無いかもしれない", "違反:"),
    ("parent-missing-undecided-kind", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,明細,未定（Q-R-002）,S-999,担当者,記入中,,明細を見る,明細,F-002,,order-tab.md,F-002\n"),
        **{"v1/requirements/screens/order-tab.md": doc("S-003", "明細")}), None, [], 1, "親画面: S-999 が画面の表に無い", ""),
    ("prose-na-emphasis", good(LIST_MD=doc("S-001", "受注一覧", {"9. 他システム連携": "**N/A**"})), None, [], 1, "が N/A だけで理由が無い", ""),
    ("prose-na-list-mark", good(LIST_MD=doc("S-001", "受注一覧", {"9. 他システム連携": "- N/A"})), None, [], 1, "が N/A だけで理由が無い", ""),
    ("prose-comment-open-in-fence", good(LIST_MD=doc("S-001", "受注一覧", {"3. レイアウト": MARK + "\n\n```html\n<!-- 例: ここに部品\n```",
                                                                         "11. 表示ルール": "日付は YYYY/MM/DD <!-- メモ -->"})),
     None, [], 0, "違反 0 件", "違反:"),
    ("prose-indented-heading", good(LIST_MD=doc("S-001", "受注一覧").replace("\n## 7. 状態\n", "\n  ## 7. 状態\n")), None, [], 0, "違反 0 件", "違反:"),
    # ---- U8 spec-loop の版
    ("spec-loop-too-old", base(), ("version", "0.92.9"), [], 4, "spec-loop の版 0.92.9", "違反"),
    ("spec-loop-too-new", base(), ("version", "1.0.0"), [], 4, "対応の範囲の外", "違反"),
    ("spec-loop-in-range-named", base(), ("version", "0.99.0"), [], 0, "spec-loop 0.99.0", "違反:"),
    ("spec-loop-version-unreadable", base(), ("version", "0.93"), [], 4, "spec-loop の版が読めない", ""),
    ("spec-loop-named-not-spec-loop", base(), ("name", "other"), [], 4, "--spec-loop が指す", ""),
    ("spec-loop-env-not-spec-loop", base(), ("env-name", "other"), [], 4, "SCREEN_SPEC_SPEC_LOOP が指す", ""),
    ("spec-loop-env-in-range", base(), ("env-name", "spec-loop"), [], 0, "違反 0 件", ""),
    ("spec-loop-not-found", base(), ("alone",), [], 4, "spec-loop が見つからない", ""),
    ("spec-loop-from-cache", base(), ("cache", "0.93.0"), [], 0, "違反 0 件", ""),
    ("spec-loop-from-cache-too-old", base(), ("cache", "0.90.0"), [], 4, "spec-loop の版 0.90.0", ""),
    # ---- 表どうし・形（A11）
    ("key-overlap", good(I=I_HEAD + I1 + I2 + I3 + I4 + "S-002,S-002,備考,3,備考,表示,備考,,,,,,,F-002\n"), None, [], 1,
     "画面と項目の番号 S-002 が重なる", ""),
    ("header-wrong", good(S=S_HEAD.replace(",根拠\n", ",根拠,備考\n") + S1.replace("\n", ",\n") + S2.replace("\n", ",\n")), None, [], 1,
     "見出し行が決まり", ""),
    ("table-missing", good(T=None), None, [], 1, "transitions.csv: 表が無い", ""),
    ("kind-invalid", good(S=S_HEAD + S1 + S2.replace(",form,", ",page,")), None, [], 1, "種別 'page' は決まった値", ""),
    ("status-invalid", good(S=S_HEAD + S1 + S2.replace(",記入中,", ",確定,")), None, [], 1, "ステータス '確定' は決まった値", ""),
    ("parent-on-top", good(S=S_HEAD + S1.replace(",top,,", ",top,S-002,") + S2), None, [], 1, "親画面: 種別 top の画面には書かない", ""),
    ("tab-without-parent", with_files(
        good(S=S_HEAD + S1 + S2 + "S-003,明細,tab,,担当者,記入中,,明細を見る,明細,F-002,,order-tab.md,F-002\n"),
        **{"v1/requirements/screens/order-tab.md": doc("S-003", "明細")}), None, [], 1, "必須の欄が空: requirements/screens/data/screens.csv S-003 親画面", ""),
    ("order-not-positive", good(I=I_HEAD + I1.replace(",1,受注日,", ",0,受注日,") + I2 + I3 + I4), None, [], 1, "並び順: '0' は正の整数でない", ""),
    ("required-on-display", good(I=I_HEAD + I1 + I2.replace(",ボタン,,,,", ",ボタン,,,はい,") + I3 + I4), None, [], 1,
     "I-002 必須: 種類 ボタン の項目には書かない", ""),
    ("list-column-without-sort", good(I=I_HEAD + I1.replace(",はい,いいえ,", ",,いいえ,") + I2 + I3 + I4), None, [], 3,
     "必須の欄が空: requirements/screens/data/screen-items.csv I-001 並び替え", ""),
    ("required-empty", good(S=S_HEAD + S1.replace(",受注一覧,top,", ",,top,") + S2), None, [], 3,
     "必須の欄が空: requirements/screens/data/screens.csv S-001 画面名", ""),
    ("basis-empty", good(T=T_HEAD + T1 + T2.replace(",F-002\n", ",\n")), None, [], 3, "必須の欄が空: requirements/screens/data/transitions.csv T-002 根拠", ""),
    ("merge-header-differs", with_files(base(), **{V2_S: S_HEAD.replace(",根拠\n", ",根拠,備考\n")}), None, [], 1, "版の重ね合わせ: ", ""),
    # ---- 判定していない（2）
    # ---- profile（#1094）
    ("profile-unset-no-section", with_files(base(), **{SETTINGS_CSV: UNSET_SETTINGS}), None, [], 0, "違反 0 件・必須の欄が空 0 件・未決定 0 件", "実現方式"),
    ("web-spa-good", web_spa(), None, [], 0, "違反 0 件・必須の欄が空 0 件・未決定 0 件・警告 0 件・起票の候補 0 件", "違反:"),
    ("web-spa-undecided-good", web_spa(S=SW_HEAD + S1.replace("\n", f",{UNDECIDED}\n") + WS2, T=TW_HEAD + WT1 + T2.replace("\n", f",{UNDECIDED}\n"),
                                       LIST_MD=doc("S-001", "受注一覧") + profile_section(UNDECIDED + "（Q-R-002 で決める）"),
                                       NEW_MD=doc("S-002", "受注登録") + profile_section(f"**{UNDECIDED}**"),
                                       COMMON="# 共通仕様\n\n" + profile_section(UNDECIDED)),
     None, [], 0, "違反 0 件・必須の欄が空 0 件・未決定 0 件・警告 0 件・起票の候補 0 件", "違反:"),
    ("web-spa-no-common-ok", web_spa(COMMON=None), None, [], 0, "違反 0 件・必須の欄が空 0 件・未決定 0 件", "違反:"),
    ("web-spa-no-section", web_spa(NEW_MD=doc("S-002", "受注登録")), None, [], 1, "order-new.md: 節 ## 実現方式: web-spa が無い（profile web-spa）", ""),
    ("web-spa-section-in-comment", web_spa(NEW_MD=doc("S-002", "受注登録") + "\n<!--" + profile_section() + "-->\n"), None, [], 1,
     "order-new.md: 節 ## 実現方式: web-spa が無い", ""),
    ("web-spa-section-as-h3", web_spa(NEW_MD=doc("S-002", "受注登録") + profile_section().replace("## 実現方式", "### 実現方式")), None, [], 1,
     "order-new.md: 節 ## 実現方式: web-spa が無い", ""),
    ("web-spa-section-not-last", web_spa(NEW_MD=doc("S-002", "受注登録").replace("## 未決の論点", profile_section().lstrip("\n") + "\n## 未決の論点")),
     None, [], 1, "を末尾（## 未決の論点 の後ろ）に置いていない", ""),
    ("web-spa-section-twice", web_spa(NEW_MD=doc("S-002", "受注登録") + profile_section() + profile_section()), None, [], 1,
     "節 ## 実現方式: web-spa が 2 つある", ""),
    ("web-spa-subsection-missing", web_spa(NEW_MD=doc("S-002", "受注登録") + profile_section(subsections(SUBSECTIONS[:-1]))), None, [], 1,
     "に小見出し ### 認証と権限の外れ が無い", ""),
    ("web-spa-subsection-empty", web_spa(NEW_MD=doc("S-002", "受注登録") + profile_section(subsections(SUBSECTIONS, {"一覧の送り方": "<!-- あとで -->"}))),
     None, [], 1, "小見出し ### 一覧の送り方 が空", ""),
    ("web-spa-subsection-na-only", web_spa(NEW_MD=doc("S-002", "受注登録") + profile_section(subsections(SUBSECTIONS, {"ダイアログの実体": "N/A"}))),
     None, [], 1, "小見出し ### ダイアログの実体 が N/A だけで理由が無い", ""),
    ("web-spa-common-no-section", web_spa(COMMON="# 共通仕様\n\n## 用語\n"), None, [], 1, "common.md: 節 ## 実現方式: web-spa が無い", ""),
    ("web-spa-common-subsection-missing", web_spa(COMMON="# 共通仕様\n" + profile_section(subsections(COMMON_SUBSECTIONS[:1]))), None, [], 1,
     "に小見出し ### 対象デバイスと画面幅 が無い", ""),
    ("web-spa-header-core-only", web_spa(S=S_HEAD + S1 + S2), None, [], 1, "見出し行が決まり（profile web-spa の列を足した）", ""),
    ("unset-header-with-profile-column", with_files(web_spa(), **{SETTINGS_CSV: UNSET_SETTINGS}), None, [], 1, "screens.csv:1: 見出し行が決まり", ""),
    ("profile-unknown", web_spa(SETTINGS=WEB_SPA.replace("web-spa", "desktop")), None, [], 1, "'desktop' はこのプラグインの profile（web-spa）でも 未設定 でもない", ""),
    ("profile-twice", web_spa(SETTINGS=WEB_SPA + "profile,web-spa\n"), None, [], 1, "profile の行が 2 つある", ""),
    ("web-spa-path-empty", web_spa(S=SW_HEAD + S1.replace("\n", ",\n") + WS2), None, [], 3,
     "必須の欄が空: requirements/screens/data/screens.csv S-001 パス", ""),
    ("web-spa-tab-path-empty-ok", with_files(
        web_spa(S=SW_HEAD + WS1 + WS2 + "S-003,受注の明細,tab,S-002,担当者,記入中,,明細を見る,明細の一覧,F-002,,order-tab.md,F-002,\n"),
        **{"v1/requirements/screens/order-tab.md": doc("S-003", "受注の明細") + profile_section()}), None, [], 0, "違反 0 件・必須の欄が空 0 件", "違反:"),
    ("web-spa-path-not-slash", web_spa(S=SW_HEAD + WS1 + S2.replace("\n", ",orders/new\n")), None, [], 1, "S-002 パス: 'orders/new' は / で始まらない", ""),
    ("web-spa-path-marker", web_spa(S=SW_HEAD + WS1 + S2.replace("\n", ",未定（D-S-001）\n")), None, [], 3, "S-002 パス: 未決定の印 '未定'", "違反:"),
    ("web-spa-tab-kind-bad", web_spa(T=TW_HEAD + WT1 + T2.replace("\n", ",新しいタブ\n")), None, [], 1, "種類 '新しいタブ' は決まった値（同じタブ・別タブ）でない", ""),
    ("web-spa-v2-doc-without-section", with_files(
        web_spa(), **{"v2/requirements/screens/order-new.md": doc("S-002", "受注登録")}), None, [], 1,
     "order-new.md: 節 ## 実現方式: web-spa が無い", ""),
    ("no-args", {}, None, ["<none>"], 2, "usage:", "Traceback"),
    ("docs-missing", {}, None, ["<missing>"], 2, "ディレクトリが無い", ""),
    ("upto-bad", base(), None, ["--upto", "0"], 2, "--upto には", ""),
    ("upto-out-of-range", base(), None, ["--upto", "5"], 2, "判定していない", ""),
    ("features-not-utf8", good(FEATURES=b"id,\xff\n"), None, [], 2, "UTF-8 で読めない", ""),
]


failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def copy_spec_loop(dest: Path, name: str = "spec-loop", version: str | None = None) -> Path:
    assert_in_tmp(dest)
    for part in (".claude-plugin", "scripts"):
        shutil.copytree(SPEC_LOOP / part, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
    manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    manifest["name"] = name
    if version is not None:
        manifest["version"] = version
    (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return dest


def copy_plugin(source: Path, dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


NUMBER = re.compile(r"(?<![A-Za-z0-9-])[QD]-(?:[RSFD]-)?[0-9]{3,}")


def run_one(plugin: Path, sibling: Path, case_dir: Path, case) -> tuple[int, str]:
    name, files, how, args, _, _, _ = case
    assert_in_tmp(case_dir)
    docs = case_dir / "docs"
    docs.mkdir(parents=True)
    for rel, body in files.items():
        path = docs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    home = case_dir / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR", "SCREEN_SPEC_SPEC_LOOP")}
    env["HOME"] = str(home)
    script = plugin / "scripts" / TARGET
    extra: list[str] = []
    if how is not None:
        kind = how[0]
        if kind == "version":
            extra = ["--spec-loop", str(copy_spec_loop(case_dir / "alt-spec-loop", version=how[1]))]
        elif kind == "name":
            extra = ["--spec-loop", str(copy_spec_loop(case_dir / "alt-spec-loop", name=how[1]))]
        elif kind == "env-name":
            env["SCREEN_SPEC_SPEC_LOOP"] = str(copy_spec_loop(case_dir / "alt-spec-loop", name=how[1]))
        elif kind == "alone":
            script = copy_plugin(plugin, case_dir / "alone" / "screen-spec") / "scripts" / TARGET
        elif kind == "cache":
            config = case_dir / "config"
            cache = config / "plugins" / "cache" / "market"
            script = copy_plugin(plugin, cache / "screen-spec" / "0.1.0") / "scripts" / TARGET
            installed = copy_spec_loop(cache / "spec-loop" / how[1], version=how[1])
            copy_spec_loop(cache / "spec-loop" / "0.99.9", version="0.99.9")  # 名指されていない版（積み上がったキャッシュ）
            (config / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": {
                "spec-loop@market": [{"scope": "user", "installPath": str(installed), "version": how[1]}],
                "spec-loop@other-market": [{"scope": "user", "installPath": str(cache / "spec-loop" / "0.99.9"), "version": "0.99.9"}],
            }}), encoding="utf-8")
            env["CLAUDE_CONFIG_DIR"] = str(config)
    if args == ["<none>"]:
        argv: list[str] = []
    elif args == ["<missing>"]:
        argv = [str(case_dir / "nowhere")]
    else:
        argv = [str(docs), *args]
    # 書かないことは、正本だけでなく走らせた場所（cwd）と、読み込む spec-loop・screen-spec の写し（`__pycache__`）でも見る
    watched = (case_dir, sibling.parent)
    before = [snapshot(root) for root in watched]
    proc = subprocess.run([sys.executable, "-I", str(script), *argv, *extra], capture_output=True, text=True, cwd=case_dir, env=env)
    out = proc.stdout + proc.stderr
    if [snapshot(root) for root in watched] != before:
        out += "\n<<正本か走らせた場所か読み込んだプラグインにファイルを書いた>>"
    written = "".join(b.decode("utf-8", "replace") if isinstance(b, bytes) else b for b in files.values())
    invented = sorted({n for n in NUMBER.findall(out) if n not in written})
    if invented:
        out += f"\n<<正本に無い Q&A の番号を出した: {invented}>>"
    return proc.returncode, out


def as_expected(case, result: tuple[int, str]) -> bool:
    _, _, _, _, code, text, absent = case
    return (result[0] == code and text in result[1] and not (absent and absent in result[1])
            and "Traceback" not in result[1] and "<<" not in result[1])


def run_cases(plugin: Path, sibling: Path, work: Path, only: str | None = None) -> dict[str, tuple[int, str]]:
    return {case[0]: run_one(plugin, sibling, work / f"case{i}", case) for i, case in enumerate(CASES) if only is None or case[0] == only}


# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("辿り始めを全部の画面にする", "reached = walk(entries)", "reached = set(screens)", "unreachable-screen"),
    ("入口が無いのを見ない", "        if not entries:\n", "        if False:\n", "no-entry"),
    ("タブを親から辿らない", "edges.get(here, []) + children.get(here, [])", "edges.get(here, [])", "good-tab-reached-by-parent"),
    ("遷移の無いボタンを見ない", "if row.get(\"種類\") == BUTTON and key not in triggered:", "if False:", "button-without-transition"),
    ("きっかけの画面を見ない", "elif row.get(\"遷移元\") and items[trigger].get(\"画面ID\") not in (None, row[\"遷移元\"]):", "elif False:",
     "trigger-on-other-screen"),
    ("きっかけの項目が在るかを見ない", "if trigger not in items:", "if False:", "trigger-missing-item"),
    ("遷移が指す画面を見ない", "if value and value not in screens:", "if False:", "transition-to-missing"),
    ("項目が指す画面を見ない", "if screen and screen not in screens:", "if False:", "item-on-missing-screen"),
    ("表に無い Q&A を警告にする", "self.report.violations.append(f\"{where}: Q&A {number} が Q&A 表に無い\")",
     "self.report.warnings.append(f\"{where}: Q&A {number} が Q&A 表に無い\")", "qa-missing"),
    ("消した Q&A を違反にする", "if number in self.removed:", "if False:", "qa-removed-warns"),
    ("回答のある行を警告しない", "elif row.get(\"回答\") != self.qa.NO_ANSWER:", "elif False:", "qa-reflected-warns"),
    ("内部の Q&A 表を引かない", "self.all_qa = {**whole.qa, **whole.internal}", "self.all_qa = dict(whole.qa)", "good-internal-qa"),
    ("散文の Q&A の番号を見ない", "            self.references(where, line)\n", "            pass\n", "qa-missing-in-prose"),
    ("根拠の機能の番号を見ない", "for match in self.feature_number.finditer(decided[\"根拠\"]):", "for match in []:", "feature-number-in-basis-missing"),
    ("成果物の表に在るかを見ない", "elif value not in known:", "elif False:", "feature-missing"),
    ("成果物の表が無いのを見ない", "if known is None:", "if False:", "features-absent"),
    ("遷移の操作を見ない", "            if operation:\n", "            if False:\n", "role-missing"),
    ("帳票を見ない", "for value in self.split(row.get(\"帳票\")):", "for value in []:", "report-missing"),
    ("未決定の印を数えない", "        if hits:\n", "        if False:\n", "marker-in-table"),
    ("起票の候補を出さない", "if not self.qa_number.search(value):", "if False:", "marker-without-number"),
    ("⚠️ だけを警告しない", "if any(sign in value for sign in WARNING_SIGNS):", "if False:", "warning-sign-only"),
    ("印のあるセルも値の決まりに当てる", "                self.undecided_cells.add((path, key, name))\n                continue\n",
     "                self.undecided_cells.add((path, key, name))\n", "marker-skips-reference"),
    ("散文の未決定の印を見ない", "            self.marked(where, line)\n", "            pass\n", "marker-in-prose"),
    ("空の節を見ない", "self.report.violations.append(f\"{path}:{at + 1}: 節 ## {heading} が空", "None and (f\"{path}:{at + 1}: 節 ## {heading} が空", "prose-empty-section"),
    ("理由の無い N/A を見ない", "self.report.violations.append(f\"{path}:{at + 1}: 節 ## {heading} が N/A だけ", "None and (f\"{path}:{at + 1}: 節 ## {heading} が N/A だけ",
     "prose-na-without-reason"),
    ("N/A の強調を理由に数える", "DECORATION.sub(\"\", LIST_MARK.sub(\"\", content))", "LIST_MARK.sub(\"\", content)", "prose-na-emphasis"),
    ("N/A の箇条書きの印を理由に数える", "DECORATION.sub(\"\", LIST_MARK.sub(\"\", content))", "DECORATION.sub(\"\", content)", "prose-na-list-mark"),
    ("散文の節の表を出す印を中身に数える", "if tabled and TABLE_MARK in body:", "if TABLE_MARK in body:", "prose-mark-in-prose-section"),
    ("散文の節の表を出す印を中身に数える（コメントを外さない）", "HEADING_LINE.sub(\"\", COMMENT.sub(\"\", body))", "HEADING_LINE.sub(\"\", body)",
     "prose-mark-in-prose-section"),
    ("無い節を見ない", "            if name not in found:\n", "            if False:\n", "prose-missing-section"),
    ("節の順を見ない", "if [found[name] for name in order] != sorted(found[name] for name in order):", "if False:", "prose-order"),
    ("重なる節を見ない", "            if heading in found:\n", "            if False:\n", "prose-duplicate-section"),
    ("コードブロックの中の見出しを数える", "opened = FENCE.match(line.lstrip())\n            if fence is not None:\n", "opened = None\n            if fence is not None:\n", "heading-in-fence"),
    ("最初の見出しの画面ID を見ない", "if title is None or key not in title[2]:", "if title is None:", "prose-title-without-id"),
    ("無い仕様書を見ない", "self.report.violations.append(f\"{SCREENS} {key} 仕様書: {path} が無い\")", "pass", "prose-file-missing"),
    ("表から指されない仕様書を見ない", "elif name not in referenced:", "elif False:", "prose-orphan"),
    ("common.md を表から指されない仕様書に数える", "            if name == COMMON:\n", "            if False:\n", "prose-common-not-orphan"),
    ("仕様書を 2 つの画面が指すのを見ない", "elif document in documents:", "elif False:", "doc-shared"),
    ("版の範囲を見ない", "if not (SPEC_LOOP_MIN <= version < SPEC_LOOP_BELOW):", "if False:", "spec-loop-too-old"),
    ("上限を含める", "SPEC_LOOP_MIN <= version < SPEC_LOOP_BELOW", "SPEC_LOOP_MIN <= version <= SPEC_LOOP_BELOW", "spec-loop-too-new"),
    ("名指しが spec-loop かを見ない", "if not is_spec_loop(root):", "if False:", "spec-loop-named-not-spec-loop"),
    ("環境変数を読まない", "(SPEC_LOOP_ENV, os.environ.get(SPEC_LOOP_ENV) or None)", "(SPEC_LOOP_ENV, None)", "spec-loop-env-not-spec-loop"),
    ("隣の spec-loop を探さない", "    if is_spec_loop(sibling):\n", "    if False:\n", "good"),
    ("キャッシュの記録を読まない", "chosen = project if project else user", "chosen = []", "spec-loop-from-cache"),
    ("キャッシュのマーケットプレイスを見ない", "f\"{SPEC_LOOP_NAME}@{market}\"", "f\"{SPEC_LOOP_NAME}@other-market\"", "spec-loop-from-cache-too-old"),
    ("表をまたいだ番号の重なりを見ない", "for key in sorted(set(keys_a) & set(keys_b)):", "for key in []:", "key-overlap"),
    ("見出し行を見ない", "elif whole.headers[path] != self.columns[path]:", "elif False:", "header-wrong"),
    ("揃っていない表を見ない", "self.report.violations.append(f\"{path}: 表が無い（3 つの表は揃えて置く。行が無くても見出し行は置く）\")", "pass", "table-missing"),
    ("種別を見ない", "self.one_of(f\"{where} 種別\", kind, SCREEN_KINDS, \"種別\")", "None", "kind-invalid"),
    ("ステータスを見ない", "self.one_of(f\"{where} ステータス\", row.get(\"ステータス\"), STATUSES, \"ステータス\")", "None", "status-invalid"),
    ("親画面を書いてはならない種別を見ない", "self.must_be_empty(f\"{where} 親画面\", parent, f\"種別 {kind} の画面\")", "None", "parent-on-top"),
    ("タブの親画面の空を見ない", "self.report.empty.append(f\"{where} 親画面（種別 {kind} の画面は親画面を書く）\")", "pass", "tab-without-parent"),
    ("並び順を見ない", "if order and not re.fullmatch(r\"[1-9][0-9]{0,8}\", order):", "if False:", "order-not-positive"),
    ("種類に合わない列を見ない", "self.must_be_empty(f\"{where} {name}\", row.get(name), f\"種類 {kind} の項目\")\n            for",
     "None\n            for", "required-on-display"),
    ("一覧の列の並び替えの空を見ない", "self.report.empty.append(f\"{where} {name}（種類 {LIST_COLUMN} の項目は書く）\")", "pass", "list-column-without-sort"),
    ("必須の欄の空を見ない", "if not decided[name] and name not in MAY_BE_EMPTY[path] and name in COLUMNS[path]:", "if False:", "required-empty"),
    ("重ね合わせの違反を見ない", "        if problems:\n            for problem in problems:", "        if False:\n            for problem in problems:",
     "merge-header-differs"),
    ("--upto を渡さない", "self.versions.merge(self.docs, self.upto)", "self.versions.merge(self.docs, None)", "upto-ignores-later"),
    ("印のあるセルの Q&A の番号を見ない", "                self.references(where, value)  # 印に添えた", "                pass  # 印に添えた", "marker-cell-bad-qa"),
    ("未決定の遷移先でも辿れないを違反にする", "if anywhere or key in maybe:", "if key in maybe:", "marker-on-reach-target"),
    ("遷移元が辿れない未決定の遷移先でも警告にする", "and (row.get(\"遷移元\") in maybe or undecided(TRANSITIONS, key, \"遷移元\"))", "", "reach-own-undecided-target"),
    ("未決定の遷移元の遷移先を辿らない", "seeds += [row[\"遷移先\"]", "seeds += [][:0] and [row[\"遷移先\"]", "marker-on-reach-source"),
    ("未決定の親画面を辿らない", "or (undecided(SCREENS, key, \"親画面\") and row.get(\"種別\") in REACHED_WITH_PARENT)]", "]", "marker-on-tab-parent"),
    ("未決定の親画面をどの種別でも警告にする", "and row.get(\"種別\") in REACHED_WITH_PARENT)]", ")]", "reach-list-with-undecided-parent"),
    ("未決定を先へ伝えない", "maybe = walk(set(seeds) | reached)", "maybe = set(seeds) | reached", "reach-undecided-propagates"),
    ("未決定のきっかけでもボタンを違反にする", "if len(keys) <= room:", "if False:", "marker-on-trigger"),
    ("指しうる数より多いボタンを警告にする", "if len(keys) <= room:", "if room:", "button-more-than-undecided-triggers"),
    ("画面ID が未決定のボタンを指しうる数を数えない", "room = sum(open_by_source.values()) if screen is None else", "room = 0 if screen is None else", "button-undecided-screen"),
    ("未決定の種別でも入口が無いを違反にする", "if any(undecided(SCREENS, key, \"種別\") for key in screens):", "if False:", "marker-on-entry-kind"),
    ("種別が未決定の画面の親画面を見ない", "            elif parent and parent not in screens:\n", "            elif False:\n", "parent-missing-undecided-kind"),
    ("コメントの中の見出しを数える", "        lines = self.without_comments(text)\n", "        lines = text.splitlines()\n", "prose-heading-in-comment"),
    ("コードブロックの中の <!-- をコメントに数える", "            if fence is not None or opened:\n", "            if False:\n", "prose-comment-open-in-fence"),
    ("字下げした見出しを見ない", "HEADING = re.compile(r\" {0,3}(#{1,6})", "HEADING = re.compile(r\"(#{1,6})", "prose-indented-heading"),
    ("小見出しを中身に数える", "HEADING_LINE.sub(\"\", COMMENT.sub(\"\", body))", "COMMENT.sub(\"\", body)", "prose-subheading-only"),
    ("N/A の大文字小文字を区別する", "、\\-－—–()（）\\[\\]「」]*\", re.IGNORECASE)", "、\\-－—–()（）\\[\\]「」]*\")", "prose-na-lowercase"),
    ("N/A の飾りを理由に数える", "、\\-－—–()（）\\[\\]「」]*", "、]*", "prose-na-decorated"),
    ("__pycache__ を書く", "sys.dont_write_bytecode = True", "sys.dont_write_bytecode = False", "good"),
    # ---- profile（#1094）
    ("設定の profile を読まない", "self.profile = self.read_profile(whole)", "self.profile = UNSET", "web-spa-no-section"),
    ("profile の列を求めない", "extra = PROFILES[self.profile][\"columns\"] if self.profile in PROFILES else {}", "extra = {}", "web-spa-good"),
    ("知らない profile を通す", "if values[0] != UNSET and values[0] not in PROFILES:", "if False:", "profile-unknown"),
    ("profile の行の重なりを見ない", "        if len(values) > 1:\n", "        if False:\n", "profile-twice"),
    ("仕様書の profile の節を見ない", "        if self.profile in PROFILES:\n            last = names[-1]", "        if False:\n            last = names[-1]", "web-spa-no-section"),
    ("profile の節が無いのを見ない", "self.report.violations.append(f\"{path}: 節 ## {name} が無い（profile {self.profile}）\")", "pass", "web-spa-no-section"),
    ("2 つある profile の節を見ない", "for index in places[1:]:", "for index in []:", "web-spa-section-twice"),
    ("profile の節が末尾かを見ない", "if after is not None and at < after:", "if False:", "web-spa-section-not-last"),
    ("方式が未定でも小見出しを求める", "        if undecided_profile(HEADING_LINE.sub(", "        if False and undecided_profile(HEADING_LINE.sub(", "web-spa-undecided-good"),
    ("無い小見出しを見ない", "            if found is None:\n", "            if False:\n", "web-spa-subsection-missing"),
    ("空の小見出しを見ない", "self.report.violations.append(f\"{path}:{sub_at + 1}: 小見出し ### {subsection} が空", "None and (f\"{path}:{sub_at + 1}: 小見出し ### {subsection} が空",
     "web-spa-subsection-empty"),
    ("理由の無い N/A の小見出しを見ない", "self.report.violations.append(f\"{path}:{sub_at + 1}: 小見出し ### {subsection} が N/A だけ", "None and (f\"{path}:{sub_at + 1}: 小見出し ### {subsection} が N/A だけ",
     "web-spa-subsection-na-only"),
    ("共通仕様の profile の節を見ない", "                if self.profile in PROFILES:\n                    lines = self.without_comments(common)",
     "                if False:\n                    lines = self.without_comments(common)", "web-spa-common-no-section"),
    ("言い回しを未決定の印に数える", "hits = self.find_markers(mask_undecided(value))", "hits = self.find_markers(value)", "web-spa-undecided-good"),
    ("パスの空を見ない", "                    if row.get(\"種別\") not in CHILD_KINDS:", "                    if False:", "web-spa-path-empty"),
    ("tab のパスの空も求める", "                    if row.get(\"種別\") not in CHILD_KINDS:", "                    if True:", "web-spa-tab-path-empty-ok"),
    ("パスの形を見ない", "elif not value.startswith(\"/\"):", "elif False:", "web-spa-path-not-slash"),
    ("言い回しのパスを値の決まりに当てる", "if value is None or undecided_profile(value):", "if value is None:", "web-spa-undecided-good"),
    ("遷移の種類の値を見ない", "                if value and not undecided_profile(value):", "                if False:", "web-spa-tab-kind-bad"),
    ("言い回しの種類を値の決まりに当てる", "                if value and not undecided_profile(value):", "                if value:", "web-spa-undecided-good"),
    ("profile の列を必須の欄の空に数える", " and name in COLUMNS[path]:", ":", "web-spa-good"),
    ("未決定を 0 にする", "return 3 if self.undecided or self.empty else 0", "return 0", "marker-in-table"),
]
OO_MUTATIONS = [("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else")]


def oo_problems(plugin: Path, cwd: Path) -> list[str]:
    proc = subprocess.run([sys.executable, "-I", "-OO", str(plugin / "scripts" / TARGET)], capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        return [f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}"]
    return []


# ---- references との突き合わせ

def section(markdown: str, heading: str) -> str:
    level = len(heading) - len(heading.lstrip("#"))
    start = markdown.index(heading)
    rest = markdown[start + len(heading):]
    found = re.search(rf"^#{{1,{level}}} ", rest, flags=re.MULTILINE)
    return rest[:found.start()] if found else rest


def rows_of(text: str) -> list[list[str]]:
    return [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in text.splitlines() if re.match(r"^\| `[^`]+` \|", line)]


def ticked(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


def profile_mismatches(module, profiles: str, directories: list[str]) -> list[str]:
    """profile の定数と `references/profiles.md`・`profiles/` のディレクトリ（#1094）。"""
    problems = []

    def same(what: str, ours, theirs) -> None:
        if ours != theirs:
            problems.append(f"{what}: 本体 {ours!r} ／ references {theirs!r}")

    try:
        listed = [ticked(r[0])[0] for r in rows_of(section(profiles, "## profile の一覧"))]
        spa = section(profiles, "## `web-spa`")
        columns = rows_of(section(spa, "### 表の列"))
        screen = [ticked(r[0])[0] for r in rows_of(section(spa, "### 仕様書の小見出し"))]
        common = [ticked(r[0])[0] for r in rows_of(section(spa, "### 共通仕様の小見出し"))]
        deciders = {ticked(r[0])[0]: r for r in rows_of(section(spa, "### 誰が決めるか"))}
        choose = section(profiles, "## 選び方")
        undecided = section(profiles, "## 方式が未定のとき")
        adds = section(profiles, "## 足すもの")
    except ValueError as e:
        return [f"references/profiles.md の節が無い: {e}"]
    same("profile の名前", sorted(module.PROFILES), sorted(listed))
    same("profiles/ のディレクトリ", sorted(module.PROFILES), sorted(directories))
    tables = {"screens.csv": module.SCREENS, "transitions.csv": module.TRANSITIONS}
    ours = {path: names for path, names in module.PROFILES["web-spa"]["columns"].items()}
    theirs: dict[str, list[str]] = {}
    for row in columns:
        theirs.setdefault(tables.get(ticked(row[0])[0], ticked(row[0])[0]), []).append(ticked(row[1])[0])
    same("web-spa の列", ours, theirs)
    by_name = {ticked(r[1])[0]: r for r in columns}
    same("パスの列", module.PATH_COLUMN in by_name and ticked(by_name[module.PATH_COLUMN][0])[0] == "screens.csv", True)
    same("パスを空にしてよい種別", list(module.CHILD_KINDS), ticked(by_name.get(module.PATH_COLUMN, ["", "", "", ""])[3]))
    same("種類の列", module.TAB_COLUMN in by_name and ticked(by_name[module.TAB_COLUMN][0])[0] == "transitions.csv", True)
    same("種類の値", list(module.TAB_KINDS), ticked(by_name.get(module.TAB_COLUMN, ["", "", ""])[2]))
    same("パスは / で始まる", "（`/` で始まる）" in by_name.get(module.PATH_COLUMN, ["", "", ""])[2], True)
    same("仕様書の小見出し", module.PROFILES["web-spa"]["screen"], screen)
    same("共通仕様の小見出し", module.PROFILES["web-spa"]["common"], common)
    same("節の名前", [module.PROFILE_SECTION + "<profile>"], sorted(set(re.findall(r"`## ([^`]+: <profile>)`", adds))))
    same("方式が未定の言い回し", [module.PROFILE_UNDECIDED.pattern], sorted(set(re.findall(r"`(N/A。[^`]+)`", undecided))))
    same("未設定", [module.UNSET], re.findall(r"\*\*`([^`]+)` なら、profile の列と節を求めない", choose))
    # 各項目を誰が決めるか（共有の Q&A 表か spec/qa-dev.csv か）が書いてある
    items = [n for names in module.PROFILES["web-spa"]["columns"].values() for n in names] + screen + common
    same("誰が決めるかの項目", sorted(items), sorted(deciders))
    for name, row in deciders.items():
        if not re.fullmatch(r"(`shared/qa\.csv`|`spec/qa-dev\.csv`)(・(`shared/qa\.csv`|`spec/qa-dev\.csv`))*", row[-1]):
            problems.append(f"誰が決めるか: {name} の起票する表 {row[-1]!r} が共有の Q&A 表か spec/qa-dev.csv でない")
    return problems


def reference_mismatches(module, tables: str, prose: str, boundary: str) -> list[str]:
    problems = []

    def same(what: str, ours, theirs) -> None:
        if ours != theirs:
            problems.append(f"{what}: 本体 {ours!r} ／ references {theirs!r}")

    for path, heading in ((module.SCREENS, "## 画面（`screens.csv`）"), (module.ITEMS, "## 項目（`screen-items.csv`）"),
                          (module.TRANSITIONS, "## 遷移（`transitions.csv`）")):
        if heading not in tables:
            problems.append(f"{heading} が無い")
            continue
        rows = rows_of(section(tables, heading).split("\n### ")[0])
        same(f"{path} の列", module.COLUMNS[path], [ticked(r[0])[0] for r in rows])
        same(f"{path} の空でよい列", module.MAY_BE_EMPTY[path], {ticked(r[0])[0] for r in rows if r[-1] != "いいえ"})
        same(f"{path} の置き場所", path.rsplit("/", 1)[1] in section(tables, "## 置き場所"), True)
    same("置き場所の根", module.SCREENS_DIR in tables, True)
    same("種別", list(module.SCREEN_KINDS), [ticked(r[0])[0] for r in rows_of(section(tables, "### 種別"))])
    same("入口の種別", module.ENTRY_KIND, next((ticked(r[0])[0] for r in rows_of(section(tables, "### 種別")) if "入口" in r[1]), None))
    same("項目の種類", list(module.ITEM_KINDS), [ticked(r[0])[0] for r in rows_of(section(tables, "### 項目の種類"))])
    screens = {ticked(r[0])[0]: r for r in rows_of(section(tables, "## 画面（`screens.csv`）").split("\n### ")[0])}
    same("ステータス", list(module.STATUSES), ticked(screens.get("ステータス", ["", ""])[1]))
    same("親画面を持つ種別", list(module.CHILD_KINDS), [v for v in ticked(screens.get("親画面", ["", ""])[1]) if v in module.SCREEN_KINDS])
    same("親から辿れる種別", list(module.REACHED_WITH_PARENT), re.findall(r"`(\w+)` は親の画面が辿れれば辿れる", tables))
    same("区切り", [module.SEPARATOR], re.findall(r"値を `(.)` で区切る", tables))
    items = {ticked(r[0])[0]: r for r in rows_of(section(tables, "## 項目（`screen-items.csv`）").split("\n### ")[0])}
    same("はいといいえ", list(module.YES_NO), ticked(items.get("必須", ["", ""])[1])[1:])
    same("ボタン・入力・一覧の列", [module.BUTTON, module.INPUT, module.LIST_COLUMN],
         [ticked(items.get("中身", ["", ""])[2])[0:1] and ticked(items.get("中身", ["", ""])[2])[0],
          ticked(items.get("必須", ["", ""])[1])[0:1] and ticked(items.get("必須", ["", ""])[1])[0],
          ticked(items.get("並び替え", ["", ""])[1])[0:1] and ticked(items.get("並び替え", ["", ""])[1])[0]])
    prose_rows = [r for r in rows_of(section(prose, "## 節")) if r[0].startswith("`## ")]
    same("散文の節", module.SECTIONS, [(ticked(r[0])[0][3:], r[1] == "表で持つ") for r in prose_rows])
    same("表を出す印", [module.TABLE_MARK], re.findall(r"表を出す印 `([^`]+)`", prose))
    same("共通仕様のファイル", module.COMMON in prose and module.COMMON in tables, True)
    found = re.search(r"\| `([0-9.]+)` \| `([0-9.]+)` \|", boundary)
    same("spec-loop の版の範囲", (module.SPEC_LOOP_MIN, module.SPEC_LOOP_BELOW),
         (tuple(map(int, found.group(1).split("."))), tuple(map(int, found.group(2).split(".")))) if found else None)
    same("環境変数", [module.SPEC_LOOP_ENV], re.findall(r"環境変数 `([A-Z_]+)`", boundary))
    same("記録のファイル", module.INSTALLED.split("/")[-1] in boundary, True)
    settings = section(tables, "## 案件ごとの設定（`settings.csv`）")
    same("設定のファイル", f"`{module.SETTINGS}`" in settings, True)
    same("設定の見出し行", f"見出し行は `{','.join(module.SETTINGS_COLUMNS)}`" in settings, True)
    same("設定の profile", re.findall(r"^\| `(profile)` \|.*\| `([^`]+)` \|$", settings, flags=re.MULTILINE), [(module.PROFILE_KEY, module.UNSET)])
    return problems


REFERENCE_MUTATIONS = [
    ("画面の列の名前を変える", "tables", "| `ステータス` | `下書き`・`記入中` のどちらか | いいえ |", "| `状態` | `下書き`・`記入中` のどちらか | いいえ |"),
    ("画面の列を空でよいにする", "tables", "| `主たる利用者` | 主に使う人（ロール） | いいえ |", "| `主たる利用者` | 主に使う人（ロール） | はい |"),
    ("ステータスを増やす", "tables", "`下書き`・`記入中` のどちらか", "`下書き`・`記入中`・`確定` のどれか"),
    ("種別を減らす", "tables", "| `static` | 中身の決まった表示（ヘルプ・規約） |\n", ""),
    ("入口の種別を変える", "tables", "| `top` | 入口の画面。検査はここから遷移で辿る |", "| `top` | トップの画面 |"),
    ("項目の種類を変える", "tables", "| `一覧の列` | 一覧の列。", "| `列` | 一覧の列。"),
    ("遷移の列を足す", "tables", "| `結果` | ステータスの遷移・完了の知らせ | はい |", "| `結果` | ステータスの遷移・完了の知らせ | はい |\n| `種類` | 別タブ | はい |"),
    ("区切りを変える", "tables", "値を `、` で区切る", "値を `;` で区切る"),
    ("タブを親から辿らない", "tables", "（`tab` は親の画面が辿れれば辿れる）", "（タブも遷移で辿る）"),
    ("散文の節を表で持つにする", "prose", "| `## 7. 状態` | 散文 |", "| `## 7. 状態` | 表で持つ |"),
    ("散文の節の順を変える", "prose", "| `## 10. 同時編集` | 散文 |\n| `## 11. 表示ルール` | 散文 |", "| `## 11. 表示ルール` | 散文 |\n| `## 10. 同時編集` | 散文 |"),
    ("表を出す印を変える", "prose", "表を出す印 `<!-- screen-spec: 表 -->`", "表を出す印 `<!-- table -->`"),
    ("版の下限を変える", "boundary", "| `0.93.0` | `1.0.0` |", "| `0.94.0` | `1.0.0` |"),
    ("版の上限を変える", "boundary", "| `0.93.0` | `1.0.0` |", "| `0.93.0` | `0.94.0` |"),
    ("環境変数の名前を変える", "boundary", "環境変数 `SCREEN_SPEC_SPEC_LOOP`", "環境変数 `SPEC_LOOP_DIR`"),
    ("設定の profile の既定を変える", "tables", "か `未設定` | `未設定` |", "か `未設定` | `なし` |"),
]
PROFILE_MUTATIONS = [
    ("profile を足す", "| `web-spa` | `profiles/web-spa/` |", "| `web-spa` | `profiles/web-spa/` |\n| `desktop` | `profiles/desktop/` |"),
    ("列の名前を変える", "| `screens.csv` | `パス` |", "| `screens.csv` | `ルート` |"),
    ("列の表を変える", "| `transitions.csv` | `種類` |", "| `screens.csv` | `種類` |"),
    ("種類の値を変える", "`同じタブ`・`別タブ` のどちらで", "`同じタブ`・`別タブ`・`窓` のどれで"),
    ("パスを空にしてよい種別を変える", "種別が `tab`・`dialog` のときだけ空でよい", "種別が `tab` のときだけ空でよい"),
    ("小見出しを落とす", "| `一覧の送り方` | ページ番号か", "| `送り方` | ページ番号か"),
    ("共通仕様の小見出しを変える", "| `アプリの外枠` | 共通ヘッダー", "| `外枠` | 共通ヘッダー"),
    ("言い回しを変える", "`N/A。実現方式が未定` と書いておける", "`N/A。方式が未定` と書いておける"),
    ("誰が決めるかを落とす", "| `一覧の送り方` | 利用者 | `shared/qa.csv` |\n", ""),
    ("起票する表を変える", "| `パス` | 開発者 | `spec/qa-dev.csv` |", "| `パス` | 開発者 | 開発者が決める |"),
    ("節の名前を変える", "`## 実現方式: <profile>` を 1 つ置き、下の「仕様書の小見出し」", "`## 方式: <profile>` を 1 つ置き、下の「仕様書の小見出し」"),
]


def load(path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_screens_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    killers = {killer for *_, killer in MUTATIONS}
    assert killers <= set(names), f"変異の殺す試料が無い: {killers - set(names)}"
    with tempfile.TemporaryDirectory(prefix="check-screens-test-") as tmp:
        tmp_path = Path(tmp)
        plugins = tmp_path / "plugins"
        plugin = copy_plugin(PLUGIN, plugins / "screen-spec")
        sibling = copy_spec_loop(plugins / "spec-loop")
        results = run_cases(plugin, sibling, tmp_path / "work")
        for case in CASES:
            result = results[case[0]]
            check(f"試料が期待どおりでない: {case[0]}", as_expected(case, result), f"exit={result[0]} {result[1][-500:]}")

        module = load(plugin / "scripts" / TARGET)
        docs = {"tables": (REFS / "tables.md").read_text(encoding="utf-8"), "prose": (REFS / "prose.md").read_text(encoding="utf-8"),
                "boundary": (REFS / "spec-loop.md").read_text(encoding="utf-8")}
        problems = reference_mismatches(module, docs["tables"], docs["prose"], docs["boundary"])
        check("本体の定数が references と一致しない", not problems, "; ".join(problems))
        profiles_md = (REFS / "profiles.md").read_text(encoding="utf-8")
        directories = sorted(d.name for d in (PLUGIN / "profiles").iterdir() if d.is_dir())
        problems = profile_mismatches(module, profiles_md, directories)
        check("本体の profile の定数が references/profiles.md・profiles/ と一致しない", not problems, "; ".join(problems))
        check("崩すと不一致になる: profiles/ のディレクトリを足す", bool(profile_mismatches(module, profiles_md, directories + ["desktop"])))
        for name, before, after in PROFILE_MUTATIONS:
            if profiles_md.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {profiles_md.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(profile_mismatches(module, profiles_md.replace(before, after), directories)))
        for name, which, before, after in REFERENCE_MUTATIONS:
            if docs[which].count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {docs[which].count(before)} 回現れる")
                continue
            broken = dict(docs)
            broken[which] = docs[which].replace(before, after)
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(module, broken["tables"], broken["prose"], broken["boundary"])))

        source = (PLUGIN / "scripts" / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            root = tmp_path / f"mut{index}" / "plugins"
            mutated = copy_plugin(PLUGIN, root / "screen-spec")
            copy_spec_loop(root / "spec-loop")
            (mutated / "scripts" / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            case = next(c for c in CASES if c[0] == killer)
            result = run_cases(mutated, root / "spec-loop", tmp_path / f"mutwork{index}", only=killer)[killer]
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(case, result), result[1][-300:])

        problems = oo_problems(plugin, tmp_path)
        check("-OO の引数なしで使い方の誤り（2）にならない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(OO_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_plugin(PLUGIN, tmp_path / f"oo-mut{index}" / "screen-spec")
            (mutated / "scripts" / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(oo_problems(mutated, tmp_path)))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(OO_MUTATIONS)} 件・references の崩し {len(REFERENCE_MUTATIONS) + len(PROFILE_MUTATIONS) + 1} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
