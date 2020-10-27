import matplotlib.pyplot as plt
from typing import Iterable, NamedTuple, List


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


if __name__ == '__main__':
	viz = Visualizer()
	panel = Panel(range(10), range(0, 20, 2), "Ooga", "Booga")
	viz.show([panel])
#     BASE_PATH = Path("~/university/jump_model_exp/third_iteration").expanduser()
#     size = 150
#     scale = 2.0
#     genome_maker = GenomeMaker()
#     while scale < 2.1:
#         logging.info("Starting iterations for scale: %s size: %s", scale, size)
#         main(size, scale, base_path=BASE_PATH, genome_maker=genome_maker)
#         scale = round(scale + 0.1, ndigits=2)
#     # fire.Fire(main)