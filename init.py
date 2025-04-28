import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load data
@st.cache_data
def load_data():
    master = pd.read_csv("cleaned_master.csv")
    ticket_types = pd.read_csv("ticket_type.csv")
    service_types = pd.read_csv("service_type.csv")
    
    # Map IDs to names
    master["ticket_type"] = master["ticket_type_short_code"].map(
        dict(zip(ticket_types["ticket_type_id"], ticket_types["ticket_type_name"])))
    master["service_type"] = master["bus_service_id"].map(
        dict(zip(service_types["service_type_id"], service_types["service_type_name"])))
    
    # Convert dates and calculate derived metrics
    master["ticket_datetime"] = pd.to_datetime(
        master["ticket_date"] + " " + master["ticket_time"])
    master["ticket_date"] = master["ticket_datetime"].dt.date  # Extract date for filtering
    
    # Calculate revenue per km and passengers per km
    master["revenue_per_km"] = master["px_total_amount"] / master["travelled_KM"].replace(0, 1)
    master["passengers_per_km"] = master["px_count"] / master["travelled_KM"].replace(0, 1)
    
    return master

df = load_data()

# --- Dashboard Layout ---
st.title("🚌 Bus Ticket Sales Dashboard")
st.markdown("Analyze ticket sales by type, service, route and schedule performance.")

