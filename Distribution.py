import logging
from typing import Dict, List, NamedTuple, Iterable, Tuple
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import gzip

from src.time_func import time_func

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


class Panel(NamedTuple):
	# xs: Iterable[int]
	# ys: Iterable[int]
	title: str
	xlabel: str
	ylabel: str
	kwargs: dict


class HistogramVisualizer:
	MAX_PANEL = 224

	def __init__(self):
		self._panel = 221

	def get_next_panel_id(self) -> int:
		if self._panel > self.MAX_PANEL:
			raise RuntimeError("Cannot visualize more than 4 panels.")
		res = self._panel
		self._panel += 1
		return res

	def add_panel(self, panel: Panel):
		panel_id = self.get_next_panel_id()
		plt.subplot(panel_id)
		# plt.plot(panel.xs, panel.ys)
		plt.hist(**panel.kwargs)
		plt.xlabel = panel.xlabel
		plt.ylabel = panel.ylabel
		plt.title(panel.title)
		plt.legend()

	def show(self, panels: List[Panel]):
		if len(panels) > 4 or not panels:
			raise ValueError("Invalid argument")
		plt.figure()
		for panel in panels:
			self.add_panel(panel)
		plt.show()


class DistData:
	def __init__(self):
		self.avg_occurrences: List[float] = []
		self.avg_jumps: List[float] = []


AvgByEdge = Dict[int, DistData]


class JumpStats:
	def __init__(self):
		self.avg: List[float] = []
		self.total: List[float] = []


AvgJumps = Dict[int, JumpStats]


def read_distributions(data_path: Path) -> Tuple[Dict[str, AvgByEdge], AvgJumps]:
	avg_jumps = {}
	distribution = {}
	for data_f in data_path.glob("*.gz"):
		with gzip.open(str(data_f.absolute()), "r") as f:
			data = json.loads(f.read().decode())
		edge_len = data["expected_edge_len"]
		stats = data["island_stats"]
		average_jumps = round(data["avg_jumps"], 2)
		total_jumps = data["total_jumps"]
		jump_stats = avg_jumps.setdefault(edge_len, JumpStats())
		assert total_jumps != average_jumps
		jump_stats.avg.append(average_jumps)
		jump_stats.total.append(total_jumps)
		for k, v in stats.items():
			assert len(v) == 1
			dist_data = distribution.setdefault(k, {}).setdefault(edge_len, DistData())
			dist_data.avg_occurrences.append(round(v[0], 1))
			dist_data.avg_jumps.append(average_jumps)
	return distribution, avg_jumps

# # Make a separate list for each airline
# x1 = list(flights[flights['name'] == 'United Air Lines Inc.']['arr_delay'])
# x2 = list(flights[flights['name'] == 'JetBlue Airways']['arr_delay'])
# x3 = list(flights[flights['name'] == 'ExpressJet Airlines Inc.']['arr_delay'])
# x4 = list(flights[flights['name'] == 'Delta Air Lines Inc.']['arr_delay'])
# x5 = list(flights[flights['name'] == 'American Airlines Inc.']['arr_delay'])
#
# # Assign colors for each airline and the names
# colors = ['#E69F00', '#56B4E9', '#F0E442', '#009E73', '#D55E00']
# names = ['United Air Lines Inc.', 'JetBlue Airways', 'ExpressJet Airlines Inc.'',
# 													 'Delta Air Lines Inc.', 'American Airlines Inc.']

# Make the histogram using a list of lists
# Normalize the flights and assign colors and names


def make_occurrences_panel(distributions: Dict[str, AvgByEdge], island_size: int) -> Panel:
	island = sorted({k: v for k, v in distributions[str(island_size)].items()}.items())
	return Panel(
		title=f'Average occurrences of island of size {island_size} genes', xlabel="Average Occurrences", ylabel="Edge Length",
		kwargs={
			"x": [v.avg_occurrences for _, v in island], "bins": len(island), "label": [f"EdgeLen: {v}" for v, _ in island]}
	)


def make_jumps_panel(distributions: Dict[str, AvgByEdge], island_size: int) -> Panel:
	island = sorted({k: v for k, v in distributions[str(island_size)].items()}.items())
	return Panel(
		title=f'Average jumps for island size {island_size} genes', xlabel="Average Jumps", ylabel="Edge Length",
		kwargs={
			"x": [v for _, v in island], "bins": len(island), "label": [f"EdgeLen: {v}" for v, _ in island]}
	)


def make_total_jumps_panels(average_jumps: AvgJumps) -> List[Panel]:
	avg_jumps = sorted({k: v.avg for k, v in average_jumps.items()}.items())
	total_jumps = sorted({k: v.total for k, v in average_jumps.items()}.items())
	return [
		Panel(
			title=f'Average jumps by edge length', xlabel="Average Jumps", ylabel="Edge Length",
			kwargs={
				"x": [v for _, v in avg_jumps], "bins": len(avg_jumps), "label": [f"EdgeLen: {v}" for v, _ in avg_jumps]}
		),
		Panel(
			title=f'Total jumps by edge length', xlabel="Total Jumps", ylabel="Edge Length",
			kwargs={
				"x": [v for _, v in total_jumps], "bins": len(total_jumps), "label": [f"EdgeLen: {v}" for v, _ in total_jumps]}
		),
	]


def plot_jumps(average_jumps: AvgJumps):
	viz = HistogramVisualizer()
	panels = make_total_jumps_panels(average_jumps)
	viz.show(panels)


def plot_distribution(distributions: Dict[str, AvgByEdge], island_sizes: List[int]):
	viz = HistogramVisualizer()
	assert len(island_sizes) == 4
	panels = [make_occurrences_panel(distributions, island) for island in island_sizes]
	assert len(panels) == 4
	viz.show(panels)

	# plt.hist(
	# 	x=[v for _, v in island],
	# 	bins=len(island), label=[f"EdgeLen: {v}" for v, _ in island]
	# )
	#
	# # Plot formatting
	# plt.legend()
	# plt.xlabel('Occurrences')
	# plt.ylabel('Edge Length')
	# plt.title(f'Occurrences of size {island_size} islands')
	# plt.show()


if __name__ == '__main__':
	DATA_PATH = Path("~/university/jump_model_exp/4096_island_out/distributions").expanduser()
	assert DATA_PATH.exists() and DATA_PATH.is_dir()
	with time_func(f"Reading distributions from {DATA_PATH}"):
		dists, jumps = read_distributions(DATA_PATH)
	# with time_func("Plotting histogram"):
	# 	plot_distribution(dists, [2**5, 2**6, 2**7, 2**8])
	with time_func("Plotting jumps"):
		plot_jumps(jumps)


# viz = HistogramVisualizer()
# panel = Panel(range(10), range(0, 20, 2), "Ooga", "Booga")
# viz.show([panel])