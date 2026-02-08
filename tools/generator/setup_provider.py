#!/usr/bin/env python3
"""
Setup Provider - настройка API ключей для LLM провайдеров

Использование:
    python -m tools.generator.setup_provider openrouter --api-key sk-xxx
    python -m tools.generator.setup_provider anthropic  # Интерактивно
"""

import argparse
import os
import sys
from pathlib import Path


# Маппинг провайдеров на env переменные
PROVIDER_ENV_MAP = {
    'ollama': None,  # Не требует ключа
    'anthropic': 'ANTHROPIC_API_KEY',
    'openai': 'OPENAI_API_KEY',
    'deepseek': 'DEEPSEEK_API_KEY',
    'xai': 'XAI_API_KEY',
    'cerebras': 'CEREBRAS_API_KEY',
    'kilo': 'KILO_API_KEY',
    'openrouter': 'OPENROUTER_API_KEY',
}

# Провайдеры с настраиваемым base URL
PROVIDERS_WITH_BASE_URL = {
    'ollama': 'OLLAMA_BASE_URL',
    'kilo': 'KILO_BASE_URL',
}


def get_env_file_path() -> Path:
    """Получить путь к .env файлу (в корне проекта)"""
    # Ищем корень проекта (где есть .git или README.md)
    current = Path(__file__).parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'README.md').exists():
            return current / '.env'
        current = current.parent

    # Fallback - рядом с setup_provider.py
    return Path(__file__).parent.parent.parent / '.env'


def read_env_file(env_file: Path) -> dict:
    """
    Прочитать .env файл и вернуть словарь ключ=значение

    Returns:
        dict: {key: value, ...}
    """
    env_dict = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if not line or line.startswith('#'):
                    continue
                # Парсим KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()
    return env_dict


def write_env_file(env_file: Path, env_dict: dict):
    """
    Записать env_dict в .env файл

    Args:
        env_file: Путь к файлу
        env_dict: Словарь переменных
    """
    # Группируем переменные по провайдерам для читаемости
    lines = []
    lines.append("# LLM Provider API Keys\n")
    lines.append("# Создано автоматически через setup_provider.py\n\n")

    # Группы провайдеров
    provider_groups = {
        'ollama': ['OLLAMA_BASE_URL', 'OLLAMA_DEFAULT_MODEL'],
        'anthropic': ['ANTHROPIC_API_KEY', 'ANTHROPIC_DEFAULT_MODEL'],
        'openai': ['OPENAI_API_KEY', 'OPENAI_DEFAULT_MODEL'],
        'deepseek': ['DEEPSEEK_API_KEY', 'DEEPSEEK_DEFAULT_MODEL'],
        'xai': ['XAI_API_KEY', 'XAI_DEFAULT_MODEL'],
        'cerebras': ['CEREBRAS_API_KEY', 'CEREBRAS_DEFAULT_MODEL'],
        'kilo': ['KILO_API_KEY', 'KILO_BASE_URL', 'KILO_DEFAULT_MODEL'],
        'openrouter': ['OPENROUTER_API_KEY', 'OPENROUTER_DEFAULT_MODEL'],
    }

    provider_names = {
        'ollama': 'Ollama (локальный)',
        'anthropic': 'Anthropic (Claude)',
        'openai': 'OpenAI (ChatGPT)',
        'deepseek': 'DeepSeek',
        'xai': 'xAI (Grok)',
        'cerebras': 'Cerebras',
        'kilo': 'Kilo AI',
        'openrouter': 'OpenRouter',
    }

    written_keys = set()

    for provider, keys in provider_groups.items():
        # Проверяем есть ли переменные для этого провайдера
        has_vars = any(key in env_dict for key in keys)
        if not has_vars:
            continue

        lines.append(f"# {provider_names.get(provider, provider)}\n")
        for key in keys:
            if key in env_dict:
                lines.append(f"{key}={env_dict[key]}\n")
                written_keys.add(key)
        lines.append("\n")

    # Добавляем остальные переменные (не относящиеся к конкретному провайдеру)
    other_vars = {k: v for k, v in env_dict.items() if k not in written_keys}
    if other_vars:
        lines.append("# Другие настройки\n")
        for key, value in sorted(other_vars.items()):
            lines.append(f"{key}={value}\n")

    # Записываем
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def setup_provider(
    provider: str,
    api_key: str = None,
    base_url: str = None,
    default_model: str = None
):
    """
    Сохранить настройки провайдера в .env файл

    Args:
        provider: Имя провайдера
        api_key: API ключ
        base_url: Base URL (опционально)
        default_model: Модель по умолчанию (опционально)
    """
    env_file = get_env_file_path()

    print(f"\n📝 Настройка провайдера: {provider}")
    print(f"   Файл конфигурации: {env_file}")

    # Ollama не требует API ключа
    if provider == 'ollama':
        print("   ℹ️  Ollama не требует API ключа (локальный сервер)")
        if not base_url:
            base_url = input("   Введите URL Ollama (Enter для http://localhost:11434): ").strip()
            if not base_url:
                base_url = "http://localhost:11434"

    # Получаем env ключ для провайдера
    env_key = PROVIDER_ENV_MAP.get(provider)
    if env_key is None and provider != 'ollama':
        print(f"❌ Неизвестный провайдер: {provider}")
        sys.exit(1)

    # Читаем текущий .env
    env_dict = read_env_file(env_file)

    # Обновляем API ключ
    if env_key and api_key:
        env_dict[env_key] = api_key
        print(f"   ✓ API ключ: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")

    # Обновляем base URL если указан
    if base_url and provider in PROVIDERS_WITH_BASE_URL:
        base_url_key = PROVIDERS_WITH_BASE_URL[provider]
        env_dict[base_url_key] = base_url
        print(f"   ✓ Base URL: {base_url}")

    # Обновляем default model если указан
    if default_model:
        model_key = f"{provider.upper()}_DEFAULT_MODEL"
        env_dict[model_key] = default_model
        print(f"   ✓ Default model: {default_model}")

    # Сохраняем
    write_env_file(env_file, env_dict)

    print(f"\n✅ Провайдер {provider} настроен!")
    print(f"\nТеперь можно использовать:")
    print(f"   python -m tools.generator.main --provider {provider} --theme \"замок\"")


