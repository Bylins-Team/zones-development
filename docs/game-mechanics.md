# Справочник игровых механик МУД "Былины"

> **Источник:** Кодовая база движка ~/repos/mud
> **Дата:** 2026-02-06
> **Назначение:** Полный справочник для создания зон без обращения к движку

---

## 1. СИСТЕМА ХАРАКТЕРИСТИК

### 1.1 Базовые характеристики (Stats)

```yaml
strength:     # Сила (Str)
  affects: [damage, carry_weight, bash]
  range: [10-50]  # 10-25 персонажи, до 50 с бонусами

dexterity:    # Ловкость (Dex)
  affects: [ac, initiative, dodge, reflex_save]
  range: [10-50]

constitution: # Телосложение (Con)
  affects: [hp, hp_regen, stability_save]
  range: [10-50]

wisdom:       # Мудрость (Wis)
  affects: [mana_regen, will_save, spell_resist]
  range: [10-50]

intelligence: # Интеллект (Int)
  affects: [mana, spell_power, spell_success]
  range: [10-50]

charisma:     # Обаяние (Cha)
  affects: [charm, prices, leadership]
  range: [10-50]
```

### 1.2 Модификаторы от Intelligence

| Int | Spell Knowledge | To Skilluse | Mana/Tic | Spell Success | Improve | Observation |
|-----|----------------|-------------|----------|---------------|---------|-------------|
| 0   | 10             | -10         | 10       | 0             | 2       | -5          |
| 5   | 22             | -8          | 20       | 0             | 3       | -3          |
| 10  | 42             | -6          | 60       | 0             | 4       | 0           |
| 15  | 60             | -2          | 75       | 0             | 5       | 1           |
| 18  | 72             | 0           | 84       | 0             | 7       | 2           |
| 20  | 78             | 2           | 90       | 0             | 8       | 3           |
| 25  | 90             | 5           | 100      | 0             | 9       | 5           |
| 30  | 96             | 8           | 120      | 0             | 11      | 8           |
| 40  | 100            | 10          | 160      | 0             | 13      | 12          |
| 50  | 100            | 12          | 200      | 0             | 15      | 15          |

### 1.3 Размер (Size)

Влияет на:
- **AC бонус** - защита
- **Bash бонус** - сила толчка
- **Interpolation** - интерполяция навыков
- **Initiative** - инициатива

---

## 2. СИСТЕМА УРОВНЕЙ

### 2.1 Диапазоны

```yaml
zone_level:
  min: 1
  max: 50

character_level:
  min: 1
  max: 50
  newbie_threshold: 10  # Новичок
```

### 2.2 Формула расчета параметров мобов

```python
def calc_mob_param(base, level, remorts, low_increment, increment, threshold_mort):
    """
    Базовая формула расчета параметров мобов

    Args:
        base: Базовое значение параметра
        level: Уровень моба
        remorts: Количество перевоплощений (обычно 0 для мобов)
        low_increment: Прирост до порога
        increment: Прирост после порога
        threshold_mort: Порог перевоплощений
    """
    low_morts = min(remorts, threshold_mort)
    high_morts = max(0, remorts - threshold_mort)

    inc_sum = low_increment * low_morts + increment * high_morts

    scale = level / 30.0  # Базовый масштаб на 30-й уровень

    return round((base + inc_sum) * scale)

# Пример для HP:
# calc_mob_param(base=800, level=15, remorts=0,
#                low_increment=0, increment=0, threshold_mort=0)
# = 800 * (15/30) = 400 HP для 15 lvl моба
```

### 2.3 Рекомендации по параметрам мобов

