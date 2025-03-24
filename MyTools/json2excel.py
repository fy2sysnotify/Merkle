import pandas as pd

excel_file = 'output.xlsx'

df = pd.read_json('input.json')
df.to_excel(excel_file)
