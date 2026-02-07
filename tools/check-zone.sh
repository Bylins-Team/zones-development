#!/bin/bash
# Быстрая проверка зоны

if [ $# -eq 0 ]; then
    echo "Использование: $0 <файл_зоны.yaml>"
    exit 1
fi

ZONE_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$ZONE_FILE" ]; then
    echo "Ошибка: файл '$ZONE_FILE' не найден"
    exit 1
fi

echo "Проверка зоны: $ZONE_FILE"
echo "================================"
echo

# Запускаем валидатор
python3 "$SCRIPT_DIR/validator.py" "$ZONE_FILE"

exit $?
