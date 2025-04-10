import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import os

# Configure Streamlit page layout
st.set_page_config(layout="wide")
st.title("AI Chatbot: Data Analysis and Chart Generator")
st.write("Upload your data file (CSV or Excel) and generate interactive charts using Python and R.")

# File uploader widget
uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Read the file using Pandas
    try:
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
        else:
            data = pd.read_excel(uploaded_file)
        st.subheader("Data Preview")
        st.dataframe(data.head())
    except Exception as e:
        st.error(f"Error reading file: {e}")
    
    # Show data summary statistics
    st.subheader("Data Summary")
    st.write(data.describe())
    
    # Button to generate a chart using Python
    if st.button("Generate Python Chart"):
        if "category" in data.columns and "value" in data.columns:
            fig, ax = plt.subplots(figsize=(8, 4))
            # Group by the 'category' column and sum the 'value' column
            summary = data.groupby("category")["value"].sum()
            summary.plot(kind="bar", ax=ax)
            ax.set_title("Python Generated Chart")
            ax.set_xlabel("Category")
            ax.set_ylabel("Sum of Value")
            st.pyplot(fig)
        else:
            st.warning("The data does not contain the required columns: 'category' and 'value'.")
    
    # Button to generate a chart using R
    if st.button("Generate R Chart"):
        # Create a temporary folder if it does not exist
        temp_folder = "temp"
        os.makedirs(temp_folder, exist_ok=True)
        
        # Save the uploaded file temporarily for processing by the R script
        file_path = os.path.join(temp_folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Define the output path for the R-generated chart image
        r_chart_path = os.path.join(temp_folder, "r_chart.png")
        
        # Call the R script using subprocess
        try:
            subprocess.run(["Rscript", "generate_chart.R", file_path, r_chart_path], check=True)
            st.image(r_chart_path, caption="R Generated Chart", use_column_width=True)
        except subprocess.CalledProcessError as e:
            st.error("An error occurred while generating the R chart.")
