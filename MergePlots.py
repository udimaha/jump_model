import fire
import logging
from pathlib import Path

from src.plots.merge import merge_files

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


def main(output_dir: str, output_name: str, visualized_path: str):
	output_dir = Path(output_dir).expanduser()
	visualized_path = Path(visualized_path).expanduser()
	assert visualized_path.is_dir()
	normalized_pattern = "normalized_*.png"
	pattern = "island_*.png"

	merge_files(visualized_path, pattern, output_dir / output_name)
	merge_files(visualized_path, normalized_pattern, output_dir / f"norm-{output_name}")


if __name__ == '__main__':
	fire.Fire(main)
