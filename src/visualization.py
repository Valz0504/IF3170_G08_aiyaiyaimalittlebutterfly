from itertools import combinations, product
from math import isfinite, log
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from .models import Problem, SearchResult, State
from .problem import loaded_weight, score
from .validation import is_inside, oriented_dimensions


def _configure_axes(ax, lower, upper) -> None:
    spans = [max(end - start, 1) for start, end in zip(lower, upper)]
    ax.set_xlim(lower[0], upper[0])
    ax.set_ylim(lower[1], upper[1])
    ax.set_zlim(lower[2], upper[2])
    ax.set_box_aspect(spans)
    ax.set_xlabel("x / lebar", labelpad=10, fontsize=9)
    ax.set_ylabel("y / panjang", labelpad=10, fontsize=9)
    ax.set_zlabel("z / tinggi", labelpad=10, fontsize=9)
    ax.tick_params(labelsize=8, pad=2)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    ax.view_init(elev=23, azim=-55)


def _draw_truck(ax, dimensions) -> None:
    vertices = list(product(*[(0, size) for size in dimensions]))
    for first, second in combinations(vertices, 2):
        if sum(a != b for a, b in zip(first, second)) == 1:
            ax.plot(*zip(first, second), color="#333333", linewidth=1.2)


def _draw_package(ax, package, placement, color) -> None:
    x, y, z = placement.position
    w, l, h = oriented_dimensions(package, placement.orientation)
    ax.bar3d(
        x, y, z, w, l, h, color=color, alpha=0.7, shade=True,
        edgecolor="#b42318" if package.is_fragile else "#333333",
        linewidth=1.8 if package.is_fragile else 0.6,
    )
    ax.text(
        x + w / 2, y + l / 2, z + h,
        package.id + (" *" if package.is_fragile else ""),
        ha="center", va="bottom", fontsize=9, zorder=10000,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 1},
    )


