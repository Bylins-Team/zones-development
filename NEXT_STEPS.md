# Следующие шаги

## Что было сделано только что

✅ **Исследован движок** `~/repos/mud`
- Изучены все игровые механики
- Найдены формулы баланса
- Собраны все константы (флаги, типы, расы)

✅ **Создан справочник** `docs/game-mechanics.md`
- Все характеристики и модификаторы
- Флаги мобов, объектов, комнат
- Типы атак и урона
- Расы и роли мобов
- Формулы расчета HP, exp, gold, damage
- Константы и рекомендации

✅ **Обновлен формат** `docs/zone-format-v2.md`
- Добавлены роли мобов (BOSS, TRASH, etc)
- Добавлены расы из движка
- Обновлены формулы баланса
- Добавлены все флаги из движка

---

## Что нужно сделать СЕЙЧАС

### 1. Обновить пример зоны "Соляные копи" ⚠️ ПРИОРИТЕТ

Файл: `zones/draft/salt-mines-example.yaml`

**Текущие проблемы (оценка 66/100):**
- ❌ Неправильный баланс наград
- ❌ Нет ролей мобов
- ❌ Нет рас мобов
- ❌ Топология слишком линейна

**Что исправить:**

#### a) Добавить роли и расы мобам

```yaml
# Было:
mobiles:
  - id: "salt_golem"
    level: 13
    stats:
      hp: 800    # НЕПРАВИЛЬНО для lvl 13

# Должно быть:
mobiles:
  - id: "salt_golem"
    level: 13
    role: "TRASH"        # ← ДОБАВИТЬ
    race: "CONSTRUCT"    # ← ДОБАВИТЬ
    stats:
      hp: 800            # ОК для trash
```

#### b) Пересчитать опыт и золото

**Текущие значения:**
```yaml
salt_golem:     exp: 800   → ДОЛЖНО: 1690  (13^2 * 10)
salt_mummy:     exp: 500   → ДОЛЖНО: 1210  (11^2 * 10)
salt_spirit:    exp: 600   → ДОЛЖНО: 1440  (12^2 * 10)
salt_guardian:  exp: 2000  → ДОЛЖНО: 5070  (13^2 * 30 для BOSS)
salt_ooze:      exp: 400   → ДОЛЖНО: 1000  (10^2 * 10)

salt_golem:     gold: [50,150]   → ДОЛЖНО: [45,85]    (13*5 * 0.7-1.3)
salt_guardian:  gold: [200,500]  → ДОЛЖНО: [220,420]  (13*25 * 0.7-1.3 для BOSS)
```

#### c) Улучшить топологию

**Цель:** Снизить линейность с 75% до <50%

**Как:**
1. Добавить 2-3 комнаты с боковыми ответвлениями
2. Создать альтернативный путь к боссу
3. Добавить секретные проходы
4. Создать петлю (можно вернуться другим путем)

**Пример:**
```
Было:
[Вход] → [Коридор] → [Развилка] → [Зал статуй] → [Босс]
                          ↓
                     [Лагерь]

Должно быть:
                  ↗ [Пещера 1] → [Пещера 2] ↘
[Вход] → [Коридор] → [Развилка] → [Зал статуй] → [Босс]
                          ↓             ↓
                      [Лагерь] ← [Старые шахты]
                                      ↓
                                 [Секретная]
```

#### d) Добавить флаги из движка

```yaml
# Пример для голема
behavior:
  aggressive: true
  sentinel: false      # ← ДОБАВИТЬ все базовые флаги
  scavenger: false
  aware: true          # ← Нельзя backstab (голем из камня)
  memory: true
  helper: true
  wimpy: false
  stay_zone: true
  no_charm: true       # ← Конструкт нельзя очаровать
  no_sleep: true       # ← Конструкт не спит
  no_bash: false
  no_blind: true       # ← У конструкта нет глаз
```

### 2. Обновить валидатор ⚠️ ПРИОРИТЕТ

Файл: `tools/validator.py`

**Что обновить:**

#### a) Формулы опыта и золота

```python
# В функции _check_rewards()

# БЫЛО:
expected_exp = 10 * (mob_level ** 2) * 1.0

# ДОЛЖНО БЫТЬ:
role_mult = {
    'TRASH': 10,
    'BOSS': 30,
    'elite': 15  # для других ролей
}
expected_exp = (mob_level ** 2) * role_mult.get(mob.get('role', 'TRASH'), 10)

# БЫЛО:
expected_gold = 5 * mob_level

# ДОЛЖНО БЫТЬ:
role_gold_mult = {
    'TRASH': 5,
    'BOSS': 25,
    'elite': 10
}
expected_gold = mob_level * role_gold_mult.get(mob.get('role', 'TRASH'), 5)
```

