# Zone Generator - Implementation Status

**Дата:** 2026-02-06
**Статус:** Phase 1 Infrastructure - 80% Complete

---

## Обзор

Реализация автоматического генератора зон для МУД "Былины" с использованием LLM (Ollama).

**Цель:** Сократить время создания зоны с 3-5 часов до 15-30 минут с интерактивным контролем качества.

---

## Прогресс по фазам

### ✅ Фаза 1: Infrastructure (80% завершено)

**Создано:**

#### 1. Базовая структура проекта
```
tools/generator/
├── config.py              ✅ Конфигурация моделей
├── llm/
│   ├── ollama_client.py   ✅ Клиент Ollama API
│   └── context_manager.py ✅ Управление context window
├── balance/
│   └── formulas.py        ✅ Формулы баланса
├── prompts/
│   └── library.py         ✅ Библиотека промптов
├── utils/
│   ├── interactive.py     ✅ Интерактивные утилиты
│   └── yaml_utils.py      ✅ YAML утилиты
└── agents/                🔲 Агенты (пусто)
```

**Статистика:**
- Файлов: 12
- Строк кода: ~1636
- Модулей: 6

#### 2. Ключевые компоненты

##### ✅ config.py (90 строк)
- Конфигурация моделей для разных этапов
- qwen2.5:14b для креативных задач
- qwen2.5:7b для структурных задач
- qwen2.5:32b-q4 для refiner
- Температуры и параметры генерации

##### ✅ llm/ollama_client.py (130 строк)
- HTTP клиент для Ollama API
- Переиспользует логику из validator.py
- Retry logic при timeout (180s → 360s)
- Function calling support
- Оценка токенов (1 token ≈ 4 символа)
- Проверка подключения и список моделей

##### ✅ llm/context_manager.py (140 строк)
- Управление context window (32k tokens)
- summarize_rooms/mobs для контекста
- fit_into_budget для вписывания в лимиты
- Batch prompts для генерации

##### ✅ balance/formulas.py (230 строк)
- Формулы из validator.py и game-mechanics.md
- calc_mob_exp: level² × role_mult
- calc_mob_gold: level × role_mult × (0.7-1.3)
- calc_damage_dice: NdN+B формат
- Все множители ролей (TRASH, BOSS, etc)
- Парсинг и валидация урона
- Unit-тестируемые функции

##### ✅ prompts/library.py (650 строк)
- Централизованные промпты для всех этапов
- SYSTEM_DESIGNER: системный промпт
- get_idea_prompt: генерация концепции
- get_lore_prompt: детальный лор
- get_structure_prompt: топология комнат
- get_rooms_prompt: batch генерация описаний
- get_mobs_prompt: создание NPC с балансом
- get_objects_prompt: лут и экипировка
- get_quests_prompt: квесты
- get_refiner_prompt: исправление ошибок

**Особенности промптов:**
- Включают YAML схемы
- Примеры из salt-mines-example.yaml
- Формулы баланса inline
- Славянская атмосфера и терминология

##### ✅ utils/interactive.py (240 строк)
- user_approve: запрос одобрения (y/n)
- user_choice: выбор из списка
- user_edit: открытие $EDITOR для правки
- user_edit_yaml/user_edit_batch: специализированные редакторы
- show_diff: colored diff с unified format
- print_section: форматированный вывод
- progress_bar: простой progress indicator

##### ✅ utils/yaml_utils.py (210 строк)
- extract_code_block: извлечение YAML из markdown
- safe_parse_yaml: парсинг с retry (2 попытки)
- safe_parse_json: парсинг JSON
- assemble_zone_yaml: сборка state → YAML
- sanitize_filename: очистка имени файла
- validate_yaml_structure: базовая валидация
- merge_yaml_files: слияние для рефайнмента
- count_elements: подсчет rooms/mobs/objects

---

### 🔲 Фаза 1: Осталось (20%)

#### Agents (7 файлов, ~700 строк)

