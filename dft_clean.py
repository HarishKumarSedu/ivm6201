import pandas as pd
import re 
from dft import *

def rename_column_with_testname_data(file_path:str,sheet_name:str):
    try:
        # In pandas, row indexing starts at 0, so row 2 is index 1
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        raw_data = df.iloc[:, :] # make shallow copy of the raw data
        raw_data.iloc[2,0] = 'Pin_No' # replace parameter
        raw_data.iloc[3,1] = 'Instructions'
        raw_data.iloc[2,1] = 'Parameter'
        raw_data.columns = [ x.strip().replace(' ', '_') if isinstance(x, str) else x for x in raw_data.iloc[2].tolist()]
        raw_data.set_index('Parameter', inplace=True)
        raw_data.loc['Typ'] = raw_data.loc['Typ'].apply(lambda x : parse_multiplier_value(x))
        raw_data.loc['Min'] = raw_data.loc['Min'].apply(lambda x : parse_multiplier_value(x))
        raw_data.loc['Max'] = raw_data.loc['Max'].apply(lambda x : parse_multiplier_value(x))
        # with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
        #     # Write the new DataFrame to the specified sheet
        #     raw_data.to_excel(writer, sheet_name='Reference', index=False)
        return raw_data
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []