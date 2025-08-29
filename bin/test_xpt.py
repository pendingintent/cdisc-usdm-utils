# This file only works for python=3.10

import xport
import xport.v56
import pandas as pd
import os

csv_file = "./output_from_main/TA.CSV"

df = pd.read_csv(csv_file)
print(df)


ds = xport.Dataset(df, name="TA", label="Trial Arms")

ds = ds.rename(columns={k: k.upper()[:8] for k in ds})

for k, v in ds.items():
    v.label = k.title()
    if v.dtype == "object":
        v.format = "$CHAR20."
    else:
        v.format = "10.2"

library = xport.Library({"TA": ds})

with open("./output_from_main/TA.xpt", "wb") as f:
    xport.v56.dump(library, f)
