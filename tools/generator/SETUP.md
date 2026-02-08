# Настройка провайдеров

Для удобной работы с разными LLM провайдерами используйте утилиту `setup_provider`.

## Быстрый старт

### Интерактивная настройка

```bash
python -m tools.generator.setup_provider
```

Утилита спросит:
1. Какой провайдер настроить
2. API ключ
3. Дополнительные параметры (base URL, модель по умолчанию)

### Настройка через CLI

```bash
# OpenRouter
python -m tools.generator.setup_provider openrouter --api-key sk-or-v1-xxx

# Anthropic (Claude)
python -m tools.generator.setup_provider anthropic --api-key sk-ant-xxx

# OpenAI (ChatGPT)
python -m tools.generator.setup_provider openai --api-key sk-xxx

# DeepSeek
python -m tools.generator.setup_provider deepseek --api-key sk-xxx

# xAI (Grok)
python -m tools.generator.setup_provider xai --api-key xai-xxx

# Cerebras
python -m tools.generator.setup_provider cerebras --api-key xxx

# Kilo AI
python -m tools.generator.setup_provider kilo \
    --api-key xxx \
    --base-url https://api.kilo.ai/v1

# Ollama (локальный)
python -m tools.generator.setup_provider ollama \
    --base-url http://localhost:11434
```

## Где хранятся ключи?

Все ключи сохраняются в `.env` файле в корне проекта.

Структура `.env`:
```bash
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-xxx

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxx

# Ollama (локальный)
OLLAMA_BASE_URL=http://localhost:11434
```

## Использование после настройки

После настройки просто выбирайте провайдер через `--provider`:

```bash
# Использовать OpenRouter
python -m tools.generator.main --provider openrouter --theme "замок"

# Использовать Anthropic
python -m tools.generator.main --provider anthropic --theme "лес"

# Использовать локальный Ollama
python -m tools.generator.main --provider ollama --theme "подземелье"
```

## Проверка настроенных провайдеров

```bash
python -m tools.generator.list_providers
```

Покажет:
- Какие провайдеры настроены (есть API ключи)
- Какие модели доступны
- Статус подключения

## Дополнительные параметры

### Указать модель по умолчанию

```bash
python -m tools.generator.setup_provider anthropic \
    --api-key sk-ant-xxx \
    --default-model claude-opus-4.6-20250808
```

### Custom base URL (для Kilo, Ollama)

```bash
python -m tools.generator.setup_provider ollama \
    --base-url http://192.168.1.100:11434
```

## Безопасность

⚠️ **Важно:**
- `.env` файл включен в `.gitignore` и не попадет в репозиторий
- Не коммитьте `.env` файл в git
- Не делитесь API ключами

## Получение API ключей

### OpenRouter
- Сайт: https://openrouter.ai
- Регистрация: https://openrouter.ai/keys
- Доступ ко всем популярным моделям через один API
- Пополнение баланса от $5

### Anthropic (Claude)
- Сайт: https://console.anthropic.com
- API: https://console.anthropic.com/settings/keys
- Модели: Claude Opus 4.6, Sonnet 4.5, Haiku 4.5
- Цена: от $3/M tokens (Haiku) до $15/M tokens (Opus)

### OpenAI (ChatGPT)
- Сайт: https://platform.openai.com
- API: https://platform.openai.com/api-keys
- Модели: GPT-4o, GPT-4-turbo, GPT-3.5
- Цена: от $0.15/M tokens (GPT-3.5) до $5/M tokens (GPT-4o)

### DeepSeek
- Сайт: https://platform.deepseek.com
- Модели: DeepSeek Chat, DeepSeek Coder
- Цена: очень дешево ($0.14-0.28/M tokens)

### xAI (Grok)
- Сайт: https://x.ai
- API: https://console.x.ai
- Модели: Grok 2

### Cerebras
- Сайт: https://cerebras.ai
- Модели: Llama 3.3 70B, Llama 3.1 8B
- Особенность: очень быстрая генерация

### Kilo AI
- OpenAI-совместимый провайдер
- Настраиваемые модели и endpoint

### Ollama (локальный)
- Сайт: https://ollama.ai
- **Бесплатно** - запуск моделей локально
- Требует GPU (рекомендуется 8GB+ VRAM)
- Модели: Qwen 2.5, Llama 3, Mistral, и др.

## Troubleshooting

### Ошибка "Provider not available"

```bash
# Проверьте что ключ сохранен
cat .env | grep OPENROUTER_API_KEY

# Перенастройте провайдер
python -m tools.generator.setup_provider openrouter
```

### Ошибка "API key invalid"

Проверьте что ключ скопирован полностью:
```bash
python -m tools.generator.setup_provider openrouter --api-key sk-or-v1-полный_ключ
```

### .env файл не создается

Убедитесь что запускаете из корня проекта:
```bash
cd /path/to/mud-zones-development
python -m tools.generator.setup_provider openrouter --api-key xxx
```

## FAQ

**Q: Нужно ли перезапускать после изменения .env?**
A: Да, environment variables загружаются при старте. Перезапустите команду.

**Q: Можно ли использовать несколько провайдеров?**
A: Да! Настройте несколько провайдеров и переключайтесь через `--provider`.

**Q: Можно ли удалить провайдер?**
A: Да, просто удалите соответствующие строки из `.env` файла.

**Q: Где хранить .env файл на production?**
A: Используйте secrets manager (GitHub Secrets, AWS Secrets Manager, etc.) или зашифрованный файл.
