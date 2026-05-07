
---

# 🌍 EcoBattle: Agentic Earth Defense System

**EcoBattle** is a stateful, AI-powered sustainability engine that transforms real-world environmental actions into a gamified "Earth Defense" experience. Unlike simple trackers, EcoBattle uses an **Agentic Workflow** to verify data, calculate carbon impact using standardized metrics, and generate dynamic, non-linear narratives.



---

##  Key Engineering Features

* **Agentic Orchestration (LangGraph):** Employs a directed acyclic graph (DAG) to manage stateful AI transitions between data extraction, verification, and narrative generation.
* **Multi-Tiered Verification:** Combines a deterministic **Carbon Engine** (standardized emission factors) with a probabilistic **LLM Fallback** to ensure data integrity.
* **High Availability Logic:** Built-in regex-based extraction fallbacks to maintain system functionality during API rate-limiting or outages.
* **Dynamic Narrative Scaling:** A "Game Master" LLM node that analyzes user history to invent unique titles and adaptive difficulty challenges.

---

##  Tech Stack & Dependencies

| Tool | Purpose | Why? |
| :--- | :--- | :--- |
| **FastAPI** | Backend Framework | High-performance, asynchronous REST API with automatic Pydantic validation. |
| **LangGraph** | Agentic Logic | Manages the "State" of the AI conversation, allowing for complex, branching decision loops. |
| **LangChain** | AI Pipeline | Provides a structured framework for prompt templating and JSON output parsing. |
| **Gemini 1.5 Flash** | Core LLM | Fast, cost-effective multimodal model used for reasoning and creative generation. |
| **Streamlit** | Frontend UI | Rapid prototyping for a clean, data-focused user dashboard in pure Python. |
| **Pydantic** | Data Integrity | Ensures that LLM outputs strictly follow the schema required by the backend. |

---

##  System Workflow

The application follows a sophisticated 4-step processing loop:

1.  **Extraction Node:** The LLM extracts the `action`, `quantity`, and `category` from raw user text.
2.  **Verification Node:** The system cross-references the category against the **Carbon Engine**. If found, it uses verified emission factors; if not, the AI reasons an estimate.
3.  **Generation Node:** The Game Master updates the `Earth Health`, calculates the new `Level`, and generates two branching mission choices (The Sprint vs. The Marathon).
4.  **Persistence:** The state is updated in the global `user_db`, reflecting real-time changes in the UI.



---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/CH4RUU/ecobattle.git
cd ecobattle
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```text
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
You will need two terminal windows:

**Terminal 1 (Backend):**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
streamlit run app.py
```

---

## 📸 Visual Documentation

### Swagger UI (Backend API)
The backend provides a fully documented interactive API. Explore every endpoint, schema, and response model at `http://127.0.0.1:8000/docs`.
<img width="1600" height="822" alt="PHOTO-2026-05-03-13-14-55" src="https://github.com/user-attachments/assets/b0dd2376-2438-4a72-ae21-bb2bb826b743" />

<img width="1600" height="1040" alt="PHOTO-2026-05-03-14-58-36" src="https://github.com/user-attachments/assets/f0215d9e-be58-412d-abbe-282bc7458c3a" />

### EcoBattle Dashboard (Frontend)
A real-time dashboard featuring dynamic health bars, CO2 telemetry, and AI-generated level titles.
<img width="1600" height="765" alt="PHOTO-2026-05-07-15-31-39" src="https://github.com/user-attachments/assets/25b0be8f-0a91-4432-be57-482a46240fa9" />
<img width="1600" height="1040" alt="PHOTO-2026-05-03-19-28-03" src="https://github.com/user-attachments/assets/65cdaa89-aadf-4771-88c3-728cef0df24b" />


---

## 📈 Future Roadmap
- [ ] **Vision Integration:** Use Gemini Vision to verify actions via photo uploads.
- [ ] **SQL Persistence:** Replace in-memory dictionary with a PostgreSQL database.
- [ ] **Global Leaderboards:** Competitive "EcoWarrior" rankings.

---
**Developed by [Charu Jagguka](https://github.com/CH4RUU)** *Building the future of Agentic AI and Sustainability.*
