# LangGraph Mode для Zone Generator

## Что это?

**LangGraph** - это фреймворк для создания stateful workflows с LLM. В контексте Zone Generator это дает:

- ✅ **Автоматические циклы валидации** - retry при плохом качестве
- ✅ **Conditional edges** - разные пути генерации
- ✅ **Checkpoints** - сохранение прогресса, можно прервать и продолжить
- ✅ **Human-in-the-loop** - явные точки review
- ✅ **Граф состояний** - визуализация workflow

## Установка

```bash
pip install langgraph langchain-core

# Или из requirements.txt
pip install -r requirements.txt
```

## Использование

### Базовый запуск

```bash
python3 -m tools.generator.main \
  --use-langgraph \
  --theme "Заброшенная мельница" \
  --level 10-15
```

### С профилем GPU

```bash
python3 -m tools.generator.main \
  --use-langgraph \
  --profile rtx4070ti-max \
  --theme "Осада Суздаля булгарами" \
  --level 13-18 \
  --interactive
```

### Автоматический режим

```bash
python3 -m tools.generator.main \
  --use-langgraph \
  --auto \
  --theme "Болото кикимор" \
  --level 15-20
```

## Отличия от SimpleZoneGenerator

| Возможность | SimpleZoneGenerator | LangGraph |
|------------|---------------------|-----------|
| Базовая генерация | ✅ | ✅ |
| Interactive режим | ✅ | ✅ |
| Auto режим | ✅ | ✅ |
| --refine | ✅ | ❌ (пока) |
| Автоматический retry | ❌ | ✅ |
| Checkpoints | ❌ | ✅ |
| Валидация в workflow | ❌ | ✅ |
| Визуализация графа | ❌ | ✅ |
| Conditional edges | ❌ | ✅ |

## Архитектура

```
[START]
   ↓
[idea_node] → [human_review?] → retry? → [idea_node]
   ↓                                ↓
[lore_node]                        OK
   ↓
[structure_node]
   ↓
[rooms_node]
   ↓
[mobs_node]
   ↓
[objects_node]
   ↓
[quests_node]
   ↓
[validation_node] → score < 75? → [refinement_node] → [validation_node]
   ↓                        ↓
  OK                       retry
   ↓
[END]
```

## Checkpoints

LangGraph автоматически сохраняет состояние после каждого узла.

### Прервать и продолжить

```bash
# Запустить генерацию
python3 -m tools.generator.main --use-langgraph --theme "..."

# Прервать (Ctrl+C)
^C
⚠️  Генерация прервана пользователем
   Прогресс сохранён в checkpoint, можно продолжить

# Продолжить (TODO: пока не реализовано)
python3 -m tools.generator.main --use-langgraph --resume <thread_id>
```

## Преимущества для качества

### 1. Автоматический retry при плохих результатах

LangGraph может автоматически regenerate этап если:
- Human review отклонил результат
- Validation score слишком низкий
- Есть критичные ошибки

### 2. Iterative refinement

После валидации автоматически запускается refinement если score < 75.

### 3. Conditional paths

Разные типы зон могут идти разными путями:
- Простые зоны → быстрый путь без refinement
- Сложные зоны → с дополнительной валидацией

## Ограничения

### Пока не реализовано

- ❌ --refine режим в LangGraph (используйте SimpleZoneGenerator)
- ❌ Resume from checkpoint
- ❌ Визуализация графа
- ❌ Custom conditional edges
- ❌ Multi-agent collaboration

### Требования

- Python 3.10+
- langgraph >= 0.2.0
- langchain-core >= 0.3.0

## Когда использовать?

**Используйте LangGraph когда:**
- Нужны автоматические retry
- Генерация долгая и хотите checkpoints
- Хотите экспериментировать с workflow
- Нужна валидация в процессе генерации

**Используйте SimpleZoneGenerator когда:**
- Нужен --refine режим
- Хотите простоту
- Не хотите устанавливать дополнительные зависимости
- Генерация быстрая (< 10 минут)

## Примеры

### Пример 1: Простая зона с LangGraph

```bash
python3 -m tools.generator.main \
  --use-langgraph \
  --theme "Тренировочный полигон" \
  --level 1-5 \
  --auto
```

### Пример 2: Сложная зона с review

```bash
python3 -m tools.generator.main \
  --use-langgraph \
  --profile rtx4070ti-max \
  --theme "Логово дракона в горах" \
  --level 35-40 \
  --interactive
```

### Пример 3: Экспериментальная генерация

```bash
python3 -m tools.generator.main \
  --use-langgraph \
  --theme "Случайная зона" \
  --level 20-25 \
  --auto
```

## Troubleshooting

### LangGraph не установлен

```
❌ Ошибка: LangGraph не установлен
Установите: pip install langgraph langchain-core
```

**Решение:**
```bash
pip install langgraph langchain-core
```

### --refine не работает

```
❌ Ошибка: --refine не поддерживается в LangGraph режиме
```

**Решение:** Используйте SimpleZoneGenerator (без --use-langgraph):
```bash
python3 -m tools.generator.main --refine zones/draft/zone.yaml
```

## Roadmap

- [ ] Resume from checkpoint
- [ ] Визуализация графа (mermaid diagram)
- [ ] Custom conditional edges через конфиг
- [ ] Multi-agent collaboration
- [ ] Streaming output
- [ ] Progress tracking (tqdm)
- [ ] Refine mode в LangGraph
