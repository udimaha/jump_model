import json
import logging
import statistics
import struct
import time
import numpy.random
from math import isclose
from typing import Optional, NamedTuple, Dict, List, Tuple

from .genome import GenomeMaker, make_identity_genome
from .newick import NewickParser
from .occurrences import Occurrences, serialize_occurrences, deserialize_occurrences
from .phylip import PhylipNeighborConstructor, PhylipTreeDistCalculator
from .suffix_trees.STree import STree
from .synteny_index import calculate_synteny_distance
from .time_func import time_func
from .tree import TreeNode, BranchLenStats, YuleTreeGenerator


def fill_genome(
        node: TreeNode, genome_size: int, total_jumped: Optional[List[int]], maker: GenomeMaker):
    assert total_jumped is not None
    if node.father is None:
        identity_genome = make_identity_genome(genome_size)
        node.genome = identity_genome
    else:
        assert maker
        jumped, node.genome = maker.make(node.father.genome, scale=node.edge_len)
        total_jumped.append(jumped)
    for child in node.children:
        fill_genome(child, genome_size=genome_size, maker=maker, total_jumped=total_jumped)


class TreeDesc(NamedTuple):
    newick: str
    internal_edges: int
    branch_stats: BranchLenStats

    def to_json(self) -> dict:
        return {
           "newick": self.newick,
           "internal_edge_count": self.internal_edges,
           "edge_count": self.branch_stats.count,
           "median_edge_len": self.branch_stats.median,
           "average_edge_len": self.branch_stats.average,
        }

    def serialize(self) -> bytes:
        newick = self.newick.encode()
        format_ = f"i{len(newick)}siiff"
        return struct.pack(
            format_, len(newick), newick, self.internal_edges, self.branch_stats.count,
            self.branch_stats.median, self.branch_stats.average)

    @classmethod
    def deserialize(cls, data: bytes) -> Tuple[int, 'TreeDesc']:
        newick_len, = struct.unpack("i", data[:4])
        format_ = f"{newick_len}siiff"
        total_parsed = 4+struct.calcsize(format_)
        newick, internal_edges, edge_count, median_edge, avg_edge = struct.unpack(
            format_, data[4:total_parsed])
        return total_parsed, TreeDesc(
            newick.decode(), internal_edges, BranchLenStats(avg_edge, median_edge, edge_count))


class OldResult(NamedTuple):
    model_tree: TreeDesc
    constructed_tree: TreeDesc
    genome_size: int
    neighborhood_size: int
    expected_edge_len: float
    exclusive_edges: int
    false_positive: float
    false_negative: float
    tree_dist: float

    def to_json(self) -> str:
        data = {
            "model": self.model_tree.to_json(),
            "constructed": self.constructed_tree.to_json(),
            "genome_size": self.genome_size,
            "neighborhood_size": self.neighborhood_size,
            "expected_edge_len": self.expected_edge_len,
            "exclusive_edges": self.exclusive_edges,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "tree_dist": self.tree_dist
        }
        return json.dumps(data, indent=4)


def run_scenario_old(
    size: int, scale: float, neighborhood_size: int, genome_size: int,
        genome_maker: GenomeMaker) -> OldResult:
    with time_func("Constructing the Yule tree"):
        res = YuleTreeGenerator(size=size, scale=scale, seed=genome_maker.seed).construct()
    with time_func("Get branch statistics"):
        branch_stats = res.root.branch_len_stats()
    logging.info(
        "Branch count: %s avg: %s median: %s expected: %s", branch_stats.count,
        branch_stats.average, branch_stats.median, scale)
    total_jumped = []
    with time_func(f"Filling genome, size: {genome_size}"):
        fill_genome(res.root, genome_size=genome_size, maker=genome_maker, total_jumped=total_jumped)
    assert len(res.leaves) == size

    leaves_matrix = {}

    def fill_leaves_matrix():
        for row, l1 in enumerate(res.leaves):
            for l2 in res.leaves:
                leaves_matrix.setdefault(row, []).append((l1, l2))
    with time_func("Filling leaves matrix"):
        fill_leaves_matrix()
    distance_matrix = {}

    def fill_distance_matrix():
        calculated = {}
        durations = []
        for leave_vector in leaves_matrix.values():
            for l1, l2 in leave_vector:
                name1 = l1.name
                name2 = l2.name
                key = tuple(sorted([name1, name2]))
                if key in calculated:
                    distance = calculated[key]
                else:
                    if l1.name == l2.name:  # Small optimization
                        distance = 0
                    else:
                        time_before_call = time.monotonic()
                        distance = calculate_synteny_distance(l1.genome, l2.genome, neighborhood_size)
                        duration = time.monotonic() - time_before_call
                        durations.append(duration)

                    calculated[key] = distance
                distance_matrix.setdefault(l1.name, []).append(distance)
        total = sum(durations)
        size = len(durations)
        max_duration = max(durations)
        logging.info(
            "Number of calculations: %s avg duration: %s max duration: %s total duration: %s", size, total / size, max_duration, total)
    with time_func("Filling distance matrix"):
        fill_distance_matrix()

    constructor = PhylipNeighborConstructor()
    with time_func("Runing Phylip Neighbor constructor"):
        orig, constructed = constructor.construct(res.root, distance_matrix)
    distance_calc = PhylipTreeDistCalculator()
    with time_func("Runing Phylip TreeDist"):
        distance_res = distance_calc.calc(orig, constructed)
    logging.debug("Original tree: ")
    logging.debug(orig)
    logging.debug("Constructed tree:")
    logging.debug(constructed)
    logging.debug("TreeDist result:")
    logging.debug(distance_res)
    internal_branches_orig = len([c for c in orig if c == ')']) - 1
    internal_branches_constructed = len([c for c in constructed if c == ')']) - 1
    distance_without_len = distance_calc.calc(orig, constructed, False)
    assert distance_without_len // 1 == distance_without_len
    distance_without_len = int(distance_without_len)
    logging.debug("Distance without len: %s", distance_without_len)
    common_edges = ((internal_branches_orig + internal_branches_constructed) - distance_without_len) / 2
    if internal_branches_orig == 0:
        fp = 1
    else:
        fp = (internal_branches_orig - common_edges) / internal_branches_orig
    if internal_branches_constructed == 0:
        fn = 1
    else:
        fn = (internal_branches_constructed - common_edges) / internal_branches_constructed
    logging.debug("False positive estimator: %s", fp)
    logging.debug("False negative estimator: %s", fn)
    model_tree = TreeDesc(orig, internal_branches_orig, branch_stats)
    constructed_res = NewickParser(constructed).parse()
    constructed_tree = TreeDesc(constructed, internal_branches_constructed, constructed_res.root.branch_len_stats())
    return OldResult(
        model_tree, constructed_tree, genome_size, neighborhood_size, scale, distance_without_len,
        fp, fn, distance_res
    )


