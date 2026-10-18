from random import Random
from time import perf_counter

from ..models import Problem, SearchResult
from ..problem import generate_initial_state, score
from .hill_climbing_steepest_ascent import _best_neighbor, _nonnegative_limit, _validate_parameters


def solve(
    problem: Problem, *, seed: int = 11, max_iterations: int | None = None,
    max_sideways_moves: int = 100,
) -> SearchResult:
    """HC Sideways: PPT IF3170 Beyond Classical Search, halaman 26–27.

    Score boleh tetap, tetapi tidak turun. Batas sideways dihitung berturut-turut
    dan direset setelah perbaikan. Nilai 0 menonaktifkan sideways. Satu iterasi
    adalah satu pemeriksaan neighborhood, termasuk pemeriksaan tanpa perpindahan.
    """
    _validate_parameters(seed, max_iterations)
    _nonnegative_limit(max_sideways_moves, "max_sideways_moves")
    initial_state = generate_initial_state(problem, Random(seed))
    rng = Random(seed + 1)

    started = perf_counter()
    current = initial_state
    current_score = score(problem, current)
    iterations = sideways_moves = consecutive_sideways = 0
    history = [{"iteration": 0, "score": current_score, "consecutive_sideways": 0}]
    stop_reason = "max_iterations"

    while max_iterations is None or iterations < max_iterations:
        neighbor, neighbor_score = _best_neighbor(
            problem, current, current_score, rng,
            allow_sideways=max_sideways_moves > 0,
        )
        iterations += 1
        if neighbor is not None:
            if neighbor_score == current_score:
                consecutive_sideways += 1
                sideways_moves += 1
            else:
                consecutive_sideways = 0
            current, current_score = neighbor, neighbor_score
        history.append({
            "iteration": iterations, "score": current_score,
            "consecutive_sideways": consecutive_sideways,
        })
        if neighbor is None:
            stop_reason = "local_optimum"
            break
        if max_sideways_moves > 0 and consecutive_sideways >= max_sideways_moves:
            stop_reason = "max_sideways_moves"
            break

    duration_seconds = perf_counter() - started
    return SearchResult(
        algorithm="hc_sideways", initial_state=initial_state, final_state=current,
        final_score=current_score, iterations=iterations,
        duration_seconds=duration_seconds, seed=seed, stop_reason=stop_reason,
        parameters={"max_iterations": max_iterations, "max_sideways_moves": max_sideways_moves},
        history=history,
        metrics={"sideways_moves": sideways_moves, "consecutive_sideways": consecutive_sideways},
    )