def plot_state(problem: Problem, state: State, title: str = "State paket") -> Figure:
    value = score(problem, state)
    weight = loaded_weight(problem, state)
    packages = problem.packages
    colors = {package.id: plt.get_cmap("tab20")(index % 20) for index, package in enumerate(packages)}
    inside = [package for package in packages if is_inside(problem, package, state.placements[package.id])]
    outside = [package for package in packages if package not in inside]

    table_height = max(1.3, 0.3 * (len(packages) + 1))
    figure = plt.figure(figsize=(15, 6 + table_height), layout="constrained")
    grid = figure.add_gridspec(2, 2, height_ratios=(5, table_height))
    truck_ax = figure.add_subplot(grid[0, 0], projection="3d")
    outside_ax = figure.add_subplot(grid[0, 1], projection="3d")
    table_ax = figure.add_subplot(grid[1, :])
    figure.suptitle(
        f"{title}\nScore: {value:g} | Berat: {weight:g} / {problem.truck.max_capacity:g}"
        f" | Dalam: {len(inside)} | Luar: {len(outside)}",
        fontsize=14,
    )

    dimensions = problem.truck.dimensions.as_tuple()
    _configure_axes(truck_ax, (0, 0, 0), dimensions)
    _draw_truck(truck_ax, dimensions)
    truck_ax.set_title(f"Dalam truk — ukuran {dimensions}")
    for package in inside:
        _draw_package(truck_ax, package, state.placements[package.id], colors[package.id])

    outside_ax.set_title("Paket di luar — koordinat asli")
    if outside:
        positions = [state.placements[package.id].position for package in outside]
        ends = [
            tuple(start + size for start, size in zip(
                state.placements[package.id].position,
                oriented_dimensions(package, state.placements[package.id].orientation),
            ))
            for package in outside
        ]
        lower = tuple(min(position[axis] for position in positions) for axis in range(3))
        upper = tuple(max(end[axis] for end in ends) for axis in range(3))
        _configure_axes(outside_ax, lower, upper)
        for package in outside:
            _draw_package(outside_ax, package, state.placements[package.id], colors[package.id])
    else:
        outside_ax.set_axis_off()
        outside_ax.text2D(0.5, 0.5, "Semua paket berada di dalam truk.",
                          transform=outside_ax.transAxes, ha="center")

    table_ax.set_axis_off()
    table_ax.set_title("* Fragile: tepi merah. Ukuran mengikuti orientasi; posisi adalah sudut kiri-bawah-belakang.", fontsize=10)
    if packages:
        rows = []
        for package in packages:
            placement = state.placements[package.id]
            rows.append([
                package.id, "Dalam" if package in inside else "Luar",
                str(placement.position), str(oriented_dimensions(package, placement.orientation)),
                ",".join(placement.orientation), "Ya" if package.is_fragile else "Tidak",
                f"{package.value:g}", f"{package.weight:g}", str(package.eta),
            ])
        table = table_ax.table(
            cellText=rows,
            colLabels=["ID", "Lokasi", "Posisi (x,y,z)", "Ukuran (x,y,z)", "Sumbu w,l,h", "Fragile", "Value", "Berat", "ETA"],
            colWidths=[0.10, 0.07, 0.18, 0.15, 0.13, 0.08, 0.07, 0.07, 0.05],
            cellLoc="center", bbox=[0, 0, 1, 0.95],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        for (row, column), cell in table.get_celld().items():
            cell.set_edgecolor("#dddddd")
            if row == 0:
                cell.set_facecolor("#edf2ed")
                cell.set_text_props(weight="bold")
            elif column == 0:
                cell.set_facecolor(colors[packages[row - 1].id])
    else:
        table_ax.text(0.5, 0.5, "Tidak ada paket pada input.", ha="center", va="center")
    return figure


def _column(history: list[dict], name: str, allow_missing: bool = False) -> list[float]:
    values = []
    for row in history:
        value = row.get(name)
        if value is None and allow_missing:
            values.append(float("nan"))
        elif type(value) not in (int, float) or not isfinite(value):
            raise ValueError(f"History harus memiliki kolom numerik berhingga '{name}'.")
        else:
            values.append(value)
    return values


def plot_history(result: SearchResult) -> Figure:
    if not result.history:
        raise ValueError("History kosong; jalankan algoritma terlebih dahulu.")
    algorithm = result.algorithm.lower().replace(" ", "_").replace("-", "_")
    if algorithm in ("hc", "hill_climbing", "steepest_ascent_hill_climbing"):
        kind = "hc"
    elif algorithm in ("sa", "simulated_annealing"):
        kind = "sa"
    elif algorithm in ("ga", "genetic_algorithm"):
        kind = "ga"
    else:
        raise ValueError("Nama algoritma harus hc/hill_climbing, sa/simulated_annealing, atau ga/genetic_algorithm.")
    iterations = _column(result.history, "iteration")
    if any(value < 0 or value != int(value) for value in iterations) or any(
        first >= second for first, second in zip(iterations, iterations[1:])
    ):
        raise ValueError("Nomor iterasi harus integer nonnegatif dan meningkat.")

    if kind == "ga":
        series = [("Maksimum populasi", _column(result.history, "max_score"), "#00BCD4", "-"),
                  ("Rata-rata populasi", _column(result.history, "mean_score"), "#3274a1", "--")]
    else:
        series = [("Score state", _column(result.history, "score"), "#00BCD4", "-")]
        if kind == "sa":
            series.append(("Best-so-far", _column(result.history, "best_score"), "#b56a00", "--"))
    log_ratios = _column(result.history, "log_acceptance_ratio", allow_missing=True) if kind == "sa" else []

    figure, axes = plt.subplots(2 if kind == "sa" else 1, 1, figsize=(10, 8 if kind == "sa" else 5),
                               squeeze=False, layout="constrained")
    objective_ax = axes[0, 0]
    for label, values, color, style in series:
        objective_ax.plot(iterations, values, label=label, color=color, linestyle=style, marker=".")
    objective_ax.set_ylabel("Objective / total value")
    objective_ax.legend()
    details = f"{result.algorithm} | Iterasi: {result.iterations} | Durasi: {result.duration_seconds:.3f} s | Seed: {result.seed}"
    if kind == "ga":
        population = len(result.final_population) if result.final_population is not None else result.parameters.get("population_size", "belum dicatat")
        details += f"\nPopulasi: {population}"
    elif kind == "sa":
        details += f"\nEpisode stuck: {result.metrics.get('stuck_episodes', 'belum dicatat')}"
        ratio_ax = axes[1, 0]
        ratio_ax.plot(iterations, [value / log(10) for value in log_ratios], color="#3274a1", marker=".")
        ratio_ax.axhline(0, color="#888888", linestyle=":", label="Rasio = 1")
        ratio_ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: rf"$10^{{{value:g}}}$"))
        ratio_ax.set_ylabel(r"$e^{\Delta E/T}$ (skala log)")
        ratio_ax.set_title("Rasio eksponensial; probabilitas penerimaan dibatasi maksimum 1")
        ratio_ax.legend()
    figure.suptitle(details, fontsize=12)
    for ax in axes.flat:
        ax.set_xlabel("Generasi" if kind == "ga" else "Iterasi")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(alpha=0.25)
    return figure


def save_figure(figure: Figure, path: str | Path) -> None:
    destination = Path(path)
    image_format = destination.suffix.lstrip(".").lower() or "png"
    if image_format not in figure.canvas.get_supported_filetypes():
        raise ValueError(f"Format gambar tidak didukung: {image_format}.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as handle:
        figure.savefig(handle, format=image_format, dpi=150, bbox_inches="tight")
