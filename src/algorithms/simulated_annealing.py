from ..models import Problem, SearchResult


def solve(
    problem: Problem, *, seed: int = 11, max_iterations: int = 1000,
    initial_temperature: float = 100.0, cooling_rate: float = 0.95,
    min_temperature: float = 0.001,
) -> SearchResult:
    raise NotImplementedError("Simulated Annealing belum diimplementasikan.")