**Общая структура агента:**
```python
def agent_name(state: Dict) -> Dict:
    """Агент для этапа X"""
    prompts = PromptLibrary()
    ollama = OllamaClient()

    # 1. Генерация промпта
    prompt = prompts.get_X_prompt(...)

    # 2. Вызов LLM
    response = ollama.generate(prompt, stage='X')

    # 3. Парсинг ответа
    data = safe_parse_yaml(response['content'])

    # 4. Post-processing (если нужно)
    # Например: применение формул баланса для мобов

    # 5. Обновление state
    state['X'] = data

    return state
```

##### 🔲 agents/idea_agent.py (~80 строк)
- Генерация концепции зоны
- Вход: user_theme (опционально), level_range
- Выход: JSON с id, name, description, folklore_basis, etc
- Температура: 0.8 (высокая креативность)

##### 🔲 agents/lore_agent.py (~90 строк)
- Детальный лор на основе идеи
- Вход: idea
- Выход: JSON с history, folklore_basis, key_characters, atmosphere, etc
- Температура: 0.7

##### 🔲 agents/structure_agent.py (~100 строк)
- Топология комнат (граф)
- Вход: idea, lore
- Выход: JSON с rooms_graph (id, exits, sector, notes)
- Температура: 0.3 (точность)

##### 🔲 agents/rooms_agent.py (~150 строк)
- **Batch генерация комнат (по 3 за раз)**
- Вход: lore, structure, previous_rooms
- Выход: YAML список комнат
- Температура: 0.5
- **Особенности:**
  - Цикл по батчам (0, 3, 6, ...)
  - summarize_rooms для контекста
  - Human review КАЖДОГО batch

##### 🔲 agents/mobs_agent.py (~140 строк)
- Генерация мобов
- Вход: lore, rooms_summary, level_range
- Выход: YAML список мобов
- Температура: 0.4
- **POST-PROCESSING:**
  - Применение calc_mob_exp
  - Применение calc_mob_gold
  - Корректировка damage_dice если нужно
  - Валидация stats

##### 🔲 agents/objects_agent.py (~80 строк)
- Генерация объектов (лут)
- Вход: lore, mobs_summary, level_range
- Выход: YAML список объектов
- Температура: 0.5

##### 🔲 agents/quests_agent.py (~90 строк)
- Генерация квестов
- Вход: lore, rooms/mobs/objects summaries
- Выход: YAML список квестов
- Температура: 0.6

#### Main CLI (1 файл, ~300 строк)

##### 🔲 main.py
```python
#!/usr/bin/env python3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='Zone Generator для МУД "Былины"'
    )

    # Режимы
    parser.add_argument('--interactive', action='store_true', default=True)
    parser.add_argument('--auto', action='store_true')
    parser.add_argument('--refine', type=str)

    # Параметры
    parser.add_argument('--theme', type=str)
    parser.add_argument('--level', type=str)
    parser.add_argument('--output', type=str, default='zones/draft/')
    parser.add_argument('--model', type=str, default='qwen2.5:14b')
    parser.add_argument('--ollama-url', type=str, default='http://localhost:11434')

    args = parser.parse_args()

    # Simple sequential generator (без LangGraph пока)
    generator = SimpleZoneGenerator(
        interactive=args.interactive and not args.auto,
        ollama_url=args.ollama_url
    )

    if args.refine:
        # Режим улучшения
        generator.refine_zone(args.refine)
    else:
        # Режим создания
        generator.generate_zone(
            theme=args.theme,
            level_range=parse_level_range(args.level)
        )

class SimpleZoneGenerator:
    """Простой sequential генератор (MVP без LangGraph)"""

    def generate_zone(self, theme, level_range):
        state = {
            'user_theme': theme,
            'level_range': level_range
        }

        # Этап 1: Idea
        state = idea_agent(state)
        if self.interactive:
            if not user_approve("Одобрить идею?"):
                state['idea'] = user_edit(state['idea'])

        # Этап 2: Lore
        state = lore_agent(state)
        if self.interactive:
            if not user_approve("Одобрить лор?"):
                state['lore'] = user_edit(state['lore'])

        # Этап 3: Structure
        state = structure_agent(state)
        if self.interactive:
            if not user_approve("Одобрить структуру?"):
                state['structure'] = user_edit(state['structure'])

        # Этап 4: Rooms (batch)
        state = rooms_agent(state)

        # Этап 5: Mobs
        state = mobs_agent(state)
        if self.interactive:
            if not user_approve("Одобрить мобов?"):
                state['mobiles'] = user_edit(state['mobiles'])

        # Этап 6: Objects
        state = objects_agent(state)
        if self.interactive:
            if not user_approve("Одобрить объекты?"):
                state['objects'] = user_edit(state['objects'])

        # Этап 7: Quests
        state = quests_agent(state)
        if self.interactive:
            if not user_approve("Одобрить квесты?"):
                state['quests'] = user_edit(state['quests'])

        # Валидация
        zone_yaml = assemble_zone_yaml(state)
        score, errors = self.validate(zone_yaml)

        print(f"Валидация: {score}/100")

        if score < 90:
            if user_approve("Запустить рефайнмент?"):
                state = self.refine(state, errors, max_iterations=3)

        # Сохранение
        filename = sanitize_filename(state['idea']['name']) + '.yaml'
        output_path = Path(self.output_dir) / filename
        output_path.write_text(zone_yaml, encoding='utf-8')

        print(f"✅ Зона сохранена: {output_path}")
```

