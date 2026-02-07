# Zone Generator - Руководство пользователя

## Быстрый старт

### 1. Установка моделей Ollama

```bash
# Основная модель для большинства этапов
docker exec ollama ollama pull qwen2.5:14b

# Быстрая модель для структурных задач
docker exec ollama ollama pull qwen2.5:7b

# Мощная модель для рефайнмента (опционально)
docker exec ollama ollama pull qwen2.5:32b-q4_K_M
```

### 2. Проверка установки

```bash
# Проверить что Ollama работает
curl http://localhost:11434/api/tags

# Список доступных моделей
docker exec ollama ollama list
```

### 3. Генерация первой зоны

```bash
# Интерактивный режим (рекомендуется для начала)
python3 -m tools.generator.main \
  --theme "заброшенная мельница" \
  --level "10-15"
```

## Режимы работы

### Интерактивный режим (по умолчанию)

Позволяет контролировать каждый этап генерации:

```bash
python3 -m tools.generator.main \
  --interactive \
  --theme "соляные копи" \
  --level "10-15"
```

**Workflow:**
1. Генерация концепции → Review (одобрить/редактировать/регенерировать)
2. Генерация лора → Review
3. Генерация структуры → Review
4. Генерация комнат (batch по 3) → Review каждого batch
5. Генерация мобов → Review
6. Генерация объектов → Review
7. Генерация квестов → Review
8. Сохранение в zones/draft/

**На каждом этапе доступны действия:**
- `y` - одобрить и продолжить
- `n` - отклонить и регенерировать
- При выборе редактирования откроется $EDITOR (nano по умолчанию)

### Автоматический режим

Генерация без остановок:

```bash
python3 -m tools.generator.main \
  --auto \
  --level "20-25"
```

Полезно для:
- Быстрого прототипирования
- Генерации нескольких вариантов для выбора лучшего
- Экспериментов с разными темами

### Режим улучшения (будет реализован в Phase 4)

```bash
python3 -m tools.generator.main \
  --refine zones/draft/old_zone.yaml
```

## Параметры командной строки

```
--interactive       Интерактивный режим (по умолчанию)
--auto              Автоматический режим без остановок
--refine <file>     Улучшить существующую зону

--theme <text>      Тема зоны (например "логово змея")
--level <range>     Диапазон уровней: "10-15" или "20"

--output <dir>      Директория сохранения (по умолчанию zones/draft/)
--model <name>      Модель Ollama (по умолчанию qwen2.5:14b)
--ollama-url <url>  URL Ollama API (по умолчанию http://localhost:11434)
```

## Примеры использования

### Зона для новичков

```bash
python3 -m tools.generator.main \
  --theme "тренировочный полигон дружины" \
  --level "1-5"
```

### Средняя зона с подземельем

```bash
python3 -m tools.generator.main \
  --theme "заброшенная соляная шахта с духами" \
  --level "15-20"
```

### Сложная зона с боссом

```bash
python3 -m tools.generator.main \
  --theme "логово змея Горыныча" \
  --level "35-40"
```

### Быстрая генерация нескольких вариантов

```bash
# Генерируем 3 варианта автоматически
for i in {1..3}; do
  python3 -m tools.generator.main \
    --auto \
    --theme "древний курган" \
    --level "25-30"
done

# Выбираем лучший и дорабатываем интерактивно
```

## Что генерируется

### Структура зоны

```yaml
zone:
  meta:
    id: "generated_zone_id"
    name: "Название зоны"
    author: "Zone Generator"
    version: "1.0"
    description: "Описание зоны"
    folklore_basis: "Фольклорная основа"
    level_min: 10
    level_recommended: 13
    level_max: 15
    difficulty: 1.0
    wealth: 1.0
    tags: [...]
    entry_points: [...]

  lore:
    history: "История места"
    folklore_basis: "Детальная фольклорная основа"
    current_state: "Текущее состояние"
    conflict: "Основной конфликт"
    key_characters: [...]
    atmosphere: {...}
    secrets: [...]

  rooms: [8-12 комнат]
  mobiles: [4-8 мобов]
  objects: [6-10 объектов]
  quests: [1-3 квеста]
```

