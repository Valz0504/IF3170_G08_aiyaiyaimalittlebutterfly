from itertools import count
from math import exp, isfinite
from random import Random
from time import perf_counter

from ..models import Problem, SearchResult, State
from ..neighbors import iter_neighbors, sample_neighbor
from ..problem import generate_initial_state, score


def _validate_parameters(
    problem: Problem,
    seed: int,
    max_iterations: int,
    initial_temperature: int | float,
    cooling_rate: int | float,
    min_temperature: int | float,
) -> None:
    if not isinstance(problem, Problem):
        raise ValueError("problem harus berupa Problem.")
    if type(seed) is not int:
        raise ValueError("seed harus berupa integer.")
    if type(max_iterations) is not int or max_iterations <= 0:
        raise ValueError("max_iterations harus berupa bilangan bulat positif.")
    for name, value in (
        ("initial_temperature", initial_temperature),
        ("min_temperature", min_temperature),
    ):
        if type(value) not in (int, float) or not isfinite(value) or value <= 0:
            raise ValueError(f"{name} harus berupa angka positif berhingga.")
    if type(cooling_rate) not in (int, float) or not isfinite(cooling_rate) or not 0 < cooling_rate < 1:
        raise ValueError("cooling_rate harus berada di antara 0 dan 1.")
    if min_temperature >= initial_temperature:
        raise ValueError("min_temperature harus lebih kecil dari initial_temperature.")


def _is_stuck(problem: Problem, state: State, current_score: int | float) -> bool:
    return not any(
        score(problem, neighbor) > current_score
        for neighbor in iter_neighbors(problem, state)
    )


def solve(
    problem: Problem, *, seed: int = 11, max_iterations: int = 1000,
    initial_temperature: float = 100.0, cooling_rate: float = 0.95,
    min_temperature: float = 0.001,
) -> SearchResult:
    _validate_parameters(
        problem, seed, max_iterations,
        initial_temperature, cooling_rate, min_temperature,
    )
    initial_temp = float(initial_temperature)
    cooling = float(cooling_rate)
    min_temp = float(min_temperature)

    initial_state = generate_initial_state(problem, Random(seed))
    rng = Random(seed + 1)

    start_time = perf_counter()

    current = initial_state
    current_score = score(problem, current)
    best_state = current
    best_score = current_score

    history: list[dict] = [{
        "iteration": 0,
        "score": current_score,
        "best_score": best_score,
        "temperature": initial_temp,
        "delta": None,
        "log_acceptance_ratio": None,
        "acceptance_probability": None,
        "accepted": None,
    }]

    stuck_cache: dict[tuple, bool] = {}
    was_stuck = False
    stuck_episodes = 0
    stuck_iterations = 0
    iterations = 0
    stop_reason = "min_temperature"

    def schedule(t: int) -> float:
        nonlocal stop_reason
        if t > max_iterations:
            stop_reason = "max_iterations"
            return 0.0
        temperature = initial_temp * (cooling ** (t - 1))
        if temperature < min_temp:
            stop_reason = "min_temperature"
            return 0.0
        return temperature

    for t in count(1):
        T = schedule(t)
        if T == 0:
            break

        iterations = t
        next_state = sample_neighbor(problem, current, rng)

        if next_state is None:
            delta_e = None
            log_acceptance_ratio = None
            acceptance_probability = None
            accepted = None
        else:
            next_score = score(problem, next_state)
            delta_e = next_score - current_score
            log_acceptance_ratio = delta_e / T

            if delta_e > 0:
                current = next_state
                current_score = next_score
                acceptance_probability = 1.0
                accepted = True
            else:
                acceptance_probability = exp(log_acceptance_ratio)
                if rng.random() < acceptance_probability:
                    current = next_state
                    current_score = next_score
                    accepted = True
                else:
                    accepted = False

            if current_score > best_score:
                best_state = current
                best_score = current_score

        state_key = tuple(sorted(current.placements.items()))
        is_stuck = stuck_cache.get(state_key)
        if is_stuck is None:
            is_stuck = _is_stuck(problem, current, current_score)
            stuck_cache[state_key] = is_stuck
        if is_stuck:
            stuck_iterations += 1
            if not was_stuck:
                stuck_episodes += 1
        was_stuck = is_stuck

        history.append({
            "iteration": t,
            "score": current_score,
            "best_score": best_score,
            "temperature": T,
            "delta": delta_e,
            "log_acceptance_ratio": log_acceptance_ratio,
            "acceptance_probability": acceptance_probability,
            "accepted": accepted,
        })

    duration_seconds = perf_counter() - start_time

    return SearchResult(
        algorithm="sa",
        initial_state=initial_state,
        final_state=current,
        final_score=current_score,
        iterations=iterations,
        duration_seconds=duration_seconds,
        seed=seed,
        stop_reason=stop_reason,
        parameters={
            "seed": seed,
            "max_iterations": max_iterations,
            "initial_temperature": initial_temp,
            "cooling_rate": cooling,
            "min_temperature": min_temp,
        },
        history=history,
        metrics={
            "stuck_episodes": stuck_episodes,
            "stuck_iterations": stuck_iterations,
            "best_score": best_score,
        },
        best_state=best_state,
    )
