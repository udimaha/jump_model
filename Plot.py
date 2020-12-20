import gzip
import time
import json
import statistics
from pathlib import Path
import logging
from typing import List


logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


class SummaryStatistics:
	def __init__(self, v: List[int]):
		self._mean: float = statistics.mean(v)
		self._median: float = statistics.median(v)


def _process_file(to_process: Path):
	output = OUTPUT / to_process.name
	assert not output.exists()
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
				"total_jumps": data['total_jumps'],
				"avg_jumps": data['avg_jumps'],
			}
		f.write(json.dumps(data).encode())


if __name__ == '__main__':
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
