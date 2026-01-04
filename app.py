import streamlit as st
import requests
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, grounding
import os

# --- 1. CONFIGURATION ---
# Your Google Cloud Project ID
PROJECT_ID = "travel-app-plan-01" 

# --- THE FIX IS HERE ---
# We switched to 'product_id' and pasted the value from your error message
GUMROAD_PRODUCT_ID = "mELAK3OMYuHEWyMiVJQtkA=="

# --- 2. AUTHENTICATION (THE GATE) ---
def check_license(key):
    """Verifies the license key with Gumroad."""
    try:
        # Note: We changed 'product_permalink' to 'product_id' in the request below
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_id": GUMROAD_PRODUCT_ID, 
                "license_key": key
            }
        )
        data = response.json()
        
        # --- DEBUGGING (Keep this for now) ---
        if data.get("success") == False:
            st.error(f"Gumroad Error: {data.get('message', 'Unknown Error')}")
        # -------------------------------------

        return data.get("success", False) and not data.get("purchase", {}).get("refunded", False)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False

# Session State for Login
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 VIP Travel Agent Login")
    st.write("Enter your License Key to access the live planner.")
    
    key_input = st.text_input("License Key", type="password")
    
    if st.button("Log In"):
        with st.spinner("Verifying key..."):
            if check_license(key_input):
                st.session_state.authenticated = True
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("Invalid License Key. Please purchase access.")
    st.stop() # Stop here if not logged in

# --- 3. THE APP (ONLY RUNS AFTER LOGIN) ---
st.set_page_config(page_title="Live Travel Planner", page_icon="✈️")

vertexai.init(project=PROJECT_ID, location="us-central1")
tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

system_instruction = """
You are an expert Live Travel Planner. 
MANDATORY: You must use Google Search to verify all details (prices, hours, weather).
Output format: Produce a structured itinerary with BOLD prices and times.
"""

model = GenerativeModel(
    "gemini-1.5-pro-001",
    system_instruction=[system_instruction],
    tools=[tool]
)

st.title("✈️ Live AI Travel Planner")
st.caption("Real-time data powered by Google Gemini")

destination = st.text_input("Where to?", "Kyoto, Japan")
when = st.text_input("When?", "Next April")
preferences = st.text_area("What do you like?", "Food, History, Nature")

if st.button("Plan My Trip"):
    with st.spinner("Searching live prices and availability..."):
        try:
            prompt = f"Plan a trip to {destination} for {when}. User likes: {preferences}."
            response = model.generate_content(prompt)
            st.markdown(response.text)
        except Exception as e:
            st.error(f"An error occurred: {e}")
