#!/usr/bin/env python
# coding: utf-8
import logging
import gzip
import json
from pathlib import Path
from typing import NamedTuple

import fire

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


def main(config: str):
    config_path = Path(config).expanduser()
    configuration = parse_configuration(config_path)
    configuration.validate()
    logging.info("Getting information from real data!")
    occurr = read_real_data(configuration.data_path)
    with gzip.open(str(configuration.output_path), "w") as f_gz:
        f_gz.write(json.dumps(occurr).encode())


if __name__ == '__main__':
    fire.Fire(main)
