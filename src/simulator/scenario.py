import gzip
import json
import logging
import statistics
import struct
import time
import uuid
from concurrent import futures
from pathlib import Path

import numpy.random
from math import isclose
from typing import NamedTuple

from src.genome import GenomeMaker
from src.occurrences import Occurrences, serialize_occurrences, deserialize_occurrences
from src.simulator.configuration import Configuration, MAX_PROCESSES
from src.suffix_trees.STree import STree
from src.time_func import time_func
from src.tree import YuleTreeGenerator, fill_genome, TreeDesc


class Result(NamedTuple):
    model_tree: TreeDesc
    genome_size: int
    expected_edge_len: float
    leaves_count: int
    total_jumps: int
    avg_jumps: float
    alpha: float
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
            "occurrences": json.dumps(self.occurrences),
            "alpha": self.alpha
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


def run_scenario(size: int, scale: float, genome_size: int, alpha: float, ultrametric: bool) -> Result:
    with time_func("Seeding numpy random"):
        random_seed = int(time.time())
        numpy.random.seed(random_seed)
        genome_maker = GenomeMaker(random_seed, alpha)

    with time_func("Constructing the Yule tree"):
        res = YuleTreeGenerator(size=size, scale=scale, seed=random_seed).construct(ultrametric)
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
    concat_genomes = [leaf.genome.genes for leaf in res.leaves]
    suffix_tree = STree(concat_genomes)
    with time_func("Counting occurrences"):
        occurrences = suffix_tree.occurrences()
    return Result(
        model_tree, genome_size, scale, size, sum(total_jumped), statistics.mean(total_jumped) if total_jumped else 0,
        alpha, random_seed, occurrences
    )


def run_single_job(
        pattern: str, leaf_count: int, scale: float, base_path: Path, alpha: float, genome_size: int, idx: int,
        ultrametric: bool):
    assert pattern
    with time_func(f"Running tree: {idx} of scenario with {leaf_count} leaves, alpha: {alpha} and scale: {scale}"):
        result = run_scenario(leaf_count, scale, genome_size=genome_size, alpha=alpha, ultrametric=ultrametric)
    outdir = base_path / str(scale)
    outdir.mkdir(exist_ok=True)
    output = outdir / f"{uuid.uuid4()}_{pattern}"
    with gzip.open(str(output.with_suffix(".json.gz")), "w") as f_gz:
        f_gz.write(result.to_json().encode())


def run_scenarios(configuration: Configuration, scale: float):
    assert 0 < configuration.processes <= MAX_PROCESSES
    pattern = configuration.file_pattern(scale)
    with futures.ThreadPoolExecutor(max_workers=configuration.processes) as executor:
        jobs = [
            executor.submit(
                run_single_job, pattern, configuration.leaf_count, scale, configuration.data_path, configuration.alpha,
                configuration.genome_size, idx, configuration.ultrametric)
            for idx in range(configuration.tree_count)]
        for job in futures.as_completed(jobs):
            try:
                job.result()
            except Exception as e:
                logging.exception("Failed running job!!!")
