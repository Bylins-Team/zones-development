# Формат файлов зон v2.0

> **Версия:** 2.0
> **Дата:** 2026-02-06
> **Основано на:** Реальной кодовой базе движка "Былины"
> **Справочник:** См. `game-mechanics.md` для всех констант

---

## Изменения от v1.0

- Добавлены **роли мобов** (BOSS, TRASH, TANK, etc)
- Добавлены **расы мобов** из движка
- Обновлены **формулы баланса** (HP, exp, gold)
- Добавлены все **флаги** из движка (мобы, объекты, комнаты)
- Добавлены **типы атак** и **типы урона**
- Добавлены **сопротивления** (диапазон -100 до +75)
- Добавлены **материалы** объектов
- Обновлены **секторы** комнат

---

## Структура YAML файла зоны

```yaml
zone:
  meta:          # Метаинформация
  rooms:         # Комнаты
  mobiles:       # Мобы (NPC)
  objects:       # Объекты (предметы)
  triggers:      # Триггеры (опционально)
  quests:        # Квесты (опционально)
```

---

## Секция META

```yaml
meta:
  id: "zone_001"
  name: "Название зоны"
  author: "Автор"
  version: "2.0"
  created: "2026-02-06"

  description: |
    Описание зоны

  folklore_basis: |
    Фольклорная основа

  # Уровни (1-50)
  level_min: 10
  level_recommended: 13
  level_max: 15

  # Параметры зоны
  difficulty: 1.0          # Множитель сложности (0.5-2.0)
  wealth: 1.0              # Множитель богатства (0.5-2.0)

  # Теги
  tags:
    - underground
    - undead
    - slavic_folklore

  # Точки входа
  entry_points:
    - "room_001"
```

---

## Секция ROOMS

```yaml
rooms:
  - id: "room_001"
    vnum: 10001              # Виртуальный номер
    name: "Короткое название"

    description: |
      Детальное описание комнаты (100-500 символов рекомендуется).

    examine: |
      Дополнительное описание при examine.

    # Сектор (тип местности) - см. game-mechanics.md раздел 8.2
    sector: "INSIDE"         # INSIDE, CITY, FIELD, FOREST, HILLS, MOUNTAIN
                             # WATER_SWIM, WATER_NOSWIM, UNDERWATER, FLYING
                             # ROAD, THICK_ICE, NORMAL_ICE, THIN_ICE, SECRET

    # Флаги комнаты - см. game-mechanics.md раздел 8.1
    flags:
      - "DARKED"             # Темно (нужен свет)
      - "INDOORS"            # В помещении
      - "NO_MAGIC"           # Нет магии (опционально)
      # Другие: DEATH_TRAP, PEACEFUL, SOUNDPROOF, NO_TRACK
      #         TUNNEL, NO_TELEPORT_IN, NO_RECALL, NO_SUMMON
      #         GODS_ROOM, ARENA, SLOW_REGEN, FAST_REGEN, ICE

    # Выходы
    exits:
      - direction: "north"   # north, east, south, west, up, down
        to_room: "room_002"
        description: "Описание выхода"

        # Дверь (опционально)
        door:
          name: "Дверь"
          flags:             # HAS_DOOR, CLOSED, LOCKED, PICKPROOF, HIDDEN, BROKEN_LOCK
            - "HAS_DOOR"
            - "CLOSED"
          key_vnum: 10201    # ID ключа (опционально)
          difficulty: 10     # Сложность взлома (опционально)

    # Спавн мобов
    mobiles:
      - mobile_id: "mob_001"
        max_count: 2         # Максимум одновременно
        respawn_time: 300    # Секунды

    # Спавн объектов
    objects:
      - object_id: "obj_001"
        max_count: 1
        respawn_time: 600

    # Атмосферные сообщения
    atmosphere:
      - message: "Текст сообщения."
        chance: 20           # Процент
```

---

## Секция MOBILES

