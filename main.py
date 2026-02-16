import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import List, Dict, Any
import logging
import ollama  # Replaced google.genai with ollama

# --- Logging Setup ---
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

# Load environment variables (Still used for Slack)
load_dotenv()
import os

# Force find the .env file in the current directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
if not SLACK_TOKEN:
    logger.error("🛑 CRITICAL: SLACK_BOT_TOKEN is still missing after load_dotenv!")

# LOCAL MODEL CONFIGURATION
# Using gemma:2b or gemma3:1b for CPU-only performance
LOCAL_MODEL = "gemma:2b" 

def clean_raw_context(raw_context: dict) -> dict:
    # 1. Clean Active Windows safely
    cleaned_windows = [
        str(title) for title in raw_context.get('active_windows', [])
        if isinstance(title, str) and not any(kw in title for kw in ["PopupHost", "File Explorer"])
    ]
    sensitive_keywords = ["TOKEN", "PASSWORD", ".ENV", "SECRET", "KEY"]
    
    cleaned_windows = [
        title for title in raw_context.get('active_windows', [])
        if not any(word in title.upper() for word in sensitive_keywords)
        and not any(kw in title for kw in ["PopupHost", "File Explorer"])
    ]
    # 2. Clean Slack Messages safely (The 'text' fix)
    raw_slack = raw_context.get('slack_messages', [])
    cleaned_slack_messages = []
    
    if isinstance(raw_slack, list):
        for msg in raw_slack:
            # SAFETY: Check if it's a dict and has 'text' before accessing
            if isinstance(msg, dict) and 'text' in msg:
                text_content = msg.get('text', '')
                if "has joined" not in text_content and "has left" not in text_content:
                    cleaned_slack_messages.append(msg)
    
    raw_context['active_windows'] = cleaned_windows
    raw_context['slack_messages'] = cleaned_slack_messages
    return raw_context

# --- FileSessionService Setup ---
SESSION_DIR_GLOBAL = "sessions"
os.makedirs(SESSION_DIR_GLOBAL, exist_ok=True) 

class FileSessionService:
    """Handles persistent storage and retrieval of paused task context."""
    
    SESSION_DIR = "sessions" 
    
    def __init__(self):
        # We only store the ID to keep RAM usage low on 8GB/16GB setups
        self.active_session_key: str | None = None

    def _get_file_path(self, session_id: str) -> str:
        """Helper to locate the session file on disk."""
        return os.path.join(self.SESSION_DIR, f"{session_id}.json")

    def create_session(self, project_name: str, context_data: dict) -> str:
        """Saves context and immediately clears heavy data from RAM."""
        session_id = f"{project_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        file_path = self._get_file_path(session_id)
        
        with open(file_path, 'w') as f:
            json.dump(context_data, f, indent=4)
            
        self.active_session_key = session_id
        return session_id
    
    def get_session(self, session_id: str) -> dict | None:
        """Retrieves context from Long Term Memory (Disk)."""
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None

SESSION_SERVICE = FileSessionService()

# --- NEW: Helper for Local CPU-Efficient Prompting ---
# --- Updated call_ollama in main.py ---
def call_ollama(system_instruction: str, user_prompt: str) -> str:
    try:
        logger.info(f"Invoking Ollama ({LOCAL_MODEL})...")
        response = ollama.generate(
            model=LOCAL_MODEL,
            system=system_instruction,
            prompt=user_prompt,
            # CHENNAI LAPTOP OPTIMIZATIONS
            options={
                'num_thread': 4,    # Limits CPU usage so you can still use VS Code
                'num_predict': 200, # Prevents the 'cut off' error you saw earlier
                'num_ctx': 1024,    # Memory window for 5 messages + window titles
                'temperature': 0.1  # Keeps the response focused and predictable
            }
        )
        # Accessing content safely to avoid 'text' key error
        return response.get('response', '').strip()
    except Exception as e:
        logger.error(f"Ollama Error: {e}")
        return f"Error: Local model failed. {str(e)}"
