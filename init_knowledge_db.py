#this is for the Agricultural_knowledge database that is it takes the data from the Crop_recommendation.csv and puts it into the database
import sqlite3
import csv
import logging
import zipfile
import shutil
from pathlib import Path
from pathlib import PurePosixPath

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = PROJECT_DIR / "archive"


def ingest_archived_csv_to_knowledge_db(
    archive_path=ARCHIVE_DIR / "archive.zip",
    csv_filename=ARCHIVE_DIR / "Crop_recommendation.csv",
):
    archive_path = Path(archive_path)
    csv_path = Path(csv_filename)
    db_path = PROJECT_DIR / "Databases" / "agricultural_knowledge.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Use the standalone CSV when present; otherwise extract it from the ZIP.
    if not csv_path.exists() and archive_path.exists():
        logging.info(f"Extracting {csv_path.name} from {archive_path}...")
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                member = next(
                    (
                        name
                        for name in zf.namelist()
                        if PurePosixPath(name).name == csv_path.name
                    ),
                    None,
                )
                if member is None:
                    logging.error(f"'{csv_path.name}' was not found inside '{archive_path}'")
                    return
                with zf.open(member) as source, csv_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
            logging.info("Extraction complete.")
        except Exception as e:
            logging.error(f"Failed to extract from archive: {e}")
            return

    if not csv_path.exists():
        logging.error(f"CSV file not found: '{csv_path}'")
        return

    # Step 2: Connect to SQLite and ingest the CSV data
    conn = sqlite3.connect(db_path)
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
        with csv_path.open(mode='r', encoding='utf-8') as file:
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
        logging.info(f"Successfully processed '{csv_path}' and updated '{db_path}'!")

    except Exception as e:
        logging.error(f"An error occurred while parsing the CSV: {e}")

if __name__ == "__main__":
    ingest_archived_csv_to_knowledge_db()
