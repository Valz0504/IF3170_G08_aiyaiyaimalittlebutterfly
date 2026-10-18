from random import Random
from time import perf_counter

from ..models import Placement, Problem, SearchResult, State
from ..neighbors import outside_slots, sample_neighbor
from ..problem import generate_initial_state, score
from ..validation import is_inside, validate_state

MUTATION_PROBABILITY = 0.05

# pilih parent pake roullete wheel, peluang sebanding dengan fitness
def random_selection(population: list[State], fitness: list[int | float], rng: Random) -> State:
    largest = max(fitness)
    if largest == 0:
        return rng.choice(population)
    return rng.choices(population, weights=[value / largest for value in fitness], k=1)[0]


# fix child yang ngelanggar constraint setelah hasil crossover
def repair(problem: Problem, child: State) -> State:
    if not validate_state(problem, child):
        return child
    # Mulai dari slot luar unik; coba placement warisan dari bawah ke atas.
    state = State({
        package.id: Placement(position, child.placements[package.id].orientation)
        for package, position in zip(problem.packages, outside_slots(problem))
    })
    for package in sorted(problem.packages, key=lambda item: child.placements[item.id].position[2]):
        placement = child.placements[package.id]
        if is_inside(problem, package, placement):
            placements = dict(state.placements)
            placements[package.id] = placement
            candidate = State(placements)
            if not validate_state(problem, candidate):
                state = candidate
    return state


# crossover 1 titik pada urutan paket
def reproduce(problem: Problem, first: State, second: State, rng: Random) -> State:
    if len(problem.packages) < 2:
        return State(first.placements)
    cut = rng.randrange(1, len(problem.packages))
    child = State({
        package.id: (first if index < cut else second).placements[package.id]
        for index, package in enumerate(problem.packages)
    })
    return repair(problem, child)


# ngambil neighbor valid 
def mutate(problem: Problem, child: State, rng: Random) -> State:
    candidate = sample_neighbor(problem, child, rng)
    return child if candidate is None else candidate


def solve(
    problem: Problem, *, seed: int = 11, population_size: int = 20,
    generations: int = 100,
) -> SearchResult:
    if type(seed) is not int:
        raise ValueError("Seed harus berupa integer.")
    for name, value in (("population_size", population_size), ("generations", generations)):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} harus berupa integer positif.")

    initial_rng = Random(seed)
    population = [generate_initial_state(problem, initial_rng) for _ in range(population_size)]
    initial_population = list(population)
    rng = Random(seed + 1)
    started = perf_counter()
    fitness = [score(problem, individual) for individual in population]
    initial_state = population[max(range(population_size), key=fitness.__getitem__)]
    history = [{"iteration": 0, "max_score": max(fitness), "mean_score": sum(fitness) / population_size}]

    for generation in range(1, generations + 1):
        new_population = []
        for _ in range(population_size):
            first = random_selection(population, fitness, rng)
            second = random_selection(population, fitness, rng)
            child = reproduce(problem, first, second, rng)
            if rng.random() < MUTATION_PROBABILITY:
                child = mutate(problem, child, rng)
            new_population.append(child)
        population = new_population
        fitness = [score(problem, individual) for individual in population]
        history.append({
            "iteration": generation,
            "max_score": max(fitness),
            "mean_score": sum(fitness) / population_size,
        })

    final_state = population[max(range(population_size), key=fitness.__getitem__)]
    return SearchResult(
        algorithm="ga", initial_state=initial_state, final_state=final_state,
        final_score=max(fitness), iterations=generations,
        duration_seconds=perf_counter() - started, seed=seed,
        stop_reason="generation_limit",
        parameters={
            "population_size": population_size, "generations": generations,
            "mutation_probability": MUTATION_PROBABILITY,
            "selection": "roulette_wheel", "crossover": "one_point", "elitism": False,
        },
        history=history, initial_population=initial_population,
        final_population=list(population),
    )