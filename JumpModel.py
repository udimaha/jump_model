#!/usr/bin/env python
# coding: utf-8
import logging
from pathlib import Path

import fire

from src.simulator.scenario import run_scenarios
from src.simulator.configuration import parse_configuration

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


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
        run_scenarios(configuration, scale=current_scale)
        current_scale = round(current_scale + configuration.scale.step, ndigits=2)


if __name__ == '__main__':
    fire.Fire(main)
