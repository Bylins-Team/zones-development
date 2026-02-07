"""
Ollama Client для генерации контента
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, List, Any
from ..config import MODEL_CONFIG, TEMPERATURE_CONFIG, GENERATION_CONFIG


class OllamaClient:
    """Клиент для работы с Ollama API"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_config = MODEL_CONFIG
        self.temp_config = TEMPERATURE_CONFIG
        self.timeout = GENERATION_CONFIG['ollama_timeout']
        self.retry_enabled = GENERATION_CONFIG['ollama_retry']

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
        Генерация текста через Ollama

        Args:
            prompt: Промпт для генерации
            stage: Этап генерации ('idea', 'lore', 'rooms', etc)
            system: Системный промпт (опционально)
            tools: Инструменты для function calling (опционально)
            temperature: Температура (опционально, иначе из конфига)
            timeout: Таймаут в секундах (опционально)
            retry: Повторить при timeout

        Returns:
            Dict с ключами:
                - content: текст ответа
                - tool_calls: вызовы инструментов (если есть)
                - model: использованная модель
        """
        model = self.model_config.get(stage, 'qwen2.5:14b')
        temp = temperature if temperature is not None else self.temp_config.get(stage, 0.5)
        timeout_val = timeout if timeout is not None else self.timeout

        data = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temp,
                'top_p': 0.9
            }
        }

        if system:
            data['system'] = system

        if tools:
            data['tools'] = tools

        try:
            url = f"{self.ollama_url}/api/generate"
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=timeout_val) as response:
                result = json.loads(response.read().decode('utf-8'))

                return {
                    'content': result.get('response', ''),
                    'tool_calls': result.get('tool_calls', []),
                    'model': model,
                    'done': result.get('done', True)
                }

        except urllib.error.URLError as e:
            if 'timeout' in str(e).lower() and retry and self.retry_enabled:
                print(f"⏱️  Timeout {timeout_val}s. Повторная попытка с {timeout_val*2}s...")
                return self.generate(
                    prompt, stage, system, tools, temp,
                    timeout=timeout_val*2, retry=False
                )
            else:
                raise RuntimeError(f"Не удалось подключиться к Ollama: {e}")

        except Exception as e:
            raise RuntimeError(f"Ошибка при вызове Ollama: {e}")

    def estimate_tokens(self, text: str) -> int:
        """
        Оценка количества токенов
        1 token ≈ 4 символа для русского текста
        """
        return len(text) // 4

    def check_connection(self) -> bool:
        """Проверка доступности Ollama"""
        try:
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """Получить список доступных моделей"""
        try:
            url = f"{self.ollama_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                return [m['name'] for m in result.get('models', [])]
        except:
            return []
