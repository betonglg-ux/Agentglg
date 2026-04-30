# Экспортный пакет для GitHub-зеркала

Репозиторий назначения: `betonglg-ux/Agentglg`

Назначение: этот файл собирает в одном месте текущий состав экспортного пакета для GitHub-зеркала. Его задача — помочь быстро перенести текущие наработки агента в репозиторий и затем использовать их для восстановления или клонирования похожего агента.

## 1. Что уже входит в экспортный пакет

### Базовые служебные файлы
- `AGENTS.md` — переносимая копия актуальных инструкций агента;
- `automation/README.md` — описание реальной схемы синхронизации;
- `automation/sync_agentglg_mirror.py` — рабочий скрипт сборки зеркала;
- `agent-development/github-mirror-manifest.md` — манифест структуры зеркала и правил дублирования;
- `agent-development/current-agent-instructions.md` — переносимая копия текущих инструкций агента;
- `agent-development/agent-summary.md` — краткая карточка агента для восстановления и клонирования;
- `agent-development/github-export-bundle.md` — текущий сводный файл экспортного пакета.

### Индексы и инвентаризация
- `agent-development/files-index/attached-files-index.md` — индекс видимых файлов агента;
- `agent-development/files-index/templates-index.md` — индекс шаблонов по типам протоколов;
- `agent-development/skills/README.md` — индекс обязательного навыка и правил его переноса.

### Обязательные рабочие материалы
- папка `protocols/` с шаблонами по типам испытаний;
- прикреплённый навык `glavlab-protocol-review`;
- текущая конфигурация инструкций агента;
- 4 канонических файла памяти.

### Память и её дубли
- `agent-development/confirmed-error-patterns.md`
- `agent-development/missed-findings-log.md`
- `agent-development/template-notes.md`
- `agent-development/user-confirmed-corrections.md`
- `agent-development/memory-exports/README.md`
- `agent-development/memory-exports/confirmed-error-patterns-export.md`
- `agent-development/memory-exports/missed-findings-export.md`
- `agent-development/memory-exports/template-notes-export.md`
- `agent-development/memory-exports/user-corrections-export.md`
- `agent-development/memory-exports/raw-memory/*.md`

## 2. Что нужно выгружать в GitHub в первую очередь

Порядок приоритета:
1. `current-agent-instructions.md`
2. 4 канонических файла памяти
3. `agent-summary.md`
4. `github-mirror-manifest.md`
5. `automation/sync_agentglg_mirror.py`
6. `skills/README.md`
7. `files-index/attached-files-index.md`
8. `files-index/templates-index.md`
9. содержимое `protocols/`
10. changelog и служебные memory-файлы контроля

## 3. Минимальный набор для создания нового похожего агента

Чтобы быстро собрать похожего агента, нужно восстановить:
- инструкции из `agent-development/current-agent-instructions.md`;
- корневой `AGENTS.md` и папку `automation/`;
- обязательный навык `glavlab-protocol-review`;
- шаблоны из `protocols/`;
- индексы файлов и навыков;
- четыре канонических файла памяти;
- правила GitHub-зеркала из `github-mirror-manifest.md`.

## 4. Что ещё остаётся сделать позже

Следующие этапы усилят экспорт:
- поддерживать описания зеркала синхронно со скриптом;
- при возможности зафиксировать материалы навыка `glavlab-protocol-review` в зеркале подробнее;
- регулярно пополнять четыре канонических файла памяти подтверждёнными наработками;
- периодически проверять `MEMORY-SYNC-STATUS.md` после заметных обновлений памяти.

## 5. Смысл этого пакета

Текущий агент остаётся основной рабочей средой.
Этот экспортный пакет нужен для того, чтобы GitHub был не просто архивом, а понятной и пригодной к повторному развертыванию копией ключевых наработок агента.
