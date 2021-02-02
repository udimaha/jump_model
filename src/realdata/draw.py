from pathlib import Path

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

FONT_SIZE = 4
LABEL_ROTATION_ANGLE = 30
PNG_DPI = 2500
FIGURE_HEIGHT = 3
FIGURE_ASPECT = 3.3
X_AXIS = "occur"


def draw_csvs(out_dir: Path, data_dir: Path):
    for csv_file in data_dir.iterdir():
        data_set = pd.read_csv(csv_file)
        data_set = data_set.sort_values(by=["occur"])
        print(data_set)
        for normalized in (False,):# True):
            if normalized:
                ys = "norm-density"
                filename = f"norm-dist-{csv_file.name}"
            else:
                ys = "density"
                filename = f"dist-{csv_file.name}"
            out_file = (out_dir / filename).with_suffix(".png")
            if out_file.exists():
                continue
            g = sns.catplot(data=data_set, x=X_AXIS, y=ys, kind="bar", height=FIGURE_HEIGHT, aspect=FIGURE_ASPECT)
            g.set_xticklabels(rotation=LABEL_ROTATION_ANGLE, fontsize=FONT_SIZE)
            plt.savefig(str(out_file), dpi=PNG_DPI)
            plt.close(str(out_file))