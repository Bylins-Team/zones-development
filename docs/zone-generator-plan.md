# План: Zone Generator для МУД "Былины"

## Контекст

Текущая система разработки зон состоит из:
- Ручное написание YAML зон по формату zone-format-v2.md
- Валидатор (tools/validator.py) оценивает качество по 100-балльной шкале
- LLM (Qwen2.5:14b через Ollama) используется только для экспертной оценки (20 баллов)
- Достижение 90+ баллов требует нескольких итераций ручных правок

**Проблема:** Создание одной зоны требует 3-5 часов ручной работы (структура, описания, баланс мобов, лут).

**Решение:** Автоматизировать генерацию зон с использованием LLM, оставив оператору возможность вносить коррективы на каждом этапе.

**Цель инструмента:**
- Генерировать черновики зон автоматически (идея → лор → комнаты → мобы → объекты → квесты)
- Работать offline через локальный Ollama (без интернета)
- Интерактивный режим с возможностью ручных правок на каждом этапе
- Итеративный рефайнмент для достижения 90+ баллов
- Использовать как для создания новых зон, так и для доработки существующих

---

## Архитектура

### Выбор фреймворка: LangGraph

**Почему LangGraph:**
- Multi-stage workflow (idea → lore → structure → rooms → mobs → objects → quests)
- Stateful процесс (накопление контекста по мере генерации)
- Human-in-the-loop (встроенная поддержка inspection points)
- Iterative refinement (циклы в графе для валидации → исправления)
- Durable execution (checkpoint механизм для долгих генераций)
- Работает локально (не требует интернета)

**Альтернатива:** Pure Python state machine (сложнее, но возможно как fallback)

### Компоненты системы

```
┌─────────────────────────────────────────────┐
│         CLI Interface (main.py)             │
│  Режимы: --interactive / --auto / --refine  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    LangGraph Orchestrator (workflow)        │
│                                             │
│  ┌─────┐  ┌─────┐  ┌──────┐  ┌─────┐      │
│  │Idea │→ │Lore │→ │Struct│→ │Rooms│       │
│  └─────┘  └─────┘  └──────┘  └─────┘      │
│                                             │
│  ┌─────┐  ┌───────┐  ┌──────┐             │
│  │Mobs │→ │Objects│→ │Quests│              │
│  └─────┘  └───────┘  └──────┘             │
│                 │                           │
│                 ▼                           │
│         ┌──────────────┐                    │
│         │  Validator   │                    │
│         │ (existing)   │                    │
│         └──────────────┘                    │
│                 │                           │
│        (score < 90?)                        │
│                 │                           │
│                 ▼                           │
│         ┌──────────────┐                    │
│         │   Refiner    │ (max 3 iter)      │
│         └──────────────┘                    │
└─────────────────────────────────────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ Human Review │ (каждый этап)
         │ + Edit Mode  │
         └──────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ zones/draft/ │
         │  zone.yaml   │
         └──────────────┘
```

### Интеракция с оператором

**Точки вмешательства:**
1. После генерации идеи → одобрить/отредактировать/регенерировать
2. После генерации лора → просмотр/правка
3. После структуры (топология) → корректировка графа комнат
4. После batch комнат (каждые 3-4 комнаты) → правка описаний
5. После мобов → правка характеристик/описаний
6. После объектов → правка лута
7. После квестов → правка сюжета
8. После валидации → решение о рефайнменте или ручной доработке

**Режимы работы:**
- `--interactive` (по умолчанию): пауза на каждом этапе для одобрения/правки
- `--auto`: полная автогенерация без остановок (для экспериментов)
- `--refine <zone.yaml>`: загрузка существующей зоны и улучшение

---

## Model Configuration

```python
# RTX 2080 Ti = 11GB VRAM
# Qwen2.5:14b (9GB) - влезает
# Qwen2.5:32b-q4_K_M (10-11GB quantized) - влезает!

MODEL_CONFIG = {
    # Креативные этапы - нужна модель помощнее
    'idea': 'qwen2.5:14b',          # Генерация идеи (креативность)
    'lore': 'qwen2.5:14b',          # Фольклор и нарратив
    'rooms': 'qwen2.5:14b',         # Качество описаний критично
    'mobs': 'qwen2.5:14b',          # Описания + характеристики
    'quests': 'qwen2.5:14b',        # Нарративное качество

    # Структурные этапы - можно быстрее модель
    'structure': 'qwen2.5:7b',      # Топология (простая задача)
    'objects': 'qwen2.5:7b',        # Описания объектов проще

    # Рефайнмент - самая сложная задача
    'refiner': 'qwen2.5:32b-q4',    # Quantized 32B (влезет в 11GB)
}
```

**Рекомендуемая установка моделей:**

