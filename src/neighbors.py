from dataclasses import replace
from itertools import chain, combinations, product
from random import Random
from typing import Iterator

from .models import Placement, Position, Problem, State
from .validation import _positive_attempts, _require_valid, validate_state


# nentuin tempat di luar truk dengan jarak yg cukup
def outside_slots(problem: Problem) -> tuple[Position, ...]:
    spacing = 1 + max(
        (side for package in problem.packages for side in package.dimensions.as_tuple()),
        default=0,
    )
    return tuple(
        (problem.truck.dimensions.w + 1 + index * spacing, 0, 0)
        for index in range(len(problem.packages))
    )


# create empty state (ga ada paket di dalam truk)
def create_empty_state(problem: Problem) -> State:
    return State({
        package.id: Placement(position)
        for package, position in zip(problem.packages, outside_slots(problem))
    })


# buat state baru dengan posisi 1 paket diubah, orientasi tetap
def move_package(state: State, package_id: str, position: Position) -> State:
    placements = dict(state.placements)
    placements[package_id] = replace(placements[package_id], position=position)
    return State(placements)


# buat state baru dengan posisi 2 paket ditukar, orientasi masing-masing tetap
def swap_packages(state: State, first_id: str, second_id: str) -> State:
    placements = dict(state.placements)
    first, second = placements[first_id], placements[second_id]
    placements[first_id] = replace(first, position=second.position)
    placements[second_id] = replace(second, position=first.position)
    return State(placements)


# buat state baru dengan 1 paket dirotasi 90derajat terhadap sumbu yg dipilih
def rotate_package(state: State, package_id: str, axis: str) -> State:
    if axis not in ("x", "y", "z"):
        raise ValueError("Sumbu rotasi harus x, y, atau z.")
    first, second = [name for name in ("x", "y", "z") if name != axis]
    mapping = {axis: axis, first: second, second: first}
    placement = state.placements[package_id]
    orientation = tuple(mapping[name] for name in placement.orientation)
    placements = dict(state.placements)
    placements[package_id] = replace(placement, orientation=orientation)
    return State(placements)


# buat neighbor valid satu per satu pakai move, rotate, dan swap
def iter_neighbors(problem: Problem, state: State) -> Iterator[State]:
    _require_valid(problem, state)
    w, l, h = problem.truck.dimensions.as_tuple()
    slots = outside_slots(problem)
    for package in problem.packages:
        positions = chain(product(range(w), range(l), range(h)), slots)
        for position in positions:
            if position != state.placements[package.id].position:
                candidate = move_package(state, package.id, position)
                if not validate_state(problem, candidate):
                    yield candidate
        for axis in ("x", "y", "z"):
            candidate = rotate_package(state, package.id, axis)
            if not validate_state(problem, candidate):
                yield candidate
    for first, second in combinations(problem.packages, 2):
        candidate = swap_packages(state, first.id, second.id)
        if not validate_state(problem, candidate):
            yield candidate


# return 1 neighbor valid secara acak. return None kalo batas percobaan habis
def sample_neighbor(
    problem: Problem, state: State, rng: Random, max_attempts: int = 100,
) -> State | None:
    _positive_attempts(max_attempts)
    _require_valid(problem, state)
    if not problem.packages:
        return None
    w, l, h = problem.truck.dimensions.as_tuple()
    volume = w * l * h
    slots = outside_slots(problem)
    moves = ("move", "rotate", "swap") if len(problem.packages) > 1 else ("move", "rotate")
    for _ in range(max_attempts):
        package = rng.choice(problem.packages)
        operation = rng.choice(moves)
        if operation == "move":
            index = rng.randrange(volume + len(slots))
            position = slots[index - volume] if index >= volume else (
                index // (l * h), (index // h) % l, index % h,
            )
            candidate = move_package(state, package.id, position)
        elif operation == "rotate":
            candidate = rotate_package(state, package.id, rng.choice(("x", "y", "z")))
        else:
            first, second = rng.sample(problem.packages, 2)
            candidate = swap_packages(state, first.id, second.id)
        if candidate != state and not validate_state(problem, candidate):
            return candidate
    return None