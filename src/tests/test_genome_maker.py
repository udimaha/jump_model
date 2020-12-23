import logging
from typing import List

import pytest
from numpy.random import default_rng
from src.genome import GenomeMaker, make_identity_genome, build_new_genome, NewPositions, Stayed, GenomeSegment, \
    gather_stayed, get_occupied_by_jumps, get_didnt_jump


class MockDefaultRNG:
    def __init__(self, seed: int = 9, choice_func = None, geometric_func = None, exponential_func = None):
        self._default_rng = default_rng(seed)
        self._exponential_func = exponential_func
        self._choice_func = choice_func
        self._geometric_func = geometric_func

    def exponential(self, scale, size):
        if self._exponential_func is not None:
            return self._exponential_func(scale, size)
        return self._default_rng.exponential(scale, size)

    def choice(self, data, size=None):
        if self._choice_func is not None:
            return self._choice_func(data, size)
        return self._default_rng.choice(data, size)

    def geometric(self, p: float, size=None):
        if self._geometric_func is not None:
            return self._geometric_func(p, size)
        return self._default_rng.geometric(p, size)


class TestableGenomeMaker(GenomeMaker):
    __test__ = False

    def __init__(self, rng: MockDefaultRNG, seed: int = 1, alpha: float = 1):
        super().__init__(seed, alpha)
        self._rndm_gen = rng


def count_jumped(genome_maker: GenomeMaker, scale: float = 0.5, genome_size: int = 20, iterations: int = 10) -> int:
    genome = make_identity_genome(genome_size)
    return sum(1 if genome_maker.make(genome, scale=scale)[0] > 0 else 0 for _ in range(iterations))


@pytest.mark.parametrize("jumping_positions, expected", (
    [
        ([], [GenomeSegment(0, 32)]),
        ([GenomeSegment(start=2, size=17)], [GenomeSegment(start=0, size=2), GenomeSegment(start=19, size=13)])
    ]
))
def test_get_didnt_jump(jumping_positions: List[GenomeSegment], expected: List[GenomeSegment]):
    genome = make_identity_genome(32)
    assert get_didnt_jump(genome, jumping_positions) == expected


@pytest.mark.parametrize("new_positions, expected", (
        [
            ({}, []),  # Nothing jumps
            ({6: [GenomeSegment(0, 10), GenomeSegment(12, 10)]}, [GenomeSegment(6, 20)]),
            ({6: [GenomeSegment(0, 10)], 9: [GenomeSegment(12, 3)]}, [GenomeSegment(6, 10), GenomeSegment(16, 3)]),
            (
                    {
                        0: [GenomeSegment(1, 5)],
                        1: [GenomeSegment(6, 3)],
                        2: [GenomeSegment(10, 1)],
                        3: [GenomeSegment(11, 1)]
                    },
                    [GenomeSegment(0, 5), GenomeSegment(5, 3), GenomeSegment(8, 1), GenomeSegment(9, 1)]
            ),
            (
                {
                    15: [GenomeSegment(start=2, size=1)], 17: [GenomeSegment(start=19, size=1)]
                },
                [GenomeSegment(15, 1), GenomeSegment(17, 1)]
            )
        ]
    ))
def test_get_occupied_by_jumps(new_positions: NewPositions, expected: List[GenomeSegment]):
    assert get_occupied_by_jumps(new_positions) == expected


@pytest.mark.parametrize("new_positions, expected", (
        [
            ({}, {0: GenomeSegment(0, 32)}),  # Nothing jumps
            ({0: [GenomeSegment(0, 32)]}, {}),  # Everything jumped together
            ({i: [GenomeSegment(31-i, 1)] for i in range(32)}, {}),  # Everything jumps independently
            ({16: [GenomeSegment(0, 16)]}, {0: GenomeSegment(16, 16)}),
            ({0: [GenomeSegment(0, 16)]}, {16: GenomeSegment(16, 16)}),
            (
                {2: [GenomeSegment(15, 1), GenomeSegment(17, 1)]},
                {0: GenomeSegment(0, 2), 4: GenomeSegment(2, 13), 17: GenomeSegment(16, 1), 18: GenomeSegment(18, 14)}
            ),
            (
                {2: [GenomeSegment(15, 3)], 4: [GenomeSegment(20, 4)], 16: [GenomeSegment(0, 4)]},
                {0: GenomeSegment(4, 2), 9: GenomeSegment(6, 7), 20: GenomeSegment(13, 2), 22: GenomeSegment(18, 2), 24: GenomeSegment(24, 8)}
            ),
            (
                {0: [GenomeSegment(start=2, size=17)]},
                {17: GenomeSegment(start=0, size=2), 19: GenomeSegment(start=19, size=13)}
            )
        ]
    ))
def test_gather_stayed(new_positions: NewPositions, expected: Stayed):
    genome = make_identity_genome(32)
    assert gather_stayed(genome, new_positions) == expected


@pytest.mark.parametrize("new_positions, stayed, expected", (
        [
            (
                {2: [GenomeSegment(1, 1), GenomeSegment(4, 1)]},
                {0: GenomeSegment(0, 1), 1: GenomeSegment(2, 1), 4: GenomeSegment(3, 1), 5: GenomeSegment(5, 1)},
                [(0, 1), (2, 1), (1, 1), (4, 1), (3, 1), (5, 1)]
            ),
            (
                {2: [GenomeSegment(1, 1), GenomeSegment(4, 3)]},
                {0: GenomeSegment(0, 1), 1: GenomeSegment(2, 1), 6: GenomeSegment(3, 1)},
                [(0, 1), (2, 1), (1, 1), (4, 3), (3, 1)]
            )
        ]
))
def test_build_new_genome(new_positions: NewPositions, stayed: Stayed, expected: List[GenomeSegment]):
    assert expected == build_new_genome(new_positions, stayed)


@pytest.mark.parametrize("scale", (0.5, 0.9, 1))
@pytest.mark.parametrize("alpha", (0.1, 0.5, 0.9, 1))
def test_genome_maker(scale: float, alpha: float):
    genome_maker = GenomeMaker(1, alpha)
    iterations = 32
    assert count_jumped(genome_maker, scale, iterations=iterations) > 0


@pytest.mark.parametrize("scale", (0.1, 0.5, 0.9, 1))
def test_nothing_jumps(scale: float):
    genome_maker = TestableGenomeMaker(MockDefaultRNG(exponential_func=lambda scale_, size_: [0]*size_))
    iterations = 32
    assert count_jumped(genome_maker, scale, iterations=iterations) == 0


def test_everything_jumps_individually():
    genome_maker = TestableGenomeMaker(MockDefaultRNG(exponential_func=lambda scale_, size_: [1]*size_))
    iterations = 32
    assert count_jumped(genome_maker, iterations=iterations) > 0


def test_everything_jumps_to_the_same_place():
    genome_maker = TestableGenomeMaker(
        MockDefaultRNG(
            exponential_func=lambda scale_, size_: [1]*size_, choice_func=lambda data_, size_: [1]*size_))
    iterations = 32
    assert count_jumped(genome_maker, iterations=iterations) == iterations


def test_everything_jumps_together():
    genome_size = 32
    iterations = 32
    genome_maker = TestableGenomeMaker(
        MockDefaultRNG(
            exponential_func=lambda scale_, size_: [1]*size_, geometric_func=lambda p, size: [genome_size]*size))
    assert count_jumped(genome_maker, iterations=iterations) == iterations