```bash
# Основная модель
docker exec ollama ollama pull qwen2.5:14b

# Быстрая модель для простых задач
docker exec ollama ollama pull qwen2.5:7b

# Мощная quantized модель для refiner (влезет в 11GB!)
docker exec ollama ollama pull qwen2.5:32b-q4_K_M
```

---

## Context Window Management

**Qwen2.5 context window:** 32,768 tokens

**Расчёт использования для batch комнат:**

| Компонент | Символы | Токены (÷4) | % от 32k |
|-----------|---------|-------------|----------|
| **Одна комната (YAML)** | | | |
| - description | ~500 | ~125 | 0.4% |
| - examine | ~300 | ~75 | 0.2% |
| - exits, meta | ~300 | ~75 | 0.2% |
| **ИТОГО 1 комната** | ~1100 | **~275** | **0.9%** |
| | | | |
| **Batch 3 комнаты** | ~3300 | **~825** | **2.5%** |
| **Batch 4 комнаты** | ~4400 | **~1100** | **3.4%** |
| | | | |
| **Prompt overhead** | | | |
| - System prompt | ~800 | ~200 | 0.6% |
| - YAML schema | ~3200 | ~800 | 2.4% |
| - Lore context | ~2000 | ~500 | 1.5% |
| - Previous rooms summary | ~1200-2000 | ~300-500 | 1.5% |
| - Instructions | ~800 | ~200 | 0.6% |
| **ИТОГО overhead** | ~8000-10000 | **~2000-2500** | **7.6%** |
| | | | |
| **TOTAL input (batch 3)** | ~11300 | **~2825** | **8.6%** |
| **TOTAL input (batch 4)** | ~12400 | **~3100** | **9.5%** |
| | | | |
| **Generation budget (output)** | ~8000-12000 | **~2000-3000** | **9.1%** |
| | | | |
| **ИТОГО используется** | ~20000-24000 | **~5000-6000** | **18%** |

**Вывод:** Batch 3-4 комнаты использует ~18% context window - безопасный запас.

**Tradeoff размера батча:**

| Batch Size | Tokens | API Calls (12 комнат) | Consistency | Speed | Рекомендация |
|------------|--------|----------------------|-------------|-------|--------------|
| 1 комната | ~4000 | 12 | ⭐⭐⭐⭐⭐ Отлично | 🐌 Медленно (12 запросов) | Для критичных зон |
| 3 комнаты | ~5500 | 4 | ⭐⭐⭐⭐ Хорошо | 🚀 Быстро (4 запроса) | **Рекомендуется** |
| 4 комнаты | ~6000 | 3 | ⭐⭐⭐ Средне | 🚀🚀 Очень быстро (3 запроса) | Для простых зон |
| 6 комнат | ~8000 | 2 | ⭐⭐ Слабо | 🚀🚀🚀 Супер быстро (2 запроса) | Не рекомендуется |

**Рекомендация:** Batch **3 комнаты** - золотая середина (хорошая консистентность + приемлемая скорость).

---

## Структура проекта

```
tools/generator/
├── __init__.py
├── main.py                 # CLI entry point
├── orchestrator.py         # LangGraph workflow
├── config.py               # Конфигурация моделей
├── agents/                 # Агенты генерации
│   ├── __init__.py
│   ├── idea_agent.py
│   ├── lore_agent.py
│   ├── structure_agent.py
│   ├── rooms_agent.py
│   ├── mobs_agent.py
│   ├── objects_agent.py
│   └── quests_agent.py
├── llm/                    # LLM интеграция
│   ├── __init__.py
│   ├── ollama_client.py   # Wrapper над Ollama API
│   └── context_manager.py # Управление context window
├── prompts/                # Промпты для LLM
│   ├── __init__.py
│   └── library.py         # Централизованные промпты
├── balance/                # Формулы баланса
│   ├── __init__.py
│   └── formulas.py        # Из game-mechanics.md
└── utils/
    ├── __init__.py
    ├── yaml_utils.py
    └── interactive.py     # Интерактивные промпты оператору
```

---

## Фазы реализации

### Фаза 1: Инфраструктура и базовая генерация (3-5 дней) ✅ В ПРОЦЕССЕ

**Создано:**
- ✅ Структура проекта
- ✅ config.py с конфигурацией моделей
- ✅ llm/ollama_client.py (переиспользует логику из validator.py)
- ✅ llm/context_manager.py (управление context window)
- ✅ balance/formulas.py (извлечённые формулы баланса)
- ✅ utils/interactive.py (интерактивные утилиты)
- ✅ utils/yaml_utils.py (работа с YAML)

