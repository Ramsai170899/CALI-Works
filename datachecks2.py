import pandas as pd
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import os

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

def load_input_file():
    input_path = filedialog.askopenfilename(title="Input File Selection", filetypes=[("CSV files", "*.csv")])
    if input_path:
        print("\nInput file loaded successfully.\n")
        return pd.read_csv(input_path)
    else:
        print("\nNo Input file selected.\n")
        return None

def is_date_greater(date1, date2):
    if isinstance(date1, str):
        date1 = datetime.strptime(date1, "%d-%m-%Y")
    if isinstance(date2, str):
        date2 = datetime.strptime(date2, "%d-%m-%Y")
    return date1 > date2

def check_inf(row):
    expiry_greater = is_date_greater(row['Expiry Date'], row['Valuation Date'])
    coverage_effective_less_valuation = is_date_greater(row['Coverage Effective date'], row['Valuation Date'])
    coverage_effective_less_expiry = is_date_greater(row['Coverage Effective date'], row['Expiry Date'])
    return expiry_greater and coverage_effective_less_valuation and coverage_effective_less_expiry

def check_TR(row):
    return is_date_greater(row['Valuation Date'], row['Expiry Date'])

def check_claim(row):
    return is_date_greater(row['claim date'], row['Valuation Date'])

def data_checks_by_status(row):
    status = row['Status']
    if status == 'inf':
        return check_inf(row)
    elif status == 'TR':
        return check_TR(row)
    elif status == 'claim':
        return check_claim(row)
    else:
        return True

def data_checks_boundary_values(row):
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
    product_name = row['UIN']
    entry_age = row['PH Entry Age']  
    sa = row['Sum Assured']
    policy_term = row['Policy Term_Month']
    if not (age_limits.get(product_name, (18, float('inf')))[0] <= entry_age <= age_limits.get(product_name, (18, float('inf')))[1]):
        return False
    if not (sa_limits.get(product_name, (1000, float('inf')))[0] <= sa <= sa_limits.get(product_name, (1000, float('inf')))[1]):
        return False
    if not (policy_term_limits.get(product_name, (1, float('inf')))[0] <= policy_term <= policy_term_limits.get(product_name, (1, float('inf')))[1]):
        return False
    return True

def perform_data_checks(input_dataset):
    print("\nData Validation process...")
    failed_checks = []
    for index, row in input_dataset.iterrows():
        if not data_checks_by_status(row):
            failed_checks.append((row['Policy/CoI Number'], row['Status'], "Data checks by status failed"))
        if not data_checks_boundary_values(row):
            failed_checks.append((row['Policy/CoI Number'], row['Status'], "Boundary value check failed"))
    
    if not failed_checks:
        print("All data checks passed successfully!")
    else:
        for check in failed_checks:
            print(f"Data check failed for COI {check[0]} - Status: {check[1]} - Reason: {check[2]}")

def separate_csv_files_by_uin(input_dataset):
    output_directory = filedialog.askdirectory(title="Select Directory to Save CSV Files")
    if output_directory:
        uin_groups = input_dataset.groupby('UIN')
        for uin, group in uin_groups:
            output_path = os.path.join(output_directory, f"{uin}.csv")
            group.to_csv(output_path, index=False)
            print(f"CSV file created for UIN {uin} at {output_path}")

if __name__ == "__main__":
    input_dataset = load_input_file()
    if input_dataset is not None:
        perform_data_checks(input_dataset)
        print("\nData Check process Completed!\n")
        response = messagebox.askyesno("Separate CSV Files", "Do you want separate CSV files for each UIN?")
        if response:
            separate_csv_files_by_uin(input_dataset)
