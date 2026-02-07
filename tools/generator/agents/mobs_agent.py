"""
Mobs Agent - генерация мобов с автоматическим балансом
"""

from typing import Dict
from ..llm import OllamaClient, ContextManager
from ..prompts import PromptLibrary
from ..utils import safe_parse_yaml, print_section
from ..balance import (
    calc_mob_exp,
    calc_mob_gold,
    calc_damage_dice,
    damage_close_enough
)
from ..tools_definitions import get_tools_for_stage, execute_tool_call


def mobs_agent(state: Dict, ollama_url: str = "http://localhost:11434") -> Dict:
    """
    Генерация мобов с автоматическим балансом

    Args:
        state: State с ключами 'lore', 'rooms', 'idea'

    Returns:
        State с добавленным ключом 'mobiles' (list)
    """
    if 'lore' not in state:
        raise ValueError("Отсутствует 'lore' в state")
    if 'rooms' not in state:
        raise ValueError("Отсутствует 'rooms' в state")
    if 'idea' not in state:
        raise ValueError("Отсутствует 'idea' в state")

    prompts = PromptLibrary()
    ollama = OllamaClient(ollama_url=ollama_url)
    context_mgr = ContextManager()

    lore = state['lore']
    rooms = state['rooms']
    idea = state['idea']

    level_range = tuple(idea.get('level_range', [10, 15]))
    estimated_mobs = idea.get('estimated_mobs', 6)

    # Summarize комнаты для контекста
    rooms_summary = context_mgr.summarize_rooms(rooms)

    # Генерация промпта
    prompt = prompts.get_mobs_prompt(lore, rooms_summary, level_range, estimated_mobs)

    print("\n👾 Генерация мобов...")
    print(f"   Уровни: {level_range[0]}-{level_range[1]}")
    print(f"   Примерно мобов: {estimated_mobs}")

    try:
        # Получаем tools для этапа mobs
        tools = get_tools_for_stage('mobs')

        # Вызов LLM с function calling
        response = ollama.generate(
            prompt=prompt,
            stage='mobs',
            system=prompts.SYSTEM_DESIGNER,
            tools=tools if tools else None
        )

        # Обработка tool calls если есть
        if response.get('tool_calls'):
            print(f"   🔧 LLM вызвал {len(response['tool_calls'])} функций для расчётов")
            for tool_call in response['tool_calls']:
                tool_name = tool_call['function']['name']
                arguments = tool_call['function']['arguments']
                result = execute_tool_call(tool_name, arguments)
                print(f"      • {tool_name}({arguments}) = {result}")

        # Парсинг ответа
        parsed = safe_parse_yaml(response['content'])

        # Извлекаем мобов
        if isinstance(parsed, dict) and 'mobiles' in parsed:
            mobiles = parsed['mobiles']
        elif isinstance(parsed, list):
            mobiles = parsed
        else:
            raise ValueError(f"Неожиданный формат ответа: {type(parsed)}")

        print(f"\n   🔧 POST-PROCESSING баланса...")

        # POST-PROCESSING: применяем формулы баланса
        for idx, mob in enumerate(mobiles):
            level = mob.get('level', level_range[0])
            role = mob.get('role', 'TRASH')
            mob_name = mob.get('name', {}).get('nominative', f'Моб {idx+1}')

            # 1. Пересчитываем EXP
            correct_exp = calc_mob_exp(level, role)
            if 'loot' not in mob:
                mob['loot'] = {}
            mob['loot']['exp'] = correct_exp

            # 2. Пересчитываем Gold
            gold_min, gold_max = calc_mob_gold(level, role)
            if 'gold' not in mob['loot']:
                mob['loot']['gold'] = {}
            mob['loot']['gold']['min'] = gold_min
            mob['loot']['gold']['max'] = gold_max

            # 3. Проверяем и корректируем урон если нужно
            if 'stats' in mob and 'damage_dice' in mob['stats']:
                current_damage = mob['stats']['damage_dice']
                expected_damage = calc_damage_dice(level, role)

                # Если урон сильно отличается, корректируем
                if not damage_close_enough(current_damage, expected_damage, threshold=0.5):
                    print(f"      ⚠️  {mob_name}: урон {current_damage} → {expected_damage}")
                    mob['stats']['damage_dice'] = expected_damage
            else:
                # Если урона нет, добавляем
                if 'stats' not in mob:
                    mob['stats'] = {}
                mob['stats']['damage_dice'] = calc_damage_dice(level, role)

            print(f"      ✓ {mob_name} (L{level} {role}): exp={correct_exp}, "
                  f"gold={gold_min}-{gold_max}, dmg={mob['stats']['damage_dice']}")

        # Обновление state
        state['mobiles'] = mobiles

        print(f"\n   ✓ Всего мобов: {len(mobiles)}")

        # Статистика по ролям
        role_counts = {}
        for mob in mobiles:
            role = mob.get('role', 'UNKNOWN')
            role_counts[role] = role_counts.get(role, 0) + 1

        print(f"   📊 Роли:")
        for role, count in sorted(role_counts.items()):
            print(f"      • {role}: {count}")

        return state

    except Exception as e:
        print(f"   ✗ Ошибка при генерации мобов: {e}")
        raise
