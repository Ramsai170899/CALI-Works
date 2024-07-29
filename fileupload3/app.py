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

@app.route('/', methods=['GET'])
def index():
    success = request.args.get('success', default=False, type=bool)
    return render_template('upload.html', success=success)


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    
    if file.filename == '':
        return redirect(url_for('index'))
    
    # Read the uploaded CSV file
    new_data = pd.read_csv(file)
    
    # If data.csv doesn't exist, create it
    if not os.path.exists(DATA_FILE):
        new_data.to_csv(DATA_FILE, index=False)
    else:
        # Append to existing data.csv
        append_to_data_file(new_data)
    
    # Redirect to index with a success message
    return redirect(url_for('index', success=True))


@app.route('/view', methods=['GET'])
def view_data():
    mph_codes = []
    key_value_pairs = None  # Initialize key_value_pairs
    
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            mph_codes = df['MPH Code'].unique().tolist()
        except pd.errors.EmptyDataError:
            mph_codes = []
    
    return render_template('view.html', mph_codes=mph_codes, key_value_pairs=key_value_pairs)

@app.route('/filter', methods=['POST'])
def filter_data():
    selected_mph = request.form.get('mph_code')
    filtered_data = None
    
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            filtered_data = df[df['MPH Code'] == selected_mph]
        except pd.errors.EmptyDataError:
            filtered_data = None
    
    # Transform the filtered data into a key-value format
    key_value_pairs = None
    if filtered_data is not None and not filtered_data.empty:
        key_value_pairs = filtered_data.iloc[0].to_frame().reset_index()
        key_value_pairs.columns = ['Field', 'Value']  # Rename columns for clarity

    return render_template('view.html', mph_codes=df['MPH Code'].unique().tolist(), key_value_pairs=key_value_pairs)

if __name__ == '__main__':
    app.run(debug=True)
