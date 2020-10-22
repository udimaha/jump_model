import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Tuple

from tree import TreeNode


class PhylipDrawer:
    BASE_PATH = Path("~/phylip-3.695/exe").expanduser()
    DRAWGRAM_PATH = BASE_PATH / "drawgram.app/Contents/MacOS/drawgram"
    FONT_PATH = BASE_PATH / "font5"
    OUTPUT_PATH = BASE_PATH / "plotfile"
    INPUT_PATH = BASE_PATH / "intree"

    def __init__(self):
        assert self.BASE_PATH.exists()
        assert self.DRAWGRAM_PATH.exists()
        assert self.DRAWGRAM_PATH.is_file()

    def draw(self, tree: TreeNode, output: Path):
        if self.OUTPUT_PATH.exists():
            self.OUTPUT_PATH.unlink()
        self.INPUT_PATH.write_text(tree.to_newick())
        subprocess.check_call(
            f"echo Y | {self.DRAWGRAM_PATH}", shell=True, cwd=self.BASE_PATH, stdout=subprocess.DEVNULL)
        assert self.OUTPUT_PATH.exists()
        self.OUTPUT_PATH.rename(output)


class PhylipNeighborConstructor:
    BASE_PATH = Path("~/phylip-3.695/exe").expanduser()
    NEIGHBOR_PATH = BASE_PATH / "neighbor.app/Contents/MacOS/neighbor"
    OUT_TREE = BASE_PATH / "outtree"
    OUTPUT_PATHS = [OUT_TREE, BASE_PATH / "outfile"]
    INPUT_PATH = BASE_PATH / "infile"

    def __init__(self):
        assert self.BASE_PATH.exists()
        assert self.NEIGHBOR_PATH.exists()
        assert self.NEIGHBOR_PATH.is_file()

    def construct(self, root: TreeNode, matrix: Dict[str, List[float]]) -> Tuple[str, str]:
        for f in self.OUTPUT_PATHS:
            if f.exists():
                f.unlink()
        text = f'  {len(matrix)}\n' +  '\n'.join(
            name + ' '*9 + '  '.join(
                str(round(distance, 4)).ljust(6, '0') for distance in distances) for name, distances in matrix.items())
        self.INPUT_PATH.write_text(text)
        subprocess.check_call(
            f"echo Y | {self.NEIGHBOR_PATH}", shell=True, cwd=self.BASE_PATH, stdout=subprocess.DEVNULL)
        for f in self.OUTPUT_PATHS:
            assert f.exists()
        orig_tree = root.to_newick()
        constructed_tree = self.OUT_TREE.read_text().replace("\n", "")
        return orig_tree, constructed_tree


class PhylipTreeDistCalculator:
    BASE_PATH = Path("~/phylip-3.695/exe").expanduser()
    TREE_DIST_PATH = BASE_PATH / "treedist.app/Contents/MacOS/treedist"
    OUTPUT_PATH = BASE_PATH / "outfile"
    INPUT_PATH = BASE_PATH / "intree"

    def __init__(self):
        assert self.BASE_PATH.exists()
        assert self.TREE_DIST_PATH.exists()
        assert self.TREE_DIST_PATH.is_file()

    def calc(self, tree1: str, tree2: str, use_edge_length: bool = True) -> float:
        if self.OUTPUT_PATH.exists():
            self.OUTPUT_PATH.unlink()
        self.INPUT_PATH.write_text(tree1 + '\n' + tree2)
        with NamedTemporaryFile("w") as input_file:
            options = "Y"
            if not use_edge_length:
                options = f"D\n{options}"
            input_file.write(options)
            input_file.flush()
            subprocess.check_call(
                f"{self.TREE_DIST_PATH} < {input_file.name}", shell=True, cwd=self.BASE_PATH, stdout=subprocess.DEVNULL)
        assert self.OUTPUT_PATH.exists()
        text = self.OUTPUT_PATH.read_text().strip()
        last_line = text.split('\n')[-1]
        return float(last_line.replace("Trees 1 and 2:", "").strip())