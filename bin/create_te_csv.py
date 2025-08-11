import csv
import json

COLUMNS = [
    "STUDYID","DOMAIN","ETCD","ELEMENT","TESTRL","TEENRL","TEDUR"
]

def main(usdm_file, output_file):
    with open(usdm_file) as f:
        usdm = json.load(f)

    study_version = usdm["study"]["versions"][0]
    study_id = ''
    if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
        study_id = study_version["studyIdentifiers"][0].get("text", "")

    study_design = study_version["studyDesigns"][0] if study_version.get("studyDesigns") else {}
    elements = study_design.get("elements", [])

    rows = []
    import re
    for element in elements:
        testrl = (element.get("transitionStartRule") or {}).get("text", "")
        teenrl = (element.get("transitionEndRule") or {}).get("text", "")
        # Remove non-breaking spaces and other special whitespace
        testrl = re.sub(r'[\u00A0\u200B\u202F\uFEFF]', ' ', testrl)
        teenrl = re.sub(r'[\u00A0\u200B\u202F\uFEFF]', ' ', teenrl)
        # Remove all double quotes and strip whitespace
        testrl = testrl.replace('"', '').strip()
        teenrl = teenrl.replace('"', '').strip()
        row = {
            "STUDYID": study_id,
            "DOMAIN": "TE",
            "ETCD": element.get("name", ""),
            "ELEMENT": element.get("description", ""),
            "TESTRL": testrl,
            "TEENRL": teenrl,
            "TEDUR": ""  # Not implemented: requires scheduleTimelines traversal
        }
        rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    main('files/usdm_sdw_v4.0.0_amendment.json', 'output/TE.CSV')
