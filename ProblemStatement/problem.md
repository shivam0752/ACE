# Aether Context Engine (ACE)
## Automated Infrastructure Orchestration — Full Project Document

---
## PROBLEM STATEMENT

Modern AI assistants and automation tools suffer from a fundamental limitation — **they are stateless**. Every interaction starts from zero. The system has no memory of who you are, what you previously discussed, what your preferences are, or what decisions were made in past sessions.

This creates three real problems in professional and personal workflows:

**Problem 1 — Context Loss**
Every time a user interacts with an AI agent, they must re-explain their situation, preferences, and history. A project manager using an AI tool to plan tasks has to re-input context every single session. This is inefficient and breaks workflow continuity.

**Problem 2 — No Preference Learning**
Existing automation tools treat every user the same. They don't adapt to individual working styles, preferences, or historical patterns. A travel planning tool that doesn't remember you prefer window seats and budget hotels will always feel like starting from scratch.

**Problem 3 — Disconnected Tool Ecosystems**
Most AI agents work in isolation — they can answer questions but cannot take actions across multiple external tools and services simultaneously. A truly useful agent needs to fetch live data, process it with intelligence, remember the outcome, and act across multiple systems in one coherent workflow.

**ACE solves all three problems** by building a stateful AI orchestration layer — a system that maintains persistent user context, learns preferences over time, processes natural language requests using Gemini, fetches live data through MCP servers, and coordinates multi-step actions across tools — all in one coherent pipeline.

The initial use case is **intelligent travel planning** — a domain that requires live data fetching, budget calculation, preference memory, and multi-step decision making — making it an ideal stress test for the architecture. But the underlying engine is designed to be use-case agnostic and extensible to any domain.

---

## WHAT ACE DOES — FUNCTIONAL OVERVIEW

A user opens the ACE interface and types:

> *"Plan a 5-day trip to Manali for 2 people in the first week of August. Budget around ₹30,000. I prefer hills over beaches and I don't like crowded tourist spots."*

ACE then:

1. **Receives** the natural language input via the frontend
2. **Retrieves** the user's stored context and preferences from the database (previous trips, stated preferences, budget patterns)
3. **Constructs** a context-enriched prompt combining the new request + historical preferences
4. **Calls Gemini** to process the request, generate a structured plan, and identify what live data is needed
5. **Fetches live data** through MCP servers — travel sites, weather, location data, pricing
6. **Re-processes** the fetched data through Gemini to generate a final coherent plan with budget breakdown
7. **Stores** the new interaction, preferences stated, and outcome back into the user's context database
8. **Returns** a complete, structured response — itinerary, budget breakdown, accommodation suggestions, travel tips — to the frontend
9. **Updates** the user profile with any new preferences inferred from this interaction

The next time the user asks anything, ACE already knows they prefer hills, hate crowds, and have a moderate budget — without being told again.

---

## TECH STACK

### Frontend
- **React.js** — user interface
- **Tailwind CSS** — styling
- **Axios** — API calls from frontend to backend

### Backend
- **Python (FastAPI)** — main backend framework, handles all API routes, orchestration logic
- **LangChain** — orchestration framework that manages the multi-step Gemini calls, prompt chaining, and tool use
- **Google Gemini API (gemini-1.5-flash or gemini-1.5-pro)** — the language model brain of ACE

### Memory / Context Storage
- **Supabase (PostgreSQL)** — stores user profiles, preference history, past interaction summaries
- **LangChain Memory Module** — manages in-session context passing between dialogue turns

### MCP / Live Data Layer
- **MCP Servers** — for fetching live travel data, locations, pricing
- Alternatively: direct API integrations with travel APIs (Amadeus, Skyscanner, Google Places API) if MCP servers aren't available

### Deployment
- **Railway or Render** — backend deployment (free tier available, simple Python/FastAPI deployment)
- **Vercel** — frontend deployment (free tier, perfect for React)
- **Supabase** — already cloud-hosted, no separate deployment needed

### Version Control
- **GitHub** — code repository, also serves as proof of work for interviews

---

