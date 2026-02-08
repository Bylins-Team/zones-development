# Resuming Generation with `--resume`

Zone Generator поддерживает продолжение генерации с checkpoint через `--resume`.

## Как работает --resume

LangGraph автоматически сохраняет состояние в SQLite БД (`.checkpoints/langgraph_checkpoints.db`) после каждого узла графа.

При использовании `--resume` восстанавливается:
- ✅ **Весь прогресс генерации** (idea, lore, structure, rooms, mobs, objects, quests)
- ✅ **Состояние валидации** (score, errors, warnings)
- ✅ **Текущий этап** (на котором остановились)
- ✅ **Счетчики итераций** (refinement_iteration, validation_attempts)

## ⚠️ Что НЕ восстанавливается автоматически

При `--resume` НЕ восстанавливаются CLI параметры:
- ❌ **--provider** (LLM провайдер)
- ❌ **--interactive** / **--auto** (режим)
- ❌ **--ollama-url** (endpoint)
- ❌ **--profile** (профиль моделей для Ollama)

**ВАЖНО:** Эти параметры нужно указывать явно при каждом resume!

## Примеры использования

### 1. Базовое resume (продолжить с тем же провайдером)

```bash
# Оригинальная генерация
python -m tools.generator.main --auto --theme "замок" --level "10-15"
# Output: Thread ID: zone_20260208_143022_abc123de

# Генерация упала/прервалась
# Продолжить с того же места (Ollama):
python -m tools.generator.main --resume zone_20260208_143022_abc123de --auto
```

### 2. Resume со сменой провайдера

Если генерация упала из-за проблемы с Ollama, можно продолжить с другим провайдером:

```bash
# Оригинальная генерация с Ollama
python -m tools.generator.main --auto --theme "замок" --level "10-15"
# Thread ID: zone_20260208_143022_abc123de
# ❌ Упало на этапе mobs (невалидный YAML)

# Продолжить с Claude (более надёжный для YAML)
python -m tools.generator.main \\
  --resume zone_20260208_143022_abc123de \\
  --provider anthropic \\
  --auto

# Или с ChatGPT
python -m tools.generator.main \\
  --resume zone_20260208_143022_abc123de \\
  --provider openai \\
  --auto
```

### 3. Resume в интерактивном режиме

Если генерация была в автоматическом режиме, можно продолжить в интерактивном:

```bash
# Оригинальная генерация (auto)
python -m tools.generator.main --auto --theme "замок" --level "10-15"

# Продолжить в интерактивном режиме (проверять каждый этап)
python -m tools.generator.main \\
  --resume zone_20260208_143022_abc123de \\
  --interactive
```

### 4. Resume с другой моделью (Ollama)

Если хотите использовать другой профиль моделей Ollama:

```bash
# Оригинальная генерация (default profile)
python -m tools.generator.main --auto --theme "замок"

# Продолжить с максимальным качеством (все 14b модели)
python -m tools.generator.main \\
  --resume zone_20260208_143022_abc123de \\
  --profile rtx4070ti-max \\
  --auto
```

## Когда использовать --resume

### ✅ Используйте --resume когда:

1. **Генерация прервалась/упала:**
   - Timeout Ollama
   - Ошибка парсинга YAML/JSON
   - Системная ошибка
   - Ctrl+C прервал процесс

2. **Хотите сменить провайдер:**
   - Ollama дает плохое качество → переключить на Claude
   - Ollama слишком медленный → переключить на Cerebras
   - Закончились API credits → переключить на Ollama

3. **Хотите изменить режим:**
   - Auto → Interactive (проверить этапы руками)
   - Interactive → Auto (ускорить процесс)

### ❌ НЕ используйте --resume когда:

1. **Хотите начать новую зону** - просто не указывайте --resume
2. **Изменились параметры зоны** (theme, level) - resume использует старые
3. **Checkpoint устарел** - лучше начать заново

## Как найти Thread ID

Thread ID выводится в начале генерации:

```
╔══════════════════════════════════════════════════════════════╗
║          ZONE GENERATOR - LangGraph Mode                     ║
╚══════════════════════════════════════════════════════════════╝
🆔 Thread ID: zone_20260208_143022_abc123de    ← Это ваш Thread ID
   Для продолжения используйте: --resume zone_20260208_143022_abc123de
```

## Полный пример workflow

```bash
# 1. Начать генерацию с Ollama
python -m tools.generator.main --auto --theme "древний храм" --level "15-20"
# Thread ID: zone_20260208_150000_xyz789

# 2. Упало на mobs с ошибкой YAML парсинга
# Смотрим debug файл: /tmp/llm_yaml_error_mobs_20260208_150430.yaml

# 3. Пробуем продолжить с Claude (лучше для YAML)
python -m tools.generator.main \\
  --resume zone_20260208_150000_xyz789 \\
  --provider anthropic \\
  --auto

# 4. Успех! Зона сгенерирована
```

## Troubleshooting

### Ошибка "Checkpoint не найден"

```
❌ Ошибка: Checkpoint для zone_xxx не найден
```

**Решение:**
- Проверьте что Thread ID правильный (скопируйте точно)
- Убедитесь что `.checkpoints/langgraph_checkpoints.db` существует
- Возможно checkpoint устарел - начните генерацию заново

### Resume не меняет провайдер

```bash
# Оригинальная генерация с Ollama
python -m tools.generator.main --auto --theme "замок"

# Resume БЕЗ указания --provider
python -m tools.generator.main --resume zone_xxx --auto
# ❌ Продолжит использовать Ollama!
```

**Решение:** Всегда указывайте `--provider` явно при resume:
```bash
python -m tools.generator.main --resume zone_xxx --provider anthropic --auto
```

### Генерация зацикливается после resume

Если генерация зацикливается на validation/refinement:

1. Проверьте счетчик итераций (макс 10)
2. Смените провайдер на более надёжный
3. Или начните генерацию заново (без --resume)

## Технические детали

### Что сохраняется в checkpoint

SQLite БД (`.checkpoints/langgraph_checkpoints.db`) содержит:
- Полный state графа (ZoneGenerationState)
- History всех узлов
- Pending tasks
- Channel values

### Размер checkpoint

Типичный checkpoint для зоны:
- Маленькая зона (5-7 комнат): ~50-100 KB
- Средняя зона (10-15 комнат): ~200-500 KB
- Большая зона (20+ комнат): ~1-2 MB

### Очистка старых checkpoints

Checkpoints накапливаются в БД. Для очистки:

```bash
# Удалить всю БД (все checkpoints)
rm .checkpoints/langgraph_checkpoints.db

# Или использовать SQL для выборочной очистки
sqlite3 .checkpoints/langgraph_checkpoints.db "DELETE FROM checkpoints WHERE created_at < datetime('now', '-7 days')"
```

## FAQ

**Q: Могу ли я изменить theme/level при resume?**
A: Нет, theme и level берутся из checkpoint. Начните новую генерацию.

**Q: Сколько хранятся checkpoints?**
A: Бесконечно, пока не удалите БД вручную.

**Q: Можно ли resume на другой машине?**
A: Да, если скопировать `.checkpoints/` директорию. Но API ключи нужно настроить на новой машине.

**Q: Resume работает с --no-langgraph?**
A: Нет, --resume требует LangGraph mode (который используется по умолчанию).

**Q: Что если я потерял Thread ID?**
A: Можно найти в логах или извлечь из БД:
```bash
sqlite3 .checkpoints/langgraph_checkpoints.db "SELECT DISTINCT thread_id FROM checkpoints ORDER BY created_at DESC LIMIT 10"
```
