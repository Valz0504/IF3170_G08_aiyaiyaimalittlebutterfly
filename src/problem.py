from decimal import Decimal
from itertools import product
from random import Random

from .models import ORIENTATIONS, Placement, Position, Problem, State
from .neighbors import outside_slots
from .validation import (
    _bounds, _positive_attempts, _require_valid, _weight_sum,
    is_inside, oriented_dimensions, validate_state,
)


# ngitung total value paket di dalam truk
def score(problem: Problem, state: State) -> int | float:
    _require_valid(problem, state)
    return sum(
        package.value for package in problem.packages
        if is_inside(problem, package, state.placements[package.id])
    )


# ngitung total berat paket dalam truk setelah validasi _require_valid
def loaded_weight(problem: Problem, state: State) -> int | float:
    _require_valid(problem, state)
    total = _weight_sum(
        package for package in problem.packages
        if is_inside(problem, package, state.placements[package.id])
    )
    return int(total) if total == total.to_integral_value() else float(total)


# memetakan setiap sel truk ke ID paket yang menempatinya
def build_occupancy(problem: Problem, state: State) -> dict[Position, str | None]:
    _require_valid(problem, state)
    w, l, h = problem.truck.dimensions.as_tuple()
    occupancy = dict.fromkeys(product(range(w), range(l), range(h)))
    for package in problem.packages:
        placement = state.placements[package.id]
        if is_inside(problem, package, placement):
            x, y, z, end_x, end_y, end_z = _bounds(package, placement)
            for cell in product(range(x, end_x), range(y, end_y), range(z, end_z)):
                occupancy[cell] = package.id
    return occupancy


# buat initial state acak
def generate_initial_state(problem: Problem, rng: Random, max_attempts: int = 100) -> State:
    _positive_attempts(max_attempts)
    state = State({
        package.id: Placement(position, rng.choice(ORIENTATIONS))
        for package, position in zip(problem.packages, outside_slots(problem))
    })
    order = list(problem.packages)
    rng.shuffle(order)
    limits = problem.truck.dimensions.as_tuple()
    weight = Decimal(0)
    capacity = Decimal(str(problem.truck.max_capacity))
    for package in order:
        package_weight = Decimal(str(package.weight))
        if weight + package_weight > capacity:
            continue
        orientations = [
            orientation for orientation in ORIENTATIONS
            if all(size <= limit for size, limit in zip(oriented_dimensions(package, orientation), limits))
        ]
        if not orientations:
            continue
        for _ in range(max_attempts):
            orientation = rng.choice(orientations)
            dimensions = oriented_dimensions(package, orientation)
            position = tuple(rng.randrange(limit - size + 1) for size, limit in zip(dimensions, limits))
            placements = dict(state.placements)
            placements[package.id] = Placement(position, orientation)
            candidate = State(placements)
            if not validate_state(problem, candidate):
                state = candidate
                weight += package_weight
                break
    return state