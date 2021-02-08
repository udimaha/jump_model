from pathlib import Path
import logging
import fire
import re

from src.likelihood.parse import parse_csv_dict, gather_csvs
from src.likelihood.calculate import likelihood

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


def main(
		simulated_dir: str, simulated_glob: str, realdata_dir: str, realdata_glob: str,
		simulated_regex: str = r"\d+", realdata_regex: str = r"\d+"):
	simulated_dir = Path(simulated_dir).expanduser()
	realdata_dir = Path(realdata_dir).expanduser()
	realdata_regex = re.compile(realdata_regex)
	simulated_regex = re.compile(simulated_regex)
	realdata_csvs = gather_csvs(realdata_dir, realdata_glob, realdata_regex)
	simulated_csvs = gather_csvs(simulated_dir, simulated_glob, simulated_regex)
	for missing_key in realdata_csvs.keys() - simulated_csvs.keys():
		realdata_csvs.pop(missing_key, None)
	for missing_key in simulated_csvs.keys() - realdata_csvs.keys():
		simulated_csvs.pop(missing_key, None)
	realdata_csvs = parse_csv_dict(realdata_csvs)
	simulated_csvs = parse_csv_dict(simulated_csvs)
	assert realdata_csvs.keys() == simulated_csvs.keys()
	probability = sum(likelihood(simulated_csvs[word_size], realdata_csvs[word_size]) for word_size in simulated_csvs)
	print(f"Probability score is: {probability}")
	return probability


if __name__ == '__main__':
	fire.Fire(main)
