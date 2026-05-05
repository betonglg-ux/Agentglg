# Экспортный пакет для GitHub-зеркала

Репозиторий назначения: `betonglg-ux/Agentglg`

Назначение: этот файл собирает в одном месте текущий состав экспортного пакета для GitHub-зеркала, чтобы по нему можно было быстро синхронизировать рабочие дубли агента и восстановить похожего агента в будущем.

## 1. Что сейчас входит в экспортный пакет

### Базовые служебные файлы
- `agent-development/github-mirror-manifest.md` — манифест структуры зеркала и правил дублирования;
- `agent-development/current-agent-instructions.md` — актуальная переносимая копия текущих инструкций агента;
- `agent-development/agent-summary.md` — краткая карточка агента для восстановления и клонирования;
- `agent-development/CHANGELOG.md` — журнал значимых изменений;
- `agent-development/github-export-bundle.md` — текущий сводный файл экспортного пакета.

### Симметричные зеркальные копии рабочих memory-файлов
- `agent-development/confirmed-error-patterns.md`
- `agent-development/missed-findings-log.md`
- `agent-development/template-notes.md`
- `agent-development/user-confirmed-corrections.md`
- `agent-development/user-preferences.md`
- `agent-development/slack-user-corrections.md`
- `agent-development/memory-save-log.md`

### Индексы и инвентаризация
- `agent-development/files-index/attached-files-index.md` — индекс видимых файлов агента;
- `agent-development/files-index/templates-index.md` — индекс шаблонов по типам протоколов;
- `agent-development/skills/README.md` — индекс обязательного навыка и правил его переноса.

### Обязательные рабочие материалы
- папка `protocols/` с шаблонами по типам испытаний;
- папка `xl/` с техническими ресурсами табличных файлов;
- прикреплённый навык `glavlab-protocol-review`;
- текущая конфигурация инструкций агента;
- накопленные данные в Memory;
- настроенный Slack-канал с рабочими Slack-инструкциями;
- GitHub-интеграция для зеркала.

### Export-файлы памяти
- `agent-development/memory-exports/README.md`
- `agent-development/memory-exports/confirmed-error-patterns-export.md`
- `agent-development/memory-exports/missed-findings-export.md`
- `agent-development/memory-exports/template-notes-export.md`
- `agent-development/memory-exports/user-corrections-export.md`
- `agent-development/memory-exports/user-preferences-export.md`
- `agent-development/memory-exports/memory-save-log-export.md`

## 2. Что нужно выгружать в GitHub в первую очередь

Порядок приоритета:
1. `current-agent-instructions.md`
2. симметричные зеркальные копии рабочих memory-файлов в `agent-development/`
3. `memory-exports/*`
4. `agent-summary.md`
5. `github-mirror-manifest.md`
6. `CHANGELOG.md`
7. `skills/README.md`
8. `files-index/attached-files-index.md`
9. `files-index/templates-index.md`
10. содержимое `protocols/`
11. важные материалы из `xl/`, если они нужны для восстановления шаблонов

## 3. Что теперь считается обязательной рутиной

После каждого значимого изменения агент должен в том же рабочем цикле проверить и обновить:
- `agent-development/current-agent-instructions.md`;
- нужные файлы в `agent-development/memory-exports/`;
- связанные симметричные зеркальные пары рабочих memory-файлов в `agent-development/`;
- `agent-development/agent-summary.md`, если изменилось поведение, структура или режим работы агента;
- `agent-development/github-export-bundle.md`, если изменился состав полного зеркала;
- `agent-development/github-mirror-manifest.md`, если изменились правила дублирования или ожидаемая структура зеркала;
- `agent-development/CHANGELOG.md`.

Это не ручное исключение, а нормальный обязательный цикл сопровождения зеркала.

## 4. Минимальный набор для создания нового похожего агента

Чтобы быстро собрать похожего агента, нужно восстановить:
- инструкции из `agent-development/current-agent-instructions.md`;
- обязательный навык `glavlab-protocol-review`;
- шаблоны из `protocols/`;
- индексы файлов и навыков;
- первичные зеркальные копии рабочих memory-файлов в `agent-development/`;
- export важных данных из Memory;
- журнал событий сохранения памяти;
- правила GitHub-зеркала из `github-mirror-manifest.md`;
- жёсткие правила записи памяти и Slack-подтверждений.

## 5. Что ещё важно держать в голове при синхронизации

- локальная Memory остаётся первичным источником истины;
- симметричные файлы в `agent-development/` и export-файлы в `memory-exports/` — файловые дубли для зеркала;
- GitHub не должен автоматически переопределять более новое локальное состояние;
- если локальные служебные копии расходятся с реальными инструкциями и памятью, сначала нужно сверять текущий агент, защитные снимки и подтверждённые пользовательские правки;
- синхронизация разрешена только в сторону `текущий агент -> GitHub-зеркало`.

## 6. Смысл этого пакета

Текущий агент остаётся основной рабочей средой.
Этот экспортный пакет нужен для того, чтобы GitHub был не просто архивом, а актуальным и пригодным к повторному развертыванию файловым зеркалом ключевых наработок агента.
