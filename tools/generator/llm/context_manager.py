"""
Context Manager для управления context window
"""

import json
from typing import List, Dict, Any


class ContextManager:
    """Управление context window для больших зон"""

    def __init__(self, max_tokens: int = 32768):
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        """
        Оценка токенов: 1 token ≈ 4 символа для русского
        """
        return len(text) // 4

    def summarize_rooms(self, rooms: List[Dict]) -> str:
        """
        Краткие summaries комнат для контекста
        Возвращает только ключевую информацию без полных описаний
        """
        summaries = []
        for room in rooms:
            summary = {
                'id': room.get('id', ''),
                'name': room.get('name', ''),
                'sector': room.get('sector', 'INSIDE'),
                'exits': [e.get('direction', '') for e in room.get('exits', [])]
            }
            summaries.append(summary)

        # JSON компактнее YAML для summaries
        return json.dumps(summaries, ensure_ascii=False, separators=(',', ':'))

    def summarize_mobs(self, mobs: List[Dict]) -> str:
        """Краткие summaries мобов"""
        summaries = []
        for mob in mobs:
            summary = {
                'id': mob.get('id', ''),
                'name': mob.get('name', ''),
                'level': mob.get('level', 0),
                'role': mob.get('role', '')
            }
            summaries.append(summary)
        return json.dumps(summaries, ensure_ascii=False, separators=(',', ':'))

    def fit_into_budget(
        self,
        system: str,
        schema: str,
        context: str,
        instructions: str,
        budget: int
    ) -> Dict[str, Any]:
        """
        Вписать все компоненты в бюджет токенов

        Args:
            system: Системный промпт
            schema: YAML схема
            context: Контекст (лор, предыдущие комнаты, etc)
            instructions: Инструкции по генерации
            budget: Максимум токенов для input

        Returns:
            Dict с компонентами, вписанными в бюджет
        """
        # Обязательные компоненты (не сжимаются)
        required = system + schema + instructions
        required_tokens = self.estimate_tokens(required)

        # Доступно для context
        available = budget - required_tokens

        if available <= 0:
            raise ValueError(
                f"Schema + instructions слишком большие: {required_tokens} токенов "
                f"при бюджете {budget}"
            )

        # Truncate context если нужно
        context_tokens = self.estimate_tokens(context)
        if context_tokens > available:
            max_chars = available * 4
            context = context[:max_chars] + "\n...(truncated)"
            print(f"⚠️  Контекст урезан: {context_tokens} → {available} токенов")

        return {
            'system': system,
            'schema': schema,
            'context': context,
            'instructions': instructions,
            'total_tokens': self.estimate_tokens(required + context)
        }

    def create_batch_prompt(
        self,
        base_prompt: str,
        items: List[Any],
        batch_size: int
    ) -> List[str]:
        """
        Разбить генерацию на батчи

        Args:
            base_prompt: Базовый промпт
            items: Элементы для генерации (комнаты, мобы, etc)
            batch_size: Размер батча

        Returns:
            Список промптов для каждого батча
        """
        prompts = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_prompt = base_prompt.replace(
                '{batch}', json.dumps(batch, ensure_ascii=False)
            )
            prompts.append(batch_prompt)

        return prompts
