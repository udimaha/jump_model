#!/usr/bin/env python
# coding: utf-8
import logging
import gzip
from pathlib import Path
from typing import Optional
import uuid
from src.genome import GenomeMaker
from src.scenario import run_scenario
from src.time_func import time_func

logging.basicConfig(level=logging.INFO)


def main(
        size: int, scale: float, base_path: Path, iterations: int = 10,
        genome_maker: Optional[GenomeMaker] = None, genome_size: int = 1024):
    pattern = f"scale_{scale}_size_{size}_genome_{genome_size}.json"
    for idx in range(iterations):
        with time_func(f"Running {idx} iteration of scenario with size {size} and scale {scale}"):
            result = run_scenario(
                size, scale, genome_size=genome_size, genome_maker=genome_maker)
        output = (base_path / f"{uuid.uuid4()}_{pattern}")
        with gzip.open(str(output.with_suffix(".json.gz")), "w") as f_gz:
            f_gz.write(result.to_json().encode())


if __name__ == '__main__':
    BASE_PATH = Path("~/university/jump_model_exp/seventh_iteration").expanduser()
    size = 150
    scale = 0.1
    step = 0.1
    genome_maker = GenomeMaker()
    while scale < 0.2:
        logging.info("Starting iterations for scale: %s size: %s", scale, size)
        main(size, scale, base_path=BASE_PATH, genome_maker=genome_maker)
        scale = round(scale + step, ndigits=2)
    # fire.Fire(main)
