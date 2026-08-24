#!/bin/sh
# このリポジトリのスキルを、Claude Code の skills ディレクトリへ素のスキルとして symlink する。
#
#   usage: scripts/link-skills.sh [-d <skills-dir>] [-n] [<name> ...]
#
#     <name>   対象のスキル名（省略時は plugins/ 配下の全スキル）
#     -d DIR   置き場所（省略時は $HOME/.claude/skills = 全プロジェクトで有効）
#     -n       何をするかだけ表示して、実際には変更しない
#
# なぜスクリプトにしてあるか（#57）:
#
# 同じ手順を README と docs に手で複製していたところ、4 ラウンド連続で実バグが出た。しかも
# 毎回「前ラウンドの修正が次の穴を開ける」形だった（警告の位置 → `.bak` 衝突と `-d` すり抜け
# → clone 未確認 → clone ガードが相対パスで素通り）。手続きを 1 箇所に集めてテストを当てる。
#
# 設計上の要点:
#
# 1. **ソースのパスを人間に入力させない。** スクリプト自身の位置からリポジトリルートを解決する。
#    #56 の HIGH は「利用者が書いた `repo=` が相対パスだとガードを素通りする」ものだった
#    （`ln -s` は第 1 引数をそのまま保存し、相対リンクは*リンクの置き場所*から解決されるのに、
#    ガードは*カレントディレクトリ*基準で評価されていた）。入力を無くせばこの類は消える。
# 2. **張った後に必ず解決を確認する。** ガードを増やすより、結果を検査するほうが漏れにくい。
# 3. **退避先の名前は必ず未使用にする。** 同一秒に衝突すると `mv` が黙って上書きすることがある。
# 4. **失敗したら黙って終わらない。** メッセージは stderr、終了コードは非 0。
#
# POSIX sh で書く（bash / zsh / dash で同じ挙動にするため）。

set -u

usage() {
	cat <<'USAGE'
usage: scripts/link-skills.sh [-d <skills-dir>] [-n] [<name> ...]

  <name>   対象のスキル名（省略時は plugins/ 配下の全スキル）
  -d DIR   置き場所（省略時は $HOME/.claude/skills）
  -n       変更せず、何をするかだけ表示する
USAGE
}

warn() {
	printf '%s\n' "$*" >&2
}

# スクリプト自身の位置からリポジトリルートを解決する。
# CDPATH を潰し、pwd -P で絶対パスにする（symlink 経由で呼ばれても実体の絶対パスになる）。
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || {
	warn "中止: スクリプトの位置を解決できませんでした。"
	exit 1
}
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd -P) || {
	warn "中止: リポジトリルートを解決できませんでした。"
	exit 1
}

skills_dir=""
# 「-d が渡されていない」と「-d に空文字列が渡された」を区別する。
# 混同すると `-d "$SOMEDIR"` で SOMEDIR 未設定のとき、黙って $HOME/.claude/skills が対象になる。
skills_dir_given=0
dry_run=0

while [ $# -gt 0 ]; do
	case $1 in
	-d)
		[ $# -ge 2 ] || {
			warn "中止: -d には置き場所を渡してください。"
			exit 2
		}
		skills_dir=$2
		skills_dir_given=1
		shift 2
		;;
	-n)
		dry_run=1
		shift
		;;
	-h | --help)
		usage
		exit 0
		;;
	--)
		shift
		break
		;;
	-*)
		warn "中止: 不明なオプション: $1"
		usage >&2
		exit 2
		;;
	*)
		break
		;;
	esac
done

if [ "$skills_dir_given" -eq 1 ]; then
	# 空を既定値へのフォールバックにしない（実環境が対象になってしまう）
	if [ -z "$skills_dir" ]; then
		warn "中止: -d に空の値が渡されました。置き場所を明示してください。"
		exit 2
	fi
else
	# HOME が未設定・空なら置き場所を決められない
	if [ -z "${HOME:-}" ]; then
		warn "中止: HOME が設定されていません。-d で置き場所を指定してください。"
		exit 2
	fi
	skills_dir=$HOME/.claude/skills
fi

