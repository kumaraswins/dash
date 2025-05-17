import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
import numpy as np # Import numpy for handling NaN and inf
import base64 # For embedding images/icons if needed (though SVGs/Emojis preferred)

# Configure page settings
st.set_page_config(
    page_title="Transport Analytics Dashboard",
    page_icon="🚍", # Using an emoji icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for improved aesthetics and spacing
st.markdown("""
<style>
    /* General body styling */
    body {
        font-family: 'Inter', sans-serif; /* Using a modern font */
        background-color: #f4f7f9; /* Light background */
        color: #333;
    }

    /* Header styling */
    .stApp > header {
        background-color: #ffffff; /* White header */
        padding: 10px 20px;
        border-bottom: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Title styling */
    h1 {
        color: #2c3e50; /* Dark blue heading */
        font-weight: 700;
        margin-bottom: 5px;
    }

    /* Subheader styling */
    h2, h3, h4 {
        color: #34495e; /* Slightly lighter blue */
        margin-top: 20px;
        margin-bottom: 15px;
        border-bottom: 1px solid #ecf0f1; /* Subtle separator */
        padding-bottom: 5px;
    }

    /* Metric card styling */
    .metric-card {
        padding: 20px; /* Increased padding */
        border-radius: 10px; /* More rounded corners */
        background-color: #ffffff; /* White background */
        box-shadow: 0 4px 8px rgba(0,0,0,0.08); /* Softer shadow */
        margin-bottom: 20px; /* Increased margin */
        border: 1px solid #dcdcdc; /* Subtle border */
        transition: transform 0.2s ease-in-out; /* Add hover effect */
    }
    .metric-card:hover {
        transform: translateY(-5px); /* Lift card on hover */
    }
    .metric-title {
        font-size: 15px; /* Slightly larger font */
        color: #7f8c8d; /* Muted grey */
        font-weight: 500;
        margin-bottom: 8px; /* Space below title */
    }
    .metric-value {
        font-size: 28px; /* Larger value font */
        font-weight: 700;
        color: #2c3e50; /* Dark blue */
    }

    /* Plot container styling */
    .plot-container {
        background-color: #ffffff; /* White background */
        padding: 20px; /* Increased padding */
        border-radius: 10px; /* Rounded corners */
        box-shadow: 0 2px 6px rgba(0,0,0,0.05); /* Subtle shadow */
        margin-bottom: 30px; /* Increased margin */
        border: 1px solid #dcdcdc; /* Subtle border */
    }

    /* Filter section styling */
    .stMultiSelect, .stSelectbox, .stSlider, .stCheckbox, .stRadio {
        margin-bottom: 15px; /* Space below filter elements */
    }

    /* Expander styling */
    .stExpander {
        border: 1px solid #dcdcdc;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
    }

    /* Table styling in dataframes */
    .stDataFrame {
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border-radius: 8px;
        overflow: hidden; /* Ensures rounded corners apply */
    }

    /* Improve spacing around elements */
    .stVerticalBlock {
        gap: 1.5rem; /* Increase vertical spacing between blocks */
    }

    /* Custom button styling (example) */
    .stButton>button {
        background-color: #3498db; /* Blue button */
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2980b9; /* Darker blue on hover */
    }

</style>
""", unsafe_allow_html=True)





@st.cache_data
def load_data():
    """
    Loads data from an Excel file, performs data cleaning and preparation.
    Caches the data to improve performance.
    """
    # Read Excel file
    # Assuming the Excel file is named 'city_dashboard_datewise_data.xlsx' and is in a 'data' subdirectory
    try:
        df = pd.read_excel("data/city_dashboard_datewise_data.xlsx")
        #st.success("Data loaded successfully!")
    except FileNotFoundError:
        st.error("Error: Data file not found. Please make sure 'city_dashboard_datewise_data.xlsx' is in a 'data' subdirectory.")
        st.stop() # Stop execution if file is not found
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        st.stop()

    # --- Data Cleaning and Preparation ---

    # Convert 'running_date' to datetime, coercing errors to NaT (Not a Time)
    df['running_date'] = pd.to_datetime(df['running_date'], errors='coerce')
    # Drop rows where 'running_date' is NaT
    df.dropna(subset=['running_date'], inplace=True)

    # Create date-related columns
    df['month'] = df['running_date'].dt.month_name()
    df['day_of_week'] = df['running_date'].dt.day_name()
    df['service_type'] = df['color_line'] # Rename for clarity if needed later

    # Ensure critical numeric columns are numeric, coercing errors to NaN
    numeric_cols = ['total_amount', 'travel_distance', 'trip_number', 'total_count', 'running_time']
    for col in numeric_cols:
        # Check if column exists before attempting conversion
        if col in df.columns:
             df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            st.warning(f"Column '{col}' not found in data. Skipping numeric conversion for this column.")
            # Add the column with default 0s if it's critical for later steps
            if col in ['total_amount', 'travel_distance', 'trip_number', 'total_count']:
                 df[col] = 0 # Add column with default value

    # Calculate Epkm (Earnings per Kilometer)
    # Handle potential division by zero and NaN values
    # Use .copy() to avoid SettingWithCopyWarning
    df_cleaned = df.copy()

    # Calculate raw Epkm, will result in inf for division by zero and NaN for NaNs
    # Add a small epsilon to travel_distance to avoid exact division by zero
    epsilon = 1e-9
    df_cleaned['Epkm'] = df_cleaned['total_amount'] / (df_cleaned['travel_distance'] + epsilon)

    # Replace infinite values (division by zero) with 0
    df_cleaned['Epkm'] = df_cleaned['Epkm'].replace([np.inf, -np.inf], 0)

    # Replace NaN values (from division with NaN or other issues) with 0
    df_cleaned['Epkm'] = df_cleaned['Epkm'].fillna(0)

    # Round the final Epkm values for display
    df_cleaned['Epkm'] = df_cleaned['Epkm'].round(2)

    # Ensure total_count and trip_number are treated as integers where appropriate
    for col in ['total_count', 'trip_number']:
         if col in df_cleaned.columns:
             # Use Int64 to allow for NaN values before filling
             df_cleaned[col] = df_cleaned[col].astype('Int64').fillna(0)


    # Drop rows with NaN in critical numeric columns after coercion and Epkm calculation
    # Only drop if the column exists
    critical_cols_to_check = [col for col in ['total_amount', 'travel_distance', 'Epkm', 'total_count', 'trip_number'] if col in df_cleaned.columns]
    df_cleaned.dropna(subset=critical_cols_to_check, inplace=True)

    # Check if data is empty after cleaning
    if df_cleaned.empty:
        st.error("Error: No valid data remaining after processing. Please check your data file for correct formats and missing values in critical columns.")
        st.stop()

    return df_cleaned

# Load data
df = load_data()

# Get filter options from the loaded data
# Ensure only months present in the data are options
available_months = sorted(df['month'].unique(),
                        key=lambda x: datetime.strptime(x, "%B").month)
day_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
              'Friday', 'Saturday', 'Sunday']
color_lines = df['service_type'].unique()
route_options = sorted(df['route_no'].unique().tolist()) # Sort route options

# Dashboard Header
st.title("🚍 KTCL Performance Dashboard")
st.markdown("""
<div style="margin-bottom: 30px; font-size: 1.1em; color: #555;">
    Comprehensive analysis of passenger traffic and revenue performance for KTCL.
</div>
""", unsafe_allow_html=True)

# Filters Section
st.markdown("### Data Filters")
st.markdown("Select criteria below to filter the dashboard data.")

