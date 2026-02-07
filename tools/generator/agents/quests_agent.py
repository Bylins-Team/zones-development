"""
Quests Agent - генерация квестов
"""

from typing import Dict
from ..llm import OllamaClient, ContextManager
from ..prompts import PromptLibrary
from ..utils import safe_parse_yaml


def quests_agent(state: Dict, ollama_url: str = "http://localhost:11434") -> Dict:
    """
    Генерация квестов

    Args:
        state: State с ключами 'lore', 'rooms', 'mobiles', 'objects'

    Returns:
        State с добавленным ключом 'quests' (list)
    """
    if 'lore' not in state:
        raise ValueError("Отсутствует 'lore' в state")

    prompts = PromptLibrary()
    ollama = OllamaClient(ollama_url=ollama_url)
    context_mgr = ContextManager()

    lore = state['lore']

    # Summaries для контекста
    rooms_summary = context_mgr.summarize_rooms(state.get('rooms', []))
    mobs_summary = context_mgr.summarize_mobs(state.get('mobiles', []))
    objects_summary = ""  # TODO: Добавить summarize_objects если нужно

    # Генерация промпта
    prompt = prompts.get_quests_prompt(lore, rooms_summary, mobs_summary, objects_summary)

    print("\n📜 Генерация квестов...")

    try:
        # Вызов LLM
        response = ollama.generate(
            prompt=prompt,
            stage='quests',
            system=prompts.SYSTEM_DESIGNER
        )

        # Парсинг ответа
        parsed = safe_parse_yaml(response['content'])

        # Извлекаем квесты
        if isinstance(parsed, dict) and 'quests' in parsed:
            quests = parsed['quests']
        elif isinstance(parsed, list):
            quests = parsed
        else:
            # Квесты опциональны, можно пропустить
            print("   ⚠️  Квесты не сгенерированы (не критично)")
            quests = []

        # Обновление state
        state['quests'] = quests

        print(f"   ✓ Всего квестов: {len(quests)}")

        if quests:
            print(f"   📊 Квесты:")
            for quest in quests:
                quest_name = quest.get('name', 'Безымянный квест')
                quest_type = quest.get('type', 'UNKNOWN')
                print(f"      • {quest_name} ({quest_type})")

        return state

    except Exception as e:
        print(f"   ⚠️  Ошибка при генерации квестов: {e}")
        # Квесты не критичны, можно продолжить
        state['quests'] = []
        return state