| Уровень | HP (обычный) | HP (элита) | HP (босс) | Урон (NdN+B) | Exp (база) |
|---------|--------------|------------|-----------|--------------|------------|
| 1-5     | 50-150       | 150-300    | 300-500   | 1d4+0        | 50-200     |
| 6-10    | 200-400      | 400-800    | 800-1200  | 1d6+1        | 200-500    |
| 11-15   | 500-1000     | 1000-2000  | 2000-3500 | 2d6+2        | 500-1500   |
| 16-20   | 1200-2000    | 2000-3500  | 3500-5000 | 2d8+4        | 1500-3000  |
| 21-25   | 2500-3500    | 3500-5000  | 5000-7500 | 3d8+6        | 3000-5000  |
| 26-30   | 4000-5500    | 5500-7500  | 7500-10k  | 3d10+8       | 5000-8000  |
| 31-40   | 6000-9000    | 9000-12k   | 12k-18k   | 4d10+10      | 8000-15k   |
| 41-50   | 10k-15k      | 15k-22k    | 22k-35k   | 5d12+15      | 15k-30k    |

---

## 3. ФЛАГИ МОБОВ

### 3.1 Основные флаги (MOB_FLAGS)

```yaml
# Базовое поведение
SPEC:              # Имеет специальную процедуру
SENTINEL:          # Не двигается из комнаты
SCAVENGER:         # Подбирает предметы
AWARE:             # Нельзя заколоть в спину
AGGRESSIVE:        # Атакует игроков в комнате
STAY_ZONE:         # Не выходит за пределы зоны
WIMPY:             # Убегает при ранении
MEMORY:            # Помнит атакующих
HELPER:            # Помогает другим NPC в бою
AGGRESSIVE_DAY:    # Агрессивен днем
AGGRESSIVE_NIGHT:  # Агрессивен ночью

# Иммунитеты
NO_CHARM:          # Нельзя очаровать
NO_SUMMON:         # Нельзя призвать
NO_SLEEP:          # Нельзя усыпить
NO_BASH:           # Нельзя сбить с ног
NO_BLIND:          # Нельзя ослепить
NO_HOLD:           # Нельзя удержать
NO_SILENCE:        # Нельзя заставить замолчать
NO_FEAR:           # Не боится
```

### 3.2 Дыхания драконов

```yaml
FIRE_BREATH:       # Огненное дыхание (урон огнем)
GAS_BREATH:        # Газовое дыхание (яд)
FROST_BREATH:      # Ледяное дыхание (холод)
ACID_BREATH:       # Кислотное дыхание (кислота)
LIGHTING_BREATH:   # Электрическое дыхание (молния)

# Урон: GET_NDD(ch) * 0.5 и GET_SDD(ch) * 0.5
# Частота: каждые 3-5 раундов
```

### 3.3 Позиции моба

```yaml
DEAD:       # Мертв
MORTALLY:   # Смертельно ранен
INCAP:      # Недееспособен
STUNNED:    # Оглушен
SLEEPING:   # Спит
RESTING:    # Отдыхает
SITTING:    # Сидит
FIGHTING:   # Дерется
STANDING:   # Стоит
```

---

## 4. КЛАССЫ И РОЛИ МОБОВ

### 4.1 Роли мобов (для баланса)

```yaml
BOSS:          # Босс - главный противник зоны
  hp_mult: 3.0
  damage_mult: 1.5
  exp_mult: 3.0
  gold_mult: 5.0

TRASH:         # Обычный моб
  hp_mult: 1.0
  damage_mult: 1.0
  exp_mult: 1.0
  gold_mult: 1.0

TANK:          # Танк - много HP, мало урона
  hp_mult: 2.0
  damage_mult: 0.7
  exp_mult: 1.3

MELLEE_DMG:    # Ближний боец
  hp_mult: 1.2
  damage_mult: 1.4
  exp_mult: 1.5

ARCHER:        # Лучник
  hp_mult: 0.8
  damage_mult: 1.3
  exp_mult: 1.3

ROGUE:         # Разбойник
  hp_mult: 0.9
  damage_mult: 1.5
  exp_mult: 1.4
  special: [backstab, dodge]

MAGE_DMG:      # Маг-урон
  hp_mult: 0.6
  damage_mult: 2.0
  exp_mult: 1.6

MAGE_BUFF:     # Маг-поддержка
  hp_mult: 0.7
  damage_mult: 0.8
  exp_mult: 1.2

HEALER:        # Целитель
  hp_mult: 1.0
  damage_mult: 0.5
  exp_mult: 1.1
```

