import os.path
import sys
import pandas as pd
import json  
from datetime import datetime
from dateutil import relativedelta
import tkinter as tk
from tkinter import filedialog
import warnings
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

today = datetime.today()

root = tk.Tk()
root.withdraw()  

file_path = filedialog.askopenfilename(title="Product Master Selection",filetypes=[("CSV files", "*.csv")])

if file_path:
    products = pd.read_csv(file_path).to_dict(orient='records')
    print("\nProduct master file loaded successfully.\n")
else:
    print("\nNo product master file selected.\n")


input_path = filedialog.askopenfilename(title ="Input File Selection",filetypes=[("CSV files", "*.csv")])
if input_path:
    input_dataset = pd.read_csv(input_path)
    print("\nInput filepath loaded successfully.\n")
else:
    print("\nNo Input file selected.\n")

output_report_path =  "Reserve_Calculation_" + today.strftime("%d-%b-%Y") + ".csv"

inputs = {
    'UIN' : 'N001',
    'Current_Product_Number':1,
    'Product_name':'',

    # Model Points
    'ph_entry_age':35,
    'ph_sex':'F',
    'pt_months':17,
    'ppt_months':1,
    'SA':50000,
    'Premium':199,
    'premium_frequency':'Annual',
    'Prem_fq':1,
    'profit_margin':0.12,
    'Area':'Avenue',
    'Product_Type':'Pure Protection',
    'PH_Effective_Date':'23-May-23',
    'maturity_date':'13-Nov-24',
    'policy_no':149,
    'status' :'inf',

    # Assumptions - Best Estimate
    'FixedExp_BE':200,
    'RenExp_BE':50,
    'VarExp_Initial_BE':0.10,
    'LapseAssump_BE':1,
    'MortAssump_BE':2.5,
    'MorbAssump_BE':1,
    'InterestAssump_RFR':0.01,
    'ExpInflation':0.005,
    'sh_tax':0.3,
    'FY_Commission':0.3,
    'Ren_Commission':0.05,
    'Claim_expense_fixed_BE':50,

    # Benifits
    'HasDeathBenefit':1,
    'HasMorbidityBenefit':0,
    'HasSurrenderBenefit':0,
    'HasSurvivalBenefit':0,
    'HasMaturityBenefit':0,

    # Decrement Tables
    'Mort_table_no':'Mortality_table_No_2',
    'Morb_table_no':'Morbidity_Table_No_1',
    'Lapse_table_no':'Lapse_Table_No_1',

    #Assumptions - Rerserving
    'MAD_FLAG':1,
    'FixedExp_Val':200,
    'RenExp_Val':55,
    'Claim_expense_fixed_Val':55,
    'LapseAssump_Val':1.2,
    'MortAssump_Val':2.7355289539,
    'MorbAssump_Val':1.10,
    'Expense_Val':1.10,
    'InterestAssump_BE':0.075,
    'InterestAssump_Val':0.0645,
    'ExpInflation_Trad':0.07,
    'ExpInflation_Val':0.077,
    'Res_Sol_Factor':0.045,
    'SAR_Sol_Factor':0.00045,
    'SolMar_Req_Reg':1.5,
    'rdr':0.1,
    'Rdr_monthly':0.008,
    'Reserving':0.01
}

def ValueMatch(decrement_arry,ff_arry,reserve_arry):
    decrement_df = pd.DataFrame(decrement_arry)
    ff_df = pd.DataFrame(ff_arry)
    reserve_df = pd.DataFrame(reserve_arry)

    combined_df = pd.concat([decrement_df, ff_df, reserve_df], axis=1)

    columns_to_store = ['Mortality_Rate', 'Morbidity_Rate', 
                        'Lives_at_end','reserves', 'upr',
                        'reserves_per_policy', 'upr_per_policy', 'final_reserve']

    # columns_to_store = ['reserves', 'upr','reserves_per_policy', 'upr_per_policy', 'final_reserve']
    
    combined_df[columns_to_store].to_csv("Value_match_test.csv", index=False)

