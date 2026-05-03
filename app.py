import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px

# ==========================================
# 1. API Configuration & Model Picker
# ==========================================
def get_ai_model():
    try:
        API_KEY = st.secrets["API_KEY"]
        genai.configure(api_key=API_KEY)
        # We use a primary and a backup model to prevent the 'NotFound' error
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        return None

model = get_ai_model()

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
# 3. Map Generation (The Cartoon Map)
# ==========================================
def draw_region_map():
    state_mapping = {
        'WA':'West', 'OR':'West', 'CA':'West', 'NV':'West', 'ID':'West', 'MT':'West', 'WY':'West', 'UT':'West', 'AZ':'West', 'NM':'West', 'CO':'West', 'AK':'West', 'HI':'West',
        'ND':'Mid-west', 'SD':'Mid-west', 'NE':'Mid-west', 'KS':'Mid-west', 'MN':'Mid-west', 'IA':'Mid-west', 'MO':'Mid-west', 'WI':'Mid-west', 'IL':'Mid-west', 'MI':'Mid-west', 'IN':'Mid-west', 'OH':'Mid-west',
        'TX':'South', 'OK':'South', 'AR':'South', 'LA':'South', 'MS':'South', 'TN':'South', 'KY':'South', 'AL':'South', 'GA':'South', 'FL':'South', 'SC':'South', 'NC':'South', 'VA':'South', 'WV':'South', 'MD':'South', 'DE':'South',
        'PA':'Northeast', 'NJ':'Northeast', 'NY':'Northeast', 'CT':'Northeast', 'RI':'Northeast', 'MA':'Northeast', 'VT':'Northeast', 'NH':'Northeast', 'ME':'Northeast'
    }
    df = pd.DataFrame(list(state_mapping.items()), columns=['State', 'Region'])
    # Your requested colors: West=Blue, South=Red, Mid-west=Yellow, Northeast=Green
    color_map = {'West': '#3498db', 'South': '#e74c3c', 'Mid-west': '#f1c40f', 'Northeast': '#2ecc71'}

    fig = px.choropleth(
        df, locations='State', locationmode="USA-states", 
        color='Region', color_discrete_map=color_map, scope="usa"
    )
    fig.update_layout(
        geo=dict(showlakes=False, bgcolor='rgba(0,0,0,0)'),
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    return fig

# ==========================================
# 4. App UI & Logic
# ==========================================
st.set_page_config(page_title="Wildlife Explorer", page_icon="🌍", layout="centered")

st.title("🌍 US Endangered Species Explorer")
st.markdown("---")

if model is None:
    st.error("⚠️ API Key Error. Check your Streamlit Secrets.")
    st.stop()

# --- STAGE 1: Selection ---
if st.session_state.stage == 'selection':
    st.plotly_chart(draw_region_map(), use_container_width=True)
    
    st.write("### 🐾 Start Your Discovery")
    regions = ["West", "South", "Mid-west", "Northeast"]
    classes = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Invertebrates"]

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.chosen_region = st.selectbox("1. Choose a Region:", regions)
    with col2:
        st.session_state.chosen_class = st.selectbox("2. Choose an Animal Class:", classes)

    if st.button("Generate Top 10 List"):
        with st.spinner("AI is researching current species data..."):
            prompt = f"List the top 10 most endangered {st.session_state.chosen_class} in the {st.session_state.chosen_region}ern USA. Return ONLY a comma-separated list of common names."
            try:
                response = model.generate_content(prompt)
                st.session_state.animal_list = [n.strip() for n in response.text.split(",") if n.strip()]
                st.rerun()
            except Exception as e:
                st.error(f"Could not reach AI: {e}")

    if st.session_state.animal_list:
        st.markdown("---")
        chosen_animal = st.selectbox("3. Pick an animal to investigate:", st.session_state.animal_list)
        if st.button("Research Species Details"):
            st.session_state.selected_animal_name = chosen_animal
            set_stage('loading_profile')
            st.rerun()

# --- STAGE 2: Generate Profile (The fix is here!) ---
elif st.session_state.stage == 'loading_profile':
    with st.spinner(f"Compiling research for the {st.session_state.selected_animal_name}..."):
        # Explicit instruction to the AI to avoid errors
        prompt = f"""Generate wildlife data for the {st.session_state.selected_animal_name}.
        Return ONLY raw JSON with these exact keys:
        'description', 'history', 'survival_data', 'endangerment_reasons', 'habitat', 'issues' (list of 3 strings).
        Do not include markdown markers like ```json."""
        
        try:
            # First Attempt
            response = model.generate_content(prompt)
            clean_json = response.text.strip().replace("```json", "").replace("```", "")
            st.session_state.animal_profile = json.loads(clean_json)
            set_stage('details')
            st.rerun()
        except Exception:
            # Fallback Attempt if the first call fails
            try:
                # We try one more time with a slightly different model call
                fallback_model = genai.GenerativeModel('gemini-pro')
                response = fallback_model.generate_content(prompt)
                clean_json = response.text.strip().replace("```json", "").replace("```", "")
                st.session_state.animal_profile = json.loads(clean_json)
                set_stage('details')
                st.rerun()
            except Exception:
                st.error("The AI research tool is currently unavailable. Please go back and try a different animal.")
                if st.button("← Back to Selection"):
                    set_stage('selection')
                    st.rerun()

# --- STAGE 3: Show Details ---
elif st.session_state.stage == 'details':
    p = st.session_state.animal_profile
    st.header(f"Species Profile: {st.session_state.selected_animal_name}")
    
    st.subheader("Physical Description")
    st.write(p['description'])
    
    st.subheader("History & Habitat")
    st.write(f"**History:** {p['history']}")
    st.write(f"**Specific Habitat:** {p['habitat']}")
    
    st.subheader("Survival & Threat Data")
    st.write(f"**Survival Skills:** {p['survival_data']}")
    st.write(f"**Why they are Endangered:** {p['endangerment_reasons']}")
    
    st.error("### ⚠️ Top 3 Pressing Concerns")
    for issue in p['issues']:
        st.write(f"- {issue}")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Choose Different Animal"):
            set_stage('selection')
            st.rerun()
    with c2:
        if st.button("Propose a Solution →"):
            set_stage('action')
            st.rerun()

# --- STAGE 4: AI Brainstorming ---
elif st.session_state.stage == 'action':
    p = st.session_state.animal_profile
    st.header("Action Plan & AI Chat")
    
    issue = st.radio("Choose one of the 3 main issues to solve:", p['issues'])
    
    st.write("---")
    user_idea = st.text_area("What is something that can be done in order to help solve this specie's issue?", placeholder="Type your idea here...")
    
    if st.button("Submit Idea for AI Feedback"):
        if user_idea:
            with st.spinner("Our AI Expert is reviewing your proposal..."):
                prompt = f"Animal: {st.session_state.selected_animal_name}. Issue: {issue}. User Idea: {user_idea}. 1. Identify flaws. 2. Provide realistic approach. 3. First step for user."
                response = model.generate_content(prompt)
                
                st.info("### AI Feedback")
                st.write(response.text)
                
                st.success("### Your concern for wildlife well-being is appreciated!")
                st.write("Keep researching with these organizations:")
                st.markdown("- [World Wildlife Fund (WWF)](https://www.worldwildlife.org/)\n- [National Wildlife Federation](https://www.nwf.org/)\n- [Center for Biological Diversity](https://www.biologicaldiversity.org/)")
        else:
            st.warning("Please enter an idea first!")
    
    if st.button("← Back to Species Info"):
        set_stage('details')
        st.rerun()