### 4.2 Расы мобов

```yaml
BASIC:             100  # Базовая раса
HUMAN:             101  # Человек
BEASTMAN:          102  # Зверолюд
BIRD:              103  # Птица
ANIMAL:            104  # Животное
REPTILE:           105  # Рептилия
FISH:              106  # Рыба
INSECT:            107  # Насекомое
PLANT:             108  # Растение
CONSTRUCT:         109  # Конструкт (голем, автомат)
ZOMBIE:            110  # Зомби
GHOST:             111  # Призрак
BOGGART:           112  # Бука
SPIRIT:            113  # Дух
MAGIC_CREATURE:    114  # Магическое существо
```

---

## 5. ТИПЫ АТАК

### 5.1 Физические атаки

```yaml
type_hit:          # Удар (кулаком, оружием)
type_skin:         # Кожей (наносит урон телом)
type_whip:         # Хлыстом
type_slash:        # Рубящий удар (мечом)
type_bite:         # Укус
type_bludgeon:     # Тупое оружие (дубина)
type_crush:        # Раздавливание
type_pound:        # Толчок
type_claw:         # Когти
type_maul:         # Избиение
type_thrash:       # Размахивание
type_pierce:       # Пронзание (копьем)
type_blast:        # Взрыв
type_punch:        # Кулак
type_stab:         # Укол (кинжалом)
type_pick:         # Острие (кирка)
type_sting:        # Жало (укус насекомого)
```

### 5.2 Специальные атаки

```yaml
bash:              # Сбить с ног
  cooldown: 3
  stun_duration: 1-2

stun:              # Оглушение
  cooldown: 5
  duration: 2

power_strike:      # Мощный удар
  damage_mult: 2.0
  cooldown: 4

poison:            # Отравление
  duration: 10
  damage_per_tick: "1d4"

disease:           # Болезнь
  duration: 20
  debuff: -2 stats

fear:              # Страх
  duration: 3
  effect: flee

chill_touch:       # Ледяное касание
  damage: cold
  debuff: -1 Str

acid:              # Кислота
  damage: acid
  dot: "1d6 per round"

slow:              # Замедление
  duration: 4
  move_cost: x2
```

---

## 6. ТИПЫ УРОНА

### 6.1 Основные типы

```yaml
UNDEF_DMG:     # Неопределенный урон
PHYS_DMG:      # Физический урон (проходит через броню)
MAGIC_DMG:     # Магический урон (через сопротивления)
POISON_DMG:    # Яд (особые правила)
PURE_DMG:      # Чистый урон (игнорирует все защиты)
```

### 6.2 Элементальные сопротивления

```yaml
# Диапазон: -100 до +75 (для игроков макс 75)
# Отрицательные = уязвимость, положительные = сопротивление

FIRE:          # Огонь
AIR:           # Воздух
WATER:         # Вода
EARTH:         # Земля
VITALITY:      # Жизненная сила
MIND:          # Разум
IMMUNITY:      # Иммунитет
DARK:          # Тьма
```

### 6.3 Флаги атаки

```yaml
IGNORE_SANCT:        # Игнорирует санкуарий
IGNORE_PRISM:        # Игнорирует призму
IGNORE_ARMOR:        # Игнорирует броню
HALF_IGNORE_ARMOR:   # Полуигнор брони
IGNORE_ABSORBE:      # Игнорирует поглощение
CRIT_HIT:            # Критический удар
CRIT_LUCK:           # Крит удачи
IGNORE_FIRE_SHIELD:  # Игнорирует огненный щит
MAGIC_REFLECT:       # Отражает магию
VICTIM_FIRE_SHIELD:  # Накладывает огненный щит на жертву
VICTIM_AIR_SHIELD:   # Накладывает воздушный щит
VICTIM_ICE_SHIELD:   # Накладывает ледяной щит
```

