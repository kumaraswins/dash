import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
# Configure page settings
st.set_page_config(
    page_title="Public Transport Analytics Dashboard",
    page_icon="🚍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .metric-card {
        padding: 15px;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
    }
    .metric-title {
        font-size: 14px;
        color: #555;
        font-weight: 500;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #222;
    }
    .header {
        margin-bottom: 20px;
    }
    .plot-container {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Load and prepare data
@st.cache_data
def load_data():
    # Read Excel file
    # Assuming the Excel file is named 'smart_city_dashboard_datewise_data.xlsx' and is in a 'data' subdirectory
    try:
        df = pd.read_excel("data/smart_city_dashboard_datewise_data.xlsx")
    except FileNotFoundError:
        st.error("Error: Data file not found. Please make sure 'smart_city_dashboard_datewise_data.xlsx' is in a 'data' subdirectory.")
        st.stop()

    # Convert date and time columns
    df['running_date'] = pd.to_datetime(df['running_date'], errors='coerce')
    # Drop rows with invalid dates
    df.dropna(subset=['running_date'], inplace=True)

    df['day_of_week'] = df['running_date'].dt.day_name()
    # Convert time columns, handling potential errors
    try:
        df['start_time'] = pd.to_datetime(df['start_time'].astype(str)).dt.time
        df['end_time'] = pd.to_datetime(df['end_time'].astype(str)).dt.time
    except Exception as e:
        st.warning(f"Could not convert time columns. Please check their format. Error: {e}")
        # Continue without time columns or handle as needed

    # Ensure numeric types and calculate metrics, handling potential errors
    numeric_cols = ['total_amount', 'travel_distance', 'total_count']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate Epkm only if travel_distance is not zero to avoid division by zero
    df['Epkm'] = df['total_amount'] / df['travel_distance']

    # Replace infinite values (division by zero) with 0
    df['Epkm'] = df['Epkm'].replace([np.inf, -np.inf], 0)

    # Replace NaN values (from division with NaN or other issues) with 0
    df['Epkm'] = df['Epkm'].fillna(0)

    # Round the final Epkm values
    df['Epkm'] = df['Epkm'].round(2)

    df['service_type'] = df['color_line']

    # Drop rows with NaN in critical numeric columns after coercion
    df.dropna(subset=numeric_cols + ['Epkm'], inplace=True)

    if df.empty:
        st.error("Error: No valid data remaining after processing. Please check your data file for correct formats.")
        st.stop()

    return df

# Load data
df = load_data()

# Dashboard Header
st.title("🚍 Public Transport Performance Dashboard")
st.markdown("""
<div style="margin-bottom: 30px;">
    Comprehensive analysis of passenger traffic, revenue, and operational efficiency
</div>
""", unsafe_allow_html=True)

# Filters Section
st.markdown("### Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    time_period = st.selectbox(
        "Time Period",
        ["Daily", "Weekly", "Monthly"],
        index=0
    )

with col2:
    # Use df['service_type'].unique() directly after loading data
    color_lines = df['service_type'].unique()
    color_filter = st.multiselect(
        "Service Type (Color Line)",
        options=color_lines,
        default=[] # Default to all selected
    )

with col3:
    day_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # Ensure only days present in the filtered data are selected by default
    present_days = df['day_of_week'].unique().tolist()
    day_filter = st.multiselect(
        "Day of Week",
        options=day_options,
        default=[] # Default to all present days
    )

with col4:
    # Use df['route_no'].unique() directly after loading data
    route_options = df['route_no'].unique()
    route_filter = st.multiselect(
        "Route",
        options=route_options,
        default=[] # Default to all selected
    )

# Apply filters - Modified logic to handle empty multiselects
# Start with a condition that includes all rows
filter_condition = pd.Series(True, index=df.index)

# Apply color filter if not empty
if color_filter:
    filter_condition = filter_condition & (df['service_type'].isin(color_filter))

# Apply day filter if not empty
if day_filter:
    filter_condition = filter_condition & (df['day_of_week'].isin(day_filter))

# Apply route filter if not empty
if route_filter:
    filter_condition = filter_condition & (df['route_no'].isin(route_filter))

# Apply the combined filter condition
filtered_df = df[filter_condition].copy()


# Check if filtered_df is empty after applying filters
if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop() # Stop execution if no data matches filters


# Calculate summary metrics
total_passengers = filtered_df['total_count'].sum()
total_revenue = filtered_df['total_amount'].sum()
total_distance = filtered_df['travel_distance'].sum()
avg_epkm = filtered_df['Epkm'].mean() if not filtered_df['Epkm'].empty else 0 # Handle case where Epkm might be empty after filtering


# Display Key Metrics
st.markdown("### Key Performance Indicators")
metric_cols = st.columns(4)

with metric_cols[0]:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Passengers</div>
            <div class="metric-value">{total_passengers:,}</div>
        </div>
    """, unsafe_allow_html=True)

with metric_cols[1]:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">₹{total_revenue:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with metric_cols[2]:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Distance</div>
            <div class="metric-value">{total_distance:,} km</div>
        </div>
    """, unsafe_allow_html=True)

