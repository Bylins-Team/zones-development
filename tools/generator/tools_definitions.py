"""
Определения функций (tools) для function calling в LLM

Эти функции LLM может вызывать для точных вычислений
вместо того чтобы пытаться считать математику сам.
"""

from typing import List, Dict


# === TOOLS ДЛЯ БАЛАНСА МОБОВ ===

BALANCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calc_mob_exp",
            "description": "Рассчитать EXP для моба по формуле: level² × role_mult. TRASH=10, ELITE=15, MINI_BOSS=20, BOSS=30.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Уровень моба (1-50)"
                    },
                    "role": {
                        "type": "string",
                        "enum": ["TRASH", "ELITE", "MINI_BOSS", "BOSS"],
                        "description": "Роль моба в зоне"
                    }
                },
                "required": ["level", "role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calc_mob_gold",
            "description": "Рассчитать диапазон золота для моба: level × role_mult × (0.7-1.3). TRASH=5, ELITE=10, MINI_BOSS=15, BOSS=25.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Уровень моба (1-50)"
                    },
                    "role": {
                        "type": "string",
                        "enum": ["TRASH", "ELITE", "MINI_BOSS", "BOSS"],
                        "description": "Роль моба в зоне"
                    }
                },
                "required": ["level", "role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calc_damage_dice",
            "description": "Рассчитать урон моба в формате NdN+B. Формула зависит от level и role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Уровень моба (1-50)"
                    },
                    "role": {
                        "type": "string",
                        "enum": ["TRASH", "ELITE", "MINI_BOSS", "BOSS"],
                        "description": "Роль моба в зоне"
                    }
                },
                "required": ["level", "role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calc_player_hp",
            "description": "Рассчитать средний HP игрока на уровне (для баланса боссов).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Уровень игрока (1-50)"
                    }
                },
                "required": ["level"]
            }
        }
    }
]


# === TOOLS ДЛЯ СТРУКТУРЫ ===

STRUCTURE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "validate_room_graph",
            "description": "Проверить что граф комнат валидный (нет битых связей, все комнаты достижимы).",
            "parameters": {
                "type": "object",
                "properties": {
                    "rooms": {
                        "type": "array",
                        "description": "Список комнат с exits",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "exits": {
                                    "type": "object",
                                    "properties": {
                                        "north": {"type": "string"},
                                        "south": {"type": "string"},
                                        "east": {"type": "string"},
                                        "west": {"type": "string"},
                                        "up": {"type": "string"},
                                        "down": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                },
                "required": ["rooms"]
            }
        }
    }
]


# === ФУНКЦИИ-ОБРАБОТЧИКИ ===

def execute_tool_call(tool_name: str, arguments: Dict) -> Dict:
    """
    Выполнить вызов функции от LLM

    Args:
        tool_name: Имя функции
        arguments: Аргументы функции

    Returns:
        Результат выполнения
    """
    from .balance import (
        calc_mob_exp,
        calc_mob_gold,
        calc_damage_dice,
        calc_player_hp
    )

    if tool_name == "calc_mob_exp":
        level = arguments["level"]
        role = arguments["role"]
        exp = calc_mob_exp(level, role)
        return {"exp": exp}

    elif tool_name == "calc_mob_gold":
        level = arguments["level"]
        role = arguments["role"]
        gold_min, gold_max = calc_mob_gold(level, role)
        return {"gold_min": gold_min, "gold_max": gold_max}

    elif tool_name == "calc_damage_dice":
        level = arguments["level"]
        role = arguments["role"]
        damage = calc_damage_dice(level, role)
        return {"damage_dice": damage}

    elif tool_name == "calc_player_hp":
        level = arguments["level"]
        hp = calc_player_hp(level)
        return {"player_hp": hp}

    elif tool_name == "validate_room_graph":
        rooms = arguments["rooms"]
        # TODO: Реализовать валидацию графа
        return {"valid": True, "errors": []}

    else:
        return {"error": f"Unknown tool: {tool_name}"}


def get_tools_for_stage(stage: str) -> List[Dict]:
    """
    Получить список tools для этапа генерации

    Args:
        stage: Название этапа (idea, lore, mobs, etc.)

    Returns:
        Список определений функций для LLM
    """
    if stage == "mobs":
        return BALANCE_TOOLS

    elif stage == "structure":
        return STRUCTURE_TOOLS

    else:
        return []  # Другие этапы пока без tools
