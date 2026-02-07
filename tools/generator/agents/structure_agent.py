"""
Structure Agent - генерация топологии зоны (граф комнат)
"""

from typing import Dict
from ..llm import OllamaClient
from ..prompts import PromptLibrary
from ..utils import safe_parse_json
from ..config import GENERATION_CONFIG


def structure_agent(state: Dict, ollama_url: str = "http://localhost:11434") -> Dict:
    """
    Генерация структуры зоны (топология комнат)

    Args:
        state: State с ключами 'idea' и 'lore'

    Returns:
        State с добавленным ключом 'structure' (dict)
    """
    if 'idea' not in state:
        raise ValueError("Отсутствует 'idea' в state")
    if 'lore' not in state:
        raise ValueError("Отсутствует 'lore' в state")

    prompts = PromptLibrary()
    ollama = OllamaClient(ollama_url=ollama_url)

    idea = state['idea']
    lore = state['lore']

    # Генерация промпта
    prompt = prompts.get_structure_prompt(idea, lore)

    print("\n🗺️  Генерация структуры зоны...")
    print(f"   Зона: {idea['name']}")

    try:
        # Вызов LLM с увеличенным timeout (сложный промпт)
        timeout = GENERATION_CONFIG.get('timeout_structure', 300)
        response = ollama.generate(
            prompt=prompt,
            stage='structure',
            system=prompts.SYSTEM_DESIGNER,
            timeout=timeout
        )

        # Парсинг ответа
        structure = safe_parse_json(response['content'])

        # Валидация
        if 'rooms_graph' not in structure:
            raise ValueError("Отсутствует 'rooms_graph' в структуре")

        if 'total_rooms' not in structure:
            structure['total_rooms'] = len(structure['rooms_graph'])

        # Обновление state
        state['structure'] = structure

        print(f"   ✓ Комнат: {structure['total_rooms']}")
        print(f"   ✓ Топология: {structure.get('topology_type', 'mixed')}")
        print(f"   ✓ Секций: {len(structure.get('sections', []))}")

        return state

    except Exception as e:
        print(f"   ✗ Ошибка при генерации структуры: {e}")
        raise
