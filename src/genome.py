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


class GenomeSegment(NamedTuple):
    start: int
    size: int

    def __len__(self) -> int:
        return self.size

    def __contains__(self, item) -> bool:
        if not isinstance(item, int):
            return False
        return item in range(self.start, self.start + self.size)

    @classmethod
    def from_interval(cls, interval: Interval) -> 'GenomeSegment':
        return GenomeSegment(start=interval.left, size=interval.length)

    @property
    def end(self) -> int:
        return self.start + self.size

    def make_interval(self) -> Interval:
        return Interval(left=self.start, right=self.end)

    def suffix(self, offset: int) -> 'GenomeSegment':
        assert 0 <= offset < self.size
        return GenomeSegment(self.start+offset, self.size-offset)

    def prefix(self, size: int) -> 'GenomeSegment':
        assert 0 <= size <= self.size, f"Received size: {size} my size is: {self.size}"
        return GenomeSegment(self.start, size)


class Genome:
    def __init__(self, genes: List[int]):
        self._genes = genes
        self._len = len(genes)
        assert self._len == len(set(self._genes)), "All genes must be unique"
        self._neighborhoods = {}

    def __eq__(self, other: 'Genome'):
        return self.len == other.len and self.genes == other.genes

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

    def by_segment(self, segment: GenomeSegment) -> List[int]:
        return self._genes[segment.start:segment.start + segment.size]


def make_identity_genome(size: int) -> Genome:
    return Genome(list(range(1, size+1)))


NewPositions = Dict[int, List[GenomeSegment]]


def get_occupied_by_jumps(jump_positions: NewPositions) -> List[GenomeSegment]:
    raw_occupied_by_jumping = [
        GenomeSegment(new_index, sum(map(len, jumps))) for new_index, jumps in jump_positions.items()]
    occupied_by_jumping = []
    last_occupied: Optional[GenomeSegment] = None
    for occupied in raw_occupied_by_jumping:
        if last_occupied is None or occupied.start not in last_occupied:
            occupied_by_jumping.append(occupied)
            last_occupied = occupied
        else:
            occupied_by_jumping.append(GenomeSegment(start=last_occupied.end, size=occupied.size))
            last_occupied = GenomeSegment(start=last_occupied.start, size=last_occupied.size+occupied.size)
    return occupied_by_jumping


Stayed = Dict[int, GenomeSegment]


def get_didnt_jump(genome: Genome, jumping_positions: List[GenomeSegment]) -> List[GenomeSegment]:
    didnt_jump = []
    index = 0
    for jump in jumping_positions:
        if index < jump.start:
            didnt_jump.append(GenomeSegment(index, jump.start - index))
        index = jump.end
    if index < genome.len:
        didnt_jump.append(GenomeSegment(index, genome.len - index))
    return didnt_jump


def gather_stayed(genome: Genome, new_positions: NewPositions) -> Stayed:
    if not new_positions:
        return {0: GenomeSegment(start=0, size=len(genome))}
    occupied_by_jumping = get_occupied_by_jumps(new_positions)

    non_jumping_count = genome.len - sum(map(len, occupied_by_jumping))
    if non_jumping_count == 0:
        logging.info("All the genes jumped!")
        return {}
    assert non_jumping_count > 0
    jumping_positions = sorted(itertools.chain.from_iterable(new_positions.values()), key=lambda pos: pos.start)
    didnt_jump = get_didnt_jump(genome, jumping_positions)
    stayed = {}
    last_filled = 0  # TODO: Use the last filled to set the key in the 'stayed' dictionary
    occupied_iter = iter(map(lambda segment: segment.make_interval(), occupied_by_jumping))
    non_jumping_iter = iter(didnt_jump)
    occupied = non_jumping = None
    try:
        occupied: Optional[Interval] = next(occupied_iter)
        non_jumping: Optional[GenomeSegment] = next(non_jumping_iter)
        assert non_jumping is not None
        assert occupied is not None
        while True:
            non_jumping_interval = Interval(
                left=last_filled, right=last_filled+non_jumping.size)
            if not non_jumping_interval.overlaps(occupied):
                if non_jumping_interval >= occupied:
                    last_filled = occupied.right
                    occupied: Interval = next(occupied_iter)
                else:
                    stayed[last_filled] = non_jumping
                    last_filled += non_jumping.size
                    non_jumping = None
                    non_jumping: GenomeSegment = next(non_jumping_iter)
            else:
                if non_jumping_interval.left < occupied.left:
                    step = occupied.left - non_jumping_interval.left
                    assert step > 0, f"occ: {occupied}, non_jump: {non_jumping_interval}"
                    stayed[last_filled] = non_jumping.prefix(step)
                    non_jumping = non_jumping.suffix(step)
                last_filled = occupied.right
                occupied: Interval = next(occupied_iter)
    except StopIteration:
        if non_jumping is not None:
            stayed[last_filled] = non_jumping
            last_filled += non_jumping.size
            for non_jumping in non_jumping_iter:  # Exhaust the iterator
                stayed[last_filled] = non_jumping
                last_filled += non_jumping.size
    return stayed


