import csv
import logging
from concurrent import futures
from pathlib import Path
from typing import Dict

from src.tabulate.process import Tabulated
from src.tabulate.configuration import Configuration


def _write_csv(csv_out: Path, occurrences: Dict[int, int]):
    if not occurrences:
        csv_out.unlink()
        return
    total = sum(occurrences.values())
    assert total > 0, f"Total is {total} for {csv_out}, expected positive!"
    fieldnames = ["occur", "density", "relative"]
    with csv_out.open("w") as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
        writer.writeheader()
        for occur, density in occurrences.items():
            writer.writerow(
                {"occur": occur, "density": density, "relative": density / total})


def write_csvs(configuration: Configuration, tabulated: Tabulated):
    def _csv_out(size_: int) -> Path:
        return configuration.output_folder / f"words-{size_}-genes.csv"

    with futures.ThreadPoolExecutor(max_workers=configuration.processes) as executor:
        jobs = [
            executor.submit(
                _write_csv, _csv_out(size_), occurrences)
            for size_, occurrences in tabulated.items()]
        for job in futures.as_completed(jobs):
            try:
                job.result()
            except Exception as e:
                logging.exception("Failed running job!!!")