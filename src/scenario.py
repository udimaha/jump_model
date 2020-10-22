import json
import logging
import time
from typing import Optional, NamedTuple

from genome import GenomeMaker, make_identity_genome
from newick import NewickParser
from phylip import PhylipNeighborConstructor, PhylipTreeDistCalculator
from synteny_index import calculate_synteny_distance
from time_func import time_func
from tree import TreeNode, BranchLenStats, YuleTreeGenerator


def fill_genome(node: TreeNode, genome_size: int = 10, maker: Optional[GenomeMaker] = None):
    if not maker:
        maker = GenomeMaker()
    if node.father is None:
        identity_genome = make_identity_genome(genome_size)
        node.genome = identity_genome
    else:
        assert maker
        node.genome = maker.make(node.father.genome, scale=node.edge_len)
    for child in node.children:
        fill_genome(child, genome_size=genome_size, maker=maker)


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


class Result(NamedTuple):
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


def run_scenario(
    size: int, scale: float, neighborhood_size: int, genome_size: int,
        genome_maker: Optional[GenomeMaker] = None) -> Result:
    with time_func("Constructing the Yule tree"):
        res = YuleTreeGenerator(size=size, scale=scale).construct()
    with time_func("Get branch statistics"):
        branch_stats = res.root.branch_len_stats()
    logging.info(
        "Branch count: %s avg: %s median: %s expected: %s", branch_stats.count,
        branch_stats.average, branch_stats.median, scale)
    with time_func(f"Filling genome, size: {genome_size}"):
        fill_genome(res.root, genome_size=genome_size, maker=genome_maker)
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
    print("Original tree: ")
    print(orig)
    print("Constructed tree:")
    print(constructed)
    print("TreeDist result:")
    print(distance_res)
    internal_branches_orig = len([c for c in orig if c == ')']) - 1
    internal_branches_constructed = len([c for c in constructed if c == ')']) - 1
    distance_without_len = distance_calc.calc(orig, constructed, False)
    assert distance_without_len // 1 == distance_without_len
    distance_without_len = int(distance_without_len)
    print(f"Distance without len: {distance_without_len}")
    common_edges = ((internal_branches_orig + internal_branches_constructed) - distance_without_len) / 2
    if internal_branches_orig == 0:
        fp = 1
    else:
        fp = (internal_branches_orig - common_edges) / internal_branches_orig
    if internal_branches_constructed == 0:
        fn = 1
    else:
        fn = (internal_branches_constructed - common_edges) / internal_branches_constructed
    print(f"False positive estimator: {fp}")
    print(f"False negative estimator: {fn}")
    model_tree = TreeDesc(orig, internal_branches_orig, branch_stats)
    constructed_res = NewickParser(constructed).parse()
    constructed_tree = TreeDesc(constructed, internal_branches_constructed, constructed_res.root.branch_len_stats())
    return Result(
        model_tree, constructed_tree, genome_size, neighborhood_size, scale, distance_without_len,
        fp, fn, distance_res
    )
