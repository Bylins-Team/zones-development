"""
Фабрика для создания LLM клиентов
"""

from typing import Optional, Dict
from .universal_client import UniversalLLMClient
from .ollama_client import OllamaClient
from .providers import ProviderConfig, normalize_provider_name
from ..config import (
    DEFAULT_LLM_PROVIDER,
    PROVIDER_MODEL_CONFIGS,
    TEMPERATURE_CONFIG,
    GENERATION_CONFIG
)


class LLMClientFactory:
    """Фабрика для создания LLM клиентов"""

    @staticmethod
    def create_client(
        provider: Optional[str] = None,
        use_universal: bool = True,
        timeout: Optional[int] = None,
        model: Optional[str] = None,
        model_config: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Создать LLM клиент

        Args:
            provider: Имя провайдера ('ollama', 'anthropic', 'openai', etc.)
                     Если None, использует DEFAULT_LLM_PROVIDER
            use_universal: Использовать UniversalLLMClient (True) или
                          legacy OllamaClient (False, только для Ollama)
            timeout: Дефолтный timeout в секундах
            model: Модель для всех этапов (override конфига)
            model_config: Словарь stage -> model (override конфига)
            **kwargs: Дополнительные параметры для клиента

        Returns:
            UniversalLLMClient или OllamaClient
        """
        # Провайдер по умолчанию
        if provider is None:
            provider = DEFAULT_LLM_PROVIDER

        provider = normalize_provider_name(provider)

        # Проверяем доступность
        if not ProviderConfig.is_provider_available(provider):
            available = ProviderConfig.list_available_providers()
            raise ValueError(
                f"❌ Провайдер '{provider}' недоступен!\n"
                f"   Причина: нет API ключа в .env\n"
                f"   Доступные провайдеры: {', '.join(available)}\n\n"
                f"   Чтобы использовать {provider}:\n"
                f"   1. Скопируйте .env.example в .env\n"
                f"   2. Добавьте API ключ для {provider.upper()}"
            )

        # Модели для провайдера (из конфига или переданные)
        final_model_config = PROVIDER_MODEL_CONFIGS.get(provider, {}).copy()

        # Override из параметров
        if model_config:
            final_model_config.update(model_config)

        # Если указана одна модель для всех этапов
        if model:
            final_model_config = {
                stage: model
                for stage in ['idea', 'lore', 'structure', 'rooms', 'mobs', 'objects', 'quests', 'refiner']
            }

        # Timeout
        if timeout is None:
            timeout = GENERATION_CONFIG.get('ollama_timeout', 300)

        # Для Ollama можем использовать legacy клиент или универсальный
        if provider == 'ollama' and not use_universal:
            return OllamaClient(
                ollama_url=ProviderConfig.get_base_url('ollama'),
                timeout=timeout,
                **kwargs
            )

        # Универсальный клиент для всех провайдеров
        return UniversalLLMClient(
            provider=provider,
            model_config=final_model_config,
            temp_config=TEMPERATURE_CONFIG,
            timeout=timeout,
            retry_enabled=GENERATION_CONFIG.get('ollama_retry', True)
        )

    @staticmethod
    def get_provider_info(provider: Optional[str] = None) -> Dict:
        """
        Получить информацию о провайдере

        Args:
            provider: Имя провайдера (или None для дефолтного)

        Returns:
            Словарь с информацией о провайдере
        """
        if provider is None:
            provider = DEFAULT_LLM_PROVIDER

        provider = normalize_provider_name(provider)

        return {
            'provider': provider,
            'available': ProviderConfig.is_provider_available(provider),
            'has_api_key': ProviderConfig.get_api_key(provider) is not None,
            'base_url': ProviderConfig.get_base_url(provider),
            'default_model': ProviderConfig.get_default_model(provider),
            'model_config': PROVIDER_MODEL_CONFIGS.get(provider, {}),
        }

    @staticmethod
    def list_providers() -> Dict[str, bool]:
        """
        Список всех провайдеров и их доступность

        Returns:
            {'ollama': True, 'anthropic': False, ...}
        """
        return {
            provider: ProviderConfig.is_provider_available(provider)
            for provider in ProviderConfig.PROVIDER_ENV_KEYS.keys()
        }


# Convenience функция
def create_llm_client(provider: Optional[str] = None, **kwargs):
    """Удобная функция для создания клиента"""
    return LLMClientFactory.create_client(provider=provider, **kwargs)