with metric_cols[3]:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg EPKM</div>
            <div class="metric-value">₹{avg_epkm:.2f}</div>
        </div>
    """, unsafe_allow_html=True)

# Visualizations Section
st.markdown("---")
st.markdown("## Performance Analysis")

# Row 1: Day-wise and Route Performance
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Passenger Traffic by Day")
    # Ensure all days of the week are considered, even if no data, for consistent x-axis
    day_stats = filtered_df.groupby('day_of_week', observed=True)['total_count'].sum().reindex(day_options).fillna(0)
    fig = px.bar(
        day_stats,
        x=day_stats.index, # Explicitly set x to index for correct ordering
        y=day_stats.values,
        color=day_stats.values,
        color_continuous_scale='Blues',
        labels={'y': 'Passenger Count', 'x': 'Day of Week'} # Correct labels
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Top/Bottom Routes by Passengers")
    # Calculate route stats only if filtered_df is not empty
    if not filtered_df.empty:
        route_stats = filtered_df.groupby('route_no')['total_count'].sum()
        # Ensure there are enough routes to display top/bottom 5
        if len(route_stats) >= 10:
            top_5_routes = route_stats.nlargest(5)
            bottom_5_routes = route_stats.nsmallest(5)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=top_5_routes.index,
                y=top_5_routes.values,
                name='Top 5',
                marker_color='#1f77b4'
            ))
            fig.add_trace(go.Bar(
                x=bottom_5_routes.index,
                y=bottom_5_routes.values,
                name='Bottom 5',
                marker_color='#ff7f0e'
            ))
            fig.update_layout(barmode='group', title='Top 5 and Bottom 5 Routes by Passengers')
            st.plotly_chart(fig, use_container_width=True)
        elif not route_stats.empty:
             # If less than 10 routes, just show all routes
            fig = px.bar(route_stats, x=route_stats.index, y=route_stats.values, title='Passenger Count by Route')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No route data available for the selected filters.")
    else:
        st.info("No route data available for the selected filters.")


# Row 2: Time Series and Efficiency Metrics
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Revenue Trend Over Time")
    if time_period == "Daily":
        # Grouping by date and summing revenue
        time_series = filtered_df.groupby('running_date')['total_amount'].sum().reset_index()
        fig = px.line(time_series, x='running_date', y='total_amount', labels={'total_amount': 'Revenue (₹)', 'running_date': 'Date'}, title='Daily Revenue Trend')
    elif time_period == "Weekly":
        # Grouping by week and summing revenue
        # Ensure week is treated as categorical for plotting if not sorted chronologically
        weekly = filtered_df.groupby(filtered_df['running_date'].dt.isocalendar().week)['total_amount'].sum().reset_index()
        fig = px.line(weekly, x='week', y='total_amount', labels={'total_amount': 'Revenue (₹)', 'week': 'Week Number'}, title='Weekly Revenue Trend')
    else:  # Monthly
        # Grouping by year and month to ensure correct chronological order
        monthly = filtered_df.groupby([filtered_df['running_date'].dt.year, filtered_df['running_date'].dt.month])['total_amount'].sum().reset_index()
        monthly['YearMonth'] = pd.to_datetime(monthly['running_date'].dt.year.astype(str) + '-' + monthly['running_date'].dt.month.astype(str) + '-01') # Create a datetime for sorting and plotting
        monthly = monthly.sort_values('YearMonth')
        fig = px.line(monthly, x='YearMonth', y='total_amount', labels={'total_amount': 'Revenue (₹)', 'YearMonth': 'Month'}, title='Monthly Revenue Trend')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Efficiency by Route (EPKM)")
    # Calculate epkm stats only if filtered_df is not empty
    if not filtered_df.empty:
        epkm_stats = filtered_df.groupby('route_no')['Epkm'].mean().sort_values()
        fig = px.bar(
            epkm_stats,
            orientation='h',
            color=epkm_stats.values,
            color_continuous_scale='Viridis',
            labels={'value': 'EPKM (₹/km)', 'index': 'Route'},
            title='Average EPKM by Route'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No EPKM data available for the selected filters.")


# Data Table Section
st.markdown("---")
st.header("Detailed Data")

with st.expander("View Raw Data Table"):
    st.dataframe(filtered_df)


# Export Option
st.markdown("---")
with st.expander("Export Data"):
    st.write(f"Filtered dataset contains {len(filtered_df)} records")
    st.download_button(
        "Download as CSV",
        filtered_df.to_csv(index=False).encode('utf-8'),
        "transport_data.csv",
        "text/csv"
    )