# Use columns for filters for better layout
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    # Month selection
    month_filter = st.multiselect(
        "Select Month(s)",
        options=available_months,
        default=[], # Default to all months
        help="Filter data by selecting one or more months."
    )

    # Weekly drill-down for selected months - only show if data is not empty and exactly one month is selected
    week_filter = None # Initialize week_filter
    # Check if exactly one month is selected and if there's data for that month
    if len(month_filter) == 1 and not df[df['month'].isin(month_filter)].empty:
        selected_month_num = datetime.strptime(month_filter[0], "%B").month
        month_df = df[df['running_date'].dt.month == selected_month_num].copy() # Use .copy()
        if not month_df.empty:
             # Calculate week numbers relative to the start of the year (ISO week)
             week_options = sorted(month_df['running_date'].dt.isocalendar().week.unique())

             week_filter = st.multiselect(
                 "Select Week(s) (within selected month)",
                 options=week_options,
                 default=week_options, # Default to all weeks in the selected month
                 help="Compare specific weeks within the selected month."
             )
        else:
             st.info(f"No data found for {month_filter[0]} to show weekly breakdown.")


with filter_col2:
    day_filter = st.multiselect(
        "Select Day(s) of Week",
        options=day_options,
        default=[], # Default to all days
        help="Filter data by selecting one or more days of the week."
    )

with filter_col3:
    service_filter = st.multiselect(
        "Select Service Type(s)",
        options=color_lines,
        default=[], # Default to all service types
        help="Filter data by selecting one or more service types (e.g., Red, Blue)."
    )

with filter_col4:
    route_filter = st.multiselect(
        "Select Route(s)",
        options=route_options,
        default=[], # Default to all routes
        help="Filter data by selecting one or more route numbers."
    )

# Apply filters
# Start with a condition that includes all rows
filter_condition = pd.Series(True, index=df.index)

# Apply month filter if not empty
if month_filter:
    filter_condition = filter_condition & (df['month'].isin(month_filter))

# Apply weekly filter if applicable and not empty
# Check if week_filter is not None (meaning a single month was selected) and if it's not empty
if week_filter is not None and week_filter:
     # Ensure the weekly filter is applied only to the data already filtered by month
     # This prevents applying week numbers from other months if the user clears the month filter after selecting weeks
     filter_condition = filter_condition & (df['running_date'].dt.isocalendar().week.isin(week_filter))
elif week_filter is not None and not week_filter:
     # If weekly filter is shown but empty, it means the user explicitly deselected all weeks
     # In this case, the filter condition should exclude all rows for weekly data within the selected month
     # However, the simpler approach is that if week_filter is an empty list, the condition `isin([])` will evaluate to False for all rows,
     # effectively filtering out everything related to the weekly selection.
     # The check `week_filter is not None` handles the case where the weekly filter wasn't even displayed.
     pass # No action needed if week_filter is empty, the isin([]) check handles it.


# Apply day filter if not empty
if day_filter:
    filter_condition = filter_condition & (df['day_of_week'].isin(day_filter))

# Apply service filter if not empty
if service_filter:
    filter_condition = filter_condition & (df['service_type'].isin(service_filter))

# Apply route filter if not empty
if route_filter:
    filter_condition = filter_condition & (df['route_no'].isin(route_filter))


# Apply the combined filter condition to get the final filtered DataFrame
# Use .copy() to avoid SettingWithCopyWarning in subsequent operations
filtered_df = df[filter_condition].copy()

# Check if filtered_df is empty after applying filters
if filtered_df.empty:
    st.warning("⚠️ No data available for the selected filters. Please adjust your filter criteria.")
    st.stop() # Stop execution if no data matches filters


# Metrics Section
st.markdown("### Key Performance Indicators (KPIs)")
st.markdown("Overview of key transport metrics based on current filters.")

# Use columns for KPI cards
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5) # 5 columns for 5 KPIs

# Calculate metrics only if filtered_df is not empty (already checked above, but good practice)
if not filtered_df.empty:
    total_trips = filtered_df.shape[0] # Count of rows after filtering represents total trips
    total_passengers = filtered_df['total_count'].sum()
    total_revenue = filtered_df['total_amount'].sum()
    total_distance = filtered_df['travel_distance'].sum()
    # Calculate average running time if column exists and is numeric
    average_running_time = filtered_df['running_time'].mean() if 'running_time' in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df['running_time']) and not filtered_df['running_time'].isnull().all() else 0 # Added average running time
    avg_epkm = filtered_df['Epkm'].mean() if not filtered_df['Epkm'].isnull().all() else 0 # Handle case where Epkm might be empty after filtering
else:
    total_trips = 0
    total_passengers = 0
    total_revenue = 0
    total_distance = 0
    average_running_time = 0
    avg_epkm = 0

with kpi_col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Trips</div>
            <div class="metric-value">{total_trips:,}</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Passengers</div>
            <div class="metric-value">{total_passengers:,}</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">₹{total_revenue:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Distance</div>
            <div class="metric-value">{total_distance:,.0f} km</div>
        </div>
    """, unsafe_allow_html=True)

with kpi_col5:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Avg EPKM</div>
            <div class="metric-value">₹{avg_epkm:.2f}</div>
        </div>
    """, unsafe_allow_html=True)

# Visualization Section
st.markdown("## Performance Analysis")
st.markdown("Explore detailed performance metrics and trends.")

