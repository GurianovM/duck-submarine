# Утка-подлодка «Кряква»

Проект №9 практической работы «Безумное средство передвижения», стихия — вода.
Подводная лодка в форме резиновой утки: плавает по поверхности, ныряет на затопленных балластных цистернах, крякает и не умеет ходить по суше.

| Роль | Участник |
|---|---|
| A — автор ТЗ и тестов | Клинный А. И. (№9) |
| B — ревьюер | Ивчук М. П. (№7) |
| C — ревьюер | Гурьянов М. С. (№5) |
| D — разработчик | Игнатьева М. С. (№8) |

Требования к аппарату — в [SPEC.md](SPEC.md), тест-кейсы — в [TEST_CASES.md](TEST_CASES.md).

## Что нужно

Python 3.8 или новее. Внешних зависимостей нет, используется только стандартная библиотека.
Реализация проверялась на Python 3.12.3.

## Структура

```
duck-submarine/
├── duck_submarine.py         # реализация: DuckSubmarine и исключения
├── tests/
│   └── test_duck_submarine.py
├── SPEC.md                   # ТЗ
├── TEST_CASES.md             # Test Case Specification
├── BUGREPORT.md              # вопросы разработчика к ТЗ и тестам
├── ACCEPTANCE.md, FIXES.md   # приёмка
├── DEMO.md, PRESENTATION.md  # материалы к защите
├── CHANGELOG.md, RESPONSES.md, REVIEW_*.md
└── docs/kryakva.svg
```

## Запуск тестов

Из корня репозитория:

```bash
python -m unittest discover -s tests -v
```

На Windows, если `python` не найден, то же самое через `py`:

```powershell
py -m unittest discover -s tests -v
```

Должно получиться:

```
Ran 31 tests in 0.004s

OK
```

Пара моментов, на которых легко споткнуться:

- запускать нужно именно из корня: модуль `duck_submarine.py` лежит там, и `python -m` добавляет текущую папку в `sys.path`;
- `python -m unittest` без `discover -s tests` тесты не найдёт (в `tests/` нет `__init__.py`), будет `NO TESTS RAN`;
- `python tests/test_duck_submarine.py` тоже не сработает: в этом случае Python ищет модуль внутри `tests/` и падает с `ModuleNotFoundError`.

## Пример

```python
from duck_submarine import DuckSubmarine, DuckOutOfAir

duck = DuckSubmarine("Кряква", mass_kg=80, ballast_capacity_l=200,
                     max_speed_kmh=10)
duck.move(10, "surface")       # 1.0 ч, воздух 90
duck.flood_tanks(120)          # балласт выше порога 100 л
duck.move(5, "underwater")     # 1.0 ч, воздух 70, под водой
duck.can_overcome("net")       # True: под сетью можно только нырнув

try:
    duck.move(20, "underwater")
except DuckOutOfAir as error:
    print(error.required, error.available)   # 80.0 70.0
```

Подробный прогон с выводом — в [DEMO.md](DEMO.md).

## Вопросы к ТЗ

Всё, что при реализации оказалось неоднозначным, записано в [BUGREPORT.md](BUGREPORT.md) вместе с тем, как это сделано в коде сейчас. Тесты и SPEC разработчиком не менялись.
