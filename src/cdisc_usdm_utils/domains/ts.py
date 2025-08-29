import csv
import json
import pandas as pd
import datetime
import os
import re
from cdisc_usdm_utils.validation import (
    validate_dataset_json,
    write_validation_report,
    validate_against_jsonschema,
)
from pathlib import Path

TS_COLUMNS = [
    "STUDYID",
    "DOMAIN",
    "TSSEQ",
    "TSGRPID",
    "TSPARMCD",
    "TSPARM",
    "TSVAL",
    "TSVALNF",
    "TSVALCD",
    "TSVCDREF",
    "TSVCDVER",
]


def _load_tsparm_spec(tsparm_spec_file: str):
    tsparm_map = []
    with open(tsparm_spec_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tsparm_map.append(row)
    return tsparm_map


def generate(
    usdm_file: str,
    output_file: str,
    ts_spec_file: str | None = None,
    tsparm_spec_file: str | None = None,
):
    # TS spec currently unused; TSPARM spec required for mapping
    if tsparm_spec_file is None:
        tsparm_spec_file = str(Path("spec/TSPARM_spec.csv").resolve())

    # Optional terminology
    try:
        terminology = pd.read_excel(
            "files/SDTM Terminology.xls", header=None, usecols=[0, 1], dtype=str
        )
        terminology.columns = ["code", "codelist_code"]
    except Exception:
        terminology = pd.DataFrame(columns=["code", "codelist_code"])  # not used yet

    with open(usdm_file) as f:
        usdm = json.load(f)

    study_version = usdm["study"]["versions"][0]
    study_id = ""
    if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
        study_id = study_version["studyIdentifiers"][0].get("text", "")

    tsparm_map = _load_tsparm_spec(tsparm_spec_file)

    rows = []
    seq = 1
    study_design = (
        study_version["studyDesigns"][0] if study_version.get("studyDesigns") else {}
    )

    def has_characteristic(decode):
        for c in study_design.get("characteristics", []):
            if (
                c.get("decode", "").upper() == decode.upper()
                or c.get("code", "") == decode
            ):
                return True
        return False

    def get_min_max_age(which):
        vals = []
        for pop in study_design.get("population", {}).get("cohorts", []):
            age = pop.get("plannedAge", {}).get("range", {})
            v = age.get("minValue" if which == "min" else "maxValue")
            unit = age.get("unit", "")
            if v is not None:
                vals.append((v, unit))
        pop = study_design.get("population", {})
        age = pop.get("plannedAge", {}).get("range", {})
        v = age.get("minValue" if which == "min" else "maxValue")
        unit = age.get("unit", "")
        if v is not None:
            vals.append((v, unit))
        if not vals:
            return None, None
        if which == "min":
            return min(vals, key=lambda x: x[0])
        return max(vals, key=lambda x: x[0])

    def yn_code(val):
        if val is True:
            return "Y", "C49488"
        if val is False:
            return "N", "C49487"
        return "", ""

    for parm in tsparm_map:
        row = {col: "" for col in TS_COLUMNS}
        row["STUDYID"] = study_id
        row["DOMAIN"] = "TS"
        row["TSSEQ"] = seq
        row["TSPARMCD"] = parm["TSPARMCD"]
        row["TSPARM"] = parm["TSPARM"]
        tsp = parm["TSPARMCD"]

        if tsp == "ADAPT":
            val = has_characteristic("Adaptive Design")
            row["TSVAL"], row["TSVALCD"] = yn_code(val)
        elif tsp == "EXTTIND":
            val = has_characteristic("Extension Study Design")
            row["TSVAL"], row["TSVALCD"] = yn_code(val)
        elif tsp == "RANDOM":
            val = has_characteristic("Randomized")
            row["TSVAL"], row["TSVALCD"] = yn_code(val)
        elif tsp == "HLTSUBJI":
            pop = study_design.get("population", {})
            val = pop.get("includesHealthySubjects")
            row["TSVAL"], row["TSVALCD"] = yn_code(val)
        elif tsp == "RDIND":
            inds = study_design.get("indications", [])
            val = None
            for ind in inds:
                if "isRareDisease" in ind:
                    val = ind["isRareDisease"]
                    break
            row["TSVAL"], row["TSVALCD"] = yn_code(val)
        elif tsp == "AGEMIN":
            v, unit = get_min_max_age("min")
            if v is not None:
                row["TSVAL"] = (
                    f"P{int(v)}Y"
                    if unit and unit.lower() in ["year", "years", "yr", "y"]
                    else str(v)
                )
            else:
                row["TSVAL"] = ""
                row["TSVALNF"] = "UNK"
        elif tsp == "AGEMAX":
            v, unit = get_min_max_age("max")
            if v is not None:
                row["TSVAL"] = (
                    f"P{int(v)}Y"
                    if unit and unit.lower() in ["year", "years", "yr", "y"]
                    else str(v)
                )
            else:
                row["TSVAL"] = ""
                row["TSVALNF"] = "UNK"

        rows.append(row)
        seq += 1

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TS_COLUMNS)
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
            if col.get("name") in TS_COLUMNS:
                schema_columns.append(col)
    elif "$defs" in schema and "Column" in schema["$defs"]:
        for colname in TS_COLUMNS:
            schema_columns.append(
                {
                    "name": colname,
                    "label": colname,
                    "dataType": "string",
                    "itemOID": f"IT.TS.{colname}",
                }
            )
    dataset_json = {
        "datasetJSONCreationDateTime": datetime.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "datasetJSONVersion": "1.1",
        "itemGroupOID": "IG.TS",
        "records": len(rows),
        "name": "TS",
        "label": "Trial Summary",
        "columns": schema_columns,
        "rows": [],
        "originator": "cdisc-usdm-utils",
        "studyOID": study_id,
        "sourceSystem": {"name": "cdisc-usdm-utils", "version": "1.0"},
    }
    for row in rows:
        dataset_json["rows"].append([row[col] for col in TS_COLUMNS])
    json_path = re.sub(r"\.csv$", ".dataset.json", output_file, flags=re.IGNORECASE)
    with open(json_path, "w") as jf:
        json.dump(dataset_json, jf, indent=2)
    ok, problems = validate_dataset_json(dataset_json, "TS", TS_COLUMNS)
    if not ok:
        report = write_validation_report(json_path, problems)
        print(f"[TS] Dataset-JSON validation found issues. See {report}")
    schema_ok, schema_problems = validate_against_jsonschema(
        dataset_json, os.path.join("files", "dataset.schema.json")
    )
    if not schema_ok and schema_problems:
        report = write_validation_report(json_path + ".schema", schema_problems)
        print(f"[TS] JSON Schema validation issues. See {report}")

    return output_file, json_path
