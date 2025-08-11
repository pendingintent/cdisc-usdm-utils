import csv
import json

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
    population = study_design.get("population", {})
    criterion_ids = population.get("criterionIds", [])
    eligibility_criteria = {
        ec["id"]: ec for ec in study_design.get("eligibilityCriteria", [])
    }
    # Get protocol version from documentVersionIds
    doc_version_ids = study_version.get("documentVersionIds", [])
    doc_versions = {}
    for doc in usdm.get("study", {}).get("documentVersions", []):
        doc_versions[doc.get("id")] = doc
    # Fallback: scan all top-level keys for StudyDefinitionDocumentVersion objects
    if not doc_versions:
        for k, v in usdm.items():
            if isinstance(v, list):
                for item in v:
                    if (
                        isinstance(item, dict)
                        and item.get("instanceType") == "StudyDefinitionDocumentVersion"
                    ):
                        doc_versions[item.get("id")] = item
    tivers = "1"  # Static string for now as cannot determine from where this is mapped.
    """
    for doc_id in doc_version_ids:
        doc = doc_versions.get(doc_id)
        if doc and doc.get("version"):
            tivers = doc["version"]
            break
    """
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
        # Remove 'IE' prefix from IETEST if present
        if ietest.startswith("IE"):
            ietest = ietest[2:]
        row = {
            "STUDYID": study_id,
            "DOMAIN": "TI",
            "IETESTCD": ietestcd,
            "IETEST": ietest,
            "IECAT": iecat,
            "IESCAT": "",  # Not available in USDM
            "TIRL": crit.get("label", ""),
            "TIVERS": tivers,
        }
        rows.append(row)

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    main("files/usdm_sdw_v4.0.0_amendment.json", "output/TI.CSV")
