import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from data_analyzer import detect_column_types

def is_meaningful_numeric(series):
    """Check if a numeric column has meaningful variation"""
    if series.nunique() < 2:
        return False
    if series.std() == 0:
        return False
    # Check if it's not just an ID column
    if series.is_monotonic_increasing and series.diff().dropna().nunique() <= 1:
        return False
    return True

def get_important_correlations(df, numeric_cols, threshold=0.3):
    """Get correlations that are strong and meaningful"""
    if len(numeric_cols) < 2:
        return []
    
    corr_matrix = df[numeric_cols].corr()
    important_corrs = []
    
    for i in range(len(numeric_cols)):
        for j in range(i+1, len(numeric_cols)):
            corr_value = abs(corr_matrix.iloc[i, j])
            if corr_value > threshold:
                important_corrs.append({
                    'pair': (numeric_cols[i], numeric_cols[j]),
                    'correlation': corr_matrix.iloc[i, j]
                })
    
    return sorted(important_corrs, key=lambda x: abs(x['correlation']), reverse=True)

def get_meaningful_categories(series, max_categories=10):
    """Get categorical columns with a reasonable number of unique values"""
    unique_count = series.nunique()
    if 2 <= unique_count <= max_categories:
        # Check value distribution
        value_counts = series.value_counts()
        # Ensure no single value dominates (e.g., > 95% of data)
        if value_counts.iloc[0] / len(series) < 0.95:
            return True
    return False

