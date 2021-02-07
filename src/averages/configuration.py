import json
from pathlib import Path
from typing import NamedTuple

MAX_PROCESSES = 20


class Configuration(NamedTuple):
	data_folder: Path
	output_folder: Path
	file_pattern: str
	processes: int

	def validate(self):
		assert self.data_folder.is_dir()
		assert next(self.data_folder.iterdir(), None) is not None
		assert 0 < self.processes <= MAX_PROCESSES


def parse_configuration(config_path: Path) -> Configuration:
	assert config_path.is_file(), f"Configuration file not found at: [{config_path}]"
	with config_path.open("r") as f:
		configuration = json.load(f)

	def get_conf_val(key: str, default=None):
		if key not in configuration:
			if default:
				return default
			raise KeyError(f"Invalid configuration! Missing key: [{key}]")
		return configuration[key]

	data_path = get_conf_val("data")
	output_path = get_conf_val("output")
	processes = int(get_conf_val("processes"))
	file_pattern = get_conf_val("file_pattern", "*.gz")
	return Configuration(
		data_folder=Path(data_path).expanduser(), output_folder=Path(output_path).expanduser(),
		file_pattern=file_pattern, processes=processes)
