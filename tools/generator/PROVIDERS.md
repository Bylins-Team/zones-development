# Multi-Provider LLM Support

Zone Generator теперь поддерживает множественные LLM провайдеры!

## Поддерживаемые провайдеры

### 🟢 Локальные (бесплатно)
- **Ollama** - локальные модели (Qwen, Llama, Mistral, etc.)

### 💰 Облачные (платные API)
- **Anthropic** - Claude 4.5/4.6 (Opus, Sonnet, Haiku)
- **OpenAI** - ChatGPT (GPT-4o, GPT-4o-mini)
- **DeepSeek** - DeepSeek Chat
- **xAI** - Grok 2
- **Cerebras** - Llama 3.1/3.3 (сверхбыстрые)

## Быстрый старт

### 1. Настройка API ключей

Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте ваши API ключи:
```bash
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# OpenAI (ChatGPT)
OPENAI_API_KEY=sk-xxxxx

# DeepSeek
DEEPSEEK_API_KEY=xxxxx

# xAI (Grok)
XAI_API_KEY=xxxxx

# Cerebras
CEREBRAS_API_KEY=xxxxx
```

### 2. Проверка доступных провайдеров

```bash
python -m tools.generator.list_providers
```

Вывод покажет какие провайдеры настроены:
```
✅ OLLAMA          ДОСТУПЕН
❌ ANTHROPIC       НЕ НАСТРОЕН (нет API ключа)
❌ OPENAI          НЕ НАСТРОЕН (нет API ключа)
...
```

### 3. Использование

#### Использовать Ollama (по умолчанию)
```bash
python -m tools.generator.main --auto --theme "древний замок" --level "10-15"
```

#### Использовать Claude (Anthropic)
```bash
python -m tools.generator.main --provider anthropic --auto --theme "древний замок" --level "10-15"
```

#### Использовать ChatGPT (OpenAI)
```bash
python -m tools.generator.main --provider openai --auto --theme "древний замок" --level "10-15"
```

#### Использовать DeepSeek
```bash
python -m tools.generator.main --provider deepseek --auto --theme "древний замок" --level "10-15"
```

#### Использовать Grok (xAI)
```bash
python -m tools.generator.main --provider xai --auto --theme "древний замок" --level "10-15"
```

#### Использовать Cerebras
```bash
python -m tools.generator.main --provider cerebras --auto --theme "древний замок" --level "10-15"
```

## Алиасы провайдеров

Для удобства поддерживаются алиасы:
- `--provider claude` → `anthropic`
- `--provider chatgpt` или `--provider gpt` → `openai`
- `--provider grok` → `xai`

## Конфигурация моделей

Для каждого провайдера настроены оптимальные модели для разных этапов:

### Anthropic (Claude)
- **Креативные задачи** (idea, lore, rooms, quests): Claude Sonnet 4.5
- **Структурные задачи** (structure, objects): Claude Haiku 4.5
- **Refinement**: Claude Opus 4.6 (самая мощная)

### OpenAI (ChatGPT)
- **Креативные задачи**: GPT-4o
- **Структурные задачи**: GPT-4o-mini
- **Refinement**: GPT-4o

### Ollama (локально)
- **Креативные задачи**: Qwen2.5:14b
- **Структурные задачи**: Qwen2.5:7b (быстрее)
- **Refinement**: Qwen2.5:14b

Модели можно изменить в `tools/generator/config.py` → `PROVIDER_MODEL_CONFIGS`

## Стоимость

### Бесплатно:
- **Ollama** - полностью бесплатно (локально на вашем GPU/CPU)

### Платно (примерные цены):
- **Claude Sonnet 4.5**: $3/1M input tokens, $15/1M output tokens
- **Claude Haiku 4.5**: $0.25/1M input, $1.25/1M output
- **GPT-4o**: $2.50/1M input, $10/1M output
- **GPT-4o-mini**: $0.15/1M input, $0.60/1M output
- **DeepSeek**: ~$0.14/1M input, ~$0.28/1M output (дешево!)
- **Grok 2**: ~$5/1M tokens
- **Cerebras**: ~$0.60/1M tokens (очень быстро!)

**Оценка стоимости генерации одной зоны:**
- Ollama: **$0** (бесплатно)
- DeepSeek: **~$0.05-0.10**
- GPT-4o-mini: **~$0.10-0.20**
- Claude Haiku/Sonnet: **~$0.50-1.00**
- GPT-4o: **~$1.00-2.00**
- Claude Opus: **~$2.00-5.00**

## Рекомендации

### Для экспериментов:
- **Ollama** (бесплатно, локально)
- **DeepSeek** (очень дешево, хорошее качество)

### Для производства:
- **Claude Sonnet 4.5** (отличное качество, умеренная цена)
- **GPT-4o** (стабильное качество)

### Для быстрых итераций:
- **Cerebras** (сверхбыстрые ответы)
- **Claude Haiku 4.5** (быстро и дешево)

### Для максимального качества:
- **Claude Opus 4.6** (лучшее качество, дорого)

## Troubleshooting

### Ошибка "Провайдер недоступен"
```
❌ Провайдер 'anthropic' недоступен!
   Причина: нет API ключа в .env
```

**Решение:**
1. Проверьте что `.env` файл существует
2. Убедитесь что API ключ правильно указан
3. Перезапустите скрипт после добавления ключа

### Проверка подключения
```bash
# Проверить все провайдеры
python -m tools.generator.list_providers

# Попробовать сгенерировать маленькую зону для теста
python -m tools.generator.main --provider anthropic --auto --theme "тест" --level "1-5"
```

## Дополнительная настройка

### Изменить провайдер по умолчанию

В `.env`:
```bash
DEFAULT_LLM_PROVIDER=anthropic
```

Или через environment variable:
```bash
export DEFAULT_LLM_PROVIDER=anthropic
python -m tools.generator.main --auto ...
```

### Изменить модели для провайдера

Отредактируйте `tools/generator/config.py` → `PROVIDER_MODEL_CONFIGS`:
```python
PROVIDER_MODEL_CONFIGS = {
    'anthropic': {
        'idea': 'claude-opus-4.6-20250808',  # Поменяли на Opus
        'lore': 'claude-sonnet-4.5-20250929',
        # ...
    }
}
```

## Документация провайдеров

- **Anthropic**: https://docs.anthropic.com/
- **OpenAI**: https://platform.openai.com/docs
- **DeepSeek**: https://platform.deepseek.com/
- **xAI**: https://docs.x.ai/
- **Cerebras**: https://docs.cerebras.ai/
