import random

import pytest

from ..occurrences import Occurrences, serialize_occurrences, deserialize_occurrences
from src.simulator.scenario import Result
from ..tree import BranchLenStats, TreeDesc


def _rand_int() -> int:
	return random.randint(1, 10000)


def _make_branch_stats() -> BranchLenStats:
	return BranchLenStats(random.random(), random.random(), _rand_int())


def _make_tree_desc() -> TreeDesc:
	tree_size = random.randint(16, 255)
	fake_newick = ''.join(map(chr, range(tree_size)))
	return TreeDesc(fake_newick, _rand_int(), _make_branch_stats())


def _make_occurrences() -> Occurrences:
	occ = {}
	island_count = random.randint(16, 255)
	for island_size in random.sample(range(1, 4096), island_count):
		samples_count = random.randint(7, 1024)
		occ[island_size] = list(random.choices(range(2, 255), k=samples_count))
	return occ


def _make_result() -> Result:
	return Result(_make_tree_desc(), _rand_int(), random.random(), _rand_int(), _make_occurrences())


@pytest.mark.parametrize("desc", [_make_tree_desc() for _ in range(1024)])
def test_serialize_tree_desc(desc: TreeDesc):
	serialized = desc.serialize()
	parsed, deserialized = TreeDesc.deserialize(serialized)
	assert parsed > 0
	assert desc == deserialized, f"Failed desc serialization test! Desc: [{desc}] != [{deserialized}]"


@pytest.mark.parametrize("occ", [_make_occurrences() for _ in range(1024)])
def test_serialize_occurrences(occ: Occurrences):
	serialized = serialize_occurrences(occ)
	deserialized = deserialize_occurrences(serialized)
	assert occ == deserialized, f"Failed occurrences serialization test! Occ: [{occ}] != [{deserialized}]"


@pytest.mark.parametrize("res", [_make_result() for _ in range(1024)])
def test_serialize_result(res: Result):
	serialized = res.serialize()
	deserialized = Result.deserialize(serialized)
	assert res == deserialized, f"Failed Result serialization test! res: [{res}] != [{deserialized}]"
