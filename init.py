import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="Transport Analytics Dashboard",
    page_icon="🚍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Main containers */
    .main-container {
        padding: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid #4e73df;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
        height: 120px;
    }
    .metric-title {
        color: #5a5c69;
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #2e59a9;
        font-size: 1.8rem;
        font-weight: 700;
        font-family: 'Arial', sans-serif;
    }
    
    /* Insight cards */
    .insight-card {
        background-color: #f0f8ff;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #4e73df;
    }
    .warning-card {
        background-color: #fff0f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #e74a3b;
    }
    
    /* Filters */
    .stMultiSelect [data-baseweb=select] span{
        max-width: 250px;
        font-size: 0.85rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# Load sample data (replace with your actual data loading)

@st.cache_data
def load_data():
    chunk_size = 75000
    all_chunks = []
    reader = pd.read_csv("data/cleaned_master.csv", chunksize=chunk_size)
    for i, chunk in enumerate(reader):
        print(f"Loading chunk {i+1} (up to {chunk_size*(i+1)} records)...")
        all_chunks.append(chunk)
        if i == 0: # Load the first chunk and process mappings
            master = chunk.copy()
            ticket_types = pd.read_csv("data/ticket_type.csv")
            service_types = pd.read_csv("data/service_type.csv")
            form_four = pd.read_csv("data/form_four_trip-6.csv")
            kms_mapping = form_four.set_index(['schedule_no', 'route_id'])['kms'].to_dict()

            # Map IDs to names
            master["ticket_type"] = master["ticket_type_short_code"].map(
                dict(zip(ticket_types["ticket_type_id"], ticket_types["ticket_type_name"])))
            master["service_type"] = master["bus_service_id"].map(
                dict(zip(service_types["service_type_id"], service_types["service_type_name"])))

            # Convert dates and calculate derived metrics
            master["ticket_datetime"] = pd.to_datetime(
                master["ticket_date"] + " " + master["ticket_time"])
            master["ticket_date"] = master["ticket_datetime"].dt.date  # Extract date for filtering

            # Calculate initial revenue per km and passengers per km (on the first chunk)
            master["revenue_per_km"] = master["px_total_amount"] / master["travelled_KM"].replace(0, 1)
            master["passengers_per_km"] = master["px_count"] / master["travelled_KM"].replace(0, 1)

            def update_travelled_km(row):
                key = (row['schedule_no'], row['route_id'])
                return kms_mapping.get(key, row['travelled_KM'])

            master['travelled_KM'] = master.apply(update_travelled_km, axis=1)
        elif i > 0: # For subsequent chunks, perform the same transformations
            chunk["ticket_type"] = chunk["ticket_type_short_code"].map(
                dict(zip(ticket_types["ticket_type_id"], ticket_types["ticket_type_name"])))
            chunk["service_type"] = chunk["bus_service_id"].map(
                dict(zip(service_types["service_type_id"], service_types["service_type_name"])))
            chunk["ticket_datetime"] = pd.to_datetime(
                chunk["ticket_date"] + " " + chunk["ticket_time"])
            chunk["ticket_date"] = chunk["ticket_datetime"].dt.date
            chunk["revenue_per_km"] = chunk["px_total_amount"] / chunk["travelled_KM"].replace(0, 1)
            chunk["passengers_per_km"] = chunk["px_count"] / chunk["travelled_KM"].replace(0, 1)
            chunk['travelled_KM'] = chunk.apply(update_travelled_km, axis=1)
            master = pd.concat([master, chunk]) # Concatenate with the main DataFrame
            print(f"Processed chunk {i+1} (up to {chunk_size*(i+1)} records).")
        if i == 0: # Only need to load supporting CSVs once
            ticket_types = pd.read_csv("data/ticket_type.csv")
            service_types = pd.read_csv("data/service_type.csv")
            form_four = pd.read_csv("data/form_four_trip-6.csv")
            kms_mapping = form_four.set_index(['schedule_no', 'route_id'])['kms'].to_dict()

    print("All data chunks loaded and processed.")
    return master

df = load_data()

# ====================
# SIDEBAR NAVIGATION
# ====================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Dashboard",
    ["Summary Overview",  "Fleet Monitoring",   
      "Route Performance","Route Optimization","Sustainability"],
    label_visibility="collapsed"
)


