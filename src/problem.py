from decimal import Decimal
from itertools import product
from random import Random

from .models import ORIENTATIONS, Placement, Position, Problem, State
from .neighbors import outside_slots
from .validation import (
    _bounds, _positive_attempts, _require_valid, _weight_sum,
    is_inside, oriented_dimensions, validate_state,
)


_ACTIVE_OBJECTIVE = "default"


# objective wajib: ngitung total value paket di dalam truk
def score_default(problem: Problem, state: State) -> int | float:
    _require_valid(problem, state)
    return sum(
        package.value for package in problem.packages
        if is_inside(problem, package, state.placements[package.id])
    )


# objective bonus:
# 1. value paket di dalam truk
# 2. prioritas bongkar-muat sepanjang y
# 3. stabilitas titik berat terhadap ketinggian z
# 4. rasio luas alas paket yang tertopang
def score_bonus(problem: Problem, state: State) -> int | float:
    _require_valid(problem, state)
    packages = {package.id: package for package in problem.packages}
    _, l_truck, h_truck = problem.truck.dimensions.as_tuple()
    capacity = problem.truck.max_capacity
    boxes = {
        package.id: _bounds(package, state.placements[package.id])
        for package in problem.packages
        if is_inside(problem, package, state.placements[package.id])
    }
    if not boxes:
        return 0

    total = 0.0
    for key, box in boxes.items():
        package = packages[key]
        x1, y1, z1, x2, y2, _ = box
        base_area = (x2 - x1) * (y2 - y1)

        urgency = 1.0 / (1.0 + package.eta)
        access = y2 / l_truck
        eta_component = urgency * (1.0 + access)

        weight_ratio = (package.weight / capacity) if capacity > 0 else 0.0
        height_factor = 1.0 - (z1 / h_truck)
        cog_component = weight_ratio * height_factor

        if z1 == 0:
            support_ratio = 1.0
        else:
            supported_area = sum(
                max(0, min(x2, boxes[other][3]) - max(x1, boxes[other][0]))
                * max(0, min(y2, boxes[other][4]) - max(y1, boxes[other][1]))
                for other in boxes
                if other != key and boxes[other][5] == z1
            )
            support_ratio = supported_area / base_area

        total += (
            package.value
            + 2.0 * eta_component
            + 2.0 * cog_component
            + 1.0 * support_ratio
        )
    return round(total, 6)


OBJECTIVES = {
    "default": score_default,
    "bonus": score_bonus,
}


def set_objective(objective: str) -> str:
    global _ACTIVE_OBJECTIVE
    if objective not in OBJECTIVES:
        raise ValueError(f"Objective harus salah satu dari: {', '.join(OBJECTIVES)}.")
    _ACTIVE_OBJECTIVE = objective
    return _ACTIVE_OBJECTIVE


def get_objective() -> str:
    return _ACTIVE_OBJECTIVE


def score(
    problem: Problem, state: State, *, objective: str | None = None,
) -> int | float:
    chosen = _ACTIVE_OBJECTIVE if objective is None else objective
    if chosen not in OBJECTIVES:
        raise ValueError(f"Objective harus salah satu dari: {', '.join(OBJECTIVES)}.")
    return OBJECTIVES[chosen](problem, state)


def objective_upper_bound(
    problem: Problem, *, objective: str | None = None,
) -> int | float:
    chosen = _ACTIVE_OBJECTIVE if objective is None else objective
    if chosen not in OBJECTIVES:
        raise ValueError(f"Objective harus salah satu dari: {', '.join(OBJECTIVES)}.")
    if chosen == "default":
        return sum(package.value for package in problem.packages)
    capacity = problem.truck.max_capacity
    total = sum(
        package.value
        + 2.0 * (2.0 / (1.0 + package.eta))
        + 2.0 * ((package.weight / capacity) if capacity > 0 else 0.0)
        + 1.0
        for package in problem.packages
    )
    return round(total, 6)



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