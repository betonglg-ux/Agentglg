# GitHub Mirror Manifest

Репозиторий: `betonglg-ux/Agentglg`

Назначение: этот манифест описывает актуальную структуру GitHub-зеркала для текущего агента. Текущий агент продолжает работать в своей среде, а GitHub хранит чистую, переносимую и регулярно актуализируемую копию ключевых материалов.

## Базовые принципы
- текущая конфигурация агента является основной рабочей средой;
- GitHub является внешним зеркалом и архивом развития;
- важные наработки не должны оставаться только внутри Memory, если они нужны для переноса в другого агента;
- при расхождениях сначала нужно ориентироваться на актуальное состояние текущего агента, затем обновлять зеркало в GitHub.

## Актуальная структура репозитория

```text
AGENTS.md
automation/
  README.md
  run_agentglg_sync.sh
  setup_github_auth.sh
  sync_agentglg_mirror.py
github-mirror-manifest.md
agent-development/
  CHANGELOG.md
  CANONICAL-MEMORY.md
  MEMORY-SYNC-STATUS.md
  confirmed-error-patterns.md
  missed-findings-log.md
  template-notes.md
  user-confirmed-corrections.md
  current-agent-instructions.md
  agent-summary.md
  memory-exports/
    README.md
    confirmed-error-patterns-export.md
    missed-findings-export.md
    template-notes-export.md
    user-corrections-export.md
  skills/
    README.md
    glavlab-protocol-review/
      SKILL.md
  files-index/
    README.md
    attached-files-index.md
    templates-index.md
  protocols/
    README.md
    Адгезия/
    Анкеры/
    Бетон/
    Влажность/
    Металл/
    Момент затяжки/
    Нагрузки/
    Сварка/
    Толщина ЛКП/
    Уплотнение/
```

## Что считается каноническим

- основная рабочая память агента живет в `/workspace/memory/*.md`;
- в GitHub канонические копии этой памяти живут в:
  - `agent-development/confirmed-error-patterns.md`
  - `agent-development/missed-findings-log.md`
  - `agent-development/template-notes.md`
  - `agent-development/user-confirmed-corrections.md`
- `agent-development/memory-exports/raw-memory/` хранит только прямые дубли этих же четырех файлов;
- другие файлы в зеркале не должны конкурировать с этими четырьмя по смыслу.

## Что должно храниться в разделах

### Корень репозитория
- `AGENTS.md` — переносимая копия актуальных инструкций;
- `automation/` — рабочие скрипты синхронизации и их инструкция;
- `github-mirror-manifest.md` — краткое описание правил зеркала.

### `agent-development/`
- канонические файлы памяти;
- индексы файлов и шаблонов;
- карточка агента и план восстановления;
- `CHANGELOG.md` с короткой историей значимых изменений;
- `CANONICAL-MEMORY.md` и `MEMORY-SYNC-STATUS.md` для контроля памяти.

### `agent-development/skills/`
Зеркало материалов обязательного навыка `glavlab-protocol-review`.

### `agent-development/files-index/`
Индекс файлов агента, чтобы можно было быстро понять, какие материалы были прикреплены и зачем они нужны.

### `agent-development/protocols/`
Зеркальная структура папок с шаблонами и рабочими типами протоколов.

### `agent-development/memory-exports/`
- `raw-memory/` — прямые копии четырех канонических файлов памяти;
- `*-export.md` — короткие указатели на канонические файлы;
- `memory-index.md` — список реально выгруженных файлов памяти.

## Что нужно фиксировать в GitHub в первую очередь
1. Актуальные инструкции агента.
2. Четыре канонических файла памяти.
3. Ключевой навык `glavlab-protocol-review`.
4. Шаблоны из `agent-development/protocols/`.
5. Индексы и план восстановления.
6. Changelog изменений.

## Что пригодится для размножения агента
При создании нового похожего агента нужно в первую очередь восстановить:
- инструкции из `current-agent-instructions.md`;
- скрипты из `automation/`;
- структуру навыков из папки `skills/`;
- индексы и список прикрепляемых файлов из `files-index/`;
- устойчивые знания из четырех канонических файлов памяти.

## Статус этого манифеста
Это рабочий манифест текущей схемы. При изменении структуры зеркала его нужно обновлять вместе со скриптом синхронизации.
