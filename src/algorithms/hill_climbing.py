from random import Random
from time import perf_counter

from ..models import Problem, SearchResult
from ..neighbors import iter_neighbors
from ..problem import generate_initial_state, score


def solve(
    problem: Problem, *, seed: int = 11, max_iterations: int | None = None,
) -> SearchResult:
    """Steepest Ascent: pilih neighbor terbaik, terima hanya perbaikan ketat.

    Acuan: IF3170 Beyond Classical Search, halaman 16 dan 22 (Steepest Ascent).
    Neighbor dienumerasi bertahap, tanpa menyimpan semuanya. Jika beberapa
    neighbor terbaik memiliki score sama, reservoir sampling memilih salah
    satunya dengan RNG pencarian yang terpisah dari RNG initial state.

    Satu iterasi adalah satu pemeriksaan seluruh neighbor, termasuk pemeriksaan
    terakhir tanpa perpindahan. History iterasi 0 menyimpan score initial state.
    """
    if type(seed) is not int:
        raise ValueError("Seed harus berupa integer.")
    if max_iterations is not None and (
        type(max_iterations) is not int or max_iterations <= 0
    ):
        raise ValueError("max_iterations harus berupa integer positif atau None.")

    initial_state = generate_initial_state(problem, Random(seed))
    rng = Random(seed + 1)

    started = perf_counter()
    current = initial_state
    current_score = score(problem, current)
    iterations = 0
    history = [{"iteration": 0, "score": current_score}]
    stop_reason = "max_iterations"

    while max_iterations is None or iterations < max_iterations:
        best_neighbor = None
        best_score = current_score
        tied_best = 0

        for neighbor in iter_neighbors(problem, current):
            neighbor_score = score(problem, neighbor)
            if neighbor_score > best_score:
                best_neighbor = neighbor
                best_score = neighbor_score
                tied_best = 1
            elif best_neighbor is not None and neighbor_score == best_score:
                tied_best += 1
                if rng.randrange(tied_best) == 0:
                    best_neighbor = neighbor

        iterations += 1
        if best_neighbor is not None:
            current = best_neighbor
            current_score = best_score
        history.append({"iteration": iterations, "score": current_score})

        if best_neighbor is None:
            stop_reason = "local_optimum"
            break

    duration_seconds = perf_counter() - started
    return SearchResult(
        algorithm="hc",
        initial_state=initial_state,
        final_state=current,
        final_score=current_score,
        iterations=iterations,
        duration_seconds=duration_seconds,
        seed=seed,
        stop_reason=stop_reason,
        parameters={"max_iterations": max_iterations},
        history=history,
    )
