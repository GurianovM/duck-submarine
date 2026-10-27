"""Утка-подлодка «Кряква».

Реализация по SPEC.md v1.0 (проект №9, автор ТЗ — Клинный А. И.).
Разработчик: Игнатьева М. С.
"""

import math
import sys

SURFACE = "surface"
UNDERWATER = "underwater"
GROUND = "ground"
TERRAINS = (SURFACE, UNDERWATER, GROUND)

NET = "net"
SHALLOWS = "shallows"
REEF = "reef"
OBSTACLES = (NET, SHALLOWS, REEF)

MAX_AIR = 100.0
DIVE_THRESHOLD_RATIO = 0.5
SPEED_RATIO = {SURFACE: 1.0, UNDERWATER: 0.5}
AIR_PER_KM = {SURFACE: 1.0, UNDERWATER: 4.0}
AIR_PER_QUACK = 1.0
AIR_PER_BLOWN_LITER = 0.25


class CrazyVehicleError(Exception):
    """Базовое исключение безумных транспортов."""


class DuckError(CrazyVehicleError):
    """Базовое доменное исключение утки-подлодки."""


class DuckCannotWaddle(DuckError):
    """Утка не умеет передвигаться по суше."""


class DuckTooBuoyant(DuckError):
    """Цистерны заполнены меньше порога погружения."""


class DuckHullBreached(DuckError):
    """Нырять с пробитым корпусом нельзя."""


class DuckOutOfAir(DuckError):
    """Расход воздуха больше текущего запаса.

    Атрибуты ``required`` и ``available`` — сколько воздуха нужно
    и сколько есть на момент ошибки.
    """

    def __init__(self, required: float, available: float) -> None:
        self.required = float(required)
        self.available = float(available)
        super().__init__(
            f"not enough air: required {self.required:g}, "
            f"have {self.available:g}"
        )


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_number_type(value: object, param: str) -> None:
    if not _is_number(value):
        raise TypeError(f"{param} must be a number")


