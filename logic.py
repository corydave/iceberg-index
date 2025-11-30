import os
import requests
from dotenv import load_dotenv

# Load the API Key from your .env file
load_dotenv()
API_KEY = os.getenv("CENSUS_API_KEY")

# --- CONFIGURATION ---
YEAR = "2024"
DATA_SET = "acs/acs5/subject" # American Community Survey 5-Year Data

# --- THE "PROXY" RISK MAP ---
# This dictionary acts as the "Crosswalk" between Census Job Buckets and AI Risk.
# Scores are derived from the Eloundou et al. (OpenAI) paper "GPTs are GPTs".
# Scale: 0.0 (Safe) to 1.0 (Highly Exposed)
RISK_SCORES = {
    "Management": 0.60,
    "Business_Financial": 0.75,
    "Computer_Math": 0.95,        # The "Tip" (High visibility)
    "Architecture_Engineering": 0.45,
    "Science_Life_Physical": 0.40,
    "Social_Services": 0.25,
    "Legal": 0.85,                # High hidden risk (paralegals/contracts)
    "Education": 0.45,
    "Arts_Media": 0.70,           # High risk (Generative AI)
    "Healthcare_Practitioners": 0.25, # Doctors/Nurses (Low)
    "Healthcare_Support": 0.15,
    "Protective_Service": 0.10,
    "Food_Prep": 0.10,
    "Cleaning_Maintenance": 0.05,
    "Personal_Care": 0.15,
    "Sales": 0.55,
    "Office_Admin": 0.90,         # The "Submerged Iceberg" (High Volume)
    "Farming_Fishing": 0.05,
    "Construction": 0.05,
    "Production": 0.15,
    "Transportation": 0.25,
    "Material_Moving": 0.20
}

# --- CENSUS VARIABLE MAPPING ---
# S2401 is "Occupation by Sex for the Civilian Employed Population"
# S2401_C01_001E is "Total". The others are the broad job buckets.
CENSUS_VARS = {
    "S2401_C01_001E": "Total_Workers",
    "S2401_C01_002E": "Management",
    "S2401_C01_003E": "Business_Financial",
    "S2401_C01_005E": "Computer_Math",
    "S2401_C01_006E": "Architecture_Engineering",
    "S2401_C01_007E": "Science_Life_Physical",
    "S2401_C01_008E": "Social_Services",
    "S2401_C01_009E": "Legal",
    "S2401_C01_010E": "Education",
    "S2401_C01_011E": "Arts_Media",
    "S2401_C01_012E": "Healthcare_Practitioners",
    "S2401_C01_013E": "Healthcare_Support",
    "S2401_C01_014E": "Protective_Service",
    "S2401_C01_015E": "Food_Prep",
    "S2401_C01_016E": "Cleaning_Maintenance",
    "S2401_C01_017E": "Personal_Care",
    "S2401_C01_018E": "Sales",
    "S2401_C01_019E": "Office_Admin",
    "S2401_C01_020E": "Farming_Fishing",
    "S2401_C01_021E": "Construction",
    "S2401_C01_022E": "Production",
    "S2401_C01_023E": "Transportation",
    "S2401_C01_024E": "Material_Moving"
}

def get_data(zip_code):
    """
    Fetches raw Census data for a specific Zip Code.
    Returns a dictionary of {Category_Name: Worker_Count}
    """
    if not API_KEY:
        return {"error": "Missing API Key. Check your .env file."}

    # Prepare the API URL
    # We join all the variable codes with commas
    var_list = ",".join(CENSUS_VARS.keys())
    url = f"https://api.census.gov/data/{YEAR}/{DATA_SET}?get={var_list}&for=zip%20code%20tabulation%20area:{zip_code}&key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"Census API Error: {response.status_code}"}
            
        data = response.json()
        
        # Census returns a list of lists. Row 0 is headers, Row 1 is values.
        # We need to map the confusing codes (S2401...) to our friendly names.
        headers = data[0]
        values = data[1]
        
        parsed_data = {}
        
        for i, code in enumerate(headers):
            if code in CENSUS_VARS:
                friendly_name = CENSUS_VARS[code]
                try:
                    # Convert "1,200" string to 1200 integer
                    count = int(values[i]) if values[i] else 0
                    parsed_data[friendly_name] = count
                except ValueError:
                    parsed_data[friendly_name] = 0
                    
        return parsed_data

    except Exception as e:
        return {"error": str(e)}

def calculate_iceberg_score(zip_code):
    """
    The Main Logic:
    1. Gets jobs for the zip code.
    2. Multiplies job counts by Risk Score.
    3. Returns a weighted average (0-100).
    """
    # 1. Get the Data
    jobs_data = get_data(zip_code)
    
    if "error" in jobs_data:
        return jobs_data # Pass the error up to the UI
        
    total_workers = jobs_data.get("Total_Workers", 0)
    
    if total_workers < 10:
        return {"error": "Population too low to calculate index."}

    # 2. Calculate Weighted Risk
    total_risk_mass = 0
    
    # We also want to find what is driving the risk (for the UI)
    highest_risk_category = "None"
    highest_count = 0

    for category, count in jobs_data.items():
        if category == "Total_Workers": continue
        
        # Get the risk factor (default to 0.5 if not found)
        risk_factor = RISK_SCORES.get(category, 0.5)
        
        # Accumulate the weighted score
        total_risk_mass += (count * risk_factor)
        
        # Track the biggest sector for the UI "Insight"
        if count > highest_count:
            highest_count = count
            highest_risk_category = category

    # 3. Normalize to 0-100
    final_score = (total_risk_mass / total_workers) * 100
    
    return {
        "zip": zip_code,
        "index_score": round(final_score, 1),
        "total_workers": total_workers,
        "dominant_sector": highest_risk_category.replace("_", " "),
        "raw_data": jobs_data # Return this so we can graph it later!
    }

# --- TEST BLOCK ---
# This allows you to run "python logic.py" to verify it works
# before building the website.
if __name__ == "__main__":
    test_zip = "14424" # Canandaigua
    print(f"Testing logic for {test_zip}...")
    result = calculate_iceberg_score(test_zip)
    print(result)
