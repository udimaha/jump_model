import logging
from typing import NamedTuple, Dict, Optional, Iterable, Tuple, List

from src.tree import TreeNode


class NewickParserResult(NamedTuple):
    tree_map: Dict[str, TreeNode]
    root: TreeNode


class ParserContext:
    END_CHAR = ";"
    SPECIAL_CHARS = ":,;()"

    def __init__(self, data: str):
        if not data:
            raise ValueError("Parser initialized with empty data")
        if data[-1] != self.END_CHAR:
            raise SyntaxError(f"Tree must end with: [{self.END_CHAR}]")
        self.data = data
        self.cursor = 0
        self.data_len = len(data)

    @property
    def last_parsed(self) -> Optional[str]:
        if self.cursor == 0:
            return None
        return self.data[self.cursor - 1]

    @property
    def at_end(self) -> bool:
        assert self.cursor <= self.data_len
        return self.cursor == self.data_len

    @property
    def data_range(self) -> Iterable[int]:
        return range(self.cursor, self.data_len)

    def advance(self, count: int):
        assert count > 0
        if count + self.cursor > self.data_len:
            raise ValueError("Advancing cursor out of bounds")
        self.cursor += count

    def parse_token(self) -> Optional[Tuple[int, int, str]]:
        for idx in self.data_range:
            if self.data[idx] in self.SPECIAL_CHARS:
                start = self.cursor
                self.cursor = idx + 1
                logging.debug("Parsed token: [%s]", self.data[start:idx])
                return start, idx, self.data[idx]
        return None


class NewickParser:
    PROPERTY_MARKER = ":"
    NODE_SEPERATOR = ","
    SUBTREE_START_MARKER = "("
    SUBTREE_END_MARKER = ")"
    NODE_END_MARKERS = NODE_SEPERATOR + SUBTREE_END_MARKER
    ROOT_NAME = "ROOT"

    def __init__(self, data: str):
        self._context = ParserContext(data)
        self._tree_map = {}
        self._node_count = 0
        self._subtree_depth = 0

    @property
    def data(self) -> str:
        return self._context.data

    def parse(self) -> NewickParserResult:
        nodes = self._parse_nodes()
        if len(nodes) > 1:
            raise SyntaxError("Tree must have a single root!")
        elif len(nodes) == 0:
            raise SyntaxError("Received empty tree!")
        root = nodes[0]
        assert self.ROOT_NAME not in self._tree_map, f"{self.ROOT_NAME} is a reserved node name."
        root.name = self.ROOT_NAME
        assert root.father is None
        assert root.btstrp is None
        assert root.edge_len in [None, 0]
        return NewickParserResult(self._tree_map, root)

    def _at_node_end(self) -> bool:
        return self._context.at_end or (
            self._context.last_parsed is not None and self._context.last_parsed in self.NODE_END_MARKERS)

    def _parse_nodes(self) -> List[TreeNode]:
        nodes = []
        token_res = self._context.parse_token()
        while token_res is not None:
            children = []
            start, end, tok = token_res
            if tok != self.SUBTREE_START_MARKER:
                assert start <= end
            else:
                orig_depth = self._subtree_depth
                self._subtree_depth += 1
                logging.debug("Entering recursion depth: [%s]", self._subtree_depth)
                children = self._parse_nodes()
                logging.debug("Exiting recursion depth: [%s]", self._subtree_depth)
                assert children
                if self._subtree_depth != orig_depth:
                    raise SyntaxError(
                        f"Input tree has unbalanced brackets! Orig: [{orig_depth}] curr: [{self._subtree_depth}]")
                self._context.advance(1)  # Advance the last bracket

            name = None
            bootstrap = None
            edge_len = None
            if not self._context.at_end:
                if children:
                    name = "-".join((child.name for child in children))
                else:
                    if start == end:
                        raise SyntaxError(f"All nodes must have names! end: {end}")
                    name = self._context.data[start:end]
                    logging.debug("Parsed name: [%s]", name)
                if name in self._tree_map:
                    raise SyntaxError(f"Name {name} appears twice in the tree! Node names must be unique")
                if not self._at_node_end():
                    edge_len = self._parse_edge_len()
                    logging.debug("Parsed edge len: [%s]", edge_len)
                if not self._at_node_end():
                    bootstrap = self._parse_bootstrap()
                    logging.debug(f"Parsed bootstrap: [%s]", bootstrap)
            node = TreeNode(
                id_=self._node_count, name=name, edge_len=edge_len, bootstrap=bootstrap, children=children)
            self._node_count += 1
            self._tree_map[name] = node
            nodes.append(node)
            last_parsed = self._context.last_parsed
            assert last_parsed is not None
            if last_parsed == self.SUBTREE_END_MARKER:
                logging.debug("Encountered subtree end marker at: [%s]", self._context.cursor)
                if self._subtree_depth == 0:
                    raise SyntaxError(f"Input tree has unbalanced brackets! cursor: [{self._context.cursor}]")
                self._subtree_depth -= 1
                return nodes
            token_res = self._context.parse_token()
        return nodes

    def _parse_edge_len(self) -> Optional[float]:
        return self._parse_property(self.PROPERTY_MARKER + self.NODE_END_MARKERS + ParserContext.END_CHAR)

    def _parse_bootstrap(self) -> Optional[float]:
        return self._parse_property(self.NODE_END_MARKERS + ParserContext.END_CHAR)

    def _parse_property(self, markers: Iterable[str]) -> Optional[float]:
        token_res = self._context.parse_token()
        if token_res is None:
            raise SyntaxError("Malformed tree")
        start, end, tok = token_res
        if tok not in markers:
            raise SyntaxError(f"Nodes missing properties! tok: [{tok}] expected: [{markers}] cursor: [{self._context.cursor}]")
        assert end >= start
        if end == start:
            return None
        else:
            try:
                return float(self.data[start:end])
            except ValueError:
                raise SyntaxError(f"Malformed property! {self.data[start:end]}")
