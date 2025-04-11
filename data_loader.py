import pandas as pd
from io import StringIO
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

def geocode_location(location, geolocator):
    """
    Convert a location string to latitude and longitude
    """
    try:
        location_data = geolocator.geocode(location)
        if location_data:
            return pd.Series({'latitude': location_data.latitude, 'longitude': location_data.longitude})
        return pd.Series({'latitude': None, 'longitude': None})
    except GeocoderTimedOut:
        time.sleep(1)  # Wait for 1 second before retrying
        try:
            location_data = geolocator.geocode(location)
            if location_data:
                return pd.Series({'latitude': location_data.latitude, 'longitude': location_data.longitude})
        except:
            pass
        return pd.Series({'latitude': None, 'longitude': None})
    except:
        return pd.Series({'latitude': None, 'longitude': None})

def add_geocoding(df, location_column):
    """
    Add latitude and longitude columns based on location names
    """
    geolocator = Nominatim(user_agent="my_data_analyzer")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Get coordinates for each location
    total_rows = len(df)
    coordinates_list = []
    
    for idx, location in enumerate(df[location_column]):
        # Update progress
        progress = (idx + 1) / total_rows
        progress_bar.progress(progress)
        status_text.text(f"Geocoding: {idx+1}/{total_rows} locations...")
        
        if pd.isna(location):
            coordinates_list.append(pd.Series({'latitude': None, 'longitude': None}))
        else:
            coordinates_list.append(geocode_location(str(location), geolocator))
        
        # Add small delay to respect rate limits
        time.sleep(0.1)
    
    # Convert results to DataFrame
    coordinates_df = pd.DataFrame(coordinates_list)
    
    # Add new columns to original DataFrame
    df['latitude'] = coordinates_df['latitude']
    df['longitude'] = coordinates_df['longitude']
    
    # Clear progress bar and status
    progress_bar.empty()
    status_text.empty()
    
    return df

def load_data(uploaded_file):
    """
    Load data from various file formats into a pandas DataFrame
    Supports CSV, Excel (multiple sheets), and JSON files
    """
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_type == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_type == 'xlsx':
            # Read Excel info first
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            
            if len(sheet_names) > 1:
                # If multiple sheets exist, let user select which sheet to use
                selected_sheet = st.selectbox(
                    "Select the sheet to analyze:",
                    options=sheet_names,
                    index=len(sheet_names)-1  # Default to last sheet
                )
                df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            else:
                # If only one sheet, read it directly
                df = pd.read_excel(uploaded_file)
        elif file_type == 'json':
            df = pd.read_json(uploaded_file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Check for location columns that might need geocoding
        text_columns = df.select_dtypes(include=['object']).columns
        potential_location_columns = [
            col for col in text_columns
            if any(loc_term in col.lower() 
                  for loc_term in ['location', 'city', 'country', 'state', 'address', 'place'])
        ]
        
        if potential_location_columns and 'latitude' not in df.columns and 'longitude' not in df.columns:
            st.write("📍 Location columns detected! Would you like to generate coordinates?")
            selected_location_column = st.selectbox(
                "Select the column containing location names:",
                options=potential_location_columns
            )
            
            if st.button("Generate Coordinates"):
                df = add_geocoding(df, selected_location_column)
                st.success(f"✅ Added latitude and longitude coordinates for {selected_location_column}")
        
        return df
    
    except Exception as e:
        raise Exception(f"Error loading file: {str(e)}")
