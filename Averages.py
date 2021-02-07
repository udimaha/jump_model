from concurrent import futures
from pathlib import Path
import logging
import fire

from src.averages.configuration import parse_configuration
from src.averages.process import process_file

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')


def main(config: str):
	config_path = Path(config).expanduser()
	configuration = parse_configuration(config_path)
	configuration.validate()
	configuration.output_folder.mkdir(exist_ok=True)
	data_files = list(
		filter(
			lambda x: not (configuration.output_folder / x.name).exists(),
			configuration.data_folder.glob(configuration.file_pattern)))
	logging.info("Going over %s data files!", len(data_files))
	with futures.ThreadPoolExecutor(max_workers=configuration.processes) as executor:
		jobs = []
		for data_file in data_files:
			try:
				output = configuration.output_folder / data_file.name
				assert not output.exists()
				jobs.append(executor.submit(process_file, output, data_file))
			except Exception:
				logging.exception("oops")
		assert jobs, "No jobs to run!"
		for job in futures.as_completed(jobs):
			try:
				job.result()
			except Exception as e:
				logging.exception("Failed running job!!!")
	logging.info("DONE :)")


if __name__ == '__main__':
	fire.Fire(main)
