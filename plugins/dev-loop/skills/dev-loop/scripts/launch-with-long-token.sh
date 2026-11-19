#!/bin/bash
# 長期トークン（`claude setup-token`）で claude を起動する起動口（#584）。
#
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh [claude の引数 ...]
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh --store-token   # 入れる・入れ替える
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh --status        # 入っているか
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh --account <名前> [上のどれか]
#     bash <このスキルの base ディレクトリ>/scripts/launch-with-long-token.sh --install-launcher [置く場所]   # 版を含まない短い起動口を置く
#
# **1 本のコマンドで足りる**（#1287）: キーチェーンに項目が無くても、**対話の端末（標準入力が端末）で、Claude Code のセッションの外なら、
#   --store-token と同じ入力を求めて登録し、そのまま起動する**。別の端末で --store-token を先に打つ必要は無い。
#   非対話（claude -p を起こす外側のループなど）・セッションの中では、今までどおり止まる。
#   `claude setup-token` はブラウザの認証なので自動化しない——別のタブで走らせ、表示されたトークンを入力に貼る。
# --install-launcher [置く場所]: 版を含まない起動口 dev-loop-cruise を置く（既定は ~/.local/bin。置いたものは呼ぶたびに、
#   入っている dev-loop プラグインの最新の版のこのスクリプトを探して呼ぶ——プラグインを更新しても、打つコマンドは変わらない）。
#   使い方: dev-loop-cruise <親 Issue> [--absent]（= このスクリプトに "/dev-loop:cruise <親 Issue> [--absent]" を渡す）・
#   dev-loop-cruise [--account <名前>] --store-token|--status。**--account は最初に置く**。
#   置いた起動口でないファイルが同じ名前で在れば（切れたシンボリックリンクも）、上書きせず止まる（2）。
#   **cruise の引数は、最初が親 Issue の番号、残りは --absent のような長いオプション（空白を含む語・claude の引数は止まる（2））。
#   --account・--store-token・--status・--install-launcher は、cruise の引数の位置に置けない**（止まる（2）。1 本の語にまとめるので、本体の「--account は最初」の検査をすり抜けるため）。**--account と一緒には使わない**（実行時に渡す）。
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
#   Claude Code の外（別のタブでよい）で `claude setup-token` を走らせ、表示されたトークンをそのプロンプトに貼る。
#   **起動のときの登録（上の 1 本のコマンド）も同じ入力で、同じ守りを掛ける。**
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
#   - **起動のときの登録に進むのは、項目が無い（44）・標準入力が端末・Claude Code のセッションの外の 3 つが揃うときだけ**——
#     ほかの読めない理由（ロック・拒否）では進まない（入れ直しても直らない）。登録が失敗したら起動せずに止まる（2）
#   - **--install-launcher は、置いた起動口でないファイルを上書きしない**（2）。トークンには触れない
#
# 守らない:
#   - トークンが有効か（期限切れ・取り消し）——起動してみるまで分からない。切れていれば起動した claude が 401 を出す
#   - 起動のときの登録の入力が、画面に出ないこと・Ctrl-C で途中で止めたときの項目の状態（--store-token と同じ security のプロンプト）
#   - 置いた起動口の PATH——置く場所が PATH に無ければ、その旨を出すだけ
#   - 長期トークンで cruise のどの機能が動くか——公開ページの測る表
#   - 起動したセッションの Bash の環境にトークンが見えること——Claude Code 2.1.316 は起動時の CLAUDE_CODE_OAUTH_TOKEN を
#     Bash の環境から外す。長期トークンで起動したかは /status か check-unattended-env.py の「認証」で見る（env で見ない）
#   - security のプロンプトが入力を画面に出さないこと——man に書いていない。試していない
#   - macOS 以外のキーチェーン
#
# 終了コード: 起動したら claude の終了コード（exec するので claude そのもの）。起動しなかったら
#   2: トークンが読めない（項目が無い（security の 44。登録に進めない形のとき）・ほかの理由で読めない・値が空・security が無い・macOS でない）・
#      起動のときの登録が失敗した。--status で項目が無い・読めない。--account の名前が不正・最初に無い。
#      --install-launcher が置けない（名前が使われている・引数が不正・書けない）
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
LAUNCHER_MARK="# launch-with-long-token.sh --install-launcher が置いた起動口"

