#!/usr/bin/env python3
"""
Проверка установленных зависимостей для Zone Generator
"""

import sys

def check_dependencies():
    """Проверить все необходимые зависимости"""
    print("Python версия:", sys.version)
    print("Python путь:", sys.executable)
    print("\n" + "="*60)
    print("Проверка зависимостей:")
    print("="*60 + "\n")

    deps = {
        'pyyaml': 'PyYAML',
        'langgraph': 'LangGraph',
        'langchain_core': 'LangChain Core',
        'tqdm': 'tqdm'
    }

    missing = []
    installed = []

    for module, name in deps.items():
        try:
            __import__(module)
            import importlib
            mod = importlib.import_module(module)
            version = getattr(mod, '__version__', 'unknown')
            print(f"✅ {name}: {version}")
            installed.append(name)
        except ImportError as e:
            print(f"❌ {name}: НЕ УСТАНОВЛЕН ({e})")
            missing.append(name)

    print("\n" + "="*60)

    if missing:
        print(f"\n⚠️  Отсутствуют зависимости: {', '.join(missing)}")
        print("\nУстановите:")
        print("  pip install langgraph langchain-core pyyaml tqdm")
        return False
    else:
        print("\n✅ Все зависимости установлены!")

        # Дополнительная проверка LangGraph импортов
        print("\n" + "="*60)
        print("Проверка LangGraph импортов:")
        print("="*60 + "\n")

        try:
            from langgraph.graph import StateGraph, END
            print("✅ langgraph.graph.StateGraph")
            print("✅ langgraph.graph.END")
        except ImportError as e:
            print(f"❌ langgraph.graph: {e}")
            return False

        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            print("✅ langgraph.checkpoint.sqlite.SqliteSaver")
        except ImportError as e:
            print(f"❌ langgraph.checkpoint.sqlite: {e}")
            return False

        print("\n✅ LangGraph полностью работоспособен!")
        return True

if __name__ == '__main__':
    success = check_dependencies()
    sys.exit(0 if success else 1)
