from .genetic_algorithm import solve as genetic_algorithm
from .hill_climbing_steepest_ascent import solve as hill_climbing
from .hill_climbing_random_restart import solve as hill_climbing_random_restart
from .hill_climbing_sideways import solve as hill_climbing_sideways
from .hill_climbing_stochastic import solve as hill_climbing_stochastic
from .simulated_annealing import solve as simulated_annealing


ALGORITHMS = {
    "hc": hill_climbing,
    "hc_sideways": hill_climbing_sideways,
    "hc_random_restart": hill_climbing_random_restart,
    "hc_stochastic": hill_climbing_stochastic,
    "sa": simulated_annealing,
    "ga": genetic_algorithm,
}
