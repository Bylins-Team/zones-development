# LLM-оценка зон

## Обзор

Валидатор зон поддерживает экспертную оценку с использованием больших языковых моделей (LLM) через Ollama.

## Установка и настройка

### Запуск Ollama через Docker

```bash
# Настроить nvidia-container-toolkit (один раз)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Запустить контейнер Ollama с GPU
docker run -d --gpus all --restart=unless-stopped --name ollama \
  -p 11434:11434 -v ollama:/root/.ollama ollama/ollama

# Проверить доступ к GPU
docker exec ollama nvidia-smi

# Скачать модель (рекомендуется Qwen2.5:14b для русского языка)
docker exec ollama ollama pull qwen2.5:14b

# Проверить доступные модели
docker exec ollama ollama list
```

### Использование без GPU (CPU mode)

Для CPU используйте меньшую модель (qwen2.5:7b) или увеличьте таймаут:

```bash
docker run -d --restart=unless-stopped --name ollama \
  -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
docker exec ollama ollama pull qwen2.5:7b
```

## Использование валидатора

### Базовое использование (с LLM)

```bash
python3 tools/validator.py zones/draft/salt-mines-example.yaml
```

### Отключение LLM-оценки

```bash
python3 tools/validator.py --no-llm zones/draft/salt-mines-example.yaml
```

### Custom Ollama URL

```bash
python3 tools/validator.py --ollama-url http://server:11434 zones/draft/zone.yaml
```

## Критерии LLM-оценки

LLM оценивает зону по трем критериям (максимум 20 баллов):

1. **Атмосферность и погружение** (0-8 баллов)
   - Насколько описания создают яркую атмосферу
   - Степень погружения игрока в мир зоны
   - Эмоциональное воздействие текстов

2. **Уникальность и оригинальность** (0-6 баллов)
   - Отличие от типичных MUD-зон
   - Креативность подхода к теме
   - Оригинальность игровых механик

3. **Соответствие фольклору** (0-6 баллов)
   - Точность использования славянского фольклора
   - Глубина фольклорной основы
   - Аутентичность мифологических элементов

## Распределение баллов в валидаторе

После интеграции LLM система оценок:

| Категория                    | Баллы |
|------------------------------|-------|
| Техническая корректность     | 20    |
| Структурная полнота          | 15    |
| Качество текста              | 25    |
| Игровой баланс               | 15    |
| Атмосферность (автоматика)   | 5     |
| **LLM экспертная оценка**    | **20**|
| **ИТОГО**                    | **100**|

## Рекомендуемые модели

### Для русского языка

1. **qwen2.5:14b** (рекомендуется)
   - Отличное качество русского языка
   - ~9GB VRAM/RAM
   - Хороший баланс качества и скорости

2. **qwen2.5:32b** (для мощных систем)
   - Лучшее качество оценки
   - ~19GB VRAM/RAM
   - Медленнее, но точнее

3. **qwen2.5:7b** (для слабых систем)
   - Быстрая работа
   - ~4.5GB VRAM/RAM
   - Приемлемое качество

### Смена модели

Отредактируйте `tools/validator.py`, метод `_call_ollama()`:

```python
def _call_ollama(self, prompt: str, model: str = "qwen2.5:14b") -> Optional[str]:
    # Измените model на нужную
```

## Производительность

- **Первый запрос**: 30-60 секунд (загрузка модели в память)
- **Последующие**: 10-30 секунд (модель уже в памяти)
- **Таймаут**: 180 секунд (настраивается в коде)

## Troubleshooting

### LLM-запрос таймаутится

Увеличьте таймаут в `validator.py`:

```python
with urllib.request.urlopen(req, timeout=300) as response:  # 5 минут
```

### Ollama недоступен

Проверьте статус контейнера:

```bash
docker ps | grep ollama
curl http://localhost:11434/api/tags
```

### Модель слишком медленная

Используйте меньшую модель (qwen2.5:7b) или отключите LLM-оценку с флагом `--no-llm`.

## Пример вывода

```
======================================================================
ЭКСПЕРТНАЯ ОЦЕНКА (LLM):
  Баллы: 16/20
  Обоснование: Описания создают яркую атмосферу, погружая игрока
  в гнетущее и мистическое пространство соляных копей. Уникальность
  проявляется через использование соли не только как элемент дизайна,
  но и как символ тюрьмы для душ, что отличает зону от типичных
  текстовых ролевых игр. Соответствие славянскому фольклору высокое
  благодаря использованию соляного мифа о защите и превращении в
  тюрьму для душ.
======================================================================
ОЦЕНКА: 89/100 баллов
✓✓ ХОРОШО - нужны минорные правки (89.0%)
======================================================================
```

## Интеграция в CI/CD

Для автоматической проверки зон без LLM в CI:

```yaml
# .github/workflows/validate-zones.yml
- name: Validate zones
  run: |
    for zone in zones/draft/*.yaml; do
      python3 tools/validator.py --no-llm "$zone"
    done
```

Для полной проверки с LLM на выделенном сервере:

```yaml
- name: Validate with LLM
  run: |
    python3 tools/validator.py \
      --ollama-url http://llm-server:11434 \
      zones/draft/zone.yaml
```
