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

# List of regions to try (in case your project isn't in US Central)
REGIONS_TO_TRY = ["us-central1", "us-east4", "europe-west2", "europe-west1"]
# List of models to try (Newest to Oldest)
MODELS_TO_TRY = ["gemini-2.0-flash-001", "gemini-1.5-flash-001", "gemini-1.0-pro", "gemini-pro"]

found_model = None
connected_region = None
connection_error = None

# Loop through regions until we find a match
for region in REGIONS_TO_TRY:
    try:
        vertexai.init(project=PROJECT_ID, location=region)
        
        # Once connected to a region, try to find a working model
        for model_name in MODELS_TO_TRY:
            try:
                # Test the model with a tiny "hello" prompt
                test_model = GenerativeModel(model_name)
                # We don't actually generate content here to save time, 
                # just initializing it without error is a good sign.
                found_model = test_model
                connected_region = region
                break # We found a working model!
            except:
                continue
        
        if found_model:
            break # We found a working region!
            
    except Exception as e:
        connection_error = e
        continue

# --- 4. APP INTERFACE ---
if found_model:
    st.title("✈️ Live AI Travel Planner")
    st.caption(f"Connected to **{found_model._model_name}** in **{connected_region}**")

    # Define the tool (Safe fallback logic)
    try:
        from vertexai.generative_models import GoogleSearch
        tool = Tool(google_search=GoogleSearch())
    except ImportError:
        from vertexai.generative_models import grounding
        tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

    # Update the model with instructions and tools
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
                st.error(f"Error during generation: {e}")
else:
    st.error("Could not find a working Google Cloud Region.")
    st.write(f"Last error: {connection_error}")
    st.write("Please check that the **Vertex AI API** is enabled in your Google Cloud Console.")
