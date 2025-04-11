import pandas as pd
import numpy as np
import re

def detect_column_types(df):
    """
    Intelligently detect column types and categorize them
    """
    column_types = {
        'datetime': [],
        'geographic': {
            'latitude': [],
            'longitude': [],
            'location': []
        },
        'numeric': {
            'continuous': [],
            'discrete': [],
            'percentage': [],
            'monetary': []
        },
        'categorical': {
            'nominal': [],
            'ordinal': [],
            'binary': []
        },
        'text': [],
        'id': []
    }
    
    # Regular expressions for detection
    lat_patterns = r'lat|latitude|^lat$|^latitude$'
    lon_patterns = r'lon|longitude|^lng$|^long$'
    money_patterns = r'price|cost|revenue|sales|income|expense|payment|amount|^[$€£¥]'
    date_patterns = r'date|time|year|month|day'
    id_patterns = r'id$|_id$|^id_|code$|number$'
    
    for col in df.columns:
        col_lower = col.lower()
        sample_values = df[col].dropna().head(100)
        
        # Check if column is datetime
        if df[col].dtype == 'datetime64[ns]' or re.search(date_patterns, col_lower):
            try:
                pd.to_datetime(sample_values)
                column_types['datetime'].append(col)
                continue
            except:
                pass
        
        # Check for geographic coordinates
        if re.search(lat_patterns, col_lower) and df[col].dtype in ['float64', 'int64']:
            if df[col].between(-90, 90).all():
                column_types['geographic']['latitude'].append(col)
                continue
                
        if re.search(lon_patterns, col_lower) and df[col].dtype in ['float64', 'int64']:
            if df[col].between(-180, 180).all():
                column_types['geographic']['longitude'].append(col)
                continue
        
        # Numeric types
        if df[col].dtype in ['int64', 'float64']:
            # Check if it's a percentage
            if df[col].between(0, 100).all() and '%' in col_lower:
                column_types['numeric']['percentage'].append(col)
            # Check if it's monetary
            elif re.search(money_patterns, col_lower):
                column_types['numeric']['monetary'].append(col)
            # Check if it's discrete (mostly whole numbers)
            elif df[col].dropna().apply(lambda x: float(x).is_integer()).all():
                column_types['numeric']['discrete'].append(col)
            else:
                column_types['numeric']['continuous'].append(col)
            continue
        
        # Categorical types
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            unique_vals = df[col].nunique()
            if unique_vals == 2:
                column_types['categorical']['binary'].append(col)
            elif unique_vals <= len(df) * 0.05:  # If unique values are less than 5% of total rows
                if re.search(id_patterns, col_lower):
                    column_types['id'].append(col)
                else:
                    column_types['categorical']['nominal'].append(col)
            else:
                column_types['text'].append(col)
            continue
    
    return column_types

def analyze_data(df):
    """
    Perform smart, context-aware analysis on the dataset
    """
    results = {}
    
    # Basic info
    results['total_rows'] = len(df)
    results['total_columns'] = len(df.columns)
    
    # Smart column type detection
    column_types = detect_column_types(df)
    results['column_types'] = column_types
    
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
    
    # Context-aware numerical summary
    numeric_summaries = {}
    
    # Regular numeric columns
    regular_numeric = column_types['numeric']['continuous'] + column_types['numeric']['discrete']
    if regular_numeric:
        numeric_summaries['regular'] = df[regular_numeric].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
    
    # Percentage columns
    if column_types['numeric']['percentage']:
        numeric_summaries['percentage'] = df[column_types['numeric']['percentage']].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
    
    # Monetary columns
    if column_types['numeric']['monetary']:
        numeric_summaries['monetary'] = df[column_types['numeric']['monetary']].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
    
    # Geographic columns
    if column_types['geographic']['latitude'] or column_types['geographic']['longitude']:
        geo_cols = column_types['geographic']['latitude'] + column_types['geographic']['longitude']
        numeric_summaries['geographic'] = df[geo_cols].agg([
            'count', 'min', 'max'
        ]).round(4)  # More precision for coordinates
    
    results['numeric_summaries'] = numeric_summaries
    
    # Categorical analysis
    categorical_summaries = {}
    for cat_type, cols in column_types['categorical'].items():
        if cols:
            summaries = {}
            for col in cols:
                value_counts = df[col].value_counts()
                summaries[col] = {
                    'unique_values': len(value_counts),
                    'top_5_values': value_counts.head().to_dict()
                }
            categorical_summaries[cat_type] = summaries
    
    results['categorical_summaries'] = categorical_summaries
    
    return results
