"""
Structure Agent - генерация топологии зоны (граф комнат)
"""

from typing import Dict, Set, List
from collections import deque
from ..llm import create_llm_client
from ..prompts import PromptLibrary
from ..utils import safe_parse_json
from ..config import GENERATION_CONFIG


def validate_graph_connectivity(rooms_graph: List[Dict], entry_point: str) -> tuple[Set[str], Set[str]]:
    """
    Проверяет связность графа комнат методом BFS

    Args:
        rooms_graph: Список комнат с exits
        entry_point: ID точки входа

    Returns:
        (reachable_rooms, unreachable_rooms) - множества ID комнат
    """
    # Строим граф смежности (двунаправленный)
    adjacency = {}
    all_rooms = set()

    for room in rooms_graph:
        room_id = room.get('id')
        if not room_id:
            continue

        all_rooms.add(room_id)
        if room_id not in adjacency:
            adjacency[room_id] = set()

        # Добавляем связи из exits (в обе стороны - граф неориентированный)
        for exit_info in room.get('exits', []):
            to_room = exit_info.get('to_room')
            if to_room:
                adjacency[room_id].add(to_room)
                if to_room not in adjacency:
                    adjacency[to_room] = set()
                adjacency[to_room].add(room_id)  # Обратная связь

    # BFS от entry_point
    reachable = set()
    queue = deque([entry_point])
    reachable.add(entry_point)

    while queue:
        current = queue.popleft()
        for neighbor in adjacency.get(current, []):
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    unreachable = all_rooms - reachable

    return reachable, unreachable


def fix_unreachable_rooms(rooms_graph: List[Dict], entry_point: str, unreachable: Set[str]) -> List[Dict]:
    """
    Автоматически добавляет связи для недостижимых комнат

    Стратегия: для каждой недостижимой комнаты добавляем exit к случайной достижимой комнате
    (и обратную связь)

    Args:
        rooms_graph: Список комнат
        entry_point: ID точки входа
        unreachable: Множество ID недостижимых комнат

    Returns:
        Исправленный rooms_graph
    """
    import random

    # Находим достижимые комнаты (кроме entry_point, чтобы не перегружать его)
    reachable, _ = validate_graph_connectivity(rooms_graph, entry_point)
    reachable_list = [r for r in reachable if r != entry_point]

    if not reachable_list:
        # Если кроме entry_point нет достижимых - связываем с entry_point
        reachable_list = [entry_point]

    # Для каждой недостижимой комнаты добавляем связь
    room_dict = {room['id']: room for room in rooms_graph}

    for unreach_id in unreachable:
        # Выбираем случайную достижимую комнату для связи
        target_room_id = random.choice(reachable_list)

        # Добавляем exit из недостижимой к достижимой
        if unreach_id in room_dict:
            if 'exits' not in room_dict[unreach_id]:
                room_dict[unreach_id]['exits'] = []

            # Определяем направление (случайное из основных)
            directions = ['north', 'south', 'east', 'west']
            direction = random.choice(directions)

            room_dict[unreach_id]['exits'].append({
                'direction': direction,
                'to_room': target_room_id
            })

            print(f"   🔧 Автофикс: добавлена связь {unreach_id} --{direction}--> {target_room_id}")

        # Добавляем обратный exit из достижимой к недостижимой
        if target_room_id in room_dict:
            if 'exits' not in room_dict[target_room_id]:
                room_dict[target_room_id]['exits'] = []

            # Обратное направление
            reverse_dir = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
            reverse_direction = reverse_dir.get(direction, 'north')

            room_dict[target_room_id]['exits'].append({
                'direction': reverse_direction,
                'to_room': unreach_id
            })

    return list(room_dict.values())


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
    provider = state.get('provider', 'ollama')
    model = state.get('model')
    model_config = state.get('model_config')
    llm = create_llm_client(provider=provider, model=model, model_config=model_config)

    idea = state['idea']
    lore = state['lore']

    # Генерация промпта
    prompt = prompts.get_structure_prompt(idea, lore)

    print("\n🗺️  Генерация структуры зоны...")
    print(f"   Зона: {idea['name']}")

    try:
        # Вызов LLM с увеличенным timeout (сложный промпт)
        timeout = GENERATION_CONFIG.get('timeout_structure', 300)
        response = llm.generate(
            prompt=prompt,
            stage='structure',
            system=prompts.SYSTEM_DESIGNER,
            timeout=timeout
        )

        # Проверка ответа
        if not response or 'content' not in response:
            raise ValueError(f"LLM вернул некорректный ответ: {response}")

        content = response['content']
        if not content or not content.strip():
            raise ValueError("LLM вернул пустой content")

        # Парсинг ответа
        structure = safe_parse_json(content)

        # Валидация
        if 'rooms_graph' not in structure:
            raise ValueError("Отсутствует 'rooms_graph' в структуре")

        # Проверка соответствия total_rooms и len(rooms_graph)
        actual_rooms = len(structure['rooms_graph'])
        declared_rooms = structure.get('total_rooms', actual_rooms)

        if actual_rooms != declared_rooms:
            print(f"   ⚠️  Несоответствие: total_rooms={declared_rooms}, но сгенерировано {actual_rooms} комнат")
            print(f"   → Исправляем total_rooms на фактическое количество")
            structure['total_rooms'] = actual_rooms
        elif 'total_rooms' not in structure:
            structure['total_rooms'] = actual_rooms

        # ВАЛИДАЦИЯ СВЯЗНОСТИ ГРАФА
        entry_point = structure.get('entry_point', 'room_001')
        print(f"   🔍 Проверка связности графа (entry: {entry_point})...")

        reachable, unreachable = validate_graph_connectivity(structure['rooms_graph'], entry_point)

        if unreachable:
            print(f"   ⚠️  Обнаружено {len(unreachable)} недостижимых комнат: {sorted(unreachable)}")
            print(f"   🔧 Автоматическое исправление графа...")

            # Автоматически добавляем связи для недостижимых комнат
            structure['rooms_graph'] = fix_unreachable_rooms(
                structure['rooms_graph'],
                entry_point,
                unreachable
            )

            # Проверяем что исправление сработало
            reachable_after, unreachable_after = validate_graph_connectivity(
                structure['rooms_graph'],
                entry_point
            )

            if unreachable_after:
                print(f"   ⚠️  Всё ещё есть {len(unreachable_after)} недостижимых комнат!")
            else:
                print(f"   ✓ Граф исправлен: все комнаты достижимы")
        else:
            print(f"   ✓ Граф связный: все {len(reachable)} комнат достижимы")

        # Обновление state
        state['structure'] = structure

        print(f"   ✓ Комнат: {structure['total_rooms']}")
        print(f"   ✓ Топология: {structure.get('topology_type', 'mixed')}")
        print(f"   ✓ Секций: {len(structure.get('sections', []))}")

        return state

    except Exception as e:
        print(f"   ✗ Ошибка при генерации структуры: {e}")
        raise
