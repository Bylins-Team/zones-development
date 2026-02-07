"""
Утилиты для интерактивного взаимодействия с оператором
"""

import json
import yaml
import tempfile
import subprocess
import os
from typing import Dict, List, Any
from difflib import unified_diff


def user_approve(message: str) -> bool:
    """
    Запросить одобрение у оператора

    Args:
        message: Сообщение для отображения

    Returns:
        True если одобрено (y), False иначе
    """
    while True:
        response = input(f"\n{message} (y/n): ").lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            return True
        elif response in ['n', 'no', 'нет', 'н']:
            return False
        else:
            print("Пожалуйста, введите 'y' (да) или 'n' (нет)")


def user_choice(message: str, options: List[str]) -> str:
    """
    Выбор из списка опций

    Args:
        message: Сообщение для отображения
        options: Список опций

    Returns:
        Выбранная опция
    """
    print(f"\n{message}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")

    while True:
        try:
            choice_input = input("Выбор (номер): ").strip()
            choice = int(choice_input) - 1
            if 0 <= choice < len(options):
                return options[choice]
            else:
                print(f"Введите число от 1 до {len(options)}")
        except ValueError:
            print("Введите корректный номер")
        except KeyboardInterrupt:
            print("\nОтменено")
            return options[0]  # Вернуть первую опцию по умолчанию


def user_edit(data: Dict, editor: str = None) -> Dict:
    """
    Открыть редактор для правки JSON/YAML

    Args:
        data: Данные для редактирования
        editor: Редактор (по умолчанию $EDITOR или nano)

    Returns:
        Отредактированные данные
    """
    if editor is None:
        editor = os.environ.get('EDITOR', 'nano')

    # Определяем формат по типу данных
    is_yaml = isinstance(data, dict) and 'zone' in data

    # Сохраняем во временный файл
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml' if is_yaml else '.json',
        delete=False,
        encoding='utf-8'
    ) as f:
        if is_yaml:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)
        temp_file = f.name

    try:
        # Открываем редактор
        subprocess.run([editor, temp_file], check=True)

        # Загружаем обратно
        with open(temp_file, 'r', encoding='utf-8') as f:
            if is_yaml:
                return yaml.safe_load(f)
            else:
                return json.load(f)

    except subprocess.CalledProcessError:
        print(f"⚠️  Ошибка при запуске редактора {editor}")
        return data
    except Exception as e:
        print(f"⚠️  Ошибка при чтении файла: {e}")
        return data
    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_file)
        except:
            pass


def user_edit_yaml(yaml_str: str, editor: str = None) -> Dict:
    """
    Открыть редактор для правки YAML строки

    Args:
        yaml_str: YAML строка
        editor: Редактор

    Returns:
        Распарсенные данные
    """
    if editor is None:
        editor = os.environ.get('EDITOR', 'nano')

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(yaml_str)
        temp_file = f.name

    try:
        subprocess.run([editor, temp_file], check=True)

        with open(temp_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    finally:
        try:
            os.unlink(temp_file)
        except:
            pass


def user_edit_batch(items: List[Dict], editor: str = None) -> List[Dict]:
    """
    Редактирование списка элементов (batch комнат, мобов, etc)

    Args:
        items: Список элементов
        editor: Редактор

    Returns:
        Отредактированный список
    """
    return user_edit({'items': items}, editor).get('items', items)


def show_diff(before: str, after: str, label_before: str = "До", label_after: str = "После"):
    """
    Показать diff между двумя версиями

    Args:
        before: Старая версия
        after: Новая версия
        label_before: Метка для старой версии
        label_after: Метка для новой версии
    """
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)

    diff = unified_diff(
        before_lines,
        after_lines,
        fromfile=label_before,
        tofile=label_after,
        lineterm=''
    )

    # Цветной вывод если терминал поддерживает
    try:
        for line in diff:
            if line.startswith('+'):
                print(f"\033[92m{line}\033[0m", end='')  # Зеленый
            elif line.startswith('-'):
                print(f"\033[91m{line}\033[0m", end='')  # Красный
            elif line.startswith('@'):
                print(f"\033[96m{line}\033[0m", end='')  # Cyan
            else:
                print(line, end='')
    except:
        # Fallback без цветов
        for line in diff:
            print(line, end='')


def print_section(title: str, content: Any = None):
    """
    Красиво напечатать секцию

    Args:
        title: Заголовок секции
        content: Содержимое (опционально)
    """
    width = 60
    print("\n" + "=" * width)
    print(f" {title.upper()}")
    print("=" * width)

    if content is not None:
        if isinstance(content, dict):
            print(json.dumps(content, ensure_ascii=False, indent=2))
        elif isinstance(content, list):
            for item in content:
                print(f"  • {item}")
        else:
            print(content)
        print("-" * width)


def progress_bar(current: int, total: int, prefix: str = ""):
    """
    Простой progress bar

    Args:
        current: Текущее значение
        total: Общее значение
        prefix: Префикс для отображения
    """
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    percent = int(100 * current / total)

    print(f"\r{prefix} [{bar}] {percent}% ({current}/{total})", end='', flush=True)

    if current >= total:
        print()  # Новая строка в конце
