"""
Idea Agent - генерация концепции зоны
"""

from typing import Dict
from ..llm import create_llm_client
from ..prompts import PromptLibrary
from ..utils import safe_parse_json


def idea_agent(state: Dict, ollama_url: str = "http://localhost:11434") -> Dict:
    """
    Генерация концепции зоны

    Args:
        state: State с ключами:
            - user_theme (опционально): Тема от пользователя
            - level_range (опционально): (min, max) уровни
            - provider (опционально): LLM провайдер

    Returns:
        State с добавленным ключом 'idea' (dict)
    """
    prompts = PromptLibrary()
    provider = state.get('provider', 'ollama')
    model = state.get('model')
    model_config = state.get('model_config')
    llm = create_llm_client(provider=provider, model=model, model_config=model_config)

    # Получить параметры
    user_theme = state.get('user_theme')
    level_range = state.get('level_range')
    requested_rooms = state.get('requested_rooms')

    # Генерация промпта
    prompt = prompts.get_idea_prompt(user_theme, level_range, requested_rooms)

    print("\n🎨 Генерация концепции зоны...")
    if user_theme:
        print(f"   Тема: {user_theme}")
    if level_range:
        print(f"   Уровни: {level_range[0]}-{level_range[1]}")
    if requested_rooms:
        print(f"   Желаемое количество комнат: {requested_rooms}")

    try:
        # Вызов LLM
        response = llm.generate(
            prompt=prompt,
            stage='idea',
            system=prompts.SYSTEM_DESIGNER
        )

        # Парсинг ответа
        idea = safe_parse_json(response['content'])

        # Валидация обязательных полей
        required_fields = ['id', 'name', 'description', 'level_range']
        missing = [f for f in required_fields if f not in idea]
        if missing:
            raise ValueError(f"Отсутствуют обязательные поля: {missing}")

        # Если пользователь явно указал количество комнат - используем его
        if requested_rooms:
            idea['estimated_rooms'] = requested_rooms
            print(f"   ℹ️  Установлено явное количество комнат: {requested_rooms}")

        # Обновление state
        state['idea'] = idea

        print(f"   ✓ Концепция: {idea['name']}")
        print(f"   ✓ Уровни: {idea['level_range']}")
        print(f"   ✓ Комнат: ~{idea.get('estimated_rooms', 'N/A')}")

        return state

    except Exception as e:
        print(f"   ✗ Ошибка при генерации идеи: {e}")
        raise
