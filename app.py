import streamlit as st
import pandas as pd
import numpy as np
from visualizer import create_smart_visualizations
import io
import openpyxl
import json
from pathlib import Path

# Try to import tabula, but don't fail if not available
try:
    import tabula
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Configure Streamlit page
st.set_page_config(
    page_title="Smart Data Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/ai-chatbot-data-charts',
        'Report a bug': "https://github.com/yourusername/ai-chatbot-data-charts/issues",
        'About': "# Smart Data Visualization\nAn intelligent data visualization tool that supports multiple file formats and creates insightful visualizations automatically."
    }
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .css-1v0mbdj.e115fcil1 {
        width: 100%;
    }
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache(allow_output_mutation=True)
def load_data(uploaded_file):
    """Load data from various file formats with caching"""
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_type == 'csv':
            # Try different encodings for CSV
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            for encoding in encodings:
                try:
                    return pd.read_csv(uploaded_file, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not read CSV with supported encodings")
            
        elif file_type in ['xls', 'xlsx']:
            return pd.read_excel(uploaded_file)
            
        elif file_type == 'json':
            return pd.read_json(uploaded_file)
            
        elif file_type == 'pdf':
            if not PDF_SUPPORT:
                raise ImportError(
                    "PDF support requires tabula-py. Install it with:\n"
                    "pip install tabula-py\n"
                    "Note: This also requires Java to be installed."
                )
            with st.spinner('Extracting tables from PDF...'):
                df_list = tabula.read_pdf(io.BytesIO(uploaded_file.read()), pages='all')
                if len(df_list) > 0:
                    return df_list
                else:
                    raise ValueError("No tables found in PDF")
                
        else:
            raise ValueError(f"Unsupported file format: {file_type}")
            
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("# 📊 Smart Data Visualization")
        st.markdown("---")
        st.markdown("""
        ### 📌 Quick Tips
        1. Upload any supported file format
        2. Select visualizations from the options
        3. Interact with the charts
        4. Download or share insights
        """)
        
        # Settings
        st.markdown("### ⚙️ Settings")
        theme = st.selectbox("Chart Theme", 
                           ["Default", "Dark", "Light", "Custom"],
                           help="Select the visual theme for charts")
        
        if theme == "Custom":
            primary_color = st.color_picker("Primary Color", "#1f77b4")
            secondary_color = st.color_picker("Secondary Color", "#ff7f0e")

    # Main content
    st.title("📊 Smart Data Visualization")
    
    # File upload section
    upload_col, example_col = st.columns([2, 1])
    
    with upload_col:
        st.write("Upload your dataset for intelligent visualization and analysis")
        file_types = ["csv", "xlsx", "xls", "json"]
        if PDF_SUPPORT:
            file_types.append("pdf")
            
        uploaded_file = st.file_uploader(
            "Upload your data file",
            type=file_types,
            help=f"Supported formats: {', '.join(file_types).upper()}",
            key="file_uploader"
        )

    with example_col:
        st.write("Or try sample data")
        sample_data = {
            "None": None,
            "Sales Data": pd.DataFrame({
                'Date': pd.date_range(start='2023-01-01', periods=100),
                'Sales': np.random.randint(100, 1000, 100),
                'Store': np.random.choice(['A', 'B', 'C'], 100),
                'Weekly_Sales': np.random.randint(1000, 5000, 100)
            }),
            "Geographic Data": pd.DataFrame({
                'City': ['New York', 'London', 'Tokyo', 'Paris', 'Sydney'],
                'Latitude': [40.7128, 51.5074, 35.6762, 48.8566, -33.8688],
                'Longitude': [-74.0060, -0.1278, 139.6503, 2.3522, 151.2093],
                'Population': np.random.randint(1000000, 10000000, 5)
            })
        }
            
        example_choice = st.selectbox("Select sample data", list(sample_data.keys()))
        if example_choice != "None" and sample_data[example_choice] is not None:
            df = sample_data[example_choice]
            
            # Create a temporary CSV file
            csv_data = df.to_csv(index=False).encode()
            uploaded_file = io.BytesIO(csv_data)
            uploaded_file.name = f"{example_choice.lower().replace(' ', '_')}.csv"

    if uploaded_file is not None:
        try:
            with st.spinner('Loading data...'):
                # Load data using the cached function
                data = load_data(uploaded_file)
                
                # Handle PDF with multiple tables
                if isinstance(data, list) and uploaded_file.name.endswith('.pdf'):
                    st.success(f"Found {len(data)} tables in the PDF")
                    selected_table = st.selectbox(
                        "Select table to analyze:",
                        range(len(data)),
                        format_func=lambda x: f"Table {x+1}"
                    )
                    df = data[selected_table]
                else:
                    df = data

            if df is not None and not df.empty:
                # Data preview in expander
                with st.expander("📋 Data Preview", expanded=True):
                    st.dataframe(
                        df.head(),
                        use_container_width=True,
                        height=200
                    )
                    
                    # Dataset info in columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows", df.shape[0])
                    with col2:
                        st.metric("Columns", df.shape[1])
                    with col3:
                        st.metric("Missing Values", df.isna().sum().sum())

                # Column details in expander
                with st.expander("📊 Column Details"):
                    col_stats = pd.DataFrame({
                        'Type': df.dtypes,
                        'Non-Null Count': df.count(),
                        'Null Count': df.isna().sum(),
                        'Unique Values': df.nunique()
                    })
                    st.dataframe(col_stats, use_container_width=True)

                # Create visualizations with error handling
                try:
                    create_smart_visualizations(df)
                except ModuleNotFoundError as e:
                    if 'statsmodels' in str(e):
                        st.error("""
                        ⚠️ Missing required package: statsmodels
                        
                        Please install it using:
                        ```bash
                        pip install statsmodels
                        ```
                        """)
                    else:
                        raise e
                
                # Export options
                st.markdown("---")
                export_col1, export_col2 = st.columns(2)
                with export_col1:
                    if st.button("📥 Download Processed Data"):
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "Download CSV",
                            csv,
                            "processed_data.csv",
                            "text/csv",
                            key='download-csv'
                        )
                with export_col2:
                    if st.button("📊 Download Visualizations"):
                        st.info("Feature coming soon!")
            
            else:
                st.error("The uploaded file contains no data")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            if isinstance(e, ImportError) and "tabula" in str(e):
                st.warning("""
                📌 To enable PDF support, please install tabula-py:
                ```bash
                pip install tabula-py
                ```
                Note: This also requires Java to be installed on your system.
                """)
    else:
        # Welcome message and features
        st.info("👋 Welcome! Please upload a file to begin the analysis.")
        
        # Features showcase
        st.markdown("### ✨ Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 📁 Supported Formats
            - CSV files
            - Excel workbooks
            - JSON data
            """ + ("- PDF tables\n" if PDF_SUPPORT else ""))
            
        with col2:
            st.markdown("""
            #### 📊 Smart Visualizations
            - Automatic chart selection
            - Interactive plots
            - Statistical insights
            - Trend analysis
            """)
            
        with col3:
            st.markdown("""
            #### 🛠️ Tools
            - Data cleaning
            - Missing value handling
            - Outlier detection
            - Export options
            """)

if __name__ == "__main__":
    main()
