import pandas as pd
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import os
import csv

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

def load_input_file():
    input_path = filedialog.askopenfilename(title="Input File Selection", filetypes=[("CSV files", "*.csv")])
    if input_path:
        print("\nInput file loaded successfully.\n")
        return pd.read_csv(input_path, parse_dates=['Expiry Date', 'Coverage Effective date'], dayfirst=True)
    else:
        print("\nNo Input file selected.\n")
        return None

def is_date_greater(date1, date2):
    return date1 > date2

def check_inf(row, valuation_date):
    conditions_failed = []

    expiry_greater = row['Expiry Date'] > valuation_date
    if not expiry_greater:
        conditions_failed.append("Expiry Date should be greater than Valuation Date")
    
    coverage_effective_less_valuation = row['Coverage Effective date'] < valuation_date
    if not coverage_effective_less_valuation:
        conditions_failed.append("Coverage Effective date should be less than Valuation Date")
    
    coverage_effective_less_expiry = row['Coverage Effective date'] < row['Expiry Date']
    if not coverage_effective_less_expiry:
        conditions_failed.append("Coverage Effective date should be less than Expiry Date")
    
    return not conditions_failed, conditions_failed

def check_TR(row, valuation_date):
    conditions_failed = []
    tr_condition = valuation_date > row['Expiry Date']
    if not tr_condition:
        conditions_failed.append("Valuation Date should be greater than Expiry Date")
    return tr_condition, conditions_failed

def check_claim(row, valuation_date):
    conditions_failed = []
    claim_condition = row['claim date'] > valuation_date
    if not claim_condition:
        conditions_failed.append("Claim date should be greater than Valuation Date")
    return claim_condition, conditions_failed

def data_checks_by_status(row, valuation_date):
    status = str(row['Status']).strip()  
    conditions_failed = []
    if status == 'inf':
        result, conditions_failed = check_inf(row, valuation_date)
    elif status == 'TR':
        result, conditions_failed = check_TR(row, valuation_date)
    else:
        result = True
    return result, conditions_failed

def data_checks_boundary_values(row):
    conditions_failed = []
    age_limits = {
        '163N001V01': (18, 70),
        '163N004V01': (18, 62),
        '163N003V01': (18, 60),
        '163N002V01': (18, 60)
    }
    sa_limits = {
        '163N001V01': (1000, 200000),
        '163N004V01': (10000, 2500000),
        '163N003V01': (50000, 2000000),
        '163N002V01': (1000, 200000)
    }
    policy_term_limits = {
        '163N001V01': (1, 36),
        '163N004V01': (1, 240),
        '163N003V01': (12, 12),
        '163N002V01': (12, 12)
    }    
    product_name = str(row['UIN']).strip()  # Convert to string and strip whitespace
    entry_age = int(row['PH Entry Age'])  # Convert to integer
    sa = float(row['Sum Assured'])  # Convert to float
    policy_term = int(row['Policy Term_Month'])  # Convert to integer
    if not (age_limits.get(product_name, (18, float('inf')))[0] <= entry_age <= age_limits.get(product_name, (18, float('inf')))[1]):
        conditions_failed.append("Entry Age is out of bounds")
    if not (sa_limits.get(product_name, (1000, float('inf')))[0] <= sa <= sa_limits.get(product_name, (1000, float('inf')))[1]):
        conditions_failed.append("Sum Assured is out of bounds")
    if not (policy_term_limits.get(product_name, (1, float('inf')))[0] <= policy_term <= policy_term_limits.get(product_name, (1, float('inf')))[1]):
        conditions_failed.append("Policy Term is out of bounds")
    return len(conditions_failed) == 0, conditions_failed

def perform_data_checks(input_dataset, valuation_date):
    print("\n\t\t ->> Data Validation process <<- ")
    print("\t\t___________________________________\n")
    failed_checks = []
    for index, row in input_dataset.iterrows():
        status_result, status_conditions_failed = data_checks_by_status(row, valuation_date)
        boundary_result, boundary_conditions_failed = data_checks_boundary_values(row)
        if not status_result:
            failed_checks.append((row['Policy/CoI Number'], row['Status'], "Data checks by status failed", status_conditions_failed))
        if not boundary_result:
            failed_checks.append((row['Policy/CoI Number'], row['Status'], "Boundary value check failed", boundary_conditions_failed))
    
    if not failed_checks:
        print("\n\tAll data checks passed successfully!")
    else:
        for check in failed_checks:
            print(f"\nData check failed for COI {check[0]} || Status: {check[1]} || Reason: {check[2]} || Failed conditions: {check[3]}")
    
    return failed_checks

def separate_csv_files_by_uin(input_dataset):
    output_directory = filedialog.askdirectory(title="Select Directory to Save CSV Files")
    if output_directory:
        print("\n\nCreating CSV files:")
        uin_groups = input_dataset.groupby('UIN')
        for uin, group in uin_groups:
            output_path = os.path.join(output_directory, f"{uin}.csv")
            group.to_csv(output_path, index=False)
            print(f"\tCSV file created for UIN {uin} at {output_path}")

def save_failed_records_to_csv(failed_checks, input_dataset):
    if failed_checks:
        response = messagebox.askyesno("Save Failed Records", "Do you want to save the failed records to a separate CSV file?")
        if response:
            print("\n\nSaving Failed records : ")
            output_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Failed Records")
            if output_path:
                with open(output_path, 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow(input_dataset.columns.tolist() + ['Failed Conditions'])
                    for check in failed_checks:
                        index = input_dataset[input_dataset['Policy/CoI Number'] == check[0]].index[0]
                        row_data = input_dataset.loc[index].tolist()
                        csv_writer.writerow(row_data + [', '.join(check[3])])
                print(f"\tFailed records saved to {output_path}")

if __name__ == "__main__":
    valuation_date = pd.Timestamp(datetime.today().date())
    print("\n\t\t ===>> Data Validation Output <<===")
    print("\t\t_____________________________________\n")

    print("\nValuation Date:", valuation_date.strftime("%d-%m-%Y"))

    input_dataset = load_input_file()
    if input_dataset is not None:
        failed_checks = perform_data_checks(input_dataset, valuation_date)
        print("\n\n\t\t ==>> Data Validation Process Completed ! <<== \n")
        save_failed_records_to_csv(failed_checks,input_dataset)
        response = messagebox.askyesno("Separate CSV Files", "Do you want separate CSV files for each UIN?")
        if response:
            separate_csv_files_by_uin(input_dataset)
    print("\n\nProcess Completed !")