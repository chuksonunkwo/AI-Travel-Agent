import streamlit as st
import requests
import vertexai
# NOTE: We removed 'GoogleSearch' from this line to prevent the crash
from vertexai.generative_models import GenerativeModel, Tool
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

# --- 3. BULLETPROOF MODEL SETUP ---
st.set_page_config(page_title="Live Travel Planner", page_icon="✈️")
vertexai.init(project=PROJECT_ID, location="us-central1")

# We define the tool inside a Try/Except block
# This prevents the "ImportError" from crashing the app at startup
try:
    # Try to import the NEW Gemini 2.0 tool
    from vertexai.generative_models import GoogleSearch
    tool = Tool(google_search=GoogleSearch())
    model_name = "gemini-2.0-flash-001"
    version_label = "2.0 Flash (Latest)"
except ImportError:
    # If that fails, fallback to the OLD Gemini 1.5 tool
    # We import 'grounding' here only if needed
    from vertexai.generative_models import grounding
    tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())
    model_name = "gemini-1.5-flash-001"
    version_label = "1.5 Flash (Backup)"

system_instruction = """
You are an expert Live Travel Planner. 
MANDATORY: Use Google Search to verify all prices and hours.
Output format: Structured itinerary with BOLD prices.
"""

model = GenerativeModel(
    model_name, 
    system_instruction=[system_instruction],
    tools=[tool]
)

# --- 4. APP INTERFACE ---
st.title("✈️ Live AI Travel Planner")
st.caption(f"Powered by Google Gemini {version_label}")

destination = st.text_input("Where to?", "Luanda, Angola")
when = st.text_input("When?", "Next April")
preferences = st.text_area("Interests?", "Food, History")

if st.button("Plan Trip"):
    with st.spinner(f"Planning with {version_label}..."):
        try:
            prompt = f"Plan a trip to {destination} for {when}. User likes: {preferences}."
            response = model.generate_content(prompt)
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
