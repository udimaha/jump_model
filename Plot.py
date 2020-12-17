import time
import json
import statistics
from pathlib import Path
import logging
import matplotlib.pyplot as plt
from typing import Iterable, NamedTuple, List


class SummaryStatistics:
	def __init__(self, v: List[int]):
		self._mean: float = statistics.mean(v)
		self._median: float = statistics.median(v)


class Panel(NamedTuple):
	xs: Iterable[int]
	ys: Iterable[int]
	xlabel: str
	ylabel: str


class Visualizer:
	MAX_PANEL = 224

	def __init__(self):
		self._panel = 221

	def get_next_panel_id(self) -> int:
		if self._panel == self.MAX_PANEL:
			raise RuntimeError("Cannot visualize more than 4 panels.")
		res = self._panel
		self._panel += 1
		return res

	def add_panel(self, panel: Panel):
		panel_id = self.get_next_panel_id()
		plt.subplot(panel_id)
		plt.plot(panel.xs, panel.ys)
		plt.xlabel = panel.xlabel
		plt.ylabel = panel.ylabel

	def show(self, panels: List[Panel]):
		if len(panels) > 4 or not panels:
			raise ValueError("Invalid argument")
		plt.figure()
		for panel in panels:
			self.add_panel(panel)
		plt.show()


def _process_file(to_process: Path):
	output = OUTPUT / to_process.name
	assert not output.exists()
	island_data = {}
	start = time.monotonic()
	with to_process.open("r") as f:
		data = json.load(f)
	data['occurrences'] = json.loads(data['occurrences'])
	leaves = data['leaves_count']
	genome_size = int(data['genome_size'])
	expected_edge = data['expected_edge_len']
	found_some = False
	for k in range(1, genome_size):
		key = str(k)
		if key not in data['occurrences']:
			island_data.setdefault(k, []).append(1)
		else:
			found_some = True
			# if int(k) > 10 or int(k) == 1:
			# 	continue
			v = list(data['occurrences'][key])
			max_unique = leaves * (genome_size - k + 1)
			unique_islands = max_unique - sum(v)
			nominator = sum(v) + unique_islands
			denominator = len(v) + unique_islands
			# v.extend([1]*unique_islands)
			island_data.setdefault(k, []).append(nominator / denominator)
	logging.info(
		"Finished processing single file, took: %s seconds with dict size of %s",
		time.monotonic() - start, len(data['occurrences']))
	if not found_some:
		logging.warning("FOUND NO REPETITIONS FOR ANY K!")
	with output.with_suffix(".json").open("w") as f:
		json.dump(
			{
				"expected_edge_len": expected_edge,
				"island_stats": island_data,
				"total_jumps": data['total_jumps'],
				"avg_jumps": data['avg_jumps'],
			}, f)


if __name__ == '__main__':
	# viz = Visualizer()
	# panel = Panel(range(10), range(0, 20, 2), "Ooga", "Booga")
	# viz.show([panel])
	OUTPUT = Path("~/university/jump_model_exp/1024_island_out").expanduser()
	OUTPUT.mkdir(exist_ok=True)
	BASE_PATH = Path("~/university/jump_model_exp/sixth_iteration").expanduser()
	data_files = list(filter(lambda x: not (OUTPUT / x.name).exists(), BASE_PATH.glob("*.json")))
	logging.info("Going over %s data files!", len(data_files))
	last_reported = 0
	step = len(data_files) // 10
	for index, data_file in enumerate(data_files):
		if index - last_reported > step:
			logging.info("Processed %s%", index // step * 10)
			last_reported = index
		try:
			_process_file(data_file)
		except Exception:
			logging.exception("oops")
	logging.info("DONE :)")
#     # fire.Fire(main)
