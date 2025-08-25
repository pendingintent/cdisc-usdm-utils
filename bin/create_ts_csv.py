
import csv
import json
import pandas as pd

TS_COLUMNS = [
    "STUDYID","DOMAIN","TSSEQ","TSGRPID","TSPARMCD","TSPARM","TSVAL","TSVALNF","TSVALCD","TSVCDREF","TSVCDVER"
]

# Helper to safely get nested values from dicts/lists
def get_nested(data, path):
    keys = path.split('.')
    for key in keys:
        if isinstance(data, list):
            try:
                data = data[0]
            except IndexError:
                return ''
        if isinstance(data, dict):
            data = data.get(key, '')
        else:
            return ''
    return data if not isinstance(data, (dict, list)) else ''

# Load TSPARM spec for mapping

def load_tsparm_spec(tsparm_spec_file):
    tsparm_map = []
    with open(tsparm_spec_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tsparm_map.append(row)
    return tsparm_map

# Main function

def main(usdm_file, ts_spec_file, tsparm_spec_file, output_file):
    # Load SDTM Terminology Excel (column A: code, column B: codelist code)
    terminology_xls = "files/SDTM Terminology.xls"
    terminology = None
    try:
        terminology = pd.read_excel(terminology_xls, header=None, usecols=[0,1], dtype=str)
        terminology.columns = ["code", "codelist_code"]
    except Exception as e:
        terminology = pd.DataFrame(columns=["code", "codelist_code"])
        with open(usdm_file) as f:
            usdm = json.load(f)

        study_version = usdm["study"]["versions"][0]
        study_id = ''
        if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
            study_id = study_version["studyIdentifiers"][0].get("text", "")

        tsparm_map = load_tsparm_spec(tsparm_spec_file)

        rows = []
        seq = 1
        study_design = study_version["studyDesigns"][0] if study_version.get("studyDesigns") else {}
        # Helper for characteristics
        def has_characteristic(decode):
            for c in study_design.get("characteristics", []):
                if c.get("decode", "").upper() == decode.upper() or c.get("code", "") == decode:
                    return True
            return False
        # Helper for population min/max age
        def get_min_max_age(which):
            vals = []
            for pop in study_design.get("population", {}).get("cohorts", []):
                age = pop.get("plannedAge", {}).get("range", {})
                v = age.get("minValue" if which=="min" else "maxValue")
                unit = age.get("unit", "")
                if v is not None:
                    vals.append((v, unit))
            # fallback to population
            pop = study_design.get("population", {})
            age = pop.get("plannedAge", {}).get("range", {})
            v = age.get("minValue" if which=="min" else "maxValue")
            unit = age.get("unit", "")
            if v is not None:
                vals.append((v, unit))
            if not vals:
                return None, None
            if which == "min":
                minval = min(vals, key=lambda x: x[0])
                return minval
            else:
                maxval = max(vals, key=lambda x: x[0])
                return maxval
        # Helper for boolean Y/N + code
        def yn_code(val):
            if val is True:
                return "Y", "C49488"
            elif val is False:
                return "N", "C49487"
            return '', ''
        for parm in tsparm_map:
            row = {col: '' for col in TS_COLUMNS}
            row["STUDYID"] = study_id
            row["DOMAIN"] = "TS"
            row["TSSEQ"] = seq
            row["TSPARMCD"] = parm["TSPARMCD"]
            row["TSPARM"] = parm["TSPARM"]
            tsp = parm["TSPARMCD"]

            # --- Example logic for key parameters ---
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
                    row["TSVAL"] = f"P{int(v)}Y" if unit and unit.lower() in ["year", "years", "yr", "y"] else str(v)
                else:
                    row["TSVAL"] = ''
                    row["TSVALNF"] = 'UNK'
            elif tsp == "AGEMAX":
                v, unit = get_min_max_age("max")
                if v is not None:
                    row["TSVAL"] = f"P{int(v)}Y" if unit and unit.lower() in ["year", "years", "yr", "y"] else str(v)
                else:
                    row["TSVAL"] = ''
                    row["TSVALNF"] = 'UNK'
            # Do not populate TSVAL, TSVALNF, TSVALCD, TSVCDREF, TSVCDVER for generic parameters
            rows.append(row)
            seq += 1

        # Write CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=TS_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        # --- Generate Dataset-JSON ---
        import datetime
        import os
        import re
        schema_path = os.path.join("files", "dataset.schema.json")
        with open(schema_path) as f:
            schema = json.load(f)
        schema_columns = []
        TS_COLUMNS = ["STUDYID","DOMAIN","TSSEQ","TSGRPID","TSPARMCD","TSPARM","TSVAL","TSVALNF","TSVALCD","TSVCDREF","TSVCDVER"]
        if "columns" in schema:
            for col in schema["columns"]:
                if col.get("name") in TS_COLUMNS:
                    schema_columns.append(col)
        elif "$defs" in schema and "Column" in schema["$defs"]:
            for colname in TS_COLUMNS:
                schema_columns.append({
                    "name": colname,
                    "label": colname,
                    "dataType": "string",
                    "itemOID": f"IT.TS.{colname}"
                })
        dataset_json = {
            "datasetJSONCreationDateTime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "datasetJSONVersion": "1.1",
            "itemGroupOID": "IG.TS",
            "records": len(rows),
            "name": "TS",
            "label": "Trial Summary",
            "columns": schema_columns,
            "rows": [],
            "originator": "cdisc-usdm-utils",
            "studyOID": study_id,
            "sourceSystem": {"name": "cdisc-usdm-utils", "version": "1.0"}
        }
        for row in rows:
            dataset_json["rows"].append([row[col] for col in TS_COLUMNS])
        json_path = re.sub(r'\.csv$', '.dataset.json', output_file, flags=re.IGNORECASE)
        with open(json_path, "w") as jf:
            json.dump(dataset_json, jf, indent=2)
        print(f"TS.CSV and TS.dataset.json generated.")

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=TS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create TS dataset from USDM JSON.")
    parser.add_argument("usdm_file", help="Input USDM JSON file")
    parser.add_argument("output_file", help="Output TS CSV file")
    parser.add_argument("--ts_spec_file", default="spec/TS_spec.csv", help="TS spec file")
    parser.add_argument("--tsparm_spec_file", default="spec/TSPARM_spec.csv", help="TSPARM spec file")
    args = parser.parse_args()
    main(args.usdm_file, args.ts_spec_file, args.tsparm_spec_file, args.output_file)