class Result(NamedTuple):
    model_tree: TreeDesc
    genome_size: int
    expected_edge_len: float
    leaves_count: int
    total_jumps: int
    avg_jumps: float
    seed: int
    occurrences: Occurrences

    def to_json(self) -> str:
        data = {
            "model": self.model_tree.to_json(),
            "genome_size": self.genome_size,
            "total_jumps": self.total_jumps,
            "avg_jumps": self.avg_jumps,
            "expected_edge_len": self.expected_edge_len,
            "leaves_count": self.leaves_count,
            "seed": self.seed,
            "occurrences": json.dumps(self.occurrences)
        }
        return json.dumps(data, indent=4)

    def serialize(self) -> bytes:
        format_ = "ifiif"
        return self.model_tree.serialize() + struct.pack(
            format_, self.genome_size, self.expected_edge_len, self.leaves_count) + serialize_occurrences(self.occurrences)

    @classmethod
    def deserialize(cls, data: bytes) -> 'Result':
        parsed, model_tree = TreeDesc.deserialize(data)
        format_ = "ifiif"
        total_parsed = parsed+struct.calcsize(format_)
        genome_size, expected_edge_len, leaves_count, total_jumps, avg_jumps = struct.unpack(format_, data[parsed:total_parsed])
        occurrences = deserialize_occurrences(data[total_parsed:])
        return Result(model_tree, genome_size, expected_edge_len, leaves_count, total_jumps, avg_jumps, occurrences)

    def __eq__(self, other: 'Result') -> bool:
        if self.genome_size != other.genome_size or not isclose(
                self.expected_edge_len, other.expected_edge_len, rel_tol=1e-07) or self.leaves_count != other.leaves_count or self.total_jumps != other.total_jumps or isclose(self.avg_jumps, other.avg_jumps):
            return False
        if self.model_tree != other.model_tree:
            return False
        if len(self.occurrences) != len(other.occurrences):
            return False
        for k, v in self.occurrences.items():
            if k not in other.occurrences:
                return False
            if v != other.occurrences[k]:
                return False
        return True


def run_scenario(
    size: int, scale: float, genome_size: int) -> Result:
    with time_func("Seeding numpy random"):
        random_seed = int(time.time() * 1000000)
        numpy.random.seed(random_seed)
        genome_maker = GenomeMaker(random_seed)

    with time_func("Constructing the Yule tree"):
        res = YuleTreeGenerator(size=size, scale=scale, seed=random_seed).construct()
    with time_func("Get branch statistics"):
        branch_stats = res.root.branch_len_stats()
    logging.info(
        "Branch count: %s avg: %s median: %s expected: %s", branch_stats.count,
        branch_stats.average, branch_stats.median, scale)
    total_jumped = []
    with time_func(f"Filling genome, size: {genome_size}"):
        fill_genome(res.root, genome_size=genome_size, maker=genome_maker, total_jumped=total_jumped)

    assert len(res.leaves) == size

    newick = res.root.to_newick()
    internal_branches_orig = len([c for c in newick if c == ')']) - 1
    model_tree = TreeDesc(newick, internal_branches_orig, branch_stats)
    suffix_tree = STree([''.join(map(chr, leaf.genome.genes)) for leaf in res.leaves])
    with time_func("Counting occurrences"):
        occurrences = suffix_tree.occurrences()
    return Result(
        model_tree, genome_size, scale, size, sum(total_jumped), statistics.mean(total_jumped) if total_jumped else 0,
        random_seed, occurrences
    )