# Global filters in sidebar
st.sidebar.title("Global Filters")
date_range = st.sidebar.date_input(
    "📅 Date Range",
    value=[df['ticket_datetime'].min(), df['ticket_datetime'].max()],
    key="global_date_range"
)

service_types = st.sidebar.multiselect(
    "🔧 Service Types",
    options=df['service_type'].unique(),
    default=[],
    key="global_service_types"
)

# Apply global filters
if service_types: # Check if service_types list is not empty
    filtered_df = df[
        (df['ticket_datetime'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
        (df['service_type'].isin(service_types))
    ]
else:
     filtered_df = df[
        (df['ticket_datetime'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
    ]

# ====================
# PAGE 1: SUMMARY OVERVIEW
# ====================
if page == "Summary Overview":
    st.title("📊 Summary Overview")
    
    # Horizontal filters
    with st.container():
        cols = st.columns(4)
        with cols[0]:
            ticket_types = st.multiselect(
                "🎟️ Ticket Types",
                options=df['ticket_type'].unique(),
                default=[],
                key="summary_ticket_types"
            )
        with cols[1]:
            routes = st.multiselect(
                "🛣️ Routes (Optional)",
                options=df['route_no'].unique(),
                key="summary_routes"
            )
    
    # Apply additional filters
    summary_df = filtered_df.copy()
    if ticket_types:
        summary_df = summary_df[summary_df['ticket_type'].isin(ticket_types)]
    if routes:
        summary_df = summary_df[summary_df['route_no'].isin(routes)]
    
    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Passengers</div>
            <div class="metric-value">{summary_df['px_count'].sum():,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">₹{summary_df['px_total_amount'].sum():,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Distance</div>
            <div class="metric-value">{summary_df['travelled_KM'].sum():,.0f} KM</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg EPKM</div>
            <div class="metric-value">₹{summary_df['revenue_per_km'].mean():.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    tab1, tab2 = st.tabs(["Passenger Analysis", "Revenue Analysis"])
    
    with tab1:
        left_column, right_column = st.columns(2)

        # Top 5 Routes by Passengers
        route_passengers_top = summary_df.groupby('route_no')['px_count'].sum().nlargest(5).sort_values(ascending=False)
        top_colors = ['green'] * len(route_passengers_top)  # Color all bars green
        fig1_top = px.bar(
            route_passengers_top,
            y=route_passengers_top.index,
            x=route_passengers_top.values,
            color_discrete_sequence=top_colors,  # Apply the green color list
            title="<b>Top 5 Routes by Passenger Count</b>",
            labels={'x': 'Passengers', 'y': 'Route'},
            height=400
        )
        fig1_top.update_layout(
            xaxis_title="Passengers",
            yaxis_title="Route",
        )
        left_column.plotly_chart(fig1_top, use_container_width=True)

        # Bottom 5 Routes by Passengers
        route_passengers_bottom = summary_df.groupby('route_no')['px_count'].sum().nsmallest(5).sort_values(ascending=False)
        bottom_colors = ['red'] * len(route_passengers_bottom)  # Color all bars red
        fig1_bottom = px.bar(
            route_passengers_bottom,
            y=route_passengers_bottom.index,
            x=route_passengers_bottom.values,
            color_discrete_sequence=bottom_colors,  # Apply the red color list
            title="<b>Bottom 5 Routes by Passenger Count</b>",
            labels={'x': 'Passengers', 'y': 'Route'},
            height=400
        )
        fig1_bottom.update_layout(
            xaxis_title="Passengers",
            yaxis_title="Route",
        )
        right_column.plotly_chart(fig1_bottom, use_container_width=True)
    
    with tab2:
        # Revenue Trend
        daily_revenue = summary_df.resample('D', on='ticket_datetime')['px_total_amount'].sum()
        fig2 = px.line(
            daily_revenue,
            title="<b>Daily Revenue Trend</b>",
            labels={'value': 'Revenue (₹)', 'date': 'Date'},
            height=400
        )
        
        # Highlight top 3 days
        top_days = daily_revenue.nlargest(3)
        for date, value in top_days.items():
            fig2.add_annotation(
                x=date,
                y=value,
                text=f"Peak: ₹{value:,.0f}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40
            )
        
        st.plotly_chart(fig2, use_container_width=True)

# ====================
# PAGE 2: ROUTE PERFORMANCE
# ====================
elif page == "Route Performance":
    st.title("🛣️ Route Performance")
    
    # Horizontal filters
    with st.container():
        cols = st.columns(3)
        with cols[0]:
            selected_route = st.selectbox(
                "Select Route",
                options=sorted(filtered_df['route_no'].unique()),
                key="route_selector"
            )
    
    # Filter data for selected route
    route_df = filtered_df[filtered_df['route_no'] == selected_route]
    
    # Metrics cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Trips</div>
            <div class="metric-value">{route_df['trip_no'].nunique():,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Passengers</div>
            <div class="metric-value">{route_df['px_count'].sum():,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">₹{route_df['px_total_amount'].sum():,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    tab1, tab2 = st.tabs(["Schedule Efficiency", "Revenue Analysis"])
    
    with tab1:
        # Schedulewise EPKM
        schedule_stats = route_df.groupby('schedule_no').agg({
            'px_total_amount': 'sum',
            'travelled_KM': 'mean',
            'trip_no': 'nunique'
        }).reset_index()
        schedule_stats['epkm'] = schedule_stats['px_total_amount'] / schedule_stats['travelled_KM']
        
        fig1 = px.bar(
            schedule_stats.sort_values('epkm', ascending=False),
            x='schedule_no',
            y='epkm',
            color='epkm',
            color_continuous_scale='Viridis',
            title=f"<b>Schedule-wise EPKM for {selected_route}</b>",
            labels={'epkm': 'Revenue per KM (₹)', 'schedule_no': 'Schedule'},
            height=450
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        # Revenue vs Distance
        trip_stats = route_df.groupby('trip_no').agg({
            'px_total_amount': 'sum',
            'travelled_KM': 'mean',
            'px_count': 'sum'
        }).reset_index()
        
        fig2 = px.scatter(
            trip_stats,
            x='travelled_KM',
            y='px_total_amount',
            size='px_count',
            color='px_total_amount',
            hover_name='trip_no',
            title=f"<b>Revenue vs Distance for {selected_route}</b>",
            labels={
                'px_total_amount': 'Revenue (₹)',
                'travelled_KM': 'Distance (KM)',
                'px_count': 'Passengers'
            },
            color_continuous_scale='thermal',
            height=450
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Dynamic Insights
    st.subheader("Performance Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Performing Schedules**")
        top_schedules = schedule_stats.nlargest(3, 'epkm')
        for _, row in top_schedules.iterrows():
            st.markdown(f"""
            <div class="insight-card">
                🏆 <b>{row['schedule_no']}</b><br>
                ₹{row['epkm']:.2f} per KM | {row['trip_no']} trips
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Revenue Leakage Alerts**")
        avg_revenue = trip_stats['px_total_amount'].mean()
        low_rev_trips = trip_stats[trip_stats['px_total_amount'] < avg_revenue * 0.7]
        
        if not low_rev_trips.empty:
            for _, row in low_rev_trips.nsmallest(3, 'px_total_amount').iterrows():
                st.markdown(f"""
                <div class="warning-card">
                    ⚠️ <b>Trip {row['trip_no']}</b><br>
                    ₹{row['px_total_amount']:.2f} | {row['travelled_KM']:.1f} KM
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("No significant revenue leakage detected")

# ====================
# PAGE 4: ROUTE OPTIMIZATION
# ====================
elif page == "Route Optimization":
    st.title("📈 Route Optimization")
    
    # Filters in horizontal layout
    with st.container():
        cols = st.columns(3)
        with cols[0]:
            route_option = st.selectbox(
                "Select Route (Optional)",
                options=["All"] + sorted(filtered_df['route_no'].unique()),
                key="opt_route_selector"
            )
        with cols[1]:
            min_distance = st.number_input(
                "Min Distance (KM)",
                min_value=0,
                max_value=int(filtered_df['travelled_KM'].max()),
                value=0,
                key="opt_min_distance"
            )
        with cols[2]:
            max_distance = st.number_input(
                "Max Distance (KM)",
                min_value=0,
                max_value=int(filtered_df['travelled_KM'].max()),
                value=int(filtered_df['travelled_KM'].max()),
                key="opt_max_distance"
            )
    
    # Apply filters
    optimization_df = filtered_df.copy()
    if route_option != "All":
        optimization_df = optimization_df[optimization_df['route_no'] == route_option]
    
    optimization_df = optimization_df[
        (optimization_df['travelled_KM'] >= min_distance) &
        (optimization_df['travelled_KM'] <= max_distance)
    ]
    
    # Metrics
    avg_passenger_km = optimization_df['passengers_per_km'].mean()
    avg_revenue_km = optimization_df['revenue_per_km'].mean()
    efficiency_score = avg_revenue_km / avg_passenger_km if avg_passenger_km else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Passengers/KM</div>
            <div class="metric-value">{avg_passenger_km:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg Revenue/KM</div>
            <div class="metric-value">₹{avg_revenue_km:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Efficiency Score</div>
            <div class="metric-value">{efficiency_score:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    tab1, tab2, tab3 = st.tabs(["Passenger Density", "Revenue Efficiency", "Route Efficiency"])
    
    with tab1:
        # Passenger Density
        passenger_density = optimization_df.groupby('route_no')['passengers_per_km'].mean().sort_values(ascending=False).reset_index()
        fig1 = px.bar(
            passenger_density,
            x='route_no',
            y='passengers_per_km',
            title="<b>Passenger Density by Route</b>",
            labels={'passengers_per_km': 'Passengers per KM', 'route_no': 'Route'},
            height=450
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        # Revenue Efficiency
        revenue_efficiency = optimization_df.groupby('route_no')['revenue_per_km'].mean().sort_values(ascending=False).reset_index()
        fig2 = px.bar(
            revenue_efficiency,
            x='route_no',
            y='revenue_per_km',
            title="<b>Revenue per KM by Route</b>",
            labels={'revenue_per_km': 'Revenue per KM (₹)', 'route_no': 'Route'},
            height=450
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        # Route Efficiency Score
        route_efficiency = optimization_df.groupby('route_no').apply(lambda x: x['revenue_per_km'].mean() / x['passengers_per_km'].mean() if x['passengers_per_km'].mean() else 0).sort_values(ascending=False).reset_index(name='efficiency_score')
        fig3 = px.bar(
            route_efficiency,
            x='route_no',
            y='efficiency_score',
            title="<b>Route Efficiency Score</b>",
            labels={'efficiency_score': 'Efficiency Score', 'route_no': 'Route'},
            color='efficiency_score',
            color_continuous_scale='viridis',
            height=450
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # Dynamic Insights
    st.subheader("Optimization Insights")
    
    st.markdown("""
    Based on your selected filters, here are some potential route optimization suggestions:
    """, unsafe_allow_html=True)
    
    # Suggest routes to merge/cancel
    low_performing_routes = route_efficiency[route_efficiency['efficiency_score'] < 0.8]  # Example threshold
    if not low_performing_routes.empty:
        st.markdown(f"""
        <div class="warning-card">
            ⚠️ <b>Consider merging/cancelling the following routes:</b>
        </div>
        """, unsafe_allow_html=True)
        for _, route in low_performing_routes.iterrows():
            st.markdown(f"""
            <div class="insight-card">
                Route {route['route_no']} (Efficiency Score: {route['efficiency_score']:.2f})
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="insight-card">
            ✅ No routes identified for potential merging/cancellation based on the selected criteria.
        </div>
        """, unsafe_allow_html=True)
    
    # Suggest routes for extra buses
    high_density_routes = passenger_density[passenger_density['passengers_per_km'] > 5]  # Example threshold
    if not high_density_routes.empty:
        st.markdown(f"""
        <div class="insight-card">
            🚌 <b>Consider adding more buses to the following routes during peak hours:</b>
        </div>
        """, unsafe_allow_html=True)
        for _, route in high_density_routes.iterrows():
            st.markdown(f"""
            <div class="insight-card">
                Route {route['route_no']} (Passenger Density: {route['passengers_per_km']:.2f})
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="insight-card">
            ✅ No routes identified as needing additional buses based on the selected criteria.
        </div>
        """, unsafe_allow_html=True)


elif page == "Fleet Monitoring":
    st.title("🚌 Fleet Monitoring")
    
    # Filters
    with st.container():
        cols = st.columns(2)
        with cols[0]:
            selected_vehicle = st.selectbox(
                "Select Vehicle (Optional)",
                options=["All"] + sorted(df['vehicle_no'].unique()),
                key="fleet_vehicle_selector"
            )
        with cols[1]:
             date_range_form_four = st.date_input(
                "Date Range",
                value=(df['ticket_datetime'].min(), df['ticket_datetime'].max()),
                key = 'fleet_date_range'
            )
            
    # Filter data (assuming you have vehicle data in your main DataFrame)
    fleet_df = df.copy() #Using the main dataframe as the user did not provide a new one.
    
    if selected_vehicle != "All":
        fleet_df = fleet_df[fleet_df['vehicle_no'] == selected_vehicle]
    
    fleet_df = fleet_df[
        (fleet_df['ticket_datetime'].dt.date >= date_range_form_four[0]) & (fleet_df['ticket_datetime'].dt.date <= date_range_form_four[1])
    ]
        
    # Metrics (example calculations - adjust based on your actual data structure)
    total_distance = fleet_df['travelled_KM'].sum()
    total_trips = fleet_df['trip_no'].sum()
    
    # Calculate active and idle vehicles.  This assumes that if a vehicle has ANY trips in the filtered data, it is considered active.
    active_vehicles = fleet_df['vehicle_no'].unique().size
    total_vehicles = df['vehicle_no'].nunique() # Get the total number of unique vehicles from the entire dataset.
    idle_vehicles = total_vehicles - active_vehicles
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Distance</div>
            <div class="metric-value">{total_distance:,.0f} KM</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Trips</div>
            <div class="metric-value">{total_trips:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
   
    
    # Charts
    tab1, tab2 = st.tabs(["Vehicle Utilization", "Distance Trend"])
    
    with tab1:
        # Trips per Vehicle
        trips_per_vehicle = fleet_df.groupby('vehicle_no')['trip_no'].nunique().sort_values(ascending=False).reset_index(name='trips')
        fig1 = px.bar(
            trips_per_vehicle,
            x='vehicle_no',
            y='trips',
            title="<b>Trips Made per Vehicle</b>",
            labels={'trips': 'Number of Trips', 'vehicle_no': 'Vehicle'},
            height=450
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        # Distance Trend (Example: Monthly)
        distance_trend = fleet_df.groupby(fleet_df['ticket_datetime'].dt.to_period('M'))['travelled_KM'].sum().reset_index()
        distance_trend['ticket_datetime'] = distance_trend['ticket_datetime'].dt.to_timestamp()
        fig2 = px.line(
            distance_trend,
            x='ticket_datetime',
            y='travelled_KM',
            title="<b>Monthly Distance Travelled</b>",
            labels={'travelled_KM': 'Distance (KM)', 'ticket_datetime': 'Date'},
            height=450
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Dynamic Insights
    st.subheader("Fleet Insights")
    
    st.markdown("""
    Based on the selected filters, here are some fleet monitoring insights:
    """, unsafe_allow_html=True)
    
    # Detect underutilized buses
    avg_trips_per_vehicle = fleet_df.groupby('vehicle_no')['trip_no'].nunique().mean()
    underutilized_vehicles = trips_per_vehicle[trips_per_vehicle['trips'] < avg_trips_per_vehicle * 0.7] # Example threshold
    if not underutilized_vehicles.empty:
        st.markdown("<h4 style='color:red;'>⚠️ Underutilized Buses:</h4>", unsafe_allow_html=True)
        fig = px.bar(
            underutilized_vehicles,
            x='vehicle_no',
            y='trips',
            labels={'trips': 'Number of Trips', 'vehicle_no': 'Vehicle'},
            title="Underutilized Vehicles"
        )
        st.plotly_chart(fig)
       
    else:
        st.markdown(f"""
        <div class="insight-card">
            ✅ No underutilized vehicles detected based on the selected criteria.
        </div>
        """, unsafe_allow_html=True)
    
    # Detect overused buses
    overutilized_vehicles = trips_per_vehicle[trips_per_vehicle['trips'] > avg_trips_per_vehicle * 1.3]  # Example threshold
    if not overutilized_vehicles.empty:
        st.markdown(f"<h4 style='color:red;'>⚠️ Overused Buses:</h4>", unsafe_allow_html=True)
        fig = px.bar(
            overutilized_vehicles,
            x='vehicle_no',
            y='trips',
            labels={'trips': 'Number of Trips', 'vehicle_no': 'Vehicle'},
            title="Overutilized Vehicles"
        )
        st.plotly_chart(fig)
    else:
        st.markdown(f"""
        <div class="insight-card">
            ✅ No overused vehicles detected based on the selected criteria.
        </div>
        """, unsafe_allow_html=True)



# ====================
# PAGE 6: SUSTAINABILITY DASHBOARD
# ====================
elif page == "Sustainability":
    st.title("🌿 Sustainability Dashboard")
    
    # Horizontal filters
    with st.container():
        cols = st.columns(2)
        with cols[0]:
            # Use a single-select dropdown for Bus Type, with "All" option
            bus_type_option = st.selectbox(
                "Select Bus Type",
                options=["All", "EV INTERSTATE", "MANUAL LOCAL INTERSTATE"],  # Corrected options
                key="sustain_bus_type"
            )
    
    # Apply filters
    sustain_df = filtered_df.copy()
    
    # Filter by bus type.  Correctly apply the filter.
    if bus_type_option == "EV INTERSTATE":
        sustain_df = sustain_df[sustain_df['service_type'] == "EV INTERSTATE"]
    elif bus_type_option == "MANUAL LOCAL INTERSTATE":
        sustain_df = sustain_df[sustain_df['service_type'] == "MANUAL LOCAL INTERSTATE"]
    # "All" requires no filtering
    
    # 1.  Calculate total distance for EV and Diesel
    total_distance_ev = sustain_df[sustain_df['service_type'] == "EV INTERSTATE"]['travelled_KM'].sum()
    total_distance_diesel = sustain_df[sustain_df['service_type'] == "MANUAL LOCAL INTERSTATE"]['travelled_KM'].sum()
    total_distance_all = sustain_df['travelled_KM'].sum() # For CO2 savings calculation
    
    # 2.  CO2 Emissions (Estimates) - Simplified for demonstration
    # Assume a fixed emission factor for diesel and zero for EV.
    diesel_emission_factor = 0.3  # kg CO2 per KM (example value, replace with actual data)
    
    co2_emitted_diesel = total_distance_diesel * diesel_emission_factor
    co2_emitted_ev = 0  # EV emits zero CO2
    total_co2_emitted = co2_emitted_diesel + co2_emitted_ev
    
    # 3. CO2 Saved (Projected) - compared to if *all* were diesel.
    co2_emitted_all_diesel = total_distance_all * diesel_emission_factor
    co2_saved = co2_emitted_all_diesel - total_co2_emitted
    
    # Metrics Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">KM Driven (Diesel)</div>
            <div class="metric-value">{total_distance_diesel:,.0f} KM</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">KM Driven (EV)</div>
            <div class="metric-value">{total_distance_ev:,.0f} KM</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CO2 Emissions (Est.)</div>
            <div class="metric-value">{total_co2_emitted:,.0f} kg</div>
        </div>
        """, unsafe_allow_html=True)
    
    col4 = st.columns(1)
    with col4[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CO2 Saved (Projected)</div>
            <div class="metric-value">{co2_saved:,.0f} kg</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    
    
    # Dynamic Insights
    st.subheader("Sustainability Insights")
    
    if total_distance_ev > 0:
        st.markdown(f"""
        <div class="insight-card">
            ✅ EV buses have contributed to a reduction of {co2_saved:.0f} kg of CO2 emissions.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="insight-card">
            ⚠️ No EV buses in operation during the selected period. Consider increasing EV deployment to reduce emissions.
        </div>
        """, unsafe_allow_html=True)
    
    # Suggesting eco-friendly routes (simplified)
    # In a real scenario, you'd have data on route-specific emissions.
    st.markdown("💡 **Potential Eco-Friendly Routes:**", unsafe_allow_html=True)
    
    #  Suggest top 3 routes with highest EV KM.
    route_ev_km = sustain_df[sustain_df['service_type'] == 'EV INTERSTATE'].groupby('route_no')['travelled_KM'].sum().sort_values(ascending=False)
    
    if not route_ev_km.empty:
        for route, distance in route_ev_km.head(3).items(): #show top 3 routes
            st.markdown(f"""
            <div class="insight-card">
                Route {route}: {distance:.0f} KM (EV)
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("No EV bus operation on any route during this period.",unsafe_allow_html=True)

# ====================
# DATA EXPORT
# ====================
with st.sidebar:
    st.download_button(
        label="⬇️ Export Data",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name=f"transport_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        use_container_width=True
    )
