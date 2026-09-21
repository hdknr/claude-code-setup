#!/usr/bin/env bash
# 新規の周のために、規約どおりの worktree を作って確かめる。
#
#     bash <このスキルの base ディレクトリ>/scripts/prepare-worktree.sh <issue-number> <説明>
#
# **置き場所に理由がある。** `dev-loop` は**どのリポジトリでも使うスキル**なので、
# **対象リポジトリの `scripts/` に置いてはならない**——そこに在るとは限らない。
# **一度そこに置いて PR に出し、マージ後に気づいた**（#136 段 1）。
#
# ## このスクリプトがやらないこと
#
# **`EnterWorktree` は呼べない。** あれはハーネスの道具で、シェルからは起動できない。
# **このスクリプトは worktree を*作って確かめる*ところまで**で、
# **セッションをそこへ入れるのは道具の仕事**である。作ったあとに
# `EnterWorktree` へ `path` を渡すこと。
#
# **既存の worktree には入らない。** 再開の周は形が違う——
# **`find-cycle.py` で探し、`references/resume.md` に従う。**
# **このスクリプトは、当たるものが無かったときだけ使う。**
#
# ## 何を守るか
#
# - **先に見る。** 同じ番号の worktree / ブランチが在れば**作らずに止まる**
#   （**再開の周を新規として踏み潰さない**）。
#   **当たり方は部分一致で、広い**——`issue-9` は `issue/99-foo` にも当たる。
#   **失敗する側は安全**（新しい周を再開の道へ送るだけで、踏み潰さない）だが、
#   **広いことは隠さない**（`find-cycle.py` と同じ扱い）。
# - **root を解決できなかったら作らない**（終了コード 5）。
#   **「無い」と「見られなかった」は別である。**
# - **既存の一覧を見られなかったら作らない**（終了コード 6）。
#   **5 と別の番号にする**——**同じにすると、片方を壊しても他方が同じ答えを返し、
#   変異が殺せない。** **どちらにも専用の観測と変異がある**（後者は偽の `git` を使う）。
# - **絶対パスで組み立てる。** 相対パスはシェルの cwd を起点に解決されるので、
#   別の worktree の中から走らせると**入れ子で生える**。
# - **メインの作業ツリーを `--path-format=absolute` で解決する。**
#   **`--git-common-dir` は相対で返ることがあり、その相対は cwd を起点にする**
#   ——root を起点に解決すると、**サブディレクトリから走らせたときに
#   リポジトリの*親*を指す**（実測で再現した）。
# - **規約どおりの名前で切る。** `issue/<番号>-<説明>`。
#   **道具に任せると `worktree-` 接頭辞が付いて規約から外れる**（#96 で 3 例）。
# - **start-point を渡して切る。** `git worktree add -b` は **start-point を省略すると
#   HEAD に落ちる**（`man git-worktree`: 「If `<commit-ish>` is omitted, it defaults to HEAD」）
#   ので、**手元の既定ブランチが古いと周の全部が古い原本の上で進む**（#148）。
#   **既定ブランチのリモート追跡参照を解決して渡す。**
# - **切る前に取り直す。** リモート追跡参照そのものが古ければ、start-point を渡しても古い。
#   **最善努力である**——**オフラインでも止めない**が、**取り直せなかったことは黙らない。**
# - **`origin` が無ければ、HEAD から切ったことを言う。** ローカルだけのリポジトリでは
#   解決できるものが無い。**黙って HEAD に落ちるのが #148 の欠陥そのもの**なので、
#   **落ちたこと自体を出力する。** **「無い」と「見られなかった」は別である。**
# - **切ったブランチに upstream を付けない。** リモート追跡参照を start-point にすると
#   **既定で upstream が `origin/<既定>` に設定される**（実測）。すると `status -sb` が
#   `[ahead N, behind M]` を出し、**設定次第で `git pull` が既定ブランチをこの周に
#   マージしうる**——**他人のマージ済みの作業が周に入る**（不変条件 A の破れ）。
#   **`--no-track` で付けない。**
# - **解決した start-point が壊れていたら、死なずに言う。** `git symbolic-ref` は
#   **dangling な `origin/HEAD`** でも成功する。**そのまま渡すと `git worktree add` が
#   `fatal` で死に、終了コードが文書化した集合の外に出る。**
# - **関門に渡す base を、完全な SHA で出力する。** 周の base は**切った時点の分岐点**で、
#   **関門にはこの SHA をそのまま渡す**（`SKILL.md` 手順 4 が正）。
#   **短縮形では渡す先で曖昧になりうる**ので、**完全な SHA で出す。**
# - **肯定的な確認の材料を出す。** 作って終わりにしない——
#   **実際のブランチ名と起点コミットを出力し、呼んだ側が計画ファイルと突き合わせられるようにする。**
#   **「切ったブランチ名と一致するか」を自分で比べても意味が無い**（`-b` で切った直後なので
#   必ず一致する）。**突き合わせる相手は計画ファイルの側にある。**
#
# ## 何を守らないか
#
# - **`--path-format=absolute` は git 2.31 以降でしか使えない。**
#   **古い git では終了コード 5 になり、「root を解決できない」と出る**
#   ——**リポジトリは正常なのに、そう見える。** **版の要求はここに書いてある。**
# - **`EnterWorktree` / `ExitWorktree` の意味論**——呼べないので何も言えない。
#   **条件は `SKILL.md` 手順 4 と `references/resume.md` を正とする。**
# - **未コミットの変更の移送**——`SKILL.md` 手順 4 の移送手順を正とする
#   （**裸の `git stash` を使わない**理由も含めて、あちらにある）。
# - **入場そのもの**——上記。
# - **ssh リモートで取り直しが固まらないこと**——**測っていない。**
#   `BatchMode=yes` と `ConnectTimeout` を渡してはいるが、**確かめたのは https だけ**である。
#   **「固まらない」と書かない。**
# - **取り直しが成功したかどうかで、切るのをやめること**——**やめない。**
#   **オフラインの周を止めてはならない。** **古いかもしれないことを出力して続ける。**
# - **既定ブランチの推測が当たること**——`refs/remotes/origin/HEAD` が無いクローンでは
#   `origin/main` → `origin/master` の順に**推測する**。**推測したことは出力する。**
# - **既存の一覧を取る側が、通常の運用で失敗すること**——**`git rev-parse` が成功していれば
#   まず起きない。** **背後の守りとして置いてある。**
#   **一度ここに「テストは root の守りを壊したときにこちらが受け止める形で当てている」と
#   書いたが、それは誤りだった**——**3 巡目の Verifier が、この守りを壊してもテストが
#   全項目 ok のままであることを実験で示した。** **いまは偽の `git` を使って
#   直接当てている**（`scripts/test-worktree-scripts.py`）。

