import gzip
import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict

Tabulated = Dict[int, Dict[int, int]]


def process_file(to_process: Path, tabulated: Tabulated):
    start = time.monotonic()
    with gzip.open(str(to_process), "r") as f:
        data = json.loads(f.read().decode())
    data['occurrences'] = json.loads(data['occurrences'])
    for k, occur in data['occurrences'].items():
        k = int(k)
        if k not in tabulated:
            tabulated[k] = defaultdict(int)
        for occ in occur:
            tabulated[k][occ] += 1
    logging.info(
        "Finished processing single file, took: %s seconds with dict size of %s",
        time.monotonic() - start, len(data['occurrences']))