**Осталось:**
- prompts/library.py (промпты для LLM)
- agents/*.py (агенты генерации)
- main.py (CLI и простой sequential generator для MVP)

### Фаза 2: LangGraph Integration (2-3 дня)

- orchestrator.py (LangGraph workflow)
- State definition
- Human review nodes
- Conditional edges

### Фаза 3: Агенты генерации (3-4 дня)

- idea_agent.py
- lore_agent.py
- rooms_agent.py (с batch генерацией)
- mobs_agent.py (с post-processing баланса)
- objects_agent.py
- quests_agent.py

### Фаза 4: Refinement & Edge Cases (2-3 дня)

- refiner_agent.py
- validation_agent.py (интеграция с validator.py)
- Checkpoint механизм
- Error handling

### Фаза 5: CLI & Polish (1-2 дня)

- Финализация CLI
- Progress tracking
- Документация

---

## Оценка времени

**Фаза 1 (Infrastructure):** 3-5 дней
**Фаза 2 (LangGraph):** 2-3 дня
**Фаза 3 (Agents):** 3-4 дня
**Фаза 4 (Refinement):** 2-3 дня
**Фаза 5 (Polish):** 1-2 дня
**Тестирование и отладка:** 2-3 дня

**ИТОГО:** 13-20 дней разработки

**MVP (фазы 1-3 без LangGraph):** 5-7 дней

---

## Использование

### Новая зона (интерактивный режим)

```bash
python -m tools.generator.main --interactive --theme "проклятый лес" --level "15-20"
```

### Автоматическая генерация

```bash
python -m tools.generator.main --auto --level "25-30"
```

### Улучшение существующей зоны

```bash
python -m tools.generator.main --refine zones/draft/old_zone.yaml
```

---

## Метрики успеха

1. **Успешность генерации:** >= 90% зон проходят валидацию (score >= 60)
2. **Достижение целевого score:** >= 50% зон достигают 90+ после рефайнмента
3. **Скорость:** Полная генерация зоны <= 15 минут (на GPU)
4. **YAML валидность:** 100% генерируемых зон имеют валидный YAML
5. **Баланс:** 100% мобов имеют корректные exp/gold (благодаря post-processing)

---

## Статус

**Дата начала:** 2026-02-06
**Последнее обновление:** 2026-02-06
**Текущая фаза:** Фаза 1 (Infrastructure)
**Прогресс Фазы 1:** 80% (создана вся инфраструктура, осталось только агенты и CLI)

### Завершено в Фазе 1:

✅ **Структура проекта** (tools/generator/)
- 12 Python файлов, ~1636 строк кода
- 6 модулей: config, llm, balance, prompts, utils, agents(empty)

✅ **config.py** - Конфигурация моделей
- MODEL_CONFIG с разными моделями для разных этапов
- TEMPERATURE_CONFIG для каждого этапа
- GENERATION_CONFIG с параметрами

✅ **llm/ollama_client.py** - Ollama клиент
- Переиспользует логику из validator.py
- Retry logic при timeout
- Function calling support (для tools)
- Оценка токенов и проверка подключения

✅ **llm/context_manager.py** - Управление context window
- Оценка использования токенов
- Summarize комнат/мобов для контекста
- fit_into_budget для вписывания в лимиты
- Batch генерация промптов

✅ **balance/formulas.py** - Формулы баланса
- Извлечены из validator.py и game-mechanics.md
- calc_mob_exp, calc_mob_gold, calc_damage_dice
- Все множители ролей (ROLE_EXP_MULT, ROLE_GOLD_MULT, ROLE_DAMAGE_MULT)
- Парсинг и валидация урона (NdN+B формат)

✅ **prompts/library.py** - Библиотека промптов
- Системный промпт SYSTEM_DESIGNER
- Промпты для всех 7 этапов (idea, lore, structure, rooms, mobs, objects, quests)
- Промпт для refiner с приоритизацией ошибок
- Включены YAML схемы и примеры

✅ **utils/interactive.py** - Интерактивное взаимодействие
- user_approve, user_choice
- user_edit (открывает $EDITOR)
- show_diff (colored diff)
- print_section, progress_bar

✅ **utils/yaml_utils.py** - Работа с YAML
- safe_parse_yaml с retry
- extract_code_block из markdown
- assemble_zone_yaml (сборка state → YAML)
- validate_yaml_structure
- sanitize_filename

### Осталось в Фазе 1 (~20%):

🔲 **agents/*.py** - 7 агентов генерации
- idea_agent.py
- lore_agent.py
- structure_agent.py
- rooms_agent.py (с batch processing)
- mobs_agent.py (с post-processing баланса)
- objects_agent.py
- quests_agent.py

🔲 **main.py** - CLI entry point
- Аргументы: --interactive, --auto, --refine
- Simple sequential generator (без LangGraph для MVP)
- Интеграция с validator.py

🔲 **Тестирование базовой генерации**
- Unit tests для formulas
- Integration test для полной генерации