```yaml
mobiles:
  - id: "mob_001"
    vnum: 10101
    keywords: ["голем", "соляной", "golem"]

    # Имена (6 падежей русского языка)
    name:
      nominative: "соляной голем"      # Кто? Что?
      genitive: "соляного голема"      # Кого? Чего?
      dative: "соляному голему"        # Кому? Чему?
      accusative: "соляного голема"    # Кого? Что?
      instrumental: "соляным големом"  # Кем? Чем?
      prepositional: "соляном големе"  # О ком? О чем?

    short_description: "соляной голем стоит здесь"

    long_description: |
      Детальное описание, которое видят игроки.

    examine: |
      Описание при examine.

    # Уровень (1-50)
    level: 13

    # Роль моба - см. game-mechanics.md раздел 4.1
    role: "TRASH"            # BOSS, TRASH, TANK, MELLEE_DMG, ARCHER,
                             # ROGUE, MAGE_DMG, MAGE_BUFF, HEALER

    # Раса - см. game-mechanics.md раздел 4.2
    race: "CONSTRUCT"        # BASIC(100), HUMAN(101), BEASTMAN(102),
                             # BIRD(103), ANIMAL(104), REPTILE(105),
                             # FISH(106), INSECT(107), PLANT(108),
                             # CONSTRUCT(109), ZOMBIE(110), GHOST(111),
                             # BOGGART(112), SPIRIT(113), MAGIC_CREATURE(114)

    # Характеристики
    stats:
      # HP - см. game-mechanics.md раздел 2.3
      hp: 800                # Для lvl 13 trash: 500-1000

      # 6 базовых характеристик (10-100 для мобов)
      strength: 18           # Сила
      dexterity: 8           # Ловкость
      constitution: 20       # Телосложение
      intelligence: 6        # Интеллект
      wisdom: 6              # Мудрость
      charisma: 3            # Обаяние

      # Защита
      armor: 30              # Класс брони (ниже = лучше)

      # Атака - см. game-mechanics.md раздел 5
      damage_dice: "2d8+5"   # Урон (NdN+B)
      hit_bonus: 3           # Бонус к попаданию
      attacks_per_round: 1   # Атак за раунд

    # Поведение - см. game-mechanics.md раздел 3.1
    behavior:
      # Базовые флаги
      aggressive: true       # Атакует игроков
      sentinel: false        # Не двигается
      scavenger: false       # Подбирает предметы
      aware: false           # Нельзя backstab
      memory: true           # Помнит атакующих
      helper: true           # Помогает союзникам
      wimpy: false           # Убегает при ранении
      stay_zone: true        # Не покидает зону

      # Агрессия по времени
      aggressive_day: false
      aggressive_night: false

      # Иммунитеты
      no_charm: false        # Нельзя очаровать
      no_summon: false       # Нельзя призвать
      no_sleep: false        # Нельзя усыпить
      no_bash: false         # Нельзя bash
      no_blind: false        # Нельзя ослепить

      aggro_range: 0         # 0 = только в своей комнате

      # Тип атаки - см. game-mechanics.md раздел 5.1
      attack_type: "type_hit"  # type_hit, type_slash, type_bite, type_claw
                               # type_pierce, type_bludgeon, и т.д.

      # Специальные атаки - см. game-mechanics.md раздел 5.2
      special_attacks:
        - type: "bash"         # Сбить с ног
          chance: 15           # Процент
          cooldown: 3          # Раундов откат

        - type: "stun"         # Оглушение
          chance: 10
          cooldown: 5
          duration: 2          # Раундов действие

      # Дыхание (для драконов) - см. game-mechanics.md раздел 3.2
      breath:
        type: null             # FIRE, GAS, FROST, ACID, LIGHTING
        damage_mult: 0.5       # x0.5 урона для дыханий

    # Сопротивления - см. game-mechanics.md раздел 6.2
    # Диапазон: -100 (уязвимость) до +75 (сопротивление, макс для PC)
    resistances:
      physical: 20             # Физический урон
      fire: -20                # Огонь (уязвим)
      air: 0                   # Воздух
      water: 0                 # Вода
      earth: 0                 # Земля
      cold: 30                 # Холод
      poison: 100              # Яд (иммунитет)
      vitality: 0              # Жизненная сила
      mind: 0                  # Разум
      immunity: 0              # Иммунитет
      dark: 0                  # Тьма

    # Лут - см. game-mechanics.md раздел 10
    loot:
      # Опыт: level^2 * 10 для trash
      exp: 1690                # Для lvl 13: 13^2 * 10 = 1690

      # Золото: level * 5 (±30%) для trash
      gold:
        min: 45                # 13 * 5 * 0.7 = 45
        max: 85                # 13 * 5 * 1.3 = 85

      # Предметы
      items:
        - object_id: "obj_002"
          chance: 30           # Процент выпадения

        - object_id: "obj_003"
          chance: 15

    # Реплики
    speech:
      on_spawn: "Голем материализуется."
      on_aggro: "Голем издает скрежещущий звук!"
      on_death: "Голем рассыпается на осколки."
      on_hit_player: "Удар голема!"

      # Случайные реплики
      random:
        - message: "Голем медленно движется."
          chance: 10
```

