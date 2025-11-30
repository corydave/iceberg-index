import streamlit as st
import pandas as pd
import logic  # This imports your calculation script
from logic import RISK_SCORES # We need this to calculate the breakdown

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
        # 3. DISPLAY TOP-LEVEL METRICS
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
            st.success("Analysis: **Low Exposure** (Manual/Service Economy)")
        elif score < 60:
            st.warning("Analysis: **Moderate Exposure** (Mixed Economy)")
        else:
            st.error("Analysis: **High Exposure** (Admin/Information Heavy)")

        st.divider()

        # --- VISUALIZATION 1: JOB COMPOSITION BAR CHART ---
        st.subheader("📊 Job Composition in this Zip Code")
        
        # Convert raw data to DataFrame
        chart_data = pd.DataFrame.from_dict(result['raw_data'], orient='index', columns=['Workers'])
        
        # Clean up data (Remove 'Total' and Sort)
        if "Total_Workers" in chart_data.index:
            chart_data = chart_data.drop("Total_Workers")
        chart_data = chart_data.sort_values(by="Workers", ascending=False)
        
        st.bar_chart(chart_data)

        st.divider()

        # --- VISUALIZATION 2: WORKFORCE RISK BREAKDOWN ---
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("⚠️ Workforce Exposure")
            
            # Calculate Risk Buckets
            high_risk = 0
            med_risk = 0
            low_risk = 0

            for sector, count in result['raw_data'].items():
                if sector == "Total_Workers": continue
                
                # Look up risk score (default to 0.5 if missing)
                risk_val = RISK_SCORES.get(sector, 0.5)
                
                if risk_val >= 0.7:
                    high_risk += count
                elif risk_val >= 0.4:
                    med_risk += count
                else:
                    low_risk += count

            # Display Chart
            risk_df = pd.DataFrame({
                'Category': ['High Risk (AI Ready)', 'Medium Risk (Augmented)', 'Low Risk (Safe)'],
                'Workers': [high_risk, med_risk, low_risk]
            })
            st.bar_chart(risk_df.set_index('Category'), color=["#FF4B4B", "#FFA500", "#008000"])

        # --- VISUALIZATION 3: SAFE HARBORS ---
        with col_b:
            st.subheader("🛡️ Local Safe Harbors")
            st.write("Largest sectors with the *lowest* automation risk:")

            # Create a list of (Sector, Count, Risk)
            safe_sectors = []
            for sector, count in result['raw_data'].items():
                if sector == "Total_Workers": continue
                risk_val = RISK_SCORES.get(sector, 0.5)
                # Only show sectors with at least 50 people
                if count > 50: 
                    safe_sectors.append((sector, count, risk_val))

            # Sort by Risk (Ascending) -> Low risk first
            safe_sectors.sort(key=lambda x: x[2])

            # Display Top 3
            for i in range(min(3, len(safe_sectors))):
                sector_name = safe_sectors[i][0].replace("_", " ")
                st.success(f"**{sector_name}** ({safe_sectors[i][1]} jobs)")

        st.divider()

        # --- VISUALIZATION 4: BIAS ANALYSIS ---
        st.subheader("🤖 AI Bias Warning")
        
        admin_count = result['raw_data'].get('Office_Admin', 0)
        total = result['total_workers']
        admin_percent = int((admin_count / total) * 100)

        if (admin_count / total) > 0.15:
            st.warning(f"""
            **High Administrative Exposure Detected.** {admin_percent}% of this zip code works in Office & Admin Support.
            
            *Why this matters:* Research suggests AI tools (like LLMs) disproportionately impact 
            clerical roles, which historically employ a higher percentage of women. 
            This area may face gender-skewed economic disruption.
            """)
        else:
            st.info(f"""
            **Low Administrative Exposure.**
            Only {admin_percent}% of this workforce is in Office/Admin roles. 
            This area relies more on physical or specialized labor, which currently shows less algorithmic bias regarding displacement.
            """)
