from random import Random
from time import perf_counter

from ..models import Problem, SearchResult
from ..problem import generate_initial_state, score
from .hill_climbing_steepest_ascent import _best_neighbor, _nonnegative_limit, _validate_parameters


def solve(
    problem: Problem, *, seed: int = 11, max_iterations: int | None = None,
    max_restarts: int = 10,
) -> SearchResult:
    """Random Restart HC sesuai PPT IF3170 halaman 28, dengan batas restart.

    max_restarts tidak menghitung percobaan awal; max_iterations berlaku per
    percobaan. History memakai nomor pemeriksaan global, dan kolom restart
    menunjukkan percobaannya (0 = awal). Final state adalah terbaik lintas
    percobaan. Hentikan lebih awal jika jumlah value seluruh paket tercapai;
    bound ini cukup untuk membuktikan optimum, tetapi tidak selalu dapat dicapai.
    """
    _validate_parameters(seed, max_iterations)
    _nonnegative_limit(max_restarts, "max_restarts")
    initial_rng = Random(seed)
    initial_state = generate_initial_state(problem, initial_rng)
    rng = Random(seed + 1)

    started = perf_counter()
    initialization_seconds = 0.0
    current = best_state = initial_state
    current_score = best_score = score(problem, current)
    upper_bound = sum(package.value for package in problem.packages)
    history = [{
        "iteration": 0, "score": current_score, "best_score": best_score,
        "restart": 0, "restart_iteration": 0,
    }]
    runs = []
    iterations = 0
    stop_reason = "max_restarts"

    for restart in range(max_restarts + 1):
        if restart:
            before_initialization = perf_counter()
            current = generate_initial_state(problem, initial_rng)
            initialization_seconds += perf_counter() - before_initialization
            current_score = score(problem, current)
            if current_score > best_score:
                best_state, best_score = current, current_score
        run_initial_score = current_score
        run_iterations = 0
        run_stop_reason = "max_iterations"

        while max_iterations is None or run_iterations < max_iterations:
            neighbor, neighbor_score = _best_neighbor(problem, current, current_score, rng)
            run_iterations += 1
            iterations += 1
            if neighbor is not None:
                current, current_score = neighbor, neighbor_score
                if current_score > best_score:
                    best_state, best_score = current, current_score
            history.append({
                "iteration": iterations, "score": current_score, "best_score": best_score,
                "restart": restart, "restart_iteration": run_iterations,
            })
            if best_score >= upper_bound:
                run_stop_reason = "objective_upper_bound"
                break
            if neighbor is None:
                run_stop_reason = "local_optimum"
                break

        runs.append({
            "restart": restart, "iterations": run_iterations,
            "initial_score": run_initial_score, "final_score": current_score,
            "stop_reason": run_stop_reason,
        })
        if best_score >= upper_bound:
            stop_reason = "objective_upper_bound"
            break

    duration_seconds = perf_counter() - started - initialization_seconds
    return SearchResult(
        algorithm="hc_random_restart", initial_state=initial_state,
        final_state=best_state, final_score=best_score, best_state=best_state,
        iterations=iterations, duration_seconds=duration_seconds,
        seed=seed, stop_reason=stop_reason,
        parameters={"max_iterations": max_iterations, "max_restarts": max_restarts},
        history=history,
        metrics={
            "restarts": len(runs) - 1,
            "iterations_per_restart": [run["iterations"] for run in runs],
            "runs": runs,
        },
    )
