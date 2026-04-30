# Автоматизация GitHub-зеркала

Эта папка подготавливает автоматическую синхронизацию репозитория `betonglg-ux/Agentglg` без ручной правки индексов и служебных файлов.

## Что делает синхронизация

- пересобирает зеркало только из канонических источников, а не копирует весь workspace целиком;
- копирует `AGENTS.md` и папку `automation/`;
- собирает `agent-development/` из инструкций, шаблонов, навыка и памяти;
- заново генерирует индексы файлов и шаблонов;
- переносит ключевой навык `glavlab-protocol-review`;
- обновляет `CHANGELOG.md`;
- синхронизирует 4 канонических файла памяти в `agent-development/*.md`;
- дублирует те же 4 файла в `agent-development/memory-exports/raw-memory/`;
- перед коммитом проверяет, что канонические файлы памяти и raw-копии побайтно совпадают с источником;
- коммитит и, если доступ настроен, отправляет изменения в GitHub.

## Канонические файлы памяти

- `confirmed-error-patterns.md`
- `missed-findings-log.md`
- `template-notes.md`
- `user-confirmed-corrections.md`

Именно эти четыре файла считаются памятью, которая обязана попадать в GitHub.

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