---

## 7. ТИПЫ ОБЪЕКТОВ

### 7.1 Основные типы

```yaml
UNDEFINED:           0   # Не определен
LIGHT_SOURCE:        1   # Источник света
SCROLL:              2   # Свиток
WAND:                3   # Палочка
STAFF:               4   # Посох
WEAPON:              5   # Оружие
ELEMENT_WEAPON:      6   # Элементальное оружие
MISSILE:             7   # Снаряд
TREASURE:            8   # Сокровище
ARMOR:               9   # Броня
POTION:             10   # Зелье
OTHER:              12   # Прочее
TRASH:              13   # Мусор
TRAP:               14   # Ловушка
CONTAINER:          15   # Контейнер
NOTE:               16   # Записка
LIQUID_CONTAINER:   17   # Емкость с жидкостью
KEY:                18   # Ключ
FOOD:               19   # Еда
MONEY:              20   # Деньги
PEN:                21   # Перо
BOAT:               22   # Лодка
FOUNTAIN:           23   # Фонтан
BOOK:               24   # Книга
INGREDIENT:         25   # Ингредиент
MAGIC_INGREDIENT:   26   # Магический ингредиент
CRAFT_MATERIAL:     27   # Материал ремесла
BANDAGE:            28   # Повязка
LIGHT_ARMOR:        29   # Легкая броня
MEDIUM_ARMOR:       30   # Средняя броня
HEAVY_ARMOR:        31   # Тяжелая броня
```

### 7.2 Материалы

```yaml
UNDEFINED:         # Не определен
BULAT:             # Булат
BRONZE:            # Бронза
IRON:              # Железо
STEEL:             # Сталь
FORGED_STEEL:      # Кованая сталь
PRECIOUS_METEL:    # Драгоценный металл
CRYSTAL:           # Кристалл
WOOD:              # Дерево
HARD_WOOD:         # Твердое дерево
CERAMIC:           # Керамика
GLASS:             # Стекло
STONE:             # Камень
BONE:              # Кость
CLOTH:             # Ткань
SKIN:              # Кожа
ORGANIC:           # Органика
PAPER:             # Бумага
DIAMOND:           # Алмаз
```

### 7.3 Флаги объектов

```yaml
GLOW:              # Светится
HUM:               # Гудит
NORENT:            # Нельзя сдать на хранение
NODONATE:          # Нельзя пожертвовать
INVISIBLE:         # Невидимо
MAGIC:             # Магическое
NODROP:            # Нельзя бросить
BLESS:             # Благословлено
NOSELL:            # Нельзя продать
DECAY:             # Распадается
POISONED:          # Отравлено
SHARPEN:           # Заточено
FIRE:              # Горит огнем
TWO_HANDS:         # Двуручное
ARMORED:           # Усилено броней
BLOODY:            # Окровавлено
```

---

## 8. ФЛАГИ КОМНАТ

### 8.1 Основные флаги

```yaml
DARKED:            # Темная комната (нужен свет)
DEATH_TRAP:        # Смертельная ловушка
INDOORS:           # В помещении
PEACEFUL:          # Мирная (нельзя драться)
SOUNDPROOF:        # Звукоизолированная
NO_TRACK:          # Нельзя отследить
NO_MAGIC:          # Магия не работает
TUNNEL:            # Туннель (лимит на количество)
NO_TELEPORT_IN:    # Нельзя телепортироваться
GODS_ROOM:         # Только для богов
ARENA:             # Арена (особые правила)
NO_RECALL:         # Нельзя отозваться
NO_SUMMON:         # Нельзя призвать
SLOW_REGEN:        # Медленная регенерация
FAST_REGEN:        # Быстрая регенерация
ICE:               # Ледяная (скользко)
```

