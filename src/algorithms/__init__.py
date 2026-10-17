from .genetic_algorithm import solve as genetic_algorithm
from .hill_climbing import solve as hill_climbing
from .simulated_annealing import solve as simulated_annealing


ALGORITHMS = {
    "hc": hill_climbing,
    "sa": simulated_annealing,
    "ga": genetic_algorithm,
}