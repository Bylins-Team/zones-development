# Формат файлов зон

## Структура YAML файла зоны

Файл зоны состоит из нескольких основных секций:

```yaml
zone:
  meta:          # Метаинформация о зоне
  rooms:         # Комнаты
  mobiles:       # Мобы (NPC)
  objects:       # Объекты (предметы)
  triggers:      # Триггеры и скрипты (опционально)
  quests:        # Квесты (опционально)
```

## Секция META

Общая информация о зоне.

```yaml
meta:
  id: "zone_001"                    # Уникальный ID зоны
  name: "Соляные копи"              # Название зоны
  author: "Автор"                   # Автор зоны
  version: "1.0"                    # Версия
  created: "2026-02-06"             # Дата создания

  # Описание и тематика
  description: |
    Древние соляные копи, где добывали соль для сохранения пищи.
    Теперь соль законсервировала не только мертвых, но и само время.

  folklore_basis: |
    Соль в славянской мифологии - защита от нечисти, но здесь
    она превратилась в тюрьму для душ.

  # Игровые параметры
  level_min: 10                     # Минимальный уровень
  level_recommended: 13             # Рекомендуемый уровень
  level_max: 15                     # Максимальный уровень

  # Теги для категоризации
  tags:
    - underground
    - undead
    - slavic_folklore

  # Точки входа в зону (ID комнат)
  entry_points:
    - "room_001"
```

## Секция ROOMS

Описание комнат зоны.

```yaml
rooms:
  - id: "room_001"                  # Уникальный ID комнаты
    vnum: 10001                     # Виртуальный номер (для совместимости)
    name: "Вход в копи"             # Короткое название

    # Детальное описание
    description: |
      Широкий проход ведет вглубь горы. Стены покрыты белым налетом
      соли, который искрится в тусклом свете факелов. Воздух сухой
      и соленый, першит в горле. Под ногами скрипят кристаллы соли.

    # Дополнительное описание при examine
    examine: |
      Стены изъедены временем и влагой. Местами видны следы кирок.
      Белая соляная пыль покрывает все поверхности.

    # Сектор (тип местности)
    sector: "underground"

    # Флаги комнаты
    flags:
      - "dark"                      # Темно (нужен свет)
      - "no_magic"                  # Магия не работает (опционально)
      - "indoors"                   # Помещение

    # Выходы
    exits:
      - direction: "north"          # Направление
        to_room: "room_002"         # ID целевой комнаты
        description: "Темный проход уходит на север."

      - direction: "south"
        to_room: "outside_world"    # Выход за пределы зоны
        description: "На юг ведет выход из копей."

    # Мобы в комнате (спавн)
    mobiles:
      - mobile_id: "mob_001"        # ID моба
        max_count: 2                # Максимум одновременно
        respawn_time: 300           # Время респавна (секунды)

    # Объекты в комнате
    objects:
      - object_id: "obj_001"
        max_count: 1
        respawn_time: 600

    # Атмосферные сообщения (случайные)
    atmosphere:
      - message: "Соляная пыль искрится в воздухе."
        chance: 20                  # Шанс появления (%)
      - message: "Где-то вдали слышен скрип кристаллов."
        chance: 15
```

## Секция MOBILES

Описание мобов (NPC).

```yaml
mobiles:
  - id: "mob_001"                   # Уникальный ID моба
    vnum: 10101                     # Виртуальный номер
    keywords:                       # Ключевые слова для таргетинга
      - "голем"
      - "соляной"
      - "golem"

    # Имена (падежи для русского языка)
    name:
      nominative: "соляной голем"   # Именительный: кто? что?
      genitive: "соляного голема"   # Родительный: кого? чего?
      dative: "соляному голему"     # Дательный: кому? чему?
      accusative: "соляного голема" # Винительный: кого? что?
      instrumental: "соляным големом" # Творительный: кем? чем?
      prepositional: "соляном големе" # Предложный: о ком? о чем?

    short_description: "соляной голем стоит здесь"
    long_description: |
      Массивная фигура из кристаллов соли медленно движется по копям.
      Голем сложен из прозрачных и мутных кристаллов, в которых
      играют отблески света. Его движения сопровождаются скрипом и
      звоном осыпающихся кристаллов.

    examine: |
      Кристаллическое тело голема пронизано трещинами. В глубине
      кристаллов видны застывшие фигуры - возможно, его жертвы.

    # Характеристики
    level: 13

    stats:
      hp: 2000                      # Здоровье
      mana: 0                       # Мана (если использует магию)

      # Базовые характеристики
      strength: 18
      dexterity: 8
      constitution: 20
      intelligence: 6
      wisdom: 6
      charisma: 3

      # Защита
      armor: 30                     # Класс брони

      # Атака
      damage_dice: "2d8+5"          # Кость урона
      hit_bonus: 3                  # Бонус к попаданию
      attacks_per_round: 1

    # Поведение
    behavior:
      aggressive: true              # Агрессивен
      assist: true                  # Помогает союзникам
      memory: true                  # Помнит врагов

      aggro_range: 0                # 0 = атакует только в своей комнате

      # Специальные способности
      special_attacks:
        - type: "bash"              # Таран
          chance: 15                # Шанс использования (%)
          cooldown: 3               # Откат (раунды)

        - type: "stun"              # Оглушение
          chance: 10
          cooldown: 5
          duration: 2               # Длительность (раунды)

    # Сопротивления (в процентах)
    resistances:
      physical: 20
      fire: -20                     # Уязвим к огню
      cold: 30
      poison: 100                   # Иммунитет

    # Лут
    loot:
      gold:
        min: 50
        max: 150

      exp: 800                      # Опыт за убийство

      items:
        - object_id: "obj_002"
          chance: 30                # Шанс выпадения (%)

        - object_id: "obj_003"
          chance: 15

    # Реплики
    speech:
      on_spawn: "Соляной голем медленно поворачивает голову."
      on_aggro: "Голем издает скрежещущий звук!"
      on_death: "Голем рассыпается на кристаллы соли."

      random:                       # Случайные реплики
        - message: "Кристаллы на теле голема звенят."
          chance: 10
```

