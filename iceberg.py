import pandas as pd
import requests

# --- CONFIGURATION ---
CENSUS_API_KEY = "1c864adc7f0b8f04c2ad40412fe7f8abff5ea1e0"  # Get one at api.census.gov
YEAR = "2023"

# --- PART 1: DEFINE THE RISK MAP ---
# Since Census data is broader than O*NET, we manually map major Census buckets 
# to an approximate aggregate risk score based on the Eloundou et al. paper.
# High Score = High Automation Potential.
RISK_MAP = {
    # Management, business, science, and arts
    "Management": 0.65, 
    "Business_Financial": 0.75, 
    "Computer_Math": 0.85,    # The "Tip of the Iceberg"
    "Architecture_Engineering": 0.40,
    "Science": 0.35,
    "Legal": 0.80,            # High hidden exposure
    "Education": 0.50,        # Mixed (Grading vs Teaching)
    "Healthcare_Practitioners": 0.25,
    
    # Service Occupations
    "Healthcare_Support": 0.15,
    "Protective_Service": 0.10,
    "Food_Service": 0.10,
    "Cleaning_Maintenance": 0.05,
    
    # Sales & Office (THE HUGE HIDDEN SECTOR)
    "Sales": 0.55,
    "Office_Admin": 0.85,     # The "Submerged" part of the Iceberg
    
    # Blue Collar / Manual
    "Construction": 0.05,
    "Maintenance_Repair": 0.10,
    "Production": 0.15,
    "Transportation": 0.25,
}

# --- PART 2: CENSUS VARIABLES (ACS Subject Table S2401) ---
# These codes map to the broad categories above for the 2023 ACS 5-Year Data.
# S2401_C01_001E is Total. The rest are specific rows in that column.
CENSUS_VARS = {
    "S2401_C01_001E": "Total_Workers",
    "S2401_C01_002E": "Management", # Broad bucket
    "S2401_C01_005E": "Computer_Math", 
    "S2401_C01_013E": "Education",
    "S2401_C01_015E": "Healthcare_Practitioners",
    "S2401_C01_019E": "Healthcare_Support",
    "S2401_C01_021E": "Protective_Service",
    "S2401_C01_024E": "Food_Service",
    "S2401_C01_027E": "Sales",
    "S2401_C01_028E": "Office_Admin",
    "S2401_C01_031E": "Construction",
    "S2401_C01_036E": "Production",
    "S2401_C01_037E": "Transportation"
}

def get_zip_disruption_score(zip_code):
    # Construct the API Call
    vars_string = ",".join(CENSUS_VARS.keys())
    url = f"https://api.census.gov/data/{YEAR}/acs/acs5/subject?get={vars_string}&for=zip%20code%20tabulation%20area:{zip_code}&key={CENSUS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
    except:
        return None # Zip code likely invalid or not in ACS

    # Parse Response (Census returns [Headers, Data])
    headers = data[0]
    values = data[1]
    
    # Create a simple dictionary: {'Total_Workers': 15000, 'Management': 4000...}
    zip_data = {}
    for i, code in enumerate(headers):
        if code in CENSUS_VARS:
            friendly_name = CENSUS_VARS[code]
            try:
                zip_data[friendly_name] = int(values[i])
            except:
                zip_data[friendly_name] = 0

    # --- THE CALCULATION ---
    total_workers = zip_data.get("Total_Workers", 1)
    weighted_risk_sum = 0
    
    for category, count in zip_data.items():
        if category in RISK_MAP:
            # How many people * Risk Factor
            weighted_risk_sum += (count * RISK_MAP[category])

    # Final Index Score (0 to 100)
    # A score of 45+ is considered "High Exposure"
    final_score = (weighted_risk_sum / total_workers) * 100
    
    return {
        "zip": zip_code,
        "score": round(final_score, 1),
        "total_workers": total_workers,
        "primary_risk_factor": "Office & Admin" if zip_data.get("Office_Admin", 0) > zip_data.get("Computer_Math", 0) else "Tech"
    }

# --- TEST IT ---
# 14424 = Canandaigua, 14604 = Downtown Rochester, 94025 = Menlo Park (Meta HQ)
test_zips = ["14424", "14604", "94025"] 

print(f"{'ZIP':<10} | {'SCORE':<10} | {'MAIN RISK'}")
print("-" * 35)

for z in test_zips:
    result = get_zip_disruption_score(z)
    if result:
        print(f"{result['zip']:<10} | {result['score']:<10} | {result['primary_risk_factor']}")