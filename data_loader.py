import pandas as pd
from io import StringIO

def load_data(uploaded_file):
    """
    Load data from various file formats into a pandas DataFrame
    """
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_type == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_type == 'xlsx':
            df = pd.read_excel(uploaded_file)
        elif file_type == 'json':
            df = pd.read_json(uploaded_file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return df
    
    except Exception as e:
        raise Exception(f"Error loading file: {str(e)}")
