import pandas as pd
import numpy as np

def analyze_data(df):
    """
    Perform comprehensive analysis on the dataset
    """
    results = {}
    
    # Basic info
    results['total_rows'] = len(df)
    results['total_columns'] = len(df.columns)
    
    # Data types analysis
    dtypes = df.dtypes.reset_index()
    dtypes.columns = ['Column', 'Data Type']
    results['dtypes_df'] = dtypes
    
    # Missing values analysis
    missing = pd.DataFrame({
        'Column': df.columns,
        'Missing Values': df.isnull().sum(),
        'Missing %': (df.isnull().sum() / len(df) * 100).round(2)
    })
    results['missing_df'] = missing
    
    # Numerical summary
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        numeric_summary = df[numeric_cols].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
        
        # Calculate mode separately (may have multiple values)
        modes = df[numeric_cols].mode().iloc[0]
        numeric_summary.loc['mode'] = modes
        
        results['numeric_summary'] = numeric_summary.T
    else:
        results['numeric_summary'] = pd.DataFrame()
    
    return results
