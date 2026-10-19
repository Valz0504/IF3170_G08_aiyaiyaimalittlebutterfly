import csv
import json
from dataclasses import asdict, fields
from math import isfinite
from pathlib import Path
from shutil import rmtree

from .models import Dimensions, Package, Placement, Problem, SearchResult, State, Truck
from .problem import OBJECTIVES, get_objective, score, set_objective


def _object(data: object, keys: set[str], label: str) -> dict:
    if not isinstance(data, dict):
        raise ValueError(f"{label} harus berupa object JSON.")
    if set(data) != keys:
        raise ValueError(f"Field {label} harus tepat: {', '.join(sorted(keys))}.")
    return data


def _dimensions(data: object) -> Dimensions:
    return Dimensions(**_object(data, {"w", "l", "h"}, "dimensions"))


def _truck_from_dict(raw: object) -> tuple[Truck, int]:
    if not isinstance(raw, dict):
        raise ValueError("truck harus berupa object JSON.")
    allowed = {"dimensions", "max_capacity"}
    count = 1
    if "count" in raw:
        allowed = {"dimensions", "max_capacity", "count"}
        count = raw["count"]
        if type(count) is not int or count <= 0:
            raise ValueError("count truk harus berupa bilangan bulat positif.")
    item = _object(raw, allowed, "truck")
    return Truck(_dimensions(item["dimensions"]), item["max_capacity"]), count


def problem_from_dict(data: dict) -> Problem:
    if not isinstance(data, dict):
        raise ValueError("input harus berupa object JSON.")
    keys = set(data)
    if not keys <= {"truck", "trucks", "packages"} or "packages" not in keys or not (keys & {"truck", "trucks"}):
        raise ValueError("Field input harus memuat packages serta truck atau trucks.")
    trucks: list[Truck] = []
    if "trucks" in data:
        if not isinstance(data["trucks"], list) or not data["trucks"]:
            raise ValueError("trucks harus berupa array JSON yang tidak kosong.")
        for raw_truck in data["trucks"]:
            truck_obj, count = _truck_from_dict(raw_truck)
            trucks.extend([truck_obj] * count)
    elif "truck" in data:
        truck_obj, count = _truck_from_dict(data["truck"])
        trucks.extend([truck_obj] * count)

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
        truck=trucks[0],
        packages=tuple(packages),
        trucks=tuple(trucks),
    )


def problem_to_dict(problem: Problem) -> dict:
    result = {
        "truck": asdict(problem.truck),
        "packages": [asdict(package) for package in problem.packages],
    }
    if len(problem.trucks) > 1:
        result["trucks"] = [asdict(truck) for truck in problem.trucks]
    return result


def state_from_dict(data: dict) -> State:
    data = _object(data, {"placements"}, "state")
    if not isinstance(data["placements"], dict):
        raise ValueError("placements harus berupa object JSON.")
    placements = {}
    for key, raw in data["placements"].items():
        if not isinstance(raw, dict):
            raise ValueError("placement harus berupa object JSON.")
        expected = {"position", "orientation", "truck"} if "truck" in raw else {"position", "orientation"}
        item = _object(raw, expected, "placement")
        position = _object(item["position"], {"x", "y", "z"}, "position")
        orientation = _object(item["orientation"], {"w", "l", "h"}, "orientation")
        truck_idx = item.get("truck", 0)
        placements[key] = Placement(
            position=tuple(position[axis] for axis in ("x", "y", "z")),
            orientation=tuple(orientation[side] for side in ("w", "l", "h")),
            truck=truck_idx,
        )
    return State(placements)


def state_to_dict(state: State) -> dict:
    has_multi_truck = any(placement.truck != 0 for placement in state.placements.values())
    placements = {}
    for key, placement in state.placements.items():
        entry = {
            "position": dict(zip(("x", "y", "z"), placement.position)),
            "orientation": dict(zip(("w", "l", "h"), placement.orientation)),
        }
        if has_multi_truck:
            entry["truck"] = placement.truck
        placements[key] = entry
    return {"placements": placements}


def with_trucks(problem: Problem, num_trucks: int | None) -> Problem:
    if num_trucks is None:
        return problem
    if type(num_trucks) is not int or num_trucks <= 0:
        raise ValueError("Jumlah truk harus berupa bilangan bulat positif.")
    if num_trucks == len(problem.trucks):
        return problem
    if len(problem.trucks) == 1:
        trucks = (problem.truck,) * num_trucks
    else:
        trucks = tuple(problem.trucks[i % len(problem.trucks)] for i in range(num_trucks))
    return Problem(truck=trucks[0], packages=problem.packages, trucks=trucks)


def load_problem(path: str | Path, *, trucks: int | None = None) -> Problem:
    with Path(path).open(encoding="utf-8") as handle:
        problem = problem_from_dict(json.load(handle))
    return with_trucks(problem, trucks)


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
        for name in OBJECTIVES:
            if snapshot["score"] == score(problem, state, objective=name):
                set_objective(name)
                break
        else:
            raise ValueError("Score snapshot tidak sesuai dengan state.")
    return problem, state


