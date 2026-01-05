import streamlit as st
import requests
import vertexai
# We import 'GoogleSearch' directly to manually build the tool
from vertexai.generative_models import GenerativeModel, Tool, GoogleSearch
import os

# --- 1. CONFIGURATION ---
PROJECT_ID = "travel-app-plan-01" 
GUMROAD_PRODUCT_ID = "mELAK3OMYuHEWyMiVJQtkA=="

# --- 2. AUTHENTICATION ---
def check_license(key):
    try:
        response = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={"product_id": GUMROAD_PRODUCT_ID, "license_key": key}
        )
        data = response.json()
        return data.get("success", False) and not data.get("purchase", {}).get("refunded", False)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False

# Session State
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 VIP Travel Agent Login")
    key_input = st.text_input("Enter License Key", type="password")
    if st.button("Log In"):
        if check_license(key_input):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid License Key.")
    st.stop()

# --- 3. APP LOGIC ---
st.set_page_config(page_title="Live Travel Planner", page_icon="✈️")
vertexai.init(project=PROJECT_ID, location="us-central1")

# --- THE FIX: Manual Tool Construction ---
# This explicitly creates the tool for Gemini 2.0
tool = Tool(google_search=GoogleSearch())

system_instruction = """
You are an expert Live Travel Planner. 
MANDATORY: Use Google Search to verify all prices and hours.
Output format: Structured itinerary with BOLD prices.
"""

model = GenerativeModel(
    "gemini-2.0-flash-001", 
    system_instruction=[system_instruction],
    tools=[tool]
)

st.title("✈️ Live AI Travel Planner (2.0)")
destination = st.text_input("Where to?", "Kyoto, Japan")
when = st.text_input("When?", "Next April")
preferences = st.text_area("Interests?", "Food, History")

if st.button("Plan Trip"):
    with st.spinner("Using Gemini 2.0 Flash..."):
        try:
            prompt = f"Plan a trip to {destination} for {when}. User likes: {preferences}."
            response = model.generate_content(prompt)
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
