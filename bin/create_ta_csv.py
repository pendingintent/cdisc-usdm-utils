import csv
import json
import datetime
import os
from cdisc_usdm_utils.validation import get_dataset_schema_path
import re
import sys
import warnings

# Define the output columns
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

# Map columns to USDM Path and Attribute from the spec
USDM_PATHS = {
    "STUDYID": "study.studyVersion.studyIdentifier.studyIdentifier",
    "DOMAIN": None,  # Set to 'TA'
    "ARMCD": "study.studyVersion.studyDesigns.studyDesign.arms.StudyArm.name",
    "ARM": "study.studyVersion.studyDesigns.studyDesign.arms.StudyArm.description",
    "TAETORD": None,  # Derived, see spec
    "ETCD": "study.studyVersion.studyDesigns.studyDesign.studyCells.StudyCell.elements.StudyElement.name",
    "ELEMENT": "study.studyVersion.studyDesigns.studyDesign.studyCells.StudyCell.elements.StudyElement.description",
    "TABRANCH": "study.studyVersion.studyDesigns.studyDesign.scheduleTimelines.ScheduleTimeline.instances.ScheduledDecisionInstance.conditionAssignments",
    "TATRANS": "study.studyVersion.studyDesigns.studyDesign.scheduleTimelines.ScheduleTimeline.instances.ScheduledDecisionInstance.conditionAssignments",
    "EPOCH": "study.studyVersion.studyDesigns.studyDesign.studyCells.StudyCell.epoch.StudyEpoch.name",
}


# Helper to safely get nested values from dicts/lists
def get_nested(data, path):
    keys = path.split(".")
    for key in keys:
        if isinstance(data, list):
            try:
                data = data[0]
            except IndexError:
                return ""
        if isinstance(data, dict):
            data = data.get(key, "")
        else:
            return ""
    return data if not isinstance(data, (dict, list)) else ""


def _emit_deprecation_warning():
    msg = (
        "DEPRECATED: bin/create_ta_csv.py will be removed in a future release.\n"
        "Use the unified CLI instead:\n"
        "  python -m cdisc_usdm_utils.cli sdtm one --domain TA --usdm-file <USDM_JSON> --out-dir <OUT_DIR>\n"
    )
    try:
        warnings.simplefilter("default", DeprecationWarning)
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
    except Exception:
        pass
    try:
        print(msg, file=sys.stderr)
    except Exception:
        pass


# Main function
def main(usdm_file, output_file):
    _emit_deprecation_warning()

    with open(usdm_file) as f:
        usdm = json.load(f)

    study_version = usdm["study"]["versions"][0]
    study_id = ""
    if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
        study_id = study_version["studyIdentifiers"][0].get("text", "")

    # Get studyDesign and referenced lists
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

    # Write CSV
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # --- Generate Dataset-JSON ---

    # Load schema for columns
    schema_path = get_dataset_schema_path()
    with open(schema_path) as f:
        schema = json.load(f)
    # Find TA columns in schema
    # If schema has a columns array, use it; else, fallback to COLUMNS
    schema_columns = []
    if "columns" in schema:
        for col in schema["columns"]:
            if col.get("name") in COLUMNS:
                schema_columns.append(col)
    elif "$defs" in schema and "Column" in schema["$defs"]:
        # Fallback: build from COLUMNS
        for colname in COLUMNS:
            schema_columns.append(
                {
                    "name": colname,
                    "label": colname,
                    "dataType": "string",
                    "itemOID": f"IT.TA.{colname}",
                }
            )

    # Build Dataset-JSON structure
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
    # Add row data as arrays in column order
    for row in rows:
        dataset_json["rows"].append([row[col] for col in COLUMNS])

    # Write Dataset-JSON file
    json_path = re.sub(r"\.csv$", ".dataset.json", output_file, flags=re.IGNORECASE)
    with open(json_path, "w") as jf:
        json.dump(dataset_json, jf, indent=2)
    print(f"TA.CSV and TA.dataset.json generated.")


if __name__ == "__main__":
    _emit_deprecation_warning()
    main("files/pilot_LLZT_protocol.json", "output/TA.CSV")