# 1. Date Range Filter
min_date = df["ticket_date"].min()
max_date = df["ticket_date"].max()
selected_dates = st.sidebar.date_input(
    "📅 Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# 2. Ticket Type (Product) Filter
ticket_types = df["ticket_type"].unique()
selected_ticket_types = st.sidebar.multiselect(
    "🎟️ Ticket Types",
    options=ticket_types,
    default=ticket_types
)

# 3. Route Filter
routes = df["route_no"].unique()
selected_routes = st.sidebar.multiselect(
    "🛣️ Routes",
    options=routes,
    default=routes
)

# 4. Service Type Filter
service_types = df["service_type"].unique()
selected_services = st.sidebar.multiselect(
    "🚌 Service Types",
    options=service_types,
    default=service_types
)

# Apply all filters
filtered_df = df[
    (df["ticket_date"].between(selected_dates[0], selected_dates[1])) &
    (df["ticket_type"].isin(selected_ticket_types)) &
    (df["route_no"].isin(selected_routes)) &
    (df["service_type"].isin(selected_services))
]

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8,tab9 = st.tabs([
    "🚌 Summary Overview", "Ticket Types", "Service Analysis",
    "Route Performance", "Optimization Summary",
    "Fleet Summary", "Route Efficiency", 
    "Passenger Metrics" ,"📅 Monthly Trends"
])

# Sales Overview Tab
with tab1:
    st.header("🚌 Summary Overview")

    # col1, col2, col3 = st.columns(3)
    # col1.metric("Total Tickets", len(filtered_df))
    # col2.metric("Total Revenue", f"₹{filtered_df['px_total_amount'].sum():,.2f}")
    # col3.metric("Avg. Ticket Price", f"₹{filtered_df['px_total_amount'].mean():,.2f}")
    # Metrics

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Passengers", f"{filtered_df['px_count'].sum():,}")
    col2.metric("Total Revenue", f"₹{filtered_df['px_total_amount'].sum():,.2f}")
    col3.metric("Total Distance", f"{filtered_df['travelled_KM'].sum():,.0f} KM")

    col4, col5 = st.columns(2)

    col4.metric("Avg EPKM", f"₹{filtered_df['revenue_per_km'].mean():.2f}/KM")
    col5.metric("Total Tickets", len(filtered_df))
    
    route_passengers = filtered_df.groupby("route_no")["px_count"].sum().sort_values(ascending=False)
    daily_revenue = filtered_df.resample('D', on='ticket_datetime')["px_total_amount"].sum()

    # Daily sales trend
    daily_sales = filtered_df.groupby(filtered_df["ticket_datetime"].dt.date)["px_total_amount"].sum().reset_index()
    fig = px.line(daily_sales, x="ticket_datetime", y="px_total_amount", 
                 title="Daily Revenue Trend", labels={"px_total_amount": "Revenue (₹)"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Passenger Count by Route")
    st.bar_chart(route_passengers)

    st.subheader("Key Insights")
    best_route = route_passengers.idxmax()
    st.success(f"🌟 Best Performing Route: {best_route} with {route_passengers.max():,} passengers")
    
    peak_day = daily_revenue.idxmax().strftime('%Y-%m-%d')
    st.info(f"📈 Peak Revenue Day: {peak_day} (₹{daily_revenue.max():,.2f})")

# Ticket Types Tab
with tab2:
    st.header("Ticket Type Analysis")

    ticket_summary = filtered_df.groupby("ticket_type").agg(
        total_tickets=("ticket_type", "count"),
        total_revenue=("px_total_amount", "sum"),
        avg_revenue=("px_total_amount", "mean")
    ).sort_values("total_revenue", ascending=False)
    
    # Format with Styler
    ticket_summary_styled = ticket_summary.style.format({
        "total_revenue": "₹{:,.2f}",
        "avg_revenue": "₹{:,.2f}"
    }).background_gradient(cmap="Blues", subset=["total_revenue"])
    
    st.dataframe(ticket_summary_styled, use_container_width=True)
    
    ticket_counts = filtered_df["ticket_type"].value_counts().reset_index()
    fig = px.pie(ticket_counts, names="ticket_type", values="count", 
                title="Ticket Type Distribution")
    st.plotly_chart(fig, use_container_width=True)

# Service Analysis Tab
with tab3:
    st.header("Service Type Analysis")

    # --- Summary Table ---
    service_summary = filtered_df.groupby("service_type").agg(
        total_tickets=("service_type", "count"),
        total_revenue=("px_total_amount", "sum"),
        avg_distance_km=("travelled_KM", "mean"),
        avg_revenue_per_km=("revenue_per_km", "mean")
    ).sort_values("total_revenue", ascending=False)
    
    # Format with Styler
    service_summary_styled = service_summary.style.format({
        "total_revenue": "₹{:,.2f}",
        "avg_distance_km": "{:,.1f} km",
        "avg_revenue_per_km": "₹{:,.2f}/km"
    }).highlight_max(subset=["total_revenue"], color="#90EE90")
    
    st.dataframe(service_summary_styled, use_container_width=True)


    service_revenue = filtered_df.groupby("service_type")["px_total_amount"].sum().reset_index()
    fig = px.bar(service_revenue, x="service_type", y="px_total_amount", 
                title="Revenue by Service Type", labels={"px_total_amount": "Revenue (₹)"})
    st.plotly_chart(fig, use_container_width=True)

# Route and Schedule Performance Tab
with tab4:
    st.header("Route and Schedule Performance")
    
    # Route selection
    route_list = df["route_no"].unique()
    selected_route = st.selectbox("Select Route", route_list)
    
    # Filter data for selected route
    route_df = filtered_df[filtered_df["route_no"] == selected_route]

    # Summary Table
    st.subheader(f"📈 Route {selected_route} Summary")
    route_summary = route_df.groupby("schedule_no").agg(
        total_tickets=("schedule_no", "count"),
        total_revenue=("px_total_amount", "sum"),
        avg_distance=("travelled_KM", "mean"),
        avg_epkm=("revenue_per_km", "mean")
    ).sort_values("total_revenue", ascending=False)
    
    # Format with Styler
    route_summary_styled = route_summary.style.format({
        "total_revenue": "₹{:,.2f}",
        "avg_distance": "{:,.1f} km",
        "avg_epkm": "₹{:,.2f}/km"
    }).set_properties(**{
        "background-color": "#f7f7f7",
        "border": "1px solid #d3d3d3"
    })
    
    st.dataframe(route_summary_styled, use_container_width=True)
    
    # EPKM by Schedule
    st.subheader(f"Schedulewise EPKM for {selected_route}")
    epkm_data = route_df.groupby("schedule_no").agg({
        "px_total_amount": "sum",
        "travelled_KM": "mean",
        "revenue_per_km": "mean"
    }).reset_index()
    
    fig1 = px.bar(epkm_data, x="schedule_no", y="revenue_per_km",
                 title=f"Earnings Per Kilometer (EPKM) by Schedule - {selected_route}",
                 labels={"revenue_per_km": "EPKM (₹/km)", "schedule_no": "Schedule"})
    st.plotly_chart(fig1, use_container_width=True)
    
    # Revenue vs Distance
    st.subheader(f"Revenue vs Distance for {selected_route}")
    fig2 = px.scatter(route_df, x="travelled_KM", y="px_total_amount",
                     color="schedule_no", trendline="lowess",
                     title=f"Revenue vs Distance Traveled - {selected_route}",
                     labels={"px_total_amount": "Revenue (₹)", "travelled_KM": "Distance (km)"})
    st.plotly_chart(fig2, use_container_width=True)
    
    # Show raw data
    st.subheader("Route Performance Data")
    st.dataframe(route_df[["schedule_no", "trip_no", "travelled_KM", "px_total_amount", "revenue_per_km"]]
                .sort_values("revenue_per_km", ascending=False))

with tab5:
    st.header("Route Optimization Summary")
    
    # Calculate the summary
    optimization_summary = df.groupby('route_no').agg({
        'px_total_amount': 'sum',          # Revenue
        'travelled_KM': 'sum',            # Distance
        'revenue_per_km': 'mean',          # Revenue per km
    }).reset_index().rename(columns={
        'route_no': 'Route',
        'px_total_amount': 'Revenue',
        'travelled_KM': 'Distance',
        'revenue_per_km': 'Revenue_per_km'
    })
    
    # Styled Table with Interactive Features
    st.subheader("Key Route Metrics")
    
    # Sortable DataFrame
    st.dataframe(
        optimization_summary.style
        .format({
            "Revenue": "₹{:,.2f}",
            "Distance": "{:,.1f} km",
            "Revenue_per_km": "₹{:,.2f}/km"
        })
        .background_gradient(subset=["Revenue"], cmap="Greens")
        .highlight_max(subset=["Revenue_per_km"], color="lightgreen"),
        use_container_width=True
    )
    
    # Download Button
    csv = optimization_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="route_optimization_summary.csv",
        mime="text/csv"
    )

    st.metric("Most Efficient Route", 
          optimization_summary.loc[optimization_summary["Revenue_per_km"].idxmax(), "Route"],
          delta=f"₹{optimization_summary['Revenue_per_km'].max():.2f}/km")
    
    # Visualizations
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(optimization_summary, 
                    x="Route", y="Revenue",
                    title="Total Revenue by Route")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(optimization_summary,
                        x="Distance", y="Revenue_per_km",
                        color="Route", size="Revenue",
                        title="Efficiency: Revenue/km vs Distance")
        st.plotly_chart(fig, use_container_width=True)

with tab6:
    st.header("🚍 Fleet & Sustainability Optimization")

    optimization_actions = pd.DataFrame({
        "Issue": [
            "Low occupancy trips",
            "Overloaded trips",
            "Long empty routes",
            "High EPKM routes",
            "Short high-load routes"
        ],
        "Metric": [
            "Passengers/km < 0.5",
            "Passenger load > 90% capacity",
            "Distance high, Passenger low",
            "EPKM > ₹15/km",
            "Distance < 20km, Load > 80%"
        ],
        "Action": [
            "Remove or club these trips",
            "Add more buses or stagger timings",
            "Shorten or re-route",
            "Schedule more frequency",
            "Assign electric buses"
        ],
        "Impact": [
            "Reduce fuel waste",
            "Improve passenger experience",
            "Cut operational costs",
            "Maximize profitability",
            "Lower carbon emissions"
        ]
    })
    electric_bus_routes = optimization_actions[optimization_actions["Action"].str.contains("electric")]
    co2_saved = len(electric_bus_routes) * 20  # kg CO2/bus/day

    # Key Metrics Summary
    st.subheader("🔍 Route Health Indicators")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Low-Occupancy Trips", "12", "5% of total")  # Example data
    col2.metric("Overloaded Trips", "8", "3% of total")
    col3.metric("High-EPKM Routes", "15", "Prioritize expansion")
    col4.metric("Estimated CO2 Reduction", f"{co2_saved}", "kg/day")
    
    # Actionable Insights Table
    st.subheader("🛠️ Optimization Actions")
    
    # Style the table
    st.dataframe(
        optimization_actions.style
        .applymap(lambda x: "background-color: #FFF8E1" if "electric" in str(x).lower() else "")
        .set_properties(**{"border": "1px solid #E0E0E0"}),
        use_container_width=True
    )
    
    # Visualizations
    st.subheader("📊 Route Performance Analysis")
    
    # Example: Low-Occupancy vs Overloaded Routes
    fig = px.scatter(
        df, 
        x="travelled_KM", 
        y="px_total_amount",  # Proxy for passengers (replace with actual passenger count if available)
        color="route_no",
        size="revenue_per_km",
        hover_data=["schedule_no"],
        title="Occupancy vs Distance (Size = EPKM)"
    )
    fig.add_hline(y=df["px_total_amount"].quantile(0.9), line_dash="dash", 
                 annotation_text="Overload Threshold (90%)")
    fig.add_hline(y=df["px_total_amount"].quantile(0.1), line_dash="dash", 
                 annotation_text="Low-Occupancy Threshold (10%)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Downloadable Recommendations
    st.download_button(
        label="📥 Download Optimization Plan",
        data=optimization_actions.to_csv(index=False).encode('utf-8'),
        file_name="route_optimization_actions.csv",
        mime="text/csv"
    )

with tab7:
    st.header("🔄 Route Efficiency Optimizer")
    
    # Calculate Key Metrics
    route_stats = df.groupby('route_no').agg(
        total_revenue=('px_total_amount', 'sum'),
        total_distance=('travelled_KM', 'sum'),
        ticket_count=('ticket_type', 'count')  # Proxy for passenger count
    ).reset_index()
    
    # Avoid division by zero
    route_stats['revenue_per_km'] = route_stats['total_revenue'] / route_stats['total_distance'].replace(0, 1)
    route_stats['tickets_per_km'] = route_stats['ticket_count'] / route_stats['total_distance'].replace(0, 1)
    
    # Efficiency Score (0-5 scale)
    route_stats['efficiency_score'] = (
        (route_stats['revenue_per_km'] / route_stats['revenue_per_km'].max() * 2.5) +
        (route_stats['tickets_per_km'] / route_stats['tickets_per_km'].max() * 2.5)
    ).clip(0, 5)
    
    # Key Metrics Summary
    st.subheader("🚩 Quick Insights")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg. Tickets/km", f"{route_stats['tickets_per_km'].mean():.2f}")
    col2.metric("Top EPKM Route", 
                route_stats.loc[route_stats['revenue_per_km'].idxmax(), 'route_no'],
                f"₹{route_stats['revenue_per_km'].max():.2f}/km")
    col3.metric("Lowest Efficiency", 
                route_stats.loc[route_stats['efficiency_score'].idxmin(), 'route_no'],
                f"Score: {route_stats['efficiency_score'].min():.1f}/5")
    
    # Visualizations
    st.subheader("📈 Route Efficiency Analysis")
    
    # Chart 1: Tickets per km
    fig1 = px.bar(route_stats.sort_values('tickets_per_km', ascending=False),
                 x='route_no', y='tickets_per_km',
                 title="Ticket Density (Tickets/km)",
                 labels={'tickets_per_km': 'Tickets per km'},
                 color='tickets_per_km')
    st.plotly_chart(fig1, use_container_width=True)
    
    # Chart 2: Revenue per km
    fig2 = px.bar(route_stats.sort_values('revenue_per_km', ascending=False),
                 x='route_no', y='revenue_per_km',
                 title="Revenue Efficiency (₹/km)",
                 labels={'revenue_per_km': 'Revenue per km'},
                 color='revenue_per_km')
    st.plotly_chart(fig2, use_container_width=True)
    
    # Chart 3: Efficiency Score
    fig3 = px.bar(route_stats.sort_values('efficiency_score', ascending=False),
                 x='route_no', y='efficiency_score',
                 title="Route Efficiency Score (0-5)",
                 color='efficiency_score',
                 color_continuous_scale='RdYlGn')
    st.plotly_chart(fig3, use_container_width=True)
    
    # Actionable Recommendations
    st.subheader("💡 Optimization Actions")
    
    recommendations = []
    for _, row in route_stats.iterrows():
        if row['tickets_per_km'] < 0.3:  # Low ticket density
            action = "🚫 Merge/Cancel (Low demand)"
        elif row['revenue_per_km'] > 15:  # High revenue
            action = "🔄 Add peak-hour trips"
        elif row['efficiency_score'] < 2:  # Low efficiency
            action = "🛣️ Re-route"
        else:
            action = "✅ Optimal"
        
        recommendations.append({
            "Route": row['route_no'],
            "Tickets/km": round(row['tickets_per_km'], 2),
            "Revenue/km": f"₹{row['revenue_per_km']:.2f}",
            "Efficiency Score": f"{row['efficiency_score']:.1f}/5",
            "Action": action
        })
    
    rec_df = pd.DataFrame(recommendations)
    
    # Color coding
    def color_actions(val):
        if "Merge/Cancel" in val: return 'background-color: #FFCDD2'
        elif "Add peak-hour" in val: return 'background-color: #C8E6C9'
        elif "Re-route" in val: return 'background-color: #FFF9C4'
        else: return ''
    
    st.dataframe(
        rec_df.style.applymap(color_actions, subset=['Action']),
        use_container_width=True
    )

# New Tab: Passenger & Revenue Metrics
with tab8:
    st.header("🧮 Passenger & Revenue per Kilometer Analysis")
    
    # Calculate aggregated metrics by route
    route_metrics = filtered_df.groupby('route_no').agg({
        'px_count': 'sum',
        'travelled_KM': 'sum',
        'px_total_amount': 'sum'
    }).reset_index()
    
    # Calculate passengers per km and revenue per km
    route_metrics['passengers_per_km'] = route_metrics['px_count'] / route_metrics['travelled_KM'].replace(0, 1)
    route_metrics['revenue_per_km'] = route_metrics['px_total_amount'] / route_metrics['travelled_KM'].replace(0, 1)
    
    # Sort by revenue per km
    route_metrics = route_metrics.sort_values('revenue_per_km', ascending=False)
    
    # Display metrics table
    st.subheader("Route Efficiency Metrics")
    
    metrics_styled = route_metrics.style.format({
        'px_count': '{:,.0f}',
        'travelled_KM': '{:,.1f} km',
        'px_total_amount': '₹{:,.2f}',
        'passengers_per_km': '{:,.2f}',
        'revenue_per_km': '₹{:,.2f}'
    }).background_gradient(subset=['passengers_per_km'], cmap='Blues')\
      .background_gradient(subset=['revenue_per_km'], cmap='Greens')
    
    st.dataframe(metrics_styled, use_container_width=True)
    
    # Visualization: Passengers/km vs Revenue/km
    st.subheader("Correlation: Passengers/km vs Revenue/km")
    
    fig1 = px.scatter(route_metrics, 
                     x='passengers_per_km', 
                     y='revenue_per_km',
                     size='px_total_amount',  # Size by total revenue
                     color='route_no',        # Color by route
                     hover_data=['travelled_KM', 'px_count'],
                     title="Efficiency Matrix: Passengers/km vs Revenue/km",
                     labels={
                         'passengers_per_km': 'Passengers per Kilometer',
                         'revenue_per_km': 'Revenue per Kilometer (₹)'
                     })
    
    fig1.update_layout(
        xaxis=dict(tickformat='.2f'),
        yaxis=dict(tickformat='₹,.2f')
    )
    
    # Add quadrant lines and annotations
    avg_passengers = route_metrics['passengers_per_km'].mean()
    avg_revenue = route_metrics['revenue_per_km'].mean()
    
    fig1.add_hline(y=avg_revenue, line_dash="dash", line_color="gray", 
                  annotation_text="Avg Revenue/km")
    fig1.add_vline(x=avg_passengers, line_dash="dash", line_color="gray", 
                  annotation_text="Avg Passengers/km")
    
    # Add quadrant labels
    fig1.add_annotation(x=avg_passengers*1.5, y=avg_revenue*1.5, 
                      text="High efficiency", showarrow=False, 
                      font=dict(size=12, color="green"))
    fig1.add_annotation(x=avg_passengers*0.5, y=avg_revenue*0.5, 
                      text="Low efficiency", showarrow=False, 
                      font=dict(size=12, color="red"))
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Dual Metrics Chart
    st.subheader("Comparison: Passengers/km and Revenue/km by Route")
    
    # Create figure with secondary y-axis
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add bar chart for passengers/km
    fig2.add_trace(
        go.Bar(
            x=route_metrics['route_no'],
            y=route_metrics['passengers_per_km'],
            name="Passengers/km",
            marker_color='royalblue'
        ),
        secondary_y=False
    )
    
    # Add line chart for revenue/km
    fig2.add_trace(
        go.Scatter(
            x=route_metrics['route_no'],
            y=route_metrics['revenue_per_km'],
            name="Revenue/km",
            marker_color='green',
            mode='lines+markers'
        ),
        secondary_y=True
    )
    
    # Set titles and labels
    fig2.update_layout(
        title="Route Performance: Passengers/km vs Revenue/km",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    fig2.update_xaxes(title_text="Route Number")
    fig2.update_yaxes(title_text="Passengers per km", secondary_y=False)
    fig2.update_yaxes(title_text="Revenue per km (₹)", secondary_y=True)
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Time-based Analysis
    st.subheader("Time-based Efficiency Analysis")
    
    # Group by date and calculate metrics
    date_metrics = filtered_df.groupby(filtered_df["ticket_datetime"].dt.date).agg({
        'px_count': 'sum',
        'travelled_KM': 'sum',
        'px_total_amount': 'sum'
    }).reset_index()
    
    date_metrics['passengers_per_km'] = date_metrics['px_count'] / date_metrics['travelled_KM'].replace(0, 1)
    date_metrics['revenue_per_km'] = date_metrics['px_total_amount'] / date_metrics['travelled_KM'].replace(0, 1)
    
    # Plot the time series
    fig3 = px.line(date_metrics, x="ticket_datetime", y=["passengers_per_km", "revenue_per_km"],
                  title="Daily Efficiency Metrics",
                  labels={
                      "ticket_datetime": "Date",
                      "value": "Metric Value",
                      "variable": "Metric Type"
                  })
    
    # Update y-axis format for revenue
    fig3.update_traces(
        yaxis="y2",
        selector=dict(name="revenue_per_km")
    )
    
    fig3.update_layout(
        yaxis_title="Passengers per km",
        yaxis2=dict(
            title="Revenue per km (₹)",
            overlaying="y",
            side="right"
        )
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # Additional analysis: Route recommendations based on metrics
    st.subheader("📋 Route Recommendations Based on Efficiency")
    
    recommendations = []
    for _, row in route_metrics.iterrows():
        if row['passengers_per_km'] > avg_passengers and row['revenue_per_km'] > avg_revenue:
            status = "⭐ High performing (Increase frequency)"
            color = "#C8E6C9"  # Light green
        elif row['passengers_per_km'] > avg_passengers and row['revenue_per_km'] < avg_revenue:
            status = "👥 High occupancy, low revenue (Review pricing)"
            color = "#FFF9C4"  # Light yellow
        elif row['passengers_per_km'] < avg_passengers and row['revenue_per_km'] > avg_revenue:
            status = "💰 High revenue, low occupancy (Premium service)"
            color = "#BBDEFB"  # Light blue
        else:
            status = "⚠️ Underperforming (Consider restructuring)"
            color = "#FFCDD2"  # Light red
        
        recommendations.append({
            "Route": row['route_no'],
            "Passengers/km": f"{row['passengers_per_km']:.2f}",
            "Revenue/km": f"₹{row['revenue_per_km']:.2f}",
            "Status": status,
            "Color": color
        })
    
    rec_df = pd.DataFrame(recommendations)
    
    # Style the recommendations table
    def color_status(val):
        for rec in recommendations:
            if val == rec['Status']:
                return f"background-color: {rec['Color']}"
        return ""
    
    st.dataframe(
        rec_df[["Route", "Passengers/km", "Revenue/km", "Status"]].style
        .applymap(color_status, subset=['Status']),
        use_container_width=True
    )


with tab9:
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
    col1.metric("Latest Month Revenue", f"₹{latest_month['Revenue']:,.2f}")
    col2.metric("Ticket Count", f"{latest_month['Ticket_Count']:,}")
    col3.metric("Revenue/km", f"₹{latest_month['Revenue_per_KM']:.2f}")
    
    # 3. Trend Charts
    st.subheader("Trend Analysis")
    
    fig1 = px.line(monthly_data.reset_index(), 
                 x='ticket_datetime', y='Revenue',
                 title="Monthly Revenue Trend",
                 labels={'ticket_datetime': 'Month', 'Revenue': 'Revenue (₹)'})
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
                      labels={'Revenue_per_KM': '₹/km'})
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        fig4 = px.line(monthly_data.reset_index(),
                      x='ticket_datetime', y='Avg_Ticket_Price',
                      title="Average Ticket Price",
                      labels={'Avg_Ticket_Price': 'Price (₹)'})
        st.plotly_chart(fig4, use_container_width=True)
    
    # 5. Data Table
    st.subheader("Monthly Data")
    st.dataframe(
        monthly_data.style.format({
            'Revenue': '₹{:,.2f}',
            'Revenue_per_KM': '₹{:,.2f}',
            'Avg_Ticket_Price': '₹{:,.2f}'
        }),
        use_container_width=True
    )




# Raw data table (all tabs)
st.sidebar.header("Raw Data Preview")
if st.sidebar.checkbox("Show raw data"):
    st.subheader("Filtered Raw Data")
    st.dataframe(filtered_df)