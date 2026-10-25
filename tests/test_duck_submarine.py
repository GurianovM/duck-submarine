"""Тесты для утки-подлодки «Кряква» (SPEC.md v1.0, TEST_CASES.md v1.0).

Запуск из корня репозитория:

    python -m unittest discover -s tests -v

Модульные тесты построены по паттерну AAA (Arrange-Act-Assert),
сценарные — по Given-When-Then через тестовые обёртки Pilot и Pike.
Каждый тест содержит ID своего тест-кейса в имени и в docstring.
"""

import unittest

from duck_submarine import (
    CrazyVehicleError,
    DuckCannotWaddle,
    DuckError,
    DuckHullBreached,
    DuckOutOfAir,
    DuckSubmarine,
    DuckTooBuoyant,
)

PLACES = 6
NAN = float("nan")
INF = float("inf")


def make_duck(**overrides):
    """Эталонный аппарат из SPEC 4: 80 кг, 200 л, 10 км/ч, воздух 100."""
    params = {
        "name": "Кряква",
        "mass_kg": 80.0,
        "ballast_capacity_l": 200.0,
        "max_speed_kmh": 10.0,
        "air": 100.0,
    }
    params.update(overrides)
    return DuckSubmarine(**params)


def snapshot(duck):
    """Наблюдаемое состояние аппарата для проверки атомарности."""
    return (
        duck.air,
        duck.position_km,
        duck.is_submerged,
        duck.hull_intact,
        duck.ballast_l,
    )


# Тестовые обёртки для сценариев (не являются частью реализации)


class Pilot:
    """Эмулятор пилота: управляет аппаратом на доменном языке."""

    def __init__(self, duck):
        self._duck = duck

    def плыть_по_поверхности(self, distance_km):
        return self._duck.move(distance_km, "surface")

    def плыть_под_водой(self, distance_km):
        return self._duck.move(distance_km, "underwater")

    def идти_по_суше(self, distance_km):
        return self._duck.move(distance_km, "ground")

    def может_преодолеть(self, obstacle):
        return self._duck.can_overcome(obstacle)

    def затопить_цистерны(self, liters):
        self._duck.flood_tanks(liters)

    def продуть_цистерны(self, liters):
        self._duck.blow_tanks(liters)

    def крякнуть(self, times):
        self._duck.quack(times)

    def накачать_воздух(self, amount):
        self._duck.refill_air(amount)

    def заделать_пробоину(self):
        self._duck.patch_hull()


class Pike:
    """Щука-диверсант: событие внешнего мира, пробивает корпус."""

    def укусить(self, duck):
        duck.breach_hull()


# Модульные тесты (AAA)


