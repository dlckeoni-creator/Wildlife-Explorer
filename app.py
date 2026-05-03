import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px

# ==========================================
# 1. API Configuration (Secrets Integration)
# ==========================================
try:
    API_KEY = st.secrets["API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('models/gemini-1.5-flash') 
except Exception:
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
    color_map = {'West': '#3498db', 'South': '#e74c3c', 'Mid-west': '#f1c40f', 'Northeast': '#2ecc71'}

    fig = px.choropleth(
        df, locations='State', locationmode="USA-states", 
        color='Region', color_discrete_map=color_map, scope="usa",
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

if model is None:
    st.error("⚠️ API Key Not Found. Please ensure 'API_KEY' is added to your Streamlit Secrets.")
    st.stop()

# --- STAGE 1: Selection ---
if st.session_state.stage == 'selection':
    st.plotly_chart(draw_region_map(), use_container_width=True)
    regions = ["West", "South", "Mid-west", "Northeast"]
    classes = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Invertebrates"]

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.chosen_region = st.selectbox("Choose a Region:", regions)
    with col2:
        st.session_state.chosen_class = st.selectbox("Choose an Animal Class:", classes)

    if st.button("Generate Top 10 Endangered List"):
        with st.spinner("AI is analyzing regional data..."):
            prompt = f"List the top 10 most threatened or endangered {st.session_state.chosen_class} in the {st.session_state.chosen_region}ern United States. Return ONLY a comma-separated list of names."
            response = model.generate_content(prompt)
            st.session_state.animal_list = [n.strip() for n in response.text.split(",") if n.strip()]
            st.rerun()

    if st.session_state.animal_list:
        st.markdown("---")
        chosen_animal = st.selectbox("Choose an animal:", st.session_state.animal_list)
        if st.button("View Detailed Profile"):
            st.session_state.selected_animal_name = chosen_animal
            set_stage('loading_profile')
            st.rerun()

# --- STAGE 2: Generate Profile ---
elif st.session_state.stage == 'loading_profile':
    with st.spinner(f"AI is researching {st.session_state.selected_animal_name}..."):
        prompt = f"Return ONLY raw JSON for the endangered {st.session_state.selected_animal_name} in the US with keys: 'description', 'history', 'survival_data', 'endangerment_reasons', 'habitat', 'issues' (list of 3)."
        try:
            response = model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            st.session_state.animal_profile = json.loads(clean_json)
            set_stage('details')
            st.rerun()
        except:
            st.error("Error researching animal.")
            if st.button("Back"):
                set_stage('selection')
                st.rerun()

# --- STAGE 3: Show Details ---
elif st.session_state.stage == 'details':
    p = st.session_state.animal_profile
    st.header(st.session_state.selected_animal_name)
    st.write(f"**Description:** {p['description']}")
    st.write(f"**History:** {p['history']}")
    st.write(f"**Survival Facts:** {p['survival_data']}")
    st.write(f"**Threats:** {p['endangerment_reasons']}")
    st.write(f"**Habitat:** {p['habitat']}")
    st.error("**Top 3 Pressing Concerns:**")
    for issue in p['issues']:
        st.write(f"⚠️ {issue}")
    
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

# --- STAGE 4: AI Chatbot ---
elif st.session_state.stage == 'action':
    p = st.session_state.animal_profile
    st.header("Conservation Brainstorming")
    issue = st.radio("Focus on this issue:", p['issues'])
    user_idea = st.text_area("What is something that can be done in order to help solve this specie's issue?")
    
    if st.button("Submit Idea to AI"):
        with st.spinner("Analyzing..."):
            prompt = f"Animal: {st.session_state.selected_animal_name}. Issue: {issue}. Idea: {user_idea}. 1. Identify flaws. 2. Realistic approach. 3. First step."
            response = model.generate_content(prompt)
            st.info("### AI Feedback")
            st.write(response.text)
            st.success("Your concern for wildlife well-being is appreciated!")
            st.markdown("- [WWF](https://www.worldwildlife.org/)\n- [NWF](https://www.nwf.org/)\n- [Center for Biological Diversity](https://www.biologicaldiversity.org/)")
    
    if st.button("← Back to Species Details"):
        set_stage('details')
        st.rerun()