---

## Секция OBJECTS

```yaml
objects:
  - id: "obj_001"
    vnum: 10201
    keywords: ["кристалл", "соль", "crystal"]

    # Имена (6 падежей)
    name:
      nominative: "соляной кристалл"
      genitive: "соляного кристалла"
      dative: "соляному кристаллу"
      accusative: "соляной кристалл"
      instrumental: "соляным кристаллом"
      prepositional: "соляном кристалле"

    short_description: "соляной кристалл"
    long_description: "Соляной кристалл лежит здесь."

    examine: |
      Детальное описание при examine.

    # Тип объекта - см. game-mechanics.md раздел 7.1
    type: "TREASURE"         # LIGHT_SOURCE, SCROLL, WAND, STAFF, WEAPON,
                             # ARMOR, POTION, CONTAINER, KEY, FOOD, MONEY,
                             # TREASURE, BOOK, INGREDIENT, и т.д.

    # Свойства
    properties:
      weight: 2              # Вес (фунты)
      value: 50              # Стоимость (золото)

      # Материал - см. game-mechanics.md раздел 7.2
      material: "CRYSTAL"    # BULAT, BRONZE, IRON, STEEL, CRYSTAL, WOOD,
                             # STONE, BONE, CLOTH, SKIN, DIAMOND, и т.д.

      # Флаги - см. game-mechanics.md раздел 7.3
      flags:
        - "GLOW"             # Светится
        - "MAGIC"            # Магическое
        # Другие: HUM, NORENT, NODONATE, INVISIBLE, NODROP,
        #         BLESS, NOSELL, DECAY, POISONED, SHARPEN,
        #         FIRE, TWO_HANDS, ARMORED, BLOODY

      # Эффекты (бонусы, проки)
      effects:
        - type: "bonus_stat"
          stat: "strength"   # или dexterity, constitution, и т.д.
          value: 1

        - type: "proc_on_hit"
          proc_type: "slow"
          chance: 10         # Процент
          duration: 3        # Раундов

    # ДЛЯ ОРУЖИЯ (если type: WEAPON)
    weapon:
      damage_dice: "2d6+2"
      weapon_type: "longsword"  # sword, dagger, axe, mace, spear, etc
      damage_type: "slash"      # slash, pierce, blunt

      hit_bonus: 2              # Бонус к попаданию
      damage_bonus: 2           # Бонус к урону

    # ДЛЯ БРОНИ (если type: ARMOR/LIGHT_ARMOR/MEDIUM_ARMOR/HEAVY_ARMOR)
    armor:
      armor_class: 5
      wear_location: "body"     # head, body, arms, legs, hands, feet,
                                # neck, finger, waist, wrist, shield

    # ДЛЯ КОНТЕЙНЕРА (если type: CONTAINER)
    container:
      capacity: 100             # Вместимость (фунты)
      key_vnum: null            # ID ключа (null = не заперт)

      # Содержимое при спавне
      contains:
        - object_id: "obj_coin"
          count: 10

    # ДЛЯ ЕДЫ (если type: FOOD)
    food:
      hours: 4                  # На сколько часов утоляет голод
      poisoned: false           # Отравлено

    # ДЛЯ ЗЕЛЬЯ (если type: POTION)
    potion:
      effects:
        - spell: "heal"
          level: 10
        - spell: "cure_poison"
          level: 5
```

