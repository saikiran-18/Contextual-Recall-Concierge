import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import List, Dict, Any
import logging

log_file_name = "concierge_agent_trace.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_name, mode='a', encoding='utf-8'), 
        logging.StreamHandler() 
    ]
)
logger = logging.getLogger('AGENT_FLOW')

# Import custom tools
from tools.system_tools import get_active_windows, fetch_recent_slack_msgs

# Import the Google GenAI SDK
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the Gemini Client
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        LLM_MODEL = 'gemini-2.5-flash'
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        client = None
else:
    print("Warning: GEMINI_API_KEY not found. Using placeholder LLM function.")
    client = None

def clean_raw_context(raw_context: dict) -> dict:
    """
    Filters and cleans the raw data before sending it to the LLM.
    - Filters system windows.
    - Filters join messages from Slack.
    """
    
    # 1. Clean Active Windows
    irrelevant_desktop_titles = ["Windows Input Experience", "PopupHost", "File Explorer"]
    
    cleaned_windows = [
        title for title in raw_context.get('active_windows', [])
        if not any(keyword in title for keyword in irrelevant_desktop_titles)
    ]
    
    # 2. Clean Slack Messages
    cleaned_slack_messages = [
        msg for msg in raw_context.get('slack_messages', [])
        if "has joined the channel" not in msg.get('text', '') and 
           "has left the channel" not in msg.get('text', '')
    ]
    
    # Update the raw context with the filtered lists
    raw_context['active_windows'] = cleaned_windows
    raw_context['slack_messages'] = cleaned_slack_messages
    
    return raw_context

# --- FileSessionService Setup ---
SESSION_DIR_GLOBAL = "sessions"
os.makedirs(SESSION_DIR_GLOBAL, exist_ok=True) 

class FileSessionService:
    """Handles persistent storage and retrieval of paused task context using JSON files."""
    
    SESSION_DIR = SESSION_DIR_GLOBAL 
    
    def __init__(self):
        self.active_session_key: str | None = None

    def _get_file_path(self, session_id: str) -> str:
        """Returns the full path to the session file."""
        return os.path.join(FileSessionService.SESSION_DIR, f"{session_id}.json")

    def create_session(self, project_name: str, context_data: dict) -> str:
        """Saves the final, compacted context to a file."""
        session_id = f"{project_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        file_path = self._get_file_path(session_id)
        
        with open(file_path, 'w') as f:
            json.dump(context_data, f, indent=4)
            
        self.active_session_key = session_id
        return session_id
    
    def get_session(self, session_id: str) -> dict | None:
        """Retrieves context from a file (Long Term Memory)."""
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None

# Initialize the Session Service
SESSION_SERVICE = FileSessionService()

# --- LLM Integration Function ---
def call_llm_for_compaction(raw_context: dict, next_step_prompt: str) -> str:
    """
    Sends the raw context to the Gemini LLM for summarization (Context Compaction).
    """
    if not client:
        # Fallback to the old stub if the API key is missing
        return f"## Context Compaction Summary (FALLBACK - LLM Disabled)\nYour saved next step: {next_step_prompt}"
        
    print("\n[LLM-Agent] Calling Gemini to summarize and compact context...")
    
    # 1. Define the System Instruction (Context Engineering Prompt)
    system_instruction = (
        "You are the 'Context Compactor' agent. Your task is to analyze the provided raw JSON data "
        "representing a user's paused work state. You must generate a concise, action-oriented "
        "Markdown summary that focuses ONLY on the most relevant active windows/files and "
        "synthesizes the key discussion points from the Slack messages. "
        "The goal is to eliminate cognitive load when the user resumes the task."
    )
    
    # 2. Define the User Prompt
    user_prompt = (
        f"The user has paused the task: {raw_context['project_name']}\n"
        f"The user's ABSOLUTE NEXT STEP is: '{next_step_prompt}'\n\n"
        "Here is the raw context data captured from their system and communication tools:\n"
        "--- RAW CONTEXT ---\n"
        f"{json.dumps(raw_context, indent=2)}\n"
        "-------------------\n\n"
        "Please provide the final summary in a single Markdown block."
    )

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1 
            )
        )
        return response.text
    
    except Exception as e:
        print(f"Gemini API Error during compaction: {e}")
        return f"## Context Compaction Summary (API FAILURE)\nCould not reach the LLM. Error: {str(e)}"

def call_llm_for_suggestion(raw_context: dict) -> str:
    """
    Sends the raw context to the Gemini LLM for generating the most logical next step.
    This simulates a specialized Suggestor Agent.
    """
    if not client:
        return "ERROR: LLM not available for suggestion. Please type the next step manually."
        
    logger.info("[Suggestor-Agent] Calling Gemini to generate next step...")
    
    # 1. Define the System Instruction (Suggestor Prompt)
    system_instruction = (
        "You are the 'Next Step Suggestor' agent. Analyze the provided context, focusing on "
        "active windows and recent communication snippets. Your single output must be the "
        "most logical, high-priority next action item for the user to resume their work. "
        "DO NOT use Markdown formatting; provide only the suggested sentence."
    )
    
    # 2. Define the User Prompt (Sends ALL the captured data)
    user_prompt = (
        "Here is the user's paused context:\n"
        "--- RAW CONTEXT ---\n"
        f"{json.dumps(raw_context, indent=2)}\n"
        "-------------------\n\n"
        "Generate a single, direct, actionable sentence for the user's 'Absolute Next Step'."
    )

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3 
            )
        )
        return response.text.strip()
    
    except Exception as e:
        logger.error(f"Gemini API Error during suggestion: {e}")
        return f"ERROR: Could not generate suggestion ({str(e)}). Please type the step manually."

