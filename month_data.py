import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime
# from PIL import Image  # Not used, so removed
from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(
    page_title="Smart City Transit Dashboard",
    page_icon="🚍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# Custom CSS
st.markdown(
    """
<style>
    [data-testid=stSidebar],[data-testid=stSidebar] p {
        background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
        color: white;
    }
    .metric-card {
        padding: 20px;
        background: #f0f4f8;
        border-radius: 12px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.3s;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border: 1px solid #e0e0e0;
    }
    .metric-card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
    }
    .st-emotion-cache-1v0mbdj {
        border-radius: 15px;
    }
    .month-comparison-table td,
    .month-comparison-table th {
        padding: 10px;
        text-align: center;
        border-bottom: 1px solid #ddd;
    }
    .month-comparison-table th {
        background-color: #f5f5f5;
        color: #2c3e50;
    }
    .month-comparison-table tr:hover {
        background-color: #fffaf0;
    }
    .highlight-green {
        background-color: #e6f4ea;
        color: #1a5235;
    }
    .highlight-red {
        background-color: #fdeaea;
        color: #670e10;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_excel(
            "data/smart_city_dashboard_datewise_data.xlsx", sheet_name="trip_revenue-5"
        )
    except FileNotFoundError:
        st.error("Error: 'smart_city_dashboard_datewise_data.xlsx' not found.")
        st.info(
            "Please ensure the Excel file is in the correct location (e.g., in a 'data' subfolder or the same directory as the script) and the path is updated accordingly."
        )
        st.stop()

    # Clean data
    df["running_date"] = pd.to_datetime(df["running_date"]).dt.date
    df["running_time"] = (
        pd.to_timedelta(df["running_time"].astype(str)).dt.total_seconds() / 3600
    )

    # Convert to string type
    df["color_line"] = df["color_line"].astype(str)
    df["route_no"] = df["route_no"].astype(str)
    df["schedule_number"] = df["schedule_number"].astype(str)

    # Calculate 'Epkm'
    df["travel_distance"] = df["travel_distance"].replace(0, np.nan)
    df["Epkm"] = df["total_amount"] / df["travel_distance"]
    df["Epkm"] = df["Epkm"].fillna(0)

    # Extract day of week and month name
    temp_running_date_dt = pd.to_datetime(df["running_date"])
    df["day_of_week"] = temp_running_date_dt.dt.day_name()
    df["month"] = temp_running_date_dt.dt.month_name()

    return df


df = load_data()


# --- Helper Functions ---
def create_kpi_card(title, value, icon=None, delta=None):
    """Creates a KPI card with a title, value, icon, and color."""
    delta_html = ""
    if delta is not None:
        # Extract numeric part of delta if it's a string
        if isinstance(delta, str):
            if delta.startswith("#"):  # Check if it's a color code
                delta_value = None  # Set to None to indicate no delta
            else:
                try:
                    delta_value = float(delta.strip("+- %"))
                except ValueError:
                    delta_value = (
                        delta  # Keep original string if conversion fails
                    )
        else:
            delta_value = delta
        if isinstance(delta_value, (int, float)):
            color = "#2ECC71" if delta_value >= 0 else "#E74C3C"
            delta_html = (
                f"<div style='font-size:14px; color:{color}; font-weight:bold;'>{delta_value:+.1f}%</div>"
            )
        else:
            delta_html = (
                f"<div style='font-size:14px; color:#7F8C8D'>{delta}</div>"
            )  # Display delta as is

    return f"""
    <div class="metric-card">
        <div style='font-size:24px; margin-bottom:10px;'>{icon or ""}</div>
        <div style='font-size:18px; color:#3498db; font-weight:bold;'>{title}</div>
        <div style='font-size:30px; font-weight:bold; margin-bottom:10px; color: #2c3e50;'>{value}</div>
        {delta_html}
    </div>
    """


def create_bar_chart(data, x, y, title, xlabel, ylabel, color=None, color_continuous_scale=None):
    """Creates a bar chart with customizable labels and colors."""
    if color:
        chart = (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X(x, title=xlabel),
                y=alt.Y(y, title=ylabel),
                color=color,
                tooltip=[x, y, color],
            )
            .properties(title=title, height=350)
            .configure_header(titleFontSize=18, labelFontSize=14)
            .configure_axis(titleFontSize=14, labelFontSize=12)
        )
    else:
        chart = (
            alt.Chart(data)
            .mark_bar()
            .encode(x=alt.X(x, title=xlabel), y=alt.Y(y, title=ylabel), tooltip=[x, y])
            .properties(title=title, height=350)
            .configure_header(titleFontSize=18, labelFontSize=14)
            .configure_axis(titleFontSize=14, labelFontSize=12)
        )

    return chart.interactive()


def create_line_chart(data, x, y, title, xlabel, ylabel):
    """Creates a line chart with customizable labels."""
    chart = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(x=alt.X(x, title=xlabel), y=alt.Y(y, title=ylabel), tooltip=[x, y])
        .properties(title=title, height=350)
        .configure_header(titleFontSize=18, labelFontSize=14)
        .configure_axis(titleFontSize=14, labelFontSize=12)
    )
    return chart.interactive()


def create_table(data, title):
    """Creates a styled table."""
    st.markdown(
        f"<h3 style='font-size: 24px; color: #2c3e50; margin-bottom: 15px;'>{title}</h3>",
        unsafe_allow_html=True,
    )
    st.dataframe(
        data,
        column_config={
            "Total_Passengers": st.column_config.NumberColumn(format=",d"),
            "Total_Revenue": st.column_config.NumberColumn(format="₹%,.2f"),
            "Total_Distance": st.column_config.NumberColumn(format="%,.2f"),
            "Avg_EPKM": st.column_config.NumberColumn(format="₹%,.2f"),
        },
        use_container_width=True,
    )


# --- Sidebar Filters ---
st.sidebar.header("Filters")
min_date_val = df["running_date"].min()
max_date_val = df["running_date"].max()

date_range_selected = st.sidebar.date_input(
    "Date Range",
    value=[min_date_val, max_date_val],
    min_value=min_date_val,
    max_value=max_date_val,
)
start_date = date_range_selected[0]
end_date = date_range_selected[0] if len(date_range_selected) == 1 else date_range_selected[1]

service_types_selected = st.sidebar.multiselect(
    "Service Type", options=sorted(df["color_line"].unique()), default=[]
)

routes_selected = st.sidebar.multiselect(
    "Route", options=sorted(df["route_no"].unique()), default=[]
)

days_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
available_days = [day for day in days_order if day in df["day_of_week"].unique()]
day_of_week_selected = st.sidebar.multiselect(
    "Day of Week", options=available_days, default=[]
)

months_order = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
available_months = [month for month in months_order if month in df["month"].unique()]
month_selected = st.sidebar.multiselect(
    "Month", options=available_months, default=[]
)

# --- Main Content ---
st.title("Transit Performance Dashboard")

# Handle empty filters
active_service_types = (
    service_types_selected if service_types_selected else df["color_line"].unique()
)
active_routes = routes_selected if routes_selected else df["route_no"].unique()
active_days = day_of_week_selected if day_of_week_selected else df["day_of_week"].unique()
active_months = month_selected if month_selected else df["month"].unique()

# Filter data
filtered_df = df[
    (df["running_date"] >= start_date)
    & (df["running_date"] <= end_date)
    & (df["color_line"].isin(active_service_types))
    & (df["route_no"].isin(active_routes))
    & (df["day_of_week"].isin(active_days))
    & (df["month"].isin(active_months))
]

# --- Executive Summary ---
st.markdown(
    "<h2 style='font-size: 28px; color: #2c3e50; margin-bottom: 25px;'>Executive Summary</h2>",
    unsafe_allow_html=True,
)
if not filtered_df.empty:
    total_passengers = filtered_df["total_passenger"].sum()
    total_revenue = filtered_df["total_amount"].sum()
    total_distance = filtered_df["travel_distance"].sum()
    avg_epkm = filtered_df["Epkm"].mean() if not filtered_df.empty else 0

    summary_df = pd.DataFrame({
        "Metric": ["Total Passengers", "Total Revenue (₹)", "Total Distance (KM)", "Avg EPKM (₹/KM)"],
        "Value": [total_passengers, total_revenue, total_distance, avg_epkm],
    })
    

    kpi_cols = st.columns(4)
    passenger_icon = "👥"  # Using emoji
    revenue_icon = "💰"  # Using emoji
    distance_icon = "📏"  # Using emoji
    epkm_icon = "📈"  # Using emoji

    kpi_cols[0].markdown(
        create_kpi_card("Total Passengers", f"{total_passengers:,.0f}", passenger_icon, "+8.5%"),
        unsafe_allow_html=True,
    )
    kpi_cols[1].markdown(
        create_kpi_card("Total Revenue (₹)", f"₹{total_revenue:,.0f}", revenue_icon, "+10.2%"),
        unsafe_allow_html=True,
    )
    kpi_cols[2].markdown(
        create_kpi_card("Total Distance (KM)", f"₹{total_distance:,.0f}", distance_icon, "-2.3%"),
        unsafe_allow_html=True,
    )
    kpi_cols[3].markdown(
        create_kpi_card("Avg EPKM (₹/KM)", f"₹{avg_epkm:,.2f}", epkm_icon, "+5.6%"),
        unsafe_allow_html=True,
    )
else:
    st.info("No data available for the current filter selection to display KPIs.")

# --- Charts ---
st.markdown("---")
st.markdown(
    "<h2 style='font-size: 28px; color: #2c3e50; margin-bottom: 25px;'>Performance Analysis</h2>",
    unsafe_allow_html=True,
)

if not filtered_df.empty:
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Passenger & Revenue Trends",
            "Route Performance",
            "EPKM Analysis",
            "Month-wise Comparison",
        ]
    )

    with tab1:
        col1_chart_tab1, col2_chart_tab1 = st.columns(2)

        with col1_chart_tab1:
            daily_passengers = (
                filtered_df.groupby("running_date")["total_passenger"].sum().reset_index()
            )
            fig_daily_pass = create_line_chart(
                daily_passengers,
                "running_date",
                "total_passenger",
                "Daily Passenger Count",
                "Date",
                "Passengers",
            )
            st.altair_chart(fig_daily_pass, use_container_width=True)

        with col2_chart_tab1:
            daily_revenue = (
                filtered_df.groupby("running_date")["total_amount"].sum().reset_index()
            )
            fig_daily_rev = create_line_chart(
                daily_revenue,
                "running_date",
                "total_amount",
                "Daily Revenue Trend",
                "Date",
                "Revenue (₹)",
            )
            st.altair_chart(fig_daily_rev, use_container_width=True)

    with tab2:
        col1_chart_tab2, col2_chart_tab2 = st.columns(2)

        with col1_chart_tab2:
            route_passengers_top = (
                filtered_df.groupby("route_no")["total_passenger"]
                .sum()
                .nlargest(5)
                .reset_index()
            )
            if not route_passengers_top.empty:
                fig_top_routes = create_bar_chart(
                    route_passengers_top,
                    "total_passenger",
                    "route_no",
                    "Top 5 Routes by Passengers",
                    "Passengers",
                    "Route",
                    color="total_passenger",
                )
                fig_top_routes.configure_mark(color="green")
                st.altair_chart(fig_top_routes, use_container_width=True)
            else:
                st.write(
                    "Not enough data for Top 5 Routes by Passengers with current filters."
                )

        with col2_chart_tab2:
            route_passengers_bottom = (
                filtered_df.groupby("route_no")["total_passenger"]
                .sum()
                .nsmallest(5)
                .reset_index()
            )
            if not route_passengers_bottom.empty:
                fig_bottom_routes = create_bar_chart(
                    route_passengers_bottom,
                    "total_passenger",
                    "route_no",
                    "Bottom 5 Routes by Passengers",
                    "Passengers",
                    "Route",
                    color="total_passenger",
                )
                fig_bottom_routes.configure_mark(color="red")
                st.altair_chart(fig_bottom_routes, use_container_width=True)
            else:
                st.write(
                    "Not enough data for Bottom 5 Routes by Passengers with current filters."
                )

    with tab3:
        col1_chart_tab3, col2_chart_tab3 = st.columns(2)

        with col1_chart_tab3:
            service_epkm = (
                filtered_df.groupby("color_line")["Epkm"].mean().reset_index().dropna()
            )
            if not service_epkm.empty:
                fig_service_epkm = create_bar_chart(
                    service_epkm,
                    "color_line",
                    "Epkm",
                    "Average EPKM by Service Type",
                    "Service Type",
                    "Avg. EPKM (₹/KM)",
                    color="Epkm",
                    color_continuous_scale="viridis",
                )
                st.altair_chart(fig_service_epkm, use_container_width=True)
            else:
                st.warning(
                    "Insufficient data to calculate EPKM metrics. Try adjusting filters."
                )

   
    with tab4:
        st.subheader("Month-wise Comparison")
        month_wise_df = (
            filtered_df.groupby("month")
            .agg(
                Total_Passengers=("total_passenger", "sum"),
                Total_Revenue=("total_amount", "sum"),
                Total_Distance=("travel_distance", "sum"),
                Avg_EPKM=("Epkm", "mean"),
            )
            .reset_index()
        )
        month_wise_df["Month_Number"] = pd.to_datetime(
            month_wise_df["month"], format="%B"
        ).dt.month
        month_wise_df = month_wise_df.sort_values("Month_Number")
        month_wise_df = month_wise_df.drop(columns=["Month_Number"])

        # Calculate month-on-month comparison metrics
        comparison_df = pd.DataFrame()
        comparison_df["Month"] = month_wise_df["month"]
        comparison_df["Passengers"] = month_wise_df["Total_Passengers"]
        comparison_df["Revenue"] = month_wise_df["Total_Revenue"]
        comparison_df["Distance"] = month_wise_df["Total_Distance"]
        comparison_df["EPKM"] = month_wise_df["Avg_EPKM"]

        comparison_df["Passenger_MoM"] = comparison_df["Passengers"].pct_change() * 100
        comparison_df["Revenue_MoM"] = comparison_df["Revenue"].pct_change() * 100
        comparison_df["Distance_MoM"] = comparison_df["Distance"].pct_change() * 100
        comparison_df["EPKM_MoM"] = comparison_df["EPKM"].pct_change() * 100

        # Create a styled DataFrame
        styled_df = comparison_df.style.format({
            "Passengers": "{:,.0f}",
            "Revenue": "₹{:,.2f}",
            "Distance": "{:,.2f} KM",
            "EPKM": "₹{:,.2f}",
            "Passenger_MoM": "{:+.1f}%",
            "Revenue_MoM": "{:+.1f}%",
            "Distance_MoM": "{:+.1f}%",
            "EPKM_MoM": "{:+.1f}%"
        }).map(lambda x: "color: green" if isinstance(x, str) and x.startswith('+') and float(x.strip('+%')) >= 0 
                        else "color: red" if isinstance(x, str) and (x.startswith('-') or (x.startswith('+') and float(x.strip('+%')) < 0))
                        else "", subset=["Passenger_MoM", "Revenue_MoM", "Distance_MoM", "EPKM_MoM"])

        # Display the styled DataFrame
        st.dataframe(
            styled_df,
            column_config={
                "Month": "Month",
                "Passengers": "Passengers",
                "Revenue": "Revenue (₹)",
                "Distance": "Distance (KM)",
                "EPKM": "EPKM (₹/KM)",
                "Passenger_MoM": "Passenger MoM %",
                "Revenue_MoM": "Revenue MoM %",
                "Distance_MoM": "Distance MoM %",
                "EPKM_MoM": "EPKM MoM %"
            },
            use_container_width=True,
            height=(len(comparison_df) + 1) * 35 + 3
        )
else:
    st.warning("No data available for the selected filters to display charts.")

style_metric_cards(border_left_color="#3498DB")
