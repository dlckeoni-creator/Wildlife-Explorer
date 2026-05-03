import streamlit as st
import google.generativeai as genai

# Pull the API key securely from Streamlit's secrets
API_KEY = st.secrets["API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 1. API Configuration & Setup
# ==========================================
# Replace 'YOUR_API_KEY' with your actual Google Gemini API key
# Or set it as an environment variable for better security.
API_KEY = "YOUR_API_KEY" 
if API_KEY != "YOUR_API_KEY":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# ==========================================
# 2. Database (Sample Data)
# ==========================================
# To keep the code manageable, here is the structure using one example.
# You will expand this dictionary with the other 239 animals.
wildlife_data = {
    "West": {
        "Mammals": {
            "Gray Wolf": {
                "description": "The largest extant member of the canine family, known for their pack hunting.",
                "history": "Once roaming most of North America, their populations were decimated by the mid-20th century due to hunting and habitat loss.",
                "survival_data": "Packs require large territories (up to 1,000 square miles) and rely heavily on elk, deer, and moose.",
                "endangerment_reasons": "Human-wildlife conflict, habitat fragmentation, and loss of legal protections in certain states.",
                "habitat": "Forests, inland scrub, and mountainous regions in states like Idaho, Wyoming, and Washington.",
                "issues": [
                    "Conflict with local ranchers and livestock.",
                    "Habitat fragmentation blocking migration routes.",
                    "Poaching and illegal hunting."
                ]
            },
            "Sierra Nevada Bighorn Sheep": {
                "description": "A distinct subspecies of bighorn sheep known for their large, curled horns.",
                "history": "Population dropped to around 100 individuals in the 1990s due to diseases introduced by domestic sheep.",
                "survival_data": "They inhabit steep, rocky terrain to escape predators and forage on alpine vegetation.",
                "endangerment_reasons": "Disease transmission (pneumonia) from domestic sheep, mountain lion predation, and harsh winters.",
                "habitat": "The high peaks and eastern slopes of the Sierra Nevada mountains in California.",
                "issues": [
                    "Spread of fatal pneumonia from domestic sheep grazing nearby.",
                    "Predation by mountain lions on vulnerable, small herds.",
                    "Loss of foraging habitat due to climate change."
                ]
            }
        }
    }
}

regions = ["West", "South", "Mid-west", "Northeast"]
classes = ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Invertebrates"]

# ==========================================
# 3. Session State Management
# ==========================================
# Streamlit re-runs from top to bottom on every interaction. 
# We use session_state to remember where the user is in the flow.
if 'stage' not in st.session_state:
    st.session_state.stage = 'selection'
if 'selected_animal' not in st.session_state:
    st.session_state.selected_animal = None

def set_stage(stage):
    st.session_state.stage = stage

# ==========================================
# 4. App UI & Logic
# ==========================================
st.set_page_config(page_title="Wildlife Conservation Explorer", page_icon="🐾", layout="centered")

st.title("🐾 Wildlife Conservation Explorer")
st.write("Discover endangered species across the United States and brainstorm ways to secure their future.")
st.markdown("---")

# --- STAGE 1: Selection ---
if st.session_state.stage == 'selection':
    col1, col2 = st.columns(2)
    with col1:
        selected_class = st.selectbox("1. Choose an Animal Class:", classes)
    with col2:
        selected_region = st.selectbox("2. Choose a Region:", regions)

    st.subheader(f"Endangered {selected_class} in the {selected_region}")
    
    # Check if we have data for this combination
    if selected_region in wildlife_data and selected_class in wildlife_data[selected_region]:
        animals = list(wildlife_data[selected_region][selected_class].keys())
        chosen_animal = st.selectbox("Select a species to learn more:", animals)
        
        if st.button("Explore Species"):
            st.session_state.selected_animal = wildlife_data[selected_region][selected_class][chosen_animal]
            st.session_state.selected_animal_name = chosen_animal
            set_stage('details')
    else:
        st.info("Data for this specific region and class is currently being updated. Please try West -> Mammals for a live demo!")

# --- STAGE 2: Animal Details ---
elif st.session_state.stage == 'details':
    animal = st.session_state.selected_animal
    
    st.header(st.session_state.selected_animal_name)
    
    st.markdown(f"**Description:** {animal['description']}")
    st.markdown(f"**Brief History:** {animal['history']}")
    st.markdown(f"**Survival Data:** {animal['survival_data']}")
    st.markdown(f"**Why they are endangered:** {animal['endangerment_reasons']}")
    st.markdown(f"**Specific Habitat:** {animal['habitat']}")
    
    st.error("**Top 3 Pressing Concerns:**")
    for i, issue in enumerate(animal['issues'], 1):
        st.write(f"{i}. {issue}")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Selection"):
            set_stage('selection')
    with col2:
        if st.button("Continue to Action Plan →"):
            set_stage('action')

# --- STAGE 3: AI Brainstorming ---
elif st.session_state.stage == 'action':
    animal = st.session_state.selected_animal
    animal_name = st.session_state.selected_animal_name
    
    st.header("Take Action")
    st.write(f"Focusing on the **{animal_name}**, please select one of the pressing issues below that you'd like to help solve:")
    
    chosen_issue = st.radio("Select an issue:", animal['issues'])
    
    user_idea = st.text_area(
        "What is something that can be done in order to help solve this species' issue?", 
        placeholder="Type your creative solution here..."
    )
    
    if st.button("Submit Idea"):
        if not user_idea:
            st.warning("Please enter an idea first!")
        elif model is None:
            st.error("Please add your Gemini API key at the top of the code to enable the AI.")
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
                
                try:
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
                    
                except Exception as e:
                    st.error(f"An error occurred with the AI: {e}")
            
    st.markdown("---")
    if st.button("← Back to Species Details"):
        set_stage('details')
