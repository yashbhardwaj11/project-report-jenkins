import openpyxl
import json

# Load the Excel file
file_path = 'benchmarking.xlsx'  # Fixed file name
wb = openpyxl.load_workbook(file_path)

# Select the active sheet
sheet = wb.active

# Initialize an empty dictionary
data_dict = {}

# Iterate over rows in the first two columns
for row in sheet.iter_rows(min_row=1, max_col=2, values_only=True):
    name, value = row
    data_dict[name] = value

# Convert the dictionary to JSON format and print
json_data = json.dumps(data_dict, indent=4)
print(json_data)
