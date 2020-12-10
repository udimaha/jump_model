import random

import pytest


def _make_strings(string_count: int, string_size: int):
	base = list(map(chr, range(string_size)))
	strings = []
	for _ in range(string_count):
		new_ = list(base)
		random.shuffle(new_)
		strings.append(''.join(new_))
	return strings


@pytest.mark.parametrize("string", _make_strings(100, 100))
@pytest.mark.parametrize("island_size", range(1, 100))
def test_count_unique(string: str, island_size: int):
	count = len(range(island_size-1, len(string)))
	assert count == (len(string) - island_size + 1)
