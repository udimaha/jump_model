#!/usr/bin/env python
# coding: utf-8
import logging
import gzip
import json
from pathlib import Path
from typing import Optional, NamedTuple
import uuid

import fire

from src.scenario import run_scenario
from src.time_func import time_func


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def run_scenarios(
        leaf_count: int, scale: float, base_path: Path, alpha: float, tree_count: int,
        genome_size: int):
    pattern = f"scale_{scale}_leaves_{leaf_count}_genome_{genome_size}_alpha_{alpha}.json"
    for idx in range(tree_count):
        with time_func(f"Running tree: {idx} of scenario with {leaf_count} leaves, alpha: {alpha} and scale: {scale}"):
            result = run_scenario(
                leaf_count, scale, genome_size=genome_size)
        output = (base_path / f"{uuid.uuid4()}_{pattern}")
        with gzip.open(str(output.with_suffix(".json.gz")), "w") as f_gz:
            f_gz.write(result.to_json().encode())


class Scale(NamedTuple):
    begin: float
    end: float
    step: float

    def validate(self):
        assert self.begin < self.end <= 1
        assert self.step < 1 and self.begin + self.step < self.end


class Configuration(NamedTuple):
    data_path: Path
    tree_count: int
    alpha: float
    genome_size: int
    leaf_count: int
    scale: Scale

    def validate(self):
        assert self.tree_count > 0
        assert 0 < self.alpha <= 1
        assert self.genome_size > 0
        assert self.data_path.is_dir()
        self.scale.validate()


def parse_configuration(config_path: Path) -> Configuration:
    assert config_path.is_file(), f"Configuration file not found at: [{config_path}]"
    with config_path.open("r") as f:
        configuration = json.load(f)

    def get_conf_val(key: str):
        if key not in configuration:
            raise KeyError(f"Invalid configuration! Missing key: [{key}]")
        return configuration[key]

    tree_count = get_conf_val("tree_count")
    data_path = get_conf_val("data_path")
    alpha = get_conf_val("alpha")
    genome_size = get_conf_val("genome_size")
    leaf_count = get_conf_val("leaf_count")
    scale = Scale(*get_conf_val("scale"))
    return Configuration(
        data_path=Path(data_path).expanduser(), tree_count=tree_count, alpha=alpha,
        genome_size=genome_size, leaf_count=leaf_count, scale=scale
    )


def main(config: str):
    config_path = Path(config).expanduser()
    configuration = parse_configuration(config_path)
    configuration.validate()
    logging.info(
        "Running scenarios for genome size: %s tree count: %s leaf count: %s alpha: %s", configuration.genome_size,
        configuration.tree_count, configuration.leaf_count, configuration.alpha)
    current_scale = configuration.scale.begin
    while current_scale <= configuration.scale.end:
        logging.info(
            "Starting iterations for scale: %s ", current_scale)
        run_scenarios(
            leaf_count=configuration.leaf_count, scale=current_scale, base_path=configuration.data_path,
            alpha=configuration.alpha, tree_count=configuration.tree_count, genome_size=configuration.genome_size)
        current_scale = round(current_scale + configuration.scale.step, ndigits=2)


if __name__ == '__main__':
    fire.Fire(main)
