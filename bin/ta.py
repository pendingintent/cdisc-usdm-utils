import json
import pandas as pd

in_file = "files/pilot_LLZT_protocol.json"
out_file = "TDD/TA.csv"

try:
    with open(in_file, "r") as f:
        usdm = json.load(f)
except FileNotFoundError:
    print("The file {} was not found...".format(in_file))

# debug
# print(usdm.keys())

studyId = usdm["study"]["versions"][0]["studyIdentifiers"][0]["text"]
domain = "TA"

num = 1

# Create list of dictionaries for arms and epochs
cells = usdm["study"]["versions"][0]["studyDesigns"][0]["studyCells"]
# encounters = usdm['study']['versions'][0]['studyDesigns'][0]['encounters']
arms = usdm["study"]["versions"][0]["studyDesigns"][0]["arms"]
epochs = usdm["study"]["versions"][0]["studyDesigns"][0]["epochs"]
elements = epochs = usdm["study"]["versions"][0]["studyDesigns"][0]["elements"]

# Create dataframe for epochs and normalize the type column
epochsDF = pd.DataFrame(
    epochs,
    columns=["id", "name", "label", "description", "type", "previousId", "nextId"],
)
types = pd.json_normalize(epochsDF.type)
types.columns = [f"type_{col}" for col in types.columns]
epochsDF = pd.concat([epochsDF, types], axis=1)
# debug
# print(epochsDF.head())

# Create dataframe for arms and normnalize the type and dataOriginType columns
armsDF = pd.DataFrame(
    arms, columns=["id", "name", "label", "description", "type", "dataOriginType"]
)
types = pd.json_normalize(armsDF.type)
types.columns = [f"type_{col}" for col in types.columns]
origins = pd.json_normalize(armsDF.dataOriginType)
origins.columns = [f"dataOriginType_{col}" for col in origins.columns]
armsDF = pd.concat([armsDF, types, origins], axis=1)
armsDF = armsDF.drop(
    columns=[
        "type_extensionAttributes",
        "type_codeSystem",
        "type_codeSystemVersion",
        "type_instanceType",
        "dataOriginType_id",
        "dataOriginType_extensionAttributes",
        "dataOriginType_codeSystem",
        "dataOriginType_codeSystemVersion",
        "dataOriginType_instanceType",
    ]
)
# debug
# print(armsDF.head())

# Create the cells dataframe
cellsDF = pd.DataFrame(cells, columns=["id", "armId", "epochId", "elementIds"])
# debug
# print(cellsDF.head())

# Merge the cells and arms into a dataframe
ta_df = pd.merge(cellsDF, armsDF, how="left", left_on="armId", right_on="id")
ta_df["elementId"] = ta_df["elementIds"].apply(lambda x: "".join(map(str, x)))
ta_df = ta_df.drop(columns=["id_x", "id_y", "elementIds"])

# debug
# print(ta_df.head())

# create the elements dataframe
elementsDF = pd.DataFrame(
    elements,
    columns=[
        "id",
        "name",
        "label",
        "description",
        "transitionStartRule",
        "transitionEndRule",
    ],
)
startRules = pd.json_normalize(elementsDF.transitionStartRule)
startRules.columns = [f"transitionStartRule_{col}" for col in startRules.columns]
endRules = pd.json_normalize(elementsDF.transitionEndRule)
endRules.columns = [f"transitionEndRule_{col}" for col in endRules.columns]
elementsDF = pd.concat([elementsDF, startRules, endRules], axis=1)
elementsDF = elementsDF[
    [
        "id",
        "name",
        "label",
        "description",
        "transitionStartRule_text",
        "transitionEndRule_text",
    ]
]
# debug
# print(elementsDF.head())

# Merge the ta dataframe with the elements dataframe
ta_df = pd.merge(ta_df, elementsDF, how="left", left_on="elementId", right_on="id")
print(ta_df.columns)
