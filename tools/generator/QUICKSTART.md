# Zone Generator - Quick Start Guide

## Установка моделей

```bash
# Основная модель (9GB VRAM)
docker exec ollama ollama pull qwen2.5:14b

# Быстрая модель для структурных задач (4GB VRAM)
docker exec ollama ollama pull qwen2.5:7b

# Мощная модель для рефайнмента (10-11GB VRAM)
docker exec ollama ollama pull qwen2.5:32b-q4_K_M
```

## Проверка установки

```bash
# Проверить что Ollama работает
curl http://localhost:11434/api/tags

# Проверить доступные модели
docker exec ollama ollama list
```

## Использование (когда будет готово)

### Создание новой зоны

```bash
# Интерактивный режим (по умолчанию)
python -m tools.generator.main \
  --theme "заброшенная мельница" \
  --level "10-15"

# Автоматическая генерация
python -m tools.generator.main \
  --auto \
  --level "20-25"
```

### Улучшение существующей зоны

```bash
python -m tools.generator.main \
  --refine zones/draft/old_zone.yaml
```

### Опции

```
--interactive       Интерактивный режим с паузами на review (по умолчанию)
--auto              Автоматическая генерация без остановок
--refine <file>     Улучшить существующую зону
--theme <text>      Тема зоны (например "соляные копи")
--level <range>     Диапазон уровней (например "10-15")
--output <dir>      Директория для сохранения (по умолчанию zones/draft/)
--model <name>      Модель Ollama (по умолчанию qwen2.5:14b)
--ollama-url <url>  URL Ollama API (по умолчанию http://localhost:11434)
```

## Workflow генерации

```
1. Idea Generation → Концепция зоны
   ↓ [review/edit/regenerate]

2. Lore Generation → Детальный лор
   ↓ [review/edit]

3. Structure Generation → Топология комнат (граф)
   ↓ [review/edit]

4. Rooms Generation → Описания комнат (batch по 3)
   ↓ [review каждого batch]

5. Mobs Generation → NPC с автоматическим балансом
   ↓ [review/edit]

6. Objects Generation → Лут и экипировка
   ↓ [review/edit]

7. Quests Generation → Квесты
   ↓ [review/edit]

8. Validation → Проверка через validator.py
   ↓ [score < 90?]

9. Refinement → Автоматическое исправление ошибок (max 3 iter)
   ↓

10. Final Zone → zones/draft/zone_name.yaml
```

## Интерактивные команды

На каждом этапе доступны:
- **y** - одобрить и продолжить
- **n** - отклонить и регенерировать
- **e** - открыть редактор для правки (использует $EDITOR или nano)
- **s** - пропустить этап (для тестирования)

## Ожидаемое время генерации

На RTX 2080 Ti (11GB VRAM):
- **Автоматический режим:** 10-12 минут
- **Интерактивный режим:** 15-30 минут (в зависимости от правок)

На слабом GPU (8GB VRAM):
- Используйте только qwen2.5:7b для всех этапов
- Время увеличится до 15-20 минут (auto) / 30-45 минут (interactive)

## Формулы баланса (автоматически применяются)

**Опыт моба:**
```
exp = level² × role_multiplier

TRASH: ×10
BOSS: ×30
MELLEE_DMG: ×15
MAGE_DMG: ×18
```

**Золото моба:**
```
gold = level × role_multiplier × random(0.7-1.3)

TRASH: ×5
BOSS: ×25
MELLEE_DMG: ×8
MAGE_DMG: ×12
```

**Урон моба:**
```
player_hp = 100 + level × 20
base_damage = player_hp × 0.1
expected_damage = base_damage × role_multiplier

TRASH: ×1.0
BOSS: ×1.5
MAGE_DMG: ×2.0
TANK: ×0.7
```

## Советы

### Для лучшего качества:
1. Используйте интерактивный режим
2. Задавайте конкретную тему (например "заброшенный монастырь" вместо "подземелье")
3. Редактируйте описания комнат в batch review
4. Проверяйте баланс мобов перед финализацией

### Для экспериментов:
1. Используйте --auto для быстрого прототипирования
2. Генерируйте несколько вариантов и выбирайте лучший
3. Используйте --refine для улучшения существующих зон

### При проблемах:
1. **Timeout:** Увеличится автоматически (180s → 360s)
2. **Невалидный YAML:** Откроется редактор для исправления
3. **Низкий score:** Запустится рефайнмент (max 3 итерации)
4. **Out of memory:** Используйте qwen2.5:7b для всех этапов

## Проверка результата

```bash
# Валидация сгенерированной зоны
python tools/validator.py zones/draft/generated_zone.yaml

# Ожидаемые результаты:
# - Score >= 60: минимум для игропригодности
# - Score >= 75: хорошее качество
# - Score >= 90: отличное качество (цель рефайнмента)
```

## Структура сгенерированной зоны

```yaml
zone:
  meta:
    id: "zone_id"
    name: "Название"
    level_min: 10
    level_recommended: 13
    level_max: 15
    # ...

  lore:
    history: "..."
    folklore_basis: "..."
    # ...

  rooms: [...]      # 8-12 комнат
  mobiles: [...]    # 4-8 мобов
  objects: [...]    # 6-10 объектов
  quests: [...]     # 1-3 квеста
```

## Примеры команд

```bash
# Простая зона для новичков
python -m tools.generator.main --level "1-5" --theme "тренировочный полигон"

# Средняя зона с подземельем
python -m tools.generator.main --level "15-20" --theme "заброшенная шахта"

# Сложная зона с боссом
python -m tools.generator.main --level "35-40" --theme "логово змея Горыныча"

# Улучшение низкокачественной зоны
python -m tools.generator.main --refine zones/draft/low_quality_zone.yaml
```

## Дополнительная информация

- **Полный план:** [docs/zone-generator-plan.md](../../docs/zone-generator-plan.md)
- **Статус реализации:** [IMPLEMENTATION_STATUS.md](../../IMPLEMENTATION_STATUS.md)
- **Формат зон:** [docs/zone-format-v2.md](../../docs/zone-format-v2.md)
- **Игровые механики:** [docs/game-mechanics.md](../../docs/game-mechanics.md)
