import os
import numpy as np
import pandas as pd

print(os.cpu_count())
csv_path = '../../../../Downloads/38_Public_Test_Set_and_Submmision_Template/public_x.csv'
df = pd.read_csv(csv_path)
# save col name to text file
# col_names = df.columns.tolist()
# with open('col_names.txt', 'w') as f:
#     for col in col_names:
#         f.write(col + '\n')

# correlation matrix
# exclude the first column
df = df.iloc[:, 1:]
# calculate correlation matrix
corr = df.corr()
# save to csv
corr.to_csv('corr.csv')