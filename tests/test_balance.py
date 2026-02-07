"""
Тесты для формул баланса
"""

import sys
from pathlib import Path

# Добавляем путь к tools
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from generator.balance import (
    calc_mob_exp,
    calc_mob_gold,
    calc_damage_dice,
    calc_player_hp,
    parse_damage_dice,
    calc_avg_damage,
    damage_close_enough
)


def test_mob_exp():
    """Тест расчета опыта моба"""
    # TRASH: level^2 * 10
    assert calc_mob_exp(13, 'TRASH') == 1690  # 169 * 10
    assert calc_mob_exp(10, 'TRASH') == 1000  # 100 * 10

    # BOSS: level^2 * 30
    assert calc_mob_exp(13, 'BOSS') == 5070  # 169 * 30
    assert calc_mob_exp(10, 'BOSS') == 3000  # 100 * 30

    # MELLEE_DMG: level^2 * 15
    assert calc_mob_exp(13, 'MELLEE_DMG') == 2535  # 169 * 15

    print("✓ test_mob_exp passed")


def test_mob_gold():
    """Тест расчета золота моба"""
    # TRASH: level * 5 * (0.7-1.3)
    min_g, max_g = calc_mob_gold(13, 'TRASH')
    assert min_g == 45  # 13*5*0.7 = 45.5 -> 45
    assert max_g == 84  # 13*5*1.3 = 84.5 -> 84

    # BOSS: level * 25 * (0.7-1.3)
    min_g, max_g = calc_mob_gold(13, 'BOSS')
    assert min_g == 227  # 13*25*0.7
    assert max_g == 422  # 13*25*1.3

    print("✓ test_mob_gold passed")


def test_player_hp():
    """Тест расчета HP игрока"""
    assert calc_player_hp(10) == 300  # 100 + 10*20
    assert calc_player_hp(13) == 360  # 100 + 13*20
    assert calc_player_hp(1) == 120   # 100 + 1*20

    print("✓ test_player_hp passed")


def test_damage_dice():
    """Тест генерации урона"""
    # TRASH level 13
    dice = calc_damage_dice(13, 'TRASH')
    assert 'd' in dice
    assert '+' in dice

    # Проверяем что средний урон близок к ожидаемому
    # player_hp(13) = 360, base = 36, TRASH mult = 1.0, expected = 36
    avg = calc_avg_damage(dice)
    assert 30 <= avg <= 42, f"Средний урон {avg} вне диапазона 30-42"

    # BOSS должен наносить больше урона
    boss_dice = calc_damage_dice(13, 'BOSS')
    boss_avg = calc_avg_damage(boss_dice)
    assert boss_avg > avg, "BOSS должен наносить больше урона чем TRASH"

    print("✓ test_damage_dice passed")


def test_parse_damage_dice():
    """Тест парсинга строки урона"""
    num, size, bonus = parse_damage_dice("2d8+5")
    assert num == 2
    assert size == 8
    assert bonus == 5

    num, size, bonus = parse_damage_dice("3d6")
    assert num == 3
    assert size == 6
    assert bonus == 0

    num, size, bonus = parse_damage_dice("1d12+10")
    assert num == 1
    assert size == 12
    assert bonus == 10

    print("✓ test_parse_damage_dice passed")


def test_avg_damage():
    """Тест расчета среднего урона"""
    # 2d8+5: avg = 2*(8+1)/2 + 5 = 9 + 5 = 14
    assert calc_avg_damage("2d8+5") == 14.0

    # 1d6+0: avg = 1*(6+1)/2 + 0 = 3.5
    assert calc_avg_damage("1d6") == 3.5

    print("✓ test_avg_damage passed")


def test_damage_close_enough():
    """Тест сравнения урона"""
    # Одинаковый урон
    assert damage_close_enough("2d8+5", "2d8+5")

    # Близкий урон (avg: 14 vs 13)
    assert damage_close_enough("2d8+5", "2d8+4", threshold=0.3)

    # Слишком разный урон
    assert not damage_close_enough("2d8+5", "1d6+2", threshold=0.3)

    print("✓ test_damage_close_enough passed")


def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "="*50)
    print("BALANCE FORMULAS TESTS")
    print("="*50 + "\n")

    test_mob_exp()
    test_mob_gold()
    test_player_hp()
    test_damage_dice()
    test_parse_damage_dice()
    test_avg_damage()
    test_damage_close_enough()

    print("\n" + "="*50)
    print("✅ Все тесты пройдены!")
    print("="*50 + "\n")


if __name__ == '__main__':
    run_all_tests()
