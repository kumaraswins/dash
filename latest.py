import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

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
    df = pd.read_excel("data/smart_city_dashboard_datewise_data.xlsx")
    
    # Convert and create columns
    df['running_date'] = pd.to_datetime(df['running_date'])
    df['month'] = df['running_date'].dt.month_name()
    df['day_of_week'] = df['running_date'].dt.day_name()
    df['service_type'] = df['color_line']
    df['Epkm'] = (df['total_amount'] / df['travel_distance']).round(2)
    
    return df

# Load data
df = load_data()

# Get filter options
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
# Filters Section
st.markdown("### Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    month_filter = st.multiselect(
        "Month",
        options=available_months,
        default=available_months,
        help="Filter by month(s)"
    )
    # If empty, use all months
    month_filter = month_filter if month_filter else available_months

with col2:
    day_filter = st.multiselect(
        "Day of Week",
        options=day_options,
        default=day_options
    )
    # If empty, use all days
    day_filter = day_filter if day_filter else day_options

with col3:
    service_filter = st.multiselect(
        "Service Type",
        options=color_lines,
        default=color_lines
    )
    # If empty, use all service types
    service_filter = service_filter if service_filter else color_lines

with col4:
    route_filter = st.multiselect(
        "Route",
        options=route_options,
        default=route_options
    )
    # If empty, use all routes
    route_filter = route_filter if route_filter else route_options

# Apply filters - no need for additional checks since we've handled empty cases above
filtered_df = df[
    (df['month'].isin(month_filter)) &
    (df['day_of_week'].isin(day_filter)) &
    (df['service_type'].isin(service_filter)) &
    (df['route_no'].isin(route_filter))
]

# Metrics Section
st.markdown("### Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Passengers</div>
            <div class="metric-value">{filtered_df['total_count'].sum():,}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">₹{filtered_df['total_amount'].sum():,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Distance</div>
            <div class="metric-value">{filtered_df['travel_distance'].sum():,} km</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg EPKM</div>
            <div class="metric-value">₹{filtered_df['Epkm'].mean():.2f}</div>
        </div>
    """, unsafe_allow_html=True)

# Visualization Section
st.markdown("## Performance Analysis")

# Revenue Analysis
with st.container():
    st.markdown("#### Revenue Trends")
    
    tab1, tab2 = st.tabs(["Monthly View", "Daily Pattern"])
    
    with tab1:
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
    
    with tab2:
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

# Route Performance
st.markdown("#### Route Performance")
col1, col2 = st.columns(2)

with col1:
    route_passengers = filtered_df.groupby('route_no')['total_count'].sum().nlargest(10)
    fig = px.bar(
        route_passengers,
        title="Top Routes by Passenger Count",
        labels={'value': 'Passengers', 'index': 'Route'}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    route_epkm = filtered_df.groupby('route_no')['Epkm'].mean().nlargest(10)
    fig = px.bar(
        route_epkm,
        title="Top Routes by Revenue Efficiency (EPKM)",
        labels={'value': 'EPKM (₹/km)', 'index': 'Route'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Export Option
with st.expander("Export Data"):
    st.download_button(
        "Download Filtered Data",
        filtered_df.to_csv(index=False).encode('utf-8'),
        "filtered_transport_data.csv",
        "text/csv"
    )