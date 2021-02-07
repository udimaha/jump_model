import itertools
from typing import Set, Dict, Union, Optional, List, Generator, Callable, Tuple

Input = Union[List[int], List[List[int]]]
Suffix = Tuple


def input_type(input_: Input) -> str:
    """Checks the validity of the input.

    In case of an invalid input throws ValueError.
    """
    if not input_:
        raise ValueError("Received empty input!")
    if isinstance(input_[0], list):
        assert len(input_) > 1
        if all(isinstance(item, list) for item in input_):
            input_: List[List[int]]
            if all(all(isinstance(item, int) for item in numlist) for numlist in input_):
                return 'gst'
    elif isinstance(input_[0], int):
        if all(isinstance(item, int) for item in input_):
            return 'st'
    raise ValueError("String argument should be of type String or a list of strings")


def terminal_symbols_generator() -> Generator[int, None, None]:
    for term in itertools.count(start=-1, step=-1):
        yield term


def starts_with(to_check: List[int], possible_prefix: Union[Tuple[int], List[int]]) -> bool:
    if len(possible_prefix) > len(to_check):
        return False
    return list(possible_prefix) == to_check[:len(possible_prefix)]


class STree:
    """Class representing the suffix tree."""

    def __init__(self, input_: Input):
        self.root = SNode()
        self.root.depth = 0
        self.root.idx = 0
        self.root.parent = self.root
        self.root.add_suffix_link(self.root)
        self.word: List[int] = []
        assert input_
        if isinstance(input_[0], list):
            input_: List[List[int]]
            assert all(numlist for numlist in input_)
            assert all(all(num >= 0 for num in numlist) for numlist in input_)
        else:
            input_: List[int]
            assert all(num >= 0 for num in input_)
        self.build(input_)

    def build(self, x: Input):
        """Builds the Suffix tree on the given input.
        If the input is of type List of Strings:
        Generalized Suffix Tree is built.

        :param x: String or List of Strings
        """
        if not x:
            raise ValueError("Received empty input!")
        if isinstance(x[0], list) and len(x) == 1:
            x = x[0]
        type_ = input_type(x)

        if type_ == 'st':
            x += [next(terminal_symbols_generator())]
            self._build(x)
        if type_ == 'gst':
            self._build_generalized(x)

    def _build(self, x: List[int]):
        """Builds a Suffix tree."""
        self.word = x
        self._build_McCreight(x)

    def _build_McCreight(self, x: List[int]):
        """Builds a Suffix tree using McCreight O(n) algorithm.

        Algorithm based on:
        McCreight, Edward M. "A space-economical suffix tree construction algorithm." - ACM, 1976.
        Implementation based on:
        UH CS - 58093 String Processing Algorithms Lecture Notes
        """
        u = self.root
        d = 0
        for i in range(len(x)):
            while u.depth == d and u.has_transition((x[d + i],)):
                u = u.get_transition_link((x[d + i],))
                d = d + 1
                while d < u.depth and x[u.idx + d] == x[i + d]:
                    d = d + 1
            if d < u.depth:
                u = make_node(x, u, d)
            make_leaf(x, i, u, d)
            if not u.get_suffix_link():
                compute_slink(x, u)
            u = u.get_suffix_link()
            d = d - 1
            if d < 0:
                d = 0

    def _build_generalized(self, xs: List[List[int]]):
        """Builds a Generalized Suffix Tree (GST) from the array of strings provided.
        """
        terminal_gen = terminal_symbols_generator()
        #self._terminals = [next(terminal_gen) for _ in range(len(xs))]
        #assert len(set(self._terminals)) == len(xs) == len(self._terminals)
        _xs: List[int] = list(itertools.chain.from_iterable(x + [next(terminal_gen)] for x in xs))
        self.word = _xs
        self._generalized_word_starts(xs)
        self._build(_xs)
        self.root.traverse(self._label_generalized)
        self.root.get_occurrences()

    def _label_generalized(self, node: "SNode"):
        """Helper method that labels the nodes of GST with indexes of strings
        found in their descendants.
        """
        if node.is_leaf():
            x = {self._get_word_start_index(node.idx)}
        else:
            x = {n for ns in node.transition_links.values() for n in ns.generalized_idxs}
        node.generalized_idxs = x

    def _get_word_start_index(self, idx: int) -> int:
        """Helper method that returns the index of the string based on node's
        starting index"""
        i = 0
        for _idx in self.word_starts[1:]:
            if idx < _idx:
                return i
            else:
                i += 1
        return i

    def _get_branch(self, node) -> List[int]:
        if node is node.parent:
            return []
        """Helper method, returns the edge label between a node and it's parent"""
        return self._get_branch(node.parent) + self.word[node.idx + node.parent.depth: node.idx + node.depth]

    def _count_occurrences(self, node: "SNode") -> bool:
        if node in self._visited:
            return True
        self._visited.add(node)
        count = node.get_occurrences()
        assert count > 0, f"WTF? {node}"
        if count == 1:  # TODO: Test how much does this improve performance-wise
            return False
        island = self._get_branch(node)  # node.branch
        start_sub_island = self._get_branch(node.parent)
        assert starts_with(island, start_sub_island), f"Island is: {island} sub-island is: {start_sub_island} parent is: {node.parent}"
        start_gap = len(island) - len(start_sub_island)
        for gap_index in (start_gap,):
            for gap in range(1, gap_index):
                key = len(island) - gap
                self._occurences.setdefault(key, []).append(count)
        self._occurences.setdefault(len(island), []).append(count)
        return True

    def occurrences(self) -> dict:
        self._occurences = {}
        self._visited: Set["SNode"] = set()  # TODO: Fuck this is stupid
        self._visited.add(self.root)
        self.root.traverse_if(self._count_occurrences)
        return self._occurences

    def lcs(self, string_idxs= -1) -> List[int]:
        """Returns the Largest Common Substring of Strings provided in stringIdxs.
        If stringIdxs is not provided, the LCS of all strings is returned.

        ::param stringIdxs: Optional: List of indexes of strings.
        """
        if string_idxs == -1 or not isinstance(string_idxs, list):
            string_idxs = set(range(len(self.word_starts)))
        else:
            string_idxs = set(string_idxs)

        deepest = self._find_lcs(self.root, string_idxs)
        start = deepest.idx
        end = deepest.idx + deepest.depth
        return self.word[start:end]

    def _find_lcs(self, node: "SNode", string_idxs: Set[int]) -> "SNode":
        """Helper method that finds LCS by traversing the labeled GSD."""
        nodes = [
            self._find_lcs(n, string_idxs)
            for n in node.transition_links.values()
            if n.generalized_idxs.issuperset(string_idxs)
        ]
        if not nodes:
            return node
        deepest = max(nodes, key=lambda n: n.depth)
        return deepest

    def _generalized_word_starts(self, xs: List[List[int]]):
        """Helper method returns the starting indexes of strings in GST"""
        self.word_starts = []
        i = 0
        for n in range(len(xs)):
            self.word_starts.append(i)
            i += len(xs[n]) + 1

    def find(self, y: Suffix) -> int:
        node = self.root
        while True:
            edge = self._edge_label(node, node.parent)
            if starts_with(edge, y):
                return node.idx

            i = 0
            while i < len(edge) and edge[i] == y[0]:
                y = y[1:]
                i += 1

            if i != 0:
                if i == len(edge) and y:
                    pass
                else:
                    return -1

            node = node.get_transition_link((y[0],))
            if not node:
                return -1

    def find_all(self, y: Suffix) -> Set[int]:
        node = self.root
        while True:
            edge = self._edge_label(node, node.parent)
            if starts_with(edge, y):
                break
            i = 0
            while i < len(edge) and edge[i] == y[0]:
                y = y[1:]
                i += 1

            if i != 0:
                if i == len(edge) and y:
                    pass
                else:
                    return set()

            node = node.get_transition_link((y[0],))
            if not node:
                return set()
        leaves = node.get_leaves()
        return {n.idx for n in leaves}

    def _edge_label(self, node: "SNode", parent: "SNode") -> List[int]:
        """Helper method, returns the edge label between a node and it's parent"""
        return self.word[node.idx + parent.depth: node.idx + node.depth]


