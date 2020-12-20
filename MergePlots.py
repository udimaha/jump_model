from tempfile import TemporaryDirectory
from typing import List
import imageio
import fire
import re
import logging
from pathlib import Path
from PIL import Image
from pygifsicle import optimize as optimize_giff
from src.time_func import time_func

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


NUMBER_REGEX = r"\d+"
NUMBER_MATCHER = re.compile(NUMBER_REGEX)


def merge_files(directory: Path, file_pattern: str, output: Path):
	# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
	assert directory.is_dir()
	relevant = list(directory.glob(file_pattern))
	by_key = {}
	with time_func(f"Going over {len(relevant)} files"):
		for file in relevant:
			integers = NUMBER_MATCHER.findall(file.name)
			assert len(integers) == 1
			key = int(integers[0])
			by_key[key] = file
	steps = len(by_key) / 10
	with time_func("Creating the GIFF"):
		with imageio.get_writer(output, mode='I') as writer:
			for index, (_, filename) in sorted(by_key.items()):
				if index % steps == 0:
					logging.info("Progress %s percent done", index / steps * 10)
				image = imageio.imread(filename)
				writer.append_data(image)
	optimize_giff(output)
	# img, *imgs = [Image.open(f) for _, f in sorted(by_key.items())]
	# img.save(
	# 	fp=output, format='GIF', append_images=imgs, save_all=True, duration=200, loop=0)


if __name__ == '__main__':
	output_path = Path("~/university/jump_model_exp/").expanduser()
	visualized_path = Path("~/university/jump_model_exp/4096_island_out/visualized/").expanduser()
	assert visualized_path.is_dir()
	normalized_pattern = "normalized_*.png"
	pattern = "island_*.png"

	# Test
	normalized = list(visualized_path.glob(normalized_pattern))
	raw = list(visualized_path.glob(pattern))
	assert len(normalized) == len(raw)
	assert len(normalized) > 0
	assert list(map(str, normalized)) != list(map(str, raw))
	# Test

	merge_files(visualized_path, pattern, output_path / "island-3-4096.gif")
	merge_files(visualized_path, normalized_pattern, output_path / "norm-island-3-4096.gif")