## SYSTEM ARCHITECTURE DIAGRAM (text format)

```
USER (React Frontend)
        ↓
    FastAPI Backend
        ↓
  Context Retrieval (Supabase — fetch user history + preferences)
        ↓
  Prompt Construction (LangChain — merge user input + context)
        ↓
  Gemini API Call 1 — understand intent + identify data needs
        ↓
  MCP Server / Travel API calls — fetch live data
        ↓
  Gemini API Call 2 — synthesize live data + context into final plan
        ↓
  Context Update (Supabase — store new preferences + interaction summary)
        ↓
  Response returned to Frontend
```

---

## 6 EVALUATION METRICS

These are the metrics you establish to measure whether ACE is working correctly — these become your "6 evaluation metrics to ensure system runtime accuracy" from the resume bullet.

| Metric | What it measures | How you measure it |
|---|---|---|
| **1. Workflow Completion Rate** | Percentage of user requests that complete the full pipeline without errors or fallbacks | (Successful completions / Total requests) × 100 — logged in Supabase |
| **2. Preference Retention Accuracy** | Does the system correctly apply stored preferences in subsequent sessions without being re-told | Manual test — run 10 sessions, check if preferences applied correctly in follow-up sessions |
| **3. Budget Calculation Variance** | How close is ACE's budget estimate to actual prices fetched from live APIs | (Estimated budget - Actual fetched price) / Actual price — tracked per session |
| **4. Context Relevance Score** | Does the context retrieved from previous sessions actually improve the quality of the current response | User rating prompt at end of session (1-5) — averaged across sessions |
| **5. API Response Latency** | Total time from user input to final response returned — end to end | Timestamp at input and output, difference logged per request in milliseconds |
| **6. Hallucination Rate** | Percentage of responses where Gemini generates travel details not supported by live fetched data | Manual review of 20 sample outputs — flag responses where itinerary items don't match fetched data |

---

## PHASES

---

### PHASE 1 — Foundation (Day 1-2)
**Goal:** Get the basic pipeline working — input → Gemini → output. No memory yet.

**Tasks:**
- Set up Python FastAPI project structure
- Install dependencies: `fastapi`, `uvicorn`, `langchain`, `google-generativeai`, `python-dotenv`
- Set up `.env` file with Gemini API key
- Create a single `/chat` POST endpoint that:
  - Accepts a user message
  - Sends it to Gemini with a basic system prompt
  - Returns Gemini's response
- Set up React frontend with a simple chat interface
- Connect frontend to backend via Axios

**Deliverable:** A working chat interface where you can send a travel query and get a Gemini response back.

**What to test:** Send "Plan a 3-day trip to Goa for 2 people with ₹20,000 budget" — Gemini should return a coherent plan.

---

### PHASE 2 — Memory Layer (Day 3-4)
**Goal:** Add persistent user context so ACE remembers preferences across sessions.

**Tasks:**
- Set up Supabase project — create two tables:
  - `users` table: `user_id`, `name`, `created_at`
  - `user_context` table: `user_id`, `preference_key`, `preference_value`, `updated_at`
  - `interaction_history` table: `user_id`, `session_id`, `input`, `output`, `timestamp`
- Install Supabase Python client: `supabase-py`
- Add context retrieval function — before every Gemini call, fetch the user's stored preferences from Supabase
- Add context update function — after every response, parse the interaction for new preferences and store them
- Modify the prompt construction to include retrieved context:

```
System: You are ACE, an intelligent travel planning assistant.
User Context: {retrieved_preferences}
Current Request: {user_input}
```

**Deliverable:** Send a query mentioning "I prefer budget accommodation" — end the session. Start a new session and ask for a trip plan without mentioning budget preference — ACE should still recommend budget options.

**What to test:** Preference persistence across 3 separate sessions.

---

### PHASE 3 — Live Data Integration (Day 5-6)
**Goal:** Connect ACE to live data sources so recommendations are based on real prices and availability.

