"""
Refiner Agent - исправление ошибок в сгенерированной зоне
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

from ..llm import OllamaClient
from ..prompts import PromptLibrary
from ..utils import safe_parse_yaml, extract_code_block


def run_validator(zone_file: Path) -> Tuple[List[str], List[str], int]:
    """
    Запуск validator.py для зоны

    Args:
        zone_file: Путь к YAML файлу зоны

    Returns:
        (errors, warnings, score)
    """
    validator_path = Path(__file__).parent.parent.parent / "validator.py"

    if not validator_path.exists():
        print(f"⚠️  Validator не найден: {validator_path}")
        return ([], ["Validator не найден"], 0)

    try:
        # Запускаем validator (UTF-8 для Windows)
        # Timeout 180s для LLM оценки (может быть долгой)
        result = subprocess.run(
            [sys.executable, str(validator_path), str(zone_file)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=180
        )

        output = result.stdout + result.stderr

        # DEBUG: Показываем что вернул validator
        print(f"🐛 DEBUG: Validator return code: {result.returncode}")
        print(f"🐛 DEBUG: Validator output length: {len(output)} chars")
        if output:
            print(f"🐛 DEBUG: First 500 chars of output:\n{output[:500]}")
        else:
            print(f"🐛 DEBUG: Validator returned EMPTY output!")

        # Парсим вывод validator
        errors = []
        warnings = []
        score = 0

        lines = output.split('\n')
        for line in lines:
            # Ищем score (проверяем все возможные форматы)
            if 'ОЦЕНКА:' in line or 'Общий балл:' in line or 'Score:' in line:
                try:
                    # Формат: "ОЦЕНКА: 73/100 баллов" или "Score: 73/100"
                    score_str = line.split(':')[-1].strip().split('/')[0].strip()
                    score = int(score_str)
                except:
                    pass

            # Собираем ошибки
            if '❌' in line or 'ERROR' in line or 'Ошибка:' in line:
                errors.append(line.strip())
            elif '⚠️' in line or 'WARNING' in line or 'Предупреждение:' in line:
                warnings.append(line.strip())

        return (errors, warnings, score)

    except subprocess.TimeoutExpired:
        return (["Validator timeout"], [], 0)
    except Exception as e:
        return ([f"Ошибка запуска validator: {e}"], [], 0)


def refiner_agent(
    zone_file: Path,
    ollama_url: str = "http://localhost:11434",
    max_iterations: int = 3,
    target_score: int = 75
) -> Path:
    """
    Агент для улучшения зоны через итеративное исправление ошибок

    Args:
        zone_file: Путь к YAML файлу зоны
        ollama_url: URL Ollama API
        max_iterations: Максимум итераций улучшения
        target_score: Целевой балл валидации

    Returns:
        Путь к улучшенному файлу
    """
    print(f"\n{'='*60}")
    print(f"🔧 REFINER AGENT - Исправление ошибок зоны")
    print(f"{'='*60}\n")

    print(f"📂 Файл: {zone_file}")

    # Проверяем что файл существует
    if not zone_file.exists():
        raise FileNotFoundError(f"Файл не найден: {zone_file}")

    # Загружаем исходный YAML
    with open(zone_file, 'r', encoding='utf-8') as f:
        current_yaml = f.read()

    print(f"✓ Загружено {len(current_yaml)} символов\n")

    ollama = OllamaClient(ollama_url=ollama_url)
    prompts = PromptLibrary()

    # Итеративное улучшение
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'─'*60}")
        print(f"🔄 ИТЕРАЦИЯ {iteration}/{max_iterations}")
        print(f"{'─'*60}\n")

        # Сохраняем текущую версию во временный файл
        temp_file = zone_file.parent / f"{zone_file.stem}_temp.yaml"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(current_yaml)

        # Запускаем validator
        print("📊 Запуск validator...")
        errors, warnings, score = run_validator(temp_file)

        print(f"\n✓ Валидация завершена:")
        print(f"   Балл: {score}/100")
        print(f"   Ошибок: {len(errors)}")
        print(f"   Предупреждений: {len(warnings)}")

        # Удаляем временный файл
        temp_file.unlink()

        # Проверяем достигли ли цели
        if score >= target_score and len(errors) == 0:
            print(f"\n✅ Целевой балл достигнут: {score} >= {target_score}")
            print(f"✅ Ошибок нет")
            break

        if len(errors) == 0 and len(warnings) == 0:
            print(f"\n✅ Ошибок и предупреждений нет")
            print(f"   Балл: {score}/100")
            break

        # Показываем ошибки
        if errors:
            print(f"\n❌ Критичные ошибки (первые 10):")
            for err in errors[:10]:
                print(f"   {err}")

        if warnings:
            print(f"\n⚠️  Предупреждения (первые 5):")
            for warn in warnings[:5]:
                print(f"   {warn}")

        # Формируем feedback для LLM
        if score < 60:
            llm_feedback = "Качество низкое. Улучши описания, добавь детали атмосферы."
        elif score < 75:
            llm_feedback = "Качество среднее. Добавь больше сенсорных деталей и атмосферы."
        else:
            llm_feedback = "Качество хорошее. Просто исправь технические ошибки."

        # Генерируем промпт для исправления
        prompt = prompts.get_refiner_prompt(
            zone_yaml=current_yaml,
            validation_errors=errors,
            validation_warnings=warnings,
            llm_feedback=llm_feedback,
            iteration=iteration
        )

        # Вызываем LLM
        print(f"\n🤖 Генерация исправлений...")
        response = ollama.generate(
            prompt=prompt,
            stage='refiner',
            system=prompts.SYSTEM_DESIGNER,
            timeout=300  # 5 минут на большие зоны
        )

        # Извлекаем YAML из ответа
        refined_yaml = extract_code_block(response['content'], 'yaml')

        if not refined_yaml:
            print(f"\n⚠️  LLM не вернул валидный YAML, используем оригинал")
            break

        # Проверяем что YAML парсится
        parsed = safe_parse_yaml(refined_yaml)
        if parsed is None:
            print(f"\n⚠️  Исправленный YAML не парсится, используем оригинал")
            break

        # Обновляем текущую версию
        current_yaml = refined_yaml
        print(f"✓ Исправления применены ({len(refined_yaml)} символов)")

    # Сохраняем улучшенную версию
    output_file = zone_file.parent / f"{zone_file.stem}_refined.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(current_yaml)

    print(f"\n{'='*60}")
    print(f"✅ Улучшенная зона сохранена: {output_file}")
    print(f"{'='*60}\n")

    # Финальная валидация
    print("📊 Финальная валидация...")
    errors, warnings, score = run_validator(output_file)

    print(f"\n📈 РЕЗУЛЬТАТ:")
    print(f"   Балл: {score}/100")
    print(f"   Ошибок: {len(errors)}")
    print(f"   Предупреждений: {len(warnings)}")

    if score >= target_score:
        print(f"\n🎉 Целевой балл достигнут!")
    else:
        print(f"\n⚠️  Целевой балл не достигнут ({score} < {target_score})")
        print(f"   Возможно нужно ещё улучшение или ручная правка")

    return output_file
