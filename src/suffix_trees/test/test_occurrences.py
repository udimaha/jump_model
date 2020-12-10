import time
from typing import List
import random

import pytest

from ..STree import STree


def yield_token(string: str):
	for i in range(len(string) + 1):
		for j in range(i):
			yield string[j:i]


def count_naive(strings: List[str]):
	occurrences = {}
	for s in strings:
		for token in yield_token(s):
			if token not in occurrences:
				occurrences[token] = 0
			occurrences[token] += 1
	flat = {}
	# print(occurrences)
	for k, v in occurrences.items():
		if v <= 1:
			continue
		key = len(k)
		flat.setdefault(key, []).append(v)
	return flat


def _make_strings(string_count: int, string_size: int):
	base = list(map(chr, range(string_size)))
	strings = []
	for _ in range(string_count):
		new_ = list(base)
		random.shuffle(new_)
		strings.append(''.join(new_))
	return strings


def assert_algo(strings: List[str], check_runtime: bool = True):
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


def run_scenario(string_count: int = 256, string_size: int = 301):
	strings = _make_strings(string_count, string_size)
	assert_algo(strings)


@pytest.mark.parametrize("run", range(16))
def test_occurrences(run: int):
	run_scenario()


def _superset(string: str) -> List[str]:
	return [string[:i] for i in reversed(range(1, len(string) + 1))]


def test_specific():
	string = "abcdefghijk"
	strings = _superset(string)
	assert_algo(strings, False)
	strings.append(string + "xyz")
	assert_algo(strings, False)
	strings.append(string + "lmnop")
	assert_algo(strings, False)


def test_repeated():
	string = ''.join(["abcdefghijk"] * 16)
	strings = _superset(string)
	assert_algo(strings, False)
