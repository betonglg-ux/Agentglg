#!/usr/bin/env bash
set -euo pipefail

SCRIPT="/workspace/memory/automation/sync_agentglg_mirror.py"

if [[ ! -f "${SCRIPT}" ]]; then
  echo "Экспорт в зеркало не запущен: скрипт ${SCRIPT} не найден."
  exit 1
fi

exec python3 "${SCRIPT}" --only-if-changed "$@"
