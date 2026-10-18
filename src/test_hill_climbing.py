import unittest
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.algorithms.hill_climbing import solve
from src.experiments import load_problem, load_result, save_result
from src.models import Dimensions, Package, Placement, Problem, State, Truck
from src.neighbors import create_empty_state, iter_neighbors, move_package
from src.problem import build_occupancy, generate_initial_state, score
from src.validation import validate_state


class HillClimbingTests(unittest.TestCase):
    def setUp(self):
        # Dua paket bersaing untuk satu sel: optimum dapat dibuktikan manual.
        self.problem = Problem(
            Truck(Dimensions(1, 1, 1), 1),
            (
                Package("low", Dimensions(1, 1, 1), 2, 1, False, 1),
                Package("high", Dimensions(1, 1, 1), 9, 1, False, 1),
            ),
        )
        self.empty = create_empty_state(self.problem)

    def solve_from(self, state, **parameters):
        with patch(
            "src.algorithms.hill_climbing.generate_initial_state",
            return_value=state,
        ):
            return solve(self.problem, **parameters)

    def test_selects_best_neighbor_instead_of_first_improvement(self):
        result = self.solve_from(self.empty)
        self.assertEqual(result.final_score, 9)
        self.assertEqual(result.final_state.placements["high"].position, (0, 0, 0))
        self.assertEqual(result.history, [
            {"iteration": 0, "score": 0},
            {"iteration": 1, "score": 9},
            {"iteration": 2, "score": 9},
        ])
        self.assertEqual(result.iterations, 2)
        self.assertEqual(result.stop_reason, "local_optimum")
        self.assertEqual(validate_state(self.problem, result.final_state), [])
        self.assertTrue(all(
            score(self.problem, neighbor) <= result.final_score
            for neighbor in iter_neighbors(self.problem, result.final_state)
        ))
        self.assertEqual(result.initial_state, self.empty)
        self.assertEqual(score(self.problem, self.empty), 0)

    def test_swap_can_improve_full_truck(self):
        initial = move_package(self.empty, "low", (0, 0, 0))
        result = self.solve_from(initial)
        self.assertEqual(result.final_score, 9)
        self.assertEqual(score(self.problem, initial), 2)

    def test_plateau_is_not_accepted(self):
        problem = Problem(
            Truck(Dimensions(2, 1, 1), 1),
            (Package("zero", Dimensions(1, 1, 1), 0, 1, False, 0),),
        )
        initial = State({"zero": Placement((0, 0, 0))})
        with patch(
            "src.algorithms.hill_climbing.generate_initial_state", return_value=initial,
        ):
            result = solve(problem)
        self.assertEqual(result.final_state, initial)
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.stop_reason, "local_optimum")

    def test_iteration_limit_does_not_claim_local_optimum(self):
        problem = Problem(
            Truck(Dimensions(2, 1, 1), 2), self.problem.packages,
        )
        with patch(
            "src.algorithms.hill_climbing.generate_initial_state",
            return_value=create_empty_state(problem),
        ):
            result = solve(problem, max_iterations=1)
        self.assertEqual(result.final_score, 9)
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.stop_reason, "max_iterations")
        self.assertEqual(result.parameters, {"max_iterations": 1})
        self.assertTrue(any(
            score(problem, neighbor) > result.final_score
            for neighbor in iter_neighbors(problem, result.final_state)
        ))

    def test_optimum_detected_on_last_allowed_iteration(self):
        result = self.solve_from(self.empty, max_iterations=2)
        self.assertEqual(result.stop_reason, "local_optimum")
        self.assertEqual(result.iterations, 2)

    def test_empty_problem_has_no_neighbors(self):
        problem = Problem(self.problem.truck, ())
        result = solve(problem)
        self.assertEqual(result.final_score, 0)
        self.assertEqual(result.final_state, State({}))
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.stop_reason, "local_optimum")

    def test_oversized_package_stays_outside(self):
        problem = Problem(
            self.problem.truck,
            (Package("big", Dimensions(2, 2, 2), 100, 1, False, 0),),
        )
        result = solve(problem)
        self.assertEqual(result.final_score, 0)
        self.assertEqual(result.final_state, result.initial_state)
        self.assertEqual(validate_state(problem, result.final_state), [])

    def test_tied_best_neighbors_are_reproducible(self):
        problem = Problem(
            Truck(Dimensions(3, 1, 1), 1), (self.problem.packages[0],),
        )
        with patch(
            "src.algorithms.hill_climbing.generate_initial_state",
            return_value=create_empty_state(problem),
        ):
            first = solve(problem, seed=22)
            second = solve(problem, seed=22)
        self.assertEqual(first.final_score, 2)
        self.assertEqual(first.final_state, second.final_state)
        self.assertEqual(first.history, second.history)

    def test_invalid_parameters_are_rejected(self):
        for seed in (True, 1.5, "11", None):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                solve(self.problem, seed=seed)
        for limit in (True, False, 0, -1, 1.5, "2"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                solve(self.problem, max_iterations=limit)

    def test_example_reproducibility_and_result_round_trip(self):
        root = Path(__file__).resolve().parents[1]
        problem = load_problem(root / "data" / "example.json")
        first = solve(problem, seed=11)
        second = solve(problem, seed=11)
        self.assertEqual(first.initial_state, generate_initial_state(problem, Random(11)))
        self.assertEqual(first.final_state, second.final_state)
        self.assertEqual(first.history, second.history)
        self.assertEqual(first.algorithm, "hc")
        self.assertEqual(first.parameters, {"max_iterations": None})
        self.assertGreaterEqual(first.duration_seconds, 0)
        scores = [row["score"] for row in first.history]
        self.assertTrue(all(a < b for a, b in zip(scores[:-2], scores[1:-1])))
        self.assertEqual(scores[-1], scores[-2])
        self.assertEqual(len(first.history), first.iterations + 1)
        self.assertEqual(validate_state(problem, first.final_state), [])
        self.assertEqual(set(first.final_state.placements), {p.id for p in problem.packages})
        self.assertEqual(len(build_occupancy(problem, first.final_state)), 4 * 6 * 3)
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "hc"
            save_result(destination, problem, first)
            loaded_problem, loaded_result = load_result(destination / "run.json")
            self.assertEqual(loaded_problem, problem)
            self.assertEqual(loaded_result, first)
            self.assertTrue((destination / "history.csv").is_file())


if __name__ == "__main__":
    unittest.main()
