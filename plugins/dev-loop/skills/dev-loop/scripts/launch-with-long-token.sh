#!/bin/bash
# 長期トークン（`claude setup-token`）で claude を起動する起動口（#584）。
#
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh [claude の引数 ...]
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh --store-token   # 入れる・入れ替える
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh --status        # 入っているか
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh --account <名前> [上のどれか]
#
# --account <名前>: アカウントごとに別の項目（サービス名 claude-long-token-<名前>）を使う。名前は英数字で始め、英数字と . _ -（`-` で始まる名前は断る）。**--account は最初に置く**——ほかの位置（`--account=…` の形も）にあれば止まる（2）。--store-token・--status の後ろに引数があっても止まる（2）。
#   週の上限に近いアカウントから別のアカウントに切り替えて起動し直すため（利用者の指示 2026-10-29。
#   切り替えるのは利用者で、cruise は切り替えない）。付けなければ claude-long-token。
#
# macOS のキーチェーン（サービス名 claude-long-token）からトークンを読み、
# CLAUDE_CODE_OAUTH_TOKEN に入れて claude を起動する（引数はそのまま渡す——
# `… launch-with-long-token.sh "/dev-loop:cruise 474 --absent"` で cruise から始められる）。
# **この端末で起動する claude だけに効かせる**——.zshrc・.env・リポジトリに置かない。
# 入れ方と、確かめていないことは公開ページを正とする:
# https://hdknr.github.io/claude-code-setup/usage/cruise-long-lived-token/
#
# なぜ要るか: 対話ログイン（/login）の OAuth のアクセストークンは 8 時間で切れ、
# 更新に失敗すると不在の cruise が 401 で止まる（#584 で Mac Studio を測った）。
#
# --store-token: キーチェーンに入れる（在れば入れ替える。security add-generic-password -U … -w）。
#   **値は security のプロンプトに貼らせ、引数・表示・このスクリプトの変数に載せない**
#   （man security: 「-w を最後に置くと prompt される（recommended）」）。**Claude Code のセッションの中で走らせない**——
#   別の端末で `claude setup-token` を走らせ、表示されたトークンをそのプロンプトに貼る。
#   コメントに入れた日時（UTC）を残す——**トークンの発行日・期限ではない**（期限は手元からは読めない）。
# --status: 項目が在るかと、入れた日時（コメント）だけを出す。値は読まない（-w を付けない）。
#
# 守る:
#   - **トークンが読めなければ、claude を起動せずに理由を出して止まる**——対話ログインのまま起動すると、
#     気づかないまま 8 時間で止まる状態に戻る。項目が無い・値が空・security が無い・macOS でない。
#     **項目が無い（44）とほかの理由で読めない（ロック・拒否）を分けて言う**——後者は入れ直しても直らない
#   - **長期トークンより先に使われる認証が環境にあれば止まる**——ANTHROPIC_AUTH_TOKEN は
#     CLAUDE_CODE_OAUTH_TOKEN より先に使われ、承認済みの ANTHROPIC_API_KEY は OAuth より先に使われる
#     （Claude Code 2.1.312 の本体の文字列で読んだ。版が変われば変わりうる）
#   - **トークンを出力に出さない**——表示・ログ・引数（ps に出る）に載せない。環境変数で渡す
#   - 環境に別の CLAUDE_CODE_OAUTH_TOKEN が既にあっても、キーチェーンの値で上書きする
#   - **--store-token を Claude Code のセッションの中（CLAUDECODE=1）では走らせない**——止まる（2）
#
# 守らない:
#   - トークンが有効か（期限切れ・取り消し）——起動してみるまで分からない。切れていれば起動した claude が 401 を出す
#   - 長期トークンで cruise のどの機能が動くか——公開ページの測る表
#   - security のプロンプトが入力を画面に出さないこと——man に書いていない。試していない
#   - macOS 以外のキーチェーン
#
# 終了コード: 起動したら claude の終了コード（exec するので claude そのもの）。起動しなかったら
#   2: トークンが読めない（項目が無い（security の 44）・ほかの理由で読めない・値が空・security が無い・macOS でない）。
#      --status で項目が無い・読めない。--account の名前が不正・最初に無い
#   3: 長期トークンより先に使われる認証が環境にある
#   --store-token は security の終了コード

