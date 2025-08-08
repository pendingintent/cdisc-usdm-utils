import json
import pandas as pd

in_file = "data/usdm.json"
out_file = "TDD/TE.csv"

try:
    with open(in_file, 'r') as f:
        usdm = json.load(f)
except FileNotFoundError:
    print('The file {} was not found...'.format(in_file))


# debug
# print(usdm.keys())

studyId = usdm['study']['versions'][0]['studyIdentifiers'][0]['text']
domain = 'TV'

headers = ["STUDYID", "DOMAIN", "VISITNUM", "VISIT", "VISITDY", "ARMCD", "ARM", "TVSTRL", "TVENRL"]
encountersL = []
visitnumL = []
visitL = []
visitdyL = []       # TODO: timings
armcdL = []
armL = []
tvstrlL = []
tvenrlL = []
num = 1


encounters = usdm['study']['versions'][0]['studyDesigns'][0]['encounters']
# debug
print('Number of visits is ', len(encounters))

for e in range(0, len(encounters)):
    visitnumL.append(num)
    visitL.append(encounters[e]['name'])
    
    if(encounters[e]['transitionStartRule']):
        tvstrlL.append(encounters[e]['transitionStartRule']['text'])
    if(encounters[e]['transitionEndRule']):
        tvenrlL.append(encounters[e]['transitionEndRule']['text'])
    tvenrlL.append(encounters[e])
    num = num + 1