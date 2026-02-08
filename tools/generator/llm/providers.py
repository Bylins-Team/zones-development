"""
Конфигурация LLM провайдеров и маппинг моделей
"""

from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()


class ProviderConfig:
    """Конфигурация провайдеров LLM"""

    # Маппинг провайдер → API key environment variable
    PROVIDER_ENV_KEYS = {
        'ollama': None,  # Локальный, не требует ключа
        'anthropic': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY',
        'xai': 'XAI_API_KEY',
        'cerebras': 'CEREBRAS_API_KEY',
        'kilo': 'KILO_API_KEY',  # Kilo AI (OpenAI-compatible)
        'openrouter': 'OPENROUTER_API_KEY',  # OpenRouter (unified LLM access)
    }

    # Маппинг провайдер → base URL (для провайдеров с custom endpoint)
    PROVIDER_BASE_URLS = {
        'ollama': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        'deepseek': 'https://api.deepseek.com',
        'cerebras': 'https://api.cerebras.ai/v1',
        'kilo': os.getenv('KILO_BASE_URL', 'https://api.kilo.ai/v1'),  # Настраиваемый
        'openrouter': 'https://openrouter.ai/api/v1',
    }

    # Дефолтные модели для каждого провайдера
    DEFAULT_MODELS = {
        'ollama': os.getenv('OLLAMA_DEFAULT_MODEL', 'qwen2.5:14b'),
        'anthropic': os.getenv('ANTHROPIC_DEFAULT_MODEL', 'claude-sonnet-4.5-20250929'),
        'openai': os.getenv('OPENAI_DEFAULT_MODEL', 'gpt-4o'),
        'deepseek': os.getenv('DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat'),
        'xai': os.getenv('XAI_DEFAULT_MODEL', 'grok-2-latest'),
        'cerebras': os.getenv('CEREBRAS_DEFAULT_MODEL', 'llama-3.3-70b'),
        'kilo': os.getenv('KILO_DEFAULT_MODEL', 'kilo-chat'),  # Настраиваемая модель
        'openrouter': os.getenv('OPENROUTER_DEFAULT_MODEL', 'anthropic/claude-sonnet-4.5'),
    }

    # LiteLLM model prefixes для каждого провайдера
    LITELLM_PREFIXES = {
        'ollama': 'ollama/',
        'anthropic': 'anthropic/',
        'openai': 'openai/',
        'deepseek': 'deepseek/',
        'xai': 'xai/',
        'cerebras': 'cerebras/',
        'kilo': 'openai/',  # Kilo использует OpenAI-совместимый API
        'openrouter': 'openrouter/',
    }

    # Рекомендуемые модели для разных задач (по провайдеру)
    RECOMMENDED_MODELS = {
        'ollama': {
            'creative': 'qwen2.5:14b',      # Креативные задачи (lore, rooms)
            'structural': 'qwen2.5:7b',     # Структурные задачи (structure)
            'refiner': 'qwen2.5:14b',       # Рефайнмент
        },
        'anthropic': {
            'creative': 'claude-sonnet-4.5-20250929',
            'structural': 'claude-haiku-4.5-20251001',
            'refiner': 'claude-opus-4.6-20250808',
        },
        'openai': {
            'creative': 'gpt-4o',
            'structural': 'gpt-4o-mini',
            'refiner': 'gpt-4o',
        },
        'deepseek': {
            'creative': 'deepseek-chat',
            'structural': 'deepseek-chat',
            'refiner': 'deepseek-chat',
        },
        'xai': {
            'creative': 'grok-2-latest',
            'structural': 'grok-2-latest',
            'refiner': 'grok-2-latest',
        },
        'cerebras': {
            'creative': 'llama-3.3-70b',
            'structural': 'llama-3.1-8b',
            'refiner': 'llama-3.3-70b',
        },
        'kilo': {
            'creative': 'kilo-chat',
            'structural': 'kilo-chat',
            'refiner': 'kilo-chat',
        },
        'openrouter': {
            'creative': 'anthropic/claude-sonnet-4.5',
            'structural': 'anthropic/claude-haiku-4.5',
            'refiner': 'anthropic/claude-opus-4.6',
        },
    }

    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Получить API ключ для провайдера"""
        env_key = ProviderConfig.PROVIDER_ENV_KEYS.get(provider)
        if env_key is None:
            return None
        return os.getenv(env_key)

    @staticmethod
    def get_base_url(provider: str) -> Optional[str]:
        """Получить base URL для провайдера"""
        return ProviderConfig.PROVIDER_BASE_URLS.get(provider)

    @staticmethod
    def get_default_model(provider: str) -> str:
        """Получить дефолтную модель для провайдера"""
        return ProviderConfig.DEFAULT_MODELS.get(provider, 'gpt-4o')

    @staticmethod
    def get_litellm_model_name(provider: str, model: str) -> str:
        """
        Преобразовать имя модели в формат LiteLLM

        Например:
        - ollama + qwen2.5:14b → ollama/qwen2.5:14b
        - anthropic + claude-sonnet-4.5 → anthropic/claude-sonnet-4.5-20250929
        """
        prefix = ProviderConfig.LITELLM_PREFIXES.get(provider, '')

        # Для Ollama не добавляем prefix если модель уже содержит ollama/
        if provider == 'ollama' and not model.startswith('ollama/'):
            return f"{prefix}{model}"

        # Для других провайдеров
        if not model.startswith(prefix):
            return f"{prefix}{model}"

        return model

    @staticmethod
    def is_provider_available(provider: str) -> bool:
        """Проверить доступность провайдера (есть ли API ключ)"""
        if provider == 'ollama':
            return True  # Локальный, всегда доступен

        api_key = ProviderConfig.get_api_key(provider)
        return api_key is not None and api_key != '' and not api_key.startswith('your_')

    @staticmethod
    def list_available_providers() -> list[str]:
        """Список доступных провайдеров (с валидными ключами)"""
        return [
            provider for provider in ProviderConfig.PROVIDER_ENV_KEYS.keys()
            if ProviderConfig.is_provider_available(provider)
        ]


# Алиасы для более понятных имен
PROVIDER_ALIASES = {
    'claude': 'anthropic',
    'chatgpt': 'openai',
    'gpt': 'openai',
    'grok': 'xai',
}


def normalize_provider_name(provider: str) -> str:
    """Нормализовать имя провайдера (поддержка алиасов)"""
    return PROVIDER_ALIASES.get(provider.lower(), provider.lower())
