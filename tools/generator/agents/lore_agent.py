"""
Lore Agent - генерация детального лора зоны
"""

from typing import Dict
from ..llm import create_llm_client
from ..prompts import PromptLibrary
from ..utils import safe_parse_json


def lore_agent(state: Dict, ollama_url: str = "http://localhost:11434") -> Dict:
    """
    Генерация детального лора на основе концепции

    Args:
        state: State с ключом 'idea'

    Returns:
        State с добавленным ключом 'lore' (dict)
    """
    if 'idea' not in state:
        raise ValueError("Отсутствует 'idea' в state. Запустите idea_agent сначала.")

    prompts = PromptLibrary()
    provider = state.get('provider', 'ollama')
    llm = create_llm_client(provider=provider)

    idea = state['idea']

    # Генерация промпта
    prompt = prompts.get_lore_prompt(idea)

    print("\n📖 Генерация лора зоны...")
    print(f"   Зона: {idea['name']}")

    try:
        # Вызов LLM
        response = llm.generate(
            prompt=prompt,
            stage='lore',
            system=prompts.SYSTEM_DESIGNER
        )

        # Парсинг ответа
        lore = safe_parse_json(response['content'])

        # Валидация
        required_fields = ['history', 'folklore_basis', 'current_state']
        missing = [f for f in required_fields if f not in lore]
        if missing:
            raise ValueError(f"Отсутствуют обязательные поля лора: {missing}")

        # Обновление state
        state['lore'] = lore

        print(f"   ✓ История: {len(lore.get('history', ''))} символов")
        print(f"   ✓ Ключевые персонажи: {len(lore.get('key_characters', []))}")
        print(f"   ✓ Секреты: {len(lore.get('secrets', []))}")

        return state

    except Exception as e:
        print(f"   ✗ Ошибка при генерации лора: {e}")
        raise
