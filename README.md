# Transport Analytics Dashboard - Analysis and Documentation

## Overview
This Streamlit-based Transport Analytics Dashboard provides comprehensive insights into public transportation operations, including passenger analytics, route performance, fleet monitoring, and sustainability metrics. The dashboard is designed to help transportation managers optimize operations, improve efficiency, and reduce environmental impact.

## Key Features

### 1. Summary Overview
- **Metrics**: Total passengers, revenue, distance, and average EPKM (Earnings Per Kilometer)
- **Visualizations**:
  - Top/Bottom 5 routes by passenger count
  - Daily revenue trend with peak day highlights
- **Filters**: Date range, service types, ticket types, and routes

### 2. Route Performance
- **Metrics**: Total trips, passengers, and revenue for selected route
- **Visualizations**:
  - Schedule-wise EPKM (Earnings Per Kilometer)
  - Revenue vs. distance scatter plot
- **Insights**: Top performing schedules and revenue leakage alerts

### 3. Route Optimization
- **Metrics**: Passenger density, revenue efficiency, and efficiency score
- **Visualizations**:
  - Passenger density by route
  - Revenue per KM by route
  - Route efficiency score
- **Recommendations**: Route merging/cancellation suggestions and bus allocation

### 4. Fleet Monitoring
- **Metrics**: Total distance, trips, and vehicle utilization
- **Visualizations**:
  - Trips per vehicle
  - Monthly distance trend
- **Alerts**: Underutilized and overused vehicle identification

### 5. Sustainability Dashboard
- **Metrics**: KM driven (EV vs Diesel), CO2 emissions, and savings
- **Visualizations**: EV vs Diesel comparison charts
- **Recommendations**: Eco-friendly route suggestions

## Technical Implementation

### Data Structure
The dashboard uses multiple CSV files:
- `cleaned_master.csv`: Primary transaction data
- `ticket_type.csv`: Ticket type reference
- `service_type.csv`: Service type reference
- `form_four_trip-6.csv`: Route distance mapping

### Key Functions
1. **Data Loading**: 
   - `load_data()` loads and merges all data sources
   - Implements caching for performance

2. **Data Processing**:
   - Calculates derived metrics (EPKM, passengers per KM)
   - Maps IDs to human-readable names
   - Handles date/time conversions

3. **Visualization**:
   - Uses Plotly Express for interactive charts
   - Custom styling with CSS for professional appearance
   - Dynamic annotations for highlighting key insights

4. **User Interaction**:
   - Global filters in sidebar
   - Page-specific filters
   - Tabbed interfaces for different analysis views

### Custom Styling
The dashboard features custom CSS for:
- Metric cards with consistent styling
- Insight/warning cards with color coding
- Responsive layout adjustments
- Professional tab styling

## Usage Recommendations

### For Transportation Managers
1. **Daily Operations**:
   - Use the Summary Overview to monitor KPIs
   - Check Route Performance for problem routes
   - Review Fleet Monitoring for vehicle utilization

2. **Strategic Planning**:
   - Use Route Optimization for network planning
   - Consult Sustainability metrics for eco-friendly initiatives

3. **Troubleshooting**:
   - Identify revenue leakage points
   - Detect underperforming routes/schedules
   - Spot maintenance needs through vehicle utilization

### For Data Teams
1. **Data Requirements**:
   - Ensure all source files are updated regularly
   - Maintain consistent ID mappings
   - Verify distance calculations

2. **Enhancements**:
   - Add real-time data integration
   - Incorporate weather/event data for contextual analysis
   - Develop predictive models for demand forecasting

## Limitations and Future Improvements

### Current Limitations
1. Static data loading (CSV files)
2. Simplified CO2 calculations
3. Basic efficiency scoring model

### Recommended Enhancements
1. **Data Integration**:
   - Connect to live databases/APIs
   - Add automated data refresh

2. **Advanced Analytics**:
   - Implement machine learning for demand prediction
   - Add anomaly detection for irregular patterns

3. **User Features**:
   - Custom report generation
   - Alert/notification system
   - User-specific dashboards

4. **Visualization**:
   - Interactive maps for route visualization
   - More sophisticated scenario modeling tools

## Setup Instructions

1. **Requirements**:
   - Python 3.8+
   - Streamlit
   - Pandas
   - Plotly

2. **Installation**:
   ```bash
   pip install streamlit pandas plotly
   ```

3. **Data Preparation**:
   - Place all CSV files in a `data` subdirectory
   - Ensure consistent column naming

4. **Running**:
   ```bash
   streamlit run dashboard.py
   ```

## Conclusion
This Transport Analytics Dashboard provides a comprehensive tool for managing public transportation operations. By offering both high-level overviews and detailed route/schedule analysis, it enables data-driven decision making for improved efficiency, profitability, and sustainability.