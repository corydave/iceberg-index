import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go # NEW IMPORT FOR RADAR CHART
import logic
from logic import RISK_SCORES

# --- PAGE CONFIG ---
st.set_page_config(page_title="The Iceberg Index", layout="wide")

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

        # ... NEW VISUALIZATIONS ...
        
        st.divider()

        # =========================================
        # VIZ 1: THE QUADRANT OF DOOM (Bubble Chart)
        # =========================================
        st.subheader("💰 Economic Vulnerability Matrix (Risk vs. Reward)")
        st.markdown("Are high-paying jobs safer? Often, the opposite is true.")

        # 1. Prepare Data (Renaming keys to be 'Safe' for Altair)
        bubble_data = []
        for sector, count in result['raw_data'].items():
            if sector == "Total_Workers" or count == 0: continue 
            
            bubble_data.append({
                'Sector': sector.replace("_", " "),
                'Jobs': count,
                'Risk': float(RISK_SCORES.get(sector, 0.5)),
                'Salary': int(SALARY_ESTIMATES.get(sector, 50000))
            })
        
        bubble_df = pd.DataFrame(bubble_data)

        if not bubble_df.empty:
            # 2. Context Lines (Vertical at $60k, Horizontal at 0.5)
            # We define these FIRST so they sit behind the bubbles
            v_line = alt.Chart(pd.DataFrame({'Salary': [60000]})).mark_rule(strokeDash=[5,5], color='gray').encode(x='Salary:Q')
            h_line = alt.Chart(pd.DataFrame({'Risk': [0.5]})).mark_rule(strokeDash=[5,5], color='gray').encode(y='Risk:Q')

            # 3. Main Bubble Chart
            bubbles = alt.Chart(bubble_df).mark_circle().encode(
                x=alt.X('Salary:Q', axis=alt.Axis(title='Estimated Annual Salary', format='$,d'), scale=alt.Scale(zero=False, padding=20)),
                y=alt.Y('Risk:Q', axis=alt.Axis(title='AI Exposure Score (0.0 - 1.0)'), scale=alt.Scale(domain=[0, 1])),
                size=alt.Size('Jobs:Q', scale=alt.Scale(range=[100, 1000]), legend=None), 
                color=alt.Color('Risk:Q', scale=alt.Scale(scheme='greenblue', domain=[1, 0]), legend=None),
                tooltip=['Sector', 'Jobs', alt.Tooltip('Salary:Q', format='$,d'), 'Risk:Q']
            )

            # 4. Layer and Display
            # Note: We put bubbles LAST in the sum so they draw on top of the lines
            st.altair_chart(v_line + h_line + bubbles, use_container_width=True, theme="streamlit")
            st.caption("Bubbles sized by number of local jobs. Top-Right = High Pay / High Risk.")
        
        else:
            st.warning("Not enough data in this Zip Code to generate the Economic Matrix.")


        st.divider()

        # =========================================
        # VIZ 2: THE SPIDER WEB BENCHMARK (Radar Chart)
        # =========================================
        col_radar_L, col_radar_R = st.columns([2,1])

        with col_radar_L:
            st.subheader("🕸️ Economic Shape (Local vs. National)")
            st.markdown("How this area's job mix compares to the US average baseline.")

            # 1. Prepare Data (Calculate Local Percentages)
            radar_categories = []
            local_vals = []
            national_vals = []

            # Let's pick 8 representative sectors to keep the chart readable
            key_sectors = ["Management", "Computer_Math", "Healthcare_Practitioners", "Sales", 
                           "Office_Admin", "Construction", "Production", "Food_Prep"]

            total_local = result['total_workers']

            for sector in key_sectors:
                radar_categories.append(sector.replace("_", " "))
                # Calculate local %
                loc_count = result['raw_data'].get(sector, 0)
                local_vals.append((loc_count / total_local) * 100)
                # Get national baseline %
                national_vals.append(NATIONAL_BASELINE_PCT.get(sector, 0))
            
            # Close the loop for radar chart geometry
            radar_categories.append(radar_categories[0])
            local_vals.append(local_vals[0])
            national_vals.append(national_vals[0])

            # 2. Build Plotly Radar Chart
            fig = go.Figure()

            # Trace 1: National Baseline (Gray background)
            fig.add_trace(go.Scatterpolar(
                r=national_vals,
                theta=radar_categories,
                fill='toself',
                name='National Avg',
                line=dict(color='gray', dash='dot'),
                fillcolor='rgba(128, 128, 128, 0.2)'
            ))

            # Trace 2: Local Data (Blue highlight)
            fig.add_trace(go.Scatterpolar(
                r=local_vals,
                theta=radar_categories,
                fill='toself',
                name=f'Zip {target_zip}',
                line=dict(color='#0047AB'), # College Blue color
                fillcolor='rgba(0, 71, 171, 0.5)'
            ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, max(local_vals + national_vals) + 5])),
                showlegend=True,
                margin=dict(t=20, b=20, l=40, r=40)
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col_radar_R:
             st.info("""
             **How to read this:**
             The gray shape is the "typical" US economy. The blue shape is this specific zip code.
             
             Spikes indicate where this local economy is heavily concentrated compared to the norm.
             """)


        st.divider()
        
        # =========================================
        # VIZ 3: THE EDUCATION PARADOX
        # =========================================
        st.subheader("🎓 The 'Degree of Defense' Paradox")
        st.markdown("Does requiring a higher degree protect a sector from AI? Data suggests the opposite.")

        # 1. Prepare Data (Group by Education Level)
        edu_data = {}

        for sector, count in result['raw_data'].items():
             if sector == "Total_Workers" or count < 10: continue
             
             edu_level = EDUCATION_MAPPING.get(sector, "Unspecified")
             risk_score = RISK_SCORES.get(sector, 0.5)
             
             if edu_level not in edu_data:
                 edu_data[edu_level] = {'total_risk': 0, 'sector_count': 0}
             
             # We are averaging the risk scores of the sectors in this edu bucket
             edu_data[edu_level]['total_risk'] += risk_score
             edu_data[edu_level]['sector_count'] += 1

        # Format for chart
        final_edu_list = []
        for level, data in edu_data.items():
            if data['sector_count'] > 0:
                avg_risk = data['total_risk'] / data['sector_count']
                final_edu_list.append({'Education Level': level, 'Avg AI Risk': avg_risk})
        
        edu_df = pd.DataFrame(final_edu_list)

        # Define logical sort order for education
        edu_sort = ["No Formal Credential", "High School/Certificate", "High School/H.S. Diploma+", 
                    "High School/Apprenticeship", "Certificate/Associate's", "Bachelor's", 
                    "Bachelor's/Master's", "Bachelor's+", "Master's", "Professional Degree"]

        # 2. Build Altair Chart
        edu_chart = alt.Chart(edu_df).mark_bar().encode(
            x=alt.X('Education Level', sort=edu_sort),
            y=alt.Y('Avg AI Risk', scale=alt.Scale(domain=[0, 1])),
            color=alt.Color('Avg AI Risk', scale=alt.Scale(scheme='redyellowgreen', domain=[1, 0]), legend=None),
            tooltip=['Education Level', alt.Tooltip('Avg AI Risk', format='.2f')]
        ).properties(height=350)

        st.altair_chart(edu_chart, use_container_width=True)
        st.caption("Average AI Risk Score of sectors typically requiring this education level.")



