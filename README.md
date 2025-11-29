📄 Contextual Recall Concierge Agent
🚀 Project Overview
The Contextual Recall Concierge is an AI-powered agent designed under the Concierge Agents track to automate and optimize the high-friction task of context switching for knowledge workers.
The agent is deployed via a Streamlit UI, providing interactive forms for capturing user intent and displaying the synthesis of complex data.
Upon receiving a "pause" command, the agent automatically captures the user's complete work state (open files, active browser tabs, recent team communication) and synthesizes it into a single, concise summary using an LLM. This Long Term Memory snapshot allows the user to resume complex tasks instantly, eliminating the cognitive load and time wasted on re-orientation.
🛠️ Project Requirements and Concepts Implemented
This project successfully integrates six core concepts:
|
| Concept | Implementation in the Concierge Agent |
| Sequential Agents | The core workflow follows a strict, four-step pipeline: Activity_Tracker $\rightarrow$ Suggestor Agent (Prediction) $\rightarrow$ Context_Compactor $\rightarrow$ Memory_Storer. |
| Agent powered by an LLM | Two dedicated LLM agents are used: Context Compactor (for synthesis) and the Suggestor Agent (for prediction), both powered by Gemini 2.5 Flash. |
| Custom Tools | Two tools were created and integrated into the Activity_Tracker: get_active_windows() (OS interaction) and fetch_recent_slack_msgs() (communication API). |
| Context Engineering | Input filtering is implemented within the Activity_Tracker to remove low-value noise (e.g., system windows, Slack "user joined" messages) before sending the data to the LLM, improving summarization quality. |
| Long Term Memory | The InMemorySessionService was upgraded to the FileSessionService, which saves the compacted context as a JSON file in the /sessions directory, ensuring task state persistence. |
| Observability | Structured logging is used via Python's logging module. Every agent step is recorded with a timestamp and status level, creating an audit trace in the console and the concierge_agent_trace.log file. |
🏗️ Final Architecture (The Four-Agent Pipeline)
| Agent Name | Role & Core Action | Output/Function |
| 1. Activity_Tracker | Capture & Filter | Provides clean raw context (files + filtered Slack history) to the LLM agents. |
| 2. Suggestor Agent | Prediction | Uses the LLM to analyze the raw context to predict the most likely next step when the user is unsure (LLM Prediction). |
| 3. Context_Compactor | Synthesis | Uses the user's chosen "Absolute Next Step" and the raw context to generate the final, structured Markdown summary. |
| 4. Memory_Storer | Persistence | Saves the final summary to disk, acting as the system's Long Term Memory. |
⚙️ Setup and Installation
Prerequisites
Python 3.10+
Slack App (Bot Token and Channel ID).
Gemini API Key.
Installation Steps
Clone the Repository (or setup the files).
Create and Activate Virtual Environment:
python -m venv venv
.\venv\Scripts\activate   # Windows PowerShell



Install Dependencies:
pip install -r requirements.txt



Configure Environment Variables: Create a file named .env in the project root and add your sensitive credentials:
# .env
GEMINI_API_KEY="AIzaSy...YOUR_GEMINI_KEY"
SLACK_BOT_TOKEN="xoxb-YOUR-SLACK-BOT-TOKEN-HERE"



▶️ How to Run and Test (Streamlit Deployment)
The agent is run via the Streamlit web server.
Start the Streamlit Application:
streamlit run streamlit_app.py



Test the PAUSE Command:
In the browser UI, click the "💡 Suggest Next Step (Analyze Context)" button. Observe the LLM prediction populate the text field.
Enter a Project Name.
Click "Capture & Pause Task". The agent executes the 4-step pipeline, and the terminal prints the sequential logs (Observability).
Test the RESUME Command:
Select the newly created session ID in the dropdown menu.
The complete Contextual Recall Snapshot (Immediate Next Step, LLM Compaction Summary, and Workspace Environment) will be displayed immediately.
