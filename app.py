import streamlit as st
import pandas as pd
from data_loader import load_data
from data_analyzer import analyze_data
from visualizer import create_visualizations
from report_generator import generate_report

st.set_page_config(page_title="Data Analysis Dashboard", layout="wide")

def main():
    st.title("📊 Interactive Data Analysis Dashboard")
    st.write("Upload your dataset (CSV, XLSX, or JSON) for instant analysis")

    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=["csv", "xlsx", "json"],
        help="Upload your data file in CSV, Excel, or JSON format"
    )

    if uploaded_file is not None:
        # Load data
        try:
            df = load_data(uploaded_file)
            
            # Display data preview
            st.header("📋 Data Preview")
            st.dataframe(df.head(), use_container_width=True)
            
            # Data info and analysis
            st.header("📈 Data Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Dataset Info")
                analysis_results = analyze_data(df)
                st.write(f"Total Rows: {analysis_results['total_rows']}")
                st.write(f"Total Columns: {analysis_results['total_columns']}")
                
                st.subheader("Data Types")
                st.dataframe(analysis_results['dtypes_df'], use_container_width=True)
                
                st.subheader("Missing Values")
                st.dataframe(analysis_results['missing_df'], use_container_width=True)
            
            with col2:
                st.subheader("Numerical Summary")
                st.dataframe(analysis_results['numeric_summary'], use_container_width=True)
            
            # Visualizations
            st.header("🎨 Visualizations")
            create_visualizations(df)
            
            # Report Generation
            st.header("📑 Export Report")
            if st.button("Generate Report"):
                report_path = generate_report(df, analysis_results)
                with open(report_path, "rb") as f:
                    st.download_button(
                        "Download Report",
                        f,
                        file_name="data_analysis_report.pdf",
                        mime="application/pdf"
                    )
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
