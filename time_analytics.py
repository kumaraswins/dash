import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose

# Enhanced data loading with time features
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_master.csv")
    df['ticket_datetime'] = pd.to_datetime(df['ticket_date'] + ' ' + df['ticket_time'])
    
    # Time-based features
    df['hour'] = df['ticket_datetime'].dt.hour
    df['day_of_week'] = df['ticket_datetime'].dt.day_name()
    df['month'] = df['ticket_datetime'].dt.month_name()
    df['week'] = df['ticket_datetime'].dt.isocalendar().week
    df['date'] = df['ticket_datetime'].dt.date
    
    # Business metrics
    df['revenue_per_km'] = df['px_total_amount'] / df['travelled_KM'].replace(0, 1)
    return df

df = load_data()

# ===== DASHBOARD LAYOUT =====
st.title("🕒 Time-Based Ticket Analytics")
st.markdown("Analyze temporal patterns in ticket sales and passenger behavior")

# Sidebar controls
with st.sidebar:
    st.header("Filters")
    date_range = st.date_input("Date Range", 
                             [df['ticket_datetime'].min(), df['ticket_datetime'].max()])
    
    time_granularity = st.radio("Time Granularity", 
                              ['Hourly', 'Daily', 'Weekly', 'Monthly'], index=1)
    
    route_filter = st.multiselect("Routes", options=df['route_no'].unique())

# Apply filters
filtered_df = df[
    (df['ticket_datetime'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) & 
    (df['route_no'].isin(route_filter if route_filter else df['route_no'].unique()))
]

# ===== VISUALIZATIONS =====
tab1, tab2, tab3 = st.tabs(["Demand Patterns", "Revenue Analysis", "Operational Metrics"])

with tab1:
    # Visualization 1: Temporal Demand Heatmap
    st.subheader("Passenger Demand Patterns")
    
    if time_granularity == 'Hourly':
        heatmap_data = filtered_df.groupby(['day_of_week', 'hour'])['px_count'].sum().unstack()
        fig = px.imshow(heatmap_data, 
                        labels=dict(x="Hour", y="Day", color="Passengers"),
                        title="Hourly Demand by Weekday")
    else:
        period = 'date' if time_granularity == 'Daily' else 'week' if time_granularity == 'Weekly' else 'month'
        heatmap_data = filtered_df.groupby([period, 'day_of_week'])['px_count'].sum().unstack()
        fig = px.imshow(heatmap_data, 
                        labels=dict(x="Day", y=time_granularity, color="Passengers"),
                        title=f"{time_granularity} Demand by Weekday")
    
    st.plotly_chart(fig, use_container_width=True)

    # Visualization 2: Anomaly Detection
    st.subheader("Demand Anomalies")
    ts_data = filtered_df.resample('D', on='ticket_datetime')['px_count'].sum()
    result = seasonal_decompose(ts_data, model='additive', period=7)
    
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True)
    fig.add_trace(go.Scatter(x=ts_data.index, y=ts_data, name='Actual'), row=1, col=1)
    fig.add_trace(go.Scatter(x=result.trend.index, y=result.trend, name='Trend'), row=2, col=1)
    fig.add_trace(go.Scatter(x=result.seasonal.index, y=result.seasonal, name='Seasonal'), row=3, col=1)
    fig.add_trace(go.Scatter(x=result.resid.index, y=result.resid, name='Residual'), row=4, col=1)
    fig.update_layout(height=600, title_text="Time Series Decomposition")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Visualization 3: Revenue Trend Comparison
    st.subheader("Revenue Performance")
    
    col1, col2 = st.columns(2)
    with col1:
        period = time_granularity[:-2].lower()  # Convert "Hourly" -> "hour" etc.
        rev_trend = filtered_df.resample(period[0].upper(), on='ticket_datetime')['px_total_amount'].sum()
        fig = px.line(rev_trend, title=f"{time_granularity} Revenue Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        rev_by_route = filtered_df.groupby('route_no')['px_total_amount'].sum().nlargest(10)
        fig = px.pie(rev_by_route, names=rev_by_route.index, 
                    title="Top 10 Routes by Revenue")
        st.plotly_chart(fig, use_container_width=True)
    
    # Visualization 4: Revenue per KM by Time
    st.subheader("Revenue Efficiency")
    time_epkm = filtered_df.groupby('hour').agg(
        revenue=('px_total_amount','sum'),
        distance=('travelled_KM','sum')
    ).assign(epkm=lambda x: x['revenue']/x['distance'])
    
    fig = px.bar(time_epkm, x=time_epkm.index, y='epkm',
                title="Revenue per KM by Hour of Day")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    # Visualization 5: Service Type Time Patterns
    st.subheader("Service Utilization")
    service_hourly = filtered_df.groupby(['hour','service_type'])['ticket_id'].count().unstack()
    fig = px.area(service_hourly, title="Hourly Ticket Sales by Service Type")
    st.plotly_chart(fig, use_container_width=True)
    
    # Visualization 6: Trip Frequency Analysis
    st.subheader("Trip Scheduling")
    if not filtered_df.empty:
        fig = px.density_heatmap(
            filtered_df, 
            x='hour', 
            y='trip_no',
            z='px_count',
            histfunc="sum",
            title="Passenger Density by Trip & Hour"
        )
        st.plotly_chart(fig, use_container_width=True)

# ===== DATA EXPORT =====
st.sidebar.download_button(
    label="Download Filtered Data",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_ticket_data.csv",
    mime="text/csv"
)