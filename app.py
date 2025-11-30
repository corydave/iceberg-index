import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go # NEW IMPORT FOR RADAR CHART
import logic
from logic import RISK_SCORES

# --- REFERENCE DATA LOOKUP TABLES (APPROXIMATE NATIONAL AVERAGES) ---

# Estimated average annual salary for context (Source: BLS/O*NET proxy)
SALARY_ESTIMATES = {
    "Management": 110000, "Business_Financial": 85000, "Computer_Math": 105000,
    "Architecture_Engineering": 95000, "Science_Life_Physical": 80000, "Social_Services": 60000,
    "Legal": 120000, "Education": 65000, "Arts_Media": 70000,
    "Healthcare_Practitioners": 100000, "Healthcare_Support": 45000, "Protective_Service": 55000,
    "Food_Prep": 35000, "Cleaning_Maintenance": 38000, "Personal_Care": 40000,
    "Sales": 50000, "Office_Admin": 48000, "Farming_Fishing": 40000,
    "Construction": 55000, "Production": 45000, "Transportation": 50000, "Material_Moving": 38000
}

# Typical entry-level education required (Source: O*NET proxy)
EDUCATION_MAPPING = {
    "Management": "Bachelor's+", "Business_Financial": "Bachelor's", "Computer_Math": "Bachelor's+",
    "Architecture_Engineering": "Bachelor's+", "Science_Life_Physical": "Bachelor's+", "Social_Services": "Master's",
    "Legal": "Professional Degree", "Education": "Bachelor's/Master's", "Arts_Media": "Bachelor's",
    "Healthcare_Practitioners": "Professional Degree", "Healthcare_Support": "Certificate/Associate's", "Protective_Service": "High School/H.S. Diploma+",
    "Food_Prep": "No Formal Credential", "Cleaning_Maintenance": "No Formal Credential", "Personal_Care": "High School/Certificate",
    "Sales": "High School/H.S. Diploma+", "Office_Admin": "High School/H.S. Diploma+", "Farming_Fishing": "No Formal Credential",
    "Construction": "High School/Apprenticeship", "Production": "High School/H.S. Diploma+", "Transportation": "High School/Certificate", "Material_Moving": "No Formal Credential"
}

# Approximate National Workforce Composition Baseline (for comparison)
NATIONAL_BASELINE_PCT = {
    "Management": 11, "Business_Financial": 6, "Computer_Math": 4,
    "Architecture_Engineering": 2, "Science_Life_Physical": 1, "Social_Services": 2,
    "Legal": 1, "Education": 6, "Arts_Media": 2,
    "Healthcare_Practitioners": 6, "Healthcare_Support": 4, "Protective_Service": 2,
    "Food_Prep": 6, "Cleaning_Maintenance": 3, "Personal_Care": 3,
    "Sales": 9, "Office_Admin": 12, "Farming_Fishing": 1,
    "Construction": 5, "Production": 6, "Transportation": 4, "Material_Moving": 5
}
# ---------------------------------------------------------

# --- PAGE CONFIG ---
st.set_page_config(page_title="The Iceberg Index", layout="wide")
# ... rest of your app follows ...


# --- PAGE CONFIG ---
st.set_page_config(page_title="The Iceberg Index", layout="wide")

# --- HEADER ---
st.title("The Iceberg Index: Local AI Disruption Map")
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
        st.subheader("Job Composition in this Zip Code")
        
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
            st.subheader("Workforce Exposure")
            
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
            # st.bar_chart(risk_df.set_index('Category'), color=["#FF4B4B", "#FFA500", "#008000"])
            
            # Display Chart using Altair for custom colors
            risk_df = pd.DataFrame({
                'Category': ['High Risk (AI Ready)', 'Medium Risk (Augmented)', 'Low Risk (Safe)'],
                'Workers': [high_risk, med_risk, low_risk],
                'Color': ["#FF4B4B", "#FFA500", "#008000"] # We explicitly define the color for each row
            })

            c = alt.Chart(risk_df).mark_bar().encode(
                x=alt.X('Category', sort=None), # sort=None keeps our High/Med/Low order
                y='Workers',
                color=alt.Color('Color', scale=None), # Tell Altair to use the literal hex codes in our data
                tooltip=['Category', 'Workers']
            )
            
            st.altair_chart(c, use_container_width=True)        

        # --- VISUALIZATION 3: SAFE HARBORS ---
        with col_b:
            st.subheader("Local Safe Harbors")
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
        st.subheader("AI Bias Warning")
        
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


