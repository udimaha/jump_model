import logging
import re
from pathlib import Path

import imageio
from pygifsicle import optimize as optimize_giff

from src.time_func import time_func

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
	step = len(by_key) / 10
	with time_func("Creating the GIFF"):
		with imageio.get_writer(output, mode='I') as writer:
			for index, (_, filename) in enumerate(sorted(by_key.items())):
				if index % step == 0:
					logging.info("Progress %s percent done", (index // step) * 10)
				image = imageio.imread(filename)
				writer.append_data(image)
	with time_func(f"Optimizing giff: {output}"):
		optimize_giff(str(output.absolute()))