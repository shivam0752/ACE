import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

use_supabase = bool(SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "your_supabase_project_url")

if use_supabase:
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Connected to Supabase successfully!")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}. Falling back to SQLite.")
        use_supabase = False

# SQLite database setup for fallback/local development
DB_FILE = "ace_memory.db"

def init_sqlite():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create user_context table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_context (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        preference_key TEXT NOT NULL,
        preference_value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, preference_key),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)
    
    # Create interaction_history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interaction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        input TEXT NOT NULL,
        output TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)

    # Create metrics_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metrics_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        latency_ms REAL NOT NULL,
        status TEXT NOT NULL,
        budget_variance REAL,
        context_relevance_rating INTEGER,
        workflow_completed BOOLEAN NOT NULL,
        hallucination_detected BOOLEAN DEFAULT NULL,
        preference_retention_accurate BOOLEAN DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

if not use_supabase:
    init_sqlite()

def get_or_create_user(name: str = "Default User", user_id: str = "00000000-0000-0000-0000-000000000000") -> str:
    """Gets user_id or creates a new user if not exists."""
    if use_supabase:
        try:
            res = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
            if res.data:
                return res.data[0]["user_id"]
            
            # Create user
            insert_res = supabase.table("users").insert({"user_id": user_id, "name": name}).execute()
            return insert_res.data[0]["user_id"]
        except Exception as e:
            print(f"Supabase user error: {e}. Using SQLite fallback.")
    
    # SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
    
    cursor.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
    conn.commit()
    conn.close()
    return user_id

