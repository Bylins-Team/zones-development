# Выбор моделей для генерации

После настройки провайдера (через `setup_provider`) вы можете выбирать конкретные модели для генерации.

## Использование модели по умолчанию

```bash
# Использует настройки из конфига для выбранного провайдера
python -m tools.generator.main --provider openrouter --theme "замок"
```

## Одна модель для всех этапов

Параметр `--model` применяет указанную модель ко **всем** этапам генерации:

```bash
# OpenRouter - использовать Claude Opus для всего
python -m tools.generator.main \
  --provider openrouter \
  --model anthropic/claude-opus-4.6 \
  --theme "древний храм"

# Anthropic - использовать Sonnet
python -m tools.generator.main \
  --provider anthropic \
  --model claude-sonnet-4.5-20250929 \
  --theme "лес"

# Ollama - использовать Qwen 2.5 32B
python -m tools.generator.main \
  --provider ollama \
  --model qwen2.5:32b \
  --theme "подземелье"
```

## Разные модели для разных этапов

Параметр `--models` позволяет точно настроить модель для каждого этапа:

```bash
# Opus для креатива, Haiku для структуры
python -m tools.generator.main \
  --provider anthropic \
  --models '{"idea": "claude-opus-4.6-20250808", "lore": "claude-opus-4.6-20250808", "structure": "claude-haiku-4.5-20251001", "rooms": "claude-sonnet-4.5-20250929"}' \
  --theme "замок"

# OpenRouter - микс разных моделей
python -m tools.generator.main \
  --provider openrouter \
  --models '{"idea": "anthropic/claude-opus-4.6", "lore": "openai/gpt-4o", "rooms": "anthropic/claude-sonnet-4.5"}' \
  --theme "лес"

# Ollama - разные размеры Qwen
python -m tools.generator.main \
  --provider ollama \
  --models '{"idea": "qwen2.5:14b", "structure": "qwen2.5:7b", "refiner": "qwen2.5:32b"}' \
  --theme "пещера"
```

## Этапы генерации

Каждый этап может использовать свою модель:

- **idea** - генерация концепции зоны
- **lore** - создание лора и истории
- **structure** - построение топологии (граф комнат)
- **rooms** - описания комнат
- **mobs** - создание мобов
- **objects** - создание объектов
- **quests** - создание квестов
- **refiner** - улучшение зоны (если валидация не прошла)

## Примеры стратегий

### Стратегия 1: Максимальное качество

Самые мощные модели для всех этапов:

```bash
# Anthropic - всё на Opus
python -m tools.generator.main \
  --provider anthropic \
  --model claude-opus-4.6-20250808 \
  --theme "замок" --rooms 15
```

**Плюсы:** Лучшее качество
**Минусы:** Дорого ($15/M tokens)

### Стратегия 2: Сбалансированная

Мощные модели для креатива, быстрые для структуры:

```bash
# OpenRouter - Opus для креатива, Haiku для остального
python -m tools.generator.main \
  --provider openrouter \
  --models '{"idea": "anthropic/claude-opus-4.6", "lore": "anthropic/claude-opus-4.6", "rooms": "anthropic/claude-sonnet-4.5", "structure": "anthropic/claude-haiku-4.5", "mobs": "anthropic/claude-sonnet-4.5", "objects": "anthropic/claude-haiku-4.5", "quests": "anthropic/claude-sonnet-4.5", "refiner": "anthropic/claude-opus-4.6"}' \
  --theme "храм"
```

**Плюсы:** Хорошее качество, умеренная цена
**Минусы:** Сложная настройка

### Стратегия 3: Экономная

Дешевые модели для всего:

```bash
# OpenRouter - DeepSeek (очень дешево)
python -m tools.generator.main \
  --provider openrouter \
  --model deepseek/deepseek-chat \
  --theme "замок"

# Ollama - локально, бесплатно
python -m tools.generator.main \
  --provider ollama \
  --model qwen2.5:14b \
  --theme "лес"
```

**Плюсы:** Дешево/бесплатно
**Минусы:** Качество ниже

### Стратегия 4: Гибридная (разные провайдеры)

К сожалению, нельзя смешивать провайдеры в одной генерации. Но можно использовать `--resume` для смены провайдера:

```bash
# Начать с Ollama
python -m tools.generator.main \
  --provider ollama \
  --theme "замок" \
  --auto
# Thread ID: zone_20260208_120000_abc123

# Если застряло на mobs, продолжить с Anthropic
python -m tools.generator.main \
  --resume zone_20260208_120000_abc123 \
  --provider anthropic \
  --model claude-sonnet-4.5-20250929 \
  --auto
```

