import csv
import logging
from pathlib import Path
from typing import Dict


def read_csv(csv_: Path) -> Dict[int, int]:
	result = {}
	with csv_.open("r") as csv_f:
		reader = csv.DictReader(csv_f)
		for row in reader:
			result[int(row["occur"])] = int(row["density"])
	return result


def parse_csv_dict(csv_dict: Dict[int, Path]) -> Dict[int, Dict[int, int]]:
	return {
		word_size: read_csv(csv_) for word_size, csv_ in csv_dict.items()
	}


def gather_csvs(directory: Path, glob_pattern: str, size_regex) -> Dict[int, Path]:
	csvs = {}
	for file_ in directory.glob(glob_pattern):
		word_sizes = size_regex.findall(file_.name)
		if len(word_sizes) != 1:
			logging.warning("Skipping file %s as it did not contain integer to infer word size!", file_)
			continue
		word_size = int(word_sizes[0])
		if word_size in csvs:
			logging.warning("Encoutered duplicate file for word size %s! [%s]", word_size, file_)
		csvs[word_size] = file_
	return csvs
