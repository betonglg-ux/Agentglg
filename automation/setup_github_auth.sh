#!/usr/bin/env bash
set -euo pipefail

TOKEN="${AGENTGLG_GITHUB_TOKEN:-${GITHUB_TOKEN:-}}"
TOKEN_FILE="/workspace/memory/agentglg-github-token.txt"

if [[ -z "${TOKEN}" ]]; then
  echo "Не найден токен. Задайте AGENTGLG_GITHUB_TOKEN или GITHUB_TOKEN и запустите снова." >&2
  exit 1
fi

mkdir -p /workspace/memory
printf '%s\n' "${TOKEN}" > "${TOKEN_FILE}"
chmod 600 "${TOKEN_FILE}"

git config --global credential.helper store
printf 'protocol=https\nhost=github.com\nusername=x-access-token\npassword=%s\n\n' "${TOKEN}" | git credential approve

cat <<'EOF'
Авторизация для git настроена.
Токен сохранен в памяти агента для будущих автоматических запусков.
Теперь синхронизацию можно запускать так:

python3 /workspace/automation/sync_agentglg_mirror.py

Для пробного запуска без отправки:

python3 /workspace/automation/sync_agentglg_mirror.py --no-push
EOF
