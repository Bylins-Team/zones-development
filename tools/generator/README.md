# Zone Generator для МУД "Былины"

Автоматическая генерация зон с использованием LLM (Ollama).

## Статус проекта

**Текущая фаза:** Фаза 1 - Infrastructure (80% завершено)

**Что реализовано:**
- ✅ Базовая структура проекта
- ✅ Конфигурация моделей (config.py)
- ✅ Ollama Client с retry logic и function calling support
- ✅ Context Manager для управления context window
- ✅ Balance Formulas (извлечены из validator.py и game-mechanics.md)
- ✅ Интерактивные утилиты (user_approve, user_edit, show_diff)
- ✅ YAML утилиты (парсинг, сборка, валидация)
- ✅ Библиотека промптов для всех этапов генерации

**Статистика:**
- Файлов: 12
- Строк кода: ~1636
- Модулей: 6 (config, llm, balance, prompts, utils, agents)

## Структура проекта

```
tools/generator/
├── README.md              # Этот файл
├── __init__.py
├── config.py              # Конфигурация моделей и параметров
│
├── llm/                   # LLM интеграция
│   ├── __init__.py
│   ├── ollama_client.py   # Клиент Ollama API
│   └── context_manager.py # Управление context window
│
├── balance/               # Игровой баланс
│   ├── __init__.py
│   └── formulas.py        # Формулы exp/gold/damage
│
├── prompts/               # Промпты для генерации
│   ├── __init__.py
│   └── library.py         # Все промпты
│
├── utils/                 # Утилиты
│   ├── __init__.py
│   ├── interactive.py     # Интерактивное взаимодействие
│   └── yaml_utils.py      # Работа с YAML
│
├── agents/                # TODO: Агенты генерации
│   ├── idea_agent.py
│   ├── lore_agent.py
│   ├── structure_agent.py
│   ├── rooms_agent.py
│   ├── mobs_agent.py
│   ├── objects_agent.py
│   └── quests_agent.py
│
├── main.py                # TODO: CLI entry point
└── orchestrator.py        # TODO: LangGraph workflow
```

## Конфигурация моделей

Система использует разные модели Ollama для разных этапов:

| Этап | Модель | Температура | Причина |
|------|--------|-------------|---------|
| idea | qwen2.5:14b | 0.8 | Креативность |
| lore | qwen2.5:14b | 0.7 | Нарратив |
| rooms | qwen2.5:14b | 0.5 | Качество описаний |
| mobs | qwen2.5:14b | 0.4 | Баланс + описания |
| quests | qwen2.5:14b | 0.6 | Сюжет |
| structure | qwen2.5:7b | 0.3 | Быстрая модель для топологии |
| objects | qwen2.5:7b | 0.5 | Быстрая модель для простых описаний |
| refiner | qwen2.5:32b-q4 | 0.3 | Максимальная точность для исправлений |

### Требования к железу

**Минимум:**
- GPU: 8GB VRAM (для qwen2.5:7b)
- RAM: 16GB

**Рекомендуется:**
- GPU: 11GB+ VRAM (RTX 2080 Ti, 3080, 4080)
- RAM: 32GB

**Установка моделей:**

```bash
# Основная модель (9GB)
docker exec ollama ollama pull qwen2.5:14b

# Быстрая модель (4GB)
docker exec ollama ollama pull qwen2.5:7b

# Мощная quantized модель для refiner (10-11GB)
docker exec ollama ollama pull qwen2.5:32b-q4_K_M
```

## Context Window Management

**Context window Qwen2.5:** 32,768 tokens

**Batch размер для комнат:** 3 комнаты (рекомендуется)
- Использует ~18% context window
- 4 API calls для зоны из 12 комнат
- Хорошая консистентность описаний

## Использование (планируется)

### Создание новой зоны (интерактивный режим)

```bash
python -m tools.generator.main \
  --interactive \
  --theme "проклятый лес" \
  --level "15-20"
```

### Автоматическая генерация

```bash
python -m tools.generator.main \
  --auto \
  --level "25-30"
```

### Улучшение существующей зоны

```bash
python -m tools.generator.main \
  --refine zones/draft/old_zone.yaml
```

## Workflow генерации

```
1. Idea Generation
   ↓ (user review)
2. Lore Generation
   ↓ (user review)
3. Structure Generation (топология комнат)
   ↓ (user review)
4. Rooms Generation (батчами по 3 комнаты)
   ↓ (user review каждого batch)
5. Mobs Generation (с auto balance)
   ↓ (user review)
6. Objects Generation
   ↓ (user review)
7. Quests Generation
   ↓ (user review)
8. Validation (через validator.py)
   ↓ (score < 90?)
9. Refinement (max 3 iterations)
   ↓
10. Final Zone → zones/draft/
```

## Формулы баланса

Система автоматически применяет формулы баланса из `game-mechanics.md`:

**Опыт моба:**
```python
exp = level² * role_multiplier

ROLE_MULT = {
    'TRASH': 10,
    'BOSS': 30,
    'TANK': 10,
    'MELLEE_DMG': 15,
    # ...
}
```

**Золото моба:**
```python
gold_center = level * role_multiplier
gold_min = gold_center * 0.7
gold_max = gold_center * 1.3

ROLE_MULT = {
    'TRASH': 5,
    'BOSS': 25,
    # ...
}
```

**Урон моба:**
```python
player_hp = 100 + level * 20
base_damage = player_hp * 0.1
expected_damage = base_damage * role_multiplier

# Конвертируется в формат NdN+B
```

## Следующие шаги

### Phase 1 (осталось ~20%)
- [ ] Создать agents/*.py (7 агентов)
- [ ] Создать main.py (CLI + simple sequential generator)
- [ ] Протестировать базовую генерацию

### Phase 2 (LangGraph integration)
- [ ] orchestrator.py (LangGraph workflow)
- [ ] State management
- [ ] Human-in-the-loop nodes
- [ ] Conditional edges

### Phase 3 (Agents)
- [ ] Доработать агенты с LangGraph state
- [ ] Batch генерация комнат
- [ ] Post-processing баланса мобов

### Phase 4 (Refinement)
- [ ] Refiner agent
- [ ] Validation integration
- [ ] Checkpoint механизм
- [ ] Error handling

### Phase 5 (Polish)
- [ ] CLI finalization
- [ ] Progress tracking (tqdm)
- [ ] Документация
- [ ] Examples

## Ссылки

- [План разработки](../../docs/zone-generator-plan.md)
- [Формат зон](../../docs/zone-format-v2.md)
- [Игровые механики](../../docs/game-mechanics.md)
- [Валидатор](../validator.py)

## Лицензия

MIT
