from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)
DATA_FILE = 'data.csv'

def append_to_data_file(new_data):
    """Append new data to the existing data.csv file."""
    existing_data = pd.read_csv(DATA_FILE)
    combined_data = pd.concat([existing_data, new_data], ignore_index=True)
    combined_data.to_csv(DATA_FILE, index=False)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            return redirect(request.url)
        
        # Read the uploaded CSV file
        new_data = pd.read_csv(file)
        
        # If data.csv doesn't exist, create it
        if not os.path.exists(DATA_FILE):
            new_data.to_csv(DATA_FILE, index=False)
        else:
            # Append to existing data.csv
            append_to_data_file(new_data)
        
        return redirect(url_for('upload_file'))
    
    # Render the upload form and dropdown
    mph_codes = []
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            mph_codes = df['MPH Code'].unique().tolist()
        except pd.errors.EmptyDataError:
            # Handle the case where data.csv is empty
            mph_codes = []
    
    return render_template('upload.html', mph_codes=mph_codes)

@app.route('/filter', methods=['POST'])
def filter_data():
    selected_mph = request.form.get('mph_code')
    filtered_data = None
    mph_codes = []
    
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            filtered_data = df[df['MPH Code'] == selected_mph]
            mph_codes = df['MPH Code'].unique().tolist()
        except pd.errors.EmptyDataError:
            # Handle the case where data.csv is empty
            filtered_data = None
            mph_codes = []
    
    return render_template('upload.html', mph_codes=mph_codes, filtered_data=filtered_data.to_html(classes='data', header="true", index=False) if filtered_data is not None else None)

if __name__ == '__main__':
    app.run(debug=True)
