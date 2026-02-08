"""
YAML утилиты для работы с зонами
"""

import re
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def extract_code_block(text: str, language: str = 'yaml') -> str:
    """
    Извлечь код из markdown блока

    Args:
        text: Текст с markdown
        language: Язык блока (yaml, json, etc)

    Returns:
        Извлеченный код
    """
    # Простой подход через строковые операции (надёжнее regex)
    markers = [f'```{language}', '```']

    for marker in markers:
        if marker in text:
            # Находим начало блока
            start_idx = text.find(marker)
            if start_idx == -1:
                continue

            # Пропускаем маркер
            content_start = start_idx + len(marker)

            # Пропускаем все whitespace (пробелы, табы, переносы строк)
            while content_start < len(text) and text[content_start] in ' \t\r\n':
                content_start += 1

            # Находим закрывающие ```
            end_idx = text.find('```', content_start)
            if end_idx == -1:
                continue

            # Извлекаем контент
            content = text[content_start:end_idx].strip()
            if content:
                # DEBUG
                if content.startswith('```'):
                    print(f"🐛 DEBUG extract_code_block: Контент всё ещё начинается с ``` !")
                    print(f"🐛 DEBUG: marker={marker}, start_idx={start_idx}, content_start={content_start}, end_idx={end_idx}")
                    print(f"🐛 DEBUG: Первые 100 символов: {text[:100]}")
                return content

    # Если блока нет, возвращаем как есть
    result = text.strip()
    if result.startswith('```'):
        print(f"🐛 DEBUG extract_code_block: Блок не найден, возвращаем как есть, но начинается с ```!")
        print(f"🐛 DEBUG: language={language}, text length={len(text)}")
        print(f"🐛 DEBUG: Первые 100 символов: {text[:100]}")
    return result


def safe_parse_yaml(text: str, retry_count: int = 2, stage: str = "unknown") -> Dict:
    """
    Безопасный парсинг YAML с retry при ошибках

    Args:
        text: YAML текст
        retry_count: Количество попыток
        stage: Этап генерации (для отладки)

    Returns:
        Распарсенные данные

    Raises:
        yaml.YAMLError: Если все попытки провалились (с детальной информацией)
    """
    # Извлекаем YAML из markdown если есть
    yaml_text = extract_code_block(text, 'yaml')

    for attempt in range(retry_count):
        try:
            return yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            if attempt < retry_count - 1:
                print(f"⚠️  YAML ошибка (попытка {attempt + 1}/{retry_count}): {e}")
                # Пытаемся базово исправить
                yaml_text = yaml_text.replace('\t', '  ')  # Табы → пробелы
            else:
                # Сохраняем полный вывод модели для отладки
                import tempfile
                import datetime

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = Path(tempfile.gettempdir()) / f"llm_yaml_error_{stage}_{timestamp}.yaml"
                debug_file.write_text(text, encoding='utf-8')

                # Пытаемся показать контекст ошибки
                error_str = str(e)
                lines = yaml_text.split('\n')

                # Извлекаем номер строки из ошибки
                import re
                line_match = re.search(r'line (\d+)', error_str)
                error_line = int(line_match.group(1)) - 1 if line_match else 0

                # Показываем контекст (±5 строк)
                context_start = max(0, error_line - 5)
                context_end = min(len(lines), error_line + 5)
                context = '\n'.join(f"{'>' if i == error_line else ' '} {i+1:3}: {lines[i]}" for i in range(context_start, context_end))

                # Детальное сообщение об ошибке
                error_message = f"""
╔══════════════════════════════════════════════════════════════╗
║  ❌ ОШИБКА ПАРСИНГА YAML ОТ LLM                              ║
╚══════════════════════════════════════════════════════════════╝

Этап: {stage}
Ошибка: {e}

Контекст (строки {context_start+1}-{context_end}):
{context}

📄 Полный вывод модели сохранён в:
   {debug_file}

💡 КАК ИСПРАВИТЬ:

1. RETRY С ДРУГОЙ МОДЕЛЬЮ:
   Если используете Ollama, попробуйте более мощную модель:
   --provider anthropic    # Claude (платно, но надёжнее)
   --provider openai       # ChatGPT (платно)

2. РУЧНАЯ ПРАВКА YAML:
   Откройте файл: {debug_file}
   Исправьте YAML синтаксис
   Скопируйте исправленный контент в нужный файл

3. ПРОДОЛЖИТЬ С CHECKPOINT (--resume):
   Генерация сохранена в checkpoint. Чтобы продолжить:

   a) Найдите Thread ID в выводе выше (зона_20XXXXXX_XXXXXXXX)
   b) Запустите с теми же параметрами + --resume:

      python -m tools.generator.main \\
        --resume zone_20XXXXXX_XXXXXXXX \\
        --provider anthropic  # Можно сменить провайдер!

   ⚠️  С --resume восстанавливается:
       - Весь прогресс (idea, lore, structure, rooms, mobs...)
       - НО НЕ восстанавливается provider/модель!
       - Нужно явно указать --provider если хотите другой

4. ИЗМЕНИТЬ ТЕМПЕРАТУРУ/МОДЕЛЬ:
   В config.py → TEMPERATURE_CONFIG['{stage}']
   Уменьшите температуру для более строгого следования формату

5. ПРОВЕРИТЬ ПРОМПТ:
   prompts/library.py → get_{stage}_prompt()
   Возможно нужно уточнить YAML схему в промпте
"""
                raise yaml.YAMLError(error_message) from e

    return {}


