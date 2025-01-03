import openpyxl

def print_benchmarking_data(file_name):
    try:
        # Load the workbook
        workbook = openpyxl.load_workbook(file_name)

        # Get the first sheet
        sheet = workbook.active

        # Iterate through the rows and print the content in the required format
        headers = [cell.value for cell in sheet[1]]  # Get headers from the first row
        print("\n".join([str(header) for header in headers]))  # Convert headers to strings before joining

        for row in sheet.iter_rows(min_row=2, values_only=True):
            # Convert all values to strings before printing
            for header, value in zip(headers, row):
                print(f"{header}: {str(value)}")  # Convert value to string
            print()  # Add a blank line between entries
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Specify the filename and call the function
file_name = "benchmarking.xlsx"
print_benchmarking_data(file_name)
