"""
LLM интеграция для Zone Generator
"""

from .ollama_client import OllamaClient
from .context_manager import ContextManager

__all__ = ['OllamaClient', 'ContextManager']
