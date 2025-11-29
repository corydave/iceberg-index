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

        # 5. THE MAP
        # We start centered on the Finger Lakes (approx lat/long)
        # In a V2, you can use a geocoder to center exactly on the zip.
        m = folium.Map(location=[42.88, -77.28], zoom_start=9)
        
        # Add a marker for the zip
        folium.Marker(
            [42.88, -77.28], 
            popup=f"Zip: {target_zip}\nScore: {score}",
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

        st_folium(m, width=800, height=500)

        # 6. RAW DATA TABLE (For you to inspect)
        with st.expander("See Raw Census Data"):
            st.json(result['raw_data'])