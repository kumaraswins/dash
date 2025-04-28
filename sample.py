import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# Load data with caching
@st.cache_data
def load_data():
    master = pd.read_csv("master.csv")
    ticket_types = pd.read_csv("ticket_type.csv")
    service_types = pd.read_csv("service_type.csv")
    
    # Data transformations
    master["ticket_type"] = master["ticket_type_short_code"].map(
        dict(zip(ticket_types["ticket_type_id"], ticket_types["ticket_type_name"])))
    master["service_type"] = master["bus_service_id"].map(
        dict(zip(service_types["service_type_id"], service_types["service_type_name"])))
    master["ticket_datetime"] = pd.to_datetime(master["ticket_date"] + " " + master["ticket_time"])
    master["revenue_per_km"] = master["px_total_amount"] / master["travelled_KM"].replace(0, 1)
    return master

df = load_data()

# Sidebar filters
st.sidebar.header("Global Filters")
date_range = st.sidebar.date_input("Date Range", 
    [df["ticket_datetime"].min(), df["ticket_datetime"].max()])
service_filter = st.sidebar.multiselect("Service Type", 
    options=df["service_type"].unique(), default=df["service_type"].unique())
ticket_filter = st.sidebar.multiselect("Ticket Type", 
    options=df["ticket_type"].unique(), default=df["ticket_type"].unique())

