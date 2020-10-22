import itertools
import logging
import statistics
from typing import NamedTuple, Optional, List

from name_gen import NameGenerator
from genome import Genome


class BranchLenStats(NamedTuple):
    average: float
    median: float
    count: int


class TreeNode:
    def __init__(
            self, id_: int, name: str = '', edge_len: Optional[float] = None, bootstrap: Optional[float] = None,
            children: List["TreeNode"] = [], father: Optional["TreeNode"] = None):
        self.id = id_
        self.father = father
        self.children = children
        self.name = name
        self.edge_len = edge_len
        self.btstrp = bootstrap
        for child in self.children:
            child.father = self
        self.genome: Optional[Genome] = None

    def distance_from_root(self) -> float:  # TODO: This can be cached
        if self.father is None:
            return 0
        return (self.edge_len or 0) + self.father.distance_from_root()

    def extend(self, extend_to: float):
        my_distance = self.distance_from_root()
        logging.debug("Extending %s to %s. current: [%s]", self.name, extend_to, my_distance)
        assert my_distance <= extend_to
        delta = extend_to - my_distance
        if self.edge_len is None:
            self.edge_len = 0
        self.edge_len += delta
        new_distance = self.distance_from_root()
        assert isclose(new_distance, extend_to), f"Failed extending node {self.name}! distance {new_distance} expected: {extend_to}"
        logging.debug("Done extending, new length [%s]", new_distance)

    def to_newick(self) -> str:
        res = ''
        if self.children:
            res += f"({','.join((child.to_newick() for child in self.children))})"
        if self.name:
            res += self.name
        if self.edge_len:
            res += f":{self.edge_len}"
        if self.btstrp:
            res += f":{self.btstrp}"
        if self.father is None:
            res += ';'
        return res

    def print_genome(self, indent: int = 0, max_name_length: int = 8):
        prefix = " " * indent

        def _print(data: str):
            print(prefix + data)

        _print(str(self.genome))
        indent += round(len(self.genome) / 2)  # To align with the name of the node
        prefix = " " * indent
        if self.children:
            _print("|")
            for child in self.children:
                child.print_genome(indent)

    def print(self, indent: int = 0, max_name_length: int = 8):
        prefix = " " * indent

        def _print(data: str):
            print(prefix + data)

        name = self.name
        if len(self.name) > max_name_length:
            boundry = max_name_length // 2
            name = f"{name[:boundry]}...{name[-boundry:]}"
        if self.father:
            edge_len = self.edge_len or r"N\A"
            name = f"[{edge_len}]{name}"
        _print(name)
        indent += round(len(name) / 2)  # To align with the name of the node
        prefix = " " * indent
        if self.children:
            _print("|")
            for child in self.children:
                child.print(indent)

    def _get_branch_lengths(self) -> List[float]:
        res = []
        if self.father:
            res.append(self.edge_len)
        res.extend(itertools.chain.from_iterable(
            child._get_branch_lengths() for child in self.children))
        return res

    def branch_len_stats(self) -> BranchLenStats:
        lengths = self._get_branch_lengths()
        count = len(lengths)
        return BranchLenStats(sum(lengths) / count, statistics.median(lengths), count)


class TreeView(NamedTuple):
    root: TreeNode
    leaves: List[TreeNode]


class YuleTreeGenerator:  # TODO: Calculate average branch length, assert that it is as expected
    FLOATING_PNT_DIGITS = 5

    def __init__(self, size: int, scale: float):
        if scale <= 0:
            raise ValueError("scale must be a positive number")
        if size != 1 and size % 2 != 0:
            raise ValueError("size must be an even number")

        self._rndm_gen = default_rng()
        self._size = size
        self._scale = scale
        self._leaves: List[TreeNode] = []
        self._last_id = 0

    def _split(self):
        to_split: TreeNode = self._rndm_gen.choice(self._leaves)
        assert not to_split.children
        new = [
            TreeNode(
                self._last_id + i, edge_len=self._rndm_gen.exponential(scale=self._scale), father=to_split)
            for i in range(2)]
        to_split.children = new
        self._last_id += 2
        self._leaves.remove(to_split)
        self._leaves.extend(new)
        # self.complete_max_depth()

    def construct(self, complete_max_depth: bool = False) -> TreeView:
        root = TreeNode(0)
        if self._size == 1:
            return root
        self._leaves.append(root)
        while len(self._leaves) < self._size:
            self._split()
        if complete_max_depth:
            self.complete_max_depth()
        self.name_leaves()
        return TreeView(root, self._leaves)

    def name_leaves(self):
        name_gen = NameGenerator()
        for leaf in self._leaves:
            leaf.name = name_gen.next()

    def complete_max_depth(self):
        max_edge_len = max(leaf.distance_from_root() for leaf in self._leaves)
        for leaf in self._leaves:
            leaf.extend(max_edge_len)
        assert all(isclose(leaf.distance_from_root(), max_edge_len) for leaf in self._leaves)