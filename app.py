import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px

# ==========================================
# 1. API Configuration
# ==========================================
# Replace with your actual key (Keep this secure!)
API_KEY = "AIzaSyDWwWnJrk3-Jc0fubRsXWD9Vh_dHoWw6ZM" 

if API_KEY != "AIzaSyDWwWnJrk3-Jc0fubRsXWD9Vh_dHoWw6ZM":
    genai.configure(api_key=API_KEY)
    # Using 1.5-flash as the standard fast model
    model = genai.GenerativeModel('models/gemini-1.5-flash') 
else:
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
    # Define the 4 regions and their states
    state_mapping = {
        'WA':'West', 'OR':'West', 'CA':'West', 'NV':'West', 'ID':'West', 'MT':'West', 'WY':'West', 'UT':'West', 'AZ':'West', 'NM':'West', 'CO':'West', 'AK':'West', 'HI':'West',
        'ND':'Mid-west', 'SD':'Mid-west', 'NE':'Mid-west', 'KS':'Mid-west', 'MN':'Mid-west', 'IA':'Mid-west', 'MO':'Mid-west', 'WI':'Mid-west', 'IL':'Mid-west', 'MI':'Mid-west', 'IN':'Mid-west', 'OH':'Mid-west',
        'TX':'South', 'OK':'South', 'AR':'South', 'LA':'South', 'MS':'South', 'TN':'South', 'KY':'South', 'AL':'South', 'GA':'South', 'FL':'South', 'SC':'South', 'NC':'South', 'VA':'South', 'WV':'South', 'MD':'South', 'DE':'South',
        'PA':'Northeast', 'NJ':'Northeast', 'NY':'Northeast', 'CT':'Northeast', 'RI':'Northeast', 'MA':'Northeast', 'VT':'Northeast', 'NH':'Northeast', 'ME':'Northeast'
    }
    
    df = pd.DataFrame(list(state_mapping.items()), columns=['State', 'Region'])
    
    # Assign specific colors to regions based on your prompt
    color_map = {
        'West': '#3498db',      # Blue
        'South': '#e74c3c',     # Red
        'Mid-west': '#f1c40f',  # Yellow
        'Northeast': '#2ecc71'  # Green
    }

    # Create the choropleth map
    fig = px.choropleth(
        df, 
        locations='State', 
        locationmode="USA-states", 
        color='Region',
        color_discrete_map=color_map,
        scope="usa",
        title="US Wildlife Regions"
    )
    
    # Stylize to make it look cleaner and more "cartoon" flat
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
    st.error("⚠️ Please add your Gemini API key at the top of the app.py code.")
    st.stop()

# --- STAGE 1: Visual Map & Selection ---
if st.session_state.stage == 'selection':
    # Display the interactive map
    st.plotly_chart(draw_region_map(), use_container_width=True)
    
    st.write("### Select Your Parameters")
    regions = ["West", "South", "Mid-west", "Northeast"]
    classes = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Invertebrates"]

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.chosen_region = st.selectbox("1. Choose a Region from the map:", regions)
    with col2:
        st.session_state.chosen_class = st.selectbox("2. Choose an Animal Class:", classes)

    if st.button("Generate Top 10 Endangered List"):
        with st.spinner("AI is analyzing conservation data..."):
            prompt = f"List the top 10 most threatened or endangered {st.session_state.chosen_class} in the {st.session_state.chosen_region}ern United States. Return ONLY a comma-separated list of their common names, nothing else."
            response = model.generate_content(prompt)
            
            clean_list = [name.strip() for name in response.text.split(",") if name.strip()]
            st.session_state.animal_list = clean_list
            st.success("Data Retrieved!")

    # Show the list if it has been generated
    if st.session_state.animal_list:
        st.markdown("---")
        st.subheader(f"Top 10 Endangered {st.session_state.chosen_class} in the {st.session_state.chosen_region}")
        chosen_animal = st.selectbox("Select a specific animal to study:", st.session_state.animal_list)
        
        if st.button("Learn About This Species"):
            st.session_state.selected_animal_name = chosen_animal
            set_stage('loading_profile')
            st.rerun()

