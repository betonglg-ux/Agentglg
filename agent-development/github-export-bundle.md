# Экспортный пакет для GitHub-зеркала

Репозиторий назначения: `betonglg-ux/Agentglg`

Назначение: этот файл собирает в одном месте текущий состав экспортного пакета для GitHub-зеркала. Его задача — помочь быстро перенести текущие наработки агента в репозиторий и затем использовать их для восстановления или клонирования похожего агента.

## 1. Что уже входит в экспортный пакет

### Базовые служебные файлы
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
- папка `xl/` с техническими ресурсами табличных файлов;
- прикреплённый навык `glavlab-protocol-review`;
- текущая конфигурация инструкций агента;
- накопленные данные в Memory.

### Заготовки для экспорта Memory
- `agent-development/memory-exports/README.md`
- `agent-development/memory-exports/confirmed-error-patterns-export.md`
- `agent-development/memory-exports/missed-findings-export.md`
- `agent-development/memory-exports/template-notes-export.md`
- `agent-development/memory-exports/user-corrections-export.md`

## 2. Что нужно выгружать в GitHub в первую очередь

Порядок приоритета:
1. `current-agent-instructions.md`
2. `agent-summary.md`
3. `github-mirror-manifest.md`
4. `skills/README.md`
5. `files-index/attached-files-index.md`
6. `files-index/templates-index.md`
7. содержимое `protocols/`
8. важные материалы из `xl/`, если они нужны для восстановления шаблонов
9. экспортированные данные из `memory-exports/`
10. changelog и подтверждённые паттерны по мере накопления

## 3. Минимальный набор для создания нового похожего агента

Чтобы быстро собрать похожего агента, нужно восстановить:
- инструкции из `agent-development/current-agent-instructions.md`;
- обязательный навык `glavlab-protocol-review`;
- шаблоны из `protocols/`;
- индексы файлов и навыков;
- экспорт важных данных из Memory;
- правила GitHub-зеркала из `github-mirror-manifest.md`.

## 4. Что ещё остаётся сделать позже

Следующие этапы усилят экспорт:
- выгрузить в GitHub сами файлы этого пакета;
- дополнить полный индекс файлов, если файловое дерево покажет больше элементов;
- отдельно описать, какие файлы из `xl/` обязательны для восстановления;
- при возможности зафиксировать материалы навыка `glavlab-protocol-review` в зеркале подробнее;
- регулярно пополнять `memory-exports/` подтверждёнными наработками.

## 5. Смысл этого пакета

Текущий агент остаётся основной рабочей средой.
Этот экспортный пакет нужен для того, чтобы GitHub был не просто архивом, а понятной и пригодной к повторному развертыванию копией ключевых наработок агента.
