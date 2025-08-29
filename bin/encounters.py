# data['study']['versions'][0]['studyDesigns'][0]['encounters']
# len(data['study']['versions'][0]['studyDesigns'][0]['encounters']) = 12
# This identifies 12 encounters (visits)
import json
import pandas as pd

# load the JSON file
# this creates a dictionary
# usdm = "data/CDISC_Pilot_Study.json" #invalid USDM file
usdm = "files/pilot_LLZT_protocol.json"
with open(usdm) as f:
    data = json.load(f)


# create a list of encounters
encounters = data["study"]["versions"][0]["studyDesigns"][0]["encounters"]

# print encounter
i = 0
for i in range(0, len(encounters)):
    print("Encounter Name: ", encounters[i]["name"])
    print("Encounter Label: ", encounters[i]["label"])
