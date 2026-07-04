# Aether Context Engine (ACE) — System Description & Startup Guide

The Aether Context Engine (ACE) is a stateful orchestration layer for AI travel planning. It solves the stateless limitations of LLMs by preserving persistent user preferences and history, enriching prompts with context, routing to live external APIs via LangChain, and monitoring performance metrics on an admin dashboard.

---

## 🏗️ System Architecture

ACE is structured as a two-pass orchestrator:

```
                  ┌─────────────────────────┐
                  │   React Web Frontend    │
                  └────────────┬────────────┘
                               │ (JSON API)
                               ▼
                  ┌─────────────────────────┐
                  │     FastAPI Backend     │
                  └──────┬────────────▲─────┘
                         │            │
             ┌───────────▼───┐    ┌───┴───────────┐
             │ SQLite/Supabase│    │ LangChain/    │
             │ Context Memory│    │ Gemini 2.5    │
             └───────────────┘    └──────┬────────┘
                                         │
                                   ┌─────▼────────┐
                                   │  Live APIs   │
                                   │ (Weather,    │
                                   │ Currency,    │
                                   │ Places)      │
                                   └──────────────┘
```

1. **User Request Reception:** The user submits a trip request.
2. **Context & History Retrieval:** The backend fetches user preferences and historical sessions from SQLite/Supabase.
3. **Pass 1 (Intent & Routing):** Gemini reads the request, decides which external tools are needed (Weather, Places, Currency conversion), and LangChain executes them.
4. **Pass 2 (Synthesize Itinerary):** The backend merges the retrieved context, live tool outputs, and user preferences into a final prompt. Gemini generates a structured JSON plan containing the itinerary, budget breakdown, hotels, and travel tips.
5. **Preference Extraction & Metrics Logging:** In the background, user preferences are parsed and updated. Response latency, workflow completion, budget variance, and preference accuracy metrics are logged.

---

## 🚀 How to Start the System

### Prerequisites
- Python 3.11+
- Node.js & npm
- [Google Gemini API Key](https://aistudio.google.com/)

---

### Step 1: Backend Setup
1. Open a terminal in the `backend` folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   Add your `GEMINI_API_KEY` (and optionally `SUPABASE_URL`/`SUPABASE_KEY` if you are not using local SQLite).
5. Start the FastAPI server:
   ```bash
   python -m uvicorn main:app --reload
   ```
   The backend will run at `http://127.0.0.1:8000`.

---

### Step 2: Frontend Setup
1. Open a terminal in the `frontend` folder:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure the backend URL in a `.env` file (copied from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Verify it points to:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
4. Run the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will run at `http://localhost:5173`.

---

### Step 3: Running via Docker (Optional)
If you prefer running the backend containerized:
1. Build the Docker image from the `backend` folder:
   ```bash
   docker build -t ace-backend .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env ace-backend
   ```
