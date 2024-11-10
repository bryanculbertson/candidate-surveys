import json
import pathlib
from collections.abc import Sequence


def load_conf(config_path: pathlib.Path, fields: Sequence[str]) -> dict:
    conf = None
    with config_path.open() as config_file:
        conf = json.loads(config_file.read())

    for i, x in enumerate(conf["file_structure"]):
        if isinstance(x, int):
            print("Replacing %s with %s in file_structure." % (x, fields[x]))
            conf["file_structure"][i] = fields[x]

    for i, x in enumerate(conf["candidate_details"]):
        if isinstance(x, int):
            print("Replacing %s with %s in candidate_details." % (x, fields[x]))
            conf["candidate_details"][i] = fields[x]

    overrides = {}
    for k, v in conf["question_overrides"].items():
        if k.isnumeric():
            k = int(k)
            print("Replacing '%s' with '%s' in question_overrides." % (fields[k], v))
            overrides[fields[k]] = v
        else:
            overrides[k] = v
    conf["question_overrides"] = overrides

    return conf
