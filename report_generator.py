import pandas as pd
from fpdf import FPDF
import tempfile
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Data Analysis Report', 0, 1, 'C')
        self.ln(10)

def generate_report(df, analysis_results):
    """
    Generate a PDF report with analysis results
    """
    pdf = PDF()
    pdf.add_page()
    
    # Dataset Overview
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Dataset Overview', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Total Rows: {analysis_results['total_rows']}", 0, 1)
    pdf.cell(0, 10, f"Total Columns: {analysis_results['total_columns']}", 0, 1)
    
    # Data Types
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Data Types', 0, 1)
    pdf.set_font('Arial', '', 12)
    for _, row in analysis_results['dtypes_df'].iterrows():
        pdf.cell(0, 10, f"{row['Column']}: {row['Data Type']}", 0, 1)
    
    # Missing Values
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Missing Values Analysis', 0, 1)
    pdf.set_font('Arial', '', 12)
    for _, row in analysis_results['missing_df'].iterrows():
        pdf.cell(0, 10, 
                f"{row['Column']}: {row['Missing Values']} ({row['Missing %']}%)", 
                0, 1)
    
    # Numerical Summary
    if not analysis_results['numeric_summary'].empty:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Numerical Summary', 0, 1)
        pdf.set_font('Arial', '', 12)
        for col in analysis_results['numeric_summary'].index:
            pdf.cell(0, 10, f"\n{col}:", 0, 1)
            stats = analysis_results['numeric_summary'].loc[col]
            for stat_name, value in stats.items():
                pdf.cell(0, 10, f"  {stat_name}: {value}", 0, 1)
    
    # Save to temporary file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'data_analysis_report.pdf')
    pdf.output(temp_path)
    
    return temp_path
