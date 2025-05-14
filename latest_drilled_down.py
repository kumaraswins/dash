import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
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
        df = pd.read_excel("data/city_dashboard_datewise_data.xlsx")
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
    numeric_cols = ['total_amount', 'travel_distance', 'trip_number'] # Include trip_number
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
st.title("🚍 FTransport Performance Dashboard")
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
        default=[], # Default to all months
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
        default=[] # Default to all days
    )

with col3:
    service_filter = st.multiselect(
        "Service Type",
        options=color_lines,
        default=[] # Default to all service types
    )

with col4:
    route_filter = st.multiselect(
        "Route",
        options=route_options,
        default=[] # Default to all routes
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
    # Add new tabs for analysis
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([ # Added tab6
        "Monthly View",
        "Daily Pattern",
        "Schedule-wise EPKM",
        "Trips per Schedule by Date (Bar Chart)",
        "Route Performance",
        "Daily Passenger Trend" # New tab title
    ])

    with tab1:
        st.markdown("#### Monthly Revenue Trend")
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

            

            st.markdown("---")
            st.markdown("##### Drill Down: Daily Trend for a Specific Month")
            # Add a selectbox to choose a month for drill-down
            selected_month_drilldown = st.selectbox(
                "Select a Month to see Daily Trend",
                options=['Select a Month'] + available_months,
                key='monthly_daily_drilldown' # Unique key
            )

            if selected_month_drilldown != 'Select a Month':
                # Filter data for the selected month
                daily_data_for_month = filtered_df[filtered_df['month'] == selected_month_drilldown]

                if not daily_data_for_month.empty:
                    # Group by date and sum revenue for the selected month
                    daily_revenue_drilldown = daily_data_for_month.groupby('running_date')['total_amount'].sum().reset_index()

                    fig_daily_drilldown = px.line(
                        daily_revenue_drilldown,
                        x='running_date',
                        y='total_amount',
                        title=f"Daily Revenue Trend for {selected_month_drilldown}",
                        labels={'total_amount': 'Revenue (₹)', 'running_date': 'Date'}
                    )
                    st.plotly_chart(fig_daily_drilldown, use_container_width=True)
                else:
                    st.info(f"No data available for daily trend in {selected_month_drilldown} with current filters.")


        else:
            st.info("No data available for monthly revenue trend.")


    with tab2:
        st.markdown("#### Average Daily Revenue by Month")
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

            

            st.markdown("---")
            st.markdown("##### Drill Down: Filter by Specific Day(s) of Week")
            # Add a multiselect to filter by specific days of the week
            selected_days_drilldown = st.multiselect(
                "Select Day(s) of Week to Highlight",
                options=day_options,
                default=[],
                key='daily_day_filter' # Unique key
            )

            if selected_days_drilldown:
                # Filter data for the selected days
                daily_data_filtered_days = daily_revenue[daily_revenue['day_of_week'].isin(selected_days_drilldown)]

                if not daily_data_filtered_days.empty:
                     fig_daily_filtered = px.bar(
                        daily_data_filtered_days,
                        x='day_of_week',
                        y='total_amount',
                        color='month',
                        barmode='group',
                        category_orders={"day_of_week": day_options},
                        title=f"Average Daily Revenue for Selected Days ({', '.join(selected_days_drilldown)}) by Month",
                        labels={'total_amount': 'Average Revenue (₹)', 'day_of_week': 'Day of Week'}
                    )
                     st.plotly_chart(fig_daily_filtered, use_container_width=True)
                else:
                    st.info("No data available for the selected days of the week with current filters.")


        else:
            st.info("No data available for daily revenue pattern.")

    with tab3:
        st.markdown("#### Average EPKM by Schedule")
        # Ensure data exists before plotting
        if not filtered_df.empty:
            # Calculate average EPKM per schedule number
            schedule_epkm = filtered_df.groupby('schedule_number')['Epkm'].mean().reset_index()

            # Sort by average EPKM for better visualization (optional)
            schedule_epkm = schedule_epkm.sort_values('Epkm', ascending=False)

            fig = px.bar(
                schedule_epkm,
                x='schedule_number',
                y='Epkm',
                title="Average EPKM per Schedule Number",
                labels={'Epkm': 'Average EPKM (₹/km)', 'schedule_number': 'Schedule Number'}
            )
            st.plotly_chart(fig, use_container_width=True)

            

            st.markdown("---")
            st.markdown("##### Drill Down: Compare Specific Schedules")
            # Add a multiselect to filter by specific schedules
            selected_schedules_drilldown = st.multiselect(
                "Select Schedule(s) to Compare",
                options=sorted(filtered_df['schedule_number'].unique().tolist()),
                default=[],
                key='schedule_compare_filter' # Unique key
            )

            if selected_schedules_drilldown:
                # Filter data for the selected schedules
                schedule_data_filtered = filtered_df[filtered_df['schedule_number'].isin(selected_schedules_drilldown)]

                if not schedule_data_filtered.empty:
                    # Calculate average EPKM for the selected schedules
                    schedule_epkm_filtered = schedule_data_filtered.groupby('schedule_number')['Epkm'].mean().reset_index()

                    fig_schedule_drilldown = px.bar(
                        schedule_epkm_filtered,
                        x='schedule_number',
                        y='Epkm',
                        title=f"Average EPKM for Selected Schedules ({', '.join(map(str, selected_schedules_drilldown))})",
                        labels={'Epkm': 'Average EPKM (₹/km)', 'schedule_number': 'Schedule Number'}
                    )
                    st.plotly_chart(fig_schedule_drilldown, use_container_width=True)
                else:
                    st.info("No data available for the selected schedules with current filters.")


        else:
            st.info("No data available for schedule-wise EPKM analysis.")

    with tab4: # This is now the 'Trips per Schedule by Date (Bar Chart)' tab
        st.markdown("#### Total Trips per Schedule by Date ")

        # Add Route filter specifically for this tab
        route_filter_tab4 = st.multiselect(
            "Select Route(s) for this chart",
            options=route_options,
            default=route_options[0], # Default to all routes for this tab
            key='route_filter_tab4' # Changed key to reflect new tab number
        )

        # Apply the route filter for this tab
        tab4_filtered_df = filtered_df[filtered_df['route_no'].isin(route_filter_tab4)].copy()

        # Add Schedule filter specifically for this tab
        schedule_options_tab4 = sorted(tab4_filtered_df['schedule_number'].unique().tolist())
        schedule_filter_tab4 = st.multiselect(
            "Select Schedule(s) for this chart",
            options=schedule_options_tab4,
            default=schedule_options_tab4, # Default to all schedules for this tab
            key='schedule_filter_tab4' # Add a unique key
        )

        # Apply the schedule filter for this tab
        tab4_filtered_df = tab4_filtered_df[tab4_filtered_df['schedule_number'].isin(schedule_filter_tab4)].copy()


        # Ensure data exists after applying tab-specific filter before plotting
        if not tab4_filtered_df.empty:
            # Group by date and schedule, find the max trip number for each group
            trips_per_schedule_day_bar = tab4_filtered_df.groupby(['running_date', 'schedule_number'])['trip_number'].max().reset_index()

            # Create a bar chart showing max trip number over time for each schedule
            fig = px.bar(
                trips_per_schedule_day_bar,
                x='running_date',
                y='trip_number',
                color='schedule_number', # Use schedule_number for different bars/colors
                title="Total Trips per Schedule by Date",
                labels={'running_date': 'Date', 'trip_number': 'Total Trips', 'schedule_number': 'Schedule Number'},
                hover_name='schedule_number', # Add hover name
                hover_data={'running_date': True, 'trip_number': True, 'schedule_number': False} # Add hover data
            )

            # Improve layout for date axis if needed (optional)
            fig.update_layout(xaxis_title="Date", yaxis_title="Total Trips")

            st.plotly_chart(fig, use_container_width=True)

            # Add table below the chart
            st.markdown("##### Data Table for Trips per Schedule")
            st.dataframe(trips_per_schedule_day_bar)

            

        else:
            st.info("No data available for trips per schedule analysis with the selected route(s) and schedule(s).")

    with tab5: # This is now the 'Route Performance' tab
        st.markdown("#### Route Performance Overview")

        # Add a selectbox to choose a route for drill-down
        selected_route_drilldown = st.selectbox(
            "Select a Route to see Performance by Day of Week",
            options=['Select a Route'] + sorted(filtered_df['route_no'].unique().tolist()),
            key='route_performance_drilldown' # Unique key
        )

        if selected_route_drilldown != 'Select a Route':
            st.markdown(f"##### Performance by Day of Week for Route {selected_route_drilldown}")
            # Filter data for the selected route
            route_data_drilldown = filtered_df[filtered_df['route_no'] == selected_route_drilldown]

            if not route_data_drilldown.empty:
                # Group by day of week and calculate metrics
                route_grouped_df = route_data_drilldown.groupby('day_of_week', observed=True).agg(
                    Total_Revenue=('total_amount', 'sum'),
                    Total_Passengers=('total_count', 'sum'),
                    Average_EPKM=('Epkm', 'mean')
                ).reindex(day_options).fillna(0).reset_index() # Reindex to ensure all days are present and ordered


                # Display trend charts for the selected route
                if not route_grouped_df.empty:
                    fig_route_revenue_day = px.bar( # Changed to bar chart
                        route_grouped_df,
                        x='day_of_week',
                        y='Total_Revenue',
                        title=f"Revenue by Day of Week for Route {selected_route_drilldown}",
                        labels={'Total_Revenue': 'Revenue (₹)', 'day_of_week': 'Day of Week'},
                         category_orders={"day_of_week": day_options} # Ensure correct day order
                    )
                    st.plotly_chart(fig_route_revenue_day, use_container_width=True)

                    fig_route_passengers_day = px.bar( # Changed to bar chart
                        route_grouped_df,
                        x='day_of_week',
                        y='Total_Passengers',
                        title=f"Passengers by Day of Week for Route {selected_route_drilldown}",
                        labels={'Total_Passengers': 'Passengers', 'day_of_week': 'Day of Week'},
                        category_orders={"day_of_week": day_options} # Ensure correct day order
                    )
                    st.plotly_chart(fig_route_passengers_day, use_container_width=True)

                    fig_route_epkm_day = px.bar( # Changed to bar chart
                        route_grouped_df,
                        x='day_of_week',
                        y='Average_EPKM',
                        title=f"EPKM by Day of Week for Route {selected_route_drilldown}",
                        labels={'Average_EPKM': 'Average EPKM (₹/km)', 'day_of_week': 'Day of Week'},
                        category_orders={"day_of_week": day_options} # Ensure correct day order
                    )
                    st.plotly_chart(fig_route_epkm_day, use_container_width=True)

                else:
                    st.info(f"No data available for day of week performance for Route {selected_route_drilldown} with current filters.")


        st.markdown("---") # Separator for drill-down section

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

    with tab6: # New tab for Comparative Daily Revenue Analysis
        # st.markdown("#### Comparative Daily Revenue Analysis")

        # # Ensure data exists before calculation and plotting
        # if not filtered_df.empty:
        #     # Create monthly and weekly aggregates
        #     monthly_avg = filtered_df.groupby(
        #         pd.Grouper(key='running_date', freq='M')
        #     )['total_amount'].mean().reset_index()
        #     monthly_avg['period_type'] = 'Monthly'
        #     monthly_avg['period_label'] = monthly_avg['running_date'].dt.strftime('%b %Y')

        #     weekly_avg = filtered_df.groupby(
        #         pd.Grouper(key='running_date', freq='W-MON')
        #     )['total_amount'].mean().reset_index()
        #     weekly_avg['period_type'] = 'Weekly'
        #     weekly_avg['period_label'] = weekly_avg['running_date'].dt.strftime('Week of %b %d, %Y')

        #     # Combine data
        #     combined_data = pd.concat([monthly_avg, weekly_avg])

        #     # Create date range selector
        #     min_date = filtered_df['running_date'].min()
        #     max_date = filtered_df['running_date'].max()

        #     col1, col2 = st.columns(2)
        #     with col1:
        #         start_date = st.date_input(
        #             "Start Date",
        #             value=min_date,
        #             min_value=min_date,
        #             max_value=max_date,
        #             key='comp_start_date' # Unique key
        #         )
        #     with col2:
        #         end_date = st.date_input(
        #             "End Date",
        #             value=max_date,
        #             min_value=min_date,
        #             max_value=max_date,
        #             key='comp_end_date' # Unique key
        #         )

        #     # Filter data based on selection
        #     combined_data = combined_data[
        #         (combined_data['running_date'] >= pd.to_datetime(start_date)) &
        #         (combined_data['running_date'] <= pd.to_datetime(end_date))
        #     ]

        #     # Visualization
        #     if not combined_data.empty:
        #         fig = px.line(
        #             combined_data,
        #             x='running_date',
        #             y='total_amount',
        #             color='period_type',
        #             line_dash='period_type',
        #             hover_name='period_label',
        #             hover_data={
        #                 'running_date': False,
        #                 'total_amount': ':.2f',
        #                 'period_type': False,
        #                 'period_label': False
        #             },
        #             labels={
        #                 'total_amount': 'Average Daily Revenue (₹)',
        #                 'running_date': 'Date',
        #                 'period_type': 'Aggregation Period'
        #             },
        #             title="Comparative Daily Revenue Trends"
        #         )

        #         # Add range slider
        #         fig.update_layout(
        #             xaxis=dict(
        #                 rangeselector=dict(
        #                     buttons=list([
        #                         dict(count=1, label="1m", step="month", stepmode="backward"),
        #                         dict(count=3, label="3m", step="month", stepmode="backward"),
        #                         dict(count=6, label="6m", step="month", stepmode="backward"),
        #                         dict(step="all")
        #                     ])
        #                 ),
        #                 rangeslider=dict(visible=True),
        #                 type="date"
        #             )
        #         )

        #         st.plotly_chart(fig, use_container_width=True)

        #         # Add explanatory text
        #         st.markdown("""
        #         **How to use this analysis:**
        #         - Compare the blue (monthly) and red (weekly) trend lines
        #         - Use the date range selectors above to focus on specific periods
        #         - Hover over data points to see exact values and time periods
        #         - Use the range slider below the chart to zoom in/out

        #         **Key insights to look for:**
        #         - Consistency between weekly and monthly trends
        #         - Seasonal patterns visible in monthly data
        #         - Short-term fluctuations visible in weekly data
        #         - Significant deviations between weekly and monthly averages
        #         """)

        #         # Optional: Show data table
        #         with st.expander("View Raw Data"):
        #             st.dataframe(combined_data.sort_values('running_date'))
        #     else:
        #         st.info("No data available for the selected date range.")

        # else:
        #     st.info("No data available for revenue trend comparison.")

        st.markdown("#### Daily Passenger Trend Analysis")
    
        if not filtered_df.empty:
            # Create analysis type selector
            analysis_type = st.radio(
                "Select Analysis Type",
                options=["Day-of-Week Pattern", "Monthly Trend", "Route Comparison", "Passenger vs Revenue Correlation"],
                horizontal=True
            )
            
            if analysis_type == "Day-of-Week Pattern":
                st.markdown("##### Passenger Distribution by Day of Week")
                
                # Calculate average passengers by day of week
                daily_pattern = filtered_df.groupby('day_of_week', observed=True).agg(
                    avg_passengers=('total_count', 'mean'),
                    total_passengers=('total_count', 'sum')
                ).reindex(day_options).reset_index()
                
                # Create visualization
                fig = px.bar(
                    daily_pattern,
                    x='day_of_week',
                    y='avg_passengers',
                    color='day_of_week',
                    title="Average Daily Passengers by Day of Week",
                    labels={'avg_passengers': 'Average Passengers', 'day_of_week': 'Day of Week'},
                    category_orders={"day_of_week": day_options}
                )
                
                # Add line for total passengers (secondary axis)
                fig.add_trace(go.Scatter(
                    x=daily_pattern['day_of_week'],
                    y=daily_pattern['total_passengers'],
                    name='Total Passengers',
                    line=dict(color='black', width=2),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    yaxis2=dict(
                        title='Total Passengers',
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                **Insights:**
                - Compare average (blue bars) vs total (black line) passenger patterns
                - Identify peak days for passenger volume
                - Weekday vs weekend patterns
                """)
                
                # Add drill-down by service type
                if st.checkbox("Breakdown by Service Type", key='service_breakdown'):
                    service_pattern = filtered_df.groupby(['day_of_week', 'service_type'])['total_count'].mean().unstack()
                    fig = px.bar(
                        service_pattern,
                        barmode='group',
                        title="Passenger Distribution by Day and Service Type",
                        labels={'value': 'Average Passengers', 'day_of_week': 'Day of Week'},
                        category_orders={"day_of_week": day_options}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            elif analysis_type == "Monthly Trend":
                st.markdown("##### Monthly Passenger Trend")
                
                # Calculate monthly trends
                monthly_trend = filtered_df.groupby(pd.Grouper(key='running_date', freq='M')).agg(
                    total_passengers=('total_count', 'sum'),
                    avg_daily_passengers=('total_count', 'mean')
                ).reset_index()
                
                # Create visualization
                fig = px.line(
                    monthly_trend,
                    x='running_date',
                    y=['total_passengers', 'avg_daily_passengers'],
                    title="Monthly Passenger Trends",
                    labels={'value': 'Passengers', 'running_date': 'Month'},
                    markers=True
                )
                
                # Add bar chart for total passengers
                fig.add_trace(go.Bar(
                    x=monthly_trend['running_date'],
                    y=monthly_trend['total_passengers'],
                    name='Total Passengers',
                    opacity=0.3,
                    marker_color='lightgray'
                ))
                
                fig.update_layout(
                    hovermode='x unified',
                    yaxis_title='Passenger Count'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                **Insights:**
                - Overall monthly trends (gray bars)
                - Average daily passengers (line)
                - Seasonal patterns and anomalies
                """)
                
                # Add YoY comparison if data spans multiple years
                if filtered_df['running_date'].dt.year.nunique() > 1:
                    if st.checkbox("Show Year-over-Year Comparison"):
                        yoy_data = filtered_df.copy()
                        yoy_data['year'] = yoy_data['running_date'].dt.year
                        yoy_data['month'] = yoy_data['running_date'].dt.month_name()
                        
                        fig = px.line(
                            yoy_data.groupby(['year', 'month'])['total_count'].sum().reset_index(),
                            x='month',
                            y='total_count',
                            color='year',
                            title="Year-over-Year Monthly Comparison",
                            category_orders={"month": available_months}
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            elif analysis_type == "Route Comparison":
                st.markdown("##### Route Performance Analysis")
                
                # Calculate route statistics
                route_stats = filtered_df.groupby('route_no').agg(
                    total_passengers=('total_count', 'sum'),
                    avg_passengers=('total_count', 'mean'),
                    epkm=('Epkm', 'mean')
                ).reset_index()
                
                # Create scatter plot
                fig = px.scatter(
                    route_stats,
                    x='avg_passengers',
                    y='epkm',
                    size='total_passengers',
                    color='route_no',
                    hover_name='route_no',
                    title="Route Efficiency Analysis",
                    labels={
                        'avg_passengers': 'Average Passengers per Trip',
                        'epkm': 'Revenue per Kilometer (EPKM)',
                        'total_passengers': 'Total Passengers'
                    }
                )
                
                # Add reference lines
                avg_passengers = route_stats['avg_passengers'].mean()
                avg_epkm = route_stats['epkm'].mean()
                fig.add_hline(y=avg_epkm, line_dash="dot", annotation_text=f"Avg EPKM: {avg_epkm:.2f}")
                fig.add_vline(x=avg_passengers, line_dash="dot", annotation_text=f"Avg Passengers: {avg_passengers:.1f}")
                
                st.plotly_chart(fig, use_container_width=True)
                
               
                # Add top/bottom performers tables
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Top 5 Routes by Passengers**")
                    st.dataframe(
                        route_stats.nlargest(5, 'total_passengers')[['route_no', 'total_passengers']]
                        .style.format({'total_passengers': '{:,.0f}'})
                    )
                
                with col2:
                    st.markdown("**Top 5 Routes by EPKM**")
                    st.dataframe(
                        route_stats.nlargest(5, 'epkm')[['route_no', 'epkm']]
                        .style.format({'epkm': '₹{:.2f}'})
                    )
            
            elif analysis_type == "Passenger vs Revenue Correlation":
                st.markdown("##### Passenger Count vs Revenue Relationship")
                
                # Calculate correlation
                correlation = filtered_df['total_count'].corr(filtered_df['total_amount'])
                
                # Create scatter plot
                fig = px.scatter(
                    filtered_df,
                    x='total_count',
                    y='total_amount',
                    trendline="ols",
                    color='service_type',
                    hover_data=['route_no', 'running_date'],
                    title=f"Passenger-Revenue Relationship (Correlation: {correlation:.2f})",
                    labels={
                        'total_count': 'Passenger Count',
                        'total_amount': 'Revenue (₹)'
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                
                
                # Add breakdown by service type
                if st.checkbox("Show Breakdown by Service Type"):
                    service_correlations = filtered_df.groupby('service_type').apply(
                        lambda x: x['total_count'].corr(x['total_amount'])
                    ).reset_index(name='correlation')
                    
                    fig = px.bar(
                        service_correlations,
                        x='service_type',
                        y='correlation',
                        color='service_type',
                        title="Passenger-Revenue Correlation by Service Type",
                        labels={'correlation': 'Correlation Coefficient'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("No data available for passenger trend analysis.")


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