# 対象のスキル名を決める。引数が無ければ plugins/<name>/skills/<name>/SKILL.md を持つものすべて。
#
# 名前は文字列に連結せず**位置パラメータ**に積む。文字列にして `for name in $names` で回すと、
# **zsh は未クォートの変数展開を語分割しない**ため 1 個の名前として扱われる（実際に踏んだ）。
# 位置パラメータなら sh / bash / zsh / dash で同じに回る。
if [ $# -eq 0 ]; then
	for dir in "$repo_root"/plugins/*/; do
		[ -d "$dir" ] || continue
		name=$(basename -- "$dir")
		[ -f "$dir/skills/$name/SKILL.md" ] || continue
		set -- "$@" "$name"
	done
	if [ $# -eq 0 ]; then
		warn "中止: $repo_root/plugins/ に skills/<name>/SKILL.md を持つプラグインがありません。"
		exit 1
	fi
fi

failed=0
linked=0

for name in "$@"; do
	src=$repo_root/plugins/$name/skills/$name
	target=$skills_dir/$name

	# スキル名は 1 つのディレクトリ名。スラッシュや `..` を許すと、連結先が
	# plugins/ の外や skills ディレクトリの外を指す（`cmux/../cmux` は ln まで到達していた）。
	# 連結先に SKILL.md が無いので結果的には止まるが、それは偶然なので明示的に弾く。
	case $name in
	"" | . | .. | */*)
		warn "中止 ($name): スキル名は 1 つのディレクトリ名で指定してください。"
		failed=1
		continue
		;;
	esac

	# 素のスキルとして置けるのは、マニフェストを持たないものだけ。
	# `.claude-plugin/` を持つものを置くと、名前空間付き（<name>:<skill>）になってしまう。
	if [ ! -f "$src/SKILL.md" ]; then
		warn "中止 ($name): $src/SKILL.md がありません。"
		failed=1
		continue
	fi
	if [ -e "$src/.claude-plugin" ]; then
		warn "中止 ($name): $src に .claude-plugin があります。素のスキルとして置くと名前空間が付きます。"
		failed=1
		continue
	fi

	if [ "$dry_run" -eq 1 ]; then
		printf '%s -> %s\n' "$target" "$src"
		continue
	fi

	if ! mkdir -p -- "$skills_dir"; then
		warn "中止 ($name): $skills_dir を作れませんでした。"
		failed=1
		continue
	fi

	# 既にあるものをどかす。
	# -e は壊れた symlink に対して偽になるので、-L を先に見る。
	if [ -L "$target" ]; then
		if ! rm -f -- "$target"; then
			warn "中止 ($name): 既存の symlink $target を外せませんでした。"
			failed=1
			continue
		fi
	elif [ -e "$target" ]; then
		# 退避先は必ず未使用の名前にする（同一秒の衝突で黙って上書きしないため）
		ts=$(date +%Y%m%d%H%M%S 2>/dev/null || echo backup)
		backup=$target.bak.$ts
		n=1
		while [ -e "$backup" ] || [ -L "$backup" ]; do
			backup=$target.bak.$ts.$n
			n=$((n + 1))
		done
		if ! mv -- "$target" "$backup"; then
			warn "中止 ($name): $target を退避できませんでした。手で移動してから再実行してください。"
			failed=1
			continue
		fi
		printf '退避: %s -> %s\n' "$target" "$backup"
	fi

	if ! ln -s -- "$src" "$target"; then
		warn "中止 ($name): symlink を張れませんでした ($target)。"
		failed=1
		continue
	fi

	# ガードを足すより、結果を検査するほうが漏れにくい。
	# 相対パスや壊れた参照は、ここで必ず捕まる。
	if [ ! -f "$target/SKILL.md" ]; then
		warn "中止 ($name): 張った symlink が解決しません ($target -> $src)。"
		rm -f -- "$target"
		failed=1
		continue
	fi

	printf '%s -> %s\n' "$target" "$src"
	linked=$((linked + 1))
done

if [ "$dry_run" -eq 0 ] && [ "$linked" -gt 0 ]; then
	printf '\n次のセッションから、名前空間の付かない名前で呼べます（例: /%s）。\n' "$1"
fi

exit "$failed"
