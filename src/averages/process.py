import gzip
import json
import logging
import time
from pathlib import Path


def process_file(output: Path, to_process: Path):
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