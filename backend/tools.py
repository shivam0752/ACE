import urllib.request
import json
import urllib.parse
import os
from typing import Dict, Any, List

def get_weather(location: str) -> Dict[str, Any]:
    """
    Fetches the 7-day weather forecast for a given location.
    Resolves the location to latitude and longitude using Nominatim,
    then queries Open-Meteo.
    """
    try:
        # Step 1: Geocoding via Nominatim
        encoded_location = urllib.parse.quote(location)
        geocode_url = f"https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1"
        
        req = urllib.request.Request(
            geocode_url, 
            headers={'User-Agent': 'AetherContextEngine/1.0 (contact: admin@ace.ai)'}
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if not data:
            return {"error": f"Could not find coordinates for location: {location}"}
            
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        display_name = data[0].get("display_name", location)
        
        # Step 2: Fetch weather from Open-Meteo
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_mean,weathercode&timezone=auto"
        
        with urllib.request.urlopen(weather_url, timeout=5) as response:
            weather_data = json.loads(response.read().decode('utf-8'))
            
        daily = weather_data.get("daily", {})
        forecasts = []
        if daily:
            time_list = daily.get("time", [])
            temp_max = daily.get("temperature_2m_max", [])
            temp_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_probability_mean", [])
            
            for i in range(min(7, len(time_list))):
                forecasts.append({
                    "date": time_list[i],
                    "max_temp": f"{temp_max[i]}°C" if i < len(temp_max) else "N/A",
                    "min_temp": f"{temp_min[i]}°C" if i < len(temp_min) else "N/A",
                    "rain_probability": f"{precip[i]}%" if i < len(precip) else "N/A"
                })
                
        return {
            "resolved_location": display_name,
            "latitude": lat,
            "longitude": lon,
            "forecast": forecasts
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather for {location}: {str(e)}"}

def get_exchange_rate(base_currency: str, target_currency: str) -> Dict[str, Any]:
    """
    Fetches the currency conversion rate between base_currency and target_currency.
    """
    try:
        base = base_currency.upper().strip()
        target = target_currency.upper().strip()
        url = f"https://open.er-api.com/v6/latest/{base}"
        
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get("result") != "success":
            return {"error": f"Failed to fetch exchange rates for {base}"}
            
        rates = data.get("rates", {})
        rate = rates.get(target)
        if not rate:
            return {"error": f"Currency {target} not supported or found under base {base}"}
            
        return {
            "base": base,
            "target": target,
            "rate": rate,
            "last_updated": data.get("time_last_update_utc", "N/A")
        }
    except Exception as e:
        return {"error": f"Failed to fetch exchange rate: {str(e)}"}

def get_places_info(location: str, place_type: str = "tourist_attraction") -> Dict[str, Any]:
    """
    Finds attractions/points of interest in the given location.
    Uses Google Places API if GOOGLE_PLACES_API_KEY is configured,
    otherwise falls back to OpenStreetMap Nominatim.
    """
    google_key = os.getenv("GOOGLE_PLACES_API_KEY")
    query = f"{location} {place_type}"
    
    if google_key and google_key != "your_google_places_api_key_here":
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={encoded_query}&key={google_key}"
            
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            results = data.get("results", [])
            places = []
            for item in results[:5]:
                location_data = item.get("geometry", {}).get("location", {})
                places.append({
                    "name": item.get("name"),
                    "address": item.get("formatted_address"),
                    "type": place_type,
                    "rating": item.get("rating"),
                    "user_ratings_total": item.get("user_ratings_total"),
                    "lat": location_data.get("lat"),
                    "lon": location_data.get("lng")
                })
                
            if places:
                return {
                    "source": "Google Places API",
                    "query": query,
                    "places": places
                }
        except Exception as e:
            print(f"Google Places API failed ({e}), falling back to Nominatim.")
            
    # Fallback to Nominatim
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=5"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'AetherContextEngine/1.0 (contact: admin@ace.ai)'}
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        places = []
        for item in data:
            places.append({
                "name": item.get("display_name", "").split(",")[0],
                "address": ", ".join(item.get("display_name", "").split(",")[1:4]),
                "type": item.get("type", "attraction"),
                "lat": item.get("lat"),
                "lon": item.get("lon")
            })
            
        if not places:
            return {"message": f"No specific {place_type} results found via OSM Nominatim for {location}."}
            
        return {
            "source": "OpenStreetMap Nominatim",
            "query": query,
            "places": places
        }
    except Exception as e:
        return {"error": f"Failed to fetch places info: {str(e)}"}