set -euo pipefail

NUMBER="${1:?使い方: bash prepare-worktree.sh <issue-number> <説明>}"
SLUG="${2:?使い方: bash prepare-worktree.sh <issue-number> <説明>}"

if ! printf '%s' "$NUMBER" | grep -Eq '^[0-9]+$'; then
  echo "Issue 番号は数字だけで指定する: $NUMBER" >&2
  exit 2
fi

# **`--path-format=absolute` で取る。** `--git-common-dir` は**相対で返ることがあり、
# その相対は*cwd*を起点にする**——**リポジトリの root ではない。**
# 一度 `$ROOT` を起点に解決しており、**メインの作業ツリーのサブディレクトリから
# 走らせると `MAIN` がリポジトリの*親*になっていた**（実測で再現。`/code-review` が指摘）。
# **結果、リポジトリの外に `.claude/worktrees/` を作ろうとする**
# ——実リポジトリなら `~/Projects/hdknr/` である。
if ! COMMON="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
  echo "git でリポジトリを解決できなかった。作らない。" >&2
  exit 5
fi
MAIN="$(cd "$(dirname "$COMMON")" && pwd -P)"

BRANCH="issue/${NUMBER}-${SLUG}"
PATH_ABS="${MAIN}/.claude/worktrees/issue-${NUMBER}"

echo "メインの作業ツリー: ${MAIN}"
echo "作ろうとしているもの: ${PATH_ABS}  [${BRANCH}]"
echo

# **先に見る。** 当たったら作らない。
if ! WT_ALL="$(git worktree list 2>/dev/null)" || ! BR_ALL="$(git branch --all --list "*${NUMBER}*" 2>/dev/null)"; then
  echo "git で既存の worktree / ブランチを見られなかった。作らない。" >&2
  echo "**「当たらなかった」とは答えない**——見られていない。" >&2
  # **root の解決とは別の終了コードにする。** 同じにすると**2 つの守りが
  # 区別できず、片方を壊しても他方が同じ答えを返して変異が殺せない**
  # （実際にそうなっていた）。
  exit 6
fi
EXISTING_WT="$(printf '%s\n' "$WT_ALL" | grep -F "issue-${NUMBER}" || true)"
EXISTING_BR="$BR_ALL"
if [ -n "$EXISTING_WT" ] || [ -n "$EXISTING_BR" ]; then
  echo "既に当たるものがある。**作らない。**" >&2
  [ -n "$EXISTING_WT" ] && echo "  worktree:" && printf '    %s\n' "$EXISTING_WT" >&2
  [ -n "$EXISTING_BR" ] && echo "  ブランチ:" && printf '    %s\n' "$EXISTING_BR" >&2
  echo >&2
  echo "再開の周かもしれない。find-cycle.py で探し、references/resume.md に従うこと。" >&2
  exit 3
fi

