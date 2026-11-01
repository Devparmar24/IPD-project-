#this is for the Agricultural_knowledge database that is it takes the data from the Crop_recommendation.csv and puts it into the database
import sqlite3
import csv
import logging
import zipfile
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ingest_archived_csv_to_knowledge_db(archive_path="archive.zip", csv_filename="Crop_recommendation.csv"):
    db_name = "agricultural_knowledge.db"
    
    # Step 1: Extract the CSV from the archive if it hasn't been extracted yet
    if os.path.exists(archive_path):
        logging.info(f"Extracting {csv_filename} from {archive_path}...")
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extract(csv_filename, path=".")
            logging.info("Extraction complete.")
        except Exception as e:
            logging.error(f"Failed to extract from archive: {e}")
            return
    elif not os.path.exists(csv_filename):
        logging.error(f"Archive '{archive_path}' and standalone file '{csv_filename}' both not found in E:\\Dev\\IPD Project\\")
        return

    # Step 2: Connect to SQLite and ingest the CSV data
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crop_ideal_conditions (
            crop_name TEXT PRIMARY KEY,
            min_temp REAL,
            max_temp REAL,
            min_humidity REAL,
            max_humidity REAL,
            min_ph REAL,
            max_ph REAL,
            min_rainfall REAL,
            max_rainfall REAL
        )
    ''')

    crop_stats = {}

    try:
        with open(csv_filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                crop = row['label'].title()
                temp = float(row['temperature'])
                humidity = float(row['humidity'])
                ph = float(row['ph'])
                rainfall = float(row['rainfall'])

                if crop not in crop_stats:
                    crop_stats[crop] = {
                        'temps': [], 'humidities': [], 'phs': [], 'rainfalls': []
                    }
                
                crop_stats[crop]['temps'].append(temp)
                crop_stats[crop]['humidities'].append(humidity)
                crop_stats[crop]['phs'].append(ph)
                crop_stats[crop]['rainfalls'].append(rainfall)

        for crop, data in crop_stats.items():
            min_temp, max_temp = min(data['temps']), max(data['temps'])
            min_hum, max_hum = min(data['humidities']), max(data['humidities'])
            min_ph, max_ph = min(data['phs']), max(data['phs'])
            min_rain, max_rain = min(data['rainfalls']), max(data['rainfalls'])

            cursor.execute('''
                INSERT OR REPLACE INTO crop_ideal_conditions 
                (crop_name, min_temp, max_temp, min_humidity, max_humidity, min_ph, max_ph, min_rainfall, max_rainfall)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (crop, min_temp, max_temp, min_hum, max_hum, min_ph, max_ph, min_rain, max_rain))

        conn.commit()
        conn.close()
        logging.info(f"Successfully processed '{csv_filename}' and updated '{db_name}'!")

    except Exception as e:
        logging.error(f"An error occurred while parsing the CSV: {e}")

if __name__ == "__main__":
    # Change "archive.zip" if your zip file has a different name (e.g., "archive (1).zip")
    ingest_archived_csv_to_knowledge_db(archive_path="archive.zip", csv_filename="Crop_recommendation.csv")