import csv
import pathlib

from candidate_surveys.conf_tools import load_conf
from candidate_surveys.pdf_tools import dump_questionnare_to_pdf


def generate_pdfs(
    responses_path: pathlib.Path,
    config_path: pathlib.Path,
    logos_dir: pathlib.Path,
    output_dir: pathlib.Path,
) -> None:
    with responses_path.open() as responses_file:
        # Assumptions about the file:
        #  * Tab delimited
        #  * Proper '\n' delimiters for end-of-line
        #  * The first line in the file contains column key names. These must match
        #    the ALL_CAPS globals at the top of this file.
        responses_reader = csv.DictReader(responses_file, delimiter=",")
        fieldnames = list(responses_reader.fieldnames or [])
        conf = load_conf(config_path, fieldnames)

        conf["logo_directory"] = str(logos_dir)
        conf["output_directory"] = str(output_dir)

        for row in responses_reader:
            dump_questionnare_to_pdf(row, conf)