# --- Sequential Agents ---

# Agent 1: The Activity_Tracker
def Activity_Tracker(project_name: str, slack_channel_id: str) -> dict:
    logger.info(f"[Activity_Tracker] Starting data capture for '{project_name}'...")
    
    # Tool Call A & B: Get raw context
    raw_context = {
        "project_name": project_name,
        "active_windows": get_active_windows(),
        "slack_messages": fetch_recent_slack_msgs(slack_channel_id, count=10)
    }
    
    # Filter the raw data before passing to the LLM
    cleaned_context = clean_raw_context(raw_context)
    
    logger.info(f"[Activity_Tracker] Raw data collected and filtered. Windows: {len(cleaned_context['active_windows'])} | Messages: {len(cleaned_context['slack_messages'])}")
    return cleaned_context

# Agent 2: The Context_Compactor (LLM-Powered Agent)
def Context_Compactor(raw_context: dict, next_step_prompt: str) -> dict:
    logger.info("[Context_Compactor] Starting LLM-powered context compaction...")
    
    # Call the LLM with the raw data
    compacted_summary = call_llm_for_compaction(raw_context, next_step_prompt)
    
    # Combine everything for the final handoff
    final_context = {
        "project_name": raw_context['project_name'],
        "timestamp": datetime.now().isoformat(),
        "user_next_step": next_step_prompt,
        "compacted_summary": compacted_summary,
    }
    
    logger.info("[Context_Compactor] Context successfully compacted.")
    return final_context

# Agent 3: The Memory_Storer (State Management)
def Memory_Storer(final_context: dict) -> str:
    logger.info("[Memory_Storer] Storing session to long-term memory...")
    
    # Handles Sessions & State Management
    session_id = SESSION_SERVICE.create_session(
        final_context['project_name'], 
        final_context
    )
    
    logger.info(f"[Memory_Storer] Session saved successfully: {session_id}")
    return session_id

def suggest_next_step(slack_channel_id: str) -> str:
    """
    Orchestrates the suggestion workflow: captures context and asks LLM for the next step.
    """
    # 1. Capture Raw Context (runs Agent 1: Activity_Tracker)
    raw_context = Activity_Tracker("Suggestion Task", slack_channel_id)
    
    # 2. Call the LLM Suggestor Agent
    suggestion = call_llm_for_suggestion(raw_context)
    
    return suggestion

# --- Orchestration Function (The /pause-task command) ---

def pause_task(project_name: str, slack_channel_id: str, next_step_prompt: str):
    """
    Executes the full sequential agent workflow upon the /pause-task command.
    """
    print("\n==============================================")
    print(f"| PAUSE TASK: {project_name.upper()}")
    print("==============================================")

    # Sequential Flow: Agent 1 -> Agent 2 -> Agent 3 
    raw_context = Activity_Tracker(project_name, slack_channel_id)
    final_context = Context_Compactor(raw_context, next_step_prompt)
    session_id = Memory_Storer(final_context)
    
    # Final Output to User (Printed to console, visible in Streamlit logs)
    print("\n----------------------------------------------")
    print("✅ TASK PAUSED SUCCESSFULLY.")
    print(f"Session ID: {session_id}")
    print("----------------------------------------------")
    print("Context Summary for Resume:")
    print(final_context['compacted_summary'])
    print("----------------------------------------------")

def resume_task(session_id: str):
    """
    Simulates the /resume-task command, retrieving and presenting context 
    from Long Term Memory.
    """
    logger.info(f"\n==============================================")
    logger.info(f"| RESUME TASK: Retrieving Session {session_id}")
    logger.info(f"==============================================")
    
    retrieved_context = SESSION_SERVICE.get_session(session_id)

    if retrieved_context:
        project_name = retrieved_context['project_name']
        next_step = retrieved_context['user_next_step']
        summary = retrieved_context['compacted_summary']
        
        logger.info(f"✅ Context Retrieved for: {project_name}")
        
        print("\n--- YOUR CONTEXTUAL RECALL SNAPSHOT ---")
        print(f"**Project:** {project_name}")
        print(f"**Paused:** {retrieved_context['timestamp'].split('T')[0]}")
        print("\n")
        print(f"🎯 **IMMEDIATE NEXT STEP:** {next_step}")
        print("\n")
        print("### LLM Compaction Summary:")
        print(summary)
        print("---------------------------------------")
    else:
        logger.error(f"Session ID {session_id} not found in Long Term Memory.")
        
# --- Example Usage ---

def run_cli_test():
    """
    Function to test the agent when main.py is run directly from the command line (CLI).
    """
    # --- SIMULATE THE USER COMMAND (PAUSE) ---
    PROJECT_NAME = "Contextual Concierge Core"
    SLACK_CHANNEL = "C09U8ART7QT" 
    NEXT_STEP = "Refactor the main.py LLM call to handle large output sizes and check for memory leaks in the session service."

    # Execute the Pause workflow
    pause_task(PROJECT_NAME, SLACK_CHANNEL, NEXT_STEP)

    # --- SIMULATING THE USER COMMAND (RESUME) ---
    current_session_key = SESSION_SERVICE.active_session_key
    
    if current_session_key:
        # Execute the Resume workflow, retrieving data from disk
        resume_task(current_session_key)
    else:
        logger.error("Could not retrieve active session key to simulate resume.")

if __name__ == '__main__':
    # When gui_app.py imports main.py, this code will be skipped.
    run_cli_test()