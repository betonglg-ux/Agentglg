#!/usr/bin/env bash
set -euo pipefail

PRIMARY_SCRIPT="/workspace/automation/sync_agentglg_mirror.py"
FALLBACK_SCRIPT="/workspace/agent_files/agent-development/automation/sync_agentglg_mirror.py"

if [[ ! -d /workspace ]]; then
  echo "Синхронизация не запущена: рабочая папка /workspace недоступна."
  exit 1
fi

if [[ -f "${PRIMARY_SCRIPT}" ]]; then
  exec python3 "${PRIMARY_SCRIPT}" --only-if-changed
fi

if [[ -f "${FALLBACK_SCRIPT}" ]]; then
  exec python3 "${FALLBACK_SCRIPT}" --only-if-changed
fi

if [[ ! -d /workspace/automation ]]; then
  echo "Синхронизация не запущена: папка /workspace/automation недоступна, а резервный скрипт в /workspace/agent_files/agent-development/automation тоже не найден."
  exit 1
fi

echo "Синхронизация не запущена: скрипты ${PRIMARY_SCRIPT} и ${FALLBACK_SCRIPT} не найдены."
exit 1
