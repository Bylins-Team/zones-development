#!/usr/bin/env python3
"""
Утилита для просмотра доступных LLM провайдеров
"""

import sys
from .llm import LLMClientFactory, ProviderConfig
from .config import DEFAULT_LLM_PROVIDER, PROVIDER_MODEL_CONFIGS


def list_providers():
    """Показать список всех провайдеров и их статус"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          ДОСТУПНЫЕ LLM ПРОВАЙДЕРЫ                            ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    providers_status = LLMClientFactory.list_providers()

    for provider, available in providers_status.items():
        status_icon = "✅" if available else "❌"
        status_text = "ДОСТУПЕН" if available else "НЕ НАСТРОЕН"

        print(f"{status_icon} {provider.upper():<15} {status_text}")

        if available:
            info = LLMClientFactory.get_provider_info(provider)
            models = PROVIDER_MODEL_CONFIGS.get(provider, {})

            # Показываем модели
            print(f"   Модели:")
            for stage, model in models.items():
                print(f"   - {stage:12} → {model}")

            # Base URL для некоторых провайдеров
            if info['base_url']:
                print(f"   Base URL: {info['base_url']}")

        else:
            # Подсказка как настроить
            env_key = ProviderConfig.PROVIDER_ENV_KEYS.get(provider)
            if env_key:
                print(f"   💡 Для активации добавьте {env_key} в .env")

        print()

    # Дефолтный провайдер
    print(f"📌 Провайдер по умолчанию: {DEFAULT_LLM_PROVIDER.upper()}")
    if not ProviderConfig.is_provider_available(DEFAULT_LLM_PROVIDER):
        print(f"   ⚠️  Внимание: дефолтный провайдер не настроен!")

    print("\n" + "="*64)
    print("Использование:")
    print("  --provider ollama      # Использовать Ollama (локальный)")
    print("  --provider anthropic   # Использовать Claude")
    print("  --provider openai      # Использовать ChatGPT")
    print("  --provider deepseek    # Использовать DeepSeek")
    print("  --provider xai         # Использовать Grok")
    print("  --provider cerebras    # Использовать Cerebras")
    print("="*64)


if __name__ == '__main__':
    list_providers()
