"""
Refiner Agent - исправление ошибок в сгенерированной зоне
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

from ..llm import create_llm_client
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
        print(f"⚠️  Validator не найден: {validator_path}", flush=True)
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
        print(f"🐛 DEBUG: Validator return code: {result.returncode}", flush=True)
        print(f"🐛 DEBUG: Validator output length: {len(output)} chars", flush=True)
        if output:
            print(f"🐛 DEBUG: First 500 chars of output:\n{output[:500]}", flush=True)
        else:
            print(f"🐛 DEBUG: Validator returned EMPTY output!", flush=True)

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
    provider: str = "ollama",
    model: str = None,
    model_config: dict = None,
    max_iterations: int = 3,
    target_score: int = 75,
    ollama_url: str = "http://localhost:11434"  # Backward compatibility
) -> Path:
    """
    Агент для улучшения зоны через итеративное исправление ошибок

    Args:
        zone_file: Путь к YAML файлу зоны
        provider: Провайдер LLM ('ollama', 'openrouter', etc.)
        model: Модель для всех этапов (переопределяет model_config)
        model_config: Словарь stage -> model
        max_iterations: Максимум итераций улучшения
        target_score: Целевой балл валидации
        ollama_url: URL Ollama API (для обратной совместимости)

    Returns:
        Путь к улучшенному файлу
    """
    print(f"\n{'='*60}", flush=True)
    print(f"🔧 REFINER AGENT - Исправление ошибок зоны", flush=True)
    print(f"{'='*60}\n", flush=True)

    print(f"📂 Файл: {zone_file}", flush=True)
    print(f"🌐 Провайдер: {provider}", flush=True)
    if model:
        print(f"🤖 Модель: {model}", flush=True)

    # Проверяем что файл существует
    if not zone_file.exists():
        raise FileNotFoundError(f"Файл не найден: {zone_file}")

    # Загружаем исходный YAML
    with open(zone_file, 'r', encoding='utf-8') as f:
        current_yaml = f.read()

    print(f"✓ Загружено {len(current_yaml)} символов\n", flush=True)

    # Создаём LLM клиент через фабрику
    llm = create_llm_client(
        provider=provider,
        model=model,
        model_config=model_config,
        ollama_url=ollama_url
    )
    prompts = PromptLibrary()

    # Итеративное улучшение
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'─'*60}", flush=True)
        print(f"🔄 ИТЕРАЦИЯ {iteration}/{max_iterations}", flush=True)
        print(f"{'─'*60}\n", flush=True)

        # Сохраняем текущую версию во временный файл
        temp_file = zone_file.parent / f"{zone_file.stem}_temp.yaml"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(current_yaml)

        # Запускаем validator
        print("📊 Запуск validator...", flush=True)
        errors, warnings, score = run_validator(temp_file)

        print(f"\n✓ Валидация завершена:", flush=True)
        print(f"   Балл: {score}/100", flush=True)
        print(f"   Ошибок: {len(errors)}", flush=True)
        print(f"   Предупреждений: {len(warnings)}", flush=True)

        # Удаляем временный файл
        temp_file.unlink()

        # Проверяем достигли ли цели
        if score >= target_score and len(errors) == 0:
            print(f"\n✅ Целевой балл достигнут: {score} >= {target_score}", flush=True)
            print(f"✅ Ошибок нет", flush=True)
            break

        if len(errors) == 0 and len(warnings) == 0:
            print(f"\n✅ Ошибок и предупреждений нет", flush=True)
            print(f"   Балл: {score}/100", flush=True)
            break

        # Показываем ошибки
        if errors:
            print(f"\n❌ Критичные ошибки (первые 10):", flush=True)
            for err in errors[:10]:
                print(f"   {err}", flush=True)

        if warnings:
            print(f"\n⚠️  Предупреждения (первые 5):", flush=True)
            for warn in warnings[:5]:
                print(f"   {warn}", flush=True)

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
        print(f"\n🤖 Генерация исправлений...", flush=True)
        response = llm.generate(
            prompt=prompt,
            stage='refiner',
            system=prompts.SYSTEM_DESIGNER,
            timeout=300  # 5 минут на большие зоны
        )

        # Извлекаем YAML из ответа
        refined_yaml = extract_code_block(response['content'], 'yaml')

        if not refined_yaml:
            print(f"\n⚠️  LLM не вернул валидный YAML, используем оригинал", flush=True)
            break

        # Проверяем что YAML парсится
        parsed = safe_parse_yaml(refined_yaml)
        if parsed is None:
            print(f"\n⚠️  Исправленный YAML не парсится, используем оригинал", flush=True)
            break

        # КРИТИЧНО: Проверяем что структура сохранена
        if not isinstance(parsed, dict) or 'zone' not in parsed:
            print(f"\n⚠️  LLM вернул невалидную структуру (нет корневого 'zone'), используем оригинал", flush=True)
            print(f"      Ключи в ответе: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}", flush=True)
            break

        # Проверяем обязательные секции
        zone_data = parsed.get('zone', {})
        required_sections = ['meta', 'rooms']  # Минимально необходимые
        missing_sections = [s for s in required_sections if s not in zone_data]

        if missing_sections:
            print(f"\n⚠️  LLM вернул неполную структуру, отсутствуют секции: {missing_sections}", flush=True)
            print(f"      Используем оригинал", flush=True)
            break

        # Обновляем текущую версию
        current_yaml = refined_yaml
        print(f"✓ Исправления применены ({len(refined_yaml)} символов)", flush=True)

    # Сохраняем улучшенную версию
    output_file = zone_file.parent / f"{zone_file.stem}_refined.yaml"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(current_yaml)

    print(f"\n{'='*60}", flush=True)
    print(f"✅ Улучшенная зона сохранена: {output_file}", flush=True)
    print(f"{'='*60}\n", flush=True)

    # Финальная валидация
    print("📊 Финальная валидация...", flush=True)
    errors, warnings, score = run_validator(output_file)

    print(f"\n📈 РЕЗУЛЬТАТ:", flush=True)
    print(f"   Балл: {score}/100", flush=True)
    print(f"   Ошибок: {len(errors)}", flush=True)
    print(f"   Предупреждений: {len(warnings)}", flush=True)

    if score >= target_score:
        print(f"\n🎉 Целевой балл достигнут!", flush=True)
    else:
        print(f"\n⚠️  Целевой балл не достигнут ({score} < {target_score})", flush=True)
        print(f"   Возможно нужно ещё улучшение или ручная правка", flush=True)

    return output_file
