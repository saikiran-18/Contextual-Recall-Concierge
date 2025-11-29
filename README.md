

# 📄 Contextual Recall Concierge Agent

## 🚀 Project Summary

The **Contextual Recall Concierge Agent** is an AI-powered solution designed to eliminate the cognitive load of **context switching** for knowledge workers. By automating the capture and synthesis of a user's complete work state upon a "pause" command, the agent creates a **Long Term Memory snapshot** that allows for instant task resumption, saving significant time and improving focus.

## 🏗️ Final Architecture: The Four-Agent Pipeline

The core of the system is a **Sequential Agents** workflow, executing a strict four-step pipeline to transform raw activity data into a persistent, actionable summary.

| \# | Agent Name | Role & Core Action | Output/Function |
| :---: | :--- | :--- | :--- |
| **1** | **Activity\_Tracker** | Capture the complete work state (**Custom Tools**) and perform **Context Engineering** (filtering noise like system windows). | Provides clean raw context (files + filtered Slack history) to the LLM agents. |
| **2** | **Suggestor Agent** | Analyzes the raw context using an **LLM** (**Gemini 2.5 Flash**) to predict the most likely next step when the user is unsure. | LLM Prediction of the next step. |
| **3** | **Context\_Compactor** | Uses the user's chosen "Absolute Next Step" and the raw context to generate the final, structured Markdown summary (**Agent powered by an LLM**). | The final, structured Markdown summary (The Snapshot). |
| **4** | **Memory\_Storer** | Acts as the system's **Long Term Memory** by persisting the final summary to disk (**FileSessionService**). | Saves the final summary to disk in the `/sessions` directory. |

## 🛠️ Core AI/Agent Concepts Implemented

| Concept | Implementation in the Concierge Agent |
| :--- | :--- |
| **Sequential Agents** | The entire workflow is a strict pipeline: Activity\_Tracker $\rightarrow$ Suggestor Agent $\rightarrow$ Context\_Compactor $\rightarrow$ Memory\_Storer. |
| **Agent powered by an LLM** | Both the **Suggestor Agent** (Prediction) and **Context Compactor** (Synthesis) are dedicated agents powered by **Gemini 2.5 Flash**. |
| **Custom Tools** | Implemented within the Activity\_Tracker: `get_active_windows()` (OS interaction) and `fetch_recent_slack_msgs()` (communication API). |
| **Context Engineering** | Input filtering within the **Activity\_Tracker** removes low-value noise (e.g., Slack "user joined" messages) before LLM summarization. |
| **Long Term Memory** | Upgraded to the **FileSessionService**, which saves the compacted context as a JSON file, ensuring task state persistence. |
| **Observability** | Structured logging (Python's logging module) records every agent step with a timestamp and status, creating an audit trace in `concierge_agent_trace.log`. |

## ⚙️ Setup and Installation Instructions

### Prerequisites

  * **Python 3.10+**
  * **Slack App** (Bot Token and Channel ID)
  * **Gemini API Key**

### Installation Steps

1.  **Clone the Repository (or setup files).**
2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # Windows PowerShell
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:** Create a file named `.env` in the project root:
    ```bash
    # .env
    GEMINI_API_KEY="AIzaSy...YOUR_GEMINI_KEY"
    SLACK_BOT_TOKEN="xoxb-YOUR-SLACK-BOT-TOKEN-HERE"
    ```

### ▶️ How to Run and Test (Streamlit Deployment)

1.  **Start the Streamlit Application:**
    ```bash
    streamlit run streamlit_app.py
    ```
2.  **Test the PAUSE Command:**
      * In the browser UI, click **"💡 Suggest Next Step (Analyze Context)"**.
      * Enter a **Project Name**.
      * Click **"Capture & Pause Task"**. (Observe the terminal print the sequential logs for the 4-step pipeline.)
3.  **Test the RESUME Command:**
      * Select the newly created **session ID** in the dropdown menu.
      * The complete **Contextual Recall Snapshot** (Immediate Next Step, LLM Compaction Summary, and Workspace Environment) will be displayed immediately.