### 8.2 Типы секторов (местности)

```yaml
INSIDE:            # В помещении
CITY:              # Город
FIELD:             # Поле
FOREST:            # Лес
HILLS:             # Холмы
MOUNTAIN:          # Горы
WATER_SWIM:        # Вода (плыть)
WATER_NOSWIM:      # Вода (не плыть, нужна лодка)
UNDERWATER:        # Под водой
FLYING:            # В воздухе
SECRET:            # Секретная
ROAD:              # Дорога
THICK_ICE:         # Толстый лед
NORMAL_ICE:        # Обычный лед
THIN_ICE:          # Тонкий лед
```

### 8.3 Флаги выходов

```yaml
HAS_DOOR:          # Есть дверь
CLOSED:            # Закрыто
LOCKED:            # Заперто
PICKPROOF:         # Нельзя отпереть отмычкой
HIDDEN:            # Скрытый выход
BROKEN_LOCK:       # Замок сломан
```

---

## 9. СОХРАНЯЮЩИЕ БРОСКИ (SAVING THROWS)

```yaml
# Диапазон: 1-300 (1 - лучший, 300 - худший)

WILL:              # Воля (против магии разума)
CRITICAL:          # Критический (против крит. ударов)
STABILITY:         # Стабильность (против толчков)
REFLEX:            # Рефлекс (против ловкости)
```

---

## 10. ФОРМУЛЫ БАЛАНСА

### 10.1 HP Регенерация персонажа

```python
def hp_regen(con, age, position, in_fight, poisoned):
    """
    Расчет регенерации HP
    """
    restore = max(10, con * 3 // 2)

    # По возрасту
    if age < 20:    gain = restore - 3
    elif age < 30:  gain = restore
    elif age < 35:  gain = restore
    elif age < 50:  gain = restore - 2
    elif age < 75:  gain = restore - 3
    else:           gain = restore - 5

    # Модификаторы позиции
    percent = 100
    if position == "sleep":   percent += 100
    if position == "rest":    percent += 50
    if position == "sit":     percent += 25

    # В бою
    if in_fight:
        percent -= 50

    # Отравление
    if poisoned:
        percent //= 2

    return gain * percent // 100
```

### 10.2 Mana Регенерация

```python
def mana_regen(intelligence, position, in_fight, caster_class):
    """
    Расчет регенерации маны
    """
    # Базовый gain от интеллекта (см. таблицу выше)
    gain = int_app[intelligence]['mana_per_tic']

    percent = 100

    # Позиция
    if caster_class:
        if position == "sleep":  percent += 80
        if position == "rest":   percent += 45
        if position == "sit":    percent += 30

    # В бою
    if in_fight:
        if caster_class:
            percent -= 50
        else:
            percent -= 90

    return gain * percent // 100
```

### 10.3 Броня (AC)

```python
def calc_armor(dex, armor_items, magic_bonuses):
    """
    Расчет класса брони

    AC: чем НИЖЕ - тем ЛУЧШЕ защита
    """
    base_ac = 100  # Базовая AC

    # Бонус от ловкости
    dex_bonus = (dex - 10) * 2

    # Броня с предметов
    armor_value = sum(item.armor for item in armor_items)

    # Магические бонусы
    magic_ac = sum(magic_bonuses)

    # Итоговая AC
    ac = base_ac - dex_bonus - armor_value - magic_ac

    return ac
```

### 10.4 Урон в бою

```python
def calc_damage(num_dice, size_dice, bonus, multipliers):
    """
    Расчет урона

    Args:
        num_dice: количество кубиков (NdN)
        size_dice: размер кубика (NdN)
        bonus: постоянный бонус (+B)
        multipliers: множители (крит, баш, и т.д.)
    """
    import random

    # Бросаем кости
    dice_result = sum(random.randint(1, size_dice) for _ in range(num_dice))

    # Базовый урон
    damage = dice_result + bonus

    # Применяем множители
    for mult in multipliers:
        damage = int(damage * mult)

    return max(1, damage)  # Минимум 1 урон
```

