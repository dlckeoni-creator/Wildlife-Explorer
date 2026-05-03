import streamlit as st
from groq import Groq
import json
import pandas as pd
import plotly.express as px

# ==========================================
# 1. API Configuration (Groq - High Speed)
# ==========================================
try:
    # Pulls the key from Streamlit Cloud Secrets
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # We use Llama 3.3 70B - it is incredibly fast and smart
    AI_MODEL = "llama-3.3-70b-versatile" 
except Exception:
    client = None

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

def set_stage(stage):
    st.session_state.stage = stage

# ==========================================
# 3. The "Cartoon Map" (Plotly)
# ==========================================
def draw_region_map():
    state_mapping = {
        'WA':'West', 'OR':'West', 'CA':'West', 'NV':'West', 'ID':'West', 'MT':'West', 'WY':'West', 'UT':'West', 'AZ':'West', 'NM':'West', 'CO':'West', 'AK':'West', 'HI':'West',
        'ND':'Mid-west', 'SD':'Mid-west', 'NE':'Mid-west', 'KS':'Mid-west', 'MN':'Mid-west', 'IA':'Mid-west', 'MO':'Mid-west', 'WI':'Mid-west', 'IL':'Mid-west', 'MI':'Mid-west', 'IN':'Mid-west', 'OH':'Mid-west',
        'TX':'South', 'OK':'South', 'AR':'South', 'LA':'South', 'MS':'South', 'TN':'South', 'KY':'South', 'AL':'South', 'GA':'South', 'FL':'South', 'SC':'South', 'NC':'South', 'VA':'South', 'WV':'South', 'MD':'South', 'DE':'South',
        'PA':'Northeast', 'NJ':'Northeast', 'NY':'Northeast', 'CT':'Northeast', 'RI':'Northeast', 'MA':'Northeast', 'VT':'Northeast', 'NH':'Northeast', 'ME':'Northeast'
    }
    df = pd.DataFrame(list(state_mapping.items()), columns=['State', 'Region'])
    # Your specific colors: West=Blue, South=Red, Mid-west=Yellow, Northeast=Green
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

if client is None:
    st.error("⚠️ Groq API Key Not Found. Check your Streamlit Secrets.")
    st.stop()

# --- STAGE 1: Selection ---
if st.session_state.stage == 'selection':
    st.plotly_chart(draw_region_map(), use_container_width=True)
    
    st.write("### 🐾 Start Your Discovery")
    regions = ["West", "South", "Mid-west", "Northeast"]
    classes = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Invertebrates"]

    col1, col2 = st.columns(2)
    with col1:
        chosen_region = st.selectbox("1. Choose a Region:", regions)
    with col2:
        chosen_class = st.selectbox("2. Choose an Animal Class:", classes)

    if st.button("Generate Top 10 List"):
        with st.spinner("Groq AI is researching..."):
            prompt = f"List the top 10 most endangered {chosen_class} in the {chosen_region}ern USA. Return ONLY a comma-separated list of common names, nothing else."
            
            completion = client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text_result = completion.choices[0].message.content
            st.session_state.animal_list = [n.strip() for n in text_result.split(",") if n.strip()]
            st.rerun()

    if st.session_state.animal_list:
        st.markdown("---")
        selected = st.selectbox("3. Pick an animal to investigate:", st.session_state.animal_list)
        if st.button("Research Species Details"):
            st.session_state.selected_animal_name = selected
            set_stage('loading_profile')
            st.rerun()

# --- STAGE 2: Generate Profile ---
elif st.session_state.stage == 'loading_profile':
    with st.spinner(f"Groq fetching data for the {st.session_state.selected_animal_name}..."):
        prompt = f"""Generate wildlife data for the {st.session_state.selected_animal_name}.
        Return ONLY raw JSON with these exact keys:
        'description', 'history', 'survival_data', 'endangerment_reasons', 'habitat', 'issues' (list of 3 strings)."""
        
        try:
            # Groq's JSON mode is extremely reliable
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            st.session_state.animal_profile = json.loads(response.choices[0].message.content)
            set_stage('details')
            st.rerun()
        except Exception as e:
            st.error(f"Error researching animal: {e}")
            if st.button("← Back to Selection"):
                set_stage('selection')
                st.rerun()

# --- STAGE 3: Show Details ---
elif st.session_state.stage == 'details':
    p = st.session_state.animal_profile
    st.header(f"Species Profile: {st.session_state.selected_animal_name}")
    
    st.write(f"**Description:** {p['description']}")
    st.write(f"**History:** {p['history']}")
    st.write(f"**Specific Habitat:** {p['habitat']}")
    st.write(f"**Survival Skills:** {p['survival_data']}")
    st.write(f"**Why they are Endangered:** {p['endangerment_reasons']}")
    
    st.error("### ⚠️ Top 3 Pressing Concerns")
    for i, issue in enumerate(p['issues'], 1):
        st.write(f"{i}. {issue}")
    
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
    user_idea = st.text_area("What is something that can be done in order to help solve this specie'