def get_user_preferences(user_id: str) -> dict:
    """Fetches user preferences as key-value pairs."""
    if use_supabase:
        try:
            res = supabase.table("user_context").select("preference_key, preference_value").eq("user_id", user_id).execute()
            return {item["preference_key"]: item["preference_value"] for item in res.data}
        except Exception as e:
            print(f"Supabase fetch preferences error: {e}. Using SQLite fallback.")
            
    # SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT preference_key, preference_value FROM user_context WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def save_user_preference(user_id: str, key: str, value: str):
    """Saves or updates user preference."""
    if use_supabase:
        try:
            # Upsert in Supabase (requires unique constraint user_id + preference_key)
            supabase.table("user_context").upsert({
                "user_id": user_id,
                "preference_key": key,
                "preference_value": value,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            return
        except Exception as e:
            print(f"Supabase upsert preference error: {e}. Using SQLite fallback.")

    # SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_context (user_id, preference_key, preference_value, updated_at)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id, preference_key) DO UPDATE SET
        preference_value = excluded.preference_value,
        updated_at = CURRENT_TIMESTAMP
    """, (user_id, key, value))
    conn.commit()
    conn.close()

def log_interaction(user_id: str, session_id: str, user_input: str, model_output: str):
    """Logs the user interaction."""
    if use_supabase:
        try:
            supabase.table("interaction_history").insert({
                "user_id": user_id,
                "session_id": session_id,
                "input": user_input,
                "output": model_output,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            return
        except Exception as e:
            print(f"Supabase log interaction error: {e}. Using SQLite fallback.")

    # SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO interaction_history (user_id, session_id, input, output, timestamp)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, session_id, user_input, model_output))
    conn.commit()
    conn.close()

def log_metrics(user_id: str, session_id: str, latency_ms: float, status: str, budget_variance: float = None, workflow_completed: bool = True, hallucination_detected: bool = None, preference_retention_accurate: bool = None):
    """Logs runtime execution metrics."""
    if use_supabase:
        try:
            supabase.table("metrics_logs").insert({
                "user_id": user_id,
                "session_id": session_id,
                "latency_ms": latency_ms,
                "status": status,
                "budget_variance": budget_variance,
                "workflow_completed": workflow_completed,
                "hallucination_detected": hallucination_detected,
                "preference_retention_accurate": preference_retention_accurate,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            return
        except Exception as e:
            print(f"Supabase log metrics error: {e}. Using SQLite fallback.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO metrics_logs (user_id, session_id, latency_ms, status, budget_variance, workflow_completed, hallucination_detected, preference_retention_accurate, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, session_id, latency_ms, status, budget_variance, workflow_completed, hallucination_detected, preference_retention_accurate))
    conn.commit()
    conn.close()

def submit_rating(session_id: str, rating: int):
    """Updates the user feedback context relevance rating for a given session."""
    if use_supabase:
        try:
            # Update the latest metric log for this session in Supabase
            res = supabase.table("metrics_logs").select("id").eq("session_id", session_id).order("timestamp", desc=True).limit(1).execute()
            if res.data:
                log_id = res.data[0]["id"]
                supabase.table("metrics_logs").update({"context_relevance_rating": rating}).eq("id", log_id).execute()
            return
        except Exception as e:
            print(f"Supabase submit rating error: {e}. Using SQLite fallback.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE metrics_logs 
    SET context_relevance_rating = ? 
    WHERE id = (
        SELECT id FROM metrics_logs 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    )
    """, (rating, session_id))
    conn.commit()
    conn.close()

def get_aggregated_metrics() -> dict:
    """Aggregates all 6 core metrics from the logs."""
    if use_supabase:
        try:
            res = supabase.table("metrics_logs").select("*").execute()
            rows = res.data
        except Exception as e:
            print(f"Supabase fetch metrics error: {e}. Using SQLite fallback.")
            rows = []
    else:
        rows = []
        
    if not rows:
        # Fetch from SQLite
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM metrics_logs ORDER BY timestamp DESC")
            rows = [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"SQLite fetch metrics error: {e}")
            rows = []
        finally:
            conn.close()

    total_runs = len(rows)
    if total_runs == 0:
        return {
            "workflow_completion_rate": 100.0,
            "average_latency_ms": 0.0,
            "average_budget_variance": 0.0,
            "average_context_relevance": 0.0,
            "preference_retention_accuracy": 100.0,
            "hallucination_rate": 0.0,
            "total_sessions": 0,
            "total_runs": 0,
            "recent_logs": []
        }

    successful_runs = sum(1 for r in rows if r.get("workflow_completed"))
    workflow_completion_rate = (successful_runs / total_runs) * 100.0

    latencies = [r.get("latency_ms") for r in rows if r.get("latency_ms") is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # Budget Variance (absolute average)
    variances = [abs(r.get("budget_variance")) for r in rows if r.get("budget_variance") is not None]
    avg_variance = (sum(variances) / len(variances)) * 100.0 if variances else 0.0

    # Context relevance rating
    ratings = [r.get("context_relevance_rating") for r in rows if r.get("context_relevance_rating") is not None]
    avg_relevance = sum(ratings) / len(ratings) if ratings else 0.0

    # Preference Retention Accuracy
    retention_checks = [1 if r.get("preference_retention_accurate") else 0 for r in rows if r.get("preference_retention_accurate") is not None]
    retention_accuracy = (sum(retention_checks) / len(retention_checks)) * 100.0 if retention_checks else 100.0

    # Hallucination Rate
    hallucination_checks = [1 if r.get("hallucination_detected") else 0 for r in rows if r.get("hallucination_detected") is not None]
    hallucination_rate = (sum(hallucination_checks) / len(hallucination_checks)) * 100.0 if hallucination_checks else 0.0

    unique_sessions = len(set(r.get("session_id") for r in rows))

    return {
        "workflow_completion_rate": round(workflow_completion_rate, 2),
        "average_latency_ms": round(avg_latency, 2),
        "average_budget_variance": round(avg_variance, 2),
        "average_context_relevance": round(avg_relevance, 2),
        "preference_retention_accuracy": round(retention_accuracy, 2),
        "hallucination_rate": round(hallucination_rate, 2),
        "total_sessions": unique_sessions,
        "total_runs": total_runs,
        "recent_logs": rows[:30]
    }

def update_audit(log_id: int, hallucination_detected: bool = None, preference_retention_accurate: bool = None):
    """Updates the hallucination audit and preference retention status for a log entry."""
    if use_supabase:
        try:
            update_data = {}
            if hallucination_detected is not None:
                update_data["hallucination_detected"] = hallucination_detected
            if preference_retention_accurate is not None:
                update_data["preference_retention_accurate"] = preference_retention_accurate
            
            if update_data:
                supabase.table("metrics_logs").update(update_data).eq("id", log_id).execute()
            return
        except Exception as e:
            print(f"Supabase update audit error: {e}. Using SQLite fallback.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if hallucination_detected is not None:
        cursor.execute("UPDATE metrics_logs SET hallucination_detected = ? WHERE id = ?", (hallucination_detected, log_id))
    if preference_retention_accurate is not None:
        cursor.execute("UPDATE metrics_logs SET preference_retention_accurate = ? WHERE id = ?", (preference_retention_accurate, log_id))
    conn.commit()
    conn.close()