# Apply filters
filtered_df = df[
    (df["ticket_type"].isin(ticket_filter)) &
    (df["service_type"].isin(service_filter)) &
    (df["ticket_datetime"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
]

# Page navigation
pages = {
    "Summary Overview": "page1",
    "Route Performance": "page2",
    "Trip Analysis": "page3",
    "Route Optimization": "page4",
    "Fleet Monitoring": "page5",
    "Sustainability Dashboard": "page6"
}
selected_page = st.sidebar.selectbox("Navigation", list(pages.keys()))

# Page 1: Summary Overview
if selected_page == "Summary Overview":
    st.title("🚌 Summary Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Passengers", f"{filtered_df['px_count'].sum():,}")
    col2.metric("Total Revenue", f"₹{filtered_df['px_total_amount'].sum():,.2f}")
    col3.metric("Total Distance", f"{filtered_df['travelled_KM'].sum():,.0f} KM")
    col4.metric("Avg EPKM", f"₹{filtered_df['revenue_per_km'].mean():.2f}/KM")
    
    # Charts
    st.subheader("Passenger Count by Route")
    route_passengers = filtered_df.groupby("route_no")["px_count"].sum().sort_values(ascending=False)
    st.bar_chart(route_passengers)
    
    st.subheader("Revenue Trend")
    daily_revenue = filtered_df.resample('D', on='ticket_datetime')["px_total_amount"].sum()
    st.line_chart(daily_revenue)
    
    # Insights
    st.subheader("Key Insights")
    best_route = route_passengers.idxmax()
    st.success(f"🌟 Best Performing Route: {best_route} with {route_passengers.max():,} passengers")
    
    peak_day = daily_revenue.idxmax().strftime('%Y-%m-%d')
    st.info(f"📈 Peak Revenue Day: {peak_day} (₹{daily_revenue.max():,.2f})")

# Page 2: Route Performance
elif selected_page == "Route Performance":
    st.title("🛣️ Route Performance")
    route = st.selectbox("Select Route", df["route_no"].unique())
    
    route_df = filtered_df[filtered_df["route_no"] == route]
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Trips", len(route_df["trip_no"].unique()))
    col2.metric("Total Passengers", route_df["px_count"].sum())
    col3.metric("Total Revenue", f"₹{route_df['px_total_amount'].sum():,.2f}")
    
    # Charts
    st.subheader("Schedulewise EPKM")
    epkm_data = route_df.groupby("schedule_no")["revenue_per_km"].mean().sort_values()
    st.bar_chart(epkm_data)
    
    st.subheader("Revenue vs Distance")
    fig = px.scatter(route_df, x="travelled_KM", y="px_total_amount", 
                   size="px_count", color="schedule_no",
                   hover_name="trip_no")
    st.plotly_chart(fig)
    
    # Insights
    worst_schedule = epkm_data.idxmin()
    st.warning(f"⚠️ Underperforming Schedule: {worst_schedule} (₹{epkm_data.min():.2f}/KM)")

# ... (Previous imports and Page 1-2 code remain the same) ...

# Page 3: Trip Analysis
elif selected_page == "Trip Analysis":
    st.title("🚍 Trip Analysis")
    
    # Slicers
    col1, col2 = st.columns(2)
    selected_route = col1.selectbox("Select Route", df["route_no"].unique(), key="trip_route")
    selected_schedule = col2.selectbox("Select Schedule", 
                                     df[df["route_no"] == selected_route]["schedule_no"].unique(),
                                     key="trip_schedule")
    
    # Filter data
    trip_df = filtered_df[
        (filtered_df["route_no"] == selected_route) & 
        (filtered_df["schedule_no"] == selected_schedule)
    ]
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Revenue/Trip", f"₹{trip_df['px_total_amount'].mean():.2f}")
    col2.metric("Avg Distance/Trip", f"{trip_df['travelled_KM'].mean():.1f} KM")
    col3.metric("Avg Passengers/Trip", f"{trip_df['px_count'].mean():.1f}")
    
    # Charts
    st.subheader("EPKM Trend by Trip")
    fig = px.line(trip_df.sort_values("ticket_datetime"), 
                 x="ticket_datetime", y="revenue_per_km",
                 title=f"Revenue Efficiency Trend - {selected_route} {selected_schedule}")
    st.plotly_chart(fig)
    
    st.subheader("Passenger Load Distribution")
    fig = px.histogram(trip_df, x="px_count", nbins=20,
                      title="Frequency of Passenger Loads")
    st.plotly_chart(fig)
    
    # Insights
    threshold = trip_df["revenue_per_km"].quantile(0.25)
    low_perf_trips = trip_df[trip_df["revenue_per_km"] < threshold]
    if not low_perf_trips.empty:
        st.warning(f"⚠️ {len(low_perf_trips)} trips below EPKM threshold (₹{threshold:.2f}/KM)")

# Page 4: Route Optimization
elif selected_page == "Route Optimization":
    st.title("📊 Route Optimization")
    
    # Slicers
    distance_range = st.slider("Distance Range (KM)", 
                             min_value=int(df["travelled_KM"].min()),
                             max_value=int(df["travelled_KM"].max()),
                             value=(10, 50))
    
    # Calculate optimization metrics
    route_stats = filtered_df.groupby("route_no").agg({
        "px_count": "sum",
        "travelled_KM": "sum",
        "px_total_amount": "sum",
        "trip_no": "nunique"
    }).reset_index()
    
    route_stats["pass_per_km"] = route_stats["px_count"] / route_stats["travelled_KM"]
    route_stats["revenue_per_km"] = route_stats["px_total_amount"] / route_stats["travelled_KM"]
    route_stats["efficiency_score"] = (route_stats["pass_per_km"] * route_stats["revenue_per_km"]) / route_stats["trip_no"]
    
    # Filter by distance
    avg_dist = filtered_df.groupby("route_no")["travelled_KM"].mean()
    route_stats = route_stats[avg_dist.between(*distance_range)].reset_index()
    
    # Visualizations
    st.subheader("Passenger Density by Route")
    fig = px.bar(route_stats.sort_values("pass_per_km", ascending=False),
                x="route_no", y="pass_per_km",
                title="Passengers per Kilometer")
    st.plotly_chart(fig)
    
    st.subheader("Efficiency Score Ranking")
    fig = px.bar(route_stats.sort_values("efficiency_score", ascending=False),
                x="route_no", y="efficiency_score",
                color="efficiency_score")
    st.plotly_chart(fig)
    
    # Optimization suggestions
    st.subheader("Optimization Recommendations")
    if not route_stats.empty:
        best_route = route_stats.loc[route_stats["efficiency_score"].idxmax()]
        worst_route = route_stats.loc[route_stats["efficiency_score"].idxmin()]
        
        st.success(f"✅ Expand service on **{best_route['route_no']}** (Score: {best_route['efficiency_score']:.2f})")
        st.error(f"❌ Review **{worst_route['route_no']}** (Score: {worst_route['efficiency_score']:.2f})")

# Page 5: Fleet Monitoring
elif selected_page == "Fleet Monitoring":
    st.title("🚌 Fleet Monitoring")
    
    # Vehicle selector
    selected_vehicle = st.selectbox("Select Vehicle (Optional)", 
                                  [""] + list(df["vehicle_no"].unique()))
    
    # Filter data
    fleet_df = filtered_df.copy()
    if selected_vehicle:
        fleet_df = fleet_df[fleet_df["vehicle_no"] == selected_vehicle]
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Vehicles", fleet_df["vehicle_no"].nunique())
    col2.metric("Avg Trips/Vehicle", f"{fleet_df.groupby('vehicle_no')['trip_no'].nunique().mean():.1f}")
    col3.metric("Avg KM/Vehicle", f"{fleet_df.groupby('vehicle_no')['travelled_KM'].sum().mean():,.0f}")
    
    # Charts
    st.subheader("Vehicle Utilization")
    vehicle_stats = fleet_df.groupby("vehicle_no").agg({
        "travelled_KM": "sum",
        "trip_no": "nunique"
    }).reset_index()
    
    fig = px.scatter(vehicle_stats, x="trip_no", y="travelled_KM",
                    size="travelled_KM", hover_name="vehicle_no",
                    title="Trips vs Distance by Vehicle")
    st.plotly_chart(fig)
    
    # Maintenance alerts
    st.subheader("Maintenance Alerts")
    high_use = vehicle_stats[vehicle_stats["travelled_KM"] > vehicle_stats["travelled_KM"].quantile(0.9)]
    if not high_use.empty:
        st.warning(f"🚨 {len(high_use)} vehicles in top 10% usage need inspection")

# Page 6: Sustainability Dashboard
elif selected_page == "Sustainability Dashboard":
    st.title("🌱 Sustainability Dashboard")
    
    # Mock sustainability data (replace with actual data if available)
    sustainability_df = filtered_df.copy()
    sustainability_df["bus_type"] = sustainability_df["vehicle_no"].apply(
        lambda x: "Electric" if int(x[-1]) % 3 == 0 else "Diesel")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    electric_km = sustainability_df[sustainability_df["bus_type"] == "Electric"]["travelled_KM"].sum()
    total_km = sustainability_df["travelled_KM"].sum()
    col1.metric("Electric KM", f"{electric_km:,.0f} ({electric_km/total_km:.1%})")
    col2.metric("CO₂ Saved", f"{(total_km * 0.1):,.0f} kg")  # 0.1kg/km savings estimate
    col3.metric("Fuel Savings", f"₹{(total_km * 5):,.0f}")  # ₹5/km savings estimate
    
    # Charts
    st.subheader("Energy Mix by Distance")
    fig = px.pie(sustainability_df, names="bus_type", values="travelled_KM",
                title="Percentage of Kilometers by Fuel Type")
    st.plotly_chart(fig)
    
    st.subheader("Monthly Emissions Trend")
    monthly_emissions = sustainability_df.resample('M', on='ticket_datetime').apply(
        lambda x: (x["travelled_KM"] * (0.1 if x["bus_type"] == "Electric" else 0.8)).sum()
    )
    fig = px.line(monthly_emissions, title="Estimated CO₂ Emissions (kg)")
    st.plotly_chart(fig)
    
    # Recommendations
    st.subheader("Electrification Opportunities")
    diesel_routes = sustainability_df[sustainability_df["bus_type"] == "Diesel"]
    if not diesel_routes.empty:
        candidate = diesel_routes.groupby("route_no")["travelled_KM"].sum().idxmax()
        st.info(f"💡 Prioritize **{candidate}** for electrification (highest diesel KM)")

# ... (Existing export functionality remains the same) ...

# Data Export
if st.sidebar.button("Export Filtered Data"):
    st.sidebar.download_button(
        label="Download CSV",
        data=filtered_df.to_csv().encode('utf-8'),
        file_name=f"bus_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )