import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CropRecommendationEngine:
    def __init__(
        self,
        db_path=Path(__file__).resolve().parent / "Databases" / "farm_telemetry.db",
        city_name="Vasai",
    ):
        self.db_path = db_path
        self.city_name = city_name
        # The engine will fetch exact coordinates for this city dynamically
        self.lat, self.lon = self.geolocate_city(city_name)
        
        # Base expected yield (tons per hectare)
        self.base_yields = {"Rice": 4.5, "Cotton": 2.2, "Sugarcane": 70.0, "Millets": 1.5}
        
        # REQUIRED: Create a free account at data.gov.in to get your API key
        self.gov_api_key = "YOUR_DATA_GOV_IN_API_KEY_HERE" 

    def geolocate_city(self, city):
        """Converts a city name like 'Junagadh' into exact latitude and longitude."""
        logging.info(f"Geolocating coordinates for {city}...")
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if "results" in data:
                lat = data["results"][0]["latitude"]
                lon = data["results"][0]["longitude"]
                logging.info(f"Found {city} at Lat: {lat}, Lon: {lon}")
                return lat, lon
            else:
                logging.warning(f"City '{city}' not found. Defaulting to 19.39, 72.83.")
                return 19.39, 72.83
        except Exception as e:
            logging.error(f"Geocoding failed: {e}")
            return 19.39, 72.83

    def fetch_local_telemetry(self):
        logging.info("Fetching local ESP32 field telemetry...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT soil_moisture, temperature, humidity FROM field_telemetry ORDER BY rowid DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            return {"moisture": row[0], "temp": row[1], "humidity": row[2]} if row else None
        except sqlite3.OperationalError as e:
            logging.error(f"Database error: {e}")
            return None

    def fetch_14_day_weather(self):
        """Fetches the last 14 days of actual climate data for the specific GPS coordinates."""
        logging.info(f"Fetching 14-day climate history for {self.city_name}...")
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={self.lat}&longitude={self.lon}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,rain_sum&timezone=auto"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            total_rain = sum(data['daily']['rain_sum'])
            avg_max_temp = sum(data['daily']['temperature_2m_max']) / len(data['daily']['temperature_2m_max'])
            return {"total_rain_mm": total_rain, "avg_max_temp": avg_max_temp}
        except Exception as e:
            logging.error(f"Weather API failed: {e}")
            return {"total_rain_mm": 50.0, "avg_max_temp": 32.0}

    def fetch_live_market_prices(self):
        """
        Fetches real-time wholesale prices from the Indian Government's Open Data API.
        Converts Quintal prices to Per Ton (10 Quintals = 1 Ton).
        """
        logging.info("Attempting to fetch live wholesale prices from data.gov.in...")
        
        if self.gov_api_key == "YOUR_DATA_GOV_IN_API_KEY_HERE":
            logging.warning("No Government API key provided. Falling back to cached market estimates.")
            return {"Rice": 25000, "Cotton": 65000, "Sugarcane": 3000, "Millets": 35000}

        # Official resource ID for daily Mandi prices (may require updating based on current data.gov.in portal)
        resource_id = "9ef84268-d588-465a-a308-a864a43d0070" 
        url = f"https://api.data.gov.in/resource/{resource_id}?api-key={self.gov_api_key}&format=json&limit=100"
        
        prices_per_ton = {}
        try:
            response = requests.get(url)
            response.raise_for_status()
            records = response.json().get("records", [])
            
            # Parse the JSON for specific commodities and convert Modal Price (Rs/Quintal) to Rs/Ton
            for record in records:
                commodity = record.get("commodity", "").title()
                price_per_quintal = float(record.get("modal_price", 0))
                
                if commodity == "Paddy(Dhan)(Common)":
                    prices_per_ton["Rice"] = price_per_quintal * 10
                elif commodity == "Cotton":
                    prices_per_ton["Cotton"] = price_per_quintal * 10
                elif commodity == "Jowar(Sorghum)":
                    prices_per_ton["Millets"] = price_per_quintal * 10

            # Fill in missing data if the live market is closed or missing a specific crop today
            defaults = {"Rice": 25000, "Cotton": 65000, "Sugarcane": 3000, "Millets": 35000}
            for crop in defaults:
                if crop not in prices_per_ton:
                    prices_per_ton[crop] = defaults[crop]
                    
            return prices_per_ton
            
        except Exception as e:
            logging.error(f"Live Market API failed: {e}. Using cached data.")
            return {"Rice": 25000, "Cotton": 65000, "Sugarcane": 3000, "Millets": 35000}

    def calculate_yield(self, crop, climate_data, seed_quality):
        base = self.base_yields.get(crop, 0)
        seed_multipliers = {"Premium": 1.15, "Standard": 1.0, "Low": 0.80}
        seed_factor = seed_multipliers.get(seed_quality, 1.0)
        
        climate_factor = 1.0
        if crop == "Rice" and climate_data["total_rain_mm"] < 40:
            climate_factor = 0.6 
        elif crop == "Millets" and climate_data["total_rain_mm"] < 40:
            climate_factor = 1.1 
            
        return round(base * seed_factor * climate_factor, 2)

    def generate_recommendation(self, seed_quality="Standard"):
        telemetry = self.fetch_local_telemetry()
        if not telemetry:
            logging.error("No ESP32 telemetry found.")
            return

        weather = self.fetch_14_day_weather()
        prices = self.fetch_live_market_prices()
        
        logging.info(f"--- ALGORITHM INPUTS ---")
        logging.info(f"Location: {self.city_name} (Lat: {self.lat}, Lon: {self.lon})")
        logging.info(f"Local Soil: {telemetry['moisture']}% Moisture | {telemetry['temp']}°C")
        logging.info(f"14-Day Weather: {weather['total_rain_mm']}mm Rain | {weather['avg_max_temp']:.1f}°C Avg Max")
        
        best_crop = None
        highest_revenue = 0
        analysis_report = {}

        for crop in self.base_yields.keys():
            proj_yield = self.calculate_yield(crop, weather, seed_quality)
            revenue = proj_yield * prices.get(crop, 0)
            analysis_report[crop] = {"yield": proj_yield, "revenue": revenue}
            
            if crop == "Rice" and telemetry["moisture"] < 30:
                continue 

            if revenue > highest_revenue:
                highest_revenue = revenue
                best_crop = crop

        logging.info(f"--- FINANCIAL PROJECTION ---")
        for c, data in analysis_report.items():
            logging.info(f"{c}: {data['yield']} Tons/Hectare -> Rs. {data['revenue']:,.2f}")
            
        logging.info(f">>> OPTIMAL RECOMMENDATION: {best_crop.upper()} <<<")


if __name__ == "__main__":
    # You can now type any city name here (e.g., "Alibag", "Junagadh", "Pune")
    engine = CropRecommendationEngine(city_name="Alibag")
    engine.generate_recommendation(seed_quality="Premium")