from src.genome import Genome


def calculate_synteny_index(g1: Genome, g2: Genome, gene: int, neighborhood_size: int) -> int:
    n1 = g1.get_neighbourhood(gene, neighborhood_size)
    n2 = g2.get_neighbourhood(gene, neighborhood_size)
    return len(n1 & n2)


def calculate_synteny_distance(g1: Genome, g2: Genome, neighborhood_size: int) -> float:
    set1 = set(g1.genes)
    set2 = set(g2.genes)
    all_genes = set1 | set2
    intersection = all_genes & set1 & set2
    sum_ = 0
    for gene in intersection:
        sum_ += calculate_synteny_index(g1, g2, gene, neighborhood_size)
    return 1 - ((sum_ / (2*neighborhood_size)) / len(all_genes))
