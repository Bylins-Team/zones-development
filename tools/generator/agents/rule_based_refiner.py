"""
Rule-based Refiner - быстрое исправление типичных проблем без LLM
"""

from pathlib import Path
import yaml
from typing import Dict, Any


def refine_zone_rules(zone_file: Path, output_file: Path = None, max_description_length: int = 600) -> Path:
    """
    Исправляет типичные проблемы в зоне программно (без LLM)

    Исправления:
    1. Добавляет entrance_rooms если отсутствуют
    2. Сокращает слишком длинные описания комнат
    3. Сохраняет остальное без изменений

    Args:
        zone_file: Путь к исходному файлу зоны
        output_file: Путь для сохранения (по умолчанию: *_refined.yaml)
        max_description_length: Макс длина описания комнаты (default: 600)

    Returns:
        Путь к исправленному файлу
    """
    print(f"\n{'='*60}")
    print(f"🔧 RULE-BASED REFINER - Быстрые исправления")
    print(f"{'='*60}\n")

    print(f"📂 Входной файл: {zone_file}")

    # Загружаем YAML
    with open(zone_file, 'r', encoding='utf-8') as f:
        zone_data = yaml.safe_load(f)

    if 'zone' not in zone_data:
        raise ValueError("Невалидный формат зоны: отсутствует корневой ключ 'zone'")

    zone = zone_data['zone']
    changes_made = []

    # ===== 1. Исправление entrance_rooms =====
    if 'meta' not in zone:
        zone['meta'] = {}

    if 'entrance_rooms' not in zone['meta'] or not zone['meta']['entrance_rooms']:
        # Берём первую комнату как точку входа
        rooms = zone.get('rooms', [])
        if rooms:
            first_room_id = rooms[0]['id']
            zone['meta']['entrance_rooms'] = [first_room_id]
            changes_made.append(f"✓ Добавлена точка входа: {first_room_id}")
            print(f"✓ Добавлена точка входа: {first_room_id}")

    # ===== 2. Сокращение длинных описаний =====
    rooms = zone.get('rooms', [])
    long_descriptions_fixed = 0

    for room in rooms:
        room_id = room.get('id', 'unknown')
        room_name = room.get('name', 'unknown')
        description = room.get('description', '')

        if len(description) > max_description_length:
            # Сокращаем до max_description_length символов, обрезая по последнему предложению
            truncated = description[:max_description_length]

            # Ищем последнюю точку
            last_period = truncated.rfind('.')
            if last_period > max_description_length * 0.7:  # Если точка не слишком далеко
                truncated = truncated[:last_period + 1]
            else:
                # Если точки нет, обрезаем по последнему пробелу
                last_space = truncated.rfind(' ')
                if last_space > 0:
                    truncated = truncated[:last_space] + '...'

            room['description'] = truncated.strip()
            long_descriptions_fixed += 1
            print(f"✓ Сокращено описание комнаты '{room_name}' ({room_id}): {len(description)} → {len(truncated)} символов")

    if long_descriptions_fixed > 0:
        changes_made.append(f"✓ Сокращено {long_descriptions_fixed} длинных описаний")

    # ===== Сохранение =====
    if output_file is None:
        output_file = zone_file.parent / f"{zone_file.stem}_refined.yaml"

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(zone_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    print(f"\n{'='*60}")
    print(f"✅ Исправленная зона сохранена: {output_file}")
    print(f"{'='*60}\n")

    print(f"📊 ИТОГО ИСПРАВЛЕНИЙ: {len(changes_made)}")
    for change in changes_made:
        print(f"   {change}")

    return output_file


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tools.generator.agents.rule_based_refiner <zone_file.yaml>")
        sys.exit(1)

    zone_file = Path(sys.argv[1])
    output = refine_zone_rules(zone_file)
    print(f"\n✅ Готово: {output}")
