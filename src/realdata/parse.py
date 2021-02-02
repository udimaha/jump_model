import csv
import gzip
import json
import logging
import statistics
from pathlib import Path
from typing import NamedTuple, Tuple

from src.occurrences import Occurrences
from src.suffix_trees.STree import STree
from src.time_func import time_func


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


def _read_real_data(
        data_dir: Path, name_key: str = "Cog",
        field_names: Tuple[str] = ("Taxid", "Gene name", "Contig", "Srnd", "Start", "Stop", "Length", "Cog")
) -> Occurrences:
    names = {}
    genomes = []
    sizes = []
    for file_ in data_dir.iterdir():
        genome = []
        with file_.open("r") as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=field_names)
            next(reader)  # Skip header
            for line in reader:
                name = line[name_key]
                if name not in names:
                    names[name] = len(names)
                gene_id = names[name]
                genome += [gene_id]
        if genome is not None:
            logging.info("Done parsing genome: %s genome size is: %d", file_, len(genome))
            sizes.append(len(genome))
            genomes.append(genome)
    with time_func(f"Constructing the suffix tree for {len(genomes)} genomes!"):
        suffix_tree = STree(genomes)
    with time_func(f"Counting occurrences for {len(genomes)} genomes!"):
        logging.info(
            "Smallest geome is: %d longest geome is: %d average genome is: %d median genome is: %d",
            min(sizes), max(sizes), statistics.mean(sizes), statistics.median(sizes))
        return suffix_tree.occurrences()


def parse_realdata(config_path: Path):
    configuration = parse_configuration(config_path)
    configuration.validate()
    logging.info("Getting information from real data!")
    occurr = _read_real_data(configuration.data_path)
    with gzip.open(str(configuration.output_path), "w") as f_gz:
        f_gz.write(json.dumps(occurr).encode())
