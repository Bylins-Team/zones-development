"""
Централизованная библиотека промптов для генерации зон
"""

import json
from typing import Dict, Tuple, List, Any


class PromptLibrary:
    """Библиотека промптов для всех этапов генерации"""

    # Системный промпт для всех этапов
    SYSTEM_DESIGNER = """Ты - эксперт по дизайну зон для славянского MUD "Былины".

Твои знания:
- Славянский фольклор (былины, сказки, поверья)
- Игровой баланс и механики MUD
- YAML форматы зон
- Атмосферное описание локаций

Стиль написания:
- Атмосферные описания с сенсорными деталями (звуки, запахи, текстуры)
- Историчность и фольклорная достоверность
- Без анахронизмов и современных терминов
- Использование архаичной лексики где уместно
- Короткие, ёмкие предложения для геймплея

Игровой мир "Былины":
- Действие в Древней Руси времён былинных богатырей
- Присутствуют персонажи из былин и сказок
- Славянская мифология (домовые, лешие, русалки, нежить)
- Реалистичная средневековая атмосфера с элементами магии
- Система уровней 1-50, рекомендуемые зоны для групп 3-5 игроков"""

    @staticmethod
    def get_idea_prompt(
        user_theme: str = None,
        level_range: Tuple[int, int] = None,
        requested_rooms: int = None
    ) -> str:
        """
        Промпт для генерации идеи зоны

        Args:
            user_theme: Тема от пользователя (опционально)
            level_range: Диапазон уровней (опционально)
            requested_rooms: Желаемое количество комнат (опционально)

        Returns:
            Промпт для LLM
        """
        theme_text = f"\n\nТема от пользователя: {user_theme}" if user_theme else ""
        level_text = (
            f"\n\nЦелевые уровни: {level_range[0]}-{level_range[1]}"
            if level_range else "\n\nЦелевые уровни: определи сам (1-50)"
        )
        rooms_text = (
            f"\n\n⚠️ ВАЖНО: estimated_rooms должно быть РОВНО {requested_rooms} (пользователь явно указал)"
            if requested_rooms else ""
        )

        return f"""Создай концепцию новой зоны для МУД "Былины".{theme_text}{level_text}{rooms_text}

Зона должна:
1. Основываться на славянском фольклоре (былины, сказки, поверья)
2. Иметь уникальную атмосферу и историю
3. Подходить для указанных уровней
4. Содержать интересные механики и челленджи

Выдай JSON:
```json
{{
  "id": "zone_identifier",
  "name": "Название зоны",
  "author": "Zone Generator",
  "description": "Краткое описание (2-3 предложения)",
  "folklore_basis": "На каком фольклоре основана",
  "level_range": [min, max],
  "recommended_level": number,
  "difficulty": 1.0,
  "wealth": 1.0,
  "tags": ["underground", "undead", "slavic_folklore", ...],
  "estimated_rooms": number,
  "estimated_mobs": number,
  "main_theme": "Основная тема/механика зоны",
  "unique_features": ["Уникальная особенность 1", "Особенность 2", ...]
}}
```

Примеры тем:
- Заброшенные соляные копи с духами рудокопов
- Логово лесного нечистого
- Древний курган с ожившими воинами
- Затонувший град Китеж
- Избушка бабы Яги на границе миров"""

    @staticmethod
    def get_lore_prompt(idea: Dict) -> str:
        """
        Промпт для генерации лора зоны

        Args:
            idea: Концепция зоны

        Returns:
            Промпт для LLM
        """
        return f"""На основе концепции зоны создай детальный лор (фольклорную основу).

КОНЦЕПЦИЯ:
{idea}

Создай лор который включает:
1. История места (как появилось, что там было раньше)
2. Фольклорная основа (какие поверья, былины, сказки связаны)
3. Текущее состояние (что там сейчас происходит)
4. Конфликт/драма (почему игрокам туда идти)
5. Ключевые персонажи (главные NPC и их роли)
6. Атмосфера (звуки, запахи, визуальные образы)

Выдай JSON:
```json
{{
  "history": "Детальная история места (3-5 предложений)",
  "folklore_basis": "Фольклорная основа (какие поверья, из каких источников)",
  "current_state": "Что сейчас там происходит",
  "conflict": "Основной конфликт/драма",
  "key_characters": [
    {{"name": "Имя", "role": "Роль в истории", "description": "Краткое описание"}}
  ],
  "atmosphere": {{
    "sounds": ["Звук 1", "Звук 2"],
    "smells": ["Запах 1", "Запах 2"],
    "visuals": ["Визуальный образ 1", "Образ 2"],
    "feeling": "Общее ощущение места"
  }},
  "secrets": ["Секрет 1 (для квестов)", "Секрет 2"]
}}
```

Помни о славянском фольклоре и атмосфере Древней Руси!"""

    @staticmethod
    def get_structure_prompt(idea: Dict, lore: Dict) -> str:
        """
        Промпт для генерации структуры зоны (топология комнат)

        Args:
            idea: Концепция зоны
            lore: Лор зоны

        Returns:
            Промпт для LLM
        """
        return f"""Создай ИНТЕРЕСНУЮ структуру зоны (топологию комнат).

КОНЦЕПЦИЯ:
{idea}

ЛОР:
{lore}

🗺️ ТРЕБОВАНИЯ К ТОПОЛОГИИ:
1. **ОБЯЗАТЕЛЬНО РОВНО {idea.get('estimated_rooms', 12)} КОМНАТ** в rooms_graph массиве!
2. **НЕ ДЕЛАЙ ПЛОСКОЙ!** Используй вертикальность (up/down)
3. Добавь ЦИКЛЫ в графе (можно вернуться разными путями)
4. Секретные комнаты (не на прямом пути)
5. Shortcut'ы (обходные пути после открытия дверей/квестов)

📐 ПАТТЕРНЫ ТОПОЛОГИИ (используй комбинацию):

**Hub-and-Spoke** (центральная комната + ответвления):
```
    [A]
     |
[B]--[HUB]--[C]
     |
    [D]
```

**Vertical Dungeon** (многоуровневое подземелье):
```
[Entrance]
    |down
[Level 1] --east-- [Secret]
    |down
[Level 2]
    |down
[Boss Chamber]
```

**Maze-like** (лабиринт с циклами):
```
[A]--[B]--[C]
 |    |    |
[D]--[E]--[F]
 |         |
[G]-------[H]
```

**Linear with Branches** (основной путь + боковые ответвления):
```
    [Secret1]
       |
[Start]--[A]--[B]--[C]--[Boss]
              |
          [Secret2]
```

**Circular** (кольцевая структура):
```
[A]--[B]
 |    |
[D]--[C]
```

⚠️ ИЗБЕГАЙ:
- ❌ Только линейные цепочки (скучно!)
- ❌ Все комнаты на одном уровне (используй up/down!)
- ❌ Нет циклов (игрок должен иметь выбор пути)
- ❌ Нет секретов

✅ ИСПОЛЬЗУЙ:
- ✅ Вертикальность (башни, подземелья, колодцы)
- ✅ Циклы (разные пути к одной цели)
- ✅ Секретные комнаты (hidden exits, за квестами)
- ✅ Shortcut'ы (сокращенный путь назад после прохождения)
- ✅ Развилки (выбор пути влияет на сложность)

Выдай JSON:
```json
{{
  "total_rooms": number,
  "entry_point": "room_001",
  "topology_type": "mixed",  // Используй "mixed" для интересных зон!
  "sections": [
    {{
      "name": "Entrance Level",
      "rooms": ["room_001", "room_002"],
      "theme": "Темный вход, предчувствие опасности"
    }},
    {{
      "name": "Underground Maze",
      "rooms": ["room_003", "room_004", "room_005"],
      "theme": "Запутанные коридоры, циклы"
    }},
    {{
      "name": "Boss Chamber",
      "rooms": ["room_006"],
      "theme": "Финальная битва"
    }}
  ],
  "rooms_graph": [
    {{
      "id": "room_001",
      "name": "Темный вход",
      "sector": "INSIDE",
      "exits": [
        {{"direction": "north", "to_room": "room_002"}},
        {{"direction": "down", "to_room": "room_003"}},  // Вертикальность!
        {{"direction": "south", "to_room": "world_forest_01"}}  // Выход в мир
      ],
      "notes": "Точка входа, должна давать выбор пути"
    }},
    {{
      "id": "room_002",
      "name": "Башня стража",
      "sector": "INSIDE",
      "exits": [
        {{"direction": "south", "to_room": "room_001"}},
        {{"direction": "up", "to_room": "room_007"}},  // Вверх на башню!
        {{"direction": "east", "to_room": "room_004", "flags": ["HIDDEN"]}}  // Секрет!
      ],
      "notes": "Опциональная ветка, ведет к секрету"
    }},
    {{
      "id": "room_003",
      "name": "Подземный коридор",
      "sector": "UNDERGROUND",
      "exits": [
        {{"direction": "up", "to_room": "room_001"}},
        {{"direction": "north", "to_room": "room_004"}},
        {{"direction": "east", "to_room": "room_005"}}  // Развилка!
      ],
      "notes": "Развилка: север к боссу, восток к сокровищам"
    }},
    {{
      "id": "room_004",
      "name": "Зал с ловушками",
      "sector": "UNDERGROUND",
      "exits": [
        {{"direction": "south", "to_room": "room_003"}},
        {{"direction": "north", "to_room": "room_006"}},  // К боссу
        {{"direction": "west", "to_room": "room_002", "flags": ["HIDDEN"]}}  // Обратный shortcut
      ],
      "notes": "Основной путь к боссу, опасный"
    }},
    {{
      "id": "room_005",
      "name": "Сокровищница",
      "sector": "UNDERGROUND",
      "exits": [
        {{"direction": "west", "to_room": "room_003"}},
        {{"direction": "north", "to_room": "room_006"}}  // Альтернативный путь к боссу!
      ],
      "notes": "Опциональная ветка, лут, но тоже ведет к боссу"
    }},
    {{
      "id": "room_006",
      "name": "Логово босса",
      "sector": "UNDERGROUND",
      "exits": [
        {{"direction": "south", "to_room": "room_004"}},  // Основной вход
        {{"direction": "west", "to_room": "room_005"}},   // Альтернативный вход
        {{"direction": "up", "to_room": "room_001", "flags": ["CLOSED", "QUEST_UNLOCK"]}}  // Shortcut после победы!
      ],
      "notes": "BOSS ROOM! 2 входа + shortcut наверх после победы"
    }},
    {{
      "id": "room_007",
      "name": "Вершина башни (секрет)",
      "sector": "INSIDE",
      "exits": [
        {{"direction": "down", "to_room": "room_002"}}
      ],
      "notes": "Секретная комната с уникальным лутом"
    }}
  ]
}}
```

☝️ ОБРАТИ ВНИМАНИЕ в примере:
- ✅ Вертикальность: up/down между уровнями
- ✅ Циклы: room_003 ←→ room_004 ←→ room_006 ←→ room_005 ←→ room_003
- ✅ Секреты: room_007 (скрытый exit), room_002 (HIDDEN exit)
- ✅ Shortcut: room_006 → room_001 (после победы над боссом)
- ✅ Развилки: room_003 дает выбор пути
- ✅ Множественные входы к боссу: через room_004 ИЛИ room_005

⚠️ КРИТИЧНО:
Массив rooms_graph ДОЛЖЕН содержать РОВНО {idea.get('estimated_rooms', 12)} элементов!
Каждый элемент - это одна комната с id, name, sector, exits.
НЕ ОСТАНАВЛИВАЙСЯ раньше времени - генерируй ВСЕ комнаты!
Секторы (sector):
- INSIDE: внутри помещения
- UNDERGROUND: подземелье
- FOREST: лес
- FIELD: поле
- CITY: город
- MOUNTAIN: горы
- WATER_SWIM: вода (можно плавать)
- ROAD: дорога

Направления (direction): north, south, east, west, up, down"""

    @staticmethod
    def get_rooms_prompt(
        lore: Dict,
        structure: Dict,
        previous_rooms: str,
        batch_info: List[Dict],
        batch_index: int
    ) -> str:
        """
        Промпт для генерации batch комнат

        Args:
            lore: Лор зоны
            structure: Структура зоны
            previous_rooms: Summary предыдущих комнат (JSON)
            batch_info: Информация о текущем batch (из rooms_graph)
            batch_index: Номер batch (для отслеживания)

        Returns:
            Промпт для LLM
        """
        return f"""Создай детальные описания для batch комнат #{batch_index + 1}.

ЛОР ЗОНЫ:
{lore}

ПРЕДЫДУЩИЕ КОМНАТЫ (summary):
{previous_rooms}

КОМНАТЫ ДЛЯ ГЕНЕРАЦИИ (топология из структуры):
```json
{json.dumps(batch_info, ensure_ascii=False, indent=2)}
```

⚠️ ВАЖНО:
- Exits показаны для справки (можешь упомянуть направления в описаниях)
- НЕ включай "id" и "exits" в ответ - они будут добавлены автоматически!
- Генерируй ТОЛЬКО: name, description, examine, flags, sector, vnum

Для КАЖДОЙ комнаты создай:
1. description: Детальное описание (100-500 символов)
   - Визуальные детали (что видно)
   - Звуки (что слышно)
   - Запахи (что чувствуется)
   - Текстуры (как ощущается)
   - Атмосфера

2. examine: Дополнительное описание при examine (50-300 символов)
   - Скрытые детали
   - История места
   - Интересные элементы

3. flags: Флаги комнаты
   - INDOORS: в помещении
   - DARKED: темно (нужен свет)
   - PEACEFUL: мирная зона (нет боя)
   - NO_MAGIC: нет магии
   - TUNNEL: узкий туннель (только 1 персонаж)

Выдай YAML (БЕЗ id и exits - они добавятся автоматически!):
```yaml
rooms:
  - vnum: 20001  # Инкрементируй для каждой комнаты
    name: "Короткое название"

    description: |
      Детальное описание с сенсорными деталями.
      Атмосферное, без анахронизмов.

    examine: |
      Дополнительное описание при examine.

    sector: "INSIDE"

    flags:
      - "INDOORS"
      - "DARKED"
```

ВАЖНО:
- Описания на русском, атмосферные
- Без анахронизмов (никакого электричества, огнестрела, современных терминов)
- Сенсорные детали (звуки, запахи, текстуры)
- Короткие предложения для удобства чтения
- Соответствие лору зоны"""

    @staticmethod
    def get_mobs_prompt(
        lore: Dict,
        rooms_summary: str,
        level_range: Tuple[int, int],
        estimated_mobs: int,
        already_generated: int = 0
    ) -> str:
        """
        Промпт для генерации мобов

        Args:
            lore: Лор зоны
            rooms_summary: Summary комнат
            level_range: Диапазон уровней зоны
            estimated_mobs: Количество мобов для этого batch
            already_generated: Сколько мобов уже сгенерировано

        Returns:
            Промпт для LLM
        """
        batch_info = f" (batch: уже {already_generated}, генерируем ещё {estimated_mobs})" if already_generated > 0 else ""
        return f"""Создай {estimated_mobs} мобов (NPC) для зоны{batch_info}.

🔧 ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
У тебя есть функции для точных расчётов баланса:
- calc_mob_exp(level, role) - рассчитать EXP моба
- calc_mob_gold(level, role) - рассчитать gold моба
- calc_damage_dice(level, role) - рассчитать урон моба
- calc_player_hp(level) - средний HP игрока

ИСПОЛЬЗУЙ эти функции вместо того чтобы считать вручную!

ЛОР ЗОНЫ:
{lore}

КОМНАТЫ (summary):
{rooms_summary}

ПАРАМЕТРЫ:
- Уровни зоны: {level_range[0]}-{level_range[1]}
- Количество мобов: {estimated_mobs} (±2)

Создай разнообразных мобов:
1. TRASH (60-70%): обычные враги, слабые
2. BOSS (10-15%): сильные боссы (1-2 на зону)
3. Специальные роли (20-30%): TANK, MELLEE_DMG, ARCHER, MAGE_DMG, HEALER

Для КАЖДОГО моба:
1. Имя (в падежах: nominative, genitive, dative, accusative, instrumental, prepositional)
2. Уровень (в пределах level_range)
3. Роль (TRASH, BOSS, TANK, MELLEE_DMG, ARCHER, ROGUE, MAGE_DMG, MAGE_BUFF, HEALER)
4. Раса (ТОЛЬКО валидные): BASIC, HUMAN, BEASTMAN, BIRD, ANIMAL, REPTILE, FISH, INSECT, PLANT, CONSTRUCT, ZOMBIE, GHOST, BOGGART, SPIRIT, MAGIC_CREATURE
5. Описания (description, examine, action)
6. Характеристики (stats) - НЕ заполняй exp и gold, они рассчитаются автоматически!

⚠️ ВАЖНО: Используй ТОЛЬКО расы из списка выше! UNDEAD, GIANT, DRAGON, DEMON - НЕ валидны!

Выдай YAML:
```yaml
mobiles:
  - id: "mob_001"
    vnum: 20101

    name:
      nominative: "Соляной призрак"
      genitive: "Соляного призрака"
      dative: "Соляному призраку"
      accusative: "Соляного призрака"
      instrumental: "Соляным призраком"
      prepositional: "Соляном призраке"

    level: 13
    role: "TRASH"
    race: "GHOST"  # Полупрозрачный дух - используем GHOST вместо UNDEAD

    description: |
      Полупрозрачная фигура в изодранной рубахе рудокопа.

    examine: |
      Через его тело видны кристаллы соли за спиной.

    action: |
      Соляной призрак стонет и тянет руки к живым.

    stats:
      hp: 260          # HP = 100 + level * 20 (примерно)
      damage_dice: "2d8+15"  # ИСПОЛЬЗУЙ функцию calc_damage_dice(level, role)!
      armor_class: 30   # AC = базовый - уровень (меньше = лучше броня)
      hitroll: 10       # Hitroll ≈ level / 2
      # exp и gold НЕ указывай - используй calc_mob_exp() и calc_mob_gold()!

    abilities:
      - "bash"        # Умения: bash, kick, rescue, disarm, etc

    flags:
      - "AGGRESSIVE"  # Агрессивен
      - "SENTINEL"    # Не покидает комнату

    resistances:
      fire: -25       # Уязвим к огню
      cold: 50        # Устойчив к холоду

    loot:
      items:
        - item_id: "obj_001"
          chance: 30  # 30% шанс
      # exp и gold НЕ указывай здесь!

    spawn:
      rooms: ["room_002", "room_003"]
      max_count: 3    # Максимум в зоне
```

ФОРМУЛЫ (справка, НЕ используй в YAML):
- HP: 100 + level * 20 (примерно, варьируй ±20%)
- AC: 100 - level * 2 (меньше = лучше броня)
- Hitroll: level / 2 (±2)
- Damroll: level / 3 (±2)
- EXP: level² * role_mult (TRASH=10, BOSS=30) - РАССЧИТАЕТСЯ АВТОМАТИЧЕСКИ
- Gold: level * role_mult * (0.7-1.3), TRASH=5, BOSS=25 - РАССЧИТАЕТСЯ АВТОМАТИЧЕСКИ

Роли:
- TRASH: обычный враг (exp_mult=10, gold_mult=5)
- BOSS: босс (exp_mult=30, gold_mult=25)
- TANK: танк (exp_mult=10, gold_mult=5, урон ниже)
- MELLEE_DMG: ближний боец (exp_mult=15, gold_mult=8)
- ARCHER: лучник (exp_mult=12, gold_mult=7)
- ROGUE: разбойник (exp_mult=15, gold_mult=10)
- MAGE_DMG: маг урона (exp_mult=18, gold_mult=12)
- MAGE_BUFF: маг поддержки (exp_mult=8, gold_mult=4)
- HEALER: целитель (exp_mult=6, gold_mult=6)"""

    @staticmethod
    def get_objects_prompt(
        lore: Dict,
        mobs_summary: str,
        level_range: Tuple[int, int]
    ) -> str:
        """
        Промпт для генерации объектов (лута)

        Args:
            lore: Лор зоны
            mobs_summary: Summary мобов
            level_range: Диапазон уровней

        Returns:
            Промпт для LLM
        """
        return f"""Создай объекты (предметы, лут) для зоны.

ЛОР ЗОНЫ:
{lore}

МОБЫ (summary):
{mobs_summary}

УРОВНИ ЗОНЫ: {level_range[0]}-{level_range[1]}

Создай предметы:
1. Обычный лут (60%): расходники, слабые предметы
2. Хороший лут (30%): полезная экипировка
3. Уникальные предметы (10%): бонусы, квестовые предметы

Типы объектов:
- WEAPON: оружие
- ARMOR: броня
- POTION: зелья
- SCROLL: свитки
- KEY: ключи
- TREASURE: сокровища
- FOOD: еда
- LIGHT: источники света

Выдай YAML:
```yaml
objects:
  - id: "obj_001"
    vnum: 20201
    type: "TREASURE"

    name:
      nominative: "Соляной кристалл"
      genitive: "Соляного кристалла"
      # ... все падежи

    description: |
      Прозрачный кристалл соли с замороженной внутри тенью.

    examine: |
      Внутри кристалла видна застывшая человеческая фигура.

    value: 50        # Стоимость в золоте
    weight: 1        # Вес в фунтах

    material: "CRYSTAL"  # Материал: STEEL, WOOD, LEATHER, CRYSTAL, etc

    # Для экипировки
    wear_slots: ["HOLD"]  # Слоты: HEAD, BODY, LEGS, HANDS, WEAPON, SHIELD, etc

    affects:         # Бонусы (для экипировки)
      strength: 1    # +1 к силе
      armor: -5      # -5 к AC (улучшает защиту)

    flags:
      - "MAGIC"      # Магический
      - "GLOW"       # Светится
```

ВАЖНО:
- Предметы должны соответствовать лору зоны
- Уникальные названия и описания
- Баланс: не давай слишком мощные бонусы для уровня"""

    @staticmethod
    def get_quests_prompt(
        lore: Dict,
        rooms_summary: str,
        mobs_summary: str,
        objects_summary: str
    ) -> str:
        """
        Промпт для генерации квестов

        Args:
            lore: Лор зоны
            rooms_summary: Summary комнат
            mobs_summary: Summary мобов
            objects_summary: Summary объектов

        Returns:
            Промпт для LLM
        """
        return f"""Создай квесты для зоны.

ЛОР ЗОНЫ:
{lore}

КОМНАТЫ: {rooms_summary}
МОБЫ: {mobs_summary}
ОБЪЕКТЫ: {objects_summary}

Создай 1-3 квеста:
1. Основной квест: исследование зоны, убийство босса
2. Побочный квест (опционально): сбор предметов, спасение NPC
3. Скрытый квест (опционально): секретная локация, редкий лут

Выдай YAML:
```yaml
quests:
  - id: "quest_001"
    name: "Название квеста"
    type: "KILL|COLLECT|ESCORT|EXPLORE"

    description: |
      Описание квеста (что нужно сделать)

    objectives:
      - type: "KILL"
        target: "mob_boss"
        count: 1

      - type: "COLLECT"
        item: "obj_key"
        count: 1

    rewards:
      exp: 5000
      gold: 200
      items: ["obj_reward"]

    giver_npc: "npc_questgiver"  # Кто даёт квест
    completion_npc: "npc_questgiver"  # Кому сдавать
```

Типы квестов:
- KILL: убить мобов
- COLLECT: собрать предметы
- ESCORT: провести NPC
- EXPLORE: исследовать комнаты
- DELIVER: доставить предмет"""

    @staticmethod
    def get_refiner_prompt(
        zone_yaml: str,
        validation_errors: List[str],
        validation_warnings: List[str],
        llm_feedback: str,
        iteration: int
    ) -> str:
        """
        Промпт для рефайнмента (исправления ошибок)

        Args:
            zone_yaml: Текущий YAML зоны
            validation_errors: Список ошибок валидации
            validation_warnings: Список предупреждений
            llm_feedback: Feedback от LLM оценки
            iteration: Номер итерации

        Returns:
            Промпт для LLM
        """
        errors_text = chr(10).join(f"- {e}" for e in validation_errors[:10]) if validation_errors else "Нет критичных ошибок"
        warnings_text = chr(10).join(f"- {w}" for w in validation_warnings[:5]) if validation_warnings else "Нет предупреждений"

        return f"""ИСПРАВЬ ОШИБКИ В ЗОНЕ (итерация {iteration}/3).

⚠️ КРИТИЧЕСКИ ВАЖНО: СОХРАНЯЙ СТРУКТУРУ YAML!
Твой ответ ДОЛЖЕН начинаться с корневого ключа 'zone:' и содержать ВСЕ секции!

ОБЯЗАТЕЛЬНАЯ СТРУКТУРА:
```yaml
zone:
  meta:
    id: "zone_id"
    name: "Название"
    # ... остальные мета-поля
  lore:
    # ... лор зоны
  rooms:
    - id: "room_001"
      # ... данные комнаты
  mobiles:
    - id: "mob_001"
      # ... данные моба
  objects:
    - id: "obj_001"
      # ... данные объекта
  quests:
    - id: "quest_001"
      # ... данные квеста
```

ТЕКУЩАЯ ЗОНА:
```yaml
{zone_yaml}
```

КРИТИЧНЫЕ ОШИБКИ (обязательны к исправлению):
{errors_text}

ПРЕДУПРЕЖДЕНИЯ (исправь где возможно):
{warnings_text}

LLM FEEDBACK:
{llm_feedback}

ЗАДАЧА:
1. ✅ ОБЯЗАТЕЛЬНО: Сохрани структуру 'zone: {{ meta, lore, rooms, mobiles, objects, quests }}'
2. ✅ Исправь ВСЕ критичные ошибки из списка выше
3. ✅ Исправь предупреждения где возможно (особенно длинные описания)
4. ✅ Улучши качество описаний если указано в feedback
5. ✅ Сохрани атмосферу и лор

❌ НЕ ДЕЛАЙ:
- НЕ меняй общую структуру YAML (корень должен быть 'zone:')
- НЕ удаляй секции (meta, lore, rooms, mobiles, objects, quests)
- НЕ переписывай всё заново — только исправляй ошибки
- НЕ меняй ID элементов без крайней необходимости

ПРАВИЛА БАЛАНСА:
- EXP моба: level² * role_mult (TRASH=10, BOSS=30, TANK=10, MELLEE_DMG=20, ARCHER=15, ROGUE=25, MAGE_DMG=18, MAGE_BUFF=16, HEALER=14)
- Gold моба: level * role_mult * (0.7-1.3) где TRASH=5, BOSS=25, TANK=5, MELLEE_DMG=10, ARCHER=8, ROGUE=15, MAGE_DMG=12, MAGE_BUFF=9, HEALER=8
- Урон: формат NdN+B (например: 2d6+10, 3d8+15)

Выдай ПОЛНЫЙ ИСПРАВЛЕННЫЙ YAML зоны, начиная с 'zone:' и включая ВСЕ секции!"""
