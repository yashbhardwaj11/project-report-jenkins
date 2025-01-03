import pandas as pd

# Function to calculate the average benchmarking results
def calculate_avg_benchmarking(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Clean the column names by stripping any leading/trailing spaces
    df.columns = df.columns.str.strip()

    # List of the benchmark parameters for which we need to calculate the average
    benchmarking_params = [
        'CPU Cores (mCpu)',
        'RAM (MiB)',
        'Replica Count',
        'Test Duration (in minutes)',
        'Packages Processed',
        'Avg Response Time',
        'Error Rate'
    ]

    # Calculate and print the average for each parameter
    averages = {}
    for param in benchmarking_params:
        if param in df.columns:
            avg_value = df[param].mean()
            averages[param] = avg_value
        else:
            averages[param] = "Column not found"

    return averages

# Main function
if __name__ == "__main__":
    # Path to the benchmarking.xlsx file
    file_path = 'benchmarking.xlsx'

    # Calculate average benchmarking results
    avg_results = calculate_avg_benchmarking(file_path)

    # Print the results
    print("Average Benchmarking Results:")
    for param, avg in avg_results.items():
        print(f"{param}: {avg}")
