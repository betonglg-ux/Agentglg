# Индекс текущих файлов агента

Назначение: этот файл автоматически собирается из рабочей среды агента и помогает быстро понять, что именно выгружается в GitHub-зеркало.

## 1. Служебные файлы развития агента
- `agent-development/CHANGELOG.md`
- `agent-development/agent-summary.md`
- `agent-development/current-agent-instructions.md`
- `agent-development/files-index/templates-index.md`
- `agent-development/memory-exports/README.md`
- `agent-development/memory-exports/confirmed-error-patterns-export.md`
- `agent-development/memory-exports/memory-save-log-export.md`
- `agent-development/memory-exports/missed-findings-export.md`
- `agent-development/memory-exports/template-notes-export.md`
- `agent-development/memory-exports/user-corrections-export.md`
- `agent-development/memory-exports/user-preferences-export.md`
- `agent-development/recovery-plan.md`
- `agent-development/skills/README.md`

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
- `agent-development/` хранит материалы для воспроизведения и развития агента;
- `xl/` хранит технические ресурсы, связанные с табличными материалами.

## 5. Приоритеты зеркалирования
1. все шаблоны из `protocols/`;
2. служебные материалы из `agent-development/`;
3. память агента и экспорт устойчивых правил;
4. технические файлы, если они реально нужны для восстановления среды.