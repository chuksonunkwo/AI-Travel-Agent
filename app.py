import streamlit as st
import requests
import vertexai
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
    except:
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

# --- 3. AUTO-DISCOVERY ENGINE (The Fix) ---
st.set_page_config(page_title="Live Travel Planner", page_icon="✈️")

# We prioritize UK/Europe first since US failed
REGIONS_TO_TRY = ["europe-west2", "europe-west1", "us-central1", "us-east4", "asia-northeast1"]
# We try the standard stable models first
MODELS_TO_TRY = ["gemini-1.5-flash-001", "gemini-1.0-pro", "gemini-pro"]

found_model = None
connected_region = None
connection_error = None

status_text = st.empty()
status_text.caption("🔌 Connecting to Google Cloud...")

# Loop through regions until we find a match
for region in REGIONS_TO_TRY:
    try:
        # Try to connect to this region
        vertexai.init(project=PROJECT_ID, location=region)
        
        # Once connected, try to find a working model
        for model_name in MODELS_TO_TRY:
            try:
                # Just initializing the class checks if the model exists in this region
                test_model = GenerativeModel(model_name)
                found_model = test_model
                connected_region = region
                break # Found a working model!
            except:
                continue
        
        if found_model:
            break # Found a working region!
            
    except Exception as e:
        connection_error = e
        continue

status_text.empty() # Clear the loading text

# --- 4. APP INTERFACE ---
if found_model:
    st.title("✈️ Live AI Travel Planner")
    st.caption(f"✅ Connected to **{found_model._model_name}** in **{connected_region}**")

    # Safe Tool Loading (Fallback logic)
    try:
        # Try the modern tool first
        from vertexai.generative_models import GoogleSearch
        tool = Tool(google_search=GoogleSearch())
    except:
        # Fallback to the classic tool
        from vertexai.generative_models import grounding
        tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

    # Configure the model
    found_model._system_instruction = ["""
    You are an expert Live Travel Planner. 
    MANDATORY: Use Google Search to verify all prices and hours.
    Output format: Structured itinerary with BOLD prices.
    """]
    found_model._tools = [tool]

    destination = st.text_input("Where to?", "Luanda, Angola")
    when = st.text_input("When?", "Next April")
    preferences = st.text_area("Interests?", "Food, History")

    if st.button("Plan Trip"):
        with st.spinner("Planning..."):
            try:
                prompt = f"Plan a trip to {destination} for {when}. User likes: {preferences}."
                response = found_model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Generation Error: {e}")
else:
    st.error("❌ Could not connect to any Google Cloud Region.")
    st.write("We tried: London, Belgium, US, and Asia.")
    st.write(f"Last technical error: {connection_error}")
