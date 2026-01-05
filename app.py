import streamlit as st
import requests
import vertexai
# We import generic classes to avoid import errors
from vertexai.generative_models import GenerativeModel, Tool
import os

# --- 1. CONFIGURATION ---
PROJECT_ID = "travel-app-plan-01" 
GUMROAD_PRODUCT_ID = "mELAK3OMYuHEWyMiVJQtkA=="
LOCATION = "us-central1" # Explicitly defining location

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

# --- 3. ROBUST MODEL LOADING ---
st.set_page_config(page_title="Live Travel Planner", page_icon="✈️")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Try/Except block to handle library versions AND model availability
try:
    # OPTION A: Try the latest Gemini 2.0
    from vertexai.generative_models import GoogleSearch
    tool = Tool(google_search=GoogleSearch())
    model_name = "gemini-2.0-flash-001"
    version_label = "2.0 Flash (Latest)"
except ImportError:
    # OPTION B: Fallback to Gemini 1.0 Pro (The "Old Reliable")
    # We use this because we know it exists in your project
    from vertexai.generative_models import grounding
    tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())
    model_name = "gemini-1.0-pro" 
    version_label = "1.0 Pro (Standard)"

system_instruction = """
You are an expert Live Travel Planner. 
MANDATORY: Use Google Search to verify all prices and hours.
Output format: Structured itinerary with BOLD prices.
"""

# We wrap the model creation in another try block just in case
try:
    model = GenerativeModel(
        model_name, 
        system_instruction=[system_instruction],
        tools=[tool]
    )
except Exception as e:
    # If 2.0 fails for any reason, force downgrade to 1.0 immediately
    st.warning(f"Note: Switched to Standard Model due to: {e}")
    model = GenerativeModel("gemini-1.0-pro", system_instruction=[system_instruction])
    version_label = "1.0 Pro (Safe Mode)"

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
