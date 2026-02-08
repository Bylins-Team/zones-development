"""
Универсальный LLM клиент на базе LiteLLM
Поддерживает: Ollama, Anthropic, OpenAI, DeepSeek, xAI, Cerebras и др.
"""

import os
from typing import Dict, Any, Optional, List
from litellm import completion
from .providers import ProviderConfig, normalize_provider_name


class UniversalLLMClient:
    """Универсальный клиент для работы с разными LLM провайдерами"""

    def __init__(
        self,
        provider: str = 'ollama',
        model_config: Optional[Dict[str, str]] = None,
        temp_config: Optional[Dict[str, float]] = None,
        timeout: int = 300,
        retry_enabled: bool = True
    ):
        """
        Args:
            provider: Имя провайдера ('ollama', 'anthropic', 'openai', etc.)
            model_config: Маппинг stage → model name
            temp_config: Маппинг stage → temperature
            timeout: Timeout в секундах
            retry_enabled: Включить retry при ошибках
        """
        self.provider = normalize_provider_name(provider)
        self.model_config = model_config or {}
        self.temp_config = temp_config or {}
        self.timeout = timeout
        self.retry_enabled = retry_enabled

        # Проверяем доступность провайдера
        if not ProviderConfig.is_provider_available(self.provider):
            available = ProviderConfig.list_available_providers()
            raise ValueError(
                f"Провайдер '{self.provider}' недоступен (нет API ключа). "
                f"Доступные: {', '.join(available)}"
            )

        # API ключ и base URL
        self.api_key = ProviderConfig.get_api_key(self.provider)
        self.base_url = ProviderConfig.get_base_url(self.provider)

        # Устанавливаем environment variables для LiteLLM
        if self.api_key:
            env_key = ProviderConfig.PROVIDER_ENV_KEYS[self.provider]
            if env_key:
                os.environ[env_key] = self.api_key

        if self.base_url and self.provider == 'ollama':
            os.environ['OLLAMA_API_BASE'] = self.base_url

    def generate(
        self,
        prompt: str,
        stage: str,
        system: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Генерация текста через LLM

        Args:
            prompt: Промпт для генерации
            stage: Этап генерации ('idea', 'lore', 'rooms', etc.) - для выбора модели
            system: Системный промпт
            tools: Function calling tools (опционально)
            temperature: Температура (override конфига)
            timeout: Timeout в секундах (override дефолтного)
            retry: Включить retry при ошибках

        Returns:
            {
                'content': str,
                'model': str,
                'usage': dict,
                'tool_calls': list (опционально)
            }
        """
        # Выбор модели для этапа
        model = self.model_config.get(stage)
        if not model:
            # Fallback на дефолтную модель провайдера
            model = ProviderConfig.get_default_model(self.provider)

        # Преобразуем в формат LiteLLM
        litellm_model = ProviderConfig.get_litellm_model_name(self.provider, model)

        # Температура
        temp = temperature if temperature is not None else self.temp_config.get(stage, 0.5)

        # Timeout
        timeout_val = timeout if timeout is not None else self.timeout

        # Формируем messages
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})

        # Параметры вызова
        call_params = {
            'model': litellm_model,
            'messages': messages,
            'temperature': temp,
            'timeout': timeout_val,
        }

        # Добавляем tools если есть (function calling)
        if tools:
            call_params['tools'] = tools
            call_params['tool_choice'] = 'auto'

        # Ollama-специфичные параметры
        if self.provider == 'ollama':
            call_params['api_base'] = self.base_url

        try:
            # Вызов LiteLLM
            response = completion(**call_params)

            # Парсим ответ
            message = response.choices[0].message
            result = {
                'content': message.content or '',
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens,
                },
                'done': True
            }

            # Если были tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                result['tool_calls'] = [
                    {
                        'name': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                    for tc in message.tool_calls
                ]

            return result

        except Exception as e:
            # Retry при timeout
            if 'timeout' in str(e).lower() and retry and self.retry_enabled:
                print(f"⏱️  Timeout {timeout_val}s. Повторная попытка с {timeout_val*2}s...")
                return self.generate(
                    prompt, stage, system, tools, temp,
                    timeout=timeout_val*2, retry=False
                )
            else:
                raise RuntimeError(f"Ошибка при вызове {self.provider}: {e}")

    def estimate_tokens(self, text: str) -> int:
        """
        Оценка количества токенов

        Примерные значения:
        - Русский текст: ~4 символа на токен
        - Английский текст: ~4 символа на токен
        - Код: ~3.5 символа на токен
        """
        return len(text) // 4

    def get_model_for_stage(self, stage: str) -> str:
        """Получить имя модели для этапа"""
        model = self.model_config.get(stage)
        if not model:
            model = ProviderConfig.get_default_model(self.provider)
        return ProviderConfig.get_litellm_model_name(self.provider, model)

    def get_provider_info(self) -> Dict[str, Any]:
        """Получить информацию о текущем провайдере"""
        return {
            'provider': self.provider,
            'available': ProviderConfig.is_provider_available(self.provider),
            'base_url': self.base_url,
            'has_api_key': self.api_key is not None,
            'default_model': ProviderConfig.get_default_model(self.provider),
        }
