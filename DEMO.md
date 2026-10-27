# DEMO: «Кряква» в деле

Сценарий показа на защите: сначала прогон тестов, потом короткая «прогулка» утки через публичный интерфейс. Занимает 3–4 минуты.

Подготовка: Python 3.8+, терминал открыт в корне репозитория.

## 1. Тесты

```bash
python -m unittest discover -s tests -v
```

Ожидаемый хвост вывода (unittest идёт по классам в алфавитном порядке, поэтому последним печатается TC-20, а не TC-31):

```
test_tc20_blow_tanks_errors (test_duck_submarine.TestTanks.test_tc20_blow_tanks_errors)
TC-20. Неверные аргументы продува и нехватка воздуха; атомарность. ... ok

----------------------------------------------------------------------
Ran 31 tests in 0.004s

OK
```

Если спросят про отдельный сценарий, его можно запустить по ID, например «Щуку-диверсанта»:

```bash
python -m unittest discover -s tests -k tc27 -v
```

## 2. Прогулка утки

Код ниже сохранить как `demo.py` в корне репозитория (или вставить в интерактивный `python`, запущенный из корня) и запустить `python demo.py`.

```python
from duck_submarine import DuckSubmarine, DuckError

duck = DuckSubmarine("Кряква", mass_kg=80, ballast_capacity_l=200,
                     max_speed_kmh=10)
print(duck.get_status())

print("по поверхности 10 км:", duck.move(10, "surface"), "ч")
print("сеть пройдём?", duck.can_overcome("net"))

duck.flood_tanks(120)
print("можно нырять?", duck.can_dive)
print("под водой 5 км:", duck.move(5, "underwater"), "ч")
print("сеть пройдём?", duck.can_overcome("net"))

duck.quack(3)
print("воздух после трёх кряков:", duck.air)

for distance, terrain in ((20, "underwater"), (1, "ground")):
    try:
        duck.move(distance, terrain)
    except DuckError as error:
        print(type(error).__name__, "-", error)

duck.breach_hull()
print("после укуса щуки:", duck.get_status())

duck.patch_hull()
duck.refill_air(1000)
print("после ремонта и накачки:", duck.get_status())
```

Вывод (Python 3.12.3):

```
{'name': 'Кряква', 'air': 100.0, 'position_km': 0.0, 'is_submerged': False, 'hull_intact': True, 'ballast_l': 0.0, 'can_dive': False}
по поверхности 10 км: 1.0 ч
сеть пройдём? False
можно нырять? True
под водой 5 км: 1.0 ч
сеть пройдём? True
воздух после трёх кряков: 67.0
DuckOutOfAir - not enough air: required 80, have 67
DuckCannotWaddle - duck cannot waddle: the ground is not water
после укуса щуки: {'name': 'Кряква', 'air': 67.0, 'position_km': 15.0, 'is_submerged': False, 'hull_intact': False, 'ballast_l': 120.0, 'can_dive': False}
после ремонта и накачки: {'name': 'Кряква', 'air': 100.0, 'position_km': 15.0, 'is_submerged': False, 'hull_intact': True, 'ballast_l': 120.0, 'can_dive': True}
```

## 3. Что проговорить по ходу

1. **Порог погружения.** У эталонной утки цистерны на 200 л, порог — половина, 100 л. На пустых цистернах `can_dive == False`, после `flood_tanks(120)` — `True`. Само затопление утку не топит: под воду она уходит только через `move(..., "underwater")`.
2. **Препятствия смотрят на текущее состояние.** Сеть на поверхности не пройти, даже когда нырнуть уже можно. После погружения та же проверка даёт `True`.
3. **Атомарность.** На 20 км под водой нужно 80 воздуха, а есть 67. Выбрасывается `DuckOutOfAir` с `required` и `available`, а позиция и воздух остаются прежними: в статусе после укуса щуки по-прежнему 15 км и 67.
4. **Порядок проверок.** Суша отбивается `DuckCannotWaddle` раньше любых проверок воздуха (SPEC 6.3), в сценарии TC-29 это видно при нулевом воздухе.
5. **Пробоина.** `breach_hull()` — аварийное всплытие, `can_dive` становится `False`, хотя балласт 120 л. После `patch_hull()` утка остаётся на поверхности, а `refill_air(1000)` упирается в потолок 100.

## 4. Если спросят про спорные места

Открытые вопросы к ТЗ (огромные `int`, подклассы чисел, формат сообщений) собраны в [BUGREPORT.md](BUGREPORT.md). Там же записано, как каждый из них сделан в коде сейчас.