#### b) Проверка ролей и рас

```python
# Добавить в _validate_structure()

VALID_ROLES = ['BOSS', 'TRASH', 'TANK', 'MELLEE_DMG', 'ARCHER',
               'ROGUE', 'MAGE_DMG', 'MAGE_BUFF', 'HEALER']

VALID_RACES = ['BASIC', 'HUMAN', 'BEASTMAN', 'BIRD', 'ANIMAL',
               'REPTILE', 'FISH', 'INSECT', 'PLANT', 'CONSTRUCT',
               'ZOMBIE', 'GHOST', 'BOGGART', 'SPIRIT', 'MAGIC_CREATURE']

for mob in zone.get('mobiles', []):
    role = mob.get('role')
    if not role:
        self.warnings.append(ValidationError(
            "warning", "Structure", f"Моб '{mob.get('id')}' без роли"
        ))
    elif role not in VALID_ROLES:
        self.errors.append(ValidationError(
            "error", "Structure", f"Неизвестная роль '{role}'"
        ))
```

#### c) Проверка диапазонов характеристик

```python
# В _validate_balance()

for mob in zone.get('mobiles', []):
    stats = mob.get('stats', {})

    for stat in ['strength', 'dexterity', 'constitution', 'wisdom', 'intelligence', 'charisma']:
        value = stats.get(stat, 10)
        if not (10 <= value <= 100):
            self.errors.append(ValidationError(
                "error", "Balance",
                f"Моб '{mob.get('id')}': {stat}={value} вне диапазона 10-100"
            ))
```

#### d) Исправить проверку стиля (ложное срабатывание на "кулак")

```python
# В _check_style()

# БЫЛО:
for word in anachronisms:
    if word in all_text:  # ← НЕПРАВИЛЬНО: находит "кул" в "кулак"

# ДОЛЖНО БЫТЬ:
import re
for word in anachronisms:
    pattern = r'\b' + re.escape(word) + r'\b'  # ← Только целые слова
    if re.search(pattern, all_text, re.IGNORECASE):
```

### 3. Протестировать обновления

```bash
# После обновления зоны и валидатора
python3 tools/validator.py zones/draft/salt-mines-example.yaml

# Цель: 90+ баллов
```

---

## Что делать ПОТОМ

### 4. Создать конвертер в формат движка

Файл: `tools/converter.py`

**Задача:** YAML → формат движка (.wld, .mob, .obj, .zon)

**Исследовать:**
- Формат .wld файлов (комнаты)
- Формат .mob файлов (мобы)
- Формат .obj файлов (объекты)
- Формат .zon файлов (команды зоны)

**Источник:** `~/repos/mud/lib/world/`

### 5. Создать новую зону

Выбрать из `zones/ideas/zone-ideas.md`:
1. **Покинутая пасека** (12-18 lvl) - хорошая для практики
2. **Свадебный пир-призрак** (8-12 lvl) - новичковая зона
3. **Птичий город** (20-25 lvl) - сложная архитектура

### 6. Дополнительные инструменты

- Визуализатор карт зон
- Калькулятор баланса
- Генератор заготовок

---

## Быстрый старт

```bash
# 1. Перейти в директорию проекта
cd /home/kvirund/repos/mud-zones-development

# 2. Прочитать справочник
cat docs/game-mechanics.md

# 3. Посмотреть новый формат
cat docs/zone-format-v2.md

# 4. Обновить зону "Соляные копи"
$EDITOR zones/draft/salt-mines-example.yaml

# 5. Проверить
python3 tools/validator.py zones/draft/salt-mines-example.yaml

# 6. Повторять шаги 4-5 до оценки 90+
```

---

## Приоритеты

1. ⚠️ **ВЫСОКИЙ** - Обновить salt-mines-example.yaml (роли, расы, баланс)
2. ⚠️ **ВЫСОКИЙ** - Обновить validator.py (формулы, флаги)
3. 🔵 **СРЕДНИЙ** - Исследовать формат .wld/.mob/.obj/.zon движка
4. 🔵 **СРЕДНИЙ** - Создать конвертер
5. 🟢 **НИЗКИЙ** - Создать новые зоны

---

## Справочные документы

- `docs/game-mechanics.md` - ВСЕ игровые механики из движка
- `docs/zone-format-v2.md` - Обновленный формат зон
- `docs/quality-metrics.md` - Система оценки
- `docs/zone-requirements.md` - Требования к зонам
- `CHANGELOG.md` - Что изменилось
- `TODO.md` - Детальный список задач
