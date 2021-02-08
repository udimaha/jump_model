from typing import Dict

import numpy


def likelihood(simulated: Dict[int, int], realdata: Dict[int, int]):
	total_simulated = sum(simulated.values())
	total_realdata = sum(realdata.values())
	res = 0
	for size, occur in realdata.items():
		if occur == 0:
			continue
		if size not in simulated:
			continue
		res += ((occur / total_realdata) * numpy.log(simulated[size] / total_simulated))
	return res
