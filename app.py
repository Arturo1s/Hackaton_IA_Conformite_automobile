from dotenv import load_dotenv
import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

# ----------------------------------------------------------
# 1. Hugging Face LLM CALLER
# ----------------------------------------------------------
import os
# Load environment variables from env/.env
load_dotenv(".env")

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

def hf_llm(prompt):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400
    }

    response = requests.post(
        "https://router.huggingface.co/chat/completions",
        headers=headers,
        json=payload,
        timeout=120
    )

    try:
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Unexpected response format: {result}"
    except Exception as e:
        try:
            error_data = response.json()
            return f"LLM error: {error_data}"
        except:
            return f"LLM error: {response.status_code} - {response.text}"


# ----------------------------------------------------------
# 2. SIMPLE SCRAPERS FOR REGULATION SOURCES
# ----------------------------------------------------------
def scrape_eu_regulations():
    """Scrape EU battery regulations (mock simplifié)."""
    url = "https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32023R1542"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    paragraphs = [p.get_text() for p in soup.find_all("p")]
    text = "\n".join(paragraphs[:20])  # simple + rapide
    return text


def scrape_nhtsa_airbags():
    """Scrape NHTSA mock."""
    url = "https://www.nhtsa.gov/laws-regulations"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    titles = [h.get_text() for h in soup.find_all("h2")]
    return "\n".join(titles[:15])


def scrape_china_cybersec():
    """Mock — pas de site officiel lisible sans login."""
    return """
China Automotive Cybersecurity Draft 2024:
- Mandatory encryption for CAN bus
- OTA updates must be logged and auditable
- All telematics modules must pass penetration testing
"""


# ----------------------------------------------------------
# 3. LLM — extract compliance requirements
# ----------------------------------------------------------
def extract_requirements(raw_text):
    prompt = f"""
You are a regulatory compliance extraction AI.
Extract clear engineering REQUIREMENTS from the following text.

TEXT:
{raw_text}

Return a list only, format:
- Requirement: <short engineering requirement>
    """

    return hf_llm(prompt)


# ----------------------------------------------------------
# 4. Compare with vehicle specs
# ----------------------------------------------------------
def compare_specs_to_requirements(requirements, vehicle_specs):

    prompt = f"""
You are an automotive compliance analysis AI.

Given the REQUIREMENTS extracted:
{requirements}

And the VEHICLE SPECIFICATIONS:
{vehicle_specs}

1. Determine requirement-by-requirement if the car is compliant (YES/NO).
2. Compute a GLOBAL COMPLIANCE SCORE (0-100%).
3. Return JSON only, format:

{{
  "score": <int>,
  "analysis": [
      {{"requirement": "...", "status": "YES/NO", "explanation": "..."}}
  ]
}}

Only return JSON, nothing else.
    """

    result = hf_llm(prompt)

    # Try to parse JSON safely
    try:
        json_start = result.index("{")
        json_data = json.loads(result[json_start:])
        return json_data
    except:
        return {"score": 0, "analysis": [{"requirement": "Parsing error", "status": "NO"}]}


# ----------------------------------------------------------
# STREAMLIT UI
# ----------------------------------------------------------
st.title("🔎 GPS Réglementaire – Prototype Hackathon")
st.subheader("Automated regulatory scraping + LLM compliance scoring")

st.markdown("---")

# ----------------------------------------------------------
# Step 1: Vehicle specifications
# ----------------------------------------------------------
st.header("🚗 1. Provide Vehicle Specifications")

vehicle_specs = st.text_area(
    "Enter car technical specifications:",
    """
Battery: 55 kWh Lithium-ion, meets REACH Annex XVII
Airbags: front + side, using Bosch airbag module 2024
Connectivity: 4G modem, OTA updates enabled, encrypted TLS1.3
Materials: dashboard plastic contains 8% recycled material
"""
)

# ----------------------------------------------------------
# Step 2: Select regulation sources
# ----------------------------------------------------------
st.header("📚 2. Select Regulation Sources to Scrape")

sources = st.multiselect(
    "Sources:",
    ["EU Battery Regulation", "US NHTSA Airbags", "China Cybersecurity"],
    default=["EU Battery Regulation", "US NHTSA Airbags"]
)


# ----------------------------------------------------------
# Step 3: SCRAPE
# ----------------------------------------------------------
if st.button("🔎 Scrape Regulations"):
    scraped_text = ""

    if "EU Battery Regulation" in sources:
        scraped_text += "\n\n=== EU Regulation ===\n" + scrape_eu_regulations()

    if "US NHTSA Airbags" in sources:
        scraped_text += "\n\n=== NHTSA Airbags ===\n" + scrape_nhtsa_airbags()

    if "China Cybersecurity" in sources:
        scraped_text += "\n\n=== China Cybersecurity ===\n" + scrape_china_cybersec()

    st.success("Regulations scraped!")
    st.text_area("Scraped Text", scraped_text, height=300)

    st.session_state["scraped"] = scraped_text


# ----------------------------------------------------------
# Step 4: Extract Requirements
# ----------------------------------------------------------
if "scraped" in st.session_state:
    if st.button("🧠 Extract Engineering Requirements (LLM)"):
        req = extract_requirements(st.session_state["scraped"])
        st.session_state["requirements"] = req
        st.success("Requirements extracted!")
        st.text_area("Extracted Requirements", req, height=250)


# ----------------------------------------------------------
# Step 5: Compliance Scoring
# ----------------------------------------------------------
if "requirements" in st.session_state:
    if st.button("📊 Compute Compliance Score"):
        result = compare_specs_to_requirements(
            st.session_state["requirements"],
            vehicle_specs
        )
        st.session_state["result"] = result

        st.success("Compliance score generated!")

        st.metric("Global Compliance Score", f"{result['score']} %")

        df = pd.DataFrame(result["analysis"])
        st.dataframe(df)
