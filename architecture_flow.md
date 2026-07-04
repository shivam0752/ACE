# 🌀 Aether Context Engine (ACE) — Flow & Justification

This document details the overall flow of the **Aether Context Engine (ACE)** application and explains how it justifies the following professional description:

> **Aether Context Engine (ACE) — Automated Infrastructure Orchestration**
> * Engineered a stateful orchestration framework merging headless automation tools with large language models to process context-aware dialogue chains, establishing 6 evaluation metrics to ensure system runtime accuracy.

---

## 🏗️ 1. Overall Application Flow

ACE is a stateful orchestration engine designed for context-aware travel itinerary generation. It follows a multi-stage, two-pass execution cycle:

```
[ User Request ]
       │
       ▼
 ┌───────────┐      1. Retrieve Context
 │  FastAPI  │ ◄───────────────────────────┐
 └─────┬─────┘                             │
       │                              ┌────┴────┐
       ├────────────────────────────► │ DB / Memory │ (SQLite/Supabase)
       │      6. Background Extract   └────▲────┘
       │                                   │
       ▼                                   │ 7. Save Metrics
 ┌───────────┐                             │
 │ LangChain │ (Pass 1: Tool Routing)      │
 └─────┬─────┘                             │
       │                                   │
       ▼                                   │
 ┌───────────┐ (Headless API Automation)   │
 │   Tools   │ ──► Weather / Places / Rates│
 └─────┬─────┘                             │
       │                                   │
       ▼                                   │
 ┌───────────┐ (Pass 2: JSON Synthesis)    │
 │  Gemini   │ ────────────────────────────┘
 └─────┬─────┘
       │
       ▼
[ Structured JSON Itinerary ]
```

### Step-by-Step Execution Sequence

1. **Dialogue Input**: The user sends a request (e.g., *"Plan a 3-day budget trip to Paris"*) via the React Frontend.
2. **Stateful Context Retrieval**: The backend fetches existing user preferences (e.g., `budget_level: budget`, `dietary: vegetarian`) and chat history from SQLite/Supabase.
3. **Pass 1: Intent & Tool Routing**: LangChain coordinates with `gemini-2.5-flash` to evaluate the request and dynamically determine if headless external tools are needed (e.g., weather forecast, currency exchange rate, tourist places lookup).
4. **Headless Automation Execution**: Selected API tools fetch real-time data asynchronously (Open-Meteo, OpenStreetMap, or Google Places API).
5. **Pass 2: Dialogue Synthesis**: Gemini synthesizes the itinerary, combining the user's input, retrieved user preferences, and real-time tool data into a structured JSON response matching a strict schema.
6. **Asynchronous Preference Extraction**: In a background thread, the engine analyzes the latest turn to extract new preferences (e.g. *"prefers luxury hotels"*) and updates the database.
7. **Runtime Metrics Evaluation**: The system measures and writes 6 distinct evaluation metrics to the database, exposing them on the admin dashboard.

---

## 🎯 2. Justifying the Core Description

Below is the mapping showing exactly how the codebase validates the professional description:

### 🔑 "Stateful Orchestration Framework"
* **Implementation**: Stored in [db.py](file:///d:/antigravity/projects/ACE/backend/db.py), the engine maintains a relational database storing `user_context` (key-value preferences) and `interaction_history`.
* **Justification**: Unlike typical stateless LLM calls, ACE retrieves historical state before generation and runs a background extraction task (`extract_and_save_preferences` in [main.py](file:///d:/antigravity/projects/ACE/backend/main.py#L80-L113)) to persistently save new preferences for future turns.

### 🔌 "Merging Headless Automation Tools with LLMs"
* **Implementation**: Built in [tools.py](file:///d:/antigravity/projects/ACE/backend/tools.py) (functions: `get_weather`, `get_exchange_rate`, `get_places_info`) and integrated with LangChain's Tool Calling layer in [main.py](file:///d:/antigravity/projects/ACE/backend/main.py#L161-L199).
* **Justification**: Gemini decides which tools to invoke, and LangChain routes the arguments dynamically to raw, headless HTTP integrations, seamlessly injecting external data back into the LLM context.

### 💬 "Process Context-Aware Dialogue Chains"
* **Implementation**: Structured system instructions in [main.py](file:///d:/antigravity/projects/ACE/backend/main.py#L201-L258). Stored preferences are dynamically appended as instructions (e.g., `CRITICAL: You MUST strictly adhere to the above user preferences`).
* **Justification**: Every generation is strictly bound by historical context, ensuring the dialogue chain remains cohesive and personalization persists across multiple user queries.

### 📊 "Establishing 6 Evaluation Metrics to Ensure System Runtime Accuracy"
* **Implementation**: Formulated inside [db.py](file:///d:/antigravity/projects/ACE/backend/db.py#L241-L316) and calculated dynamically in [main.py](file:///d:/antigravity/projects/ACE/backend/main.py#L288-L332).
* **Justification**: ACE tracks exactly **6 core runtime evaluation metrics** that assess the health, accuracy, and relevance of the agent:
  1. **Workflow Completion Rate**: Evaluates system runtime reliability by recording success vs. failure status.
  2. **Response Latency (ms)**: Measures real-time performance and system overhead.
  3. **Budget Variance**: Parses the user's requested budget constraints vs. the generated itinerary cost to flag budget overflows.
  4. **Context Relevance Rating**: Logs user feedback on the relevance and utility of the response.
  5. **Preference Retention Accuracy**: Employs an automated logic rule (e.g. flagging luxury suggestions made during active budget preferences) to verify LLM compliance with user constraints.
  6. **Hallucination Rate**: Connects to an auditing interface allowing human-in-the-loop reviewers to review interactions and flag factual inconsistencies.
