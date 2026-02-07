"""
Конфигурация Zone Generator
"""

# RTX 2080 Ti = 11GB VRAM
# Qwen2.5:14b (9GB) - влезает
# Qwen2.5:32b-q4_K_M (10-11GB quantized) - влезает!

MODEL_CONFIG = {
    # Все этапы используют легкую модель 7b (4GB VRAM)
    'idea': 'qwen2.5:7b',
    'lore': 'qwen2.5:7b',
    'rooms': 'qwen2.5:7b',
    'mobs': 'qwen2.5:7b',
    'quests': 'qwen2.5:7b',
    'structure': 'qwen2.5:7b',
    'objects': 'qwen2.5:7b',
    'refiner': 'qwen2.5:7b',
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
