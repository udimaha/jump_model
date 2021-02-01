import time
from typing import List
import random

import pytest

from ..STree import STree


def yield_token(string: List[int]):
	for i in range(len(string) + 1):
		for j in range(i):
			yield tuple(string[j:i])


def count_naive(strings: List[List[int]]):
	occurrences = {}
	for s in strings:
		for token in yield_token(s):
			if token not in occurrences:
				occurrences[token] = 0
			occurrences[token] += 1
	flat = {}
	for k, v in occurrences.items():
		if v <= 1:
			continue
		key = len(k)
		flat.setdefault(key, []).append(v)
	return flat


def _make_strings(string_count: int, string_size: int) -> List[List[int]]:
	base = list(range(string_size))
	strings = []
	for _ in range(string_count):
		new_ = list(base)
		random.shuffle(new_)
		strings.append(new_)
	return strings


def assert_algo(strings: List[List[int]], check_runtime: bool = True):
	x = STree(strings)
	occurrences_start = time.perf_counter()
	res = x.occurrences()
	occurrences_runtime = time.perf_counter() - occurrences_start
	naive_start = time.perf_counter()
	naive = count_naive(strings)
	naive_runtime = time.perf_counter() - naive_start
	if check_runtime:
		assert occurrences_runtime < naive_runtime
	for k, v in naive.items():
		assert k in res, f"{k} not found in occurrences result!"
		assert sorted(res[k]) == sorted(v), f"Occurrences algorithm produced different results than naive algo for island size {k}: naive {v} != {res[k]} occurrences"


def run_scenario(string_count: int = 8, string_size: int = 301):
	strings = _make_strings(string_count, string_size)
	assert_algo(strings)


@pytest.mark.parametrize("run", range(16))
def test_occurrences(run: int):
	run_scenario()


def _superset(string: List[int]) -> List[List[int]]:
	return [string[:i] for i in reversed(range(1, len(string) + 1))]


def test_specific():
	string = list(range(11)) # "abcdefghijk"
	strings = _superset(string)
	assert_algo(strings, False)
	strings.append(string + [100,101,102])
	assert_algo(strings, False)
	strings.append(string + [80,81,82,83])
	assert_algo(strings, False)


# @pytest.mark.skip(reason="Currently fails for repeating input")
# def test_repeated():
# 	# string = ''.join(["abcdefghijk"] * 2)
# 	string = ''.join(["abcd"] * 2)
# 	strings = _superset(string)
# 	assert_algo(strings, False)

#

