"""
Профили конфигурации для разных GPU
"""

# Профили моделей для разных GPU и задач
MODEL_PROFILES = {
    # === RTX 4070 Ti (12GB VRAM) ===

    'default': {
        'description': 'RTX 4070 Ti - сбалансированный (14b креативные, 7b структурные)',
        'vram': '12GB',
        'models': {
            'idea': 'qwen2.5:14b',
            'lore': 'qwen2.5:14b',
            'rooms': 'qwen2.5:14b',
            'mobs': 'qwen2.5:14b',
            'quests': 'qwen2.5:14b',
            'structure': 'qwen2.5:7b',
            'objects': 'qwen2.5:7b',
            'refiner': 'qwen2.5:14b',
        }
    },

    'rtx4070ti-max': {
        'description': 'RTX 4070 Ti - максимальное качество (все 14b)',
        'vram': '12GB',
        'models': {
            'idea': 'qwen2.5:14b',
            'lore': 'qwen2.5:14b',
            'rooms': 'qwen2.5:14b',
            'mobs': 'qwen2.5:14b',
            'quests': 'qwen2.5:14b',
            'structure': 'qwen2.5:14b',
            'objects': 'qwen2.5:14b',
            'refiner': 'qwen2.5:14b',
        }
    },

    'rtx4070ti-light': {
        'description': 'RTX 4070 Ti - быстрый режим (все 7b)',
        'vram': '12GB',
        'models': {
            'idea': 'qwen2.5:7b',
            'lore': 'qwen2.5:7b',
            'rooms': 'qwen2.5:7b',
            'mobs': 'qwen2.5:7b',
            'quests': 'qwen2.5:7b',
            'structure': 'qwen2.5:7b',
            'objects': 'qwen2.5:7b',
            'refiner': 'qwen2.5:7b',
        }
    },

    # === RTX 2080 Ti (11GB VRAM) ===

    'rtx2080ti-balanced': {
        'description': 'RTX 2080 Ti - сбалансированный (14b креативные, 7b структурные)',
        'vram': '11GB',
        'models': {
            'idea': 'qwen2.5:14b',
            'lore': 'qwen2.5:14b',
            'rooms': 'qwen2.5:14b',
            'mobs': 'qwen2.5:14b',
            'quests': 'qwen2.5:14b',
            'structure': 'qwen2.5:7b',
            'objects': 'qwen2.5:7b',
            'refiner': 'qwen2.5:14b',
        }
    },

    'rtx2080ti-max': {
        'description': 'RTX 2080 Ti - максимум (все 14b, может быть медленно)',
        'vram': '11GB',
        'models': {
            'idea': 'qwen2.5:14b',
            'lore': 'qwen2.5:14b',
            'rooms': 'qwen2.5:14b',
            'mobs': 'qwen2.5:14b',
            'quests': 'qwen2.5:14b',
            'structure': 'qwen2.5:14b',
            'objects': 'qwen2.5:14b',
            'refiner': 'qwen2.5:14b',
        }
    },

    'rtx2080ti-light': {
        'description': 'RTX 2080 Ti - легкий (все 7b, быстро)',
        'vram': '11GB',
        'models': {
            'idea': 'qwen2.5:7b',
            'lore': 'qwen2.5:7b',
            'rooms': 'qwen2.5:7b',
            'mobs': 'qwen2.5:7b',
            'quests': 'qwen2.5:7b',
            'structure': 'qwen2.5:7b',
            'objects': 'qwen2.5:7b',
            'refiner': 'qwen2.5:7b',
        }
    },

    # === Слабые GPU (< 8GB VRAM) ===

    'low-vram': {
        'description': 'Слабые GPU - только 7b модели (< 8GB VRAM)',
        'vram': '6-8GB',
        'models': {
            'idea': 'qwen2.5:7b',
            'lore': 'qwen2.5:7b',
            'rooms': 'qwen2.5:7b',
            'mobs': 'qwen2.5:7b',
            'quests': 'qwen2.5:7b',
            'structure': 'qwen2.5:7b',
            'objects': 'qwen2.5:7b',
            'refiner': 'qwen2.5:7b',
        }
    },

    # === CPU-only (без GPU) ===

    'cpu-only': {
        'description': 'CPU-only режим (очень медленно, только 7b)',
        'vram': 'N/A',
        'models': {
            'idea': 'qwen2.5:7b',
            'lore': 'qwen2.5:7b',
            'rooms': 'qwen2.5:7b',
            'mobs': 'qwen2.5:7b',
            'quests': 'qwen2.5:7b',
            'structure': 'qwen2.5:7b',
            'objects': 'qwen2.5:7b',
            'refiner': 'qwen2.5:7b',
        }
    },
}


def get_profile(profile_name: str = 'default') -> dict:
    """
    Получить профиль конфигурации по имени

    Args:
        profile_name: Имя профиля (default, rtx4070ti-max, rtx2080ti-balanced, etc.)

    Returns:
        Dict с конфигурацией модели

    Raises:
        ValueError: Если профиль не найден
    """
    if profile_name not in MODEL_PROFILES:
        available = ', '.join(MODEL_PROFILES.keys())
        raise ValueError(
            f"Профиль '{profile_name}' не найден.\n"
            f"Доступные профили: {available}"
        )

    return MODEL_PROFILES[profile_name]


def list_profiles() -> None:
    """Вывести список всех доступных профилей"""
    print("Доступные профили конфигурации:\n")

    for name, profile in MODEL_PROFILES.items():
        desc = profile['description']
        vram = profile['vram']

        # Подсчитаем уникальные модели
        models = set(profile['models'].values())
        models_str = ', '.join(sorted(models))

        print(f"  {name:20} - {desc}")
        print(f"  {'':20}   VRAM: {vram}, Модели: {models_str}\n")


if __name__ == '__main__':
    list_profiles()
