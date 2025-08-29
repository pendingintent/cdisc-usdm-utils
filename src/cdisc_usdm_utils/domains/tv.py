import csv
import json
import os
import re
import datetime
from cdisc_usdm_utils.validation import (
    validate_dataset_json,
    write_validation_report,
    validate_against_jsonschema,
)

COLUMNS = [
    "STUDYID",
    "DOMAIN",
    "VISITNUM",
    "VISIT",
    "VISITDY",
    "ARMCD",
    "ARM",
    "TVSTRL",
    "TVENRL",
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
    encounters = study_design.get("encounters", [])
    encounter_map = {e["id"]: e for e in encounters}

    # Determine visit order via previousId chaining
    visit_order = []
    id_to_prev = {e["id"]: e.get("previousId") for e in encounters}
    first = next((eid for eid, prev in id_to_prev.items() if not prev), None)
    if first:
        curr = first
        while curr:
            visit_order.append(curr)
            curr = next(
                (e["id"] for e in encounters if e.get("previousId") == curr), None
            )
    else:
        visit_order = [e["id"] for e in encounters]

    rows = []
    for arm in arms.values():
        armcd = arm.get("name", "") or ""
        armname = arm.get("description", "") or ""
        for idx, eid in enumerate(visit_order, 1):
            enc = encounter_map[eid]
            tvstrl = (enc.get("transitionStartRule") or {}).get("text", "") or ""
            tvenrl = (enc.get("transitionEndRule") or {}).get("text", "") or ""
            tvstrl = (
                re.sub(r"[\u00A0\u200B\u202F\uFEFF]", " ", tvstrl)
                .replace('"', "")
                .strip()
                or ""
            )
            tvenrl = (
                re.sub(r"[\u00A0\u200B\u202F\uFEFF]", " ", tvenrl)
                .replace('"', "")
                .strip()
                or ""
            )
            desc = enc.get("description", "")
            visitdy = ""
            if idx == 1:
                visitdy = "0"
            elif desc:
                m = re.search(r"Day (\d+)", desc)
                if m:
                    visitdy = m.group(1)
            row = {
                "STUDYID": study_id or "",
                "DOMAIN": "TV",
                "VISITNUM": idx,
                "VISIT": enc.get("name", "") or "",
                "VISITDY": visitdy,
                "ARMCD": armcd,
                "ARM": armname,
                "TVSTRL": tvstrl,
                "TVENRL": tvenrl,
            }
            rows.append(row)

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Dataset-JSON
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
                    "itemOID": f"IT.TV.{colname}",
                }
            )
    dataset_json = {
        "datasetJSONCreationDateTime": datetime.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "datasetJSONVersion": "1.1",
        "itemGroupOID": "IG.TV",
        "records": len(rows),
        "name": "TV",
        "label": "Trial Visits",
        "columns": schema_columns,
        "rows": [],
        "originator": "cdisc-usdm-utils",
        "studyOID": study_id,
        "sourceSystem": {"name": "cdisc-usdm-utils", "version": "1.0"},
    }
    for row in rows:
        dataset_json["rows"].append([row[col] for col in COLUMNS])
    json_path = os.path.splitext(output_file)[0] + ".dataset.json"
    with open(json_path, "w") as jf:
        json.dump(dataset_json, jf, indent=2)
    ok, problems = validate_dataset_json(dataset_json, "TV", COLUMNS)
    if not ok:
        report = write_validation_report(json_path, problems)
        print(f"[TV] Dataset-JSON validation found issues. See {report}")
    schema_ok, schema_problems = validate_against_jsonschema(
        dataset_json, os.path.join("files", "dataset.schema.json")
    )
    if not schema_ok and schema_problems:
        report = write_validation_report(json_path + ".schema", schema_problems)
        print(f"[TV] JSON Schema validation issues. See {report}")

    return output_file, json_path
