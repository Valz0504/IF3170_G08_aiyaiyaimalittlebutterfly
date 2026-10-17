import argparse
from random import Random

from .experiments import load_problem, load_state, save_state
from .models import Problem, State
from .problem import generate_initial_state, loaded_weight, score
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
    initial.add_argument("--output", help="Simpan snapshot ke file JSON baru.")
    validate = commands.add_parser("validate", help="Periksa snapshot state tersimpan.")
    validate.add_argument("state", help="Path snapshot JSON hasil init.")
    visualize = commands.add_parser("visualize", help="Tampilkan atau simpan visualisasi state.")
    visualize.add_argument("state", help="Path snapshot JSON hasil init atau state akhir.")
    visualize.add_argument("--output", help="Simpan gambar, misalnya output/scratch/initial.png.")
    visualize.add_argument("--title", default="State paket")
    visualize.add_argument("--show", action="store_true", help="Buka jendela gambar meskipun memakai --output.")
    args = parser.parse_args()

    try:
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
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
