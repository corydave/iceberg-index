# The Iceberg Index: Local AI Disruption Map

**A localized visualization tool for analyzing "Hidden" AI labor market exposure.**

<center>

[**View Live App**](https://iceberg-index.streamlit.app/)

</center>

## About the Project
Popular narratives often frame AI disruption as a "Tech Sector" problem affecting coders and software engineers. The **Iceberg Index** challenges this view. It posits that visible tech disruption is merely the "tip of the iceberg," while the largest volume of exposure lies "submerged" in administrative, logistical, and middle-management roles.

This tool allows educators, policymakers, and community leaders to visualize this exposure at the **Zip Code level**, effectively creating a "Digital Twin" of the local economy to assess AI readiness.

## Visualizations & Features

* **Disruption Index Score:** A composite score (0-100) indicating the aggregate AI exposure of a local workforce.
* **The "Quadrant of Doom" (Risk vs. Reward):** An economic vulnerability matrix comparing **Estimated Salary** against **AI Risk**. It visually demonstrates that high-paying jobs are often highly exposed.
* **Economic Shape (Radar Chart):** Benchmarks the local job mix against the National US Average to identify local economic specializations.
* **Education Paradox:** Analyzes risk by education level, highlighting how degrees (Bachelor's/Master's) often correlate with *higher* AI exposure than trade certifications.
* **Bias Warning:** Flags potential gender-skewed displacement risks in administrative-heavy zip codes.

## Data Sources & Methodology

This application bridges three distinct datasets to generate real-time analysis:

1.  **Workforce Data:** Real-time integration with the **US Census Bureau API** (American Community Survey 5-Year Data, 2023). This provides granular counts of workers by occupation for every Zip Code Tabulation Area (ZCTA) in the US.
2.  **AI Exposure Scores:** Based on the methodology from *Eloundou et al. (2023) "GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models."* Occupations are scored based on the technical feasibility of LLMs to reduce the time required for core tasks.
3.  **O*NET Crosswalk:** Custom logic maps specific O*NET job codes to broad Census occupational categories to allow for geospatial analysis.

## Tech Stack

* **Python 3.11**
* **Streamlit:** Frontend application framework.
* **Pandas:** Data manipulation and cross-referencing.
* **Altair & Plotly:** Advanced data visualization (Bubble & Radar charts).
* **US Census API:** Live data fetching.

## Installation & Local Development

To run this tool on your own machine:

1.  **Clone the repository**
    ```bash
    git clone https://github.com/corydave/iceberg-index
    ```

    ```
    cd iceberg-index
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up API Key**
    * Get a free key from the [US Census Bureau](https://api.census.gov/data/key_signup.html).
    * Create a `.env` file in the root directory.
    * Add your key: `CENSUS_API_KEY=your_key_here`

4.  **Run the App**
    ```bash
    streamlit run app.py
    ```

## License

This project is open-source and available under the MIT License.

***
*Built for the FLX AI Hub.*
