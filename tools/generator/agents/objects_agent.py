"""
Objects Agent - генерация объектов (лут, экипировка)
"""

from typing import Dict
from ..llm import create_llm_client, ContextManager
from ..prompts import PromptLibrary
from ..utils import safe_parse_yaml


def objects_agent(state: Dict, ollama_url: str = "http://localhost:11434") -> Dict:
    """
    Генерация объектов (предметы, лут)

    Args:
        state: State с ключами 'lore', 'mobiles', 'idea'

    Returns:
        State с добавленным ключом 'objects' (list)
    """
    if 'lore' not in state:
        raise ValueError("Отсутствует 'lore' в state")
    if 'mobiles' not in state:
        raise ValueError("Отсутствует 'mobiles' в state")
    if 'idea' not in state:
        raise ValueError("Отсутствует 'idea' в state")

    prompts = PromptLibrary()
    provider = state.get('provider', 'ollama')
    model = state.get('model')
    model_config = state.get('model_config')
    llm = create_llm_client(provider=provider, model=model, model_config=model_config)
    context_mgr = ContextManager()

    lore = state['lore']
    mobiles = state['mobiles']
    idea = state['idea']

    level_range = tuple(idea.get('level_range', [10, 15]))

    # Summarize мобов для контекста
    mobs_summary = context_mgr.summarize_mobs(mobiles)

    # Генерация промпта
    prompt = prompts.get_objects_prompt(lore, mobs_summary, level_range)

    print("\n💎 Генерация объектов...")
    print(f"   Уровни: {level_range[0]}-{level_range[1]}")

    try:
        # Вызов LLM
        response = llm.generate(
            prompt=prompt,
            stage='objects',
            system=prompts.SYSTEM_DESIGNER
        )

        # Парсинг ответа
        parsed = safe_parse_yaml(response['content'], stage='objects')

        # Извлекаем объекты
        if isinstance(parsed, dict) and 'objects' in parsed:
            objects = parsed['objects']
        elif isinstance(parsed, list):
            objects = parsed
        else:
            raise ValueError(f"Неожиданный формат ответа: {type(parsed)}")

        # Обновление state
        state['objects'] = objects

        print(f"   ✓ Всего объектов: {len(objects)}")

        # Статистика по типам
        type_counts = {}
        for obj in objects:
            obj_type = obj.get('type', 'UNKNOWN')
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

        print(f"   📊 Типы:")
        for obj_type, count in sorted(type_counts.items()):
            print(f"      • {obj_type}: {count}")

        return state

    except Exception as e:
        print(f"   ✗ Ошибка при генерации объектов: {e}")
        raise
