"""
Mobs Agent - генерация мобов с автоматическим балансом
"""

from typing import Dict
from ..llm import create_llm_client, ContextManager
from ..prompts import PromptLibrary
from ..utils import safe_parse_yaml, print_section
from ..config import GENERATION_CONFIG
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
    provider = state.get('provider', 'ollama')
    llm = create_llm_client(provider=provider)
    context_mgr = ContextManager()

    lore = state['lore']
    rooms = state['rooms']
    idea = state['idea']

    level_range = tuple(idea.get('level_range', [10, 15]))
    estimated_mobs = idea.get('estimated_mobs', 6)
    BATCH_SIZE = 5  # Генерируем по 5 мобов за раз

    # Summarize комнаты для контекста
    rooms_summary = context_mgr.summarize_rooms(rooms)

    print("\n👾 Генерация мобов...")
    print(f"   Уровни: {level_range[0]}-{level_range[1]}")
    print(f"   Всего мобов: {estimated_mobs}")
    print(f"   Batch размер: {BATCH_SIZE}")

    all_mobiles = []

    # Генерация по батчам
    for batch_idx in range(0, estimated_mobs, BATCH_SIZE):
        batch_end = min(batch_idx + BATCH_SIZE, estimated_mobs)
        batch_count = batch_end - batch_idx

        print(f"\n   📦 Batch {batch_idx//BATCH_SIZE + 1}/{(estimated_mobs + BATCH_SIZE - 1)//BATCH_SIZE}")
        print(f"      Мобов в batch: {batch_count}")

        # Генерация промпта для batch
        prompt = prompts.get_mobs_prompt(
            lore,
            rooms_summary,
            level_range,
            batch_count,  # Запрашиваем только нужное количество для batch
            already_generated=len(all_mobiles)  # Сколько уже сгенерировано
        )

        try:
            # Получаем tools для этапа mobs
            tools = get_tools_for_stage('mobs')

            # Вызов LLM с function calling (увеличенный timeout для батча мобов)
            response = llm.generate(
                prompt=prompt,
                stage='mobs',
                system=prompts.SYSTEM_DESIGNER,
                tools=tools if tools else None,
                timeout=GENERATION_CONFIG['timeout_mobs']  # 300s = 5 минут
            )

            # Обработка tool calls если есть
            if response.get('tool_calls'):
                print(f"      🔧 LLM вызвал {len(response['tool_calls'])} функций")

            # Парсинг ответа
            parsed = safe_parse_yaml(response['content'], stage='mobs')

            # Извлекаем мобов
            if isinstance(parsed, dict) and 'mobiles' in parsed:
                batch_mobiles = parsed['mobiles']
            elif isinstance(parsed, list):
                batch_mobiles = parsed
            else:
                raise ValueError(f"Неожиданный формат ответа: {type(parsed)}")

            # POST-PROCESSING: применяем формулы баланса для batch
            for idx, mob in enumerate(batch_mobiles):
                level = mob.get('level', level_range[0])
                role = mob.get('role', 'TRASH')
                mob_name = mob.get('name', {}).get('nominative', f'Моб {len(all_mobiles)+idx+1}')

                # 0. Проверяем и исправляем расу если невалидна
                VALID_RACES = ['BASIC', 'HUMAN', 'BEASTMAN', 'BIRD', 'ANIMAL',
                               'REPTILE', 'FISH', 'INSECT', 'PLANT', 'CONSTRUCT',
                               'ZOMBIE', 'GHOST', 'BOGGART', 'SPIRIT', 'MAGIC_CREATURE']

                # Маппинг невалидных рас на валидные
                RACE_MAPPING = {
                    'UNDEAD': 'ZOMBIE',      # Нежить → Зомби
                    'GIANT': 'BEASTMAN',     # Гигант → Зверочеловек
                    'DRAGON': 'REPTILE',     # Дракон → Рептилия
                    'DEMON': 'MAGIC_CREATURE', # Демон → Магическое существо
                    'ELEMENTAL': 'MAGIC_CREATURE', # Элементаль → Магическое существо
                }

                current_race = mob.get('race')
                if current_race and current_race not in VALID_RACES:
                    new_race = RACE_MAPPING.get(current_race, 'BASIC')
                    print(f"      🔧 {mob_name}: раса '{current_race}' → '{new_race}'")
                    mob['race'] = new_race
                elif not current_race:
                    # Если расы нет вообще - ставим BASIC
                    mob['race'] = 'BASIC'

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

            # Добавляем к общему списку
            all_mobiles.extend(batch_mobiles)

            print(f"      ✓ Сгенерировано мобов: {len(batch_mobiles)}")

        except Exception as e:
            print(f"      ✗ Ошибка при генерации batch: {e}")
            raise

    # ВАЖНО: Присваиваем уникальные ID всем мобам
    for idx, mob in enumerate(all_mobiles, start=1):
        mob['id'] = f"mob_{idx:03d}"  # mob_001, mob_002, etc.

    # Обновление state
    state['mobiles'] = all_mobiles

    print(f"\n   ✓ Всего сгенерировано мобов: {len(all_mobiles)}")

    # Статистика по ролям
    role_counts = {}
    for mob in all_mobiles:
        role = mob.get('role', 'UNKNOWN')
        role_counts[role] = role_counts.get(role, 0) + 1

    print(f"   📊 Роли:")
    for role, count in sorted(role_counts.items()):
        print(f"      • {role}: {count}")

    return state
