import sqlite3

conn = sqlite3.connect("farm_telemetry.db")
cursor = conn.cursor()

# Ensure the table exists even if mqtt_ingest.py hasn't run yet
cursor.execute('''CREATE TABLE IF NOT EXISTS field_telemetry 
                  (soil_moisture REAL, temperature REAL, humidity REAL)''')

# Inject realistic demo data (45.5% moisture, 31°C, 65% humidity)
cursor.execute("INSERT INTO field_telemetry (soil_moisture, temperature, humidity) VALUES (45.5, 31.0, 65.0)")

conn.commit()
conn.close()

print("Demo ESP32 telemetry injected successfully.")