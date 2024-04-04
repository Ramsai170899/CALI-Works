from tkinter import *
from tkcalendar import Calendar
from datetime import datetime
import pandas as pd
import warnings
from tkinter import filedialog, messagebox
import os
import csv

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

def load_input_file():
    input_path = filedialog.askopenfilename(title="Input File Selection", filetypes=[("CSV files", "*.csv")])
    if input_path:
        print("\nInput file loaded successfully.\n")
        # Read the data without parsing dates yet
        df = pd.read_csv(input_path)
        # Parse dates explicitly with specified format
        df['Expiry Date'] = pd.to_datetime(df['Expiry Date'], format='%d-%m-%Y')
        df['Coverage Effective date'] = pd.to_datetime(df['Coverage Effective date'], format='%d-%m-%Y')
        return df
    else:
        print("\nNo Input file selected.\n")
        return None

def is_date_greater(date1, date2):
    return date1 > date2

def check_inf(row, valuation_date):
    conditions_failed = []

    # Convert 'Expiry Date' and 'Coverage Effective date' to Timestamp objects
    expiry_date = pd.to_datetime(row['Expiry Date'])
    coverage_effective_date = pd.to_datetime(row['Coverage Effective date'])

    # Perform comparisons
    expiry_greater = expiry_date >= valuation_date
    if not expiry_greater:
        conditions_failed.append("Expiry Date should be greater than Valuation Date")
    
    effective_less_or_equal_valuation = coverage_effective_date <= valuation_date
    if not effective_less_or_equal_valuation:
        conditions_failed.append("Coverage Effective date should be less than or equal to Valuation Date")

    
    coverage_effective_less_expiry = coverage_effective_date < expiry_date
    if not coverage_effective_less_expiry:
        conditions_failed.append("Coverage Effective date should be less than Expiry Date")
    
    return not conditions_failed, conditions_failed

def data_checks_by_status(row, valuation_date):
    status = str(row['Status']).strip()  
    conditions_failed = []
    if status == 'inf':
        result, conditions_failed = check_inf(row, valuation_date)
    # elif status == 'TR':
    #     result, conditions_failed = check_TR(row, valuation_date)
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
    premium_limits = {
        '163N001V01': (1, 52982),
        '163N004V01': (1, 492734),
        '163N002V01': (1, 7560)
    }
    policy_term_limits = {
        '163N001V01': (1, 36),
        '163N004V01': (1, 240),
        '163N003V01': (12, 12),
        '163N002V01': (12, 12)
    }    
    product_name = str(row['UIN']).strip() 
    entry_age = int(row['PH Entry Age']) 
    sa = float(row['Sum Assured'])
    premium = float(row['Premium'])  
    policy_term = int(row['Policy Term_Month'])  
    ph_gender = str(row['PH Gender']).strip()  

    if not (age_limits.get(product_name, (18, float('inf')))[0] <= entry_age <= age_limits.get(product_name, (18, float('inf')))[1]):
        conditions_failed.append("Entry Age is out of bounds")
    
    if not (sa_limits.get(product_name, (1000, float('inf')))[0] <= sa <= sa_limits.get(product_name, (1000, float('inf')))[1]):
        conditions_failed.append("Sum Assured is out of bounds")
    
    if not (premium_limits.get(product_name, (1, float('inf')))[0] <= premium <= premium_limits.get(product_name, (1, float('inf')))[1]):
        conditions_failed.append("Premium is out of bounds")
    
    if not (policy_term_limits.get(product_name, (1, float('inf')))[0] <= policy_term <= policy_term_limits.get(product_name, (1, float('inf')))[1]):
        conditions_failed.append("Policy Term is out of bounds")
    
    if ph_gender not in ['Female', 'Male']:
        conditions_failed.append("PH Gender should be either Female or Male")

    return len(conditions_failed) == 0, conditions_failed

def perform_data_checks(input_dataset, valuation_date):
    print("\n\t\t ->> Data Validation process <<- ")
    print("\t\t___________________________________\n")
    failed_checks = []
    duplicate_records = set()  # Using a set to store duplicate Policy/CoI Numbers

    # List of columns to check for empty values or 0
    columns_to_check = ['Sum Assured', 'Premium', 'Policy Term_Month']  # Add your column names here

    # Check for duplicate Policy/CoI Numbers
    duplicate_policy_coi = input_dataset[input_dataset.duplicated(subset=['Policy/CoI Number'], keep=False)]
    if not duplicate_policy_coi.empty:
        duplicate_records = set(duplicate_policy_coi['Policy/CoI Number'])  # Storing duplicate Policy/CoI Numbers

    for index, row in input_dataset.iterrows():
        status_result, status_conditions_failed = data_checks_by_status(row, valuation_date)
        boundary_result, boundary_conditions_failed = data_checks_boundary_values(row)

        # Check for empty values or 0 in specified columns
        missing_or_zero_conditions_failed = []
        for column in columns_to_check:
            if pd.isnull(row[column]) or row[column] == 0:
                missing_or_zero_conditions_failed.append(f"Value missing or zero in column '{column}'")

        if missing_or_zero_conditions_failed:
            failed_checks.append((row['Policy/CoI Number'], row['Status'], "Empty values or 0 check failed", missing_or_zero_conditions_failed))

        if row['Policy/CoI Number'] in duplicate_records:  # Checking if current record's Policy/CoI Number is in the set of duplicates
            failed_checks.append((row['Policy/CoI Number'], row['Status'], "Duplicate Policy/CoI Number", [row['Policy/CoI Number']]))

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


