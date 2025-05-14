import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go  # Add this line
import numpy as np # Import numpy for handling NaN and inf


# Configure page settings
st.set_page_config(
    page_title="Transport Analytics Dashboard",
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
    .plot-container {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Read Excel file
    # Assuming the Excel file is named 'smart_city_dashboard_datewise_data.xlsx' and is in a 'data' subdirectory
    try:
        df = pd.read_excel("data/smart_city_dashboard_datewise_data.xlsx")
    except FileNotFoundError:
        st.error("Error: Data file not found. Please make sure 'smart_city_dashboard_datewise_data.xlsx' is in a 'data' subdirectory.")
        st.stop()

    # Convert and create columns
    df['running_date'] = pd.to_datetime(df['running_date'], errors='coerce')
    # Drop rows with invalid dates
    df.dropna(subset=['running_date'], inplace=True)

    df['month'] = df['running_date'].dt.month_name()
    df['day_of_week'] = df['running_date'].dt.day_name()
    df['service_type'] = df['color_line']

    # Ensure numeric types for calculation
    numeric_cols = ['total_amount', 'travel_distance']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate Epkm using vectorized operations and handle potential issues
    # Calculate raw Epkm, will result in inf for division by zero and NaN for NaNs
    df['Epkm'] = df['total_amount'] / df['travel_distance']

    # Replace infinite values (division by zero) with 0
    df['Epkm'] = df['Epkm'].replace([np.inf, -np.inf], 0)

    # Replace NaN values (from division with NaN or other issues) with 0
    df['Epkm'] = df['Epkm'].fillna(0)

    # Round the final Epkm values
    df['Epkm'] = df['Epkm'].round(2)

    # Ensure total_count is numeric and handle NaNs
    df['total_count'] = pd.to_numeric(df['total_count'], errors='coerce')
    df['total_count'] = df['total_count'].fillna(0)


    # Drop rows with NaN in critical numeric columns after coercion and Epkm calculation
    df.dropna(subset=numeric_cols + ['Epkm', 'total_count'], inplace=True)


    if df.empty:
        st.error("Error: No valid data remaining after processing. Please check your data file for correct formats.")
        st.stop()

    return df

# Load data
df = load_data()

# Get filter options
# Ensure only months present in the data are options
available_months = sorted(df['month'].unique(),
                        key=lambda x: datetime.strptime(x, "%B").month)
day_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
              'Friday', 'Saturday', 'Sunday']
color_lines = df['service_type'].unique()
route_options = df['route_no'].unique()

# Dashboard Header
st.title("🚍 Transport Performance Dashboard")
st.markdown("""
<div style="margin-bottom: 30px;">
    Comprehensive analysis of passenger traffic and revenue performance
</div>
""", unsafe_allow_html=True)

# Filters Section

st.markdown("### Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Month selection
    month_filter = st.multiselect(
        "Month",
        options=available_months,
        default=available_months, # Default to all months
        help="Filter by month(s)"
    )

    # Weekly drill-down for selected months - only show if data is not empty
    week_filter = None # Initialize week_filter
    if len(month_filter) == 1 and not df[df['month'].isin(month_filter)].empty:  # Only show weeks when exactly one month is selected and data exists for that month
        selected_month_num = datetime.strptime(month_filter[0], "%B").month
        month_df = df[df['running_date'].dt.month == selected_month_num]
        if not month_df.empty:
             week_options = sorted(month_df['running_date'].dt.isocalendar().week.unique())

             week_filter = st.multiselect(
                 "Week of Month",
                 options=week_options,
                 default=week_options, # Default to all weeks in the selected month
                 help="Compare specific weeks within the selected month"
             )


with col2:
    day_filter = st.multiselect(
        "Day of Week",
        options=day_options,
        default=day_options # Default to all days
    )

with col3:
    service_filter = st.multiselect(
        "Service Type",
        options=color_lines,
        default=color_lines # Default to all service types
    )

with col4:
    route_filter = st.multiselect(
        "Route",
        options=route_options,
        default=route_options # Default to all routes
    )

# Apply filters
# Start with a condition that includes all rows
filter_condition = pd.Series(True, index=df.index)

# Apply month filter if not empty
if month_filter:
    filter_condition = filter_condition & (df['month'].isin(month_filter))

# Apply weekly filter if applicable and not empty
if week_filter is not None and week_filter:
     filter_condition = filter_condition & (df['running_date'].dt.isocalendar().week.isin(week_filter))

# Apply day filter if not empty
if day_filter:
    filter_condition = filter_condition & (df['day_of_week'].isin(day_filter))

# Apply service filter if not empty
if service_filter:
    filter_condition = filter_condition & (df['service_type'].isin(service_filter))

# Apply route filter if not empty
if route_filter:
    filter_condition = filter_condition & (df['route_no'].isin(route_filter))


# Apply the combined filter condition
filtered_df = df[filter_condition].copy()

# Check if filtered_df is empty after applying filters
if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop() # Stop execution if no data matches filters


# Metrics Section
st.markdown("### Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

# Calculate metrics only if filtered_df is not empty
if not filtered_df.empty:
    total_passengers = filtered_df['total_count'].sum()
    total_revenue = filtered_df['total_amount'].sum()
    total_distance = filtered_df['travel_distance'].sum()
    avg_epkm = filtered_df['Epkm'].mean() if not filtered_df['Epkm'].isnull().all() else 0 # Handle case where Epkm might be empty after filtering
else:
    total_passengers = 0
    total_revenue = 0
    total_distance = 0
    avg_epkm = 0


with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Passengers</div>
            <div class="metric-value">{total_passengers:,}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">₹{total_revenue:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Distance</div>
            <div class="metric-value">{total_distance:,} km</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg EPKM</div>
            <div class="metric-value">₹{avg_epkm:.2f}</div>
        </div>
    """, unsafe_allow_html=True)

# Visualization Section
st.markdown("## Performance Analysis")

# Revenue Analysis
with st.container():
    st.markdown("#### Revenue Trends")

    tab1, tab2 = st.tabs(["Monthly View", "Daily Pattern"])

    with tab1:
        # Ensure data exists before plotting
        if not filtered_df.empty:
            monthly_revenue = filtered_df.groupby('month').agg({
                'total_amount': 'sum',
                'total_count': 'sum'
            }).reindex(available_months).reset_index()

            fig = px.line(
                monthly_revenue,
                x='month',
                y='total_amount',
                markers=True,
                title="Monthly Revenue Trend",
                labels={'total_amount': 'Revenue (₹)', 'month': 'Month'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for monthly revenue trend.")


    with tab2:
        # Ensure data exists before plotting
        if not filtered_df.empty:
            daily_revenue = filtered_df.groupby(['month', 'day_of_week']).agg({
                'total_amount': 'mean'
            }).reset_index()

            fig = px.bar(
                daily_revenue,
                x='day_of_week',
                y='total_amount',
                color='month',
                barmode='group',
                category_orders={"day_of_week": day_options},
                title="Average Daily Revenue by Month",
                labels={'total_amount': 'Average Revenue (₹)', 'day_of_week': 'Day of Week'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for daily revenue pattern.")


# Weekly Comparison Visualization
# Only show if exactly one month is selected and more than one week is selected
if len(month_filter) == 1 and week_filter is not None and len(week_filter) > 1:
    st.markdown("#### Weekly Performance Comparison")

    # Prepare weekly data
    # Ensure data exists before plotting
    if not filtered_df.empty:
        weekly_comparison = filtered_df.groupby(
            [filtered_df['running_date'].dt.isocalendar().week, 'day_of_week']
        ).agg({
            'total_amount': 'sum',
            'total_count': 'sum'
        }).reset_index()

        # Sort by week and day order
        # Ensure week_options is not empty before using it in sorting
        if week_options:
             weekly_comparison = weekly_comparison.sort_values(['week', 'day_of_week'],
                                                        key=lambda x: x.map({k: v for v, k in enumerate(week_options + day_options)}))

             # Create comparison chart
             fig = px.bar(
                 weekly_comparison,
                 x='day_of_week',
                 y='total_amount',
                 color='week',
                 barmode='group',
                 category_orders={"day_of_week": day_options},
                 title=f"Weekly Revenue Comparison for {month_filter[0]}",
                 labels={'total_amount': 'Revenue (₹)', 'day_of_week': 'Day of Week'}
             )
             st.plotly_chart(fig, use_container_width=True)
        else:
             st.info("No weekly data available for comparison in the selected month.")
    else:
        st.info("No data available for weekly performance comparison.")


# Route Performance
st.markdown("#### Route Performance")
col1, col2 = st.columns(2)

with col1:
    # Ensure data exists before plotting
    if not filtered_df.empty:
        route_passengers = filtered_df.groupby('route_no')['total_count'].sum().nlargest(10)
        fig = px.bar(
            route_passengers,
            title="Top Routes by Passenger Count",
            labels={'value': 'Passengers', 'index': 'Route'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for route passenger performance.")

with col2:
    # Ensure data exists before plotting
    if not filtered_df.empty:
        route_epkm = filtered_df.groupby('route_no')['Epkm'].mean().nlargest(10)
        fig = px.bar(
            route_epkm,
            title="Top Routes by Revenue Efficiency (EPKM)",
            labels={'value': 'EPKM (₹/km)', 'index': 'Route'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for route EPKM efficiency.")


# Data Table Section
st.markdown("---")
st.header("Detailed Data")

with st.expander("View Raw Data Table"):
    # Ensure data exists before displaying
    if not filtered_df.empty:
        st.dataframe(filtered_df)
    else:
        st.info("No detailed data available for the selected filters.")


# Export Option
st.markdown("---")
with st.expander("Export Data"):
    # Only show download button if data exists
    if not filtered_df.empty:
        st.write(f"Filtered dataset contains {len(filtered_df)} records")
        st.download_button(
            "Download Filtered Data",
            filtered_df.to_csv(index=False).encode('utf-8'),
            "filtered_transport_data.csv",
            "text/csv"
        )
    else:
        st.info("No data available to export.")
