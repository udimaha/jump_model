import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def populate_realdata_csv(data_json: Path, out_dir: Path, min_occur: int, min_density: int):
    with data_json.open("r") as f:
        data = json.load(f)
    sample_id = 0
    fieldnames = ["occur", "density", "norm-density"]
    for size_, dist in data.items():
        csv_out = out_dir / f"realdata-{size_}.csv"
        found_any = False
        with csv_out.open("w") as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
            writer.writeheader()
            density = defaultdict(int)
            for occur in dist:
                density[occur] += 1
            for occur, density_ in density.items():
                if density_ < min_density or occur < min_occur:
                    continue
                found_any = True
                writer.writerow(
                    {"occur": occur, "density": density_, "norm-density": np.log(density_)})
            sample_id += 1
        if not found_any:
            csv_out.unlink()
