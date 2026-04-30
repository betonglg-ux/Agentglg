# Sync Guarantees

Этот файл фиксирует минимальные гарантии исправной синхронизации GitHub-зеркала агента.

## Что обязано совпадать всегда

Источник истины в рабочей среде:
- `/workspace/memory/confirmed-error-patterns.md`
- `/workspace/memory/missed-findings-log.md`
- `/workspace/memory/template-notes.md`
- `/workspace/memory/user-confirmed-corrections.md`

Канонические копии в GitHub:
- `agent-development/confirmed-error-patterns.md`
- `agent-development/missed-findings-log.md`
- `agent-development/template-notes.md`
- `agent-development/user-confirmed-corrections.md`

Контрольные raw-копии:
- `agent-development/memory-exports/raw-memory/confirmed-error-patterns.md`
- `agent-development/memory-exports/raw-memory/missed-findings-log.md`
- `agent-development/memory-exports/raw-memory/template-notes.md`
- `agent-development/memory-exports/raw-memory/user-confirmed-corrections.md`

## Что считается успешной синхронизацией

- все четыре файла памяти существуют в рабочей среде;
- все четыре канонических файла существуют в `agent-development/`;
- все четыре raw-копии существуют в `agent-development/memory-exports/raw-memory/`;
- содержимое всех трех слоев совпадает побайтно;
- `agent-development/MEMORY-SYNC-STATUS.md` обновлен текущими контрольными суммами;
- изменения дошли до `origin/main`.

## Что проверять первым делом, если есть сомнение

1. Сравнить `/workspace/memory/*.md` с `agent-development/*.md`.
2. Сравнить `/workspace/memory/*.md` с `agent-development/memory-exports/raw-memory/*.md`.
3. Открыть `agent-development/MEMORY-SYNC-STATUS.md`.
4. Проверить последний коммит зеркала и голову `origin/main`.

## Что не должно происходить

- синхронизация не должна молча пропускать один из четырех memory-файлов;
- GitHub не должен хранить конкурирующую каноническую версию этих файлов в другой папке;
- старые дубли `memory/` и `agent_files/` не должны возвращаться в корень зеркала.
