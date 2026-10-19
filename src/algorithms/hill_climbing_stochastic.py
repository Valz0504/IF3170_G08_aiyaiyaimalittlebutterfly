from random import Random
from time import perf_counter

from ..models import Problem, SearchResult
from ..neighbors import sample_neighbor
from ..problem import generate_initial_state, get_objective, score, set_objective
from .hill_climbing_steepest_ascent import _validate_parameters


def solve(
    problem: Problem, *, seed: int = 11, max_iterations: int = 1000,
    objective: str | None = None,
) -> SearchResult:
    """Stochastic HC sesuai PPT IF3170 halaman 29: satu kandidat acak per iterasi.

    Terima hanya score yang meningkat. Kandidat ditolak atau sampling gagal
    tetap dihitung satu iterasi; kegagalan sampling bukan bukti local optimum.
    """
    _validate_parameters(seed, max_iterations)
    if max_iterations is None:
        raise ValueError("max_iterations harus berupa integer positif.")
    active_objective = set_objective(objective) if objective is not None else get_objective()
    initial_state = generate_initial_state(problem, Random(seed))
    rng = Random(seed + 1)

    started = perf_counter()
    current = initial_state
    current_score = score(problem, current)
    accepted_moves = rejected_moves = sample_failures = 0
    history = [{"iteration": 0, "score": current_score, "candidate_score": None, "accepted": None}]

    for iteration in range(1, max_iterations + 1):
        neighbor = sample_neighbor(problem, current, rng)
        neighbor_score = None
        accepted = None
        if neighbor is None:
            sample_failures += 1
        else:
            neighbor_score = score(problem, neighbor)
            accepted = neighbor_score > current_score
            if accepted:
                current, current_score = neighbor, neighbor_score
                accepted_moves += 1
            else:
                rejected_moves += 1
        history.append({
            "iteration": iteration, "score": current_score,
            "candidate_score": neighbor_score, "accepted": accepted,
        })

    duration_seconds = perf_counter() - started
    return SearchResult(
        algorithm="hc_stochastic", initial_state=initial_state, final_state=current,
        final_score=current_score, iterations=max_iterations,
        duration_seconds=duration_seconds, seed=seed, stop_reason="max_iterations",
        parameters={"max_iterations": max_iterations, "objective": active_objective},
        history=history,
        metrics={
            "accepted_moves": accepted_moves, "rejected_moves": rejected_moves,
            "sample_failures": sample_failures,
        },
    )
