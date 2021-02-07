import itertools
import logging
import statistics
from math import isclose
from typing import NamedTuple, Optional, List
from numpy.random import default_rng
from .name_gen import NameGenerator
from .genome import Genome


class BranchLenStats(NamedTuple):
    average: float
    median: float
    count: int

    def __eq__(self, other: 'BranchLenStats'):
        return self.count == other.count and isclose(self.average, other.average, rel_tol=1e-07) and isclose(self.median, other.median, rel_tol=1e-07)


class TreeNode:
    def __init__(
            self, id_: int, name: str = '', edge_len: Optional[float] = None, bootstrap: Optional[float] = None,
            children: Optional[List["TreeNode"]] = None, father: Optional["TreeNode"] = None):
        if children is None:
            children = []
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

    def __init__(self, size: int, scale: float, seed: int):
        if scale <= 0:
            raise ValueError("scale must be a positive number")
        self._rndm_gen = default_rng(seed)
        self._size = size
        self._scale = scale
        self._leaves: List[TreeNode] = []
        self._last_id = 0

    def new_id(self) -> int:
        self._last_id += 1
        return self._last_id

    def _split(self, to_split: TreeNode):
        new = [
            TreeNode(
                self.new_id(), edge_len=self._rndm_gen.exponential(scale=self._scale), father=to_split)
            for i in range(2)]
        to_split.children = new
        self._leaves.remove(to_split)
        self._leaves.extend(new)

    def _hang(self, to_hang: TreeNode):
        hang_at = self._rndm_gen.random() * to_hang.edge_len
        to_hang.edge_len -= hang_at
        new_father = TreeNode(
            self.new_id(), edge_len=hang_at, father=to_hang.father
        )
        siebling = TreeNode(
            self.new_id(), edge_len=self._rndm_gen.exponential(scale=self._scale), father=new_father)
        new_father.children = [siebling, to_hang]
        to_hang.father.children.remove(to_hang)
        to_hang.father.children.append(new_father)
        to_hang.father = new_father
        self._leaves.append(siebling)

    def construct(self, ultrametric: bool = False) -> TreeView:
        root = TreeNode(0)
        if self._size == 1:
            return TreeView(root, [root])
        self._leaves.append(root)
        while len(self._leaves) < self._size:
            leaf: TreeNode = self._rndm_gen.choice(self._leaves)
            assert not leaf.children
            if ultrametric and leaf is not root:
                self._hang(leaf)
            else:
                self._split(leaf)
        # if ultrametric:  # TODO: This is a naive implementation of ultrametric construction
        #     self.complete_max_depth()
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
