import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px

# ==========================================
# 1. API Configuration (Secrets Integration)
# ==========================================
# This pulls the key from your Streamlit Cloud Advanced Settings -> Secrets
try:
    API_KEY = st.secrets["API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('models/gemini-1.5-flash') 
except Exception:
    # If the secret isn't found, the error check below will trigger
    model = None

# ==========================================
# 2. Session State Management
# ==========================================
if 'stage' not in st.session_state:
    st.session_state.stage = 'selection'
if 'animal_list' not in st.session_state:
    st.session_state.animal_list = []
if 'selected_animal_name' not in st.session_state:
    st.session_state.selected_animal_name = None
if 'animal_profile' not in st.session_state:
    st.session_state.animal_profile = None
if 'chosen_region' not in st.session_state:
    st.session_state.chosen_region = "West"
if 'chosen_class' not in st.session_state:
    st.session_state.chosen_class = "Mammals"

def set_stage(stage):
    st.session_state.stage = stage

# ==========================================
# 3. Map Generation Function
# ==========================================
def draw_region_map():
    state_mapping = {
        'WA':'West', 'OR':'West', 'CA':'West', 'NV':'West', 'ID':'West', 'MT':'West', 'WY':'West', 'UT':'West', 'AZ':'West', 'NM':'West', 'CO':'West', 'AK':'West', 'HI':'West',
        'ND':'Mid-west', 'SD':'Mid-west', 'NE':'Mid-west', 'KS':'Mid-west', 'MN':'Mid-west', 'IA':'Mid-west', 'MO':'Mid-west', 'WI':'Mid-west', 'IL':'Mid-west', 'MI':'Mid-west', 'IN':'Mid-west', 'OH':'Mid-west',
        'TX':'South', 'OK':'South', 'AR':'South', 'LA':'South', 'MS':'South', 'TN':'South', 'KY':'South', 'AL':'South', 'GA':'South', 'FL':'South', 'SC':'South', 'NC':'South', 'VA':'South', 'WV':'South', 'MD':'South', 'DE':'South',
        'PA':'Northeast', 'NJ':'Northeast', 'NY':'Northeast', 'CT':'Northeast', 'RI':'Northeast', 'MA':'Northeast', 'VT':'Northeast', 'NH':'Northeast', 'ME':'Northeast'
    }
    
    df = pd.DataFrame(list(state_mapping.items()), columns=['State', 'Region'])
    
    color_map = {
        'West': '#3498db',      # Blue
        'South': '#e74c3c',     # Red
        'Mid-west': '#f1c40f',  # Yellow
        'Northeast': '#2ecc71'  # Green
    }

    fig = px.choropleth(
        df, 
        locations='State', 
        locationmode="USA-states", 
        color='Region',
        color_discrete_map=color_map,
        scope="usa",
        title="US Wildlife Regions Map"
    )
    
    fig.update_layout(
        geo=dict(showlakes=False, bgcolor='rgba(0,0,0,0)'),
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# ==========================================
# 4. App UI & Logic
# ==========================================
st.set_page_config(page_title="Endangered Species Awareness", page_icon="🌍", layout="centered")

st.title("🌍 US Endangered Species Explorer")
st.markdown("---")

# Check if the model initialized correctly
if model is None:
    st.error("⚠️ API Key Not Found. Please ensure 'API_KEY' is added to your Streamlit Secrets.")
    st.info("Go to: Manage App -> Settings -> Secrets and add: API_KEY = 'your_key_here'")
    st.stop()

# --- STAGE 1: Visual Map & Selection ---
if st.session_state.stage == 'selection':
    st.plotly_chart(draw_region_map(), use_container_width=True)
    
    st.write("### 1. Select Region and Class")
    regions = ["West", "South", "Mid-west", "Northeast"]
    classes = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Invertebrates"]

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.chosen_region = st.selectbox("Choose a Region:", regions)
    with col2:
        st.session_state.chosen_class = st.selectbox("Choose an Animal Class:", classes)

    if st.button("Generate Top 10 Endangered List"):
        with st.spinner("AI is analyzing regional conservation data..."):
            prompt = f"List the top 10 most threatened or endangered {st.session_state.chosen_class} in the {st.session_state.chosen_region}ern United States. Return ONLY a comma-separated list of their common names, nothing else."
            response = model.generate_content(prompt)
            clean_list = [name.strip() for name in response.text.split(",") if name.strip()]
            st.session_state.animal_list = clean_list
            st.rerun()

    if st.session_state.animal_list:
        st.markdown("---")
        st.subheader(f"Top 10 Endangered {st.session_state.chosen_class}")
        chosen_animal = st.selectbox("Choose an animal to research:", st.session_state.animal_list)
        
        if st.button("View Detailed Profile"):
            st.session_state.selected_animal_name = chosen_animal
            set_stage('loading_profile')
            st.rerun()

# --- STAGE 2: Generate Animal Profile ---
elif st.session_state.stage == 'loading_profile':
    with st.spinner(f"Biologist AI is researching the {st.session_state.selected_animal_name}..."):
        prompt = f"""
        Provide information on the endangered {st.session_state.selected_animal_name} in the US.
        Return ONLY raw JSON with these keys:
        "description": "Short/detailed physical description.",
        "history": "Brief history of the species.",
        "survival_data": "How it survives (diet, territory).",
        "endangerment_reasons": "Why and how it became endangered.",
        "habitat": "Specific habitat location within its region.",
        "issues": ["Issue 1", "Issue 2", "Issue 3"]
        """
        try:
            response = model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            st.session_state.animal_profile = json.loads(clean_json)
            set_stage('details')
            st.rerun()
        except Exception:
            st.error("AI Research Error. Please try again.")
            if st.button
