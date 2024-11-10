import csv

from candidate_surveys.conf_tools import load_conf
from candidate_surveys.pdf_tools import dump_questionnare_to_pdf


def generate_pdfs(
    csv_filename: str, config_filename: str, logo_directory: str, output_directory: str
) -> None:
    with open(csv_filename) as csvfile:
        # Assumptions about the file:
        #  * Tab delimited
        #  * Proper '\n' delimiters for end-of-line
        #  * The first line in the file contains column key names. These must match
        #    the ALL_CAPS globals at the top of this file.
        reader = csv.DictReader(csvfile, delimiter=",")
        conf = load_conf(config_filename, list(reader.fieldnames or []))

        conf["logo_directory"] = logo_directory.rstrip("/").strip()
        conf["output_directory"] = output_directory.rstrip("/").strip()

        for row in reader:
            dump_questionnare_to_pdf(row, conf)
