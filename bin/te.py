import json
import pandas as pd

def duration(model, elementId):
    # Lookup StudyCells
    cells = model['study']['versions'][0]['studyDesigns'][0]['studyCells']
    # debug
    # print(len(cells))
    # Lookup epochId for corresponding studyCell
    for c in range(0, len(cells)):
        if cells[c]['elementIds'][0] == elementId:
            print(cells[c]['epochId']) # debug statement -> prints the epochId
            # TODO: use the epochId to look up ScheduledActivityInstance associated with epoch
    pass


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
domain = 'TE'

elements = usdm['study']['versions'][0]['studyDesigns'][0]['elements']
# debug
# print(len(elements))

etcdList = []
elementList = []
testrlList = []
teenrlList = []

for e in range(0, len(elements)):
    etcdList.append(elements[e]['name'])
    elementList.append(elements[e]['description'])
    testrlList.append(elements[e]['transitionStartRule']['text'].replace(u'\xa0', u' '))
    if elements[e]['transitionEndRule']:
        teenrlList.append(elements[e]['transitionEndRule']['text'].replace(u'\xa0', u' '))
    else:
        teenrlList.append("")

table = {'STUDYID': studyId, 'DOMAIN': domain, 'ETCD': etcdList, 'TESTRL': testrlList, 'TEENRL': teenrlList}
print(table)
df = pd.DataFrame(table)
print(df)

duration(usdm, "StudyElement_1")