### Автоматический баланс мобов

Система автоматически применяет формулы баланса:

- **EXP:** `level² × role_multiplier`
  - TRASH: ×10
  - BOSS: ×30
  - MELLEE_DMG: ×15

- **Gold:** `level × role_multiplier × random(0.7-1.3)`
  - TRASH: ×5
  - BOSS: ×25

- **Урон:** Рассчитывается от HP игрока
  - Формат: NdN+B (например "2d8+15")

## Ожидаемое время генерации

На RTX 2080 Ti (11GB VRAM):
- **Автоматический режим:** 10-12 минут
- **Интерактивный режим:** 15-30 минут (в зависимости от правок)

На GPU с 8GB VRAM:
- Используйте только qwen2.5:7b
- Время: 15-20 минут (auto) / 30-45 минут (interactive)

## После генерации

### 1. Проверка качества

```bash
# Запустить валидатор
python3 tools/validator.py zones/draft/generated_zone.yaml
```

**Интерпретация результатов:**
- Score >= 60: Минимально игропригодна
- Score >= 75: Хорошее качество
- Score >= 90: Отличное качество (цель)

### 2. Ручная доработка

Откройте файл в редакторе и исправьте:
- Грамматические ошибки
- Несоответствия в описаниях
- Баланс (если нужно)

### 3. Улучшение через refiner (Phase 4)

```bash
python3 -m tools.generator.main --refine zones/draft/generated_zone.yaml
```

## Советы по использованию

### Для лучшего качества

1. **Используйте конкретные темы:**
   - ✅ "заброшенный монастырь с призраками монахов"
   - ❌ "подземелье"

2. **Редактируйте ключевые этапы:**
   - Idea: проверьте что тема соответствует задумке
   - Lore: уточните фольклорную основу
   - Rooms (batch 1): задайте тон описаниям

3. **Проверяйте баланс мобов:**
   - Система автоматически применяет формулы
   - Но проверьте соотношение ролей (60% TRASH, 10% BOSS)

### При проблемах

**Timeout при генерации:**
- Система автоматически увеличит timeout (180s → 360s)
- Если всё равно timeout, используйте qwen2.5:7b для всех этапов

**Невалидный YAML:**
- Откроется редактор для исправления
- Проверьте отступы (только пробелы, без табов)

**Низкий score при валидации:**
- < 60: Серьёзные проблемы, нужна ручная доработка
- 60-75: Используйте refiner (Phase 4)
- 75-90: Мелкие правки вручную

**Out of memory:**
- Используйте qwen2.5:7b для всех этапов
- Уменьшите количество комнат (измените в structure)

## Интеграция с workflow

### 1. Генерация черновика

```bash
python3 -m tools.generator.main \
  --auto \
  --theme "ваша тема" \
  --level "X-Y"
```

### 2. Валидация

```bash
python3 tools/validator.py zones/draft/zone_name.yaml
```

### 3. Доработка

- Если score >= 75: мелкие правки вручную
- Если score < 75: запустить refiner или редактировать вручную

### 4. Финализация

```bash
# Переместить в production
mv zones/draft/zone_name.yaml zones/production/

# Или закоммитить
git add zones/draft/zone_name.yaml
git commit -m "Add new zone: Zone Name"
```

## Дополнительная информация

- **Формат зон:** [docs/zone-format-v2.md](../../docs/zone-format-v2.md)
- **Игровые механики:** [docs/game-mechanics.md](../../docs/game-mechanics.md)
- **План развития:** [docs/zone-generator-plan.md](../../docs/zone-generator-plan.md)
- **Статус реализации:** [IMPLEMENTATION_STATUS.md](../../IMPLEMENTATION_STATUS.md)

## Поддержка

При возникновении проблем:
1. Проверьте что Ollama запущен: `docker ps | grep ollama`
2. Проверьте доступные модели: `docker exec ollama ollama list`
3. Запустите тесты: `python3 tests/test_balance.py`
4. Создайте issue в репозитории
