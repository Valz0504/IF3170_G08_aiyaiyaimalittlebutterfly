import argparse
from inspect import signature
from pathlib import Path
from random import Random

from .algorithms import ALGORITHMS
from .experiments import load_problem, load_state, save_result, save_state
from .models import Problem, State
from .problem import OBJECTIVES, generate_initial_state, loaded_weight, score, set_objective
from .validation import is_inside


def _print_summary(problem: Problem, state: State) -> None:
    loaded = sum(
        is_inside(problem, package, state.placements[package.id])
        for package in problem.packages
    )
    print("State valid.")
    print(f"Paket di dalam: {loaded}; di luar: {len(problem.packages) - loaded}")
    print(f"Berat: {loaded_weight(problem, state)} / {problem.truck.max_capacity}")
    print(f"Score: {score(problem, state)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fondasi persoalan Mejiro Express.")
    commands = parser.add_subparsers(dest="command", required=True)
    initial = commands.add_parser("init", help="Buat initial state acak yang valid.")
    initial.add_argument("input", help="Path dataset JSON.")
    initial.add_argument("--seed", type=int, default=11)
    initial.add_argument("--objective", choices=OBJECTIVES, default="default",
                         help="Fungsi objective: default (total value) atau bonus (multi-faktor logistik).")
    initial.add_argument("--output", help="Simpan snapshot ke file JSON baru.")
    validate = commands.add_parser("validate", help="Periksa snapshot state tersimpan.")
    validate.add_argument("state", help="Path snapshot JSON hasil init.")
    validate.add_argument("--objective", choices=OBJECTIVES, default="default",
                          help="Fungsi objective awal sebelum deteksi otomatis snapshot.")
    visualize = commands.add_parser("visualize", help="Tampilkan atau simpan visualisasi state.")
    visualize.add_argument("state", help="Path snapshot JSON hasil init atau state akhir.")
    visualize.add_argument("--objective", choices=OBJECTIVES, default="default",
                           help="Fungsi objective awal sebelum deteksi otomatis snapshot.")
    visualize.add_argument("--output", help="Simpan gambar, misalnya output/scratch/initial.png.")
    visualize.add_argument("--title", default="State paket")
    visualize.add_argument("--show", action="store_true", help="Buka jendela gambar meskipun memakai --output.")
    run = commands.add_parser("run", help="Jalankan satu algoritma dan simpan hasil.")
    run.add_argument("input", help="Path dataset JSON.")
    run.add_argument("--algorithm", choices=ALGORITHMS, required=True,
                     help="hc = Steepest Ascent; varian lain: hc_sideways, hc_random_restart, hc_stochastic; sa; ga.")
    run.add_argument("--objective", choices=OBJECTIVES, default="default",
                     help="Fungsi objective: default (total value) atau bonus (multi-faktor logistik).")
    run.add_argument("--seed", type=int, default=11)
    run.add_argument("--output", required=True, help="Direktori hasil baru, tidak boleh sudah ada.")
    run.add_argument("--plots", action="store_true", help="Sertakan gambar state dan history; membutuhkan Matplotlib.")
    run.add_argument("--max-iterations", type=int, default=argparse.SUPPRESS,
                     help="HC/SA: batas iterasi; Random Restart berlaku per percobaan. Default Stochastic/SA: 1000; HC lain: tanpa batas iterasi.")
    run.add_argument("--max-sideways-moves", type=int, default=argparse.SUPPRESS,
                     help="HC Sideways: batas sideways berturut-turut (default 100); 0 menonaktifkan sideways.")
    run.add_argument("--max-restarts", type=int, default=argparse.SUPPRESS,
                     help="HC Random Restart: batas restart setelah percobaan awal (default 10); 0 berarti hanya percobaan awal.")
    run.add_argument("--initial-temperature", type=float, default=argparse.SUPPRESS, help="SA: suhu awal.")
    run.add_argument("--cooling-rate", type=float, default=argparse.SUPPRESS, help="SA: faktor penurunan suhu.")
    run.add_argument("--min-temperature", type=float, default=argparse.SUPPRESS, help="SA: batas suhu minimum.")
    run.add_argument("--population-size", type=int, default=argparse.SUPPRESS, help="GA: jumlah individu.")
    run.add_argument("--generations", type=int, default=argparse.SUPPRESS, help="GA: jumlah generasi.")
    args = parser.parse_args()

    try:
        set_objective(args.objective)
        if args.command == "init":
            problem = load_problem(args.input)
            state = generate_initial_state(problem, Random(args.seed))
            if args.output:
                save_state(args.output, problem, state, seed=args.seed)
            _print_summary(problem, state)
            if args.output:
                print(f"Snapshot disimpan: {args.output}")
        elif args.command == "validate":
            problem, state = load_state(args.state)
            _print_summary(problem, state)
        elif args.command == "run":
            solve = ALGORITHMS[args.algorithm]
            parameters = {key: value for key, value in vars(args).items() if key in (
                "max_iterations", "initial_temperature", "cooling_rate",
                "min_temperature", "population_size", "generations",
                "max_sideways_moves", "max_restarts", "objective",
            )}
            try:
                signature(solve).bind(None, seed=args.seed, **parameters)
            except TypeError as error:
                parser.error(f"Parameter tidak sesuai untuk {args.algorithm}: {error}")
            for name in ("max_iterations", "population_size", "generations"):
                if name in parameters and parameters[name] <= 0:
                    parser.error(f"{name} harus lebih besar dari 0.")
            for name in ("max_sideways_moves", "max_restarts"):
                if name in parameters and parameters[name] < 0:
                    parser.error(f"{name} harus berupa integer nonnegatif.")
            for name in ("initial_temperature", "min_temperature"):
                if name in parameters and not 0 < parameters[name] < float("inf"):
                    parser.error(f"{name} harus positif dan berhingga.")
            if "cooling_rate" in parameters and not 0 < parameters["cooling_rate"] < 1:
                parser.error("cooling_rate harus berada di antara 0 dan 1.")
            if args.algorithm == "sa" and parameters.get("min_temperature", 0.001) >= parameters.get("initial_temperature", 100.0):
                parser.error("min_temperature harus lebih kecil dari initial_temperature.")
            if Path(args.output).exists():
                parser.error("Direktori output sudah ada. Pilih direktori baru.")
            if args.plots:
                try:
                    import matplotlib
                except ModuleNotFoundError:
                    parser.error("Instal Matplotlib terlebih dahulu: python -m pip install -r requirements.txt")
            problem = load_problem(args.input)
            result = solve(problem, seed=args.seed, **parameters)
            save_result(args.output, problem, result, plots=args.plots)
            _print_summary(problem, result.final_state)
            print(f"Iterasi: {result.iterations}; durasi: {result.duration_seconds:.3f} s")
            print(f"Berhenti: {result.stop_reason}")
            if result.algorithm == "hc_random_restart":
                print(f"Restart: {result.metrics['restarts']}")
                print(f"Iterasi per percobaan (awal, lalu restart): {result.metrics['iterations_per_restart']}")
            elif result.algorithm == "hc_sideways":
                print(f"Total sideways move: {result.metrics['sideways_moves']}")
            print(f"Hasil disimpan: {args.output}")
        else:
            problem, state = load_state(args.state)
            try:
                import matplotlib
            except ModuleNotFoundError:
                parser.error("Instal Matplotlib terlebih dahulu: python -m pip install -r requirements.txt")
            show = args.show or not args.output
            if not show:
                matplotlib.use("Agg")
            from matplotlib import pyplot as plt
            from .visualization import plot_state, save_figure

            figure = plot_state(problem, state, title=args.title)
            try:
                if args.output:
                    save_figure(figure, args.output)
                    print(f"Gambar disimpan: {args.output}")
                if show:
                    plt.show()
            finally:
                plt.close(figure)
    except FileExistsError:
        parser.error("File output sudah ada. Pilih path baru agar hasil lama tetap tersimpan.")
    except (ValueError, OSError, NotImplementedError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
