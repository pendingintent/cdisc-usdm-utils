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

    version = usdm["study"]["versions"][0]
    bcs = version.get("biomedicalConcepts", [])
    surrogates = version.get("bcSurrogates", [])

    # Extract biomedicalConcepts
    for bc in bcs:
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

    # Extract bcSurrogates
    for surr in surrogates:
        ids.append(surr.get("id", ""))
        names.append(surr.get("name", ""))
        labels.append(surr.get("label", ""))
        synonyms.append("")
        references.append(surr.get("reference", ""))
        codes.append("")
        decodes.append("")

    concepts = {
        "id": ids,
        "name": names,
        "label": labels,
        "synonyms": synonyms,
        "reference": references,
        "code": codes,
        "decode": decodes,
    }

    df = pd.DataFrame(concepts)
    df = df[["id", "name", "label", "synonyms", "reference", "code", "decode"]]
    df.to_csv(out_file, index=False)


# All logic is now inside process_usdm_biomedical_concepts_to_csv. No top-level code is needed here.
