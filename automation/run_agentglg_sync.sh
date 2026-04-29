#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="/workspace/automation/sync_agentglg_mirror.py"

if [[ ! -d /workspace ]]; then
  echo "Синхронизация не запущена: рабочая папка /workspace недоступна."
  exit 1
fi

if [[ ! -d /workspace/automation ]]; then
  echo "Синхронизация не запущена: папка /workspace/automation недоступна."
  exit 1
fi

if [[ ! -f "${SCRIPT_PATH}" ]]; then
  echo "Синхронизация не запущена: скрипт ${SCRIPT_PATH} не найден."
  exit 1
fi

exec python3 "${SCRIPT_PATH}" --only-if-changed