def safe_parse_json(text: str) -> Dict:
    """
    Безопасный парсинг JSON

    Args:
        text: JSON текст

    Returns:
        Распарсенные данные

    Raises:
        ValueError: Если текст пустой или парсинг провалился
    """
    if not text or not text.strip():
        raise ValueError("LLM вернул пустой ответ")

    # Извлекаем JSON из markdown если есть
    json_text = extract_code_block(text, 'json')

    # Удаляем комментарии // (LLM часто их добавляет, но JSON не поддерживает)
    json_text = re.sub(r'//.*?$', '', json_text, flags=re.MULTILINE)

    # Удаляем trailing commas (запятые перед ] или })
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

    # Пытаемся починить частые ошибки LLM перед парсингом
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as first_error:
        # Попытка 1: Если ошибка "Expecting ',' delimiter", это обычно означает
        # что объект не закрыт перед ] или }
        error_msg = str(first_error)
        if "Expecting ',' delimiter" in error_msg or "Expecting ':' delimiter" in error_msg:
            # Пробуем добавить } перед каждым ] в JSON
            repaired = json_text
            # Ищем паттерн: "..." \n  ] (строка заканчивается, потом идёт ])
            # и вставляем } перед ]
            repaired = re.sub(r'("\s*)(\n\s*])', r'\1}\2', repaired)

            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

        # Попытка 2: Закрываем все незакрытые скобки в конце
        open_braces = json_text.count('{') - json_text.count('}')
        open_brackets = json_text.count('[') - json_text.count(']')

        repair_suffix = ''
        for _ in range(open_braces):
            repair_suffix += '\n}'
        for _ in range(open_brackets):
            repair_suffix += '\n]'

        if repair_suffix:
            try:
                return json.loads(json_text + repair_suffix)
            except json.JSONDecodeError:
                pass

        # Если все repair попытки не помогли, выбрасываем оригинальную ошибку
        raise first_error from None
    except json.JSONDecodeError as e:
        # Пытаемся с другим форматом
        try:
            json_text = extract_code_block(text, 'javascript')
            return json.loads(json_text)
        except json.JSONDecodeError:
            # Сохраняем полный ответ в файл для отладки
            import tempfile
            debug_file = Path(tempfile.gettempdir()) / "llm_response_debug.txt"
            debug_file.write_text(text, encoding='utf-8')

            # Показываем область с ошибкой
            lines = json_text.split('\n')
            error_line = e.lineno - 1 if e.lineno else 0
            context_start = max(0, error_line - 3)
            context_end = min(len(lines), error_line + 3)
            context = '\n'.join(f"{i+1:3}: {lines[i]}" for i in range(context_start, context_end))

            raise ValueError(
                f"Не удалось распарсить JSON от LLM.\n"
                f"Ошибка: {e}\n"
                f"Контекст (строки {context_start+1}-{context_end}):\n{context}\n\n"
                f"Полный ответ сохранён в: {debug_file}"
            )


