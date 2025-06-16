from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import re
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Matplotlib
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'Uploads'  # Folder to save CSV files
app.config['ALLOWED_EXTENSIONS'] = {'csv'}  # Only allow CSV files

# Function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to sanitize CSV data
def sanitize_csv_data(df):
    for col in df.columns:
        if df[col].dtype == object:  # Check only string columns
            df[col] = df[col].apply(lambda x: re.sub(r'^[=+-]', '', str(x)) if pd.notnull(x) else x)
    return df

# Main route
@app.route('/', methods=['GET', 'POST'])
def index():
    data = None
    filename = None
    plot_url = None
    
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return render_template('index.html', error="No file uploaded.", data=None, filename=None)
        
        file = request.files['file']
        
        # Check if the file has a name
        if file.filename == '':
            return render_template('index.html', error="No file selected.", data=None, filename=None)
        
        # Check if the file is allowed
        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            try:
                # Read the CSV
                df = pd.read_csv(filepath)
                
                # Sanitize the data
                df = sanitize_csv_data(df)
                
                # Convert data to dictionary
                data = df.to_dict(orient='records')
                
                # Generate plot for numeric columns
                fig, ax = plt.subplots(figsize=(8, 5))
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                if numeric_cols.empty:
                    return render_template('index.html', error="No numeric columns found in the CSV.", data=data, filename=file.filename)
                
                for column in numeric_cols:
                    ax.plot(df[column], label=column)
                ax.set_title(f"CSV Data Plot: {file.filename}")
                ax.set_xlabel("Index")
                ax.set_ylabel("Values")
                ax.legend()
                
                # Save plot as an in-memory image
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
                plt.close(fig)  # Close figure to free memory
                
                return render_template('index.html', data=data, filename=file.filename, plot_url=plot_url)
            
            except Exception as e:
                return render_template('index.html', error=f"Error processing the CSV: {str(e)}", data=None, filename=None)
        
        else:
            return render_template('index.html', error="Invalid file type. Only CSV files are allowed.", data=None, filename=None)
    
    return render_template('index.html', data=None, filename=None)

if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)