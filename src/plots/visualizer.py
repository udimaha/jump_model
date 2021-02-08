from typing import NamedTuple, List, Dict

import seaborn as sns
from matplotlib import pyplot as plt

from src.plots.distribution import AvgByEdge, AvgJumps


class Panel(NamedTuple):
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
		sns.displot(**panel.kwargs)

	def show(self, panels: List[Panel]):
		if len(panels) > 4 or not panels:
			raise ValueError("Invalid argument")
		plt.figure()
		for panel in panels:
			self.add_panel(panel)
		plt.show()


def make_occurrences_panel(distributions: Dict[str, AvgByEdge], island_size: int) -> Panel:
	island = sorted({k: v for k, v in distributions[str(island_size)].items()}.items())
	data = [
		{"edge_length": k, "occurrences": x}
		for k, v in island for x in v.avg_occurrences
	]
	return Panel(
		title=f'Average occurrences of island of size {island_size} genes', xlabel="Average Occurrences", ylabel="Edge Length",
		kwargs={
			"data": data, "x": "occurrences", "label": [f"EdgeLen: {v}" for v, _ in island], "hue": "edge_length"}
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
	avg_jumps = sorted({k: v.avg for k, v in average_jumps.items()}.items())
	for e, jumps_ in avg_jumps:
		for j in jumps_:
			plt.hist((e, j), cumulative=True)
	plt.show()
