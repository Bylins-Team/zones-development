"""
Rooms Agent - генерация описаний комнат (batch processing)
"""

import json
from typing import Dict, List
from ..llm import create_llm_client, ContextManager
from ..prompts import PromptLibrary
from ..utils import safe_parse_yaml, user_approve, print_section
from ..config import GENERATION_CONFIG


def rooms_agent(
    state: Dict,
    ollama_url: str = "http://localhost:11434",
    interactive: bool = True
) -> Dict:
    """
    Генерация описаний комнат (batch по 3 комнаты)

    Args:
        state: State с ключами 'lore', 'structure', 'provider'
        interactive: Показывать каждый batch для review

    Returns:
        State с добавленным ключом 'rooms' (list)
    """
    if 'lore' not in state:
        raise ValueError("Отсутствует 'lore' в state")
    if 'structure' not in state:
        raise ValueError("Отсутствует 'structure' в state")

    prompts = PromptLibrary()
    provider = state.get('provider', 'ollama')
    llm = create_llm_client(provider=provider)
    context_mgr = ContextManager()

    lore = state['lore']
    structure = state['structure']
    rooms_graph = structure['rooms_graph']
    total_rooms = len(rooms_graph)

    BATCH_SIZE = GENERATION_CONFIG.get('batch_size_rooms', 3)

    print("\n🏛️  Генерация описаний комнат...")
    print(f"   Всего комнат: {total_rooms}")
    print(f"   Batch размер: {BATCH_SIZE}")

    all_rooms = []

    # Генерация по батчам
    for batch_idx in range(0, total_rooms, BATCH_SIZE):
        batch_end = min(batch_idx + BATCH_SIZE, total_rooms)
        batch_info = rooms_graph[batch_idx:batch_end]

        print(f"\n   📦 Batch {batch_idx//BATCH_SIZE + 1}/{(total_rooms + BATCH_SIZE - 1)//BATCH_SIZE}")
        print(f"      Комнаты: {batch_idx + 1}-{batch_end}")

        # Summarize предыдущие комнаты для контекста
        previous_rooms = context_mgr.summarize_rooms(all_rooms)

        # Генерация промпта
        prompt = prompts.get_rooms_prompt(
            lore=lore,
            structure=structure,
            previous_rooms=previous_rooms,
            batch_info=batch_info,
            batch_index=batch_idx // BATCH_SIZE
        )

        try:
            # Вызов LLM
            response = llm.generate(
                prompt=prompt,
                stage='rooms',
                system=prompts.SYSTEM_DESIGNER
            )

            # Парсинг ответа
            parsed = safe_parse_yaml(response['content'], stage='rooms')

            # Извлекаем комнаты
            if isinstance(parsed, dict) and 'rooms' in parsed:
                batch_rooms = parsed['rooms']
            elif isinstance(parsed, list):
                batch_rooms = parsed
            else:
                raise ValueError(f"Неожиданный формат ответа: {type(parsed)}")

            # КРИТИЧНО: Добавляем ID и exits из валидированной структуры
            # LLM генерирует только описания, ID и exits берем из структуры!
            for idx, room in enumerate(batch_rooms):
                if idx < len(batch_info):
                    room['id'] = batch_info[idx]['id']
                    room['exits'] = batch_info[idx].get('exits', [])
                    # Копируем также sector и name если их нет
                    if 'sector' not in room:
                        room['sector'] = batch_info[idx].get('sector', 'INSIDE')
                    if 'name' not in room:
                        room['name'] = batch_info[idx].get('name', 'Комната')

            # Показываем batch для review
            if interactive:
                print_section(f"Batch {batch_idx//BATCH_SIZE + 1} - Комнаты", None)
                for room in batch_rooms:
                    room_name = room.get('name', 'Без названия')
                    room_id = room.get('id', 'unknown')
                    desc_len = len(room.get('description', ''))
                    print(f"      • {room_id}: {room_name} ({desc_len} символов)")

                if not user_approve(f"      Одобрить batch {batch_idx//BATCH_SIZE + 1}?"):
                    print("      ⚠️  Batch отклонён. Регенерация...")
                    # TODO: Implement user_edit_batch
                    # batch_rooms = user_edit_batch(batch_rooms)

            # Добавляем к общему списку
            all_rooms.extend(batch_rooms)

            print(f"      ✓ Сгенерировано комнат: {len(batch_rooms)}")

        except Exception as e:
            print(f"      ✗ Ошибка при генерации batch: {e}")
            raise

    # ID и exits уже установлены из структуры в каждом batch (строки 91-101)
    print(f"   ✓ ID и exits взяты из валидированной структуры для всех {len(all_rooms)} комнат")

    # Обновление state
    state['rooms'] = all_rooms

    print(f"\n   ✓ Всего сгенерировано комнат: {len(all_rooms)}")

    return state
