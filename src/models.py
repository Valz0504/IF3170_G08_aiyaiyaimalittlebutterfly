from dataclasses import dataclass, field
from itertools import permutations
from math import isfinite
from types import MappingProxyType
from typing import Mapping

Position = tuple[int, int, int]
Orientation = tuple[str, str, str]
ORIENTATIONS: tuple[Orientation, ...] = tuple(permutations(("x", "y", "z")))

def _nonnegative_number(value: int | float, name: str) -> None:
    if type(value) not in (int, float) or value < 0:
        raise ValueError(f"{name} harus berupa angka nonnegatif.")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError(f"{name} harus berupa angka berhingga.")

@dataclass(frozen=True)
class Dimensions:
    w: int
    l: int
    h: int

    def __post_init__(self) -> None:
        if any(type(side) is not int or side <= 0 for side in self.as_tuple()):
            raise ValueError("Dimensi harus berupa bilangan bulat positif.")

    def as_tuple(self) -> tuple[int, int, int]:
        return self.w, self.l, self.h

@dataclass(frozen=True)
class Package:
    id: str
    dimensions: Dimensions
    value: int | float
    weight: int | float
    is_fragile: bool
    eta: int

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("ID paket harus berupa string yang tidak kosong.")
        if not isinstance(self.dimensions, Dimensions):
            raise ValueError("Dimensi paket harus berupa Dimensions.")
        _nonnegative_number(self.value, "Value")
        _nonnegative_number(self.weight, "Weight")
        if type(self.is_fragile) is not bool:
            raise ValueError("is_fragile harus berupa boolean.")
        if type(self.eta) is not int or self.eta < 0:
            raise ValueError("ETA harus berupa bilangan bulat nonnegatif.")


@dataclass(frozen=True)
class Truck:
    dimensions: Dimensions
    max_capacity: int | float

    def __post_init__(self) -> None:
        if not isinstance(self.dimensions, Dimensions):
            raise ValueError("Dimensi truk harus berupa Dimensions.")
        _nonnegative_number(self.max_capacity, "MaxCapacity")

@dataclass(frozen=True)
class Problem:
    truck: Truck
    packages: tuple[Package, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.truck, Truck):
            raise ValueError("truck harus berupa Truck.")
        object.__setattr__(self, "packages", tuple(self.packages))
        if any(not isinstance(package, Package) for package in self.packages):
            raise ValueError("packages harus berisi Package.")
        ids = [package.id for package in self.packages]
        if len(ids) != len(set(ids)):
            raise ValueError("ID paket harus unik.")

@dataclass(frozen=True)
class Placement:
    position: Position
    orientation: Orientation = ("x", "y", "z")

    def __post_init__(self) -> None:
        if not isinstance(self.position, (tuple, list)) or len(self.position) != 3:
            raise ValueError("Posisi harus berisi tiga koordinat integer.")
        if any(type(coordinate) is not int for coordinate in self.position):
            raise ValueError("Koordinat harus berupa bilangan bulat.")
        if not isinstance(self.orientation, (tuple, list)):
            raise ValueError("Orientasi harus berupa pemetaan sumbu untuk w, l, h.")
        object.__setattr__(self, "position", tuple(self.position))
        object.__setattr__(self, "orientation", tuple(self.orientation))
        if self.orientation not in ORIENTATIONS:
            raise ValueError("Orientasi harus berupa permutasi x, y, z.")

@dataclass(frozen=True)
class State:
    placements: Mapping[str, Placement]

    def __post_init__(self) -> None:
        if not isinstance(self.placements, Mapping):
            raise ValueError("State harus memetakan ID paket ke Placement.")
        placements = dict(self.placements)
        if any(
            not isinstance(key, str) or not isinstance(value, Placement)
            for key, value in placements.items()
        ):
            raise ValueError("State harus memetakan ID paket ke Placement.")
        object.__setattr__(self, "placements", MappingProxyType(placements))

@dataclass
class SearchResult:
    algorithm: str
    initial_state: State
    final_state: State
    final_score: int | float
    iterations: int
    duration_seconds: float
    seed: int
    stop_reason: str
    parameters: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    best_state: State | None = None
    initial_population: list[State] | None = None
    final_population: list[State] | None = None