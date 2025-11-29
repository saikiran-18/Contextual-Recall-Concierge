import pygetwindow as gw
from typing import List, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os

load_dotenv()
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CLIENT = WebClient(token=SLACK_TOKEN)

def get_active_windows() -> List[str]:
    """
    Captures the titles of all active, non-minimized windows on the user's desktop.
    This provides the agent with context about what files/tabs the user is working on.
    """
    try:
        all_windows = gw.getAllWindows()
        
        window_titles = []
        
        irrelevant_keywords = ["Program Manager", "Desktop", "Taskbar", "Settings", "Cortana", "Search", "Start", "Running applications", "Windows Security", "Calculator"]

        for window in all_windows:
            title = window.title.strip()
            
            if not title or len(title) < 3:
                continue
                
            if any(keyword in title for keyword in irrelevant_keywords):
                continue
            
            if title in window_titles:
                continue

            window_titles.append(title)
            
        return window_titles
    
    except Exception as e:
        print(f"Error capturing windows: {e}")
        return [f"ERROR: Could not capture windows. Detail: {str(e)}"]


def fetch_recent_slack_msgs(channel_id: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches the most recent messages from a specified project communication channel.
    
    Args:
        channel_id: The ID of the Slack channel (e.g., 'C12345678').
        count: The number of recent messages to fetch.
        
    Returns:
        A list of dictionaries, each containing the sender and text of a message.
    """
    if not SLACK_TOKEN:
        return [{"error": "SLACK_BOT_TOKEN not found in .env file."}]

    try:
        result = SLACK_CLIENT.conversations_history(
            channel=channel_id,
            limit=count
        )
        
        messages_context = []
        for message in result['messages']:
            if 'text' in message and 'user' in message:
                messages_context.append({
                    "user_id": message['user'],
                    "text": message['text'],
                    "ts": message['ts']
                })
        
        return messages_context
    
    except SlackApiError as e:
        print(f"Slack API Error: {e.response['error']}")
        return [{"error": f"Slack API Error: {e.response['error']}"}]
    except Exception as e:
        print(f"General Slack Error: {e}")
        return [{"error": f"General Slack Error: {str(e)}"}]
    

if __name__ == '__main__':
    print("--- Running Window Capture Test ---")
    active_titles = get_active_windows()
    print(f"Captured {len(active_titles)} active window(s):")
    for title in active_titles:
        print(f"- {title}")
    print("-----------------------------------")
    
    print("\n--- Running Slack Context Test ---")
    
    TEST_CHANNEL_ID = "CHANNEL_ID" 
    
    if TEST_CHANNEL_ID == "C06R7M4XXXX":
        print("Test skipped.")
    else:
        slack_msgs = fetch_recent_slack_msgs(channel_id=TEST_CHANNEL_ID, count=3)
        print(f"Captured {len(slack_msgs)} recent Slack message(s) from channel {TEST_CHANNEL_ID}:")
        for msg in slack_msgs:
            print(f"- [User {msg.get('user_id', 'N/A')}] {msg.get('text', 'No text')[:50]}...")

        print("----------------------------------")