# --- STAGE 2: Generate Animal Profile ---
elif st.session_state.stage == 'loading_profile':
    with st.spinner(f"AI is compiling research on the {st.session_state.selected_animal_name}..."):
        prompt = f"""
        Act as a wildlife biologist. Provide information on the endangered {st.session_state.selected_animal_name} in the United States.
        Return the data in STRICT JSON format (no markdown blocks, just the raw JSON) with exactly these keys:
        "description": "Short and detailed physical description.",
        "history": "Brief history of the species.",
        "survival_data": "Important data about how it survives.",
        "endangerment_reasons": "Details on why and how it became endangered.",
        "habitat": "Where its specific habitat is located within its region.",
        "issues": ["Issue 1", "Issue 2", "Issue 3"] (An array of exactly the 3 most pressing concerns for survival)
        """
        try:
            response = model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            st.session_state.animal_profile = json.loads(clean_json)
            set_stage('details')
            st.rerun()
        except Exception as e:
            st.error("The AI had trouble formatting the data. Please try again.")
            if st.button("← Back"):
                set_stage('selection')
                st.rerun()

# --- STAGE 3: Show Profile ---
elif st.session_state.stage == 'details':
    profile = st.session_state.animal_profile
    
    st.header(st.session_state.selected_animal_name)
    st.markdown(f"**Description:** {profile.get('description', 'N/A')}")
    st.markdown(f"**Brief History:** {profile.get('history', 'N/A')}")
    st.markdown(f"**Survival Data:** {profile.get('survival_data', 'N/A')}")
    st.markdown(f"**Endangerment Details:** {profile.get('endangerment_reasons', 'N/A')}")
    st.markdown(f"**Specific Habitat:** {profile.get('habitat', 'N/A')}")
    
    st.error("**The 3 Most Pressing Concerns:**")
    for i, issue in enumerate(profile.get('issues', []), 1):
        st.write(f"{i}. {issue}")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Map & List"):
            set_stage('selection')
            st.rerun()
    with col2:
        if st.button("Continue to Action Plan →"):
            set_stage('action')
            st.rerun()

# --- STAGE 4: AI Chatbot & Solution Brainstorming ---
elif st.session_state.stage == 'action':
    profile = st.session_state.animal_profile
    animal_name = st.session_state.selected_animal_name
    
    st.header("Help Aid Survival")
    st.write(f"Focusing on the **{animal_name}**, please select one of the 3 main issues to focus on:")
    
    chosen_issue = st.radio("Select an issue:", profile.get('issues', []))
    
    st.markdown("### AI Conservation Chatbot")
    user_idea = st.text_area(
        "What is something that can be done in order to help solve this species' issue?", 
        placeholder="Type your idea here..."
    )
    
    if st.button("Submit Idea to AI"):
        if not user_idea:
            st.warning("Please enter your idea first.")
        else:
            with st.spinner("The AI is analyzing your approach..."):
                prompt = f"""
                You are an AI wildlife conservation chatbot. 
                Animal: {animal_name}
                Issue: {chosen_issue}
                User's Idea: {user_idea}
                
                Respond directly to the user addressing these three specific points:
                1. Point out any major flaws in their idea.
                2. Provide a realistic approach to carrying out their idea.
                3. State what the first step is in how the user can help make their idea a reality or help towards the cause.
                """
                response = model.generate_content(prompt)
                
                st.info("### AI Feedback")
                st.write(response.text)
                
                st.markdown("---")
                st.success("### Your concern for wildlife well-being is appreciated!")
                st.write("Learn more and support the cause by visiting these organizations:")
                st.markdown("""
                1. [World Wildlife Fund (WWF)](https://www.worldwildlife.org/)
                2. [National Wildlife Federation (NWF)](https://www.nwf.org/)
                3. [Center for Biological Diversity](https://www.biologicaldiversity.org/)
                """)
            
    st.markdown("---")
    if st.button("← Back to Animal Info"):
        set_stage('details')
        st.rerun()