# 受け継いだ xtrace（SHELLOPTS・BASH_ENV の set -x）でトークンを標準エラーに出さない
set +x
SERVICE="claude-long-token"
ACCT=""
if [ "$1" = "--account" ]; then
    # 文字列全体で照合する（grep は行ごとなので、改行を含む名前を通してしまう）
    if ! [[ "$2" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
        echo "launch-with-long-token: --account の名前は英数字で始め、英数字と . _ - だけ（受け取った: '$2'）" >&2
        exit 2
    fi
    SERVICE="claude-long-token-$2"
    ACCT="--account $2 "
    shift 2
fi
for arg in "$@"; do
    if [ "$arg" = "--account" ] || [ "${arg#--account=}" != "$arg" ]; then
        # 先頭でないと黙って既定の項目を使う（--store-token なら既定の項目を上書きする）ので、止める
        echo "launch-with-long-token: --account は最初に置く（例: --account work --store-token）" >&2
        exit 2
    fi
done
PAGE="https://hdknr.github.io/claude-code-setup/usage/cruise-long-lived-token/"

stop() {
    code=$1
    shift
    {
        echo "launch-with-long-token: claude を起動しない——$*"
        echo "  手順: $PAGE"
    } >&2
    exit "$code"
}

if [ "$(uname -s)" != "Darwin" ]; then
    stop 2 "macOS のキーチェーンだけを読む（uname: $(uname -s)）"
fi
if ! command -v security >/dev/null 2>&1; then
    stop 2 "security コマンドが無い"
fi

case "$1" in
--store-token | --status)
    if [ $# -gt 1 ]; then
        # 後ろの引数は使わない——黙って捨てると、別のアカウントのつもりで既定の項目を上書きする
        echo "launch-with-long-token: $1 の後ろに引数を置かない（アカウントは最初に --account <名前>）" >&2
        exit 2
    fi
    ;;
esac
case "$1" in
--store-token)
    if [ "$CLAUDECODE" = "1" ]; then
        # セッションの Bash から走らせると、入れる値がセッションの記録を通りうる
        stop 2 "Claude Code のセッションの中では入れない——別の端末で bash $0 ${ACCT}--store-token を走らせる"
    fi
    echo "別の端末（Claude Code の外）で claude setup-token を走らせ、表示されたトークンを次のプロンプトに貼る。"
    echo "キーチェーンの $SERVICE に入れる（在れば入れ替える）。"
    exec security add-generic-password -U -a "$USER" -s "$SERVICE" \
        -j "launch-with-long-token.sh --store-token $(date -u +%Y-%m-%dT%H:%M:%SZ)" -w
    ;;
--status)
    attrs=$(security find-generic-password -s "$SERVICE" 2>/dev/null)
    rc=$?
    if [ "$rc" -eq 44 ]; then
        echo "キーチェーンに $SERVICE が無い（入れる: bash $0 ${ACCT}--store-token）"
        exit 2
    elif [ "$rc" -ne 0 ]; then
        echo "キーチェーンの $SERVICE を読めなかった（security の終了コード $rc——キーチェーンのロック・アクセスの拒否など）"
        exit 2
    fi
    stored=$(printf '%s\n' "$attrs" | sed -n 's/^ *"icmt"<blob>="\(.*\)"$/\1/p')
    echo "キーチェーンに $SERVICE が在る（入れた記録: ${stored:-無い}）——トークンの発行日・期限ではない。有効かは起動して確かめる"
    exit 0
    ;;
esac

for name in ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY; do
    if [ -n "${!name}" ]; then
        stop 3 "$name が環境にある——長期トークンより先に使われうる。この端末で unset $name してから起動し直す"
    fi
done

# 値はコマンド置換で変数に受けるだけ。表示しない
token=$(security find-generic-password -s "$SERVICE" -w 2>/dev/null)
rc=$?
if [ "$rc" -eq 44 ]; then
    stop 2 "キーチェーンに $SERVICE が無い（入れる: bash $0 ${ACCT}--store-token）"
elif [ "$rc" -ne 0 ]; then
    # 44 のほか（ロック・ダイアログの拒否など）を「無い」と言わない——入れ直しても直らない
    stop 2 "キーチェーンの $SERVICE を読めなかった（security の終了コード $rc——キーチェーンのロック・アクセスの拒否など。security unlock-keychain を確かめる）"
fi
if [ -z "$token" ]; then
    stop 2 "キーチェーンの $SERVICE の値が空"
fi

export CLAUDE_CODE_OAUTH_TOKEN="$token"
unset token
exec claude "$@"
