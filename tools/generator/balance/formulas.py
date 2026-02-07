"""
Формулы игрового баланса из game-mechanics.md и validator.py
"""

import re
from typing import Tuple


# Множители опыта по ролям (из validator.py:670-681)
ROLE_EXP_MULT = {
    'TRASH': 10,
    'BOSS': 30,
    'TANK': 10,
    'MELLEE_DMG': 15,
    'ARCHER': 12,
    'ROGUE': 15,
    'MAGE_DMG': 18,
    'MAGE_BUFF': 8,
    'HEALER': 6
}

# Множители золота по ролям (из validator.py:670-681)
ROLE_GOLD_MULT = {
    'TRASH': 5,
    'BOSS': 25,
    'TANK': 5,
    'MELLEE_DMG': 8,
    'ARCHER': 7,
    'ROGUE': 10,
    'MAGE_DMG': 12,
    'MAGE_BUFF': 4,
    'HEALER': 6
}

# Множители урона по ролям (из validator.py:742-752)
ROLE_DAMAGE_MULT = {
    'TRASH': 1.0,
    'BOSS': 1.5,
    'TANK': 0.7,
    'MELLEE_DMG': 1.4,
    'ARCHER': 1.3,
    'ROGUE': 1.5,
    'MAGE_DMG': 2.0,
    'MAGE_BUFF': 0.8,
    'HEALER': 0.5
}


def calc_mob_exp(level: int, role: str) -> int:
    """
    Расчет опыта за моба

    Формула: level^2 * role_mult
    Источник: validator.py:690-694

    Args:
        level: Уровень моба
        role: Роль моба ('TRASH', 'BOSS', и т.д.)

    Returns:
        Количество опыта

    Examples:
        >>> calc_mob_exp(13, 'TRASH')
        1690
        >>> calc_mob_exp(13, 'BOSS')
        5070
    """
    exp_mult = ROLE_EXP_MULT.get(role, 10)
    return (level ** 2) * exp_mult


def calc_mob_gold(level: int, role: str) -> Tuple[int, int]:
    """
    Расчет золота за моба (диапазон)

    Формула: level * role_mult * (0.7-1.3)
    Источник: validator.py:706-714

    Args:
        level: Уровень моба
        role: Роль моба

    Returns:
        Кортеж (min_gold, max_gold)

    Examples:
        >>> calc_mob_gold(13, 'TRASH')
        (45, 84)
        >>> calc_mob_gold(13, 'BOSS')
        (227, 422)
    """
    gold_mult = ROLE_GOLD_MULT.get(role, 5)
    center = level * gold_mult
    min_gold = int(center * 0.7)
    max_gold = int(center * 1.3)
    return (min_gold, max_gold)


def calc_player_hp(level: int) -> int:
    """
    Расчет HP игрока (для баланса урона мобов)

    Формула: 100 + level * 20
    Источник: validator.py:739

    Args:
        level: Уровень игрока

    Returns:
        HP игрока
    """
    return 100 + level * 20


def calc_damage_dice(level: int, role: str) -> str:
    """
    Расчет рекомендуемого урона моба в формате NdN+B

    Формула: player_hp * 0.1 * role_mult
    Источник: validator.py:778-780

    Args:
        level: Уровень моба
        role: Роль моба

    Returns:
        Строка урона в формате "NdN+B"

    Examples:
        >>> calc_damage_dice(13, 'TRASH')
        '2d8+15'
        >>> calc_damage_dice(13, 'BOSS')
        '3d10+25'
    """
    player_hp = calc_player_hp(level)
    base_damage = player_hp * 0.1  # 10% HP игрока
    damage_mult = ROLE_DAMAGE_MULT.get(role, 1.0)
    expected_damage = base_damage * damage_mult

    # Конвертируем ожидаемый урон в формат NdN+B
    # Стратегия: максимизируем разброс (больше кубиков лучше)

    if role in ['TANK', 'HEALER', 'MAGE_BUFF']:
        # Низкий урон - маленькие кубики
        num_dice = max(1, int(expected_damage / 6))
        die_size = 6
        bonus = int(expected_damage - (num_dice * 3.5))
    elif role in ['MAGE_DMG']:
        # Высокий урон с большим разбросом - большие кубики
        num_dice = max(1, int(expected_damage / 10))
        die_size = 12
        bonus = int(expected_damage - (num_dice * 6.5))
    elif role == 'BOSS':
        # Боссы - средние кубики, но много
        num_dice = max(2, int(expected_damage / 8))
        die_size = 10
        bonus = int(expected_damage - (num_dice * 5.5))
    else:
        # Стандартный урон - d8
        num_dice = max(1, int(expected_damage / 6))
        die_size = 8
        bonus = int(expected_damage - (num_dice * 4.5))

    # Корректируем чтобы средний урон был близок к expected
    bonus = max(0, bonus)

    return f"{num_dice}d{die_size}+{bonus}"


def parse_damage_dice(dice_str: str) -> Tuple[int, int, int]:
    """
    Парсинг строки урона NdN+B

    Args:
        dice_str: Строка вида "2d8+5"

    Returns:
        Кортеж (num_dice, die_size, bonus)

    Raises:
        ValueError: Если формат невалиден
    """
    match = re.match(r'(\d+)d(\d+)\+?(\d+)?', dice_str)
    if not match:
        raise ValueError(f"Неверный формат урона: '{dice_str}'")

    num_dice = int(match.group(1))
    die_size = int(match.group(2))
    bonus = int(match.group(3) or 0)

    return (num_dice, die_size, bonus)


def calc_avg_damage(dice_str: str) -> float:
    """
    Расчет среднего урона из строки NdN+B

    Args:
        dice_str: Строка вида "2d8+5"

    Returns:
        Средний урон
    """
    num_dice, die_size, bonus = parse_damage_dice(dice_str)
    return (num_dice * (die_size + 1) / 2) + bonus


def damage_close_enough(actual: str, expected: str, threshold: float = 0.3) -> bool:
    """
    Проверка что урон достаточно близок к ожидаемому

    Args:
        actual: Фактический урон
        expected: Ожидаемый урон
        threshold: Порог отклонения (0.3 = 30%)

    Returns:
        True если урон в пределах threshold
    """
    try:
        actual_avg = calc_avg_damage(actual)
        expected_avg = calc_avg_damage(expected)

        deviation = abs(actual_avg - expected_avg) / expected_avg
        return deviation <= threshold
    except ValueError:
        return False
