import csv
import json
import datetime
import os
import re
from pathlib import Path
from cdisc_usdm_utils.validation import (
    validate_dataset_json,
    write_validation_report,
    validate_against_jsonschema,
)

COLUMNS = [
    "STUDYID",
    "DOMAIN",
    "ARMCD",
    "ARM",
    "TAETORD",
    "ETCD",
    "ELEMENT",
    "TABRANCH",
    "TATRANS",
    "EPOCH",
]


def generate(usdm_file: str, output_file: str):
    with open(usdm_file) as f:
        usdm = json.load(f)

    study_version = usdm["study"]["versions"][0]
    study_id = ""
    if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
        study_id = study_version["studyIdentifiers"][0].get("text", "")

    study_design = (
        study_version["studyDesigns"][0] if study_version.get("studyDesigns") else {}
    )
    arms = {arm["id"]: arm for arm in study_design.get("arms", [])}
    epochs = {epoch["id"]: epoch for epoch in study_design.get("epochs", [])}
    elements = {el["id"]: el for el in study_design.get("elements", [])}
    study_cells = study_design.get("studyCells", [])

    rows = []
    for cell in study_cells:
        arm_id = cell.get("armId")
        epoch_id = cell.get("epochId")
        element_ids = cell.get("elementIds", [])

        arm = arms.get(arm_id, {})
        epoch = epochs.get(epoch_id, {})

        for taetord, element_id in enumerate(element_ids, 1):
            element = elements.get(element_id, {})
            row = {
                "STUDYID": study_id,
                "DOMAIN": "TA",
                "ARMCD": arm.get("name", ""),
                "ARM": arm.get("description", ""),
                "TAETORD": taetord,
                "ETCD": element.get("name", ""),
                "ELEMENT": element.get("description", ""),
                "TABRANCH": "",
                "TATRANS": "",
                "EPOCH": epoch.get("name", ""),
            }
            rows.append(row)

    Path(os.path.dirname(output_file) or ".").mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    schema_path = os.path.join("files", "dataset.schema.json")
    with open(schema_path) as f:
        schema = json.load(f)

    schema_columns = []
    if "columns" in schema:
        for col in schema["columns"]:
            if col.get("name") in COLUMNS:
                schema_columns.append(col)
    elif "$defs" in schema and "Column" in schema["$defs"]:
        for colname in COLUMNS:
            schema_columns.append(
                {
                    "name": colname,
                    "label": colname,
                    "dataType": "string",
                    "itemOID": f"IT.TA.{colname}",
                }
            )

    dataset_json = {
        "datasetJSONCreationDateTime": datetime.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "datasetJSONVersion": "1.1",
        "itemGroupOID": "IG.TA",
        "records": len(rows),
        "name": "TA",
        "label": "Trial Arms",
        "columns": schema_columns,
        "rows": [],
        "originator": "cdisc-usdm-utils",
        "studyOID": study_id,
        "sourceSystem": {"name": "cdisc-usdm-utils", "version": "1.0"},
    }
    for row in rows:
        dataset_json["rows"].append([row[col] for col in COLUMNS])

    json_path = re.sub(r"\.csv$", ".dataset.json", output_file, flags=re.IGNORECASE)
    with open(json_path, "w") as jf:
        json.dump(dataset_json, jf, indent=2)

    ok, problems = validate_dataset_json(dataset_json, "TA", COLUMNS)
    if not ok:
        report = write_validation_report(json_path, problems)
        print(f"[TA] Dataset-JSON validation found issues. See {report}")
    # JSON Schema validation (optional, requires jsonschema)
    schema_ok, schema_problems = validate_against_jsonschema(
        dataset_json, os.path.join("files", "dataset.schema.json")
    )
    if not schema_ok and schema_problems:
        report = write_validation_report(json_path + ".schema", schema_problems)
        print(f"[TA] JSON Schema validation issues. See {report}")

    return output_file, json_path
