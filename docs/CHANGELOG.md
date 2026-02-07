# Changelog - Изменения в проекте

## [2026-02-06] - Исследование движка

### Добавлено
- **docs/game-mechanics.md** - Полный справочник игровых механик из движка
  - Все характеристики и их модификаторы
  - Система уровней и формулы расчета
  - Все флаги мобов, объектов, комнат
  - Типы атак и урона
  - Расы и роли мобов
  - Формулы баланса (HP, mana, damage, exp, gold)
  - Константы и рекомендации

### Изменения в формате зон

#### Характеристики мобов
- **Было**: Произвольные значения
- **Стало**: Диапазон 10-100 для мобов (10-50 с ограничениями)

#### Флаги мобов
Добавлены из движка:
- `SPEC` - специальная процедура
- `SENTINEL` - не двигается
- `SCAVENGER` - подбирает предметы
- `AWARE` - нельзя backstab
- `AGGRESSIVE` - атакует
- `STAY_ZONE` - не покидает зону
- `WIMPY` - убегает при ранении
- `MEMORY` - помнит атакующих
- `HELPER` - помогает NPC
- `AGGRESSIVE_DAY` / `AGGRESSIVE_NIGHT` - агрессия по времени суток
- `NO_CHARM` / `NO_SUMMON` / `NO_SLEEP` / `NO_BASH` / `NO_BLIND` - иммунитеты
- `FIRE_BREATH` / `GAS_BREATH` / `FROST_BREATH` / `ACID_BREATH` / `LIGHTING_BREATH` - дыхания

#### Роли мобов
Добавлены:
- `BOSS` - босс (HP x3, exp x3, gold x5)
- `TRASH` - обычный моб
- `TANK` - танк (HP x2, damage x0.7)
- `MELLEE_DMG` - ближний боец (damage x1.4)
- `ARCHER` - лучник
- `ROGUE` - разбойник
- `MAGE_DMG` - маг-урон (HP x0.6, damage x2)
- `MAGE_BUFF` - маг-поддержка
- `HEALER` - целитель

#### Расы мобов
Добавлены все расы из движка:
- BASIC (100), HUMAN (101), BEASTMAN (102), BIRD (103), ANIMAL (104)
- REPTILE (105), FISH (106), INSECT (107), PLANT (108)
- CONSTRUCT (109) - голем, автомат
- ZOMBIE (110), GHOST (111), BOGGART (112), SPIRIT (113)
- MAGIC_CREATURE (114)

#### Типы атак
Полный список из движка (17 типов):
- type_hit, type_slash, type_bite, type_claw, type_pierce, и т.д.

#### Типы урона
- `UNDEF_DMG` - неопределенный
- `PHYS_DMG` - физический
- `MAGIC_DMG` - магический
- `POISON_DMG` - яд
- `PURE_DMG` - чистый урон

#### Флаги атаки
- `IGNORE_SANCT`, `IGNORE_PRISM`, `IGNORE_ARMOR`, `HALF_IGNORE_ARMOR`
- `IGNORE_ABSORBE`, `CRIT_HIT`, `CRIT_LUCK`
- `MAGIC_REFLECT`
- `VICTIM_FIRE_SHIELD`, `VICTIM_AIR_SHIELD`, `VICTIM_ICE_SHIELD`

#### Сопротивления
Диапазон: -100 до +75 (для PC макс 75)
- FIRE, AIR, WATER, EARTH, VITALITY, MIND, IMMUNITY, DARK

#### Флаги комнат
Добавлены:
- `DARKED` - темно (нужен свет)
- `DEATH_TRAP` - смертельная ловушка
- `INDOORS` - в помещении
- `PEACEFUL` - нельзя драться
- `SOUNDPROOF` - звукоизоляция
- `NO_TRACK`, `NO_MAGIC`, `TUNNEL`
- `NO_TELEPORT_IN`, `NO_RECALL`, `NO_SUMMON`
- `GODS_ROOM`, `ARENA`
- `SLOW_REGEN`, `FAST_REGEN`
- `ICE` - скользко

#### Секторы (типы местности)
- INSIDE, CITY, FIELD, FOREST, HILLS, MOUNTAIN
- WATER_SWIM, WATER_NOSWIM, UNDERWATER
- FLYING, SECRET, ROAD
- THICK_ICE, NORMAL_ICE, THIN_ICE

#### Типы объектов
Полный список (31 тип):
- LIGHT_SOURCE, SCROLL, WAND, STAFF, WEAPON, ARMOR, POTION
- CONTAINER, KEY, FOOD, MONEY, BOOK
- INGREDIENT, MAGIC_INGREDIENT, CRAFT_MATERIAL
- LIGHT_ARMOR, MEDIUM_ARMOR, HEAVY_ARMOR
- И другие...

#### Материалы объектов
- BULAT, BRONZE, IRON, STEEL, FORGED_STEEL, PRECIOUS_METEL
- CRYSTAL, WOOD, HARD_WOOD, CERAMIC, GLASS, STONE
- BONE, CLOTH, SKIN, ORGANIC, PAPER, DIAMOND

#### Флаги объектов
- GLOW, HUM, MAGIC, BLESS
- NORENT, NODONATE, NOSELL, NODROP
- DECAY, POISONED, SHARPEN, FIRE
- TWO_HANDS, ARMORED, BLOODY

### Формулы баланса

#### Обновлены формулы для мобов:
```python
# HP по уровням (обычный моб)
level_1-5:   50-150
level_6-10:  200-400
level_11-15: 500-1000
level_16-20: 1200-2000
level_21-25: 2500-3500
level_26-30: 4000-5500
level_31-40: 6000-9000
level_41-50: 10000-15000

# Опыт:
trash: level^2 * 10
elite: level^2 * 15
boss:  level^2 * 30

# Золото:
trash: level * 5 (±30%)
elite: level * 10 (±30%)
boss:  level * 25 (±30%)
```

### Что нужно обновить

1. **zones/draft/salt-mines-example.yaml**
   - Пересчитать HP мобов по новым формулам
   - Пересчитать опыт и золото
   - Добавить роли мобов (BOSS, TRASH, etc)
   - Добавить расы мобов
   - Обновить флаги

2. **tools/validator.py**
   - Использовать правильные формулы из game-mechanics.md
   - Проверять валидные значения флагов
   - Проверять диапазоны характеристик (10-100)
   - Проверять корректность ролей и рас

3. **docs/zone-format.md**
   - Обновить примеры с учетом новых полей
   - Добавить секцию о ролях и расах
   - Добавить ссылки на game-mechanics.md

## [2026-02-06] - Инициализация проекта

### Добавлено
- Структура проекта (zones/, docs/, tools/)
- README.md - описание проекта
- docs/zone-requirements.md - требования к зонам
- docs/quality-metrics.md - система оценки 100 баллов
- docs/zone-format.md - формат YAML
- tools/validator.py - автоматический валидатор (~50% проверок)
- zones/ideas/zone-ideas.md - 10 концептов зон
- zones/draft/salt-mines-example.yaml - пример зоны
- .gitignore
- TODO.md
- SUMMARY.md