def _validate_result(problem: Problem, result: SearchResult) -> None:
    if not isinstance(result, SearchResult):
        raise ValueError("Algoritma harus mengembalikan SearchResult.")
    for name in ("algorithm", "stop_reason"):
        if not isinstance(getattr(result, name), str) or not getattr(result, name).strip():
            raise ValueError(f"{name} harus berupa string yang tidak kosong.")
    if type(result.seed) is not int:
        raise ValueError("Seed hasil harus berupa integer.")
    if type(result.iterations) is not int or result.iterations < 0:
        raise ValueError("Jumlah iterasi harus berupa integer nonnegatif.")
    if type(result.duration_seconds) not in (int, float) or not isfinite(result.duration_seconds) or result.duration_seconds < 0:
        raise ValueError("Durasi harus berupa angka berhingga nonnegatif.")
    if not isinstance(result.parameters, dict) or not isinstance(result.metrics, dict):
        raise ValueError("parameters dan metrics harus berupa dictionary.")
    objective = result.parameters.get("objective", get_objective())
    states = [result.initial_state, result.final_state]
    if result.best_state is not None:
        states.append(result.best_state)
    for population in (result.initial_population, result.final_population):
        if population is not None:
            if not isinstance(population, list) or not population:
                raise ValueError("Populasi hasil harus berupa list state yang tidak kosong.")
            states.extend(population)
    for state in states:
        if not isinstance(state, State):
            raise ValueError("State hasil harus berupa State.")
        score(problem, state, objective=objective)
    if type(result.final_score) not in (int, float) or result.final_score != score(problem, result.final_state, objective=objective):
        raise ValueError("final_score tidak sesuai dengan final_state.")
    if not isinstance(result.history, list) or not result.history:
        raise ValueError("History harus berisi data sejak iterasi 0.")
    previous = -1
    for row in result.history:
        if not isinstance(row, dict) or any(not isinstance(key, str) for key in row):
            raise ValueError("Baris history harus berupa dictionary dengan key string.")
        iteration = row.get("iteration")
        if type(iteration) is not int or iteration <= previous:
            raise ValueError("Nomor iterasi history harus integer nonnegatif dan meningkat.")
        if any(value is not None and type(value) not in (str, int, float, bool) for value in row.values()):
            raise ValueError("Nilai kolom history harus berupa angka, boolean, string, atau None.")
        previous = iteration
    if result.history[0]["iteration"] != 0 or previous != result.iterations:
        raise ValueError("History harus dimulai dari 0 dan berakhir pada result.iterations.")


def result_to_dict(problem: Problem, result: SearchResult) -> dict:
    _validate_result(problem, result)
    data = {field.name: getattr(result, field.name) for field in fields(SearchResult)}
    for name in ("initial_state", "final_state", "best_state"):
        data[name] = state_to_dict(data[name]) if data[name] is not None else None
    for name in ("initial_population", "final_population"):
        data[name] = [state_to_dict(state) for state in data[name]] if data[name] is not None else None
    return data


def load_result(path: str | Path) -> tuple[Problem, SearchResult]:
    with Path(path).open(encoding="utf-8") as handle:
        snapshot = _object(json.load(handle), {"problem", "result"}, "run")
    problem = problem_from_dict(snapshot["problem"])
    data = dict(_object(snapshot["result"], {field.name for field in fields(SearchResult)}, "result"))
    for name in ("initial_state", "final_state", "best_state"):
        data[name] = state_from_dict(data[name]) if data[name] is not None else None
    for name in ("initial_population", "final_population"):
        if data[name] is not None:
            if not isinstance(data[name], list):
                raise ValueError(f"{name} harus berupa array atau null.")
            data[name] = [state_from_dict(state) for state in data[name]]
    result = SearchResult(**data)
    if isinstance(result.parameters, dict) and result.parameters.get("objective") in OBJECTIVES:
        set_objective(result.parameters["objective"])
    _validate_result(problem, result)
    json.dumps(snapshot, allow_nan=False)
    return problem, result


def save_result(
    directory: str | Path, problem: Problem, result: SearchResult, *, plots: bool = False,
) -> None:
    snapshot = {"problem": problem_to_dict(problem), "result": result_to_dict(problem, result)}
    content = json.dumps(snapshot, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        (destination / "run.json").write_text(content, encoding="utf-8")
        columns = list(dict.fromkeys(key for row in result.history for key in row))
        with (destination / "history.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(result.history)
        for name, state in (("initial", result.initial_state), ("final", result.final_state), ("best", result.best_state)):
            if state is not None:
                save_state(destination / f"{name}.json", problem, state, seed=result.seed)
        if plots:
            import matplotlib
            matplotlib.use("Agg")
            from matplotlib import pyplot as plt
            from .visualization import plot_history, plot_state, save_figure

            for name, state in (("initial", result.initial_state), ("final", result.final_state), ("best", result.best_state)):
                if state is not None:
                    figure = plot_state(problem, state, title=f"{result.algorithm} — {name} state")
                    try:
                        save_figure(figure, destination / f"{name}.png")
                    finally:
                        plt.close(figure)
            figure = plot_history(result)
            try:
                save_figure(figure, destination / "history.png")
            finally:
                plt.close(figure)
    except Exception:
        rmtree(destination)
        raise