


# 🧠 Contextual Recall Concierge (Local Edition)

## 🚀 Project Summary

The **Contextual Recall Concierge Agent** is a local-first AI solution designed to eliminate the cognitive load of **context switching** for knowledge workers. By automating the capture and synthesis of a user's complete work state (Active Windows + Slack history) upon a "pause" command, the agent creates a **Long-Term Memory snapshot**. This allows for instant task resumption, saving time and maintaining focus.

Originally cloud-dependent, this version has been optimized for **local CPU execution** using Ollama, ensuring 100% data privacy and zero API costs.

## 🏗️ Final Architecture: The Sequential Agent Pipeline

The system utilizes a **Sequential Agents** workflow, executing a strict four-step pipeline to transform raw activity data into a persistent, actionable summary.

| # | Agent Name | Role & Core Action | Output/Function |
| --- | --- | --- | --- |
| **1** | **Activity_Tracker** | Captures OS window titles and Slack history. Performs **Security Scrubbing** to remove sensitive tokens. | Provides clean raw context (files + filtered Slack history) to the LLM. |
| **2** | **Suggestor Agent** | Analyzes the raw context using **Ollama (Gemma 3)** to predict the most likely next step. | AI-generated prediction of the next step. |
| **3** | **Context_Compactor** | Synthesizes the chosen "Absolute Next Step" and raw data into a structured Markdown summary with emojis. | The final, structured **Recall Snapshot**. |
| **4** | **Memory_Storer** | Acts as the system's **Long Term Memory** by persisting the summary to disk as a versioned JSON file. | Saves data to the `/sessions` directory. |

## 🛠️ Local CPU Optimization & Security

| Concept | Implementation in the Concierge Agent | Benefit |
| --- | --- | --- |
| **Local LLM** | Powered by **Ollama (Gemma 3:1b/2b)**. | 100% private; runs entirely on local hardware. |
| **Resource Control** | Configured with `num_thread: 4`. | Prevents system freezing/overheating on laptops. |
| **Data Pruning** | Captures Top 5 Windows + 5 Slack Messages. | Reduces "Token Load" for faster inference on CPUs. |
| **Security Scrub** | Sensitive Keyword Filtering (Tokens/Secrets). | Automatically hides sensitive strings from the snapshot. |
| **Observability** | Structured logging in `concierge_agent_trace.log`. | Records every agent step for audit and debugging. |

## ⚙️ Setup and Installation Instructions

### Prerequisites

* **Python 3.10+**
* **Ollama Desktop** (Download from [ollama.com](https://ollama.com))
* **Slack App** (Bot Token and Channel ID)

### Installation Steps

1. **Model Setup:**
```bash
ollama pull gemma3:1b

```


2. **Virtual Environment:**
```bash
python -m venv venv
.\venv\Scripts\activate   # Windows PowerShell

```


3. **Install Dependencies:**
```bash
pip install ollama streamlit python-dotenv PyGetWindow slack_sdk

```


4. **Configure Environment:** Create a `.env` file in the project root:
```bash
# .env
SLACK_BOT_TOKEN="xoxb-YOUR-SLACK-BOT-TOKEN-HERE"

```



## ▶️ How to Run and Test

### 1. Set CPU Guardrails

To ensure stability on a standard laptop, set these environment variables in your terminal:

```powershell
$env:OLLAMA_NUM_PARALLEL=1
$env:OLLAMA_MAX_LOADED_MODELS=1
$env:OMP_NUM_THREADS=4

```

### 2. Launch the Application

```bash
streamlit run streamlit_app.py

```

### 3. Usage Workflow

* **PAUSE:** Click **"💡 Suggest Next Step"** to let the agent analyze your context. Enter a Project Name and click **"Capture & Pause Task"**.
* **RESUME:** Select your **session ID** from the dropdown. The UI will display your **Contextual Recall Snapshot** (Immediate Next Step, Categorized Slack Messages, and Workspace Environment) with full emoji formatting.