class SNode:
    __slots__ = [
        '_suffix_link', 'transition_links', 'idx', 'depth', 'parent', 'generalized_idxs', 'occurrences']

    """Class representing a Node in the Suffix tree."""

    def __init__(self, idx=-1, parent: Optional["SNode"] = None, depth=-1):
        # Links
        self._suffix_link = None
        self.transition_links: Dict[Suffix, "SNode"] = {}
        # Properties
        self.idx = idx
        self.depth = depth
        self.parent: "SNode" = parent
        self.generalized_idxs = set()
        self.occurrences = 0

    def __str__(self):
        if self.is_root:
            return "ROOT"
        if self.parent.is_root:
            my_parent = "ROOT"
        else:
            my_parent = str(self.parent)
        return (
                "SNode: idx:" + str(self.idx) +
                " transitons:" + str(list(self.transition_links.keys())) +
                " branch: " + str(self.branch) +
                " labels: " + str(self.generalized_idxs)
                # " parent: " + my_parent #+
        #        " depth:" + str(self.depth)
        )

    def get_occurrences(self) -> int:
        if self.occurrences != 0:
            return self.occurrences
        if self.is_leaf():
            self.occurrences = len(self.generalized_idxs)
        else:
            self.occurrences = sum(node.get_occurrences() for node in self.transition_links.values())
        return self.occurrences

    @property
    def is_root(self) -> bool:
        return self.parent is self

    @property
    def branch(self) -> Tuple:
        if self is self.parent:
            return ()
        # parent_branch = self.parent.branch
        # if self.parent.is_root:
        #     print("My parent is the root")
        # else:
        #     print(f"Parent branch: {parent_branch} for {self.parent}")
        # print(f"My branch is: {me[0]}")
        res = self.parent.branch + self.segment
        if self.is_leaf():
            res = res[:-1]
        return res

    @property
    def segment(self) -> Tuple:
        if self is self.parent:
            return ()
        me = [k for k, v in self.parent.transition_links.items() if v is self]
        assert len(me) == 1, f"What am I? {me}"
        res = me[0]
        if self.is_leaf():
            res = res[:-1]
        return res

    @property
    def suffix_link(self) -> "SNode":
        assert self._suffix_link
        return self._suffix_link

    def add_suffix_link(self, snode: "SNode"):
        self._suffix_link = snode

    def get_suffix_link(self) -> Union[bool, "SNode"]:
        if self._suffix_link is not None:
            return self._suffix_link
        else:
            return False

    def get_transition_link(self, suffix: Suffix) -> Union[bool, "SNode"]:
        return False if suffix not in self.transition_links else self.transition_links[suffix]

    def add_transition_link(self, snode: "SNode", suffix: Suffix):
        self.transition_links[suffix] = snode

    def has_transition(self, suffix: Suffix) -> bool:
        return suffix in self.transition_links

    def is_leaf(self):
        if self.is_root:
            return False
        #parent_branch = self.parent.branch
        return len(self.transition_links) == 0
        # return len(self.transition_links) == 0

    def traverse_if(self, f: Callable):
        if not f(self):
            return
        for node in self.transition_links.values():
            node.traverse(f)

    def traverse(self, f: Callable):
        for node in self.transition_links.values():
            node.traverse(f)
        f(self)

    def get_leaves(self):
        # Python <3.6 dicts don't perserve insertion order (and even after, we
        # shouldn't rely on dicts perserving the order) therefore these can be
        # out-of-order, so we return a set of leaves.
        if self.is_leaf():
            return {self}
        else:
            return {x for n in self.transition_links.values() for x in n.get_leaves()}


def make_node(x: List[int], u: SNode, d: int) -> SNode:
    i = u.idx
    p = u.parent
    v = SNode(idx=i, depth=d)
    v.add_transition_link(u, (x[i + d],))
    u.parent = v
    p.add_transition_link(v, (x[i + p.depth],))
    assert v is not p
    v.parent = p
    return v


def make_leaf(x: List[int], i: int, u: SNode, d: int) -> SNode:
    w = SNode()
    w.idx = i
    w.depth = len(x) - i
    u.add_transition_link(w, (x[i + d],))
    assert w is not u
    w.parent = u
    return w


def compute_slink(x: List[int], u: SNode):
    d = u.depth
    v = u.parent.get_suffix_link()
    while v.depth < d - 1:
        v = v.get_transition_link((x[u.idx + v.depth + 1],))
    if v.depth > d - 1:
        v = make_node(x, v, d - 1)
    u.add_suffix_link(v)