def _check_string_type(value: object, param: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{param} must be a string")


def _to_finite(value: float, param: str) -> float:
    """Приводит число к float; nan, ±inf и слишком большие int отвергаются."""
    try:
        number = float(value)
    except OverflowError:
        raise ValueError(f"{param} must be finite") from None
    if not math.isfinite(number):
        raise ValueError(f"{param} must be finite")
    return number


def _int_to_float(value: int) -> float:
    """Целое, не помещающееся во float, считается бесконечностью."""
    return float(value) if value <= sys.float_info.max else math.inf


def _to_positive(value: float, param: str) -> float:
    number = _to_finite(value, param)
    if number <= 0:
        raise ValueError(f"{param} must be positive")
    return number


class DuckSubmarine:
    """Подводная лодка в форме резиновой утки с балластными цистернами."""

    def __init__(
        self,
        name: str,
        mass_kg: float,
        ballast_capacity_l: float,
        max_speed_kmh: float,
        air: float = 100.0,
    ) -> None:
        _check_string_type(name, "name")
        numbers = (
            ("mass_kg", mass_kg),
            ("ballast_capacity_l", ballast_capacity_l),
            ("max_speed_kmh", max_speed_kmh),
            ("air", air),
        )
        for param, value in numbers:
            _check_number_type(value, param)

        if not name.strip():
            raise ValueError("name must not be empty")
        mass = _to_positive(mass_kg, "mass_kg")
        capacity = _to_positive(ballast_capacity_l, "ballast_capacity_l")
        speed = _to_positive(max_speed_kmh, "max_speed_kmh")
        start_air = _to_finite(air, "air")
        if not 0.0 <= start_air <= MAX_AIR:
            raise ValueError("air must be between 0 and 100")

        self._name = name
        self._mass_kg = mass
        self._ballast_capacity_l = capacity
        self._max_speed_kmh = speed
        self._air = start_air
        self._position_km = 0.0
        self._ballast_l = 0.0
        self._is_submerged = False
        self._hull_intact = True

    @property
    def name(self) -> str:
        """Имя аппарата (хранится без обрезки пробелов)."""
        return self._name

    @property
    def mass_kg(self) -> float:
        """Полная масса аппарата с пилотом, кг."""
        return self._mass_kg

    @property
    def ballast_capacity_l(self) -> float:
        """Объём балластных цистерн, л."""
        return self._ballast_capacity_l

    @property
    def max_speed_kmh(self) -> float:
        """Максимальная скорость на поверхности, км/ч."""
        return self._max_speed_kmh

    @property
    def air(self) -> float:
        """Текущий запас воздуха, 0…100."""
        return self._air

    @property
    def position_km(self) -> float:
        """Суммарное пройденное расстояние, км."""
        return self._position_km

    @property
    def is_submerged(self) -> bool:
        """Находится ли аппарат под водой."""
        return self._is_submerged

    @property
    def hull_intact(self) -> bool:
        """Цел ли корпус."""
        return self._hull_intact

    @property
    def ballast_l(self) -> float:
        """Текущий уровень воды в цистернах, л."""
        return self._ballast_l

    @property
    def dive_threshold_l(self) -> float:
        """Порог погружения: половина объёма цистерн, л."""
        return self._ballast_capacity_l * DIVE_THRESHOLD_RATIO

    @property
    def can_dive(self) -> bool:
        """Допускает ли текущее состояние погружение (SPEC 3.3)."""
        return (
            self._hull_intact
            and self._ballast_l >= self.dive_threshold_l
            and self._air > 0
        )

    def move(self, distance_km: float, terrain: str) -> float:
        """Перемещает аппарат и возвращает время в пути, ч.

        Погружение и всплытие происходят через выбор среды:
        ``"underwater"`` — под водой, ``"surface"`` — по поверхности.

        Raises:
            TypeError: дистанция не число или среда не строка.
            ValueError: дистанция не положительная и конечная,
                неизвестная среда.
            DuckCannotWaddle: среда ``"ground"``.
            DuckHullBreached: погружение с пробитым корпусом.
            DuckTooBuoyant: погружение с балластом ниже порога.
            DuckOutOfAir: на перемещение не хватает воздуха.
        """
        distance = self._validate_route(distance_km, terrain)

        if terrain == UNDERWATER:
            if not self._hull_intact:
                raise DuckHullBreached("hull is breached")
            if self._ballast_l < self.dive_threshold_l:
                raise DuckTooBuoyant(
                    f"too buoyant to dive: ballast {self._ballast_l:g} l, "
                    f"need {self.dive_threshold_l:g} l"
                )

        cost = distance * AIR_PER_KM[terrain]
        if cost > self._air:
            raise DuckOutOfAir(required=cost, available=self._air)

        hours = distance / (self._max_speed_kmh * SPEED_RATIO[terrain])
        self._air -= cost
        self._position_km += distance
        self._is_submerged = terrain == UNDERWATER
        return hours

    def can_overcome(self, obstacle: str) -> bool:
        """Проверяет препятствие по текущему состоянию, ничего не меняя.

        Raises:
            TypeError: препятствие не строка.
            ValueError: неизвестное препятствие.
        """
        _check_string_type(obstacle, "obstacle")
        if obstacle not in OBSTACLES:
            raise ValueError(f"unknown obstacle: {obstacle}")

        if obstacle == NET:
            return self._is_submerged
        if obstacle == SHALLOWS:
            return (
                not self._is_submerged
                and self._ballast_l < self.dive_threshold_l
            )
        return self._hull_intact

    def calculate_air(self, distance_km: float, terrain: str) -> float:
        """Возвращает расход воздуха на перемещение, состояние не меняет.

        Проверяет только параметры и сушу; корпус, балласт и запас
        воздуха не учитываются. При переполнении float возвращает inf.

        Raises:
            TypeError: дистанция не число или среда не строка.
            ValueError: дистанция не положительная и конечная,
                неизвестная среда.
            DuckCannotWaddle: среда ``"ground"``.
        """
        distance = self._validate_route(distance_km, terrain)
        return distance * AIR_PER_KM[terrain]

    def refill_air(self, amount: float) -> None:
        """Накачивает воздух, запас не превышает 100.

        Raises:
            TypeError: количество не число.
            ValueError: количество не положительное и конечное.
        """
        _check_number_type(amount, "amount")
        added = _to_positive(amount, "amount")
        self._air = min(MAX_AIR, self._air + added)

    def flood_tanks(self, liters: float) -> None:
        """Набирает воду в цистерны, не больше их объёма.

        Сама по себе не вызывает погружения и не тратит воздух.

        Raises:
            TypeError: объём не число.
            ValueError: объём не положительный и конечный.
        """
        _check_number_type(liters, "liters")
        added = _to_positive(liters, "liters")
        self._ballast_l = min(
            self._ballast_capacity_l, self._ballast_l + added
        )

    def blow_tanks(self, liters: float) -> None:
        """Продувает цистерны сжатым воздухом.

        Удаляется не больше воды, чем есть в цистернах; воздух тратится
        только на фактически удалённый объём. Если под водой балласт
        опускается ниже порога, аппарат всплывает.

        Raises:
            TypeError: объём не число.
            ValueError: объём не положительный и конечный.
            DuckOutOfAir: на продув не хватает воздуха.
        """
        _check_number_type(liters, "liters")
        requested = _to_positive(liters, "liters")

        removed = min(requested, self._ballast_l)
        cost = removed * AIR_PER_BLOWN_LITER
        if cost > self._air:
            raise DuckOutOfAir(required=cost, available=self._air)

        self._ballast_l -= removed
        self._air -= cost
        if self._is_submerged and self._ballast_l < self.dive_threshold_l:
            self._is_submerged = False

    def quack(self, times: int) -> None:
        """Крякает ``times`` раз, на каждый кряк уходит 1 ед. воздуха.

        Raises:
            TypeError: ``times`` не int (bool тоже не принимается).
            ValueError: ``times`` меньше 1.
            DuckOutOfAir: кряков больше, чем воздуха.
        """
        if isinstance(times, bool) or not isinstance(times, int):
            raise TypeError("times must be an int")
        if times < 1:
            raise ValueError("times must be at least 1")
        if times > self._air:
            raise DuckOutOfAir(
                required=_int_to_float(times), available=self._air
            )

        self._air -= times * AIR_PER_QUACK

    def breach_hull(self) -> None:
        """Пробоина: корпус пробит, аппарат аварийно всплывает."""
        self._hull_intact = False
        self._is_submerged = False

    def patch_hull(self) -> None:
        """Заделывает пробоину; остальное состояние не меняется."""
        self._hull_intact = True

    def get_status(self) -> dict:
        """Возвращает новый словарь-снимок состояния."""
        return {
            "name": self._name,
            "air": self._air,
            "position_km": self._position_km,
            "is_submerged": self._is_submerged,
            "hull_intact": self._hull_intact,
            "ballast_l": self._ballast_l,
            "can_dive": self.can_dive,
        }

    def _validate_route(self, distance_km: float, terrain: str) -> float:
        _check_number_type(distance_km, "distance_km")
        _check_string_type(terrain, "terrain")

        distance = _to_positive(distance_km, "distance_km")
        if terrain not in TERRAINS:
            raise ValueError(f"unknown terrain: {terrain}")
        if terrain == GROUND:
            raise DuckCannotWaddle(
                "duck cannot waddle: the ground is not water"
            )
        return distance