def assemble_zone_yaml(state: Dict) -> str:
    """
    Собрать state в финальный YAML зоны

    Args:
        state: State генерации (idea, lore, rooms, mobs, etc)

    Returns:
        YAML строка
    """
    idea = state.get('idea', {})
    lore = state.get('lore', {})
    rooms = state.get('rooms', [])
    mobiles = state.get('mobiles', [])
    objects = state.get('objects', [])
    quests = state.get('quests', [])

    zone = {
        'zone': {
            'meta': {
                'id': idea.get('id', 'unknown'),
                'name': idea.get('name', 'Новая зона'),
                'author': idea.get('author', 'Zone Generator'),
                'version': '1.0',
                'description': idea.get('description', ''),
                'recommended_level': idea.get('level_range', [1, 10])
            },
            'lore': lore,
            'rooms': rooms,
            'mobiles': mobiles,
            'objects': objects,
            'quests': quests
        }
    }

    return yaml.dump(zone, allow_unicode=True, sort_keys=False, default_flow_style=False)


def sanitize_filename(name: str) -> str:
    """
    Очистить имя файла от недопустимых символов

    Args:
        name: Имя файла

    Returns:
        Очищенное имя
    """
    # Заменяем пробелы на подчеркивания
    name = name.replace(' ', '_')

    # Удаляем недопустимые символы
    name = re.sub(r'[^\w\-.]', '', name)

    # Lowercase
    name = name.lower()

    return name


def validate_yaml_structure(data: Dict) -> tuple[bool, Optional[str]]:
    """
    Проверка базовой структуры YAML зоны

    Args:
        data: Распарсенные данные

    Returns:
        (валидна, сообщение об ошибке)
    """
    if not isinstance(data, dict):
        return False, "Данные должны быть словарем"

    if 'zone' not in data:
        return False, "Отсутствует корневая секция 'zone'"

    zone = data['zone']

    if 'meta' not in zone:
        return False, "Отсутствует секция 'meta'"

    meta = zone['meta']
    required_meta = ['id', 'name', 'author', 'version']

    for field in required_meta:
        if field not in meta:
            return False, f"Отсутствует обязательное поле 'meta.{field}'"

    return True, None


def merge_yaml_files(base_file: Path, updates: Dict) -> str:
    """
    Слияние обновлений в существующий YAML

    Args:
        base_file: Путь к базовому файлу
        updates: Обновления для применения

    Returns:
        Обновленный YAML
    """
    with open(base_file, 'r', encoding='utf-8') as f:
        base_data = yaml.safe_load(f)

    # Рекурсивное слияние
    def merge_dicts(base, updates):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                merge_dicts(base[key], value)
            else:
                base[key] = value

    merge_dicts(base_data, updates)

    return yaml.dump(base_data, allow_unicode=True, sort_keys=False, default_flow_style=False)


def count_elements(zone_yaml: str) -> Dict[str, int]:
    """
    Подсчет элементов в зоне

    Args:
        zone_yaml: YAML зоны

    Returns:
        Словарь с количествами (rooms, mobiles, objects, quests)
    """
    try:
        data = yaml.safe_load(zone_yaml)
        zone = data.get('zone', {})

        return {
            'rooms': len(zone.get('rooms', [])),
            'mobiles': len(zone.get('mobiles', [])),
            'objects': len(zone.get('objects', [])),
            'quests': len(zone.get('quests', []))
        }
    except:
        return {'rooms': 0, 'mobiles': 0, 'objects': 0, 'quests': 0}