def build_new_genome(new_positions: NewPositions, stayed: Stayed) -> List[GenomeSegment]:
    new_iter = iter(new_positions.items())
    stay_iter = iter(stayed.items())
    new_genome = list()
    stayed_genome_segment: Optional[GenomeSegment] = None
    jumps = None
    try:
        new_index, jumps = next(new_iter)
        stayed_index, stayed_genome_segment = next(stay_iter)
        stayed_genome_segment: Optional[GenomeSegment]
        while True:
            if stayed_index < new_index:
                new_genome.append(stayed_genome_segment)
                stayed_genome_segment = None
                stayed_index, stayed_genome_segment = next(stay_iter)
            else:
                new_genome.extend(jumps)
                jumps = None  # Protect from StopIteration
                new_index, jumps = next(new_iter)
    except StopIteration:
        assert (stayed_genome_segment is None) ^ (jumps is None)
        if jumps:
            new_genome.extend(jumps)
            new_genome.extend(itertools.chain.from_iterable((jumps for _, jumps in new_iter)))  # Exhaust the iterator
        if stayed_genome_segment:
            new_genome.append(stayed_genome_segment)
            new_genome.extend(segment for _, segment in stay_iter)
    return new_genome


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
        jumping: List[GenomeSegment] = self._gather_jumping(genome, scale)
        if not jumping:
            logging.debug("No genes jumped!")
            return 0, Genome(genome.genes)
        logging.debug("%s Genes are jumping: %s", len(jumping), jumping)
        raw_new_positions = {
            jump: new_index for jump, new_index in zip(
                jumping, self._rndm_gen.choice(range(genome.len), size=len(jumping)))}
        fixed_new_positions = {
            jump: new_index
            if new_index + jump.size < genome.len
            else self._rndm_gen.choice(range(genome.len - jump.size + 1)) for jump, new_index in raw_new_positions.items()
        }
        new_positions: NewPositions = dict(sorted(self._order_jumped(fixed_new_positions).items()))
        stayed: Stayed = dict(sorted(gather_stayed(genome, new_positions).items()))
        logging.debug("Genes without those that jumped: %s", stayed)
        if not stayed:
            return len(jumping), Genome(
                list(itertools.chain.from_iterable(
                    genome.by_segment(segment) for segment in itertools.chain.from_iterable(new_positions.values()))))
        new_genome_positions = build_new_genome(new_positions, stayed)
        new_genome = list(
            itertools.chain.from_iterable(
                genome.by_segment(segment) for segment in new_genome_positions))
        if len(new_genome) != genome.len:
            raise RuntimeError(f"Jumping: {new_positions} Stayed: {stayed} new_genome positions: {new_genome_positions}")
        assert len(new_genome) == genome.len, f"Size mismatch! orig len: {genome.len} new_len: {len(new_genome)} new_genome: {new_genome}"
        return len(jumping), Genome(new_genome)

    @staticmethod
    def _order_jumped(new_positions: Dict[GenomeSegment, int]) -> NewPositions:
        ordered_jumped = {}
        for jump, new_index in new_positions.items():
            ordered_jumped.setdefault(new_index, []).append(jump)
        return ordered_jumped

    def _gather_jumping(self, genome: Genome, scale: float) -> List[GenomeSegment]:
        jumping: List[GenomeSegment] = []
        index = 0
        jump_probabilities = self._rndm_gen.exponential(scale=scale, size=genome.len)
        group_size_probabilities = self._rndm_gen.geometric(self._alpha, size=genome.len)
        while index < genome.len:
            if jump_probabilities[index] < 1:
                index += 1
                continue
            group_size = min(group_size_probabilities[index], genome.len - index)
            jumping.append(GenomeSegment(index, group_size))
            index += group_size
        return jumping


def test_get_neighbourhood():
    genome_maker = GenomeMaker(1, 1)
    gene = 1
    genome = make_identity_genome(20)
    print(f"Original genome: {genome} neighborhood: {genome.get_neighbourhood(gene, 5)}")
    for i in range(10):
        mut = genome_maker.make(genome, scale=0.3)
        print(f"Iteration {i}: {mut} neighborhood: {mut.get_neighbourhood(gene, 5)}")
