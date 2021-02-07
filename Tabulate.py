from pathlib import Path
import logging
import fire

from src.tabulate.configuration import parse_configuration
from src.tabulate.csv import write_csvs
from src.tabulate.process import process_file
from src.time_func import time_func

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def main(config: str):
    config_path = Path(config).expanduser()
    configuration = parse_configuration(config_path)
    configuration.validate()
    configuration.output_folder.mkdir(exist_ok=True)
    data_files = list(configuration.data_folder.glob(configuration.file_pattern))
    logging.info("Going over %s data files!", len(data_files))
    tabulated = {}
    for data_file in data_files:
        process_file(data_file, tabulated)
    with time_func("Writing CSVs"):
        write_csvs(configuration, tabulated)
    logging.info("DONE :)")


if __name__ == '__main__':
    fire.Fire(main)
