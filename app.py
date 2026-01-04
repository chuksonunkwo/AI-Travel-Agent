import streamlit as st
import requests
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, grounding

# --- CONFIGURATION ---
PROJECT_ID = "travel-app-plan-01" # REPLACE
LOCATION = "us-central1"
GUMROAD_PRODUCT_PERMALINK = "uzyyr" # REPLACE (e.g., if url is gumroad.com/l/xyz, put 'xyz')

# --- LICENSE VALIDATION FUNCTION ---
def check_license(key):
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_permalink": GUMROAD_PRODUCT_PERMALINK,
                "license_key": key
            }
        )
        data = response.json()
        return data.get("success", False) and not data.get("purchase", {}).get("refunded", False)
    except:
        return False

# --- SESSION STATE MGMT ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- THE GATE (LOGIN SCREEN) ---
if not st.session_state.authenticated:
    st.title("🔒 AI Travel Planner Login")
    st.write("Please enter your Gumroad License Key to access the tool.")
    
    license_input = st.text_input("License Key", type="password")
    
    if st.button("Login"):
        if check_license(license_input):
            st.session_state.authenticated = True
            st.success("Access Granted!")
            st.rerun()
        else:
            st.error("Invalid or expired license key.")
    
    st.markdown("---")
    st.markdown(f"[Get a License Key here](https://gumroad.com/l/{GUMROAD_PRODUCT_PERMALINK})")
    st.stop() # Stops the app here if not authenticated

# --- MAIN APP (ONLY RUNS IF AUTHENTICATED) ---
# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())
system_instruction = """
You are a live travel planner. MANDATORY: Use Google Search to verify all prices/hours.
Output format: JSON.
"""
model = GenerativeModel("gemini-1.5-pro-001", system_instruction=[system_instruction], tools=[tool])

st.title("✈️ VIP Live Travel Planner")
# ... (Rest of your travel app code goes here)