**Tasks:**
- Integrate at least one live data source. Options:
  - **Google Places API** — for location information and recommendations
  - **Open-Meteo API** (free) — for weather data at destination
  - **ExchangeRate API** (free) — for currency if international travel
  - **MCP Travel Servers** if available in your setup
- Build a tool-use layer using LangChain's tool calling:
  - Gemini Call 1: identify what data is needed based on user query
  - API calls: fetch the required live data
  - Gemini Call 2: synthesize live data with context into final response
- Add structured output formatting — return response as JSON with sections: `itinerary`, `budget_breakdown`, `accommodation_suggestions`, `travel_tips`
- Display structured response beautifully in the React frontend

**Deliverable:** A query about Manali in August should return weather data, real location suggestions, and a structured plan — not just Gemini's training knowledge.

---

### PHASE 4 — Evaluation Metrics Dashboard (Day 7)
**Goal:** Implement the 6 evaluation metrics so ACE can measure its own performance.

**Tasks:**
- Add logging to Supabase for every interaction:
  - Timestamp in / timestamp out (latency)
  - Completion status (success / error)
  - Budget estimate vs fetched price (if applicable)
- Build a simple `/metrics` endpoint in FastAPI that returns:
  - Workflow completion rate
  - Average latency
  - Total sessions
- Add a simple metrics display panel in the React frontend
- Manually run the preference retention test (10 sessions) and log results
- Manually review 20 outputs for hallucination rate

**Deliverable:** A metrics dashboard showing live system performance stats.

---

### PHASE 5 — Deployment (Day 8)
**Goal:** Deploy ACE so it has a live URL — this is what makes it a real project you can show.

**Tasks:**
- Push full codebase to GitHub (public repository)
- Deploy backend to Railway:
  - Create `requirements.txt`
  - Create `Procfile`: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
  - Set environment variables (Gemini API key, Supabase URL, Supabase key) in Railway dashboard
- Deploy frontend to Vercel:
  - Connect GitHub repo
  - Set environment variable: `REACT_APP_API_URL` = your Railway backend URL
  - Deploy with one click
- Test full flow on live deployment

**Deliverable:** A live URL for ACE that you can open on your phone and show in an interview.

---

## RESUME BULLET (final version — for your resume)

**Aether Context Engine (ACE) — Automated Infrastructure Orchestration** | Personal Initiative Track

> Engineered a stateful AI orchestration system using Python FastAPI, LangChain, and Google Gemini API to process context-aware travel planning queries with persistent user preference memory across sessions. Integrated live data fetching via MCP servers and Google Places API, establishing 6 evaluation metrics — including workflow completion rate, preference retention accuracy, and hallucination rate — to ensure system runtime accuracy. Deployed full-stack on Railway and Vercel with Supabase as the context persistence layer.

---

## INTERVIEW ANSWER — If Asked About ACE

> "ACE was a personal initiative I built to solve a real problem I noticed with AI tools — they're stateless. Every session starts from scratch. I built an orchestration layer using Python FastAPI as the backend, LangChain to manage the multi-step Gemini calls, and Supabase for persistent context storage. The use case I built it around was travel planning — the system takes a natural language request, retrieves the user's stored preferences, enriches the prompt with that context, fetches live data through MCP servers and Google Places API, and synthesizes everything into a structured itinerary with budget breakdown. The 'stateful' part means the system remembers your preferences across sessions — if you told it once you prefer budget accommodation and hate crowded spots, it applies that to every future request without being re-told. I established 6 evaluation metrics to track system performance — workflow completion rate, preference retention accuracy, budget calculation variance, context relevance score, API latency, and hallucination rate. It's deployed live on Railway and Vercel."

---

## WHAT TO BUILD FIRST TODAY

1. Set up the FastAPI backend with a single `/chat` endpoint — 30 minutes
2. Get Gemini responding to a travel query — 30 minutes
3. Set up Supabase with the three tables — 20 minutes
4. Connect context retrieval to the prompt — 1 hour

If you can finish Phase 1 and Phase 2 before your interviews, you have a fully defensible project with real memory functionality. Phase 3 onwards makes it stronger but isn't required to talk about it confidently.