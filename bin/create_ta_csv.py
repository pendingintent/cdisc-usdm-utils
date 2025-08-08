import csv
import json

# Define the output columns
COLUMNS = [
    "STUDYID","DOMAIN","ARMCD","ARM","TAETORD","ETCD","ELEMENT","TABRANCH","TATRANS","EPOCH"
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
    "EPOCH": "study.studyVersion.studyDesigns.studyDesign.studyCells.StudyCell.epoch.StudyEpoch.name"
}

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

# Main function

def main(usdm_file, output_file):
    with open(usdm_file) as f:
        usdm = json.load(f)

    study_version = usdm["study"]["versions"][0]
    study_id = ''
    if "studyIdentifiers" in study_version and study_version["studyIdentifiers"]:
        study_id = study_version["studyIdentifiers"][0].get("text", "")

    # Get studyDesign and referenced lists
    study_design = study_version["studyDesigns"][0] if study_version.get("studyDesigns") else {}
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
                "EPOCH": epoch.get("name", "")
            }
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    main('files/usdm_sdw_v4.0.0_amendment.json', 'output/TA.CSV')
