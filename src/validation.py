from decimal import Decimal
from itertools import combinations
from typing import Iterable

from .models import ORIENTATIONS, Orientation, Package, Placement, Problem, State


def oriented_dimensions(package: Package, orientation: Orientation) -> tuple[int, int, int]:
    if orientation not in ORIENTATIONS:
        raise ValueError("Orientasi harus berupa permutasi x, y, z.")
    sides = dict(zip(orientation, package.dimensions.as_tuple()))
    return sides["x"], sides["y"], sides["z"]


# ngitung batas paket
def _bounds(package: Package, placement: Placement) -> tuple[int, ...]:
    x, y, z = placement.position
    w, l, h = oriented_dimensions(package, placement.orientation)
    return x, y, z, x + w, y + l, z + h


# cek apakah seluruh batas paket di dalam dimensi truk
def _inside(bounds: tuple[int, ...], dimensions: tuple[int, int, int]) -> bool:
    return all(0 <= bounds[axis] and bounds[axis + 3] <= dimensions[axis] for axis in range(3))


# cek overlap pada sumbu tertentu
def _overlap(a: tuple[int, ...], b: tuple[int, ...], axes: tuple[int, ...]) -> bool:
    return all(a[axis] < b[axis + 3] and b[axis] < a[axis + 3] for axis in axes)


# cek apakah suatu paket seluruhnya ada di dalam truk sesuai indeks truk pada placement
def is_inside(problem: Problem, package: Package, placement: Placement) -> bool:
    if not 0 <= placement.truck < len(problem.trucks):
        return False
    dimensions = problem.trucks[placement.truck].dimensions.as_tuple()
    return _inside(_bounds(package, placement), dimensions)


# ngitung seluruh berat paket
def _weight_sum(packages: Iterable[Package]) -> Decimal:
    return sum((Decimal(str(package.weight)) for package in packages), Decimal(0))


# cek ID, indeks truk, dinding, overlap, capacity, paket yg melayang, fragile. Return [] kalo valid
def validate_state(problem: Problem, state: State) -> list[str]:
    errors = []
    packages = {package.id: package for package in problem.packages}
    missing = packages.keys() - state.placements.keys()
    extra = state.placements.keys() - packages.keys()
    if missing:
        errors.append(f"Paket tanpa placement: {', '.join(sorted(missing))}.")
    if extra:
        errors.append(f"ID paket tidak dikenal: {', '.join(sorted(extra))}.")
    if errors:
        return errors

    num_trucks = len(problem.trucks)
    for key, placement in state.placements.items():
        if not 0 <= placement.truck < num_trucks:
            errors.append(f"Indeks truk untuk paket {key} tidak valid: {placement.truck}.")
    if errors:
        return errors

    boxes = {key: _bounds(package, state.placements[key]) for key, package in packages.items()}
    loaded_by_truck: list[list[str]] = [[] for _ in range(num_trucks)]
    outside: list[str] = []

    for key, box in boxes.items():
        truck_idx = state.placements[key].truck
        dimensions = problem.trucks[truck_idx].dimensions.as_tuple()
        if _inside(box, dimensions):
            loaded_by_truck[truck_idx].append(key)
        elif not any(box[axis + 3] <= 0 or box[axis] >= dimensions[axis] for axis in range(3)):
            errors.append(f"Paket {key} menembus dinding truk.")
        else:
            outside.append(key)

    for truck_loaded in loaded_by_truck:
        for first, second in combinations(truck_loaded, 2):
            if _overlap(boxes[first], boxes[second], (0, 1, 2)):
                errors.append(f"Paket {first} dan {second} overlap.")

    for first, second in combinations(outside, 2):
        if _overlap(boxes[first], boxes[second], (0, 1, 2)):
            errors.append(f"Paket {first} dan {second} overlap.")

    for truck_idx, truck_loaded in enumerate(loaded_by_truck):
        for first in truck_loaded:
            for second in outside:
                if state.placements[second].truck == truck_idx and _overlap(boxes[first], boxes[second], (0, 1, 2)):
                    errors.append(f"Paket {first} dan {second} overlap.")

    for truck_idx, (truck, truck_loaded) in enumerate(zip(problem.trucks, loaded_by_truck)):
        total_weight = _weight_sum(packages[key] for key in truck_loaded)
        if total_weight > Decimal(str(truck.max_capacity)):
            if num_trucks == 1:
                errors.append("Total berat melebihi kapasitas truk.")
            else:
                errors.append(f"Total berat pada truk {truck_idx + 1} melebihi kapasitas truk.")

        for key in truck_loaded:
            box = boxes[key]
            if box[2] == 0:
                continue
            supports = [
                other for other in truck_loaded
                if other != key and boxes[other][5] == box[2]
                and _overlap(box, boxes[other], (0, 1))
            ]
            if not supports:
                errors.append(f"Paket {key} melayang.")
            for other in supports:
                if packages[other].is_fragile:
                    errors.append(f"Paket fragile {other} menjadi support untuk {key}.")
    return errors


# manggil validate_state, kalo ga valid lempar ValueError
def _require_valid(problem: Problem, state: State) -> None:
    errors = validate_state(problem, state)
    if errors:
        raise ValueError("State tidak valid: " + " ".join(errors))


def _positive_attempts(attempts: int) -> None:
    if type(attempts) is not int or attempts <= 0:
        raise ValueError("Batas percobaan harus berupa bilangan bulat positif.")