import pandas as pd

# Function to fetch benchmarking parameters and their values
def fetch_benchmarking_data(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Clean the column names by stripping any leading/trailing spaces
    df.columns = df.columns.str.strip()

    # List of the benchmark parameters to fetch
    benchmarking_params = [
        'CPU Cores (mCpu)',
        'RAM (MiB)',
        'Replica Count',
        'Test Duration (in minutes)',
        'Packages Processed',
        'Avg Response Time',
        'Error Rate'
    ]

    # Fetch the parameters and their values
    results = {}
    for param in benchmarking_params:
        if param in df.columns:
            results[param] = df[param].tolist()  # Get all values as a list
        else:
            results[param] = "Column not found"

    return results

# Main function
if __name__ == "__main__":
    # Path to the benchmarking.xlsx file
    file_path = 'benchmarking.xlsx'

    # Fetch benchmarking data
    benchmarking_data = fetch_benchmarking_data(file_path)

    # Print the results
    print("Benchmarking Data:")
    for param, values in benchmarking_data.items():
        print(f"{param}: {values}")
