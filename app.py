import streamlit as st
import folium
from streamlit_folium import st_folium
import logic  # This imports your logic.py file

# --- PAGE CONFIG ---
st.set_page_config(page_title="The Iceberg Index", layout="wide")

# --- HEADER ---
st.title("🧊 The Iceberg Index: Local AI Disruption Map")
st.markdown("""
**This tool visualizes 'Hidden' AI exposure.**
While the news focuses on "Tech" jobs (the tip of the iceberg), the largest volume of disruption 
is happening in administrative, office, and logistical roles (the submerged part).
""")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Analyze a Region")
    target_zip = st.text_input("Enter Zip Code", value="14424")
    run_btn = st.button("Run Simulation", type="primary")
    
    st.markdown("---")
    st.info("Data Sources: US Census ACS (2023) & Eloundou et al. (2023) AI Exposure Findings.")

# --- MAIN APP LOGIC ---
if run_btn or target_zip:
    with st.spinner(f"Querying Census Bureau for {target_zip}..."):
        # 1. CALL YOUR LOGIC FILE
        result = logic.calculate_iceberg_score(target_zip)

    # 2. HANDLE ERRORS
    if "error" in result:
        st.error(f"Error: {result['error']}")
    else:
        # 3. DISPLAY METRICS
        col1, col2, col3 = st.columns(3)
        
        score = result['index_score']
        
        with col1:
            st.metric("Disruption Index Score", f"{score}/100")
        
        with col2:
            st.metric("Dominant Sector", result['dominant_sector'])
            
        with col3:
            st.metric("Total Workforce", f"{result['total_workers']:,}")

        # 4. COLOR LOGIC (Green/Yellow/Red)
        if score < 40:
            color = "green"
            msg = "Low Exposure (Manual/Service Heavy)"
        elif score < 60:
            color = "orange"
            msg = "Moderate Exposure (Mixed Economy)"
        else:
            color = "red"
            msg = "High Exposure (Admin/Information Heavy)"

        st.success(f"**Analysis:** {msg}")


        # ADD BAR CHARTS
        st.divider() # Adds a nice horizontal line

        st.subheader("Job Composition in this Zip Code")

        # Convert the raw dictionary to a Pandas DataFrame for easy charting
        import pandas as pd # Make sure you add 'import pandas as pd' at the very top of the file!

        # result['raw_data'] looks like {'Management': 1200, 'Sales': 400...}
        chart_data = pd.DataFrame.from_dict(result['raw_data'], orient='index', columns=['Workers'])

        # Remove the "Total_Workers" row so it doesn't skew the chart
        if "Total_Workers" in chart_data.index:
            chart_data = chart_data.drop("Total_Workers")

        # Sort it so the biggest sectors are on top
        chart_data = chart_data.sort_values(by="Workers", ascending=False)

        # Draw the chart!
        st.bar_chart(chart_data)


        # --- THE RISK DISTRIBUTION DONUT CHART ---
        
        st.subheader("Workforce Exposure Breakdown")
        
        # 1. Create 3 Buckets
        high_risk = 0
        med_risk = 0
        low_risk = 0
        
        # You'll need to copy the RISK_SCORES dict from logic.py to here temporarily
        # or just define the thresholds based on the sectors.
        # For simplicity, let's just loop through the raw data and estimate based on the logic we know.
        
        # We need the risk scores to do this accurately. 
        # A quick hack is to import the map from logic
        from logic import RISK_SCORES 
        
        for sector, count in result['raw_data'].items():
            if sector == "Total_Workers": continue
            
            score = RISK_SCORES.get(sector, 0.5)
            if score >= 0.7:
                high_risk += count
            elif score >= 0.4:
                med_risk += count
            else:
                low_risk += count
        
        # 2. Prepare Data for Chart
        risk_data = pd.DataFrame({
            'Category': ['High Exposure (AI Ready)', 'Medium Exposure (Augmented)', 'Low Exposure (Physical/Human)'],
            'Workers': [high_risk, med_risk, low_risk]
        })
        
        # 3. Display as a Bar Chart (Streamlit handles this better than donuts natively)
        st.bar_chart(risk_data.set_index('Category'), color=["#FF4B4B", "#FFA500", "#008000"])        

        # 5. THE MAP
        # We start centered on the Finger Lakes (approx lat/long)
        # In a V2, you can use a geocoder to center exactly on the zip.
        m = folium.Map(location=[42.88, -77.28], zoom_start=9)
        
        # Add a marker for the zip
        # folium.Marker(
        #     [42.88, -77.28], 
        #     popup=f"Zip: {target_zip}\nScore: {score}",
        #     icon=folium.Icon(color=color, icon="info-sign"),
        # ).add_to(m)

        # st_folium(m, width=800, height=500)

        # 6. RAW DATA TABLE (For you to inspect)
        with st.expander("See Raw Census Data"):
            st.json(result['raw_data'])
