import pandas as pd
from fmiprecice import runner

df_expected = pd.read_csv("./output/expected-result-fmi.csv")
df_calculated = pd.read_csv("./output/test-result-fmi.csv")

assert(df_expected.equals(df_calculated))
print("Test finished without error.")
