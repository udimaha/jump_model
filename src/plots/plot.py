import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import NamedTuple, Dict, List

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from src.plots.distribution import AvgByEdge
from src.time_func import time_func


class PlotData(NamedTuple):
	distributions: Dict[str, AvgByEdge]
	out_dir: Path
	lambdas: int


def plot_distribution(data: PlotData, island_sizes: List[int]):
	with TemporaryDirectory() as tmp_dir:
		for island_size_ in island_sizes:
			plot_island_distribution(data, island_size_, Path(tmp_dir))


def plot_island_distribution(data: PlotData, island_size_: int, tmp_dir: Path):
	csv_out = Path(tmp_dir, f"out_{island_size_}.csv")
	with time_func(f"Populating the CSV at {csv_out}"):
		populate_csv(csv_out, data.distributions, [island_size_])
	with time_func("Reading the CSV"):
		data_set = pd.read_csv(csv_out)
	for normalize in (True, False):
		xs = "avg_occurr" if not normalize else "ln_avg_occurr"
		with time_func("Displaying the dataset:"):
			sns.displot(
				data_set, x=xs, hue="edge_length", kind="kde",  # kde=True,
				palette=sns.color_palette("Paired", data.lambdas))
		title = f"island_size_{island_size_}"
		if normalize:
			title = "normalized_" + title
		out_fie = Path(data.out_dir, f"{title}.png")
		plt.title(title)
		plt.savefig(str(out_fie))


def populate_csv(csv_out: Path, distributions: Dict[str, AvgByEdge], island_sizes: List[int]):
	sample_id = 0
	fieldnames = ["island_size", "edge_length", "avg_occurr", "ln_avg_occurr"]
	with csv_out.open("w") as csv_f:
		writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
		writer.writeheader()
		for island_size in island_sizes:
			for edge_len, dist_data in distributions[str(island_size)].items():
				for occur in dist_data.avg_occurrences:
					writer.writerow(
						{"island_size": island_size, "edge_length": edge_len, "avg_occurr": occur, "ln_avg_occurr": np.log(occur)})
					sample_id += 1
