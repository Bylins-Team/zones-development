"""
Refiner Agent - исправление ошибок в сгенерированной зоне
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

import re
from ..llm import create_llm_client
from ..prompts import PromptLibrary
from ..utils import safe_parse_yaml, extract_code_block


def _extract_problematic_ids(messages: List[str], element_type: str) -> set:
    """
    Извлекает ID проблемных элементов из списка ошибок/warnings

    Args:
        messages: Список сообщений об ошибках/warnings
        element_type: 'room' или 'mob' или 'obj'

    Returns:
        Set ID проблемных элементов
    """
    ids = set()
    pattern = rf"'{element_type}_(\d+)'"

    for msg in messages:
        matches = re.findall(pattern, msg)
        for match in matches:
            ids.add(f"{element_type}_{match}")

    return ids


def _get_room_neighbors(room: dict, all_rooms_map: dict) -> set:
    """Получить ID соседних комнат"""
    neighbors = set()
    for exit_data in room.get('exits', []):
        to_room = exit_data.get('to_room')
        if to_room and to_room in all_rooms_map:
            neighbors.add(to_room)
    return neighbors


def _get_mobs_in_room(room_id: str, zone: dict) -> set:
    """Получить ID мобов, которые спавнятся в комнате"""
    mob_ids = set()
    for mob in zone.get('mobiles', []):
        # Проверяем есть ли spawn в этой комнате
        spawns = mob.get('spawns', [])
        for spawn in spawns:
            if spawn.get('room') == room_id:
                mob_ids.add(mob['id'])
                break
    return mob_ids


def _create_zone_subset_with_context(
    zone: dict,
    problematic_room_ids: set,
    problematic_mob_ids: set,
    context_window_tokens: int
) -> Tuple[dict, int]:
    """
    Создаёт subset зоны с проблемными элементами + контекст
    С дедупликацией и учётом budget

    Args:
        zone: Полные данные зоны
        problematic_room_ids: ID проблемных комнат
        problematic_mob_ids: ID проблемных мобов
        context_window_tokens: Доступный бюджет токенов

    Returns:
        (subset, использовано_токенов)
    """
    # Создаём карты для быстрого доступа
    all_rooms_map = {r['id']: r for r in zone.get('rooms', [])}
    all_mobs_map = {m['id']: m for m in zone.get('mobiles', [])}

    # Фиксированные части
    FIXED_OVERHEAD = 3000  # schema + errors + instructions
    remaining_budget = context_window_tokens - FIXED_OVERHEAD

    # Lore summary (краткий)
    lore = zone.get('lore', {})
    lore_summary = str(lore.get('theme', ''))[:500] if lore else ''
    lore_tokens = len(lore_summary) // 4
    remaining_budget -= lore_tokens

    # Tracking
    included_problematic_rooms = []
    included_context_rooms = {}  # id -> trimmed data
    included_context_mobs = {}   # id -> trimmed data
    seen_room_ids = set()
    seen_mob_ids = set()

    # Обрабатываем проблемные комнаты по одной
    for room_id in problematic_room_ids:
        if room_id not in all_rooms_map:
            continue

        room = all_rooms_map[room_id]

        # Стоимость проблемной комнаты (FULL)
        room_yaml = str(room)  # Приблизительно
        room_tokens = len(room_yaml) // 4

        # Соседи (только те, кого ещё НЕТ)
        neighbors = _get_room_neighbors(room, all_rooms_map)
        new_neighbors = neighbors - seen_room_ids - problematic_room_ids
        neighbor_tokens = len(new_neighbors) * 25  # ~100 chars per trimmed room

        # Мобы в комнате (только те, кого ещё НЕТ)
        mobs_here = _get_mobs_in_room(room_id, zone)
        new_mobs = mobs_here - seen_mob_ids - problematic_mob_ids
        mob_tokens = len(new_mobs) * 12  # ~50 chars per trimmed mob

        # Проверяем влезает ли
        total_cost = room_tokens + neighbor_tokens + mob_tokens
        if total_cost > remaining_budget:
            print(f"   ⚠️  Бюджет исчерпан, обработано {len(included_problematic_rooms)} комнат", flush=True)
            break

        # Добавляем
        included_problematic_rooms.append(room)
        seen_room_ids.add(room_id)
        remaining_budget -= total_cost

        # Добавляем новых соседей (trimmed)
        for neighbor_id in new_neighbors:
            neighbor = all_rooms_map[neighbor_id]
            included_context_rooms[neighbor_id] = {
                'id': neighbor_id,
                'name': neighbor.get('name', ''),
                'sector': neighbor.get('sector', 'INSIDE')
            }
            seen_room_ids.add(neighbor_id)

        # Добавляем новых мобов (trimmed)
        for mob_id in new_mobs:
            mob = all_mobs_map[mob_id]
            mob_name = mob.get('name', {})
            included_context_mobs[mob_id] = {
                'id': mob_id,
                'name': mob_name.get('nominative', '') if isinstance(mob_name, dict) else str(mob_name),
                'level': mob.get('level', 1),
                'role': mob.get('role', 'TRASH')
            }
            seen_mob_ids.add(mob_id)

    # Обрабатываем проблемных мобов аналогично
    included_problematic_mobs = []
    for mob_id in problematic_mob_ids:
        if mob_id not in all_mobs_map or mob_id in seen_mob_ids:
            continue

        mob = all_mobs_map[mob_id]
        mob_yaml = str(mob)
        mob_tokens = len(mob_yaml) // 4

        if mob_tokens > remaining_budget:
            break

        included_problematic_mobs.append(mob)
        seen_mob_ids.add(mob_id)
        remaining_budget -= mob_tokens

    # Собираем subset
    subset = {
        'meta': zone.get('meta', {}),
        'lore': {'theme': lore_summary} if lore_summary else {}
    }

    if included_problematic_rooms:
        subset['rooms'] = included_problematic_rooms

    if included_problematic_mobs:
        subset['mobiles'] = included_problematic_mobs

    if included_context_rooms:
        subset['context_rooms'] = list(included_context_rooms.values())

    if included_context_mobs:
        subset['context_mobs'] = list(included_context_mobs.values())

    used_tokens = context_window_tokens - remaining_budget
    return subset, used_tokens


def _merge_refinements(original_zone: dict, refined_zone: dict, room_ids: set, mob_ids: set) -> dict:
    """
    Мержит исправленные элементы обратно в оригинальную зону

    Args:
        original_zone: Оригинальные данные зоны
        refined_zone: Исправленные данные (subset)
        room_ids: ID исправленных комнат
        mob_ids: ID исправленных мобов

    Returns:
        Объединённая зона
    """
    result = original_zone.copy()

    # Обновляем meta если изменился
    if 'meta' in refined_zone:
        result['meta'] = refined_zone['meta']

    # Мержим комнаты
    if room_ids and 'rooms' in refined_zone:
        refined_rooms_map = {r['id']: r for r in refined_zone['rooms']}
        updated_rooms = []

        for room in original_zone.get('rooms', []):
            room_id = room.get('id')
            if room_id in room_ids and room_id in refined_rooms_map:
                # Используем исправленную версию
                updated_rooms.append(refined_rooms_map[room_id])
            else:
                # Оригинальная версия
                updated_rooms.append(room)

        result['rooms'] = updated_rooms

    # Мержим мобов
    if mob_ids and 'mobiles' in refined_zone:
        refined_mobs_map = {m['id']: m for m in refined_zone['mobiles']}
        updated_mobs = []

        for mob in original_zone.get('mobiles', []):
            mob_id = mob.get('id')
            if mob_id in mob_ids and mob_id in refined_mobs_map:
                # Используем исправленную версию
                updated_mobs.append(refined_mobs_map[mob_id])
            else:
                # Оригинальная версия
                updated_mobs.append(mob)

        result['mobiles'] = updated_mobs

    return result


def run_validator(zone_file: Path) -> Tuple[List[str], List[str], int]:
    """
    Запуск validator.py для зоны

    Args:
        zone_file: Путь к YAML файлу зоны

    Returns:
        (errors, warnings, score)
    """
    validator_path = Path(__file__).parent.parent.parent / "validator.py"

    if not validator_path.exists():
        print(f"⚠️  Validator не найден: {validator_path}", flush=True)
        return ([], ["Validator не найден"], 0)

    try:
        # Запускаем validator (UTF-8 для Windows)
        # Timeout 180s для LLM оценки (может быть долгой)
        result = subprocess.run(
            [sys.executable, str(validator_path), str(zone_file)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=180
        )

        output = result.stdout + result.stderr

        # DEBUG: Показываем что вернул validator
        print(f"🐛 DEBUG: Validator return code: {result.returncode}", flush=True)
        print(f"🐛 DEBUG: Validator output length: {len(output)} chars", flush=True)
        if output:
            print(f"🐛 DEBUG: First 500 chars of output:\n{output[:500]}", flush=True)
        else:
            print(f"🐛 DEBUG: Validator returned EMPTY output!", flush=True)

        # Парсим вывод validator
        errors = []
        warnings = []
        score = 0

        lines = output.split('\n')
        for line in lines:
            # Ищем score (проверяем все возможные форматы)
            if 'ОЦЕНКА:' in line or 'Общий балл:' in line or 'Score:' in line:
                try:
                    # Формат: "ОЦЕНКА: 73/100 баллов" или "Score: 73/100"
                    score_str = line.split(':')[-1].strip().split('/')[0].strip()
                    score = int(score_str)
                except:
                    pass

            # Собираем ошибки
            if '❌' in line or 'ERROR' in line or 'Ошибка:' in line:
                errors.append(line.strip())
            elif '⚠️' in line or 'WARNING' in line or 'Предупреждение:' in line:
                warnings.append(line.strip())

        return (errors, warnings, score)

    except subprocess.TimeoutExpired:
        return (["Validator timeout"], [], 0)
    except Exception as e:
        return ([f"Ошибка запуска validator: {e}"], [], 0)


def refiner_agent(
    zone_file: Path,
    provider: str = "ollama",
    model: str = None,
    model_config: dict = None,
    max_iterations: int = 3,
    target_score: int = 75,
    ollama_url: str = "http://localhost:11434"  # Backward compatibility
) -> Path:
    """
    Агент для улучшения зоны через итеративное исправление ошибок

    Args:
        zone_file: Путь к YAML файлу зоны
        provider: Провайдер LLM ('ollama', 'openrouter', etc.)
        model: Модель для всех этапов (переопределяет model_config)
        model_config: Словарь stage -> model
        max_iterations: Максимум итераций улучшения
        target_score: Целевой балл валидации
        ollama_url: URL Ollama API (для обратной совместимости)

    Returns:
        Путь к улучшенному файлу
    """
    print(f"\n{'='*60}", flush=True)
    print(f"🔧 REFINER AGENT - Исправление ошибок зоны", flush=True)
    print(f"{'='*60}\n", flush=True)

    print(f"📂 Файл: {zone_file}", flush=True)
    print(f"🌐 Провайдер: {provider}", flush=True)
    if model:
        print(f"🤖 Модель: {model}", flush=True)

    # Проверяем что файл существует
    if not zone_file.exists():
        raise FileNotFoundError(f"Файл не найден: {zone_file}")

    # Загружаем исходный YAML
    with open(zone_file, 'r', encoding='utf-8') as f:
        current_yaml = f.read()

    print(f"✓ Загружено {len(current_yaml)} символов\n", flush=True)

    # Создаём LLM клиент через фабрику
    llm = create_llm_client(
        provider=provider,
        model=model,
        model_config=model_config,
        ollama_url=ollama_url
    )
    prompts = PromptLibrary()

    # Итеративное улучшение
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'─'*60}", flush=True)
        print(f"🔄 ИТЕРАЦИЯ {iteration}/{max_iterations}", flush=True)
        print(f"{'─'*60}\n", flush=True)

        # Сохраняем текущую версию во временный файл
        temp_file = zone_file.parent / f"{zone_file.stem}_temp.yaml"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(current_yaml)

        # Запускаем validator
        print("📊 Запуск validator...", flush=True)
        errors, warnings, score = run_validator(temp_file)

        print(f"\n✓ Валидация завершена:", flush=True)
        print(f"   Балл: {score}/100", flush=True)
        print(f"   Ошибок: {len(errors)}", flush=True)
        print(f"   Предупреждений: {len(warnings)}", flush=True)

        # Удаляем временный файл
        temp_file.unlink()

        # Проверяем достигли ли цели
        if score >= target_score and len(errors) == 0:
            print(f"\n✅ Целевой балл достигнут: {score} >= {target_score}", flush=True)
            print(f"✅ Ошибок нет", flush=True)
            break

        if len(errors) == 0 and len(warnings) == 0:
            print(f"\n✅ Ошибок и предупреждений нет", flush=True)
            print(f"   Балл: {score}/100", flush=True)
            break

        # Показываем ошибки
        if errors:
            print(f"\n❌ Критичные ошибки (первые 10):", flush=True)
            for err in errors[:10]:
                print(f"   {err}", flush=True)

        if warnings:
            print(f"\n⚠️  Предупреждения (первые 5):", flush=True)
            for warn in warnings[:5]:
                print(f"   {warn}", flush=True)

        # Парсим текущую зону
        zone_data = safe_parse_yaml(current_yaml)
        if not zone_data or 'zone' not in zone_data:
            print(f"\n⚠️  Невалидная зона, пропускаем refinement", flush=True)
            break

        # Извлекаем проблемные ID из warnings/errors
        problematic_rooms = _extract_problematic_ids(warnings + errors, 'room')
        problematic_mobs = _extract_problematic_ids(warnings + errors, 'mob')

        print(f"\n📋 Проблемные элементы:", flush=True)
        print(f"   Комнат: {len(problematic_rooms)}", flush=True)
        print(f"   Мобов: {len(problematic_mobs)}", flush=True)

        # Если проблем нет - выходим
        total_problems = len(problematic_rooms) + len(problematic_mobs)
        if total_problems == 0:
            print(f"\n✅ Нет конкретных проблемных элементов", flush=True)
            break

        # Определяем context window модели (70% для безопасности)
        from ..config import PROVIDER_MODEL_CONFIGS, CONTEXT_WINDOWS

        # Получаем название модели
        if model:
            model_name = model
        elif model_config and 'refiner' in model_config:
            model_name = model_config['refiner']
        else:
            provider_config = PROVIDER_MODEL_CONFIGS.get(provider, {})
            model_name = provider_config.get('refiner', 'qwen2.5:14b')

        # Получаем context window (по умолчанию 32K)
        context_limit = CONTEXT_WINDOWS.get(model_name, 32768)
        context_budget = int(context_limit * 0.7)  # 70% безопасно

        print(f"\n📊 Context window: {context_limit} tokens (используем {context_budget} = 70%)", flush=True)

        # Создаём subset с контекстом и дедупликацией
        zone_subset, used_tokens = _create_zone_subset_with_context(
            zone_data['zone'],
            problematic_rooms,
            problematic_mobs,
            context_budget
        )

        print(f"   Использовано токенов: {used_tokens} / {context_budget}", flush=True)

        # Формируем feedback для LLM
        if score < 60:
            llm_feedback = "Качество низкое. Улучши описания, добавь детали атмосферы."
        elif score < 75:
            llm_feedback = "Качество среднее. Добавь больше сенсорных деталей и атмосферы."
        else:
            llm_feedback = "Качество хорошее. Просто исправь технические ошибки."

        # Генерируем промпт для исправления (ТОЛЬКО проблемные элементы)
        import yaml as yaml_lib
        subset_yaml = yaml_lib.dump({'zone': zone_subset}, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"\n📊 Размер промпта: {len(subset_yaml)} символов (вместо {len(current_yaml)})", flush=True)

        prompt = prompts.get_refiner_prompt(
            zone_yaml=subset_yaml,
            validation_errors=errors[:10],  # Топ-10 ошибок
            validation_warnings=warnings[:10],  # Топ-10 warnings
            llm_feedback=llm_feedback,
            iteration=iteration
        )

        # Вызываем LLM
        print(f"\n🤖 Генерация исправлений...", flush=True)
        response = llm.generate(
            prompt=prompt,
            stage='refiner',
            system=prompts.SYSTEM_DESIGNER,
            timeout=300
        )

        # Извлекаем YAML из ответа
        refined_yaml = extract_code_block(response['content'], 'yaml')

        if not refined_yaml:
            print(f"\n⚠️  LLM не вернул валидный YAML, используем оригинал", flush=True)
            break

        # Проверяем что YAML парсится
        parsed = safe_parse_yaml(refined_yaml)
        if parsed is None or 'zone' not in parsed:
            print(f"\n⚠️  Исправленный YAML невалиден, используем оригинал", flush=True)
            break

        # Мержим исправления обратно в полную зону
        print(f"🔄 Мерж исправлений в полную зону...", flush=True)
        zone_data['zone'] = _merge_refinements(
            zone_data['zone'],
            parsed['zone'],
            problematic_rooms,
            problematic_mobs
        )

        # Сериализуем обратно в YAML
        import yaml as yaml_lib
        current_yaml = yaml_lib.dump(zone_data, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)
        print(f"✓ Исправления применены", flush=True)

    # Сохраняем улучшенную версию
    output_file = zone_file.parent / f"{zone_file.stem}_refined.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(current_yaml)

    print(f"\n{'='*60}", flush=True)
    print(f"✅ Улучшенная зона сохранена: {output_file}", flush=True)
    print(f"{'='*60}\n", flush=True)

    # Финальная валидация
    print("📊 Финальная валидация...", flush=True)
    errors, warnings, score = run_validator(output_file)

    print(f"\n📈 РЕЗУЛЬТАТ:", flush=True)
    print(f"   Балл: {score}/100", flush=True)
    print(f"   Ошибок: {len(errors)}", flush=True)
    print(f"   Предупреждений: {len(warnings)}", flush=True)

    if score >= target_score:
        print(f"\n🎉 Целевой балл достигнут!", flush=True)
    else:
        print(f"\n⚠️  Целевой балл не достигнут ({score} < {target_score})", flush=True)
        print(f"   Возможно нужно ещё улучшение или ручная правка", flush=True)

    return output_file
