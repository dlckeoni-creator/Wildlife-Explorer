import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. API Configuration
# ==========================================
# Replace with your actual key or use st.secrets["API_KEY"] if deploying to Streamlit Cloud
API_KEY = "YOUR_API_KEY" 

if API_KEY != "YOUR_API_KEY":
    genai.configure(api_key=API_KEY)
    # Using flash for fast, dynamic generation
    model = genai.GenerativeModel('gemini-1.5-flash') 
else:
    model = None

# ==========================================
# 2. Session State Management
# ==========================================
# This prevents the app from forgetting data when the user clicks a button
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
# 3. App UI & Logic
# ==========================================
st.set_page_config(page_title="Wildlife Conservation Explorer", page_icon="🐾", layout="centered")

st.title("🐾 Wildlife Conservation Explorer")
st.write("Discover endangered species across the United States and brainstorm ways to secure their future.")
st.markdown("---")

# Stop the app if API key is missing
if model is None:
    st.error("⚠️ Please add your Gemini API key at the top of the app.py code to activate the AI.")
    st.stop()

# --- STAGE 1: Selection & List Generation ---
if st.session_state.stage == 'selection':
    regions = ["West", "South", "Mid-west", "Northeast"]
    classes = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Invertebrates"]

    col1, col2 = st.columns(2)
    with col1:
        selected_class = st.selectbox("1. Choose an Animal Class:", classes)
    with col2:
        selected_region = st.selectbox("2. Choose a US Region:", regions)

    if st.button("Generate Top 10 Endangered List"):
        with st.spinner("AI is researching the region..."):
            # Prompting the AI to return a clean, comma-separated list
            prompt = f"List the top 10 most threatened or endangered {selected_class} in the {selected_region}ern United States. Return ONLY a comma-separated list of their common names, nothing else."
            response = model.generate_content(prompt)
            
            # Clean up the AI output into a Python list
            clean_list = [name.strip() for name in response.text.split(",") if name.strip()]
            st.session_state.animal_list = clean_list
            st.success("List generated!")

    # If the list has been generated, show the next dropdown
    if st.session_state.animal_list:
        st.subheader(f"Endangered {selected_class} in the {selected_region}")
        chosen_animal = st.selectbox("Select a species to learn more:", st.session_state.animal_list)
        
        if st.button("Research This Species"):
            st.session_state.selected_animal_name = chosen_animal
            set_stage('loading_profile')
            st.rerun()

# --- STAGE 2: Generate & Show Animal Details ---
elif st.session_state.stage == 'loading_profile':
    with st.spinner(f"AI is compiling data on the {st.session_state.selected_animal_name}..."):
        # We ask the AI to output strictly in JSON so we can format it perfectly in Streamlit
        prompt = f"""
        Act as a wildlife biologist. Provide information on the endangered {st.session_state.selected_animal_name} in the United States.
        You MUST return the data in strict JSON format with exactly these keys:
        "description": "A brief physical description.",
        "history": "A brief history of the species.",
        "survival_data": "Important data about how it survives (diet, territory, etc).",
        "endangerment_reasons": "Why and how it became endangered.",
        "habitat": "Specific locations where its habitat is.",
        "issues": ["Issue 1", "Issue 2", "Issue 3"] (An array of exactly 3 pressing concerns for survival)
        
        Do not use markdown blocks, just return the raw JSON.
        """
        
        try:
            response = model.generate_content(prompt)
            # Clean the response in case the AI wraps it in markdown code blocks
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            st.session_state.animal_profile = json.loads(clean_json)
            set_stage('details')
            st.rerun()
        except Exception as e:
            st.error("The AI had trouble formatting the data. Please try again.")
            if st.button("← Back"):
                set_stage('selection')
                st.rerun()

elif st.session_state.stage == 'details':
    profile = st.session_state.animal_profile
    
    st.header(st.session_state.selected_animal_name)
    
    st.markdown(f"**Description:** {profile.get('description', 'N/A')}")
    st.markdown(f"**Brief History:** {profile.get('history', 'N/A')}")
    st.markdown(f"**Survival Data:** {profile.get('survival_data', 'N/A')}")
    st.markdown(f"**Why they are endangered:** {profile.get('endangerment_reasons', 'N/A')}")
    st.markdown(f"**Specific Habitat:** {profile.get('habitat', 'N/A')}")
    
    st.error("**Top 3 Pressing Concerns:**")
    for i, issue in enumerate(profile.get('issues', []), 1):
        st.write(f"{i}. {issue}")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to List"):
            set_stage('selection')
            st.rerun()
    with col2:
        if st.button("Continue to Action Plan →"):
            set_stage('action')
            st.rerun()

# --- STAGE 3: AI Brainstorming ---
elif st.session_state.stage == 'action':
    profile = st.session_state.animal_profile
    animal_name = st.session_state.selected_animal_name
    
    st.header("Take Action")
    st.write(f"Focusing on the **{animal_name}**, please select one of the pressing issues below that you'd like to help solve:")
    
    chosen_issue = st.radio("Select an issue:", profile.get('issues', []))
    
    user_idea = st.text_area(
        "What is something that can be done in order to help solve this species' issue?", 
        placeholder="Type your creative solution here..."
    )
    
    if st.button("Submit Idea"):
        if not user_idea:
            st.warning("Please enter an idea first!")
        else:
            with st.spinner("The AI is reviewing your conservation strategy..."):
                prompt = f"""
                You are a wildlife conservation expert. 
                Animal: {animal_name}
                Issue: {chosen_issue}
                User's Idea: {user_idea}
                
                Please evaluate the user's idea based on these criteria:
                1. Point out any major flaws or logistical challenges in their idea.
                2. Suggest a realistic, practical approach to carrying out their idea.
                3. Tell the user what the absolute first step is to help make their idea a reality.
                
                Keep the response encouraging, structured, and under 300 words.
                """
                
                response = model.generate_content(prompt)
                st.success("Analysis Complete!")
                st.markdown("### Expert Feedback:")
                st.write(response.text)
                
                st.markdown("---")
                st.markdown("### **Your concern for wildlife well-being is appreciated!**")
                st.write("Here are some organizations where you can continue to help:")
                st.markdown("""
                * [World Wildlife Fund (WWF)](https://www.worldwildlife.org/)
                * [National Wildlife Federation](https://www.nwf.org/)
                * [Center for Biological Diversity](https://www.biologicaldiversity.org/)
                """)
            
    st.markdown("---")
    if st.button("← Back to Species Details"):
        set_stage('details')
        st.rerun()
