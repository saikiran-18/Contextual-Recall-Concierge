# 📄 Contextual Recall Concierge Agent

## 🚀 Project Overview

The **Contextual Recall Concierge** is an AI-powered agent designed under the **Concierge Agents** track (Track A) to automate and optimize the high-friction task of **context switching** for knowledge workers.

Upon receiving a "pause" command, the agent automatically captures the user's complete work state (open files, active browser tabs, recent team communication) and synthesizes it into a single, concise summary using an LLM. This **Long Term Memory** snapshot allows the user to resume complex tasks instantly, eliminating the cognitive load and time wasted on re-orientation. 

---

## 🛠️ Project Requirements and Concepts Implemented

This project successfully integrates six key concepts from the course, verified via the observability trace log (`concierge_agent_trace.log`):

| Concept | Implementation in the Concierge Agent |
| :--- | :--- |
| **Sequential Agents** | The core workflow follows a strict, three-step pipeline: **`Activity_Tracker`** $\rightarrow$ **`Context_Compactor`** $\rightarrow$ **`Memory_Storer`**. |
| **Agent powered by an LLM** | The **`Context_Compactor`** uses the **Gemini 2.5 Flash** model to analyze raw system and communication data and synthesize a final summary. |
| **Custom Tools** | Two tools were created and integrated into the **`Activity_Tracker`** agent: `get_active_windows()` (OS interaction) and `fetch_recent_slack_msgs()` (communication API). |
| **Context Engineering** | Input filtering is implemented within the **`Activity_Tracker`** to remove low-value noise (e.g., system windows, Slack "user joined" messages) before sending the data to the LLM, improving summarization quality. |
| **Long Term Memory** | The volatile `InMemorySessionService` was upgraded to the **`FileSessionService`**, which saves the compacted context as a JSON file in the `/sessions` directory, ensuring task state **persistence**. |
| **Observability** | Structured logging is used via Python's `logging` module. Every agent step is recorded with a timestamp and status level, creating an audit **trace** in the console and the `concierge_agent_trace.log` file. |

---

## ⚙️ Setup and Installation

### Prerequisites

1.  **Python 3.10+**
2.  **Slack App:** A Slack Bot Token (`xoxb-***`) for a Slack App that has been installed to your workspace and invited to the target channel.
3.  **Gemini API Key:** A valid API key from Google AI Studio.

### Installation Steps

1.  **Clone the Repository (or setup the files):** Ensure all project files (`main.py`, `/tools`, etc.) are in the `/Contextual_Concierge` directory.

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # Windows PowerShell
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    

4.  **Configure Environment Variables:** Create a file named `.env` in the project root and add your sensitive credentials:
    ```env
    # .env
    GEMINI_API_KEY="AIzaSy...YOUR_GEMINI_KEY"
    SLACK_BOT_TOKEN="xoxb-YOUR-SLACK-BOT-TOKEN-HERE"
    ```

---

## ▶️ How to Run and Test

### 1. Update Configuration

Before running, ensure you set the correct Slack channel ID in `main.py`:

* Open **`main.py`**.
* Locate the `if __name__ == '__main__':` block.
* Replace the placeholder channel ID with your valid Slack channel ID.

### 2. Run the Agent Pipeline

Execute the main script from the project root:

```bash
python main.py