### 10.5 Опыт за моба

```python
def calc_mob_exp(mob_level, mob_role, player_level, group_size, zone_difficulty):
    """
    Расчет опыта за убийство моба
    """
    # Базовый опыт
    base_exp = 10 * (mob_level ** 2)

    # Множитель роли
    role_mult = {
        'trash': 1.0,
        'elite': 1.5,
        'boss': 3.0,
        'rare': 2.0
    }

    exp = base_exp * role_mult.get(mob_role, 1.0)

    # Корректировка по разнице уровней
    level_diff = mob_level - player_level
    if level_diff > 5:
        exp *= 1.2  # Бонус за сложного моба
    elif level_diff < -5:
        exp *= 0.5  # Штраф за легкого моба

    # Делим на группу
    exp = exp / max(1, group_size * 0.8)

    # Множитель сложности зоны
    exp *= zone_difficulty

    return int(exp)
```

### 10.6 Золото с моба

```python
def calc_mob_gold(mob_level, mob_role, zone_wealth):
    """
    Расчет золота с моба
    """
    # Базовое золото
    base_gold = 5 * mob_level

    # Множитель роли
    role_mult = {
        'trash': 1.0,
        'elite': 2.0,
        'boss': 5.0
    }

    gold = base_gold * role_mult.get(mob_role, 1.0)

    # Множитель богатства зоны
    gold *= zone_wealth

    # Разброс ±30%
    min_gold = int(gold * 0.7)
    max_gold = int(gold * 1.3)

    return (min_gold, max_gold)
```

---

## 11. КОНСТАНТЫ

### 11.1 Игровые константы

```yaml
MAX_GROUP_FOLLOWERS: 7      # Макс членов группы
MOB_ARMOUR_MULT: 5          # Множитель брони для мобов
MOB_AC_MULT: 5              # Множитель AC
MOB_DAMAGE_MULT: 3          # Множитель урона

FIRE_MOVES: 20              # Стоимость движения через огонь
LOOKING_MOVES: 5            # Стоимость осмотра
HEARING_MOVES: 2            # Стоимость прослушивания
SNEAK_MOVES: 1              # Стоимость крадучись
PICKLOCK_MOVES: 10          # Стоимость взлома

MAX_PC_RESIST: 75           # Макс сопротивление для PC
```

### 11.2 Время

```yaml
# Игровое время
HOURS_PER_DAY: 24
DAYS_PER_WEEK: 7
WEEKS_PER_MONTH: 4
MONTHS_PER_YEAR: 12

# Реальное время
SECS_PER_MUD_HOUR: 75       # 1 игровой час = 75 секунд
SECS_PER_MUD_DAY: 1800      # 1 игровой день = 30 минут
```

---

## 12. КЛАССЫ ПЕРСОНАЖЕЙ

```yaml
# Для справки (персонажи игроков)

SORCERER:      # Чародей (огненная магия)
CONJURER:      # Чернокнижник (темная магия)
THIEF:         # Вор
WARRIOR:       # Воин
ASSASSINE:     # Убийца
GUARD:         # Охранник
CHARMER:       # Очаровник
WIZARD:        # Волшебник
NECROMANCER:   # Некромант
PALADINE:      # Паладин
RANGER:        # Рейнджер
VIGILANT:      # Бдитель
MERCHANT:      # Купец
MAGUS:         # Маг
```

---

## 13. РЕКОМЕНДАЦИИ ПО БАЛАНСУ

### 13.1 Соотношение HP к урону

```yaml
# Для обычного моба:
time_to_kill: 5-8 rounds  # Время убийства соло игроком того же уровня

# Формула:
# mob_hp = player_dps * 6 rounds
# mob_damage = player_hp * 0.1 per round
```

