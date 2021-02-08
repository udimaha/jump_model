from src.genome import Genome
from src.phylip.synteny_index import calculate_synteny_distance


def test_calculate_synteny_distance():
    g1 = Genome(list(range(15)))
    g2 = Genome(list(range(15, 30)))
    assert calculate_synteny_distance(g1, g2, 5) == 1
    for g in [g1, g2]:
        s = calculate_synteny_distance(g, g, 5)
        assert s == 0, s
        s = calculate_synteny_distance(g, Genome(list(reversed(g.genes))), 5)
        assert s == 0, s
