import csv
import json

COLUMNS = ["STUDYID", "DOMAIN", "ETCD", "ELEMENT", "TESTRL", "TEENRL", "TEDUR"]


def main(usdm_file, output_file):
    with open(usdm_file) as f:
        usdm = json.load(f)

    study_version = usdm["study"]["versions"][0]
    study_id = ""
    if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
        study_id = study_version["studyIdentifiers"][0].get("text", "")

    study_design = (
        study_version["studyDesigns"][0] if study_version.get("studyDesigns") else {}
    )
    elements = study_design.get("elements", [])

    rows = []
    import re

    for element in elements:
        testrl = (element.get("transitionStartRule") or {}).get("text", "")
        teenrl = (element.get("transitionEndRule") or {}).get("text", "")
        # Remove non-breaking spaces and other special whitespace
        testrl = re.sub(r"[\u00A0\u200B\u202F\uFEFF]", " ", testrl)
        teenrl = re.sub(r"[\u00A0\u200B\u202F\uFEFF]", " ", teenrl)
        # Remove all double quotes and strip whitespace
        testrl = testrl.replace('"', "").strip()
        teenrl = teenrl.replace('"', "").strip()
        row = {
            "STUDYID": study_id,
            "DOMAIN": "TE",
            "ETCD": element.get("name", ""),
            "ELEMENT": element.get("description", ""),
            "TESTRL": testrl,
            "TEENRL": teenrl,
            "TEDUR": "",  # Not implemented: requires scheduleTimelines traversal
        }
        rows.append(row)

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # --- Generate Dataset-JSON ---
    import datetime
    import os
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
            schema_columns.append({
                "name": colname,
                "label": colname,
                "dataType": "string",
                "itemOID": f"IT.TE.{colname}"
            })
    dataset_json = {
        "datasetJSONCreationDateTime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "datasetJSONVersion": "1.1",
        "itemGroupOID": "IG.TE",
        "records": len(rows),
        "name": "TE",
        "label": "Trial Elements",
        "columns": schema_columns,
        "rows": [],
        "originator": "cdisc-usdm-utils",
        "studyOID": study_id,
        "sourceSystem": {"name": "cdisc-usdm-utils", "version": "1.0"}
    }
    for row in rows:
        dataset_json["rows"].append([row[col] for col in COLUMNS])
    json_path = os.path.splitext(output_file)[0] + ".dataset.json"
    with open(json_path, "w") as jf:
        json.dump(dataset_json, jf, indent=2)
    print(f"TE.CSV and TE.dataset.json generated.")


if __name__ == "__main__":
    main("files/usdm_sdw_v4.0.0_amendment.json", "output/TE.CSV")
