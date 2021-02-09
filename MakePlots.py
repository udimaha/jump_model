import logging
from pathlib import Path
import seaborn as sns
import fire

from src.plots.distribution import read_distributions
from src.plots.plot import PlotData, plot_distribution
from src.time_func import time_func

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


def main(data_path: str, output_path: str, edge_lengths: int):
	data_path = Path(data_path).expanduser()
	output_path = Path(output_path).expanduser()
	sns.set()
	assert data_path.exists() and data_path.is_dir()
	output_path.mkdir(exist_ok=True)
	with time_func(f"Reading distributions from {data_path}"):
		dists, jumps = read_distributions(data_path)
	data = PlotData(
		distributions=dists,
		out_dir=output_path,
		lambdas=edge_lengths
	)
	with time_func("Plotting histogram"):
		plot_distribution(data, [size for size in range(1, 1024)])


if __name__ == '__main__':
	fire.Fire(main)
