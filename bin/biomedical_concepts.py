import json
import pandas as pd



usdm_file = "data/usdm.json"
out_file = "data/LLZT_BiomedicalConcepts.csv"

try:
    with open(usdm_file, 'r') as file:
        usdm = json.load(file)
except FileNotFoundError:
    print('The input JSON file {} does not exist'.format(usdm_file))

# debug
# print(usdm.keys())

ids = []
names = []
synonyms = []
references = []
codes = []
decodes = []

bcs = usdm['study']['versions'][0]['biomedicalConcepts']

for b in range(0, len(bcs)):
    ids.append(bcs[b]['id'])
    names.append(bcs[b]['name'])
    synonyms.append(bcs[b]['synonyms'])
    references.append(bcs[b]['reference'])
    codes.append(bcs[b]['code']['standardCode']['code'])
    decodes.append(bcs[b]['code']['standardCode']['decode'])

# debug
# print(len(ids))
# print(len(names))
# print(len(synonyms))
# print(len(codes))
# print(len(decodes))

concepts = {'id': ids, 'name': names, 'synonyms': synonyms, 'reference': references, 'code': codes, 'decode': decodes}

# debug
# print(concepts.keys())

df = pd.DataFrame(concepts)
df.to_csv(out_file)