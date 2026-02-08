"""
Конфигурация Zone Generator
"""

import os
from dotenv import load_dotenv
from .profiles import get_profile

# Загружаем .env для API ключей
load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# LLM PROVIDER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# Провайдер по умолчанию (можно переопределить через --provider в CLI)
# Доступные: ollama, anthropic, openai, deepseek, xai, cerebras
DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'ollama')

# Конфигурация моделей для разных провайдеров
PROVIDER_MODEL_CONFIGS = {
    'ollama': {
        'idea': 'qwen2.5:14b',
        'lore': 'qwen2.5:14b',
        'structure': 'qwen2.5:7b',
        'rooms': 'qwen2.5:14b',
        'mobs': 'qwen2.5:14b',
        'objects': 'qwen2.5:7b',
        'quests': 'qwen2.5:14b',
        'refiner': 'qwen2.5:14b',
    },
    'anthropic': {
        'idea': 'claude-sonnet-4.5-20250929',
        'lore': 'claude-sonnet-4.5-20250929',
        'structure': 'claude-haiku-4.5-20251001',
        'rooms': 'claude-sonnet-4.5-20250929',
        'mobs': 'claude-sonnet-4.5-20250929',
        'objects': 'claude-haiku-4.5-20251001',
        'quests': 'claude-sonnet-4.5-20250929',
        'refiner': 'claude-opus-4.6-20250808',
    },
    'openai': {
        'idea': 'gpt-4o',
        'lore': 'gpt-4o',
        'structure': 'gpt-4o-mini',
        'rooms': 'gpt-4o',
        'mobs': 'gpt-4o',
        'objects': 'gpt-4o-mini',
        'quests': 'gpt-4o',
        'refiner': 'gpt-4o',
    },
    'deepseek': {
        'idea': 'deepseek-chat',
        'lore': 'deepseek-chat',
        'structure': 'deepseek-chat',
        'rooms': 'deepseek-chat',
        'mobs': 'deepseek-chat',
        'objects': 'deepseek-chat',
        'quests': 'deepseek-chat',
        'refiner': 'deepseek-chat',
    },
    'xai': {
        'idea': 'grok-2-latest',
        'lore': 'grok-2-latest',
        'structure': 'grok-2-latest',
        'rooms': 'grok-2-latest',
        'mobs': 'grok-2-latest',
        'objects': 'grok-2-latest',
        'quests': 'grok-2-latest',
        'refiner': 'grok-2-latest',
    },
    'cerebras': {
        'idea': 'llama-3.3-70b',
        'lore': 'llama-3.3-70b',
        'structure': 'llama-3.1-8b',
        'rooms': 'llama-3.3-70b',
        'mobs': 'llama-3.3-70b',
        'objects': 'llama-3.1-8b',
        'quests': 'llama-3.3-70b',
        'refiner': 'llama-3.3-70b',
    },
    'kilo': {
        'idea': 'kilo-chat',
        'lore': 'kilo-chat',
        'structure': 'kilo-chat',
        'rooms': 'kilo-chat',
        'mobs': 'kilo-chat',
        'objects': 'kilo-chat',
        'quests': 'kilo-chat',
        'refiner': 'kilo-chat',
    },
    'openrouter': {
        'idea': 'anthropic/claude-sonnet-4.5',
        'lore': 'anthropic/claude-sonnet-4.5',
        'structure': 'anthropic/claude-haiku-4.5',
        'rooms': 'anthropic/claude-sonnet-4.5',
        'mobs': 'anthropic/claude-sonnet-4.5',
        'objects': 'anthropic/claude-haiku-4.5',
        'quests': 'anthropic/claude-sonnet-4.5',
        'refiner': 'anthropic/claude-opus-4.6',
    },
}

# ═══════════════════════════════════════════════════════════════════
# HARDWARE PROFILES (для Ollama)
# ═══════════════════════════════════════════════════════════════════

# Профиль по умолчанию (можно переопределить через --profile в CLI)
DEFAULT_PROFILE = 'default'

# Загружаем профиль по умолчанию
# Чтобы изменить, используйте --profile в командной строке:
#   python -m tools.generator.main --profile rtx4070ti-max ...
#
# Доступные профили (см. profiles.py):
#   default              - RTX 4070 Ti сбалансированный (14b креативные, 7b структурные)
#   rtx4070ti-max        - RTX 4070 Ti максимум (все 14b)
#   rtx4070ti-light      - RTX 4070 Ti быстрый (все 7b)
#   rtx2080ti-balanced   - RTX 2080 Ti сбалансированный (14b креативные, 7b структурные)
#   rtx2080ti-max        - RTX 2080 Ti максимум (все 14b)
#   rtx2080ti-light      - RTX 2080 Ti быстрый (все 7b)
#   low-vram             - Слабые GPU < 8GB (все 7b)
#   cpu-only             - CPU-only режим (все 7b)

MODEL_CONFIG = get_profile(DEFAULT_PROFILE)['models']

# Температуры для разных задач
TEMPERATURE_CONFIG = {
    'idea': 0.8,        # Высокая для креативности
    'lore': 0.7,        # Средне-высокая
    'structure': 0.3,   # Низкая для точности
    'rooms': 0.5,       # Баланс
    'mobs': 0.4,        # Склон к точности
    'objects': 0.5,
    'quests': 0.6,      # Немного креативности
    'refiner': 0.3,     # Точность для исправлений
}

# Context window sizes
CONTEXT_WINDOWS = {
    # Ollama models
    'qwen2.5:7b': 32768,
    'qwen2.5:14b': 32768,
    'qwen2.5:32b': 32768,
    'qwen2.5:32b-q4': 32768,

    # OpenRouter models
    'deepseek/deepseek-chat': 32768,
    'deepseek/deepseek-r1': 32768,
    'anthropic/claude-sonnet-4.5': 200000,
    'anthropic/claude-opus-4.6': 200000,
    'anthropic/claude-haiku-4.5': 200000,
    'openai/gpt-4o': 128000,
    'google/gemini-pro-1.5': 1000000,  # 1M context!
}

# Альтернативные модели (для экспериментов)
ALTERNATIVE_MODELS = {
    'mistral-nemo:12b': 7 * 1024**3,    # 7GB (хуже русский)
    'gemma2:9b': 5.5 * 1024**3,         # 5.5GB (слабоват)
}

# Параметры генерации
GENERATION_CONFIG = {
    'batch_size_rooms': 3,      # Комнат за раз
    'max_refinement_iterations': 3,  # Максимум итераций улучшения
    'target_validation_score': 90,   # Целевой балл валидации
    'ollama_timeout': 180,      # Таймаут по умолчанию (секунды)
    'ollama_retry': True,       # Retry при timeout

    # Специальные таймауты для тяжелых этапов
    'timeout_structure': 600,   # Структура: сложный промпт с примерами (10 минут)
    'timeout_lore': 300,        # Лор: длинные описания (5 минут)
    'timeout_mobs': 300,        # Мобы: батчами по 5 (5 минут)
    'timeout_refiner': 600,     # Refiner: большие зоны (10 минут)
}

# Пути
DEFAULT_OUTPUT_DIR = "zones/draft/"
CHECKPOINT_DIR = ".checkpoints/"
