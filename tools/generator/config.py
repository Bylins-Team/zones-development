"""
Конфигурация Zone Generator
"""

from .profiles import get_profile

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
CONTEXT_WINDOW = {
    'qwen2.5:7b': 32768,
    'qwen2.5:14b': 32768,
    'qwen2.5:32b': 32768,
    'qwen2.5:32b-q4': 32768,
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
    'timeout_mobs': 300,        # Мобы: много расчётов + function calling (5 минут)
    'timeout_refiner': 600,     # Refiner: большие зоны (10 минут)
}

# Пути
DEFAULT_OUTPUT_DIR = "zones/draft/"
CHECKPOINT_DIR = ".checkpoints/"