---

## Секция TRIGGERS (опционально)

```yaml
triggers:
  - id: "trigger_001"
    name: "Обвал потолка"
    type: "room_enter"       # room_enter, mob_death, obj_use, time

    # Привязка
    room_id: "room_003"      # Или mob_id, obj_id в зависимости от типа

    # Условия
    conditions:
      - type: "random"
        chance: 30           # Процент

      - type: "time"         # Время суток (опционально)
        from_hour: 0
        to_hour: 6

    # Действия
    actions:
      - type: "message_room"
        text: "Потолок содрогается!"

      - type: "damage"
        target: "actor"      # actor, room, all
        damage: "2d6"

      - type: "spawn_mobile"
        mobile_id: "mob_001"
        count: 1
```

---

## Секция QUESTS (опционально)

```yaml
quests:
  - id: "quest_001"
    name: "Название квеста"
    description: |
      Описание квеста.

    level_min: 10
    level_max: 15

    # Этапы
    stages:
      - id: 1
        description: "Поговорить с NPC"
        type: "talk_to_npc"
        npc_id: "mob_npc"

      - id: 2
        description: "Найти комнату"
        type: "enter_room"
        room_id: "room_010"

      - id: 3
        description: "Убить моба"
        type: "kill_mobile"
        mobile_id: "mob_boss"
        count: 1

      - id: 4
        description: "Принести предмет"
        type: "bring_object"
        object_id: "obj_quest"
        npc_id: "mob_npc"

    # Награды
    rewards:
      exp: 3000
      gold: 500

      items:
        - object_id: "obj_reward"
          count: 1

      reputation:
        faction: "spirits"
        value: 100

    completion_message: |
      Поздравительное сообщение.
```

---

## Рекомендации по балансу

### Мобы по уровням

См. game-mechanics.md раздел 2.3 для полной таблицы.

**Пример для уровня 13 (TRASH):**
```yaml
hp: 500-1000           # Средний: 750
damage: "2d6+2"        # Средний: 9
exp: 1690              # 13^2 * 10
gold: [45, 85]         # 13 * 5 * (0.7-1.3)
```

**Для BOSS уровня 13:**
```yaml
hp: 2000-3500          # x3 от trash
damage: "3d6+4"        # Больше урона
exp: 5070              # 13^2 * 30
gold: [220, 420]       # 13 * 25 * (0.7-1.3)
```

### Шанс лута

```yaml
common_item:    30-50%
uncommon_item:  15-25%
rare_item:      5-10%
epic_item:      1-3%
quest_item:     100% (для квестовых мобов)
```

---

## Чеклист для создания моба

```yaml
✓ Обязательные поля:
  - [ ] id, vnum
  - [ ] keywords (мин 2)
  - [ ] name (все 6 падежей)
  - [ ] short_description, long_description, examine
  - [ ] level (1-50)
  - [ ] role (BOSS/TRASH/etc)
  - [ ] race
  - [ ] stats: hp, 6 характеристик, armor, damage_dice
  - [ ] behavior: все базовые флаги
  - [ ] resistances
  - [ ] loot: exp, gold, items

✓ Проверить баланс:
  - [ ] HP соответствует уровню и роли
  - [ ] Урон соответствует уровню
  - [ ] Опыт по формуле: level^2 * role_mult
  - [ ] Золото по формуле: level * role_mult * (0.7-1.3)

✓ Опциональные:
  - [ ] special_attacks
  - [ ] speech (реплики)
  - [ ] breath (для драконов)
```

---

## Конвертация в формат движка

Планируется создание скрипта `tools/converter.py`, который будет конвертировать этот YAML формат в формат движка (.wld, .mob, .obj, .zon файлы).

---

**См. также:**
- `game-mechanics.md` - полный справочник механик
- `quality-metrics.md` - система оценки зон
- `zone-requirements.md` - требования к зонам