## Как узнать доступные модели?

### OpenRouter

Смотрите на https://openrouter.ai/models

Популярные:
- `anthropic/claude-opus-4.6` - лучшее качество
- `anthropic/claude-sonnet-4.5` - сбалансированная
- `anthropic/claude-haiku-4.5` - быстрая
- `openai/gpt-4o` - GPT-4 Omni
- `google/gemini-2.0-flash-001` - Gemini Flash
- `deepseek/deepseek-chat` - очень дешево

### Anthropic (прямой API)

```bash
claude-opus-4.6-20250808      # $15/M tokens
claude-sonnet-4.5-20250929    # $3/M tokens
claude-haiku-4.5-20251001     # $0.80/M tokens
```

### OpenAI (прямой API)

```bash
gpt-4o                        # $5/M tokens
gpt-4-turbo                   # $10/M tokens
gpt-3.5-turbo                 # $0.50/M tokens
```

### Ollama (локальные)

```bash
# Список установленных моделей
docker exec ollama ollama list

# Популярные для генерации зон
qwen2.5:7b     # Быстрая (4GB VRAM)
qwen2.5:14b    # Сбалансированная (9GB VRAM)
qwen2.5:32b    # Мощная (20GB+ VRAM, quantized влезает в 11GB)
llama3.3:70b   # Очень мощная (40GB+ VRAM)
```

## Рекомендации по выбору

### Для idea и lore (креативность важна)

- 🥇 `claude-opus-4.6` - лучший для нарратива
- 🥈 `claude-sonnet-4.5` - отлично и дешевле
- 🥉 `gpt-4o` - хорошая альтернатива
- 💰 `qwen2.5:14b` (Ollama) - бесплатно, качество приемлемое

### Для structure (точность важна)

- 🥇 `claude-haiku-4.5` - быстро и точно
- 🥈 `gpt-3.5-turbo` - дешево и быстро
- 💰 `qwen2.5:7b` (Ollama) - бесплатно

### Для rooms (описания)

- 🥇 `claude-sonnet-4.5` - отличные описания
- 🥈 `gpt-4o` - хорошо для деталей
- 💰 `qwen2.5:14b` (Ollama) - приемлемо

### Для mobs (баланс важен)

- 🥇 `claude-sonnet-4.5` - хорошо следует формулам
- 🥈 `gpt-4o` - альтернатива
- 💰 `qwen2.5:14b` (Ollama) - нужен post-processing

### Для refiner (исправления)

- 🥇 `claude-opus-4.6` - лучше всего понимает ошибки
- 🥈 `claude-sonnet-4.5` - хорошая альтернатива
- 💰 `qwen2.5:32b` (Ollama) - мощная локальная модель

## Troubleshooting

### Ошибка "Model not found"

```bash
# Проверьте что модель существует
python -m tools.generator.list_providers
```

Для Ollama убедитесь что модель установлена:
```bash
docker exec ollama ollama pull qwen2.5:14b
```

### Ошибка парсинга --models JSON

Используйте одинарные кавычки для JSON:
```bash
# ✓ Правильно
--models '{"idea": "gpt-4o"}'

# ✗ Неправильно
--models {"idea": "gpt-4o"}
```

### Модель слишком медленная

Попробуйте:
1. Меньшую модель (haiku вместо opus)
2. Другого провайдера (Cerebras очень быстрый)
3. Локальный Ollama с GPU

### Плохое качество генерации

Попробуйте:
1. Более мощную модель (opus вместо haiku)
2. Другого провайдера (Claude обычно лучше для нарратива)
3. Настроить модели для разных этапов через --models

## FAQ

**Q: Можно ли смешивать провайдеры в одной генерации?**
A: Нет, но можно использовать --resume для смены провайдера между этапами.

**Q: Какая модель лучше для русского языка?**
A: Claude Sonnet/Opus отлично работают с русским. Qwen 2.5 также хорош.

**Q: Как минимизировать расходы?**
A: Используйте Ollama (бесплатно) или DeepSeek через OpenRouter ($0.14-0.28/M tokens).

**Q: --model или --models?**
A: `--model` проще (одна модель для всего). `--models` для точной настройки.

**Q: Модель из --model перезаписывает конфиг?**
A: Да, полностью. Если хотите частичный override, используйте --models.
