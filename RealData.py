#!/usr/bin/env python
# coding: utf-8
from pathlib import Path
import logging
import fire
from tempfile import TemporaryDirectory

from src.realdata.csv import populate_realdata_csv
from src.realdata.draw import draw_csvs
from src.realdata.parse import parse_realdata

DENSITY_THRESHOLD = 3
OCCURRENCES_THRESHOLD = 10

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class Main:
    def parse(self, config: str):
        config_path = Path(config).expanduser()
        parse_realdata(config_path)

    def make_csvs(self, data_file: str, outdir: str, min_occur: int, min_density: int):
        populate_realdata_csv(
            Path(data_file).expanduser(), Path(outdir).expanduser(), min_occur, min_density)

    def draw(self, data_file: str, outdir: str):
        with TemporaryDirectory() as tmpdir:
            self.make_csvs(data_file, tmpdir, min_occur=OCCURRENCES_THRESHOLD, min_density=DENSITY_THRESHOLD)
            draw_csvs(out_dir=Path(outdir).expanduser(), data_dir=Path(tmpdir))


if __name__ == '__main__':
    fire.Fire(Main)
