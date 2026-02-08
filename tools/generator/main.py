#!/usr/bin/env python3
"""
Zone Generator для МУД "Былины"

CLI entry point для автоматической генерации зон с использованием LLM.
"""

import sys
import argparse
from pathlib import Path
from typing import Tuple, Optional

# Добавляем путь к tools для импорта validator
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.agents import (
    idea_agent,
    lore_agent,
    structure_agent,
    rooms_agent,
    mobs_agent,
    objects_agent,
    quests_agent,
    refiner_agent
)
from generator.utils import (
    user_approve,
    user_edit,
    user_choice,
    print_section,
    assemble_zone_yaml,
    sanitize_filename
)
from generator.llm import OllamaClient
from generator.profiles import get_profile, list_profiles, MODEL_PROFILES
from generator import config

# LangGraph orchestrator (опционально)
try:
    from generator.orchestrator import run_zone_generation, LANGGRAPH_AVAILABLE
except ImportError:
    LANGGRAPH_AVAILABLE = False


class SimpleZoneGenerator:
    """Простой sequential генератор зон (MVP без LangGraph)"""

    def __init__(
        self,
        interactive: bool = True,
        ollama_url: str = "http://localhost:11434",
        output_dir: str = "zones/draft/",
        profile: str = "default"
    ):
        self.interactive = interactive
        self.ollama_url = ollama_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Применяем профиль конфигурации
        profile_config = get_profile(profile)
        config.MODEL_CONFIG = profile_config['models']

        print(f"📋 Профиль: {profile}")
        print(f"   {profile_config['description']}")
        print(f"   VRAM: {profile_config['vram']}\n")

        # Проверка подключения к Ollama
        ollama = OllamaClient(ollama_url=ollama_url)
        if not ollama.check_connection():
            raise RuntimeError(
                f"Не удалось подключиться к Ollama по адресу {ollama_url}\n"
                "Убедитесь что Ollama запущен: docker ps | grep ollama"
            )

    def generate_zone(
        self,
        theme: Optional[str] = None,
        level_range: Optional[Tuple[int, int]] = None
    ) -> Path:
        """
        Генерация новой зоны

        Args:
            theme: Тема зоны (опционально)
            level_range: Диапазон уровней (опционально)

        Returns:
            Путь к сгенерированному файлу
        """
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║          ZONE GENERATOR - Генерация новой зоны               ║")
        print("╚══════════════════════════════════════════════════════════════╝")

        if self.interactive:
            print("\n💡 Интерактивный режим: вы сможете одобрять каждый этап\n")
        else:
            print("\n🤖 Автоматический режим: генерация без остановок\n")

        state = {
            'user_theme': theme,
            'level_range': level_range
        }

        # ЭТАП 1: Idea
        print("\n" + "="*60)
        state = idea_agent(state, ollama_url=self.ollama_url)

        if self.interactive:
            if not self._review_stage("idea", state['idea']):
                state['idea'] = user_edit(state['idea'])

        # ЭТАП 2: Lore
        print("\n" + "="*60)
        state = lore_agent(state, ollama_url=self.ollama_url)

        if self.interactive:
            if not self._review_stage("lore", state['lore']):
                state['lore'] = user_edit(state['lore'])

        # ЭТАП 3: Structure
        print("\n" + "="*60)
        state = structure_agent(state, ollama_url=self.ollama_url)

        if self.interactive:
            if not self._review_stage("structure", state['structure']):
                state['structure'] = user_edit(state['structure'])

        # ЭТАП 4: Rooms (batch)
        print("\n" + "="*60)
        state = rooms_agent(state, ollama_url=self.ollama_url, interactive=self.interactive)

        # ЭТАП 5: Mobs
        print("\n" + "="*60)
        state = mobs_agent(state, ollama_url=self.ollama_url)

        if self.interactive:
            if not self._review_stage("mobiles", state['mobiles']):
                state['mobiles'] = user_edit(state['mobiles'])

        # ЭТАП 6: Objects
        print("\n" + "="*60)
        state = objects_agent(state, ollama_url=self.ollama_url)

        if self.interactive:
            if not self._review_stage("objects", state['objects']):
                state['objects'] = user_edit(state['objects'])

        # ЭТАП 7: Quests
        print("\n" + "="*60)
        state = quests_agent(state, ollama_url=self.ollama_url)

        if self.interactive and state.get('quests'):
            if not self._review_stage("quests", state['quests']):
                state['quests'] = user_edit(state['quests'])

        # СБОРКА и СОХРАНЕНИЕ
        print("\n" + "="*60)
        print("\n💾 Сборка финального YAML...")

        zone_yaml = assemble_zone_yaml(state)

        # Сохранение
        zone_name = state['idea'].get('name', 'new_zone')
        filename = sanitize_filename(zone_name) + '.yaml'
        output_path = self.output_dir / filename

        output_path.write_text(zone_yaml, encoding='utf-8')

        print(f"\n✅ Зона сохранена: {output_path}")

        # Валидация (если доступен validator)
        if self._validate_zone(output_path):
            print("✅ Базовая валидация пройдена")
        else:
            print("⚠️  Рекомендуется запустить validator.py для полной проверки")

        print(f"\n🎯 Следующие шаги:")
        print(f"   1. Проверить зону: python tools/validator.py {output_path}")
        print(f"   2. Отредактировать вручную если нужно")
        print(f"   3. Улучшить: python -m tools.generator.main --refine {output_path}")

        return output_path

    def refine_zone(self, zone_file: str, max_iterations: int = 3, target_score: int = 75) -> Path:
        """
        Улучшение существующей зоны

        Args:
            zone_file: Путь к YAML файлу зоны
            max_iterations: Максимум итераций улучшения
            target_score: Целевой балл валидации

        Returns:
            Путь к улучшенному файлу
        """
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║          ZONE GENERATOR - Улучшение зоны                     ║")
        print("╚══════════════════════════════════════════════════════════════╝")

        zone_path = Path(zone_file)

        if not zone_path.exists():
            raise FileNotFoundError(f"Файл не найден: {zone_file}")

        # Вызываем refiner agent
        refined_path = refiner_agent(
            zone_file=zone_path,
            ollama_url=self.ollama_url,
            max_iterations=max_iterations,
            target_score=target_score
        )

        print(f"\n🎯 Следующие шаги:")
        print(f"   1. Проверить улучшенную зону: python tools/validator.py {refined_path}")
        print(f"   2. Сравнить с оригиналом: diff {zone_file} {refined_path}")
        print(f"   3. Если нужно ещё улучшение: python -m tools.generator.main --refine {refined_path}")

        return refined_path

    def _review_stage(self, stage_name: str, data) -> bool:
        """Интерактивный review этапа"""
        print_section(f"Review: {stage_name}", None)

        # Показываем краткую информацию
        if isinstance(data, dict):
            for key, value in list(data.items())[:5]:  # Первые 5 ключей
                if isinstance(value, str):
                    preview = value[:80] + "..." if len(value) > 80 else value
                    print(f"   {key}: {preview}")
                elif isinstance(value, (list, dict)):
                    print(f"   {key}: {len(value)} элементов")
                else:
                    print(f"   {key}: {value}")
        elif isinstance(data, list):
            print(f"   Элементов: {len(data)}")
            for idx, item in enumerate(data[:3]):  # Первые 3 элемента
                if isinstance(item, dict):
                    name = item.get('name', item.get('id', f'Item {idx+1}'))
                    print(f"   • {name}")

        return user_approve(f"\n✓ Одобрить {stage_name}?")

    def _validate_zone(self, zone_file: Path) -> bool:
        """Базовая валидация YAML"""
        try:
            import yaml
            with open(zone_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Проверка базовой структуры
            if 'zone' not in data:
                return False

            zone = data['zone']
            if 'meta' not in zone:
                return False

            return True

        except Exception as e:
            print(f"⚠️  Ошибка валидации: {e}")
            return False


def parse_level_range(level_str: str) -> Tuple[int, int]:
    """
    Парсинг диапазона уровней из строки

    Args:
        level_str: Строка вида "10-15" или "20"

    Returns:
        (min_level, max_level)
    """
    if '-' in level_str:
        parts = level_str.split('-')
        return (int(parts[0]), int(parts[1]))
    else:
        level = int(level_str)
        return (level, level + 5)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Zone Generator для МУД "Былины"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  # Интерактивная генерация (LangGraph режим по умолчанию)
  %(prog)s --theme "заброшенная мельница" --level "10-15"

  # Автоматическая генерация с профилем RTX 4070 Ti максимум
  %(prog)s --auto --profile rtx4070ti-max --theme "соляные копи"

  # Продолжить генерацию после Ctrl+C (используется последний checkpoint)
  %(prog)s --resume zone_20260207_a1b2c3d4

  # Список всех доступных профилей
  %(prog)s --list-profiles

  # Улучшение существующей зоны (требует --no-langgraph)
  %(prog)s --no-langgraph --refine zones/draft/old_zone.yaml

  # Fallback на простой генератор (если проблемы с LangGraph)
  %(prog)s --no-langgraph --theme "тёмный лес" --level "15-20"
        """
    )

    # Режимы
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='Интерактивный режим с паузами на review (по умолчанию)'
    )
    mode_group.add_argument(
        '--auto',
        action='store_true',
        help='Автоматическая генерация без остановок'
    )
    mode_group.add_argument(
        '--refine',
        type=str,
        metavar='FILE',
        help='Улучшить существующую зону'
    )

    # Параметры зоны
    parser.add_argument(
        '--theme',
        type=str,
        help='Тема зоны (например "соляные копи")'
    )
    parser.add_argument(
        '--level',
        type=str,
        help='Диапазон уровней (например "10-15" или "20")'
    )

    # Настройки
    parser.add_argument(
        '--output',
        type=str,
        default='zones/draft/',
        help='Директория для сохранения (по умолчанию zones/draft/)'
    )
    parser.add_argument(
        '--profile',
        type=str,
        default='default',
        choices=list(MODEL_PROFILES.keys()),
        help='Профиль GPU конфигурации (по умолчанию: default)'
    )
    parser.add_argument(
        '--list-profiles',
        action='store_true',
        help='Показать все доступные профили и выйти'
    )
    parser.add_argument(
        '--ollama-url',
        type=str,
        default='http://localhost:11434',
        help='URL Ollama API'
    )

    # Параметры для режима refine
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=3,
        help='Максимум итераций улучшения для --refine (по умолчанию 3)'
    )
    parser.add_argument(
        '--target-score',
        type=int,
        default=75,
        help='Целевой балл валидации для --refine (по умолчанию 75)'
    )

    # LLM Provider
    parser.add_argument(
        '--provider',
        type=str,
        default='ollama',
        choices=['ollama', 'anthropic', 'openai', 'deepseek', 'xai', 'cerebras', 'kilo', 'openrouter', 'claude', 'chatgpt', 'gpt', 'grok'],
        help='LLM провайдер (по умолчанию: ollama). Алиасы: claude→anthropic, chatgpt/gpt→openai, grok→xai'
    )

    # Zone size
    parser.add_argument(
        '--rooms',
        type=int,
        metavar='N',
        help='Желаемое количество комнат в зоне (например: --rooms 15). По умолчанию LLM решает сам (~8-12 комнат)'
    )

    # Model selection
    parser.add_argument(
        '--model',
        type=str,
        metavar='MODEL',
        help='Модель для использования (для всех этапов). Примеры: gpt-4o, claude-opus-4.6, qwen2.5:14b, anthropic/claude-sonnet-4.5'
    )
    parser.add_argument(
        '--models',
        type=str,
        metavar='JSON',
        help='JSON конфиг моделей для разных этапов. Пример: \'{"idea": "gpt-4o", "rooms": "claude-sonnet-4.5"}\''
    )

    # Режим работы
    parser.add_argument(
        '--no-langgraph',
        action='store_true',
        help='Использовать простой sequential генератор вместо LangGraph'
    )
    parser.add_argument(
        '--resume',
        type=str,
        metavar='THREAD_ID',
        help='Продолжить генерацию с checkpoint'
    )

    args = parser.parse_args()

    # Показать профили и выйти
    if args.list_profiles:
        list_profiles()
        sys.exit(0)

    # Определяем interactive режим
    interactive = not args.auto

    # Определяем режим работы: LangGraph по умолчанию
    use_langgraph = not args.no_langgraph

    # Проверяем доступность LangGraph
    if use_langgraph and not LANGGRAPH_AVAILABLE:
        print("❌ Ошибка: LangGraph не установлен")
        print("Установите: pip install langgraph langchain-core")
        print("Или используйте: --no-langgraph (SimpleZoneGenerator)")
        sys.exit(1)

    # Валидация режимов
    if args.refine and use_langgraph:
        print("❌ Ошибка: --refine поддерживается только в SimpleZoneGenerator")
        print("Используйте: --no-langgraph --refine <file>")
        sys.exit(1)

    if args.resume and not use_langgraph:
        print("❌ Ошибка: --resume работает только в LangGraph режиме")
        print("Уберите флаг --no-langgraph для использования checkpoints")
        sys.exit(1)

    try:
        # Применяем профиль конфигурации
        profile_config = get_profile(args.profile)
        config.MODEL_CONFIG = profile_config['models']

        print(f"📋 Профиль: {args.profile}")
        print(f"   {profile_config['description']}")
        print(f"   VRAM: {profile_config['vram']}")

        if use_langgraph:
            # LangGraph режим (по умолчанию)
            print(f"   Режим: LangGraph Orchestrator\n")

            # Проверка theme только для новой генерации (не для resume)
            if not args.resume and not args.theme:
                print("❌ Ошибка: --theme обязателен для новой генерации")
                print("   Для продолжения используйте: --resume <thread_id>")
                sys.exit(1)

            level_range = parse_level_range(args.level) if args.level else (10, 15)

            # Парсим model config
            model_config = None
            if args.models:
                try:
                    import json
                    model_config = json.loads(args.models)
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга --models JSON: {e}")
                    sys.exit(1)

            run_zone_generation(
                theme=args.theme,
                level_range=level_range,
                ollama_url=args.ollama_url,
                interactive=interactive,
                output_dir=args.output,
                resume_thread_id=args.resume,
                provider=args.provider,
                requested_rooms=args.rooms,
                model=args.model,
                model_config=model_config
            )

        else:
            # SimpleZoneGenerator режим (fallback)
            print(f"   Режим: SimpleZoneGenerator (fallback)\n")

            generator = SimpleZoneGenerator(
                interactive=interactive,
                ollama_url=args.ollama_url,
                output_dir=args.output,
                profile=args.profile
            )

            if args.refine:
                # Режим улучшения
                generator.refine_zone(
                    args.refine,
                    max_iterations=args.max_iterations,
                    target_score=args.target_score
                )
            else:
                # Режим создания новой зоны
                level_range = parse_level_range(args.level) if args.level else None

                generator.generate_zone(
                    theme=args.theme,
                    level_range=level_range
                )

    except KeyboardInterrupt:
        print("\n\n⚠️  Генерация прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
