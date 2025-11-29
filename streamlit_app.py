import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

# Import the core agent logic, session service, and the LLM suggestion function
from main import pause_task, SESSION_SERVICE, suggest_next_step

# --- Streamlit Session State Initialization ---
if 'suggested_next_step' not in st.session_state:
    st.session_state['suggested_next_step'] = ""

# --- Helper function to call the real LLM Suggestor Agent ---
def llm_suggestion_handler(slack_id):
    
    st.session_state['suggested_next_step'] = "" 
    
    try:
        st.info("Running Suggestor Agent: Analyzing active context and communication...")
        
        suggestion = suggest_next_step(slack_id)

        st.session_state['suggested_next_step'] = suggestion
        st.success("Suggestion generated! Review and edit before pausing.")
    except Exception as e:
        st.error(f"Error during suggestion generation: {e}")

# --- Streamlit Application Setup ---

st.set_page_config(
    page_title="Contextual Recall Concierge",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 Contextual Recall Concierge")
st.subheader("Your AI-powered Task Memory Assistant")

# --- 1. PAUSE TASK INTERFACE (Input Form) ---

st.header("⏸️ Pause Current Task")

with st.form("pause_form"):
    st.markdown("##### 📝 Capture Context")
    
    project_name = st.text_input(
        "Project Name", 
        value="", 
        placeholder="e.g., Database Migration, API Refactor"
    )
    
    slack_channel_id = st.text_input(
        "Slack Channel ID (C0...)", 
        value="C09U8ART7QT", 
        placeholder="Required for fetching communication context"
    )

    # Suggestion Button 
    st.form_submit_button(
        "💡 Suggest Next Step (Analyze Context)", 
        on_click=llm_suggestion_handler, 
        args=[slack_channel_id]
    )
    
    next_step = st.text_area(
        "🎯 Absolute Next Step", 
        value=st.session_state['suggested_next_step'], 
        placeholder="e.g., Fix the CORS error in auth_middleware.py, OR click 'Suggest Next Step' above."
    )
    
    submitted = st.form_submit_button("Capture & Pause Task")

    if submitted:
        if not project_name or not next_step:
            st.error("Project Name and Next Step are required!")
        else:
            with st.spinner("Running sequential agents: Capture, Compaction, and Storage..."):
                try:
                    pause_task(project_name, slack_channel_id, next_step)
                    st.success(f"✅ Context saved! Session ID: {SESSION_SERVICE.active_session_key}")
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred during PAUSE. Check terminal logs for details. Error: {e}")

st.markdown("---")

# --- 2. RESUME TASK INTERFACE (Output Display) ---

st.header("▶️ Resume Task")

session_ids = []
SESSION_SERVICE_AVAILABLE = True

# --- Logic to retrieve saved sessions (Long Term Memory) ---
try:
    session_dir_path = SESSION_SERVICE.SESSION_DIR 

    if os.path.isdir(session_dir_path):
        session_files = os.listdir(session_dir_path)
        session_ids = [f.replace('.json', '') for f in session_files if f.endswith('.json')]
    else:
        st.info(f"No '{session_dir_path}' directory found yet. Please pause a task first.")

except Exception as e:
    st.error(f"Error accessing session directory: {e}")
    SESSION_SERVICE_AVAILABLE = False
    session_ids = []
# --- End of retrieval logic ---

options_list = ['Select a Paused Session...'] + session_ids

selected_session_id_with_default = st.selectbox(
    "Select a Paused Session to Resume:",
    options=options_list
)

selected_session_id = None
if selected_session_id_with_default and selected_session_id_with_default != 'Select a Paused Session...':
    selected_session_id = selected_session_id_with_default


if selected_session_id:
    # Get the context from the FileSessionService
    context = SESSION_SERVICE.get_session(selected_session_id)
    
    if context:
        st.success(f"Context Retrieved for: **{context['project_name']}**")
        
        # Display the Snapshot
        st.markdown("### 📸 Contextual Recall Snapshot")
        st.markdown(f"**Paused On:** {context['timestamp'].split('T')[0]}")
        
        # Use st.warning for visual emphasis on the action item
        st.warning(f"🎯 **IMMEDIATE NEXT STEP:** {context['user_next_step']}")
        
        st.markdown("---")
        
        # Displaying the LLM's summary of active resources prominently
        st.markdown("#### 🖥️ Workspace Environment (Files & Tabs)")
        st.markdown(context['compacted_summary']) 
    else:
        st.error(f"Error: Session ID {selected_session_id} not found on disk.")