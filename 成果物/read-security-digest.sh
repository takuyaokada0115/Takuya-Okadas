#!/bin/bash
#
# read-security-digest.sh
# -----------------------------------------------------------------------------
# MacBook のデスクトップに毎朝表示されるセキュリティダイジェストを、
# macOS 標準の音声合成コマンド `say` で読み上げるスクリプト。
#
# 使い方:
#   ./read-security-digest.sh                 # 自動探索して読み上げ
#   ./read-security-digest.sh path/to/file    # ファイルを指定して読み上げ
#   DIGEST_FILE=~/note.md ./read-security-digest.sh   # 環境変数で指定
#
# オプション（環境変数）:
#   DIGEST_FILE   読み上げるダイジェスト本文のファイルパス（最優先）
#   VOICE         音声（既定: Kyoko。英語なら Samantha など）
#   RATE          読み上げ速度 words/min（既定: 200）
#   SAVE_AUDIO    値を設定すると再生の代わりに ~/Desktop/digest.aiff へ書き出し
#
# 前提: macOS（`say` コマンド）。日本語音声 Kyoko は
#   システム設定 > アクセシビリティ > 読み上げコンテンツ からインストール可能。
# -----------------------------------------------------------------------------

set -euo pipefail

VOICE="${VOICE:-Kyoko}"
RATE="${RATE:-200}"

# --- 1. 読み上げ対象ファイルの決定 -------------------------------------------
# 優先順位: コマンド引数 > 環境変数 DIGEST_FILE > デスクトップ内の自動探索
DIGEST_FILE="${1:-${DIGEST_FILE:-}}"

if [[ -z "${DIGEST_FILE}" ]]; then
  # デスクトップから "security" や "セキュリティ" を含む txt/md を新しい順に探す
  DESKTOP="${HOME}/Desktop"
  DIGEST_FILE="$(
    find "${DESKTOP}" -maxdepth 1 -type f \
      \( -iname '*security*digest*' -o -iname '*セキュリティ*' -o -iname '*security*' \) \
      \( -name '*.txt' -o -name '*.md' -o -name '*.markdown' \) \
      -print0 2>/dev/null \
    | xargs -0 ls -t 2>/dev/null | head -n 1 || true
  )"
fi

if [[ -z "${DIGEST_FILE}" || ! -f "${DIGEST_FILE}" ]]; then
  echo "エラー: 読み上げるダイジェストが見つかりません。" >&2
  echo "  ファイルを引数で指定するか、DIGEST_FILE 環境変数を設定してください。" >&2
  echo "  例: ./read-security-digest.sh ~/Desktop/security-digest.md" >&2
  exit 1
fi

echo "読み上げ対象: ${DIGEST_FILE}"

# --- 2. 本文の整形（記号・URL を読み上げやすく除去） --------------------------
# Markdown の装飾記号や URL を落として、耳で聞きやすいプレーンテキストにする。
CLEAN_TEXT="$(
  sed -E \
    -e 's/https?:\/\/[^ ]+/（リンク省略）/g' \
    -e 's/^#{1,6}[[:space:]]*//' \
    -e 's/\*\*([^*]+)\*\*/\1/g' \
    -e 's/\*([^*]+)\*/\1/g' \
    -e 's/`([^`]+)`/\1/g' \
    -e 's/^[[:space:]]*[-*+][[:space:]]+/・/' \
    -e 's/\|/ /g' \
    "${DIGEST_FILE}"
)"

if [[ -z "${CLEAN_TEXT//[[:space:]]/}" ]]; then
  echo "エラー: ダイジェスト本文が空です。" >&2
  exit 1
fi

# --- 3. 読み上げ / 音声ファイル書き出し --------------------------------------
if [[ -n "${SAVE_AUDIO:-}" ]]; then
  OUT="${HOME}/Desktop/security-digest.aiff"
  printf '%s\n' "${CLEAN_TEXT}" | say -v "${VOICE}" -r "${RATE}" -o "${OUT}"
  echo "音声ファイルを書き出しました: ${OUT}"
else
  printf '%s\n' "${CLEAN_TEXT}" | say -v "${VOICE}" -r "${RATE}"
  echo "読み上げが完了しました。"
fi
