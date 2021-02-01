#!/usr/bin/env python
# coding: utf-8
from pathlib import Path
from typing import NamedTuple
import logging
import gzip
import json
import csv
import fire
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from tempfile import TemporaryDirectory
from collections import defaultdict
from src.scenario import read_real_data


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class Configuration(NamedTuple):
    data_path: Path
    output_path: Path

    def validate(self):
        if not self.data_path.is_dir():
            raise ValueError(f"Invalid real data path: [{self.data_path}]")


def parse_configuration(config_path: Path) -> Configuration:
    assert config_path.is_file(), f"Configuration file not found at: [{config_path}]"
    with config_path.open("r") as f:
        configuration = json.load(f)

    def get_conf_val(key: str):
        if key not in configuration:
            raise KeyError(f"Invalid configuration! Missing key: [{key}]")
        return configuration[key]

    realdata = Path(get_conf_val("real_data")).expanduser()
    output = Path(get_conf_val("output"))
    return Configuration(realdata, output)


def populate_realdata_csv(data_json: Path, out_dir: Path):
    with data_json.open("r") as f:
        data = json.load(f)
    sample_id = 0
    fieldnames = ["occur", "density", "norm-density"]
    for size_, dist in data.items():
        csv_out = out_dir / f"realdata-{size_}.csv"
        with csv_out.open("w") as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
            writer.writeheader()
            density = defaultdict(int)
            for occur in dist:
                density[occur] += 1
            for occur, density_ in density.items():
                writer.writerow(
                    {"occur": occur, "density": density_, "norm-density": np.log(density_)})
        sample_id += 1


def draw_csvs(out_dir: Path, data_dir: Path):
    for csv_file in data_dir.iterdir():
        data_set = pd.read_csv(csv_file)
        data_set = data_set.sort_values(by=["occur"])
        print(data_set)
        for normalized in (True, False):
            if normalized:
                ys = "norm-density"
                filename = f"norm-dist-{csv_file.name}"
            else:
                ys = "density"
                filename = f"dist-{csv_file.name}"
            plt.figure(figsize=(20, 20))
            sns.catplot(data=data_set, x="occur", y=ys)
            out_file = (out_dir / filename).with_suffix(".png")
            plt.savefig(str(out_file))


class Main:
    def parse(self, config: str):
        config_path = Path(config).expanduser()
        configuration = parse_configuration(config_path)
        configuration.validate()
        logging.info("Getting information from real data!")
        occurr = read_real_data(configuration.data_path)
        with gzip.open(str(configuration.output_path), "w") as f_gz:
            f_gz.write(json.dumps(occurr).encode())

    def draw(self, data_file: str, outdir: str):
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            populate_realdata_csv(Path(data_file).expanduser(), tmpdir_path)
            draw_csvs(out_dir=Path(outdir).expanduser(), data_dir=tmpdir_path)


if __name__ == '__main__':
    fire.Fire(Main)
