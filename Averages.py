import gzip
import time
import json
import statistics
from pathlib import Path
import logging
import fire
from typing import List, NamedTuple

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


class SummaryStatistics:
	def __init__(self, v: List[int]):
		self._mean: float = statistics.mean(v)
		self._median: float = statistics.median(v)


def _process_file(output: Path, to_process: Path):
	island_data = {}
	start = time.monotonic()
	with gzip.open(str(to_process), "r") as f:
		data = json.loads(f.read().decode())
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
	with gzip.open(str(output), "w") as f:
		data = {
			"genome_size": genome_size,
			"leaves_count": leaves,
			"expected_edge_len": expected_edge,
			"island_stats": island_data,
			"total_jumps": data["total_jumps"],
			"avg_jumps": data["avg_jumps"],
			"alpha": data["alpha"],
			"seed": data["seed"]
		}
		f.write(json.dumps(data).encode())


class Configuration(NamedTuple):
	data_folder: Path
	output_folder: Path
	file_pattern: str

	def validate(self):
		assert self.data_folder.is_dir()
		assert next(self.data_folder.iterdir(), None) is not None


def parse_configuration(config_path: Path) -> Configuration:
	assert config_path.is_file(), f"Configuration file not found at: [{config_path}]"
	with config_path.open("r") as f:
		configuration = json.load(f)

	def get_conf_val(key: str, default=None):
		if key not in configuration:
			if default:
				return default
			raise KeyError(f"Invalid configuration! Missing key: [{key}]")
		return configuration[key]

	data_path = get_conf_val("data")
	output_path = get_conf_val("output")
	file_pattern = get_conf_val("file_pattern", "*.gz")
	return Configuration(
		data_folder=Path(data_path).expanduser(), output_folder=Path(output_path).expanduser(), file_pattern=file_pattern)


def main(config: str):
	config_path = Path(config).expanduser()
	configuration = parse_configuration(config_path)
	configuration.validate()
	configuration.output_folder.mkdir(exist_ok=True)
	data_files = list(
		filter(
			lambda x: not (configuration.output_folder / x.name).exists(),
			configuration.data_folder.glob(configuration.file_pattern)))
	logging.info("Going over %s data files!", len(data_files))
	last_reported = 0
	step = len(data_files) // 10
	for index, data_file in enumerate(data_files):
		if index - last_reported > step:
			logging.info("Processed %s%", index // step * 10)
			last_reported = index
		try:
			output = configuration.output_folder / data_file.name
			assert not output.exists()
			_process_file(output, data_file)
		except Exception:
			logging.exception("oops")
	logging.info("DONE :)")


if __name__ == '__main__':
	fire.Fire(main)
