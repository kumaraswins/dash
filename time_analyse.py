import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_master.csv", parse_dates=['ticket_date'])
    # Convert ticket_time to datetime and combine with ticket_date
    df['ticket_datetime'] = pd.to_datetime(
        df['ticket_date'].dt.strftime('%Y-%m-%d') + ' ' + df['ticket_time']
    )
    return df

df = load_data()

# --- Global Filters ---
st.sidebar.header("🔧 Global Filters")
min_date = df['ticket_datetime'].min().date()
max_date = df['ticket_datetime'].max().date()

selected_dates = st.sidebar.date_input(
    "📅 Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

selected_routes = st.sidebar.multiselect(
    "🛣️ Routes",
    options=df['route_no'].unique(),
    default=df['route_no'].unique()
)

selected_ticket_types = st.sidebar.multiselect(
    "🎟️ Ticket Types",
    options=df['ticket_type_short_code'].unique(),
    default=df['ticket_type_short_code'].unique()
)

# Apply filters
filtered_df = df[
    (df['ticket_datetime'].dt.date >= selected_dates[0]) &
    (df['ticket_datetime'].dt.date <= selected_dates[1]) &
    (df['route_no'].isin(selected_routes)) &
    (df['ticket_type_short_code'].isin(selected_ticket_types))
]

# --- New Monthly Analysis Tab ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview", 
    "Ticket Types", 
    "Route Analysis",
    "📅 Monthly Trends"  # New tab
])

with tab4:
    st.header("📈 Monthly Performance Analysis")
    
    # 1. Monthly Aggregations
    monthly_data = filtered_df.resample('M', on='ticket_datetime').agg({
        'px_total_amount': 'sum',
        'transaction_no': 'count',
        'travelled_KM': 'sum'
    }).rename(columns={
        'px_total_amount': 'Revenue',
        'transaction_no': 'Ticket_Count',
        'travelled_KM': 'Distance_KM'
    })
    
    monthly_data['Revenue_per_KM'] = monthly_data['Revenue'] / monthly_data['Distance_KM']
    monthly_data['Avg_Ticket_Price'] = monthly_data['Revenue'] / monthly_data['Ticket_Count']
    monthly_data.index = monthly_data.index.strftime('%Y-%m')  # Clean date format
    
    # 2. Key Metrics
    st.subheader("Monthly Summary")
    col1, col2, col3 = st.columns(3)
    latest_month = monthly_data.iloc[-1]
    col1.metric("Latest Month Revenue", f"${latest_month['Revenue']:,.2f}")
    col2.metric("Ticket Count", f"{latest_month['Ticket_Count']:,}")
    col3.metric("Revenue/km", f"${latest_month['Revenue_per_KM']:.2f}")
    
    # 3. Trend Charts
    st.subheader("Trend Analysis")
    
    fig1 = px.line(monthly_data.reset_index(), 
                 x='ticket_datetime', y='Revenue',
                 title="Monthly Revenue Trend",
                 labels={'ticket_datetime': 'Month', 'Revenue': 'Revenue ($)'})
    st.plotly_chart(fig1, use_container_width=True)
    
    fig2 = px.bar(monthly_data.reset_index(),
                 x='ticket_datetime', y='Ticket_Count',
                 title="Monthly Ticket Volume",
                 labels={'ticket_datetime': 'Month', 'Ticket_Count': 'Tickets Sold'})
    st.plotly_chart(fig2, use_container_width=True)
    
    # 4. Efficiency Metrics
    st.subheader("Efficiency Trends")
    col1, col2 = st.columns(2)
    
    with col1:
        fig3 = px.line(monthly_data.reset_index(),
                      x='ticket_datetime', y='Revenue_per_KM',
                      title="Revenue per Kilometer",
                      labels={'Revenue_per_KM': '$/km'})
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        fig4 = px.line(monthly_data.reset_index(),
                      x='ticket_datetime', y='Avg_Ticket_Price',
                      title="Average Ticket Price",
                      labels={'Avg_Ticket_Price': 'Price ($)'})
        st.plotly_chart(fig4, use_container_width=True)
    
    # 5. Data Table
    st.subheader("Monthly Data")
    st.dataframe(
        monthly_data.style.format({
            'Revenue': '${:,.2f}',
            'Revenue_per_KM': '${:,.2f}',
            'Avg_Ticket_Price': '${:,.2f}'
        }),
        use_container_width=True
    )

# --- Other tabs (existing implementation) ---
with tab1:
    # Your existing overview tab content
    pass

with tab2:
    # Your existing ticket types tab content
    pass

with tab3:
    # Your existing route analysis tab content
    pass