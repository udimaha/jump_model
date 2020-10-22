#!/usr/bin/env python
# coding: utf-8
import logging
from pathlib import Path
from typing import Optional
import uuid

from genome import GenomeMaker
from scenario import run_scenario
from time_func import time_func

logging.basicConfig(level=logging.INFO)


def main(
        size: int, scale: float, base_path: Path, pattern: str, iterations: int = 50,
        genome_maker: Optional[GenomeMaker] = None):
    for idx in range(iterations):
        with time_func(f"Running {idx} iteration of scenario with size {size} and scale {scale}"):
            result = run_scenario(size, scale, genome_maker=genome_maker)
        output = (base_path / f"{uuid.uuid4()}_{pattern}")
        output.write_text(result.to_json())


if __name__ == '__main__':
    BASE_PATH = Path("~/university/jump_model_exp/third_iteration").expanduser()
    size = 150
    scale = 0.1
    genome_maker = GenomeMaker()
    while scale < 2.1:
        logging.info("Starting iterations for scale: %s size: %s", scale, size)
        main(
            size, scale, base_path=BASE_PATH, pattern=f"scale_{scale}_size_{size}.json", 
            genome_maker=genome_maker)
        scale = round(scale + 0.1, ndigits=2)
    # fire.Fire(main)
