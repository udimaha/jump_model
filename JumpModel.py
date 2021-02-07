#!/usr/bin/env python
# coding: utf-8
import logging
import gzip
from concurrent import futures
from pathlib import Path
import uuid

import fire

from src.scenario import run_scenario
from src.simulator.configuration import MAX_PROCESSES, parse_configuration, Configuration
from src.time_func import time_func


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def run_single_job(
        pattern: str, leaf_count: int, scale: float, base_path: Path, alpha: float, genome_size: int, idx: int,
        ultrametric: bool):
    assert pattern
    with time_func(f"Running tree: {idx} of scenario with {leaf_count} leaves, alpha: {alpha} and scale: {scale}"):
        result = run_scenario(leaf_count, scale, genome_size=genome_size, alpha=alpha, ultrametric=ultrametric)
    outdir = base_path / str(scale)
    outdir.mkdir(exist_ok=True)
    output = outdir / f"{uuid.uuid4()}_{pattern}"
    with gzip.open(str(output.with_suffix(".json.gz")), "w") as f_gz:
        f_gz.write(result.to_json().encode())


def run_scenarios(configuration: Configuration, scale: float):
    assert 0 < configuration.processes <= MAX_PROCESSES
    pattern = configuration.file_pattern(scale)
    with futures.ThreadPoolExecutor(max_workers=configuration.processes) as executor:
        jobs = [
            executor.submit(
                run_single_job, pattern, configuration.leaf_count, scale, configuration.data_path, configuration.alpha,
                configuration.genome_size, idx, configuration.ultrametric)
            for idx in range(configuration.tree_count)]
        for job in futures.as_completed(jobs):
            try:
                job.result()
            except Exception as e:
                logging.exception("Failed running job!!!")


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
