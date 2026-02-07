"""
LangGraph Orchestrator для Zone Generator

Управляет workflow генерации зоны через граф состояний с:
- Human-in-the-loop на каждом этапе
- Автоматическими циклами валидации
- Conditional edges для retry
- Checkpoints для сохранения прогресса
"""

from typing import TypedDict, Annotated, Literal
from pathlib import Path
import operator
import uuid
import datetime

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    import sys
    print(f"⚠️  LangGraph импорт ошибка: {e}", file=sys.stderr)
    print("Установите: pip install langgraph langchain-core", file=sys.stderr)

from .agents import (
    idea_agent,
    lore_agent,
    structure_agent,
    rooms_agent,
    mobs_agent,
    objects_agent,
    quests_agent,
    refiner_agent
)
from .utils import user_approve, user_edit, user_choice, assemble_zone_yaml, sanitize_filename
from .config import GENERATION_CONFIG


class ZoneGenerationState(TypedDict):
    """Состояние генерации зоны"""
    # Входные параметры
    user_theme: str
    level_range: tuple[int, int]
    ollama_url: str
    interactive: bool

    # Сгенерированные данные
    idea: dict
    lore: dict
    structure: dict
    rooms: list[dict]
    mobiles: list[dict]
    objects: list[dict]
    quests: list[dict]

    # Метаданные
    validation_score: int
    refinement_iteration: int
    errors: Annotated[list[str], operator.add]  # Накапливаются
    warnings: Annotated[list[str], operator.add]  # Накапливаются

    # Управление flow
    should_refine: bool
    human_approved: bool
    retry_count: int
    current_stage: str  # Для отслеживания текущего этапа в human review


