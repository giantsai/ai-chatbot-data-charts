import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np

def create_visualizations(df):
    """
    Create various visualizations based on the dataset
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    # Distribution plots for numeric columns
    if len(numeric_cols) > 0:
        st.subheader("Distribution Plots")
        selected_num_col = st.selectbox("Select column for distribution plot", numeric_cols)
        
        # Histogram
        fig = px.histogram(df, x=selected_num_col, title=f"Distribution of {selected_num_col}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Box plot
        fig = px.box(df, y=selected_num_col, title=f"Box Plot of {selected_num_col}")
        st.plotly_chart(fig, use_container_width=True)
    
    # Bar charts for categorical columns
    if len(categorical_cols) > 0:
        st.subheader("Categorical Analysis")
        selected_cat_col = st.selectbox("Select column for category analysis", categorical_cols)
        
        value_counts = df[selected_cat_col].value_counts()
        fig = px.bar(
            x=value_counts.index, 
            y=value_counts.values,
            title=f"Value Counts for {selected_cat_col}"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Correlation heatmap for numeric columns
    if len(numeric_cols) >= 2:
        st.subheader("Correlation Heatmap")
        corr_matrix = df[numeric_cols].corr()
        fig = px.imshow(
            corr_matrix,
            title="Correlation Matrix",
            color_continuous_scale="RdBu"
        )
        st.plotly_chart(fig, use_container_width=True)