def interactive_setup():
    """Интерактивная настройка провайдера"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║       Интерактивная настройка LLM провайдера                 ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    providers = list(PROVIDER_ENV_MAP.keys())
    print("Доступные провайдеры:")
    for i, provider in enumerate(providers, 1):
        print(f"  {i}. {provider}")

    choice = input("\nВыберите провайдер (1-{}): ".format(len(providers))).strip()
    try:
        provider_idx = int(choice) - 1
        provider = providers[provider_idx]
    except (ValueError, IndexError):
        print("❌ Некорректный выбор")
        sys.exit(1)

    # Запрашиваем параметры
    api_key = None
    if provider != 'ollama':
        api_key = input(f"\nВведите API ключ для {provider}: ").strip()
        if not api_key:
            print("❌ API ключ обязателен")
            sys.exit(1)

    base_url = None
    if provider in PROVIDERS_WITH_BASE_URL:
        default_url = "http://localhost:11434" if provider == 'ollama' else None
        prompt = f"Base URL ({default_url if default_url else 'опционально'}): "
        base_url = input(prompt).strip()
        if not base_url and default_url:
            base_url = default_url

    default_model = input("Default model (Enter для пропуска): ").strip() or None

    # Настраиваем
    setup_provider(provider, api_key, base_url, default_model)


def main():
    parser = argparse.ArgumentParser(
        description='Настройка API ключей для LLM провайдеров',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Интерактивная настройка
  python -m tools.generator.setup_provider

  # Настройка OpenRouter
  python -m tools.generator.setup_provider openrouter --api-key sk-or-v1-xxx

  # Настройка Anthropic с указанием модели
  python -m tools.generator.setup_provider anthropic \\
      --api-key sk-ant-xxx \\
      --default-model claude-sonnet-4.5-20250929

  # Настройка Ollama с custom URL
  python -m tools.generator.setup_provider ollama \\
      --base-url http://192.168.1.100:11434

Ключи сохраняются в .env файл в корне проекта.
        """
    )

    parser.add_argument(
        'provider',
        nargs='?',
        choices=list(PROVIDER_ENV_MAP.keys()),
        help='Провайдер для настройки (если не указан - интерактивный режим)'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='API ключ провайдера'
    )

    parser.add_argument(
        '--base-url',
        type=str,
        help='Base URL (для Ollama, Kilo)'
    )

    parser.add_argument(
        '--default-model',
        type=str,
        help='Модель по умолчанию для провайдера'
    )

    args = parser.parse_args()

    # Интерактивный режим если провайдер не указан
    if not args.provider:
        interactive_setup()
        return

    # Если ключ не передан и провайдер требует ключа, спрашиваем
    api_key = args.api_key
    if not api_key and args.provider != 'ollama':
        print(f"\n📝 Настройка провайдера: {args.provider}")
        api_key = input("Введите API ключ: ").strip()
        if not api_key:
            print("❌ API ключ обязателен")
            sys.exit(1)

    setup_provider(args.provider, api_key, args.base_url, args.default_model)


if __name__ == '__main__':
    main()