#### Тестирование (~100 строк)

##### 🔲 tests/test_balance.py
```python
def test_mob_exp_calculation():
    assert calc_mob_exp(13, 'TRASH') == 1690  # 13^2 * 10
    assert calc_mob_exp(13, 'BOSS') == 5070   # 13^2 * 30

def test_mob_gold_calculation():
    min_g, max_g = calc_mob_gold(13, 'TRASH')
    assert min_g == 45   # 13*5*0.7
    assert max_g == 84   # 13*5*1.3
```

##### 🔲 tests/test_yaml_utils.py
```python
def test_safe_parse_yaml():
    yaml_str = """
    zone:
      meta:
        id: test
    """
    result = safe_parse_yaml(yaml_str)
    assert result['zone']['meta']['id'] == 'test'
```

---

### 🔲 Фаза 2: LangGraph Integration (не начато)

**Планируется:**
- orchestrator.py с LangGraph workflow
- State definition (TypedDict)
- Human review nodes
- Conditional edges (validation → refinement loop)
- Checkpoint механизм

**Зависимости:**
```bash
pip install langgraph langchain-core
```

---

### 🔲 Фаза 3: Agents Enhancement (не начато)

**Планируется:**
- Интеграция агентов с LangGraph state
- Улучшение batch обработки
- Function calling для mobs balance
- Улучшение error handling

---

### 🔲 Фаза 4: Refinement (не начато)

**Планируется:**
- refiner_agent.py
- Интеграция с validator.py
- Приоритизация ошибок
- Iterative refinement (max 3 iterations)

---

### 🔲 Фаза 5: Polish (не начато)

**Планируется:**
- CLI улучшения
- Progress tracking (tqdm)
- Документация
- Examples

---

## Технические детали

### Model Configuration

| Этап | Модель | VRAM | Температура | Скорость |
|------|--------|------|-------------|----------|
| idea | qwen2.5:14b | 9GB | 0.8 | Средняя |
| lore | qwen2.5:14b | 9GB | 0.7 | Средняя |
| rooms | qwen2.5:14b | 9GB | 0.5 | Средняя |
| mobs | qwen2.5:14b | 9GB | 0.4 | Средняя |
| quests | qwen2.5:14b | 9GB | 0.6 | Средняя |
| structure | qwen2.5:7b | 4GB | 0.3 | Быстрая |
| objects | qwen2.5:7b | 4GB | 0.5 | Быстрая |
| refiner | qwen2.5:32b-q4 | 11GB | 0.3 | Медленная |

### Context Window Usage

