import csv
import json
import re

COLUMNS = [
    "STUDYID","DOMAIN","VISITNUM","VISIT","VISITDY","ARMCD","ARM","TVSTRL","TVENRL"
]

def main(usdm_file, output_file):
    with open(usdm_file) as f:
        usdm = json.load(f)

    study_version = usdm["study"]["versions"][0]
    study_id = ''
    if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
        study_id = study_version["studyIdentifiers"][0].get("text", "")

    study_design = study_version["studyDesigns"][0] if study_version.get("studyDesigns") else {}
    arms = {arm["id"]: arm for arm in study_design.get("arms", [])}
    study_cells = study_design.get("studyCells", [])
    encounters = study_design.get("encounters", [])
    encounter_map = {e["id"]: e for e in encounters}

    # Order encounters by chaining previousId/nextId
    visit_order = []
    id_to_prev = {e["id"]: e.get("previousId") for e in encounters}
    # Find the first encounter (no previousId)
    first = next((eid for eid, prev in id_to_prev.items() if not prev), None)
    if first:
        curr = first
        while curr:
            visit_order.append(curr)
            curr = next((e["id"] for e in encounters if e.get("previousId") == curr), None)
    else:
        visit_order = [e["id"] for e in encounters]

    rows = []
    for arm in arms.values():
        armcd = arm.get("name", "") or ""
        armname = arm.get("description", "") or ""
        for idx, eid in enumerate(visit_order, 1):
            enc = encounter_map[eid]
            # Clean up special whitespace
            tvstrl = (enc.get("transitionStartRule") or {}).get("text", "") or ""
            tvenrl = (enc.get("transitionEndRule") or {}).get("text", "") or ""
            tvstrl = re.sub(r'[\u00A0\u200B\u202F\uFEFF]', ' ', tvstrl).replace('"', '').strip() or ""
            tvenrl = re.sub(r'[\u00A0\u200B\u202F\uFEFF]', ' ', tvenrl).replace('"', '').strip() or ""
            # Parse VISITDY from description (e.g., 'Day 14' -> 14), else 0/empty
            desc = enc.get("description", "")
            visitdy = ""
            if idx == 1:
                visitdy = "0"
            elif desc:
                import re as _re
                m = _re.search(r'Day (\d+)', desc)
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
                "TVENRL": tvenrl
            }
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    main('files/usdm_sdw_v4.0.0_amendment.json', 'output/TV.CSV')