if [ "$1" = "--install-launcher" ]; then
    if [ -n "$ACCT" ]; then
        echo "launch-with-long-token: --install-launcher は --account と一緒に使わない（置いた起動口に --account を渡す）" >&2
        exit 2
    fi
    if [ $# -gt 2 ]; then
        echo "launch-with-long-token: --install-launcher の後ろは置く場所 1 つだけ" >&2
        exit 2
    fi
    dir="${2:-$HOME/.local/bin}"
    target="$dir/dev-loop-cruise"
    if [ -L "$target" ] || { [ -e "$target" ] && ! grep -qF -- "$LAUNCHER_MARK" "$target" 2>/dev/null; }; then
        # シンボリックリンクは、リンク先が起動口でも断る——cat > がリンク先（別の場所）に書く
        echo "launch-with-long-token: $target がシンボリックリンクか、このスクリプトが置いた起動口ではないファイル——上書きしない（置く場所を変えるか、消してから）" >&2
        exit 2
    fi
    mkdir -p "$dir" || exit 2
    # 引用符つきの here-document——中の $ は置くときに展開せず、起動口が走るときに展開する
    cat >"$target" <<'LAUNCHER_EOF' || exit 2
#!/bin/bash
# launch-with-long-token.sh --install-launcher が置いた起動口（書き直すなら --install-launcher を打ち直す）
#
#     dev-loop-cruise <親 Issue> [--absent]                    # cruise を長期トークンで起動する
#     dev-loop-cruise [--account <名前>] --store-token|--status
#
# 版を含まない。呼ぶたびに、入っている dev-loop プラグインのいちばん新しい版の launch-with-long-token.sh を探して呼ぶ。
base="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/cache/claude-code-setup/dev-loop"
script=$(ls -d "$base"/*/skills/dev-loop/scripts/launch-with-long-token.sh 2>/dev/null | sort -V | tail -1)
if [ -z "$script" ]; then
    echo "dev-loop-cruise: dev-loop プラグインの launch-with-long-token.sh が見つからない（$base）" >&2
    exit 2
fi
account=()
if [ "$1" = "--account" ]; then
    if [ $# -lt 2 ]; then
        echo "dev-loop-cruise: --account の後ろに名前を置く" >&2
        exit 2
    fi
    account=(--account "$2")
    shift 2
fi
case "$1" in
--store-token | --status)
    exec bash "$script" "${account[@]}" "$@"
    ;;
"")
    echo "使い方: dev-loop-cruise [--account <名前>] <親 Issue> [--absent] ／ dev-loop-cruise [--account <名前>] --store-token|--status" >&2
    exit 1
    ;;
esac
for arg in "$@"; do
    case "$arg" in
    --account | --account=* | --store-token | --status | --install-launcher)
        # 1 本の語 "/dev-loop:cruise …" にまとめると、本体の「--account は最初に置く」の検査をすり抜け、cruise の引数に混ざる
        echo "dev-loop-cruise: $arg は cruise の引数に置けない（--account は最初、--store-token・--status は --account の次）" >&2
        exit 2
        ;;
    esac
done
# 最初は親 Issue の番号、残りは --absent のような長いオプションだけ（空白を含む 1 語・claude の引数（-p など）を 1 本の語に混ぜない）
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "dev-loop-cruise: 最初の引数は親 Issue の番号（例: dev-loop-cruise 1290 --absent。受け取った: '$1'）" >&2
    exit 2
fi
for arg in "${@:2}"; do
    if ! [[ "$arg" =~ ^--[a-z][a-z-]*$ ]]; then
        echo "dev-loop-cruise: 親 Issue の番号の後ろは --absent のようなオプションだけ（受け取った: '$arg'）" >&2
        exit 2
    fi
done
exec bash "$script" "${account[@]}" "/dev-loop:cruise $*"
LAUNCHER_EOF
    chmod +x "$target" || exit 2
    echo "置いた: $target"
    case ":$PATH:" in
    *":$dir:"*) ;;
    *) echo "  $dir は PATH に無い——.zshrc などで PATH に足すか、$target を絶対パスで呼ぶ" ;;
    esac
    echo "  使い方: dev-loop-cruise <親 Issue> [--absent]（キーチェーンに未登録なら、その場で入れてから起動する）"
    exit 0
fi

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
# キーチェーンに入れる（--store-token と、起動のときの登録が使う）。値は security のプロンプトに貼らせる
store_token() {
    echo "Claude Code の外（別のタブでよい）で claude setup-token を走らせ、表示されたトークンを次のプロンプトに貼る。"
    echo "キーチェーンの $SERVICE に入れる（在れば入れ替える）。"
    security add-generic-password -U -a "$USER" -s "$SERVICE" \
        -j "launch-with-long-token.sh --store-token $(date -u +%Y-%m-%dT%H:%M:%SZ)" -w
}

case "$1" in
--store-token)
    if [ "$CLAUDECODE" = "1" ]; then
        # セッションの Bash から走らせると、入れる値がセッションの記録を通りうる
        stop 2 "Claude Code のセッションの中では入れない——Claude Code の外で bash $0 ${ACCT}--store-token を走らせる"
    fi
    store_token
    exit $?
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
read_token() {
    token=$(security find-generic-password -s "$SERVICE" -w 2>/dev/null)
    rc=$?
}
read_token
if [ "$rc" -eq 44 ] && [ -t 0 ] && [ "$CLAUDECODE" != "1" ]; then
    # 項目が無い・対話の端末・Claude Code のセッションの外が揃うときだけ、登録に進んでから起動する（#1287）。
    # 44 のほか（ロック・拒否）では進まない——入れ直しても直らない
    echo "キーチェーンに $SERVICE が無い——登録してから起動する。"
    store_token
    store_rc=$?
    if [ "$store_rc" -ne 0 ]; then
        stop 2 "キーチェーンの $SERVICE に入れられなかった（security の終了コード $store_rc）"
    fi
    read_token
fi
if [ "$rc" -eq 44 ]; then
    stop 2 "キーチェーンに $SERVICE が無い（Claude Code の外の対話の端末で bash $0 ${ACCT}\"/dev-loop:cruise <親> [--absent]\" を打てば、登録してから起動する。入れるだけなら bash $0 ${ACCT}--store-token）"
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
