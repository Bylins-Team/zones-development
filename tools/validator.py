#!/usr/bin/env python3
"""
Валидатор зон для МУД "Былины"

Проверяет корректность формата зоны и оценивает качество по метрикам.
"""

import sys
import yaml
import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict


class ValidationError:
    """Ошибка валидации"""
    def __init__(self, severity: str, category: str, message: str, location: str = ""):
        self.severity = severity  # "critical", "error", "warning", "info"
        self.category = category
        self.message = message
        self.location = location

    def __str__(self):
        loc = f" ({self.location})" if self.location else ""
        return f"[{self.severity.upper()}] {self.category}: {self.message}{loc}"


class ZoneValidator:
    """Валидатор зон"""

    def __init__(self, zone_file: Path, llm_evaluation: bool = True, ollama_url: str = "http://localhost:11434"):
        self.zone_file = zone_file
        self.zone_data = None
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []
        self.score = 0
        self.max_score = 100
        self.llm_evaluation = llm_evaluation
        self.ollama_url = ollama_url
        self.llm_score = 0
        self.llm_feedback = ""

    def load_zone(self) -> bool:
        """Загрузить файл зоны"""
        try:
            with open(self.zone_file, 'r', encoding='utf-8') as f:
                self.zone_data = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(ValidationError(
                "critical", "Syntax", f"Ошибка YAML: {e}"
            ))
            return False
        except Exception as e:
            self.errors.append(ValidationError(
                "critical", "Loading", f"Не удалось загрузить файл: {e}"
            ))
            return False

    def validate(self) -> Tuple[int, int]:
        """Валидация зоны. Возвращает (баллы, макс_баллы)"""
        if not self.load_zone():
            return 0, self.max_score

        if 'zone' not in self.zone_data:
            self.errors.append(ValidationError(
                "critical", "Structure", "Отсутствует корневая секция 'zone'"
            ))
            return 0, self.max_score

        zone = self.zone_data['zone']

        # Техническая корректность (20 баллов)
        tech_score = self._validate_technical(zone)

        # Структурная полнота (15 баллов)
        struct_score = self._validate_structure(zone)

        # Качество текста (25 баллов)
        text_score = self._validate_text(zone)

        # Игровой баланс (15 баллов)
        balance_score = self._validate_balance(zone)

        # Атмосферность - автоматическая проверка (5 баллов)
        atmosphere_score = self._validate_atmosphere(zone)

        # LLM экспертная оценка (20 баллов) - если включена
        if self.llm_evaluation:
            self.llm_score, self.llm_feedback = self._llm_evaluate_zone(zone)
            self.info.append(ValidationError(
                "info", "LLM",
                f"Экспертная оценка: {self.llm_score}/20. {self.llm_feedback}"
            ))
        else:
            self.llm_score = 0
            self.llm_feedback = "LLM-оценка отключена"

        self.score = tech_score + struct_score + text_score + balance_score + atmosphere_score + self.llm_score

        return self.score, self.max_score

    def _validate_technical(self, zone: Dict) -> int:
        """Техническая корректность (20 баллов)"""
        score = 0

        # Проверка обязательных секций
        if 'meta' not in zone:
            self.errors.append(ValidationError(
                "critical", "Technical", "Отсутствует секция 'meta'"
            ))
            return 0

        score += 5  # Базовая структура корректна

        # Проверка уникальности ID
        id_score = self._check_unique_ids(zone)
        score += id_score

        # Проверка ссылочной целостности
        ref_score = self._check_references(zone)
        score += ref_score

        # Проверка связности графа
        graph_score = self._check_graph_connectivity(zone)
        score += graph_score

        return score

    def _check_unique_ids(self, zone: Dict) -> int:
        """Проверка уникальности ID (5 баллов)"""
        all_ids = defaultdict(list)

        # Собираем все ID
        for room in zone.get('rooms', []):
            if 'id' in room:
                all_ids[room['id']].append(('room', room.get('name', 'unknown')))

        for mob in zone.get('mobiles', []):
            if 'id' in mob:
                all_ids[mob['id']].append(('mobile', mob['name']['nominative']))

        for obj in zone.get('objects', []):
            if 'id' in obj:
                all_ids[obj['id']].append(('object', obj['name']['nominative']))

        # Проверяем дубликаты
        duplicates = {id_: locs for id_, locs in all_ids.items() if len(locs) > 1}

        if duplicates:
            for id_, locations in duplicates.items():
                self.errors.append(ValidationError(
                    "critical", "Technical/UniqueID",
                    f"Дубликат ID '{id_}' найден в: {', '.join(f'{t}:{n}' for t, n in locations)}"
                ))
            return 0

        return 5

    def _check_references(self, zone: Dict) -> int:
        """Проверка ссылочной целостности (5 баллов)"""
        # Собираем все существующие ID
        room_ids = {room['id'] for room in zone.get('rooms', []) if 'id' in room}
        mobile_ids = {mob['id'] for mob in zone.get('mobiles', []) if 'id' in mob}
        object_ids = {obj['id'] for obj in zone.get('objects', []) if 'id' in obj}

        errors_found = 0

        # Проверяем ссылки из комнат
        for room in zone.get('rooms', []):
            room_id = room.get('id', 'unknown')

            # Проверяем выходы
            for exit_ in room.get('exits', []):
                to_room = exit_.get('to_room')
                if to_room and not to_room.startswith('world_') and to_room not in room_ids:
                    self.errors.append(ValidationError(
                        "error", "Technical/Reference",
                        f"Комната '{room_id}' ссылается на несуществующую комнату '{to_room}'"
                    ))
                    errors_found += 1

            # Проверяем мобов
            for mob_spawn in room.get('mobiles', []):
                mob_id = mob_spawn.get('mobile_id')
                if mob_id and mob_id not in mobile_ids:
                    self.errors.append(ValidationError(
                        "error", "Technical/Reference",
                        f"Комната '{room_id}' ссылается на несуществующего моба '{mob_id}'"
                    ))
                    errors_found += 1

            # Проверяем объекты
            for obj_spawn in room.get('objects', []):
                obj_id = obj_spawn.get('object_id')
                if obj_id and obj_id not in object_ids:
                    self.errors.append(ValidationError(
                        "error", "Technical/Reference",
                        f"Комната '{room_id}' ссылается на несуществующий объект '{obj_id}'"
                    ))
                    errors_found += 1

        # Проверяем лут мобов
        for mob in zone.get('mobiles', []):
            mob_id = mob.get('id', 'unknown')
            for loot_item in mob.get('loot', {}).get('items', []):
                obj_id = loot_item.get('object_id')
                if obj_id and obj_id not in object_ids:
                    self.errors.append(ValidationError(
                        "error", "Technical/Reference",
                        f"Моб '{mob_id}' ссылается на несуществующий объект '{obj_id}' в луте"
                    ))
                    errors_found += 1

        if errors_found > 0:
            return max(0, 5 - errors_found)

        return 5

    def _check_graph_connectivity(self, zone: Dict) -> int:
        """Проверка связности графа комнат (5 баллов)"""
        rooms = zone.get('rooms', [])
        if not rooms:
            self.errors.append(ValidationError(
                "critical", "Technical/Graph", "Нет комнат в зоне"
            ))
            return 0

        # Строим граф
        room_ids = {room['id'] for room in rooms if 'id' in room}
        graph = defaultdict(set)

        for room in rooms:
            room_id = room.get('id')
            if not room_id:
                continue

            for exit_ in room.get('exits', []):
                to_room = exit_.get('to_room')
                if to_room and to_room in room_ids:  # Игнорируем внешние ссылки
                    graph[room_id].add(to_room)

        # Ищем точки входа
        entry_points = zone.get('meta', {}).get('entry_points', [])
        if not entry_points:
            self.warnings.append(ValidationError(
                "warning", "Technical/Graph", "Не указаны точки входа в зону"
            ))
            # Берем первую комнату
            entry_points = [rooms[0]['id']] if rooms else []

        if not entry_points:
            return 0

        # BFS от точки входа
        visited = set()
        queue = list(entry_points)

        while queue:
            current = queue.pop(0)
            if current in visited or current not in room_ids:
                continue
            visited.add(current)
            queue.extend(graph[current])

        # Проверяем недостижимые комнаты
        unreachable = room_ids - visited

        if unreachable:
            for room_id in unreachable:
                self.errors.append(ValidationError(
                    "error", "Technical/Graph",
                    f"Комната '{room_id}' недостижима от точек входа"
                ))
            return max(0, 5 - len(unreachable))

        return 5

    def _validate_structure(self, zone: Dict) -> int:
        """Структурная полнота (15 баллов)"""
        score = 0

        # Валидные роли и расы
        VALID_ROLES = ['BOSS', 'TRASH', 'TANK', 'MELLEE_DMG', 'ARCHER',
                       'ROGUE', 'MAGE_DMG', 'MAGE_BUFF', 'HEALER']

        VALID_RACES = ['BASIC', 'HUMAN', 'BEASTMAN', 'BIRD', 'ANIMAL',
                       'REPTILE', 'FISH', 'INSECT', 'PLANT', 'CONSTRUCT',
                       'ZOMBIE', 'GHOST', 'BOGGART', 'SPIRIT', 'MAGIC_CREATURE']

        # Количество комнат (0-3 балла)
        room_count = len(zone.get('rooms', []))
        if room_count >= 21:
            score += 3
        elif room_count >= 10:
            score += 2
        elif room_count >= 5:
            score += 1
        else:
            self.warnings.append(ValidationError(
                "warning", "Structure", f"Мало комнат: {room_count} (рекомендуется 10+)"
            ))

        # Количество мобов (0-4 балла)
        mob_count = len(zone.get('mobiles', []))
        if mob_count >= 8:
            score += 4
        elif mob_count >= 5:
            score += 3
        elif mob_count >= 3:
            score += 2
        elif mob_count >= 1:
            score += 1
        else:
            self.errors.append(ValidationError(
                "error", "Structure", "Нет мобов в зоне"
            ))

        # Проверка ролей и рас мобов
        for mob in zone.get('mobiles', []):
            mob_id = mob.get('id', 'unknown')

            # Проверка роли
            role = mob.get('role')
            if not role:
                self.warnings.append(ValidationError(
                    "warning", "Structure", f"Моб '{mob_id}' без роли"
                ))
            elif role not in VALID_ROLES:
                self.errors.append(ValidationError(
                    "error", "Structure", f"Моб '{mob_id}': неизвестная роль '{role}'"
                ))

            # Проверка расы
            race = mob.get('race')
            if not race:
                self.warnings.append(ValidationError(
                    "warning", "Structure", f"Моб '{mob_id}' без расы"
                ))
            elif race not in VALID_RACES:
                self.errors.append(ValidationError(
                    "error", "Structure", f"Моб '{mob_id}': неизвестная раса '{race}'"
                ))

        # Количество объектов (0-3 балла)
        obj_count = len(zone.get('objects', []))
        if obj_count >= 6:
            score += 3
        elif obj_count >= 3:
            score += 2
        elif obj_count >= 1:
            score += 1
        else:
            self.warnings.append(ValidationError(
                "warning", "Structure", "Мало объектов в зоне"
            ))

        # Наличие квеста (0-2 балла)
        quests = zone.get('quests', [])
        if len(quests) >= 2:
            score += 2
        elif len(quests) == 1:
            score += 1
        else:
            self.info.append(ValidationError(
                "info", "Structure", "Нет квестов (рекомендуется добавить)"
            ))

        # Топология (0-3 балла)
        topology_score = self._check_topology(zone)
        score += topology_score

        return score

    def _check_topology(self, zone: Dict) -> int:
        """Проверка топологии зоны (0-3 балла)"""
        rooms = zone.get('rooms', [])
        if not rooms:
            return 0

        # Считаем среднее количество выходов
        total_exits = sum(len(room.get('exits', [])) for room in rooms)
        avg_exits = total_exits / len(rooms) if rooms else 0

        # Проверяем на линейность
        linear_rooms = sum(1 for room in rooms if len(room.get('exits', [])) <= 2)
        linear_ratio = linear_rooms / len(rooms) if rooms else 1.0

        if avg_exits > 2.5 and linear_ratio < 0.5:
            return 3  # Сложная сеть
        elif linear_ratio < 0.7:
            return 2  # Есть развилки
        else:
            self.warnings.append(ValidationError(
                "warning", "Structure/Topology",
                f"Зона слишком линейна ({linear_ratio*100:.0f}% комнат с ≤2 выходами)"
            ))
            return 0

    def _validate_text(self, zone: Dict) -> int:
        """Качество текста (25 баллов)"""
        score = 0

        # Длина описаний комнат (0-5 баллов)
        desc_score = self._check_description_length(zone)
        score += desc_score

        # Сенсорное разнообразие (0-7 баллов)
        sensory_score = self._check_sensory_details(zone)
        score += sensory_score

        # Единство стиля (0-5 баллов)
        style_score = self._check_style(zone)
        score += style_score

        # Орфография (0-8 баллов) - базовая проверка
        spell_score = self._check_spelling(zone)
        score += spell_score

        return score

    def _check_description_length(self, zone: Dict) -> int:
        """Проверка длины описаний (0-5 баллов)"""
        rooms = zone.get('rooms', [])
        if not rooms:
            return 0

        good_count = 0

        for room in rooms:
            desc = room.get('description', '')
            desc_len = len(desc.strip())

            if 100 <= desc_len <= 500:
                good_count += 1
            elif desc_len < 50:
                self.warnings.append(ValidationError(
                    "warning", "Text/Length",
                    f"Слишком короткое описание комнаты '{room.get('id', 'unknown')}' ({desc_len} символов)",
                    room.get('name', '')
                ))
            elif desc_len > 700:
                self.warnings.append(ValidationError(
                    "warning", "Text/Length",
                    f"Слишком длинное описание комнаты '{room.get('id', 'unknown')}' ({desc_len} символов)",
                    room.get('name', '')
                ))

        ratio = good_count / len(rooms)

        if ratio >= 0.8:
            return 5
        elif ratio >= 0.6:
            return 3
        else:
            return 1

    def _check_sensory_details(self, zone: Dict) -> int:
        """Проверка сенсорных деталей (0-7 баллов)"""
        # Словари сенсорных слов
        visual_words = ['цвет', 'свет', 'тьма', 'блеск', 'сияние', 'тень', 'мрак', 'яркий', 'тусклый',
                       'искрится', 'переливается', 'мерцает', 'прозрачн', 'белый', 'черный', 'красн',
                       'зелен', 'син', 'желт', 'золот', 'сереб']

        sound_words = ['звук', 'шум', 'тишина', 'эхо', 'шепот', 'крик', 'скрип', 'звон', 'шорох',
                      'гул', 'жужжан', 'треск', 'хруст', 'слышно', 'слышен']

        smell_words = ['запах', 'аромат', 'вонь', 'благоухан', 'пахн', 'смерд', 'душн', 'затхл']

        tactile_words = ['холодн', 'тепл', 'жарк', 'влажн', 'сух', 'гладк', 'шершав', 'липк',
                        'колюч', 'острый', 'мягк', 'тверд', 'ощущение', 'касание']

        taste_words = ['сладк', 'горьк', 'кисл', 'солен', 'вкус', 'привкус']

        # Собираем весь текст
        all_text = ""
        for room in zone.get('rooms', []):
            all_text += " " + room.get('description', '')
            all_text += " " + room.get('examine', '')

        all_text = all_text.lower()

        # Подсчитываем типы чувств
        senses_found = set()

        if any(word in all_text for word in visual_words):
            senses_found.add('visual')
        if any(word in all_text for word in sound_words):
            senses_found.add('sound')
        if any(word in all_text for word in smell_words):
            senses_found.add('smell')
        if any(word in all_text for word in tactile_words):
            senses_found.add('tactile')
        if any(word in all_text for word in taste_words):
            senses_found.add('taste')

        score = min(7, int(len(senses_found) * 1.5))

        if len(senses_found) < 3:
            self.warnings.append(ValidationError(
                "warning", "Text/Sensory",
                f"Недостаточно сенсорного разнообразия (найдено {len(senses_found)} типов из 5)"
            ))

        return score

    def _check_style(self, zone: Dict) -> int:
        """Проверка единства стиля (0-5 баллов)"""
        import re

        # Анахронизмы и современные слова
        anachronisms = ['окей', 'супер', 'класс', 'круто', 'прикольно', 'реально', 'конкретн',
                       'компьютер', 'телефон', 'интернет', r'\bкул\b']  # \b для границ слова

        # Собираем весь текст
        all_text = ""
        for room in zone.get('rooms', []):
            all_text += " " + room.get('description', '')
            all_text += " " + room.get('examine', '')

        for mob in zone.get('mobiles', []):
            all_text += " " + mob.get('long_description', '')
            all_text += " " + mob.get('examine', '')

        all_text = all_text.lower()

        # Подсчитываем нарушения
        violations = 0
        for word in anachronisms:
            # Используем regex для поиска целых слов
            pattern = r'\b' + re.escape(word).replace(r'\\b', '') + r'\b'
            if re.search(pattern, all_text, re.IGNORECASE):
                self.warnings.append(ValidationError(
                    "warning", "Text/Style",
                    f"Найден анахронизм/современное слово: '{word}'"
                ))
                violations += 1

        if violations == 0:
            return 5
        elif violations <= 2:
            return 3
        elif violations <= 5:
            return 1
        else:
            return 0

    def _check_spelling(self, zone: Dict) -> int:
        """Базовая проверка орфографии (0-8 баллов)"""
        # Простая эвристическая проверка
        # В реальности здесь нужен spell checker (aspell/hunspell)

        common_typos = {
            'сталоктит': 'сталактит',
            'сталогмит': 'сталагмит',
            'втечении': 'в течении',
            'вследствие': 'в следствие',
        }

        all_text = ""
        for room in zone.get('rooms', []):
            all_text += " " + room.get('description', '')

        typo_count = 0
        for typo, correct in common_typos.items():
            if typo in all_text.lower():
                self.errors.append(ValidationError(
                    "error", "Text/Spelling",
                    f"Найдена ошибка: '{typo}' → '{correct}'"
                ))
                typo_count += 1

        # Простая проверка: слишком длинные слова (>30 символов) - вероятно опечатки
        words = re.findall(r'\b\w+\b', all_text)
        long_words = [w for w in words if len(w) > 30]

        if long_words:
            self.warnings.append(ValidationError(
                "warning", "Text/Spelling",
                f"Подозрительно длинные слова (возможно склеенные): {', '.join(long_words[:3])}"
            ))
            typo_count += len(long_words)

        if typo_count == 0:
            return 8
        elif typo_count <= 3:
            return 6
        elif typo_count <= 7:
            return 4
        elif typo_count <= 15:
            return 2
        else:
            return 0

    def _validate_balance(self, zone: Dict) -> int:
        """Игровой баланс (15 баллов)"""
        score = 0

        meta = zone.get('meta', {})
        level_min = meta.get('level_min', 1)
        level_rec = meta.get('level_recommended', 1)
        level_max = meta.get('level_max', 100)

        # Проверка уровней мобов (0-5 баллов)
        mob_level_score = self._check_mob_levels(zone, level_rec)
        score += mob_level_score

        # Проверка наград (0-5 баллов)
        reward_score = self._check_rewards(zone, level_rec)
        score += reward_score

        # Проверка урона (0-5 баллов)
        damage_score = self._check_damage(zone, level_rec)
        score += damage_score

        return score

    def _check_mob_levels(self, zone: Dict, recommended_level: int) -> int:
        """Проверка соответствия уровней мобов (0-5 баллов)"""
        mobiles = zone.get('mobiles', [])
        if not mobiles:
            return 5  # Нет мобов - не снижаем баллы

        deviations = []
        for mob in mobiles:
            mob_level = mob.get('level', 1)
            deviation = abs(mob_level - recommended_level)
            deviations.append(deviation)

            if deviation > 4:
                self.warnings.append(ValidationError(
                    "warning", "Balance/Level",
                    f"Моб '{mob.get('id', 'unknown')}' уровня {mob_level} "
                    f"слишком отличается от рекомендуемого {recommended_level}",
                    mob['name']['nominative']
                ))

        avg_deviation = sum(deviations) / len(deviations) if deviations else 0

        if avg_deviation <= 2:
            return 5
        elif avg_deviation <= 4:
            return 3
        else:
            return 1

    def _check_rewards(self, zone: Dict, recommended_level: int) -> int:
        """Проверка баланса наград (0-5 баллов)"""
        mobiles = zone.get('mobiles', [])
        if not mobiles:
            return 5

        # Множители по ролям
        ROLE_EXP_MULT = {
            'TRASH': 10,
            'BOSS': 30,
            'TANK': 10,
            'MELLEE_DMG': 15,
            'ARCHER': 13,
            'ROGUE': 14,
            'MAGE_DMG': 16,
            'MAGE_BUFF': 12,
            'HEALER': 11
        }

        ROLE_GOLD_MULT = {
            'TRASH': 5,
            'BOSS': 25,
            'TANK': 5,
            'MELLEE_DMG': 8,
            'ARCHER': 7,
            'ROGUE': 10,
            'MAGE_DMG': 8,
            'MAGE_BUFF': 6,
            'HEALER': 6
        }

        issues = 0

        for mob in mobiles:
            mob_level = mob.get('level', 1)
            mob_role = mob.get('role', 'TRASH')
            loot = mob.get('loot', {})

            # Проверка опыта: level^2 * role_mult
            exp = loot.get('exp', 0)
            exp_mult = ROLE_EXP_MULT.get(mob_role, 10)
            expected_exp = (mob_level ** 2) * exp_mult

            deviation = abs(exp - expected_exp) / expected_exp if expected_exp > 0 else 0

            if deviation > 0.3:  # Отклонение >30%
                self.warnings.append(ValidationError(
                    "warning", "Balance/Rewards",
                    f"Моб '{mob.get('id', 'unknown')}' ({mob_role}): опыт {exp} отличается "
                    f"от ожидаемого ~{int(expected_exp)}",
                    mob['name']['nominative']
                ))
                issues += 1

            # Проверка золота: level * role_mult * (0.7-1.3)
            gold_min = loot.get('gold', {}).get('min', 0)
            gold_max = loot.get('gold', {}).get('max', 0)
            avg_gold = (gold_min + gold_max) / 2

            gold_mult = ROLE_GOLD_MULT.get(mob_role, 5)
            expected_gold_center = mob_level * gold_mult
            expected_gold_min = expected_gold_center * 0.7
            expected_gold_max = expected_gold_center * 1.3

            # Проверяем, попадает ли средний золот в диапазон
            if not (expected_gold_min <= avg_gold <= expected_gold_max):
                self.warnings.append(ValidationError(
                    "warning", "Balance/Rewards",
                    f"Моб '{mob.get('id', 'unknown')}' ({mob_role}): золото {gold_min}-{gold_max} "
                    f"вне диапазона {int(expected_gold_min)}-{int(expected_gold_max)}",
                    mob['name']['nominative']
                ))
                issues += 1

        if issues == 0:
            return 5
        elif issues <= 2:
            return 3
        else:
            return 1

    def _check_damage(self, zone: Dict, recommended_level: int) -> int:
        """Проверка урона мобов (0-5 баллов)"""
        mobiles = zone.get('mobiles', [])
        if not mobiles:
            return 5

        player_hp = 100 + recommended_level * 20  # Примерная формула HP игрока

        # Множители урона по ролям
        ROLE_DAMAGE_MULT = {
            'TRASH': 1.0,
            'BOSS': 1.5,
            'TANK': 0.7,           # Танк наносит меньше урона
            'MELLEE_DMG': 1.4,
            'ARCHER': 1.3,
            'ROGUE': 1.5,
            'MAGE_DMG': 2.0,
            'MAGE_BUFF': 0.8,
            'HEALER': 0.5
        }

        issues = 0

        for mob in mobiles:
            mob_role = mob.get('role', 'TRASH')
            damage_dice = mob.get('stats', {}).get('damage_dice', '1d1')

            # Парсим кость урона (например "2d8+5")
            match = re.match(r'(\d+)d(\d+)\+?(\d+)?', damage_dice)
            if not match:
                self.warnings.append(ValidationError(
                    "warning", "Balance/Damage",
                    f"Моб '{mob.get('id', 'unknown')}': неверный формат урона '{damage_dice}'",
                    mob['name']['nominative']
                ))
                issues += 1
                continue

            num_dice = int(match.group(1))
            die_size = int(match.group(2))
            bonus = int(match.group(3) or 0)

            avg_damage = (num_dice * (die_size + 1) / 2) + bonus

            # Определяем ожидаемый урон с учетом роли
            base_damage = player_hp * 0.1  # 10% HP игрока
            damage_mult = ROLE_DAMAGE_MULT.get(mob_role, 1.0)
            expected_damage = base_damage * damage_mult

            deviation = abs(avg_damage - expected_damage) / expected_damage if expected_damage > 0 else 0

            # Для TANK, HEALER, MAGE_BUFF - допускаем больший разброс
            threshold = 1.0 if mob_role in ['TANK', 'HEALER', 'MAGE_BUFF'] else 0.8

            if deviation > threshold:  # Отклонение >threshold
                if avg_damage > expected_damage:
                    severity = "warning"
                    msg = "завышен"
                else:
                    severity = "info"
                    msg = "занижен"

                # Только для критичных ролей (не TANK/HEALER)
                if mob_role not in ['TANK', 'HEALER', 'MAGE_BUFF']:
                    self.warnings.append(ValidationError(
                        severity, "Balance/Damage",
                        f"Моб '{mob.get('id', 'unknown')}' ({mob_role}): урон {avg_damage:.1f} {msg} "
                        f"относительно ожидаемого ~{expected_damage:.1f}",
                        mob['name']['nominative']
                    ))
                    issues += 1

        if issues == 0:
            return 5
        elif issues <= 2:
            return 3
        else:
            return 1

    def _call_ollama(self, prompt: str, model: str = "qwen2.5:14b") -> Optional[str]:
        """Вызов Ollama API для получения оценки от LLM"""
        try:
            url = f"{self.ollama_url}/api/generate"
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')

        except urllib.error.URLError as e:
            self.warnings.append(ValidationError(
                "warning", "LLM",
                f"Не удалось подключиться к Ollama: {e}"
            ))
            return None
        except Exception as e:
            self.warnings.append(ValidationError(
                "warning", "LLM",
                f"Ошибка при вызове LLM: {e}"
            ))
            return None

    def _llm_evaluate_zone(self, zone: Dict) -> Tuple[int, str]:
        """Экспертная оценка зоны с помощью LLM (0-20 баллов)"""
        if not self.llm_evaluation:
            return 0, "LLM-оценка отключена"

        # Собираем контекст зоны для оценки
        meta = zone.get('meta', {})
        rooms = zone.get('rooms', [])

        # Берем несколько примеров описаний
        sample_descriptions = []
        for i, room in enumerate(rooms[:5]):  # Первые 5 комнат
            desc = room.get('description', '').strip()
            if desc:
                sample_descriptions.append(f"Комната {i+1}: {desc[:300]}...")

        folklore = meta.get('folklore_basis', '').strip()
        theme = meta.get('theme', '').strip()

        prompt = f"""Ты - эксперт по дизайну игровых зон для текстовых ролевых игр (MUD).
Оцени качество зоны по следующим критериям:

ФОЛЬКЛОРНАЯ ОСНОВА:
{folklore if folklore else 'Не указана'}

ТЕМА ЗОНЫ:
{theme if theme else 'Не указана'}

ПРИМЕРЫ ОПИСАНИЙ КОМНАТ:
{chr(10).join(sample_descriptions) if sample_descriptions else 'Нет описаний'}

ОЦЕНИ ПО КРИТЕРИЯМ:
1. Атмосферность и погружение (0-10 баллов) - насколько описания создают яркую атмосферу
2. Уникальность и оригинальность (0-10 баллов) - насколько зона отличается от типичных
3. Соответствие фольклору (0-10 баллов) - насколько хорошо зона передает славянский фольклор

Формат ответа:
ДЕТАЛИЗАЦИЯ:
- Атмосферность: X/10 - [почему именно эта оценка]
- Уникальность: X/10 - [почему именно эта оценка]
- Фольклор: X/10 - [почему именно эта оценка]
ИТОГО: X/30"""

        response = self._call_ollama(prompt)

        if not response:
            return 0, "Не удалось получить оценку от LLM"

        # Парсим ответ
        try:
            # Ищем оценку ИТОГО: X/30
            score_match = re.search(r'ИТОГО:\s*(\d+)', response)

            if score_match:
                raw_score = int(score_match.group(1))
                # Нормализуем из 30 в 20
                score = min(20, int((raw_score / 30.0) * 20))
            else:
                # Пытаемся найти число в начале ответа
                first_num = re.search(r'(\d+)', response)
                score = min(20, int(first_num.group(1))) if first_num else 10

            # Собираем полное обоснование с детализацией
            reason = response.strip()

            return score, reason

        except Exception as e:
            self.warnings.append(ValidationError(
                "warning", "LLM",
                f"Не удалось распарсить ответ LLM: {e}"
            ))
            return 0, f"Ошибка парсинга: {response[:100]}"

    def _validate_atmosphere(self, zone: Dict) -> int:
        """Атмосферность - базовая автоматическая проверка (5 баллов)"""
        score = 0

        # 1. Проверка наличия фольклорной основы (0-2 балла)
        meta = zone.get('meta', {})
        folklore = meta.get('folklore_basis', '').strip()
        if len(folklore) > 100:
            score += 2
        elif len(folklore) > 0:
            score += 1
        else:
            self.info.append(ValidationError(
                "info", "Atmosphere",
                "Рекомендуется добавить описание фольклорной основы"
            ))

        # 2. Проверка наличия атмосферных сообщений (0-3 балла)
        rooms = zone.get('rooms', [])
        rooms_with_atmosphere = sum(1 for room in rooms if room.get('atmosphere'))

        if rooms and rooms_with_atmosphere / len(rooms) > 0.7:
            score += 3
        elif rooms and rooms_with_atmosphere / len(rooms) > 0.4:
            score += 2
        elif rooms_with_atmosphere > 0:
            score += 1

        return min(5, score)  # Максимум 5 баллов

    def print_report(self):
        """Вывод отчета валидации"""
        print("=" * 70)
        print(f"ОТЧЕТ ВАЛИДАЦИИ ЗОНЫ: {self.zone_file.name}")
        print("=" * 70)
        print()

        # Критические ошибки
        critical_errors = [e for e in self.errors if e.severity == "critical"]
        if critical_errors:
            print("КРИТИЧЕСКИЕ ОШИБКИ:")
            for error in critical_errors:
                print(f"  ✗ {error}")
            print()

        # Обычные ошибки
        normal_errors = [e for e in self.errors if e.severity == "error"]
        if normal_errors:
            print("ОШИБКИ:")
            for error in normal_errors:
                print(f"  ✗ {error}")
            print()

        # Предупреждения
        if self.warnings:
            print("ПРЕДУПРЕЖДЕНИЯ:")
            for warning in self.warnings:
                print(f"  ! {warning}")
            print()

        # Информационные сообщения
        if self.info:
            print("РЕКОМЕНДАЦИИ:")
            for info in self.info:
                print(f"  ℹ {info}")
            print()

        # LLM оценка (если есть)
        if self.llm_evaluation and self.llm_feedback:
            print("=" * 70)
            print("ЭКСПЕРТНАЯ ОЦЕНКА (LLM):")
            print(f"  Баллы: {self.llm_score}/20")
            print(f"  Обоснование: {self.llm_feedback}")
            print()

        # Оценка
        print("=" * 70)
        print(f"ОЦЕНКА: {self.score}/{self.max_score} баллов")

        percentage = (self.score / self.max_score * 100) if self.max_score > 0 else 0

        if percentage >= 90:
            status = "ОТЛИЧНО - готово к интеграции"
            emoji = "✓✓✓"
        elif percentage >= 75:
            status = "ХОРОШО - нужны минорные правки"
            emoji = "✓✓"
        elif percentage >= 60:
            status = "УДОВЛЕТВОРИТЕЛЬНО - требуется доработка"
            emoji = "✓"
        elif percentage >= 45:
            status = "ПЛОХО - существенная переработка"
            emoji = "✗"
        else:
            status = "ОЧЕНЬ ПЛОХО - рекомендуется начать заново"
            emoji = "✗✗✗"

        print(f"{emoji} {status} ({percentage:.1f}%)")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Валидатор зон для МУД "Былины"')
    parser.add_argument('zone_file', type=str, help='Путь к файлу зоны (YAML)')
    parser.add_argument('--no-llm', action='store_true', help='Отключить LLM-оценку')
    parser.add_argument('--ollama-url', type=str, default='http://localhost:11434',
                       help='URL Ollama API (по умолчанию: http://localhost:11434)')

    args = parser.parse_args()
    zone_file = Path(args.zone_file)

    if not zone_file.exists():
        print(f"Ошибка: файл '{zone_file}' не найден")
        sys.exit(1)

    validator = ZoneValidator(
        zone_file,
        llm_evaluation=not args.no_llm,
        ollama_url=args.ollama_url
    )
    validator.validate()
    validator.print_report()

    # Возвращаем код выхода на основе критических ошибок
    critical_errors = [e for e in validator.errors if e.severity == "critical"]
    sys.exit(1 if critical_errors else 0)


if __name__ == '__main__':
    main()