class TestConstructor(unittest.TestCase):
    """SPEC 3.0, 3.2, 3.3."""

    def test_tc01_init_valid_defaults(self):
        """TC-01. Корректное создание, начальное состояние, int → float."""
        # Arrange / Act
        duck = DuckSubmarine(
            " Кряква ", mass_kg=80, ballast_capacity_l=200,
            max_speed_kmh=10, air=100,
        )

        # Assert
        self.assertEqual(duck.name, " Кряква ")
        self.assertAlmostEqual(duck.mass_kg, 80.0, places=PLACES)
        self.assertAlmostEqual(duck.ballast_capacity_l, 200.0, places=PLACES)
        self.assertAlmostEqual(duck.max_speed_kmh, 10.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 100.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 0.0, places=PLACES)
        self.assertAlmostEqual(duck.ballast_l, 0.0, places=PLACES)
        self.assertAlmostEqual(duck.dive_threshold_l, 100.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)
        self.assertIs(duck.hull_intact, True)
        self.assertIs(duck.can_dive, False)
        for attr in ("mass_kg", "ballast_capacity_l", "max_speed_kmh", "air",
                     "position_km", "ballast_l", "dive_threshold_l"):
            with self.subTest(attr=attr):
                self.assertIsInstance(getattr(duck, attr), float)

        default_air = DuckSubmarine("Кряква", 80, 200, 10)
        self.assertAlmostEqual(default_air.air, 100.0, places=PLACES)

    def test_tc02_init_invalid_values_raise(self):
        """TC-02. Недопустимые значения конструктора → ValueError."""
        for bad_name in ("", "   "):
            with self.subTest(name=bad_name):
                with self.assertRaises(ValueError):
                    make_duck(name=bad_name)

        for param in ("mass_kg", "ballast_capacity_l", "max_speed_kmh"):
            for value in (0, -1, NAN, INF, -INF):
                with self.subTest(param=param, value=value):
                    with self.assertRaises(ValueError):
                        make_duck(**{param: value})

        for bad_air in (-0.1, 100.1, NAN, INF, -INF):
            with self.subTest(air=bad_air):
                with self.assertRaises(ValueError):
                    make_duck(air=bad_air)

        for ok_air in (0, 100):
            with self.subTest(air=ok_air):
                duck = make_duck(air=ok_air)
                self.assertAlmostEqual(duck.air, float(ok_air), places=PLACES)

    def test_tc03_init_wrong_types_raise(self):
        """TC-03. Неверные типы → TypeError; типы проверяются раньше значений."""
        cases = [
            {"name": 123},
            {"name": None},
            {"mass_kg": "80"},
            {"mass_kg": True},
            {"ballast_capacity_l": None},
            {"max_speed_kmh": [10]},
            {"air": "50"},
            {"air": True},
            {"air": None},
            {"name": "", "mass_kg": "80"},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(TypeError):
                    make_duck(**overrides)

    def test_tc04_attributes_read_only(self):
        """TC-04. Публичные атрибуты доступны только для чтения."""
        # Arrange
        duck = make_duck()
        assignments = [
            ("name", "Другая"),
            ("mass_kg", 1.0),
            ("ballast_capacity_l", 1.0),
            ("max_speed_kmh", 1.0),
            ("air", 50.0),
            ("position_km", 5.0),
            ("is_submerged", True),
            ("hull_intact", False),
            ("ballast_l", 10.0),
            ("dive_threshold_l", 1.0),
            ("can_dive", True),
        ]
        for attr, value in assignments:
            with self.subTest(attr=attr):
                # Act / Assert
                with self.assertRaises(AttributeError):
                    setattr(duck, attr, value)


class TestMove(unittest.TestCase):
    """SPEC 3.4.1, 6.3."""

    def test_tc05_move_surface(self):
        """TC-05. Плавание по поверхности: скорость max_speed, расход 1 ед./км."""
        # Arrange
        duck = make_duck()

        # Act
        hours = duck.move(5, "surface")

        # Assert
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(duck.air, 95.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 5.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)

    def test_tc06_move_underwater_and_surfacing(self):
        """TC-06. Погружение: скорость ×0.5, расход 4 ед./км; всплытие через surface."""
        # Arrange
        duck = make_duck()
        duck.flood_tanks(120)

        # Act
        hours = duck.move(5, "underwater")

        # Assert
        self.assertAlmostEqual(hours, 1.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 80.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 5.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # Act: всплытие
        hours = duck.move(2, "surface")

        # Assert
        self.assertAlmostEqual(hours, 0.2, places=PLACES)
        self.assertAlmostEqual(duck.air, 78.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 7.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)

    def test_tc07_move_ground_raises_cannot_waddle(self):
        """TC-07. Суша → DuckCannotWaddle, состояние не меняется."""
        # Arrange
        on_surface = make_duck()
        submerged = make_duck()
        submerged.flood_tanks(120)
        submerged.move(1, "underwater")

        for duck in (on_surface, submerged):
            with self.subTest(is_submerged=duck.is_submerged):
                before = snapshot(duck)

                # Act / Assert
                with self.assertRaises(DuckCannotWaddle):
                    duck.move(1, "ground")
                self.assertEqual(snapshot(duck), before)

    def test_tc08_move_invalid_args(self):
        """TC-08. Дистанция ≤ 0, nan/inf, неизвестная среда → ValueError; неверные типы → TypeError."""
        # Arrange
        duck = make_duck()
        before = snapshot(duck)

        value_cases = ((0, "surface"), (-5, "surface"), (NAN, "surface"),
                       (INF, "surface"), (-INF, "surface"),
                       (1, "space"), (1, ""))
        for args in value_cases:
            with self.subTest(kind="value", args=args):
                # Act / Assert
                with self.assertRaises(ValueError):
                    duck.move(*args)

        type_cases = (("10", "surface"), (True, "surface"),
                      (None, "surface"), ([1], "surface"),
                      (1, 1), (1, None))
        for args in type_cases:
            with self.subTest(kind="type", args=args):
                with self.assertRaises(TypeError):
                    duck.move(*args)

        self.assertEqual(snapshot(duck), before)

    def test_tc09_move_out_of_air_and_exact_budget(self):
        """TC-09. Нехватка воздуха → DuckOutOfAir; расход ровно равен запасу допустим."""
        with self.subTest(case="поверхность, не хватает"):
            # Arrange
            duck = make_duck(air=10)
            before = snapshot(duck)

            # Act
            with self.assertRaises(DuckOutOfAir) as ctx:
                duck.move(20, "surface")

            # Assert
            self.assertAlmostEqual(ctx.exception.required, 20.0, places=PLACES)
            self.assertAlmostEqual(
                ctx.exception.available, 10.0, places=PLACES)
            self.assertEqual(snapshot(duck), before)

        with self.subTest(case="под водой, не хватает"):
            duck = make_duck(air=10)
            duck.flood_tanks(120)
            before = snapshot(duck)
            with self.assertRaises(DuckOutOfAir) as ctx:
                duck.move(3, "underwater")
            self.assertAlmostEqual(ctx.exception.required, 12.0, places=PLACES)
            self.assertAlmostEqual(
                ctx.exception.available, 10.0, places=PLACES)
            self.assertEqual(snapshot(duck), before)

        with self.subTest(case="поверхность, ровно в ноль"):
            duck = make_duck(air=100)
            hours = duck.move(100, "surface")
            self.assertAlmostEqual(hours, 10.0, places=PLACES)
            self.assertAlmostEqual(duck.air, 0.0, places=PLACES)
            self.assertAlmostEqual(duck.position_km, 100.0, places=PLACES)

        with self.subTest(case="под водой, ровно в ноль"):
            duck = make_duck(air=100)
            duck.flood_tanks(100)
            hours = duck.move(25, "underwater")
            self.assertAlmostEqual(hours, 5.0, places=PLACES)
            self.assertAlmostEqual(duck.air, 0.0, places=PLACES)
            self.assertIs(duck.is_submerged, True)

    def test_tc10_dive_ballast_threshold(self):
        """TC-10. Порог погружения: меньше половины ёмкости → DuckTooBuoyant, ровно половина — можно."""
        for ballast in (0, 99.9):
            with self.subTest(ballast=ballast):
                # Arrange
                duck = make_duck()
                if ballast:
                    duck.flood_tanks(ballast)
                before = snapshot(duck)

                # Act / Assert
                self.assertIs(duck.can_dive, False)
                with self.assertRaises(DuckTooBuoyant):
                    duck.move(1, "underwater")
                self.assertEqual(snapshot(duck), before)

        with self.subTest(ballast=100):
            # Arrange
            duck = make_duck()
            duck.flood_tanks(100)

            # Act
            self.assertIs(duck.can_dive, True)
            duck.move(1, "underwater")

            # Assert
            self.assertIs(duck.is_submerged, True)

    def test_tc11_hull_breach_blocks_dive_not_surface(self):
        """TC-11. Пробитый корпус запрещает погружение, но не плавание по поверхности."""
        # Arrange
        duck = make_duck()
        duck.flood_tanks(150)
        duck.breach_hull()
        before = snapshot(duck)

        # Act / Assert
        self.assertIs(duck.can_dive, False)
        with self.assertRaises(DuckHullBreached):
            duck.move(1, "underwater")
        self.assertEqual(snapshot(duck), before)

        hours = duck.move(1, "surface")
        self.assertAlmostEqual(hours, 0.1, places=PLACES)
        self.assertAlmostEqual(duck.air, 99.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)

    def test_tc12_move_check_priority(self):
        """TC-12. При нескольких нарушениях — первое по порядку SPEC 6.3."""
        with self.subTest(case="пробоина + пустые цистерны"):
            duck = make_duck()
            duck.breach_hull()
            with self.assertRaises(DuckHullBreached):
                duck.move(1, "underwater")

        with self.subTest(case="пустые цистерны + нет воздуха"):
            duck = make_duck(air=0)
            with self.assertRaises(DuckTooBuoyant):
                duck.move(1, "underwater")

        with self.subTest(case="пробоина + нет воздуха"):
            duck = make_duck(air=0)
            duck.flood_tanks(150)
            duck.breach_hull()
            with self.assertRaises(DuckHullBreached):
                duck.move(1, "underwater")

        with self.subTest(case="суша + нет воздуха"):
            duck = make_duck(air=0)
            with self.assertRaises(DuckCannotWaddle):
                duck.move(1, "ground")

        with self.subTest(case="суша + нулевая дистанция"):
            duck = make_duck()
            with self.assertRaises(ValueError):
                duck.move(0, "ground")

        with self.subTest(case="неверный тип + неизвестная среда"):
            duck = make_duck()
            with self.assertRaises(TypeError):
                duck.move("1", "space")

        with self.subTest(case="поверхность + нет воздуха"):
            duck = make_duck(air=0)
            with self.assertRaises(DuckOutOfAir):
                duck.move(1, "surface")


class TestCalculateAir(unittest.TestCase):
    """SPEC 3.4.3."""

    def test_tc13_calculate_air(self):
        """TC-13. Расчёт расхода без изменения состояния и без проверок домена; ошибки параметров."""
        # Arrange
        duck = make_duck()
        before = snapshot(duck)

        # Act / Assert
        self.assertAlmostEqual(duck.calculate_air(10, "surface"), 10.0,
                               places=PLACES)
        self.assertAlmostEqual(duck.calculate_air(10, "underwater"), 40.0,
                               places=PLACES)
        self.assertEqual(snapshot(duck), before)

        poor = make_duck(air=10)
        self.assertAlmostEqual(poor.calculate_air(1000, "underwater"), 4000.0,
                               places=PLACES)
        self.assertAlmostEqual(poor.air, 10.0, places=PLACES)

        breached = make_duck()
        breached.breach_hull()
        self.assertAlmostEqual(breached.calculate_air(10, "underwater"), 40.0,
                               places=PLACES)

        # Проверка переполнения
        self.assertEqual(duck.calculate_air(1e308, "underwater"), INF)

        with self.assertRaises(DuckCannotWaddle):
            duck.calculate_air(1, "ground")
        for args in ((0, "surface"), (NAN, "surface"), (INF, "surface"), (-INF, "surface"), (1, "space")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    duck.calculate_air(*args)
        for args in (("1", "surface"), (True, "surface"), (1, 1)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    duck.calculate_air(*args)
        self.assertEqual(snapshot(duck), before)


class TestCanOvercome(unittest.TestCase):
    """SPEC 3.4.2."""

    def _states(self):
        empty_tanks = make_duck()

        flooded_on_surface = make_duck()
        flooded_on_surface.flood_tanks(150)

        submerged = make_duck()
        submerged.flood_tanks(120)
        submerged.move(1, "underwater")

        breached = make_duck()
        breached.breach_hull()

        submerged_no_air = make_duck(air=20)
        submerged_no_air.flood_tanks(100)
        submerged_no_air.move(5, "underwater")

        at_threshold = make_duck()
        at_threshold.flood_tanks(100)

        return {
            "на поверхности, цистерны пусты":
                (empty_tanks, {"net": False, "shallows": True, "reef": True}),
            "на поверхности, цистерны 150 л":
                (flooded_on_surface,
                 {"net": False, "shallows": False, "reef": True}),
            "под водой":
                (submerged, {"net": True, "shallows": False, "reef": True}),
            "с пробоиной":
                (breached, {"net": False, "shallows": True, "reef": False}),
            "под водой, воздух 0":
                (submerged_no_air,
                 {"net": True, "shallows": False, "reef": True}),
            "на поверхности, цистерны ровно на пороге":
                (at_threshold,
                 {"net": False, "shallows": False, "reef": True}),
        }

    def test_tc14_can_overcome_matrix(self):
        """TC-14. Полная матрица 3 препятствия × 6 состояний; состояние не меняется."""
        for state_name, (duck, expected) in self._states().items():
            for obstacle, result in expected.items():
                with self.subTest(state=state_name, obstacle=obstacle):
                    # Arrange
                    before = snapshot(duck)

                    # Act
                    actual = duck.can_overcome(obstacle)

                    # Assert
                    self.assertIs(actual, result)
                    self.assertEqual(snapshot(duck), before)

    def test_tc15_can_overcome_invalid(self):
        """TC-15. Неизвестное препятствие → ValueError, не строка → TypeError."""
        # Arrange
        duck = make_duck()
        before = snapshot(duck)

        # Act / Assert
        for obstacle in ("mountain", ""):
            with self.subTest(obstacle=obstacle):
                with self.assertRaises(ValueError):
                    duck.can_overcome(obstacle)
        for obstacle in (42, None):
            with self.subTest(obstacle=obstacle):
                with self.assertRaises(TypeError):
                    duck.can_overcome(obstacle)
        self.assertEqual(snapshot(duck), before)


class TestRefillAir(unittest.TestCase):
    """SPEC 3.4.4."""

    def test_tc16_refill_air(self):
        """TC-16. Накачка воздуха не выше 100; неверные аргументы отвергаются."""
        for start, amount, expected in ((20, 50, 70.0),
                                        (50, 1000, 100.0),
                                        (100, 0.5, 100.0)):
            with self.subTest(start=start, amount=amount):
                # Arrange
                duck = make_duck(air=start)

                # Act
                result = duck.refill_air(amount)

                # Assert
                self.assertIsNone(result)
                self.assertAlmostEqual(duck.air, expected, places=PLACES)

        # Arrange
        duck = make_duck(air=50)
        for amount in (0, -5, NAN, INF, -INF):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    duck.refill_air(amount)
        for amount in ("10", True, None):
            with self.subTest(amount=amount):
                with self.assertRaises(TypeError):
                    duck.refill_air(amount)
        self.assertAlmostEqual(duck.air, 50.0, places=PLACES)


class TestTanks(unittest.TestCase):
    """SPEC 3.4.5, 3.4.6."""

    def test_tc17_flood_tanks(self):
        """TC-17. Затопление цистерн: не выше ёмкости, воздух и положение не меняются."""
        # Arrange
        duck = make_duck()

        # Act / Assert
        self.assertIsNone(duck.flood_tanks(120))
        self.assertAlmostEqual(duck.ballast_l, 120.0, places=PLACES)
        duck.flood_tanks(50)
        self.assertAlmostEqual(duck.ballast_l, 170.0, places=PLACES)
        duck.flood_tanks(1000)
        self.assertAlmostEqual(duck.ballast_l, 200.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 100.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)

        fresh = make_duck()
        before = snapshot(fresh)
        for liters in (0, -1, NAN, INF, -INF):
            with self.subTest(liters=liters):
                with self.assertRaises(ValueError):
                    fresh.flood_tanks(liters)
        for liters in ("5", True, None):
            with self.subTest(liters=liters):
                with self.assertRaises(TypeError):
                    fresh.flood_tanks(liters)
        self.assertEqual(snapshot(fresh), before)

    def test_tc18_blow_tanks_values(self):
        """TC-18. Продув: 0.25 ед. воздуха за фактически удалённый литр, не ниже нуля."""
        with self.subTest(case="обычный продув"):
            # Arrange
            duck = make_duck()
            duck.flood_tanks(150)

            # Act
            result = duck.blow_tanks(50)

            # Assert
            self.assertIsNone(result)
            self.assertAlmostEqual(duck.ballast_l, 100.0, places=PLACES)
            self.assertAlmostEqual(duck.air, 87.5, places=PLACES)

        with self.subTest(case="больше, чем есть в цистернах"):
            duck = make_duck()
            duck.flood_tanks(120)
            duck.blow_tanks(1000)
            self.assertAlmostEqual(duck.ballast_l, 0.0, places=PLACES)
            self.assertAlmostEqual(duck.air, 70.0, places=PLACES)

        with self.subTest(case="пустые цистерны, воздуха нет"):
            duck = make_duck(air=0)
            before = snapshot(duck)
            duck.blow_tanks(10)
            self.assertEqual(snapshot(duck), before)

        with self.subTest(case="ровно весь воздух"):
            duck = make_duck(air=10)
            duck.flood_tanks(120)
            duck.move(1, "underwater")
            # Осталось 6 воздуха (10 - 1 * 4)
            result = duck.blow_tanks(24) # 24 * 0.25 = 6
            self.assertIsNone(result)
            self.assertAlmostEqual(duck.air, 0.0, places=PLACES)
            self.assertAlmostEqual(duck.ballast_l, 96.0, places=PLACES)
            self.assertIs(duck.is_submerged, False)
            self.assertAlmostEqual(duck.position_km, 1.0, places=PLACES)

    def test_tc19_blow_tanks_surfacing_rule(self):
        """TC-19. Продув ниже порога под водой — всплытие; ровно на пороге — остаётся."""
        # Arrange
        duck = make_duck()
        duck.flood_tanks(120)
        duck.move(1, "underwater")

        # Act: до порога включительно
        duck.blow_tanks(20)

        # Assert
        self.assertAlmostEqual(duck.ballast_l, 100.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 91.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # Act: ниже порога
        duck.blow_tanks(1)

        # Assert
        self.assertAlmostEqual(duck.ballast_l, 99.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 90.75, places=PLACES)
        self.assertIs(duck.is_submerged, False)
        self.assertAlmostEqual(duck.position_km, 1.0, places=PLACES)

    def test_tc20_blow_tanks_errors(self):
        """TC-20. Неверные аргументы продува и нехватка воздуха; атомарность."""
        # Arrange
        duck = make_duck()
        duck.flood_tanks(150)
        before = snapshot(duck)

        # Act / Assert
        for liters in (0, -1, NAN, INF, -INF):
            with self.subTest(liters=liters):
                with self.assertRaises(ValueError):
                    duck.blow_tanks(liters)
        for liters in ("5", True, None):
            with self.subTest(liters=liters):
                with self.assertRaises(TypeError):
                    duck.blow_tanks(liters)
        self.assertEqual(snapshot(duck), before)

        poor = make_duck(air=5)
        poor.flood_tanks(150)
        before = snapshot(poor)
        with self.assertRaises(DuckOutOfAir) as ctx:
            poor.blow_tanks(50)
        self.assertAlmostEqual(ctx.exception.required, 12.5, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 5.0, places=PLACES)
        self.assertEqual(snapshot(poor), before)


class TestQuack(unittest.TestCase):
    """SPEC 3.4.7."""

    def test_tc21_quack(self):
        """TC-21. Кряк: 1 ед. воздуха за раз в любом состоянии; ошибки аргументов и нехватка воздуха."""
        with self.subTest(case="на поверхности"):
            # Arrange
            duck = make_duck()

            # Act
            result = duck.quack(3)

            # Assert
            self.assertIsNone(result)
            self.assertAlmostEqual(duck.air, 97.0, places=PLACES)
            self.assertAlmostEqual(duck.position_km, 0.0, places=PLACES)

        with self.subTest(case="под водой"):
            duck = make_duck()
            duck.flood_tanks(120)
            duck.move(1, "underwater")
            duck.quack(2)
            self.assertAlmostEqual(duck.air, 94.0, places=PLACES)
            self.assertIs(duck.is_submerged, True)

        with self.subTest(case="с пробоиной"):
            duck = make_duck()
            duck.breach_hull()
            duck.quack(1)
            self.assertAlmostEqual(duck.air, 99.0, places=PLACES)
            self.assertIs(duck.hull_intact, False)

        with self.subTest(case="ровно весь воздух"):
            duck = make_duck(air=3)
            duck.quack(3)
            self.assertAlmostEqual(duck.air, 0.0, places=PLACES)

        duck = make_duck()
        for times in (0, -1):
            with self.subTest(times=times):
                with self.assertRaises(ValueError):
                    duck.quack(times)
        for times in (2.5, True, "3", None):
            with self.subTest(times=times):
                with self.assertRaises(TypeError):
                    duck.quack(times)
        self.assertAlmostEqual(duck.air, 100.0, places=PLACES)

        with self.subTest(case="не хватает воздуха"):
            poor = make_duck(air=4)
            with self.assertRaises(DuckOutOfAir) as ctx:
                poor.quack(5)
            self.assertAlmostEqual(ctx.exception.required, 5.0, places=PLACES)
            self.assertAlmostEqual(ctx.exception.available, 4.0, places=PLACES)
            self.assertAlmostEqual(poor.air, 4.0, places=PLACES)


class TestHull(unittest.TestCase):
    """SPEC 3.4.8, 3.4.9."""

    def test_tc22_breach_hull(self):
        """TC-22. Пробоина под водой — аварийное всплытие; остальное не меняется; повтор безопасен."""
        # Arrange
        duck = make_duck()
        duck.flood_tanks(150)
        duck.move(5, "underwater")

        # Act
        duck.breach_hull()
        duck.breach_hull()

        # Assert
        self.assertIs(duck.hull_intact, False)
        self.assertIs(duck.is_submerged, False)
        self.assertIs(duck.can_dive, False)
        self.assertAlmostEqual(duck.air, 80.0, places=PLACES)
        self.assertAlmostEqual(duck.ballast_l, 150.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 5.0, places=PLACES)

        with self.subTest(case="на поверхности"):
            surface = make_duck()
            surface.breach_hull()
            self.assertIs(surface.hull_intact, False)
            self.assertIs(surface.is_submerged, False)
            self.assertAlmostEqual(surface.air, 100.0, places=PLACES)

    def test_tc23_patch_hull(self):
        """TC-23. Заделка пробоины: аппарат остаётся на поверхности, can_dive зависит от балласта и воздуха."""
        with self.subTest(case="цистерны заполнены"):
            # Arrange
            duck = make_duck()
            duck.flood_tanks(150)
            duck.breach_hull()

            # Act
            duck.patch_hull()

            # Assert
            self.assertIs(duck.hull_intact, True)
            self.assertIs(duck.is_submerged, False)
            self.assertIs(duck.can_dive, True)

        with self.subTest(case="цистерны пусты"):
            duck = make_duck()
            duck.breach_hull()
            duck.patch_hull()
            self.assertIs(duck.hull_intact, True)
            self.assertIs(duck.can_dive, False)

        with self.subTest(case="воздух 0"):
            duck = make_duck(air=0)
            duck.flood_tanks(150)
            duck.breach_hull()
            duck.patch_hull()
            self.assertIs(duck.hull_intact, True)
            self.assertIs(duck.can_dive, False)

        with self.subTest(case="корпус и так цел"):
            duck = make_duck()
            duck.flood_tanks(150)
            before = snapshot(duck)
            duck.patch_hull()
            self.assertEqual(snapshot(duck), before)

        with self.subTest(case="целый корпус под водой"):
            duck = make_duck()
            duck.flood_tanks(120)
            duck.move(1, "underwater") # Теперь утка под водой
            before = snapshot(duck)
            duck.patch_hull()
            self.assertIs(duck.hull_intact, True)
            self.assertIs(duck.is_submerged, True) # Она осталась под водой!
            self.assertEqual(snapshot(duck), before)


class TestStatusAndExceptions(unittest.TestCase):
    """SPEC 3.4.10, 6.1."""

    def test_tc24_get_status(self):
        """TC-24. Статус: ровно нужные ключи, верные значения, это копия."""
        # Arrange
        duck = make_duck()
        duck.flood_tanks(120)
        duck.move(5, "underwater")

        # Act
        status = duck.get_status()

        # Assert
        self.assertEqual(
            set(status),
            {"name", "air", "position_km", "is_submerged", "hull_intact",
             "ballast_l", "can_dive"},
        )
        self.assertEqual(status["name"], "Кряква")
        self.assertAlmostEqual(status["air"], 80.0, places=PLACES)
        self.assertAlmostEqual(status["position_km"], 5.0, places=PLACES)
        self.assertIs(status["is_submerged"], True)
        self.assertIs(status["hull_intact"], True)
        self.assertAlmostEqual(status["ballast_l"], 120.0, places=PLACES)
        self.assertIs(status["can_dive"], True)

        status["air"] = 0.0
        status["is_submerged"] = False
        self.assertAlmostEqual(duck.air, 80.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

    def test_tc25_exception_hierarchy(self):
        """TC-25. Иерархия доменных исключений."""
        for exc in (DuckCannotWaddle, DuckOutOfAir,
                    DuckTooBuoyant, DuckHullBreached):
            with self.subTest(exc=exc.__name__):
                self.assertTrue(issubclass(exc, DuckError))
        self.assertTrue(issubclass(DuckError, CrazyVehicleError))
        self.assertTrue(issubclass(CrazyVehicleError, Exception))

        by_position = DuckOutOfAir(6, 2)
        self.assertAlmostEqual(by_position.required, 6.0, places=PLACES)
        self.assertAlmostEqual(by_position.available, 2.0, places=PLACES)
        by_name = DuckOutOfAir(required=7, available=3)
        self.assertAlmostEqual(by_name.required, 7.0, places=PLACES)
        self.assertAlmostEqual(by_name.available, 3.0, places=PLACES)


# Сценарные тесты (Given-When-Then)


class TestScenarios(unittest.TestCase):
    """SPEC 4.2."""

    def test_tc26_lily_delivery(self):
        """TC-26. Сценарий 5 «Доставка кувшинок»."""
        # Given эталонная «Кряква» с воздухом 100 на поверхности
        duck = make_duck()
        pilot = Pilot(duck)

        # When пилот плывёт по поверхности 10 км
        hours = pilot.плыть_по_поверхности(10)
        # Then время 1.0 ч, воздух 90, пройдено 10 км, на поверхности
        self.assertAlmostEqual(hours, 1.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 90.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 10.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)

        # When пилот проверяет мель и сеть / Then мель пройдёт, сеть нет
        self.assertIs(pilot.может_преодолеть("shallows"), True)
        self.assertIs(pilot.может_преодолеть("net"), False)

        # When пилот затапливает цистерны на 120 л
        pilot.затопить_цистерны(120)
        # Then нырнуть можно, мель теперь не пройти
        self.assertAlmostEqual(duck.ballast_l, 120.0, places=PLACES)
        self.assertIs(duck.can_dive, True)
        self.assertIs(pilot.может_преодолеть("shallows"), False)

        # When пилот плывёт под водой 5 км
        hours = pilot.плыть_под_водой(5)
        # Then время 1.0 ч, воздух 70, пройдено 15 км, под водой
        self.assertAlmostEqual(hours, 1.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 70.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 15.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # When пилот проверяет сеть / Then пройдёт
        self.assertIs(pilot.может_преодолеть("net"), True)

        # When пилот крякает 3 раза / Then воздух 67
        pilot.крякнуть(3)
        self.assertAlmostEqual(duck.air, 67.0, places=PLACES)

        # When пилот пытается плыть под водой 20 км
        with self.assertRaises(DuckOutOfAir) as ctx:
            pilot.плыть_под_водой(20)
        # Then нужно 80, есть 67, состояние прежнее
        self.assertAlmostEqual(ctx.exception.required, 80.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 67.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 15.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 67.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # When пилот накачивает 30 воздуха и плывёт под водой 20 км
        pilot.накачать_воздух(30)
        hours = pilot.плыть_под_водой(20)
        # Then время 4.0 ч, воздух 17, пройдено 35 км, под водой
        self.assertAlmostEqual(hours, 4.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 17.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 35.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

    def test_tc27_pike_saboteur(self):
        """TC-27. Сценарий 6 «Щука-диверсант»."""
        # Given эталонная «Кряква» с воздухом 100, цистерны затоплены на 150 л
        duck = make_duck()
        pilot = Pilot(duck)
        pike = Pike()
        pilot.затопить_цистерны(150)

        # When пилот плывёт под водой 4 км
        hours = pilot.плыть_под_водой(4)
        # Then время 0.8 ч, воздух 84, пройдено 4 км, под водой
        self.assertAlmostEqual(hours, 0.8, places=PLACES)
        self.assertAlmostEqual(duck.air, 84.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 4.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # When щука кусает корпус
        pike.укусить(duck)
        # Then пробоина, аварийное всплытие, нырять нельзя
        self.assertIs(duck.hull_intact, False)
        self.assertIs(duck.is_submerged, False)
        self.assertIs(duck.can_dive, False)

        # When пилот пытается нырнуть на 2 км / Then DuckHullBreached
        with self.assertRaises(DuckHullBreached):
            pilot.плыть_под_водой(2)
        self.assertAlmostEqual(duck.air, 84.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 4.0, places=PLACES)

        # When пилот проверяет риф / Then не пройдёт
        self.assertIs(pilot.может_преодолеть("reef"), False)

        # When пилот плывёт по поверхности 6 км
        hours = pilot.плыть_по_поверхности(6)
        # Then время 0.6 ч, воздух 78, пройдено 10 км
        self.assertAlmostEqual(hours, 0.6, places=PLACES)
        self.assertAlmostEqual(duck.air, 78.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 10.0, places=PLACES)

        # When пилот заделывает пробоину
        pilot.заделать_пробоину()
        # Then корпус цел, нырять можно, аппарат по-прежнему на поверхности
        self.assertIs(duck.hull_intact, True)
        self.assertIs(duck.can_dive, True)
        self.assertIs(duck.is_submerged, False)
        # And риф пройдёт
        self.assertIs(pilot.может_преодолеть("reef"), True)

        # When пилот плывёт под водой 5 км
        hours = pilot.плыть_под_водой(5)
        # Then время 1.0 ч, воздух 58, пройдено 15 км, под водой
        self.assertAlmostEqual(hours, 1.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 58.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 15.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

    def test_tc28_emergency_surfacing(self):
        """TC-28. Сценарий 7 «Аварийное всплытие»."""
        # Given «Поплавок»: 60 кг, цистерны 100 л, 8 км/ч, воздух 60
        duck = make_duck(name="Поплавок", mass_kg=60,
                         ballast_capacity_l=100, max_speed_kmh=8, air=60)
        pilot = Pilot(duck)
        # Then порог погружения 50 л
        self.assertAlmostEqual(duck.dive_threshold_l, 50.0, places=PLACES)

        # When пилот затапливает цистерны до краёв и плывёт под водой 4 км
        pilot.затопить_цистерны(100)
        hours = pilot.плыть_под_водой(4)
        # Then время 1.0 ч, воздух 44, под водой
        self.assertAlmostEqual(hours, 1.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 44.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # When пилот продувает 30 л
        pilot.продуть_цистерны(30)
        # Then балласт 70, воздух 36.5, всё ещё под водой, сеть пройдёт
        self.assertAlmostEqual(duck.ballast_l, 70.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 36.5, places=PLACES)
        self.assertIs(duck.is_submerged, True)
        self.assertIs(pilot.может_преодолеть("net"), True)

        # When пилот продувает ещё 20 л
        pilot.продуть_цистерны(20)
        # Then балласт ровно на пороге 50, воздух 31.5, всё ещё под водой
        self.assertAlmostEqual(duck.ballast_l, 50.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 31.5, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # When пилот продувает ещё 10 л
        pilot.продуть_цистерны(10)
        # Then балласт 40 ниже порога: автоматическое всплытие, воздух 29
        self.assertAlmostEqual(duck.ballast_l, 40.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 29.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)
        # And мель пройдёт, сеть нет
        self.assertIs(pilot.может_преодолеть("shallows"), True)
        self.assertIs(pilot.может_преодолеть("net"), False)

        # When пилот пытается нырнуть на 1 км / Then DuckTooBuoyant
        before = snapshot(duck)
        with self.assertRaises(DuckTooBuoyant):
            pilot.плыть_под_водой(1)
        self.assertEqual(snapshot(duck), before)

        # When пилот затапливает 80 л / Then балласт 100 (не больше ёмкости)
        pilot.затопить_цистерны(80)
        self.assertAlmostEqual(duck.ballast_l, 100.0, places=PLACES)

        # When пилот плывёт под водой 2 км
        hours = pilot.плыть_под_водой(2)
        # Then время 0.5 ч, воздух 21, пройдено 6 км, под водой
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(duck.air, 21.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 6.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

    def test_tc29_duck_on_shore(self):
        """TC-29. Сценарий 8 «Утка на берегу»."""
        # Given эталонная «Кряква» с воздухом 40 на поверхности
        duck = make_duck(air=40)
        pilot = Pilot(duck)

        # When пилот пытается идти по суше 1 км
        before = snapshot(duck)
        with self.assertRaises(DuckCannotWaddle):
            pilot.идти_по_суше(1)
        # Then состояние не изменилось
        self.assertEqual(snapshot(duck), before)
        # And сеть не пройти, мель и риф пройдут
        self.assertIs(pilot.может_преодолеть("net"), False)
        self.assertIs(pilot.может_преодолеть("shallows"), True)
        self.assertIs(pilot.может_преодолеть("reef"), True)

        # When пилот плывёт по поверхности 30 км
        hours = pilot.плыть_по_поверхности(30)
        # Then время 3.0 ч, воздух 10, пройдено 30 км
        self.assertAlmostEqual(hours, 3.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 10.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 30.0, places=PLACES)

        # When пилот пытается идти по суше 5 км / Then снова DuckCannotWaddle
        with self.assertRaises(DuckCannotWaddle):
            pilot.идти_по_суше(5)
        self.assertAlmostEqual(duck.position_km, 30.0, places=PLACES)

        # When пилот крякает 10 раз / Then воздух 0
        pilot.крякнуть(10)
        self.assertAlmostEqual(duck.air, 0.0, places=PLACES)

        # When пилот пытается плыть по поверхности 1 км
        with self.assertRaises(DuckOutOfAir) as ctx:
            pilot.плыть_по_поверхности(1)
        # Then нужно 1, есть 0
        self.assertAlmostEqual(ctx.exception.required, 1.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)

        # When пилот пытается идти по суше 1 км при воздухе 0
        # Then DuckCannotWaddle (проверка суши идёт раньше проверки воздуха)
        with self.assertRaises(DuckCannotWaddle):
            pilot.идти_по_суше(1)

        # When пилот накачивает 1000 воздуха / Then воздух 100 (не больше максимума)
        pilot.накачать_воздух(1000)
        self.assertAlmostEqual(duck.air, 100.0, places=PLACES)

        # Then итог
        self.assertAlmostEqual(duck.position_km, 30.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)

    def test_tc30_last_bubble(self):
        """TC-30. Сценарий 9 «Последний пузырёк»."""
        # Given эталонная «Кряква» с воздухом 100, цистерны затоплены на 100 л
        duck = make_duck()
        pilot = Pilot(duck)
        pilot.затопить_цистерны(100)

        # When пилот плывёт под водой 25 км
        hours = pilot.плыть_под_водой(25)
        # Then время 5.0 ч, воздух 0, пройдено 25 км, под водой
        self.assertAlmostEqual(hours, 5.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 0.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 25.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)
        # And нырять заново нельзя, но сеть и риф пройдут, мель нет
        self.assertIs(duck.can_dive, False)
        self.assertIs(pilot.может_преодолеть("net"), True)
        self.assertIs(pilot.может_преодолеть("reef"), True)
        self.assertIs(pilot.может_преодолеть("shallows"), False)

        # When пилот пытается всплыть на 0.5 км
        with self.assertRaises(DuckOutOfAir) as ctx:
            pilot.плыть_по_поверхности(0.5)
        # Then нужно 0.5, есть 0, аппарат остаётся под водой
        self.assertAlmostEqual(ctx.exception.required, 0.5, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)
        self.assertAlmostEqual(duck.position_km, 25.0, places=PLACES)

        # When пилот пытается крякнуть / Then нужно 1, есть 0
        with self.assertRaises(DuckOutOfAir) as ctx:
            pilot.крякнуть(1)
        self.assertAlmostEqual(ctx.exception.required, 1.0, places=PLACES)

        # When пилот пытается продуть 20 л / Then нужно 5, есть 0, балласт прежний
        with self.assertRaises(DuckOutOfAir) as ctx:
            pilot.продуть_цистерны(20)
        self.assertAlmostEqual(ctx.exception.required, 5.0, places=PLACES)
        self.assertAlmostEqual(duck.ballast_l, 100.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # When пилот затапливает ещё 50 л (воздух для этого не нужен)
        pilot.затопить_цистерны(50)
        # Then балласт 150
        self.assertAlmostEqual(duck.ballast_l, 150.0, places=PLACES)

        # When пилот накачивает 10 воздуха / Then воздух 10, нырять можно
        pilot.накачать_воздух(10)
        self.assertAlmostEqual(duck.air, 10.0, places=PLACES)
        self.assertIs(duck.can_dive, True)

        # When пилот всплывает на 5 км
        hours = pilot.плыть_по_поверхности(5)
        # Then время 0.5 ч, воздух 5, пройдено 30 км, на поверхности
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(duck.air, 5.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 30.0, places=PLACES)
        self.assertIs(duck.is_submerged, False)

        # When пилот ныряет на 1 км
        hours = pilot.плыть_под_водой(1)
        # Then время 0.2 ч, воздух 1, пройдено 31 км, под водой
        self.assertAlmostEqual(hours, 0.2, places=PLACES)
        self.assertAlmostEqual(duck.air, 1.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 31.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

    def test_tc31_exactly_at_threshold(self):
        """TC-31. Сценарий 10 «Ровно на пороге»."""
        # Given «Ровня»: 70 кг, цистерны 100 л, 20 км/ч, воздух 30
        duck = make_duck(name="Ровня", mass_kg=70,
                         ballast_capacity_l=100, max_speed_kmh=20, air=30)
        pilot = Pilot(duck)
        pike = Pike()

        # When пилот затапливает 50 л
        pilot.затопить_цистерны(50)
        # Then балласт равен порогу, нырять можно, мель не пройти
        self.assertAlmostEqual(duck.ballast_l, duck.dive_threshold_l,
                               places=PLACES)
        self.assertIs(duck.can_dive, True)
        self.assertIs(pilot.может_преодолеть("shallows"), False)

        # When пилот плывёт под водой 4 км
        hours = pilot.плыть_под_водой(4)
        # Then время 0.4 ч, воздух 14, пройдено 4 км, под водой
        self.assertAlmostEqual(hours, 0.4, places=PLACES)
        self.assertAlmostEqual(duck.air, 14.0, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 4.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)

        # When щука кусает корпус
        pike.укусить(duck)
        # Then аварийное всплытие, нырять нельзя
        self.assertIs(duck.is_submerged, False)
        self.assertIs(duck.hull_intact, False)
        self.assertIs(duck.can_dive, False)

        # When пилот продувает 50 л
        pilot.продуть_цистерны(50)
        # Then балласт 0, воздух 1.5
        self.assertAlmostEqual(duck.ballast_l, 0.0, places=PLACES)
        self.assertAlmostEqual(duck.air, 1.5, places=PLACES)

        # When пилот заделывает пробоину
        pilot.заделать_пробоину()
        # Then корпус цел, но нырять нельзя — цистерны пусты
        self.assertIs(duck.hull_intact, True)
        self.assertIs(duck.can_dive, False)

        # When пилот пытается нырнуть на 1 км / Then DuckTooBuoyant
        with self.assertRaises(DuckTooBuoyant):
            pilot.плыть_под_водой(1)

        # When пилот затапливает 50 л / Then нырять можно (воздух 1.5 > 0)
        pilot.затопить_цистерны(50)
        self.assertIs(duck.can_dive, True)

        # When пилот пытается нырнуть на 1 км
        before = snapshot(duck)
        with self.assertRaises(DuckOutOfAir) as ctx:
            pilot.плыть_под_водой(1)
        # Then нужно 4, есть 1.5, состояние прежнее
        self.assertAlmostEqual(ctx.exception.required, 4.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 1.5, places=PLACES)
        self.assertEqual(snapshot(duck), before)

        # When пилот накачивает 10 воздуха и ныряет на 2 км
        pilot.накачать_воздух(10)
        hours = pilot.плыть_под_водой(2)
        # Then время 0.2 ч, воздух 3.5, пройдено 6 км, под водой
        self.assertAlmostEqual(hours, 0.2, places=PLACES)
        self.assertAlmostEqual(duck.air, 3.5, places=PLACES)
        self.assertAlmostEqual(duck.position_km, 6.0, places=PLACES)
        self.assertIs(duck.is_submerged, True)


if __name__ == "__main__":
    unittest.main()
