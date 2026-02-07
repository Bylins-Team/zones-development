"""
Конфигурация Zone Generator
"""

# RTX 4070 Ti = 12GB VRAM (Ada Lovelace, очень быстрая)
# Qwen2.5:14b (9GB) - влезает комфортно, лучшая утилизация GPU
# Qwen3:8b (5GB) - новее, но меньше (если доступен)
# Qwen2.5:32b-q4_K_M (10-11GB quantized) - тоже влезет!

MODEL_CONFIG = {
    # RTX 4070 Ti: используем 14b для баланса качества и скорости
    # 9GB занято, 3GB свободно для KV cache
    'idea': 'qwen2.5:14b',          # Креативная генерация концепции
    'lore': 'qwen2.5:14b',          # Фольклор и нарратив
    'rooms': 'qwen2.5:14b',         # Качество описаний комнат
    'mobs': 'qwen2.5:14b',          # Описания + характеристики мобов
    'quests': 'qwen2.5:14b',        # Нарративное качество квестов

    # Структурные этапы - можно 7b (быстрее, проще задача)
    'structure': 'qwen2.5:7b',      # Топология графа комнат
    'objects': 'qwen2.5:7b',        # Описания объектов

    # Рефайнмент - 14b для качества финальной полировки
    'refiner': 'qwen2.5:14b',

    # Для слабых машин (< 8GB VRAM) закомментируйте выше и используйте:
    # 'idea': 'qwen2.5:7b',
    # 'lore': 'qwen2.5:7b',
    # 'rooms': 'qwen2.5:7b',
    # 'mobs': 'qwen2.5:7b',
    # 'quests': 'qwen2.5:7b',
    # 'structure': 'qwen2.5:7b',
    # 'objects': 'qwen2.5:7b',
    # 'refiner': 'qwen2.5:7b',
}

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
    'ollama_timeout': 180,      # Таймаут запроса в секундах
    'ollama_retry': True,       # Retry при timeout
}

# Пути
DEFAULT_OUTPUT_DIR = "zones/draft/"
CHECKPOINT_DIR = ".checkpoints/"
