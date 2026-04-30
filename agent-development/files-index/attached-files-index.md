# Индекс текущих файлов агента

Назначение: этот файл автоматически собирается из рабочей среды агента и помогает быстро понять, что именно выгружается в GitHub-зеркало.

## 1. Канонические источники в рабочей среде
- `AGENTS.md`
- `automation/README.md`
- `automation/run_agentglg_sync.sh`
- `automation/setup_github_auth.sh`
- `automation/sync_agentglg_mirror.py`
- `memory/confirmed-error-patterns.md`
- `memory/missed-findings-log.md`
- `memory/template-notes.md`
- `memory/user-confirmed-corrections.md`
- `glavlab-protocol-review/SKILL.md`

## 2. Папка `protocols/`
### `protocols/Адгезия`
- `2.0 Адгезия.xls`

### `protocols/Анкеры`
- `2.0 Анкеры.xlsx`

### `protocols/Бетон`
- `#2.0 Кубики 10х10х10 Finale.xls`
- `#2.0 Кубики 7х7х7  Finale.xls`
- `2.0 Бетон. Схема В..xls`
- `2.0 Бетон. Схема Г..xls`
- `2.0 ИПС универсальная .xls`
- `2.0 Керны. Бетон.xls`

### `protocols/Влажность`
- `#2.0 Влажность.xlsx`

### `protocols/Металл`
- `2.0 Рвем металл универсальная.xlsx`

### `protocols/Момент затяжки`
- `#2.0 Момент затяжки.xlsx`

### `protocols/Нагрузки`
- `2.0 Лестницы, ограждения.xlsx`
- `2.0 Лестничные марши.xlsx`
- `2.0 Монорельсы, петли.xlsx`

### `protocols/Сварка`
- `#2.0 ВИК УК - универсальная..xlsx`

### `protocols/Толщина ЛКП`
- `2.0 ЛКП.xls`

### `protocols/Уплотнение`
- `2.0 ПДУ ГРУНТ.xls`
- `2.0 ПДУ ПЕСОК..xls`
- `2.0 ПДУ ЩЕБЕНЬ.xls`
- `2.0 Экспресс-метод В-1..xls`

## 3. Папка `xl/`
- файлов найдено: 45

Первые файлы:
- `xl/_rels/workbook.xml.rels`
- `xl/charts/chart1.xml`
- `xl/charts/colors1.xml`
- `xl/charts/style1.xml`
- `xl/drawings/_rels/drawing2.xml.rels`
- `xl/drawings/drawing1.xml`
- `xl/drawings/drawing2.xml`
- `xl/drawings/drawing3.xml`
- `xl/drawings/drawing4.xml`
- `xl/drawings/drawing5.xml`
- `xl/drawings/drawing6.xml`
- `xl/drawings/vmlDrawing1.vml`
- `xl/drawings/vmlDrawing2.vml`
- `xl/drawings/vmlDrawing3.vml`
- `xl/media/image1.png`
- `xl/media/image10.png`
- `xl/media/image11.png`
- `xl/media/image12.png`
- `xl/media/image13.png`
- `xl/media/image14.png`
- и ещё 25 файлов

## 4. Что означает эта структура
- `protocols/` хранит шаблоны протоколов, на которых держится сверка PDF;
- `agent-development/` хранит канонические материалы для воспроизведения и развития агента;
- `xl/` показан только как технический источник локальной среды и не должен дублироваться в корень зеркала.

## 5. Приоритеты зеркалирования
1. инструкции агента и automation-скрипты;
2. четыре канонических файла памяти;
3. все шаблоны из `protocols/`;
4. ключевой навык и служебные индексы `agent-development/`.
