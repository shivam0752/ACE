import os
import json
import time
import re
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Import LangChain components
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import database and tools module
import db
import tools

# Load environment variables
load_dotenv()

# Configure Google Gemini API for legacy direct usage if needed
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key or gemini_key == "your_gemini_api_key_here":
    gemini_key = os.environ.get("GEMINI_API_KEY")

if not gemini_key:
    print("Warning: GEMINI_API_KEY environment variable is not set.")
else:
    genai.configure(api_key=gemini_key)


app = FastAPI(title="Aether Context Engine (ACE) API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "00000000-0000-0000-0000-000000000000"
    session_id: Optional[str] = "default_session"

class ChatResponse(BaseModel):
    response: str

class RateRequest(BaseModel):
    session_id: str
    rating: int

class AuditRequest(BaseModel):
    log_id: int
    hallucination_detected: Optional[bool] = None
    preference_retention_accurate: Optional[bool] = None

# Define LangChain Tools
@tool
def get_weather(location: str) -> str:
    """Fetches the 7-day weather forecast for a given location, including max/min temperatures and rain probability."""
    return json.dumps(tools.get_weather(location))

@tool
def get_exchange_rate(base_currency: str, target_currency: str) -> str:
    """Fetches the currency conversion rate between base_currency and target_currency."""
    return json.dumps(tools.get_exchange_rate(base_currency, target_currency))

@tool
def get_places_info(location: str, place_type: str = "tourist_attraction") -> str:
    """Finds attractions, points of interest, or hotel suggestions in a given location."""
    return json.dumps(tools.get_places_info(location, place_type))


def extract_and_save_preferences(user_id: str, user_msg: str, assistant_msg: str):
    """Background task to extract preferences from the turn and save them."""
    if not gemini_key:
        return
    
    extraction_prompt = (
        "You are an intelligent user preference extraction engine. "
        "Analyze the following conversation turn between a User and a Travel Assistant. "
        "Identify if the user explicitly stated or strongly implied any travel preferences, interests, constraints, or styles "
        "(such as budget level, destination type, dietary restrictions, preferred activities, hotel class, specific dislikes, etc.).\n\n"
        "Respond ONLY with a JSON list of key-value pairs representing updated preferences, or an empty list if none were found. "
        "Use exactly this JSON format: [{\"key\": \"preference_name\", \"value\": \"preference_value\"}]. "
        "Ensure keys are short and descriptive (e.g. 'budget_level', 'likes_nature', 'dislikes_crowds').\n\n"
        f"User Message: {user_msg}\n"
        f"Assistant Message: {assistant_msg}\n"
    )
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        # Enforce JSON output format
        response = model.generate_content(
            extraction_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        prefs = json.loads(response.text.strip())
        if isinstance(prefs, list):
            for item in prefs:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    db.save_user_preference(user_id, item["key"].strip(), item["value"].strip())
                    print(f"Extracted and saved preference: {item['key']} -> {item['value']}")
    except Exception as e:
        print(f"Error during preference extraction: {e}")

def extract_budget(text: str) -> Optional[float]:
    # Regex to find currency and number, e.g. ₹20,000, 20000, $500, etc.
    pattern = r'(?:[\$\u20A8-\u20B9]|\bINR\b|\bUSD\b)?\s*(\d{1,3}(?:,\d{3})+|\d+)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    for m in matches:
        val = float(m.replace(',', ''))
        if val > 100: # ignore very small numbers like number of guests or days
            return val
    return None

def verify_preference_retention(preferences: dict, plan: dict) -> bool:
    if not preferences:
        return True
    
    accommodations = plan.get("accommodation_suggestions", [])
    for pref_k, pref_v in preferences.items():
        pref_k_lower = pref_k.lower()
        pref_v_lower = pref_v.lower()
        if "budget" in pref_v_lower or "budget" in pref_k_lower:
            types = [h.get("type", "").lower() for h in accommodations]
            if types and all("luxury" in t for t in types):
                return False
        if "luxury" in pref_v_lower or "luxury" in pref_k_lower:
            types = [h.get("type", "").lower() for h in accommodations]
            if types and all("budget" in t for t in types):
                return False
    return True

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    if not gemini_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API Key is not configured. Please set the GEMINI_API_KEY environment variable."
        )
    start_time = time.time()
    user_id = "00000000-0000-0000-0000-000000000000"
    try:
        # 1. Ensure user exists
        user_id = db.get_or_create_user(user_id=request.user_id)
        
        # 2. Retrieve user context/preferences
        preferences = db.get_user_preferences(user_id)
        pref_context = ""
        if preferences:
            pref_context = "\n".join([f"- {k}: {v}" for k, v in preferences.items()])
            
        # 3. Pass 1: Tool routing using LangChain's Tool Calling layer
        live_data_payload = {}
        
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=gemini_key,
                temperature=0.0
            )
            llm_with_tools = llm.bind_tools([get_weather, get_exchange_rate, get_places_info])
            
            tool_routing_message = [
                SystemMessage(content="You are a tool routing agent. Decide if any tools are needed to answer the user query. Choose from: get_weather, get_exchange_rate, and get_places_info."),
                HumanMessage(content=request.message)
            ]
            
            ai_msg = llm_with_tools.invoke(tool_routing_message)
            
            if ai_msg.tool_calls:
                for tool_call in ai_msg.tool_calls:
                    tool_name = tool_call.get("name")
                    args = tool_call.get("args", {})
                    
                    if tool_name == "get_weather" and "location" in args:
                        print(f"[LANGCHAIN TOOL] Calling get_weather for {args['location']}")
                        res = tools.get_weather(args["location"])
                        live_data_payload["weather"] = res
                    elif tool_name == "get_exchange_rate" and "base_currency" in args and "target_currency" in args:
                        print(f"[LANGCHAIN TOOL] Calling get_exchange_rate from {args['base_currency']} to {args['target_currency']}")
                        res = tools.get_exchange_rate(args["base_currency"], args["target_currency"])
                        live_data_payload["exchange_rate"] = res
                    elif tool_name == "get_places_info" and "location" in args:
                        ptype = args.get("place_type", "tourist_attraction")
                        print(f"[LANGCHAIN TOOL] Calling get_places_info for {args['location']} (type: {ptype})")
                        res = tools.get_places_info(args["location"], ptype)
                        live_data_payload["places"] = res
        except Exception as tool_err:
            print(f"Error determining or executing tools via LangChain: {tool_err}")

        # 4. Pass 2: Generation using context, preferences, and fetched live data
        system_instruction = (
            "You are ACE (Aether Context Engine), an intelligent, stateful travel planning assistant. "
            "Help the user plan their trip by providing a detailed, engaging, and well-thought-out itinerary, "
            "along with budget recommendations and travel tips.\n\n"
            "You must output a structured JSON plan matching the schema below. "
            "If the user is NOT asking to plan a trip or you are just answering a conversational query, "
            "set `is_itinerary` to false and put your conversational response in the `conversational_response` field.\n\n"
            "JSON Response Schema:\n"
            "{\n"
            "  \"is_itinerary\": true,\n"
            "  \"destination\": \"Name of Destination (if planning a trip)\",\n"
            "  \"duration_days\": 3,\n"
            "  \"weather_forecast\": \"Short summary of weather forecast\",\n"
            "  \"currency_conversion\": \"Short summary of currency conversion rate if relevant, else null\",\n"
            "  \"itinerary\": [\n"
            "     {\n"
            "        \"day\": 1,\n"
            "        \"theme\": \"Day Theme\",\n"
            "        \"activities\": [\n"
            "           {\"time\": \"Morning/Afternoon/Evening\", \"activity\": \"Activity Name\", \"description\": \"Detailed description\"}\n"
            "        ]\n"
            "     }\n"
            "  ],\n"
            "  \"budget_breakdown\": {\n"
            "     \"accommodation\": \"estimated cost\",\n"
            "     \"transport\": \"estimated cost\",\n"
            "     \"food\": \"estimated cost\",\n"
            "     \"activities\": \"estimated cost\",\n"
            "     \"total_estimated\": \"total estimated cost\"\n"
            "  },\n"
            "  \"accommodation_suggestions\": [\n"
            "     {\"name\": \"Hotel Name\", \"type\": \"Budget/Mid-range/Luxury\", \"price_per_night\": \"price\", \"description\": \"short description\"}\n"
            "  ],\n"
            "  \"travel_tips\": [\n"
            "     \"tip 1\", \"tip 2\"\n"
            "  ],\n"
            "  \"conversational_response\": \"A warm, personal summary or response explaining the plan to the user.\"\n"
            "}\n"
        )
        
        if pref_context:
            system_instruction += (
                f"\n### Stored User Preferences:\n{pref_context}\n\n"
                "CRITICAL: You MUST strictly adhere to the above user preferences in all plans, suggestions, "
                "and answers. Do not recommend options that contradict them."
            )
        else:
            system_instruction += (
                "\nSince the user has no stored preferences yet, plan based on their query, "
                "and ask relevant preference questions if they are helpful."
            )
            
        final_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_key,
            temperature=0.7,
            model_kwargs={"response_mime_type": "application/json"}
        )
        
        user_message_with_live_data = request.message
        if live_data_payload:
            user_message_with_live_data += f"\n\n### Live Real-Time Data Fetched:\n{json.dumps(live_data_payload, indent=2)}"
            
        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_message_with_live_data)
        ]
        
        response = final_llm.invoke(messages)
        response_text = response.content
        
        # 5. Log interaction to history
        db.log_interaction(
            user_id=user_id,
            session_id=request.session_id,
            user_input=request.message,
            model_output=response_text
        )
        
        # 6. Extract user preferences asynchronously in the background
        background_tasks.add_task(
            extract_and_save_preferences,
            user_id=user_id,
            user_msg=request.message,
            assistant_msg=response_text
        )
        
        # 7. Log runtime metrics
        latency_ms = (time.time() - start_time) * 1000
        budget_variance = None
        preference_retention_accurate = True
        try:
            plan = json.loads(response_text)
            if plan.get("is_itinerary"):
                # Parse budget variance
                target_budget = extract_budget(request.message)
                estimated_budget_str = plan.get("budget_breakdown", {}).get("total_estimated")
                estimated_budget = extract_budget(str(estimated_budget_str)) if estimated_budget_str else None
                
                if target_budget and estimated_budget:
                    budget_variance = (estimated_budget - target_budget) / target_budget
                
                # Check preference retention accuracy
                preference_retention_accurate = verify_preference_retention(preferences, plan)
        except Exception as parse_err:
            print(f"Error parsing response JSON for metrics: {parse_err}")
            
        db.log_metrics(
            user_id=user_id,
            session_id=request.session_id,
            latency_ms=latency_ms,
            status="success",
            budget_variance=budget_variance,
            workflow_completed=True,
            preference_retention_accurate=preference_retention_accurate
        )
        
        return ChatResponse(response=response_text)
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        try:
            db.log_metrics(
                user_id=user_id,
                session_id=request.session_id,
                latency_ms=latency_ms,
                status="error",
                workflow_completed=False
            )
        except Exception as log_err:
            print(f"Failed to log error metrics: {log_err}")
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "ok", "api_key_configured": gemini_key is not None}

@app.get("/metrics")
async def get_metrics():
    try:
        return db.get_aggregated_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@app.post("/rate")
async def rate_session(request: RateRequest):
    try:
        db.submit_rating(request.session_id, request.rating)
        return {"status": "success", "message": f"Rating of {request.rating} submitted for session {request.session_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting rating: {str(e)}")

@app.post("/audit")
async def audit_log(request: AuditRequest):
    try:
        db.update_audit(
            log_id=request.log_id,
            hallucination_detected=request.hallucination_detected,
            preference_retention_accurate=request.preference_retention_accurate
        )
        return {"status": "success", "message": f"Audit updated for log {request.log_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating audit: {str(e)}")
