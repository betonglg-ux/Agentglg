#!/usr/bin/env bash
set -euo pipefail

SCRIPT="/workspace/memory/memory/automation/sync_agentglg_mirror.py"

if [[ ! -f "${SCRIPT}" ]]; then
  echo "Экспорт в зеркало не запущен: скрипт ${SCRIPT} не найден."
  exit 1
fi

exec python3 "${SCRIPT}" --workspace /workspace/memory --only-if-changed "$@"
