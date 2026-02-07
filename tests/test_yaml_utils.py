"""
Тесты для YAML утилит
"""

import sys
from pathlib import Path

# Добавляем путь к tools
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from generator.utils import (
    extract_code_block,
    safe_parse_yaml,
    safe_parse_json,
    sanitize_filename,
    validate_yaml_structure
)


def test_extract_code_block():
    """Тест извлечения кода из markdown"""
    # YAML блок
    text = """
    Вот YAML:
    ```yaml
    zone:
      meta:
        id: test
    ```
    """
    result = extract_code_block(text, 'yaml')
    assert 'zone:' in result
    assert 'id: test' in result

    # JSON блок
    text2 = """
    ```json
    {"key": "value"}
    ```
    """
    result2 = extract_code_block(text2, 'json')
    assert '"key"' in result2

    print("✓ test_extract_code_block passed")


def test_safe_parse_yaml():
    """Тест безопасного парсинга YAML"""
    # Простой YAML
    yaml_str = """
zone:
  meta:
    id: test_zone
    name: "Тестовая зона"
"""
    result = safe_parse_yaml(yaml_str)
    assert result['zone']['meta']['id'] == 'test_zone'
    assert result['zone']['meta']['name'] == 'Тестовая зона'

    # YAML в markdown блоке
    yaml_md = """
    ```yaml
    zone:
      meta:
        id: test2
    ```
    """
    result2 = safe_parse_yaml(yaml_md)
    assert result2['zone']['meta']['id'] == 'test2'

    print("✓ test_safe_parse_yaml passed")


def test_safe_parse_json():
    """Тест безопасного парсинга JSON"""
    # Простой JSON
    json_str = '{"id": "zone_001", "name": "Test Zone"}'
    result = safe_parse_json(json_str)
    assert result['id'] == 'zone_001'
    assert result['name'] == 'Test Zone'

    # JSON в markdown
    json_md = """
    ```json
    {"level": 13, "role": "TRASH"}
    ```
    """
    result2 = safe_parse_json(json_md)
    assert result2['level'] == 13
    assert result2['role'] == 'TRASH'

    print("✓ test_safe_parse_json passed")


def test_sanitize_filename():
    """Тест очистки имени файла"""
    # Пробелы → подчеркивания
    assert sanitize_filename("Соляные копи") == "соляные_копи"

    # Недопустимые символы удаляются
    assert sanitize_filename("Зона#123/test") == "зона123test"

    # Lowercase
    assert sanitize_filename("ТЕСТ") == "тест"

    print("✓ test_sanitize_filename passed")


def test_validate_yaml_structure():
    """Тест валидации структуры YAML"""
    # Валидная структура
    valid_data = {
        'zone': {
            'meta': {
                'id': 'test',
                'name': 'Test',
                'author': 'Tester',
                'version': '1.0'
            }
        }
    }
    is_valid, error = validate_yaml_structure(valid_data)
    assert is_valid
    assert error is None

    # Отсутствует 'zone'
    invalid1 = {'meta': {}}
    is_valid, error = validate_yaml_structure(invalid1)
    assert not is_valid
    assert 'zone' in error

    # Отсутствует 'meta'
    invalid2 = {'zone': {}}
    is_valid, error = validate_yaml_structure(invalid2)
    assert not is_valid
    assert 'meta' in error

    # Отсутствует обязательное поле
    invalid3 = {'zone': {'meta': {'id': 'test'}}}
    is_valid, error = validate_yaml_structure(invalid3)
    assert not is_valid
    assert 'name' in error

    print("✓ test_validate_yaml_structure passed")


def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "="*50)
    print("YAML UTILS TESTS")
    print("="*50 + "\n")

    test_extract_code_block()
    test_safe_parse_yaml()
    test_safe_parse_json()
    test_sanitize_filename()
    test_validate_yaml_structure()

    print("\n" + "="*50)
    print("✅ Все тесты пройдены!")
    print("="*50 + "\n")


if __name__ == '__main__':
    run_all_tests()