## Секция OBJECTS

Описание объектов (предметов).

```yaml
objects:
  - id: "obj_001"                   # Уникальный ID объекта
    vnum: 10201                     # Виртуальный номер
    keywords:
      - "кристалл"
      - "соль"
      - "crystal"

    # Имена (падежи)
    name:
      nominative: "соляной кристалл"
      genitive: "соляного кристалла"
      dative: "соляному кристаллу"
      accusative: "соляной кристалл"
      instrumental: "соляным кристаллом"
      prepositional: "соляном кристалле"

    short_description: "соляной кристалл"
    long_description: "Прозрачный соляной кристалл лежит здесь."

    examine: |
      Красивый прозрачный кристалл соли размером с кулак.
      Внутри видны причудливые узоры.

    # Тип объекта
    type: "treasure"                # treasure, weapon, armor, food, potion, key, container, etc.

    # Свойства
    properties:
      weight: 2                     # Вес (фунты)
      value: 50                     # Стоимость (золото)

      material: "salt"              # Материал

      flags:
        - "glow"                    # Светится

    # Для оружия (если type: weapon)
    # weapon:
    #   damage_dice: "1d6"
    #   weapon_type: "sword"
    #   damage_type: "slash"

    # Для брони (если type: armor)
    # armor:
    #   armor_class: 5
    #   wear_location: "body"

    # Для контейнеров (если type: container)
    # container:
    #   capacity: 100
    #   key_id: "obj_key_001"

  - id: "obj_002"
    vnum: 10202
    keywords: ["меч", "соляной", "sword"]

    name:
      nominative: "соляной меч"
      genitive: "соляного меча"
      dative: "соляному мечу"
      accusative: "соляной меч"
      instrumental: "соляным мечом"
      prepositional: "соляном мече"

    short_description: "соляной меч"
    long_description: "Меч из кристаллической соли лежит здесь."

    examine: |
      Необычный меч, выкованный из кристаллической соли.
      Несмотря на хрупкий вид, он довольно острый и прочный.
      На лезвии видны магические руны.

    type: "weapon"

    properties:
      weight: 5
      value: 500
      material: "salt_crystal"

      flags:
        - "magic"
        - "glow"

      # Специальные эффекты
      effects:
        - type: "bonus_stat"
          stat: "strength"
          value: 1

        - type: "proc_on_hit"       # Срабатывает при ударе
          proc_type: "slow"
          chance: 10
          duration: 3

    weapon:
      damage_dice: "2d6+2"
      weapon_type: "longsword"
      damage_type: "slash"

      # Бонусы к попаданию/урону
      hit_bonus: 2
      damage_bonus: 2
```

## Секция TRIGGERS (опционально)

Скрипты и триггеры для интерактивности.

```yaml
triggers:
  - id: "trigger_001"
    name: "Обвал потолка"
    type: "room_enter"              # Триггер при входе в комнату

    room_id: "room_003"

    conditions:
      - type: "random"
        chance: 30                  # 30% шанс

    actions:
      - type: "message_room"
        text: "Потолок содрогается, и соляные кристаллы осыпаются вниз!"

      - type: "damage"
        target: "actor"             # Тот, кто вошел
        damage: "2d6"

      - type: "spawn_mobile"
        mobile_id: "mob_001"
        count: 1
```

## Секция QUESTS (опционально)

Описание квестов в зоне.

```yaml
quests:
  - id: "quest_001"
    name: "Освобождение душ"
    description: |
      Старый призрак просит освободить души, заключенные в соляных
      кристаллах. Для этого нужно найти и уничтожить источник
      проклятия - огромный кристалл в глубине копей.

    level_min: 10
    level_max: 15

    # Этапы квеста
    stages:
      - id: 1
        description: "Поговорить с призраком у входа"
        type: "talk_to_npc"
        npc_id: "mob_ghost"

      - id: 2
        description: "Найти главный зал копей"
        type: "enter_room"
        room_id: "room_010"

      - id: 3
        description: "Уничтожить проклятый кристалл"
        type: "destroy_object"
        object_id: "obj_cursed_crystal"

      - id: 4
        description: "Вернуться к призраку"
        type: "talk_to_npc"
        npc_id: "mob_ghost"

    # Награды
    rewards:
      exp: 2000
      gold: 500
      items:
        - object_id: "obj_reward_amulet"
          count: 1

      reputation:
        faction: "spirits"
        value: 100
```

## Полный пример

См. файл `zones/draft/salt-mines-example.yaml` для полного примера зоны.

## Конвертация в формат движка

Позже будет создан скрипт `tools/converter.py`, который будет конвертировать
наш YAML формат в формат, ожидаемый движком МУД.

## Валидация

Используйте скрипт `tools/validator.py` для проверки корректности файла зоны
перед коммитом.

```bash
python tools/validator.py zones/draft/my-zone.yaml
```
