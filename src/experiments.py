import json
from dataclasses import asdict
from pathlib import Path

from .models import Dimensions, Package, Placement, Problem, State, Truck
from .problem import score


def _object(data: object, keys: set[str], label: str) -> dict:
    if not isinstance(data, dict):
        raise ValueError(f"{label} harus berupa object JSON.")
    if set(data) != keys:
        raise ValueError(f"Field {label} harus tepat: {', '.join(sorted(keys))}.")
    return data


def _dimensions(data: object) -> Dimensions:
    return Dimensions(**_object(data, {"w", "l", "h"}, "dimensions"))


def problem_from_dict(data: dict) -> Problem:
    data = _object(data, {"truck", "packages"}, "input")
    truck = _object(data["truck"], {"dimensions", "max_capacity"}, "truck")
    if not isinstance(data["packages"], list):
        raise ValueError("packages harus berupa array JSON.")
    packages = []
    for raw in data["packages"]:
        item = _object(raw, {"id", "dimensions", "value", "weight", "is_fragile", "eta"}, "package")
        packages.append(Package(
            id=item["id"],
            dimensions=_dimensions(item["dimensions"]),
            value=item["value"],
            weight=item["weight"],
            is_fragile=item["is_fragile"],
            eta=item["eta"],
        ))
    return Problem(
        truck=Truck(_dimensions(truck["dimensions"]), truck["max_capacity"]),
        packages=tuple(packages),
    )


def problem_to_dict(problem: Problem) -> dict:
    return {
        "truck": asdict(problem.truck),
        "packages": [asdict(package) for package in problem.packages],
    }


def state_from_dict(data: dict) -> State:
    data = _object(data, {"placements"}, "state")
    if not isinstance(data["placements"], dict):
        raise ValueError("placements harus berupa object JSON.")
    placements = {}
    for key, raw in data["placements"].items():
        item = _object(raw, {"position", "orientation"}, "placement")
        position = _object(item["position"], {"x", "y", "z"}, "position")
        orientation = _object(item["orientation"], {"w", "l", "h"}, "orientation")
        placements[key] = Placement(
            position=tuple(position[axis] for axis in ("x", "y", "z")),
            orientation=tuple(orientation[side] for side in ("w", "l", "h")),
        )
    return State(placements)


def state_to_dict(state: State) -> dict:
    return {"placements": {
        key: {
            "position": dict(zip(("x", "y", "z"), placement.position)),
            "orientation": dict(zip(("w", "l", "h"), placement.orientation)),
        }
        for key, placement in state.placements.items()
    }}


def load_problem(path: str | Path) -> Problem:
    with Path(path).open(encoding="utf-8") as handle:
        return problem_from_dict(json.load(handle))


def save_state(
    path: str | Path, problem: Problem, state: State, *, seed: int | None = None,
) -> None:
    if seed is not None and type(seed) is not int:
        raise ValueError("Seed harus berupa integer atau None.")
    snapshot = {
        "problem": problem_to_dict(problem),
        "state": state_to_dict(state),
        "score": score(problem, state),
        "seed": seed,
    }
    content = json.dumps(snapshot, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        handle.write(content)


def load_state(path: str | Path) -> tuple[Problem, State]:
    with Path(path).open(encoding="utf-8") as handle:
        snapshot = _object(json.load(handle), {"problem", "state", "score", "seed"}, "snapshot")
    problem = problem_from_dict(snapshot["problem"])
    state = state_from_dict(snapshot["state"])
    if snapshot["score"] != score(problem, state):
        raise ValueError("Score snapshot tidak sesuai dengan state.")
    return problem, state