import csv
import json
import os
import datetime
from cdisc_usdm_utils.validation import (
    validate_dataset_json,
    write_validation_report,
    validate_against_jsonschema,
)

COLUMNS = [
    "STUDYID",
    "DOMAIN",
    "IETESTCD",
    "IETEST",
    "IECAT",
    "IESCAT",
    "TIRL",
    "TIVERS",
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
    population = study_design.get("population", {})
    criterion_ids = population.get("criterionIds", [])
    eligibility_criteria = {
        ec["id"]: ec for ec in study_design.get("eligibilityCriteria", [])
    }

    tivers = "1"  # Static per current bin script

    rows = []
    for cid in criterion_ids:
        crit = eligibility_criteria.get(cid, {})
        decode = (
            crit.get("category", {}).get("decode", "") if crit.get("category") else ""
        )
        if decode.lower().startswith("inclusion"):
            iecat = "INCLUSION"
        elif decode.lower().startswith("exclusion"):
            iecat = "EXCLUSION"
        else:
            iecat = ""
        ietest = crit.get("label", "")
        ietestcd = crit.get("identifier", "")
        if not ietestcd.startswith("IE"):
            ietestcd = f"IE{ietestcd}"
        if ietest.startswith("IE"):
            ietest = ietest[2:]
        row = {
            "STUDYID": study_id,
            "DOMAIN": "TI",
            "IETESTCD": ietestcd,
            "IETEST": ietest,
            "IECAT": iecat,
            "IESCAT": "",
            "TIRL": crit.get("label", ""),
            "TIVERS": tivers,
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
                    "itemOID": f"IT.TI.{colname}",
                }
            )
    dataset_json = {
        "datasetJSONCreationDateTime": datetime.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "datasetJSONVersion": "1.1",
        "itemGroupOID": "IG.TI",
        "records": len(rows),
        "name": "TI",
        "label": "Trial Inclusion/Exclusion Criteria",
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
    ok, problems = validate_dataset_json(dataset_json, "TI", COLUMNS)
    if not ok:
        report = write_validation_report(json_path, problems)
        print(f"[TI] Dataset-JSON validation found issues. See {report}")
    schema_ok, schema_problems = validate_against_jsonschema(
        dataset_json, os.path.join("files", "dataset.schema.json")
    )
    if not schema_ok and schema_problems:
        report = write_validation_report(json_path + ".schema", schema_problems)
        print(f"[TI] JSON Schema validation issues. See {report}")

    return output_file, json_path