# def save_failed_records_to_csv(failed_checks, input_dataset):
#     if failed_checks:
#         response = messagebox.askyesno("Save Failed Records", "Do you want to save the failed records to a separate CSV file?")
#         if response:
#             print("\n\nSaving Failed records : ")
#             output_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Failed Records")
#             if output_path:
#                 columns_to_save = ['MPH Code', 'Policy/CoI Number', 'UIN', 'Coverage Effective date', 'Expiry Date', 'maturity date', 'PH DOB', 'Valuation Date', 'Premium', 'Sum Assured', 'Policy Term_Month', 'Failed Conditions']
#                 # Create a DataFrame for failed records with the specified columns
#                 failed_dataset = pd.DataFrame(columns=columns_to_save)
#                 with open(output_path, 'w', newline='') as csvfile:
#                     csv_writer = csv.writer(csvfile)
#                     csv_writer.writerow(columns_to_save)
#                     for check in failed_checks:
#                         index = input_dataset[input_dataset['Policy/CoI Number'] == check[0]].index[0]
#                         row_data = input_dataset.loc[index, columns_to_save[:-1]].tolist()  # Exclude 'Failed Conditions' column
#                         # Convert integer values to strings
#                         row_data = [str(item) for item in row_data]
#                         csv_writer.writerow(row_data + [', '.join(check[3])])
#                 print(f"\tFailed records saved to {output_path}")



def save_failed_records_to_csv(failed_checks, input_dataset):
    if failed_checks:
        response = messagebox.askyesno("Save Failed Records", "Do you want to save the failed records to a separate CSV file?")
        if response:
            print("\n\nSaving Failed records : ")
            output_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Save Failed Records")
            if output_path:
                columns_to_save = ['MPH Code', 'Policy/CoI Number', 'UIN', 'Coverage Effective date', 'Expiry Date', 'maturity date', 'PH DOB', 'Valuation Date', 'Premium', 'Sum Assured', 'Policy Term_Month', 'Failed Conditions']
                # Create a DataFrame for failed records with the specified columns
                failed_dataset = pd.DataFrame(columns=columns_to_save)
                for check in failed_checks:
                    index = input_dataset[input_dataset['Policy/CoI Number'] == check[0]].index[0]
                    row_data = input_dataset.loc[index, columns_to_save[:-1]].tolist()  # Exclude 'Failed Conditions' column
                    # Convert integer values to strings
                    row_data = [str(item) for item in row_data]
                    # Format 'Coverage Effective date' and 'Expiry Date'
                    row_data[3] = pd.to_datetime(row_data[3]).strftime('%d-%m-%Y')
                    row_data[4] = pd.to_datetime(row_data[4]).strftime('%d-%m-%Y')
                    row_data.append(', '.join(check[3]))
                    failed_row = pd.Series(row_data, index=columns_to_save)
                    failed_dataset = pd.concat([failed_dataset, failed_row.to_frame().transpose()], ignore_index=True)

                # Save the DataFrame to CSV
                failed_dataset.to_csv(output_path, index=False)
                print(f"\tFailed records saved to {output_path}")




def get_selected_date():
    selected_date = cal.get_date()
    valuation_date = datetime.strptime(selected_date, "%d-%m-%Y").date()
    valuation_date = pd.Timestamp(valuation_date)  # Convert to pd.Timestamp
    formatted_date = valuation_date.strftime("%d-%b-%Y")
    print(f"\nValuation Date is: {formatted_date}")
    root.destroy()  
    input_dataset = load_input_file()
    if input_dataset is not None:
        failed_checks = perform_data_checks(input_dataset, valuation_date)
        print("\n\n\t\t ==>> Data Validation Process Completed ! <<== \n")
        save_failed_records_to_csv(failed_checks, input_dataset)
        response = messagebox.askyesno("Separate CSV Files", "Do you want separate CSV files for each UIN?")
        if response:
            separate_csv_files_by_uin(input_dataset)
    print("\n\nProcess Completed !")

# Create Object
root = Tk()

# Set geometry
root.geometry("600x400")
root.title("Date Selection")

# Add Calendar
cal_frame = Frame(root)
cal_frame.pack(pady=20)

cal = Calendar(cal_frame, selectmode='day', year=2024, month=3, day=31, date_pattern="dd-mm-yyyy")
cal.pack(pady=10)
cal_title = Label(cal_frame, text="Select Valuation Date (dd-mm-yyyy)", font=("Helvetica", 12))
cal_title.pack(pady=5)

# Add Button and Label
frame = Frame(root)
frame.pack(pady=20)

Button(frame, text="Get Date", command=get_selected_date).pack(side=LEFT, padx=10)

date = Label(root, text="")
date.pack(pady=20)

# Execute Tkinter
root.mainloop()

