import pandas as pd
import json


usdm = "files/pilot_LLZT_protocol.json"
out = "output/activities.csv"


with open(usdm) as f:
    data = json.load(f)

df = pd.json_normalize(data)
print(df.columns)
"""
    Index(['usdmVersion', 'systemName', 'systemVersion', 'study.id', 'study.name',
       'study.description', 'study.label', 'study.versions',
       'study.documentedBy', 'study.instanceType'],
      dtype='object')
"""

# print(df['study.versions'].to_string(index=False))
print(
    "Children of study versions: ",
    len(df[["study.versions"][0]].to_string(index=False)),
)
study_Versions = df[["study.versions"][0]]
print(study_Versions.iloc[0:5])