**Batch 3 комнаты:**
- Input: ~2825 tokens (8.6%)
- Output: ~2000 tokens (6.1%)
- Total: ~4825 tokens (14.7%)
- **Запас:** 85.3% context window

### Performance Estimates

**Время генерации (RTX 2080 Ti):**
- Idea: ~30s
- Lore: ~45s
- Structure: ~20s
- Rooms (12 комнат, 4 batches): ~3-4 min
- Mobs (6 мобов): ~2 min
- Objects (8 объектов): ~1.5 min
- Quests (2 квеста): ~1 min
- Validation: ~1 min
- **Total:** ~10-12 минут (без пауз на review)

**С интерактивным режимом:** ~15-30 минут (в зависимости от правок)

---

## Следующие шаги

### Немедленно (для завершения Phase 1)

1. **Создать agents/__init__.py**
2. **Создать 7 агентов:**
   - idea_agent.py
   - lore_agent.py
   - structure_agent.py
   - rooms_agent.py (важен batch processing!)
   - mobs_agent.py (важен post-processing баланса!)
   - objects_agent.py
   - quests_agent.py

3. **Создать main.py:**
   - CLI с argparse
   - SimpleZoneGenerator class
   - Sequential workflow
   - Интеграция с validator.py для финальной валидации

4. **Базовое тестирование:**
   - Тест формул баланса
   - Тест парсинга YAML
   - End-to-end тест генерации простой зоны (5 комнат)

### Краткосрочно (MVP)

5. **Документация:**
   - Обновить README.md
   - Создать USAGE.md с примерами
   - Записать видео-демо

6. **Рефайнмент промптов:**
   - A/B тестирование разных формулировок
   - Сбор примеров хороших/плохих генераций
   - Итерация на основе feedback

### Среднесрочно (Phase 2-3)

7. **LangGraph integration**
8. **Улучшение агентов**
9. **Function calling для точности баланса**

---

## Метрики успеха

**Критерии для завершения Phase 1:**
- ✅ Все модули инфраструктуры созданы (80% done)
- 🔲 7 агентов работают
- 🔲 main.py генерирует валидный YAML
- 🔲 Генерация простой зоны (5 комнат, 3 моба) проходит валидацию с score >= 60

**Критерии для MVP:**
- 🔲 Генерация зоны занимает <= 30 минут (с интерактивным режимом)
- 🔲 90%+ генерируемых зон имеют валидный YAML
- 🔲 50%+ зон достигают score >= 75 без ручных правок
- 🔲 100% мобов имеют корректный баланс (exp/gold автоматически)

**Критерии для Production:**
- 🔲 Генерация зоны <= 15 минут
- 🔲 50%+ зон достигают score >= 90 после рефайнмента
- 🔲 Checkpoint механизм работает (можно прервать и продолжить)
- 🔲 Документация полная

---

## Известные риски

1. **LLM невалидный YAML** (вероятность 20-30%)
   - Митигация: retry logic, user_edit fallback

2. **Не достижение 90+ score** (вероятность 40-50%)
   - Митигация: refiner agent, приоритизация критичных ошибок

3. **Context overflow для больших зон** (вероятность 10-20%)
   - Митигация: batch processing, summaries, context_manager

4. **Ollama timeout** (вероятность 10-15%)
   - Митигация: retry с увеличенным timeout, progress indicator

---

## Changelog

### 2026-02-06 (Phase 1 start)
- ✅ Создана структура проекта
- ✅ Реализованы все вспомогательные модули (llm, balance, prompts, utils)
- ✅ Написано ~1636 строк кода
- ✅ Документирован план разработки
- 🔲 Осталось: агенты и CLI

---

## Контакты и ссылки

- **План:** [docs/zone-generator-plan.md](docs/zone-generator-plan.md)
- **README:** [tools/generator/README.md](tools/generator/README.md)
- **Формат зон:** [docs/zone-format-v2.md](docs/zone-format-v2.md)
- **Игровые механики:** [docs/game-mechanics.md](docs/game-mechanics.md)