# --- Context Compactor (Ollama Version) ---
def call_llm_for_compaction(raw_context: dict, next_step_prompt: str) -> str:
    system_instruction = (
        "You are an AI Concierge. Format the output with bold headers and emojis. "
        "List every open app and tab neatly. Summarize Slack messages into an 'Important' section."
    )
    
    # Formatting lists for the model
    windows_list = "\n".join([f"  🔹 {title}" for title in raw_context.get('active_windows', [])])
    slack_list = "\n".join([f"  💬 {m.get('text', '')}" for m in raw_context.get('slack_messages', [])])
    
    user_prompt = (
        f"### 🧠 Recall Snapshot: {raw_context['project_name']}\n"
        f"**🎯 IMMEDIATE NEXT STEP:** {next_step_prompt}\n\n"
        "**🖥️ OPEN APPLICATIONS & TABS:**\n"
        f"{windows_list}\n\n"
        "**📢 IMPORTANT MESSAGES (SLACK):**\n"
        f"{slack_list}\n\n"
        "**⚠️ CRITICAL BLOCKS:** [List any technical hurdles here]"
    )

    return call_ollama(system_instruction, user_prompt)
       
# --- Suggestor Agent (Ollama Version) ---
def call_llm_for_suggestion(raw_context: dict) -> str:
    # Use a very strict system instruction
    system_instruction = "You are a direct assistant. Output ONLY the next action. No labels. No JSON. No quotes."
    
    windows_str = ", ".join(raw_context['active_windows'])
    slack_str = "\n".join([f"- {m['text']}" for m in raw_context['slack_messages']])

    user_prompt = f"Context:\nWindows: {windows_str}\nSlack: {slack_str}\n\nImmediate next step suggestion:"

    return call_ollama(system_instruction, user_prompt)

# --- Sequential Agents (Unchanged logic, different backend) ---

def Activity_Tracker(project_name: str, slack_channel_id: str) -> dict:
    logger.info(f"[Activity_Tracker] Capturing data...")
    
    # Capture raw data
    raw_slack = fetch_recent_slack_msgs(slack_channel_id, count=5)
    
    # VALIDATION: If the first item is an error, clear the list
    if raw_slack and isinstance(raw_slack[0], dict) and 'error' in raw_slack[0]:
        logger.warning(f"Slack Error detected: {raw_slack[0]['error']}")
        raw_slack = [] # Send an empty list instead of the error dict
    
    raw_context = {
        "project_name": project_name,
        "active_windows": get_active_windows()[:5],
        "slack_messages": raw_slack
    }
    
    return clean_raw_context(raw_context)

def Context_Compactor(raw_context: dict, next_step_prompt: str) -> dict:
    logger.info("[Context_Compactor] Generating summary locally...")
    compacted_summary = call_llm_for_compaction(raw_context, next_step_prompt)
    return {
        "project_name": raw_context['project_name'],
        "timestamp": datetime.now().isoformat(),
        "user_next_step": next_step_prompt,
        "compacted_summary": compacted_summary,
    }

def Memory_Storer(final_context: dict) -> str:
    logger.info("[Memory_Storer] Saving to disk...")
    return SESSION_SERVICE.create_session(final_context['project_name'], final_context)

def suggest_next_step(slack_channel_id: str) -> str:
    raw_context = Activity_Tracker("Suggestion Task", slack_channel_id)
    return call_llm_for_suggestion(raw_context)

def pause_task(project_name: str, slack_channel_id: str, next_step_prompt: str):
    raw_context = Activity_Tracker(project_name, slack_channel_id)
    final_context = Context_Compactor(raw_context, next_step_prompt)
    session_id = Memory_Storer(final_context)
    print(f"\n✅ TASK PAUSED. Session: {session_id}")

def resume_task(session_id: str):
    retrieved_context = SESSION_SERVICE.get_session(session_id)
    if retrieved_context:
        print(f"\n--- RESUME: {retrieved_context['project_name']} ---")
        print(f"🎯 NEXT: {retrieved_context['user_next_step']}")
        print(f"Summary: {retrieved_context['compacted_summary']}")

if __name__ == '__main__':
    # Test call
    pause_task("Local-Test", "C09U8ART7QT", "Verify Ollama connectivity")