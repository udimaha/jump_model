import gzip
import json
from pathlib import Path
from typing import List, Dict, Tuple


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
		average_jumps = float(data["avg_jumps"])
		total_jumps = data["total_jumps"]
		jump_stats = avg_jumps.setdefault(edge_len, JumpStats())
		# assert total_jumps != average_jumps # TODO: Fix this! Shouldn't be equal
		jump_stats.avg.append(average_jumps)
		jump_stats.total.append(total_jumps)
		for k, v in stats.items():
			assert len(v) == 1
			dist_data = distribution.setdefault(k, {}).setdefault(edge_len, DistData())
			dist_data.avg_occurrences.append(float(v[0]))
			dist_data.avg_jumps.append(average_jumps)
	return distribution, avg_jumps