# **取り直しは「先に見る」より*後*である。** **断る周（終了コード 3）で
# ネットワークに出ないため**（`/code-review` の指摘。#148）。
# **解決より*前*でもある**——**一度も fetch していないクローンでは、
# 取り直して初めて `origin/*` が生える。**
#
# **名指しされた参照がリモート追跡参照でなければ、取り直しても変わらない**ので打たない
# （`DEV_LOOP_BASE_REF` に**ローカルのブランチ**を渡す「積んだ周」がこれに当たる）。
NEED_FETCH=1
if [ -n "${DEV_LOOP_BASE_REF:-}" ]; then
  case "$(git rev-parse --symbolic-full-name "$DEV_LOOP_BASE_REF" 2>/dev/null)" in
    refs/remotes/*) NEED_FETCH=1 ;;
    *)              NEED_FETCH=0 ;;
  esac
fi

# **最善努力**——**オフラインでも止めない。**
# **`GIT_TERMINAL_PROMPT=0`** は **https** の入力待ちを止める。
# **`BatchMode=yes` と `ConnectTimeout`** は **ssh** の passphrase / 未知のホスト鍵の
# 入力待ちを止める——**片方だけでは、鍵に passphrase が付いた ssh リモートで固まりうる。**
FETCH_NOTE=""
if [ "$NEED_FETCH" = 1 ] && git remote get-url origin >/dev/null 2>&1; then
  if GIT_TERMINAL_PROMPT=0 \
     GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -oBatchMode=yes -oConnectTimeout=5" \
     git fetch --quiet origin >/dev/null 2>&1; then
    FETCH_NOTE="取り直した"
  else
    FETCH_NOTE="**取り直せなかった。古いかもしれない。**"
  fi
fi

# **start-point を解決する。** **`-b` は省略すると HEAD に落ちる**ので、
# **既定ブランチのリモート追跡参照を自分で解決して渡す**（#148）。
BASE_REF=""
BASE_HOW=""
if [ -n "${DEV_LOOP_BASE_REF:-}" ]; then
  BASE_REF="$DEV_LOOP_BASE_REF"
  BASE_HOW="環境変数 DEV_LOOP_BASE_REF"
elif BASE_REF="$(git symbolic-ref --short -q refs/remotes/origin/HEAD 2>/dev/null)"; then
  BASE_HOW="refs/remotes/origin/HEAD"
elif git rev-parse --verify -q origin/main >/dev/null 2>&1; then
  BASE_REF="origin/main"
  BASE_HOW="推測（refs/remotes/origin/HEAD が無い）"
elif git rev-parse --verify -q origin/master >/dev/null 2>&1; then
  BASE_REF="origin/master"
  BASE_HOW="推測（refs/remotes/origin/HEAD が無い）"
else
  BASE_REF=""
  BASE_HOW="解決できなかった"
fi

# **解決した参照が壊れていることがある。** `git symbolic-ref` は
# **dangling な `refs/remotes/origin/HEAD`** でも成功する（上流で既定ブランチが
# 改名され、こちらの `origin/HEAD` が古い名前を指したまま、など）。
# **そのまま渡すと `git worktree add` が `fatal: invalid reference` で死ぬ**
# ——**終了コードは文書化した 2/3/5/6 のどれでもない**（`/code-review` の指摘。#148）。
# **死なせず、HEAD に落ちたことを言う。**
if [ -n "$BASE_REF" ] && ! git rev-parse --verify -q "${BASE_REF}^{commit}" >/dev/null 2>&1; then
  echo "**解決した start-point が壊れている: ${BASE_REF}（${BASE_HOW}）**" >&2
  echo "  \`git remote set-head origin -a\` で直せることがある。**HEAD から切る。**" >&2
  BASE_HOW="解決したが壊れていた（${BASE_HOW}）"
  BASE_REF=""
fi


if [ -n "$BASE_REF" ]; then
  git worktree add --no-track "$PATH_ABS" -b "$BRANCH" "$BASE_REF" >&2
else
  # **黙って HEAD に落ちない。** 落ちたこと自体を出す（#148）。
  echo "**既定ブランチのリモート追跡参照を解決できなかった。HEAD から切る。**" >&2
  echo "  手元の既定ブランチが古ければ、周の全部が古い原本の上で進む。" >&2
  echo "  意図した base があるなら DEV_LOOP_BASE_REF に入れて切り直すこと。" >&2
  git worktree add "$PATH_ABS" -b "$BRANCH" >&2
fi

# **肯定的な確認。** 作って終わりにしない。
ACTUAL_BRANCH="$(git -C "$PATH_ABS" rev-parse --abbrev-ref HEAD)"
ACTUAL_HEAD="$(git -C "$PATH_ABS" log --oneline -1)"
# **関門に渡す base。** 切った直後は、worktree の HEAD が分岐点そのものである。
BASE_SHA="$(git -C "$PATH_ABS" rev-parse HEAD)"

echo
echo "=== 肯定的な確認 ==="
echo "ブランチ: ${ACTUAL_BRANCH}"
echo "起点:     ${ACTUAL_HEAD}"
echo "start-point: ${BASE_REF:-HEAD（解決できなかった）}  （${BASE_HOW}${FETCH_NOTE:+ / ${FETCH_NOTE}}）"
echo "base:     ${BASE_SHA}"

echo
echo "次にすること: EnterWorktree に path=${PATH_ABS} を渡して入る。"
echo "計画ファイルの「周の在り処」に、上のブランチ名・パス・起点・**base** を書くこと。"
echo "**base は関門にそのまま渡す SHA である**（SKILL.md 手順 4 が正）。"