def create_zone_graph(
    interactive: bool = True,
    max_retry: int = 2,
    target_score: int = 75
):
    """
    Создать граф генерации зоны

    Args:
        interactive: Режим с human-in-the-loop
        max_retry: Максимум попыток regenerate
        target_score: Целевой балл валидации

    Returns:
        Compiled StateGraph
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph не установлен")

    workflow = StateGraph(ZoneGenerationState)

    # === УЗЛЫ ГЕНЕРАЦИИ ===

    def idea_node(state: ZoneGenerationState) -> dict:
        """Узел генерации идеи"""
        print("\n🔧 ЭТАП 1/7: Генерация концепции зоны")
        result = idea_agent(state, ollama_url=state['ollama_url'])
        return {
            'idea': result['idea'],
            'retry_count': 0,
            'current_stage': 'idea'
        }

    def lore_node(state: ZoneGenerationState) -> dict:
        """Узел генерации лора"""
        print("\n🔧 ЭТАП 2/7: Генерация лора и атмосферы")
        result = lore_agent(state, ollama_url=state['ollama_url'])
        return {'lore': result['lore'], 'current_stage': 'lore'}

    def structure_node(state: ZoneGenerationState) -> dict:
        """Узел генерации структуры"""
        print("\n🔧 ЭТАП 3/7: Генерация топологии комнат")
        result = structure_agent(state, ollama_url=state['ollama_url'])
        return {'structure': result['structure'], 'current_stage': 'structure'}

    def rooms_node(state: ZoneGenerationState) -> dict:
        """Узел генерации комнат"""
        print("\n🔧 ЭТАП 4/7: Генерация описаний комнат")
        result = rooms_agent(state, ollama_url=state['ollama_url'])
        return {'rooms': result['rooms'], 'current_stage': 'rooms'}

    def mobs_node(state: ZoneGenerationState) -> dict:
        """Узел генерации мобов"""
        print("\n🔧 ЭТАП 5/7: Генерация мобов")
        result = mobs_agent(state, ollama_url=state['ollama_url'])
        return {'mobiles': result['mobiles'], 'current_stage': 'mobs'}

    def objects_node(state: ZoneGenerationState) -> dict:
        """Узел генерации объектов"""
        print("\n🔧 ЭТАП 6/7: Генерация объектов и лута")
        result = objects_agent(state, ollama_url=state['ollama_url'])
        return {'objects': result['objects'], 'current_stage': 'objects'}

    def quests_node(state: ZoneGenerationState) -> dict:
        """Узел генерации квестов"""
        print("\n🔧 ЭТАП 7/7: Генерация квестов")
        result = quests_agent(state, ollama_url=state['ollama_url'])
        return {'quests': result['quests'], 'current_stage': 'quests'}

    # === УЗЛЫ HUMAN-IN-THE-LOOP ===

    def human_review_node(state: ZoneGenerationState) -> dict:
        """Узел для human review"""
        if not state['interactive']:
            return {'human_approved': True}

        # Определяем текущий этап
        stage = state.get('current_stage', 'unknown')
        stage_names = {
            'idea': 'Концепция зоны',
            'lore': 'Лор и атмосфера',
            'structure': 'Топология комнат',
            'rooms': 'Описания комнат',
            'mobs': 'Мобы',
            'objects': 'Объекты и лут',
            'quests': 'Квесты'
        }
        stage_name = stage_names.get(stage, stage)

        print(f"\n{'='*60}")
        print(f"👤 REVIEW: {stage_name}")
        print(f"{'='*60}")

        # Показываем краткую информацию о сгенерированном этапе
        _show_stage_preview(state, stage)

        choice = user_choice(
            "Что делать дальше?",
            ["Одобрить и продолжить", "Редактировать", "Регенерировать"]
        )

        if choice == 0:  # Одобрить
            return {'human_approved': True, 'retry_count': 0}
        elif choice == 1:  # Редактировать
            # TODO: Запустить редактор
            print("⚠️  Редактирование пока не реализовано в LangGraph режиме")
            return {'human_approved': True, 'retry_count': 0}
        else:  # Регенерировать
            retry_count = state.get('retry_count', 0) + 1
            if retry_count >= max_retry:
                print(f"⚠️  Достигнут лимит попыток ({max_retry}), продолжаем")
                return {'human_approved': True, 'retry_count': 0}
            return {'human_approved': False, 'retry_count': retry_count}

    def _show_stage_preview(state: ZoneGenerationState, stage: str):
        """Показать preview сгенерированных данных этапа"""
        if stage == 'idea':
            idea = state.get('idea', {})
            print(f"   Название: {idea.get('name', 'N/A')}")
            print(f"   Тип: {idea.get('zone_type', 'N/A')}")
            print(f"   Уровни: {idea.get('level_range', 'N/A')}")
            print(f"   Комнат (план): {idea.get('estimated_rooms', 'N/A')}")
        elif stage == 'lore':
            lore = state.get('lore', {})
            theme = lore.get('theme', '')[:100] + '...' if len(lore.get('theme', '')) > 100 else lore.get('theme', '')
            print(f"   Тема: {theme}")
            print(f"   Атмосфера: {lore.get('atmosphere', 'N/A')}")
        elif stage == 'structure':
            structure = state.get('structure', {})
            print(f"   Комнат: {structure.get('total_rooms', 'N/A')}")
            print(f"   Топология: {structure.get('topology_type', 'N/A')}")
            print(f"   Секций: {len(structure.get('sections', []))}")
        elif stage == 'rooms':
            rooms = state.get('rooms', [])
            print(f"   Сгенерировано комнат: {len(rooms)}")
            for i, room in enumerate(rooms[:3]):  # Первые 3
                print(f"   • {room.get('name', f'Room {i+1}')}")
        elif stage == 'mobs':
            mobs = state.get('mobiles', [])
            print(f"   Сгенерировано мобов: {len(mobs)}")
            for mob in mobs[:3]:  # Первые 3
                name = mob.get('name', {}).get('nominative', 'N/A')
                level = mob.get('level', '?')
                role = mob.get('role', 'N/A')
                print(f"   • {name} (L{level} {role})")
        elif stage == 'objects':
            objects = state.get('objects', [])
            print(f"   Сгенерировано объектов: {len(objects)}")
            for obj in objects[:3]:  # Первые 3
                name = obj.get('name', {}).get('nominative', 'N/A')
                obj_type = obj.get('type', 'N/A')
                print(f"   • {name} ({obj_type})")
        elif stage == 'quests':
            quests = state.get('quests', [])
            print(f"   Сгенерировано квестов: {len(quests)}")
            for quest in quests:
                print(f"   • {quest.get('name', 'N/A')}")

    # === УЗЛЫ ВАЛИДАЦИИ ===

    def validation_node(state: ZoneGenerationState) -> dict:
        """Узел валидации зоны"""
        print("\n📊 Валидация зоны...")

        # Собираем YAML для валидации
        try:
            zone_yaml = assemble_zone_yaml(state)

            # Временный файл для валидации
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(zone_yaml)
                temp_path = Path(f.name)

            # Запускаем validator
            from .agents.refiner_agent import run_validator
            errors, warnings, score = run_validator(temp_path)

            # Удаляем временный файл
            temp_path.unlink()

            print(f"✓ Балл: {score}/100")
            print(f"  Ошибок: {len(errors)}")
            print(f"  Предупреждений: {len(warnings)}")

            should_refine = (score < target_score or len(errors) > 0)

            return {
                'validation_score': score,
                'errors': errors,
                'warnings': warnings,
                'should_refine': should_refine,
                'refinement_iteration': 0
            }

        except Exception as e:
            print(f"⚠️  Ошибка валидации: {e}")
            return {
                'validation_score': 0,
                'errors': [str(e)],
                'warnings': [],
                'should_refine': True,
                'refinement_iteration': 0
            }

    def refinement_node(state: ZoneGenerationState) -> dict:
        """Узел рефайнмента"""
        iteration = state.get('refinement_iteration', 0) + 1
        max_iterations = GENERATION_CONFIG.get('max_refinement_iterations', 3)

        if iteration > max_iterations:
            print(f"\n⚠️  Достигнут лимит итераций рефайнмента ({max_iterations})")
            return {'should_refine': False}

        print(f"\n🔧 Рефайнмент (итерация {iteration}/{max_iterations})")

        # TODO: Интегрировать refiner_agent
        # Пока просто помечаем что рефайнмент прошёл
        return {
            'refinement_iteration': iteration,
            'should_refine': False  # Временно отключаем циклы
        }

    # === ДОБАВЛЕНИЕ УЗЛОВ В ГРАФ ===

    workflow.add_node("idea", idea_node)
    workflow.add_node("lore", lore_node)
    workflow.add_node("structure", structure_node)
    workflow.add_node("rooms", rooms_node)
    workflow.add_node("mobs", mobs_node)
    workflow.add_node("objects", objects_node)
    workflow.add_node("quests", quests_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("refinement", refinement_node)

    if interactive:
        workflow.add_node("human_review", human_review_node)

    # === РЁБРА (ПЕРЕХОДЫ) ===

    # Начало: idea
    workflow.set_entry_point("idea")

    # Последовательная цепочка генерации
    if interactive:
        # С human review после каждого этапа

        # Все этапы ведут к human_review
        workflow.add_edge("idea", "human_review")
        workflow.add_edge("lore", "human_review")
        workflow.add_edge("structure", "human_review")
        workflow.add_edge("rooms", "human_review")
        workflow.add_edge("mobs", "human_review")
        workflow.add_edge("objects", "human_review")
        workflow.add_edge("quests", "human_review")

        # Единая routing функция на основе current_stage и human_approved
        def route_after_review(state: ZoneGenerationState) -> Literal[
            "idea", "lore", "structure", "rooms", "mobs", "objects", "quests", "validation"
        ]:
            """Роутинг после human review на основе текущего этапа"""
            stage = state.get('current_stage', 'idea')
            approved = state.get('human_approved', True)

            # Маппинг: этап → следующий этап
            next_stage_map = {
                'idea': 'lore',
                'lore': 'structure',
                'structure': 'rooms',
                'rooms': 'mobs',
                'mobs': 'objects',
                'objects': 'quests',
                'quests': 'validation'
            }

            if approved:
                # Одобрено - переход к следующему этапу
                return next_stage_map.get(stage, 'validation')
            else:
                # Не одобрено - повтор текущего этапа
                return stage

        workflow.add_conditional_edges("human_review", route_after_review)

    else:
        # Без review - прямая цепочка
        workflow.add_edge("idea", "lore")
        workflow.add_edge("lore", "structure")
        workflow.add_edge("structure", "rooms")
        workflow.add_edge("rooms", "mobs")
        workflow.add_edge("mobs", "objects")
        workflow.add_edge("objects", "quests")
        workflow.add_edge("quests", "validation")

    # После валидации - либо refinement, либо конец
    def after_validation(state: ZoneGenerationState) -> Literal["refinement", END]:
        return "refinement" if state['should_refine'] else END

    workflow.add_conditional_edges("validation", after_validation)

    # После refinement - повторная валидация
    workflow.add_edge("refinement", "validation")

    # === КОМПИЛЯЦИЯ С CHECKPOINTS ===

    # SQLite saver для persistent checkpoints
    checkpoint_dir = Path(".checkpoints")
    checkpoint_dir.mkdir(exist_ok=True)
    checkpoint_db = checkpoint_dir / "langgraph_checkpoints.db"

    with SqliteSaver.from_conn_string(str(checkpoint_db)) as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)
        return app


def run_zone_generation(
    theme: str,
    level_range: tuple[int, int],
    ollama_url: str = "http://localhost:11434",
    interactive: bool = True,
    output_dir: str = "zones/draft/",
    resume_thread_id: str = None
) -> Path:
    """
    Запуск генерации зоны через LangGraph

    Args:
        theme: Тема зоны
        level_range: Диапазон уровней
        ollama_url: URL Ollama API
        interactive: Интерактивный режим
        output_dir: Директория для сохранения

    Returns:
        Путь к сгенерированному файлу
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "LangGraph не установлен.\n"
            "Установите: pip install langgraph langchain-core"
        )

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          ZONE GENERATOR - LangGraph Mode                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Создаём граф
    app = create_zone_graph(interactive=interactive)

    # Thread ID для checkpoints
    if resume_thread_id:
        thread_id = resume_thread_id
        print(f"📂 Продолжение генерации: {thread_id}\n")
    else:
        # Генерируем уникальный thread_id
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        thread_id = f"zone_{timestamp}_{unique_id}"
        print(f"🆔 Thread ID: {thread_id}")
        print(f"   Для продолжения используйте: --resume {thread_id}\n")

        # Сохраняем thread_id в файл
        thread_file = Path(output_dir) / ".last_thread_id"
        thread_file.parent.mkdir(parents=True, exist_ok=True)
        with open(thread_file, 'w') as f:
            f.write(thread_id)

    # Начальное состояние
    initial_state = {
        'user_theme': theme,
        'level_range': level_range,
        'ollama_url': ollama_url,
        'interactive': interactive,
        'validation_score': 0,
        'refinement_iteration': 0,
        'errors': [],
        'warnings': [],
        'should_refine': False,
        'human_approved': True,
        'retry_count': 0,
        'current_stage': 'idea'
    }

    # Конфигурация для checkpoints
    config = {"configurable": {"thread_id": thread_id}}

    # Запускаем граф
    try:
        final_state = None
        for output in app.stream(initial_state, config):
            # Выводим промежуточные результаты
            for key, value in output.items():
                print(f"\n✓ Узел '{key}' завершён")
            final_state = output

        if not final_state:
            raise RuntimeError("Граф не вернул результат")

        # Берём последнее состояние
        state_key = list(final_state.keys())[0]
        final_zone_state = final_state[state_key]

        # Собираем финальный YAML
        zone_yaml = assemble_zone_yaml(final_zone_state)

        # Сохраняем
        zone_name = final_zone_state['idea'].get('name', 'generated_zone')
        safe_name = sanitize_filename(zone_name)
        output_path = Path(output_dir) / f"{safe_name}.yaml"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(zone_yaml)

        print(f"\n✅ Зона сохранена: {output_path}")
        print(f"📊 Итоговый балл: {final_zone_state.get('validation_score', 0)}/100")

        return output_path

    except KeyboardInterrupt:
        print("\n\n⚠️  Генерация прервана пользователем")
        print(f"   Прогресс сохранён в checkpoint")
        print(f"\n📂 Для продолжения используйте:")
        print(f"   python -m tools.generator.main --resume {thread_id}\n")
        raise

    except Exception as e:
        print(f"\n❌ Ошибка генерации: {e}")
        raise
