# CHANGELOG GitHub-зеркала

Репозиторий зеркала: `betonglg-ux/Agentglg`

Этот файл фиксирует значимые изменения в развитии агента, его экспортного пакета и материалов для будущего клонирования.

## 2026-05-16

### Изменено
- после проверки текущей рабочей среды подтверждено, что локальная память в `/workspace/memory/memory/` остаётся первичным источником истины и не требует восстановления из зеркала;
- подтверждено, что `AGENTS.md`, основные файлы памяти и рабочие шаблоны из `agent_files/` уже совпадают с GitHub-зеркалом;
- исправлены только локальные файлы автоматизации синхронизации и их переносимый raw-memory-дубль: ветка зеркала выровнена с устаревшего `master` на фактическую `main`, подтверждённую GitHub API.

### Примечания
- рабочая память не переписывалась данными зеркала;
- синхронизация выполняется только в сторону `текущий агент -> GitHub-зеркало`.

## 2026-05-05

### Изменено
- обновлены экспортные файлы памяти в `agent-development/memory-exports/` подтверждёнными пользовательскими правками и правилами проверки;
- в `user-corrections-export.md` перенесён свод подтверждённых правил, частных кейсов и правил работы с памятью и GitHub-зеркалом;
- в `template-notes-export.md` перенесены устойчивые заметки по шаблонам УК, УИ, КУ, ВС и общим правилам оформления;
- в `missed-findings-export.md` зафиксированы подтверждённые случаи пропущенных замечаний и контрольные точки, которые нельзя пропускать в будущем;
- в `confirmed-error-patterns-export.md` зафиксированы подтверждённые паттерны ошибок, исключения и правила повышенного внимания;
- синхронизирован `agent-development/current-agent-instructions.md` с текущими реальными инструкциями агента;
- обновлены сводные файлы полного зеркала: `agent-development/agent-summary.md`, `agent-development/github-export-bundle.md`, `agent-development/github-mirror-manifest.md` и `agent-development/memory-exports/README.md`;
- обновлены файловые индексы `agent-development/files-index/attached-files-index.md` и `agent-development/files-index/templates-index.md` по текущему видимому дереву файлов агента;
- создана симметричная структура между рабочими файлами памяти агента и зеркальными файлами в `agent-development/`: добавлены `agent-development/confirmed-error-patterns.md`, `agent-development/missed-findings-log.md`, `agent-development/template-notes.md`, `agent-development/user-confirmed-corrections.md`, `agent-development/user-preferences.md`, `agent-development/slack-user-corrections.md` и `agent-development/memory-save-log.md`;
- инструкции агента дополнительно уточнены так, чтобы симметрия `Memory <-> agent-development/` была закреплена как обязательный стандарт сопровождения;
- манифест зеркала обновлён под симметричную структуру памяти и теперь явно фиксирует одноимённые пары рабочих memory-файлов и зеркальных файлов в `agent-development/`;
- экспортные файлы `agent-development/memory-exports/user-corrections-export.md` и `agent-development/memory-exports/missed-findings-export.md` перезаписаны содержимым актуальных рабочих memory-файлов;
- добавлены новые экспортные файлы `agent-development/memory-exports/user-preferences-export.md` и `agent-development/memory-exports/memory-save-log-export.md`;
- в инструкции агента добавлено обязательное правило вести `memory-save-log.md` как журнал успешных и неуспешных событий сохранения памяти;
- `agent-development/memory-exports/README.md` и `agent-development/github-export-bundle.md` обновлены под новые export-файлы и актуальную схему памяти;
- в сводных файлах, индексах и структуре памяти закреплён рутинный режим: зеркальные markdown-файлы должны обновляться как обычная обязательная часть сопровождения агента после значимых изменений;
- в основные инструкции агента добавлено жёсткое исключение для протоколов КП: отсутствие нижнего колонтитула не считать ошибкой и нумерацию страниц не проверять;
- файловая копия инструкций в `agent-development/current-agent-instructions.md` обновлена под это же правило для последующей синхронизации в GitHub.

### Примечания
- локальная память остаётся первичным источником истины, а экспортные markdown-файлы служат файловым дублем для зеркала;
- содержимое подготовлено для синхронизации в GitHub-зеркало, но само внешнее обновление зеркала должно выполняться отдельно доступным каналом синхронизации.

## 2026-04-29

### Добавлено
- создан манифест GitHub-зеркала: `agent-development/github-mirror-manifest.md`;
- создан индекс текущих файлов агента: `agent-development/files-index/attached-files-index.md`;
- создан индекс шаблонов протоколов: `agent-development/files-index/templates-index.md`;
- сохранена переносимая копия текущих инструкций агента: `agent-development/current-agent-instructions.md`;
- создана краткая карточка агента: `agent-development/agent-summary.md`;
- создан индекс обязательного навыка: `agent-development/skills/README.md`;
- собран стартовый экспортный пакет: `agent-development/github-export-bundle.md`;
- подготовлена папка экспорта Memory: `agent-development/memory-exports/`;
- созданы заготовки файлов для экспорта подтверждённых наработок из Memory;
- создан пошаговый план восстановления агента из зеркала: `agent-development/recovery-plan.md`;
- создан файл changelog: `agent-development/CHANGELOG.md`.

### Изменено
- правила агента обновлены так, чтобы текущая конфигурация агента оставалась основной рабочей средой;
- GitHub закреплён как внешний дублирующий архив для файлов, навыков, экспортов Memory и материалов будущего клонирования;
- в инструкциях закреплён режим, где GitHub не заменяет агент, а хранит его переносимое зеркало.

### Примечания
- текущий экспортный комплект является стартовой базой и будет дополняться по мере инвентаризации файлов, навыков и данных Memory;
- список файлов агента пока частичный, потому что видимое файловое дерево в редакторе отображается не полностью.
