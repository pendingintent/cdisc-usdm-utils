import json
import pandas as pd


def process_usdm_biomedical_concepts_to_csv(usdm_file: str, out_file: str):
    """
    Process a USDM JSON file and output biomedical concepts to a CSV file.
    Args:
        usdm_file (str): Path to the input USDM JSON file.
        out_file (str): Path to the output CSV file.
    """
    try:
        with open(usdm_file, "r") as file:
            usdm = json.load(file)
    except FileNotFoundError:
        print(f"The input JSON file {usdm_file} does not exist")
        return

    # Prepare lists for all concepts and surrogates
    ids = []
    names = []
    labels = []
    synonyms = []
    references = []
    codes = []
    decodes = []
    parent_ids = []

    version = usdm["study"]["versions"][0]
    bcs = version.get("biomedicalConcepts", [])
    surrogates = version.get("bcSurrogates", [])

    # Extract biomedicalConcepts and their properties
    for bc in bcs:
        # Parent concept row
        ids.append(bc.get("id", ""))
        names.append(bc.get("name", ""))
        labels.append(bc.get("label", ""))
        synonyms.append(", ".join(bc.get("synonyms", [])) if bc.get("synonyms") else "")
        references.append(bc.get("reference", ""))
        code = ""
        decode = ""
        if "code" in bc and "standardCode" in bc["code"]:
            code = bc["code"]["standardCode"].get("code", "")
            decode = bc["code"]["standardCode"].get("decode", "")
        codes.append(code)
        decodes.append(decode)
        parent_ids.append("")

        # Properties as additional rows
        for prop in bc.get("properties", []):
            prop_id = prop.get("id", "")
            ids.append(prop_id)
            names.append(prop.get("name", ""))
            labels.append(prop.get("label", ""))
            synonyms.append("")
            references.append(prop.get("reference", ""))
            pcode = ""
            pdecode = ""
            if "code" in prop and "standardCode" in prop["code"]:
                pcode = prop["code"]["standardCode"].get("code", "")
                pdecode = prop["code"]["standardCode"].get("decode", "")
            codes.append(pcode)
            decodes.append(pdecode)
            parent_ids.append(bc.get("id", ""))

            # Extract ResponseCodes as child rows
            for rc in prop.get("responseCodes", []):
                rc_id = rc.get("id", "")
                ids.append(rc_id)
                names.append(rc.get("name", ""))
                labels.append(rc.get("label", ""))
                synonyms.append("")
                references.append("")
                rccode = ""
                rcdecode = ""
                if "code" in rc:
                    if "code" in rc["code"]:
                        # Nested code object
                        rccode = rc["code"].get("code", "")
                        rcdecode = rc["code"].get("decode", "")
                    else:
                        rccode = rc["code"].get("code", "")
                        rcdecode = rc["code"].get("decode", "")
                codes.append(rccode)
                decodes.append(rcdecode)
                parent_ids.append(prop_id)

    # Extract bcSurrogates
    for surr in surrogates:
        ids.append(surr.get("id", ""))
        names.append(surr.get("name", ""))
        labels.append(surr.get("label", ""))
        synonyms.append("")
        references.append(surr.get("reference", ""))
        codes.append("")
        decodes.append("")
        parent_ids.append("")

    concepts = {
        "id": ids,
        "parent_id": parent_ids,
        "name": names,
        "label": labels,
        "synonyms": synonyms,
        "reference": references,
        "code": codes,
        "decode": decodes,
    }

    df = pd.DataFrame(concepts)
    df = df[["id", "parent_id", "name", "label", "synonyms", "reference", "code", "decode"]]
    df.to_csv(out_file, index=False)


# All logic is now inside process_usdm_biomedical_concepts_to_csv. No top-level code is needed here.
