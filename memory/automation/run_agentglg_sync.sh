#!/usr/bin/env bash
set -euo pipefail

PRIMARY_SCRIPT="/workspace/memory/memory/automation/sync_agentglg_mirror.py"
FALLBACK_SCRIPT="/workspace/agent_files/agent-development/automation/sync_agentglg_mirror.py"
MEMORY_SCRIPT="/workspace/memory/memory/automation/sync_agentglg_mirror.py"

if [[ ! -d /workspace ]]; then
  echo "Экспорт в зеркало не запущен: рабочая папка /workspace недоступна."
  exit 1
fi

if [[ -f "${PRIMARY_SCRIPT}" ]]; then
  exec python3 "${PRIMARY_SCRIPT}" --workspace /workspace/memory --branch master --only-if-changed
fi

if [[ -f "${FALLBACK_SCRIPT}" ]]; then
  exec python3 "${FALLBACK_SCRIPT}" --workspace /workspace/memory --branch master --only-if-changed
fi

if [[ -f "${MEMORY_SCRIPT}" ]]; then
  exec python3 "${MEMORY_SCRIPT}" --workspace /workspace/memory --branch master --only-if-changed
fi

if [[ ! -d /workspace/memory/memory/automation ]]; then
  echo "Экспорт в зеркало не запущен: папка /workspace/memory/memory/automation недоступна, а резервные скрипты в /workspace/agent_files/agent-development/automation и /workspace/memory/memory/automation тоже не найдены."
  exit 1
fi

echo "Экспорт в зеркало не запущен: скрипты ${PRIMARY_SCRIPT}, ${FALLBACK_SCRIPT} и ${MEMORY_SCRIPT} не найдены."
exit 1