def create_smart_visualizations(df):
    """Create intelligent, focused visualizations based on data characteristics with user selection"""
    column_types = detect_column_types(df)
    
    # Create visualization options based on available data
    viz_options = []
    
    if column_types['geographic']['latitude'] and column_types['geographic']['longitude']:
        viz_options.append("Geographic Maps")
        
    if column_types['datetime']:
        viz_options.append("Time Series")
    
    numeric_cols = []
    for col_type in ['continuous', 'discrete', 'monetary', 'percentage']:
        numeric_cols.extend(column_types['numeric'][col_type])
    meaningful_numerics = [col for col in numeric_cols if is_meaningful_numeric(df[col])]
    
    if meaningful_numerics:
        viz_options.append("Key Metrics")
        if len(meaningful_numerics) >= 2:
            viz_options.append("Correlations")
    
    categorical_cols = []
    for cat_type in ['nominal', 'binary']:
        for col in column_types['categorical'][cat_type]:
            if get_meaningful_categories(df[col]):
                categorical_cols.append(col)
    
    if categorical_cols:
        viz_options.append("Category Analysis")
    
    if column_types['numeric']['monetary']:
        viz_options.append("Financial Analysis")
    
    # Selection panel
    st.sidebar.header("📊 Visualization Options")
    selected_viz = st.sidebar.multiselect(
        "Select visualizations to display:",
        viz_options,
        help="Choose which types of visualizations you want to see"
    )
    
    # Display selected visualizations
    for viz_type in selected_viz:
        if viz_type == "Geographic Maps":
            create_geographic_viz(df, 
                                column_types['geographic']['latitude'],
                                column_types['geographic']['longitude'])
        
        elif viz_type == "Time Series":
            create_time_series_viz(df, column_types['datetime'])
        
        elif viz_type == "Key Metrics":
            st.subheader("📊 Key Metrics")
            # Show distribution for most varied numeric columns (top 3)
            variances = {col: df[col].std() for col in meaningful_numerics}
            top_varied = sorted(variances.items(), key=lambda x: x[1], reverse=True)[:3]
            
            metric_col = st.selectbox("Select metric to visualize:", 
                                    [col for col, _ in top_varied])
            
            if metric_col:
                fig = px.histogram(
                    df, 
                    x=metric_col,
                    title=f"Distribution of {metric_col}",
                    marginal="box"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Correlations":
            st.subheader("🔗 Key Relationships")
            important_corrs = get_important_correlations(df, meaningful_numerics)
            if important_corrs:
                corr_pairs = [f"{pair['pair'][0]} vs {pair['pair'][1]}" 
                             for pair in important_corrs]
                selected_pair = st.selectbox("Select correlation to visualize:", 
                                           corr_pairs)
                
                if selected_pair:
                    idx = corr_pairs.index(selected_pair)
                    col1, col2 = important_corrs[idx]['pair']
                    fig = px.scatter(
                        df,
                        x=col1,
                        y=col2,
                        title=f"{col1} vs {col2} (correlation: {important_corrs[idx]['correlation']:.2f})",
                        trendline="ols"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Category Analysis":
            st.subheader("📊 Category Analysis")
            selected_cat = st.selectbox("Select category to analyze:", 
                                      categorical_cols)
            
            if selected_cat:
                value_counts = df[selected_cat].value_counts()
                fig = px.pie(
                    values=value_counts.values,
                    names=value_counts.index,
                    title=f"Distribution of {selected_cat}"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Financial Analysis":
            create_monetary_viz(df, column_types['numeric']['monetary'])

def create_geographic_viz(df, lat_cols, lon_cols):
    """Create geographic visualizations"""
    if len(lat_cols) > 0 and len(lon_cols) > 0:
        st.subheader("🗺️ Geographic Distribution")
        
        lat_col = lat_cols[0]
        lon_col = lon_cols[0]
        
        # Find a meaningful column for color coding
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        meaningful_cols = [col for col in numeric_cols 
                         if col not in [lat_col, lon_col] 
                         and is_meaningful_numeric(df[col])]
        
        color_col = None
        if meaningful_cols:
            color_col = st.selectbox("Color points by", ['None'] + meaningful_cols)
        
        fig = px.scatter_mapbox(
            df,
            lat=lat_col,
            lon=lon_col,
            color=color_col if color_col != 'None' else None,
            zoom=1
        )
        
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":30,"l":0,"b":0},
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show clustering only if there are enough distinct points
        distinct_locations = df.groupby([lat_col, lon_col]).size().reset_index()
        if len(distinct_locations) > 5:
            show_clusters = st.checkbox("Show location clusters")
            if show_clusters:
                cluster_fig = px.density_mapbox(
                    df,
                    lat=lat_col,
                    lon=lon_col,
                    zoom=1,
                    title="Location Density"
                )
                cluster_fig.update_layout(
                    mapbox_style="carto-positron",
                    margin={"r":0,"t":30,"l":0,"b":0}
                )
                st.plotly_chart(cluster_fig, use_container_width=True)

def create_time_series_viz(df, datetime_cols):
    """Create time series visualizations"""
    if datetime_cols:
        st.subheader("📈 Time Series Analysis")
        date_col = datetime_cols[0]
        
        # Convert to datetime
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Find meaningful numeric columns for time series
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        meaningful_cols = [col for col in numeric_cols if is_meaningful_numeric(df[col])]
        
        if meaningful_cols:
            # Select top 2 most varied columns
            variances = {col: df[col].std() for col in meaningful_cols}
            top_varied = sorted(variances.items(), key=lambda x: x[1], reverse=True)[:2]
            
            for col, _ in top_varied:
                # Resample by appropriate time period
                time_range = df[date_col].max() - df[date_col].min()
                if time_range.days > 365:
                    freq = 'M'  # Monthly for > 1 year
                elif time_range.days > 30:
                    freq = 'W'  # Weekly for > 1 month
                else:
                    freq = 'D'  # Daily for <= 1 month
                
                daily_data = df.set_index(date_col)[col].resample(freq).mean()
                
                fig = px.line(
                    daily_data,
                    title=f"Trend of {col} over Time"
                )
                st.plotly_chart(fig, use_container_width=True)

def create_monetary_viz(df, monetary_cols):
    """Create comprehensive visualizations for monetary data"""
    if monetary_cols:
        st.subheader("💰 Financial Analysis")
        
        # Select financial metric
        selected_col = st.selectbox("Select financial metric:", monetary_cols)
        
        # Select visualization type
        viz_type = st.radio(
            "Choose visualization type:",
            ["Distribution Analysis", "Trend Analysis", "Summary Statistics"]
        )
        
        if viz_type == "Distribution Analysis":
            col1, col2 = st.columns(2)
            
            with col1:
                # Box plot with violin
                fig_box = go.Figure()
                fig_box.add_trace(go.Box(
                    y=df[selected_col],
                    name="Box Plot",
                    boxpoints="outliers",
                    marker_color="indianred"
                ))
                fig_box.add_trace(go.Violin(
                    y=df[selected_col],
                    name="Violin",
                    side="positive",
                    line_color="lightseagreen"
                ))
                fig_box.update_layout(
                    title=f"Distribution of {selected_col}",
                    showlegend=True
                )
                st.plotly_chart(fig_box, use_container_width=True)
            
            with col2:
                # Histogram with KDE
                fig_hist = ff.create_distplot(
                    [df[selected_col].dropna()],
                    [selected_col],
                    show_rug=False
                )
                fig_hist.update_layout(title=f"Density Distribution of {selected_col}")
                st.plotly_chart(fig_hist, use_container_width=True)
        
        elif viz_type == "Trend Analysis":
            # Check if we have datetime columns
            datetime_cols = df.select_dtypes(include=['datetime64']).columns
            if len(datetime_cols) > 0:
                date_col = st.selectbox("Select date column for trend:", datetime_cols)
                
                # Aggregation options
                agg_period = st.selectbox(
                    "Select aggregation period:",
                    ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
                )
                
                agg_func = st.selectbox(
                    "Select aggregation function:",
                    ["Mean", "Sum", "Median", "Min", "Max"]
                )
                
                # Create aggregation mapping
                period_map = {
                    "Daily": "D",
                    "Weekly": "W",
                    "Monthly": "M",
                    "Quarterly": "Q",
                    "Yearly": "Y"
                }
                
                func_map = {
                    "Mean": "mean",
                    "Sum": "sum",
                    "Median": "median",
                    "Min": "min",
                    "Max": "max"
                }
                
                # Aggregate data
                df_agg = df.set_index(date_col)[selected_col].resample(
                    period_map[agg_period]
                ).agg(func_map[agg_func])
                
                # Create trend plot
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=df_agg.index,
                    y=df_agg.values,
                    mode='lines+markers',
                    name=f'{agg_period} {agg_func}'
                ))
                
                # Add trend line
                z = np.polyfit(range(len(df_agg)), df_agg.values, 1)
                p = np.poly1d(z)
                fig_trend.add_trace(go.Scatter(
                    x=df_agg.index,
                    y=p(range(len(df_agg))),
                    mode='lines',
                    name='Trend Line',
                    line=dict(dash='dash')
                ))
                
                fig_trend.update_layout(
                    title=f"{agg_period} {agg_func} of {selected_col}",
                    xaxis_title="Date",
                    yaxis_title=selected_col
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.warning("No datetime columns available for trend analysis")
        
        else:  # Summary Statistics
            col1, col2 = st.columns(2)
            
            with col1:
                stats = df[selected_col].describe()
                st.write("📊 Basic Statistics:")
                st.dataframe(stats)
            
            with col2:
                # Additional financial metrics
                metrics = pd.Series({
                    "Total": df[selected_col].sum(),
                    "Average": df[selected_col].mean(),
                    "Median": df[selected_col].median(),
                    "Std Dev": df[selected_col].std(),
                    "Skewness": df[selected_col].skew(),
                    "Kurtosis": df[selected_col].kurtosis(),
                    "Range": df[selected_col].max() - df[selected_col].min(),
                    "IQR": df[selected_col].quantile(0.75) - df[selected_col].quantile(0.25)
                })
                
                st.write("📈 Financial Metrics:")
                st.dataframe(metrics)
        
        # Show outlier analysis
        show_outliers = st.checkbox("Show Outlier Analysis")
        if show_outliers:
            Q1 = df[selected_col].quantile(0.25)
            Q3 = df[selected_col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[
                (df[selected_col] < (Q1 - 1.5 * IQR)) | 
                (df[selected_col] > (Q3 + 1.5 * IQR))
            ][selected_col]
            
            if len(outliers) > 0:
                st.write(f"Found {len(outliers)} outliers in {selected_col}:")
                fig_outliers = go.Figure()
                fig_outliers.add_trace(go.Box(
                    y=df[selected_col],
                    name="Distribution",
                    boxpoints="outliers",
                    marker=dict(color="red", size=8)
                ))
                fig_outliers.update_layout(title="Outlier Analysis")
                st.plotly_chart(fig_outliers, use_container_width=True)
                
                st.write("Outlier Statistics:")
                st.dataframe(outliers.describe())
            else:
                st.write("No significant outliers found.")

def create_categorical_viz(df, categorical_cols):
    """Create visualizations for categorical data"""
    if categorical_cols:
        st.subheader("Categorical Analysis")
        selected_col = st.selectbox("Select category", categorical_cols)
        
        # Value counts
        value_counts = df[selected_col].value_counts()
        
        # Bar chart
        fig = px.bar(
            x=value_counts.index,
            y=value_counts.values,
            title=f"Distribution of {selected_col}"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Pie chart if fewer than 10 categories
        if len(value_counts) <= 10:
            fig = px.pie(
                values=value_counts.values,
                names=value_counts.index,
                title=f"Proportion of {selected_col}"
            )
            st.plotly_chart(fig, use_container_width=True)

def create_correlation_viz(df, numeric_cols):
    """Create correlation visualization for numeric columns"""
    if len(numeric_cols) >= 2:
        st.subheader("Correlation Analysis")
        
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            title="Correlation Matrix",
            color_continuous_scale="RdBu",
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show strongest correlations
        correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                correlations.append({
                    'Variables': f"{numeric_cols[i]} vs {numeric_cols[j]}",
                    'Correlation': corr_matrix.iloc[i, j]
                })
        
        if correlations:
            df_corr = pd.DataFrame(correlations)
            df_corr = df_corr.sort_values('Correlation', key=abs, ascending=False)
            st.write("Top Correlations:")
            st.dataframe(df_corr)

def create_visualizations(df):
    """
    Create smart, context-aware visualizations based on the dataset
    """
    # Get column types from data_analyzer
    column_types = detect_column_types(df)
    
    # Geographic visualizations
    create_geographic_viz(
        df,
        column_types['geographic']['latitude'],
        column_types['geographic']['longitude']
    )
    
    # Time series visualizations
    create_time_series_viz(df, column_types['datetime'])
    
    # Monetary visualizations
    create_monetary_viz(df, column_types['numeric']['monetary'])
    
    # Regular numeric visualizations
    numeric_cols = (
        column_types['numeric']['continuous'] +
        column_types['numeric']['discrete'] +
        column_types['numeric']['percentage']
    )
    if numeric_cols:
        st.subheader("Numeric Analysis")
        selected_col = st.selectbox("Select numeric column", numeric_cols)
        
        # Distribution plot
        fig = px.histogram(
            df,
            x=selected_col,
            title=f"Distribution of {selected_col}",
            marginal="box"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Categorical visualizations
    categorical_cols = (
        column_types['categorical']['nominal'] +
        column_types['categorical']['binary']
    )
    create_categorical_viz(df, categorical_cols)
    
    # Correlation analysis for all numeric columns
    create_correlation_viz(df, numeric_cols)
