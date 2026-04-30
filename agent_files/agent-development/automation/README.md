# Автоматизация GitHub-зеркала

Эта папка подготавливает автоматическую синхронизацию репозитория `betonglg-ux/Agentglg` без ручной правки индексов и служебных файлов.

## Что делает синхронизация

- копирует `AGENTS.md`, `agent_files/` и `memory/` в зеркало;
- автоматически пересобирает `agent-development/`;
- заново генерирует индексы файлов и шаблонов;
- переносит ключевой навык `glavlab-protocol-review`;
- обновляет `CHANGELOG.md`;
- зеркалит все реальные `.md` файлы из памяти в `agent-development/memory-exports/raw-memory/`;
- коммитит и, если доступ настроен, отправляет изменения в GitHub.

## Один раз настроить доступ

```bash
export AGENTGLG_GITHUB_TOKEN=ваш_токен
bash /workspace/automation/setup_github_auth.sh
```

После этого токен будет сохранен в `/workspace/memory/agentglg-github-token.txt`, и будущие синхронизации смогут работать без ручной подстановки переменной окружения.

## Обычный запуск

```bash
python3 /workspace/automation/sync_agentglg_mirror.py
```

## Запуск только при новых изменениях

```bash
python3 /workspace/automation/sync_agentglg_mirror.py --only-if-changed
```

В этом режиме скрипт сравнивает текущий отпечаток рабочей среды с последней успешной синхронизацией и ничего не отправляет, если новых изменений нет.

## Пробный запуск без push

```bash
python3 /workspace/automation/sync_agentglg_mirror.py --no-push
```
