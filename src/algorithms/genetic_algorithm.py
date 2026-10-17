from ..models import Problem, SearchResult


def solve(
    problem: Problem, *, seed: int = 11, population_size: int = 20,
    generations: int = 100,
) -> SearchResult:
    raise NotImplementedError("Genetic Algorithm belum diimplementasikan.")