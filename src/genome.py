import itertools
import logging
from typing import List, Set, Tuple, NamedTuple, Iterator, Optional, Dict
from numpy.random import default_rng
from pandas import Interval


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


class Jump(NamedTuple):
    start: int
    size: int


class Genome:
    def __init__(self, genes: List[int]):
        self._genes = genes
        self._len = len(genes)
        assert self._len == len(set(self._genes)), "All genes must be unique"
        self._neighborhoods = {}

    @property
    def len(self) -> int:
        return self._len

    def __len__(self) -> int:
        return self._len

    def __str__(self) -> str:
        return str(self._genes)

    def __repr__(self):
        return str(self)

    @property
    def genes(self) -> List[int]:
        return self._genes

    def get_neighbourhood(self, gene: int, size: int) -> Set[int]:
        key = (gene, size)
        if key not in self._neighborhoods:
            self._neighborhoods[key] = get_neighbourhood(self._genes, gene, size)
        return self._neighborhoods[key]

    def __hash__(self) -> int:
        return hash(tuple(self._genes))

    def by_jump(self, jump: Jump) -> List[int]:
        return self._genes[jump.start:jump.start+jump.size]


def make_identity_genome(size: int) -> Genome:
    return Genome(list(range(1, size+1)))


NewPositions = Dict[int, List[List[int]]]
Stayed = Dict[int, List[int]]


class GenomeMaker:
    def __init__(self, seed: int, alpha: float):
        self._seed = seed
        assert 0 < alpha <= 1
        self._alpha = alpha
        self._rndm_gen = default_rng(seed)

    @property
    def seed(self):
        return self._seed

    def make(self, genome: Genome, scale: float) -> Tuple[int, Genome]:
        assert scale != 0
        logging.debug("Original genome: %s", genome.genes)
        jumping = self._gather_jumping(genome, scale)
        if not jumping:
            logging.debug("No genes jumped!")
            return 0, Genome(genome.genes)
        logging.debug("%s Genes are jumping: %s", len(jumping), jumping)
        raw_new_positions = {jump: self._rndm_gen.choice(range(genome.len - jump.size + 1)) for jump in jumping}
        new_positions: NewPositions = dict(sorted(self._order_jumped(genome, raw_new_positions).items()))
        stayed: Stayed = dict(sorted(self._gather_stayed(genome, jumping).items()))
        logging.debug("Genes without those that jumped: %s", stayed)
        if not stayed:
            return len(jumping), Genome(list(itertools.chain.from_iterable(itertools.chain.from_iterable(new_positions.values()))))

        new_genome = self._build_new_genome(genome, new_positions, stayed)
        return len(jumping), Genome(new_genome)

    @staticmethod
    def _build_new_genome(genome: Genome, new_positions: NewPositions, stayed: Stayed):
        new_iter = iter(new_positions.items())
        stay_iter = iter(stayed.items())
        new_genome = list()
        leftover = None
        try:
            new_index, jumps = next(new_iter)
            stayed_index, stayed_genome_segment = next(stay_iter)
            while True:
                stayed_interval = Interval(left=stayed_index, right=stayed_index + len(stayed_genome_segment))
                jump_interval = Interval(left=new_index, right=new_index + max(map(len, jumps)))
                while stayed_interval.overlaps(jump_interval):
                    if stayed_interval.left < jump_interval.left:
                        step = jump_interval.left - stayed_interval.left
                        assert step
                        new_genome.extend(stayed_genome_segment[:step])
                        stayed_genome_segment = stayed_genome_segment[step:]
                        stayed_index += step
                    new_genome.extend(itertools.chain.from_iterable(jumps))
                    leftover = stayed_genome_segment
                    new_index, jumps = next(new_iter)  # This might raise a StopIteration
                    leftover = None
                assert not stayed_interval.overlaps(jump_interval)
                if stayed_interval < jump_interval:
                    new_genome.extend(stayed_genome_segment)
                    stayed_index, stayed_genome_segment = next(stay_iter)
                else:
                    new_genome.extend(itertools.chain.from_iterable(jumps))
                    new_index, jumps = next(new_iter)
        except StopIteration:
            genome_changed = 0
            if leftover:
                new_genome.extend(leftover)
            curr_len = len(new_genome)

            def _check_genome():
                nonlocal curr_len, genome_changed
                if curr_len != len(new_genome):
                    genome_changed += 1
                curr_len = len(new_genome)

            new_genome.extend(itertools.chain.from_iterable(segment for _, segment in stay_iter))
            _check_genome()
            new_genome.extend(itertools.chain.from_iterable(itertools.chain.from_iterable(v for _, v in new_iter)))
            _check_genome()
            assert 0 <= genome_changed < 2
        assert len(new_genome) == genome.len, new_genome
        return new_genome

    @staticmethod
    def _order_jumped(genome: Genome, new_positions: Dict[Jump, int]) -> Dict[int, List[List[int]]]:
        ordered_jumped = {}
        for jump, new_index in new_positions.items():
            ordered_jumped.setdefault(new_index, []).append(genome.by_jump(jump))
        return ordered_jumped

    @staticmethod
    def _gather_stayed(genome: Genome, jumping: List[Jump]) -> Dict[int, List[int]]:
        last_index = 0
        stayed = {}
        for jump in jumping:
            if last_index < jump.start:
                stayed[last_index] = genome.genes[last_index:jump.start]
            last_index = jump.start + jump.size
        if last_index < genome.len:
            stayed[last_index] = genome.genes[last_index:]
        return stayed

    def _gather_jumping(self, genome: Genome, scale: float) -> List[Jump]:
        jumping: List[Jump] = []
        index = 0
        while index < genome.len:
            if not self._rndm_gen.exponential(scale=scale):
                index += 1
                continue
            group_size = min(self._rndm_gen.geometric(self._alpha), genome.len - index)
            jumping.append(Jump(index, group_size))
            index += group_size
        return jumping


def test_genome_maker():
    genome_maker = GenomeMaker(1, 1)
    genome = make_identity_genome(20)
    for i in range(10):
        print(f"Iteration {i}: {genome_maker.make(genome, scale=0.3)}")


def test_get_neighbourhood():
    genome_maker = GenomeMaker(1, 1)
    gene = 1
    genome = make_identity_genome(20)
    print(f"Original genome: {genome} neighborhood: {genome.get_neighbourhood(gene, 5)}")
    for i in range(10):
        mut = genome_maker.make(genome, scale=0.3)
        print(f"Iteration {i}: {mut} neighborhood: {mut.get_neighbourhood(gene, 5)}")