def calc_reserve(input):
    decrement_arry=[]
    ff_arry=[]
    reserve_arry=[]

    product = [x for x in products if x['uin'] == input['UIN']][0]

    mortality_obj = pd.read_csv(product['mortality_table_number'] +'.csv').to_dict(orient='records')
    morbidity_obj = pd.read_csv(product['morbidity_table_number'] +'.csv').to_dict(orient='records')
    lapse_obj = pd.read_csv(product['lapse_table_number'] +'.csv').to_dict(orient='records')

    inputs = {
        'UIN' : input['UIN'],
        'Current_Product_Number':input['Product No'],
        'Product_name':'',
        # Model Points
        'ph_entry_age':input['PH Entry Age'],
        'ph_sex':input['PH Gender'],
        'pt_months':input['Policy Term_Month'],
        'ppt_months':input['Premium Term_Month'],
        'SA':input['Sum Assured'],
        'Premium': input['Premium'],
        'premium_frequency':input['Premium Frequency'],
        'Prem_fq': 1 if input['Premium Frequency'] == "Annual" else 2 if input['Premium Frequency'] == "Half Yearly" else 4 if input["premium_frequency"] == "Quarterly" else 12 if input["premium_frequency"] == "Monthly" else 0,
        'profit_margin':product['profit'],
        'Area':input['Area'],
        'Product_Type':product['product_type'],
        'PH_Effective_Date': input['Coverage Effective date'],
        'maturity_date': input['maturity date'],
        'policy_no': input['Policy/CoI Number'],
        'Status' : input['Status'],

        # Assumptions - Best Estimate
        'FixedExp_BE':product['fixed_initial'],
        'RenExp_BE':product['fixed_renewal'],
        'VarExp_Initial_BE':product['initial_exp'],
        'LapseAssump_BE':product['lapse_rate'],
        'MortAssump_BE':product['mortality_rate'],
        'MorbAssump_BE':product['morbidity_rate'],
        'ExpInflation': product['expense_inflation_res'],
        'InterestAssump_RFR':product['reserving_int_rate'],
        'sh_tax':product['sh_tax_rate'],
        'FY_Commission':product['first_year_commission'],
        'Ren_Commission':product['renewal_commission'],
        'Claim_expense_fixed_BE':product['claim_expense_fixed'],

        # Benifits
        'HasDeathBenefit':product['has_death_benifit'],
        'HasMorbidityBenefit':product['has_morbidity_benifit'],
        'HasSurrenderBenefit':product['has_surrender_benefit'],
        'HasSurvivalBenefit':product['has_survival_benefit'],
        'HasMaturityBenefit':product['has_maturity_benefit'],

        # Decrement Tables
        'Mort_table_no':product['mortality_table_number'],
        'Morb_table_no':product['morbidity_table_number'],
        'Lapse_table_no':product['lapse_table_number'],

        #Assumptions - Rerserving
        'MAD_FLAG':product['mad_flag'],
        'FixedExp_Val': product['fixed_initial'],
        'RenExp_Val': 0,
        'Claim_expense_fixed_Val':55,
        'LapseAssump_Val': product['lapse_rate'] * product['lapse'] if product['mad_flag'] == 1 else product['lapse_rate'],
        'MortAssump_Val': product['mortality_rate'] * product['mortality']if product['mad_flag'] == 1 else product['mortality_rate'],
        'MorbAssump_Val': product['morbidity_rate'] * product['morbidity'] if product['mad_flag'] == 1 else product['morbidity_rate'],
        'Expense_Val':product['morbidity_rate'] * product['expense'] if product['mad_flag'] == 1 else product['morbidity_rate'],
        'InterestAssump_BE': product['pr_traditional'],
        'InterestAssump_Val': product['pr_traditional'] - product['reserving_int_rate'] if product['mad_flag'] == 1 else product['reserving_int_rate'],
        'ExpInflation_Trad': product['pr_traditional'] - product['expense_inflation_res'] if product['mad_flag'] == 1 else product['expense_inflation_res'],
        'ExpInflation_Val':0.077,
        'Res_Sol_Factor':0.045,
        'SAR_Sol_Factor':0.00045,
        'SolMar_Req_Reg':1.5,
        'rdr':0.1,
        'Rdr_monthly':0.008,
        'Reserving':0.01
    }
    inputs['RenExp_Val'] = product['fixed_renewal'] * inputs['Expense_Val'] if product['mad_flag'] == 1 else product['fixed_renewal']
    inputs['Claim_expense_fixed_Val'] = product['claim_expense_fixed'] * inputs['Expense_Val'] if product['mad_flag'] == 1 else product['claim_expense_fixed']
    inputs['ExpInflation_Val'] =  inputs['ExpInflation_Trad'] * inputs['Expense_Val']
    inputs['Res_Sol_Factor'] = product['sol_margin_res_factor'] * product['regulatory_req']
    inputs['SAR_Sol_Factor'] = product['sol_margin_sar_factor'] * product['regulatory_req']
    inputs['rdr'] = product['regulatory_req']
    inputs['Rdr_monthly'] = product['risk_discount_rate'],
    inputs['Reserving'] = ((1 + product['risk_discount_rate'])**(1/12)-1)
    decrement_item = {
        'Duration':1,
        'Month':1,
        'Year':1,
        'Age':35,
        'Mortality_Rate':0.0,
        'Morbidity_Rate':0.0,
        'Lapse_Rate':0.0,
        'Lives_start':0.0,
        'Mortality_year':0.0,
        'Morbidity_year':0.0,
        'Lapse_year':0.0,
        'Lives_at_end':0.0
        }
    ff_item = {
        'inflation_factor': 1,
        'intial_yield_rate':0,
        'premium_frequency':1
    }
    reserve_item = {
        'premium':0,
        'investment_income':0,
        'FY_commission':0,
        'initial_expense':0,
        'renewal_variable_exp':0,
        'renewal_fixed_exp':0,
        'death_payments':0,
        'morbidity_benifit':0,
        'surrender_payments':0,
        'survival_payments':0,
        'maturity_outgo':0,
        'net_cashflow':0,
        'reserves':0,
        'solvency_margin':0,
        'upr':0,
        'reserves_per_policy':0
    }

    for x in range(1, inputs['pt_months']+1):

        if decrement_item['Month'] == 12:
            decrement_item['Month'] = 1
            decrement_item['Year'] = decrement_item['Year'] + 1
        elif x != 1:
            decrement_item['Month']+= 1

        if (x > 1):
            if (decrement_item['Month'] == 1):
                ff_item['inflation_factor'] = ff_item['inflation_factor']*(1 + inputs['ExpInflation_Val'])
            if x > inputs['ppt_months']:
                ff_item['premium_frequency'] = 0
            else:
                ff_item['premium_frequency'] = inputs['Prem_Fq']*(1+(12/inputs['Prem_Fq'])*int(inputs['Prem_Fq']*(inputs['Month']-1)/12))
        decrement_item['Age'] = inputs['ph_entry_age']+ decrement_item['Year'] - 1

        mortality_rate_lookup = mortality_obj[decrement_item['Age']][inputs['ph_sex']]
        decrement_item['Mortality_Rate'] = (1-((1-mortality_rate_lookup)**(1/12)))*inputs['MortAssump_Val']*inputs['HasDeathBenefit']

        morbidity_rate_lookup = morbidity_obj[decrement_item['Age']][inputs['ph_sex']]
        decrement_item['Morbidity_Rate'] = (((1+morbidity_rate_lookup)**(1/12))-1)*inputs['MorbAssump_Val']*inputs['HasMorbidityBenefit']

        lapse_rate_lookup = lapse_obj[decrement_item['Year']][inputs['ph_sex']]
        decrement_item['Lapse_Rate'] = lapse_rate_lookup * inputs['LapseAssump_Val'] if x == 12 else 0
        decrement_item['Lives_start'] = 1 if decrement_item['Month'] == 1 and decrement_item['Year'] == 1 else decrement_item['Lives_at_end']
        decrement_item['Mortality_year'] = decrement_item['Mortality_Rate']*decrement_item['Lives_start']* (1- 0.5* decrement_item['Morbidity_Rate'])
        decrement_item['Morbidity_year'] = decrement_item['Morbidity_Rate']*decrement_item['Lives_start']* (1- 0.5* decrement_item['Mortality_Rate'])
        decrement_item['Lapse_year'] = decrement_item['Lapse_Rate']* (decrement_item['Lives_start']-decrement_item['Mortality_year']-decrement_item['Morbidity_year'])
        decrement_item['Lives_at_end'] = decrement_item['Lives_start']-decrement_item['Mortality_year']-decrement_item['Morbidity_year']-decrement_item['Lapse_year']
        decrement_arry.append(json.dumps(decrement_item))
        ff_item['intial_yield_rate'] = (1+inputs['InterestAssump_Val'])**(1/12)-1
        ff_arry.append(json.dumps(ff_item))

        reserve_item['premium'] = (inputs['Premium']*decrement_item['Lives_start']*ff_item['premium_frequency'])
        reserve_item['initial_expense'] = (reserve_item['premium']*(inputs['VarExp_Initial_BE'] if decrement_item['Year'] == 1 else 0 ) + (inputs['FixedExp_Val'] if x==1 else 0))
        reserve_item['renewal_variable_exp'] = (inputs['RenExp_BE']*reserve_item['premium']*inputs['Expense_Val'] if decrement_item['Year'] != 1 else 0)
        reserve_item['renewal_fixed_exp'] = (0 if x ==1 else (inputs['RenExp_Val']/12)*ff_item['inflation_factor']*decrement_item['Lives_start'])
        reserve_item['investment_income'] = ((reserve_item['premium']-reserve_item['renewal_variable_exp']-reserve_item['renewal_fixed_exp'])*ff_item['intial_yield_rate'])
        reserve_item['FY_commission'] = (reserve_item['premium']*(inputs['FY_Commission'] if decrement_item['Year'] == 1 else inputs['Ren_Commission']))
        reserve_item['death_payments'] = ((inputs['SA']+inputs['Claim_expense_fixed_Val'])*decrement_item['Mortality_year']*inputs['HasDeathBenefit'])
        reserve_item['morbidity_benifit'] = ((inputs['SA']+ inputs['Claim_expense_fixed_Val'])*decrement_item['Morbidity_year']*inputs['HasMorbidityBenefit'])
        reserve_item['surrender_payments'] = ((0.1+(decrement_item['Year']-1)*0.1)*decrement_item['Year']*inputs['Premium']*decrement_item['Lapse_year']*inputs['HasSurrenderBenefit'])
        reserve_item['survival_payments'] = 0
        reserve_item['maturity_outgo'] = ((inputs['SA']* decrement_item['Lives_at_end'] if x== inputs['pt_months'] else 0) * (0 if inputs['Product_Type'] =="Term" else 1) * inputs['HasMaturityBenefit'])
        reserve_item['net_cashflow'] = round(reserve_item['premium']+reserve_item['investment_income']-reserve_item['FY_commission']-reserve_item['initial_expense']-reserve_item['renewal_variable_exp']-reserve_item['renewal_fixed_exp']-reserve_item['death_payments']-reserve_item['morbidity_benifit']-reserve_item['surrender_payments']-reserve_item['survival_payments']-reserve_item['maturity_outgo'],3)
        reserve_item['upr'] = (inputs['Premium']*((inputs['pt_months']-x)/inputs['pt_months']) if inputs['ppt_months'] == 1 else ((12-inputs['Month'])/12))
        reserve_arry.append(json.dumps(reserve_item))

    ff_item['inflation_factor'] = 0
    ff_item['intial_yield_rate'] = 0
    ff_item['premium_frequency'] = 0
    ff_arry.append(json.dumps(ff_item))

    reserve_item = {
        'premium':0,
        'investment_income':0,
        'FY_commission':0,
        'initial_expense':0,
        'renewal_variable_exp':0,
        'renewal_fixed_exp':0,
        'death_payments':0,
        'morbidity_benifit':0,
        'surrender_payments':0,
        'survival_payments':0,
        'maturity_outgo':0,
        'net_cashflow':0,
        'reserves':0,
        'solvency_margin':0,
        'upr':0,
        'reserves_per_policy':0,
        'upr_per_policy':0,
        'final_reserve':0
    }
    reserve_arry.append(json.dumps(reserve_item))

    for x in reversed(range(0, inputs['pt_months'])):
        if isinstance(reserve_arry[x], str):
            reserve_arry[x] = json.loads(reserve_arry[x])
        if isinstance(reserve_arry[x+1], str):
            reserve_arry[x+1] = json.loads(reserve_arry[x+1])
        if isinstance(ff_arry[x], str):
            ff_arry[x] = json.loads(ff_arry[x])
        if isinstance(ff_arry[x+1], str):
            ff_arry[x+1] = json.loads(ff_arry[x+1])
        decrement_arry[x] = json.loads(decrement_arry[x])
        reserve_arry[x]['reserves'] = 0 if x == inputs['pt_months']+1 else (reserve_arry[x+1]['reserves'] - reserve_arry[x+1]['net_cashflow'])/(1+ff_arry[x+1]['intial_yield_rate'])
        reserve_arry[x]['solvency_margin']= (max(reserve_arry[x+1]['reserves'],reserve_arry[x+1]['upr'])*inputs['Res_Sol_Factor']+(inputs['SA']-max(reserve_arry[x+1]['reserves'],reserve_arry[x+1]['upr']))*inputs['SAR_Sol_Factor'])*inputs['SolMar_Req_Reg']
        reserve_arry[x]['reserves_per_policy']= reserve_arry[x]['reserves']/decrement_arry[x]['Lives_start']
        reserve_arry[x]['upr_per_policy']= 0 if decrement_arry[x]['Lives_start'] == 0 else reserve_arry[x]['upr']/decrement_arry[x]['Lives_start']
        reserve_arry[x]['final_reserve']= 0 if decrement_arry[x]['Lives_start'] == 0 else max(reserve_arry[x]['reserves'],reserve_arry[x]['upr'])/decrement_arry[x]['Lives_start']
            
    t_reserves =(reserve_arry[0]['reserves'] - reserve_arry[0]['net_cashflow'])/(1+ff_arry[0]['intial_yield_rate'])
    # print("\nreserves, net cashflow, initial yield rate : ",t_reserves, reserve_arry[0]['reserves'],reserve_arry[0]['net_cashflow'],ff_arry[0]['intial_yield_rate'],"\n")
    

    valuation_date_str = today.strftime("%d-%m-%Y")
    d1 = datetime.strptime(valuation_date_str, "%d-%m-%Y")
    d2 = datetime.strptime(inputs['maturity_date'], "%d-%m-%Y")
    d3 = datetime.strptime(inputs['PH_Effective_Date'], "%d-%m-%Y")
    
    datediff = relativedelta.relativedelta(d2, d1)
    outstanding_term_months = datediff.months + (datediff.years * 12)

    # datediff = relativedelta.relativedelta(d1, d3)
    policy_months = (d1.year - d3.year) * 12 + d1.month - d3.month
    if d1.day < d3.day: 
      policy_months -= 1
    final_reserve =  reserve_arry[policy_months]['reserves_per_policy']
    final_upr =  reserve_arry[policy_months]['upr_per_policy']
  
    #write the outstanding term months, reserve per policy and UPR per policy to csv file
    output_obj = {
          "UIN " : inputs['UIN'],
          "Policy No." : inputs['policy_no'],
          "Reserves Per Policy - GPV": final_reserve,
          "UPR Per Policy": final_upr,
          "Policy Term Months" : input['Policy Term_Month'],
          "Outstanding Term(Months)": outstanding_term_months,
          "Sum Assured" : inputs['SA'],
          "Premium" : inputs['Premium'],
          "Status" : inputs['Status']
    }

    # ValueMatch(decrement_arry,ff_arry,reserve_arry)

    df_out = pd.DataFrame(output_obj, index=[0])
    if os.path.exists(output_report_path):
        df_out.to_csv(output_report_path,mode='a', index=False, header=False)
    else:
        df_out.to_csv(output_report_path,mode='a', index=False, header=True)

def start_timer():
    return datetime.now()

def elapsed_time(start_time):
    return datetime.now() - start_time

def print_progress(current_index, total_records):
    progress_percentage = (current_index / total_records) * 100
    print(f"Progress: {current_index}/{total_records} records processed ({progress_percentage:.2f}%) - {datetime.now().time()}")

def process_data(input_dataset):
    start_time = start_timer()
    total_records = len(input_dataset)

    for index, input_data in input_dataset.iterrows():
        if input_data['Status'] != 'TR':
            calc_reserve(input_data)

        if index % 1000 == 0:  # Print progress every 1000 records
            print_progress(index, total_records)


    print("Processing completed.")
    print(f"Total time taken: {elapsed_time(start_time)}")

if __name__ == "__main__":
    # output_report_path = sys.argv[1]
    # input_dataset = pd.read_csv(input_path)

    process_data(input_dataset)






# 9004980090 - Vikas
    

    