import itertools
import logging
from typing import List, Set
from numpy.random import default_rng


def get_neighbourhood(genome: List[int], gene: int, size: int) -> Set[int]:
    genome_len = len(genome)
    assert size*2 <= genome_len
    assert gene in genome
    if genome_len == (size*2)+1:
        all_genes = set(genome)
        all_genes.remove(gene)
        return all_genes
    index = genome.index(gene)
    offsets = range(1, size + 1)
    forward_indexes = [(index + offset) % genome_len for offset in offsets]
    backward_indexes = [(index - offset + genome_len) % genome_len for offset in offsets]
    neighborhood = set(genome[idx] for idx in itertools.chain(forward_indexes, backward_indexes))
    assert len(neighborhood) == size*2
    return neighborhood


class Genome:
    def __init__(self, genes: List[int]):
        self._genes = genes
        self._len = len(genes)
        assert self._len == len(set(self._genes)), "All genes must be unique"
        self._neighborhoods = {}

    @property
    def len(self) -> int:
        return self._len

    @property
    def genes(self) -> List[int]:
        return self._genes

    def get_neighbourhood(self, gene: int, size: int) -> Set[int]:
        if gene not in self._neighborhoods:
            self._neighborhoods[gene] = get_neighbourhood(self._genes, gene, size)
        return self._neighborhoods[gene]

    def __hash__(self) -> int:
        return hash(tuple(self._genes))


def make_identity_genome(size: int) -> Genome:
    return Genome(list(range(1, size+1)))


class GenomeMaker:
    def __init__(self):
        self._rndm_gen = default_rng()

    def make(self, genome: Genome, scale: float) -> Genome:
        assert scale != 0
        logging.debug("Original genome: %s", genome.genes)
        jumping = [
            index
            for index, probability in enumerate(self._rndm_gen.exponential(scale=scale, size=genome.len))
            if probability >= 1]
        if not jumping:
            logging.debug("No genes jumped!")
            return Genome(genome.genes)
        logging.debug("%s Genes are jumping: %s", len(jumping), jumping)
        new_genome = list()
        last_index = 0
        for jump in jumping:
            new_genome.extend(genome.genes[last_index:jump])
            last_index = jump+1
        if last_index < genome.len:
            new_genome.extend(genome.genes[last_index:])
        logging.debug("Genes without those that jumped: %s", new_genome)
        new_positions = dict(zip(jumping, self._rndm_gen.choice(
                range(genome.len), size=len(jumping))))
        for old_idx, new_idx in new_positions.items():
            if new_idx >= len(new_genome):
                new_genome.append(genome.genes[old_idx])
                continue
            new_genome = new_genome[:new_idx] + [genome.genes[old_idx]] + new_genome[new_idx:]
        assert len(new_genome) == genome.len, new_genome
        return Genome(new_genome)


def test_genome_maker():
    genome_maker = GenomeMaker()
    genome = make_identity_genome(20)
    for i in range(10):
        print(f"Iteration {i}: {genome_maker.make(genome, scale=0.3)}")


def test_get_neighbourhood():
    genome_maker = GenomeMaker()
    gene = 1
    genome = make_identity_genome(20)
    print(f"Original genome: {genome} neighborhood: {genome.get_neighbourhood(gene, 5)}")
    for i in range(10):
        mut = genome_maker.make(genome, scale=0.3)
        print(f"Iteration {i}: {mut} neighborhood: {mut.get_neighbourhood(gene, 5)}")
