import json
from pathlib import Path

def __init__():
    institution_template = {
    "name": "name",
    "specialty": "specialty",
    "address": "address",
    "type": "institution"
    }

    provider_template = {
    "name": "name",
    "specialty": "specialty",
    "employer": "employer",
    "type": "provider"
    }

    with open("provider_data.json", "w") as provider_file:
        json.dump(provider_template, provider_file, indent=2)
    with open("institution_data.json", "w") as institution_file:
        json.dump(institution_template, institution_file, indent=2)

def write_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")

