import json
from pathlib import Path
from typing import NamedTuple

MAX_PROCESSES = 20


class Scale(NamedTuple):
    begin: float
    end: float
    step: float

    def validate(self):
        assert self.begin < self.end <= 1
        assert self.step < 1 and round(self.begin + self.step, ndigits=2) <= self.end


class Configuration(NamedTuple):
    data_path: Path
    tree_count: int
    alpha: float
    genome_size: int
    leaf_count: int
    processes: int
    ultrametric: bool
    scale: Scale

    def validate(self):
        assert self.tree_count > 0
        assert 0 < self.alpha <= 1
        assert self.genome_size > 0
        assert self.data_path.is_dir()
        assert 0 < self.processes <= MAX_PROCESSES
        self.scale.validate()

    def file_pattern(self, scale: float) -> str:
        return f"scale_{scale}_leaves_{self.leaf_count}_genome_{self.genome_size}_alpha_{self.alpha}.json"


def parse_configuration(config_path: Path) -> Configuration:
    assert config_path.is_file(), f"Configuration file not found at: [{config_path}]"
    with config_path.open("r") as f:
        configuration = json.load(f)

    def get_conf_val(key: str):
        if key not in configuration:
            raise KeyError(f"Invalid configuration! Missing key: [{key}]")
        return configuration[key]

    tree_count = int(get_conf_val("tree_count"))
    data_path = get_conf_val("data_path")
    alpha = float(get_conf_val("alpha"))
    genome_size = int(get_conf_val("genome_size"))
    leaf_count = int(get_conf_val("leaf_count"))
    processes = int(get_conf_val("processes"))
    ultrametric = bool(get_conf_val("ultrametric"))
    scale = Scale(*map(lambda x: round(x, 2), get_conf_val("scale")))
    return Configuration(
        data_path=Path(data_path).expanduser(), tree_count=tree_count, alpha=alpha,
        genome_size=genome_size, leaf_count=leaf_count, processes=processes, scale=scale,
        ultrametric=ultrametric
    )