### 13.2 Опыт vs Сложность

```yaml
# Базовая формула опыта:
trash_mob:  level^2 * 10
elite_mob:  level^2 * 15
boss_mob:   level^2 * 30

# Примеры:
level_10_trash:  1000 exp
level_10_elite:  1500 exp
level_10_boss:   3000 exp

level_20_trash:  4000 exp
level_20_elite:  6000 exp
level_20_boss:   12000 exp
```

### 13.3 Золото и лут

```yaml
# Золото:
trash: level * 5 (±30%)
elite: level * 10 (±30%)
boss:  level * 25 (±30%)

# Шанс выпадения предметов:
common_item:    30-50%
uncommon_item:  15-25%
rare_item:      5-10%
epic_item:      1-3%
quest_item:     100% (для квестовых мобов)
```

---

## 14. ПРИМЕРЫ МОБОВ

### 14.1 Обычный моб (уровень 15)

```yaml
name: "Соляной голем"
level: 15
role: TRASH

stats:
  hp: 800
  str: 18
  dex: 8
  con: 20
  wis: 6
  int: 6
  cha: 3

combat:
  damage: "2d8+5"      # Средний урон: 14
  armor: 30
  hitroll: 3
  attacks_per_round: 1

behavior:
  aggressive: yes
  memory: yes
  sentinel: no

resistances:
  physical: 20
  fire: -20            # Уязвим к огню
  cold: 30
  poison: 100          # Иммунитет

loot:
  exp: 1200
  gold: [50, 150]
  items:
    - id: "salt_shard"
      chance: 40
```

### 14.2 Элитный моб (уровень 15)

```yaml
name: "Соляной страж"
level: 15
role: BOSS

stats:
  hp: 3000             # x3.75 от обычного
  str: 22
  dex: 12
  con: 24
  wis: 10
  int: 10
  cha: 5

combat:
  damage: "3d8+8"      # Средний урон: 21.5
  armor: 40
  hitroll: 5
  attacks_per_round: 2

special_attacks:
  - type: "bash"
    chance: 20
    cooldown: 4

  - type: "power_strike"
    chance: 15
    cooldown: 5

behavior:
  aggressive: yes
  memory: yes
  sentinel: yes

resistances:
  physical: 30
  fire: -25
  cold: 50
  poison: 100
  magic: 20

loot:
  exp: 4500           # x3 от обычного
  gold: [200, 500]    # x5 от обычного
  items:
    - id: "salt_sword"
      chance: 80
    - id: "guardian_core"
      chance: 60
```

---

## 15. ЧЕКЛИСТ ДЛЯ СОЗДАНИЯ МОБА

```yaml
required:
  - [ ] Имя (все 6 падежей)
  - [ ] Уровень (1-50)
  - [ ] Роль (trash/elite/boss)
  - [ ] Раса
  - [ ] HP (по формуле)
  - [ ] 6 характеристик (Str/Dex/Con/Wis/Int/Cha)
  - [ ] Урон (NdN+B)
  - [ ] Броня
  - [ ] Описания (short/long/examine)

behavior:
  - [ ] Флаги (aggressive, memory, etc)
  - [ ] Позиция по умолчанию
  - [ ] Спецспособности (если есть)

combat:
  - [ ] Тип атаки
  - [ ] Сопротивления
  - [ ] Иммунитеты

loot:
  - [ ] Опыт
  - [ ] Золото (min/max)
  - [ ] Предметы (id + chance)

optional:
  - [ ] Реплики (on_spawn/on_aggro/on_death)
  - [ ] Скрипты
```

---

**Конец справочника**

> Этот документ содержит все необходимые игровые механики для создания зон.
> При возникновении вопросов - сначала проверьте этот справочник.
> Обновляйте документ при обнаружении новых механик в движке.