# Use a container for the tabs to keep them visually grouped
with st.container():
    st.markdown('<div class="plot-container">', unsafe_allow_html=True) # Use the plot-container class for tabs
    # Add new tabs for analysis
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 Monthly Trends",
        "☀️ Daily Patterns",
        "⏱️ Schedule EPKM",
        "🚌 Trips per Schedule",
        "🗺️ Route Performance",
        "👥 Passenger Trends",
        "💰 EPKM Analysis"
    ])

    with tab1:
        st.markdown("#### Monthly Revenue and Passenger Trends")
        st.markdown("Analyze how revenue and passenger counts change over months.")
        # Ensure data exists before plotting
        if not filtered_df.empty:
            monthly_agg = filtered_df.groupby('month').agg(
                total_amount=('total_amount', 'sum'),
                total_count=('total_count', 'sum')
            ).reindex(available_months).reset_index()

            # Create a combined chart with two y-axes
            fig = go.Figure()

            # Add Revenue line
            fig.add_trace(go.Scatter(
                x=monthly_agg['month'],
                y=monthly_agg['total_amount'],
                mode='lines+markers',
                name='Total Revenue',
                yaxis='y1',
                line=dict(color='#3498db') # Blue color
            ))

            # Add Passenger line (on secondary y-axis)
            fig.add_trace(go.Scatter(
                x=monthly_agg['month'],
                y=monthly_agg['total_count'],
                mode='lines+markers',
                name='Total Passengers',
                yaxis='y2',
                line=dict(color='#2ecc71') # Green color
            ))

            # Update layout for dual y-axes
            fig.update_layout(
                title="Monthly Revenue and Passenger Trend",
                xaxis_title="Month",
                yaxis=dict(
                    #titlefont=dict(color='#3498db'),
                    title=dict(
                        text='Revenue (₹)',
                        font=dict(
                            size=16,
                            color='#3498db',
                            family='Arial'
                        )
                    ),
                    tickfont=dict(
                        size=14,
                        color='#3498db',
                        family='Verdana'
                    ),
                ),
                yaxis2=dict(
                    title='Passengers',
                    tickfont=dict(
                        size=14,
                        color='#2ecc71',
                        family='Verdana'
                    ),
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified', # Show tooltip for both traces on hover
                legend=dict(x=0.01, y=0.99), # Position legend
                plot_bgcolor='rgba(0,0,0,0)' # Transparent background
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.markdown("##### Drill Down: Daily Trend for a Specific Month")
            st.markdown("Select a month to view the daily fluctuations in revenue.")
            # Add a selectbox to choose a month for drill-down
            selected_month_drilldown = st.selectbox(
                "Select a Month to see Daily Trend",
                options=['Select a Month'] + available_months,
                key='monthly_daily_drilldown' # Unique key
            )

            if selected_month_drilldown != 'Select a Month':
                # Filter data for the selected month
                daily_data_for_month = filtered_df[filtered_df['month'] == selected_month_drilldown].copy() # Use .copy()

                if not daily_data_for_month.empty:
                    # Group by date and sum revenue for the selected month
                    daily_revenue_drilldown = daily_data_for_month.groupby('running_date')['total_amount'].sum().reset_index()

                    fig_daily_drilldown = px.line(
                        daily_revenue_drilldown,
                        x='running_date',
                        y='total_amount',
                        title=f"Daily Revenue Trend for {selected_month_drilldown}",
                        labels={'total_amount': 'Revenue (₹)', 'running_date': 'Date'},
                        line_shape='linear', # Ensure linear interpolation
                        markers=True
                    )
                    fig_daily_drilldown.update_layout(
                         xaxis_title="Date",
                         yaxis_title="Revenue (₹)",
                         plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_daily_drilldown, use_container_width=True)
                else:
                    st.info(f"No data available for daily trend in {selected_month_drilldown} with current filters.")
        else:
            st.info("No data available for monthly trends with current filters.")


    with tab2:
        st.markdown("#### Average Daily Revenue and Passengers by Day of Week")
        st.markdown("Understand the typical performance pattern across different days of the week.")
        # Ensure data exists before plotting
        if not filtered_df.empty:
            daily_pattern_agg = filtered_df.groupby('day_of_week', observed=True).agg(
                avg_revenue=('total_amount', 'mean'),
                avg_passengers=('total_count', 'mean')
            ).reindex(day_options).fillna(0).reset_index() # Reindex to ensure all days are present and ordered

            # Create a combined bar chart
            fig = go.Figure(data=[
                go.Bar(name='Average Revenue', x=daily_pattern_agg['day_of_week'], y=daily_pattern_agg['avg_revenue'], marker_color='#3498db'),
                go.Bar(name='Average Passengers', x=daily_pattern_agg['day_of_week'], y=daily_pattern_agg['avg_passengers'], marker_color='#2ecc71')
            ])

            # Update layout
            fig.update_layout(
                barmode='group', # Group bars by day
                title="Average Daily Revenue and Passengers by Day of Week",
                xaxis_title="Day of Week",
                yaxis_title="Average Value",
                xaxis={'categoryorder':'array', 'categoryarray':day_options}, # Ensure correct day order
                legend=dict(x=0.01, y=0.99),
                plot_bgcolor='rgba(0,0,0,0)'
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.markdown("##### Drill Down: Average Daily Revenue by Month")
            st.markdown("Compare average daily revenue across months for each day of the week.")
            # Add a multiselect to filter by specific days of the week for this drilldown
            selected_days_drilldown_tab2 = st.multiselect(
                "Select Day(s) of Week to Highlight (for Monthly Comparison)",
                options=day_options,
                default=[],
                key='daily_day_filter_tab2' # Unique key for this tab's drilldown
            )

            if not filtered_df.empty:
                daily_revenue_by_month = filtered_df.groupby(['month', 'day_of_week'], observed=True).agg({
                    'total_amount': 'mean'
                }).reset_index()

                # Apply drilldown filter if selected
                if selected_days_drilldown_tab2:
                    daily_revenue_by_month = daily_revenue_by_month[
                        daily_revenue_by_month['day_of_week'].isin(selected_days_drilldown_tab2)
                    ]

                if not daily_revenue_by_month.empty:
                     fig_daily_filtered = px.bar(
                        daily_revenue_by_month,
                        x='day_of_week',
                        y='total_amount',
                        color='month',
                        barmode='group',
                        category_orders={"day_of_week": day_options, "month": available_months},
                        title=f"Average Daily Revenue by Month ({'Selected Days' if selected_days_drilldown_tab2 else 'All Days'})",
                        labels={'total_amount': 'Average Revenue (₹)', 'day_of_week': 'Day of Week', 'month': 'Month'}
                    )
                     fig_daily_filtered.update_layout(plot_bgcolor='rgba(0,0,0,0)')
                     st.plotly_chart(fig_daily_filtered, use_container_width=True)
                else:
                    st.info("No data available for the selected days of the week with current filters.")
            else:
                 st.info("No data available for daily revenue pattern.")


    with tab3:
        st.markdown("""
        <div style="border-bottom: 1px solid #e0e0e0; padding-bottom: 10px; margin-bottom: 25px;">
            <h2 style="color: #2c3e50; font-weight: 600;">Schedule Efficiency Analysis (EPKM)</h2>
            <p style="color: #7f8c8d; font-size: 15px;">Detailed analysis of revenue efficiency per schedule (Earnings per Kilometer).</p>
        </div>
        """, unsafe_allow_html=True)

        if not filtered_df.empty:
            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown("##### Controls")
                # Filter controls
                min_trips = st.slider(
                    "Minimum Trips per Schedule",
                    min_value=0,
                    # Ensure max value is based on actual data, default to a reasonable number if data is small
                    max_value=int(filtered_df['trip_number'].max()) if filtered_df['trip_number'].max() > 0 else 10,
                    value=5,
                    help="Filter schedules with at least this many trips to ensure meaningful averages."
                )

                show_annotations = st.checkbox(
                    "Show EPKM Values on Bars",
                    value=True,
                    help="Display the average EPKM value directly on each bar."
                )

                compare_mode = st.radio(
                    "Comparison View",
                    options=["Absolute Values", "vs. System Average"],
                    index=0,
                    horizontal=True,
                    help="Compare schedule EPKM values directly or against the overall system average."
                )

            with col2:
                # Calculate schedule statistics
                schedule_stats = filtered_df.groupby('schedule_number').agg(
                    avg_epkm=('Epkm', 'mean'),
                    total_trips=('trip_number', 'count'), # Count of records for the schedule
                    total_revenue=('total_amount', 'sum'),
                    total_distance=('travel_distance', 'sum')
                ).reset_index()

                # Apply minimum trips filter
                schedule_stats = schedule_stats[schedule_stats['total_trips'] >= min_trips].copy() # Use .copy()

                if not schedule_stats.empty:
                    # Create visualization
                    fig = px.bar(
                        schedule_stats.sort_values('avg_epkm', ascending=False),
                        x='schedule_number',
                        y='avg_epkm',
                        color='avg_epkm', # Color by EPKM value
                        color_continuous_scale='Viridis', # Use a color scale
                        hover_data={
                            'schedule_number': True,
                            'avg_epkm': ':.2f',
                            'total_trips': True,
                            'total_revenue': ':.0f',
                            'total_distance': ':.0f'
                        },
                        labels={
                            'avg_epkm': 'Average EPKM (₹/km)',
                            'schedule_number': 'Schedule Number'
                        },
                        title="Average EPKM by Schedule Number"
                    )

                    if compare_mode == "vs. System Average":
                        system_avg = filtered_df['Epkm'].mean()
                        fig.add_hline(
                            y=system_avg,
                            line_dash="dot",
                            line_color="#e74c3c", # Red color for average line
                            annotation_text=f"System Average: ₹{system_avg:.2f}",
                            annotation_position="bottom right"
                        )

                    if show_annotations:
                        fig.update_traces(
                            texttemplate='₹%{y:.2f}',
                            textposition='outside' # Position text outside the bars
                        )

                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', # Transparent background
                        xaxis_title="Schedule Number",
                        yaxis_title="Average EPKM (₹/km)",
                        coloraxis_showscale=False, # Hide color scale bar if coloring by y-value
                        xaxis={'categoryorder': 'total descending'}, # Order bars by value
                        hoverlabel=dict(
                            bgcolor="white",
                            font_size=12,
                            font_family="Arial"
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                    # Performance summary using markdown and f-strings for formatting
                    st.markdown("##### Schedule Performance Summary")
                    if not schedule_stats.empty:
                        top_schedule = schedule_stats.nlargest(1, 'avg_epkm').iloc[0]
                        bottom_schedule = schedule_stats.nsmallest(1, 'avg_epkm').iloc[0]
                        median_epkm = schedule_stats['avg_epkm'].median()

                        st.markdown(f"""
                        <div style="background-color: #e9ecef; padding: 15px; border-radius: 8px; margin-top: 20px;">
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                                <div style="background-color: white; padding: 10px; border-radius: 5px; border-left: 4px solid #2ecc71;">
                                    <div style="font-size: 12px; color: #7f8c8d;">Top Performing Schedule (EPKM)</div>
                                    <div style="font-size: 18px; font-weight: bold; color: #2c3e50;">{top_schedule['schedule_number']}</div>
                                    <div style="font-size: 12px; color: #7f8c8d;">EPKM: ₹{top_schedule['avg_epkm']:.2f} | Trips: {top_schedule['total_trips']:.0f}</div>
                                </div>
                                <div style="background-color: white; padding: 10px; border-radius: 5px; border-left: 4px solid #f39c12;">
                                    <div style="font-size: 12px; color: #7f8c8d;">Median EPKM</div>
                                    <div style="font-size: 18px; font-weight: bold; color: #2c3e50;">₹{median_epkm:.2f}</div>
                                    <div style="font-size: 12px; color: #7f8c8d;">50% of schedules perform above this value.</div>
                                </div>
                                <div style="background-color: white; padding: 10px; border-radius: 5px; border-left: 4px solid #e74c3c;">
                                    <div style="font-size: 12px; color: #7f8c8d;">Bottom Performing Schedule (EPKM)</div>
                                    <div style="font-size: 18px; font-weight: bold; color: #2c3e50;">{bottom_schedule['schedule_number']}</div>
                                    <div style="font-size: 12px; color: #7f8c8d;">EPKM: ₹{bottom_schedule['avg_epkm']:.2f} | Trips: {bottom_schedule['total_trips']:.0f}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                         st.info("No schedules meet the minimum trip threshold for summary.")


                    # Trend analysis
                    st.markdown("---")
                    st.markdown("#### Schedule EPKM Trend Over Time")
                    st.markdown("Track the EPKM performance of selected schedules over the filtered time period.")

                    # Get top schedules by EPKM to pre-select
                    default_selected_schedules = schedule_stats.nlargest(3, 'avg_epkm')['schedule_number'].tolist()
                    # Ensure default selections are actually in the filtered data
                    default_selected_schedules = [s for s in default_selected_schedules if s in filtered_df['schedule_number'].unique()]


                    selected_schedules_trend = st.multiselect(
                        "Select Schedules to Compare Trends",
                        options=sorted(schedule_stats['schedule_number'].unique().tolist()), # Sort options
                        default=default_selected_schedules,
                        key='schedule_trend_multiselect' # Unique key
                    )

                    if selected_schedules_trend:
                        # Filter data for selected schedules and group by date
                        trend_data = filtered_df[filtered_df['schedule_number'].isin(selected_schedules_trend)].copy() # Use .copy()
                        if not trend_data.empty:
                            trend_data_grouped = trend_data.groupby(['running_date', 'schedule_number'])['Epkm'].mean().reset_index()

                            fig = px.line(
                                trend_data_grouped,
                                x='running_date',
                                y='Epkm',
                                color='schedule_number',
                                markers=True,
                                labels={'Epkm': 'Average EPKM (₹/km)', 'running_date': 'Date', 'schedule_number': 'Schedule'},
                                color_discrete_sequence=px.colors.qualitative.Pastel, # Use a different color palette
                                title="Average Daily EPKM Trend for Selected Schedules"
                            )

                            fig.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                xaxis_title="Date",
                                yaxis_title="Average EPKM (₹/km)",
                                hovermode="x unified"
                            )

                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        else:
                             st.info("No data available for the selected schedules' trends with current filters.")

                    else:
                        st.info("Please select at least one schedule to view the trend.")


                else:
                    st.markdown("""
                    <div style="text-align: center; padding: 40px; background-color: #f8f9fa; border-radius: 8px;">
                        <h4 style="color: #7f8c8d;">No schedules meet the minimum trip threshold</h4>
                        <p style="color: #bdc3c7;">Try adjusting the minimum trips filter or checking the main data filters.</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; background-color: #f8f9fa; border-radius: 8px;">
                <h4 style="color: #7f8c8d;">No data available for Schedule EPKM analysis</h4>
                <p style="color: #bdc3c7;">Try adjusting your main filter criteria.</p>
            </div>
            """, unsafe_allow_html=True)


    with tab4:
        st.markdown("#### Total Trips per Schedule by Date")
        st.markdown("Visualize the number of trips completed by each schedule on a daily basis.")

        # Add Route filter specifically for this tab
        route_filter_tab4 = st.multiselect(
            "Filter by Route(s) for this chart",
            options=route_options,
            default=[], # Default to no routes selected, user must choose
            key='route_filter_tab4', # Unique key
            help="Select one or more routes to narrow down the schedules shown."
        )

        # Apply the route filter for this tab
        tab4_filtered_df = filtered_df.copy() # Start with the main filtered data
        if route_filter_tab4:
             tab4_filtered_df = tab4_filtered_df[tab4_filtered_df['route_no'].isin(route_filter_tab4)].copy() # Use .copy()
        else:
             st.info("Please select at least one route to view trips per schedule.")
             # Display empty state if no routes are selected
             tab4_filtered_df = pd.DataFrame() # Empty DataFrame to prevent errors below


        # Add Schedule filter specifically for this tab (dependent on route filter)
        if not tab4_filtered_df.empty:
            schedule_options_tab4 = sorted(tab4_filtered_df['schedule_number'].unique().tolist())
            schedule_filter_tab4 = st.multiselect(
                "Filter by Schedule(s) for this chart",
                options=schedule_options_tab4,
                default=schedule_options_tab4, # Default to all schedules within selected routes
                key='schedule_filter_tab4', # Add a unique key
                help="Select specific schedules to display."
            )

            # Apply the schedule filter for this tab
            if schedule_filter_tab4:
                tab4_filtered_df = tab4_filtered_df[tab4_filtered_df['schedule_number'].isin(schedule_filter_tab4)].copy() # Use .copy()
            else:
                 st.info("Please select at least one schedule to view trips.")
                 tab4_filtered_df = pd.DataFrame() # Empty DataFrame

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
                hover_data={'running_date': True, 'trip_number': True, 'schedule_number': False}, # Add hover data
                barmode='stack' # Stack bars if multiple schedules are selected for a day
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Total Trips",
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Add table below the chart
            st.markdown("##### Data Table for Trips per Schedule")
            st.dataframe(trips_per_schedule_day_bar)

        elif route_filter_tab4 and schedule_filter_tab4:
             st.info("No data available for the selected routes and schedules with current main filters.")
        # else: info messages are handled by the filter checks above


    with tab5:
        st.markdown("#### Route Performance Overview")
        st.markdown("Analyze key metrics aggregated by route.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Top Routes by Passenger Count")
            # Ensure data exists before plotting
            if not filtered_df.empty:
                # Group by route and sum passengers, get top 10
                route_passengers = filtered_df.groupby('route_no')['total_count'].sum().nlargest(10).reset_index()
                if not route_passengers.empty:
                    fig = px.bar(
                        route_passengers,
                        x='route_no',
                        y='total_count',
                        title="Top 10 Routes by Total Passenger Count",
                        labels={'total_count': 'Total Passengers', 'route_no': 'Route Number'},
                        color='total_count', # Color by passenger count
                        color_continuous_scale='Plasma' # Use a color scale
                    )
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Route Number", yaxis_title="Total Passengers")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No route data available for passenger count.")
            else:
                st.info("No data available for route passenger performance with current filters.")

        with col2:
            st.markdown("##### Top Routes by Revenue Efficiency (EPKM)")
            # Ensure data exists before plotting
            if not filtered_df.empty:
                # Group by route and calculate mean EPKM, get top 10
                route_epkm = filtered_df.groupby('route_no')['Epkm'].mean().nlargest(10).reset_index()
                if not route_epkm.empty:
                    fig = px.bar(
                        route_epkm,
                        x='route_no',
                        y='Epkm',
                        title="Top 10 Routes by Average EPKM",
                        labels={'Epkm': 'Average EPKM (₹/km)', 'route_no': 'Route Number'},
                         color='Epkm', # Color by EPKM value
                         color_continuous_scale='Viridis' # Use a color scale
                    )
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Route Number", yaxis_title="Average EPKM (₹/km)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No route data available for EPKM efficiency.")
            else:
                st.info("No data available for route EPKM efficiency with current filters.")

        st.markdown("---") # Separator for drill-down section
        st.markdown("##### Drill Down: Performance by Day of Week for a Specific Route")
        st.markdown("Select a route to see its performance breakdown by day.")
        # Add a selectbox to choose a route for drill-down
        selected_route_drilldown = st.selectbox(
            "Select a Route",
            options=['Select a Route'] + sorted(filtered_df['route_no'].unique().tolist()),
            key='route_performance_drilldown' # Unique key
        )

        if selected_route_drilldown != 'Select a Route':
            st.markdown(f"###### Performance Metrics by Day of Week for Route {selected_route_drilldown}")
            # Filter data for the selected route
            route_data_drilldown = filtered_df[filtered_df['route_no'] == selected_route_drilldown].copy() # Use .copy()

            if not route_data_drilldown.empty:
                # Group by day of week and calculate metrics
                route_grouped_df = route_data_drilldown.groupby('day_of_week', observed=True).agg(
                    Total_Revenue=('total_amount', 'sum'),
                    Total_Passengers=('total_count', 'sum'),
                    Average_EPKM=('Epkm', 'mean')
                ).reindex(day_options).fillna(0).reset_index() # Reindex to ensure all days are present and ordered and fill NaNs with 0

                # Display trend charts for the selected route
                if not route_grouped_df.empty:
                    fig_route_revenue_day = px.bar(
                        route_grouped_df,
                        x='day_of_week',
                        y='Total_Revenue',
                        title=f"Revenue by Day of Week for Route {selected_route_drilldown}",
                        labels={'Total_Revenue': 'Revenue (₹)', 'day_of_week': 'Day of Week'},
                         category_orders={"day_of_week": day_options}, # Ensure correct day order
                         color='Total_Revenue', # Color by revenue
                         color_continuous_scale='Plasma'
                    )
                    fig_route_revenue_day.update_layout(plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_route_revenue_day, use_container_width=True)

                    fig_route_passengers_day = px.bar(
                        route_grouped_df,
                        x='day_of_week',
                        y='Total_Passengers',
                        title=f"Passengers by Day of Week for Route {selected_route_drilldown}",
                        labels={'Total_Passengers': 'Passengers', 'day_of_week': 'Day of Week'},
                        category_orders={"day_of_week": day_options}, # Ensure correct day order
                        color='Total_Passengers', # Color by passengers
                        color_continuous_scale='Plasma'
                    )
                    fig_route_passengers_day.update_layout(plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_route_passengers_day, use_container_width=True)

                    fig_route_epkm_day = px.bar(
                        route_grouped_df,
                        x='day_of_week',
                        y='Average_EPKM',
                        title=f"EPKM by Day of Week for Route {selected_route_drilldown}",
                        labels={'Average_EPKM': 'Average EPKM (₹/km)', 'day_of_week': 'Day of Week'},
                        category_orders={"day_of_week": day_options}, # Ensure correct day order
                        color='Average_EPKM', # Color by EPKM
                        color_continuous_scale='Viridis'
                    )
                    fig_route_epkm_day.update_layout(plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_route_epkm_day, use_container_width=True)

                else:
                    st.info(f"No data available for day of week performance for Route {selected_route_drilldown} with current filters.")
            else:
                 st.info(f"No data available for Route {selected_route_drilldown} with current filters.")


    with tab6:
        st.markdown("#### Daily Passenger Trend Analysis")
        st.markdown("Analyze passenger trends across different dimensions.")

        if not filtered_df.empty:
            # Create analysis type selector
            analysis_type = st.radio(
                "Select Analysis Type",
                options=["Day-of-Week Pattern", "Monthly Trend", "Route Comparison", "Passenger vs Revenue Correlation"],
                horizontal=True,
                key='passenger_analysis_type' # Unique key
            )

            st.markdown("---") # Separator

            if analysis_type == "Day-of-Week Pattern":
                st.markdown("##### Average Passenger Distribution by Day of Week")
                st.markdown("View the typical passenger volume on each day.")

                # Calculate average passengers by day of week
                daily_pattern = filtered_df.groupby('day_of_week', observed=True).agg(
                    avg_passengers=('total_count', 'mean'),
                    total_passengers=('total_count', 'sum') # Include total for comparison
                ).reindex(day_options).reset_index()

                # Create visualization
                fig = go.Figure()

                # Add Bar chart for Average Passengers
                fig.add_trace(go.Bar(
                    x=daily_pattern['day_of_week'],
                    y=daily_pattern['avg_passengers'],
                    name='Average Passengers',
                    marker_color='#3498db' # Blue color
                ))

                # Add Line for Total Passengers (secondary axis)
                fig.add_trace(go.Scatter(
                    x=daily_pattern['day_of_week'],
                    y=daily_pattern['total_passengers'],
                    name='Total Passengers',
                    mode='lines+markers',
                    line=dict(color='black', width=2, dash='dot'),
                    yaxis='y2' # Assign to secondary y-axis
                ))

                fig.update_layout(
                    title="Average vs. Total Daily Passengers by Day of Week",
                    xaxis_title="Day of Week",
                    yaxis=dict(
                        title='Average Passengers',
                        #titlefont=dict(color='#3498db'),
                        #tickfont=dict(color='#3498db')
                    ),
                    yaxis2=dict(
                        title='Total Passengers',
                        #titlefont=dict(color='black'),
                        #tickfont=dict(color='black'),
                        
                        overlaying='y',
                        side='right'
                    ),
                    xaxis={'categoryorder':'array', 'categoryarray':day_options},
                    hovermode='x unified',
                    legend=dict(x=0.01, y=0.99),
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                st.plotly_chart(fig, use_container_width=True)

                st.markdown("""
                **Insights:**
                - Compare the average daily passenger count (blue bars) with the total passenger count (black dotted line) for each day.
                - Identify which days typically have higher or lower passenger traffic.
                - The black line shows the cumulative effect of the number of trips on that day across the filtered period.
                """)

                # Add drill-down by service type
                st.markdown("---")
                st.markdown("###### Breakdown by Service Type")
                if st.checkbox("Show Average Passenger Breakdown by Service Type", key='service_breakdown_passenger'):
                    service_pattern = filtered_df.groupby(['day_of_week', 'service_type'], observed=True)['total_count'].mean().unstack()
                    if not service_pattern.empty:
                        fig = px.bar(
                            service_pattern,
                            barmode='group',
                            title="Average Passenger Distribution by Day and Service Type",
                            labels={'value': 'Average Passengers', 'day_of_week': 'Day of Week', 'service_type': 'Service Type'},
                            category_orders={"day_of_week": day_options},
                            color_discrete_sequence=px.colors.qualitative.Safe # Use a colorblind-friendly palette
                        )
                        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No data available for service type breakdown with current filters.")


            elif analysis_type == "Monthly Trend":
                st.markdown("##### Monthly Passenger Trend")
                st.markdown("Track the total and average daily passenger counts over time.")

                # Calculate monthly trends
                # Group by the start of the month
                monthly_trend = filtered_df.groupby(pd.Grouper(key='running_date', freq='M')).agg(
                    total_passengers=('total_count', 'sum'),
                    avg_daily_passengers=('total_count', 'mean') # Average passenger count per record (trip) in that month
                ).reset_index()

                # Create visualization
                fig = go.Figure()

                # Add Total Passengers Bar chart
                fig.add_trace(go.Bar(
                    x=monthly_trend['running_date'],
                    y=monthly_trend['total_passengers'],
                    name='Total Passengers (Month)',
                    opacity=0.5,
                    marker_color='#bdc3c7' # Light gray bars
                ))

                # Add Average Daily Passengers Line chart
                fig.add_trace(go.Scatter(
                    x=monthly_trend['running_date'],
                    y=monthly_trend['avg_daily_passengers'],
                    name='Average Passengers (per Trip)',
                    mode='lines+markers',
                    line=dict(color='#3498db', width=2), # Blue line
                    yaxis='y2' # Assign to secondary y-axis
                ))


                fig.update_layout(
                    title="Monthly Total and Average Passenger Trends",
                    xaxis_title="Month",
                    yaxis=dict(
                        title='Total Passengers',
                        #titlefont=dict(color='#bdc3c7'),
                        #tickfont=dict(color='#bdc3c7')
                    ),
                     yaxis2=dict(
                        title=dict(
                            font=dict(
                                color='#3498db',
                                family='Arial'
                            )
                        ),
                        tickfont=dict(
                            size=14,
                            color='#3498db',
                            family='Verdana'
                        ),
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified',
                    legend=dict(x=0.01, y=0.99),
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                st.plotly_chart(fig, use_container_width=True)

                st.markdown("""
                **Insights:**
                - The gray bars show the total passenger volume for each month.
                - The blue line shows the average number of passengers per trip recorded within that month, indicating trip efficiency.
                - Observe seasonal patterns or significant changes over time.
                """)


                # Add YoY comparison if data spans multiple years
                if filtered_df['running_date'].dt.year.nunique() > 1:
                    st.markdown("---")
                    st.markdown("###### Year-over-Year Monthly Comparison")
                    if st.checkbox("Show Year-over-Year Monthly Passenger Comparison"):
                        yoy_data = filtered_df.copy()
                        yoy_data['year'] = yoy_data['running_date'].dt.year
                        yoy_data['month_name'] = yoy_data['running_date'].dt.month_name() # Use a different column name

                        # Group by year and month name
                        yoy_grouped = yoy_data.groupby(['year', 'month_name'])['total_count'].sum().reset_index()

                        fig = px.line(
                            yoy_grouped,
                            x='month_name',
                            y='total_count',
                            color='year',
                            title="Year-over-Year Monthly Passenger Comparison",
                            labels={'total_count': 'Total Passengers', 'month_name': 'Month', 'year': 'Year'},
                            category_orders={"month_name": available_months}, # Ensure correct month order
                            markers=True,
                            color_discrete_sequence=px.colors.qualitative.Vivid # Use a distinct color palette
                        )
                        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Data does not span multiple years for Year-over-Year comparison.")


            elif analysis_type == "Route Comparison":
                st.markdown("##### Route Performance Analysis (Passengers vs. EPKM)")
                st.markdown("Compare routes based on average passengers per trip and revenue efficiency.")

                # Calculate route statistics
                route_stats = filtered_df.groupby('route_no').agg(
                    total_passengers=('total_count', 'sum'),
                    avg_passengers=('total_count', 'mean'), # Average passengers per recorded trip on this route
                    epkm=('Epkm', 'mean'),
                    total_trips=('trip_number', 'count') # Total number of records/trips for the route
                ).reset_index()

                if not route_stats.empty:
                    # Create scatter plot
                    fig = px.scatter(
                        route_stats,
                        x='avg_passengers',
                        y='epkm',
                        size='total_passengers', # Size of marker by total passengers
                        color='route_no', # Color by route number
                        hover_name='route_no',
                        hover_data={
                            'avg_passengers': ':.1f',
                            'epkm': ':.2f',
                            'total_passengers': ':.0f',
                            'total_trips': ':.0f',
                            'route_no': False # Hide route_no in hover data as it's the hover_name
                        },
                        title="Route Efficiency Analysis: Average Passengers vs. EPKM",
                        labels={
                            'avg_passengers': 'Average Passengers per Trip',
                            'epkm': 'Average EPKM (₹/km)',
                            'total_passengers': 'Total Passengers (Size)'
                        },
                        size_max=30, # Max size of markers
                        color_discrete_sequence=px.colors.qualitative.T10 # Use a distinct color palette
                    )

                    # Add reference lines
                    avg_passengers_overall = filtered_df['total_count'].mean()
                    avg_epkm_overall = filtered_df['Epkm'].mean()
                    fig.add_hline(y=avg_epkm_overall, line_dash="dot", annotation_text=f"Overall Avg EPKM: ₹{avg_epkm_overall:.2f}", annotation_position="bottom right", line_color="#7f8c8d")
                    fig.add_vline(x=avg_passengers_overall, line_dash="dot", annotation_text=f"Overall Avg Passengers: {avg_passengers_overall:.1f}", annotation_position="top left", line_color="#7f8c8d")

                    fig.update_layout(
                         plot_bgcolor='rgba(0,0,0,0)',
                         xaxis_title="Average Passengers per Trip",
                         yaxis_title="Average EPKM (₹/km)",
                         hovermode='closest'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("""
                    **Insights:**
                    - Each point represents a route.
                    - X-axis: Average passengers per trip on that route.
                    - Y-axis: Average revenue earned per kilometer on that route.
                    - Marker Size: Total number of passengers carried by the route.
                    - Routes in the top-right quadrant are generally high-performing (high passengers and high EPKM).
                    - The dotted lines represent the overall average for all filtered data.
                    """)


                    # Add top/bottom performers tables
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("###### Top 5 Routes by Total Passengers")
                        st.dataframe(
                            route_stats.nlargest(5, 'total_passengers')[['route_no', 'total_passengers']]
                            .style.format({'total_passengers': '{:,.0f}'})
                        )

                    with col2:
                        st.markdown("###### Top 5 Routes by Average EPKM")
                        st.dataframe(
                            route_stats.nlargest(5, 'epkm')[['route_no', 'epkm']]
                            .style.format({'epkm': '₹{:.2f}'})
                        )
                else:
                    st.info("No route data available for comparison with current filters.")


            elif analysis_type == "Passenger vs Revenue Correlation":
                st.markdown("##### Passenger Count vs Revenue Relationship")
                st.markdown("Examine the correlation between the number of passengers and the revenue generated per trip.")

                if not filtered_df.empty:
                    # Calculate correlation
                    correlation = filtered_df['total_count'].corr(filtered_df['total_amount'])

                    # Create scatter plot
                    fig = px.scatter(
                        filtered_df,
                        x='total_count',
                        y='total_amount',
                        trendline="ols", # Add OLS regression line
                        color='service_type', # Color by service type
                        hover_data=['route_no', 'schedule_number', 'running_date'],
                        title=f"Passenger-Revenue Relationship (Correlation: {correlation:.2f})",
                        labels={
                            'total_count': 'Passenger Count (per Trip)',
                            'total_amount': 'Revenue (₹ per Trip)',
                            'service_type': 'Service Type'
                        },
                        color_discrete_sequence=px.colors.qualitative.Set2 # Use a color palette
                    )

                    fig.update_layout(
                         plot_bgcolor='rgba(0,0,0,0)',
                         xaxis_title="Passenger Count (per Trip)",
                         yaxis_title="Revenue (₹ per Trip)",
                         hovermode='closest'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("""
                    **Insights:**
                    - Each point represents a single trip record.
                    - Observe the general trend: as passenger count increases, revenue tends to increase.
                    - The trendline shows the linear relationship. A correlation coefficient close to 1 indicates a strong positive linear relationship.
                    - Points far from the trendline might indicate unusual trips (e.g., high passengers but low revenue, or vice versa).
                    - Coloring by Service Type helps identify if the relationship differs across service types.
                    """)


                    # Add breakdown by service type
                    st.markdown("---")
                    st.markdown("###### Passenger-Revenue Correlation by Service Type")
                    if st.checkbox("Show Correlation Breakdown by Service Type"):
                        # Calculate correlation for each service type
                        service_correlations = filtered_df.groupby('service_type').apply(
                            lambda x: x['total_count'].corr(x['total_amount'])
                        ).reset_index(name='correlation')

                        if not service_correlations.empty:
                             fig = px.bar(
                                service_correlations,
                                x='service_type',
                                y='correlation',
                                color='service_type',
                                title="Passenger-Revenue Correlation by Service Type",
                                labels={'correlation': 'Correlation Coefficient', 'service_type': 'Service Type'},
                                color_discrete_sequence=px.colors.qualitative.Set2 # Match scatter plot palette
                            )
                             fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_range=[-1, 1]) # Set y-axis range for correlation
                             st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No data available for service type correlation breakdown.")
                else:
                    st.info("No data available for passenger vs revenue correlation analysis.")

        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; background-color: #f8f9fa; border-radius: 8px;">
                <h4 style="color: #7f8c8d;">No data available for passenger trend analysis</h4>
                <p style="color: #bdc3c7;">Try adjusting your main filter criteria.</p>
            </div>
            """, unsafe_allow_html=True)


    with tab7:
        st.markdown("""
        <div style="border-bottom: 1px solid #e0e0e0; padding-bottom: 10px; margin-bottom: 25px;">
            <h2 style="color: #2c3e50; font-weight: 600;">EPKM Detailed Analysis</h2>
            <p style="color: #7f8c8d; font-size: 15px;">Granular analysis of revenue efficiency metrics (EPKM).</p>
        </div>
        """, unsafe_allow_html=True)

        if not filtered_df.empty:
            # Create analysis type selector
            epkm_analysis_type = st.radio(
                "Select Analysis Dimension",
                options=["Temporal Trends", "Service Comparison", "Route Efficiency", "Outlier Detection"],
                horizontal=True,
                format_func=lambda x: f"📈 {x}", # Add emoji for visual cue
                key="epkm_analysis_type" # Unique key
            )

            st.markdown("---") # Separator

            if epkm_analysis_type == "Temporal Trends":
                st.markdown("##### EPKM Trends Over Time")
                st.markdown("Analyze how the average EPKM changes over different time periods.")
                col1, col2 = st.columns([1, 3])
                with col1:
                    time_granularity = st.selectbox(
                        "Time Granularity",
                        options=["Daily", "Weekly", "Monthly"], # Removed Hourly as it might be too granular for this dataset
                        index=0, # Default to Daily
                        help="Select the time resolution for the trend analysis."
                    )

                    show_benchmark = st.checkbox(
                        "Show Overall Average EPKM",
                        value=True,
                        help="Compare the trend with the overall average EPKM across all filtered data."
                    )

                with col2:
                    freq_map = {
                        "Daily": 'D',
                        "Weekly": 'W-MON', # Start week on Monday
                        "Monthly": 'M'
                    }

                    # Group by the selected time granularity and calculate mean EPKM
                    epkm_temporal = filtered_df.groupby(pd.Grouper(
                        key='running_date',
                        freq=freq_map[time_granularity]
                    ))['Epkm'].mean().reset_index()

                    if not epkm_temporal.empty:
                        fig = px.line(
                            epkm_temporal,
                            x='running_date',
                            y='Epkm',
                            markers=True,
                            labels={'Epkm': 'Average EPKM (₹/km)', 'running_date': 'Time Period'},
                            color_discrete_sequence=['#3498db'], # Blue color
                            title=f"Average EPKM Trend ({time_granularity})"
                        )

                        if show_benchmark:
                            system_avg = filtered_df['Epkm'].mean()
                            fig.add_hline(
                                y=system_avg,
                                line_dash="dot",
                                line_color="#e74c3c", # Red color
                                annotation_text=f"Overall Average: ₹{system_avg:.2f}",
                                annotation_position="bottom right"
                            )

                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            xaxis_title="Time Period",
                            yaxis_title="Average EPKM (₹/km)",
                            hovermode="x unified"
                        )

                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.info(f"No data available for {time_granularity} EPKM trend with current filters.")


            elif epkm_analysis_type == "Service Comparison":
                st.markdown("##### EPKM Comparison by Service Type")
                st.markdown("Compare the revenue efficiency across different service types.")
                col1, col2 = st.columns([1, 3])
                with col1:
                    metric_type = st.radio(
                        "Comparison Metric",
                        options=["Mean", "Median", "95th Percentile"],
                        index=0,
                        horizontal=True,
                        help="Select the statistical metric to compare service types."
                    )

                    show_distribution = st.checkbox(
                        "Show Distribution (Violin Plot)",
                        value=True,
                        help="Display the full distribution of EPKM values for each service type."
                    )

                with col2:
                    agg_func = {
                        "Mean": 'mean',
                        "Median": 'median',
                        "95th Percentile": lambda x: x.quantile(0.95) if not x.empty else 0 # Handle empty case
                    }[metric_type]

                    # Calculate EPKM metric for each service type
                    service_epkm = filtered_df.groupby('service_type')['Epkm'].agg(agg_func).reset_index()

                    if not service_epkm.empty:
                        if show_distribution:
                            fig = px.violin(
                                filtered_df,
                                x='service_type',
                                y='Epkm',
                                box=True, # Show box plot inside violin
                                points="all", # Show all data points
                                color='service_type',
                                labels={'Epkm': 'EPKM (₹/km)', 'service_type': 'Service Type'},
                                title="EPKM Distribution by Service Type (Violin Plot)"
                            )
                        else:
                            fig = px.bar(
                                service_epkm,
                                x='service_type',
                                y='Epkm',
                                color='service_type',
                                labels={'Epkm': f'{metric_type} EPKM (₹/km)', 'service_type': 'Service Type'},
                                title=f"{metric_type} EPKM by Service Type"
                            )

                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            xaxis_title="Service Type",
                            yaxis_title=f"{metric_type} EPKM (₹/km)",
                            showlegend=False # Hide legend if coloring by x-axis
                        )

                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    else:
                         st.info("No data available for service comparison with current filters.")


            elif epkm_analysis_type == "Route Efficiency":
                st.markdown("##### Top Routes by EPKM Efficiency")
                st.markdown("Identify the routes with the highest revenue efficiency.")
                col1, col2 = st.columns([1, 3])
                with col1:
                    top_n = st.slider(
                        "Number of Top Routes to Show",
                        min_value=5,
                        max_value=min(20, filtered_df['route_no'].nunique()), # Max up to 20 or number of unique routes
                        value=10,
                        step=1,
                        help="Select how many top routes to display based on EPKM."
                    )

                    efficiency_metric = st.selectbox(
                        "Ranking Metric",
                        options=["Average EPKM", "Total EPKM"], # Simplified options
                        index=0,
                        help="Choose whether to rank by average or total EPKM."
                    )

                with col2:
                    # Calculate route statistics
                    route_stats = filtered_df.groupby('route_no').agg(
                        avg_epkm=('Epkm', 'mean'),
                        total_epkm=('Epkm', 'sum'), # Calculate total EPKM (sum of EPKM for all trips on route)
                        total_passengers=('total_count', 'sum'),
                        total_distance=('travel_distance', 'sum')
                    ).reset_index()

                    if not route_stats.empty:
                        if efficiency_metric == "Average EPKM":
                            ranking_col = 'avg_epkm'
                            y_label = "Average EPKM (₹/km)"
                            title_suffix = "by Average EPKM"
                        else: # Total EPKM
                            ranking_col = 'total_epkm'
                            y_label = "Total EPKM (₹)" # Sum of EPKM values
                            title_suffix = "by Total EPKM"

                        # Get top N routes based on the selected metric
                        top_routes = route_stats.nlargest(top_n, ranking_col).copy() # Use .copy()

                        if not top_routes.empty:
                            fig = px.bar(
                                top_routes,
                                x='route_no',
                                y=ranking_col,
                                color=ranking_col, # Color by the ranking metric
                                color_continuous_scale='Viridis',
                                labels={'route_no': 'Route Number', ranking_col: y_label},
                                title=f"Top {top_n} Routes {title_suffix}",
                                hover_data={
                                    'route_no': True,
                                    ranking_col: ':.2f',
                                    'avg_epkm': ':.2f', # Show average EPKM in hover regardless of ranking metric
                                    'total_passengers': ':.0f',
                                    'total_distance': ':.0f'
                                }
                            )

                            fig.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                xaxis_title="Route Number",
                                yaxis_title=y_label,
                                coloraxis_colorbar=dict(title=y_label)
                            )

                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.info(f"No routes found meeting the criteria for the top {top_n} list.")
                    else:
                         st.info("No route data available for efficiency analysis with current filters.")


            elif epkm_analysis_type == "Outlier Detection":
                st.markdown("##### EPKM Outlier Detection")
                st.markdown("Identify trips with unusually high or low EPKM values.")
                col1, col2 = st.columns([1, 3])
                with col1:
                    outlier_threshold = st.slider(
                        "Outlier Threshold (Z-score)",
                        min_value=1.0, # Lower min value for more sensitivity
                        max_value=5.0,
                        value=3.0,
                        step=0.5,
                        help="Adjust the Z-score threshold to define outliers. Higher values are less sensitive."
                    )

                    show_context = st.checkbox(
                        "Show All Data Points (Context)",
                        value=True,
                        help="Display all trips, highlighting potential outliers."
                    )

                with col2:
                    if not filtered_df.empty and filtered_df['Epkm'].std() > 0: # Ensure standard deviation is not zero
                        # Calculate Z-scores for EPKM
                        # Use .copy() to avoid SettingWithCopyWarning
                        df_for_outliers = filtered_df.copy()
                        df_for_outliers['epkm_zscore'] = np.abs(
                            (df_for_outliers['Epkm'] - df_for_outliers['Epkm'].mean()) / df_for_outliers['Epkm'].std()
                        )

                        # Identify outliers based on threshold
                        outliers = df_for_outliers[df_for_outliers['epkm_zscore'] > outlier_threshold].copy() # Use .copy()

                        # Determine which data to plot
                        data_to_plot = df_for_outliers if show_context else outliers

                        if not data_to_plot.empty:
                            fig = px.scatter(
                                data_to_plot,
                                x='running_date',
                                y='Epkm',
                                color='epkm_zscore' if show_context else None, # Color by Z-score only if showing context
                                size='travel_distance', # Size by travel distance
                                hover_data=['route_no', 'schedule_number', 'total_count', 'total_amount', 'travel_distance', 'Epkm', 'epkm_zscore'],
                                color_continuous_scale='RdYlGn_r' if show_context else None, # Color scale for Z-score
                                labels={'Epkm': 'EPKM (₹/km)', 'running_date': 'Date', 'epkm_zscore': 'EPKM Z-score', 'travel_distance': 'Travel Distance (km)'},
                                title=f"EPKM Outlier Detection (Z-score > {outlier_threshold})",
                                color_discrete_sequence=['#e74c3c'] if not show_context else None # Red color for outliers if not showing context
                            )

                            # Add a horizontal line at the average EPKM
                            avg_epkm_overall = filtered_df['Epkm'].mean()
                            fig.add_hline(y=avg_epkm_overall, line_dash="dot", line_color="#7f8c8d", annotation_text=f"Overall Average: ₹{avg_epkm_overall:.2f}", annotation_position="bottom left")


                            fig.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                xaxis_title="Date",
                                yaxis_title="EPKM (₹/km)",
                                coloraxis_colorbar=dict(title="Z-score") if show_context else None, # Show color bar only if showing context
                                hovermode='closest'
                            )

                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                            st.markdown(f"""
                            **Insights:**
                            - Each point represents a single trip.
                            - Points with a high Z-score (colored red/yellow if showing context, or just red if showing only outliers) are potential outliers.
                            - These trips have an EPKM value significantly different from the average.
                            - Hover over points to see details like Route, Schedule, Passengers, Revenue, Distance, and EPKM Z-score.
                            - Investigate outliers to understand potential data errors or unusual operating conditions.
                            - **Detected Outliers:** {len(outliers)} trips have an EPKM Z-score greater than {outlier_threshold}.
                            """)
                            if not outliers.empty:
                                st.markdown("###### Details of Detected Outliers")
                                st.dataframe(outliers[['running_date', 'route_no', 'schedule_number', 'total_count', 'total_amount', 'travel_distance', 'Epkm', 'epkm_zscore']].sort_values('epkm_zscore', ascending=False))
                        else:
                            st.info(f"No data points found with an EPKM Z-score greater than {outlier_threshold} for the current filters.")
                    elif filtered_df['Epkm'].std() == 0:
                         st.info("EPKM values are constant for the current filters, no outliers to detect.")
                    else:
                         st.info("No data available for EPKM outlier detection with current filters.")

        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; background-color: #f8f9fa; border-radius: 8px;">
                <h4 style="color: #7f8c8d;">No data available for EPKM analysis</h4>
                <p style="color: #bdc3c7;">Try adjusting your main filter criteria.</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Close plot-container div

# Export Option
st.markdown("---")
st.markdown("### Data Export")
with st.expander("Export Filtered Data"):
    # Only show download button if data exists
    if not filtered_df.empty:
        st.write(f"Filtered dataset contains {len(filtered_df)} records.")
        st.download_button(
            "Download Filtered Data as CSV",
            filtered_df.to_csv(index=False).encode('utf-8'),
            "filtered_transport_data.csv",
            "text/csv",
            help="Download the currently filtered data as a CSV file."
        )
    else:
        st.info("No data available to export based on current filters.")

st.markdown("---")
st.markdown("Dashboard developed using Streamlit and Plotly.")
